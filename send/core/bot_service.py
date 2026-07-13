# /opt/binarybot/core/bot_service.py
# BinaryBot — Telegram update dispatcher.
#
# BATCH-05: Legacy Admin/control-plane panel path retired.
#
# Residual responsibility after BATCH-05:
#   1. Dispatch slash admin commands to handle_admin_command (canonical admin_commands.py).
#   2. Forward VOTE_ callbacks to outcome_service (BATCH-04 canonical path).
#   3. Forward OUTCOME: legacy callbacks to outcome_service without independent mutation.
#   4. Reject retired legacy Admin panel callbacks with a clear message.
#   5. Deny all Admin-context callbacks when ADMIN_CONTROL_CHAT_ID is not configured (fail-closed).
#
from __future__ import annotations

import os
import time
from typing import Optional, Dict, Any

from core import telegram_publisher
from core.admin_commands import handle_admin_command as handle_admin_command_v2
from core import observability_logger
from core import outcome_service

# ---- Paths ----
# OUTCOMES_PATH is retained as a module attribute for BATCH-04 compatibility.
# bot_service does NOT write to this path after BATCH-04/BATCH-05.
OUTCOMES_PATH = "/opt/binarybot/state/outcomes.json"

# ---- Env ----
ADMIN_CONTROL_CHAT_ID = int(os.getenv("ADMIN_CONTROL_CHAT_ID", "0"))
ADMIN_CONTROL_THREAD_ID = int(os.getenv("ADMIN_CONTROL_THREAD_ID", "0") or "0")


def in_admin_context(chat_id: int) -> bool:
    # BATCH-05: fail-closed — access is denied when ADMIN_CONTROL_CHAT_ID is not configured.
    # The previous behavior (returning True when the env var was 0) was a fail-open
    # security defect (GAP-013). Missing configuration now denies access.
    if ADMIN_CONTROL_CHAT_ID == 0:
        return False
    return chat_id == ADMIN_CONTROL_CHAT_ID


_RETIRED_ADMIN_CALLBACKS: frozenset = frozenset({
    "ADMIN_STATUS",
    "ADMIN_SET_BUFFER",
    "ADMIN_SET_SYMBOLS",
    "ADMIN_RESEARCH",
    "ADMIN_DOCS",
    "ADMIN_BACK",
})

_RETIRED_ADMIN_PREFIXES = ("BUFFER_", "SYM_TOGGLE:", "DOC:")

_RETIRED_MSG = (
    "Admin panel buttons are retired. Use canonical slash commands "
    "(/admin, /strategy, /engine, etc.)."
)


