from __future__ import annotations

from pathlib import Path

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
from core.v2_fsm_orchestrator import advance_persistent_fsm, current_opportunity_signal_id
from state_store.state_store import default_fsm_state, load_fsm_state, save_fsm_state


def _decision(kind: str, signal_id: str, candle_ts: int) -> DecisionObject:
    tier = {
        "PRE": "SCORE_PRE_BAND",
        "CONFIRM": "SCORE_CONFIRM_BAND",
        "OPEN_NOW": "SCORE_OPEN_BAND",
    }[kind]
    return DecisionObject(
        kind=kind,
        signal_id=signal_id,
        setup=SetupContext("EUR/USD", "BUY", candle_ts, "M1", f"cycle-{candle_ts}", "test"),
        market_context=MarketContext(1.1, 0.001, 0.002, "UP", "NORMAL", "LOW"),
        structure=StructureContext(1.09, 1.12, 1.09, 1.12, 0.03, 0.02, "INSIDE", "VALID"),
        time=TimeContext(2.0, 2.0, 5.0, 0.4, None, "READY", 2.5),
        score=ScoreContext(80.0, 0.8, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Canonical evidence.",),
    )


def _after_pre(signal_id: str = "sig-v2-one", candle_ts: int = 100) -> dict:
    return advance_persistent_fsm(
        default_fsm_state(), _decision("PRE", signal_id, candle_ts), now_ts=candle_ts + 1
    ).next_state


def test_pre_and_confirm_persist_one_opportunity_identity_and_release_exact_stage() -> None:
    state = default_fsm_state()
    pre = advance_persistent_fsm(state, _decision("PRE", "sig-v2-one", 100), now_ts=101)
    assert pre.accepted and pre.state_changed
    assert pre.requested_stage == "PRE"
    assert pre.accepted_stage == "PRE"
    assert pre.stage_handoff_ready is True
    assert pre.trade_execution_ready is False
    assert pre.next_state["per_symbol"]["EUR/USD"]["state"] == "WATCHLIST"
    assert current_opportunity_signal_id(pre.next_state, "EUR/USD") == "sig-v2-one"

    confirm = advance_persistent_fsm(
        pre.next_state, _decision("CONFIRM", "sig-v2-one", 160), now_ts=161
    )
    assert confirm.accepted and confirm.state_changed
    assert confirm.requested_stage == "CONFIRM"
    assert confirm.accepted_stage == "CONFIRM"
    assert confirm.stage_handoff_ready is True
    assert confirm.trade_execution_ready is False
    assert confirm.next_state["per_symbol"]["EUR/USD"]["state"] == "CONFIRMED"
    assert current_opportunity_signal_id(confirm.next_state, "EUR/USD") == "sig-v2-one"


def test_same_stage_and_candle_do_not_rewrite_or_rerelease_persistent_state() -> None:
    decision = _decision("PRE", "sig-v2-one", 100)
    first = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)
    duplicate = advance_persistent_fsm(first.next_state, decision, now_ts=103)

    assert duplicate.accepted is True
    assert duplicate.accepted_stage is None
    assert duplicate.stage_handoff_ready is False
    assert duplicate.trade_execution_ready is False
    assert duplicate.state_changed is False
    assert duplicate.transition_event is None
    assert duplicate.reason == "DUPLICATE_STAGE_CANDLE"
    assert duplicate.reason_family == "DUPLICATE"
    assert duplicate.next_state == first.next_state


def test_open_now_persists_release_marker_without_false_live_sent_state() -> None:
    state = _after_pre()
    before = _decision("OPEN_NOW", "sig-v2-one", 160)
    result = advance_persistent_fsm(state, before, now_ts=161)

    assert result.accepted is True
    assert result.requested_stage == "OPEN_NOW"
    assert result.accepted_stage == "OPEN_NOW"
    assert result.stage_handoff_ready is True
    assert result.candidate_ready is True
    assert result.trade_execution_ready is True
    assert result.state_changed is True
    assert result.reason == "OPEN_NOW_STAGE_ACCEPTED"
    assert result.next_state["per_symbol"]["EUR/USD"]["state"] == "WATCHLIST"
    assert result.next_state["per_symbol"]["EUR/USD"]["last_open_candle_ts"] == 160
    assert current_opportunity_signal_id(result.next_state, "EUR/USD") == "sig-v2-one"


