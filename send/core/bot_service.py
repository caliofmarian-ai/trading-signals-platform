# /opt/binarybot/core/bot_service.py
# BinaryBot — Telegram update dispatcher.
#
# BATCH-05: Legacy Admin/control-plane panel path retired.
# RESTORATION-01: New admin UI capabilities restored (symbols toggle, strategy profile,
#   file/log/diagnose/audit delivery, rate limiting, graceful edit fallback).
# RECONSTRUCTION-01: Complete Telegram application experience implemented.
#   Single active UI message, guided /start entry, role-scoped home pages,
#   APP: callback dispatch, active message tracking.
#
from __future__ import annotations

import os
import json
import sys
import time
import uuid
from typing import Optional, Dict, Any

from core import telegram_publisher
from core.telegram_publisher import TelegramAPIError as _TelegramAPIError
from core.admin_commands import (
    handle_admin_command as handle_admin_command_v2,
    handle_symbols_toggle,
    handle_symbols_all,
    handle_symbols_none,
    handle_strategy_profile,
    get_current_strategy_profile,
    handle_files_list,
    handle_file_download_path,
    handle_log_export,
    handle_diagnose,
    handle_audit_runtime,
    handle_docs_list,
    get_all_known_symbols,
    get_current_strategy_profile_observation,
    _load_active_symbols_observation,
    _read_engine_events_observation,
    _find_latest_report_json,
    _iter_jsonl,
    ENGINE_EVENTS_PATH,
    REPORTS_DIR,
)
from core.admin_permissions import is_owner, get_primary_role
from core import observability_logger
from core import outcome_service
from core.owner_knowledge import (
    get_knowledge,
    render_contextual_knowledge,
    render_operational_page,
)
from core.operational_snapshot import build_status_snapshot, observed_shadow_mode
from core.telegram_runtime import admin_command_names, render_help_text, render_start_text, render_status_text
from core.telegram_targets import env_chat_id, env_thread_id, reply_target_from_message, valid_thread_id
from core import telegram_admin_ui
from core import telegram_app_nav
from monitoring import restart_guard

# ---- Paths ----
OUTCOMES_PATH = "/opt/binarybot/state/outcomes.json"

# ---- Env ----
ADMIN_CONTROL_CHAT_ID = env_chat_id("ADMIN_CONTROL_CHAT_ID") or 0
ADMIN_CONTROL_THREAD_ID = env_thread_id("ADMIN_CONTROL_THREAD_ID") or 0
UNKNOWN_COMMAND_TEXT = "Unknown command. Use /help to view available commands."

_CALLBACK_RECOVERY_KEY = "__callback_recovery__"
_RECOVERY_STALE = "stale"
_RECOVERY_UNKNOWN_APP = "unknown_app"
_RECOVERY_UNKNOWN = "unknown"
_RECOVERY_RETIRED = "retired"
_RECOVERY_UNAUTHORIZED = "unauthorized"

_CALLBACK_RECOVERY_ACK = {
    _RECOVERY_STALE: "Button expired — returned to Home.",
    _RECOVERY_UNKNOWN_APP: "Unknown action — returned to Home.",
    _RECOVERY_UNKNOWN: "Unknown action — returned to Admin Home.",
    _RECOVERY_RETIRED: "This button was retired — returned to Admin Home.",
    _RECOVERY_UNAUTHORIZED: "Access denied.",
}

# All admin commands accessible from owner private DM
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
    "/files",
    "/docs",
    "/download",
    "/log",
    "/diagnose",
    "/audit_runtime",
    "/roles",
    "/affiliate",
})

# ---- Rate limiting ----
# Per-user in-memory rate-limit store.  Entries: {key: {count, window_start}}
_RATE_STORE: Dict[str, Dict[str, Any]] = {}

# Rate-limit ceilings per operation (calls per window_seconds)
_RATE_LIMITS_CONFIG: Dict[str, tuple[int, int]] = {
    "files_list":    (20, 60),
    "file_download": (10, 60),
    "diagnose":      (5, 60),
    "audit_runtime": (3, 60),
    "mutation":      (30, 60),
}


def _check_rate_limit(user_id: int, operation: str) -> bool:
    """Return True if the user is within the rate limit for this operation."""
    max_calls, window_seconds = _RATE_LIMITS_CONFIG.get(operation, (60, 60))
    key = f"{user_id}:{operation}"
    now = time.time()
    entry = _RATE_STORE.get(key)
    if entry is None or now - entry["window_start"] > window_seconds:
        _RATE_STORE[key] = {"count": 1, "window_start": now}
        return True
    entry["count"] += 1
    return entry["count"] <= max_calls


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


def _emit_interactive_trace(payload: Dict[str, Any], *, critical: bool = False) -> None:
    observability_logger.log_warning(
        warn_type="telegram_ui_navigation_trace",
        message="Telegram interactive navigation decision",
        context=payload,
        source={"module": "bot_service", "function": "_send_interactive_page"},
    )
    if critical:
        try:
            print(json.dumps({"component": "telegram_ui_navigation", **payload}, sort_keys=True), file=sys.stderr, flush=True)
        except Exception:
            pass


def _edit_interactive_message(
    *,
    chat_id: int,
    user_id: int,
    thread_id: Optional[int],
    message_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]],
) -> tuple[bool, str]:
    """Try to edit a candidate interactive page message.

    Returns True when edit is successful or idempotent no-op, else False.

    When the edit fails because the message is stale (deleted/unavailable),
    the session clear is attempted best-effort.  A failure during the clear
    (e.g. a stale filesystem lock causing TimeoutError) is captured and
    logged but does NOT propagate.  The caller then falls through to
    send_message(), preserving the transport-first contract.
    """
    try:
        telegram_publisher.edit_message(chat_id, message_id, text, reply_markup)
        telegram_app_nav.set_active_message(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            thread_id=thread_id,
        )
        return True, "edited"
    except Exception as exc:
        failure_category = _classify_edit_message_failure(exc)
        if failure_category == "no_op":
            telegram_app_nav.set_active_message(
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id,
                thread_id=thread_id,
            )
            return True, "no_op"
        if failure_category == "stale":
            # Transport-first: clear state best-effort.  A lock timeout or
            # any other persistence failure must NOT suppress the replacement
            # send that follows.
            try:
                telegram_app_nav.clear_active_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    thread_id=thread_id,
                )
            except Exception as clear_exc:
                observability_logger.log_error({
                    "event_type": "error",
                    "data": {
                        "severity": "WARNING",
                        "error_type": "telegram_app_nav_clear_failed_on_stale",
                        "message": str(clear_exc),
                        "context": {
                            "chat_id": chat_id,
                            "user_id": user_id,
                            "message_id": message_id,
                        },
                    },
                })
            return False, "stale"
        _log_app_nav_edit_failure(
            category=failure_category,
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            exc=exc,
        )
        return False, failure_category


