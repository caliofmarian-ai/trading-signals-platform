from __future__ import annotations

import json
import copy
from dataclasses import replace
from pathlib import Path

import pytest


def _opportunity(*, direction="BUY", signal_id="research-opportunity", candle_ts=1000):
    from core.decision_object import (
        DecisionObject, MarketContext, RejectContext, ScoreContext, SetupContext,
        StrategicFlags, StructureContext, TimeContext, TradePhysicsContext,
    )
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state

    decision = DecisionObject(
        kind="PRE", signal_id=signal_id,
        setup=SetupContext("EUR/USD", direction, candle_ts, "M1", f"cycle-{candle_ts}", "test"),
        market_context=MarketContext(1.1, 0.001, 0.002, "WITH_TREND", "ACTIVE", "STABLE"),
        structure=StructureContext(1.09, 1.12, 1.09, 1.12, 0.03, 0.02, "INTERIOR", "VALID"),
        time=TimeContext(2.0, 2.0, 2.0, 0.4, None, "READY", 2.5),
        score=ScoreContext(88.0, 0.88, {"trend": 24.0}, tier="SCORE_PRE_BAND",
            trade_physics=TradePhysicsContext("READY", TPS=80.0)),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False, trade_physics_ready=True),
        reject=RejectContext(), fsm_inputs={}, explanations=("Fixture canonical evidence.",),
    )
    pre = advance_persistent_fsm(default_fsm_state(), decision, now_ts=candle_ts + 1)
    opening = replace(decision, kind="OPEN_NOW", setup=replace(decision.setup, evaluated_ts=candle_ts + 60),
        score=replace(decision.score, tier="SCORE_OPEN_BAND"))
    handoff = advance_persistent_fsm(pre.next_state, opening, now_ts=candle_ts + 61)
    assert handoff.accepted_stage == "OPEN_NOW"
    return opening, handoff


@pytest.fixture
def research(canonical_runtime_root, fresh_imports, monkeypatch):
    monkeypatch.setenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "true")
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    return fresh_imports("intelligence.shadow_model_time_research")


def _sample(stamp, price=1.1, **extra):
    return {"provider": "FINNHUB", "symbol": "EUR/USD", "price": price,
        "observed_ts": stamp, "source": "LIVE_STREAM_CURRENT_M1_CLOSE", **extra}


def _register(research, **kwargs):
    decision, handoff = _opportunity(**kwargs)
    result = research.register_accepted_open(decision, handoff, provider="FINNHUB", now_ts=1062)
    assert result["registered"]
    return decision, handoff


def _cycle(research, stamp, sample=None, provider="FINNHUB"):
    return research.run_cycle(active_provider=provider, now_ts=stamp, price_loader=lambda _symbol: sample)


def _records(research):
    return [json.loads(p.read_text()) for p in (research._root() / "records").glob("*.json")]


def test_summary_observation_survives_unrelated_shared_status_write(research):
    from runtime import runtime_status
    value = research.summary()
    research.persist_summary_status(value, observed_at=1063)
    runtime_status.write_status("running", "unrelated write")
    payload = runtime_status.read_status()
    assert payload["shadow_model_time_research"] == value
    assert payload["shadow_model_time_research_observation"] == {
        "observed_at": 1063.0, "is_heartbeat": False,
        "source": "DERIVED_RESEARCH_SUMMARY_CACHE", "currently_enabled": True,
    }


@pytest.mark.parametrize("field,value", [
    ("broker_executed", True), ("truth_domain", "MARKET_TRUTH"),
    ("price", 1.23), ("decisive_sample", 3), ("hypothetical_win_rate_percent", 80),
    ("pending", True), ("pending", 257), ("outcomes", {"WIN": -1, "LOSS": 0, "DRAW": 0, "UNKNOWN": 0}),
])
def test_invalid_or_private_summary_cache_is_rejected(research, field, value):
    summary = copy.deepcopy(research.summary())
    summary[field] = value
    with pytest.raises(ValueError):
        research.persist_summary_status(summary, observed_at=1063)
    assert research.read_summary_status() is None


def test_cached_rate_keeps_draw_unknown_outside_decisive_denominator(research):
    value = research.summary()
    value.update(status="OBSERVED", outcomes={"WIN": 2, "LOSS": 1, "DRAW": 4, "UNKNOWN": 5},
                 decisive_sample=3, hypothetical_win_rate_percent=200/3)
    research.persist_summary_status(value, observed_at=1063)
    assert research.read_summary_status()["summary"] == value
    value["hypothetical_win_rate_percent"] = 200/12
    with pytest.raises(ValueError):
        research.persist_summary_status(value, observed_at=1063)


