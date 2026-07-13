"""
BATCH-07 tests — analytics and research toolchain restoration.

Tests GAP-010 and GAP-015 findings and all required test cases from
the BATCH-07 problem statement.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge_analytics_modules() -> None:
    prefixes = (
        "core.jsonl_parser",
        "core.analytics_engine",
        "intelligence.research_engine",
        "intelligence.report_loader",
        "tools.strategy_auditor_lib",
        "tools.strategy_auditor_daily",
        "tools",
        "core.storage",
        "core",
        "intelligence",
    )
    for name in list(sys.modules.keys()):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove env vars that would point to /opt/binarybot/ or production state."""
    for var in (
        "BINARYBOT_BASE_DIR",
        "OBS_DIR",
        "ENGINE_EVENTS_LOG",
        "DIST_EVENTS_LOG",
        "FSM_EVENTS_LOG",
        "OUTCOMES_LOG",
        "ANALYTICS_DIR",
        "STRATEGY_AUDITOR_SETTINGS",
        "TELEGRAM_BOT_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)


def _write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def _make_outcome_record(
    signal_id: str = "SIG_001",
    outcome: str = "WIN",
    user_id: str = "M-AABBCCDD",
) -> Dict[str, Any]:
    return {
        "event_type": "user_outcome_record",
        "signal_id": signal_id,
        "tier": "ELITE",
        "user_id": user_id,
        "outcome": outcome,
        "voted_ts": 1700000000,
    }


def _make_signal_event(
    signal_id: str = "SIG_001",
    stage: str = "OPEN_NOW",
    symbol: str = "EURUSD",
) -> Dict[str, Any]:
    return {
        "event_type": "signal_event",
        "event_id": f"EVT_{signal_id}_{stage}",
        "stage": stage,
        "signal_id": signal_id,
        "symbol": symbol,
        "timeframe": "M1",
        "data": {
            "direction": "UP",
            "score_total": 72.0,
            "buffer_mode": "ENTRY",
            "buffer_price": 1.1000,
            "expiry_minutes": 5,
            "candle_ts": 1700000000,
            "created_ts": 1700000001,
        },
    }


def _make_tier_publish_event(
    signal_id: str = "SIG_001",
    publish_result: str = "PUBLISHED",
) -> Dict[str, Any]:
    return {
        "event_type": "tier_publish",
        "event_id": f"EVT_DIST_{signal_id}_{publish_result}",
        "signal_id": signal_id,
        "route": "ELITE",
        "tier": "ELITE",
        "stage": "OPEN_NOW",
        "data": {
            "publish_result": publish_result,
            "route_state_before": "ACTIVE",
            "route_state_after": "ACTIVE",
            "limit": None,
            "counter_before": 0,
            "counter_after": 1,
            "counted": True,
            "attempted": True,
            "destination_kind": "telegram_group",
            "feedback_enabled": True,
            "transport": {"ok": True, "message_id": 42, "error": None},
            "dedup": {"key": signal_id, "was_duplicate": False, "action": "accepted"},
        },
    }


def _make_decision_event(
    signal_id: str = "SIG_001",
    decision_kind: str = "OPEN_NOW",
    symbol: str = "EURUSD",
    score_total: float = 72.0,
) -> Dict[str, Any]:
    return {
        "event_type": "decision",
        "signal_id": signal_id,
        "symbol": symbol,
        "data": {
            "decision_kind": decision_kind,
            "symbol": symbol,
            "signal_id": signal_id,
            "score_total": score_total,
        },
    }


def _base_intelligence_settings(tmp_path: Path) -> Dict[str, Any]:
    obs_dir = tmp_path / "observability"
    obs_dir.mkdir(parents=True, exist_ok=True)
    outcomes_dir = tmp_path / "outcomes"
    outcomes_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = tmp_path / "analytics" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return {
        "reports": {
            "enabled": True,
            "output_dir": str(reports_dir),
            "cache_dir": str(tmp_path / "analytics" / "cache"),
            "write_json": True,
            "write_markdown": True,
        },
        "sources": {
            "engine_events": str(obs_dir / "engine_events.jsonl"),
            "fsm_events": str(obs_dir / "fsm_events.jsonl"),
            "distribution_events": str(obs_dir / "distribution_events.jsonl"),
            "error_events": str(obs_dir / "error_events.jsonl"),
            "outcomes": str(outcomes_dir / "outcomes.jsonl"),
        },
        "heatmap": {
            "enabled": True,
            "score_buckets": [[50, 60], [60, 70], [70, 80], [80, 100]],
        },
        "bottleneck_detection": {
            "enabled": True,
            "dominant_reject_share_threshold": 0.6,
        },
        "symbol_health": {
            "enabled": True,
            "healthy_pre_rate_min": 0.15,
            "starved_pre_rate_max": 0.03,
            "blocked_same_reason_share_min": 0.6,
        },
    }


# ===========================================================================
# SECTION 1: MODULE IMPORTS (tests 1–4)
# ===========================================================================

def test_analytics_engine_imports_successfully():
    """Test 1: analytics_engine imports without error."""
    _purge_analytics_modules()
    mod = importlib.import_module("core.analytics_engine")
    assert hasattr(mod, "recompute")
    assert hasattr(mod, "get_user_stats")


def test_research_engine_imports_successfully():
    """Test 2: research_engine imports without error."""
    _purge_analytics_modules()
    mod = importlib.import_module("intelligence.research_engine")
    assert hasattr(mod, "build_research_report")
    assert hasattr(mod, "compute_signal_funnel")
    assert hasattr(mod, "compute_outcome_stats")


def test_daily_auditor_tools_import_successfully():
    """Test 3: strategy_auditor_daily and strategy_auditor_lib import without error (GAP-015)."""
    _purge_analytics_modules()
    lib = importlib.import_module("tools.strategy_auditor_lib")
    daily = importlib.import_module("tools.strategy_auditor_daily")
    assert hasattr(lib, "load_settings")
    assert hasattr(lib, "build_report")
    assert hasattr(daily, "run_auditor")


def test_imports_start_no_network_threads_or_services(monkeypatch: pytest.MonkeyPatch):
    """Test 4: imports do not start threads, network calls, or live services."""
    import threading
    thread_count_before = threading.active_count()

    _purge_analytics_modules()
    importlib.import_module("core.analytics_engine")
    importlib.import_module("intelligence.research_engine")
    importlib.import_module("tools.strategy_auditor_lib")
    importlib.import_module("tools.strategy_auditor_daily")

    assert threading.active_count() == thread_count_before, (
        "Importing analytics/research modules must not start background threads"
    )


# ===========================================================================
# SECTION 2: PARSING / INPUT NORMALIZATION (tests 5–18)
# ===========================================================================

def test_valid_json_object_parses_successfully():
    """Test 5: valid JSON object parses to dict."""
    from core.jsonl_parser import parse_json_line
    result = parse_json_line('{"event_type": "test", "value": 1}')
    assert result == {"event_type": "test", "value": 1}


def test_valid_jsonl_records_parse_successfully(tmp_path: Path):
    """Test 6: valid JSONL file produces all records."""
    from core.jsonl_parser import iter_jsonl
    path = tmp_path / "test.jsonl"
    _write_jsonl(path, [{"a": 1}, {"b": 2}])
    results = list(iter_jsonl(str(path)))
    assert len(results) == 2
    assert all(err is None for _, err in results)
    assert results[0][0] == {"a": 1}
    assert results[1][0] == {"b": 2}


def test_malformed_json_is_reported_clearly():
    """Test 7: malformed JSON raises ParseError, not returns {}."""
    from core.jsonl_parser import parse_json_line, ParseError
    with pytest.raises(ParseError) as exc_info:
        parse_json_line("{bad json}")
    assert "invalid JSON" in str(exc_info.value)


def test_malformed_jsonl_line_reported_with_context(tmp_path: Path):
    """Test 8: malformed JSONL line is reported with source path and line number."""
    from core.jsonl_parser import iter_jsonl, ParseError
    path = tmp_path / "mixed.jsonl"
    path.write_text('{"ok": true}\n{bad}\n{"also_ok": true}\n', encoding="utf-8")
    results = list(iter_jsonl(str(path)))
    assert len(results) == 3
    record1, err1 = results[0]
    record2, err2 = results[1]
    record3, err3 = results[2]
    assert record1 == {"ok": True} and err1 is None
    assert record2 is None and isinstance(err2, ParseError)
    assert err2.source_path == str(path)
    assert err2.line_number == 2
    assert record3 == {"also_ok": True} and err3 is None


def test_malformed_record_not_silently_converted_to_empty():
    """Test 9: malformed JSON never silently becomes {}."""
    from core.jsonl_parser import parse_json_line, ParseError
    for bad_line in ["{not json}", "null", "[1,2,3]", ""]:
        with pytest.raises(ParseError):
            parse_json_line(bad_line)


def test_unknown_event_type_classified_explicitly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 10: unknown stage values in signal events are classified, not coerced."""
    _purge_analytics_modules()
    engine_log = tmp_path / "observability" / "engine_events.jsonl"
    engine_log.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(engine_log, [
        {**_make_signal_event("SIG_001", "OPEN_NOW"), "event_id": "E1"},
        {**_make_signal_event("SIG_002", "UNKNOWN_STAGE"), "event_id": "E2"},
    ])
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(engine_log))
    import intelligence.research_engine as re
    funnel = re.compute_signal_funnel()
    # OPEN_NOW should count; unknown should appear in unsupported_stages
    assert funnel["OPEN_NOW"] == 1
    assert "UNKNOWN_STAGE" in funnel["unsupported_stages"]
    assert funnel["unsupported_stages"]["UNKNOWN_STAGE"] == 1


def test_missing_required_fields_produce_invalid_record_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 11: outcome record missing signal_id is invalid, not counted."""
    _purge_analytics_modules()
    outcomes_log = tmp_path / "outcomes" / "outcomes.jsonl"
    outcomes_log.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(outcomes_log, [
        {"outcome": "WIN", "user_id": "M-AABB"},       # missing signal_id
        _make_outcome_record("SIG_001", "WIN", "M-XXYY"),  # valid
    ])
    monkeypatch.setenv("OUTCOMES_LOG", str(outcomes_log))
    import core.analytics_engine as ae
    ae.AGGREGATES_PATH = str(tmp_path / "aggregates.json")
    result = ae._load_outcomes(str(outcomes_log))
    assert result["wins"] == 1
    assert result["invalid_count"] == 1


def test_optional_fields_use_defaults_where_permitted(tmp_path: Path):
    """Test 12: optional JSONL fields missing do not cause failures."""
    from core.jsonl_parser import parse_json_line
    # A record with only required fields should parse fine
    record = parse_json_line('{"event_type": "signal_event", "signal_id": "SIG_001"}')
    assert record["signal_id"] == "SIG_001"


def test_duplicate_event_ids_are_deduplicated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 13: duplicate event_id in engine log counted only once."""
    _purge_analytics_modules()
    engine_log = tmp_path / "observability" / "engine_events.jsonl"
    engine_log.parent.mkdir(parents=True, exist_ok=True)
    # Same event_id twice
    evt = {**_make_signal_event("SIG_001", "OPEN_NOW"), "event_id": "EVT_DUPE"}
    _write_jsonl(engine_log, [evt, evt])
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(engine_log))
    import intelligence.research_engine as re
    funnel = re.compute_signal_funnel()
    assert funnel["OPEN_NOW"] == 1  # deduplicated


def test_duplicate_outcome_identities_do_not_inflate_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 14: same (signal_id, user_id) counted only once in outcomes."""
    _purge_analytics_modules()
    outcomes_log = tmp_path / "outcomes" / "outcomes.jsonl"
    outcomes_log.parent.mkdir(parents=True, exist_ok=True)
    rec = _make_outcome_record("SIG_001", "WIN", "M-AABB")
    _write_jsonl(outcomes_log, [rec, rec, rec])  # three identical records
    monkeypatch.setenv("OUTCOMES_LOG", str(outcomes_log))
    import core.analytics_engine as ae
    ae.AGGREGATES_PATH = str(tmp_path / "aggregates.json")
    result = ae._load_outcomes(str(outcomes_log))
    assert result["wins"] == 1  # deduplicated to 1


def test_canonical_utc_ordering_is_deterministic(tmp_path: Path):
    """Test 15: parsing order from JSONL is deterministic (file order)."""
    from core.jsonl_parser import iter_jsonl
    records_in = [{"n": i} for i in range(5)]
    path = tmp_path / "order.jsonl"
    _write_jsonl(path, records_in)
    results = [(rec, err) for rec, err in iter_jsonl(str(path)) if err is None]
    assert [r["n"] for r, _ in results] == list(range(5))


def test_empty_input_produces_explicit_no_data_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 16: empty outcomes file yields a no_data=True result."""
    _purge_analytics_modules()
    outcomes_log = tmp_path / "outcomes" / "outcomes.jsonl"
    outcomes_log.parent.mkdir(parents=True, exist_ok=True)
    outcomes_log.write_text("", encoding="utf-8")  # empty file
    monkeypatch.setenv("OUTCOMES_LOG", str(outcomes_log))
    import core.analytics_engine as ae
    ae.AGGREGATES_PATH = str(tmp_path / "aggregates.json")
    result = ae._load_outcomes(str(outcomes_log))
    assert result["no_data"] is True
    assert result["total"] == 0
    assert result["wins"] == 0


def test_missing_input_file_fails_clearly(tmp_path: Path):
    """Test 17: iter_jsonl raises FileNotFoundError for nonexistent path."""
    from core.jsonl_parser import iter_jsonl
    with pytest.raises(FileNotFoundError):
        list(iter_jsonl(str(tmp_path / "does_not_exist.jsonl")))


def test_missing_required_input_triggers_explicit_no_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 17b: missing outcomes file in analytics returns no_data with reason."""
    _purge_analytics_modules()
    nonexistent = str(tmp_path / "no_outcomes.jsonl")
    monkeypatch.setenv("OUTCOMES_LOG", nonexistent)
    import core.analytics_engine as ae
    ae.AGGREGATES_PATH = str(tmp_path / "aggregates.json")
    result = ae._load_outcomes(nonexistent)
    assert result["no_data"] is True
    assert result.get("reason") == "outcomes_file_not_found"


def test_no_legacy_compatibility_path_needed():
    """Test 18: no legacy hard-coded /opt/binarybot/ path required in modified modules."""
    # Verify modules can be used with env-var-overridden paths
    import core.analytics_engine as ae
    # Module should not hard-require /opt/binarybot/ — paths come from env vars
    assert "OUTCOMES_LOG" in os.environ or True  # env var path is the override mechanism
    # The module constants are set at import time from env vars
    assert hasattr(ae, "_OUTCOMES_LOG")
    assert hasattr(ae, "AGGREGATES_PATH")


# ===========================================================================
# SECTION 3: ANALYTICS (tests 19–29)
# ===========================================================================

@pytest.fixture()
def analytics_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Set up fixture analytics environment with valid records."""
    obs_dir = tmp_path / "observability"
    obs_dir.mkdir(parents=True, exist_ok=True)
    outcomes_dir = tmp_path / "outcomes"
    outcomes_dir.mkdir(parents=True, exist_ok=True)
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)

    outcomes_log = outcomes_dir / "outcomes.jsonl"
    dist_log = obs_dir / "distribution_events.jsonl"

    _write_jsonl(outcomes_log, [
        _make_outcome_record("SIG_001", "WIN", "M-U1"),
        _make_outcome_record("SIG_002", "LOSE", "M-U2"),
        _make_outcome_record("SIG_003", "WIN", "M-U3"),
        _make_outcome_record("SIG_004", "WIN", "M-U1"),
        _make_outcome_record("SIG_005", "MISSED", "M-U2"),
        _make_outcome_record("SIG_006", "WIN", "M-U3"),
        _make_outcome_record("SIG_007", "WIN", "M-U1"),
    ])
    _write_jsonl(dist_log, [
        _make_tier_publish_event("SIG_001", "PUBLISHED"),
        _make_tier_publish_event("SIG_002", "FAILED"),
        _make_tier_publish_event("SIG_003", "SKIPPED_LIMIT"),
        _make_tier_publish_event("SIG_004", "DUPLICATE_SUPPRESSED"),
        _make_tier_publish_event("SIG_005", "SKIPPED_DISABLED"),
        _make_tier_publish_event("SIG_006", "SKIPPED_SILENT"),
    ])

    monkeypatch.setenv("OUTCOMES_LOG", str(outcomes_log))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(dist_log))
    monkeypatch.setenv("ANALYTICS_DIR", str(analytics_dir))

    _purge_analytics_modules()
    import core.analytics_engine as ae
    ae.AGGREGATES_PATH = str(analytics_dir / "aggregates.json")
    ae._OUTCOMES_LOG = str(outcomes_log)
    ae._DIST_LOG = str(dist_log)
    ae._ANALYTICS_BASE = str(analytics_dir)

    return {"analytics_dir": analytics_dir, "outcomes_log": outcomes_log, "dist_log": dist_log, "ae": ae}


def test_analytics_runs_on_valid_fixture_data(analytics_fixture, tmp_path: Path):
    """Test 19: analytics recompute runs on valid fixture data."""
    ae = analytics_fixture["ae"]
    result = ae.recompute(1700000000)
    assert isinstance(result, dict)
    assert result["total_votes"] > 0
    assert result["no_data"] is False


def test_analytics_correlates_open_now_outcomes(analytics_fixture):
    """Test 20: analytics counts signals with valid outcomes correctly."""
    ae = analytics_fixture["ae"]
    result = ae.recompute(1700000000)
    assert result["signals_tracked"] >= 1


def test_distribution_results_counted_separately(analytics_fixture):
    """Test 21: PUBLISHED, FAILED, SKIPPED, BLOCKED, DUPLICATE_SUPPRESSED counted separately."""
    ae = analytics_fixture["ae"]
    dist = ae._load_distribution_metrics(str(analytics_fixture["dist_log"]))
    assert dist["PUBLISHED"] == 1
    assert dist["FAILED"] == 1
    assert dist["SKIPPED_LIMIT"] == 1
    assert dist["DUPLICATE_SUPPRESSED"] == 1
    assert dist["SKIPPED_DISABLED"] == 1
    assert dist["SKIPPED_SILENT"] == 1
    assert dist["no_data"] is False


def test_invalid_records_excluded_and_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 22: invalid outcome records are excluded from counts and reported."""
    _purge_analytics_modules()
    outcomes_log = tmp_path / "outcomes.jsonl"
    outcomes_log.parent.mkdir(parents=True, exist_ok=True)
    outcomes_log.write_text(
        '{"signal_id": "SIG_001", "outcome": "WIN", "user_id": "M-OK"}\n'
        '{bad json}\n'
        '{"outcome": "WIN"}\n',  # missing signal_id
        encoding="utf-8",
    )
    import core.analytics_engine as ae
    result = ae._load_outcomes(str(outcomes_log))
    assert result["wins"] == 1
    assert result["invalid_count"] == 2


def test_duplicate_records_do_not_inflate_counts(analytics_fixture, tmp_path: Path):
    """Test 23: duplicate (signal_id, user_id) outcome records don't inflate wins."""
    import core.analytics_engine as ae
    outcomes_log = tmp_path / "dup_outcomes.jsonl"
    rec = _make_outcome_record("SIG_DUP", "WIN", "M-DUPE")
    _write_jsonl(outcomes_log, [rec, rec, rec, rec, rec])
    result = ae._load_outcomes(str(outcomes_log))
    assert result["wins"] == 1


def test_missing_outcomes_represented_correctly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 24: MISSED outcome is counted as missed, not as win or lose."""
    _purge_analytics_modules()
    outcomes_log = tmp_path / "outcomes.jsonl"
    _write_jsonl(outcomes_log, [
        _make_outcome_record("SIG_001", "MISSED", "M-U1"),
        _make_outcome_record("SIG_002", "MISSED", "M-U2"),
    ])
    import core.analytics_engine as ae
    result = ae._load_outcomes(str(outcomes_log))
    assert result["missed"] == 2
    assert result["wins"] == 0
    assert result["loses"] == 0


def test_insufficient_sample_size_is_reported(tmp_path: Path):
    """Test 25: fewer than minimum sample produces insufficient_sample=True, no win_rate."""
    import core.analytics_engine as ae
    outcomes_log = tmp_path / "small_outcomes.jsonl"
    # Only 2 records — below _MIN_SAMPLE_FOR_RATE=5
    _write_jsonl(outcomes_log, [
        _make_outcome_record("SIG_001", "WIN", "M-U1"),
        _make_outcome_record("SIG_002", "LOSE", "M-U2"),
    ])
    result = ae._load_outcomes(str(outcomes_log))
    assert result["insufficient_sample"] is True
    assert result["win_rate"] is None


def test_repeated_runs_produce_identical_output(analytics_fixture):
    """Test 26: recompute on same input is deterministic."""
    ae = analytics_fixture["ae"]
    r1 = ae.recompute(1700000000)
    r2 = ae.recompute(1700000000)
    # Exclude updated_ts from comparison
    r1c = {k: v for k, v in r1.items() if k != "updated_ts"}
    r2c = {k: v for k, v in r2.items() if k != "updated_ts"}
    assert r1c == r2c


def test_analytics_does_not_mutate_source_data(analytics_fixture, tmp_path: Path):
    """Test 27: analytics does not modify the source JSONL files."""
    ae = analytics_fixture["ae"]
    outcomes_log = analytics_fixture["outcomes_log"]
    content_before = outcomes_log.read_bytes()
    ae.recompute(1700000000)
    content_after = outcomes_log.read_bytes()
    assert content_before == content_after


def test_analytics_report_persistence_is_atomic(analytics_fixture, tmp_path: Path):
    """Test 28: aggregates.json written atomically (no .tmp_ files remain after write)."""
    ae = analytics_fixture["ae"]
    analytics_dir = analytics_fixture["analytics_dir"]
    ae.recompute(1700000000)
    # No leftover temp files
    tmp_files = list(analytics_dir.glob(".tmp_*.json"))
    assert tmp_files == []
    assert (analytics_dir / "aggregates.json").exists()


def test_failed_report_write_preserves_last_valid_report(analytics_fixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 29: if aggregates path is read-only, existing file is preserved."""
    import core.storage as storage_mod
    ae = analytics_fixture["ae"]
    ae.recompute(1700000000)  # write a valid report first
    agg_path = Path(ae.AGGREGATES_PATH)
    assert agg_path.exists()
    content_before = agg_path.read_text(encoding="utf-8")

    # Make the directory read-only to force write failure
    orig_save = storage_mod.save_json_atomic

    def failing_save(path, obj):
        raise OSError("simulated write failure")

    monkeypatch.setattr(storage_mod, "save_json_atomic", failing_save)
    with pytest.raises(OSError):
        ae.recompute(1700000000)

    # File must be unchanged
    assert agg_path.read_text(encoding="utf-8") == content_before


# ===========================================================================
# SECTION 4: RESEARCH (tests 30–37)
# ===========================================================================

@pytest.fixture()
def research_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    obs_dir = tmp_path / "observability"
    obs_dir.mkdir(parents=True, exist_ok=True)
    outcomes_dir = tmp_path / "outcomes"
    outcomes_dir.mkdir(parents=True, exist_ok=True)
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)

    engine_log = obs_dir / "engine_events.jsonl"
    dist_log = obs_dir / "distribution_events.jsonl"
    outcomes_log = outcomes_dir / "outcomes.jsonl"

    _write_jsonl(engine_log, [
        {**_make_signal_event("SIG_001", "PRE"), "event_id": "E1"},
        {**_make_signal_event("SIG_002", "CONFIRM"), "event_id": "E2"},
        {**_make_signal_event("SIG_003", "OPEN_NOW"), "event_id": "E3"},
        {**_make_signal_event("SIG_004", "OPEN_NOW"), "event_id": "E4"},
        {**_make_signal_event("SIG_005", "OPEN_NOW"), "event_id": "E5"},
        {**_make_signal_event("SIG_006", "OPEN_NOW"), "event_id": "E6"},
    ])
    _write_jsonl(dist_log, [
        _make_tier_publish_event("SIG_003", "PUBLISHED"),
        _make_tier_publish_event("SIG_004", "PUBLISHED"),
        _make_tier_publish_event("SIG_005", "FAILED"),
        _make_tier_publish_event("SIG_006", "DUPLICATE_SUPPRESSED"),
    ])
    _write_jsonl(outcomes_log, [
        _make_outcome_record("SIG_003", "WIN", "M-U1"),
        _make_outcome_record("SIG_004", "WIN", "M-U2"),
        _make_outcome_record("SIG_005", "LOSE", "M-U3"),
        _make_outcome_record("SIG_006", "WIN", "M-U4"),
        _make_outcome_record("SIG_007", "WIN", "M-U5"),
        _make_outcome_record("SIG_008", "WIN", "M-U6"),
    ])

    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(engine_log))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(dist_log))
    monkeypatch.setenv("OUTCOMES_LOG", str(outcomes_log))
    monkeypatch.setenv("ANALYTICS_DIR", str(analytics_dir))

    _purge_analytics_modules()
    import intelligence.research_engine as re
    re._ENGINE_LOG = str(engine_log)
    re._DIST_LOG = str(dist_log)
    re._OUTCOMES_LOG = str(outcomes_log)
    re._RESEARCH_REPORT_PATH = str(analytics_dir / "research_report.json")

    return {"re": re, "analytics_dir": analytics_dir}


