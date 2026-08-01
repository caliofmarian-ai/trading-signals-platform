# /opt/binarybot/runtime/telegram_updates.py
# BinaryBot — Telegram Updates Poller

from __future__ import annotations

import os
import time
import requests
from typing import Dict, Any

from core import bot_service
from core import outcome_service
from core import observability_logger
from core import telegram_publisher


def _get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")
    return token


def _base_url() -> str:
    return f"https://api.telegram.org/bot{_get_bot_token()}"

POLL_INTERVAL = 1.5

LAST_UPDATE_ID = None


def poll_updates():
    global LAST_UPDATE_ID

    while True:
        try:
            params = {
                "timeout": 30
            }

            if LAST_UPDATE_ID:
                params["offset"] = LAST_UPDATE_ID

            r = requests.get(
                f"{_base_url()}/getUpdates",
                params=params,
                timeout=35
            )

            data = r.json()

            if not data.get("ok"):
                time.sleep(POLL_INTERVAL)
                continue

            updates = data.get("result", [])

            for update in updates:

                LAST_UPDATE_ID = update["update_id"] + 1

                process_update(update)

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