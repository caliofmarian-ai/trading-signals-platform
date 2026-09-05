from __future__ import annotations

import datetime as dt
import builtins
import hashlib
import importlib
import json
import multiprocessing
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"


def _purge() -> None:
    for name in list(sys.modules):
        if name in {
            "tools.strategy_auditor_lib",
            "tools.strategy_auditor_runtime",
            "tools.strategy_auditor_daily",
            "intelligence.report_loader",
            "runtime.runtime_status",
            "runtime.system_boot",
        }:
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _settings_payload(
    root: Path,
    *,
    reports_enabled: bool = True,
    write_json: bool = True,
    write_markdown: bool = True,
    reports_output: str = "analytics/reports",
    cache_dir: str = "analytics/cache",
    source_overrides: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    sources = {
        "engine_events": "observability/engine_events.jsonl",
        "fsm_events": "observability/fsm_events.jsonl",
        "distribution_events": "observability/distribution_events.jsonl",
        "error_events": "observability/error_events.jsonl",
        "outcomes": "outcomes/outcomes.jsonl",
    }
    if source_overrides:
        sources.update(source_overrides)
    return {
        "reports": {
            "enabled": reports_enabled,
            "output_dir": reports_output,
            "cache_dir": cache_dir,
            "write_json": write_json,
            "write_markdown": write_markdown,
        },
        "sources": sources,
        "heatmap": {
            "enabled": True,
            "score_buckets": [[50, 55], [55, 60], [60, 65], [65, 70], [70, 75], [75, 80], [80, 100]],
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
        "report_defaults": {
            "timezone": "UTC",
            "top_n_rejects": 10,
            "top_n_symbols": 10,
        },
    }


def _configure_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    reports_enabled: bool = True,
    write_json: bool = True,
    write_markdown: bool = True,
    reports_output: str = "analytics/reports",
    cache_dir: str = "analytics/cache",
    source_overrides: Dict[str, str] | None = None,
    admin_enabled: bool = True,
) -> Path:
    root = tmp_path / "runtime"
    for directory in ("config", "observability", "outcomes", "analytics", "state"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    settings = _settings_payload(
        root,
        reports_enabled=reports_enabled,
        write_json=write_json,
        write_markdown=write_markdown,
        reports_output=reports_output,
        cache_dir=cache_dir,
        source_overrides=source_overrides,
    )
    (root / "config" / "intelligence_settings.json").write_text(json.dumps(settings), encoding="utf-8")
    (root / "config" / "admin_settings.json").write_text(
        json.dumps({"feature_flags": {"strategy_auditor_enabled": admin_enabled}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("STRATEGY_AUDITOR_SETTINGS", str(root / "config" / "intelligence_settings.json"))
    for key in (
        "ANALYTICS_DIR",
        "OBS_DIR",
        "ENGINE_EVENTS_LOG",
        "FSM_EVENTS_LOG",
        "DIST_EVENTS_LOG",
        "ERROR_EVENTS_LOG",
        "OUTCOMES_LOG",
        "STRATEGY_AUDITOR_ENABLED",
        "STRATEGY_AUDITOR_DAILY_TIME_UTC",
        "RAILWAY_DEPLOYMENT_ID",
    ):
        monkeypatch.delenv(key, raising=False)
    return root


def _decision(event_id: str = "evt-1", kind: str = "PRE") -> Dict[str, Any]:
    return {
        "event_type": "decision",
        "event_id": event_id,
        "schema_version": "3.0.0",
        "symbol": "EURUSD",
        "timeframe": "M1",
        "data": {
            "decision_kind": kind,
            "symbol": "EURUSD",
            "score_total": 61.0,
            "candle_ts": 1,
        },
    }


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(row if isinstance(row, str) else json.dumps(row))
            handle.write("\n")


def _write_sources(root: Path, *, invalid: bool = False) -> None:
    _write_jsonl(root / "observability" / "engine_events.jsonl", [_decision(), "{bad json}"] if invalid else [_decision()])
    for rel in (
        "observability/fsm_events.jsonl",
        "observability/distribution_events.jsonl",
        "observability/error_events.jsonl",
        "outcomes/outcomes.jsonl",
    ):
        _write_jsonl(root / rel, [])


def _hash_sources(root: Path) -> Dict[str, str]:
    paths = {
        "engine": root / "observability" / "engine_events.jsonl",
        "fsm": root / "observability" / "fsm_events.jsonl",
        "distribution": root / "observability" / "distribution_events.jsonl",
        "errors": root / "observability" / "error_events.jsonl",
        "outcomes": root / "outcomes" / "outcomes.jsonl",
    }
    return {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()}


def _hold_lock_process(base_dir: str, ready: multiprocessing.Event, release: multiprocessing.Event) -> None:
    os.environ["BINARYBOT_BASE_DIR"] = base_dir
    sys.path.insert(0, str(SEND_ROOT))
    from tools import strategy_auditor_runtime as runtime

    with runtime._auditor_transaction_lock():
        ready.set()
        release.wait(5)


def test_settings_precedence_relative_paths_and_individual_source_env_without_obs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    custom_engine = root / "custom" / "engine.jsonl"
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(custom_engine))
    monkeypatch.delenv("OBS_DIR", raising=False)
    _purge()

    from tools import strategy_auditor_lib as lib

    loaded = lib.load_settings()
    assert loaded["reports"]["output_dir"] == str(root / "analytics" / "reports")
    assert loaded["sources"]["engine_events"] == str(custom_engine)
    assert loaded["sources"]["fsm_events"] == str(root / "observability" / "fsm_events.jsonl")

    explicit = root / "config" / "explicit_intelligence.json"
    explicit.write_text(
        json.dumps(_settings_payload(root, reports_output="explicit/reports")),
        encoding="utf-8",
    )
    assert lib.load_settings(str(explicit))["reports"]["output_dir"] == str(root / "explicit" / "reports")


def test_path_overrides_reject_relative_env_traversal_and_do_not_remap_explicit_opt_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _purge()
    from tools import strategy_auditor_lib as lib

    monkeypatch.setenv("ANALYTICS_DIR", "relative/analytics")
    with pytest.raises(lib.StrategyAuditorSettingsError, match="absolute"):
        lib.load_settings()

    monkeypatch.setenv("ANALYTICS_DIR", str(root / "analytics"))
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(root / "observability" / ".." / "state" / "source.jsonl"))
    with pytest.raises(lib.StrategyAuditorSettingsError, match="traversal"):
        lib.load_settings()

    monkeypatch.delenv("ENGINE_EVENTS_LOG", raising=False)
    monkeypatch.setenv("ANALYTICS_DIR", "/opt/binarybot/analytics")
    monkeypatch.setenv("ENGINE_EVENTS_LOG", "/opt/binarybot/observability/engine_events.jsonl")
    settings = lib.load_settings()
    assert settings["reports"]["output_dir"] == "/opt/binarybot/analytics/reports"
    assert settings["sources"]["engine_events"] == "/opt/binarybot/observability/engine_events.jsonl"


def test_relative_binarybot_base_dir_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    monkeypatch.setenv("BINARYBOT_BASE_DIR", "relative-runtime")
    _purge()
    from tools import strategy_auditor_lib as lib

    with pytest.raises(Exception, match="BINARYBOT_BASE_DIR"):
        lib.load_settings(str(root / "config" / "intelligence_settings.json"))


def test_legacy_opt_binarybot_settings_are_mapped_to_runtime_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    payload = _settings_payload(
        root,
        reports_output="/opt/binarybot/analytics/reports",
        cache_dir="/opt/binarybot/analytics/cache",
        source_overrides={
            "engine_events": "/opt/binarybot/observability/engine_events.jsonl",
            "outcomes": "/opt/binarybot/outcomes/outcomes.jsonl",
        },
    )
    (root / "config" / "intelligence_settings.json").write_text(json.dumps(payload), encoding="utf-8")
    _purge()
    from tools import strategy_auditor_lib as lib

    settings = lib.load_settings()
    assert settings["reports"]["output_dir"] == str(root / "analytics" / "reports")
    assert settings["sources"]["engine_events"] == str(root / "observability" / "engine_events.jsonl")
    assert settings["sources"]["outcomes"] == str(root / "outcomes" / "outcomes.jsonl")
    assert "/opt/binarybot" not in json.dumps(settings)


def test_resolve_reports_dir_and_consumers_fail_unavailable_on_explicit_bad_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    fallback_reports = root / "analytics" / "reports"
    fallback_reports.mkdir(parents=True)
    (fallback_reports / "daily_strategy_audit_2026-09-04.json").write_text('{"date":"wrong"}\n', encoding="utf-8")
    bad_settings = root / "config" / "bad_intelligence.json"
    bad_settings.write_text("{bad json", encoding="utf-8")
    monkeypatch.setenv("STRATEGY_AUDITOR_SETTINGS", str(bad_settings))
    _purge()
    from core import admin_commands
    from intelligence import report_loader
    from tools import strategy_auditor_lib as lib

    with pytest.raises(lib.StrategyAuditorSettingsError):
        lib.resolve_reports_dir()
    assert report_loader.list_reports() == []
    assert report_loader.load_latest_report() is None
    assert admin_commands._find_latest_report_json() is None


def test_write_reports_success_and_loader_match_same_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root, invalid=True)
    _purge()
    from intelligence import report_loader
    from tools import strategy_auditor_lib as lib

    settings = lib.load_settings()
    events = lib.load_all_events(settings)
    report = lib.build_report(
        events,
        settings,
        report_date="2026-09-05",
        scheduling_metadata={"mode": "scheduled", "attempt_id": "attempt-1"},
        analysis_window={"scope": "all_available_history"},
    )
    paths = lib.write_reports(report, settings)

    assert set(paths) == {"json", "markdown"}
    assert json.loads(Path(paths["json"]).read_text(encoding="utf-8"))["input_sources"]["engine_events"]["invalid"] == 1
    assert "analysis_window.scope=all_available_history" in json.loads(Path(paths["json"]).read_text(encoding="utf-8"))["limitations"][-1]
    assert report_loader.load_latest_report()["date"] == "2026-09-05"
    assert "## Scheduling" in Path(paths["markdown"]).read_text(encoding="utf-8")


def test_write_reports_requires_output_and_preserves_existing_artifacts_on_stage_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_lib as lib

    settings = lib.load_settings()
    report = lib.build_report(lib.load_all_events(settings), settings, report_date="2026-09-05")
    paths = lib.write_reports(report, settings)
    original_json = Path(paths["json"]).read_bytes()
    original_md = Path(paths["markdown"]).read_bytes()

    disabled = dict(settings)
    disabled["reports"] = dict(settings["reports"])
    disabled["reports"]["write_json"] = False
    disabled["reports"]["write_markdown"] = False
    with pytest.raises(lib.StrategyAuditorSettingsError):
        lib.write_reports(report, disabled)

    real_stage = lib._stage_atomic_bytes

    def fail_markdown(path: str, data: bytes) -> str:
        if path.endswith(".md"):
            raise OSError("synthetic markdown stage failure")
        return real_stage(path, data)

    monkeypatch.setattr(lib, "_stage_atomic_bytes", fail_markdown)
    with pytest.raises(OSError):
        lib.write_reports(report, settings)
    assert Path(paths["json"]).read_bytes() == original_json
    assert Path(paths["markdown"]).read_bytes() == original_md
    assert list((root / "analytics" / "reports").glob(".tmp_*")) == []

    def fail_json(path: str, data: bytes) -> str:
        if path.endswith(".json"):
            raise OSError("synthetic json stage failure")
        return real_stage(path, data)

    monkeypatch.setattr(lib, "_stage_atomic_bytes", fail_json)
    with pytest.raises(OSError):
        lib.write_reports(report, settings)
    assert Path(paths["json"]).read_bytes() == original_json
    assert Path(paths["markdown"]).read_bytes() == original_md
    assert list((root / "analytics" / "reports").glob(".tmp_*")) == []

    monkeypatch.setattr(lib, "_stage_atomic_bytes", real_stage)
    real_replace = lib._replace_staged_artifact

    def fail_markdown_replace(tmp_path: str, final_path: str) -> None:
        if final_path.endswith(".md"):
            raise OSError("synthetic markdown replace failure")
        real_replace(tmp_path, final_path)

    monkeypatch.setattr(lib, "_replace_staged_artifact", fail_markdown_replace)
    with pytest.raises(OSError):
        lib.write_reports(report, settings)
    assert Path(paths["json"]).read_bytes() == original_json
    assert Path(paths["markdown"]).read_bytes() == original_md
    assert list((root / "analytics" / "reports").glob(".tmp_*")) == []

    def fail_json_replace(tmp_path: str, final_path: str) -> None:
        if final_path.endswith(".json"):
            raise OSError("synthetic json replace failure")
        real_replace(tmp_path, final_path)

    monkeypatch.setattr(lib, "_replace_staged_artifact", fail_json_replace)
    with pytest.raises(OSError):
        lib.write_reports(report, settings)
    assert Path(paths["json"]).read_bytes() == original_json
    assert Path(paths["markdown"]).read_bytes() == original_md
    assert list((root / "analytics" / "reports").glob(".tmp_*")) == []


def test_run_auditor_success_idempotency_state_and_source_immutability(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    before = _hash_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    now = dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC)
    first = runtime.run_auditor(mode="manual", now=now)
    second = runtime.run_auditor(mode="manual", now=now + dt.timedelta(minutes=10))
    _purge()
    from tools import strategy_auditor_runtime as restarted_runtime

    after_restart = restarted_runtime.run_auditor(mode="manual", now=now + dt.timedelta(minutes=20))

    assert first["status"] == "SUCCESS"
    assert first["report_period"] == "2026-09-05"
    assert second["status"] == "ALREADY_COMPLETED"
    assert after_restart["status"] == "ALREADY_COMPLETED"
    assert _hash_sources(root) == before
    state = json.loads((root / "state" / "strategy_auditor_state.json").read_text(encoding="utf-8"))
    assert state["periods"]["2026-09-05"]["completed"] is True


def test_runtime_requires_both_outputs_for_shared_period_completion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch, write_markdown=False)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert result["status"] == "CONFIGURATION_ERROR"
    assert not (root / "state" / "strategy_auditor_state.json").exists()
    assert not list((root / "analytics").glob("reports/daily_strategy_audit_*"))


def test_reports_enabled_false_disables_run_and_worker_without_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch, reports_enabled=False)
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "09:00")
    _purge()
    from tools import strategy_auditor_lib as lib
    from tools import strategy_auditor_runtime as runtime

    settings = lib.load_settings()
    report = lib.build_report(lib.load_all_events(settings), settings, report_date="2026-09-05")
    with pytest.raises(lib.StrategyAuditorSettingsError, match="disabled"):
        lib.write_reports(report, settings)

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC))
    worker = runtime.start_worker()

    assert result["status"] == "DISABLED_BY_REPORTS_SETTING"
    assert worker["status"] == "DISABLED_BY_REPORTS_SETTING"
    assert worker["worker_started"] is False
    assert not (root / "state" / "strategy_auditor_state.json").exists()
    assert not list((root / "analytics").glob("reports/daily_strategy_audit_*"))


