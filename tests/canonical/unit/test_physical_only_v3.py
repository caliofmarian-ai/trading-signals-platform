"""Synthetic regression evidence only; fixtures never approve a real calibration."""
import copy
import importlib
import json

import pytest

from tests.canonical.integration.test_binary_strategy_v2 import _inputs
from tests.canonical.unit.test_execution_expiry_calibration import _entry
from tests.canonical.unit.test_shadow_model_time_research import _sample


@pytest.fixture
def physical(canonical_runtime_root):
    from core.physical_params import migrate_physical_params
    m1, m5, params = _inputs(canonical_runtime_root)
    return canonical_runtime_root, m1, m5, migrate_physical_params(params)


def test_active_v3_does_not_calculate_any_classical_or_physics_scores(physical, monkeypatch):
    root, m1, m5, params = physical
    from core import scoring_model, strategy_v3, trade_physics
    def forbidden(*a, **k):
        pytest.fail("score computation called by physical V3")
    monkeypatch.setattr(scoring_model, "evaluate_score", forbidden)
    monkeypatch.setattr(trade_physics, "_clamp", forbidden)
    monkeypatch.setattr(trade_physics, "_band", forbidden)
    result = strategy_v3.decide(m1, m5, params, buffer_mode="SMALL")
    assert result.decision.kind == "PRE"
    assert result.scoring.context.total is None
    assert result.scoring.context.normalized is None
    assert not result.scoring.context.components
    assert result.trade_physics.ready
    assert result.trade_physics.TPS is None
    exported = result.decision.to_dict()
    assert "score" not in exported
    assert exported["decision_policy"] == "PHYSICAL_ONLY_V3"
    assert not {"S", "T", "P", "V", "TPS"} & exported["trade_physics"].keys()
    assert "score_total" not in result.decision.fsm_inputs


def _advance_cycle(m1, m5, params, state, stamp):
    from core.strategy_v3 import decide, lifecycle_context
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    evaluation = decide(m1, m5, params, buffer_mode="SMALL",
                        context=lifecycle_context(state, "EUR/USD", now_ts=stamp))
    handoff = advance_persistent_fsm(state, evaluation.decision, now_ts=stamp)
    return evaluation, handoff


def test_physical_stages_order_identity_lead_and_restart(physical):
    _, m1, m5, params = physical
    from state_store.state_store import default_fsm_state, validate_fsm_state
    from core.signal_execution_gate import prepare_signal_execution
    pre, a = _advance_cycle(m1, m5, params, default_fsm_state(), 1000)
    assert a.accepted_stage == "PRE"
    assert a.next_state["per_symbol"]["EUR/USD"]["replacement_score"] is None
    state = validate_fsm_state(json.loads(json.dumps(a.next_state)))
    confirm, b = _advance_cycle(m1, m5, params, state, 1002)
    assert b.accepted_stage == "CONFIRM"
    early, c = _advance_cycle(m1, m5, params, b.next_state, 1029)
    assert early.decision.kind == "CONFIRM"
    assert not c.stage_handoff_ready
    opened, d = _advance_cycle(m1, m5, params, b.next_state, 1030)
    assert d.accepted_stage == "OPEN_NOW"
    assert pre.decision.signal_id == confirm.decision.signal_id == opened.decision.signal_id
    execution = prepare_signal_execution(d, opened.decision, buffer_mode="SMALL", created_ts=1030,
                                         execution_time=opened.execution_time)
    assert not execution.distribution_allowed
    assert execution.reason == "EXECUTION_TIME_UNAVAILABLE"


def test_forged_open_cannot_skip_confirm_or_lead(physical):
    _, m1, m5, params = physical
    from core.strategy_v3 import decide
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    pre, a = _advance_cycle(m1, m5, params, default_fsm_state(), 1000)
    forced = decide(m1, m5, params, buffer_mode="SMALL", context={
        "physical_stage": "OPEN_NOW", "opportunity_signal_id": pre.decision.signal_id,
        "opportunity_direction": pre.decision.setup.direction})
    result = advance_persistent_fsm(a.next_state, forced.decision, now_ts=1035)
    assert not result.stage_handoff_ready
    assert result.reason == "PHYSICAL_LIFECYCLE_ORDER_REQUIRED"


