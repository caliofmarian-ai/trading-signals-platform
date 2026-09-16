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

from billing import notification_scheduler, support_runtime
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
    # In Railway, the immutable deployment identifier is more authoritative
    # than a generic RUN_ID, which may be a local/operator placeholder.
    for name in ("RAILWAY_DEPLOYMENT_ID", "RAILWAY_SERVICE_ID", "RUN_ID"):
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

    is_healthy_start = event == "poller_started"
    if not is_healthy_start:
        observability_logger.log_warning(
            warn_type="telegram_poller_startup",
            message="Telegram polling instance state changed",
            context=payload,
            source={"module": "telegram_updates", "function": "poll_updates"},
        )

    try:
        print(
            json.dumps(payload, sort_keys=True),
            file=sys.stdout if is_healthy_start else sys.stderr,
            flush=True,
        )
    except Exception:
        pass


def _run_billing_scheduler_safely() -> None:
    """Run the restart-safe billing scheduler without risking poller liveness."""
    try:
        notification_scheduler.maybe_run_notification_cycle()
    except Exception as exc:
        observability_logger.log_error(
            {
                "event_type": "error",
                "module": "telegram_updates",
                "function": "billing_notification_scheduler",
                "error": telegram_publisher._sanitize(str(exc)),
            }
        )


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
            _run_billing_scheduler_safely()

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


def _ack_callback(callback_id: Any, text: str = "") -> None:
    """Acknowledge a callback, optionally with a bounded Telegram toast."""
    if not callback_id:
        return
    ack_text = str(text or "").strip()
    if len(ack_text) > 200:
        ack_text = f"{ack_text[:197]}..."
    try:
        if ack_text:
            telegram_publisher.answer_callback_query(str(callback_id), text=ack_text)
        else:
            telegram_publisher.answer_callback_query(str(callback_id))
    except Exception as e:
        safe_error = telegram_publisher._sanitize(str(e))
        observability_logger.log_warning(
            warn_type="callback_ack_failed",
            message="Failed to acknowledge Telegram callback",
            context={"callback_query_id": str(callback_id), "error": safe_error},
            source={"module": "telegram_updates", "function": "_ack_callback"},
        )


def _try_private_support_message(update: Dict[str, Any]) -> bool:
    message = update.get("message")
    if not isinstance(message, dict):
        return False
    try:
        result = support_runtime.handle_private_text_message(
            message,
            now_ts=int(time.time()),
        )
    except Exception as exc:
        observability_logger.log_error(
            {
                "event_type": "error",
                "module": "telegram_updates",
                "function": "support_private_message",
                "error": telegram_publisher._sanitize(str(exc)),
            }
        )
        return False
    if not result.get("handled"):
        return False
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is not None:
        try:
            telegram_publisher.send_message(
                chat_id=int(chat_id),
                text=(
                    f"Support case {result.get('case_id')}: message recorded. "
                    "The support team can reply through the audited case."
                ),
            )
        except Exception as exc:
            observability_logger.log_warning(
                warn_type="support_client_ack_failed",
                message="Support message was recorded but client acknowledgement failed",
                context={
                    "case_id": result.get("case_id"),
                    "error": telegram_publisher._sanitize(str(exc)),
                },
                source={"module": "telegram_updates", "function": "_try_private_support_message"},
            )
    return True


def _maybe_open_support_case(client_intent_id: Any) -> Optional[Dict[str, Any]]:
    if not client_intent_id:
        return None
    try:
        result = support_runtime.open_case_for_client_intent_if_needed(
            str(client_intent_id),
            now_ts=int(time.time()),
        )
        return result
    except Exception as exc:
        observability_logger.log_error(
            {
                "event_type": "error",
                "module": "telegram_updates",
                "function": "support_case_open",
                "error": telegram_publisher._sanitize(str(exc)),
            }
        )
        return None


def process_update(update: Dict[str, Any]):

    # private support message — only intercepts a non-command text when the
    # Telegram identity maps uniquely to a subscriber with exactly one active
    # support case. All other messages continue through the existing bot path.
    if "message" in update:
        if _try_private_support_message(update):
            return
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

        if data and data.startswith(notification_scheduler.CALLBACK_PREFIX):
            if chat_id is None:
                _ack_callback(callback_id, "Billing action unavailable in this context.")
                return
            try:
                result = notification_scheduler.handle_telegram_callback(
                    telegram_user_id=int(user_id),
                    telegram_chat_id=int(chat_id),
                    callback_data=str(data),
                    now_ts=int(time.time()),
                )
                ack_text = str(result.get("ack_text") or "")
                if result.get("accepted") and result.get("client_intent_id"):
                    case_result = _maybe_open_support_case(result.get("client_intent_id"))
                    if case_result and case_result.get("record"):
                        case_id = str(case_result["record"].get("case_id") or "")
                        if case_result.get("status") in {"OPENED", "EXISTS"} and case_id:
                            ack_text = (
                                f"{ack_text} Support case {case_id} is open; "
                                "send your next private message to add it to the case."
                            ).strip()
                _ack_callback(callback_id, ack_text)
            except Exception as exc:
                observability_logger.log_error(
                    {
                        "event_type": "error",
                        "module": "telegram_updates",
                        "function": "billing_callback",
                        "error": telegram_publisher._sanitize(str(exc)),
                    }
                )
                _ack_callback(callback_id, "Billing action could not be recorded.")
            return

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

        result = bot_service.process_update(update)
        # Acknowledge APP: and ADMIN_NAV: callbacks so Telegram dismisses the
        # loading spinner. Recovery paths may add a short user-visible toast;
        # all normal callbacks retain the empty acknowledgement. VOTE_
        # callbacks are already acknowledged above by _answer_callback_query.
        ack_text = (
            str(result.get("callback_ack_text") or "")
            if isinstance(result, dict)
            else ""
        )
        _ack_callback(callback_id, ack_text)


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