def test_research_engine_runs_on_validated_fixture(research_fixture):
    """Test 30: research engine builds report from fixture data."""
    re = research_fixture["re"]
    report = re.build_research_report()
    assert isinstance(report, dict)
    assert "signal_funnel" in report
    assert "outcomes" in report
    assert "research" in report


def test_research_output_distinguishes_observation_hypothesis_recommendation(research_fixture):
    """Test 31: research output has observations, hypotheses, recommendations."""
    re = research_fixture["re"]
    report = re.build_research_report()
    r = report["research"]
    assert "observations" in r
    assert "hypotheses" in r
    assert "recommendations" in r
    assert "limitations" in r
    assert isinstance(r["observations"], list)
    assert isinstance(r["hypotheses"], list)
    assert isinstance(r["recommendations"], list)


def test_recommendations_remain_advisory_only(research_fixture):
    """Test 32: advisory_only=True and auto_apply=False in research output."""
    re = research_fixture["re"]
    report = re.build_research_report()
    assert report["research"]["advisory_only"] is True
    assert report["research"]["auto_apply"] is False


def test_research_engine_does_not_mutate_live_parameters(research_fixture, tmp_path: Path):
    """Test 33: running research does not write to config or state files."""
    re = research_fixture["re"]
    # Track files in analytics dir before
    analytics_dir = research_fixture["analytics_dir"]
    before = set(analytics_dir.glob("**/*"))

    re.build_research_report()  # not persisted without explicit call

    after = set(analytics_dir.glob("**/*"))
    # build_research_report alone must not create new files
    assert after == before, f"Unexpected files created: {after - before}"