def test_missing_oversized_and_malformed_cache_are_unknown(research):
    path = Path(research.storage.state_path("shadow_research_summary.json"))
    assert research.read_summary_status() is None
    path.parent.mkdir(parents=True, exist_ok=True)
    for raw in (b'[]', b'{', b'x' * (research.MAX_SUMMARY_STATUS_BYTES + 1)):
        path.write_bytes(raw)
        assert research.read_summary_status() is None


def test_cached_observation_does_not_claim_current_activation(research, monkeypatch):
    from runtime import runtime_status
    research.persist_summary_status(research.summary(), observed_at=1063)
    monkeypatch.setenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "false")
    payload = runtime_status.read_status()
    assert payload["shadow_model_time_research"]["enabled"] is True  # At observation time.
    assert payload["shadow_model_time_research_observation"]["currently_enabled"] is False
    assert payload["shadow_model_time_research_observation"]["is_heartbeat"] is False


@pytest.mark.parametrize(("direction", "price", "outcome"), [
    ("BUY", 1.2, "WIN"), ("BUY", 1.0, "LOSS"), ("BUY", 1.1, "DRAW"),
    ("SELL", 1.0, "WIN"), ("SELL", 1.2, "LOSS"), ("SELL", 1.1, "DRAW"),
])
def test_real_post_decision_samples_form_only_hypothetical_labels(research, direction, price, outcome):
    decision, _ = _register(research, direction=direction)
    original = decision.to_dict()
    _cycle(research, 1062.5, _sample(1061.9))  # A pre-decision tick is ineligible.
    assert _records(research)[0]["state"] == "WAITING_ENTRY"
    _cycle(research, 1063, _sample(1063))
    _cycle(research, 1183, _sample(1183, price))
    row = _records(research)[0]
    assert row["outcome"] == outcome
    assert row["decision_snapshot"] == original == decision.to_dict()
    assert row["publication_status"] == "NOT_PUBLISHED"
    assert row["authoritative_for_strategy_performance"] is False
    assert row["broker_executed"] is False
    assert row["execution_calibration_proven"] is False
    assert research.summary()["outcomes"][outcome] == 1
    assert research.summary()["hypothetical_win_rate_percent"] == (None if outcome == "DRAW" else 100.0 if outcome == "WIN" else 0.0)


def test_private_export_validates_quotes_and_does_not_mutate_source(research):
    _register(research)
    _cycle(research, 1063, _sample(1063, 1.1))
    _cycle(research, 1183, _sample(1183, 1.2))
    path = next((research._root() / "records").glob("*.json"))
    row = json.loads(path.read_text())
    row["unexpected_secret"] = "never-export-this"
    row["entry_sample"]["unexpected_secret"] = "never-export-this"
    path.write_text(json.dumps(row))
    before = {str(p): p.read_bytes() for p in research._root().rglob("*") if p.is_file()}
    value = research.private_calibration_evidence()
    assert value["status"] == "VALIDATED_PRIVATE_RESEARCH"
    assert value["validated_record_count"] == 1
    item = value["records"][0]
    assert item["outcome"] == "WIN" and item["entry_sample"]["observed_ts"] == 1063
    assert item["expiry_sample"]["observed_ts"] == item["expiry_ts"] == 1183
    assert item["horizon_seconds"] == 120
    assert "never-export-this" not in json.dumps(value)
    assert "decision_snapshot" not in json.dumps(value)
    assert value["execution_calibration_proven"] is False
    assert before == {str(p): p.read_bytes() for p in research._root().rglob("*") if p.is_file()}
    row["outcome"] = "LOSS"
    path.write_text(json.dumps(row))
    assert research.private_calibration_evidence()["status"] == "SOURCE_UNAVAILABLE_OR_INVALID"
    assert research.private_calibration_evidence()["records"] == []


def test_private_export_is_bounded_and_rejects_symlinks(research):
    directory = research._root() / "records"
    directory.mkdir(parents=True)
    empty = research.private_calibration_evidence()
    assert empty["validated_record_count"] == 0
    for i in range(129):
        (directory / (f"{i:064x}" + ".json")).write_text("{}")
    assert research.private_calibration_evidence()["status"] == "INVENTORY_BOUND_EXCEEDED"
    for path in directory.iterdir():
        path.unlink()
    (directory / ("0" * 64 + ".json")).symlink_to(directory.parent / "unrelated.json")
    assert research.private_calibration_evidence()["status"] == "SOURCE_UNAVAILABLE_OR_INVALID"


def test_private_export_reader_cannot_exceed_remaining_byte_budget(research):
    _register(research)
    path = next((research._root() / "records").glob("*.json"))
    budget = [10]
    with pytest.raises(ValueError):
        research._record(research._root(), path.stem, read_budget=budget)
    assert budget[0] == -1  # At most the bound plus one overflow sentinel.


