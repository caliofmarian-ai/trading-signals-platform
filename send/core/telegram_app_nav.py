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
import json
import hashlib
import sys
import threading
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
from core.telegram_targets import valid_thread_id
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
_active_ui_lock = threading.RLock()
_active_ui_initialized = False
_active_ui_init_path: Optional[str] = None
_last_load_result: Dict[str, Any] = {"status": "not_started"}
_last_save_result: Dict[str, Any] = {"status": "not_started"}


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


def _runtime_path_ready() -> bool:
    return bool(os.getenv("BINARYBOT_BASE_DIR", "").strip())


def _deployment_identifier() -> str:
    for name in ("RAILWAY_DEPLOYMENT_ID", "RAILWAY_SERVICE_ID", "RUN_ID"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return "unknown"


def _emit_stdout_diagnostic(code: str, context: Dict[str, Any]) -> None:
    payload = {
        "component": "telegram_ui_state",
        "code": code,
        "pid": os.getpid(),
        "deployment_id": _deployment_identifier(),
        "context": context,
    }
    try:
        print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)
    except Exception:
        pass


def _log_ui_state_warning(code: str, message: str, context: Dict[str, Any]) -> None:
    _emit_stdout_diagnostic(code, context)
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
    global _last_save_result
    if not _persistence_enabled() or not _runtime_path_ready():
        _last_save_result = {
            "status": "skipped",
            "reason": "persistence_disabled_or_runtime_path_unset",
            "path": _resolved_state_path(),
        }
        return
    try:
        state_store.save_telegram_ui_state(_serialize_active_ui())
        _last_save_result = {
            "status": "ok",
            "path": _resolved_state_path(),
            "session_count": len(_active_ui),
        }
    except Exception as exc:
        _last_save_result = {
            "status": "error",
            "error": str(exc),
            "path": _resolved_state_path(),
        }
        _log_ui_state_warning(
            "TELEGRAM_UI_STATE_SAVE_FAILED",
            "Failed to persist Telegram UI active-message state",
            _last_save_result,
        )


def _resolved_state_path() -> Optional[str]:
    try:
        return state_store.telegram_ui_state_path()
    except Exception:
        return None