def _send_interactive_page(
    message: Dict[str, Any],
    user_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]],
    *,
    preferred_message_id: Optional[int] = None,
    trace_context: Optional[Dict[str, Any]] = None,
) -> None:
    """Canonical single-message delivery path for interactive Telegram pages."""
    target = reply_target_from_message(message)
    if target is None:
        return

    chat_id = target.chat_id
    thread_id = target.thread_id
    nav_diag = telegram_app_nav.get_runtime_diagnostics(chat_id=chat_id, user_id=user_id, thread_id=thread_id)
    trace_payload: Dict[str, Any] = {
        "correlation_id": (trace_context or {}).get("correlation_id") or uuid.uuid4().hex[:12],
        "update_id": (trace_context or {}).get("update_id"),
        "command_family": (trace_context or {}).get("command_family", "unknown"),
        "chat_id": chat_id,
        "user_id": user_id,
        "thread_id": thread_id,
        "session_key_fingerprint": nav_diag.get("session_key_fingerprint"),
        "preferred_message_id": preferred_message_id,
        "active_in_memory_message_id": nav_diag.get("active_message_id"),
        "persisted_message_id": nav_diag.get("persisted_message_id"),
        "resolved_state_file_path": nav_diag.get("resolved_state_path"),
        "save_state_result": nav_diag.get("save_result"),
        "load_state_result": nav_diag.get("load_result"),
        "process_id": nav_diag.get("pid"),
        "runtime_instance_id": nav_diag.get("deployment_id"),
        "deployment_identifier": nav_diag.get("deployment_id"),
    }

    if preferred_message_id is not None:
        edited, category = _edit_interactive_message(
            chat_id=chat_id,
            user_id=user_id,
            thread_id=thread_id,
            message_id=preferred_message_id,
            text=text,
            reply_markup=reply_markup,
        )
        if edited:
            trace_payload["selected_operation"] = "edit_preferred"
            trace_payload["edit_result_category"] = category
            _emit_interactive_trace(trace_payload)
            return
        trace_payload["preferred_edit_result_category"] = category

    active_message_id = telegram_app_nav.get_active_message(
        user_id=user_id,
        chat_id=chat_id,
        thread_id=thread_id,
    )
    trace_payload["active_in_memory_message_id"] = active_message_id
    if active_message_id is not None and active_message_id != preferred_message_id:
        edited, category = _edit_interactive_message(
            chat_id=chat_id,
            user_id=user_id,
            thread_id=thread_id,
            message_id=active_message_id,
            text=text,
            reply_markup=reply_markup,
        )
        if edited:
            trace_payload["selected_operation"] = "edit_active"
            trace_payload["edit_result_category"] = category
            _emit_interactive_trace(trace_payload)
            return
        trace_payload["active_edit_result_category"] = category

    try:
        result = telegram_publisher.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            thread_id=thread_id,
        )
        trace_payload["selected_operation"] = "send_replacement"
        trace_payload["edit_result_category"] = trace_payload.get("active_edit_result_category") or trace_payload.get("preferred_edit_result_category") or "send_required"
        if isinstance(result, dict):
            msg_result = result.get("result") or {}
            new_msg_id = msg_result.get("message_id")
            trace_payload["replacement_message_id"] = new_msg_id
            if new_msg_id:
                telegram_app_nav.set_active_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    message_id=new_msg_id,
                    thread_id=thread_id,
                )
        _emit_interactive_trace(
            trace_payload,
            critical=bool(trace_payload.get("preferred_edit_result_category") == "stale" or trace_payload.get("active_edit_result_category") == "stale"),
        )
        return
    except Exception as send_exc:
        trace_payload["selected_operation"] = "send_replacement"
        trace_payload["edit_result_category"] = "send_failed"
        trace_payload["send_error"] = str(send_exc)
        _emit_interactive_trace(trace_payload, critical=True)
        observability_logger.log_error({
            "event_type": "error",
            "data": {
                "severity": "ERROR",
                "error_type": "telegram_app_nav_send_failure",
                "message": str(send_exc),
                "context": {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "session_key_fingerprint": trace_payload.get("session_key_fingerprint"),
                },
            },
        })


def _handle_start_hard_reset(
    *,
    msg: Dict[str, Any],
    user_id: int,
    update_id: Any,
    page_text: str,
    page_markup: Optional[Dict[str, Any]],
) -> None:
    """Explicit /start hard-reset: always send a new anchor, never edit.

    Design:
    1. Normalize the private session key: (chat_id=user_id, user_id=user_id, thread_id=None)
       in private chats.  Non-private chats fall through to _send_interactive_page.
    2. Acquire a short-lived per-session reset guard (idempotency).
    3. Read + clear the previous tracked message ID.
    4. Best-effort deleteMessage on the old anchor.
    5. Call sendMessage exactly once.
    6. Persist the new message ID (best-effort).
    7. Log full mandatory diagnostics.

    Root cause context:
    When a Telegram user deletes the conversation on their side, the bot message
    is no longer visible.  However, Telegram may still return ok=true for
    editMessageText on that message because the message exists server-side.
    The bot therefore cannot rely on edit success as proof of visibility.
    /start must always send a new visible message, regardless of edit success.
    """
    target = reply_target_from_message(msg)
    if target is None:
        return

    chat_id = target.chat_id
    thread_id = target.thread_id

    # For non-private contexts (group chats, forum topics), fall through to the
    # normal edit-first path so that group behavior is unchanged.
    chat_type = (msg.get("chat") or {}).get("type", "")
    is_private = (chat_type == "private") or (chat_id == user_id)

    if not is_private:
        _send_interactive_page(
            msg,
            user_id,
            page_text,
            page_markup,
            trace_context={"update_id": update_id, "command_family": "/start"},
        )
        return

    # Normalize the private session key (thread_id=None for private chats).
    # Use target.chat_id for Telegram API calls; in real private chats chat_id==user_id.
    private_chat_id = chat_id
    private_thread_id: Optional[int] = None

    diag: Dict[str, Any] = {
        "event": "start_hard_reset",
        "update_id": update_id,
        "normalized_command": "/start",
        "chat_id": private_chat_id,
        "user_id": user_id,
        "session_fingerprint": telegram_app_nav.session_key_fingerprint(private_chat_id, user_id, private_thread_id),
        "edit_path_bypassed": True,
        "runtime_instance_id": os.getenv("RUN_ID", "") or os.getenv("RAILWAY_DEPLOYMENT_ID", "") or f"pid-{os.getpid()}",
        "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown"),
        "process_id": os.getpid(),
    }

    # Step 2: Acquire the per-session reset guard.
    guard = telegram_app_nav.acquire_start_reset_guard(private_chat_id, user_id, private_thread_id)
    diag["reset_guard_acquired"] = guard.get("acquired", False)
    diag["reset_generation"] = guard.get("generation", 0)

    if not guard.get("acquired"):
        # A concurrent /start is already in progress for this session.
        # Serialize: do nothing here; the first /start will create the anchor.
        diag["skipped_reason"] = "concurrent_reset_in_progress"
        _emit_interactive_trace(diag)
        return

    try:
        # Step 3: Read + clear previous session.
        reset_prep = telegram_app_nav.prepare_start_hard_reset(private_chat_id, user_id, private_thread_id)
        previous_message_id = reset_prep.get("previous_message_id")
        diag["previous_active_message_id"] = previous_message_id
        diag["session_clear_result"] = reset_prep.get("clear_result", {}).get("status", "unknown")

        # Step 4: Best-effort deleteMessage on the old anchor.
        delete_result: Optional[Dict[str, Any]] = None
        if previous_message_id is not None:
            diag["delete_attempted"] = True
            try:
                delete_result = telegram_publisher.delete_message(private_chat_id, previous_message_id)
                diag["delete_result"] = delete_result.get("outcome")
                diag["delete_error_code"] = delete_result.get("error_code")
            except Exception as del_exc:
                # delete_message is best-effort; any failure (including AttributeError
                # from mocked publishers without this method) must never suppress the send.
                diag["delete_result"] = f"error: {telegram_publisher._sanitize(str(del_exc))}"
                diag["delete_error_code"] = None
        else:
            diag["delete_attempted"] = False
            diag["delete_result"] = "skipped_no_previous_anchor"

        # Step 5+6: sendMessage exactly once.
        diag["send_attempted"] = True
        new_message_id: Optional[int] = None
        send_error: Optional[str] = None
        try:
            send_result = telegram_publisher.send_message(
                chat_id=private_chat_id,
                text=page_text,
                reply_markup=page_markup,
                thread_id=private_thread_id,
            )
            if isinstance(send_result, dict):
                msg_result = send_result.get("result") or {}
                new_message_id = msg_result.get("message_id")
            diag["send_result"] = "ok"
            diag["new_message_id"] = new_message_id
        except Exception as send_exc:
            send_error = telegram_publisher._sanitize(str(send_exc))
            diag["send_result"] = "failed"
            diag["send_error"] = send_error
            # Per contract: if sendMessage fails, do not restore previous ID;
            # leave session cleared; allow next /start to retry.
            _emit_interactive_trace(diag, critical=True)
            observability_logger.log_error({
                "event_type": "error",
                "data": {
                    "severity": "ERROR",
                    "error_type": "start_hard_reset_send_failure",
                    "context": {
                        "chat_id": private_chat_id,
                        "user_id": user_id,
                        "session_fingerprint": diag["session_fingerprint"],
                    },
                },
            })
            return

        # Step 7: Persist the new anchor (best-effort).
        # Visible delivery already succeeded; persistence failure must not delete the new message.
        persistence_result = "skipped"
        if new_message_id is not None:
            try:
                telegram_app_nav.set_active_message(
                    user_id=user_id,
                    chat_id=private_chat_id,
                    message_id=new_message_id,
                    thread_id=private_thread_id,
                )
                persistence_result = "ok"
            except Exception as persist_exc:
                persistence_result = f"failed: {telegram_publisher._sanitize(str(persist_exc))}"
                observability_logger.log_error({
                    "event_type": "error",
                    "data": {
                        "severity": "WARNING",
                        "error_type": "start_hard_reset_persistence_failed",
                        "message": persistence_result,
                        "context": {
                            "chat_id": private_chat_id,
                            "user_id": user_id,
                            "new_message_id": new_message_id,
                        },
                    },
                })

        diag["persistence_result"] = persistence_result
        _emit_interactive_trace(diag)

    finally:
        telegram_app_nav.release_start_reset_guard(private_chat_id, user_id, private_thread_id)