@pytest.mark.parametrize("field,value", [
    ("outcome", "unexpected-private-text"), ("finalized_ts", "unexpected-private-text"),
    ("expiry_ts", "unexpected-private-text"), ("expiry_sample", {"price": "unexpected-private-text"}),
])
def test_pending_export_cannot_leak_unvalidated_optional_fields(research, field, value):
    _register(research)
    path = next((research._root() / "records").glob("*.json"))
    row = json.loads(path.read_text())
    row[field] = value
    path.write_text(json.dumps(row))
    result = research.private_calibration_evidence()
    assert result["status"] == "SOURCE_UNAVAILABLE_OR_INVALID" and result["records"] == []
    assert "unexpected-private-text" not in json.dumps(result)


def test_unknown_export_requires_a_numeric_finalization_time(research):
    _register(research)
    _cycle(research, 1073)
    path = next((research._root() / "records").glob("*.json"))
    row = json.loads(path.read_text())
    assert row["outcome"] == "UNKNOWN"
    row["finalized_ts"] = "unexpected-private-text"
    path.write_text(json.dumps(row))
    assert research.private_calibration_evidence()["status"] == "SOURCE_UNAVAILABLE_OR_INVALID"


@pytest.mark.parametrize("sample", [
    _sample(1063, provider="TWELVE_DATA"), _sample(1063, symbol="GBP/USD"),
    _sample(1063, source="HISTORICAL_CANDLE"), _sample(1065), _sample(1059),
    _sample(1063, price=True), _sample(1063, price=float("nan")), _sample(1063, price=-1),
])
def test_wrong_future_stale_or_synthetic_entry_is_never_accepted(research, sample):
    _register(research)
    _cycle(research, 1063, sample)
    assert _records(research)[0]["entry_sample"] is None
    _cycle(research, 1073, None)
    assert research.summary()["outcomes"] == {"WIN": 0, "LOSS": 0, "DRAW": 0, "UNKNOWN": 1}


def test_missing_expiry_is_unknown_and_later_recovery_cannot_rewrite_it(research):
    _register(research)
    _cycle(research, 1063, _sample(1063))
    _cycle(research, 1186, _sample(1186, 1.2))
    terminal = _records(research)[0]
    assert terminal["outcome"] == "UNKNOWN"
    assert terminal["outcome_reason"] == "EXPIRY_OBSERVATION_MISSING"
    _cycle(research, 1190, _sample(1190, 1.3))
    assert _records(research)[0] == terminal


def test_provider_switch_marks_unknown_without_querying_the_other_provider(research):
    _register(research)
    _cycle(research, 1063, _sample(1063))
    calls = []
    research.run_cycle(active_provider="TWELVE_DATA", now_ts=1064,
        price_loader=lambda symbol: calls.append(symbol))
    assert calls == []
    assert _records(research)[0]["outcome_reason"] == "PROVIDER_CHANGED"


def test_restart_recovers_orphan_and_keeps_missed_checkpoint_unknown(research):
    _register(research)
    (research._root() / "active.json").unlink()  # Crash before index durability.
    research._RECOVERED.clear()
    _cycle(research, 1063, _sample(1063))
    assert _records(research)[0]["state"] == "WAITING_EXPIRY"
    research._RECOVERED.clear()
    _cycle(research, 1190, _sample(1190, 1.2))
    assert _records(research)[0]["outcome_reason"] == "RESTART_MISSED_OBSERVATION"


def test_one_opportunity_cannot_be_recounted_on_later_candles_or_after_restart(research):
    decision, handoff = _register(research)
    _cycle(research, 1063, _sample(1063))
    _cycle(research, 1183, _sample(1183, 1.2))
    research._RECOVERED.clear()
    result = research.register_accepted_open(decision, handoff, provider="FINNHUB", now_ts=1200)
    assert result["status"] == "DUPLICATE_OPPORTUNITY"
    assert research.summary()["decisive_sample"] == 1