def _load_active_ui() -> Dict[str, Any]:
    global _last_load_result
    _active_ui.clear()
    path = _resolved_state_path()
    if not _persistence_enabled():
        _last_load_result = {"status": "skipped", "reason": "persistence_disabled", "path": path}
        return dict(_last_load_result)
    if not _runtime_path_ready():
        _last_load_result = {"status": "deferred", "reason": "runtime_path_unset", "path": path}
        return dict(_last_load_result)
    try:
        raw_state = state_store.load_telegram_ui_state()
    except Exception as exc:
        _last_load_result = {"status": "error", "error": str(exc), "path": path}
        _log_ui_state_warning(
            "TELEGRAM_UI_STATE_LOAD_FAILED",
            "Telegram UI persisted state is unreadable; starting with empty active sessions",
            _last_load_result,
        )
        return dict(_last_load_result)

    sessions = raw_state.get("sessions", [])
    if not isinstance(sessions, list):
        _last_load_result = {"status": "error", "reason": "invalid_sessions_payload", "path": path}
        _log_ui_state_warning(
            "TELEGRAM_UI_STATE_INVALID_SHAPE",
            "Telegram UI persisted state has invalid sessions payload; starting empty",
            _last_load_result,
        )
        return dict(_last_load_result)
    for item in sessions:
        if not isinstance(item, dict):
            continue
        try:
            key = normalize_session_key(
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
    _last_load_result = {
        "status": "ok",
        "path": path,
        "session_count": len(_active_ui),
    }
    return dict(_last_load_result)


def normalize_session_key(chat_id: int, user_id: int, thread_id: Optional[int] = None) -> _SessionKey:
    normalized_chat_id = int(chat_id)
    normalized_user_id = int(user_id)
    normalized_thread_id = valid_thread_id(
        normalized_chat_id,
        int(thread_id) if thread_id is not None else None,
    )
    return (normalized_chat_id, normalized_user_id, normalized_thread_id)


def session_key_fingerprint(chat_id: int, user_id: int, thread_id: Optional[int] = None) -> str:
    key = normalize_session_key(chat_id, user_id, thread_id)
    raw = f"{key[0]}:{key[1]}:{key[2]}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def initialize_active_ui_state(*, force_reload: bool = False) -> Dict[str, Any]:
    global _active_ui_initialized, _active_ui_init_path
    with _active_ui_lock:
        path = _resolved_state_path()
        if (
            not force_reload
            and _active_ui_initialized
            and _active_ui_init_path == path
            and (_runtime_path_ready() or not _persistence_enabled())
        ):
            return get_runtime_diagnostics()
        load_result = _load_active_ui()
        _active_ui_initialized = True
        _active_ui_init_path = path
        if load_result.get("status") in {"ok", "deferred", "skipped"}:
            _emit_stdout_diagnostic(
                "TELEGRAM_UI_STATE_INITIALIZED",
                {
                    "status": load_result.get("status"),
                    "path": path,
                    "session_count": len(_active_ui),
                },
            )
        return get_runtime_diagnostics()


def _ensure_initialized() -> None:
    path = _resolved_state_path()
    if not _active_ui_initialized or (_runtime_path_ready() and _active_ui_init_path != path):
        initialize_active_ui_state(force_reload=True)


def get_runtime_diagnostics(
    *,
    chat_id: Optional[int] = None,
    user_id: Optional[int] = None,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    with _active_ui_lock:
        result: Dict[str, Any] = {
            "initialized": _active_ui_initialized,
            "persistence_enabled": _persistence_enabled(),
            "runtime_path_ready": _runtime_path_ready(),
            "resolved_state_path": _resolved_state_path(),
            "load_result": dict(_last_load_result),
            "save_result": dict(_last_save_result),
            "pid": os.getpid(),
            "deployment_id": _deployment_identifier(),
        }
        if chat_id is not None and user_id is not None:
            key = normalize_session_key(chat_id, user_id, thread_id)
            entry = _active_ui.get(key) or {}
            in_memory_message_id = entry.get("message_id")
            # Independently read persisted message_id — do not copy from in-memory state.
            persisted_message_id: Optional[int] = None
            if _persistence_enabled() and _runtime_path_ready():
                try:
                    persisted_message_id = state_store.read_telegram_session_message_id(
                        chat_id=chat_id,
                        user_id=user_id,
                        thread_id=thread_id,
                    )
                except Exception:
                    persisted_message_id = None
            result.update(
                {
                    "session_key": key,
                    "session_key_fingerprint": session_key_fingerprint(chat_id, user_id, thread_id),
                    "active_message_id": in_memory_message_id,
                    "persisted_message_id": persisted_message_id,
                }
            )
        return result


def set_active_message(user_id: int, chat_id: int, message_id: int, thread_id: Optional[int] = None) -> None:
    """Record the active UI message for the chat/user/thread session."""
    global _last_save_result
    _ensure_initialized()
    with _active_ui_lock:
        key = normalize_session_key(chat_id, user_id, thread_id)
        now_ts = _now_ts()
        _active_ui[key] = {
            "message_id": int(message_id),
            "updated_ts": now_ts,
        }
        _prune_active_ui(now_ts)
        if not _persistence_enabled() or not _runtime_path_ready():
            return
        try:
            state_store.update_telegram_ui_state(
                lambda payload: _merge_session_update(payload, key, int(message_id), now_ts)
            )
            _last_save_result = {
                "status": "ok",
                "path": _resolved_state_path(),
                "session_count": len(_active_ui),
            }
        except Exception as exc:
            _last_save_result = {
                "status": "error",
                "error": str(exc),
                "path": _resolved_state_path(),
            }
            _log_ui_state_warning(
                "TELEGRAM_UI_STATE_SAVE_FAILED",
                "Failed to persist Telegram UI active-message state",
                _last_save_result,
            )


def get_active_message(user_id: int, chat_id: int, thread_id: Optional[int] = None) -> Optional[int]:
    """Return message_id for the active UI panel in this chat/user/thread session."""
    _ensure_initialized()
    with _active_ui_lock:
        key = normalize_session_key(chat_id, user_id, thread_id)
        entry = _active_ui.get(key)
        if entry is None:
            return None
        now_ts = _now_ts()
        if int(entry.get("updated_ts", 0)) < (now_ts - _ACTIVE_UI_RETENTION_SECONDS):
            _active_ui.pop(key, None)
            if _persistence_enabled() and _runtime_path_ready():
                try:
                    state_store.delete_telegram_ui_session(
                        chat_id=chat_id,
                        user_id=user_id,
                        thread_id=thread_id,
                    )
                except Exception as exc:
                    _log_ui_state_warning(
                        "TELEGRAM_UI_STATE_SAVE_FAILED",
                        "Failed to prune stale Telegram UI active-message state",
                        {"error": str(exc), "path": _resolved_state_path()},
                    )
            return None
        return int(entry.get("message_id"))


def clear_active_message(user_id: int, chat_id: int, thread_id: Optional[int] = None) -> Dict[str, Any]:
    """Forget active UI message for this chat/user/thread session.

    Correctness contract:
    1. Normalize the exact key.
    2. Remove from memory whether or not it currently exists there.
    3. Invoke exact persisted deletion regardless of in-memory presence.
    4. Verify the target no longer exists in persisted state.
    5. Preserve unrelated sessions.
    6. Return a structured result.
    7. Log failures safely.
    8. Never restore the stale message ID.

    A session existing only in persisted storage is still removable.
    """
    global _last_save_result
    _ensure_initialized()
    with _active_ui_lock:
        key = normalize_session_key(chat_id, user_id, thread_id)
        _active_ui.pop(key, None)

        if not _persistence_enabled() or not _runtime_path_ready():
            return {
                "status": "ok",
                "in_memory_removed": True,
                "persisted_delete_attempted": False,
                "persisted_absent": True,
                "reason": "persistence_disabled_or_runtime_path_unset",
            }

        try:
            delete_result = state_store.delete_telegram_ui_session(
                chat_id=chat_id,
                user_id=user_id,
                thread_id=thread_id,
            )
            if delete_result.error:
                _log_ui_state_warning(
                    "TELEGRAM_UI_STATE_CLEAR_FAILED",
                    "Persisted exact-session deletion failed",
                    {
                        "error": delete_result.error,
                        "target_key": str(delete_result.target_key),
                        "path": _resolved_state_path(),
                    },
                )
                _last_save_result = {
                    "status": "error",
                    "error": delete_result.error,
                    "path": _resolved_state_path(),
                }
                return {
                    "status": "error",
                    "in_memory_removed": True,
                    "persisted_delete_attempted": True,
                    "persisted_absent": None,
                    "error": delete_result.error,
                }

            verification = state_store.verify_telegram_session_absent(
                chat_id=chat_id,
                user_id=user_id,
                thread_id=thread_id,
            )
            persisted_absent = verification.get("absent", False)
            if not persisted_absent:
                _log_ui_state_warning(
                    "TELEGRAM_UI_STATE_CLEAR_RESIDUAL",
                    "Session still present in persisted state after delete",
                    {
                        "target_key": str(key),
                        "found_message_id": verification.get("found_message_id"),
                        "path": _resolved_state_path(),
                    },
                )

            _last_save_result = {
                "status": "ok",
                "path": _resolved_state_path(),
                "session_count": len(_active_ui),
            }
            return {
                "status": "ok",
                "in_memory_removed": True,
                "persisted_delete_attempted": True,
                "persisted_absent": persisted_absent,
                "session_existed_in_persistence": delete_result.session_existed,
                "final_persisted_session_count": delete_result.final_session_count,
            }
        except Exception as exc:
            _last_save_result = {
                "status": "error",
                "error": str(exc),
                "path": _resolved_state_path(),
            }
            _log_ui_state_warning(
                "TELEGRAM_UI_STATE_SAVE_FAILED",
                "Failed to persist Telegram UI active-message state",
                _last_save_result,
            )
            return {
                "status": "error",
                "in_memory_removed": True,
                "persisted_delete_attempted": True,
                "persisted_absent": None,
                "error": str(exc),
            }


def _merge_session_update(
    payload: Dict[str, Any],
    key: _SessionKey,
    message_id: int,
    updated_ts: int,
) -> Dict[str, Any]:
    sessions = [item for item in list(payload.get("sessions", [])) if isinstance(item, dict)]
    updated = False
    for item in sessions:
        if _session_key_from_item(item) == key:
            item["message_id"] = int(message_id)
            item["updated_ts"] = int(updated_ts)
            updated = True
            break
    if not updated:
        sessions.append(
            {
                "chat_id": key[0],
                "user_id": key[1],
                "thread_id": key[2],
                "message_id": int(message_id),
                "updated_ts": int(updated_ts),
            }
        )
    payload["version"] = _ACTIVE_UI_VERSION
    payload["retention_seconds"] = _ACTIVE_UI_RETENTION_SECONDS
    payload["max_sessions"] = _ACTIVE_UI_MAX_SESSIONS
    payload["sessions"] = sessions
    return payload


def _merge_session_clear(payload: Dict[str, Any], key: _SessionKey) -> Dict[str, Any]:
    payload["sessions"] = [
        item
        for item in list(payload.get("sessions", []))
        if isinstance(item, dict)
        and _session_key_from_item(item) != key
    ]
    payload["version"] = _ACTIVE_UI_VERSION
    payload["retention_seconds"] = _ACTIVE_UI_RETENTION_SECONDS
    payload["max_sessions"] = _ACTIVE_UI_MAX_SESSIONS
    return payload


def _session_key_from_item(item: Dict[str, Any]) -> Optional[_SessionKey]:
    try:
        return normalize_session_key(
            int(item.get("chat_id")),
            int(item.get("user_id")),
            int(item.get("thread_id")) if item.get("thread_id") is not None else None,
        )
    except Exception:
        return None


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
