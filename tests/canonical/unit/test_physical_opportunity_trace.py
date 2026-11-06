"""Synthetic lifecycle evidence; never a real delivery or calibration result."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json

import pytest


@pytest.fixture
def tracing(canonical_runtime_root, monkeypatch):
    for key, value in {"OWNER_SIGNAL_DELIVERY_ENABLED":"true", "OWNER_TELEGRAM_ID":"123456789",
        "SHADOW_MODE":"true", "SHADOW_MODEL_TIME_RESEARCH_ENABLED":"true",
        "ENABLE_BROKER_EXECUTION":"false"}.items():
        monkeypatch.setenv(key, value)
    from tests.canonical.integration.test_binary_strategy_v2 import _inputs
    from core.physical_params import migrate_physical_params
    from core import strategy_v3, owner_signal_delivery
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    from intelligence import physical_opportunity_trace as trace
    m1, m5, old = _inputs(canonical_runtime_root)
    params, state = migrate_physical_params(old), default_fsm_state()
    base = m1[0]["ts"] + 10
    monkeypatch.setattr(owner_signal_delivery, "pre_receipt_ts", lambda *a: base + .25)
    def forbidden(**kwargs):
        pytest.fail("trace attempted a Telegram publication")
    from core import telegram_publisher
    monkeypatch.setattr(telegram_publisher, "send_message", forbidden)
    def cycle(stamp, *, observe=True):
        nonlocal state
        result = strategy_v3.decide(m1, m5, params, buffer_mode="SMALL",
            context=strategy_v3.lifecycle_context(state, "EUR/USD", now_ts=stamp))
        handoff = advance_persistent_fsm(state, result.decision, now_ts=stamp)
        state = handoff.next_state
        before = deepcopy((state, params))
        if observe:
            trace.observe(result, handoff, params, decision_ts=stamp,
                          observed_at=stamp+.6, provider="FINNHUB")
        assert (state, params) == before
        return result, handoff
    def saved():
        key = trace.algo_params_sha256(params)
        return trace._read(trace._path(key), key)
    return trace, cycle, saved, base, params, strategy_v3


def _reject_noise(tracing, monkeypatch):
    _, cycle, _, base, _, strategy = tracing
    baseline, _ = cycle(base+3)
    market = replace(baseline.market,
        context=replace(baseline.market.context, noise_context="UNSTABLE"),
        noise_reasons=("WICK_BODY_RATIO",))
    monkeypatch.setattr(strategy, "evaluate_market", lambda *a, **k: market)


def test_trace_explains_real_fsm_exit_before_pre_lead_without_mutating_decisions(tracing, monkeypatch, capsys):
    trace, cycle, saved, base, _, _ = tracing
    cycle(base)
    cycle(base+2)
    _reject_noise(tracing, monkeypatch)
    result, handoff = cycle(base+7)
    assert result.decision.kind == "REJECT" and handoff.resulting_state == "WATCHLIST"
    state = saved()
    assert state["event_totals"] == {"PRE":1,"CONFIRM":1,"EXIT_BEFORE_OPEN":1}
    row = next(iter(state["records"].values()))
    assert row["closed"] and set(row["events"]) == {"PRE","CONFIRM","EXIT"}
    pre, end = row["events"]["PRE"], row["events"]["EXIT"]
    assert pre["pre_receipt_available_at_evaluation"] is False
    assert pre["pre_api_age_seconds"] is None  # API acceptance was later than evaluation
    assert end["pre_api_age_seconds"] == 6.75
    assert end["remaining_pre_lead_seconds"] == 23.25
    assert end["since_first_observed_pre_seconds"] == 7
    assert end["since_first_observed_confirm_seconds"] == 5
    assert end["cooldown_remaining_seconds"] == 0
    assert end["noise_reasons"] == ["WICK_BODY_RATIO"]
    assert end["evaluation_candle_age_seconds"] == 17
    assert state["exit_noise_reasons"] == {"WICK_BODY_RATIO":1}
    output = capsys.readouterr().out
    assert "EXIT_BEFORE_OPEN" in output and "LIFECYCLE_OBSERVATION_ONLY" in output
    assert "latest_price" not in output and "123456789" not in output
    assert "score" not in output.lower()
    assert "sig-v3-" not in output
    # Later rejections and cooldown cannot be relabelled as extra episodes.
    cycle(base+9)
    assert saved() == state


def test_trace_is_restart_safe_deduplicated_and_not_a_study_or_approved_open(tracing):
    trace, cycle, saved, base, params, _ = tracing
    result, handoff = cycle(base)
    trace.observe(result, handoff, params, decision_ts=base, observed_at=base+.8, provider="FINNHUB")
    cycle(base+2)
    result, handoff = cycle(base+31)
    assert handoff.accepted_stage == "OPEN_NOW" and not result.execution_time.available
    state = saved()
    assert state["event_totals"] == {"PRE":1,"CONFIRM":1,"OPEN_NOW":1}
    assert state["exit_blockers"] == {}
    key = trace.algo_params_sha256(params)
    # Re-reading persistent evidence and replaying an accepted handoff cannot duplicate it.
    trace._last_report.clear()
    trace.observe(result, handoff, params, decision_ts=base+31, observed_at=base+32, provider="FINNHUB")
    assert saved() == state
    from intelligence import physical_expiry_calibration
    assert not physical_expiry_calibration._path().exists()
    assert trace._read(trace._path(key), key) == state


def test_chains_begun_before_tracing_have_no_backfilled_pre(tracing):
    _, cycle, saved, base, _, _ = tracing
    cycle(base, observe=False)
    cycle(base+2)
    cycle(base+31)
    assert saved()["records"] == {} and saved()["event_totals"] == {}


@pytest.mark.parametrize("disabled", ["provider","shadow","broker","research"])
def test_trace_only_uses_existing_opted_in_shadow_scope(tracing, monkeypatch, disabled):
    trace, cycle, saved, base, params, _ = tracing
    result, handoff = cycle(base, observe=False)
    if disabled != "provider":
        key, value = {"shadow":("SHADOW_MODE","false"), "broker":("ENABLE_BROKER_EXECUTION","true"),
                      "research":("SHADOW_MODEL_TIME_RESEARCH_ENABLED","false")}[disabled]
        monkeypatch.setenv(key,value)
    trace.observe(result, handoff, params, decision_ts=base, observed_at=base+1,
                  provider="TWELVE_DATA" if disabled=="provider" else "FINNHUB")
    assert saved()["records"] == {}


def test_trace_bounds_and_evicts_by_time_even_after_sorted_json_restart(tracing):
    trace, cycle, saved, base, params, _ = tracing
    result, handoff = cycle(base, observe=False)
    # All are declared synthetic independent opportunities; no market efficacy asserted.
    for index in range(trace.MAX_RECORDS + 3):
        signal_id = "sig-v3-" + str(100-index)
        state = deepcopy(handoff.next_state)
        state["per_symbol"]["EUR/USD"]["physical_signal_id"] = signal_id
        source_handoff = replace(handoff, signal_id=signal_id, next_state=state)
        source_evaluation = replace(result, decision=replace(result.decision, signal_id=signal_id))
        trace.observe(source_evaluation, source_handoff, params, decision_ts=base+index,
                      observed_at=base+index+.6, provider="FINNHUB")
        if index == trace.MAX_RECORDS//2:
            trace._path(trace.algo_params_sha256(params)).write_text(json.dumps(saved(), sort_keys=True))
    state = saved()
    assert len(state["records"]) == trace.MAX_RECORDS
    assert state["event_totals"]["PRE"] == trace.MAX_RECORDS + 3
    assert sha256(b"sig-v3-100").hexdigest() not in state["records"]
    assert min(row["events"]["PRE"]["decision_ts"] for row in state["records"].values()) == base+3
    assert len(json.dumps(state).encode()) < trace.MAX_BYTES


def test_scope_change_corruption_and_clock_rollback_do_not_rewrite_evidence(tracing):
    trace, cycle, saved, base, params, _ = tracing
    result, handoff = cycle(base)
    cycle(base+2)
    before = saved()
    trace.observe(result, handoff, params, decision_ts=base-1, observed_at=base+3, provider="FINNHUB")
    assert saved() == before
    with pytest.raises(ValueError, match="INVALID_TRACE_TIME"):
        trace.observe(result, handoff, params, decision_ts=base+5, observed_at=base+4, provider="FINNHUB")
    key = trace.algo_params_sha256(params)
    with pytest.raises(ValueError, match="INVALID_TRACE_SCOPE"):
        trace._read(trace._path(key), "a"*64)
    assert saved() == before
    path = trace._path(key)
    original = path.read_bytes()
    path.write_text("[]")
    with pytest.raises(ValueError, match="INVALID_TRACE_SCOPE"):
        trace._read(path, key)
    assert path.read_text() == "[]"  # invalid evidence is never silently reset
    path.write_bytes(original)


def test_mismatched_stage_source_cannot_create_a_trace(tracing):
    trace, cycle, saved, base, params, _ = tracing
    result, handoff = cycle(base, observe=False)
    with pytest.raises(ValueError, match="TRACE_SOURCE_IDENTITY_MISMATCH"):
        trace.observe(result, replace(handoff, signal_id="sig-v3-different"), params,
                      decision_ts=base, observed_at=base+1, provider="FINNHUB")
    assert saved()["records"] == {}


def test_a_rejection_after_observed_open_is_not_a_failed_confirm(tracing, monkeypatch):
    _, cycle, saved, base, _, strategy = tracing
    cycle(base)
    cycle(base+2)
    result, _ = cycle(base+31)
    market = replace(result.market,
        context=replace(result.market.context, noise_context="UNSTABLE"), noise_reasons=("WICK_BODY_RATIO",))
    monkeypatch.setattr(strategy, "evaluate_market", lambda *a, **k: market)
    cycle(base+32)
    state = saved()
    assert state["event_totals"]["EXIT_AFTER_OPEN"] == 1
    assert "EXIT_BEFORE_OPEN" not in state["event_totals"]
    assert state["exit_blockers"] == state["exit_noise_reasons"] == {}


def test_byte_bound_matches_indented_atomic_storage_and_keeps_new_evidence(tracing, monkeypatch):
    trace, cycle, saved, base, params, _ = tracing
    result, handoff = cycle(base)
    path = trace._path(trace.algo_params_sha256(params))
    monkeypatch.setattr(trace, "MAX_BYTES", path.stat().st_size + 256)
    for index in range(1,4):
        signal_id = "sig-v3-next-" + str(index)
        state = deepcopy(handoff.next_state)
        state["per_symbol"]["EUR/USD"]["physical_signal_id"] = signal_id
        trace.observe(replace(result, decision=replace(result.decision, signal_id=signal_id)),
            replace(handoff, signal_id=signal_id, next_state=state), params,
            decision_ts=base+index, observed_at=base+index+.6, provider="FINNHUB")
        assert path.stat().st_size <= trace.MAX_BYTES
        assert saved()["event_totals"]["PRE"] == index+1
        assert sha256(signal_id.encode()).hexdigest() in saved()["records"]
    assert len(saved()["records"]) == 1