def test_naive_clock_rejected_without_completion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 22, 0))
    assert result["status"] == "INVALID_CLOCK"
    assert not (root / "state" / "strategy_auditor_state.json").exists()


def test_scheduled_once_requires_explicit_schedule_and_uses_current_utc_date_at_2359(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    _purge()
    from tools import strategy_auditor_runtime as runtime

    missing = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 3, 29, 8, 10, tzinfo=dt.UTC))
    assert missing["status"] == "SCHEDULE_NOT_CONFIGURED"

    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "23:59")
    not_due = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 3, 29, 23, 58, tzinfo=dt.UTC))
    due = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 3, 29, 23, 59, tzinfo=dt.UTC))

    assert not_due["status"] == "NOT_DUE"
    assert due["status"] == "SUCCESS"
    assert due["report_period"] == "2026-03-29"
    assert due["schedule_identity"]["configured_time_utc"] == "23:59"
    report = json.loads(Path(due["report_paths"]["json"]).read_text(encoding="utf-8"))
    assert report["date"] == "2026-03-29"
    assert report["scheduling"]["mode"] == "scheduled"
    assert report["analysis_window"]["scope"] == "all_available_history"
    assert "08:10" not in json.dumps(report)

    next_day = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 3, 30, 23, 59, tzinfo=dt.UTC))
    assert next_day["status"] == "SUCCESS"
    assert next_day["report_period"] == "2026-03-30"
    next_report = json.loads(Path(next_day["report_paths"]["json"]).read_text(encoding="utf-8"))
    assert next_report["date"] == "2026-03-30"


