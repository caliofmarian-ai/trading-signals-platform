from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge_modules() -> None:
    prefixes = ("core.", "runtime.")
    exact = {"core", "runtime"}
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
        "FREE_LIMIT": 5,
        "BASIC_LIMIT": 20,
        "PRO_LIMIT": 50,
        "ELITE_LIMIT": None,
        "TZ": "Europe/London",
        "RESET_TIME": "23:59",
    }


def _prepare_runtime_root(tmp_path: Path, config_overrides: Dict[str, Any] | None = None) -> tuple[Path, Path]:
    root = tmp_path / "runtime"
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config = _base_channel_config()
    if config_overrides:
        config.update(config_overrides)
    config_path = config_dir / "channel_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return root, config_path


def _import_batch04_modules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_overrides: Dict[str, Any] | None = None,
) -> tuple[Any, Any, Any, Any, Any, Any, Any, Path]:
    root, config_path = _prepare_runtime_root(tmp_path, config_overrides=config_overrides)

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("OBS_DIR", str(root / "observability"))
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(root / "observability" / "engine_events.jsonl"))
    monkeypatch.setenv("FSM_EVENTS_LOG", str(root / "observability" / "fsm_events.jsonl"))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(root / "observability" / "distribution_events.jsonl"))
    monkeypatch.setenv("ADMIN_PROOFS_LOG", str(root / "observability" / "admin_proofs.jsonl"))
    monkeypatch.setenv("ERROR_EVENTS_LOG", str(root / "observability" / "error_events.jsonl"))
    monkeypatch.setenv("OUTCOMES_LOG", str(root / "outcomes" / "outcomes.jsonl"))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("ELITE_CHANNEL_ID", "1004")
    monkeypatch.setenv("COMMUNITY_FEEDBACK_SALT", "test-salt")
    monkeypatch.setenv("ADMIN_USER_ID", "7")

    _purge_modules()
    importlib.invalidate_caches()

    observability_logger = importlib.import_module("core.observability_logger")
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    outcome_service = importlib.import_module("core.outcome_service")
    distribution_router = importlib.import_module("core.distribution_router")
    telegram_updates = importlib.import_module("runtime.telegram_updates")
    bot_service = importlib.import_module("core.bot_service")
    analytics_engine = importlib.import_module("core.analytics_engine")

    distribution_router.DIST_STATE_PATH = str(root / "state" / "dist_state.json")
    distribution_router.CHANNEL_CONFIG_PATHS = [str(config_path)]
    outcome_service.OUTCOMES_JSONL = str(root / "outcomes" / "outcomes.jsonl")
    outcome_service.OPEN_REGISTRY_JSON = str(root / "outcomes" / "open_now_registry.json")
    outcome_service.OUTCOMES_INDEX_JSON = str(root / "outcomes" / "outcomes_index.json")
    bot_service.OUTCOMES_PATH = str(root / "state" / "outcomes.json")
    analytics_engine.OUTCOMES_PATH = str(root / "outcomes" / "outcomes.jsonl")
    monkeypatch.setattr(telegram_updates.time, "time", lambda: 1720000306)
    monkeypatch.setattr(bot_service.time, "time", lambda: 1720000306)

    return (
        observability_logger,
        telemetry,
        outcome_service,
        distribution_router,
        telegram_updates,
        bot_service,
        analytics_engine,
        root,
    )


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _signal_event(signal_id: str = "sig-001") -> Dict[str, Any]:
    return {
        "event_type": "signal_event",
        "stage": "OPEN_NOW",
        "signal_id": signal_id,
        "symbol": "EURUSD",
        "timeframe": "M1",
        "direction": "BUY",
        "score_total": 88.5,
        "buffer_mode": "MEDIUM",
        "buffer_price": 1.2345,
        "expiry_minutes": 5,
        "candle_ts": 1720000000,
        "created_ts": 1720000005,
        "payload": {"price": 1.11111, "test": True},
        "TPS": 57.1,
    }