@pytest.mark.parametrize(("name", "value"), [
    ("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "false"), ("SHADOW_MODE", "false"),
    ("ENABLE_BROKER_EXECUTION", "true"),
])
def test_disabled_or_execution_enabled_has_no_research_side_effects(research, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    decision, handoff = _opportunity()
    assert research.register_accepted_open(decision, handoff, provider="FINNHUB", now_ts=1062)["status"] == "DISABLED"
    assert not research._root().exists()


def test_wrong_stage_or_missing_fsm_acceptance_cannot_create_research(research):
    decision, handoff = _opportunity()
    for invalid in [replace(handoff, stage_handoff_ready=False), replace(handoff, decision_id="wrong"),
                    replace(handoff, accepted_stage="PRE"), replace(handoff, signal_id="wrong")]:
        assert research.register_accepted_open(decision, invalid, provider="FINNHUB", now_ts=1062)["status"] == "INELIGIBLE"
    assert not research._root().exists()


def test_bad_records_fail_closed_and_private_prices_never_reach_summary(research):
    _register(research)
    _cycle(research, 1063, _sample(1063, 1.10123456789))
    _cycle(research, 1183, _sample(1183, 1.20234567891))
    summary = json.dumps(research.summary())
    assert "1.10123456789" not in summary and "research-opportunity" not in summary
    assert research.summary()["profitability_established"] is False
    path = next((research._root() / "records").glob("*.json"))
    row = json.loads(path.read_text())
    row["outcome"] = "LOSS"
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match="disagrees"):
        research.summary()


def test_research_failure_including_logging_cannot_block_canonical_engine(research, monkeypatch):
    from core import signal_engine
    decision, handoff = _opportunity()
    monkeypatch.setattr(signal_engine.shadow_research, "register_accepted_open",
        lambda *a, **k: (_ for _ in ()).throw(OSError("private detail")))
    monkeypatch.setattr(signal_engine.observability_logger, "log_warning",
        lambda *a, **k: (_ for _ in ()).throw(OSError("logging unavailable")))
    signal_engine._observe_shadow_research(decision, handoff)


def test_worker_collects_research_without_creating_official_trade_truth(research, monkeypatch, capsys):
    from runtime import telemetry_market_worker as worker
    from runtime import runtime_status
    from core import storage
    from core.execution_model import derive_execution_time
    from core.fsm_decision_adapter import interpret_decision

    decision, _ = _register(research)
    assert derive_execution_time(decision, interpret_decision(decision)).available is False
    monkeypatch.setattr(worker, "run_telemetry_cycle", lambda **kwargs: {})
    monkeypatch.setattr(worker.trade_temporal_telemetry, "recover_after_restart", lambda _now: {})
    monkeypatch.setattr(worker.market_client, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(worker.market_client, "get_latest_price_sample", lambda _symbol: _sample(1063, 1.10123456789))
    def stop(_seconds):
        raise SystemExit
    with pytest.raises(SystemExit):
        worker.telemetry_market_loop(clock=lambda: 1063, sleep=stop)
    assert runtime_status.read_status()["shadow_model_time_research"]["pending"] == 1
    assert not Path(storage.root_path("observability", "open_trades_registry.json")).exists()
    assert not Path(storage.root_path("observability", "trade_temporal_telemetry.jsonl")).exists()
    assert derive_execution_time(decision, interpret_decision(decision)).available is False
    output = capsys.readouterr().out
    assert "TSP_SHADOW_RESEARCH_EVIDENCE" in output
    assert "1.10123456789" not in output and "research-opportunity" not in output


def test_index_write_failure_is_recovered_on_the_next_cycle(research, monkeypatch):
    original = research._save_index
    monkeypatch.setattr(research, "_save_index", lambda *args: (_ for _ in ()).throw(OSError("index unavailable")))
    decision, handoff = _opportunity()
    with pytest.raises(OSError):
        research.register_accepted_open(decision, handoff, provider="FINNHUB", now_ts=1062)
    monkeypatch.setattr(research, "_save_index", original)
    _cycle(research, 1063, _sample(1063))
    assert _records(research)[0]["state"] == "WAITING_EXPIRY"


def test_worker_retries_derived_status_after_transient_failure(research, monkeypatch, capsys):
    from runtime import telemetry_market_worker as worker
    monkeypatch.setattr(worker, "run_telemetry_cycle", lambda **kwargs: {})
    monkeypatch.setattr(worker.trade_temporal_telemetry, "recover_after_restart", lambda _now: {})
    monkeypatch.setattr(worker.market_client, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(worker.observability_logger, "log_warning", lambda **kwargs: None)
    original = research.persist_summary_status
    attempts = []

    def transient(value, *, observed_at):
        attempts.append(observed_at)
        if len(attempts) == 1:
            raise OSError("temporary derived status write failure")
        original(value, observed_at=observed_at)

    monkeypatch.setattr(research, "persist_summary_status", transient)
    sleeps = []

    def stop_after_retry(_seconds):
        sleeps.append(1)
        if len(sleeps) == 2:
            raise SystemExit

    with pytest.raises(SystemExit):
        worker.telemetry_market_loop(clock=lambda: 1063, sleep=stop_after_retry)
    assert attempts == [1063.0, 1063.0]
    assert research.read_summary_status()["observed_at"] == 1063
    assert capsys.readouterr().out.count("TSP_SHADOW_RESEARCH_EVIDENCE") == 1