def test_schedule_is_strict_ascii_hh_mm_and_invalid_value_not_echoed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    _purge()
    from tools import strategy_auditor_runtime as runtime

    for bad in ("9:01", "09:1", "09:01:00", "２3:59", "SECRET=abc"):
        monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", bad)
        result = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 9, 5, 10, 0, tzinfo=dt.UTC))
        assert result["status"] == "INVALID_SCHEDULE"
        assert bad not in json.dumps(result)
        assert result["schedule_identity"]["configured_time_utc"] is None


def test_aware_non_utc_instant_uses_utc_period_independent_of_host_tz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    old_tz = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "America/Los_Angeles")
    if hasattr(time, "tzset"):
        time.tzset()
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "00:30")
    try:
        _purge()
        from tools import strategy_auditor_runtime as runtime

        same_instant_london_dst = dt.datetime(
            2026,
            3,
            29,
            1,
            30,
            tzinfo=dt.timezone(dt.timedelta(hours=1)),
        )
        result = runtime.evaluate_scheduled_once(now=same_instant_london_dst)
        assert result["status"] == "SUCCESS"
        assert result["report_period"] == "2026-03-29"
        assert result["started_at"] == "2026-03-29T00:30:00Z"
        report = json.loads(Path(result["report_paths"]["json"]).read_text(encoding="utf-8"))
        assert report["date"] == "2026-03-29"
        assert report["scheduling"]["started_at"] == "2026-03-29T00:30:00Z"
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        if hasattr(time, "tzset"):
            time.tzset()