def _callback_update(
    data: str,
    *,
    chat_id: int = 1004,
    message_id: int = 808,
    user_id: int = 7,
    callback_id: str = "cb-001",
) -> Dict[str, Any]:
    return {
        "callback_query": {
            "id": callback_id,
            "data": data,
            "from": {"id": user_id},
            "message": {
                "message_id": message_id,
                "chat": {"id": chat_id},
                "text": "OPEN NOW EURUSD",
            },
        }
    }


def _register_signal(outcome_service: Any, *, signal_id: str = "sig-001", chat_id: int = 1004, message_id: int = 808) -> None:
    outcome_service.register_open_now(
        signal_id=signal_id,
        elite_chat_id=chat_id,
        open_message_id=message_id,
        open_now_ts=1720000005,
        expiry_minutes=5,
        symbol="EURUSD",
        direction="BUY",
        timeframe="M1",
        callback_route="ELITE" if chat_id == 1004 else "ADMIN_SIGNALS_LIVE",
    )


def test_trade_temporal_telemetry_import_is_side_effect_free(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    root, _ = _prepare_runtime_root(tmp_path)
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("OBS_DIR", str(root / "observability"))

    def _fail_get(*args, **kwargs):
        calls.append("get")
        raise AssertionError("network call during import")

    def _fail_post(*args, **kwargs):
        calls.append("post")
        raise AssertionError("network call during import")

    def _fail_thread(*args, **kwargs):
        raise AssertionError("thread started during import")

    monkeypatch.setattr("requests.get", _fail_get)
    monkeypatch.setattr("requests.post", _fail_post)
    monkeypatch.setattr("threading.Thread", _fail_thread)

    _purge_modules()
    importlib.invalidate_caches()
    assert importlib.import_module("core.trade_temporal_telemetry") is not None
    assert calls == []


def test_trade_registration_persists_required_fields_uses_utc_and_survives_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, telemetry, *_rest, root = _import_batch04_modules(tmp_path, monkeypatch)

    result = telemetry.register_open_now_trade(_signal_event(), now_ts=1720000005)

    assert result["status"] == "registered"
    registry = _read_json(root / "observability" / "open_trades_registry.json")
    record = registry["trades"]["sig-001"]
    assert record["signal_id"] == "sig-001"
    assert record["symbol"] == "EURUSD"
    assert record["direction"] == "BUY"
    assert record["entry_price"] == pytest.approx(1.11111)
    assert record["open_ts"] == 1720000005
    assert record["expiry_ts"] == 1720000305
    assert record["mid_expiry_ts"] == 1720000155
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", record["open_ts_utc"])
    assert telemetry.get_open_trade("sig-001")["trade_id"] == "sig-001"

    _purge_modules()
    importlib.invalidate_caches()
    telemetry_reloaded = importlib.import_module("core.trade_temporal_telemetry")
    assert telemetry_reloaded.get_open_trade("sig-001")["expiry_ts"] == 1720000305

    engine_events = _read_jsonl(root / "observability" / "engine_events.jsonl")
    registration_events = [
        event for event in engine_events
        if event["event_type"] == "decision" and event["data"]["decision_kind"] == "OPEN_NOW_REGISTERED"
    ]
    assert len(registration_events) == 1
    assert obs.validate_event(registration_events[0]) == registration_events[0]


def test_trade_registration_is_idempotent_but_conflicts_and_invalid_input_fail_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, telemetry, *_rest, root = _import_batch04_modules(tmp_path, monkeypatch)

    first = telemetry.register_open_now_trade(_signal_event(), now_ts=1720000005)
    second = telemetry.register_open_now_trade(_signal_event(), now_ts=1720000005)
    assert first["status"] == "registered"
    assert second["status"] == "already_registered"
    registry = _read_json(root / "observability" / "open_trades_registry.json")
    assert list(registry["trades"].keys()) == ["sig-001"]

    bad_event = _signal_event()
    bad_event["expiry_minutes"] = 6
    with pytest.raises(ValueError, match="conflicting OPEN_NOW registration"):
        telemetry.register_open_now_trade(bad_event, now_ts=1720000005)

    missing_field = _signal_event("sig-002")
    missing_field.pop("signal_id")
    with pytest.raises(ValueError, match="signal_id"):
        telemetry.register_open_now_trade(missing_field, now_ts=1720000005)

    invalid_type = _signal_event("sig-003")
    invalid_type["expiry_minutes"] = "five"
    with pytest.raises(ValueError, match="expiry_minutes must be an integer"):
        telemetry.register_open_now_trade(invalid_type, now_ts=1720000005)

    assert "sig-002" not in registry["trades"]
    assert "sig-003" not in registry["trades"]


def test_trade_registration_failed_persistence_and_observability_do_not_create_false_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, telemetry, *_rest, root = _import_batch04_modules(tmp_path, monkeypatch)

    monkeypatch.setattr(telemetry.storage, "save_json_atomic", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError, match="disk full"):
        telemetry.register_open_now_trade(_signal_event(), now_ts=1720000005)
    assert not (root / "observability" / "open_trades_registry.json").exists()
    assert _read_jsonl(root / "observability" / "engine_events.jsonl") == []

    _purge_modules()
    importlib.invalidate_caches()
    _, telemetry, *_rest, root = _import_batch04_modules(tmp_path, monkeypatch)
    monkeypatch.setattr(telemetry.observability_logger, "log_event", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("obs fail")))
    result = telemetry.register_open_now_trade(_signal_event(), now_ts=1720000005)
    assert result["status"] == "registered"
    assert _read_json(root / "observability" / "open_trades_registry.json")["trades"]["sig-001"]["signal_id"] == "sig-001"


