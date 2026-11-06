"""Synthetic lifecycle regression tests; no market efficacy or broker evidence."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from core import fsm_runtime as fsm
from state_store.state_store import default_fsm_state, validate_fsm_state, StateValidationError


def _pre(symbol="EUR/USD", identity="sig-v3-first", candle=1_800_000_000):
    return {"symbol": symbol, "signal_id": identity, "kind": "PRE", "candle_ts": candle,
            "decision_policy": "PHYSICAL_ONLY_V3"}


def _admit(state, item, now):
    state, event = fsm.apply_transition(state, item, now)
    if event["trigger"] in {"watchlist_added", "watchlist_refreshed", "watchlist_replaced"}:
        state["per_symbol"][item["symbol"]]["physical_signal_id"] = item["signal_id"]
    return state, event


def test_reject_keeps_fast_symbol_focus_and_no_same_symbol_timer():
    state, _ = _admit(default_fsm_state(), _pre(), 1000)
    state, event = fsm.apply_transition(state, {**_pre(), "kind": "REJECT"}, 1002)
    assert event["new_state"] == "WATCHLIST"
    assert state["per_symbol"]["EUR/USD"]["cooldown_until_ts"] is None
    state, event = _admit(state, _pre(identity="sig-v3-distinct", candle=1_800_000_060), 1003)
    assert event["trigger"] == "watchlist_refreshed"
    assert state["physical_attention"]["until_ts"] == 1120


def test_cross_symbol_window_is_exact_and_restart_safe():
    state, _ = _admit(default_fsm_state(), _pre(), 1000)
    restarted = validate_fsm_state(json.loads(json.dumps(state)))
    before = deepcopy(restarted)
    state, event = _admit(restarted, _pre("GBP/USD", "sig-v3-second"), 1119)
    assert event["trigger"] == "cross_symbol_attention_active"
    assert state["physical_attention"] == before["physical_attention"]
    assert state["watchlist"] == ["EUR/USD"]
    state, event = _admit(state, _pre("GBP/USD", "sig-v3-second"), 1120)
    assert event["trigger"] == "watchlist_added"
    assert state["physical_attention"]["symbol"] == "GBP/USD"


def test_attention_does_not_interrupt_an_existing_other_symbol_chain():
    state, _ = _admit(default_fsm_state(), _pre(), 1000)
    state, _ = _admit(state, _pre("GBP/USD", "sig-v3-second"), 1120)
    state, event = fsm.apply_transition(state, {**_pre(), "kind": "CONFIRM"}, 1121)
    assert event["trigger"] == "confirm_seen"


def test_old_physical_cooldown_is_retired_without_reviving_identity():
    state = default_fsm_state()
    state["per_symbol"]["EUR/USD"] = {"state":"COOLDOWN", "cooldown_until_ts":2000,
        "current_signal_id":"sig-v3-closed", "physical_signal_id":"sig-v3-closed"}
    migrated, events = fsm.reconcile_state(state, 1000, active_symbols=["EUR/USD"])
    row = migrated["per_symbol"]["EUR/USD"]
    assert row["state"] == "IDLE" and row["cooldown_until_ts"] is None
    assert row["physical_closed_signal_id"] == "sig-v3-closed"
    assert events[0]["trigger"] == "physical_cooldown_retired"
    assert fsm.reconcile_state(migrated, 1001)[1] == []


def test_focus_lease_expiry_has_no_physical_cooldown():
    state, _ = _admit(default_fsm_state(), _pre(), 1000)
    state, events = fsm.reconcile_state(state, 1900, active_symbols=["EUR/USD"])
    assert state["watchlist"] == [] and events[0]["new_state"] == "IDLE"
    assert state["per_symbol"]["EUR/USD"]["cooldown_until_ts"] is None


def test_closed_focus_can_yield_capacity_after_attention_without_replacing_active_idea():
    state, _ = _admit(default_fsm_state(), _pre(), 1000)
    state, _ = _admit(state, _pre("GBP/USD", "sig-v3-second"), 1120)
    state, _ = fsm.apply_transition(state, {**_pre(), "kind":"REJECT"}, 1121)
    state, event = _admit(state, _pre("USD/JPY", "sig-v3-third"), 1240)
    assert event["trigger"] == "watchlist_replaced"
    assert state["watchlist"] == ["USD/JPY", "GBP/USD"]


@pytest.mark.parametrize("field,value", [("until_ts",1121), ("started_ts",True), ("symbol",""), ("policy","UNKNOWN")])
def test_corrupt_attention_fails_validation(field, value):
    state, _ = _admit(default_fsm_state(), _pre(), 1000)
    state["physical_attention"][field] = value
    with pytest.raises(StateValidationError):
        validate_fsm_state(state)


def test_internal_open_can_be_followed_by_distinct_setup_before_expiry(canonical_runtime_root):
    from tests.canonical.integration.test_binary_strategy_v2 import _inputs
    from core.physical_params import migrate_physical_params
    from core.strategy_v3 import decide, lifecycle_context
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    m1, m5, old = _inputs(canonical_runtime_root)
    params, state = migrate_physical_params(old), default_fsm_state()
    for now in (1000,1002,1031):
        evaluated = decide(m1,m5,params,buffer_mode="SMALL",
            context=lifecycle_context(state,"EUR/USD",now_ts=now))
        handoff = advance_persistent_fsm(state,evaluated.decision,now_ts=now)
        state = handoff.next_state
        if now == 1000:
            original_pre = evaluated.decision
    assert handoff.accepted_stage == "OPEN_NOW"
    assert not evaluated.execution_time.available
    state = validate_fsm_state(json.loads(json.dumps(state)))
    replay = advance_persistent_fsm(state,original_pre,now_ts=1032)
    assert not replay.stage_handoff_ready and replay.reason == "DUPLICATE_CLOSED_OPPORTUNITY"
    assert lifecycle_context(state,"EUR/USD",now_ts=1032)["physical_stage"] == "PRE"
    fresh = replace(original_pre,signal_id="sig-v3-fresh-market-setup",
        setup=replace(original_pre.setup,evaluated_ts=original_pre.setup.evaluated_ts+60,
                      cycle_id="distinct-candle"))
    next_pre = advance_persistent_fsm(state,fresh,now_ts=1033)
    assert next_pre.accepted_stage == "PRE"
    row = next_pre.next_state["per_symbol"]["EUR/USD"]
    assert row["physical_pre_ts"] == 1033 and row["physical_confirm_ts"] is None
    assert row["last_open_candle_ts"] is None
