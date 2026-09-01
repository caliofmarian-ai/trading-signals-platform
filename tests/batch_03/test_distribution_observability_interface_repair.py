from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge_modules() -> None:
    prefixes = ("core.", "intelligence.")
    exact = {"core", "intelligence"}
    for name in list(sys.modules.keys()):
        if name in exact or name.startswith(prefixes):
            sys.modules.pop(name, None)


def _base_channel_config() -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "FREE_CHANNEL_ID": 1001,
        "BASIC_CHANNEL_ID": 1002,
        "PRO_CHANNEL_ID": 1003,
        "ELITE_CHANNEL_ID": 1004,
        "ADMIN_GROUP_ID": 2001,
        "SIGNALS_LIVE_TOPIC_ID": 3001,
        "FREE_LIMIT": 6,
        "BASIC_LIMIT": 20,
        "PRO_LIMIT": 50,
        "ELITE_LIMIT": None,
        "TZ": "Europe/London",
        "RESET_TIME": "23:59",
    }


def _prepare_runtime_root(tmp_path: Path, config_overrides: Dict[str, Any] | None = None) -> tuple[Path, Path]:
    root = tmp_path / "runtime"
    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    config = _base_channel_config()
    if config_overrides:
        config.update(config_overrides)
    config_path = config_dir / "channel_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return root, config_path


def _import_batch03_modules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_overrides: Dict[str, Any] | None = None,
) -> tuple[Any, Any, Any, Path]:
    root, config_path = _prepare_runtime_root(tmp_path, config_overrides=config_overrides)

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("OBS_DIR", str(root / "observability"))
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(root / "observability" / "engine_events.jsonl"))
    monkeypatch.setenv("FSM_EVENTS_LOG", str(root / "observability" / "fsm_events.jsonl"))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(root / "observability" / "distribution_events.jsonl"))
    monkeypatch.setenv("ADMIN_PROOFS_LOG", str(root / "observability" / "admin_proofs.jsonl"))
    monkeypatch.setenv("ERROR_EVENTS_LOG", str(root / "observability" / "error_events.jsonl"))
    monkeypatch.setenv("OUTCOMES_LOG", str(root / "outcomes" / "outcomes.jsonl"))

    _purge_modules()
    importlib.invalidate_caches()

    observability_logger = importlib.import_module("core.observability_logger")
    distribution_router = importlib.import_module("core.distribution_router")
    outcome_service = importlib.import_module("core.outcome_service")

    distribution_router.DIST_STATE_PATH = str(root / "state" / "dist_state.json")
    distribution_router.CHANNEL_CONFIG_PATHS = [str(config_path)]
    outcome_service.OUTCOMES_JSONL = str(root / "outcomes" / "outcomes.jsonl")
    outcome_service.OPEN_REGISTRY_JSON = str(root / "outcomes" / "open_now_registry.json")
    outcome_service.OUTCOMES_INDEX_JSON = str(root / "outcomes" / "outcomes_index.json")

    return observability_logger, distribution_router, outcome_service, root


def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _signal_event(stage: str = "OPEN_NOW", signal_id: str = "sig-001") -> Dict[str, Any]:
    return {
        "event_type": "signal_event",
        "stage": stage,
        "signal_id": signal_id,
        "symbol": "EURUSD",
        "timeframe": "M1",
        "direction": "CALL",
        "score_total": 88.5,
        "buffer_mode": "MEDIUM",
        "buffer_price": 1.2345,
        "expiry_minutes": 5,
        "candle_ts": 1720000000,
        "created_ts": 1720000005,
        "payload": {"test": True},
    }


def _tier_publish_event(observability_logger: Any, **overrides: Any) -> Dict[str, Any]:
    data = {
        "publish_result": "PUBLISHED",
        "route_state_before": "ACTIVE",
        "route_state_after": "ACTIVE",
        "limit": 5,
        "counter_before": 1,
        "counter_after": 2,
        "counted": True,
        "attempted": True,
        "destination_kind": "tier_channel",
        "feedback_enabled": True,
        "transport": {"ok": True, "message_id": 777, "error": None},
        "dedup": {"key": "FREE|sig-001|OPEN_NOW", "was_duplicate": False, "action": "publish"},
        "reason": None,
    }
    data.update(overrides.pop("data", {}))
    correlation = {
        "signal_id": "sig-001",
        "route": "FREE",
        "tier": "FREE",
        "stage": "OPEN_NOW",
        "symbol": "EURUSD",
        "timeframe": "M1",
        "destination_id": 1001,
        "message_id": 777,
        "candle_ts_epoch": 1720000000,
    }
    correlation.update(overrides.pop("correlation", {}))
    source = {"module": "tests", "function": "tier_publish_event"}
    source.update(overrides.pop("source", {}))
    return observability_logger.build_event(
        "tier_publish",
        data,
        source=source,
        correlation=correlation,
    )


