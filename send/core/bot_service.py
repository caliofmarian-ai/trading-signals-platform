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
import time
from typing import Optional, Dict, Any

from core import telegram_publisher
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
    _load_active_symbols,
    _find_latest_report_json,
    _iter_jsonl,
    ENGINE_EVENTS_PATH,
    REPORTS_DIR,
)
from core.admin_permissions import is_owner, get_primary_role
from core import observability_logger
from core import outcome_service
from core import fsm_runtime
from core.telegram_runtime import admin_command_names, render_help_text, render_start_text, render_status_text
from core.telegram_targets import env_chat_id, env_thread_id, reply_target_from_message, valid_thread_id
from core import telegram_admin_ui
from core import telegram_app_nav
from monitoring import restart_guard
from runtime import runtime_status

# ---- Paths ----
OUTCOMES_PATH = "/opt/binarybot/state/outcomes.json"

# ---- Env ----
ADMIN_CONTROL_CHAT_ID = env_chat_id("ADMIN_CONTROL_CHAT_ID") or 0
ADMIN_CONTROL_THREAD_ID = env_thread_id("ADMIN_CONTROL_THREAD_ID") or 0
UNKNOWN_COMMAND_TEXT = "Unknown command. Use /help to view available commands."

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


def _send_app_nav_reply(
    message: Dict[str, Any],
    user_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]],
) -> None:
    """
    Send or edit the single active UI message for this user.

    - If we have an existing active UI message for this user in the same chat,
      attempt to edit it (single-message navigation pattern, canonical §D).
    - On edit failure (message deleted/too old), or when no active message exists,
      send a new message and record it as the active UI message.
    - File/document delivery bypasses this (separate mechanism, canonical §D).
    """
    target = reply_target_from_message(message)
    if target is None:
        return

    chat_id = target.chat_id
    active = telegram_app_nav.get_active_message(user_id)

    if active is not None and active[0] == chat_id:
        # Try to edit the existing active message
        active_message_id = active[1]
        try:
            telegram_publisher.edit_message(chat_id, active_message_id, text, reply_markup)
            return
        except Exception:
            # Edit failed (message too old, deleted, etc.) — fall through to send new
            telegram_app_nav.clear_active_message(user_id)

    # Send a new message and track it
    try:
        result = telegram_publisher.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            thread_id=target.thread_id,
        )
        # Track the new message if the publisher returns message_id
        if isinstance(result, dict):
            msg_result = result.get("result") or {}
            new_msg_id = msg_result.get("message_id")
            if new_msg_id:
                telegram_app_nav.set_active_message(user_id, chat_id, new_msg_id)
    except Exception:
        pass



def _format_card(title: str, body: str) -> str:
    clean_body = str(body or "").strip()
    if not clean_body:
        return title
    return f"{title}\n\n{clean_body}"


def _admin_reply_markup(cmd: str, user_id: int, *, owner_private: bool) -> Optional[Dict[str, Any]]:
    role = get_primary_role(user_id)
    if cmd == "/admin":
        return telegram_admin_ui.admin_home_markup(role=role, include_roles_reload=not owner_private)
    if cmd == "/strategy":
        return telegram_admin_ui.strategy_markup()
    if cmd in {"/thresholds", "/sr", "/spike"}:
        return telegram_admin_ui.strategy_markup()
    if cmd == "/symbols" or cmd == "/symbols list":
        # Use toggle markup if possible; fall back to simple markup
        try:
            all_syms = get_all_known_symbols()
            active = _load_active_symbols()
            return telegram_admin_ui.symbols_toggle_markup(all_syms, active)
        except Exception:
            return telegram_admin_ui.symbols_markup()
    if cmd == "/engine":
        return telegram_admin_ui.engine_markup(include_roles_reload=not owner_private)
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
        return telegram_admin_ui.diagnose_markup()
    if cmd in {"/debug", "/roles", "/affiliate", "/log", "/audit_runtime"}:
        return telegram_admin_ui.standard_back_markup()
    return None


