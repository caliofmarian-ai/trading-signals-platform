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
from core.admin_permissions import is_owner
from core import observability_logger
from core import outcome_service
from core import fsm_runtime
from core.telegram_runtime import admin_command_names, render_help_text, render_start_text, render_status_text
from core.telegram_targets import env_chat_id, env_thread_id, reply_target_from_message, valid_thread_id
from core import telegram_admin_ui
from monitoring import restart_guard
from runtime import runtime_status

# ---- Paths ----
# OUTCOMES_PATH is retained as a module attribute for BATCH-04 compatibility.
# bot_service does NOT write to this path after BATCH-04/BATCH-05.
OUTCOMES_PATH = "/opt/binarybot/state/outcomes.json"

# ---- Env ----
ADMIN_CONTROL_CHAT_ID = env_chat_id("ADMIN_CONTROL_CHAT_ID") or 0
ADMIN_CONTROL_THREAD_ID = env_thread_id("ADMIN_CONTROL_THREAD_ID") or 0
UNKNOWN_COMMAND_TEXT = "Unknown command. Use /help to view available commands."
_OWNER_PRIVATE_COMMANDS: frozenset[str] = frozenset({
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
})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def in_admin_context(chat_id: int) -> bool:
    # BATCH-05: fail-closed — access is denied when ADMIN_CONTROL_CHAT_ID is not configured.
    # The previous behavior (returning True when the env var was 0) was a fail-open
    # security defect (GAP-013). Missing configuration now denies access.
    if ADMIN_CONTROL_CHAT_ID == 0:
        return False
    return chat_id == ADMIN_CONTROL_CHAT_ID


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _is_owner_private_context(message: Dict[str, Any], user_id: int) -> bool:
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return False
    if str(chat.get("type") or "").lower() != "private":
        return False
    chat_id = _safe_int(chat.get("id"))
    if chat_id is None or chat_id != user_id:
        return False
    return is_owner(user_id)


def _is_admin_topic_context(message: Dict[str, Any]) -> bool:
    target = reply_target_from_message(message)
    if target is None:
        return False
    if not in_admin_context(target.chat_id):
        return False
    required_thread_id = valid_thread_id(ADMIN_CONTROL_CHAT_ID, ADMIN_CONTROL_THREAD_ID)
    if required_thread_id is None:
        return True
    return target.thread_id == required_thread_id


def _can_run_admin_command(message: Dict[str, Any], user_id: int, cmd: str) -> bool:
    if _is_owner_private_context(message, user_id):
        return cmd in _OWNER_PRIVATE_COMMANDS
    return _is_admin_topic_context(message)


def _can_use_admin_callback(message: Dict[str, Any], user_id: int) -> bool:
    if _is_owner_private_context(message, user_id):
        return True
    return _is_admin_topic_context(message)


def _is_owner_private_for_message(message: Dict[str, Any], user_id: int) -> bool:
    return _is_owner_private_context(message, user_id)


def _send_reply(message: Dict[str, Any], text: str, reply_markup: Optional[Dict[str, Any]] = None) -> None:
    target = reply_target_from_message(message)
    if target is None:
        return
    telegram_publisher.send_message(
        chat_id=target.chat_id,
        text=text,
        reply_markup=reply_markup,
        thread_id=target.thread_id,
    )


def _format_card(title: str, body: str) -> str:
    clean_body = str(body or "").strip()
    if not clean_body:
        return title
    return f"{title}\n\n{clean_body}"


def _admin_reply_markup(cmd: str, *, owner_private: bool) -> Optional[Dict[str, Any]]:
    if cmd == "/admin":
        return telegram_admin_ui.admin_home_markup(include_roles_reload=not owner_private)
    if cmd == "/strategy":
        return telegram_admin_ui.strategy_markup()
    if cmd in {"/thresholds", "/sr", "/spike"}:
        return telegram_admin_ui.strategy_markup()
    if cmd == "/symbols":
        return telegram_admin_ui.symbols_markup()
    if cmd == "/engine":
        return telegram_admin_ui.engine_markup(include_roles_reload=not owner_private)
    if cmd in {"/debug", "/report", "/roles", "/affiliate"}:
        return telegram_admin_ui.standard_back_markup()
    return None