def test_invalid_schedule_and_admin_setting_veto_are_noncritical(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch, admin_enabled=False)
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "25:00")
    _purge()
    from tools import strategy_auditor_runtime as runtime

    invalid = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert invalid["status"] == "DISABLED_BY_ADMIN_SETTING"

    (root / "config" / "admin_settings.json").write_text(
        json.dumps({"feature_flags": {"strategy_auditor_enabled": True}}),
        encoding="utf-8",
    )
    invalid_schedule = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert invalid_schedule["status"] == "INVALID_SCHEDULE"


def test_corrupt_state_fails_closed_preserving_bytes_and_reports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    corrupt = root / "state" / "strategy_auditor_state.json"
    corrupt.write_bytes(b"{bad state")
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert result["status"] == "STATE_CORRUPT"
    assert corrupt.read_bytes() == b"{bad state"
    assert not list((root / "analytics").glob("reports/daily_strategy_audit_*"))


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": 1, "last_seen_period": "2026-09-05", "periods": {"2026-09-05": {}}},
        {
            "schema_version": 1,
            "last_seen_period": "2026-09-05",
            "periods": {"2026-09-05": {"completed": "false", "attempts": []}},
        },
        {
            "schema_version": 1,
            "last_seen_period": "2026-09-05",
            "periods": {
                "2026-09-05": {
                    "completed": False,
                    "attempts": [{"attempt_id": "a1", "status": "STARTED", "started_at": "x", "started_epoch": "1"}],
                }
            },
        },
        {"schema_version": 0, "last_seen_period": None, "periods": {}},
    ],
)
def test_existing_state_schema_shape_is_strictly_validated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: Dict[str, Any],
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    state_path = root / "state" / "strategy_auditor_state.json"
    original = json.dumps(payload)
    state_path.write_text(original, encoding="utf-8")
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert result["status"] == "STATE_CORRUPT"
    assert state_path.read_text(encoding="utf-8") == original
    assert not list((root / "analytics").glob("reports/daily_strategy_audit_*"))


def test_failed_attempts_backoff_retry_limit_and_no_completion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_lib as lib
    from tools import strategy_auditor_runtime as runtime

    def fail_build(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        raise RuntimeError("synthetic secret-like raw detail must not leak")

    monkeypatch.setattr(lib, "build_report", fail_build)
    base = dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC)

    assert runtime.run_auditor(mode="manual", now=base)["status"] == "FAILED"
    cooldown = runtime.run_auditor(mode="manual", now=base + dt.timedelta(seconds=299))
    assert cooldown["status"] == "RETRY_COOLDOWN"
    assert runtime.run_auditor(mode="manual", now=base + dt.timedelta(seconds=300))["status"] == "FAILED"
    assert runtime.run_auditor(mode="manual", now=base + dt.timedelta(seconds=600))["status"] == "FAILED"
    limit = runtime.run_auditor(mode="manual", now=base + dt.timedelta(seconds=900))
    assert limit["status"] == "RETRY_LIMIT_REACHED"
    assert "synthetic secret-like" not in json.dumps(limit)
    state = json.loads((root / "state" / "strategy_auditor_state.json").read_text(encoding="utf-8"))
    assert state["periods"]["2026-09-05"]["completed"] is False
    assert len(state["periods"]["2026-09-05"]["attempts"]) == 3