@pytest.mark.parametrize("gate", ["activity", "noise", "space", "speed", "time"])
def test_physical_failures_reject_every_stage(physical, monkeypatch, gate):
    _, m1, m5, params = physical
    from dataclasses import replace
    from core import strategy_v3 as strategy
    baseline = strategy.decide(m1, m5, params, buffer_mode="SMALL")
    if gate in {"activity", "noise", "speed"}:
        changes = {"activity": {"volatility_state": "INACTIVE"},
                   "noise": {"noise_context": "UNSTABLE"},
                   "speed": {"directional_effective_speed": 0.0}}[gate]
        market = replace(baseline.market, context=replace(baseline.market.context, **changes))
        monkeypatch.setattr(strategy, "evaluate_market", lambda *a, **k: market)
    elif gate == "space":
        corridor = replace(baseline.corridor, structure=replace(baseline.corridor.structure,
            available_distance=baseline.market.context.buffer_distance / 2,
            feasibility_state="CONSTRAINED"))
        monkeypatch.setattr(strategy, "evaluate_corridor", lambda *a, **k: corridor)
    else:
        monkeypatch.setattr(strategy, "evaluate_time", lambda *a, **k: replace(baseline.time,
            temporally_feasible=False, context=replace(baseline.time.context, time_state="LATE")))
    for stage in ("PRE", "CONFIRM", "OPEN_NOW"):
        evaluated = strategy.decide(m1, m5, params, buffer_mode="SMALL", context={"physical_stage": stage})
        assert evaluated.decision.kind == "REJECT"
        assert evaluated.decision.reject.hard_blockers
        assert not evaluated.execution_time.available


def test_owner_receipt_time_controls_minimum_lead(physical):
    _, m1, m5, params = physical
    from state_store.state_store import default_fsm_state
    from core.strategy_v3 import lifecycle_context
    _, a = _advance_cycle(m1, m5, params, default_fsm_state(), 1000)
    _, b = _advance_cycle(m1, m5, params, a.next_state, 1002)
    assert lifecycle_context(b.next_state, "EUR/USD", now_ts=1030, owner_pre_ts=1000.7)["physical_stage"] == "CONFIRM"
    assert lifecycle_context(b.next_state, "EUR/USD", now_ts=1031, owner_pre_ts=1000.7)["physical_stage"] == "OPEN_NOW"
    assert lifecycle_context(b.next_state, "EUR/USD", now_ts=1040, owner_pre_ts=1000.7,
                             require_owner_receipts=True)["physical_stage"] == "CONFIRM"
    assert lifecycle_context(b.next_state, "EUR/USD", now_ts=1040,
                             require_owner_receipts=True)["physical_stage"] == "PRE"


def test_scoreless_migration_is_backed_up_idempotent_and_exact(physical):
    root, _, _, expected = physical
    from core.physical_params import load_physical_runtime_algo_params
    path = root / "config/algo_params.json"
    before = path.read_bytes()
    assert load_physical_runtime_algo_params(str(path)) == expected
    assert load_physical_runtime_algo_params(str(path)) == expected
    backups = list((path.parent / "policy_migrations").glob("*.json"))
    assert len(backups) == 1 and backups[0].read_bytes() == before
    assert json.loads(path.read_text()) == expected
    assert "score_thresholds" not in expected and "strategy_v2" not in expected
    assert "rsi_call" not in expected["market_model"]
    from core import telegram_admin_ui, admin_commands
    menu = json.dumps(telegram_admin_ui.strategy_markup())
    assert "THRESHOLDS" not in menu and "Thresholds" not in menu
    before_mutation = path.read_bytes()
    assert "eliminate" in admin_commands._set_threshold("OPEN", 99)
    assert path.read_bytes() == before_mutation


@pytest.mark.parametrize("field", ["score_thresholds", "TPS", "weights", "strategy_v2"])
def test_physical_bundle_rejects_hidden_scoring_controls(physical, field):
    _, _, _, params = physical
    from core.params_loader import ParamsValidationError, validate_algo_params
    params[field] = {}
    with pytest.raises(ParamsValidationError):
        validate_algo_params(params)


def test_old_calibration_artifact_cannot_be_reused_for_scoreless_v3(physical):
    root, _, _, params = physical
    from tests.canonical.unit.test_runtime_execution_calibration import _artifact, _write, _load
    path = root / "config/execution_calibration.json"
    artifact = _artifact(params)
    _write(path, artifact)
    assert _load(path, params).status == "SCOPE_MISMATCH"
    artifact["strategy_version"] = "3.0.0"
    _write(path, artifact)
    assert _load(path, params).status == "AVAILABLE"