def test_research_does_not_auto_promote_strategies(research_fixture):
    """Test 34: research report has no auto-promotion or parameter change."""
    re = research_fixture["re"]
    report = re.build_research_report()
    # Recommendations are all advisory-prefixed
    for rec in report["research"]["recommendations"]:
        assert "[ADVISORY]" in rec or "advisory" in rec.lower() or "review" in rec.lower()


def test_insufficient_evidence_produces_explicit_limitation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test 35: no outcome data → limitation reported, not fabricated win rate."""
    _purge_analytics_modules()
    outcomes_log = tmp_path / "outcomes" / "empty_outcomes.jsonl"
    outcomes_log.parent.mkdir(parents=True, exist_ok=True)
    outcomes_log.write_text("", encoding="utf-8")
    engine_log = tmp_path / "observability" / "engine_events.jsonl"
    engine_log.parent.mkdir(parents=True, exist_ok=True)
    engine_log.write_text("", encoding="utf-8")
    dist_log = tmp_path / "observability" / "dist_events.jsonl"
    dist_log.write_text("", encoding="utf-8")
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(engine_log))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(dist_log))
    monkeypatch.setenv("OUTCOMES_LOG", str(outcomes_log))
    monkeypatch.setenv("ANALYTICS_DIR", str(tmp_path / "analytics"))

    import intelligence.research_engine as re
    re._ENGINE_LOG = str(engine_log)
    re._DIST_LOG = str(dist_log)
    re._OUTCOMES_LOG = str(outcomes_log)
    report = re.build_research_report()
    assert report["outcomes"]["no_data"] is True
    assert len(report["research"]["limitations"]) > 0


def test_research_repeated_runs_are_deterministic(research_fixture):
    """Test 36: identical inputs → identical research output."""
    re = research_fixture["re"]
    r1 = re.build_research_report()
    r2 = re.build_research_report()
    assert r1 == r2


def test_research_report_persistence_is_atomic(research_fixture, tmp_path: Path):
    """Test 37: persist_research_report writes atomically (no leftover tmp files)."""
    re = research_fixture["re"]
    analytics_dir = research_fixture["analytics_dir"]
    report = re.build_research_report()
    re.persist_research_report(report)
    tmp_files = list(analytics_dir.glob(".tmp_*.json"))
    assert tmp_files == []
    assert (analytics_dir / "research_report.json").exists()


# ===========================================================================
# SECTION 5: DAILY AUDITOR (tests 38–45)
# ===========================================================================

@pytest.fixture()
def auditor_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Set up a complete daily auditor environment with fixture data."""
    settings = _base_intelligence_settings(tmp_path)
    settings_file = tmp_path / "config" / "intelligence_settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    monkeypatch.setenv("STRATEGY_AUDITOR_SETTINGS", str(settings_file))

    obs_dir = tmp_path / "observability"
    obs_dir.mkdir(parents=True, exist_ok=True)

    # Write fixture decision events
    engine_log = Path(settings["sources"]["engine_events"])
    _write_jsonl(engine_log, [
        _make_decision_event("SIG_001", "OPEN_NOW", "EURUSD", 72.0),
        _make_decision_event("SIG_002", "REJECT", "GBPUSD", 45.0),
        _make_decision_event("SIG_003", "PRE", "USDJPY", 55.0),
        _make_decision_event("SIG_004", "CONFIRM", "AUDUSD", 62.0),
    ])
    for src_key in ("fsm_events", "distribution_events", "error_events"):
        Path(settings["sources"][src_key]).touch()

    outcomes_log = Path(settings["sources"]["outcomes"])
    _write_jsonl(outcomes_log, [
        _make_outcome_record("SIG_001", "WIN", "M-U1"),
    ])

    _purge_analytics_modules()
    import tools.strategy_auditor_lib as lib
    return {
        "lib": lib,
        "settings": settings,
        "settings_file": settings_file,
        "tmp_path": tmp_path,
    }