def test_exact_duplicate_open_now_is_observed_but_not_released_twice() -> None:
    state = _after_pre()
    decision = _decision("OPEN_NOW", "sig-v2-one", 160)
    first = advance_persistent_fsm(state, decision, now_ts=161)
    duplicate = advance_persistent_fsm(first.next_state, decision, now_ts=162)

    assert first.accepted_stage == "OPEN_NOW"
    assert first.stage_handoff_ready is True
    assert duplicate.accepted is True
    assert duplicate.accepted_stage is None
    assert duplicate.stage_handoff_ready is False
    assert duplicate.trade_execution_ready is False
    assert duplicate.state_changed is False
    assert duplicate.reason == "DUPLICATE_STAGE_CANDLE"
    assert duplicate.reason_family == "DUPLICATE"
    assert duplicate.transition_event is None
    assert duplicate.next_state == first.next_state


def test_open_now_on_new_candle_for_same_opportunity_is_not_false_duplicate() -> None:
    state = _after_pre()
    first = advance_persistent_fsm(
        state, _decision("OPEN_NOW", "sig-v2-one", 160), now_ts=161
    )
    next_candle = advance_persistent_fsm(
        first.next_state, _decision("OPEN_NOW", "sig-v2-one", 220), now_ts=221
    )

    assert next_candle.accepted is True
    assert next_candle.accepted_stage == "OPEN_NOW"
    assert next_candle.stage_handoff_ready is True
    assert next_candle.trade_execution_ready is True
    assert next_candle.state_changed is True
    assert next_candle.next_state["per_symbol"]["EUR/USD"]["last_open_candle_ts"] == 220


def test_new_pre_identity_clears_prior_open_marker_so_same_candle_is_independent() -> None:
    first_open = advance_persistent_fsm(
        _after_pre("sig-v2-one", 100),
        _decision("OPEN_NOW", "sig-v2-one", 160),
        now_ts=161,
    )
    new_pre = advance_persistent_fsm(
        first_open.next_state,
        _decision("PRE", "sig-v2-two", 160),
        now_ts=162,
    )

    assert new_pre.accepted_stage == "PRE"
    assert current_opportunity_signal_id(new_pre.next_state, "EUR/USD") == "sig-v2-two"
    assert new_pre.next_state["per_symbol"]["EUR/USD"]["last_open_candle_ts"] is None

    second_open = advance_persistent_fsm(
        new_pre.next_state,
        _decision("OPEN_NOW", "sig-v2-two", 160),
        now_ts=163,
    )
    assert second_open.accepted_stage == "OPEN_NOW"
    assert second_open.stage_handoff_ready is True
    assert second_open.trade_execution_ready is True


def test_open_now_duplicate_marker_survives_persisted_restart(tmp_path: Path) -> None:
    first = advance_persistent_fsm(
        _after_pre(), _decision("OPEN_NOW", "sig-v2-one", 160), now_ts=161
    )
    path = tmp_path / "focus_state.json"
    save_fsm_state(first.next_state, path=str(path))
    restored = load_fsm_state(path=str(path))

    assert restored["per_symbol"]["EUR/USD"]["state"] == "WATCHLIST"
    assert restored["per_symbol"]["EUR/USD"]["last_open_candle_ts"] == 160
    assert current_opportunity_signal_id(restored, "EUR/USD") == "sig-v2-one"

    duplicate = advance_persistent_fsm(
        restored, _decision("OPEN_NOW", "sig-v2-one", 160), now_ts=200
    )
    assert duplicate.reason == "DUPLICATE_STAGE_CANDLE"
    assert duplicate.reason_family == "DUPLICATE"
    assert duplicate.stage_handoff_ready is False
    assert duplicate.trade_execution_ready is False
    assert duplicate.state_changed is False


def test_confirm_or_open_now_cannot_switch_opportunity_identity() -> None:
    state = _after_pre()
    result = advance_persistent_fsm(
        state, _decision("CONFIRM", "sig-v2-other", 160), now_ts=161
    )

    assert result.accepted is False
    assert result.accepted_stage is None
    assert result.stage_handoff_ready is False
    assert result.reason_family == "IDENTITY"
    assert result.state_changed is False
    assert result.reason == "SIGNAL_ID_CONTINUITY_REQUIRED"
    assert current_opportunity_signal_id(result.next_state, "EUR/USD") == "sig-v2-one"


def test_open_now_without_pre_path_is_blocked() -> None:
    result = advance_persistent_fsm(
        default_fsm_state(), _decision("OPEN_NOW", "sig-v2-one", 100), now_ts=101
    )
    assert result.accepted is False
    assert result.accepted_stage is None
    assert result.stage_handoff_ready is False
    assert result.trade_execution_ready is False
    assert result.reason in {"SIGNAL_ID_CONTINUITY_REQUIRED", "CANONICAL_PRE_PATH_REQUIRED"}