def test_scored_research_never_admits_physical_observations(physical, monkeypatch):
    _, m1, m5, params = physical
    from core import signal_engine, strategy_v3
    from intelligence import live_score_severity_research, lifecycle_cadence_research
    def forbidden(*a, **k):
        pytest.fail("retired scoring study admitted a physical V3 observation")
    monkeypatch.setattr(live_score_severity_research, "observe", forbidden)
    monkeypatch.setattr(lifecycle_cadence_research, "observe", forbidden)
    result = strategy_v3.decide(m1, m5, params, buffer_mode="SMALL")
    signal_engine._observe_score_severity(result, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")


def test_signal_render_debug_and_logs_have_no_scores(physical):
    _, m1, m5, params = physical
    from core.strategy_v3 import decide
    from core.signal_event import build_signal_event
    from core import signal_engine, distribution_router_v3, admin_views
    result = decide(m1, m5, params, buffer_mode="SMALL")
    event = build_signal_event(result.decision, buffer_mode="SMALL", created_ts=1000,
                               execution_time=result.execution_time).to_dict()
    assert "score_total" not in event and "score_tier" not in event["payload"]
    text = distribution_router_v3._render_signal_text(event, "")
    assert "Score" not in text and "TPS" not in text
    data = {"decision_kind": "PRE", "strategic_kind": "PRE", "strategy": "BINARY_STRATEGY_V3",
        "strategy_version": "3.0.0", "canonical_spec": result.canonical_spec,
        "score_total": None, "score_tier": "PHYSICAL_READY", "direction": "BUY", "candle_ts": 1000,
        "decision_object": result.decision.to_dict(), "trade_physics": event["payload"]["trade_physics"]}
    logged = signal_engine._build_v3_event("decision_evaluated", data, correlation={})
    assert "score_total" not in logged["data"] and "score_tier" not in logged["data"]
    rendered = admin_views.render_debug_last(logged)
    assert "SCORE:" not in rendered and "TPS:" not in rendered
    assert "threshold" not in admin_views.render_strategy_status(params)


def test_governed_physical_open_reaches_candidate_and_telemetry_without_a_score(physical):
    _, m1, m5, params = physical
    from core.strategy_v3 import decide, lifecycle_context
    from core.execution_model import ExecutionCalibration
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from core.signal_execution_gate import prepare_signal_execution
    from core.trade_temporal_telemetry import _build_trade_record
    from state_store.state_store import default_fsm_state
    _, pre = _advance_cycle(m1, m5, params, default_fsm_state(), 1000)
    _, confirm = _advance_cycle(m1, m5, params, pre.next_state, 1002)
    result = decide(m1, m5, params, buffer_mode="SMALL",
        context=lifecycle_context(confirm.next_state, "EUR/USD", now_ts=1031),
        execution_calibration=ExecutionCalibration(1.0, 0.0, 2.0, 15.0, "SYNTHETIC-TEST-ONLY"))
    opened = advance_persistent_fsm(confirm.next_state, result.decision, now_ts=1031)
    execution = prepare_signal_execution(opened, result.decision, buffer_mode="SMALL", created_ts=1031,
                                         execution_time=result.execution_time)
    assert execution.distribution_allowed
    event = execution.candidate.to_dict()
    assert "score_total" not in event
    record = _build_trade_record(event, now_ts=1031, market_provider="FINNHUB", publication_evidence={
        "route_result_event_id": "TEST-ONLY-ROUTE", "visibility_event_id": "TEST-ONLY-VISIBILITY",
        "route": "OWNER_PRIVATE", "destination_id": 123456789, "message_id": 1})
    assert record["strategy_version"] == "3.0.0"
    assert record["score_total"] is None and record["TPS"] is None


@pytest.fixture
def physical_calibration(physical, monkeypatch):
    root, _, _, params = physical
    for key, value in {"OWNER_SIGNAL_DELIVERY_ENABLED":"true", "OWNER_TELEGRAM_ID":"123456789",
                       "SHADOW_MODE":"true", "ENABLE_BROKER_EXECUTION":"false",
                       "SHADOW_MODEL_TIME_RESEARCH_ENABLED":"true"}.items():
        monkeypatch.setenv(key, value)
    module = importlib.import_module("intelligence.physical_expiry_calibration")
    return root, module, params


def _capture(module, params, stamp=1000):
    item = _entry(stamp)
    item.pop("level")
    item["policy"] = "PHYSICAL_ONLY_V3"
    item["opportunity_signal_id"] = "sig-v3-synthetic-" + str(stamp)
    module.capture([item], params=params, buffer_mode="MEDIUM", strategy_version="3.0.0",
                   canonical_spec="SYNTHETIC_TEST", now_ts=stamp)


def test_physical_calibration_preserves_old_cohort_and_has_no_severity_levels(physical_calibration):
    root, module, params = physical_calibration
    legacy = root / "analytics/execution_expiry_calibration/state.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b'{"preserve":"historical scored cohort"}')
    _capture(module, params)
    state = module._read(module._path())
    assert legacy.read_bytes() == b'{"preserve":"historical scored cohort"}'
    assert set(state["policy_scopes"]) == {"PHYSICAL_ONLY_V3"}
    record = next(iter(state["records"].values()))
    assert set(record["policies"]) == {"PHYSICAL_ONLY_V3"}
    assert "levels" not in record and "score_thresholds" not in json.dumps(state)
    report = module.summary(now_ts=1000)
    assert not report["execution_calibration_proven"]
    assert report["policies"][0]["status"] == "COLLECTING_TRAINING"


def test_calibration_crash_retry_cannot_duplicate_an_opportunity(physical_calibration):
    _, module, params = physical_calibration
    _capture(module, params)
    item = _entry(1060)
    item.pop("level")
    item.update(policy="PHYSICAL_ONLY_V3", opportunity_signal_id="sig-v3-synthetic-1000")
    module.capture([item], params=params, buffer_mode="MEDIUM", strategy_version="3.0.0",
                   canonical_spec="SYNTHETIC_TEST", now_ts=1060)
    assert len(module._read(module._path())["records"]) == 1


def test_provider_eurusd_identity_admits_exactly_one_physical_chain(physical_calibration, physical):
    _, module, params = physical_calibration
    _, m1, m5, _ = physical
    from core.strategy_v3 import decide, lifecycle_context
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    for candle in m1 + m5:
        candle["symbol"] = "EURUSD"  # actual runtime identity from Finnhub normalization
    state = default_fsm_state()
    for stamp in (1000, 1002, 1031):
        result = decide(m1, m5, params, buffer_mode="SMALL",
                        context=lifecycle_context(state, "EURUSD", now_ts=stamp))
        handoff = advance_persistent_fsm(state, result.decision, now_ts=stamp)
        state = handoff.next_state
    assert handoff.accepted_stage == "OPEN_NOW"
    assert module.observe_accepted_chain(result.decision, handoff, params, now_ts=1031,
        provider="FINNHUB", buffer_mode="SMALL") is True
    module.observe_accepted_chain(result.decision, handoff, params, now_ts=1032,
        provider="FINNHUB", buffer_mode="SMALL")
    captured = module._read(module._path())
    assert captured["scope"]["symbol"] == "EUR/USD"
    assert len(captured["records"]) == 1


def test_physical_calibration_real_quote_contract_buffer_and_missingness(physical_calibration):
    _, module, params = physical_calibration
    _capture(module, params)
    module.advance(now_ts=1001, active_provider="FINNHUB", price_loader=lambda _: _sample(1001, 1.1))
    for horizon in (90, 96, 102, 108, 114, 120):
        module.advance(now_ts=1001+horizon, active_provider="FINNHUB",
                       price_loader=lambda _, t=1001+horizon: _sample(t, 1.1003))
    report = module.summary(now_ts=1200)
    assert report["finalized_entry_experiments"] == 1
    assert all(row["buffer_met"] == 1 for row in report["paired_expiry_observations"])
    _capture(module, params, 2000)
    module.advance(now_ts=2011, active_provider="FINNHUB", price_loader=lambda _: None)
    report = module.summary(now_ts=2012)
    assert all(row["unknown"] == 1 and row["losses"] == 0 for row in report["paired_expiry_observations"])
    assert report["ready_policies"] == []


def test_physical_calibration_rejects_rewriting_frozen_buffer(physical_calibration):
    _, module, params = physical_calibration
    _capture(module, params)
    state = module._read(module._path())
    row = next(iter(state["records"].values()))
    row["buffer_snapshot"]["buffer_distance"] = 2
    with pytest.raises(ValueError):
        module.validate(state)


@pytest.mark.parametrize(
    ("direction", "barrier", "expected"),
    [
        ("BUY", 1.1002999999999, "CONSTRAINED"),
        ("BUY", 1.1003, "VALID"),
        ("BUY", 1.1003000000001, "VALID"),
        ("SELL", 1.0997000000001, "CONSTRAINED"),
        ("SELL", 1.0997, "VALID"),
        ("SELL", 1.0996999999999, "VALID"),
    ],
)
def test_v3_directional_room_uses_one_exact_verdict(physical, monkeypatch, direction, barrier, expected):
    from dataclasses import replace
    from core import strategy_v3

    _, m1, m5, params = physical
    baseline = strategy_v3.decide(m1, m5, params, buffer_mode="SMALL")
    price = 1.1
    market = replace(
        baseline.market,
        direction_bias=direction,
        context=replace(baseline.market.context, latest_price=price, buffer_distance=0.0003),
    )
    monkeypatch.setattr(strategy_v3, "evaluate_market", lambda *args, **kwargs: market)
    support = barrier if direction == "SELL" else 1.099
    resistance = barrier if direction == "BUY" else 1.101
    for candle in m5:
        candle.update(open=price, close=price, high=resistance, low=support, complete=True)

    result = strategy_v3.decide(m1, m5, params, buffer_mode="SMALL")
    assert result.corridor.structure.feasibility_state == expected
    constrained = expected == "CONSTRAINED"
    assert result.trade_physics.physically_constrained == constrained
    assert result.decision.fsm_inputs["physically_constrained"] == constrained
    assert result.decision.kind == ("REJECT" if constrained else "PRE")
