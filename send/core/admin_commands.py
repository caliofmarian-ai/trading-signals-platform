from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

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
from core import storage as _storage

CONFIG_DIR = "/opt/binarybot/config"
OBS_DIR = "/opt/binarybot/observability"
REPORTS_DIR = "/opt/binarybot/analytics/reports"

ALGO_PARAMS_PATH = os.path.join(CONFIG_DIR, "algo_params.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
ADMIN_SETTINGS_PATH = os.path.join(CONFIG_DIR, "admin_settings.json")
ADMIN_EVENTS_PATH = os.path.join(OBS_DIR, "admin_events.jsonl")
ADMIN_PROOFS_PATH = os.path.join(OBS_DIR, "admin_proofs.jsonl")
ENGINE_EVENTS_PATH = os.path.join(OBS_DIR, "engine_events.jsonl")

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


def _load_admin_settings() -> Dict[str, Any]:
    data = _safe_load_json(ADMIN_SETTINGS_PATH, {})
    if not isinstance(data, dict):
        data = {}
    data.setdefault("engine_tick_interval", 2)
    data.setdefault("feature_flags", {})
    return data


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


def _decision_count() -> int:
    count = 0
    for event in _iter_jsonl(ENGINE_EVENTS_PATH) or []:
        if isinstance(event, dict) and event.get("event_type") == "decision":
            count += 1
    return count


def _engine_status() -> Dict[str, Any]:
    last = _last_decision_event()
    settings = _load_admin_settings()
    return {
        "running": "UNKNOWN" if last is None else "YES",
        "tick_interval": settings.get("engine_tick_interval", 2),
        "last_decision_ts": None if last is None else (last.get("ts_utc") or last.get("ts_epoch_ms")),
        "decision_count": _decision_count(),
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
            "date": "N/A",
            "decisions": 0,
            "rejects": 0,
            "pre": 0,
            "confirm": 0,
            "open_now": 0,
            "avg_score": "N/A",
            "top_rejects": [],
        }

    data = _safe_load_json(path, {})
    if not isinstance(data, dict):
        data = {}

    top_rejects = data.get("top_reject_reasons", [])
    if isinstance(top_rejects, dict):
        top_rejects = [f"{k}: {v}" for k, v in top_rejects.items()]
    elif not isinstance(top_rejects, list):
        top_rejects = []

    return {
        "date": data.get("date", os.path.basename(path)),
        "decisions": data.get("decisions", data.get("total_decisions", 0)),
        "rejects": data.get("rejects", 0),
        "pre": data.get("pre", 0),
        "confirm": data.get("confirm", 0),
        "open_now": data.get("open_now", 0),
        "avg_score": data.get("avg_score", "N/A"),
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
                return render_symbols(_load_active_symbols())

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

        return render_error("Unknown admin command.")

    except Exception as exc:
        _audit(user_id, cmd, "ERROR", {"error": str(exc)})
        return render_error(str(exc))
