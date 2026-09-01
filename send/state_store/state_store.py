# /opt/binarybot/state_store/state_store.py
# BinaryBot — Canonical runtime state store

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from core import storage
from core.storage import save_json_atomic, with_lock


class StateStoreError(RuntimeError):
    pass


class StateValidationError(StateStoreError):
    pass


class StateConflictError(StateStoreError):
    pass


_MISSING = object()

FSM_STATE_VERSION = "1.1.0"
RESTART_GUARD_VERSION = "1.1.0"
TELEGRAM_UI_STATE_VERSION = "1.0.0"


def runtime_root() -> str:
    return storage.base_dir()


def config_dir() -> str:
    return storage.root_path("config")


def state_dir() -> str:
    return storage.root_path("state")


def outcomes_dir() -> str:
    return storage.root_path("outcomes")


def observability_dir() -> str:
    return storage.root_path("observability")


def snapshots_dir() -> str:
    return storage.root_path("snapshots")


FOCUS_STATE_PATH = storage.state_path("focus_state.json")
DIST_STATE_PATH = storage.state_path("dist_state.json")
RESTART_GUARD_PATH = storage.state_path("restart_guard.json")
ACTIVE_SYMBOLS_PATH = storage.config_path("active_symbols.json")
SETTINGS_PATH = storage.config_path("admin_settings.json")
TELEGRAM_UI_STATE_PATH = storage.state_path("telegram_ui_state.json")


def _now_ts() -> int:
    return int(time.time())


def _legacy_root_path(name: str) -> str:
    return storage.root_path(name)


def _telegram_ui_state_path() -> str:
    return storage.state_path("telegram_ui_state.json")


def telegram_ui_state_path() -> str:
    return _telegram_ui_state_path()


