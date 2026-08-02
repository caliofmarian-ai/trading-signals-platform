# /opt/binarybot/runtime/telegram_updates.py
# BinaryBot — Telegram Updates Poller

from __future__ import annotations

import os
import json
import sys
import threading
import time
import requests
from typing import Dict, Any, Optional

from core import bot_service
from core import outcome_service
from core import observability_logger
from core import telegram_publisher
from core import telegram_app_nav


def _get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")
    return token


def _base_url() -> str:
    return f"https://api.telegram.org/bot{_get_bot_token()}"

POLL_INTERVAL = 1.5

LAST_UPDATE_ID: Optional[int] = None
_POLLER_LOCK = threading.Lock()
_POLLER_STARTED = False

# Heartbeat: timestamp of the last successful getUpdates call (or 0 if never).
# Updated atomically by the poller thread; read by liveness checks.
_POLLER_LAST_HEARTBEAT: float = 0.0
_POLLER_HEARTBEAT_LOCK = threading.Lock()
# If no heartbeat is recorded within this window the poller is considered stalled.
POLLER_HEARTBEAT_TIMEOUT_SEC: float = 120.0


def _update_poller_heartbeat() -> None:
    global _POLLER_LAST_HEARTBEAT
    with _POLLER_HEARTBEAT_LOCK:
        _POLLER_LAST_HEARTBEAT = time.monotonic()


def get_poller_heartbeat_age() -> Optional[float]:
    """Return seconds since the last poller heartbeat, or None if never started."""
    with _POLLER_HEARTBEAT_LOCK:
        ts = _POLLER_LAST_HEARTBEAT
    if ts == 0.0:
        return None
    return time.monotonic() - ts


def is_poller_alive() -> bool:
    """Return True when the poller thread has produced a recent heartbeat."""
    age = get_poller_heartbeat_age()
    if age is None:
        return False
    return age < POLLER_HEARTBEAT_TIMEOUT_SEC


def _runtime_instance_id() -> str:
    for name in ("RUN_ID", "RAILWAY_DEPLOYMENT_ID", "RAILWAY_SERVICE_ID"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return f"pid-{os.getpid()}"


def _emit_poller_startup(event: str, extra: Dict[str, Any]) -> None:
    payload = {
        "event": event,
        "component": "telegram_poller",
        "pid": os.getpid(),
        "runtime_instance_id": _runtime_instance_id(),
        "deployment_identifier": os.getenv("RAILWAY_DEPLOYMENT_ID", "").strip() or "unknown",
    }
    payload.update(extra)
    observability_logger.log_warning(
        warn_type="telegram_poller_startup",
        message="Telegram polling instance state changed",
        context=payload,
        source={"module": "telegram_updates", "function": "poll_updates"},
    )
    try:
        print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)
    except Exception:
        pass


def poll_updates():
    global LAST_UPDATE_ID, _POLLER_STARTED
    with _POLLER_LOCK:
        if _POLLER_STARTED:
            _emit_poller_startup("duplicate_poller_blocked", {"last_update_id": LAST_UPDATE_ID})
            return
        _POLLER_STARTED = True
    _emit_poller_startup(
        "poller_started",
        {
            "state_path": telegram_app_nav.get_runtime_diagnostics().get("resolved_state_path"),
            "active_ui_initialized": telegram_app_nav.get_runtime_diagnostics().get("initialized"),
        },
    )

    while True:
        try:
            params: Dict[str, Any] = {"timeout": 30}

            if LAST_UPDATE_ID:
                params["offset"] = LAST_UPDATE_ID

            r = requests.get(
                f"{_base_url()}/getUpdates",
                params=params,
                timeout=35,
            )

            data = r.json()

            if not data.get("ok"):
                time.sleep(POLL_INTERVAL)
                continue

            # Record a heartbeat after every successful getUpdates response
            # (including empty ones) so liveness checks can verify the thread
            # is not stalled.
            _update_poller_heartbeat()

            updates = data.get("result", [])

            for update in updates:
                # Advance the offset BEFORE processing so that even a failed
                # update does not block the next getUpdates call.  An
                # individual update failure is contained and logged without
                # stopping the poller loop.
                LAST_UPDATE_ID = update["update_id"] + 1

                try:
                    process_update(update)
                except Exception as update_exc:
                    safe_error = telegram_publisher._sanitize(str(update_exc))
                    observability_logger.log_error({
                        "event_type": "error",
                        "module": "telegram_updates",
                        "function": "poll_updates_per_update",
                        "update_id": update.get("update_id"),
                        "error": safe_error,
                    })

        except Exception as e:
            # Sanitize the exception string to strip any embedded bot token
            # (requests exceptions can embed the full URL including the token).
            safe_error = telegram_publisher._sanitize(str(e))
            observability_logger.log_error({
                "event_type": "error",
                "module": "telegram_updates",
                "error": safe_error,
            })

            time.sleep(3)