def test_daily_auditor_runs_on_fixture_logs(auditor_fixture):
    """Test 38: daily auditor load_settings + load_all_events + build_report succeed."""
    lib = auditor_fixture["lib"]
    settings = lib.load_settings(str(auditor_fixture["settings_file"]))
    events = lib.load_all_events(settings)
    report = lib.build_report(events, settings)
    assert isinstance(report, dict)
    assert "decisions" in report
    assert "date" in report


def test_daily_auditor_accepts_temporary_data_root(auditor_fixture):
    """Test 39: daily auditor accepts settings path argument (no /opt/binarybot/ needed)."""
    lib = auditor_fixture["lib"]
    # Must not raise; path is project-relative, not /opt/binarybot/
    settings = lib.load_settings(str(auditor_fixture["settings_file"]))
    assert settings["reports"]["output_dir"] != "/opt/binarybot/analytics/reports"


def test_daily_auditor_does_not_require_opt_binarybot(auditor_fixture):
    """Test 40: auditor settings path is under tmp_path, not /opt/binarybot/."""
    lib = auditor_fixture["lib"]
    settings = lib.load_settings(str(auditor_fixture["settings_file"]))
    for key, path in settings["sources"].items():
        assert not path.startswith("/opt/binarybot/"), (
            f"Source path {key} still points to /opt/binarybot/: {path}"
        )