def _tier_reset_event(observability_logger: Any) -> Dict[str, Any]:
    return observability_logger.build_event(
        "tier_reset",
        {
            "reset_time_london": "08:10 Europe/London",
            "effective_date_london": "2026-07-13",
            "before": {
                "tier_state": {"FREE": "ACTIVE", "BASIC": "ACTIVE", "PRO": "ACTIVE", "ELITE": "ACTIVE"},
                "open_signals_today": {"FREE": 1, "BASIC": 2, "PRO": 3, "ELITE": 0},
                "last_reset_london_date": "2026-07-12",
            },
            "after": {
                "tier_state": {"FREE": "ACTIVE", "BASIC": "ACTIVE", "PRO": "ACTIVE", "ELITE": "ACTIVE"},
                "open_signals_today": {"FREE": 0, "BASIC": 0, "PRO": 0, "ELITE": 0},
                "last_reset_london_date": "2026-07-13",
            },
        },
        source={"module": "tests", "function": "tier_reset_event"},
    )


def _route_results(events: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    return {event["route"]: event["data"]["publish_result"] for event in events if event.get("event_type") == "tier_publish"}


def test_distribution_router_and_observability_logger_import_without_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def _fail_get(*args, **kwargs):
        calls.append("get")
        raise AssertionError("network call during import")

    def _fail_post(*args, **kwargs):
        calls.append("post")
        raise AssertionError("network call during import")

    monkeypatch.setattr("requests.get", _fail_get)
    monkeypatch.setattr("requests.post", _fail_post)

    obs, router, _, _ = _import_batch03_modules(tmp_path, monkeypatch)
    assert obs is not None
    assert router is not None
    assert calls == []


def test_load_config_uses_file_values_and_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    obs, router, _, _ = _import_batch03_modules(
        tmp_path,
        monkeypatch,
        config_overrides={"FREE_LIMIT": 6, "ADMIN_GROUP_ID": 9876, "SIGNALS_LIVE_TOPIC_ID": 4321},
    )

    cfg = router.load_config()
    assert cfg["limits"]["FREE"] == 6
    assert cfg["admin"]["group_id"] == 9876
    assert cfg["admin"]["signals_live_topic_id"] == 4321

    monkeypatch.setenv("FREE_LIMIT", "9")
    monkeypatch.setenv("ADMIN_GROUP_ID", "6543")
    cfg = router.load_config()
    assert cfg["limits"]["FREE"] == 9
    assert cfg["admin"]["group_id"] == 6543
    assert obs.get_event_schema()["schema_version"] == "3.0.0"


def test_live_distribution_event_types_build_and_validate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    obs, _, _, _ = _import_batch03_modules(tmp_path, monkeypatch)

    publish_event = _tier_publish_event(obs)
    reset_event = _tier_reset_event(obs)

    assert obs.validate_event(publish_event) == publish_event
    assert obs.validate_event(reset_event) == reset_event


def test_build_event_rejects_unsupported_kwargs_clearly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    obs, _, _, _ = _import_batch03_modules(tmp_path, monkeypatch)

    with pytest.raises(TypeError, match="unexpected keyword argument"):
        obs.build_event("tier_publish", {}, source={"module": "x", "function": "y"}, extra={})


def test_unsupported_event_types_missing_fields_invalid_types_and_unknown_fields_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, _, _, _ = _import_batch03_modules(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="unsupported event_type"):
        obs.build_event("not_supported", {}, source={"module": "x", "function": "y"})

    with pytest.raises(ValueError, match="missing required fields"):
        obs.build_event(
            "tier_publish",
            {"publish_result": "PUBLISHED"},
            source={"module": "x", "function": "y"},
            correlation={"signal_id": "sig-001", "route": "FREE", "tier": "FREE", "stage": "OPEN_NOW"},
        )

    with pytest.raises(ValueError, match="counter_before must be integer"):
        _tier_publish_event(obs, data={"counter_before": "one"})

    with pytest.raises(ValueError, match="contains unknown fields"):
        _tier_publish_event(obs, data={"unexpected_field": True})


def test_event_ids_unique_timestamps_canonical_and_correlation_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, _, _, _ = _import_batch03_modules(tmp_path, monkeypatch)

    first = _tier_publish_event(obs)
    second = _tier_publish_event(obs, correlation={"message_id": 778})

    assert first["event_id"] != second["event_id"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", first["ts_utc"])
    assert isinstance(first["ts_epoch_ms"], int)
    assert first["signal_id"] == "sig-001"
    assert first["route"] == "FREE"
    assert first["tier"] == "FREE"
    assert first["destination_id"] == 1001
    assert first["message_id"] == 777


def test_successful_publication_logs_success_for_each_material_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, router, _, root = _import_batch03_modules(tmp_path, monkeypatch)
    sends: list[tuple[int, str, Any]] = []

    def _send_message(chat_id: int, text: str, reply_markup=None, thread_id=None):
        sends.append((chat_id, text, thread_id))
        return {"ok": True, "result": {"message_id": 100 + len(sends)}}

    monkeypatch.setattr(router.telegram_publisher, "send_message", _send_message)

    router.route(_signal_event(stage="PRE", signal_id="sig-success"), now_ts=1720000100)

    dist_events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    publish_events = [event for event in dist_events if event["event_type"] == "tier_publish"]
    results = _route_results(publish_events)

    assert sends
    assert results == {
        "FREE": "PUBLISHED",
        "BASIC": "PUBLISHED",
        "PRO": "PUBLISHED",
        "ELITE": "PUBLISHED",
        "ADMIN_SIGNALS_LIVE": "PUBLISHED",
    }
    assert all(event["event_type"] == "tier_publish" for event in publish_events)
    assert {event["tier"] for event in publish_events if event["route"] == "ADMIN_SIGNALS_LIVE"} == {"ELITE"}


def test_failed_publication_logs_failure_and_never_false_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, router, _, root = _import_batch03_modules(
        tmp_path,
        monkeypatch,
        config_overrides={
            "BASIC_CHANNEL_ID": None,
            "PRO_CHANNEL_ID": None,
            "ELITE_CHANNEL_ID": None,
            "ADMIN_GROUP_ID": None,
            "SIGNALS_LIVE_TOPIC_ID": None,
        },
    )

    def _send_message(*args, **kwargs):
        raise RuntimeError("telegram down")

    monkeypatch.setattr(router.telegram_publisher, "send_message", _send_message)

    router.route(_signal_event(signal_id="sig-fail"), now_ts=1720000200)

    dist_events = [event for event in _read_jsonl(root / "observability" / "distribution_events.jsonl") if event["event_type"] == "tier_publish"]
    free_events = [event for event in dist_events if event["route"] == "FREE"]

    assert len(free_events) == 1
    assert free_events[0]["data"]["publish_result"] == "FAILED"
    assert free_events[0]["data"]["transport"]["error"] == "telegram down"
    assert all(event["data"]["publish_result"] != "PUBLISHED" for event in free_events)
    assert obs.validate_event(free_events[0]) == free_events[0]


def test_silent_and_duplicate_routes_record_correct_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, router, _, root = _import_batch03_modules(
        tmp_path,
        monkeypatch,
        config_overrides={
            "BASIC_CHANNEL_ID": None,
            "PRO_CHANNEL_ID": None,
            "ELITE_CHANNEL_ID": None,
            "ADMIN_GROUP_ID": None,
            "SIGNALS_LIVE_TOPIC_ID": None,
        },
    )

    state = router._default_state()
    state["tier_state"]["FREE"] = "SILENT"
    router.save_state(state)

    monkeypatch.setattr(
        router.telegram_publisher,
        "send_message",
        lambda *args, **kwargs: {"ok": True, "result": {"message_id": 500}},
    )

    router.route(_signal_event(signal_id="sig-silent"), now_ts=1720000300)

    silent_events = [event for event in _read_jsonl(root / "observability" / "distribution_events.jsonl") if event["event_type"] == "tier_publish"]
    assert _route_results(silent_events)["FREE"] == "SKIPPED_SILENT"

    state = router._default_state()
    router.save_state(state)
    router.route(_signal_event(signal_id="sig-dup"), now_ts=1720000400)
    router.route(_signal_event(signal_id="sig-dup"), now_ts=1720000401)

    dist_events = [event for event in _read_jsonl(root / "observability" / "distribution_events.jsonl") if event["event_type"] == "tier_publish"]
    free_results = [event["data"]["publish_result"] for event in dist_events if event["route"] == "FREE" and event["signal_id"] == "sig-dup"]
    assert free_results == ["PUBLISHED", "DUPLICATE_SUPPRESSED"]


def test_logging_failures_do_not_write_malformed_json_or_duplicate_delivery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, router, _, root = _import_batch03_modules(
        tmp_path,
        monkeypatch,
        config_overrides={
            "BASIC_CHANNEL_ID": None,
            "PRO_CHANNEL_ID": None,
            "ELITE_CHANNEL_ID": None,
            "ADMIN_GROUP_ID": None,
            "SIGNALS_LIVE_TOPIC_ID": None,
        },
    )

    send_calls: list[int] = []

    def _send_message(chat_id: int, text: str, reply_markup=None, thread_id=None):
        send_calls.append(chat_id)
        return {"ok": True, "result": {"message_id": 901}}

    monkeypatch.setattr(router.telegram_publisher, "send_message", _send_message)

    original_append = obs._append_jsonl
    failures = {"remaining": 1}

    def _flaky_append(path: str, record: Dict[str, Any], *, sink: str) -> None:
        if sink == "distribution" and failures["remaining"] > 0:
            failures["remaining"] -= 1
            raise OSError("disk full")
        original_append(path, record, sink=sink)

    monkeypatch.setattr(obs, "_append_jsonl", _flaky_append)

    router.route(_signal_event(signal_id="sig-log-failure"), now_ts=1720000500)

    error_events = _read_jsonl(root / "observability" / "error_events.jsonl")
    assert len(send_calls) == 1
    assert len(error_events) == 1
    assert error_events[0]["data"]["error_type"] == "observability_log_failed"

    monkeypatch.setattr(obs, "_append_jsonl", original_append)
    router.route(_signal_event(signal_id="sig-log-failure"), now_ts=1720000501)

    dist_events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    assert len(send_calls) == 1
    assert _route_results(dist_events)["FREE"] == "DUPLICATE_SUPPRESSED"


def test_jsonl_output_remains_valid_under_repeated_writes_and_compat_records_readable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, _, _, root = _import_batch03_modules(tmp_path, monkeypatch)

    for _ in range(3):
        obs.log_event(_tier_publish_event(obs))

    obs.log_event(
        {
            "event_type": "system_health",
            "message": "Restart guard start recorded",
            "data": {"restart_count": 1, "window_seconds": 180, "max_restarts": 3},
        }
    )

    dist_events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    engine_events = _read_jsonl(root / "observability" / "engine_events.jsonl")

    assert len(dist_events) == 3
    assert engine_events[-1]["event_type"] == "system_health"
    assert engine_events[-1]["data"]["message"] == "Restart guard start recorded"
    assert all(isinstance(event, dict) for event in dist_events + engine_events)


def test_distribution_invalid_event_path_and_outcome_warning_use_canonical_warning_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, router, outcome_service, root = _import_batch03_modules(
        tmp_path,
        monkeypatch,
        config_overrides={
            "BASIC_CHANNEL_ID": None,
            "PRO_CHANNEL_ID": None,
            "ELITE_CHANNEL_ID": 1004,
            "ADMIN_GROUP_ID": None,
            "SIGNALS_LIVE_TOPIC_ID": None,
        },
    )

    router.route({"event_type": "signal_event", "symbol": "EURUSD"}, now_ts=1720000600)

    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (False, "not_elite_member"))
    result = outcome_service.handle_vote_callback(user_id=7, signal_id="sig-warning", outcome="WIN", now_ts=1720000601)

    error_events = _read_jsonl(root / "observability" / "error_events.jsonl")
    warnings = [event for event in error_events if event["event_type"] == "warning"]

    assert result["accepted"] is False
    assert {event["data"]["code"] for event in warnings} >= {
        "distribution_invalid_event",
        "membership_verification_failed",
    }
    for event in warnings:
        assert obs.validate_event(event) == event


def test_outcome_panel_enabled_event_and_schema_compatibility(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    obs, _, outcome_service, root = _import_batch03_modules(tmp_path, monkeypatch)

    outcome_service.register_open_now(
        signal_id="sig-panel",
        elite_chat_id=1004,
        open_message_id=808,
        open_now_ts=1720000700,
        expiry_minutes=5,
    )

    outcome_events = _read_jsonl(root / "outcomes" / "outcomes.jsonl")
    panel_events = [event for event in outcome_events if event["event_type"] == "outcome_panel_enabled"]

    assert len(panel_events) == 1
    assert panel_events[0]["signal_id"] == "sig-panel"
    assert obs.validate_event(panel_events[0]) == panel_events[0]
