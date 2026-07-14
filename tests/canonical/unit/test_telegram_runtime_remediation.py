from __future__ import annotations

import importlib
import json
from datetime import datetime as real_datetime, timezone
from pathlib import Path

import pytest


def _message_update(chat_id: int, user_id: int, text: str, *, chat_type: str = "private", message_thread_id: int | None = None):
    message = {
        "chat": {"id": chat_id, "type": chat_type},
        "from": {"id": user_id},
        "text": text,
    }
    if message_thread_id is not None:
        message["message_thread_id"] = message_thread_id
    return {"message": message}


def _capture_send(monkeypatch: pytest.MonkeyPatch, module) -> list[dict]:
    calls: list[dict] = []

    def _send_message(chat_id: int, text: str, reply_markup=None, thread_id=None):
        calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
                "thread_id": thread_id,
            }
        )
        return {"ok": True}

    monkeypatch.setattr(module.telegram_publisher, "send_message", _send_message)
    return calls


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_start_response_mentions_shadow_mode(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("SHADOW_MODE", "true")
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=123, user_id=1, text="/start"))

    assert len(sends) == 1
    assert "online" in sends[0]["text"].lower()
    assert "SHADOW_MODE" in sends[0]["text"]
    assert "/help" in sends[0]["text"]


def test_help_command_uses_active_inventory(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=123, user_id=1, text="/help"))

    text = sends[0]["text"]
    assert "Read-only commands" in text
    assert "Mutation commands" in text
    for command in ("/start", "/help", "/status", "/admin", "/thresholds PRE|CONFIRM|OPEN <value>", "/roles_reload"):
        assert command in text
    assert "Admin commands require the configured admin control topic" in text


def test_status_command_ready_state(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    status_mod = fresh_imports("runtime.runtime_status")
    status_mod.write_status(
        "running",
        "BinaryBot runtime running",
        recovery_required=False,
        recovery_state="HEALTHY",
        telegram_enabled=True,
        telegram_polling_started=True,
        shadow_mode=True,
        market_data_state="READY",
    )
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=123, user_id=1, text="/status"))

    text = sends[0]["text"]
    assert "Overall: READY" in text
    assert "Market data: READY" in text
    assert "Broker execution: DISABLED" in text


def test_status_command_market_data_limited_state(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    status_mod = fresh_imports("runtime.runtime_status")
    status_mod.write_status(
        "running",
        "BinaryBot runtime running",
        recovery_required=False,
        recovery_state="HEALTHY",
        telegram_enabled=True,
        telegram_polling_started=True,
        market_data_state="MARKET_DATA_LIMITED",
        market_data_note="Twelve Data HTTP 429 active",
    )
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=123, user_id=1, text="/status"))

    text = sends[0]["text"]
    assert "Overall: MARKET_DATA_LIMITED" in text
    assert "Market data: MARKET_DATA_LIMITED" in text
    assert "429" in text


def test_unknown_slash_command_gets_explicit_reply(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=123, user_id=1, text="/does_not_exist"))

    assert sends[0]["text"] == "Unknown command. Use /help to view available commands."


def test_private_reply_does_not_force_message_thread_id(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "12345")
    bot = fresh_imports("core.bot_service")
    monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", 12345)
    monkeypatch.setattr(bot, "ADMIN_CONTROL_THREAD_ID", 777)
    monkeypatch.setattr(bot, "handle_admin_command_v2", lambda text, user_id: "ok")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=12345, user_id=1001, text="/admin"))

    assert sends[0]["thread_id"] is None


def test_topic_reply_preserves_originating_message_thread_id(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", -1001)
    monkeypatch.setattr(bot, "ADMIN_CONTROL_THREAD_ID", 999)
    monkeypatch.setattr(bot, "handle_admin_command_v2", lambda text, user_id: "ok")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(
        _message_update(
            chat_id=-1001,
            user_id=1001,
            text="/admin",
            chat_type="supergroup",
            message_thread_id=42,
        )
    )

    assert sends[0]["thread_id"] == 42


def test_admin_context_remains_fail_closed_for_commands(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=-1002, user_id=1001, text="/admin", chat_type="supergroup"))

    assert "Access denied" in sends[0]["text"]