def _ack_callback(callback_id: Any) -> None:
    """Send an empty answerCallbackQuery to dismiss the Telegram loading spinner."""
    if not callback_id:
        return
    try:
        telegram_publisher.answer_callback_query(str(callback_id))
    except Exception as e:
        safe_error = telegram_publisher._sanitize(str(e))
        observability_logger.log_warning(
            warn_type="callback_ack_failed",
            message="Failed to acknowledge Telegram callback",
            context={"callback_query_id": str(callback_id), "error": safe_error},
            source={"module": "telegram_updates", "function": "_ack_callback"},
        )


def process_update(update: Dict[str, Any]):

    # message
    if "message" in update:
        bot_service.process_update(update)
        return

    # callback button
    if "callback_query" in update:
 
        cb = update["callback_query"]
 
        data = cb.get("data")
        callback_id = cb.get("id")
        user_id = cb["from"]["id"]
        message = cb.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        message_id = message.get("message_id")
 
        if data and data.startswith("VOTE_"):
            result = outcome_service.handle_vote_callback_data(
                callback_data=data,
                user_id=int(user_id),
                now_ts=int(time.time()),
                chat_id=int(chat_id) if chat_id is not None else None,
                message_id=int(message_id) if message_id is not None else None,
            )
            _answer_callback_query(callback_id, result)
            return

        bot_service.process_update(update)
        # Acknowledge APP: and ADMIN_NAV: callbacks so Telegram dismisses the
        # loading spinner.  VOTE_ callbacks are already acknowledged above via
        # _answer_callback_query which encodes the outcome text.
        _ack_callback(callback_id)


def _answer_callback_query(callback_id: Any, result: Dict[str, Any]) -> None:
    if not callback_id:
        return

    accepted = bool(result.get("accepted"))
    reason = str(result.get("reason") or "")
    if accepted and reason == "ok":
        text = "Outcome recorded."
        show_alert = False
    elif accepted and reason == "already_processed":
        text = "Outcome already recorded."
        show_alert = False
    else:
        text = {
            "elite_membership_required": "Elite membership required.",
            "unknown_signal_id": "Unknown signal.",
            "unauthorized_callback_context": "Unauthorized callback context.",
            "malformed_callback_payload": "Malformed callback payload.",
            "missing_callback_payload": "Missing callback payload.",
            "unknown_action": "Unknown callback action.",
            "invalid_outcome": "Invalid outcome.",
            "already_voted": "Outcome already submitted.",
            "vote_window_closed": "Vote window closed.",
            "too_early": "Vote not open yet.",
            "bot_token_missing": "Outcome processing unavailable.",
            "elite_channel_id_missing": "Outcome processing unavailable.",
            "community_feedback_salt_missing": "Outcome processing unavailable.",
            "outcome_security_config_missing": "Outcome processing unavailable.",
            "persistence_failed": "Outcome could not be recorded.",
        }.get(reason, "Outcome rejected.")
        show_alert = False

    try:
        requests.post(
            f"{_base_url()}/answerCallbackQuery",
            json={
                "callback_query_id": callback_id,
                "text": text,
                "show_alert": show_alert,
            },
            timeout=10,
        )
    except Exception:
        observability_logger.log_warning(
            warn_type="callback_ack_failed",
            message="Failed to acknowledge Telegram callback",
            context={
                "callback_query_id": str(callback_id),
                "result_reason": reason,
                "accepted": accepted,
            },
            source={"module": "telegram_updates", "function": "_answer_callback_query"},
        )