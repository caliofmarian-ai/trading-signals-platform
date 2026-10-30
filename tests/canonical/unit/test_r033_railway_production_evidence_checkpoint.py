"""R-033 bounded, anonymous one-time Railway observability checkpoint tests."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from scripts import railway_observability_checkpoint as probe


NOW = 1793358000


def _snapshot_data():
    return {
        "publications": {
            "status": "OBSERVED",
            "reason": "BOUNDED_PRIMARY_V3_PUBLICATION_EVIDENCE",
            "unique_open_now_published": 24,
            "published_per_hour_rolling_avg": 1.0,
            "invalid_count": 2,
            "historical_excluded_count": 0,
            "signal_id": "PRIVATE-SIGNAL-ID-NOT-FOR-RAILWAY",
            "destination_id": -1003726714813,
        },
        "lifecycle": {
            "status": "OBSERVED",
            "sources": {
                "engine": {"status": "OBSERVED", "invalid_rows": 1},
                "distribution": {"status": "OBSERVED", "invalid_rows": 0},
            },
            "pre_to_open_visible_matched_pairs": 3,
            "pre_to_open_pairs_at_least_30_seconds": 2,
            "pre_to_open_lead_median_seconds": 39.5,
            "signal_ids": ["PRIVATE-SIGNAL-ID-NOT-FOR-RAILWAY"],
        },
        "market": {
            "status": "OBSERVED",
            "reason": "VALIDATED_FINALIZED_MARKET_TRUTH",
            "verified_finalized_trade_count": 8,
            "segment_count": 1,
            "segments": [{
                "symbol": "EUR/USD", "market_provider": "FINNHUB",
                "timeframe": "M1", "strategy_version": "2.0.0",
                "wins": 5, "losses": 2, "draws": 1,
                "decisive_sample": 7,
                "descriptive_win_rate_percent": 71.43,
                "wilson_95_interval_percent": {"lower": 35.9, "upper": 91.3},
                "entry_price": 1.1234567,
                "subscriber_ref": "PRIVATE-ACCOUNT",
            }],
            "quality": {"invalid_rows": 1, "conflicting_identities": 1},
            "raw_trade_id": "PRIVATE-SIGNAL-ID-NOT-FOR-RAILWAY",
        },
        "focus": {
            "status": "OBSERVED",
            "reason": "BOUNDED_PRIMARY_V3_FSM_FOCUS_EVIDENCE",
            "focus_entries": 3, "focus_exits": 2,
            "replacement_entries_without_victim_exit": 1,
            "recent_events": [{
                "symbol": "EUR/USD",
                "signal_id": "PRIVATE-SIGNAL-ID-NOT-FOR-RAILWAY",
            }],
            "quality": {"duplicate_event_ids": 1},
        },
    }


def _compose(items):
    return probe.compose_checkpoint(now_ts=NOW, **items)


def test_objective_log_line_contains_only_aggregate_allowlisted_fields():
    raw = _snapshot_data()
    report = _compose(raw)
    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    assert report["component"] == "tsp_production_evidence_checkpoint"
    assert report["scope"] == "ONE_SHOT_PERSISTED_EVENT_OBSERVATION_AT_STARTUP"
    assert report["live_client_or_broker_acceptance"] == "NOT_TESTED"
    assert report["publication_24h"]["unique_published_open_now"] == 24
    assert report["lifecycle_24h"]["pairs_lead_at_least_30s"] == 2
    assert report["objective_market_7d"]["validated_finalized_trades"] == 8
    assert report["focus_7d"]["replacement_victim_gap_count"] == 1

    market = report["objective_market_7d"]["sample_ranked_segments"][0]
    assert market["descriptive_win_rate_percent"] == 71.43
    assert market["wilson_95_interval_percent"]["upper_percent"] == 91.3
    assert market["not_live_trading_or_statistical_proof"] is True
    for secret in ("PRIVATE-SIGNAL-ID-NOT-FOR-RAILWAY", "PRIVATE-ACCOUNT",
                   "1.1234567", "-1003726714813", "entry_price",
                   "subscriber_ref", "raw_trade_id", "recent_events"):
        assert secret not in serialized
    assert len(serialized.encode("utf-8")) < 3000


def test_unknown_sources_never_create_zeros_or_fake_win_rates():
    raw = {
        "publications": {"status": "UNKNOWN", "reason": "DISTRIBUTION_LOG_NOT_FOUND",
                         "unique_open_now_published": 0},
        "lifecycle": {"status": "UNKNOWN", "pre_to_open_visible_matched_pairs": 0},
        "market": {"status": "UNKNOWN", "reason": "MARKET_TELEMETRY_FILE_NOT_FOUND",
                   "verified_finalized_trade_count": 0,
                   "segments": [{"wins": 100, "descriptive_win_rate_percent": 100}]},
        "focus": {"status": "UNKNOWN", "focus_entries": 0},
    }
    out = _compose(raw)
    assert out["publication_24h"]["unique_published_open_now"] is None
    assert out["lifecycle_24h"]["pre_open_visible_matched_pairs"] is None
    assert out["objective_market_7d"]["validated_finalized_trades"] is None
    assert out["objective_market_7d"]["sample_ranked_segments"] == []
    assert out["focus_7d"]["observed_entries"] is None
    assert out["live_client_or_broker_acceptance"] == "NOT_TESTED"


def test_small_or_unverified_market_sample_cannot_claim_80_percent():
    raw = _snapshot_data()
    segment = raw["market"]["segments"][0]
    segment["decisive_sample"] = 4
    segment["descriptive_win_rate_percent"] = 100
    out = _compose(raw)
    assert out["objective_market_7d"]["sample_ranked_segments"][0]["descriptive_win_rate_percent"] is None
    assert out["objective_market_7d"]["sample_ranked_segments"][0]["wilson_95_interval_percent"] is None


def test_malicious_or_invalid_values_are_sanitized_not_logged():
    raw = _snapshot_data()
    raw["publications"]["reason"] = "INVALID\nTOKEN=secret"
    raw["market"]["segments"][0]["symbol"] = "EUR/USD\nPRIVATE-ACCOUNT"
    raw["market"]["segments"][0]["market_provider"] = "<script>"
    raw["market"]["segments"][0]["descriptive_win_rate_percent"] = float("nan")
    raw["market"]["segments"][0]["wilson_95_interval_percent"] = {"lower": 99, "upper": 70}
    raw["market"]["segments"][0]["wins"] = True
    raw["focus"]["quality"] = {"duplicate_event_ids": True, "invalid_rows": 2}
    out = _compose(raw)
    rendered = json.dumps(out)
    assert out["publication_24h"]["reason"] == "UNKNOWN_REASON"
    seg = out["objective_market_7d"]["sample_ranked_segments"][0]
    assert seg["symbol"] == "UNKNOWN"
    assert seg["market_provider"] == "UNKNOWN"
    assert seg["descriptive_win_rate_percent"] is None
    assert seg["wilson_95_interval_percent"] is None
    assert seg["wins"] is None
    assert "PRIVATE-ACCOUNT" not in rendered
    assert "TOKEN=secret" not in rendered
    assert "script" not in rendered
    assert out["focus_7d"]["quality"] == {"invalid_rows": 2}


def test_more_than_three_segments_are_never_printed():
    raw = _snapshot_data()
    raw["market"]["segments"] = [
        {**raw["market"]["segments"][0], "symbol": f"EUR/USD"}
        for _ in range(100)
    ]
    raw["market"]["segment_count"] = 100
    out = _compose(raw)
    assert out["objective_market_7d"]["segment_count"] == 100
    assert len(out["objective_market_7d"]["sample_ranked_segments"]) == 3


@pytest.mark.parametrize("invalid_time", [True, -1, 0, "1793358000", 1.5])
def test_invalid_time_rejected_without_logging(invalid_time):
    with pytest.raises(ValueError):
        probe.compose_checkpoint(now_ts=invalid_time, **_snapshot_data())


def test_collect_uses_same_now_and_persistent_paths_for_all_truth_domains(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import core
    sources = {
        "publication_evidence": importlib.import_module("core.publication_evidence"),
        "lifecycle_funnel_evidence": importlib.import_module("core.lifecycle_funnel_evidence"),
        "market_outcome_evidence": importlib.import_module("core.market_outcome_evidence"),
        "focus_history_evidence": importlib.import_module("core.focus_history_evidence"),
    }
    for key, module in sources.items():
        monkeypatch.setattr(core, key, module, raising=False)

    for name in ("ENGINE_EVENTS_LOG", "DIST_EVENTS_LOG", "FSM_EVENTS_LOG",
                 "TRADE_TEMPORAL_TELEMETRY_LOG"):
        monkeypatch.delenv(name, raising=False)

    captured = []
    snapshots = _snapshot_data()

    def spy(name, result):
        def reader(**kwargs):
            captured.append((name, kwargs))
            return result
        return reader

    monkeypatch.setattr(sources["publication_evidence"], "publication_snapshot",
                        spy("publication", snapshots["publications"]))
    monkeypatch.setattr(sources["lifecycle_funnel_evidence"], "build_funnel",
                        spy("lifecycle", snapshots["lifecycle"]))
    monkeypatch.setattr(sources["market_outcome_evidence"], "build_market_snapshot",
                        spy("market", snapshots["market"]))
    monkeypatch.setattr(sources["focus_history_evidence"], "build_focus_history",
                        spy("focus", snapshots["focus"]))

    out = probe.collect_checkpoint(base_dir=tmp_path, now_ts=NOW)
    assert out["publication_24h"]["unique_published_open_now"] == 24
    assert len(captured) == 4
    for _, args in captured:
        assert args["now_ts"] == NOW
    expected = {
        "publication": {"path": str(tmp_path / "observability" / "distribution_events.jsonl"),
                        "window_hours": 24},
        "lifecycle": {"engine_path": str(tmp_path / "observability" / "engine_events.jsonl"),
                      "distribution_path": str(tmp_path / "observability" / "distribution_events.jsonl"),
                      "range_days": 1},
        "market": {"path": str(tmp_path / "observability" / "trade_temporal_telemetry.jsonl"),
                   "range_days": 7, "max_segments": 3},
        "focus": {"path": str(tmp_path / "observability" / "fsm_events.jsonl"),
                  "range_days": 7},
    }
    for name, kwargs in captured:
        for key, value in expected[name].items():
            assert kwargs[key] == value


def test_reader_exception_is_isolated_from_other_truth_domains(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import core
    pub = importlib.import_module("core.publication_evidence")
    monkeypatch.setattr(core, "publication_evidence", pub, raising=False)

    def broken(**kwargs):
        raise RuntimeError("SECRET-BOT-TOKEN-DO-NOT-LOG")

    monkeypatch.setattr(pub, "publication_snapshot", broken)
    out = probe.collect_checkpoint(base_dir=tmp_path, now_ts=NOW)
    assert out["publication_24h"]["status"] == "UNKNOWN"
    assert out["publication_24h"]["reason"] == "READER_EXCEPTION"
    assert "SECRET-BOT-TOKEN-DO-NOT-LOG" not in json.dumps(out)


def test_one_stdout_line_does_not_echo_errors_or_create_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(probe, "collect_checkpoint", lambda **kwargs: _compose(_snapshot_data()))
    before = list(tmp_path.iterdir())
    probe.emit_checkpoint(base_dir=tmp_path, now_ts=NOW)
    stdout = capsys.readouterr().out.strip().splitlines()
    assert len(stdout) == 1
    assert stdout[0].startswith(probe.EVENT_PREFIX)
    assert json.loads(stdout[0][len(probe.EVENT_PREFIX):])["publication_24h"]["unique_published_open_now"] == 24
    assert list(tmp_path.iterdir()) == before


def test_collector_failure_cannot_prevent_startup_or_leak_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    def broken(**kwargs):
        raise ValueError("secret-credit-card: 4111111111111111")

    monkeypatch.setattr(probe, "collect_checkpoint", broken)
    assert probe.emit_checkpoint(base_dir=tmp_path, now_ts=NOW) is None
    output = capsys.readouterr().out
    assert output.startswith(probe.EVENT_PREFIX)
    assert "secret-credit-card" not in output
    assert json.loads(output[len(probe.EVENT_PREFIX):])["status"] == "UNKNOWN"
    assert json.loads(output[len(probe.EVENT_PREFIX):])["reason"] == "CHECKPOINT_COLLECTION_FAILED"


def test_railway_preflight_remains_before_evidence_and_worker_start():
    from inspect import getsource

    startup = importlib.import_module("scripts.railway_start")
    src = getsource(startup.main)
    assert src.index("readiness_report(base_dir=base_dir)") < src.index(
        "emit_checkpoint(base_dir=base_dir)"
    ) < src.index("start_system()")
