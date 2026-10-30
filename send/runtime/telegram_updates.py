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

from billing import membership_scheduler, notification_scheduler, support_runtime
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

# Only strictly read-only, already validated navigation can be acknowledged
# before the potentially slow Telegram edit/send and persisted-state writes.
# Payment, voting, mutations, malformed and recovery callbacks retain their
# original post-processing acknowledgements and user-visible toasts.
_FAST_ACK_OWNER_ADMIN_ACTIONS = frozenset({
    "ADMIN_NAV:HOME",
    "ADMIN_NAV:OPERATIONS",
    "ADMIN_NAV:SYSHEALTH",
    "ADMIN_NAV:SYMBOLS_COV",
    "ADMIN_NAV:DECISION_VIS",
    "ADMIN_NAV:DISTRIBUTION",
    "ADMIN_NAV:RESEARCH",
    "ADMIN_NAV:INTELLIGENCE",
})
_SLOW_CALLBACK_THRESHOLD_MS = 1500
_SLOW_CALLBACK_REMINDER_SECONDS = 60.0
_LAST_SLOW_CALLBACK_LOG_MONOTONIC = 0.0
_SLOW_CALLBACK_LOG_LOCK = threading.Lock()

# Heartbeat: timestamp of the last successful getUpdates call (or 0 if never).
# Updated atomically by the poller thread; read by liveness checks.
_POLLER_LAST_HEARTBEAT: float = 0.0
POLLER_HEARTBEAT_TIMEOUT_SEC: float = 120.0
_POLLER_HEARTBEAT_LOCK = threading.Lock()


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
    """Run billing schedulers independently without risking poller liveness."""
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

    try:
        membership_scheduler.maybe_run_membership_cycle()
    except Exception as exc:
        observability_logger.log_error(
            {
                "event_type": "error",
                "module": "telegram_updates",
                "function": "billing_membership_scheduler",
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


def _fast_ack_safe_for_navigation(update: Dict[str, Any]) -> bool:
    """Fail closed: ACK early only known, non-mutating and current UI routes.

    This is an optimization hint, not authorization: bot_service still checks
    all permissions, context and generation before any rendering or mutation.
    The conservative selection protects recovery, billing and voting toasts.
    """
    try:
        cb = update.get("callback_query")
        if not isinstance(cb, dict):
            return False
        data = cb.get("data")
        message = cb.get("message")
        actor = cb.get("from")
        if not isinstance(data, str) or not isinstance(message, dict) or not isinstance(actor, dict):
            return False
        chat = message.get("chat")
        if not isinstance(chat, dict):
            return False
        chat_id = int(chat["id"])
        user_id = int(actor["id"])
        if data in _FAST_ACK_OWNER_ADMIN_ACTIONS:
            # No fast ACK for another role or a forged/out-of-context admin
            # callback; the existing dispatcher must preserve its denial toast.
            return bool(bot_service.is_owner(user_id)) and bool(
                bot_service._can_use_admin_callback(message, user_id)
            )
        app = telegram_app_nav.parse_app_callback(data)
        if not isinstance(app, dict) or app.get("action") not in {
            telegram_app_nav.ACT_HELP, telegram_app_nav.ACT_STATUS,
        }:
            return False
        generation = app.get("generation")
        if not isinstance(generation, int) or generation <= 0:
            return False  # Legacy generation-less buttons retain recovery semantics.
        thread_id = message.get("message_thread_id")
        return bool(telegram_app_nav.callback_generation_is_current(
            chat_id=chat_id,
            user_id=user_id,
            callback_generation=generation,
            thread_id=int(thread_id) if thread_id is not None else None,
        ))
    except (TypeError, ValueError, KeyError):
        return False
    except Exception:
        # Non-critical preflight failure never prevents the governed callback.
        return False


def _report_slow_callback(*, fast_ack: bool, ack_elapsed_ms: int, handler_elapsed_ms: int, family: str) -> None:
    """Emit bounded, identity-free performance telemetry only when slow."""
    global _LAST_SLOW_CALLBACK_LOG_MONOTONIC
    if max(ack_elapsed_ms, handler_elapsed_ms) < _SLOW_CALLBACK_THRESHOLD_MS:
        return
    now = time.monotonic()
    with _SLOW_CALLBACK_LOG_LOCK:
        if (now - _LAST_SLOW_CALLBACK_LOG_MONOTONIC) < _SLOW_CALLBACK_REMINDER_SECONDS:
            return
        _LAST_SLOW_CALLBACK_LOG_MONOTONIC = now
    observability_logger.log_warning(
        warn_type="telegram_callback_slow",
        message="Callback processing exceeded the latency threshold",
        context={
            "callback_family": family,
            "fast_ack": fast_ack,
            "ack_elapsed_ms": min(max(0, ack_elapsed_ms), 60000),
            "handler_elapsed_ms": min(max(0, handler_elapsed_ms), 60000),
        },
        source={"module": "telegram_updates", "function": "process_update"},
    )


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


def _try_private_support_proof(update: Dict[str, Any]) -> bool:
    message = update.get("message")
    if not isinstance(message, dict):
        return False
    if not message.get("document") and not message.get("photo"):
        return False
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    try:
        result = support_runtime.handle_private_proof_message(
            message,
            now_ts=int(time.time()),
        )
    except Exception as exc:
        observability_logger.log_error(
            {
                "event_type": "error",
                "module": "telegram_updates",
                "function": "support_private_proof",
                "error": telegram_publisher._sanitize(str(exc)),
            }
        )
        if chat_id is not None:
            try:
                telegram_publisher.send_message(
                    chat_id=int(chat_id),
                    text=(
                        "Payment proof could not be recorded. "
                        "Please retry the attachment or contact support."
                    ),
                )
            except Exception:
                pass
        # A proof-shaped message is consumed when ingestion fails so it cannot
        # fall through to an unrelated command/navigation handler.
        return True
    if not result.get("handled"):
        return False
    if chat_id is not None:
        try:
            telegram_publisher.send_message(
                chat_id=int(chat_id),
                text=(
                    f"Support case {result.get('case_id')}: payment proof recorded. "
                    "The file is restricted to the audited support workflow."
                ),
            )
        except Exception as exc:
            observability_logger.log_warning(
                warn_type="support_proof_client_ack_failed",
                message="Payment proof was recorded but client acknowledgement failed",
                context={
                    "case_id": result.get("case_id"),
                    "error": telegram_publisher._sanitize(str(exc)),
                },
                source={"module": "telegram_updates", "function": "_try_private_support_proof"},
            )
    return True


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

    # Payment-proof attachments are intercepted before text routing. A support
    # proof never falls through to unrelated command/navigation behavior.
    if "message" in update:
        if _try_private_support_proof(update):
            return
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

        callback_started = time.monotonic()
        fast_ack = _fast_ack_safe_for_navigation(update)
        ack_elapsed_ms = 0
        if fast_ack:
            # Dismiss Telegram spinner BEFORE UI rendering, file reads or sync
            # storage. This never runs for billing, voting, mutation, unknown,
            # unauthorized, malformed or stale-generation callbacks.
            _ack_callback(callback_id)
            ack_elapsed_ms = int((time.monotonic() - callback_started) * 1000)

        handler_started = time.monotonic()
        result = bot_service.process_update(update)
        handler_elapsed_ms = int((time.monotonic() - handler_started) * 1000)

        if not fast_ack:
            # Preserve existing recovery/denial toasts and governed callback
            # ordering for all non-allowlisted routes.
            ack_text = (
                str(result.get("callback_ack_text") or "")
                if isinstance(result, dict)
                else ""
            )
            _ack_callback(callback_id, ack_text)
            ack_elapsed_ms = int((time.monotonic() - callback_started) * 1000)

        family = "APP" if isinstance(data, str) and data.startswith("APP:") else (
            "ADMIN_NAV" if isinstance(data, str) and data.startswith("ADMIN_NAV:") else "OTHER"
        )
        _report_slow_callback(
            fast_ack=fast_ack,
            ack_elapsed_ms=ack_elapsed_ms,
            handler_elapsed_ms=handler_elapsed_ms,
            family=family,
        )


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