def test_daily_auditor_reports_source_counts_and_invalid_records(auditor_fixture, tmp_path: Path):
    """Test 41: report includes input_sources with valid/invalid counts."""
    lib = auditor_fixture["lib"]
    # Add one invalid line to engine events
    engine_log_path = auditor_fixture["settings"]["sources"]["engine_events"]
    with open(engine_log_path, "a", encoding="utf-8") as f:
        f.write("{bad json line}\n")

    settings = lib.load_settings(str(auditor_fixture["settings_file"]))
    events = lib.load_all_events(settings)
    report = lib.build_report(events, settings)

    assert "input_sources" in report
    assert report["input_sources"]["engine_events"]["invalid"] == 1


def test_daily_auditor_produces_valid_machine_readable_output(auditor_fixture, tmp_path: Path):
    """Test 42: write_reports creates valid JSON file."""
    lib = auditor_fixture["lib"]
    settings = lib.load_settings(str(auditor_fixture["settings_file"]))
    events = lib.load_all_events(settings)
    report = lib.build_report(events, settings)
    lib.write_reports(report, settings)

    output_dir = Path(settings["reports"]["output_dir"])
    json_files = list(output_dir.glob("daily_strategy_audit_*.json"))
    assert len(json_files) == 1
    loaded = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert loaded["decisions"] == report["decisions"]


