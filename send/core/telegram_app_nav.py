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
- HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md

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
from core.owner_knowledge import (
    public_knowledge_key,
    render_contextual_knowledge,
    render_operational_page,
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
ACT_BACK = "BACK"
ACT_INFO_PREFIX = "INFO:"

_SUPPORTED_APP_ACTIONS: frozenset[str] = frozenset({
    ACT_HOME,
    ACT_STATUS,
    ACT_HELP,
    ACT_ADMIN,
})


def make_info_action(knowledge_key: str) -> str:
    return f"{ACT_INFO_PREFIX}{str(knowledge_key or '').strip().lower()}"


def _is_supported_app_action(action: str) -> bool:
    if action in _SUPPORTED_APP_ACTIONS:
        return True
    if isinstance(action, str) and action.startswith(ACT_INFO_PREFIX):
        return public_knowledge_key(action[len(ACT_INFO_PREFIX):])
    return False


def is_dispatchable_app_action(action: str) -> bool:
    """Return whether an APP callback action has a canonical dispatcher path."""
    return action == ACT_BACK or _is_supported_app_action(action)


def make_callback(action: str, generation: Optional[int] = None) -> str:
    if generation is not None:
        try:
            gen = int(generation)
        except Exception:
            gen = 0
        if gen > 0:
            return f"{APP_NAV_PREFIX}{gen}:{action}"
    return f"{APP_NAV_PREFIX}{action}"


def parse_app_callback(callback_data: str) -> Optional[Dict[str, Any]]:
    """Return parsed APP callback metadata or None when the payload is not APP:."""
    if not isinstance(callback_data, str):
        return None
    if not callback_data.startswith(APP_NAV_PREFIX):
        return None
    payload = callback_data[len(APP_NAV_PREFIX):].strip()
    if not payload:
        return None
    generation: Optional[int] = None
    action = payload
    maybe_generation, sep, remainder = payload.partition(":")
    if sep and maybe_generation.isdigit():
        generation = int(maybe_generation)
        action = remainder.strip()
    if not action:
        return None
    return {"action": action, "generation": generation}


def parse_app_action(callback_data: str) -> Optional[str]:
    """Return the action key if callback_data is an APP: callback, else None."""
    parsed = parse_app_callback(callback_data)
    return None if parsed is None else parsed.get("action")


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

# ---------------------------------------------------------------------------
# Per-session /start reset idempotency guard
#
# Prevents two rapid concurrent /start commands for the same session from
# creating uncontrolled duplicate anchors.
#
# Structure: { session_key: {"generation": int, "in_progress": bool, "ts": float} }
# Guards are short-lived (RESET_GUARD_TTL_SEC) and scoped per session.
# USER and ADMIN sessions use different session keys → independent guards.
# ---------------------------------------------------------------------------
_RESET_GUARDS: Dict[_SessionKey, Dict[str, Any]] = {}
_RESET_GUARD_LOCK = threading.Lock()
_RESET_GUARD_TTL_SEC = 30.0  # Guards expire after 30 s to prevent abandoned locks.

# ---------------------------------------------------------------------------
# Per-session bounded navigation history
#
# Models the "Back" contract for APP: page navigation.
#
# Design decisions:
# - History is keyed by (chat_id, user_id, thread_id) — same isolation as active UI.
# - Depth is bounded to _NAV_HISTORY_MAX_DEPTH to prevent unbounded memory growth
#   and loops (a page cannot appear twice consecutively in the stack).
# - History is in-memory only; on restart or state-loss, Back safely falls back to Home.
# - clear_nav_history() is called on /start hard reset (ACT_HOME clears implicitly).
# - Concurrency-safe via _nav_history_lock.
#
# APP: pages are currently one level deep (Status, Help, Admin from Home),
# so Back always resolves to Home. The bounded history model is implemented
# for correctness and future extension.
# ---------------------------------------------------------------------------

_NAV_HISTORY_MAX_DEPTH: int = 5  # Bounded to prevent loops and unbounded growth

_nav_history: Dict[_SessionKey, List[str]] = {}
_nav_history_lock = threading.Lock()

# { (chat_id, user_id, thread_id): {"current_action": str, "generation": int} }
_nav_session_state: Dict[_SessionKey, Dict[str, Any]] = {}
_nav_session_state_lock = threading.Lock()


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


# ---------------------------------------------------------------------------
# /start hard-reset idempotency guard helpers
# ---------------------------------------------------------------------------

def _prune_reset_guards(now: float) -> None:
    """Remove expired guards. Caller must hold _RESET_GUARD_LOCK."""
    expired = [k for k, g in _RESET_GUARDS.items() if now - g.get("ts", 0.0) > _RESET_GUARD_TTL_SEC]
    for k in expired:
        _RESET_GUARDS.pop(k, None)


def acquire_start_reset_guard(chat_id: int, user_id: int, thread_id: Optional[int] = None) -> Dict[str, Any]:
    """Acquire a per-session /start reset guard.

    Returns a result dict:
        acquired:    True  — guard acquired; caller must call release_start_reset_guard after.
        acquired:    False — a concurrent /start is already in progress for this session.
        generation:  monotonically increasing counter for this session.

    Guards are short-lived (RESET_GUARD_TTL_SEC) and expire automatically.
    USER and ADMIN session keys are always distinct → no cross-account coupling.
    """
    key = normalize_session_key(chat_id, user_id, thread_id)
    now = time.monotonic()
    with _RESET_GUARD_LOCK:
        _prune_reset_guards(now)
        guard = _RESET_GUARDS.get(key)
        if guard is not None and guard.get("in_progress") and (now - guard.get("ts", 0.0)) < _RESET_GUARD_TTL_SEC:
            return {
                "acquired": False,
                "generation": guard.get("generation", 0),
                "reason": "concurrent_reset_in_progress",
            }
        current_gen = guard.get("generation", 0) if guard is not None else 0
        new_gen = current_gen + 1
        _RESET_GUARDS[key] = {"in_progress": True, "generation": new_gen, "ts": now}
        return {"acquired": True, "generation": new_gen}


def release_start_reset_guard(chat_id: int, user_id: int, thread_id: Optional[int] = None) -> None:
    """Mark the per-session /start reset guard as complete (no longer in progress)."""
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _RESET_GUARD_LOCK:
        guard = _RESET_GUARDS.get(key)
        if guard is not None:
            guard["in_progress"] = False


# ---------------------------------------------------------------------------
# Navigation history helpers — bounded Back navigation
# ---------------------------------------------------------------------------

def push_nav_action(
    user_id: int,
    *,
    chat_id: int,
    action: str,
    thread_id: Optional[int] = None,
) -> None:
    """Push a page action to the bounded navigation history for this session.

    Consecutive duplicate entries are ignored to prevent trivial loops.
    History is bounded to _NAV_HISTORY_MAX_DEPTH entries.
    """
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_history_lock:
        stack: List[str] = list(_nav_history.get(key, []))
        if stack and stack[-1] == action:
            return  # Don't record same page twice in a row
        if len(stack) >= _NAV_HISTORY_MAX_DEPTH:
            stack = stack[-(_NAV_HISTORY_MAX_DEPTH - 1):]
        stack.append(action)
        _nav_history[key] = stack


def pop_nav_action(
    user_id: int,
    *,
    chat_id: int,
    thread_id: Optional[int] = None,
) -> Optional[str]:
    """Pop and return the most recent page action from navigation history.

    Returns None if history is empty (safe restart/state-loss fallback).
    """
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_history_lock:
        stack: List[str] = list(_nav_history.get(key, []))
        if not stack:
            return None
        action = stack.pop()
        _nav_history[key] = stack
        return action


def nav_can_go_back(
    user_id: int,
    *,
    chat_id: int,
    thread_id: Optional[int] = None,
) -> bool:
    """Return True if there is at least one previous page in the navigation history."""
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_history_lock:
        return bool(_nav_history.get(key))


def clear_nav_history(
    user_id: int,
    *,
    chat_id: int,
    thread_id: Optional[int] = None,
) -> None:
    """Clear navigation history for a session.

    Called on /start hard reset so Back cannot navigate into stale pre-reset history.
    """
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_history_lock:
        _nav_history.pop(key, None)


def begin_navigation_generation(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
) -> int:
    """Start a new APP navigation generation and reset page/history state."""
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_session_state_lock:
        previous_generation = int((_nav_session_state.get(key) or {}).get("generation", 0))
        generation = previous_generation + 1
        _nav_session_state[key] = {
            "generation": generation,
            "current_action": ACT_HOME,
        }
    clear_nav_history(user_id, chat_id=chat_id, thread_id=thread_id)
    return generation


def get_navigation_generation(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
) -> int:
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_session_state_lock:
        return int((_nav_session_state.get(key) or {}).get("generation", 0))


def get_current_nav_action(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
) -> Optional[str]:
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_session_state_lock:
        action = (_nav_session_state.get(key) or {}).get("current_action")
        return action if action in _SUPPORTED_APP_ACTIONS else None


def set_current_nav_action(
    chat_id: int,
    user_id: int,
    action: str,
    thread_id: Optional[int] = None,
) -> None:
    if action not in _SUPPORTED_APP_ACTIONS:
        return
    key = normalize_session_key(chat_id, user_id, thread_id)
    with _nav_session_state_lock:
        entry = dict(_nav_session_state.get(key) or {})
        entry["generation"] = int(entry.get("generation", 0))
        entry["current_action"] = action
        _nav_session_state[key] = entry


def callback_generation_is_current(
    *,
    chat_id: int,
    user_id: int,
    callback_generation: Optional[int],
    thread_id: Optional[int] = None,
) -> bool:
    if callback_generation is None:
        return True
    return int(callback_generation) == get_navigation_generation(chat_id, user_id, thread_id)


def record_app_navigation(
    *,
    chat_id: int,
    user_id: int,
    action: str,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Record a real APP page transition and return render metadata."""
    if action not in _SUPPORTED_APP_ACTIONS:
        action = ACT_HOME
    current = get_current_nav_action(chat_id, user_id, thread_id)
    if action == ACT_HOME:
        clear_nav_history(user_id, chat_id=chat_id, thread_id=thread_id)
        set_current_nav_action(chat_id, user_id, ACT_HOME, thread_id)
        return {
            "action": ACT_HOME,
            "include_back": False,
            "generation": get_navigation_generation(chat_id, user_id, thread_id),
            "previous_action": current,
        }
    if current in _SUPPORTED_APP_ACTIONS and current != action:
        push_nav_action(user_id, chat_id=chat_id, action=current, thread_id=thread_id)
    set_current_nav_action(chat_id, user_id, action, thread_id)
    return {
        "action": action,
        "include_back": nav_can_go_back(user_id, chat_id=chat_id, thread_id=thread_id),
        "generation": get_navigation_generation(chat_id, user_id, thread_id),
        "previous_action": current,
    }


def resolve_back_navigation(
    *,
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Pop and validate the previous APP page for a Back action."""
    current = get_current_nav_action(chat_id, user_id, thread_id)
    parent = pop_nav_action(user_id, chat_id=chat_id, thread_id=thread_id)
    if parent not in _SUPPORTED_APP_ACTIONS or parent == current:
        parent = ACT_HOME
    if parent == ACT_HOME:
        clear_nav_history(user_id, chat_id=chat_id, thread_id=thread_id)
    set_current_nav_action(chat_id, user_id, parent, thread_id)
    return {
        "action": parent,
        "include_back": parent != ACT_HOME and nav_can_go_back(user_id, chat_id=chat_id, thread_id=thread_id),
        "generation": get_navigation_generation(chat_id, user_id, thread_id),
        "previous_action": current,
    }


# ---------------------------------------------------------------------------
# /start hard-reset: read-then-clear session state
# ---------------------------------------------------------------------------

def prepare_start_hard_reset(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Read the previous active message ID and clear the session state for /start.

    This is the first half of the /start hard-reset sequence:
    1. Normalize the session key.
    2. Read the previously tracked message ID.
    3. Clear memory and persistence (best-effort).

    Returns:
        previous_message_id:  int or None — the old anchor before clearing
        session_key:          normalized session key tuple (serializable as list)
        session_fingerprint:  short hex fingerprint for logging
        clear_result:         result from clear_active_message

    Never raises.  Failures in persistence are captured and returned.
    """
    _ensure_initialized()
    key = normalize_session_key(chat_id, user_id, thread_id)
    # Read previous ID before clearing.
    previous_message_id: Optional[int] = None
    with _active_ui_lock:
        entry = _active_ui.get(key)
        if entry is not None:
            try:
                previous_message_id = int(entry["message_id"])
            except (KeyError, TypeError, ValueError):
                previous_message_id = None

    # Also check persisted state for the previous ID if not in memory.
    if previous_message_id is None:
        try:
            nav_diag = get_runtime_diagnostics(chat_id=chat_id, user_id=user_id, thread_id=thread_id)
            persisted_id = nav_diag.get("persisted_message_id")
            if persisted_id is not None:
                previous_message_id = int(persisted_id)
        except Exception:
            pass

    # Clear the session (best-effort).
    try:
        clear_result = clear_active_message(user_id=user_id, chat_id=chat_id, thread_id=thread_id)
    except Exception as exc:
        clear_result = {"status": "error", "error": str(exc)}

    # Clear navigation history so Back cannot navigate into stale pre-reset history.
    try:
        clear_nav_history(user_id=user_id, chat_id=chat_id, thread_id=thread_id)
    except Exception:
        pass

    return {
        "previous_message_id": previous_message_id,
        "session_key": list(key),
        "session_fingerprint": session_key_fingerprint(chat_id, user_id, thread_id),
        "clear_result": clear_result,
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

def _btn(text: str, action: str, generation: Optional[int] = None) -> Dict[str, str]:
    return {"text": text, "callback_data": make_callback(action, generation=generation)}


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
    shadow_mode: Optional[bool] = None,
    generation: Optional[int] = None,
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
    if shadow_mode is True:
        mode_note = (
            "Mode: SHADOW — reported runtime/configuration evidence is ON; "
            "no live signal delivery or broker execution is implied."
        )
    elif shadow_mode is False:
        mode_note = "Mode: Shadow mode is reported/configured as disabled."
    else:
        mode_note = "Mode: UNKNOWN — shadow-mode evidence was not reported."

    if primary_role == ROLE_OWNER:
        current_state = (
            f"{greeting}\n\n"
            f"You are connected as *{role_label}* — the supreme governance authority.\n\n"
            "You have full access to the admin control surface, including all governance, "
            f"operational, research and audit surfaces.\n\n{mode_note}"
        )
        markup = _kb([
            [_btn("⚙️ Admin Control Surface", ACT_ADMIN, generation)],
            [_btn("📊 System Status", ACT_STATUS, generation)],
            [
                _btn("ℹ️ What is BinaryBot?", make_info_action("home"), generation),
                _btn("❓ Help", ACT_HELP, generation),
            ],
        ])

    elif primary_role in ADMIN_TIER_ROLES:
        current_state = (
            f"{greeting}\n\n"
            f"You are connected as *{role_label}*.\n\n"
            "Your access is configured for the designated admin control channel. "
            "Navigate to the admin control channel to access your control surface.\n\n"
            f"From here you can check system status.\n\n{mode_note}"
        )
        markup = _kb([
            [_btn("📊 System Status", ACT_STATUS, generation)],
            [
                _btn("ℹ️ What is BinaryBot?", make_info_action("home"), generation),
                _btn("❓ Help", ACT_HELP, generation),
            ],
        ])

    else:
        # USER role: platform introduction
        current_state = (
            f"{greeting}\n\n"
            "Welcome to *BinaryBot* — an automated trading signal platform.\n\n"
            "This bot delivers trading signals to configured trading channels. "
            f"You can check the system status or view the command list below.\n\n{mode_note}"
        )
        markup = _kb([
            [_btn("📊 System Status", ACT_STATUS, generation)],
            [
                _btn("ℹ️ What is BinaryBot?", make_info_action("home"), generation),
                _btn("❓ Help", ACT_HELP, generation),
            ],
        ])

    text = render_operational_page("home", current_state, title="🤖 *BinaryBot*")
    return text, markup


def render_status_page(
    snapshot: Dict,
    *,
    include_back: bool = False,
    generation: Optional[int] = None,
) -> Tuple[str, Dict]:
    """
    Public system status page — consistent with the canonical render_status_text fields.

    Source: TELEGRAM_UX_v2.0.0.md §15.2 (Admin UX exposes operational state);
            Public status is canonical via /status command.

    This page is accessible to all roles and provides a read-only summary.
    The field set mirrors the original render_status_text to preserve information parity.
    """
    unavailable = "UNKNOWN (not reported)"
    overall = snapshot.get("overall_state", unavailable)
    phase = snapshot.get("runtime_phase", unavailable)
    health = snapshot.get("runtime_message", unavailable)
    recovery = snapshot.get("recovery_state", unavailable)
    market = snapshot.get("market_data_state", unavailable)
    telegram = snapshot.get("telegram_state", unavailable)
    fsm = snapshot.get("fsm_state", unavailable)
    shadow = snapshot.get("shadow_mode", unavailable)
    broker = snapshot.get("broker_state", unavailable)
    market_provider = snapshot.get("market_data_provider", unavailable)
    market_symbol = snapshot.get("market_data_symbol", unavailable)
    market_age = snapshot.get("market_data_age_seconds")
    freshness_limit = snapshot.get("market_data_freshness_limit_seconds")
    candle_counts = snapshot.get("market_data_candle_counts")
    minimum_candles = snapshot.get("market_data_minimum_candles")
    history_ready = snapshot.get("market_data_history_ready")

    current_state = (
        f"Overall: {overall}\n"
        f"Runtime phase: {phase}\n"
        f"Health: {health}\n"
        f"Recovery: {recovery}\n"
        f"Market data: {market}\n"
        f"Market provider: {market_provider}\n"
        f"Market symbol: {market_symbol}\n"
        f"Telegram: {telegram}\n"
        f"FSM: {fsm}\n"
        f"Shadow mode: {shadow}\n"
        f"Broker execution: {broker}"
    )
    if isinstance(market_age, int) and isinstance(freshness_limit, int):
        current_state += (
            f"\nLatest price age: {market_age} seconds "
            f"(maximum accepted: {freshness_limit})"
        )
    if isinstance(candle_counts, dict) and isinstance(minimum_candles, int):
        m1_count = candle_counts.get("M1")
        m5_count = candle_counts.get("M5")
        if isinstance(m1_count, int) and isinstance(m5_count, int):
            current_state += (
                f"\nReal history: M1 {m1_count}/{minimum_candles}; "
                f"M5 {m5_count}/{minimum_candles}"
            )
    if isinstance(history_ready, bool):
        current_state += (
            "\nStrategy history: READY"
            if history_ready
            else "\nStrategy history: COLLECTING — decisions remain blocked"
        )
    note = snapshot.get("market_data_note")
    if isinstance(note, str) and note.strip():
        current_state += f"\n\nMarket note: {note.strip()}"

    text = render_operational_page("status", current_state, title="📊 *System Status*")

    rows: List[List[Dict[str, str]]] = [[
        _btn("🔄 Refresh", ACT_STATUS, generation),
        _btn("ℹ️ What is this?", make_info_action("status"), generation),
    ]]
    if include_back:
        rows.append([
            _btn("⬅️ Back", ACT_BACK, generation),
            _btn("🏠 Home", ACT_HOME, generation),
        ])
    else:
        rows.append([_btn("🏠 Home", ACT_HOME, generation)])
    markup = _kb(rows)
    return text, markup


def render_help_page(
    primary_role: str,
    *,
    include_back: bool = False,
    generation: Optional[int] = None,
) -> Tuple[str, Dict]:
    """
    Role-scoped help page — shows commands appropriate for the user's role.

    Source: TELEGRAM_UX_v2.0.0.md §17 (admin command families; role-scoped availability).

    Design decision: Public commands are listed for all roles. Admin commands are
    mentioned only for admin-tier users and only as navigation hints (they require
    the admin control channel, not this button).
    """
    is_admin = primary_role in ADMIN_TIER_ROLES

    if is_admin:
        current_state = (
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
        current_state = (
            "*Available commands:*\n"
            "/start — Show the welcome page\n"
            "/status — System status\n"
            "/help — This help page\n\n"
            "BinaryBot delivers trading signals to configured channels. "
            "You will receive signals automatically when they are generated."
        )

    text = render_operational_page("help", current_state, title="❓ *Help — BinaryBot*")

    rows: List[List[Dict[str, str]]] = [[
        _btn("📊 System Status", ACT_STATUS, generation),
        _btn("ℹ️ What is this?", make_info_action("help"), generation),
    ]]
    if include_back:
        rows.append([
            _btn("⬅️ Back", ACT_BACK, generation),
            _btn("🏠 Home", ACT_HOME, generation),
        ])
    else:
        rows.append([_btn("🏠 Home", ACT_HOME, generation)])
    markup = _kb(rows)
    return text, markup


def _render_app_page(
    action: str,
    *,
    user_id: int,
    primary_role: str,
    first_name: str = "",
    shadow_mode: Optional[bool] = None,
    status_snapshot: Optional[Dict] = None,
    include_back: bool = False,
    generation: Optional[int] = None,
) -> Tuple[str, Dict]:
    if isinstance(action, str) and action.startswith(ACT_INFO_PREFIX):
        knowledge_key = action[len(ACT_INFO_PREFIX):]
        if public_knowledge_key(knowledge_key):
            rows: List[List[Dict[str, str]]] = []
            if include_back:
                rows.append([
                    _btn("⬅️ Back", ACT_BACK, generation),
                    _btn("🏠 Home", ACT_HOME, generation),
                ])
            else:
                rows.append([_btn("🏠 Home", ACT_HOME, generation)])
            return render_contextual_knowledge(knowledge_key), _kb(rows)
    if action == ACT_HOME:
        return render_welcome_page(
            user_id,
            primary_role,
            first_name=first_name,
            shadow_mode=shadow_mode,
            generation=generation,
        )
    if action == ACT_STATUS:
        snap = status_snapshot if status_snapshot is not None else {}
        return render_status_page(snap, include_back=include_back, generation=generation)
    if action == ACT_HELP:
        return render_help_page(primary_role, include_back=include_back, generation=generation)
    if action == ACT_ADMIN:
        if primary_role == ROLE_OWNER:
            text = (
                "⚙️ *Admin Control Surface*\n\n"
                "Use /admin to access the full role-scoped admin tree, or "
                "navigate directly using the admin control channel.\n\n"
                "Quick actions are also available via slash commands:\n"
                "/engine — Engine status\n"
                "/debug — Decision snapshot\n"
                "/roles — Configured roles"
            )
        else:
            text = (
                "⚙️ *Admin Control Surface*\n\n"
                "The admin control surface is available in the configured admin control channel. "
                "Please navigate there to access your role-scoped controls."
            )
        rows: List[List[Dict[str, str]]] = []
        if include_back:
            rows.append([
                _btn("⬅️ Back", ACT_BACK, generation),
                _btn("🏠 Home", ACT_HOME, generation),
            ])
        else:
            rows.append([_btn("🏠 Home", ACT_HOME, generation)])
        return text, _kb(rows)
    return render_welcome_page(
        user_id,
        primary_role,
        first_name=first_name,
        shadow_mode=shadow_mode,
        generation=generation,
    )


# ---------------------------------------------------------------------------
# Application callback dispatcher
# ---------------------------------------------------------------------------

def handle_app_action(
    action: str,
    user_id: int,
    primary_role: str,
    first_name: str = "",
    shadow_mode: Optional[bool] = None,
    status_snapshot: Optional[Dict] = None,
    chat_id: Optional[int] = None,
    thread_id: Optional[int] = None,
    callback_generation: Optional[int] = None,
) -> Tuple[str, Dict]:
    """
    Dispatch an APP: callback action to the appropriate page renderer.

    Returns (text, reply_markup).

    All actions produce a complete, navigable page. No dead ends.

    ACT_BACK pops the navigation history and renders the parent page.
    On empty history or restart/state-loss, Back falls back to Home safely.
    """
    resolved_chat_id = chat_id if chat_id is not None else user_id
    generation = get_navigation_generation(resolved_chat_id, user_id, thread_id) if chat_id is not None else None

    if (
        chat_id is not None
        and callback_generation is not None
        and not callback_generation_is_current(
            chat_id=resolved_chat_id,
            user_id=user_id,
            callback_generation=callback_generation,
            thread_id=thread_id,
        )
    ):
        return _render_app_page(
            ACT_HOME,
            user_id=user_id,
            primary_role=primary_role,
            first_name=first_name,
            shadow_mode=shadow_mode,
            include_back=False,
            generation=generation,
        )

    if action == ACT_BACK:
        meta = resolve_back_navigation(chat_id=resolved_chat_id, user_id=user_id, thread_id=thread_id)
        return _render_app_page(
            meta["action"],
            user_id=user_id,
            primary_role=primary_role,
            first_name=first_name,
            shadow_mode=shadow_mode,
            status_snapshot=status_snapshot,
            include_back=bool(meta["include_back"]),
            generation=meta["generation"],
        )

    if chat_id is not None and _is_supported_app_action(action):
        meta = record_app_navigation(
            chat_id=resolved_chat_id,
            user_id=user_id,
            action=action,
            thread_id=thread_id,
        )
        include_back = bool(meta["include_back"])
        generation = meta["generation"]
    else:
        include_back = False

    return _render_app_page(
        action if _is_supported_app_action(action) else ACT_HOME,
        user_id=user_id,
        primary_role=primary_role,
        first_name=first_name,
        shadow_mode=shadow_mode,
        status_snapshot=status_snapshot,
        include_back=include_back,
        generation=generation,
    )
