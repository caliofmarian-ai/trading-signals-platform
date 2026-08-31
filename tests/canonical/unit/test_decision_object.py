from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.decision_object import (
    DecisionObject,
    MarketContext,
    RejectContext,
    ScoreContext,
    SetupContext,
    StrategicFlags,
    StructureContext,
    TimeContext,
)


def _valid_decision() -> DecisionObject:
    return DecisionObject(
        kind="CONFIRM",
        signal_id="sig-v2-test",
        setup=SetupContext("EUR/USD", "BUY", 1_800_000_000, "M1", "cycle-1", "FINNHUB"),
        market_context=MarketContext(1.101, 0.0002, 0.0006, "WITH_TREND", "NORMAL", "STABLE", 0.0012),
        structure=StructureContext(
            support=1.100,
            resistance=1.103,
            lower_boundary=1.100,
            upper_boundary=1.103,
            corridor_width=0.003,
            available_distance=0.002,
            position="INSIDE",
            feasibility_state="VALID",
            explanation="room exists toward resistance",
        ),
        time=TimeContext(3.0, 3.3, 5.0, 0.66, 0.66, "READY"),
        score=ScoreContext(
            total=78.0,
            normalized=0.78,
            components={"context_trend": 20.0, "structure_corridor": 22.0, "time_feasibility": 18.0},
            penalties={"instability": 0.0},
            tier="STRONG",
        ),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"candidate_state": "CONFIRM"},
        explanations=("structure and time are feasible",),
    )


def test_decision_object_exposes_all_canonical_semantic_families() -> None:
    payload = _valid_decision().to_dict()

    assert set(payload) == {
        "kind", "signal_id", "setup", "market_context", "structure", "time", "score", "strategic_flags",
        "reject", "fsm_inputs", "explanations", "schema_version", "producer", "compatibility_mode",
    }
    assert payload["time"]["model_time_reach_ratio"] == pytest.approx(0.66)
    assert "expiry_minutes" not in payload["time"]
    assert "buffer_price" not in payload["market_context"]


def test_decision_object_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        _valid_decision().schema_version = "changed"  # type: ignore[misc]


def test_rejectable_decision_requires_explicit_reject_semantics() -> None:
    valid = _valid_decision()
    with pytest.raises(ValueError, match="reject semantics"):
        DecisionObject(
            kind="REJECT",
            signal_id=None,
            setup=valid.setup,
            market_context=valid.market_context,
            structure=valid.structure,
            time=valid.time,
            score=valid.score,
            strategic_flags=StrategicFlags(False, True, True, False, True, True, False),
            reject=RejectContext(),
            fsm_inputs={},
            explanations=("structure is invalid",),
        )


@pytest.mark.parametrize(
    ("time_state", "ratio"),
    [("GUARANTEED", 0.5), ("READY", -0.1), ("READY", float("inf"))],
)
def test_time_context_rejects_invented_or_invalid_evidence(time_state: str, ratio: float) -> None:
    with pytest.raises(ValueError):
        TimeContext(3.0, 3.0, 5.0, ratio, 0.6, time_state)


def test_structure_rejects_reversed_boundaries() -> None:
    with pytest.raises(ValueError, match="boundaries are reversed"):
        StructureContext(None, None, 1.2, 1.1, 0.1, 0.05, "INSIDE", "VALID")


def test_score_rejects_out_of_range_normalization() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        ScoreContext(total=110.0, normalized=1.1, components={"trend": 110.0})