def test_valid_callback_reaches_single_canonical_mutation_with_privacy_and_observability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, _, outcome_service, _, telegram_updates, bot_service, analytics_engine, root = _import_batch04_modules(tmp_path, monkeypatch)
    _register_signal(outcome_service)
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (True, "ok"))

    acks: list[Dict[str, Any]] = []
    bot_calls: list[Dict[str, Any]] = []

    monkeypatch.setattr(telegram_updates.requests, "post", lambda url, json, timeout: acks.append(json) or {"ok": True})
    monkeypatch.setattr(bot_service, "process_update", lambda update: bot_calls.append(update))

    telegram_updates.process_update(_callback_update("VOTE_|sig-001|WIN"))

    assert bot_calls == []
    raw_records = [row for row in _read_jsonl(root / "outcomes" / "outcomes.jsonl") if row["event_type"] == "user_outcome_record"]
    outcome_events = [row for row in _read_jsonl(root / "outcomes" / "outcomes.jsonl") if row["event_type"] == "user_outcome"]
    assert len(raw_records) == 1
    assert raw_records[0]["signal_id"] == "sig-001"
    assert raw_records[0]["user_id"].startswith("M-")
    assert raw_records[0]["user_id"] != "7"
    assert "telegram_user_id" not in raw_records[0]
    assert len(outcome_events) == 1
    assert outcome_events[0]["data"]["accepted"] is True
    assert obs.validate_event(outcome_events[0]) == outcome_events[0]
    assert acks == [{"callback_query_id": "cb-001", "text": "Outcome recorded.", "show_alert": False}]
    assert analytics_engine.get_user_stats(7, 30)["wins"] == 1
    assert not Path(bot_service.OUTCOMES_PATH).exists()


def test_callback_parser_rejects_malformed_unknown_and_unknown_signal_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, outcome_service, _, telegram_updates, _, _, root = _import_batch04_modules(tmp_path, monkeypatch)
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (True, "ok"))

    assert outcome_service.handle_vote_callback_data(callback_data="OTHER", user_id=7, now_ts=1720000306)["reason"] == "unknown_action"
    assert outcome_service.handle_vote_callback_data(callback_data="VOTE_|only-two-parts", user_id=7, now_ts=1720000306)["reason"] == "malformed_callback_payload"
    assert outcome_service.handle_vote_callback_data(callback_data="VOTE_|sig-001|MAYBE", user_id=7, now_ts=1720000306)["reason"] == "invalid_outcome"
    assert outcome_service.handle_vote_callback_data(callback_data="VOTE_|missing|WIN", user_id=7, now_ts=1720000306)["reason"] == "unknown_signal_id"

    acks: list[Dict[str, Any]] = []
    monkeypatch.setattr(telegram_updates.requests, "post", lambda url, json, timeout: acks.append(json) or {"ok": True})
    telegram_updates.process_update(_callback_update("VOTE_|missing|WIN"))
    assert acks[-1]["text"] == "Unknown signal."
    assert [row for row in _read_jsonl(root / "outcomes" / "outcomes.jsonl") if row["event_type"] == "user_outcome_record"] == []