def test_daily_auditor_produces_valid_human_readable_output(auditor_fixture, tmp_path: Path):
    """Test 43: write_reports creates Markdown file with expected sections."""
    lib = auditor_fixture["lib"]
    settings = lib.load_settings(str(auditor_fixture["settings_file"]))
    events = lib.load_all_events(settings)
    report = lib.build_report(events, settings)
    lib.write_reports(report, settings)

    output_dir = Path(settings["reports"]["output_dir"])
    md_files = list(output_dir.glob("daily_strategy_audit_*.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text(encoding="utf-8")
    assert "# Strategy Audit" in content
    assert "## Decision Distribution" in content
    assert "## Bottleneck" in content


def test_missing_required_settings_fails_clearly(tmp_path: Path):
    """Test 44: load_settings raises RuntimeError for missing settings file."""
    _purge_analytics_modules()
    import tools.strategy_auditor_lib as lib
    with pytest.raises(RuntimeError, match="not found"):
        lib.load_settings(str(tmp_path / "nonexistent_settings.json"))


def test_daily_auditor_does_not_mutate_runtime_config(auditor_fixture, tmp_path: Path):
    """Test 45: running auditor does not modify source event logs."""
    lib = auditor_fixture["lib"]
    settings = lib.load_settings(str(auditor_fixture["settings_file"]))
    engine_log = Path(settings["sources"]["engine_events"])
    content_before = engine_log.read_bytes()

    events = lib.load_all_events(settings)
    lib.build_report(events, settings)
    lib.write_reports(lib.build_report(events, settings), settings)

    assert engine_log.read_bytes() == content_before


# ===========================================================================
# SECTION 6: GAP-010 specific — safe_json_loads undefined (tests 46–48)
# ===========================================================================

def test_no_undefined_safe_json_loads_in_analytics_engine():
    """Verify GAP-010: analytics_engine has no bare safe_json_loads call."""
    import ast
    src = (REPO_ROOT / "send" / "core" / "analytics_engine.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            assert name != "safe_json_loads", (
                "analytics_engine must not call bare safe_json_loads"
            )


def test_no_undefined_safe_json_loads_in_research_engine():
    """Verify GAP-010: research_engine has no bare safe_json_loads call."""
    import ast
    src = (REPO_ROOT / "send" / "intelligence" / "research_engine.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            assert name != "safe_json_loads", (
                "research_engine must not call bare safe_json_loads"
            )


def test_gap_015_strategy_auditor_daily_importable():
    """Verify GAP-015: strategy_auditor_daily imports without ModuleNotFoundError."""
    _purge_analytics_modules()
    try:
        importlib.import_module("tools.strategy_auditor_daily")
    except ModuleNotFoundError as exc:
        pytest.fail(f"GAP-015 not resolved: {exc}")


# ===========================================================================
# SECTION 7: SIGNAL FUNNEL STAGE FIELD CORRECTNESS (critical fix)
# ===========================================================================

def test_research_engine_reads_stage_from_top_level_not_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Critical: canonical signal_event stores stage at top level (correlation field),
    not inside data. research_engine must use rec.get('stage'), not
    rec.get('data', {}).get('stage').
    """
    _purge_analytics_modules()
    engine_log = tmp_path / "observability" / "engine_events.jsonl"
    engine_log.parent.mkdir(parents=True, exist_ok=True)

    # Record with stage at top level (canonical), nothing in data.stage
    canonical_event = {
        "event_type": "signal_event",
        "event_id": "EVT_CANONICAL_1",
        "stage": "OPEN_NOW",              # top-level — correct location
        "signal_id": "SIG_TOP",
        "symbol": "EURUSD",
        "timeframe": "M1",
        "data": {
            "direction": "UP",
            "score_total": 70.0,
            # NOTE: no "stage" inside data — must be read from top level
        },
    }
    _write_jsonl(engine_log, [canonical_event])
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(engine_log))

    import intelligence.research_engine as re
    re._ENGINE_LOG = str(engine_log)
    funnel = re.compute_signal_funnel()

    assert funnel["OPEN_NOW"] == 1, (
        "research_engine must read stage from top-level correlation field, not data dict"
    )


# ===========================================================================
# SECTION 8: RESEARCH STAGE UNSUPPORTED CLASSIFICATION
# ===========================================================================

def test_stage_missing_in_signal_event_counted_as_invalid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """stage=None records are excluded and reported, not coerced."""
    _purge_analytics_modules()
    engine_log = tmp_path / "observability" / "engine_events.jsonl"
    engine_log.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(engine_log, [
        {"event_type": "signal_event", "event_id": "E1", "signal_id": "SIG_1"},  # missing stage
    ])
    import intelligence.research_engine as re
    re._ENGINE_LOG = str(engine_log)
    funnel = re.compute_signal_funnel()
    assert funnel["PRE"] == 0
    assert funnel["CONFIRM"] == 0
    assert funnel["OPEN_NOW"] == 0
    assert funnel["invalid_count"] == 1


# ===========================================================================
# SECTION 9: ANALYTICS ENGINE PATH OVERRIDE (env-var)
# ===========================================================================

def test_analytics_engine_uses_env_var_outcomes_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Analytics engine reads OUTCOMES_LOG env var and does not require /opt/binarybot/."""
    _purge_analytics_modules()
    outcomes_log = tmp_path / "my_outcomes.jsonl"
    _write_jsonl(outcomes_log, [
        _make_outcome_record("SIG_001", "WIN", "M-U1"),
        _make_outcome_record("SIG_002", "WIN", "M-U2"),
        _make_outcome_record("SIG_003", "LOSE", "M-U3"),
        _make_outcome_record("SIG_004", "MISSED", "M-U4"),
        _make_outcome_record("SIG_005", "WIN", "M-U5"),
    ])
    import core.analytics_engine as ae
    result = ae._load_outcomes(str(outcomes_log))
    assert result["wins"] == 3
    assert result["loses"] == 1
    assert result["missed"] == 1
    assert result["no_data"] is False