def _classify_edit_message_failure(exc: Exception) -> str:
    """
    Classify Telegram edit failure outcomes using structured error data first.

    When ``exc`` is a ``TelegramAPIError``, classification uses structured
    ``error_code`` and ``http_status`` fields.  String matching on the
    normalized description is kept as a fallback for legacy ``RuntimeError``
    instances.

    Returns:
    - "no_op":    requested content already active (``message is not modified``)
    - "stale":    message deleted/unavailable/bot blocked
    - "unexpected": any other failure
    """
    # Structured path: use TelegramAPIError fields when available.
    if isinstance(exc, _TelegramAPIError):
        if exc.is_not_modified():
            return "no_op"
        if exc.is_stale_message() or exc.is_chat_not_found():
            return "stale"
        return "unexpected"

    # Legacy fallback: string matching.
    detail = str(exc).lower()
    if "message is not modified" in detail:
        return "no_op"

    stale_markers = (
        "message to edit not found",
        "message can't be edited",
        "message can not be edited",
        "message to be replied not found",
        "chat not found",
        "bot was blocked by the user",
        "message identifier is not specified",
        "peer_id_invalid",
    )
    if any(marker in detail for marker in stale_markers):
        return "stale"

    return "unexpected"


def _log_app_nav_edit_failure(
    *,
    category: str,
    chat_id: int,
    user_id: int,
    message_id: int,
    exc: Exception,
) -> None:
    observability_logger.log_error({
        "event_type": "error",
        "data": {
            "severity": "ERROR",
            "error_type": "telegram_app_nav_edit_failure",
            "message": str(exc),
            "context": {
                "category": category,
                "chat_id": chat_id,
                "user_id": user_id,
                "message_id": message_id,
            },
        },
    })


def _send_app_nav_reply(
    message: Dict[str, Any],
    user_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]],
) -> None:
    _send_interactive_page(message, user_id, text, reply_markup)



def _format_card(title: str, body: str) -> str:
    clean_body = str(body or "").strip()
    if not clean_body:
        return title
    return f"{title}\n\n{clean_body}"


def _format_surface(knowledge_key: str, title: str, body: str) -> str:
    return render_operational_page(knowledge_key, body, title=title)


def _surface_current_state(rendered_surface: str) -> str:
    marker = "\nCurrent state\n"
    text = str(rendered_surface or "")
    return text.rsplit(marker, 1)[-1] if marker in text else text


def _active_symbols_for_markup() -> list[str]:
    observed = _load_active_symbols_observation()
    if observed is None:
        raise RuntimeError("active-symbol configuration evidence unavailable")
    return observed


def _build_canonical_admin_root_page(
    user_id: int,
    *,
    owner_private: bool,
    back_button_callback: Optional[str] = None,
) -> tuple[str, Optional[Dict[str, Any]]]:
    """
    Single source of truth for every admin root entry point.

    Both APP:ADMIN (welcome-page button) and ADMIN_NAV:HOME (back button from
    any admin sub-panel) must resolve here so the canonical single-message
    application model is preserved.

    Text:   "⚙️ Admin Control Surface" card with role/identity content.
    Markup: role-scoped canonical panel tree + trailing "🏠 Home" button
            (APP:HOME callback) so the user can always return to the welcome page.
    """
    role = get_primary_role(user_id)
    content = handle_admin_command_v2("/admin", user_id)
    command_dump_marker = "\nAvailable commands:"
    if command_dump_marker in content:
        content = content.split(command_dump_marker, 1)[0].rstrip()
    content = (
        f"{content}\n\n"
        "The buttons below are filtered to the current role. "
        "Opening a panel is read-only unless that panel presents a separately "
        "authorized and auditable control."
    )
    home_cb = telegram_app_nav.make_callback(telegram_app_nav.ACT_HOME)
    markup = telegram_admin_ui.admin_home_markup(
        role=role,
        include_roles_reload=not owner_private,
        home_button_callback=home_cb,
        back_button_callback=back_button_callback,
    )
    return _format_surface("admin_home", "⚙️ Admin Control Surface", content), markup


def _admin_reply_markup(cmd: str, user_id: int, *, owner_private: bool) -> Optional[Dict[str, Any]]:
    role = get_primary_role(user_id)
    if cmd == "/admin":
        home_cb = telegram_app_nav.make_callback(telegram_app_nav.ACT_HOME)
        return telegram_admin_ui.admin_home_markup(
            role=role,
            include_roles_reload=not owner_private,
            home_button_callback=home_cb,
        )
    if cmd == "/strategy":
        return telegram_admin_ui.strategy_markup()
    if cmd == "/thresholds":
        return telegram_admin_ui.strategy_parameter_markup("thresholds", "THRESHOLDS")
    if cmd == "/sr":
        return telegram_admin_ui.strategy_parameter_markup("sr_corridor", "SR")
    if cmd == "/spike":
        return telegram_admin_ui.strategy_parameter_markup("spike_filter", "SPIKE")
    if cmd == "/symbols" or cmd == "/symbols list":
        # Use toggle markup if possible; fall back to simple markup.
        # Default to parent_action="HOME" (matches /symbols command entry from admin root).
        try:
            all_syms = get_all_known_symbols()
            active = _active_symbols_for_markup()
            return telegram_admin_ui.symbols_toggle_markup(all_syms, active, parent_action="HOME")
        except Exception:
            return telegram_admin_ui.symbols_markup()
    if cmd == "/engine":
        return telegram_admin_ui.engine_markup(include_roles_reload=not owner_private, parent_action="HOME")
    if cmd == "/report":
        # Check if a report file is available for the download button
        try:
            import os as _os
            report_path = _find_latest_report_json()
            if report_path and _os.path.isfile(report_path):
                fname = _os.path.basename(report_path)
                return telegram_admin_ui.report_markup(has_file=True, filename=fname)
        except Exception:
            pass
        return telegram_admin_ui.standard_back_markup()
    if cmd == "/files":
        return telegram_admin_ui.files_home_markup()
    if cmd == "/docs":
        try:
            info = handle_docs_list(0)  # permissions checked in render_panel_for_command
            return telegram_admin_ui.docs_list_markup(info.get("filenames", []))
        except Exception:
            return telegram_admin_ui.standard_back_markup()
    if cmd == "/diagnose":
        return telegram_admin_ui.diagnose_markup(parent_action="HOME")
    if cmd == "/debug":
        return telegram_admin_ui.decision_visibility_markup()
    if cmd == "/roles":
        return telegram_admin_ui.roles_identity_markup(can_reload=False)
    if cmd == "/affiliate":
        return telegram_admin_ui.affiliate_markup()
    if cmd in {"/log", "/audit_runtime"}:
        return telegram_admin_ui.standard_back_markup(knowledge_key="security_audit")
    return None