def _render_panel_for_command(cmd: str, user_id: int, *, owner_private: bool) -> tuple[str, Optional[Dict[str, Any]]]:
    if cmd == "/status":
        return _format_card("📡 Status Panel", render_status_text(_build_status_snapshot())), telegram_admin_ui.status_markup()

    response_text = handle_admin_command_v2(cmd, user_id)
    title_map = {
        "/admin": "🛠️ Admin Panel",
        "/strategy": "📈 Strategy Panel",
        "/thresholds": "🎯 Thresholds Panel",
        "/sr": "📐 SR Panel",
        "/spike": "⚡ Spike Panel",
        "/symbols": "🧩 Symbols Panel",
        "/engine": "⚙️ Engine Panel",
        "/debug": "🧪 Debug Panel",
        "/report": "📊 Report Panel",
        "/roles": "👥 Roles Panel",
        "/affiliate": "💼 Affiliate Panel",
        "/roles_reload": "♻️ Roles Panel",
    }
    return _format_card(title_map.get(cmd, "🛠️ Admin Panel"), response_text), _admin_reply_markup(cmd, owner_private=owner_private)


def _handle_admin_navigation_action(action: str, user_id: int, message: Dict[str, Any]) -> Dict[str, Any]:
    owner_private = _is_owner_private_for_message(message, user_id)
    command_for_action = {
        "HOME": "/admin",
        "STATUS": "/status",
        "STRATEGY": "/strategy",
        "THRESHOLDS": "/thresholds",
        "SR": "/sr",
        "SPIKE": "/spike",
        "SYMBOLS": "/symbols list",
        "ENGINE": "/engine",
        "DEBUG": "/debug",
        "REPORT": "/report",
        "ROLES": "/roles",
        "AFFILIATE": "/affiliate",
        "RELOAD_ROLES_EXEC": "/roles_reload",
    }.get(action)

    if action == "RELOAD_ROLES_CONFIRM":
        if owner_private:
            return {"text": "Access denied (wrong chat).", "reply_markup": None}
        return {
            "text": _format_card("♻️ Confirmation", "Confirm reloading role + permission configuration?"),
            "reply_markup": telegram_admin_ui.reload_confirm_markup(),
        }

    if command_for_action is None:
        return {"text": "Unknown action.", "reply_markup": None}

    cmd = command_for_action.split()[0].lower()
    if cmd in admin_command_names():
        if owner_private and cmd not in _OWNER_PRIVATE_COMMANDS:
            return {"text": "Access denied (wrong chat).", "reply_markup": None}
        if not owner_private and not _is_admin_topic_context(message):
            return {"text": "Access denied (wrong chat).", "reply_markup": None}
    text, reply_markup = _render_panel_for_command(command_for_action, user_id, owner_private=owner_private)
    return {"text": text, "reply_markup": reply_markup}


