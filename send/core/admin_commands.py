from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from core.admin_permissions import (
    ROLES_CONFIG_PATH,
    debug_identity,
    get_affiliate_scope,
    get_primary_role,
    has_permission,
    load_roles_config,
    reload_roles_config,
    require_permission,
)
from core.admin_views import (
    render_admin_home,
    render_affiliate_scope,
    render_debug_last,
    render_engine_status,
    render_error,
    render_ok,
    render_report_summary,
    render_roles,
    render_strategy_status,
    render_symbols,
    render_unauthorized,
)
from core import params_loader as _params_loader
from core import observability_logger
from core import storage as _storage
from core.operational_snapshot import build_status_snapshot

CONFIG_DIR = _storage.root_path("config")
OBS_DIR = os.getenv("OBS_DIR", _storage.root_path("observability"))
REPORTS_DIR = os.path.join(os.getenv("ANALYTICS_DIR", _storage.root_path("analytics")), "reports")

ALGO_PARAMS_PATH = os.path.join(CONFIG_DIR, "algo_params.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
ADMIN_EVENTS_PATH = os.path.join(os.getenv("OBS_DIR", _storage.root_path("observability")), "admin_events.jsonl")
ADMIN_PROOFS_PATH = os.path.join(os.getenv("OBS_DIR", _storage.root_path("observability")), "admin_proofs.jsonl")
ENGINE_EVENTS_PATH = os.path.join(os.getenv("OBS_DIR", _storage.root_path("observability")), "engine_events.jsonl")

# ---------------------------------------------------------------------------
# File delivery security constants
# ---------------------------------------------------------------------------

# Allowed file extensions for delivery.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".md", ".txt", ".json", ".jsonl", ".log"})

# Allowed subdirectory names under BINARYBOT_BASE_DIR for file browsing.
ALLOWED_DIR_NAMES: frozenset[str] = frozenset({
    "observability", "outcomes", "analytics", "reports", "snapshots", "docs", "audit",
})

# Short dir keys used in callback data (must stay ≤3 chars to keep callback_data ≤64 bytes).
_DIR_KEY_MAP: Dict[str, str] = {
    "obs": "observability",
    "out": "outcomes",
    "ana": "analytics",
    "rpt": "reports",        # resolves to analytics/reports
    "doc": "docs",
    "aud": "audit",
    "snp": "snapshots",
}

# Secret-bearing filename patterns — never deliver these.
_SECRET_PATTERNS: tuple[str, ...] = (
    ".env", "token", "secret", "password", "passwd", ".key", "credential",
    "private", ".pem", ".p12", ".pfx", ".cer", "id_rsa", "id_ed25519",
    "id_ecdsa", "salt", ".htpasswd",
)

# Default maximum file size for delivery (bytes).  Override with MAX_DELIVERY_FILE_SIZE env var.
MAX_DELIVERY_FILE_SIZE_DEFAULT = 5 * 1024 * 1024  # 5 MB

# Maximum number of JSONL lines to include in a bounded log export.
LOG_EXPORT_MAX_LINES = 200

# Maximum number of JSONL lines to include in a runtime audit artifact.
AUDIT_MAX_LINES_PER_FILE = 50

# ---------------------------------------------------------------------------
# Canonical strategy-profile definitions (MIC/SMALL, MEDIU/MEDIUM, MARE/LARGE)
# ---------------------------------------------------------------------------
# Maps profile name → canonical algo_params mutations.
# Only score_thresholds and sr_required_multiplier are touched;
# all other params are preserved from the current file.
STRATEGY_PROFILES: Dict[str, Dict[str, Any]] = {
    "CONSERVATIVE": {  # MIC / SMALL — tighter filters, fewer signals
        "score_thresholds": {"PRE": 60, "CONFIRM": 70, "OPEN": 75},
        "sr_required_multiplier": 1.8,
    },
    "BALANCED": {  # MEDIU / MEDIUM — moderate filters
        "score_thresholds": {"PRE": 55, "CONFIRM": 65, "OPEN": 70},
        "sr_required_multiplier": 1.5,
    },
    "AGGRESSIVE": {  # MARE / LARGE — looser filters, more signals
        "score_thresholds": {"PRE": 50, "CONFIRM": 60, "OPEN": 65},
        "sr_required_multiplier": 1.2,
    },
}

# Canonical list of known symbols split by category.
CANONICAL_SYMBOLS: Dict[str, List[str]] = {
    "FOREX": [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
        "EURGBP", "EURJPY", "GBPJPY", "EURAUD", "GBPAUD",
    ],
    "CRYPTO": [
        "BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "ADAUSD",
    ],
}

# Canonical algo_params.json path resolved via storage when possible.
def _algo_params_path() -> str:
    try:
        return _storage.config_path("algo_params.json")
    except Exception:
        return ALGO_PARAMS_PATH


def _safe_load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _read_json_observation(path: str) -> Optional[Any]:
    """Read a JSON artifact without converting absence/corruption into state."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _append_jsonl(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _audit(user_id: int, command: str, result: str, details: Optional[Dict[str, Any]] = None) -> None:
    payload = {
        "event_type": "admin_change",
        "user_id": user_id,
        "primary_role": get_primary_role(user_id),
        "command": command,
        "result": result,
        "details": details or {},
    }
    _append_jsonl(ADMIN_EVENTS_PATH, payload)
    _append_jsonl(ADMIN_PROOFS_PATH, payload)
    observability_logger.send_admin_proof_telegram("admin_change", payload, int(time.time()))


def _parse_command(text: str) -> List[str]:
    return [p.strip() for p in str(text).strip().split() if p.strip()]


def _load_algo_params() -> Dict[str, Any]:
    """Load the canonical algo params for admin display. Returns empty dict on error."""
    try:
        return _params_loader.load_algo_params(_algo_params_path())
    except (_params_loader.ParamsValidationError, _params_loader.ParamsMigrationError):
        return {}
    except (FileNotFoundError, OSError):
        return {}


def _save_algo_params_validated(params: Dict[str, Any]) -> None:
    """
    Validate params against the canonical contract, then write atomically.
    Raises ParamsValidationError if validation fails — does NOT write in that case.
    """
    _params_loader.validate_algo_params(params)
    path = _algo_params_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _storage.save_json_atomic(path, params)


def _load_active_symbols_raw() -> Any:
    return _safe_load_json(ACTIVE_SYMBOLS_PATH, {})


def _flatten_active_symbols(data: Any) -> List[str]:
    if isinstance(data, list):
        return sorted({str(x).upper() for x in data if str(x).strip()})

    if isinstance(data, dict):
        flat: List[str] = []
        for _, values in data.items():
            if isinstance(values, list):
                flat.extend(str(x).upper() for x in values if str(x).strip())
        return sorted(set(flat))

    return []


def _load_active_symbols() -> List[str]:
    return _flatten_active_symbols(_load_active_symbols_raw())


def _load_active_symbols_observation() -> Optional[List[str]]:
    """Return persisted symbol evidence, or None when it is absent/invalid."""
    data = _read_json_observation(ACTIVE_SYMBOLS_PATH)
    if isinstance(data, list):
        return _flatten_active_symbols(data)
    if isinstance(data, dict):
        if any(not isinstance(values, list) for values in data.values()):
            return None
        return _flatten_active_symbols(data)
    return None


def _save_active_symbols(symbols: List[str]) -> None:
    """
    Preserve current project compatibility:
    - if active_symbols.json is a dict, update the first list bucket
    - otherwise save flat list
    """
    existing = _load_active_symbols_raw()
    normalized = sorted({str(x).upper() for x in symbols if str(x).strip()})

    if isinstance(existing, dict) and existing:
        first_key = next(iter(existing.keys()))
        if isinstance(existing[first_key], list):
            existing[first_key] = normalized
            _storage.save_json_atomic(ACTIVE_SYMBOLS_PATH, existing)
            return

    _storage.save_json_atomic(ACTIVE_SYMBOLS_PATH, normalized)


def _iter_jsonl(path: str):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except Exception:
        return


def _last_decision_event() -> Optional[Dict[str, Any]]:
    events = list(_iter_jsonl(ENGINE_EVENTS_PATH) or [])
    for event in reversed(events):
        if isinstance(event, dict) and event.get("event_type") == "decision":
            return event
    return None


def _read_engine_events_observation() -> Optional[List[Dict[str, Any]]]:
    """Read the event log strictly so absence/corruption is not reported as zero."""
    if not os.path.isfile(ENGINE_EVENTS_PATH):
        return None
    events: List[Dict[str, Any]] = []
    try:
        with open(ENGINE_EVENTS_PATH, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    return None
                events.append(record)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return events


def _engine_status() -> Dict[str, Any]:
    snapshot = build_status_snapshot()
    events = _read_engine_events_observation()
    decisions = (
        None
        if events is None
        else [event for event in events if event.get("event_type") == "decision"]
    )
    last = decisions[-1] if decisions else None
    event_gap = "UNAVAILABLE (engine event log absent or invalid)"
    return {
        "runtime_phase": snapshot["runtime_phase"],
        "tick_interval": snapshot["engine_tick_seconds"],
        "last_decision_ts": (
            event_gap
            if decisions is None
            else (
                "NONE (no decision recorded in available event log)"
                if last is None
                else (
                    last.get("ts_utc")
                    or last.get("ts_epoch_ms")
                    or "UNKNOWN (decision timestamp not reported)"
                )
            )
        ),
        "decision_count": event_gap if decisions is None else len(decisions),
    }


def _find_latest_report_json() -> Optional[str]:
    if not os.path.isdir(REPORTS_DIR):
        return None
    candidates = [
        os.path.join(REPORTS_DIR, name)
        for name in os.listdir(REPORTS_DIR)
        if name.startswith("daily_strategy_audit_") and name.endswith(".json")
    ]
    if not candidates:
        return None
    return sorted(candidates)[-1]


def _report_summary() -> Dict[str, Any]:
    path = _find_latest_report_json()
    if not path:
        return {
            "availability": "UNAVAILABLE (no report artifact found)",
        }

    data = _read_json_observation(path)
    if not isinstance(data, dict):
        return {
            "availability": "UNAVAILABLE (report artifact invalid or unreadable)",
        }

    top_rejects = data.get("top_reject_reasons", [])
    if isinstance(top_rejects, dict):
        top_rejects = [f"{k}: {v}" for k, v in top_rejects.items()]
    elif not isinstance(top_rejects, list):
        top_rejects = []

    return {
        "availability": "AVAILABLE (persisted report artifact)",
        "date": data.get("date", os.path.basename(path)),
        "decisions": data.get(
            "decisions",
            data.get("total_decisions", "UNKNOWN (not reported)"),
        ),
        "rejects": data.get("rejects", "UNKNOWN (not reported)"),
        "pre": data.get("pre", "UNKNOWN (not reported)"),
        "confirm": data.get("confirm", "UNKNOWN (not reported)"),
        "open_now": data.get("open_now", "UNKNOWN (not reported)"),
        "avg_score": data.get("avg_score", "UNKNOWN (not reported)"),
        "top_rejects": top_rejects,
    }


def _known_roles_for_view() -> Dict[str, List[str]]:
    cfg = load_roles_config()
    out: Dict[str, List[str]] = {
        "owner": [str(x) for x in cfg.get("owner", [])] if isinstance(cfg.get("owner", []), list) else [],
        "primary_admin": [str(x) for x in cfg.get("primary_admin", [])] if isinstance(cfg.get("primary_admin", []), list) else [],
        "strategy_admin": [str(x) for x in cfg.get("strategy_admin", [])] if isinstance(cfg.get("strategy_admin", []), list) else [],
        "research_admin": [str(x) for x in cfg.get("research_admin", [])] if isinstance(cfg.get("research_admin", []), list) else [],
        "analyst": [str(x) for x in cfg.get("analyst", [])] if isinstance(cfg.get("analyst", []), list) else [],
        "moderator": [str(x) for x in cfg.get("moderator", [])] if isinstance(cfg.get("moderator", []), list) else [],
        "affiliate_admin": [],
    }

    raw_aff = cfg.get("affiliate_admin", {})
    if isinstance(raw_aff, dict):
        for code, payload in raw_aff.items():
            if isinstance(payload, dict):
                out["affiliate_admin"].append(f"{code}:{payload.get('telegram_id', '')}")

    return out


# ---------------------------------------------------------------------------
# Canonical parameter mutation helpers
# All write functions:
#   1. Load current canonical params (raw JSON, not validated, to allow partial files)
#   2. Apply the mutation
#   3. Validate full result via params_loader.validate_algo_params()
#   4. Write atomically — only if validation passes
# ---------------------------------------------------------------------------

def _load_raw_algo_params() -> Dict[str, Any]:
    """Load the raw JSON without validation (for mutation-then-revalidate pattern)."""
    path = _algo_params_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _set_threshold(field: str, value: int) -> str:
    """Mutate score_thresholds.<FIELD> and persist atomically after full validation.
    Holds the algo_params lock for the full read-modify-write cycle (GAP-011).
    """
    with _storage.with_lock("algo_params"):
        params = _load_raw_algo_params()
        params.setdefault("score_thresholds", {})
        params["score_thresholds"][field.upper()] = value
        _save_algo_params_validated(params)
    return f"Threshold {field.upper()} set to {value}."


def _set_sr(value: float) -> str:
    """Mutate sr_required_multiplier and persist atomically after full validation.
    Holds the algo_params lock for the full read-modify-write cycle (GAP-011).
    """
    with _storage.with_lock("algo_params"):
        params = _load_raw_algo_params()
        params["sr_required_multiplier"] = value
        _save_algo_params_validated(params)
    return f"SR required multiplier set to {value}."


def _set_spike(field: str, value: float) -> str:
    """Mutate spike_filters.<field> and persist atomically after full validation.
    Holds the algo_params lock for the full read-modify-write cycle (GAP-011).
    """
    with _storage.with_lock("algo_params"):
        params = _load_raw_algo_params()
        params.setdefault("spike_filters", {})
        params["spike_filters"][field] = value
        _save_algo_params_validated(params)
    return f"Spike filter {field} set to {value}."


def _symbols_add(symbol: str) -> str:
    with _storage.with_lock("active_symbols"):
        symbols = _load_active_symbols()
        if symbol not in symbols:
            symbols.append(symbol)
            _save_active_symbols(symbols)
    return f"Added symbol {symbol}."


def _symbols_remove(symbol: str) -> str:
    with _storage.with_lock("active_symbols"):
        symbols = [s for s in _load_active_symbols() if s != symbol]
        _save_active_symbols(symbols)
    return f"Removed symbol {symbol}."


# ---------------------------------------------------------------------------
# Symbol management helpers
# ---------------------------------------------------------------------------

def get_all_known_symbols() -> List[str]:
    """Return the canonical list of all known symbols (FOREX + CRYPTO)."""
    result: List[str] = []
    for syms in CANONICAL_SYMBOLS.values():
        result.extend(syms)
    return sorted(set(result))


def handle_symbols_toggle(symbol: str, user_id: int) -> str:
    """Toggle a single symbol on/off.  Generates Admin Proof."""
    ok, reason = require_permission(user_id, "strategy.symbols.write")
    if not ok:
        return render_error(reason)
    sym = symbol.upper().strip()
    if not sym or not sym.isalpha() or len(sym) > 12:
        return render_error(f"Invalid symbol: {symbol!r}")
    with _storage.with_lock("active_symbols"):
        symbols = _load_active_symbols()
        if sym in symbols:
            symbols = [s for s in symbols if s != sym]
            action = "remove"
        else:
            symbols.append(sym)
            action = "add"
        _save_active_symbols(symbols)
    _audit(user_id, f"/symbols {action}", "OK", {"symbol": sym})
    return render_ok(f"{'Added' if action == 'add' else 'Removed'} symbol {sym}.")


def handle_symbols_all(user_id: int) -> str:
    """Activate all canonical symbols.  Generates Admin Proof."""
    ok, reason = require_permission(user_id, "strategy.symbols.write")
    if not ok:
        return render_error(reason)
    all_syms = get_all_known_symbols()
    with _storage.with_lock("active_symbols"):
        _save_active_symbols(all_syms)
    _audit(user_id, "/symbols all", "OK", {"count": len(all_syms)})
    return render_ok(f"Activated {len(all_syms)} canonical symbols.")


def handle_symbols_none(user_id: int) -> str:
    """Deactivate all symbols.  Generates Admin Proof."""
    ok, reason = require_permission(user_id, "strategy.symbols.write")
    if not ok:
        return render_error(reason)
    with _storage.with_lock("active_symbols"):
        _save_active_symbols([])
    _audit(user_id, "/symbols none", "OK", {})
    return render_ok("All symbols deactivated.")


# ---------------------------------------------------------------------------
# Strategy-profile helpers
# ---------------------------------------------------------------------------

def get_current_strategy_profile() -> Optional[str]:
    """
    Detect which canonical strategy profile best matches the current parameters.
    Returns the profile name if an exact match is found, otherwise None.
    """
    params = _load_algo_params()
    thresholds = params.get("score_thresholds", {})
    sr = params.get("sr_required_multiplier")
    for name, profile in STRATEGY_PROFILES.items():
        pt = profile["score_thresholds"]
        if (thresholds.get("PRE") == pt["PRE"]
                and thresholds.get("CONFIRM") == pt["CONFIRM"]
                and thresholds.get("OPEN") == pt["OPEN"]
                and sr == profile["sr_required_multiplier"]):
            return name
    return None


def handle_strategy_profile(profile: str, user_id: int) -> str:
    """
    Apply a named strategy profile (CONSERVATIVE / BALANCED / AGGRESSIVE).
    Generates Admin Proof.
    """
    ok, reason = require_permission(user_id, "strategy.thresholds.write")
    if not ok:
        return render_error(reason)
    profile_key = profile.upper().strip()
    if profile_key not in STRATEGY_PROFILES:
        return render_error(f"Unknown profile: {profile!r}. Valid: {', '.join(STRATEGY_PROFILES)}")
    defn = STRATEGY_PROFILES[profile_key]
    with _storage.with_lock("algo_params"):
        params = _load_raw_algo_params()
        params.setdefault("score_thresholds", {})
        params["score_thresholds"].update(defn["score_thresholds"])
        params["sr_required_multiplier"] = defn["sr_required_multiplier"]
        try:
            _save_algo_params_validated(params)
        except _params_loader.ParamsValidationError as exc:
            return render_error(f"Profile update rejected: {exc}")
    _audit(user_id, "/strategy profile", "OK", {"profile": profile_key, "params": defn})
    return render_ok(
        f"Strategy profile {profile_key} applied.\n"
        f"PRE={defn['score_thresholds']['PRE']} "
        f"CONFIRM={defn['score_thresholds']['CONFIRM']} "
        f"OPEN={defn['score_thresholds']['OPEN']} "
        f"SR={defn['sr_required_multiplier']}"
    )


# ---------------------------------------------------------------------------
# File-delivery security
# ---------------------------------------------------------------------------

def _max_delivery_size() -> int:
    raw = os.getenv("MAX_DELIVERY_FILE_SIZE", "").strip()
    try:
        return max(1, int(raw))
    except Exception:
        return MAX_DELIVERY_FILE_SIZE_DEFAULT


def _resolve_dir_path(dir_key: str) -> Optional[str]:
    """
    Resolve a short dir key to an absolute allowed directory path.
    Returns None if the key is unknown or the directory doesn't exist.
    """
    subdir = _DIR_KEY_MAP.get(dir_key)
    if subdir is None:
        return None
    base = _storage.base_dir()
    if dir_key == "rpt":
        # reports is analytics/reports
        candidate = os.path.join(base, "analytics", "reports")
    else:
        candidate = os.path.join(base, subdir)
    return candidate


def _is_path_safe(path: str, dir_key: str) -> Tuple[bool, str]:
    """
    Validate that a file path is safe to deliver.

    Checks:
    1. No '..' in path components.
    2. Extension is in the allowed set.
    3. Real path is under the allowed directory.
    4. Not a symlink escaping the allowed root.
    5. File size does not exceed the configured maximum.
    6. Filename does not match secret-bearing patterns.

    Returns (ok: bool, reason: str).
    """
    filename = os.path.basename(path)

    # Reject traversal attempts up front
    if ".." in path.replace("\\", "/"):
        return False, "path traversal rejected"

    # Extension check
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"unsupported extension: {ext!r}"

    # Secret filename check
    fn_lower = filename.lower()
    for pattern in _SECRET_PATTERNS:
        if pattern in fn_lower:
            return False, "filename matches a restricted pattern"

    # Resolve allowed root
    allowed_root = _resolve_dir_path(dir_key)
    if allowed_root is None:
        return False, f"unknown directory key: {dir_key!r}"

    # Real path resolution (catches symlink escapes)
    try:
        real_path = os.path.realpath(path)
        real_root = os.path.realpath(allowed_root)
    except Exception as exc:
        return False, f"path resolution failed: {exc}"

    if not real_path.startswith(real_root + os.sep) and real_path != real_root:
        return False, "path escapes allowed root"

    # Existence check
    if not os.path.isfile(real_path):
        return False, "file not found"

    # Symlink check
    if os.path.islink(path):
        link_target = os.path.realpath(path)
        if not link_target.startswith(real_root + os.sep):
            return False, "symlink escapes allowed root"

    # Size check
    try:
        size = os.path.getsize(real_path)
    except Exception as exc:
        return False, f"size check failed: {exc}"
    if size > _max_delivery_size():
        return False, f"file too large ({size} bytes; max {_max_delivery_size()})"

    return True, ""


def handle_files_list(user_id: int, dir_key: str, page: int = 0) -> Dict[str, Any]:
    """
    List files in the allowed directory for `dir_key`, paginated.

    Returns dict with keys: title, filenames, page, total_pages, error.
    """
    from core.telegram_admin_ui import FILES_PER_PAGE  # local import to avoid circular
    ok_perm, reason = require_permission(user_id, "files.view")
    if not ok_perm:
        return {"error": reason, "filenames": [], "page": 0, "total_pages": 0, "title": ""}

    dir_path = _resolve_dir_path(dir_key)
    if dir_path is None:
        return {"error": f"Unknown directory: {dir_key!r}", "filenames": [], "page": 0, "total_pages": 0, "title": ""}

    if not os.path.isdir(dir_path):
        return {"error": f"Directory not available: {dir_path}", "filenames": [], "page": 0, "total_pages": 0, "title": ""}

    try:
        all_files = sorted(
            f for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
            and os.path.splitext(f.lower())[1] in ALLOWED_EXTENSIONS
            and not any(pat in f.lower() for pat in _SECRET_PATTERNS)
        )
    except Exception as exc:
        return {"error": f"Cannot list directory: {exc}", "filenames": [], "page": 0, "total_pages": 0, "title": ""}

    total = len(all_files)
    total_pages = max(1, (total + FILES_PER_PAGE - 1) // FILES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * FILES_PER_PAGE
    page_files = all_files[start: start + FILES_PER_PAGE]

    _audit(user_id, "/files list", "OK", {"dir_key": dir_key, "page": page, "total": total})
    return {
        "error": None,
        "filenames": page_files,
        "page": page,
        "total_pages": total_pages,
        "title": f"📁 {_DIR_KEY_MAP.get(dir_key, dir_key)} ({total} files)",
    }


def handle_file_download_path(dir_key: str, filename: str, user_id: int) -> Tuple[Optional[str], str]:
    """
    Validate and return the absolute path of a file for delivery.

    Returns (path, "") on success; (None, error_msg) on failure.
    Generates an audit entry for every request.
    """
    ok_perm, reason = require_permission(user_id, "files.view")
    if not ok_perm:
        _audit(user_id, "/download", "DENIED", {"dir_key": dir_key, "filename": filename, "reason": reason})
        return None, reason

    # Sanitise filename — no path separators, no traversal
    safe_name = os.path.basename(filename)
    if safe_name != filename or not safe_name:
        _audit(user_id, "/download", "REJECTED", {"filename": filename, "reason": "traversal"})
        return None, "Invalid filename."

    dir_path = _resolve_dir_path(dir_key)
    if dir_path is None:
        _audit(user_id, "/download", "REJECTED", {"dir_key": dir_key, "reason": "unknown dir"})
        return None, f"Unknown directory: {dir_key!r}"

    full_path = os.path.join(dir_path, safe_name)
    ok, reason = _is_path_safe(full_path, dir_key)
    if not ok:
        _audit(user_id, "/download", "REJECTED", {"path": full_path, "reason": reason})
        return None, f"File rejected: {reason}"

    _audit(user_id, "/download", "OK", {"dir_key": dir_key, "filename": safe_name})
    return full_path, ""


def handle_docs_list(user_id: int) -> Dict[str, Any]:
    """List .md / .txt files in the docs directory."""
    return handle_files_list(user_id, "doc", page=0)


def handle_log_export(user_id: int) -> Tuple[Optional[str], str]:
    """
    Export a bounded, sanitized diagnostic log as a temporary file.

    Returns (tmp_path, "") on success; (None, error_msg) on failure.
    Never includes TELEGRAM_BOT_TOKEN or API secrets.
    """
    ok_perm, reason = require_permission(user_id, "diagnostics.view")
    if not ok_perm:
        return None, reason

    _REDACTED_KEYS = frozenset({
        "token", "secret", "password", "key", "salt", "credential", "api_key",
        "telegram_bot_token", "twelve_data_api_key", "community_feedback_salt",
    })

    def _redact(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: "[REDACTED]" if any(r in k.lower() for r in _REDACTED_KEYS) else _redact(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_redact(x) for x in obj]
        return obj

    lines_out: List[str] = []
    for log_path in [ENGINE_EVENTS_PATH, ADMIN_EVENTS_PATH]:
        if not os.path.exists(log_path):
            continue
        log_lines: List[str] = []
        for record in _iter_jsonl(log_path):
            log_lines.append(json.dumps(_redact(record), ensure_ascii=False))
        # Take the last LOG_EXPORT_MAX_LINES lines
        lines_out.extend(log_lines[-LOG_EXPORT_MAX_LINES:])

    if not lines_out:
        lines_out = ["# No log data available."]

    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", prefix="binarybot_log_",
            delete=False, encoding="utf-8",
        )
        tmp.write("\n".join(lines_out[:LOG_EXPORT_MAX_LINES]))
        tmp.close()
        _audit(user_id, "/log export", "OK", {"lines": len(lines_out)})
        return tmp.name, ""
    except Exception as exc:
        _audit(user_id, "/log export", "ERROR", {"error": str(exc)})
        return None, f"Log export failed: {exc}"


def handle_diagnose(user_id: int) -> str:
    """
    Generate a concise operational diagnosis covering all key subsystems.
    Requires diagnostics.view permission.
    """
    ok_perm, reason = require_permission(user_id, "diagnostics.view")
    if not ok_perm:
        return render_error(reason)

    snapshot = build_status_snapshot()

    # Recent incidents (last 3 errors from error log)
    incidents: List[str] = []
    error_log = os.path.join(OBS_DIR, "error_events.jsonl")
    for record in _iter_jsonl(error_log):
        msg = ""
        if isinstance(record, dict):
            d = record.get("data") or record
            msg = str(d.get("message") or d.get("error") or "")[:80]
        if msg:
            incidents.append(msg)
    recent_incidents = incidents[-3:] if incidents else []

    # File availability
    file_checks = {
        "algo_params": os.path.exists(_algo_params_path()),
        "active_symbols": os.path.exists(ACTIVE_SYMBOLS_PATH),
        "engine_events": os.path.exists(ENGINE_EVENTS_PATH),
    }
    file_status = ", ".join(f"{k}={'✅' if v else '⬜'}" for k, v in file_checks.items())

    lines = [
        "🩺 Diagnosis",
        "",
        f"Runtime phase: {snapshot['runtime_phase']}",
        f"Telegram polling: {snapshot['telegram_state']}",
        f"Market data: {snapshot['market_data_state']}",
        f"FSM: {snapshot['fsm_state']}",
        f"Shadow mode: {snapshot['shadow_mode']}",
        f"Broker execution: {snapshot['broker_state']}",
        f"Recovery: {snapshot['recovery_state']}",
        "",
        f"Files: {file_status}",
    ]
    if recent_incidents:
        lines.append("")
        lines.append("Recent incidents:")
        for inc in recent_incidents:
            lines.append(f"  • {inc}")
    return "\n".join(lines)


def handle_audit_runtime(user_id: int) -> Tuple[Optional[str], str]:
    """
    Generate a bounded, sanitized runtime audit artifact as a temporary JSON file.

    Never includes TELEGRAM_BOT_TOKEN, API secrets, salts, or credentials.
    Returns (tmp_path, "") on success; (None, error_msg) on failure.
    """
    ok_perm, reason = require_permission(user_id, "diagnostics.view")
    if not ok_perm:
        return None, reason

    _SECRET_ENV_KEYS = frozenset({
        "TELEGRAM_BOT_TOKEN", "TWELVE_DATA_API_KEY", "COMMUNITY_FEEDBACK_SALT",
        "SECRET", "PASSWORD", "PASSWD", "PRIVATE_KEY", "API_SECRET",
    })

    # Build env presence matrix — keys only, never values
    env_matrix: Dict[str, bool] = {}
    for key in [
        "BINARYBOT_BASE_DIR", "SHADOW_MODE", "ENABLE_BROKER_EXECUTION", "ENABLE_TELEGRAM",
        "TELEGRAM_BOT_TOKEN", "TWELVE_DATA_API_KEY", "OWNER_TELEGRAM_ID",
        "ADMIN_CONTROL_CHAT_ID", "ADMIN_CONTROL_THREAD_ID", "ADMIN_ROLES_CONFIG",
        "ADMIN_PERMISSIONS_CONFIG", "OBS_DIR", "ANALYTICS_DIR", "ALGO_PARAMS_PATH",
        "ADMIN_PROOF_CHAT_ID", "ADMIN_PROOF_THREAD_ID",
        "ADMIN_ALERTS_THREAD_ID", "ADMIN_ERRORS_THREAD_ID", "ADMIN_REPORTS_THREAD_ID",
        "MAX_DELIVERY_FILE_SIZE",
    ]:
        val = os.getenv(key)
        if key in _SECRET_ENV_KEYS:
            env_matrix[key] = val is not None and val.strip() not in {"", "replace-me"}
        else:
            env_matrix[key] = val is not None and val.strip() != ""

    # Runtime status
    try:
        from runtime import runtime_status  # type: ignore
        status = runtime_status.read_status()
    except Exception:
        status = {}

    # Directory inventory (existence only)
    base = _storage.base_dir()
    dir_inventory: Dict[str, bool] = {}
    for subdir in ["config", "observability", "outcomes", "analytics", "analytics/reports", "docs", "audit", "snapshots"]:
        dir_inventory[subdir] = os.path.isdir(os.path.join(base, subdir))

    # Bounded recent events (last AUDIT_MAX_LINES_PER_FILE from engine and admin events)
    recent_engine: List[Any] = []
    recent_admin: List[Any] = []
    for record in _iter_jsonl(ENGINE_EVENTS_PATH):
        recent_engine.append(record)
    for record in _iter_jsonl(ADMIN_EVENTS_PATH):
        recent_admin.append(record)
    recent_engine = recent_engine[-AUDIT_MAX_LINES_PER_FILE:]
    recent_admin = recent_admin[-AUDIT_MAX_LINES_PER_FILE:]

    # Recent errors (bounded)
    recent_errors: List[Any] = []
    error_log = os.path.join(OBS_DIR, "error_events.jsonl")
    for record in _iter_jsonl(error_log):
        recent_errors.append(record)
    recent_errors = recent_errors[-AUDIT_MAX_LINES_PER_FILE:]

    # Active config summary (redact secrets)
    config_summary: Dict[str, Any] = {}
    try:
        params = _load_algo_params()
        config_summary["score_thresholds"] = params.get("score_thresholds")
        config_summary["sr_required_multiplier"] = params.get("sr_required_multiplier")
        config_summary["strategy_profile"] = get_current_strategy_profile()
        observed_symbols = _load_active_symbols_observation()
        config_summary["active_symbols_count"] = (
            "UNAVAILABLE (active-symbol configuration absent or invalid)"
            if observed_symbols is None
            else len(observed_symbols)
        )
    except Exception:
        config_summary["error"] = "unable to load"

    artifact = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "generator": f"user_id={user_id}",
        "env_presence_matrix": env_matrix,
        "runtime_status": {k: v for k, v in status.items() if k not in {"token", "secret"}},
        "directory_inventory": dir_inventory,
        "config_summary": config_summary,
        "recent_engine_events": recent_engine,
        "recent_admin_events": recent_admin,
        "recent_errors": recent_errors,
        "NOTE": "Secret values are never included. Presence matrix shows existence only.",
    }

    try:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", prefix="binarybot_audit_",
            delete=False, encoding="utf-8",
        )
        json.dump(artifact, tmp, ensure_ascii=False, indent=2)
        tmp.close()
        _audit(user_id, "/audit_runtime", "OK", {"path": tmp.name})
        return tmp.name, ""
    except Exception as exc:
        _audit(user_id, "/audit_runtime", "ERROR", {"error": str(exc)})
        return None, f"Audit generation failed: {exc}"


def handle_admin_command(text: str, user_id: int) -> str:
    parts = _parse_command(text)
    if not parts:
        return render_error("Empty command.")

    identity = debug_identity(user_id)
    cmd = parts[0].lower()

    if not has_permission(user_id, "admin.view"):
        return render_unauthorized()

    try:
        if cmd == "/admin":
            return render_admin_home(identity)

        if cmd == "/strategy":
            ok, reason = require_permission(user_id, "strategy.view")
            if not ok:
                return render_error(reason)
            return render_strategy_status(_load_algo_params())

        if cmd == "/thresholds":
            if len(parts) == 1:
                ok, reason = require_permission(user_id, "strategy.view")
                if not ok:
                    return render_error(reason)
                return render_strategy_status(_load_algo_params())

            ok, reason = require_permission(user_id, "strategy.thresholds.write")
            if not ok:
                return render_error(reason)

            if len(parts) != 3:
                return render_error("Usage: /thresholds PRE|CONFIRM|OPEN <value>")

            field = parts[1].strip().upper()
            if field not in {"PRE", "CONFIRM", "OPEN"}:
                return render_error("Threshold must be PRE, CONFIRM, or OPEN.")

            try:
                value = int(float(parts[2]))
            except Exception:
                return render_error("Threshold value must be numeric.")

            if value < 0 or value > 100:
                return render_error("Threshold must be between 0 and 100.")

            try:
                message = _set_threshold(field, value)
            except _params_loader.ParamsValidationError as exc:
                return render_error(f"Threshold update rejected: {exc}")
            _audit(user_id, "/thresholds", "OK", {"field": field, "value": value})
            return render_ok(message)

        if cmd == "/sr":
            if len(parts) == 1:
                ok, reason = require_permission(user_id, "strategy.view")
                if not ok:
                    return render_error(reason)
                return render_ok(
                    f"SR required multiplier = {_load_algo_params().get('sr_required_multiplier', 'N/A')}"
                )

            ok, reason = require_permission(user_id, "strategy.sr.write")
            if not ok:
                return render_error(reason)

            try:
                value = float(parts[1])
            except Exception:
                return render_error("SR value must be numeric.")

            if value <= 0 or value > 10.0:
                return render_error("SR required multiplier must be > 0 and <= 10.0.")

            try:
                message = _set_sr(value)
            except _params_loader.ParamsValidationError as exc:
                return render_error(f"SR update rejected: {exc}")
            _audit(user_id, "/sr", "OK", {"value": value})
            return render_ok(message)

        if cmd == "/spike":
            if len(parts) == 1:
                ok, reason = require_permission(user_id, "strategy.view")
                if not ok:
                    return render_error(reason)
                return render_strategy_status(_load_algo_params())

            ok, reason = require_permission(user_id, "strategy.spike.write")
            if not ok:
                return render_error(reason)

            if len(parts) != 3:
                return render_error(
                    "Usage: /spike wick_body_ratio_max|range_z_max|jump_vs_atr_max <value>"
                )

            field = parts[1].strip().lower()
            if field not in {"wick_body_ratio_max", "range_z_max", "jump_vs_atr_max"}:
                return render_error(
                    "Field must be wick_body_ratio_max, range_z_max, or jump_vs_atr_max."
                )

            try:
                value = float(parts[2])
            except Exception:
                return render_error("Spike value must be numeric.")

            if value <= 0:
                return render_error("Spike filter value must be > 0.")

            try:
                message = _set_spike(field, value)
            except _params_loader.ParamsValidationError as exc:
                return render_error(f"Spike update rejected: {exc}")
            _audit(user_id, "/spike", "OK", {"field": field, "value": value})
            return render_ok(message)

        if cmd == "/symbols":
            if len(parts) == 1 or (len(parts) == 2 and parts[1].lower() == "list"):
                ok, reason = require_permission(user_id, "strategy.view")
                if not ok:
                    return render_error(reason)
                return render_symbols(_load_active_symbols_observation())

            ok, reason = require_permission(user_id, "strategy.symbols.write")
            if not ok:
                return render_error(reason)

            if len(parts) != 3:
                return render_error("Usage: /symbols list | /symbols add SYMBOL | /symbols remove SYMBOL")

            action = parts[1].lower()
            symbol = parts[2].upper()

            if action == "add":
                message = _symbols_add(symbol)
                _audit(user_id, "/symbols add", "OK", {"symbol": symbol})
                return render_ok(message)

            if action == "remove":
                message = _symbols_remove(symbol)
                _audit(user_id, "/symbols remove", "OK", {"symbol": symbol})
                return render_ok(message)

            return render_error("Usage: /symbols list | /symbols add SYMBOL | /symbols remove SYMBOL")

        if cmd == "/engine":
            ok, reason = require_permission(user_id, "engine.view")
            if not ok:
                return render_error(reason)
            return render_engine_status(_engine_status())

        if cmd == "/debug":
            ok, reason = require_permission(user_id, "debug.view")
            if not ok:
                return render_error(reason)
            return render_debug_last(_last_decision_event())

        if cmd == "/report":
            ok, reason = require_permission(user_id, "reports.view")
            if not ok:
                return render_error(reason)
            return render_report_summary(_report_summary())

        if cmd == "/roles":
            ok, reason = require_permission(user_id, "roles.view")
            if not ok:
                return render_error(reason)
            return render_roles(identity, _known_roles_for_view())

        if cmd == "/affiliate":
            scope = get_affiliate_scope(user_id)
            target_code = None if scope is None else scope.affiliate_code
            ok, reason = require_permission(user_id, "affiliate.view", target_affiliate_code=target_code)
            if not ok:
                return render_error(reason)

            if scope is None and not has_permission(user_id, "affiliate.view.any"):
                return render_error("No affiliate scope assigned.")

            if scope is None:
                return render_ok("Affiliate admin visibility is enabled, but no scoped record was found.")

            return render_affiliate_scope(
                {
                    "affiliate_code": scope.affiliate_code,
                    "telegram_id": scope.telegram_id,
                    "display_name": scope.affiliate_code,
                    "commission_percent": "N/A",
                }
            )

        if cmd == "/roles_reload":
            ok, reason = require_permission(user_id, "roles.write")
            if not ok:
                return render_error(reason)
            reload_roles_config()
            _audit(user_id, "/roles_reload", "OK", {"roles_config_path": ROLES_CONFIG_PATH})
            return render_ok("Roles configuration reloaded.")

        if cmd in {"/files", "/docs"}:
            dir_key = "doc" if cmd == "/docs" else None
            if cmd == "/files" and len(parts) >= 2:
                # /files <dir_key>
                dir_key = parts[1].lower()
            elif cmd == "/files":
                # No arg: show file-home listing
                return render_ok(
                    "📁 File Browser\n\nAvailable directories: "
                    + ", ".join(_DIR_KEY_MAP.keys())
                    + "\n\nUse /files <dir> or the UI buttons."
                )
            info = handle_files_list(user_id, dir_key or "obs", page=0)
            if info.get("error"):
                return render_error(info["error"])
            fnames = info.get("filenames", [])
            if not fnames:
                return render_ok(f"{info.get('title', '')}\n\nNo files found.")
            lines = [info.get("title", "Files"), ""]
            lines.extend(f"• {f}" for f in fnames)
            if info.get("total_pages", 1) > 1:
                lines.append(f"\nPage {info['page'] + 1}/{info['total_pages']}")
            return "\n".join(lines)

        if cmd == "/download":
            if len(parts) < 3:
                return render_error("Usage: /download <dir_key> <filename>")
            dir_key = parts[1].lower()
            filename = parts[2]
            path, err = handle_file_download_path(dir_key, filename, user_id)
            if err:
                return render_error(err)
            # Caller (bot_service) handles actual document send; return path marker
            return f"__FILE_PATH__:{path}"

        if cmd == "/log":
            path, err = handle_log_export(user_id)
            if err:
                return render_error(err)
            return f"__FILE_PATH__:{path}"

        if cmd == "/diagnose":
            return handle_diagnose(user_id)

        if cmd == "/audit_runtime":
            path, err = handle_audit_runtime(user_id)
            if err:
                return render_error(err)
            return f"__FILE_PATH__:{path}"

        return render_error("Unknown admin command.")

    except Exception as exc:
        _audit(user_id, cmd, "ERROR", {"error": str(exc)})
        return render_error(str(exc))