def test_source_read_failure_records_failed_attempt_without_source_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(
        tmp_path,
        monkeypatch,
        source_overrides={"engine_events": "observability"},
    )
    for rel in (
        "observability/fsm_events.jsonl",
        "observability/distribution_events.jsonl",
        "observability/error_events.jsonl",
        "outcomes/outcomes.jsonl",
    ):
        _write_jsonl(root / rel, [])
    before = {
        rel: hashlib.sha256((root / rel).read_bytes()).hexdigest()
        for rel in (
            "observability/fsm_events.jsonl",
            "observability/distribution_events.jsonl",
            "observability/error_events.jsonl",
            "outcomes/outcomes.jsonl",
        )
    }
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC))

    assert result["status"] == "FAILED"
    assert result["error"]["operation"] == "build_or_write_report"
    state = json.loads((root / "state" / "strategy_auditor_state.json").read_text(encoding="utf-8"))
    assert state["periods"]["2026-09-05"]["completed"] is False
    after = {
        rel: hashlib.sha256((root / rel).read_bytes()).hexdigest()
        for rel in before
    }
    assert after == before


@pytest.mark.parametrize(
    ("source_key", "relative_path"),
    [
        ("engine_events", "observability/engine_events.jsonl"),
        ("outcomes", "outcomes/outcomes.jsonl"),
    ],
)
def test_unreadable_source_propagates_even_when_exists_reports_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_key: str,
    relative_path: str,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    target = root / relative_path
    before = _hash_sources(root)
    _purge()
    from tools import strategy_auditor_lib as lib
    from tools import strategy_auditor_runtime as runtime

    real_exists = lib.os.path.exists
    real_open = builtins.open

    def fake_exists(path: Any) -> bool:
        if os.fspath(path) == str(target):
            return False
        return real_exists(path)

    def fake_open(path: Any, *args: Any, **kwargs: Any):
        mode = str(args[0]) if args else str(kwargs.get("mode", "r"))
        if os.fspath(path) == str(target) and "r" in mode:
            raise PermissionError("synthetic unreadable evidence secret")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(lib.os.path, "exists", fake_exists)
    monkeypatch.setattr(builtins, "open", fake_open)

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC))

    assert source_key in lib.load_settings()["sources"]
    assert result["status"] == "FAILED"
    assert result["error"]["error_type"] == "PermissionError"
    assert "synthetic unreadable evidence" not in json.dumps(result)
    assert _hash_sources(root) == before
    assert not list((root / "analytics").glob("reports/daily_strategy_audit_*"))
    state = json.loads((root / "state" / "strategy_auditor_state.json").read_text(encoding="utf-8"))
    assert state["periods"]["2026-09-05"]["completed"] is False


def test_missing_sources_remain_empty_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC))

    assert result["status"] == "SUCCESS"
    assert result["decision_count"] == 0
    report = json.loads(Path(result["report_paths"]["json"]).read_text(encoding="utf-8"))
    assert report["input_sources"]["engine_events"]["valid"] == 0
    assert report["input_sources"]["outcomes"]["valid"] == 0


def test_completion_state_save_failure_never_records_false_complete_and_reconciles_later(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    real_save = runtime._save_state
    calls = {"count": 0}

    def fail_completion_once(state):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("synthetic completion state save failure")
        return real_save(state)

    monkeypatch.setattr(runtime, "_save_state", fail_completion_once)
    now = dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC)
    failed = runtime.run_auditor(mode="manual", now=now)
    assert failed["status"] == "FAILED"
    state = json.loads((root / "state" / "strategy_auditor_state.json").read_text(encoding="utf-8"))
    assert state["periods"]["2026-09-05"]["completed"] is False
    assert state["periods"]["2026-09-05"]["attempts"][0]["status"] == "FAILED"

    monkeypatch.setattr(runtime, "_save_state", real_save)
    reconciled = runtime.run_auditor(mode="manual", now=now + dt.timedelta(seconds=1))
    assert reconciled["status"] == "ALREADY_COMPLETED"
    state = json.loads((root / "state" / "strategy_auditor_state.json").read_text(encoding="utf-8"))
    assert state["periods"]["2026-09-05"]["completed"] is True


def test_interrupted_attempt_restarts_after_backoff_and_artifact_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    started = dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC)
    state = {
        "schema_version": 1,
        "last_seen_period": "2026-09-05",
        "periods": {
            "2026-09-05": {
                "completed": False,
                "attempts": [
                    {
                        "attempt_id": "attempt-old",
                        "status": "STARTED",
                        "started_at": started.isoformat(),
                        "started_epoch": int(started.timestamp()),
                    }
                ],
            }
        },
    }
    (root / "state" / "strategy_auditor_state.json").write_text(json.dumps(state), encoding="utf-8")
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=started + dt.timedelta(seconds=301))
    assert result["status"] == "SUCCESS"
    saved = json.loads((root / "state" / "strategy_auditor_state.json").read_text(encoding="utf-8"))
    attempts = saved["periods"]["2026-09-05"]["attempts"]
    assert attempts[0]["status"] == "INTERRUPTED"
    assert attempts[1]["status"] == "COMPLETED"

    saved["periods"]["2026-09-05"]["completed"] = False
    saved["periods"]["2026-09-05"].pop("completed_attempt_id", None)
    saved["periods"]["2026-09-05"].pop("completed_at", None)
    (root / "state" / "strategy_auditor_state.json").write_text(json.dumps(saved), encoding="utf-8")
    reconciled = runtime.run_auditor(mode="manual", now=started + dt.timedelta(seconds=602))
    assert reconciled["status"] == "ALREADY_COMPLETED"