def test_owner_private_admin_commands_allowed_without_admin_topic(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    monkeypatch.setattr(bot, "handle_admin_command_v2", lambda text, user_id: f"ok:{text}:{user_id}")
    sends = _capture_send(monkeypatch, bot)

    for cmd in (
        "/admin",
        "/strategy",
        "/thresholds",
        "/sr",
        "/spike",
        "/symbols",
        "/engine",
        "/debug",
        "/report",
        "/roles",
        "/affiliate",
    ):
        bot.process_update(_message_update(chat_id=1001, user_id=1001, text=cmd, chat_type="private"))

    assert len(sends) == 11
    assert all("Access denied" not in item["text"] for item in sends)
    assert all(item["thread_id"] is None for item in sends)


def test_owner_private_roles_reload_denied_outside_admin_topic(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=1001, user_id=1001, text="/roles_reload", chat_type="private"))

    assert "Access denied" in sends[0]["text"]


def test_non_owner_admin_commands_require_configured_admin_topic_thread(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    monkeypatch.setattr(bot, "handle_admin_command_v2", lambda text, user_id: "ok")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(
        _message_update(
            chat_id=-1001,
            user_id=2002,
            text="/admin",
            chat_type="supergroup",
            message_thread_id=42,
        )
    )
    bot.process_update(
        _message_update(
            chat_id=-1001,
            user_id=2002,
            text="/admin",
            chat_type="supergroup",
            message_thread_id=999,
        )
    )

    assert "Access denied" in sends[0]["text"]
    assert "Access denied" not in sends[1]["text"]


def test_owner_private_callback_navigation_restores_admin_panels(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    edits: list[dict] = []

    monkeypatch.setattr(
        bot,
        "handle_admin_command_v2",
        lambda text, user_id: "engine ok" if text.startswith("/engine") else "ok",
    )
    monkeypatch.setattr(
        bot.telegram_publisher,
        "edit_message",
        lambda chat_id, message_id, text, reply_markup: edits.append(
            {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": reply_markup}
        ),
    )

    bot.process_update(
        {
            "callback_query": {
                "id": "cb-1",
                "from": {"id": 1001},
                "data": "ADMIN_NAV:ENGINE",
                "message": {
                    "chat": {"id": 1001, "type": "private"},
                    "message_id": 7,
                    "text": "old",
                },
            }
        }
    )

    assert edits
    assert "Engine Panel" in edits[0]["text"]
    assert edits[0]["reply_markup"]["inline_keyboard"]


def test_non_owner_callback_navigation_requires_admin_topic_thread(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(
        {
            "callback_query": {
                "id": "cb-1",
                "from": {"id": 2002},
                "data": "ADMIN_NAV:HOME",
                "message": {
                    "chat": {"id": -1001, "type": "supergroup"},
                    "message_id": 7,
                    "message_thread_id": 42,
                    "text": "old",
                },
            }
        }
    )

    assert sends
    assert "Access denied" in sends[0]["text"]


def test_admin_topic_reload_confirmation_dialog_uses_callback_navigation(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    edits: list[dict] = []
    monkeypatch.setattr(
        bot.telegram_publisher,
        "edit_message",
        lambda chat_id, message_id, text, reply_markup: edits.append(
            {"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": reply_markup}
        ),
    )

    bot.process_update(
        {
            "callback_query": {
                "id": "cb-1",
                "from": {"id": 2002},
                "data": "ADMIN_NAV:RELOAD_ROLES_CONFIRM",
                "message": {
                    "chat": {"id": -1001, "type": "supergroup"},
                    "message_id": 7,
                    "message_thread_id": 999,
                    "text": "old",
                },
            }
        }
    )

    assert edits
    assert "Confirmation" in edits[0]["text"]
    assert "ADMIN_NAV:RELOAD_ROLES_EXEC" in str(edits[0]["reply_markup"])


def test_mutation_permission_check_still_blocks_unauthorized_users(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "5000")
    algo_path = canonical_runtime_root / "config" / "algo_params.json"
    before = algo_path.read_text(encoding="utf-8")
    bot = fresh_imports("core.bot_service")
    sends = _capture_send(monkeypatch, bot)

    bot.process_update(_message_update(chat_id=5000, user_id=9999, text="/thresholds PRE 65"))

    assert "unauthorized" in sends[0]["text"].lower()
    assert algo_path.read_text(encoding="utf-8") == before


def test_startup_notification_sequencing_in_railway_path(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    start_mod = fresh_imports("scripts.railway_start")
    boot = importlib.import_module("runtime.system_boot")
    notifications: list[tuple[str, str]] = []
    boot_calls: list[str] = []

    monkeypatch.setattr(start_mod, "initialize_for_railway", lambda base_dir=None: {"ok": True})
    monkeypatch.setattr(start_mod, "readiness_report", lambda base_dir=None: {"status": "ready"})
    monkeypatch.setattr(start_mod, "send_control_notification", lambda title, message: notifications.append((title, message)))
    monkeypatch.setattr(boot, "start_system", lambda: boot_calls.append("started"))

    assert start_mod.main() == 0
    assert notifications[0][0] == "BOT STARTING"
    assert boot_calls == ["started"]


def test_startup_blocked_notification_in_railway_path(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    start_mod = fresh_imports("scripts.railway_start")
    notifications: list[tuple[str, str]] = []

    monkeypatch.setattr(start_mod, "initialize_for_railway", lambda base_dir=None: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(start_mod, "send_control_notification", lambda title, message: notifications.append((title, message)))

    assert start_mod.main() == 1
    assert notifications[0][0] == "STARTUP BLOCKED"


def _fake_threads(monkeypatch: pytest.MonkeyPatch, boot):
    class _Thread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon

        def start(self):
            return None

    monkeypatch.setattr(boot.threading, "Thread", _Thread)
    monkeypatch.setattr(boot, "start_engine", lambda: None)
    monkeypatch.setattr(boot, "poll_updates", lambda: None)
    monkeypatch.setattr(boot, "scheduler_loop", lambda: None)


def test_no_false_bot_live_before_readiness_evaluation(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("RAILWAY_READINESS_EVALUATED", raising=False)
    monkeypatch.setenv("ENABLE_TELEGRAM", "false")
    boot = fresh_imports("runtime.system_boot")
    notifications: list[tuple[str, str]] = []

    monkeypatch.setattr(boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(
        boot,
        "record_start",
        lambda: {
            "restart_count": 0,
            "window_seconds": 60,
            "max_restarts": 3,
            "previous_shutdown_kind": "graceful",
            "recovery_required": False,
            "crash_loop": False,
        },
    )
    monkeypatch.setattr(boot.fsm_runtime, "load_state", lambda: None)
    monkeypatch.setattr(boot.distribution_router, "load_state", lambda: None)
    monkeypatch.setattr(boot, "send_control_notification", lambda title, message: notifications.append((title, message)))
    monkeypatch.setattr(boot.time, "sleep", lambda seconds: (_ for _ in ()).throw(SystemExit(0)))
    _fake_threads(monkeypatch, boot)

    with pytest.raises(SystemExit):
        boot.start_system()

    assert "BOT LIVE" not in [title for title, _ in notifications]


def test_recovery_and_degraded_notifications(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("RAILWAY_READINESS_EVALUATED", "1")
    monkeypatch.setenv("ENABLE_TELEGRAM", "false")
    boot = fresh_imports("runtime.system_boot")
    notifications: list[tuple[str, str]] = []

    monkeypatch.setattr(boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(
        boot,
        "record_start",
        lambda: {
            "restart_count": 1,
            "window_seconds": 60,
            "max_restarts": 3,
            "previous_shutdown_kind": "crash",
            "recovery_required": True,
            "crash_loop": False,
        },
    )
    monkeypatch.setattr(boot.fsm_runtime, "load_state", lambda: None)
    monkeypatch.setattr(boot.distribution_router, "load_state", lambda: None)
    monkeypatch.setattr(boot, "send_control_notification", lambda title, message: notifications.append((title, message)))
    monkeypatch.setattr(boot.time, "sleep", lambda seconds: (_ for _ in ()).throw(SystemExit(0)))
    _fake_threads(monkeypatch, boot)

    with pytest.raises(SystemExit):
        boot.start_system()

    titles = [title for title, _ in notifications]
    assert "RECOVERY STARTED" in titles
    assert "RECOVERY COMPLETED" in titles
    assert "DEGRADED SAFE MODE" in titles
    assert "BOT LIVE" in titles


def test_blocked_startup_notification(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    boot = fresh_imports("runtime.system_boot")
    notifications: list[tuple[str, str]] = []

    monkeypatch.setattr(boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(
        boot,
        "record_start",
        lambda: {
            "restart_count": 1,
            "window_seconds": 60,
            "max_restarts": 3,
            "previous_shutdown_kind": "crash",
            "recovery_required": True,
            "crash_loop": False,
        },
    )
    monkeypatch.setattr(boot.fsm_runtime, "load_state", lambda: (_ for _ in ()).throw(ValueError("invalid state")))
    monkeypatch.setattr(boot, "send_control_notification", lambda title, message: notifications.append((title, message)))

    boot.start_system()

    assert notifications[0][0] == "RECOVERY STARTED"
    assert notifications[-1][0] == "STARTUP BLOCKED"


def test_twelve_data_429_alert_aggregation_and_recovery(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ADMIN_PROOF_CHAT_ID", "-2001")
    monkeypatch.setenv("TWELVE_DATA_API_KEY", "offline-key")
    market = fresh_imports("runtime.market_client")
    obs = market.observability_logger
    status_mod = importlib.import_module("runtime.runtime_status")
    sends: list[str] = []
    network_calls: list[int] = []

    class _FakeDateTime:
        current_ts = 1_700_000_000

        @classmethod
        def now(cls, tz=None):
            return real_datetime.fromtimestamp(cls.current_ts, tz=tz or timezone.utc)

    class _Response429:
        status_code = 429
        text = "rate limited"

        def json(self):
            return {"status": "error"}

    class _Response200:
        status_code = 200
        text = "ok"

        def json(self):
            return {
                "values": [
                    {
                        "datetime": "2024-01-01 00:00:00",
                        "open": "1.1",
                        "high": "1.2",
                        "low": "1.0",
                        "close": "1.15",
                    }
                ]
            }

    responses = [_Response429(), _Response429(), _Response200()]

    def _get(*_args, **_kwargs):
        network_calls.append(1)
        return responses.pop(0)

    def _send_message(chat_id: int, text: str, reply_markup=None, thread_id=None):
        sends.append(text)
        return {"ok": True}

    obs._OPERATIONAL_INCIDENTS.clear()
    market._RATE_LIMIT_STATE.update({"active": False, "retry_after_ts": 0, "first_seen_ts": 0, "latest_seen_ts": 0, "count": 0})
    monkeypatch.setattr(market, "datetime", _FakeDateTime)
    monkeypatch.setattr(market.requests, "get", _get)
    monkeypatch.setattr(obs.telegram_publisher, "send_message", _send_message)

    with pytest.raises(market.MarketDataRateLimitError):
        market.fetch_klines("EUR/USD", "1min")
    assert len(sends) == 1
    assert status_mod.read_status()["market_data_state"] == "MARKET_DATA_LIMITED"

    _FakeDateTime.current_ts += 10
    with pytest.raises(market.MarketDataRateLimitError):
        market.fetch_klines("EUR/USD", "1min")
    assert len(sends) == 1
    assert len(network_calls) == 1

    _FakeDateTime.current_ts += 301
    with pytest.raises(market.MarketDataRateLimitError):
        market.fetch_klines("EUR/USD", "1min")
    assert len(sends) == 2

    _FakeDateTime.current_ts += 301
    candles = market.fetch_klines("EUR/USD", "1min")
    assert candles
    assert any("RECOVERED" in text for text in sends)
    assert status_mod.read_status()["market_data_state"] == "READY"


def test_canonical_error_event_shape_and_bounded_log_failure_growth(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    obs = fresh_imports("core.observability_logger")
    obs.log_error({"event_type": "error", "module": "engine_loop", "error": "boom", "symbol": "EUR/USD"})

    error_events = _read_jsonl(canonical_runtime_root / "observability" / "error_events.jsonl")
    assert error_events
    payload = error_events[0]["data"]
    assert payload["severity"] == "ERROR"
    assert payload["error_type"] == "engine_loop"
    assert payload["message"] == "boom"
    assert payload["context"]["symbol"] == "EUR/USD"

    original_append = obs._append_jsonl

    def _flaky_append(path: str, record: dict, *, sink: str):
        if sink != "error":
            raise OSError("disk full")
        return original_append(path, record, sink=sink)

    monkeypatch.setattr(obs, "_append_jsonl", _flaky_append)
    for _ in range(5):
        obs.log_event(
            obs.build_event(
                "engine_start",
                {"message": "loop"},
                source={"module": "test", "function": "bounded"},
            )
        )

    error_events = _read_jsonl(canonical_runtime_root / "observability" / "error_events.jsonl")
    observability_failures = [event for event in error_events if event["data"]["error_type"] == "observability_log_failed"]
    assert len(observability_failures) == 1


def test_admin_proof_local_persistence_survives_telegram_failure(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_PROOF_CHAT_ID", "-2001")
    ac = fresh_imports("core.admin_commands")
    obs = importlib.import_module("core.observability_logger")

    monkeypatch.setattr(obs.telegram_publisher, "send_message", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("telegram down")))

    result = ac.handle_admin_command("/thresholds PRE 65", 1001)

    assert "OK" in result
    proofs = (canonical_runtime_root / "observability" / "admin_proofs.jsonl").read_text(encoding="utf-8")
    assert proofs.strip()