def _safe_int(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except Exception as exc:
        raise StateValidationError(f"{field_name} must be an integer or null") from exc


def _safe_float(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception as exc:
        raise StateValidationError(f"{field_name} must be a number or null") from exc


def _safe_str(value: Any, field_name: str, *, allow_none: bool = True) -> Optional[str]:
    if value is None and allow_none:
        return None
    if not isinstance(value, str):
        raise StateValidationError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized and not allow_none:
        raise StateValidationError(f"{field_name} must be a non-empty string")
    return normalized or None


def _json_equal(left: Any, right: Any) -> bool:
    return json.dumps(left, sort_keys=True, ensure_ascii=False) == json.dumps(right, sort_keys=True, ensure_ascii=False)


def _read_json_file(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return _MISSING
    except json.JSONDecodeError as exc:
        raise StateValidationError(f"Invalid JSON in {path}: {exc.msg}") from exc
    except OSError as exc:
        raise StateValidationError(f"Unable to read {path}: {exc}") from exc


def _emit_warning(code: str, message: str, context: Dict[str, Any]) -> None:
    try:
        from core import observability_logger

        observability_logger.log_warning(
            warn_type=code,
            message=message,
            context=context,
            source={"module": "state_store", "function": "_emit_warning"},
        )
    except Exception:
        pass


@dataclass(frozen=True)
class JsonArtifact:
    name: str
    canonical_path: str
    legacy_paths: tuple[str, ...]
    lock_name: str
    default_factory: Callable[[], Dict[str, Any]]
    validator: Callable[[Any], Dict[str, Any]]
    required: bool = False


def default_fsm_state() -> Dict[str, Any]:
    return {
        "version": FSM_STATE_VERSION,
        "mode": "WIDE_SCAN",
        "watchlist": [],
        "per_symbol": {},
        "last_updated_ts": _now_ts(),
    }


def default_dist_state() -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "last_reset_london_date": None,
        "tier_state": {
            "FREE": "ACTIVE",
            "BASIC": "ACTIVE",
            "PRO": "ACTIVE",
            "ELITE": "ACTIVE",
        },
        "open_signals_today": {
            "FREE": 0,
            "BASIC": 0,
            "PRO": 0,
            "ELITE": 0,
        },
        "dedup": {},
        "last_updated_ts": _now_ts(),
    }


def default_restart_guard_state() -> Dict[str, Any]:
    now_ts = _now_ts()
    return {
        "version": RESTART_GUARD_VERSION,
        "window_seconds": 60,
        "max_restarts": 3,
        "starts": [],
        "last_shutdown": {"kind": "unknown", "ts": None},
        "last_start_ts": None,
        "last_updated_ts": now_ts,
    }


def default_settings() -> Dict[str, Any]:
    return {
        "buffer_mode": "MEDIUM",
        "engine_tick_interval": 2,
        "feature_flags": {},
        "last_updated_ts": _now_ts(),
    }


def default_active_symbols() -> Dict[str, Any]:
    return {
        "symbols": [],
        "last_updated_ts": _now_ts(),
    }


def default_telegram_ui_state() -> Dict[str, Any]:
    return {
        "version": TELEGRAM_UI_STATE_VERSION,
        "retention_seconds": 7 * 24 * 60 * 60,
        "max_sessions": 1000,
        "sessions": [],
        "last_updated_ts": _now_ts(),
    }


def _normalize_symbol_state(symbol: str, raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise StateValidationError(f"per_symbol[{symbol}] must be an object")

    normalized = dict(raw)
    state = str(raw.get("state") or "IDLE").strip().upper()
    if state not in {"IDLE", "WATCHLIST", "CONFIRMED", "LIVE_SENT", "COOLDOWN"}:
        raise StateValidationError(f"per_symbol[{symbol}].state is unsupported: {state}")

    normalized["state"] = state
    normalized["current_signal_id"] = _safe_str(raw.get("current_signal_id"), f"per_symbol[{symbol}].current_signal_id")
    normalized["last_pre_candle_ts"] = _safe_int(raw.get("last_pre_candle_ts"), f"per_symbol[{symbol}].last_pre_candle_ts")
    normalized["last_confirm_candle_ts"] = _safe_int(raw.get("last_confirm_candle_ts"), f"per_symbol[{symbol}].last_confirm_candle_ts")
    normalized["last_open_candle_ts"] = _safe_int(raw.get("last_open_candle_ts"), f"per_symbol[{symbol}].last_open_candle_ts")
    normalized["cooldown_until_ts"] = _safe_int(raw.get("cooldown_until_ts"), f"per_symbol[{symbol}].cooldown_until_ts")
    normalized["focus_enter_ts"] = _safe_int(raw.get("focus_enter_ts"), f"per_symbol[{symbol}].focus_enter_ts")
    normalized["focus_ttl_seconds"] = _safe_int(raw.get("focus_ttl_seconds"), f"per_symbol[{symbol}].focus_ttl_seconds")
    normalized["last_exit_reason"] = _safe_str(raw.get("last_exit_reason"), f"per_symbol[{symbol}].last_exit_reason")
    normalized["last_transition_ts"] = _safe_int(raw.get("last_transition_ts"), f"per_symbol[{symbol}].last_transition_ts")
    normalized["replacement_score"] = _safe_float(raw.get("replacement_score"), f"per_symbol[{symbol}].replacement_score")
    normalized["replacement_score_ts"] = _safe_int(raw.get("replacement_score_ts"), f"per_symbol[{symbol}].replacement_score_ts")
    return normalized


def validate_fsm_state(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise StateValidationError("FSM state must be an object")

    normalized = dict(raw)
    watchlist_raw = raw.get("watchlist", [])
    if not isinstance(watchlist_raw, list):
        raise StateValidationError("FSM watchlist must be a list")

    watchlist: list[str] = []
    for item in watchlist_raw:
        if not isinstance(item, str) or not item.strip():
            raise StateValidationError("FSM watchlist entries must be non-empty strings")
        value = item.strip()
        if value not in watchlist:
            watchlist.append(value)

    if len(watchlist) > 2:
        raise StateValidationError("FSM watchlist exceeds canonical capacity of 2")

    per_symbol_raw = raw.get("per_symbol", {})
    if not isinstance(per_symbol_raw, dict):
        raise StateValidationError("FSM per_symbol must be an object")

    per_symbol = {
        str(symbol): _normalize_symbol_state(str(symbol), payload)
        for symbol, payload in per_symbol_raw.items()
    }

    for symbol in watchlist:
        state = per_symbol.setdefault(symbol, _normalize_symbol_state(symbol, {}))
        if state["state"] == "IDLE":
            state["state"] = "WATCHLIST"

    normalized["version"] = str(raw.get("version") or FSM_STATE_VERSION)
    normalized["watchlist"] = watchlist
    normalized["per_symbol"] = per_symbol
    normalized["mode"] = "FOCUS_MODE" if watchlist else "WIDE_SCAN"
    normalized["last_updated_ts"] = _safe_int(raw.get("last_updated_ts"), "FSM.last_updated_ts") or _now_ts()
    return normalized


def validate_dist_state(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise StateValidationError("Distribution state must be an object")

    normalized = dict(default_dist_state())
    normalized.update(raw)

    tier_state = normalized.get("tier_state")
    if not isinstance(tier_state, dict):
        raise StateValidationError("Distribution tier_state must be an object")
    open_signals_today = normalized.get("open_signals_today")
    if not isinstance(open_signals_today, dict):
        raise StateValidationError("Distribution open_signals_today must be an object")
    dedup = normalized.get("dedup")
    if not isinstance(dedup, dict):
        raise StateValidationError("Distribution dedup must be an object")

    for tier in ("FREE", "BASIC", "PRO", "ELITE"):
        state = str(tier_state.get(tier) or "ACTIVE").upper()
        if state not in {"ACTIVE", "SILENT", "DISABLED"}:
            raise StateValidationError(f"Distribution tier_state[{tier}] is unsupported: {state}")
        tier_state[tier] = state
        open_signals_today[tier] = _safe_int(open_signals_today.get(tier), f"Distribution open_signals_today[{tier}]") or 0

    normalized["version"] = str(normalized.get("version") or "1.0.0")
    normalized["last_reset_london_date"] = _safe_str(normalized.get("last_reset_london_date"), "Distribution.last_reset_london_date")
    normalized["tier_state"] = tier_state
    normalized["open_signals_today"] = open_signals_today
    normalized["dedup"] = dedup
    normalized["last_updated_ts"] = _safe_int(normalized.get("last_updated_ts"), "Distribution.last_updated_ts") or _now_ts()
    return normalized


def validate_restart_guard_state(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise StateValidationError("Restart guard state must be an object")

    normalized = dict(default_restart_guard_state())
    normalized.update(raw)

    starts_raw = normalized.get("starts", [])
    if not isinstance(starts_raw, list):
        raise StateValidationError("Restart guard starts must be a list")
    starts = [_safe_int(item, "Restart guard starts[]") for item in starts_raw]
    normalized["starts"] = [item for item in starts if item is not None]

    last_shutdown = normalized.get("last_shutdown", {})
    if last_shutdown is None:
        last_shutdown = {}
    if not isinstance(last_shutdown, dict):
        raise StateValidationError("Restart guard last_shutdown must be an object")

    kind = str(last_shutdown.get("kind") or "unknown").strip().lower()
    if kind not in {"unknown", "running", "graceful"}:
        raise StateValidationError(f"Restart guard last_shutdown.kind is unsupported: {kind}")

    normalized["version"] = str(normalized.get("version") or RESTART_GUARD_VERSION)
    normalized["window_seconds"] = _safe_int(normalized.get("window_seconds"), "Restart guard window_seconds") or 60
    normalized["max_restarts"] = _safe_int(normalized.get("max_restarts"), "Restart guard max_restarts") or 3
    normalized["last_shutdown"] = {
        "kind": kind,
        "ts": _safe_int(last_shutdown.get("ts"), "Restart guard last_shutdown.ts"),
    }
    normalized["last_start_ts"] = _safe_int(normalized.get("last_start_ts"), "Restart guard last_start_ts")
    normalized["last_updated_ts"] = _safe_int(normalized.get("last_updated_ts"), "Restart guard last_updated_ts") or _now_ts()
    return normalized


def validate_settings(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise StateValidationError("Settings state must be an object")

    normalized = dict(default_settings())
    normalized.update(raw)

    buffer_mode = str(normalized.get("buffer_mode") or "MEDIUM").strip().upper()
    if buffer_mode not in {"SMALL", "MEDIUM", "LARGE"}:
        raise StateValidationError(f"Unsupported buffer_mode: {buffer_mode}")

    feature_flags = normalized.get("feature_flags", {})
    if not isinstance(feature_flags, dict):
        raise StateValidationError("feature_flags must be an object")

    normalized["buffer_mode"] = buffer_mode
    normalized["engine_tick_interval"] = _safe_int(normalized.get("engine_tick_interval"), "engine_tick_interval") or 2
    normalized["feature_flags"] = feature_flags
    normalized["last_updated_ts"] = _safe_int(normalized.get("last_updated_ts"), "last_updated_ts") or _now_ts()
    return normalized


def validate_active_symbols(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, list):
        raw = {"symbols": raw}
    if not isinstance(raw, dict):
        raise StateValidationError("Active symbols must be a list or object")

    normalized = dict(raw)
    if "symbols" in normalized and isinstance(normalized["symbols"], list):
        normalized["symbols"] = [str(item).strip().upper() for item in normalized["symbols"] if str(item).strip()]
    for key, value in list(normalized.items()):
        if isinstance(value, list):
            normalized[key] = [str(item).strip().upper() for item in value if str(item).strip()]
    normalized["last_updated_ts"] = _safe_int(normalized.get("last_updated_ts"), "last_updated_ts") or _now_ts()
    return normalized


def _normalize_telegram_thread_id(chat_id: int, thread_id: Optional[int]) -> Optional[int]:
    """Canonical thread_id normalization for Telegram sessions.

    For private chats (positive chat_id) thread_id is always None.
    For supergroups/channels (negative chat_id) thread_id must be a positive integer.
    thread_id <= 0 and thread_id=None are both treated as absent (None).

    This must produce identical results for:
    - no message_thread_id field
    - explicit None / JSON null
    - thread_id=0
    - missing key
    """
    if thread_id is None or thread_id <= 0:
        return None
    if chat_id >= 0:
        return None
    return thread_id


def _normalize_telegram_session_key(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int],
) -> tuple[int, int, Optional[int]]:
    """Return the canonical (chat_id, user_id, thread_id) key for a Telegram UI session."""
    return (int(chat_id), int(user_id), _normalize_telegram_thread_id(int(chat_id), thread_id))


def validate_telegram_ui_state(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise StateValidationError("Telegram UI state must be an object")

    normalized = dict(default_telegram_ui_state())
    normalized.update(raw)

    version = str(normalized.get("version") or TELEGRAM_UI_STATE_VERSION).strip()
    if version != TELEGRAM_UI_STATE_VERSION:
        raise StateValidationError(f"Telegram UI state version is unsupported: {version}")

    retention_seconds = _safe_int(normalized.get("retention_seconds"), "Telegram UI retention_seconds") or (7 * 24 * 60 * 60)
    if retention_seconds < 60:
        retention_seconds = 60

    max_sessions = _safe_int(normalized.get("max_sessions"), "Telegram UI max_sessions") or 1000
    if max_sessions < 1:
        max_sessions = 1

    sessions_raw = normalized.get("sessions", [])
    if not isinstance(sessions_raw, list):
        raise StateValidationError("Telegram UI sessions must be a list")

    now_ts = _now_ts()
    cutoff_ts = now_ts - retention_seconds
    dedup: Dict[tuple[int, int, Optional[int]], Dict[str, Any]] = {}

    for item in sessions_raw:
        if not isinstance(item, dict):
            raise StateValidationError("Telegram UI session entries must be objects")

        chat_id = _safe_int(item.get("chat_id"), "Telegram UI session chat_id")
        user_id = _safe_int(item.get("user_id"), "Telegram UI session user_id")
        message_id = _safe_int(item.get("message_id"), "Telegram UI session message_id")
        raw_thread_id = _safe_int(item.get("thread_id"), "Telegram UI session thread_id")
        updated_ts = _safe_int(item.get("updated_ts"), "Telegram UI session updated_ts") or now_ts
        if chat_id is None or user_id is None or message_id is None:
            raise StateValidationError("Telegram UI session chat_id/user_id/message_id are required integers")
        if updated_ts < cutoff_ts:
            continue
        # Normalize the thread_id so that 0, None, and missing all resolve identically.
        thread_id = _normalize_telegram_thread_id(chat_id, raw_thread_id)
        key = _normalize_telegram_session_key(chat_id, user_id, raw_thread_id)
        prior = dedup.get(key)
        if prior is None or updated_ts >= int(prior["updated_ts"]):
            dedup[key] = {
                "chat_id": chat_id,
                "user_id": user_id,
                "thread_id": thread_id,
                "message_id": message_id,
                "updated_ts": updated_ts,
            }

    sessions = sorted(dedup.values(), key=lambda row: int(row["updated_ts"]), reverse=True)
    if len(sessions) > max_sessions:
        sessions = sessions[:max_sessions]

    normalized["version"] = TELEGRAM_UI_STATE_VERSION
    normalized["retention_seconds"] = retention_seconds
    normalized["max_sessions"] = max_sessions
    normalized["sessions"] = sessions
    normalized["last_updated_ts"] = _safe_int(normalized.get("last_updated_ts"), "Telegram UI last_updated_ts") or now_ts
    return normalized


def _artifact(
    *,
    name: str,
    canonical_path: str,
    legacy_paths: tuple[str, ...],
    lock_name: str,
    default_factory: Callable[[], Dict[str, Any]],
    validator: Callable[[Any], Dict[str, Any]],
    required: bool = False,
) -> JsonArtifact:
    return JsonArtifact(
        name=name,
        canonical_path=canonical_path,
        legacy_paths=legacy_paths,
        lock_name=lock_name,
        default_factory=default_factory,
        validator=validator,
        required=required,
    )


def _load_artifact(artifact: JsonArtifact) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(artifact.canonical_path), exist_ok=True)

    with with_lock(artifact.lock_name):
        canonical_raw = _read_json_file(artifact.canonical_path)
        legacy_payloads: list[tuple[str, Dict[str, Any]]] = []

        for legacy_path in artifact.legacy_paths:
            if legacy_path == artifact.canonical_path:
                continue
            legacy_raw = _read_json_file(legacy_path)
            if legacy_raw is _MISSING:
                continue
            legacy_payloads.append((legacy_path, artifact.validator(legacy_raw)))

        if canonical_raw is not _MISSING:
            canonical_state = artifact.validator(canonical_raw)
            for legacy_path, legacy_state in legacy_payloads:
                if not _json_equal(canonical_state, legacy_state):
                    raise StateConflictError(
                        f"{artifact.name} conflict between canonical path {artifact.canonical_path} and legacy path {legacy_path}"
                    )
                _emit_warning(
                    "LEGACY_STATE_DUPLICATE",
                    f"{artifact.name} legacy path duplicates canonical state",
                    {
                        "artifact": artifact.name,
                        "canonical_path": artifact.canonical_path,
                        "legacy_path": legacy_path,
                    },
                )
            return canonical_state

        if not legacy_payloads:
            if artifact.required:
                raise StateValidationError(f"Missing required state artifact: {artifact.canonical_path}")
            return artifact.default_factory()

        source_path, source_state = legacy_payloads[0]
        for legacy_path, legacy_state in legacy_payloads[1:]:
            if not _json_equal(source_state, legacy_state):
                raise StateConflictError(
                    f"{artifact.name} conflict between legacy paths {source_path} and {legacy_path}"
                )

        save_json_atomic(artifact.canonical_path, source_state)
        _emit_warning(
            "LEGACY_STATE_MIGRATED",
            f"{artifact.name} migrated from legacy path to canonical segmented path",
            {
                "artifact": artifact.name,
                "source_path": source_path,
                "target_path": artifact.canonical_path,
            },
        )
        return source_state


def _save_artifact(artifact: JsonArtifact, payload: Dict[str, Any]) -> None:
    normalized = artifact.validator(payload)
    normalized["last_updated_ts"] = _now_ts()
    os.makedirs(os.path.dirname(artifact.canonical_path), exist_ok=True)
    with with_lock(artifact.lock_name):
        save_json_atomic(artifact.canonical_path, normalized)


def ensure_state_dir() -> None:
    os.makedirs(state_dir(), exist_ok=True)


def load_fsm_state(path: Optional[str] = None) -> Dict[str, Any]:
    canonical_path = path or FOCUS_STATE_PATH
    legacy_paths = () if path else (_legacy_root_path("focus_state.json"),)
    return _load_artifact(
        _artifact(
            name="fsm_state",
            canonical_path=canonical_path,
            legacy_paths=legacy_paths,
            lock_name="focus_state",
            default_factory=default_fsm_state,
            validator=validate_fsm_state,
        )
    )


def save_fsm_state(state: Dict[str, Any], path: Optional[str] = None) -> None:
    canonical_path = path or FOCUS_STATE_PATH
    _save_artifact(
        _artifact(
            name="fsm_state",
            canonical_path=canonical_path,
            legacy_paths=(),
            lock_name="focus_state",
            default_factory=default_fsm_state,
            validator=validate_fsm_state,
        ),
        state,
    )


def load_dist_state(path: Optional[str] = None) -> Dict[str, Any]:
    canonical_path = path or DIST_STATE_PATH
    legacy_paths = () if path else (_legacy_root_path("dist_state.json"),)
    return _load_artifact(
        _artifact(
            name="distribution_state",
            canonical_path=canonical_path,
            legacy_paths=legacy_paths,
            lock_name="dist_state",
            default_factory=default_dist_state,
            validator=validate_dist_state,
        )
    )


def save_dist_state(state: Dict[str, Any], path: Optional[str] = None) -> None:
    canonical_path = path or DIST_STATE_PATH
    _save_artifact(
        _artifact(
            name="distribution_state",
            canonical_path=canonical_path,
            legacy_paths=(),
            lock_name="dist_state",
            default_factory=default_dist_state,
            validator=validate_dist_state,
        ),
        state,
    )


def load_restart_guard_state(path: Optional[str] = None) -> Dict[str, Any]:
    canonical_path = path or RESTART_GUARD_PATH
    legacy_paths = () if path else (_legacy_root_path("restart_guard.json"),)
    return _load_artifact(
        _artifact(
            name="restart_guard_state",
            canonical_path=canonical_path,
            legacy_paths=legacy_paths,
            lock_name="restart_guard",
            default_factory=default_restart_guard_state,
            validator=validate_restart_guard_state,
        )
    )


def save_restart_guard_state(state: Dict[str, Any], path: Optional[str] = None) -> None:
    canonical_path = path or RESTART_GUARD_PATH
    _save_artifact(
        _artifact(
            name="restart_guard_state",
            canonical_path=canonical_path,
            legacy_paths=(),
            lock_name="restart_guard",
            default_factory=default_restart_guard_state,
            validator=validate_restart_guard_state,
        ),
        state,
    )


def load_settings(path: Optional[str] = None) -> Dict[str, Any]:
    canonical_path = path or SETTINGS_PATH
    legacy_paths = () if path else (_legacy_root_path("settings.json"),)
    return _load_artifact(
        _artifact(
            name="runtime_settings",
            canonical_path=canonical_path,
            legacy_paths=legacy_paths,
            lock_name="settings",
            default_factory=default_settings,
            validator=validate_settings,
        )
    )


def save_settings(settings: Dict[str, Any], path: Optional[str] = None) -> None:
    canonical_path = path or SETTINGS_PATH
    _save_artifact(
        _artifact(
            name="runtime_settings",
            canonical_path=canonical_path,
            legacy_paths=(),
            lock_name="settings",
            default_factory=default_settings,
            validator=validate_settings,
        ),
        settings,
    )


def load_active_symbols(path: Optional[str] = None) -> Dict[str, Any]:
    canonical_path = path or ACTIVE_SYMBOLS_PATH
    legacy_paths = () if path else (_legacy_root_path("active_symbols.json"),)
    return _load_artifact(
        _artifact(
            name="active_symbols",
            canonical_path=canonical_path,
            legacy_paths=legacy_paths,
            lock_name="active_symbols",
            default_factory=default_active_symbols,
            validator=validate_active_symbols,
        )
    )


def save_active_symbols(obj: Dict[str, Any], path: Optional[str] = None) -> None:
    canonical_path = path or ACTIVE_SYMBOLS_PATH
    _save_artifact(
        _artifact(
            name="active_symbols",
            canonical_path=canonical_path,
            legacy_paths=(),
            lock_name="active_symbols",
            default_factory=default_active_symbols,
            validator=validate_active_symbols,
        ),
        obj,
    )


def load_telegram_ui_state(path: Optional[str] = None) -> Dict[str, Any]:
    canonical_path = path or _telegram_ui_state_path()
    legacy_paths = () if path else (_legacy_root_path("telegram_ui_state.json"),)
    return _load_artifact(
        _artifact(
            name="telegram_ui_state",
            canonical_path=canonical_path,
            legacy_paths=legacy_paths,
            lock_name="telegram_ui_state",
            default_factory=default_telegram_ui_state,
            validator=validate_telegram_ui_state,
        )
    )


def save_telegram_ui_state(state: Dict[str, Any], path: Optional[str] = None) -> None:
    canonical_path = path or _telegram_ui_state_path()
    _save_artifact(
        _artifact(
            name="telegram_ui_state",
            canonical_path=canonical_path,
            legacy_paths=(),
            lock_name="telegram_ui_state",
            default_factory=default_telegram_ui_state,
            validator=validate_telegram_ui_state,
        ),
        state,
    )


def update_telegram_ui_state(
    updater: Callable[[Dict[str, Any]], Dict[str, Any]],
    path: Optional[str] = None,
) -> Dict[str, Any]:
    canonical_path = path or _telegram_ui_state_path()
    artifact = _artifact(
        name="telegram_ui_state",
        canonical_path=canonical_path,
        legacy_paths=() if path else (_legacy_root_path("telegram_ui_state.json"),),
        lock_name="telegram_ui_state",
        default_factory=default_telegram_ui_state,
        validator=validate_telegram_ui_state,
    )
    os.makedirs(os.path.dirname(artifact.canonical_path), exist_ok=True)
    with with_lock(artifact.lock_name):
        canonical_raw = _read_json_file(artifact.canonical_path)
        legacy_payloads: list[tuple[str, Dict[str, Any]]] = []
        for legacy_path in artifact.legacy_paths:
            if legacy_path == artifact.canonical_path:
                continue
            legacy_raw = _read_json_file(legacy_path)
            if legacy_raw is _MISSING:
                continue
            legacy_payloads.append((legacy_path, artifact.validator(legacy_raw)))

        if canonical_raw is not _MISSING:
            current = artifact.validator(canonical_raw)
            for legacy_path, legacy_state in legacy_payloads:
                if not _json_equal(current, legacy_state):
                    raise StateConflictError(
                        f"{artifact.name} conflict between canonical path {artifact.canonical_path} and legacy path {legacy_path}"
                    )
        elif not legacy_payloads:
            current = artifact.default_factory()
        else:
            source_path, current = legacy_payloads[0]
            for legacy_path, legacy_state in legacy_payloads[1:]:
                if not _json_equal(current, legacy_state):
                    raise StateConflictError(
                        f"{artifact.name} conflict between legacy paths {source_path} and {legacy_path}"
                    )
            _emit_warning(
                "LEGACY_STATE_MIGRATED",
                f"{artifact.name} migrated from legacy path to canonical segmented path",
                {
                    "artifact": artifact.name,
                    "source_path": source_path,
                    "target_path": artifact.canonical_path,
                },
            )
        updated = updater(dict(current))
        normalized = artifact.validator(updated)
        normalized["last_updated_ts"] = _now_ts()
        save_json_atomic(artifact.canonical_path, normalized)
        return normalized


def get_buffer_mode() -> str:
    return load_settings().get("buffer_mode", "MEDIUM")


def set_buffer_mode(mode: str) -> None:
    state = load_settings()
    state["buffer_mode"] = str(mode or "").upper()
    save_settings(state)


@dataclass(frozen=True)
class TelegramSessionDeleteResult:
    """Structured evidence from delete_telegram_ui_session."""
    session_existed: bool
    session_removed: bool
    final_session_count: int
    canonical_state_path: str
    target_key: tuple
    error: Optional[str] = None


def delete_telegram_ui_session(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
    path: Optional[str] = None,
) -> TelegramSessionDeleteResult:
    """Atomically delete exactly one persisted Telegram UI session.

    Correctness contract:
    1. Accepts one normalized session key (chat_id, user_id, thread_id).
    2. Acquires the canonical Telegram UI state file lock exclusively.
    3. Reads the latest persisted document while holding the lock.
    4. Validates and normalizes all persisted session keys (thread_id=0
       collapses to None for private chats; JSON null collapses to None).
    5. Removes only the exact target session (by canonical key equality).
    6. Preserves every unrelated USER or ADMIN session.
    7. Writes atomically using save_json_atomic.
    8. Returns TelegramSessionDeleteResult with structured evidence.
    9. Callers may independently verify absence after this call.
    10. Never uses stale whole-map overwrite semantics.
    """
    canonical_path = path or _telegram_ui_state_path()
    target_key = _normalize_telegram_session_key(int(chat_id), int(user_id), thread_id)
    artifact = _artifact(
        name="telegram_ui_state",
        canonical_path=canonical_path,
        legacy_paths=() if path else (_legacy_root_path("telegram_ui_state.json"),),
        lock_name="telegram_ui_state",
        default_factory=default_telegram_ui_state,
        validator=validate_telegram_ui_state,
    )
    os.makedirs(os.path.dirname(artifact.canonical_path), exist_ok=True)
    try:
        with with_lock(artifact.lock_name):
            canonical_raw = _read_json_file(artifact.canonical_path)
            if canonical_raw is _MISSING:
                current = artifact.default_factory()
            else:
                current = artifact.validator(canonical_raw)

            sessions_before: list[Dict[str, Any]] = current.get("sessions", [])
            sessions_after: list[Dict[str, Any]] = []
            session_existed = False

            for item in sessions_before:
                if not isinstance(item, dict):
                    continue
                item_chat = _safe_int(item.get("chat_id"), "chat_id")
                item_user = _safe_int(item.get("user_id"), "user_id")
                item_thread = _safe_int(item.get("thread_id"), "thread_id")
                if item_chat is None or item_user is None:
                    sessions_after.append(item)
                    continue
                item_key = _normalize_telegram_session_key(item_chat, item_user, item_thread)
                if item_key == target_key:
                    session_existed = True
                else:
                    sessions_after.append(item)

            updated = dict(current)
            updated["sessions"] = sessions_after
            updated["last_updated_ts"] = _now_ts()
            normalized = artifact.validator(updated)
            normalized["last_updated_ts"] = _now_ts()
            save_json_atomic(artifact.canonical_path, normalized)

            return TelegramSessionDeleteResult(
                session_existed=session_existed,
                session_removed=session_existed,
                final_session_count=len(normalized.get("sessions", [])),
                canonical_state_path=canonical_path,
                target_key=target_key,
            )
    except Exception as exc:
        return TelegramSessionDeleteResult(
            session_existed=False,
            session_removed=False,
            final_session_count=-1,
            canonical_state_path=canonical_path,
            target_key=target_key,
            error=str(exc),
        )


def verify_telegram_session_absent(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
    path: Optional[str] = None,
) -> Dict[str, Any]:
    """Read persisted state and confirm the session is absent.

    Returns a dict with:
    - 'absent': True when the session is not found in persisted state.
    - 'found_message_id': the persisted message_id if found, else None.
    - 'session_count': total persisted session count.
    - 'error': non-None when the read itself failed.
    """
    canonical_path = path or _telegram_ui_state_path()
    target_key = _normalize_telegram_session_key(int(chat_id), int(user_id), thread_id)
    try:
        artifact = _artifact(
            name="telegram_ui_state",
            canonical_path=canonical_path,
            legacy_paths=() if path else (_legacy_root_path("telegram_ui_state.json"),),
            lock_name="telegram_ui_state",
            default_factory=default_telegram_ui_state,
            validator=validate_telegram_ui_state,
        )
        with with_lock(artifact.lock_name):
            canonical_raw = _read_json_file(canonical_path)
            if canonical_raw is _MISSING:
                return {
                    "absent": True,
                    "found_message_id": None,
                    "session_count": 0,
                    "error": None,
                }
            current = artifact.validator(canonical_raw)
            sessions = current.get("sessions", [])
            for item in sessions:
                if not isinstance(item, dict):
                    continue
                item_chat = _safe_int(item.get("chat_id"), "chat_id")
                item_user = _safe_int(item.get("user_id"), "user_id")
                item_thread = _safe_int(item.get("thread_id"), "thread_id")
                if item_chat is None or item_user is None:
                    continue
                item_key = _normalize_telegram_session_key(item_chat, item_user, item_thread)
                if item_key == target_key:
                    return {
                        "absent": False,
                        "found_message_id": item.get("message_id"),
                        "session_count": len(sessions),
                        "error": None,
                    }
            return {
                "absent": True,
                "found_message_id": None,
                "session_count": len(sessions),
                "error": None,
            }
    except Exception as exc:
        return {
            "absent": False,
            "found_message_id": None,
            "session_count": -1,
            "error": str(exc),
        }


def read_telegram_session_message_id(
    chat_id: int,
    user_id: int,
    thread_id: Optional[int] = None,
    path: Optional[str] = None,
) -> Optional[int]:
    """Independently read the persisted message_id for one session.

    Returns None when absent, when the file does not exist, or on error.
    This is intentionally separate from in-memory state so that diagnostics
    can confirm persisted state without relying on the runtime cache.
    """
    result = verify_telegram_session_absent(chat_id, user_id, thread_id, path=path)
    if result.get("absent"):
        return None
    return result.get("found_message_id")



def list_symbols() -> list[str]:
    obj = load_active_symbols()
    if isinstance(obj.get("symbols"), list):
        return [str(item).strip().upper() for item in obj["symbols"] if str(item).strip()]

    result: list[str] = []
    seen = set()
    for value in obj.values():
        if not isinstance(value, list):
            continue
        for item in value:
            symbol = str(item).strip().upper()
            if symbol and symbol not in seen:
                seen.add(symbol)
                result.append(symbol)
    return result


def set_symbols(symbols: list[str]) -> None:
    save_active_symbols({"symbols": list(symbols or [])})