def test_clock_rollback_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    (root / "state" / "strategy_auditor_state.json").write_text(
        json.dumps({"schema_version": 1, "last_seen_period": "2026-09-06", "periods": {}}),
        encoding="utf-8",
    )
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert result["status"] == "CLOCK_ROLLBACK_DETECTED"
    assert not list((root / "analytics").glob("reports/daily_strategy_audit_*"))


def test_duplicate_lock_is_nonblocking_for_threads_and_live_processes_across_deployments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    now = dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC)
    with runtime._auditor_transaction_lock():
        duplicate = runtime.run_auditor(mode="manual", now=now)
    assert duplicate["status"] == "DUPLICATE_IN_PROGRESS"
    journal = (root / "observability" / "strategy_auditor_events.jsonl").read_text(encoding="utf-8")
    assert "STRATEGY_AUDITOR_DUPLICATE_SUPPRESSED" in journal

    ready = multiprocessing.Event()
    release = multiprocessing.Event()
    proc = multiprocessing.Process(target=_hold_lock_process, args=(str(root), ready, release))
    proc.start()
    try:
        assert ready.wait(5)
        lock_file = root / "state" / "strategy_auditor.lock"
        old = time.time() - 1000
        os.utime(lock_file, (old, old))
        monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "different-deploy")
        process_duplicate = runtime.run_auditor(mode="manual", now=now)
        assert process_duplicate["status"] == "DUPLICATE_IN_PROGRESS"
    finally:
        release.set()
        proc.join(5)
        if proc.is_alive():
            proc.terminate()
            proc.join(5)
    assert proc.exitcode == 0


def test_alias_guard_blocks_source_output_state_overlap_before_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(
        tmp_path,
        monkeypatch,
        reports_output="observability",
        source_overrides={"engine_events": "observability/daily_strategy_audit_2026-09-05.json"},
    )
    _write_sources(root)
    _write_jsonl(root / "observability" / "daily_strategy_audit_2026-09-05.json", [_decision()])
    before = _hash_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert result["status"] == "CONFIGURATION_ERROR"
    assert "SOURCE_ALIASES" in json.dumps(result["error"])
    assert _hash_sources(root) == before
    assert not (root / "state" / "strategy_auditor_state.json").exists()


def test_alias_guard_blocks_scheduled_not_due_status_or_journal_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(
        tmp_path,
        monkeypatch,
        source_overrides={"engine_events": "state/strategy_auditor_status.json"},
    )
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "23:59")
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 9, 5, 23, 58, tzinfo=dt.UTC))
    assert result["status"] == "CONFIGURATION_ERROR"
    assert "SOURCE_ALIASES_WRITE_FILE" in json.dumps(result["error"])
    assert not (root / "state" / "strategy_auditor_status.json").exists()
    assert not (root / "observability" / "strategy_auditor_events.jsonl").exists()

    invalid_clock = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 23, 58))
    assert invalid_clock["status"] == "CONFIGURATION_ERROR"
    assert not (root / "state" / "strategy_auditor_status.json").exists()


def test_alias_guard_precedes_output_validation_for_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch, write_json=False, write_markdown=False)
    _write_sources(root)
    monkeypatch.setenv("ERROR_EVENTS_LOG", str(root / "observability" / "strategy_auditor_events.jsonl"))
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 12, 0, tzinfo=dt.UTC))
    assert result["status"] == "CONFIGURATION_ERROR"
    assert result["error"]["code"] == "SOURCE_ALIASES_WRITE_FILE"
    assert not (root / "state" / "strategy_auditor_status.json").exists()
    assert not (root / "observability" / "strategy_auditor_events.jsonl").exists()


def test_diagnostic_guard_fails_closed_when_settings_safety_check_cannot_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    payload = _settings_payload(root, source_overrides={"error_events": "observability/strategy_auditor_events.jsonl"})
    payload["reports"]["output_dir"] = None
    (root / "config" / "intelligence_settings.json").write_text(json.dumps(payload), encoding="utf-8")
    source_journal = root / "observability" / "strategy_auditor_events.jsonl"
    source_journal.write_text('{"source":"must-stay-read-only"}\n', encoding="utf-8")
    before = source_journal.read_bytes()
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 12, 0, tzinfo=dt.UTC))

    assert result["status"] == "CONFIGURATION_ERROR"
    assert result["error"]["operation"] == "load_or_validate_settings"
    assert result["diagnostic_write_blocked"]["operation"] == "diagnostic_write_guard"
    assert source_journal.read_bytes() == before
    assert not (root / "state" / "strategy_auditor_status.json").exists()


def test_explicit_settings_path_is_used_by_early_status_and_journal_guards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    alternate = root / "config" / "alternate_intelligence.json"
    alternate_payload = _settings_payload(
        root,
        source_overrides={"error_events": "observability/strategy_auditor_events.jsonl"},
    )
    alternate.write_text(json.dumps(alternate_payload), encoding="utf-8")
    source_journal = root / "observability" / "strategy_auditor_events.jsonl"
    source_journal.write_text('{"source":"alternate-read-only"}\n', encoding="utf-8")
    before = source_journal.read_bytes()
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.delenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", raising=False)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    missing_schedule = runtime.evaluate_scheduled_once(
        now=dt.datetime(2026, 9, 5, 8, 0, tzinfo=dt.UTC),
        settings_path=str(alternate),
    )

    assert missing_schedule["status"] == "CONFIGURATION_ERROR"
    assert missing_schedule["error"]["code"] == "SOURCE_ALIASES_WRITE_FILE"
    assert source_journal.read_bytes() == before
    assert not (root / "state" / "strategy_auditor_status.json").exists()

    malformed = _settings_payload(
        root,
        source_overrides={"error_events": "observability/strategy_auditor_events.jsonl"},
    )
    malformed["reports"]["output_dir"] = None
    alternate.write_text(json.dumps(malformed), encoding="utf-8")
    malformed_result = runtime.run_auditor(
        mode="manual",
        now=dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC),
        settings_path=str(alternate),
    )
    assert malformed_result["status"] == "CONFIGURATION_ERROR"
    assert malformed_result["diagnostic_write_blocked"]["operation"] == "diagnostic_write_guard"
    assert source_journal.read_bytes() == before
    assert not (root / "state" / "strategy_auditor_status.json").exists()