def _render_panel_for_command(cmd: str, user_id: int, *, owner_private: bool) -> tuple[str, Optional[Dict[str, Any]]]:
    if cmd == "/status":
        return _format_card("📊 Status Panel", render_status_text(_build_status_snapshot())), telegram_admin_ui.status_markup()

    response_text = handle_admin_command_v2(cmd, user_id)
    title_map = {
        "/admin": "🛠️ Admin Panel",
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
    markup = _admin_reply_markup(base_cmd, user_id, owner_private=owner_private)
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

    # ---- RELOAD_ROLES flow (admin-topic only) ----
    if action == "RELOAD_ROLES_CONFIRM":
        if owner_private:
            return {"text": "Access denied (wrong chat).", "reply_markup": None}
        return {
            "text": _format_card("🔄 Confirmation", "Confirm reloading role + permission configuration?"),
            "reply_markup": telegram_admin_ui.reload_confirm_markup(),
        }

    # ---- Symbol toggle callbacks ----
    if action.startswith("SYM_TOGGLE:"):
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded. Please wait before making more changes.", "reply_markup": None}
        sym = action[len("SYM_TOGGLE:"):]
        result = handle_symbols_toggle(sym, user_id)
        # Refresh toggle markup
        try:
            all_syms = get_all_known_symbols()
            active = _load_active_symbols()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active)
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        return {"text": _format_card("💱 Symbols Panel", result), "reply_markup": markup}

    if action == "SYMBOLS_ALL":
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        result = handle_symbols_all(user_id)
        try:
            all_syms = get_all_known_symbols()
            active = _load_active_symbols()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active)
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        return {"text": _format_card("💱 Symbols Panel", result), "reply_markup": markup}

    if action == "SYMBOLS_NONE":
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        result = handle_symbols_none(user_id)
        try:
            all_syms = get_all_known_symbols()
            active = _load_active_symbols()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active)
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        return {"text": _format_card("💱 Symbols Panel", result), "reply_markup": markup}

    # ---- Strategy profile callbacks ----
    if action == "PROFILE_HOME":
        current = get_current_strategy_profile()
        return {
            "text": _format_card("⚙️ Strategy Profile", f"Current profile: {current or 'custom'}"),
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
                f"This will set:\n{desc}\n\nConfirm?"
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
            "text": _format_card("⚙️ Strategy Profile", result),
            "reply_markup": telegram_admin_ui.strategy_quick_markup(current),
        }

    # ---- Files/Docs callbacks ----
    if action == "FILES_HOME":
        if not _check_rate_limit(user_id, "files_list"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        return {
            "text": "📁 File Browser\n\nSelect a directory:",
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
                "text": _format_card(title, "No files found."),
                "reply_markup": telegram_admin_ui.files_home_markup(),
            }
        return {
            "text": _format_card(title, f"Page {info['page'] + 1}/{info['total_pages']}"),
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
            return {"text": "📄 Documents\n\nNo documents found.", "reply_markup": telegram_admin_ui.standard_back_markup()}
        return {
            "text": _format_card("📄 Documents", f"{len(fnames)} file(s) available"),
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
        return {"text": text, "reply_markup": telegram_admin_ui.diagnose_markup()}

    if action == "AUDIT" or action == "SH_AUDIT" or action == "SECAUDIT_AUDIT":
        if not _check_rate_limit(user_id, "audit_runtime"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        path, err = handle_audit_runtime(user_id)
        if err:
            return {"text": f"Audit failed: {err}", "reply_markup": telegram_admin_ui.standard_back_markup()}
        return {"text": "", "reply_markup": None, "__file_path__": path, "__caption__": "binarybot_audit.json"}

    # ---- Canonical panel actions ----
    # Source: ADMIN_TREE_MAP_v2.0.0.md §6

    if action == "OPERATIONS":
        # Operations panel: engine state, ops actions, strategy parameter access.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.2; ADMIN_CONTROL_SPEC_v2.0.0.md §6
        text, _ = _render_panel_for_command("/engine", user_id, owner_private=owner_private)
        return {
            "text": _format_card("⚙️ Operations", text.split("\n\n", 1)[-1] if "\n\n" in text else text),
            "reply_markup": telegram_admin_ui.operations_markup(),
        }

    if action == "OPS_ENGINE":
        text, markup = _render_panel_for_command("/engine", user_id, owner_private=owner_private)
        return {"text": text, "reply_markup": markup}

    if action == "SYMBOLS_COV":
        # Symbols & Coverage panel entry point.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.3; ADMIN_CONTROL_SPEC_v2.0.0.md §7
        try:
            all_syms = get_all_known_symbols()
            active = _load_active_symbols()
            markup = telegram_admin_ui.symbols_toggle_markup(all_syms, active)
        except Exception:
            markup = telegram_admin_ui.symbols_markup()
        text, _ = _render_panel_for_command("/symbols list", user_id, owner_private=owner_private)
        return {"text": _format_card("💱 Symbols & Coverage", text.split("\n\n", 1)[-1] if "\n\n" in text else text), "reply_markup": markup}

    if action == "DECISION_VIS":
        # Decision Visibility panel: last decision, gate results, rejection reasons.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.4; ADMIN_CONTROL_SPEC_v2.0.0.md §8
        text, _ = _render_panel_for_command("/debug", user_id, owner_private=owner_private)
        return {
            "text": _format_card("🔍 Decision Visibility", text.split("\n\n", 1)[-1] if "\n\n" in text else text),
            "reply_markup": telegram_admin_ui.decision_visibility_markup(),
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
            "text": _format_card("📡 Distribution Control", content),
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
            "text": _format_card("📊 Research & Analytics", text.split("\n\n", 1)[-1] if "\n\n" in text else text),
            "reply_markup": markup,
        }

    if action == "INTELLIGENCE":
        # Intelligence panel: decision intelligence, drift signals, anomaly summaries.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.7; ADMIN_CONTROL_SPEC_v2.0.0.md §11
        from core.admin_views import render_intelligence_panel
        try:
            recent_events: list = []
            for ev in _iter_recent_engine_events(limit=50):
                recent_events.append(ev)
        except Exception:
            recent_events = []
        content = render_intelligence_panel(recent_events)
        return {
            "text": _format_card("🧠 Intelligence", content),
            "reply_markup": telegram_admin_ui.intelligence_markup(),
        }

    if action == "SYSHEALTH":
        # System Health panel: aggregated health summary.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.10; ADMIN_CONTROL_SPEC_v2.0.0.md §14
        from core.admin_views import render_system_health_summary
        snapshot = _build_status_snapshot()
        content = render_system_health_summary(snapshot)
        return {
            "text": _format_card("🩺 System Health", content),
            "reply_markup": telegram_admin_ui.system_health_markup(),
        }

    if action == "SH_ENGINE":
        text, markup = _render_panel_for_command("/engine", user_id, owner_private=owner_private)
        return {"text": text, "reply_markup": markup}

    if action == "ROLES":
        # Roles & Identity panel: role info, scope summary, reload option for authorized roles.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.9
        from core.admin_permissions import get_primary_role, has_permission
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
            "text": _format_card("📖 Governance & Docs", summary),
            "reply_markup": telegram_admin_ui.governance_docs_markup(fnames),
        }

    if action == "SECAUDIT":
        # Security & Audit panel: audit trail, admin action logs.
        # Source: ADMIN_TREE_MAP_v2.0.0.md §6.12
        from core.admin_views import render_security_audit_panel
        content = render_security_audit_panel()
        return {
            "text": _format_card("🔒 Security & Audit", content),
            "reply_markup": telegram_admin_ui.security_audit_markup(),
        }

    # ---- Standard navigation ----
    command_for_action = {
        "HOME": "/admin",
        "STATUS": "/status",
        "STRATEGY": "/strategy",
        "THRESHOLDS": "/thresholds",
        "SR": "/sr",
        "SPIKE": "/spike",
        "SYMBOLS": "/symbols list",
        "SYMBOLS_COV": "/symbols list",
        "ENGINE": "/engine",
        "DEBUG": "/debug",
        "REPORT": "/report",
        "ROLES": "/roles",
        "AFFILIATE": "/affiliate",
        "RELOAD_ROLES_EXEC": "/roles_reload",
    }.get(action)

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


def _iter_recent_engine_events(limit: int = 50) -> list:
    """Return the most recent engine events (up to limit) from engine_events.jsonl."""
    try:
        events = list(_iter_jsonl(ENGINE_EVENTS_PATH))
        return events[-limit:] if len(events) > limit else events
    except Exception:
        return []


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
                shadow = _env_flag("SHADOW_MODE", default=False)
                primary_role = get_primary_role(user_id)
                first_name = (msg.get("from") or {}).get("first_name", "") or ""
                page_text, page_markup = telegram_app_nav.render_welcome_page(
                    user_id, primary_role, first_name=first_name, shadow_mode=shadow
                )
                _send_app_nav_reply(msg, user_id, page_text, page_markup)
                return

            if cmd == "/help":
                primary_role = get_primary_role(user_id)
                page_text, page_markup = telegram_app_nav.render_help_page(primary_role)
                _send_app_nav_reply(msg, user_id, page_text, page_markup)
                return

            if cmd == "/status":
                page_text, page_markup = telegram_app_nav.render_status_page(_build_status_snapshot())
                _send_app_nav_reply(msg, user_id, page_text, page_markup)
                return

            if cmd in admin_command_names():
                if not _can_run_admin_command(msg, user_id, cmd):
                    _send_reply(msg, "Access denied (wrong chat).")
                    return
                owner_private = _is_owner_private_for_message(msg, user_id)
                response_text, reply_markup = _render_panel_for_command(text, user_id, owner_private=owner_private)
                # Handle file-path return signals
                if response_text.startswith("__FILE_PATH__:"):
                    file_path = response_text[len("__FILE_PATH__:"):]
                    _send_document_reply(msg, file_path, caption=cmd)
                    return
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

            # ---- APP: navigation callbacks — handled for all roles, all contexts ----
            app_action = telegram_app_nav.parse_app_action(data)
            if app_action is not None:
                shadow = _env_flag("SHADOW_MODE", default=False)
                primary_role = get_primary_role(user_id)
                first_name = (cb.get("from") or {}).get("first_name", "") or ""
                page_text, page_markup = telegram_app_nav.handle_app_action(
                    action=app_action,
                    user_id=user_id,
                    primary_role=primary_role,
                    first_name=first_name,
                    shadow_mode=shadow,
                    status_snapshot=_build_status_snapshot() if app_action == telegram_app_nav.ACT_STATUS else None,
                )
                # Edit the message that held the button (single-message pattern)
                if message_id:
                    try:
                        telegram_publisher.edit_message(chat_id, message_id, page_text, page_markup)
                        # Update active message tracking to this message
                        telegram_app_nav.set_active_message(user_id, chat_id, message_id)
                        return
                    except Exception:
                        pass
                # Fallback: send new message
                _send_app_nav_reply(msg_obj, user_id, page_text, page_markup)
                return

            # ---- ADMIN_NAV: callbacks — require admin context ----
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

            # File delivery: send as document, skip text edit
            if res.get("__file_path__"):
                file_path = res["__file_path__"]
                caption = res.get("__caption__", "")
                _send_document_reply(msg_obj, file_path, caption=caption)
                return

            original_text = msg_obj.get("text", "") or ""

            if data.startswith("VOTE_|") and message_id:
                outcome_line = res.get("text", "")
                new_text = original_text
                if outcome_line and outcome_line not in original_text:
                    new_text = f"{original_text}\n\n{outcome_line}".strip()
                telegram_publisher.edit_message(chat_id, message_id, new_text, {"inline_keyboard": []})
            elif message_id and res.get("reply_markup") is not None:
                try:
                    telegram_publisher.edit_message(
                        chat_id, message_id, res.get("text"), res.get("reply_markup")
                    )
                except Exception:
                    # Graceful fallback: send as new message if edit fails
                    _send_reply(msg_obj, res.get("text", ""), res.get("reply_markup"))
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