def _build_status_snapshot() -> Dict[str, Any]:
    status = runtime_status.read_status()
    runtime_phase = str(status.get("phase") or "unknown").lower()
    market_data_state = str(status.get("market_data_state") or "UNKNOWN").upper()
    recovery_required = bool(status.get("recovery_required"))
    recovery_state = str(status.get("recovery_state") or ("DEGRADED_SAFE" if recovery_required else "HEALTHY"))
    telegram_enabled = bool(status.get("telegram_enabled", _env_flag("ENABLE_TELEGRAM", default=False)))
    telegram_polling_started = bool(status.get("telegram_polling_started"))
    telegram_state = "DISABLED"
    if telegram_enabled:
        telegram_state = "ENABLED (polling started)" if telegram_polling_started else "ENABLED (polling pending)"

    fsm_state = "UNAVAILABLE"
    try:
        state = fsm_runtime.load_state()
        watchlist = state.get("watchlist", []) if isinstance(state, dict) else []
        mode = str(state.get("mode") or "UNKNOWN") if isinstance(state, dict) else "UNKNOWN"
        fsm_state = f"{mode} watchlist={len(watchlist)}"
    except Exception:
        pass

    broker_state = "DISABLED"
    if _env_flag("ENABLE_BROKER_EXECUTION", default=False):
        broker_state = "NOT REPORTED AS AVAILABLE"

    overall_state = "DEGRADED"
    if runtime_phase == "blocked":
        overall_state = "BLOCKED"
    elif market_data_state == "MARKET_DATA_LIMITED":
        overall_state = "MARKET_DATA_LIMITED"
    elif runtime_phase == "running" and not recovery_required:
        overall_state = "READY"

    return {
        "overall_state": overall_state,
        "runtime_phase": runtime_phase.upper(),
        "runtime_message": str(status.get("message") or "unknown"),
        "recovery_state": recovery_state,
        "market_data_state": market_data_state,
        "market_data_note": str(status.get("market_data_note") or "").strip(),
        "telegram_state": telegram_state,
        "fsm_state": fsm_state,
        "shadow_mode": "ON" if bool(status.get("shadow_mode", _env_flag("SHADOW_MODE", default=False))) else "OFF",
        "broker_state": broker_state,
    }


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
    message_thread_id: Optional[int] = None,
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

    admin_action = telegram_admin_ui.parse_action(data)
    if admin_action is not None:
        message = {
            "chat": {"id": chat_id, "type": "private" if chat_id > 0 else "supergroup"},
        }
        if message_thread_id is not None:
            message["message_thread_id"] = message_thread_id
        return _handle_admin_navigation_action(admin_action, user_id, message)

    # ---- Admin panel callbacks: require authorised admin chat context (BATCH-05: fail-closed) ----
    context_message: Dict[str, Any] = {"chat": {"id": chat_id, "type": "private" if chat_id > 0 else "supergroup"}}
    if message_thread_id is not None:
        context_message["message_thread_id"] = message_thread_id
    if not _is_admin_topic_context(context_message):
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
            cmd = text.split()[0].split("@", 1)[0].lower()
            if cmd == "/start":
                _send_reply(msg, render_start_text(shadow_mode=_env_flag("SHADOW_MODE", default=False)))
                return
            if cmd == "/help":
                _send_reply(msg, render_help_text())
                return
            if cmd == "/status":
                _send_reply(msg, render_status_text(_build_status_snapshot()))
                return
            if cmd in admin_command_names():
                if not _can_run_admin_command(msg, user_id, cmd):
                    _send_reply(msg, "Access denied (wrong chat).")
                    return
                owner_private = _is_owner_private_for_message(msg, user_id)
                response_text, reply_markup = _render_panel_for_command(text, user_id, owner_private=owner_private)
                _send_reply(msg, response_text, reply_markup)
                return
            _send_reply(msg, UNKNOWN_COMMAND_TEXT)
            return

        if cb:
            data = cb.get("data") or ""
            msg_obj = cb.get("message") or {}
            chat_id = int(msg_obj["chat"]["id"])
            user_id = int(cb["from"]["id"])
            message_id = msg_obj.get("message_id")

            admin_action = telegram_admin_ui.parse_action(data)
            if admin_action is not None and not _can_use_admin_callback(msg_obj, user_id):
                _send_reply(msg_obj, "Access denied (wrong chat).")
                return

            if admin_action is not None:
                res = _handle_admin_navigation_action(admin_action, user_id, msg_obj)
            else:
                res = handle_callback(
                    chat_id,
                    user_id,
                    data,
                    message_id=message_id,
                    message_thread_id=msg_obj.get("message_thread_id"),
                )

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
                _send_reply(msg_obj, res.get("text", ""), res.get("reply_markup"))

    except Exception as e:
        observability_logger.log_error({
            "event_type": "error",
            "data": {
                "severity": "ERROR",
                "error_type": "bot_service_exception",
                "message": str(e),
            },
        })
