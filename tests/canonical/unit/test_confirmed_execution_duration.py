"""Synthetic evidence for advance preparation, not approval of live calibration."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest


def _decision(stage, stamp, *, model=5.3, needed=3.8):
    from core.decision_object import (DecisionObject, MarketContext, RejectContext, ScoreContext,
        SetupContext, StrategicFlags, StructureContext, TimeContext)
    from core.market_history_policy import HISTORY_POLICY
    return DecisionObject(kind=stage, signal_id="sig-v3-confirm-duration",
        setup=SetupContext("EUR/USD", "BUY", stamp, "M1", f"cycle-{stamp}", "test"),
        market_context=MarketContext(1.1, 0.001, 0.002, "UP", "ACTIVE", "STABLE"),
        structure=StructureContext(1.09, 1.12, 1.09, 1.12, 0.03, 0.02, "INSIDE", "VALID"),
        score=ScoreContext(None, None, {}, tier="PHYSICAL_READY"),
        time=TimeContext(3.0, needed, model, needed/model, None, "READY", model/needed),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"decision_policy": "PHYSICAL_ONLY_V3", "history_policy": HISTORY_POLICY},
        explanations=("Synthetic duration lifecycle evidence.",))


def _calibration(source="SYNTHETIC-TEST-ONLY"):
    from core.execution_model import ExecutionCalibration
    return ExecutionCalibration(1.0, 0.1, 1.0, 15.0, source)


def _step(state, stage, stamp, *, calibration=True, bind=True, model=5.3, needed=3.8):
    from core.execution_model import derive_execution_time
    from core.fsm_decision_adapter import interpret_decision
    from core.v2_fsm_orchestrator import advance_persistent_fsm, bind_confirmed_execution_time
    decision = _decision(stage, stamp, model=model, needed=needed)
    value = _calibration() if calibration is True else calibration or None
    execution = derive_execution_time(decision, interpret_decision(decision), value)
    handoff = advance_persistent_fsm(state, decision, now_ts=stamp)
    if bind:
        handoff, execution = bind_confirmed_execution_time(handoff, decision, execution)
    return decision, handoff, execution


def _confirmed(*, calibration=True, bind=True):
    from state_store.state_store import default_fsm_state
    _, pre, _ = _step(default_fsm_state(), "PRE", 1000)
    return _step(pre.next_state, "CONFIRM", 1002, calibration=calibration, bind=bind)


def test_exact_duration_is_available_at_confirm_and_survives_restart_and_new_model(canonical_runtime_root):
    from core.signal_event import build_signal_event
    from state_store.state_store import validate_fsm_state
    decision, confirm, prepared = _confirmed()
    assert prepared.confirm_expiry_minutes == pytest.approx(4.77)
    assert prepared.open_now_expiry_minutes is None
    event = build_signal_event(decision, buffer_mode="MEDIUM", created_ts=1002, execution_time=prepared)
    assert event.confirm_expiry_minutes == pytest.approx(4.77)
    assert event.expiry_minutes is None
    state = validate_fsm_state(json.loads(json.dumps(confirm.next_state)))
    before = deepcopy(state)
    _, opened, execution = _step(state, "OPEN_NOW", 1032, model=5.4)
    assert execution.available
    assert execution.open_now_expiry_minutes == prepared.confirm_expiry_minutes
    assert execution.open_now_expiry_minutes != pytest.approx(5.4 * 0.9)
    assert opened.stage_handoff_ready  # independent physical acceptance remains explicit
    assert state == before  # binding never changes the caller's persisted snapshot


@pytest.mark.parametrize("changes,reason", [
    ({"model": 7.0}, "NO_LONGER_FEASIBLE"),
    ({"needed": 4.9}, "NO_LONGER_FEASIBLE"),
    ({"calibration": False}, "REVALIDATION_UNAVAILABLE"),
])
def test_changed_conditions_block_open_without_changing_confirmed_duration(canonical_runtime_root, changes, reason):
    _, confirm, prepared = _confirmed()
    original = deepcopy(confirm.next_state["per_symbol"]["EUR/USD"]["physical_confirm_execution"])
    _, opened, execution = _step(confirm.next_state, "OPEN_NOW", 1032, **changes)
    assert not execution.available
    assert execution.open_now_expiry_minutes is None
    assert execution.confirm_expiry_minutes is None
    assert reason in execution.explanation
    assert opened.next_state["per_symbol"]["EUR/USD"]["physical_confirm_execution"] == original
    assert original["duration_minutes"] == prepared.confirm_expiry_minutes


def test_changed_calibration_cannot_replace_the_prepared_duration(canonical_runtime_root):
    _, confirm, _ = _confirmed()
    _, _, execution = _step(confirm.next_state, "OPEN_NOW", 1032, calibration=_calibration("DIFFERENT-TEST-ONLY"))
    assert not execution.available
    assert execution.explanation == "CONFIRM_DURATION_CALIBRATION_CHANGED"


def test_missing_or_legacy_confirm_plan_cannot_be_invented_at_open(canonical_runtime_root):
    _, confirm, _ = _confirmed(bind=False)
    _, _, execution = _step(confirm.next_state, "OPEN_NOW", 1032)
    assert not execution.available
    assert execution.explanation == "EXACT_GOVERNED_DURATION_UNAVAILABLE_AT_CONFIRM"


def test_uncalibrated_confirm_remains_study_when_calibration_appears(canonical_runtime_root):
    _, confirm, execution = _confirmed(calibration=False)
    row = confirm.next_state["per_symbol"]["EUR/USD"]
    assert not execution.available
    assert row["physical_confirm_execution_status"] == "UNAVAILABLE"
    assert row["physical_confirm_execution"] is None
    assert row["physical_confirm_model_seconds"] == 5.3 * 60
    _, repeated, execution = _step(confirm.next_state, "CONFIRM", 1004)
    assert not execution.available
    assert repeated.next_state["per_symbol"]["EUR/USD"]["physical_confirm_execution"] is None
    _, _, execution = _step(repeated.next_state, "OPEN_NOW", 1032)
    assert not execution.available


def test_repeated_confirm_retains_first_preparation(canonical_runtime_root):
    _, confirm, prepared = _confirmed()
    _, repeated, execution = _step(confirm.next_state, "CONFIRM", 1004, model=5.4)
    assert execution.confirm_expiry_minutes == prepared.confirm_expiry_minutes
    assert repeated.next_state["per_symbol"]["EUR/USD"]["physical_confirm_ts"] == 1002


def test_infeasible_calibrated_confirm_is_blocked_and_never_downgraded_to_study(canonical_runtime_root):
    from state_store.state_store import default_fsm_state, validate_fsm_state
    _, pre, _ = _step(default_fsm_state(), "PRE", 1000)
    _, confirm, execution = _step(pre.next_state, "CONFIRM", 1002, needed=4.9)
    assert not execution.available
    assert execution.explanation == "CONFIRM_DURATION_BLOCKED"
    row = confirm.next_state["per_symbol"]["EUR/USD"]
    assert row["physical_confirm_execution_status"] == "BLOCKED"
    assert row["physical_confirm_execution"] is None
    state = validate_fsm_state(json.loads(json.dumps(confirm.next_state)))
    _, opened, execution = _step(state, "OPEN_NOW", 1032)
    assert not execution.available
    assert execution.explanation == "CONFIRM_DURATION_BLOCKED"
    assert opened.next_state["per_symbol"]["EUR/USD"]["physical_confirm_execution_status"] == "BLOCKED"


def test_physical_confirm_cannot_publish_only_an_interval(canonical_runtime_root):
    from core.signal_event import SignalEventUnavailable, build_signal_event
    decision, _, prepared = _confirmed()
    event = build_signal_event(decision, buffer_mode="MEDIUM", created_ts=1002, execution_time=prepared)
    with pytest.raises(SignalEventUnavailable, match="physical CONFIRM requires an exact"):
        replace(event, confirm_expiry_minutes=None)


@pytest.mark.parametrize("field,value", [
    ("duration_minutes", float("nan")), ("duration_minutes", float("inf")),
    ("duration_minutes", True), ("duration_minutes", 99),
    ("calibration_source", ""), ("signal_id", "sig-v3-another"),
    ("direction", "SELL"), ("confirmed_ts", 1003),
])
def test_corrupt_frozen_plan_is_rejected_on_reload(canonical_runtime_root, field, value):
    from state_store.state_store import StateValidationError, validate_fsm_state
    _, confirm, _ = _confirmed()
    state = deepcopy(confirm.next_state)
    state["per_symbol"]["EUR/USD"]["physical_confirm_execution"][field] = value
    with pytest.raises(StateValidationError):
        validate_fsm_state(state)