def _render_panel_for_command(cmd: str, user_id: int, *, owner_private: bool) -> tuple[str, Optional[Dict[str, Any]]]:
    if cmd == "/status":
        return _format_surface("status", "📊 Status Panel", render_status_text(_build_status_snapshot())), telegram_admin_ui.status_markup()

    response_text = handle_admin_command_v2(cmd, user_id)
    title_map = {
        "/admin": "⚙️ Admin Control Surface",
        "/strategy": "⚙️ Strategy Panel",
        "/thresholds": "🎯 Thresholds Panel",
        "/sr": "📐 S/R Panel",
        "/spike": "⚡ Spike Filter Panel",
        "/symbols": "💱 Symbols Panel",
        "/symbols list": "💱 Symbols Panel",
        "/engine": "🤖 Engine Panel",
        "/debug": "🐞 Debug Panel",
        "/report": "📈 Reports Panel",
        "/roles": "👥 Roles Panel",
        "/affiliate": "🤝 Affiliate Panel",
        "/roles_reload": "🔄 Roles Reload",
        "/files": "📁 File Browser",
        "/docs": "📄 Documents",
        "/download": "📥 Download",
        "/log": "📋 Log Export",
        "/diagnose": "🩺 Diagnose",
        "/audit_runtime": "🔍 Runtime Audit",
    }
    # Extract base command (without arguments)
    base_cmd = cmd.split()[0].lower()
    title = title_map.get(cmd) or title_map.get(base_cmd, "🛠️ Admin Panel")
    knowledge_map = {
        "/admin": "admin_home",
        "/strategy": "strategy",
        "/thresholds": "thresholds",
        "/sr": "sr_corridor",
        "/spike": "spike_filter",
        "/symbols": "symbols_coverage",
        "/engine": "engine",
        "/debug": "decision_visibility",
        "/report": "research_analytics",
        "/roles": "roles_identity",
        "/affiliate": "affiliate",
        "/files": "files_reports",
        "/docs": "governance_docs",
        "/log": "security_audit",
        "/diagnose": "diagnostics",
        "/audit_runtime": "security_audit",
    }
    knowledge_key = knowledge_map.get(base_cmd)
    markup = _admin_reply_markup(base_cmd, user_id, owner_private=owner_private)
    if knowledge_key:
        return _format_surface(knowledge_key, title, response_text), markup
    return _format_card(title, response_text), markup


def _send_document_reply(message: Dict[str, Any], file_path: str, caption: Optional[str] = None) -> None:
    """Send a file via Telegram sendDocument. Removes tmp files after sending."""
    import os as _os
    target = reply_target_from_message(message)
    if target is None:
        return
    try:
        telegram_publisher.send_document(
            chat_id=target.chat_id,
            file_path=file_path,
            caption=caption,
            thread_id=target.thread_id,
        )
    finally:
        # Clean up temp files (paths starting with /tmp/)
        try:
            if file_path.startswith(_os.sep + "tmp") and _os.path.exists(file_path):
                _os.unlink(file_path)
        except Exception:
            pass