def test_callback_security_configuration_and_context_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, outcome_service, _, telegram_updates, _, _, root = _import_batch04_modules(tmp_path, monkeypatch)
    _register_signal(outcome_service)
    monkeypatch.setenv("COMMUNITY_FEEDBACK_SALT", "")

    result = outcome_service.handle_vote_callback_data(
        callback_data="VOTE_|sig-001|WIN",
        user_id=7,
        now_ts=1720000306,
        chat_id=1004,
        message_id=808,
    )
    assert result["accepted"] is False
    assert result["reason"] == "community_feedback_salt_missing"

    monkeypatch.setenv("COMMUNITY_FEEDBACK_SALT", "test-salt")
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (True, "ok"))
    unauthorized = outcome_service.handle_vote_callback_data(
        callback_data="VOTE_|sig-001|WIN",
        user_id=7,
        now_ts=1720000306,
        chat_id=9999,
        message_id=9999,
    )
    assert unauthorized["reason"] == "unauthorized_callback_context"
    assert [row for row in _read_jsonl(root / "outcomes" / "outcomes.jsonl") if row["event_type"] == "user_outcome_record"] == []

    acks: list[Dict[str, Any]] = []
    monkeypatch.setattr(telegram_updates.requests, "post", lambda url, json, timeout: acks.append(json) or {"ok": True})
    telegram_updates.process_update(_callback_update("VOTE_|sig-001|WIN", chat_id=9999, message_id=9999))
    assert acks[-1]["text"] == "Unauthorized callback context."


def test_duplicate_callback_and_restart_replay_are_idempotent_without_duplicate_success_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, _, outcome_service, _, telegram_updates, _, _, root = _import_batch04_modules(tmp_path, monkeypatch)
    _register_signal(outcome_service)
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (True, "ok"))

    acks: list[Dict[str, Any]] = []
    monkeypatch.setattr(telegram_updates.requests, "post", lambda url, json, timeout: acks.append(json) or {"ok": True})

    telegram_updates.process_update(_callback_update("VOTE_|sig-001|WIN"))
    telegram_updates.process_update(_callback_update("VOTE_|sig-001|WIN"))

    _purge_modules()
    importlib.invalidate_caches()
    obs, _, outcome_service, _, telegram_updates, _, _, root = _import_batch04_modules(tmp_path, monkeypatch)
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (True, "ok"))
    monkeypatch.setattr(telegram_updates.requests, "post", lambda url, json, timeout: acks.append(json) or {"ok": True})
    telegram_updates.process_update(_callback_update("VOTE_|sig-001|WIN"))

    rows = _read_jsonl(root / "outcomes" / "outcomes.jsonl")
    raw_records = [row for row in rows if row["event_type"] == "user_outcome_record"]
    success_events = [
        row for row in rows
        if row["event_type"] == "user_outcome" and row["data"]["accepted"] is True
    ]
    assert len(raw_records) == 1
    assert len(success_events) == 1
    assert obs.validate_event(success_events[0]) == success_events[0]
    assert acks[0]["text"] == "Outcome recorded."
    assert acks[1]["text"] == "Outcome already recorded."
    assert acks[2]["text"] == "Outcome already recorded."


def test_rejections_do_not_mutate_state_and_emit_canonical_failure_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, _, outcome_service, _, telegram_updates, _, _, root = _import_batch04_modules(tmp_path, monkeypatch)
    _register_signal(outcome_service)
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (False, "not_elite_member"))

    acks: list[Dict[str, Any]] = []
    monkeypatch.setattr(telegram_updates.requests, "post", lambda url, json, timeout: acks.append(json) or {"ok": True})
    telegram_updates.process_update(_callback_update("VOTE_|sig-001|WIN"))

    warnings = [row for row in _read_jsonl(root / "observability" / "error_events.jsonl") if row["event_type"] == "warning"]
    assert acks[-1]["text"] == "Elite membership required."
    assert [row for row in _read_jsonl(root / "outcomes" / "outcomes.jsonl") if row["event_type"] == "user_outcome_record"] == []
    assert {row["data"]["code"] for row in warnings} >= {"membership_verification_failed"}
    for warning in warnings:
        assert obs.validate_event(warning) == warning


