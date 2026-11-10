"""Synthetic arithmetic evidence only; not calibration or runtime acceptance."""
from dataclasses import FrozenInstanceError, asdict
import json
import math

import pytest

from intelligence.second_precision_duration import (
    POLICY, DurationCandidateUnavailable, prepare_candidate,
)


@pytest.mark.parametrize("minutes,seconds", [
    (3.45, 207), (8.6, 516), (4.77, 287), (5, 300),
    (0.05, 3), (8.600001, 517), (2.375, 143),
])
def test_candidate_preserves_seconds_without_ceiling_to_a_minute(minutes, seconds):
    result = prepare_candidate(minutes, minimum_minutes=.01, maximum_minutes=15)
    assert result.policy == POLICY
    assert result.duration_seconds == seconds
    assert type(result.duration_seconds) is int
    assert result.duration_minutes == seconds / 60
    assert result.adjusted_seconds == pytest.approx(minutes * 60)
    assert 0 <= result.duration_seconds - result.adjusted_seconds < 1
    json.dumps(asdict(result), allow_nan=False)


def test_consumes_existing_directional_physics_time_without_new_multiplier():
    buffer_distance, directional_speed = .000516, .00006
    existing_adjusted_time = buffer_distance / directional_speed
    result = prepare_candidate(existing_adjusted_time, minimum_minutes=1, maximum_minutes=15)
    assert result.duration_seconds == 516  # 8 min 36 s, not 9 min


@pytest.mark.parametrize("invalid", [None, True, False, "3.45", 0, -1, float("nan"), float("inf"), -float("inf"), 10**400])
@pytest.mark.parametrize("field", ["adjusted_minutes", "minimum_minutes", "maximum_minutes"])
def test_invalid_or_missing_evidence_never_creates_a_duration(invalid, field):
    values = dict(adjusted_minutes=3.45, minimum_minutes=1, maximum_minutes=15)
    values[field] = invalid
    with pytest.raises(DurationCandidateUnavailable):
        prepare_candidate(**values)


def test_minimum_is_applied_before_second_quantization():
    result = prepare_candidate(.5, minimum_minutes=1.01, maximum_minutes=2)
    assert result.duration_seconds == 61


@pytest.mark.parametrize("needed,minimum,maximum", [(16, 1, 15), (8.605, 1, 8.609), (1, 2, 1), (.001, .001, .01)])
def test_infeasible_horizon_is_not_clamped_into_an_apparent_success(needed, minimum, maximum):
    with pytest.raises(DurationCandidateUnavailable):
        prepare_candidate(needed, minimum_minutes=minimum, maximum_minutes=maximum)


def test_exact_maximum_and_machine_drift_do_not_create_an_extra_second():
    for needed in (8.6, math.nextafter(8.6, math.inf), math.nextafter(8.6, 0)):
        result = prepare_candidate(needed, minimum_minutes=1, maximum_minutes=8.6)
        assert result.duration_seconds == 516
    with pytest.raises(DurationCandidateUnavailable):
        prepare_candidate(8.6000000001, minimum_minutes=1, maximum_minutes=8.6)


def test_candidate_is_immutable_and_contains_no_opening_time_or_execution_authority():
    result = prepare_candidate(3.45, minimum_minutes=1, maximum_minutes=15)
    with pytest.raises(FrozenInstanceError):
        result.duration_seconds = 300
    assert set(asdict(result)) == {
        "policy", "adjusted_seconds", "duration_seconds", "minimum_seconds", "maximum_seconds",
    }


def test_sweep_never_uses_integer_minute_buckets_or_shortens_required_movement():
    values = []
    for second in range(60, 900):
        needed = (second + .25) / 60
        result = prepare_candidate(needed, minimum_minutes=1, maximum_minutes=15)
        assert result.duration_seconds == second + 1
        assert 0 < result.duration_seconds - result.adjusted_seconds < 1
        values.append(result.duration_seconds)
    assert len(set(values)) == 840