def _handle_admin_navigation_action(action: str, user_id: int, message: Dict[str, Any]) -> Dict[str, Any]:
    owner_private = _is_owner_private_for_message(message, user_id)

    # ---- BACK: navigate to canonical immediate parent ----
    # Uses the static CANONICAL_ADMIN_PARENT_MAP for deterministic, loop-free navigation.
    # For context-sensitive pages (OPS_ENGINE→OPERATIONS, SH_ENGINE→SYSHEALTH) the
    # correct parent is encoded in the originating Back button rather than this fallback.
    if action == "BACK":
        return _handle_admin_navigation_action("HOME", user_id, message)

    # ---- Contextual Owner/operator knowledge ----
    # Payload: INFO:<knowledge_key>:<safe_return_action>
    if action.startswith(telegram_admin_ui.KNOWLEDGE_ACTION_PREFIX):
        payload = action[len(telegram_admin_ui.KNOWLEDGE_ACTION_PREFIX):]
        knowledge_key, separator, return_action = payload.partition(":")
        entry = get_knowledge(knowledge_key)
        role = get_primary_role(user_id)
        if (
            not separator
            or entry is None
            or not telegram_admin_ui.knowledge_visible_for_role(role, entry.key)
        ):
            return {
                "text": "Knowledge unavailable for this role or surface.",
                "reply_markup": telegram_admin_ui.standard_back_markup(),
            }
        return {
            "text": render_contextual_knowledge(entry.key),
            "reply_markup": telegram_admin_ui.knowledge_detail_markup(return_action),
        }

    # ---- RELOAD_ROLES flow (admin-topic only) ----
    if action == "RELOAD_ROLES_CONFIRM":
        if owner_private:
            return {
                "text": "Access denied (wrong chat).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }
        return {
            "text": _format_card("🔄 Confirmation", "Confirm reloading role + permission configuration?"),
            "reply_markup": telegram_admin_ui.reload_confirm_markup(cancel_action="ROLES"),
        }

    if action == "RELOAD_ROLES_EXEC":
        from core.admin_permissions import has_permission
        if owner_private or not _is_admin_topic_context(message):
            return {
                "text": "Access denied (wrong chat).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }
        if not has_permission(user_id, "roles.write"):
            return {
                "text": "Access denied (missing permission).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }
        text = handle_admin_command_v2("/roles_reload", user_id)
        return {
            "text": _format_card("🔄 Roles Reload", text),
            "reply_markup": telegram_admin_ui.roles_identity_markup(can_reload=True),
        }

    # ---- Symbol toggle callbacks ----
    if action.startswith("SYM_TOGGLE:"):
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded. Please wait before making more changes.", "reply_markup": None}
        sym_payload = action[len("SYM_TOGGLE:"):]
        if ":" in sym_payload:
            parent_action, sym = sym_payload.split(":", 1)
        else:
            parent_action, sym = "HOME", sym_payload
        if parent_action not in {"HOME", "STRATEGY"}:
            parent_action = "HOME"
        result = handle_symbols_toggle(sym, user_id)
        # Refresh toggle markup
        try:
            all_syms = get_all_known_symbols()
            active = _active_symbols_for_markup()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active, parent_action=parent_action)
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        return {"text": _format_surface("symbols_coverage", "💱 Symbols Panel", result), "reply_markup": markup}

    if action == "SYMBOLS_ALL" or action.startswith("SYMBOLS_ALL:"):
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        parent_action = action.split(":", 1)[1] if ":" in action else "HOME"
        if parent_action not in {"HOME", "STRATEGY"}:
            parent_action = "HOME"
        result = handle_symbols_all(user_id)
        try:
            all_syms = get_all_known_symbols()
            active = _active_symbols_for_markup()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active, parent_action=parent_action)
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        return {"text": _format_surface("symbols_coverage", "💱 Symbols Panel", result), "reply_markup": markup}

    if action == "SYMBOLS_NONE" or action.startswith("SYMBOLS_NONE:"):
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        parent_action = action.split(":", 1)[1] if ":" in action else "HOME"
        if parent_action not in {"HOME", "STRATEGY"}:
            parent_action = "HOME"
        result = handle_symbols_none(user_id)
        try:
            all_syms = get_all_known_symbols()
            active = _active_symbols_for_markup()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active, parent_action=parent_action)
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        return {"text": _format_surface("symbols_coverage", "💱 Symbols Panel", result), "reply_markup": markup}

    # ---- Strategy profile callbacks ----
    if action == "PROFILE_HOME":
        current = get_current_strategy_profile()
        current_observation = get_current_strategy_profile_observation()
        return {
            "text": _format_surface(
                "strategy",
                "⚙️ Strategy Profile",
                f"Current profile: {current_observation}",
            ),
            "reply_markup": telegram_admin_ui.strategy_quick_markup(current),
        }

    if action.startswith("PROFILE_CONFIRM:"):
        profile = action[len("PROFILE_CONFIRM:"):]
        profile_upper = profile.upper()
        from core.admin_commands import STRATEGY_PROFILES
        defn = STRATEGY_PROFILES.get(profile_upper)
        if defn is None:
            return {"text": "Unknown profile.", "reply_markup": None}
        desc = (
            f"PRE={defn['score_thresholds']['PRE']} "
            f"CONFIRM={defn['score_thresholds']['CONFIRM']} "
            f"OPEN={defn['score_thresholds']['OPEN']} "
            f"SR={defn['sr_required_multiplier']}"
        )
        return {
            "text": _format_card(
                f"⚙️ Apply {profile_upper}?",
                "This will update future-facing strategy parameters to:\n"
                f"{desc}\n\n"
                "The change can alter which future candidates pass a gate. "
                "It does not guarantee more signals, a higher win rate, or profit.\n\n"
                "Confirm?"
            ),
            "reply_markup": telegram_admin_ui.strategy_profile_confirm_markup(profile_upper),
        }

    if action.startswith("PROFILE_EXEC:"):
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        profile = action[len("PROFILE_EXEC:"):]
        result = handle_strategy_profile(profile, user_id)
        current = get_current_strategy_profile()
        return {
            "text": _format_surface("strategy", "⚙️ Strategy Profile", result),
            "reply_markup": telegram_admin_ui.strategy_quick_markup(current),
        }

    # ---- Files/Docs callbacks ----
    if action == "FILES_HOME":
        if not _check_rate_limit(user_id, "files_list"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        return {
            "text": _format_surface("files_reports", "📁 File Browser", "Select an allowed artifact directory."),
            "reply_markup": telegram_admin_ui.files_home_markup(),
        }

    if action.startswith("FILES:"):
        if not _check_rate_limit(user_id, "files_list"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        parts = action.split(":")
        if len(parts) < 3:
            return {"text": "Invalid files action.", "reply_markup": None}
        dir_key = parts[1]
        try:
            page = int(parts[2])
        except Exception:
            page = 0
        info = handle_files_list(user_id, dir_key, page=page)
        if info.get("error"):
            return {"text": _format_card("📁 Files", f"Error: {info['error']}"), "reply_markup": telegram_admin_ui.files_home_markup()}
        fnames = info.get("filenames", [])
        title = info.get("title", "📁 Files")
        if not fnames:
            return {
                "text": _format_surface("files_reports", title, "No files found."),
                "reply_markup": telegram_admin_ui.files_home_markup(),
            }
        return {
            "text": _format_surface("files_reports", title, f"Page {info['page'] + 1}/{info['total_pages']}"),
            "reply_markup": telegram_admin_ui.files_list_markup(
                fnames, info["page"], info["total_pages"], dir_key
            ),
        }

    if action == "DOCS":
        if not _check_rate_limit(user_id, "files_list"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        info = handle_docs_list(user_id)
        if info.get("error"):
            return {"text": _format_card("📄 Documents", f"Error: {info['error']}"), "reply_markup": telegram_admin_ui.standard_back_markup()}
        fnames = info.get("filenames", [])
        if not fnames:
            return {
                "text": _format_surface("governance_docs", "📄 Documents", "No active documents found."),
                "reply_markup": telegram_admin_ui.standard_back_markup(
                    knowledge_key="governance_docs",
                    return_action="DOCS",
                ),
            }
        return {
            "text": _format_surface("governance_docs", "📄 Documents", f"{len(fnames)} file(s) available"),
            "reply_markup": telegram_admin_ui.docs_list_markup(fnames),
        }

    if action.startswith("FILE_DL:"):
        if not _check_rate_limit(user_id, "file_download"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        parts = action.split(":", 2)
        if len(parts) < 3:
            return {"text": "Invalid download action.", "reply_markup": None}
        dir_key = parts[1]
        filename = parts[2]
        path, err = handle_file_download_path(dir_key, filename, user_id)
        if err:
            return {"text": f"Download failed: {err}", "reply_markup": telegram_admin_ui.standard_back_markup()}
        # Signal the caller to send a document (not a text reply)
        return {"text": "", "reply_markup": None, "__file_path__": path, "__caption__": filename}

    if action == "LOG":
        if not _check_rate_limit(user_id, "diagnose"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        path, err = handle_log_export(user_id)
        if err:
            return {"text": f"Log export failed: {err}", "reply_markup": telegram_admin_ui.standard_back_markup()}
        return {"text": "", "reply_markup": None, "__file_path__": path, "__caption__": "binarybot_log.log"}

    if action == "DIAGNOSE" or action == "OPS_DIAGNOSE" or action == "SH_DIAGNOSE":
        if not _check_rate_limit(user_id, "diagnose"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        text = handle_diagnose(user_id)
        # Preserve caller context in the Back button.
        if action == "OPS_DIAGNOSE":
            diagnose_parent = "OPERATIONS"
        elif action == "SH_DIAGNOSE":
            diagnose_parent = "SYSHEALTH"
        else:
            diagnose_parent = "HOME"
        return {
            "text": _format_surface("diagnostics", "🩺 Diagnostics", text),
            "reply_markup": telegram_admin_ui.diagnose_markup(parent_action=diagnose_parent),
        }

    if action in {"AUDIT", "OPS_AUDIT", "SH_AUDIT", "DIAG_SH_AUDIT", "SECAUDIT_AUDIT"}:
        if not _check_rate_limit(user_id, "audit_runtime"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        path, err = handle_audit_runtime(user_id)
        if err:
            if action == "OPS_AUDIT":
                markup = telegram_admin_ui.diagnose_markup(parent_action="OPERATIONS")
            elif action == "DIAG_SH_AUDIT":
                markup = telegram_admin_ui.diagnose_markup(parent_action="SYSHEALTH")
            elif action == "SH_AUDIT":
                markup = telegram_admin_ui.system_health_markup()
            elif action == "SECAUDIT_AUDIT":
                markup = telegram_admin_ui.security_audit_markup()
            else:
                markup = telegram_admin_ui.diagnose_markup(parent_action="HOME")
            return {"text": f"Audit failed: {err}", "reply_markup": markup}
        return {"text": "", "reply_markup": None, "__file_path__": path, "__caption__": "binarybot_audit.json"}

    # ---- Canonical panel actions ----
    # Source: ADMIN_TREE_MAP_v2.0.0.md §6

    if action == "OPERATIONS":
        # Operations panel: engine state, ops actions, strategy parameter access.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.2; ADMIN_CONTROL_SPEC_v2.0.0.md §6
        text, _ = _render_panel_for_command("/engine", user_id, owner_private=owner_private)
        return {
            "text": _format_surface("operations", "⚙️ Operations", _surface_current_state(text)),
            "reply_markup": telegram_admin_ui.operations_markup(),
        }

    if action == "OPS_ENGINE":
        # Engine panel from Operations context — Back returns to Operations.
        include_reload = not owner_private
        markup = telegram_admin_ui.engine_markup(
            include_roles_reload=include_reload,
            parent_action="OPERATIONS",
        )
        text, _ = _render_panel_for_command("/engine", user_id, owner_private=owner_private)
        return {"text": text, "reply_markup": markup}

    if action == "SYMBOLS_COV":
        # Symbols & Coverage panel entry point.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.3; ADMIN_CONTROL_SPEC_v2.0.0.md §7
        try:
            all_syms = get_all_known_symbols()
            active = _active_symbols_for_markup()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active, parent_action="HOME")
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        text, _ = _render_panel_for_command("/symbols list", user_id, owner_private=owner_private)
        return {
            "text": _format_surface(
                "symbols_coverage",
                "💱 Symbols & Coverage",
                _surface_current_state(text),
            ),
            "reply_markup": markup,
        }

    if action == "DECISION_VIS":
        # Decision Visibility panel: last decision, gate results, rejection reasons.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.4; ADMIN_CONTROL_SPEC_v2.0.0.md §8
        text, _ = _render_panel_for_command("/debug", user_id, owner_private=owner_private)
        return {
            "text": _format_surface(
                "decision_visibility",
                "🔍 Decision Visibility",
                _surface_current_state(text),
            ),
            "reply_markup": telegram_admin_ui.decision_visibility_markup(),
        }

    if action == "STRATEGY_COMPARE":
        # Read-only comparison of live strategy_v2 and the canonical shadow pipeline.
        from core import storage as _storage
        from core.admin_views import render_strategy_comparison

        snapshot_path = _storage.root_path("observability", "canonical_shadow_snapshot.json")
        snapshot = _storage.load_json(snapshot_path, default={})
        return {
            "text": _format_surface(
                "decision_visibility",
                "⚖️ Strategy Comparison",
                _surface_current_state(
                    render_strategy_comparison(
                        snapshot if isinstance(snapshot, dict) else None,
                        now_ts=int(time.time()),
                    )
                ),
            ),
            "reply_markup": telegram_admin_ui.strategy_comparison_markup(),
        }

    if action == "DISTRIBUTION":
        # Distribution Control panel: route status, channel readiness.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.5; ADMIN_CONTROL_SPEC_v2.0.0.md §9
        from core.admin_views import render_distribution_panel
        routes = []
        if ADMIN_CONTROL_CHAT_ID:
            routes.append(f"Admin control chat: {ADMIN_CONTROL_CHAT_ID}")
        content = render_distribution_panel(ADMIN_CONTROL_CHAT_ID, ADMIN_CONTROL_THREAD_ID, routes)
        return {
            "text": _format_surface("distribution", "📡 Distribution Control", content),
            "reply_markup": telegram_admin_ui.distribution_markup(),
        }

    if action == "RESEARCH":
        # Research & Analytics panel: performance summaries, analytics reports.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.6; ADMIN_CONTROL_SPEC_v2.0.0.md §10
        text, _ = _render_panel_for_command("/report", user_id, owner_private=owner_private)
        try:
            import os as _os
            report_path = _find_latest_report_json()
            if report_path and _os.path.isfile(report_path):
                fname = _os.path.basename(report_path)
                markup = telegram_admin_ui.research_markup(has_file=True, filename=fname)
            else:
                markup = telegram_admin_ui.research_markup()
        except Exception:
            markup = telegram_admin_ui.research_markup()
        return {
            "text": _format_surface(
                "research_analytics",
                "📊 Research & Analytics",
                _surface_current_state(text),
            ),
            "reply_markup": markup,
        }

    if action == "INTELLIGENCE":
        # Intelligence panel: decision intelligence, drift signals, anomaly summaries.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.7; ADMIN_CONTROL_SPEC_v2.0.0.md §11
        from core.admin_views import render_intelligence_panel
        recent_events = _iter_recent_engine_events(limit=50)
        content = render_intelligence_panel(recent_events)
        return {
            "text": _format_surface("intelligence", "🧠 Intelligence", content),
            "reply_markup": telegram_admin_ui.intelligence_markup(),
        }

    if action == "SYSHEALTH":
        # System Health panel: aggregated health summary.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.10; ADMIN_CONTROL_SPEC_v2.0.0.md §14
        from core.admin_views import render_system_health_summary
        snapshot = _build_status_snapshot()
        content = render_system_health_summary(snapshot)
        return {
            "text": _format_surface("system_health", "🩺 System Health", content),
            "reply_markup": telegram_admin_ui.system_health_markup(),
        }

    if action == "SH_ENGINE":
        # Engine panel from System Health context — Back returns to System Health.
        include_reload = not owner_private
        markup = telegram_admin_ui.engine_markup(
            include_roles_reload=include_reload,
            parent_action="SYSHEALTH",
        )
        text, _ = _render_panel_for_command("/engine", user_id, owner_private=owner_private)
        return {"text": text, "reply_markup": markup}

    if action == "ROLES":
        # Roles & Identity panel: role info, scope summary, reload option for authorized roles.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.9
        from core.admin_permissions import has_permission
        can_reload = has_permission(user_id, "roles.write") and not owner_private
        text, _ = _render_panel_for_command("/roles", user_id, owner_private=owner_private)
        return {
            "text": text,
            "reply_markup": telegram_admin_ui.roles_identity_markup(can_reload=can_reload),
        }

    if action == "GOVDOCS":
        # Governance & Docs panel: canonical specs, change-control references.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.11
        if not _check_rate_limit(user_id, "files_list"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        info = handle_docs_list(user_id)
        if info.get("error"):
            return {
                "text": _format_card("📖 Governance & Docs", f"Error: {info['error']}"),
                "reply_markup": telegram_admin_ui.standard_back_markup(),
            }
        fnames = info.get("filenames", [])
        summary = f"{len(fnames)} canonical document(s) available." if fnames else "No documents found."
        return {
            "text": _format_surface("governance_docs", "📖 Governance & Docs", summary),
            "reply_markup": telegram_admin_ui.governance_docs_markup(fnames),
        }

    if action == "SECAUDIT":
        # Security & Audit panel: audit trail, admin action logs.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.12
        from core.admin_views import render_security_audit_panel
        content = render_security_audit_panel()
        return {
            "text": _format_surface("security_audit", "🔒 Security & Audit", content),
            "reply_markup": telegram_admin_ui.security_audit_markup(),
        }

    # ---- Standard navigation ----
    # HOME is handled below as the canonical admin root entry point.
    # SYMBOLS is handled explicitly below so the toggle markup gets the correct
    # parent_action="STRATEGY" (Symbols is a sub-page of Strategy, not Admin Home).
    command_for_action = {
        "STATUS": "/status",
        "STRATEGY": "/strategy",
        "THRESHOLDS": "/thresholds",
        "SR": "/sr",
        "SPIKE": "/spike",
        "ENGINE": "/engine",
        "DEBUG": "/debug",
        "REPORT": "/report",
        "ROLES": "/roles",
        "AFFILIATE": "/affiliate",
    }.get(action)

    # ---- SYMBOLS: reached from Strategy panel — Back returns to Strategy ----
    if action == "SYMBOLS":
        try:
            all_syms = get_all_known_symbols()
            active = _active_symbols_for_markup()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active, parent_action="STRATEGY")
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        text, _ = _render_panel_for_command("/symbols list", user_id, owner_private=owner_private)
        return {
            "text": _format_surface(
                "symbols_coverage",
                "💱 Symbols Panel",
                _surface_current_state(text),
            ),
            "reply_markup": markup,
        }

    # ---- HOME: canonical admin root — single source of truth ----
    if action == "HOME":
        text, markup = _build_canonical_admin_root_page(user_id, owner_private=owner_private)
        return {"text": text, "reply_markup": markup}

    if command_for_action is None:
        return {
            "text": "Unknown action.",
            "reply_markup": None,
            _CALLBACK_RECOVERY_KEY: _RECOVERY_UNKNOWN,
        }

    cmd = command_for_action.split()[0].lower()
    if cmd in admin_command_names():
        if owner_private and cmd not in _OWNER_PRIVATE_COMMANDS:
            return {
                "text": "Access denied (wrong chat).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }
        if not owner_private and not _is_admin_topic_context(message):
            return {
                "text": "Access denied (wrong chat).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }
    text, reply_markup = _render_panel_for_command(command_for_action, user_id, owner_private=owner_private)
    return {"text": text, "reply_markup": reply_markup}


def _build_status_snapshot() -> Dict[str, Any]:
    return build_status_snapshot()

def _iter_recent_engine_events(limit: int = 50) -> Optional[list]:
    """Return the most recent engine events (up to limit) from engine_events.jsonl."""
    events = _read_engine_events_observation()
    if events is None:
        return None
    return events[-limit:] if len(events) > limit else events


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


def _recovery_preferred_message_id(
    message: Dict[str, Any],
    user_id: int,
    callback_message_id: Optional[int],
) -> Optional[int]:
    """Choose a recovery edit target without reviving an obsolete panel.

    Normal callbacks prefer their originating message. Recovery callbacks are
    different: the originating message may be from an older navigation
    generation. When a different active message is tracked, leave the old
    message untouched and let the canonical delivery path edit the active one.
    If no active message is known, the callback message remains the safest
    available edit target and avoids creating an unnecessary second panel.
    """
    target = reply_target_from_message(message)
    if target is None:
        return callback_message_id
    active_message_id = telegram_app_nav.get_active_message(
        user_id=user_id,
        chat_id=target.chat_id,
        thread_id=target.thread_id,
    )
    if active_message_id is None or active_message_id == callback_message_id:
        return callback_message_id
    return None


def _callback_ack_result(recovery_kind: str) -> Dict[str, str]:
    return {
        "callback_ack_text": _CALLBACK_RECOVERY_ACK.get(
            recovery_kind,
            _CALLBACK_RECOVERY_ACK[_RECOVERY_UNKNOWN],
        )
    }


def _recover_application_home(
    message: Dict[str, Any],
    user_id: int,
    callback_message_id: Optional[int],
    *,
    primary_role: str,
    first_name: str,
    shadow_mode: Optional[bool],
    update_id: Any,
    recovery_kind: str,
) -> None:
    target = reply_target_from_message(message)
    if target is None:
        return
    page_text, page_markup = telegram_app_nav.handle_app_action(
        action=telegram_app_nav.ACT_HOME,
        user_id=user_id,
        primary_role=primary_role,
        first_name=first_name,
        shadow_mode=shadow_mode,
        chat_id=target.chat_id,
        thread_id=target.thread_id,
    )
    _send_interactive_page(
        message,
        user_id,
        page_text,
        page_markup,
        preferred_message_id=_recovery_preferred_message_id(
            message,
            user_id,
            callback_message_id,
        ),
        trace_context={
            "update_id": update_id,
            "command_family": f"APP_RECOVERY:{recovery_kind}",
        },
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
        if not _can_use_admin_callback(message, user_id):
            return {
                "text": "Access denied (wrong chat).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }
        return _handle_admin_navigation_action(admin_action, user_id, message)

    # ---- Admin panel callbacks: require authorised admin chat context (BATCH-05: fail-closed) ----
    context_message: Dict[str, Any] = {"chat": {"id": chat_id, "type": "private" if chat_id > 0 else "supergroup"}}
    if message_thread_id is not None:
        context_message["message_thread_id"] = message_thread_id
    if not _can_use_admin_callback(context_message, user_id):
        return {
            "text": "Access denied (wrong chat).",
            "reply_markup": None,
            _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
        }

    if data in _RETIRED_ADMIN_CALLBACKS or any(data.startswith(p) for p in _RETIRED_ADMIN_PREFIXES):
        return {
            "text": _RETIRED_MSG,
            "reply_markup": None,
            _CALLBACK_RECOVERY_KEY: _RECOVERY_RETIRED,
        }

    return {
        "text": "Unknown action.",
        "reply_markup": None,
        _CALLBACK_RECOVERY_KEY: _RECOVERY_UNKNOWN,
    }


def process_update(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Telegram update dispatcher.

    Public commands (/start, /help, /status):
      - Use the app-nav single-message pattern (edit active UI message if possible).
      - /start shows the role-scoped guided welcome page.
      - /help and /status show role-scoped help and status pages with navigation.

    Admin commands:
      - Require admin context (admin control topic or owner private DM).
      - Dispatched to handle_admin_command / panel handlers.

    APP: callbacks:
      - Application navigation (Home, Status, Help, Admin, etc.).
      - Edit the originating message (single-message pattern).

    ADMIN_NAV: callbacks:
      - Admin panel navigation within the admin control surface.
      - Require admin context.

    VOTE_ / OUTCOME: callbacks:
      - Forwarded to outcome_service without admin-context checks.

    File delivery:
      - __file_path__ responses → send_document (separate message, canonical exception).
    """
    try:
        update_id = update.get("update_id")
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
                shadow = observed_shadow_mode()
                primary_role = get_primary_role(user_id)
                first_name = (msg.get("from") or {}).get("first_name", "") or ""
                target = reply_target_from_message(msg)
                generation = None
                if target is not None:
                    generation = telegram_app_nav.begin_navigation_generation(
                        target.chat_id,
                        user_id,
                        target.thread_id,
                    )
                page_text, page_markup = telegram_app_nav.render_welcome_page(
                    user_id,
                    primary_role,
                    first_name=first_name,
                    shadow_mode=shadow,
                    generation=generation,
                )
                _handle_start_hard_reset(
                    msg=msg,
                    user_id=user_id,
                    update_id=update_id,
                    page_text=page_text,
                    page_markup=page_markup,
                )
                return

            if cmd == "/help":
                primary_role = get_primary_role(user_id)
                target = reply_target_from_message(msg)
                page_text, page_markup = telegram_app_nav.handle_app_action(
                    action=telegram_app_nav.ACT_HELP,
                    user_id=user_id,
                    primary_role=primary_role,
                    first_name=(msg.get("from") or {}).get("first_name", "") or "",
                    shadow_mode=observed_shadow_mode(),
                    chat_id=target.chat_id if target is not None else chat_id,
                    thread_id=target.thread_id if target is not None else None,
                )
                _send_interactive_page(
                    msg,
                    user_id,
                    page_text,
                    page_markup,
                    trace_context={"update_id": update_id, "command_family": "/help"},
                )
                return

            if cmd == "/status":
                primary_role = get_primary_role(user_id)
                target = reply_target_from_message(msg)
                page_text, page_markup = telegram_app_nav.handle_app_action(
                    action=telegram_app_nav.ACT_STATUS,
                    user_id=user_id,
                    primary_role=primary_role,
                    first_name=(msg.get("from") or {}).get("first_name", "") or "",
                    shadow_mode=observed_shadow_mode(),
                    status_snapshot=_build_status_snapshot(),
                    chat_id=target.chat_id if target is not None else chat_id,
                    thread_id=target.thread_id if target is not None else None,
                )
                _send_interactive_page(
                    msg,
                    user_id,
                    page_text,
                    page_markup,
                    trace_context={"update_id": update_id, "command_family": "/status"},
                )
                return

            if cmd in admin_command_names():
                if not _can_run_admin_command(msg, user_id, cmd):
                    _send_interactive_page(
                        msg,
                        user_id,
                        "Access denied (wrong chat).",
                        None,
                        trace_context={"update_id": update_id, "command_family": cmd},
                    )
                    return
                owner_private = _is_owner_private_for_message(msg, user_id)
                if cmd == "/admin":
                    target = reply_target_from_message(msg)
                    if target is not None:
                        nav_meta = telegram_app_nav.record_app_navigation(
                            chat_id=target.chat_id,
                            user_id=user_id,
                            action=telegram_app_nav.ACT_ADMIN,
                            thread_id=target.thread_id,
                        )
                        app_back_cb = (
                            telegram_app_nav.make_callback(
                                telegram_app_nav.ACT_BACK,
                                generation=nav_meta["generation"],
                            )
                            if nav_meta.get("include_back")
                            else None
                        )
                    else:
                        app_back_cb = None
                    response_text, reply_markup = _build_canonical_admin_root_page(
                        user_id,
                        owner_private=owner_private,
                        back_button_callback=app_back_cb,
                    )
                else:
                    response_text, reply_markup = _render_panel_for_command(text, user_id, owner_private=owner_private)
                # Handle file-path return signals
                if response_text.startswith("__FILE_PATH__:"):
                    file_path = response_text[len("__FILE_PATH__:"):]
                    _send_document_reply(msg, file_path, caption=cmd)
                    return
                _send_interactive_page(
                    msg,
                    user_id,
                    response_text,
                    reply_markup,
                    trace_context={"update_id": update_id, "command_family": cmd},
                )
                return
            _send_interactive_page(
                msg,
                user_id,
                UNKNOWN_COMMAND_TEXT,
                None,
                trace_context={"update_id": update_id, "command_family": cmd},
            )
            return

        if cb:
            data = cb.get("data") or ""
            msg_obj = cb.get("message") or {}
            chat_id = int(msg_obj["chat"]["id"])
            user_id = int(cb["from"]["id"])
            message_id = msg_obj.get("message_id")

            # ---- APP: navigation callbacks — handled for all roles, all contexts ----
            app_cb = telegram_app_nav.parse_app_callback(data)
            if (
                app_cb is None
                and isinstance(data, str)
                and data.startswith(telegram_app_nav.APP_NAV_PREFIX)
            ):
                _recover_application_home(
                    msg_obj,
                    user_id,
                    message_id,
                    primary_role=get_primary_role(user_id),
                    first_name=(cb.get("from") or {}).get("first_name", "") or "",
                    shadow_mode=observed_shadow_mode(),
                    update_id=update_id,
                    recovery_kind=_RECOVERY_UNKNOWN_APP,
                )
                return _callback_ack_result(_RECOVERY_UNKNOWN_APP)
            app_action = None if app_cb is None else app_cb.get("action")
            if app_action is not None:
                shadow = observed_shadow_mode()
                primary_role = get_primary_role(user_id)
                first_name = (cb.get("from") or {}).get("first_name", "") or ""
                thread_id = reply_target_from_message(msg_obj).thread_id if reply_target_from_message(msg_obj) is not None else None
                callback_generation = app_cb.get("generation") if isinstance(app_cb, dict) else None

                callback_is_stale = (
                    callback_generation is not None
                    and not telegram_app_nav.callback_generation_is_current(
                        chat_id=chat_id,
                        user_id=user_id,
                        callback_generation=callback_generation,
                        thread_id=thread_id,
                    )
                )
                if callback_is_stale:
                    _recover_application_home(
                        msg_obj,
                        user_id,
                        message_id,
                        primary_role=primary_role,
                        first_name=first_name,
                        shadow_mode=shadow,
                        update_id=update_id,
                        recovery_kind=_RECOVERY_STALE,
                    )
                    return _callback_ack_result(_RECOVERY_STALE)

                if not telegram_app_nav.is_dispatchable_app_action(app_action):
                    _recover_application_home(
                        msg_obj,
                        user_id,
                        message_id,
                        primary_role=primary_role,
                        first_name=first_name,
                        shadow_mode=shadow,
                        update_id=update_id,
                        recovery_kind=_RECOVERY_UNKNOWN_APP,
                    )
                    return _callback_ack_result(_RECOVERY_UNKNOWN_APP)

                # APP:ADMIN must resolve to the same canonical admin root as ADMIN_NAV:HOME.
                # Intercept here so both entry points produce an identical page.
                if app_action == telegram_app_nav.ACT_ADMIN:
                    owner_private = _is_owner_private_for_message(msg_obj, user_id)
                    if is_owner(user_id) or _is_admin_topic_context(msg_obj):
                        nav_meta = telegram_app_nav.record_app_navigation(
                            chat_id=chat_id,
                            user_id=user_id,
                            action=telegram_app_nav.ACT_ADMIN,
                            thread_id=thread_id,
                        )
                        page_text, page_markup = _build_canonical_admin_root_page(
                            user_id,
                            owner_private=owner_private,
                            back_button_callback=(
                                telegram_app_nav.make_callback(
                                    telegram_app_nav.ACT_BACK,
                                    generation=nav_meta["generation"],
                                )
                                if nav_meta.get("include_back")
                                else None
                            ),
                        )
                    else:
                        # Non-owner, non-admin context: informational redirect.
                        page_text, page_markup = telegram_app_nav.handle_app_action(
                            action=app_action,
                            user_id=user_id,
                            primary_role=primary_role,
                            first_name=first_name,
                            shadow_mode=shadow,
                            status_snapshot=None,
                            chat_id=chat_id,
                            thread_id=thread_id,
                            callback_generation=callback_generation,
                        )
                else:
                    page_text, page_markup = telegram_app_nav.handle_app_action(
                        action=app_action,
                        user_id=user_id,
                        primary_role=primary_role,
                        first_name=first_name,
                        shadow_mode=shadow,
                        status_snapshot=(
                            _build_status_snapshot()
                            if app_action in {telegram_app_nav.ACT_STATUS, telegram_app_nav.ACT_BACK}
                            else None
                        ),
                        chat_id=chat_id,
                        thread_id=thread_id,
                        callback_generation=callback_generation,
                    )
                _send_interactive_page(
                    msg_obj,
                    user_id,
                    page_text,
                    page_markup,
                    preferred_message_id=message_id,
                    trace_context={"update_id": update_id, "command_family": f"APP:{app_action}"},
                )
                return None

            # ---- ADMIN_NAV: callbacks — require admin context ----
            admin_action = telegram_admin_ui.parse_action(data)
            if admin_action is not None and not _can_use_admin_callback(msg_obj, user_id):
                return _callback_ack_result(_RECOVERY_UNAUTHORIZED)

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

            # File delivery: send as document, skip text edit
            if res.get("__file_path__"):
                file_path = res["__file_path__"]
                caption = res.get("__caption__", "")
                _send_document_reply(msg_obj, file_path, caption=caption)
                return None

            recovery_kind = res.get(_CALLBACK_RECOVERY_KEY)
            if recovery_kind == _RECOVERY_UNAUTHORIZED:
                return _callback_ack_result(_RECOVERY_UNAUTHORIZED)
            if recovery_kind in {_RECOVERY_UNKNOWN, _RECOVERY_RETIRED}:
                owner_private = _is_owner_private_for_message(msg_obj, user_id)
                page_text, page_markup = _build_canonical_admin_root_page(
                    user_id,
                    owner_private=owner_private,
                )
                _send_interactive_page(
                    msg_obj,
                    user_id,
                    page_text,
                    page_markup,
                    preferred_message_id=_recovery_preferred_message_id(
                        msg_obj,
                        user_id,
                        message_id,
                    ),
                    trace_context={
                        "update_id": update_id,
                        "command_family": f"CALLBACK_RECOVERY:{recovery_kind}",
                    },
                )
                return _callback_ack_result(recovery_kind)

            original_text = msg_obj.get("text", "") or ""

            if data.startswith("VOTE_|") and message_id:
                outcome_line = res.get("text", "")
                new_text = original_text
                if outcome_line and outcome_line not in original_text:
                    new_text = f"{original_text}\n\n{outcome_line}".strip()
                telegram_publisher.edit_message(chat_id, message_id, new_text, {"inline_keyboard": []})
            else:
                _send_interactive_page(
                    msg_obj,
                    user_id,
                    res.get("text", ""),
                    res.get("reply_markup"),
                    preferred_message_id=message_id,
                    trace_context={"update_id": update_id, "command_family": data.split(":", 1)[0] if isinstance(data, str) and ":" in data else data},
                )
            return None

    except Exception as e:
        observability_logger.log_error({
            "event_type": "error",
            "data": {
                "severity": "ERROR",
                "error_type": "bot_service_exception",
                "message": str(e),
            },
        })