def test_runtime_status_overlay_does_not_persist_or_downgrade_health(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _purge()
    from runtime import runtime_status
    from tools import strategy_auditor_runtime as runtime

    runtime_status.write_status("running", "ok", market_data_state="READY")
    runtime._write_status({"status": "SUCCESS", "decision_count": 1})
    observed = runtime_status.read_status()
    assert observed["phase"] == "running"
    assert observed["market_data_state"] == "READY"
    assert observed["strategy_auditor"]["status"] == "SUCCESS"

    runtime_status.update_status(broker_state="READY")
    raw = json.loads((root / "state" / "runtime_status.json").read_text(encoding="utf-8"))
    assert "strategy_auditor" not in raw
    assert runtime_status.read_status()["strategy_auditor"]["status"] == "SUCCESS"


def test_status_and_journal_include_last_attempt_success_and_lifecycle_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 9, 0, tzinfo=dt.UTC))
    assert result["status"] == "SUCCESS"
    status = json.loads((root / "state" / "strategy_auditor_status.json").read_text(encoding="utf-8"))
    assert status["last_attempt"]["status"] == "SUCCESS"
    assert status["last_success"]["decision_count"] == 1
    journal = (root / "observability" / "strategy_auditor_events.jsonl").read_text(encoding="utf-8")
    assert "STRATEGY_AUDITOR_RUN_STARTED" in journal
    assert "STRATEGY_AUDITOR_RUN_COMPLETED" in journal


def test_status_history_survives_skip_cooldown_duplicate_and_journal_is_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "09:00")
    _purge()
    from tools import strategy_auditor_lib as lib
    from tools import strategy_auditor_runtime as runtime

    success = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 10, 5, 9, 0, tzinfo=dt.UTC))
    assert success["status"] == "SUCCESS"
    status_path = root / "state" / "strategy_auditor_status.json"
    status_path.unlink()
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "false")
    disabled = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 10, 6, 8, 0, tzinfo=dt.UTC))
    assert disabled["status"] == "DISABLED"
    disabled_status = json.loads(status_path.read_text(encoding="utf-8"))
    assert disabled_status["last_attempt"]["status"] == "SUCCESS"
    assert disabled_status["last_success"]["report_period"] == "2026-10-05"
    assert disabled_status["last_success"]["report_paths"]["json"].endswith("daily_strategy_audit_2026-10-05.json")

    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    not_due_after_restart = runtime.evaluate_scheduled_once(now=dt.datetime(2026, 10, 6, 8, 30, tzinfo=dt.UTC))
    assert not_due_after_restart["status"] == "NOT_DUE"
    not_due_status = json.loads(status_path.read_text(encoding="utf-8"))
    assert not_due_status["last_attempt"]["status"] == "SUCCESS"
    assert not_due_status["last_success"]["report_paths"]["markdown"].endswith("daily_strategy_audit_2026-10-05.md")
    assert "<bounded>" not in json.dumps(not_due_status["last_success"])

    def fail_build(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        raise RuntimeError("synthetic failure must stay sanitized")

    monkeypatch.setattr(lib, "build_report", fail_build)
    failed = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 10, 6, 9, 0, tzinfo=dt.UTC))
    assert failed["status"] == "FAILED"
    assert runtime.run_auditor(mode="manual", now=dt.datetime(2026, 10, 6, 9, 1, tzinfo=dt.UTC))["status"] == "RETRY_COOLDOWN"
    assert runtime.run_auditor(mode="manual", now=dt.datetime(2026, 10, 6, 9, 2, tzinfo=dt.UTC))["status"] == "RETRY_COOLDOWN"
    assert runtime.evaluate_scheduled_once(now=dt.datetime(2026, 10, 7, 8, 0, tzinfo=dt.UTC))["status"] == "NOT_DUE"
    assert runtime.evaluate_scheduled_once(now=dt.datetime(2026, 10, 7, 8, 1, tzinfo=dt.UTC))["status"] == "NOT_DUE"
    with runtime._auditor_transaction_lock():
        assert runtime.run_auditor(mode="manual", now=dt.datetime(2026, 10, 7, 9, 10, tzinfo=dt.UTC))["status"] == "DUPLICATE_IN_PROGRESS"

    status = json.loads((root / "state" / "strategy_auditor_status.json").read_text(encoding="utf-8"))
    assert status["last_attempt"]["status"] == "FAILED"
    assert status["last_attempt"]["report_period"] == "2026-10-06"
    assert status["last_success"]["report_period"] == "2026-10-05"

    journal = (root / "observability" / "strategy_auditor_events.jsonl").read_text(encoding="utf-8")
    assert "STRATEGY_AUDITOR_RUN_STARTED" in journal
    assert "STRATEGY_AUDITOR_RUN_COMPLETED" in journal
    assert "STRATEGY_AUDITOR_RUN_FAILED" in journal
    assert "STRATEGY_AUDITOR_NOT_DUE" in journal
    assert "STRATEGY_AUDITOR_DUPLICATE_SUPPRESSED" in journal
    assert journal.count("STRATEGY_AUDITOR_RETRY_COOLDOWN") == 1
    assert journal.count("STRATEGY_AUDITOR_NOT_DUE") == 2


