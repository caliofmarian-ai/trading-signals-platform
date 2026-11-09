"""Prospective second-resolution duration candidate, NOT a runtime expiry policy.

Consumes the already computed adjusted movement time. It neither recomputes
market indicators nor authorizes publication, calibration, or broker execution.
The active strategy is deliberately not wired to this module until lifecycle
migration and evidence-cohort separation are verified.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_EVEN
from math import isfinite, ulp


POLICY = "ADJUSTED_MOVEMENT_SECOND_CEILING_V1"
_MAX_FLOAT_SNAP_SECONDS = Decimal("0.000000001")


class DurationCandidateUnavailable(ValueError):
    """No feasible whole-second candidate exists inside the supplied limits."""


@dataclass(frozen=True)
class DurationCandidate:
    policy: str
    adjusted_seconds: float
    duration_seconds: int
    minimum_seconds: float
    maximum_seconds: float

    @property
    def duration_minutes(self) -> float:
        """Compatibility projection; duration_seconds is the primary value."""
        return self.duration_seconds / 60


def _seconds(value: int | float, name: str) -> tuple[Decimal, Decimal]:
    if type(value) not in (int, float):
        raise DurationCandidateUnavailable(f"{name} must be a finite positive number")
    try:
        if not isfinite(value) or value <= 0:
            raise DurationCandidateUnavailable(f"{name} must be a finite positive number")
        raw = Decimal(str(value)) * 60
        approximate_seconds = float(raw)
        if not isfinite(approximate_seconds):
            raise DurationCandidateUnavailable(f"{name} exceeds the supported numerical range")
    except (OverflowError, ValueError) as exc:
        raise DurationCandidateUnavailable(f"{name} is invalid") from exc
    # Suppress only binary-float representation drift at positive whole seconds.
    # This is bounded by four ULPs and at most one nanosecond; genuine fractional
    # seconds are still ceiled, not rounded down. Zero is never synthesized.
    normalized = raw
    if type(value) is float:
        nearest = raw.to_integral_value(rounding=ROUND_HALF_EVEN)
        tolerance = min(Decimal(str(4 * ulp(approximate_seconds))), _MAX_FLOAT_SNAP_SECONDS)
        if nearest > 0 and abs(raw - nearest) <= tolerance:
            normalized = nearest
    return raw, normalized


def prepare_candidate(
    adjusted_minutes: int | float,
    *,
    minimum_minutes: int | float,
    maximum_minutes: int | float,
) -> DurationCandidate:
    """Smallest feasible whole-second horizon, never a claimed optimal expiry.

    The minimum is honored before quantization. A maximum is a hard bound, not
    permission to shorten an infeasible required move. Neither limits nor safety
    multipliers have defaults. There are no clock timestamps or time extensions.
    """
    raw, adjusted = _seconds(adjusted_minutes, "adjusted_minutes")
    minimum_raw, minimum = _seconds(minimum_minutes, "minimum_minutes")
    maximum_raw, maximum = _seconds(maximum_minutes, "maximum_minutes")
    if maximum < minimum:
        raise DurationCandidateUnavailable("maximum_minutes must be at least minimum_minutes")
    required = max(adjusted, minimum)
    if required > maximum:
        raise DurationCandidateUnavailable("required movement time exceeds the maximum")
    duration = int(required.to_integral_value(rounding=ROUND_CEILING))
    if duration <= 0 or Decimal(duration) > maximum:
        raise DurationCandidateUnavailable("no whole-second duration fits inside the limits")
    return DurationCandidate(
        policy=POLICY,
        adjusted_seconds=float(raw),
        duration_seconds=duration,
        minimum_seconds=float(minimum_raw),
        maximum_seconds=float(maximum_raw),
    )