def test_failed_persistence_is_not_acknowledged_as_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, outcome_service, _, telegram_updates, _, _, root = _import_batch04_modules(tmp_path, monkeypatch)
    _register_signal(outcome_service)
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (True, "ok"))
    monkeypatch.setattr(outcome_service.storage, "append_jsonl", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("no space")))

    acks: list[Dict[str, Any]] = []
    monkeypatch.setattr(telegram_updates.requests, "post", lambda url, json, timeout: acks.append(json) or {"ok": True})

    telegram_updates.process_update(_callback_update("VOTE_|sig-001|WIN"))

    assert acks[-1]["text"] == "Outcome could not be recorded."
    assert [row for row in _read_jsonl(root / "outcomes" / "outcomes.jsonl") if row["event_type"] == "user_outcome_record"] == []
    index_path = root / "outcomes" / "outcomes_index.json"
    if index_path.exists():
        index = _read_json(index_path)
        assert index["voted"] == {}
        assert index["processed_callbacks"] == {}


def test_legacy_bot_service_path_forwards_to_canonical_service_without_admin_store_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, outcome_service, _, _, bot_service, _, root = _import_batch04_modules(tmp_path, monkeypatch)
    _register_signal(outcome_service, chat_id=2001, message_id=909)
    monkeypatch.setattr(outcome_service, "_elite_membership_ok", lambda user_id: (True, "ok"))
    monkeypatch.setattr(bot_service.telegram_publisher, "edit_message", lambda *args, **kwargs: None)
    monkeypatch.setattr(bot_service.telegram_publisher, "send_message", lambda *args, **kwargs: None)

    bot_service.process_update(_callback_update("VOTE_|sig-001|WIN", chat_id=2001, message_id=909))

    rows = _read_jsonl(root / "outcomes" / "outcomes.jsonl")
    assert [row for row in rows if row["event_type"] == "user_outcome_record"]
    assert not Path(bot_service.OUTCOMES_PATH).exists()


def test_outcome_panel_registration_tracks_multiple_callback_contexts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    obs, _, outcome_service, _, _, _, _, root = _import_batch04_modules(tmp_path, monkeypatch)

    first = outcome_service.register_open_now(
        signal_id="sig-ctx",
        elite_chat_id=1004,
        open_message_id=808,
        open_now_ts=1720000005,
        expiry_minutes=5,
        symbol="EURUSD",
        direction="BUY",
        timeframe="M1",
        callback_route="ELITE",
    )
    second = outcome_service.register_open_now(
        signal_id="sig-ctx",
        elite_chat_id=2001,
        open_message_id=909,
        open_now_ts=1720000005,
        expiry_minutes=5,
        symbol="EURUSD",
        direction="BUY",
        timeframe="M1",
        callback_route="ADMIN_SIGNALS_LIVE",
    )

    assert first["status"] == "registered"
    assert second["status"] == "updated_context"
    registry = _read_json(root / "outcomes" / "open_now_registry.json")
    contexts = registry["sig-ctx"]["callback_contexts"]
    assert len(contexts) == 2
    outcome_events = [row for row in _read_jsonl(root / "outcomes" / "outcomes.jsonl") if row["event_type"] == "outcome_panel_enabled"]
    assert len(outcome_events) == 2
    for event in outcome_events:
        assert obs.validate_event(event) == event


def test_signal_engine_can_import_trade_temporal_telemetry_module_after_batch04(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _import_batch04_modules(tmp_path, monkeypatch)
    signal_engine = importlib.import_module("core.signal_engine")
    telemetry = signal_engine._load_trade_temporal_telemetry()
    assert telemetry.register_open_now_trade is not None
