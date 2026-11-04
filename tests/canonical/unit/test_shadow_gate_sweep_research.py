from __future__ import annotations

import copy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest


@pytest.fixture
def sweep(canonical_runtime_root, fresh_imports, monkeypatch):
    monkeypatch.setenv("SHADOW_GATE_SWEEP_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    return fresh_imports("intelligence.shadow_gate_sweep_research")


def _row(created, *, tps=80.0, outcome="WIN", bundle="a" * 64, identity=None):
    """Offline aggregate-algorithm fixture, not a live-market observation."""
    return {
        "record_id": identity or sha256(str(created).encode()).hexdigest(),
        "protocol": "SHADOW_MODEL_TIME_RESEARCH_V1", "parameter_bundle_sha256": bundle,
        "strategy_version": "2.0.0", "strategy_spec": "ALGO_SPEC_v3.0.0",
        "created_ts": float(created), "horizon_seconds": 120.0,
        "state": "FINAL" if outcome is not None else "WAITING_ENTRY",
        "outcome": outcome, "finalized_ts": created + 121 if outcome else None,
        "decision_snapshot": {"schema_version": "2.0.0", "score": {"trade_physics": {
            "TPS": tps, "formula_version": "TRADE_PHYSICS_MODEL_SPEC_v1.0.0",
            "feature_schema_version": "1.0.0"}}},
    }


def _source(sweep, monkeypatch, rows):
    monkeypatch.setattr(sweep.source, "snapshot_records", lambda: copy.deepcopy(rows))


def _hundred(*, outcome="WIN", start=2000):
    return [_row(start + index * 3600, outcome=outcome) for index in range(100)]


@pytest.mark.parametrize("level", [-1, 21, True, 1.0, "1", None])
def test_levels_have_strict_integer_bounds(sweep, level):
    with pytest.raises(ValueError):
        sweep.threshold(level)


@pytest.mark.parametrize("name,value", [
    ("SHADOW_GATE_SWEEP_RESEARCH_ENABLED", "false"),
    ("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "false"),
    ("SHADOW_MODE", "false"), ("ENABLE_BROKER_EXECUTION", "true"),
])
def test_disabled_scope_has_no_side_effects(sweep, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    assert sweep.update(now_ts=1000) == {"status": "DISABLED"}
    assert not sweep._path("experiment.json").exists()


def test_empty_prospective_start_is_not_success_or_a_guarantee(sweep):
    result = sweep.update(now_ts=1000)
    assert result["status"] == "WAITING_FOR_OPPORTUNITIES"
    assert result["active_level"] == 0
    assert [row["minimum_tps"] for row in result["levels"]] == list(range(0, 101, 5))
    assert result["active_metrics"]["decisive_sample"] == 0
    assert result["active_metrics"]["hypothetical_win_rate_percent"] is None
    assert result["active_metrics"]["wilson_95_iid_reference_percent"] is None
    assert all(result[flag] is False for flag in sweep._FALSE_FLAGS)
    assert sweep.read_summary_status()["is_heartbeat"] is False


def test_paired_cutoffs_count_draw_unknown_pending_separately_and_can_get_worse(sweep, monkeypatch):
    sweep.update(now_ts=1000)
    rows = [_row(2000, tps=80), _row(3000, tps=100, outcome="LOSS"),
            _row(4000, outcome="DRAW"), _row(5000, outcome="UNKNOWN"),
            _row(6000, outcome=None)]
    _source(sweep, monkeypatch, rows)
    result = sweep.update(now_ts=6100)
    broad = result["levels"][0]["all"]
    assert broad["outcomes"] == {"WIN": 1, "LOSS": 1, "DRAW": 1, "UNKNOWN": 1}
    assert broad["decisive_sample"] == 2 and broad["pending"] == 1
    assert broad["hypothetical_win_rate_percent"] == 50
    assert broad["unknown_fraction"] == 0.25
    strict = result["levels"][20]["all"]
    assert strict["outcomes"]["LOSS"] == 1 and strict["hypothetical_win_rate_percent"] == 0
    assert result["levels"][16]["all"] == broad
    assert result["levels"][17]["all"] == strict
    assert result["active_level"] == 0


def test_nonoverlap_selection_is_fixed_before_outcomes_and_cutoffs(sweep, monkeypatch):
    sweep.update(now_ts=1000)
    rows = [_row(2000, tps=50, outcome="UNKNOWN"),
            _row(2001, tps=100, outcome="WIN"),
            _row(2132, tps=100, outcome="WIN"),  # touches reserved endpoint
            _row(2133, tps=100, outcome="LOSS")]
    _source(sweep, monkeypatch, rows)
    result = sweep.update(now_ts=3000)
    common = result["levels"][20]["common_nonoverlapping"]
    assert common["outcomes"] == {"WIN": 0, "LOSS": 1, "DRAW": 0, "UNKNOWN": 0}
    assert result["active_metrics"]["outcomes"]["UNKNOWN"] == 1
    assert result["active_metrics"]["outcomes"]["LOSS"] == 1
    rows[0]["outcome"] = "WIN"
    assert [r["record_id"] for r in sweep._nonoverlapping(rows)] == [rows[0]["record_id"], rows[3]["record_id"]]


def test_old_registration_is_not_imported_even_when_outcome_finishes_after_start(sweep, monkeypatch):
    sweep.update(now_ts=2000)
    _source(sweep, monkeypatch, [_row(1999), _row(2001)])
    result = sweep.update(now_ts=3000)
    assert result["excluded"]["before_activation"] == 1
    assert result["levels"][0]["all"]["decisive_sample"] == 1


@pytest.mark.parametrize("tps,bundle", [(None, "a" * 64), (True, "a" * 64),
    (100.01, "a" * 64), (float("nan"), "a" * 64), (80, None)])
def test_missing_invalid_features_are_visible_exclusions_never_zero_imputation(sweep, monkeypatch, tps, bundle):
    sweep.update(now_ts=1000)
    _source(sweep, monkeypatch, [_row(2000, tps=tps, bundle=bundle)])
    result = sweep.update(now_ts=3000)
    assert result["excluded"]["missing_provenance_or_tps"] == 1
    assert result["active_metrics"]["decisive_sample"] == 0
    assert result["active_level"] == 0


@pytest.mark.parametrize("outcome", ["WIN", "LOSS"])
def test_progression_uses_quantity_quality_not_an_attractive_rate_and_survives_restart(sweep, monkeypatch, outcome):
    sweep.update(now_ts=1000)
    rows = _hundred(outcome=outcome)
    _source(sweep, monkeypatch, rows)
    now = rows[-1]["finalized_ts"] + 30
    result = sweep.update(now_ts=now)
    assert result["active_level"] == 1
    assert len(result["completed_levels"]) == 1
    assert result["completed_levels"][0]["metrics"]["outcomes"][outcome] == 100
    assert result["active_metrics"]["decisive_sample"] == 0
    original_ledger = json.loads(sweep._path("experiment.json").read_text())
    again = sweep.update(now_ts=now + 10)
    assert again["active_level"] == 1  # old cohort cannot advance the next level
    assert again["completed_levels"] == result["completed_levels"]
    assert json.loads(sweep._path("experiment.json").read_text()) == original_ledger
    assert sweep.read_summary_status()["summary"] == again


@pytest.mark.parametrize("case", ["small", "one_date", "unknown", "pending"])
def test_inadequate_or_incomplete_evidence_cannot_advance(sweep, monkeypatch, case):
    sweep.update(now_ts=1000)
    rows = _hundred()
    if case == "small":
        rows.pop()
    elif case == "one_date":
        rows = [_row(2000 + index * 200) for index in range(100)]
    elif case == "unknown":
        rows += [_row(500000 + index * 200, outcome="UNKNOWN") for index in range(6)]
    else:
        rows.append(_row(500000, outcome=None))
    _source(sweep, monkeypatch, rows)
    assert sweep.update(now_ts=600000)["active_level"] == 0


def test_next_level_uses_only_later_opportunities_and_keeps_discovery_control(sweep, monkeypatch):
    sweep.update(now_ts=1000)
    rows = _hundred()
    _source(sweep, monkeypatch, rows)
    boundary = rows[-1]["finalized_ts"] + 30
    sweep.update(now_ts=boundary)
    rows.append(_row(boundary + 1, tps=5, outcome="LOSS"))
    rows.append(_row(boundary + 200, tps=4.999, outcome="WIN"))
    result = sweep.update(now_ts=boundary + 400)
    assert result["active_metrics"]["outcomes"]["LOSS"] == 1
    assert result["active_metrics"]["decisive_sample"] == 1
    assert result["levels"][0]["all"]["decisive_sample"] == 102
    assert result["levels"][1]["all"]["decisive_sample"] == 101


@pytest.mark.parametrize("field", ["bundle", "formula", "schema"])
def test_parameter_or_model_drift_pauses_instead_of_mixing_evidence(sweep, monkeypatch, field):
    sweep.update(now_ts=1000)
    rows = _hundred()
    drift = _row(500000)
    if field == "bundle":
        drift["parameter_bundle_sha256"] = "b" * 64
    else:
        key = "formula_version" if field == "formula" else "feature_schema_version"
        drift["decision_snapshot"]["score"]["trade_physics"][key] = "different"
    rows.append(drift)
    _source(sweep, monkeypatch, rows)
    result = sweep.update(now_ts=600000)
    assert result["status"] == "PAUSED_BASELINE_CHANGED"
    assert result["excluded"]["baseline_changed"] == 1
    assert result["active_level"] == 0


@pytest.mark.parametrize("raw", ["{", "[]", '{"active_level":20}', "x" * (128 * 1024 + 1)])
def test_corrupt_ledger_cannot_reset_or_activate_a_level(sweep, raw):
    sweep.update(now_ts=1000)
    path = sweep._path("experiment.json")
    path.write_text(raw)
    with pytest.raises((ValueError, TypeError)):
        sweep.update(now_ts=2000)
    assert path.read_text() == raw


@pytest.mark.parametrize("private_field", ["price", "signal_id", "decision_snapshot"])
def test_private_or_inconsistent_cache_never_reaches_runtime_audit(sweep, private_field):
    sweep.update(now_ts=1000)
    path = sweep._path("summary.json")
    payload = json.loads(path.read_text())
    payload["summary"]["levels"][0]["all"][private_field] = "private"
    path.write_text(json.dumps(payload))
    assert sweep.read_summary_status() is None


def test_cache_does_not_assert_heartbeat_or_current_activation(sweep, monkeypatch):
    from runtime import runtime_status
    sweep.update(now_ts=1000)
    runtime_status.write_status("running", "unrelated overwrite")
    monkeypatch.setenv("SHADOW_GATE_SWEEP_RESEARCH_ENABLED", "false")
    status = runtime_status.read_status()
    assert status["shadow_gate_sweep_research"]["active_level"] == 0
    observation = status["shadow_gate_sweep_research_observation"]
    assert observation["observed_at"] == 1000
    assert observation["is_heartbeat"] is False and observation["currently_enabled"] is False


def test_winning_streak_never_produces_a_certain_win_interval(sweep):
    lower, upper = sweep._wilson(100, 100)
    assert 96 < lower < 97 and upper == pytest.approx(100)
    assert lower < 100


def test_worker_failure_is_isolated_retried_and_does_not_print_private_details(sweep, monkeypatch, capsys):
    from runtime import telemetry_market_worker as worker
    monkeypatch.setattr(worker, "run_telemetry_cycle", lambda **kwargs: {})
    monkeypatch.setattr(worker.trade_temporal_telemetry, "recover_after_restart", lambda _now: {})
    monkeypatch.setattr(worker.market_client, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(worker.observability_logger, "log_warning", lambda **kwargs: None)
    original, calls, sleeps = sweep.update, [], []
    def transient(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise OSError("private quote or identity")
        return original(**kwargs)
    def stop_after_retry(_seconds):
        sleeps.append(1)
        if len(sleeps) == 2:
            raise SystemExit
    monkeypatch.setattr(sweep, "update", transient)
    with pytest.raises(SystemExit):
        worker.telemetry_market_loop(clock=lambda: 1000, sleep=stop_after_retry)
    assert len(calls) == 2
    assert sweep.read_summary_status()["summary"]["active_level"] == 0
    output = capsys.readouterr().out
    assert "private quote" not in output
    assert output.count("TSP_GATE_SWEEP_RESEARCH_EVIDENCE") == 1
    assert not Path(sweep.storage.root_path("observability", "open_trades_registry.json")).exists()


def test_real_collector_preserves_parameter_provenance_before_outcome(sweep):
    from core.decision_object import (DecisionObject, SetupContext, MarketContext, StructureContext,
        TimeContext, ScoreContext, TradePhysicsContext, StrategicFlags, RejectContext)
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    sweep.update(now_ts=900)
    decision = DecisionObject(
        kind="PRE", signal_id="private-opportunity",
        setup=SetupContext("EUR/USD", "BUY", 1000, "M1", "cycle", "fixture"),
        market_context=MarketContext(1.1, 0.001, 0.002, "WITH_TREND", "ACTIVE", "STABLE"),
        structure=StructureContext(1.09, 1.12, 1.09, 1.12, 0.03, 0.02, "INTERIOR", "VALID"),
        time=TimeContext(2, 2, 2, 0.4, None, "READY", 2.5),
        score=ScoreContext(88, 0.88, {"trend": 24}, tier="SCORE_PRE_BAND",
            trade_physics=TradePhysicsContext("READY", TPS=80)),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False, trade_physics_ready=True),
        reject=RejectContext(), fsm_inputs={}, explanations=("Offline fixture.",))
    pre = advance_persistent_fsm(default_fsm_state(), decision, now_ts=1001)
    opening = replace(decision, kind="OPEN_NOW", setup=replace(decision.setup, evaluated_ts=1060),
        score=replace(decision.score, tier="SCORE_OPEN_BAND"))
    handoff = advance_persistent_fsm(pre.next_state, opening, now_ts=1061)
    result = sweep.source.register_accepted_open(opening, handoff, provider="FINNHUB", now_ts=1062,
                                                parameter_bundle_sha256="a" * 64)
    assert result["registered"] is True
    sample = lambda ts, price: {"provider": "FINNHUB", "symbol": "EUR/USD", "price": price,
        "observed_ts": ts, "source": "LIVE_STREAM_CURRENT_M1_CLOSE"}
    sweep.source.run_cycle(active_provider="FINNHUB", now_ts=1063, price_loader=lambda _: sample(1063, 1.1))
    sweep.source.run_cycle(active_provider="FINNHUB", now_ts=1183, price_loader=lambda _: sample(1183, 1.2))
    before = sweep.source.snapshot_records()
    report = sweep.update(now_ts=1184)
    assert report["levels"][16]["all"]["outcomes"]["WIN"] == 1
    assert report["levels"][17]["all"]["decisive_sample"] == 0
    assert sweep.source.snapshot_records() == before
    assert before[0]["parameter_bundle_sha256"] == "a" * 64
    assert before[0]["decision_snapshot"] == opening.to_dict()
    assert "private-opportunity" not in json.dumps(report) and '"price"' not in json.dumps(report)


def test_signal_engine_hashes_the_exact_validated_parameter_bundle(sweep, monkeypatch):
    from core import signal_engine
    from types import SimpleNamespace
    monkeypatch.setattr("runtime.market_client.configured_provider", lambda: "FINNHUB")
    captured = []
    monkeypatch.setattr(signal_engine.shadow_research, "register_accepted_open",
                        lambda *args, **kwargs: captured.append(kwargs))
    params = {"score_thresholds": {"OPEN": 85, "PRE": 65, "CONFIRM": 75}}
    signal_engine._observe_shadow_research(SimpleNamespace(kind="OPEN_NOW"), None, params=params)
    expected = sha256(json.dumps(params, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    assert captured[0]["parameter_bundle_sha256"] == expected


def test_all_twenty_one_levels_end_in_review_without_selecting_a_production_gate(sweep, monkeypatch):
    sweep.update(now_ts=1000)
    rows, next_start = [], 2000
    _source(sweep, monkeypatch, rows)
    for level in range(21):
        cohort = _hundred(start=next_start)
        for row in cohort:
            row["decision_snapshot"]["score"]["trade_physics"]["TPS"] = 100
        rows.extend(cohort)
        now = cohort[-1]["finalized_ts"] + 30
        report = sweep.update(now_ts=now)
        assert len(report["completed_levels"]) == level + 1
        next_start = now + 1000
    assert report["active_level"] is None and report["active_minimum_tps"] is None
    assert report["status"] == "REVIEW_REQUIRED"
    assert all(report[flag] is False for flag in sweep._FALSE_FLAGS)
    assert sweep.read_summary_status()["summary"] == report
    marker = sweep.evidence_summary(report)
    assert marker["completed_level_count"] == 21
    assert len(json.dumps(marker)) < 12 * 1024


def test_collection_budget_is_frozen_in_the_ledger(sweep):
    sweep.update(now_ts=1000)
    path = sweep._path("experiment.json")
    state = json.loads(path.read_text())
    state["collection_targets"]["decisive_nonoverlapping"] = 1
    path.write_text(json.dumps(state))
    with pytest.raises(ValueError, match="refusing to restart"):
        sweep.update(now_ts=2000)
