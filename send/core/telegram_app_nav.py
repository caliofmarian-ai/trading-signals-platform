"""
send/core/telegram_app_nav.py

Canonical Telegram application navigation layer.

Implements:
- Guided /start entry (canonical §E)
- Role-scoped home pages for every canonical role (canonical §C)
- Single active UI message model: navigate by editing, not sending new messages (canonical §D)
- Back / Home / Refresh behavior throughout (canonical §D)
- Page contracts: title, description, authorized actions (canonical §F)
- Application-level callback dispatch separate from admin-tree callbacks

Callback prefix: APP:

Canonical sources:
- TELEGRAM_UX_v2.0.0.md §15–§18 (Admin UX), §29, §31
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §3–§5
- ADMIN_TREE_MAP_v2.0.0.md §3 (/admin entry)

Implementation decision record:
- /start in private DM shows the role-scoped welcome page.
- OWNER in private DM gets full admin access button (consistent with existing DM owner privilege).
- Non-owner admin roles in private DM are informed of their role and directed to the admin
  control channel (security boundary preserved: admin control surface requires the configured chat).
- USER role /start shows the platform introduction and public action buttons.
- No button press grants any role; roles are resolved exclusively from admin_permissions.
- All pages have: title, concise description, authorized buttons, no dead end.
- Active message tracking is scoped by `(chat_id, user_id, thread_id)` and kept in-memory
  with minimal persisted metadata for restart/redeploy-safe recovery.
  If no tracked message exists for the current session, a new message is sent;
  subsequent navigations edit that message.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

from core.role_constants import (
    ROLE_OWNER,
    ROLE_PRIMARY_ADMIN,
    ROLE_STRATEGY_ADMIN,
    ROLE_RESEARCH_ADMIN,
    ROLE_ANALYST,
    ROLE_MODERATOR,
    ROLE_AFFILIATE_ADMIN,
    ROLE_USER,
    ROLE_LABELS,
    ADMIN_TIER_ROLES,
)
from state_store import state_store

# ---------------------------------------------------------------------------
# Callback routing
# ---------------------------------------------------------------------------

APP_NAV_PREFIX = "APP:"

# Application-level action constants
ACT_HOME = "HOME"
ACT_STATUS = "STATUS"
ACT_HELP = "HELP"
ACT_ADMIN = "ADMIN"


def make_callback(action: str) -> str:
    return f"{APP_NAV_PREFIX}{action}"


def parse_app_action(callback_data: str) -> Optional[str]:
    """Return the action key if callback_data is an APP: callback, else None."""
    if not isinstance(callback_data, str):
        return None
    if not callback_data.startswith(APP_NAV_PREFIX):
        return None
    action = callback_data[len(APP_NAV_PREFIX):].strip()
    return action or None


# ---------------------------------------------------------------------------
# Active UI message state
# Single-source-of-truth for the "current bot UI message" per chat/user/thread session.
# Hybrid model:
# - in-memory authoritative map for runtime-speed lookups
# - persisted minimal metadata for restart/redeploy-safe recovery
# ---------------------------------------------------------------------------

_SessionKey = Tuple[int, int, Optional[int]]

_ACTIVE_UI_VERSION = "1.0.0"
_DEFAULT_RETENTION_SECONDS = 7 * 24 * 60 * 60
_DEFAULT_MAX_SESSIONS = 1000

# { (chat_id, user_id, thread_id): {"message_id": int, "updated_ts": int} }
_active_ui: Dict[_SessionKey, Dict[str, int]] = {}


def _safe_env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except Exception:
        return default
    return value if value > 0 else default


_ACTIVE_UI_RETENTION_SECONDS = _safe_env_int("TELEGRAM_UI_STATE_RETENTION_SECONDS", _DEFAULT_RETENTION_SECONDS)
_ACTIVE_UI_MAX_SESSIONS = _safe_env_int("TELEGRAM_UI_STATE_MAX_SESSIONS", _DEFAULT_MAX_SESSIONS)


def _now_ts() -> int:
    return int(time.time())


def _persistence_enabled() -> bool:
    mode = os.getenv("TELEGRAM_UI_PERSISTENCE", "auto").strip().lower()
    if mode in {"0", "false", "off", "no", "disabled"}:
        return False
    if mode in {"1", "true", "on", "yes", "enabled"}:
        return True
    return bool(os.getenv("BINARYBOT_BASE_DIR", "").strip())


def _log_ui_state_warning(code: str, message: str, context: Dict[str, Any]) -> None:
    try:
        from core import observability_logger

        observability_logger.log_warning(
            warn_type=code,
            message=message,
            context=context,
            source={"module": "telegram_app_nav", "function": "_log_ui_state_warning"},
        )
    except Exception:
        pass


def _prune_active_ui(now_ts: Optional[int] = None) -> None:
    now = now_ts if now_ts is not None else _now_ts()
    cutoff = now - _ACTIVE_UI_RETENTION_SECONDS
    stale = [key for key, entry in _active_ui.items() if int(entry.get("updated_ts", 0)) < cutoff]
    for key in stale:
        _active_ui.pop(key, None)

    if len(_active_ui) <= _ACTIVE_UI_MAX_SESSIONS:
        return
    ordered = sorted(_active_ui.items(), key=lambda item: int(item[1].get("updated_ts", 0)), reverse=True)
    keep = {key for key, _ in ordered[:_ACTIVE_UI_MAX_SESSIONS]}
    for key in list(_active_ui):
        if key not in keep:
            _active_ui.pop(key, None)


def _serialize_active_ui() -> Dict[str, Any]:
    _prune_active_ui()
    sessions = [
        {
            "chat_id": key[0],
            "user_id": key[1],
            "thread_id": key[2],
            "message_id": int(entry["message_id"]),
            "updated_ts": int(entry.get("updated_ts", _now_ts())),
        }
        for key, entry in _active_ui.items()
    ]
    return {
        "version": _ACTIVE_UI_VERSION,
        "retention_seconds": _ACTIVE_UI_RETENTION_SECONDS,
        "max_sessions": _ACTIVE_UI_MAX_SESSIONS,
        "sessions": sessions,
        "last_updated_ts": _now_ts(),
    }


def _persist_active_ui() -> None:
    if not _persistence_enabled():
        return
    try:
        state_store.save_telegram_ui_state(_serialize_active_ui())
    except Exception as exc:
        _log_ui_state_warning(
            "TELEGRAM_UI_STATE_SAVE_FAILED",
            "Failed to persist Telegram UI active-message state",
            {"error": str(exc)},
        )


def _load_active_ui() -> None:
    _active_ui.clear()
    if not _persistence_enabled():
        return
    try:
        raw_state = state_store.load_telegram_ui_state()
    except Exception as exc:
        _log_ui_state_warning(
            "TELEGRAM_UI_STATE_LOAD_FAILED",
            "Telegram UI persisted state is unreadable; starting with empty active sessions",
            {"error": str(exc)},
        )
        return

    sessions = raw_state.get("sessions", [])
    if not isinstance(sessions, list):
        _log_ui_state_warning(
            "TELEGRAM_UI_STATE_INVALID_SHAPE",
            "Telegram UI persisted state has invalid sessions payload; starting empty",
            {},
        )
        return
    for item in sessions:
        if not isinstance(item, dict):
            continue
        try:
            key = _active_session_key(
                int(item.get("chat_id")),
                int(item.get("user_id")),
                int(item.get("thread_id")) if item.get("thread_id") is not None else None,
            )
            _active_ui[key] = {
                "message_id": int(item.get("message_id")),
                "updated_ts": int(item.get("updated_ts") or _now_ts()),
            }
        except Exception:
            continue
    _prune_active_ui()


def _active_session_key(chat_id: int, user_id: int, thread_id: Optional[int] = None) -> _SessionKey:
    return (int(chat_id), int(user_id), int(thread_id) if thread_id is not None else None)


def set_active_message(user_id: int, chat_id: int, message_id: int, thread_id: Optional[int] = None) -> None:
    """Record the active UI message for the chat/user/thread session."""
    _active_ui[_active_session_key(chat_id, user_id, thread_id)] = {
        "message_id": int(message_id),
        "updated_ts": _now_ts(),
    }
    _prune_active_ui()
    _persist_active_ui()


def get_active_message(user_id: int, chat_id: int, thread_id: Optional[int] = None) -> Optional[int]:
    """Return message_id for the active UI panel in this chat/user/thread session."""
    key = _active_session_key(chat_id, user_id, thread_id)
    entry = _active_ui.get(key)
    if entry is None:
        return None
    now_ts = _now_ts()
    if int(entry.get("updated_ts", 0)) < (now_ts - _ACTIVE_UI_RETENTION_SECONDS):
        _active_ui.pop(key, None)
        _persist_active_ui()
        return None
    return int(entry.get("message_id"))


def clear_active_message(user_id: int, chat_id: int, thread_id: Optional[int] = None) -> None:
    """Forget active UI message for this chat/user/thread session."""
    key = _active_session_key(chat_id, user_id, thread_id)
    removed = _active_ui.pop(key, None)
    if removed is not None:
        _persist_active_ui()


_load_active_ui()


# ---------------------------------------------------------------------------
# Internal keyboard helpers
# ---------------------------------------------------------------------------

def _btn(text: str, action: str) -> Dict[str, str]:
    return {"text": text, "callback_data": make_callback(action)}


def _kb(rows: List[List[Dict[str, str]]]) -> Dict[str, List[List[Dict[str, str]]]]:
    return {"inline_keyboard": rows}


# ---------------------------------------------------------------------------
# Page renderers — one per canonical page/surface
# Each renderer returns (text, reply_markup).
#
# Page contract (canonical §F):
#   - identifiable page title
#   - concise canonical explanation
#   - only authorized actions
#   - understandable button labels
#   - appropriate navigation (Back/Home/Refresh where applicable)
#   - no dead end
#   - consistent rendering from slash command and callback entry points
# ---------------------------------------------------------------------------


def render_welcome_page(
    user_id: int,
    primary_role: str,
    first_name: str = "",
    shadow_mode: bool = False,
) -> Tuple[str, Dict]:
    """
    Role-scoped welcome page rendered on /start.

    Source: TELEGRAM_UX_v2.0.0.md §15–§18; ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5

    Design decisions (not canonically prescribed, minimum neutral behavior):
    - OWNER private DM: full admin access available via button.
    - Non-owner admin roles in any context: show role, inform of admin channel.
    - USER role: show platform introduction, public action buttons.
    - No button grants any role.
    """
    greeting = f"Hello, {first_name}!" if first_name else "Hello!"
    role_label = ROLE_LABELS.get(primary_role, primary_role)
    shadow_note = "\n\n⚠️ Shadow mode is active. No live signal delivery." if shadow_mode else ""

    if primary_role == ROLE_OWNER:
        text = (
            f"🤖 *BinaryBot*{shadow_note}\n\n"
            f"{greeting}\n\n"
            f"You are connected as *{role_label}* — the supreme governance authority.\n\n"
            "You have full access to the admin control surface, including all governance, "
            "operational, research and audit surfaces."
        )
        markup = _kb([
            [_btn("⚙️ Admin Control Surface", ACT_ADMIN)],
            [_btn("📊 System Status", ACT_STATUS)],
        ])

    elif primary_role in ADMIN_TIER_ROLES:
        text = (
            f"🤖 *BinaryBot*{shadow_note}\n\n"
            f"{greeting}\n\n"
            f"You are connected as *{role_label}*.\n\n"
            "Your access is configured for the designated admin control channel. "
            "Navigate to the admin control channel to access your control surface.\n\n"
            "From here you can check system status."
        )
        markup = _kb([
            [_btn("📊 System Status", ACT_STATUS)],
            [_btn("❓ Help", ACT_HELP)],
        ])

    else:
        # USER role: platform introduction
        text = (
            f"🤖 *BinaryBot*{shadow_note}\n\n"
            f"{greeting}\n\n"
            "Welcome to *BinaryBot* — an automated trading signal platform.\n\n"
            "This bot delivers trading signals to configured trading channels. "
            "You can check the system status or view the command list below."
        )
        markup = _kb([
            [_btn("📊 System Status", ACT_STATUS)],
            [_btn("❓ Help", ACT_HELP)],
        ])

    return text, markup


def render_status_page(snapshot: Dict) -> Tuple[str, Dict]:
    """
    Public system status page — consistent with the canonical render_status_text fields.

    Source: TELEGRAM_UX_v2.0.0.md §15.2 (Admin UX exposes operational state);
            Public status is canonical via /status command.

    This page is accessible to all roles and provides a read-only summary.
    The field set mirrors the original render_status_text to preserve information parity.
    """
    overall = snapshot.get("overall_state", "UNKNOWN")
    phase = snapshot.get("runtime_phase", "unknown")
    health = snapshot.get("runtime_message", "unknown")
    recovery = snapshot.get("recovery_state", "UNKNOWN")
    market = snapshot.get("market_data_state", "UNKNOWN")
    telegram = snapshot.get("telegram_state", "UNKNOWN")
    fsm = snapshot.get("fsm_state", "UNKNOWN")
    shadow = snapshot.get("shadow_mode", "OFF")
    broker = snapshot.get("broker_state", "NOT AVAILABLE")

    text = (
        "📊 *System Status*\n\n"
        f"Overall: {overall}\n"
        f"Runtime phase: {phase}\n"
        f"Health: {health}\n"
        f"Recovery: {recovery}\n"
        f"Market data: {market}\n"
        f"Telegram: {telegram}\n"
        f"FSM: {fsm}\n"
        f"Shadow mode: {shadow}\n"
        f"Broker execution: {broker}"
    )
    note = snapshot.get("market_data_note")
    if isinstance(note, str) and note.strip():
        text += f"\n\nMarket note: {note.strip()}"

    markup = _kb([
        [_btn("🔄 Refresh", ACT_STATUS)],
        [_btn("🏠 Home", ACT_HOME)],
    ])
    return text, markup


def render_help_page(primary_role: str) -> Tuple[str, Dict]:
    """
    Role-scoped help page — shows commands appropriate for the user's role.

    Source: TELEGRAM_UX_v2.0.0.md §17 (admin command families; role-scoped availability).

    Design decision: Public commands are listed for all roles. Admin commands are
    mentioned only for admin-tier users and only as navigation hints (they require
    the admin control channel, not this button).
    """
    is_admin = primary_role in ADMIN_TIER_ROLES

    if is_admin:
        text = (
            "❓ *Help — BinaryBot*\n\n"
            "*Public commands (available anywhere):*\n"
            "/start — Show the welcome page\n"
            "/status — System status\n"
            "/help — This help page\n\n"
            "*Admin commands (admin control channel required):*\n"
            "/admin — Admin control surface\n"
            "/engine — Engine status\n"
            "/debug — Latest decision snapshot\n"
            "/report — Latest strategy report\n"
            "/roles — Configured roles\n"
            "… and more (see admin control surface)\n\n"
            "_Your role:_ " + ROLE_LABELS.get(primary_role, primary_role)
        )
    else:
        text = (
            "❓ *Help — BinaryBot*\n\n"
            "*Available commands:*\n"
            "/start — Show the welcome page\n"
            "/status — System status\n"
            "/help — This help page\n\n"
            "BinaryBot delivers trading signals to configured channels. "
            "You will receive signals automatically when they are generated."
        )

    markup = _kb([
        [_btn("📊 System Status", ACT_STATUS)],
        [_btn("🏠 Home", ACT_HOME)],
    ])
    return text, markup


# ---------------------------------------------------------------------------
# Application callback dispatcher
# ---------------------------------------------------------------------------

def handle_app_action(
    action: str,
    user_id: int,
    primary_role: str,
    first_name: str = "",
    shadow_mode: bool = False,
    status_snapshot: Optional[Dict] = None,
) -> Tuple[str, Dict]:
    """
    Dispatch an APP: callback action to the appropriate page renderer.

    Returns (text, reply_markup).

    All actions produce a complete, navigable page. No dead ends.
    """
    if action == ACT_HOME:
        return render_welcome_page(user_id, primary_role, first_name=first_name, shadow_mode=shadow_mode)

    if action == ACT_STATUS:
        snap = status_snapshot if status_snapshot is not None else {}
        return render_status_page(snap)

    if action == ACT_HELP:
        return render_help_page(primary_role)

    if action == ACT_ADMIN:
        # Only OWNER can trigger admin surface from app nav (other roles use admin channel).
        if primary_role == ROLE_OWNER:
            # Delegate to admin home; return a pointer page.
            text = (
                "⚙️ *Admin Control Surface*\n\n"
                "Use /admin to access the full role-scoped admin tree, or "
                "navigate directly using the admin control channel.\n\n"
                "Quick actions are also available via slash commands:\n"
                "/engine — Engine status\n"
                "/debug — Decision snapshot\n"
                "/roles — Configured roles"
            )
            markup = _kb([
                [_btn("🏠 Home", ACT_HOME)],
            ])
        else:
            text = (
                "⚙️ *Admin Control Surface*\n\n"
                "The admin control surface is available in the configured admin control channel. "
                "Please navigate there to access your role-scoped controls."
            )
            markup = _kb([
                [_btn("🏠 Home", ACT_HOME)],
            ])
        return text, markup

    # Unknown action: safe fallback to home (canonical: no dead ends)
    return render_welcome_page(user_id, primary_role, first_name=first_name, shadow_mode=shadow_mode)