def handle_callback(
    chat_id: int,
    user_id: int,
    data: str,
    message_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Callback dispatcher.

    VOTE_ callbacks are forwarded to outcome_service without admin-context checks —
    they originate from the public signal panel and are not Admin mutations.

    All Admin panel callbacks require a valid admin context and are rejected
    with a clear message (legacy buttons retired in BATCH-05).
    """
    # ---- VOTE_|signal_id|outcome — canonical BATCH-04 path ----
    if data.startswith("VOTE_|"):
        parts = data.split("|")
        if len(parts) != 3:
            return {"text": "Invalid vote payload.", "reply_markup": None}
        signal_id = (parts[1] or "").strip()
        outcome = (parts[2] or "").strip().upper()
        res = outcome_service.handle_vote_callback(
            user_id=user_id,
            signal_id=signal_id,
            outcome=outcome,
            now_ts=int(time.time()),
            chat_id=chat_id,
            message_id=message_id,
        )
        if res.get("accepted"):
            if res.get("reason") == "already_processed":
                return {"text": "Outcome already recorded.", "reply_markup": None}
            return {"text": f"OUTCOME: {outcome}", "reply_markup": None}
        return {"text": f"Outcome rejected: {res.get('reason')}", "reply_markup": None}

    # ---- VOTE_ generic — canonical BATCH-04 path ----
    if data.startswith("VOTE_"):
        res = outcome_service.handle_vote_callback_data(
            callback_data=data,
            user_id=user_id,
            now_ts=int(time.time()),
            chat_id=chat_id,
            message_id=message_id,
        )
        if res.get("accepted"):
            return {"text": "Outcome recorded.", "reply_markup": None}
        return {"text": f"Outcome rejected: {res.get('reason')}", "reply_markup": None}

    # ---- OUTCOME:<outcome>:<signal_id> — legacy format delegated to outcome_service ----
    if data.startswith("OUTCOME:"):
        parts = data.split(":", 2)
        if len(parts) != 3:
            return {"text": "Invalid outcome payload.", "reply_markup": None}
        outcome = (parts[1] or "").strip().upper()
        signal_id = (parts[2] or "").strip()
        res = outcome_service.handle_vote_callback(
            user_id=user_id,
            signal_id=signal_id,
            outcome=outcome,
            now_ts=int(time.time()),
            chat_id=chat_id,
            message_id=message_id,
        )
        if not res.get("accepted"):
            return {"text": f"Outcome error: {res.get('reason')}", "reply_markup": None}
        if res.get("reason") == "already_processed":
            return {"text": f"Already set: {outcome}", "reply_markup": None}
        return {"text": f"OUTCOME: {outcome}", "reply_markup": None}

    # ---- Admin panel callbacks: require authorised admin chat context (BATCH-05: fail-closed) ----
    if not in_admin_context(chat_id):
        return {"text": "Access denied (wrong chat).", "reply_markup": None}

    if data in _RETIRED_ADMIN_CALLBACKS or any(data.startswith(p) for p in _RETIRED_ADMIN_PREFIXES):
        return {"text": _RETIRED_MSG, "reply_markup": None}

    return {"text": "Unknown action.", "reply_markup": None}


def process_update(update: Dict[str, Any]) -> None:
    """
    Telegram update dispatcher.
    - Slash admin commands → canonical handle_admin_command (admin_commands.py).
    - Callbacks → handle_callback (VOTE forwarding + retired panel rejection).
    """
    try:
        msg = update.get("message") or {}
        cb = update.get("callback_query") or {}
        text = ""

        if msg:
            chat_id = int(msg["chat"]["id"])
            user_id = int(msg["from"]["id"])
            text = (msg.get("text") or "").strip()

        if text.startswith("/"):
            admin_commands = {
                "/admin", "/strategy", "/thresholds", "/sr", "/spike",
                "/symbols", "/engine", "/debug", "/report", "/roles",
                "/affiliate", "/roles_reload",
            }
            cmd = text.split()[0].lower()
            if cmd in admin_commands:
                response_text = handle_admin_command_v2(text, user_id)
                telegram_publisher.send_message(
                    chat_id, response_text, None, ADMIN_CONTROL_THREAD_ID or None
                )
                return

        if cb:
            data = cb.get("data") or ""
            chat_id = int(cb["message"]["chat"]["id"])
            user_id = int(cb["from"]["id"])
            msg_obj = cb.get("message") or {}
            message_id = msg_obj.get("message_id")

            res = handle_callback(chat_id, user_id, data, message_id=message_id)

            original_text = msg_obj.get("text", "") or ""

            if data.startswith("VOTE_|") and message_id:
                outcome_line = res.get("text", "")
                new_text = original_text
                if outcome_line and outcome_line not in original_text:
                    new_text = f"{original_text}\n\n{outcome_line}".strip()
                telegram_publisher.edit_message(chat_id, message_id, new_text, {"inline_keyboard": []})
            elif message_id and res.get("reply_markup") is not None:
                telegram_publisher.edit_message(
                    chat_id, message_id, res.get("text"), res.get("reply_markup")
                )
            else:
                telegram_publisher.send_message(
                    chat_id, res.get("text", ""), res.get("reply_markup"), ADMIN_CONTROL_THREAD_ID or None
                )

    except Exception as e:
        observability_logger.log_error({
            "event_type": "error",
            "data": {
                "severity": "ERROR",
                "error_type": "bot_service_exception",
                "message": str(e),
            },
        })