def test_admin_report_summary_tracks_settings_but_download_root_fails_closed_outside_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    external_reports = tmp_path / "external_reports"
    root = _configure_root(tmp_path, monkeypatch, reports_output=str(external_reports))
    _write_sources(root)
    _purge()
    from core import admin_commands
    from tools import strategy_auditor_runtime as runtime

    result = runtime.run_auditor(mode="manual", now=dt.datetime(2026, 9, 5, 22, 0, tzinfo=dt.UTC))
    assert result["status"] == "SUCCESS"
    assert Path(result["report_paths"]["json"]).parent == external_reports
    assert admin_commands._find_latest_report_json() == result["report_paths"]["json"]
    assert admin_commands._resolve_dir_path("rpt") is None


def test_system_boot_worker_invalid_config_noncritical_and_cooperative_stop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "not-a-time")
    _purge()
    from runtime import system_boot

    invalid = system_boot._start_strategy_auditor_thread()
    assert invalid["status"] == "INVALID_SCHEDULE"
    assert invalid["worker_started"] is False

    from tools import strategy_auditor_runtime as runtime

    entered = threading_event = multiprocessing.Event()

    def fake_loop(stop_event, *, now_provider=None):
        entered.set()
        stop_event.wait(5)

    monkeypatch.setattr(runtime, "worker_loop", fake_loop)
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "09:00")
    started = system_boot._start_strategy_auditor_thread()
    assert started["status"] == "WORKER_STARTED"
    assert threading_event.wait(5)
    system_boot._stop_strategy_auditor_worker(timeout=1)
    assert system_boot._AUDITOR_THREAD is not None
    assert not system_boot._AUDITOR_THREAD.is_alive()


def test_worker_loop_survives_evaluation_failure_and_waits_configured_interval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from tools import strategy_auditor_runtime as runtime

    class FakeStop:
        def __init__(self) -> None:
            self.wait_calls: list[float] = []

        def is_set(self) -> bool:
            return bool(self.wait_calls)

        def wait(self, seconds: float) -> bool:
            self.wait_calls.append(seconds)
            return True

    def raise_once(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        raise RuntimeError("synthetic worker failure")

    stop = FakeStop()
    monkeypatch.setattr(runtime, "evaluate_scheduled_once", raise_once)
    runtime.worker_loop(stop)  # type: ignore[arg-type]

    assert stop.wait_calls == [runtime.WORKER_EVALUATION_INTERVAL_SECONDS]
    status = json.loads((root / "state" / "strategy_auditor_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "FAILED"
    journal = (root / "observability" / "strategy_auditor_events.jsonl").read_text(encoding="utf-8")
    assert "STRATEGY_AUDITOR_WORKER_FAILED" in journal


def test_system_boot_configured_starts_one_worker_and_disabled_starts_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    _purge()
    from runtime import system_boot
    from tools import strategy_auditor_runtime as runtime

    started_events: list[Any] = []

    def fake_loop(stop_event, *, now_provider=None):
        started_events.append(stop_event)
        stop_event.wait(5)

    monkeypatch.setattr(runtime, "worker_loop", fake_loop)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "09:00")
    first = system_boot._start_strategy_auditor_thread()
    second = system_boot._start_strategy_auditor_thread()
    assert first["status"] == "WORKER_STARTED"
    assert second["status"] == "WORKER_ALREADY_STARTED"
    assert len(started_events) == 1
    system_boot._stop_strategy_auditor_worker(timeout=1)

    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "false")
    disabled = system_boot._start_strategy_auditor_thread()
    assert disabled["status"] == "DISABLED"
    assert disabled["worker_started"] is False


def test_system_boot_worker_invalid_settings_path_is_noncritical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "00:00")
    monkeypatch.setenv("STRATEGY_AUDITOR_SETTINGS", str(root / "config" / "missing-intelligence.json"))
    _purge()
    from runtime import system_boot
    from tools import strategy_auditor_runtime as runtime

    started = system_boot._start_strategy_auditor_thread()
    assert started["status"] == "CONFIGURATION_ERROR"
    assert started["worker_started"] is False
    assert started["error"]["operation"] == "diagnostic_write_guard"
    assert not (root / "state" / "strategy_auditor_status.json").exists()


def test_cli_real_failure_returns_nonzero_and_sanitized_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _configure_root(tmp_path, monkeypatch)
    _write_sources(root)
    (root / "state" / "strategy_auditor_state.json").write_text("{bad json", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(SEND_ROOT),
            "BINARYBOT_BASE_DIR": str(root),
            "STRATEGY_AUDITOR_SETTINGS": str(root / "config" / "intelligence_settings.json"),
            "TMPDIR": str(REPO_ROOT / ".cache" / "tmp"),
        }
    )
    (REPO_ROOT / ".cache" / "tmp").mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, "-m", "tools.strategy_auditor_daily"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert completed.returncode != 0
    assert "Traceback" not in completed.stdout + completed.stderr
    assert "bad json" not in completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["status"] == "STATE_CORRUPT"
    assert payload["error"]["error_type"] == "StrategyAuditorStateCorrupt"
