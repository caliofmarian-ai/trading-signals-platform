from __future__ import annotations

import copy
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest


@pytest.fixture
def box(canonical_runtime_root, fresh_imports, monkeypatch):
    for key in ("SHADOW_GATE_TIMEBOX_RESEARCH_ENABLED", "SHADOW_GATE_SWEEP_RESEARCH_ENABLED",
                "SHADOW_MODEL_TIME_RESEARCH_ENABLED", "SHADOW_MODE"):
        monkeypatch.setenv(key, "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    module = fresh_imports("intelligence.shadow_gate_timebox_research")
    monkeypatch.setattr(module, "REQUEST_STARTED_AT", 1000.0)
    monkeypatch.setattr(module, "DEADLINE", 8200.0)
    return module


def _row(created, *, tps=80, outcome="WIN", reason=None, bundle="a" * 64, finalized=None):
    # Offline algorithm fixture; never reported as an actual live observation.
    return {"record_id": sha256(str(created).encode()).hexdigest(),
            "protocol": "SHADOW_MODEL_TIME_RESEARCH_V1", "parameter_bundle_sha256": bundle,
            "strategy_version": "2.0.0", "strategy_spec": "ALGO_SPEC_v3.0.0",
            "created_ts": float(created), "horizon_seconds": 120.0,
            "state": "FINAL" if outcome is not None else "WAITING_ENTRY",
            "outcome": outcome, "outcome_reason": reason,
            "finalized_ts": finalized if finalized is not None else created + 121 if outcome else None,
            "entry_sample": {"observed_ts": created + 1},
            "decision_snapshot": {"schema_version": "2.0.0", "score": {"trade_physics": {
                "TPS": tps, "formula_version": "TRADE_PHYSICS_MODEL_SPEC_v1.0.0",
                "feature_schema_version": "1.0.0"}}}}


def _feed(now):
    return lambda _: {"provider": "FINNHUB", "symbol": "EUR/USD", "price": 1.1,
                      "observed_ts": now, "source": "LIVE_STREAM_CURRENT_M1_CLOSE"}


def _update(box, now, rows, monkeypatch):
    monkeypatch.setattr(box.source, "snapshot_records", lambda: copy.deepcopy(rows))
    return box.update(now_ts=now, price_loader=_feed(now))


@pytest.mark.parametrize("flag,value", [
    ("SHADOW_GATE_TIMEBOX_RESEARCH_ENABLED", "false"), ("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "false"),
    ("SHADOW_MODE", "false"), ("ENABLE_BROKER_EXECUTION", "true")])
def test_disabled_test_cannot_write_or_replace_legacy_ledger(box, monkeypatch, flag, value):
    monkeypatch.setenv(flag, value)
    assert box.update(now_ts=1100, price_loader=_feed(1100)) == {"status": "DISABLED"}
    assert not box._path("experiment.json").exists()


def test_expired_or_future_window_does_not_start_a_replacement_two_hours(box):
    assert box.update(now_ts=999, price_loader=_feed(999))["status"] == "BEFORE_REQUEST_WINDOW"
    assert box.update(now_ts=8200, price_loader=_feed(8200))["status"] == "EXPIRED_BEFORE_ACTIVATION"
    assert not box._path("experiment.json").exists()


def test_no_sample_reports_empty_not_clean_success_and_restart_keeps_deadline(box, monkeypatch):
    report = _update(box, 1100, [], monkeypatch)
    assert report["assessment"] == "NO_ELIGIBLE_OBSERVATIONS"
    assert report["evidence_complete"] is False
    assert report["deadline"] == 8200 and report["started_at"] == 1100
    assert report["metrics"]["hypothetical_win_rate_percent"] is None
    assert all(report[flag] is False for flag in box.FALSE_FLAGS)
    again = _update(box, 1900, [], monkeypatch)
    assert again["deadline"] == 8200 and again["started_at"] == 1100
    assert report["levels"][0]["minimum_tps"] == 0
    assert report["levels"][20]["minimum_tps"] == 100
    assert box.sweep.enabled() is False  # Old three-day ledger is not advanced.
    assert not box.sweep._path("experiment.json").exists()


def test_every_missing_cause_is_visible_and_excluded_from_rate(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    rows = [_row(2000), _row(2200, tps=100, outcome="LOSS"), _row(2400, outcome="DRAW")]
    rows += [_row(2600 + index * 200, outcome="UNKNOWN", reason=reason)
             for index, reason in enumerate(sorted(box.GAP_REASONS))]
    rows += [_row(4000, outcome=None)]
    report = _update(box, 7000, rows, monkeypatch)
    metrics = report["metrics"]
    assert metrics["outcomes"] == {"WIN": 1, "LOSS": 1, "DRAW": 1, "UNKNOWN": 4}
    assert metrics["decisive_sample"] == 2 and metrics["pending"] == 1
    assert metrics["hypothetical_win_rate_percent"] == 50
    assert metrics["missing_observation_causes"] == {reason: 1 for reason in box.GAP_REASONS}
    assert metrics["pending_states"] == {"WAITING_ENTRY": 1}
    assert len(metrics["gap_details"]) == 4 and not metrics["gap_details_truncated"]
    assert report["evidence_complete"] is False and report["assessment"] == "INCOMPLETE_EVIDENCE"
    assert report["levels"][20]["paired"]["hypothetical_win_rate_percent"] == 0
    assert "price" not in json.dumps(report) and "record_id" not in json.dumps(report)


def test_unexplained_missing_result_is_a_visible_error_not_an_invented_zero(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    with pytest.raises(ValueError, match="missing-observation cause"):
        _update(box, 3000, [_row(2000, outcome="UNKNOWN")], monkeypatch)
    assert box.read_summary_status()["evidence_cutoff_at"] == 1100


def test_deadline_censors_later_outcome_and_frozen_result_cannot_be_backfilled(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    rows = [_row(2000), _row(8100, outcome="WIN", finalized=8300)]
    report = _update(box, 8400, rows, monkeypatch)
    assert report["status"] == "TIMEBOX_COMPLETE" and report["evidence_cutoff_at"] == 8200
    assert report["metrics"]["outcomes"]["WIN"] == 1
    assert report["metrics"]["pending_states"] == {"WAITING_EXPIRY": 1}
    assert report["elapsed_slot_count"] == 21 and report["active_level"] is None
    before = box._path("final.json").read_bytes()
    monkeypatch.setattr(box.source, "snapshot_records", lambda: pytest.fail("frozen report reread source"))
    assert box.update(now_ts=9000, price_loader=_feed(9000)) == report
    assert box._path("final.json").read_bytes() == before


def test_final_at_exact_deadline_counts_but_registration_at_deadline_does_not(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    report = _update(box, 8300, [_row(2000, finalized=8200), _row(8200, finalized=8250)], monkeypatch)
    assert report["metrics"]["decisive_sample"] == 1
    assert report["excluded"]["after_deadline"] == 1


def test_old_registrations_not_backfilled_even_with_later_results(box, monkeypatch):
    _update(box, 2000, [], monkeypatch)
    report = _update(box, 4000, [_row(1999, finalized=2100), _row(2200)], monkeypatch)
    assert report["excluded"]["before_activation"] == 1
    assert report["metrics"]["decisive_sample"] == 1


def test_provenance_drift_pauses_interpretation_without_hiding_exclusion(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    report = _update(box, 4000, [_row(2000), _row(2200, bundle="b" * 64), _row(2400, bundle=None)], monkeypatch)
    assert report["assessment"] == "PAUSED_BASELINE_CHANGED"
    assert report["excluded"]["baseline_changed"] == 1
    assert report["excluded"]["missing_provenance_or_tps"] == 1
    assert report["metrics"]["decisive_sample"] == 1 and report["evidence_complete"] is False


def test_chronological_slots_elapse_by_time_without_becoming_validated_levels(box, monkeypatch):
    first = _update(box, 1100, [], monkeypatch)
    boundary = first["levels"][1]["slot_started_at"]
    rows = [_row(boundary - 1, tps=0, finalized=boundary + 130), _row(boundary, tps=5, finalized=boundary + 131)]
    report = _update(box, boundary + 200, rows, monkeypatch)
    assert report["active_level"] == 1 and report["elapsed_slot_count"] == 1
    assert report["levels"][0]["sequential"]["outcomes"]["WIN"] == 1
    # Common outcome-blind thinning prevents an overlapping window being counted as independent.
    assert report["levels"][1]["sequential"]["decisive_sample"] == 0
    assert "completed_level_count" not in report
    assert report["automatic_selection_allowed"] is False


@pytest.mark.parametrize("raw", ["{", "[]", '{"started_at": 1}', "x" * (128 * 1024 + 1)])
def test_corruption_cannot_reset_or_extend_the_experiment(box, monkeypatch, raw):
    _update(box, 1100, [], monkeypatch)
    box._path("experiment.json").write_text(raw)
    with pytest.raises((ValueError, TypeError)):
        _update(box, 2000, [], monkeypatch)
    assert box._path("experiment.json").read_text() == raw


@pytest.mark.parametrize("field", ["price", "decision_snapshot", "signal_id"])
def test_private_cache_fields_are_not_returned_in_audit(box, monkeypatch, field):
    _update(box, 1100, [], monkeypatch)
    report = json.loads(box._path("summary.json").read_text())
    report["levels"][0]["paired"][field] = "private"
    box._path("summary.json").write_text(json.dumps(report))
    assert box.read_summary_status() is None


def test_feed_evidence_is_fresh_only_for_valid_same_provider_actual_sample(box, monkeypatch):
    report = _update(box, 1100, [], monkeypatch)
    assert report["feed"] == {"status": "FRESH_REAL_SAMPLE", "sample_observed_at": 1100.0, "age_seconds": 0.0}
    bad = box.update(now_ts=1200, price_loader=lambda _: {"provider": "TWELVE_DATA", "price": 99})
    assert bad["feed"]["status"] == "SAMPLE_FAILED_FRESHNESS_OR_SOURCE_CHECK"
    assert bad["metrics"]["decisive_sample"] == 0
    changed = box.update(now_ts=1300, active_provider="TWELVE_DATA",
                         price_loader=lambda _: pytest.fail("must not initialize another provider"))
    assert changed["feed"]["status"] == "PROVIDER_CHANGED"


def test_diagnostics_explain_rejections_without_enrolling_them(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    decision = SimpleNamespace(kind="REJECT", reject=SimpleNamespace(hard_blockers=("TIME_NOT_FEASIBLE", "MARKET_ACTIVITY_NOT_ACTIVE")))
    handoff = SimpleNamespace(reason_family="NON_ACTIONABLE", accepted_stage=None, stage_handoff_ready=False)
    box.observe_evaluation(decision, handoff, SimpleNamespace(available=False), now_ts=1101)
    report = _update(box, 1200, [], monkeypatch)
    assert report["diagnostics"]["evaluations"] == 1
    assert report["diagnostics"]["first_evaluation_ts"] == 1101
    assert report["diagnostics"]["decision_kinds"] == {"REJECT": 1}
    assert report["diagnostics"]["blocker_counts"] == {"TIME_NOT_FEASIBLE": 1, "MARKET_ACTIVITY_NOT_ACTIVE": 1}
    assert report["metrics"]["decisive_sample"] == 0
    box.observe_evaluation(decision, handoff, SimpleNamespace(available=False), now_ts=8200)
    assert box._load_state()["diagnostics"]["evaluations"] == 1


@pytest.mark.parametrize("family", ["FOCUS", "COOLDOWN"])
def test_focus_and_cooldown_are_explicit_research_diagnostics(box, monkeypatch, family):
    _update(box, 1100, [], monkeypatch)
    decision = SimpleNamespace(kind="OPEN_NOW", reject=SimpleNamespace(hard_blockers=()))
    handoff = SimpleNamespace(reason_family=family, accepted_stage=None, stage_handoff_ready=False)
    box.observe_evaluation(decision, handoff, SimpleNamespace(available=False), now_ts=1101)
    report = _update(box, 1200, [], monkeypatch)
    assert report["diagnostics"]["fsm_reason_families"] == {family: 1}
    assert report["diagnostics"]["execution_expiry_unavailable"] == 1
    assert report["metrics"]["decisive_sample"] == 0


def test_physics_rejection_preserves_each_exact_missing_cause(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    codes = ("TRADE_PHYSICS_UNAVAILABLE_MISSING_TIME", "TRADE_PHYSICS_UNAVAILABLE_MISSING_SPEED")
    decision = SimpleNamespace(kind="REJECT", reject=SimpleNamespace(hard_blockers=codes))
    handoff = SimpleNamespace(reason_family="NON_ACTIONABLE", accepted_stage=None, stage_handoff_ready=False)
    box.observe_evaluation(decision, handoff, SimpleNamespace(available=False), now_ts=1101)
    assert _update(box, 1200, [], monkeypatch)["diagnostics"]["blocker_counts"] == dict.fromkeys(codes, 1)


def test_signal_diagnostics_failure_cannot_interrupt_execution(box, monkeypatch, capsys):
    from core import signal_engine
    monkeypatch.setattr(box, "observe_evaluation", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("private price")))
    signal_engine._observe_timebox_diagnostics(None, None, None, now_ts=1100)
    output = capsys.readouterr().out
    assert "TSP_GATE_TIMEBOX_DIAGNOSTICS_UNAVAILABLE" in output and "private price" not in output


def test_worker_closes_at_deadline_without_source_changes(box, monkeypatch, capsys):
    from runtime import telemetry_market_worker as worker
    monkeypatch.setattr(worker, "run_telemetry_cycle", lambda **kwargs: {})
    monkeypatch.setattr(worker.trade_temporal_telemetry, "recover_after_restart", lambda _now: {})
    monkeypatch.setattr(worker.market_client, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(box.source, "run_cycle", lambda **kwargs: {"changed": False})
    clock = [1100.0]
    monkeypatch.setattr(worker.market_client, "get_latest_price_sample", lambda _: _feed(clock[0])("EUR/USD"))
    def advance(_seconds):
        if clock[0] >= box.DEADLINE:
            raise SystemExit
        clock[0] = box.DEADLINE
    with pytest.raises(SystemExit):
        worker.telemetry_market_loop(clock=lambda: clock[0], sleep=advance)
    assert box.read_summary_status()["status"] == "TIMEBOX_COMPLETE"
    assert capsys.readouterr().out.count("TSP_GATE_TIMEBOX_RESEARCH_EVIDENCE") == 2


def test_worker_retries_storage_failure_and_isolates_private_error(box, monkeypatch, capsys):
    from runtime import telemetry_market_worker as worker
    monkeypatch.setattr(worker, "run_telemetry_cycle", lambda **kwargs: {})
    monkeypatch.setattr(worker.trade_temporal_telemetry, "recover_after_restart", lambda _now: {})
    monkeypatch.setattr(worker.market_client, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(box.source, "run_cycle", lambda **kwargs: {"changed": False})
    monkeypatch.setattr(worker.observability_logger, "log_warning", lambda **kwargs: None)
    clock, calls, original = [1100.0], [], box.update
    def fail_once(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise OSError("private raw quote")
        return original(**kwargs)
    monkeypatch.setattr(box, "update", fail_once)
    def advance(_seconds):
        if len(calls) >= 2:
            raise SystemExit
        clock[0] += 60
    with pytest.raises(SystemExit):
        worker.telemetry_market_loop(clock=lambda: clock[0], sleep=advance)
    assert len(calls) == 2 and box.read_summary_status() is not None
    output = capsys.readouterr().out
    assert "TSP_GATE_TIMEBOX_UNAVAILABLE" in output and "private raw quote" not in output


def test_runtime_status_distinguishes_cached_observation_and_current_enable(box, monkeypatch):
    from runtime import runtime_status
    _update(box, 1100, [], monkeypatch)
    runtime_status.write_status("running", "unrelated write")
    monkeypatch.setenv("SHADOW_GATE_TIMEBOX_RESEARCH_ENABLED", "false")
    status = runtime_status.read_status()
    assert status["shadow_gate_timebox_research"]["deadline"] == 8200
    assert status["shadow_gate_timebox_research_observation"]["currently_enabled"] is False
    assert status["shadow_gate_timebox_research_observation"]["is_heartbeat"] is False


def test_large_gap_cohort_still_roundtrips_bounded_report_without_repeating_details(box, monkeypatch):
    _update(box, 1100, [], monkeypatch)
    rows = [_row(2000 + index / 10, tps=100, outcome="UNKNOWN",
                 reason=sorted(box.GAP_REASONS)[index % 4]) for index in range(1000)]
    report = _update(box, 7000, rows, monkeypatch)
    assert report["metrics"]["outcomes"]["UNKNOWN"] == 1000
    assert len(report["metrics"]["gap_details"]) == 20
    assert report["metrics"]["gap_details_truncated"] is True
    assert box._path("summary.json").stat().st_size <= box.sweep.MAX_BYTES
    assert box.read_summary_status() == report
