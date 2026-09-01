from __future__ import annotations

from dataclasses import replace

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
from core.signal_event import SignalEventUnavailable, build_signal_event


def _decision(kind: str = "OPEN_NOW") -> DecisionObject:
    return DecisionObject(
        kind=kind,
        signal_id="sig-v2-real-opportunity" if kind in {"PRE", "CONFIRM", "OPEN_NOW"} else None,
        setup=SetupContext("EUR/USD", "BUY", 1_720_000_000, "M1", "cycle-real", "binary_strategy_v2"),
        market_context=MarketContext(1.11234, 0.0002, 0.0008, "UP", "ACTIVE", "STABLE", 0.0012),
        structure=StructureContext(1.11, 1.12, 1.11, 1.12, 0.01, 0.0012, "INSIDE", "VALID"),
        time=TimeContext(3.1, 3.8, 5.0, 0.76, None, "READY"),
        score=ScoreContext(86.0, 0.86, {"trend": 24.0}, tier="SCORE_OPEN_BAND"),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": "SCORE_OPEN_BAND"},
        explanations=("Real canonical evidence.",),
    )


def test_builds_complete_internal_v3_candidate_without_distribution() -> None:
    event = build_signal_event(_decision(), buffer_mode="medium", created_ts=1_720_000_002)

    assert event.stage == "OPEN_NOW"
    assert event.signal_id == "sig-v2-real-opportunity"
    assert event.buffer_distance == pytest.approx(0.0008)
    assert event.expiry_minutes == 5
    assert event.entry_price == pytest.approx(1.11234)
    assert event.distribution_enabled is False
    assert event.payload["canonical_specification"] == "ALGO_SPEC_v3.0.0"


def test_legacy_buffer_price_is_only_explicit_distance_alias() -> None:
    payload = build_signal_event(_decision(), buffer_mode="SMALL", created_ts=1_720_000_002).to_dict()
    assert payload["buffer_price"] == payload["buffer_distance"]


def test_same_identity_survives_pre_confirm_open_lifecycle() -> None:
    ids = {
        build_signal_event(replace(_decision(), kind=kind), buffer_mode="LARGE", created_ts=1_720_000_002).signal_id
        for kind in ("PRE", "CONFIRM", "OPEN_NOW")
    }
    assert ids == {"sig-v2-real-opportunity"}


def test_refuses_non_actionable_or_incomplete_real_time_evidence() -> None:
    with pytest.raises(SignalEventUnavailable, match="actionable"):
        build_signal_event(_decision("NO_SIGNAL"), buffer_mode="MEDIUM", created_ts=1_720_000_002)

    incomplete = replace(_decision(), time=replace(_decision().time, model_expiry=None))
    with pytest.raises(SignalEventUnavailable, match="model_expiry"):
        build_signal_event(incomplete, buffer_mode="MEDIUM", created_ts=1_720_000_002)


def test_refuses_unknown_buffer_mode_and_cannot_enable_distribution() -> None:
    with pytest.raises(SignalEventUnavailable, match="buffer_mode"):
        build_signal_event(_decision(), buffer_mode="invented", created_ts=1_720_000_002)

    event = build_signal_event(_decision(), buffer_mode="MEDIUM", created_ts=1_720_000_002)
    with pytest.raises(SignalEventUnavailable, match="distribution"):
        replace(event, distribution_enabled=True)
