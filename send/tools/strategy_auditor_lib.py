import datetime
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from core import storage as _storage


_PACKAGE_ROOT = Path(__file__).resolve().parents[1]

# Package seed fallback; runtime calls prefer BINARYBOT_BASE_DIR/config first.
_DEFAULT_SETTINGS_PATH = str(_PACKAGE_ROOT / "config" / "intelligence_settings.json")
SETTINGS_PATH = _DEFAULT_SETTINGS_PATH
EVENT_SCHEMA_PATH = os.path.join(
    str(_PACKAGE_ROOT),
    "schema",
    "event_schema.json",
)

CANONICAL_V3_SCHEMA_VERSION = "3.0.0"
CANONICAL_V3_DECISION_EVENT = "decision_evaluated"
LEGACY_DECISION_EVENT = "decision"
LEGACY_COMPATIBILITY_MODE = "LEGACY_DECISION"
PRIMARY_COMPATIBILITY_MODE = "CANONICAL_V3"
UNKNOWN_VALUE = "UNKNOWN"
_NORMALIZATION_SAMPLE_LIMIT = 10
_EVENT_SCHEMA_CACHE: Optional[Dict[str, Any]] = None
_LEGACY_BINARYBOT_PREFIX = Path("/opt/binarybot")
_LEGACY_SETTING_DEFAULTS: Dict[str, str] = {
    "reports.output_dir": "/opt/binarybot/analytics/reports",
    "reports.cache_dir": "/opt/binarybot/analytics/cache",
    "sources.engine_events": "/opt/binarybot/observability/engine_events.jsonl",
    "sources.fsm_events": "/opt/binarybot/observability/fsm_events.jsonl",
    "sources.distribution_events": "/opt/binarybot/observability/distribution_events.jsonl",
    "sources.error_events": "/opt/binarybot/observability/error_events.jsonl",
    "sources.outcomes": "/opt/binarybot/outcomes/outcomes.jsonl",
}
_SOURCE_DEFAULTS: Dict[str, str] = {
    "engine_events": "observability/engine_events.jsonl",
    "fsm_events": "observability/fsm_events.jsonl",
    "distribution_events": "observability/distribution_events.jsonl",
    "error_events": "observability/error_events.jsonl",
    "outcomes": "outcomes/outcomes.jsonl",
}
_SOURCE_ENV_OVERRIDES: Dict[str, str] = {
    "engine_events": "ENGINE_EVENTS_LOG",
    "fsm_events": "FSM_EVENTS_LOG",
    "distribution_events": "DIST_EVENTS_LOG",
    "error_events": "ERROR_EVENTS_LOG",
    "outcomes": "OUTCOMES_LOG",
}


class StrategyAuditorSettingsError(RuntimeError):
    """Raised when strategy auditor settings cannot be safely loaded."""


def _runtime_settings_path() -> str:
    base = Path(_storage.base_dir())
    return str(base / "config" / "intelligence_settings.json")


def _resolve_settings_path(path: Optional[str] = None) -> Tuple[str, str, bool]:
    if path:
        return str(Path(path).expanduser()), "argument", True

    env_path = os.getenv("STRATEGY_AUDITOR_SETTINGS", "").strip()
    if env_path:
        return str(Path(env_path).expanduser()), "STRATEGY_AUDITOR_SETTINGS", True

    runtime_path = _runtime_settings_path()
    if os.path.exists(runtime_path):
        return runtime_path, "runtime_base_config", False

    return _DEFAULT_SETTINGS_PATH, "package_seed", False


def _load_json_object(path: str, *, explicit: bool, source: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        qualifier = "explicit " if explicit else ""
        raise StrategyAuditorSettingsError(
            f"Strategy auditor {qualifier}settings file not found: {path}. "
            "Set STRATEGY_AUDITOR_SETTINGS env var to override the path."
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except json.JSONDecodeError as exc:
        raise StrategyAuditorSettingsError(
            f"Strategy auditor settings file is invalid JSON ({source})."
        ) from exc
    if not isinstance(settings, dict):
        raise StrategyAuditorSettingsError("Strategy auditor settings must be a JSON object")
    return settings


def _base_dir() -> Path:
    return Path(_storage.base_dir()).resolve(strict=False)


def _clean_path(path: Path) -> str:
    return str(path.expanduser().resolve(strict=False))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return path == root


def _has_traversal(path: Path) -> bool:
    return any(part == ".." for part in path.parts)


def _is_known_legacy_default(label: str, raw: str) -> bool:
    expected = _LEGACY_SETTING_DEFAULTS.get(label)
    return expected is not None and raw.rstrip("/") == expected


def _path_from_setting(raw: Any, *, base_dir: Path, label: str, origin: str = "settings") -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise StrategyAuditorSettingsError(f"{label} must be a non-empty path string")

    raw_path = raw.strip()
    if "\x00" in raw_path:
        raise StrategyAuditorSettingsError(f"{label} contains an invalid path character")

    candidate = Path(raw_path).expanduser()
    if _has_traversal(candidate):
        raise StrategyAuditorSettingsError(f"{label} must not contain path traversal")

    if origin == "env" and not candidate.is_absolute():
        raise StrategyAuditorSettingsError(f"{label} must be an absolute path when supplied by environment")

    if candidate.is_absolute():
        if origin == "settings" and _is_known_legacy_default(label, raw_path):
            relative = candidate.relative_to(_LEGACY_BINARYBOT_PREFIX)
            return _clean_path(base_dir / relative)
        return _clean_path(candidate)

    resolved = (base_dir / candidate).resolve(strict=False)
    if not _is_relative_to(resolved, base_dir):
        raise StrategyAuditorSettingsError(f"{label} must resolve under BINARYBOT_BASE_DIR")
    return str(resolved)


def _env_path(name: str) -> Optional[str]:
    value = os.getenv(name, "").strip()
    return value or None


def _bool_setting(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if value is None:
        return default
    return bool(value)


def load_settings(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load strategy auditor settings.

    Precedence:
    1. explicit ``path`` argument
    2. STRATEGY_AUDITOR_SETTINGS
    3. BINARYBOT_BASE_DIR/config/intelligence_settings.json when present
    4. packaged config/intelligence_settings.json seed

    Settings may use logical relative paths; they resolve under storage.base_dir().
    Legacy /opt/binarybot paths are mapped to the active base dir to avoid writes
    leaking outside the configured runtime volume.
    """
    resolved, source, explicit = _resolve_settings_path(path)
    settings = _load_json_object(resolved, explicit=explicit, source=source)
    return _apply_runtime_path_overrides(settings)


def _apply_runtime_path_overrides(settings: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(settings, dict):
        raise StrategyAuditorSettingsError("Strategy auditor settings must be a JSON object")

    normalized = dict(settings)
    base_dir = _base_dir()

    reports = dict(normalized.get("reports", {}) or {})
    analytics_dir = _env_path("ANALYTICS_DIR")
    if analytics_dir:
        analytics_root = _path_from_setting(
            analytics_dir,
            base_dir=base_dir,
            label="ANALYTICS_DIR",
            origin="env",
        )
        reports["output_dir"] = os.path.join(analytics_root, "reports")
        reports["cache_dir"] = os.path.join(analytics_root, "cache")
    else:
        reports["output_dir"] = _path_from_setting(
            reports.get("output_dir", "analytics/reports"),
            base_dir=base_dir,
            label="reports.output_dir",
            origin="settings",
        )
        reports["cache_dir"] = _path_from_setting(
            reports.get("cache_dir", "analytics/cache"),
            base_dir=base_dir,
            label="reports.cache_dir",
            origin="settings",
        )
    reports["enabled"] = _bool_setting(reports.get("enabled"), True)
    reports["write_json"] = _bool_setting(reports.get("write_json"), True)
    reports["write_markdown"] = _bool_setting(reports.get("write_markdown"), True)
    normalized["reports"] = reports

    sources = dict(normalized.get("sources", {}) or {})
    obs_dir = _env_path("OBS_DIR")
    if obs_dir:
        obs_root = _path_from_setting(obs_dir, base_dir=base_dir, label="OBS_DIR", origin="env")
        sources.setdefault("engine_events", os.path.join(obs_root, "engine_events.jsonl"))
        sources.setdefault("fsm_events", os.path.join(obs_root, "fsm_events.jsonl"))
        sources.setdefault("distribution_events", os.path.join(obs_root, "distribution_events.jsonl"))
        sources.setdefault("error_events", os.path.join(obs_root, "error_events.jsonl"))

    for key, default_path in _SOURCE_DEFAULTS.items():
        raw_path = _env_path(_SOURCE_ENV_OVERRIDES[key])
        if raw_path is None and obs_dir and key != "outcomes":
            filename = {
                "engine_events": "engine_events.jsonl",
                "fsm_events": "fsm_events.jsonl",
                "distribution_events": "distribution_events.jsonl",
                "error_events": "error_events.jsonl",
            }[key]
            raw_path = os.path.join(
                _path_from_setting(obs_dir, base_dir=base_dir, label="OBS_DIR", origin="env"),
                filename,
            )
        if raw_path is None:
            raw_path = sources.get(key, default_path)
            origin = "settings"
        else:
            origin = "env"
        sources[key] = _path_from_setting(
            raw_path,
            base_dir=base_dir,
            label=f"sources.{key}",
            origin=origin,
        )

    normalized["sources"] = sources

    return normalized


def _read_jsonl(path: str) -> Tuple[List[Dict[str, Any]], int]:
    """
    Read a JSONL file and return (valid_records, invalid_count).

    Invalid lines are counted and reported, not silently dropped.
    Missing files return ([], 0) without error.
    """
    records: List[Dict[str, Any]] = []
    invalid_count = 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if not isinstance(obj, dict):
                        invalid_count += 1
                        continue
                    records.append(obj)
                except json.JSONDecodeError:
                    invalid_count += 1
    except FileNotFoundError:
        return [], 0

    return records, invalid_count


def load_all_events(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load all event sources defined in settings["sources"].

    Returns the event collections plus per-source invalid record counts.
    """
    sources = settings["sources"]

    engine_records, engine_invalid = _read_jsonl(sources["engine_events"])
    fsm_records, fsm_invalid = _read_jsonl(sources["fsm_events"])
    distribution_records, distribution_invalid = _read_jsonl(sources["distribution_events"])
    error_records, error_invalid = _read_jsonl(sources["error_events"])

    outcomes, outcomes_invalid = _read_jsonl(sources["outcomes"])

    return {
        "engine": engine_records,
        "fsm": fsm_records,
        "distribution": distribution_records,
        "errors": error_records,
        "outcomes": outcomes,
        "invalid_counts": {
            "engine": engine_invalid,
            "fsm": fsm_invalid,
            "distribution": distribution_invalid,
            "errors": error_invalid,
            "outcomes": outcomes_invalid,
        },
    }


def _load_event_schema() -> Dict[str, Any]:
    global _EVENT_SCHEMA_CACHE
    if _EVENT_SCHEMA_CACHE is None:
        with open(EVENT_SCHEMA_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        _EVENT_SCHEMA_CACHE = loaded if isinstance(loaded, dict) else {}
    return _EVENT_SCHEMA_CACHE


def _schema_event_types() -> Dict[str, Dict[str, Any]]:
    schema = _load_event_schema()
    event_types = schema.get("event_types")
    return dict(event_types) if isinstance(event_types, dict) else {}


def _recognized_event_types() -> set[str]:
    return set(_schema_event_types())


def _supported_schema_versions() -> set[str]:
    schema = _load_event_schema()
    envelope = _dict(schema.get("envelope"))
    required = _dict(envelope.get("required"))
    version_spec = _dict(required.get("schema_version"))
    versions = version_spec.get("enum")
    if isinstance(versions, list):
        return {str(value) for value in versions if str(value).strip()}
    return {CANONICAL_V3_SCHEMA_VERSION}


def _compatibility_template() -> Dict[str, Any]:
    return {
        "primary_mode": PRIMARY_COMPATIBILITY_MODE,
        "canonical_v3_decision_events_seen": 0,
        "legacy_decision_events_seen": 0,
        "recognized_non_decision_event_counts": {},
        "supporting_event_counts": {},
        "normalized_decisions": 0,
        "normalized_by_compatibility_mode": {
            PRIMARY_COMPATIBILITY_MODE: 0,
            LEGACY_COMPATIBILITY_MODE: 0,
        },
        "normalized_decisions_with_warnings": 0,
        "normalization_warnings": {},
        "unsupported_event_types": {},
        "unsupported_schema_versions": {},
        "malformed_or_unusable_decision_events": 0,
        "malformed_examples": [],
        "conflicting_field_events": 0,
        "conflicting_fields": {},
        "duplicate_events_suppressed": 0,
        "deduplication": {
            "primary_identity": "event_id",
            "legacy_without_event_id": "not_deduplicated",
            "canonical_precedence_over_legacy": True,
        },
    }


def _text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _float_or_none(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_of_text(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for item in values:
        text = _text(str(item)) if item is not None else None
        if text:
            out.append(text)
    return out


def _split_reason_text(reason: Optional[str]) -> List[str]:
    if not reason:
        return []
    return [part.strip() for part in reason.split(";") if part.strip()]


def _increment(counter: Dict[str, Any], key: str, amount: int = 1) -> None:
    counter[key] = int(counter.get(key, 0)) + amount


def _event_brief(event: Dict[str, Any]) -> str:
    event_type = event.get("event_type") or "UNKNOWN_TYPE"
    schema_version = event.get("schema_version") or "UNKNOWN_SCHEMA"
    event_id = event.get("event_id") or "NO_EVENT_ID"
    signal_id = event.get("signal_id") or _dict(event.get("data")).get("signal_id") or "NO_SIGNAL_ID"
    return f"{event_type}@{schema_version} event_id={event_id} signal_id={signal_id}"


def _record_malformed(compatibility: Dict[str, Any], event: Dict[str, Any], reason: str) -> None:
    compatibility["malformed_or_unusable_decision_events"] += 1
    _increment(compatibility["normalization_warnings"], reason)
    if len(compatibility["malformed_examples"]) < _NORMALIZATION_SAMPLE_LIMIT:
        compatibility["malformed_examples"].append(f"{reason}: {_event_brief(event)}")


def _record_warning(compatibility: Dict[str, Any], warning: str) -> None:
    _increment(compatibility["normalization_warnings"], warning)


def _record_conflicts(compatibility: Dict[str, Any], issues: Iterable[str]) -> None:
    conflicts = [issue for issue in issues if issue.startswith("conflicting_")]
    if not conflicts:
        return
    compatibility["conflicting_field_events"] += 1
    for issue in conflicts:
        _increment(compatibility["conflicting_fields"], issue.replace("conflicting_", ""))


def _resolve_authoritative_text(
    compatibility: Dict[str, Any],
    issues: List[str],
    field_name: str,
    authorities: List[Tuple[str, Any]],
) -> Optional[str]:
    authoritative: Optional[str] = None
    for _source_name, raw_value in authorities:
        candidate = _text(raw_value)
        if candidate is None:
            continue
        if authoritative is None:
            authoritative = candidate
            continue
        if candidate != authoritative:
            issues.append(f"conflicting_{field_name}")
            _record_warning(compatibility, f"conflicting_{field_name}")
            return authoritative
    return authoritative


def _resolve_authoritative_float(
    compatibility: Dict[str, Any],
    issues: List[str],
    field_name: str,
    authorities: List[Tuple[str, Any]],
) -> Optional[float]:
    authoritative: Optional[float] = None
    for _source_name, raw_value in authorities:
        candidate = _float_or_none(raw_value)
        if candidate is None:
            continue
        if authoritative is None:
            authoritative = candidate
            continue
        if candidate != authoritative:
            issues.append(f"conflicting_{field_name}")
            _record_warning(compatibility, f"conflicting_{field_name}")
            return authoritative
    return authoritative


def _canonical_reject_reasons(data: Dict[str, Any], decision_object: Dict[str, Any]) -> List[str]:
    reject = _dict(decision_object.get("reject"))
    hard_blockers = _list_of_text(reject.get("hard_blockers"))
    if hard_blockers:
        return hard_blockers

    primary_reason = _text(reject.get("reason"))
    if primary_reason:
        split = _split_reason_text(primary_reason)
        return split or [primary_reason]

    direct_reason = _text(data.get("reject_reason") or data.get("rejected_reason"))
    if direct_reason:
        split = _split_reason_text(direct_reason)
        return split or [direct_reason]

    gates = _dict(data.get("gates"))
    for gate_name, gate_payload in gates.items():
        gate_data = _dict(gate_payload)
        reason = _text(gate_data.get("reason"))
        if reason:
            split = _split_reason_text(reason)
            return split or [reason]
        if gate_data.get("ok") is False:
            gate_name_text = _text(str(gate_name))
            if gate_name_text:
                return [gate_name_text]

    return []


def _primary_reject_reason_from_list(reject_reasons: List[str]) -> Optional[str]:
    return reject_reasons[0] if reject_reasons else None


def _legacy_reject_reasons(data: Dict[str, Any]) -> List[str]:
    direct_reason = _text(data.get("reject_reason") or data.get("rejected_reason"))
    if direct_reason:
        split = _split_reason_text(direct_reason)
        return split or [direct_reason]

    gates = _dict(data.get("gates"))
    for gate_name, gate_payload in gates.items():
        gate_data = _dict(gate_payload)
        reason = _text(gate_data.get("reason"))
        if reason:
            split = _split_reason_text(reason)
            return split or [reason]
        if gate_data.get("ok") is False:
            gate_name_text = _text(str(gate_name))
            if gate_name_text:
                return [gate_name_text]

    return []


def _normalize_v3_decision_event(event: Dict[str, Any], compatibility: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if _text(event.get("schema_version")) != CANONICAL_V3_SCHEMA_VERSION:
        schema_key = f"{CANONICAL_V3_DECISION_EVENT}@{event.get('schema_version') or UNKNOWN_VALUE}"
        _increment(compatibility["unsupported_schema_versions"], schema_key)
        return None

    data = _dict(event.get("data"))
    decision_object = _dict(data.get("decision_object"))
    setup = _dict(decision_object.get("setup"))
    score = _dict(decision_object.get("score"))

    event_id = _text(event.get("event_id"))
    decision_kind = _text(data.get("decision_kind"))
    strategy = _text(data.get("strategy"))
    strategy_version = _text(data.get("strategy_version"))
    canonical_spec = _text(data.get("canonical_spec"))
    issues: List[str] = []
    direction = _resolve_authoritative_text(
        compatibility,
        issues,
        "direction",
        [
            ("data.direction", data.get("direction")),
            ("decision_object.setup.direction", setup.get("direction")),
        ],
    )

    if event_id is None:
        _record_malformed(compatibility, event, "missing_event_id")
        return None
    if decision_kind is None:
        _record_malformed(compatibility, event, "missing_decision_kind")
        return None
    if not decision_object:
        _record_malformed(compatibility, event, "missing_decision_object")
        return None

    signal_id = _resolve_authoritative_text(
        compatibility,
        issues,
        "signal_id",
        [
            ("signal_id", event.get("signal_id")),
            ("data.signal_id", data.get("signal_id")),
            ("decision_object.signal_id", decision_object.get("signal_id")),
        ],
    )
    setup_correlation_id = _resolve_authoritative_text(
        compatibility,
        issues,
        "setup_correlation_id",
        [
            ("setup_correlation_id", event.get("setup_correlation_id")),
            ("decision_object.setup.cycle_id", setup.get("cycle_id")),
        ],
    )
    symbol = _resolve_authoritative_text(
        compatibility,
        issues,
        "symbol",
        [
            ("symbol", event.get("symbol")),
            ("decision_object.setup.symbol", setup.get("symbol")),
            ("data.symbol", data.get("symbol")),
        ],
    )
    timeframe = _resolve_authoritative_text(
        compatibility,
        issues,
        "timeframe",
        [
            ("timeframe", event.get("timeframe")),
            ("decision_object.setup.timeframe", setup.get("timeframe")),
            ("data.timeframe", data.get("timeframe")),
        ],
    )
    stage = _resolve_authoritative_text(
        compatibility,
        issues,
        "stage",
        [
            ("stage", event.get("stage")),
            ("data.stage", data.get("stage")),
        ],
    )
    score_total = _resolve_authoritative_float(
        compatibility,
        issues,
        "score_total",
        [
            ("data.score_total", data.get("score_total")),
            ("decision_object.score.total", score.get("total")),
        ],
    )
    score_tier = _resolve_authoritative_text(
        compatibility,
        issues,
        "score_tier",
        [
            ("data.score_tier", data.get("score_tier")),
            ("decision_object.score.tier", score.get("tier")),
        ],
    )
    candle_ts = data.get("candle_ts")
    if candle_ts is None:
        candle_ts = setup.get("evaluated_ts")
    elif setup.get("evaluated_ts") is not None and setup.get("evaluated_ts") != candle_ts:
        issues.append("conflicting_candle_ts")
        _record_warning(compatibility, "conflicting_candle_ts")

    if strategy is None:
        issues.append("missing_strategy")
        _record_warning(compatibility, "missing_strategy")
    if strategy_version is None:
        issues.append("missing_strategy_version")
        _record_warning(compatibility, "missing_strategy_version")
    if canonical_spec is None:
        issues.append("missing_canonical_spec")
        _record_warning(compatibility, "missing_canonical_spec")
    if direction is None:
        issues.append("missing_direction")
        _record_warning(compatibility, "missing_direction")
    if symbol is None:
        issues.append("missing_symbol")
        _record_warning(compatibility, "missing_symbol")
    if timeframe is None:
        issues.append("missing_timeframe")
        _record_warning(compatibility, "missing_timeframe")
    if score_total is None:
        issues.append("missing_score_total")
        _record_warning(compatibility, "missing_score_total")

    reject_reasons = _canonical_reject_reasons(data, decision_object)
    if decision_kind == "REJECT" and not reject_reasons:
        issues.append("missing_reject_reason")
        _record_warning(compatibility, "missing_reject_reason")
    primary_reject_reason = _primary_reject_reason_from_list(reject_reasons)

    record = {
        "source_event_type": CANONICAL_V3_DECISION_EVENT,
        "source_schema_version": CANONICAL_V3_SCHEMA_VERSION,
        "compatibility_mode": PRIMARY_COMPATIBILITY_MODE,
        "event_id": event_id,
        "signal_id": signal_id,
        "setup_correlation_id": setup_correlation_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "stage": stage,
        "decision_kind": decision_kind,
        "score_total": score_total,
        "score_tier": score_tier,
        "strategy": strategy,
        "strategy_version": strategy_version,
        "canonical_spec": canonical_spec,
        "direction": direction,
        "candle_ts": candle_ts,
        "primary_reject_reason": primary_reject_reason,
        "reject_reason": primary_reject_reason,
        "reject_reasons": reject_reasons,
        "decision_object": decision_object,
        "trade_physics": _dict(data.get("trade_physics")),
        "raw_event": event,
        "issues": issues,
    }
    _record_conflicts(compatibility, issues)
    return record


def _normalize_legacy_decision_event(event: Dict[str, Any], compatibility: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    schema_version = _text(event.get("schema_version"))
    if schema_version not in {None, "2.0.0", CANONICAL_V3_SCHEMA_VERSION}:
        schema_key = f"{LEGACY_DECISION_EVENT}@{schema_version}"
        _increment(compatibility["unsupported_schema_versions"], schema_key)
        return None

    data = _dict(event.get("data"))
    decision_kind = _text(data.get("decision_kind"))
    if decision_kind is None:
        _record_malformed(compatibility, event, "missing_decision_kind")
        return None

    issues: List[str] = []
    signal_id = _resolve_authoritative_text(
        compatibility,
        issues,
        "legacy_signal_id",
        [
            ("signal_id", event.get("signal_id")),
            ("data.signal_id", data.get("signal_id")),
        ],
    )
    symbol = _resolve_authoritative_text(
        compatibility,
        issues,
        "legacy_symbol",
        [
            ("symbol", event.get("symbol")),
            ("data.symbol", data.get("symbol")),
        ],
    )
    timeframe = _resolve_authoritative_text(
        compatibility,
        issues,
        "legacy_timeframe",
        [
            ("timeframe", event.get("timeframe")),
            ("data.timeframe", data.get("timeframe")),
        ],
    )
    score_total = _resolve_authoritative_float(
        compatibility,
        issues,
        "legacy_score_total",
        [
            ("data.score_total", data.get("score_total")),
        ],
    )

    if symbol is None:
        issues.append("missing_symbol")
        _record_warning(compatibility, "missing_symbol")
    if score_total is None:
        issues.append("missing_score_total")
        _record_warning(compatibility, "missing_score_total")

    reject_reasons = _legacy_reject_reasons(data)
    if decision_kind == "REJECT" and not reject_reasons:
        issues.append("missing_reject_reason")
        _record_warning(compatibility, "missing_reject_reason")
    primary_reject_reason = _primary_reject_reason_from_list(reject_reasons)

    record = {
        "source_event_type": LEGACY_DECISION_EVENT,
        "source_schema_version": schema_version or UNKNOWN_VALUE,
        "compatibility_mode": LEGACY_COMPATIBILITY_MODE,
        "event_id": _text(event.get("event_id")),
        "signal_id": signal_id,
        "setup_correlation_id": None,
        "symbol": symbol,
        "timeframe": timeframe,
        "stage": _text(event.get("stage") or data.get("stage")),
        "decision_kind": decision_kind,
        "score_total": score_total,
        "score_tier": _text(data.get("score_tier")),
        "strategy": None,
        "strategy_version": None,
        "canonical_spec": None,
        "direction": _text(data.get("direction") or event.get("direction")),
        "candle_ts": data.get("candle_ts"),
        "primary_reject_reason": primary_reject_reason,
        "reject_reason": primary_reject_reason,
        "reject_reasons": reject_reasons,
        "decision_object": _dict(data.get("decision_object")),
        "trade_physics": _dict(data.get("trade_physics")),
        "raw_event": event,
        "issues": issues,
    }
    _record_conflicts(compatibility, issues)
    return record


def _candidate_priority(record: Dict[str, Any]) -> int:
    return 2 if record.get("compatibility_mode") == PRIMARY_COMPATIBILITY_MODE else 1


def _finalize_compatibility(compatibility: Dict[str, Any], decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    compatibility["normalized_decisions"] = len(decisions)
    for decision in decisions:
        mode = str(decision.get("compatibility_mode") or LEGACY_COMPATIBILITY_MODE)
        compatibility["normalized_by_compatibility_mode"][mode] = (
            compatibility["normalized_by_compatibility_mode"].get(mode, 0) + 1
        )
        if decision.get("issues"):
            compatibility["normalized_decisions_with_warnings"] += 1
    compatibility["recognized_non_decision_event_counts"] = dict(sorted(compatibility["recognized_non_decision_event_counts"].items()))
    compatibility["supporting_event_counts"] = dict(sorted(compatibility["supporting_event_counts"].items()))
    compatibility["unsupported_event_types"] = dict(sorted(compatibility["unsupported_event_types"].items()))
    compatibility["unsupported_schema_versions"] = dict(sorted(compatibility["unsupported_schema_versions"].items()))
    compatibility["normalization_warnings"] = dict(sorted(compatibility["normalization_warnings"].items()))
    compatibility["conflicting_fields"] = dict(sorted(compatibility["conflicting_fields"].items()))
    return compatibility


def normalize_decision_events(events: Dict[str, Any] | List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if isinstance(events, dict):
        engine_events = events.get("engine", [])
        supporting_sources = {
            "engine": events.get("engine", []),
            "fsm": events.get("fsm", []),
            "distribution": events.get("distribution", []),
        }
    else:
        engine_events = events
        supporting_sources = {"engine": events}

    compatibility = _compatibility_template()
    recognized_event_types = _recognized_event_types()
    supported_schema_versions = _supported_schema_versions()
    candidates_by_event_id: Dict[str, Dict[str, Any]] = {}
    unkeyed_candidates: List[Dict[str, Any]] = []

    for source_events in supporting_sources.values():
        for event in source_events if isinstance(source_events, list) else []:
            if not isinstance(event, dict):
                continue
            event_type = _text(event.get("event_type"))
            if event_type in recognized_event_types and event_type not in {CANONICAL_V3_DECISION_EVENT, LEGACY_DECISION_EVENT}:
                schema_version = _text(event.get("schema_version"))
                if schema_version not in {None, *supported_schema_versions}:
                    _increment(
                        compatibility["unsupported_schema_versions"],
                        f"{event_type}@{schema_version}",
                    )
                else:
                    _increment(compatibility["recognized_non_decision_event_counts"], event_type)
                    _increment(compatibility["supporting_event_counts"], event_type)

    for event in engine_events if isinstance(engine_events, list) else []:
        if not isinstance(event, dict):
            continue

        event_type = _text(event.get("event_type"))
        if event_type is None:
            _increment(compatibility["unsupported_event_types"], UNKNOWN_VALUE)
            continue

        record: Optional[Dict[str, Any]] = None
        if event_type == CANONICAL_V3_DECISION_EVENT:
            compatibility["canonical_v3_decision_events_seen"] += 1
            record = _normalize_v3_decision_event(event, compatibility)
        elif event_type == LEGACY_DECISION_EVENT:
            compatibility["legacy_decision_events_seen"] += 1
            record = _normalize_legacy_decision_event(event, compatibility)
        elif event_type not in recognized_event_types:
            _increment(compatibility["unsupported_event_types"], event_type)

        if record is None:
            continue

        event_id = record.get("event_id")
        if isinstance(event_id, str) and event_id:
            existing = candidates_by_event_id.get(event_id)
            if existing is None:
                candidates_by_event_id[event_id] = record
            elif _candidate_priority(record) > _candidate_priority(existing):
                candidates_by_event_id[event_id] = record
                compatibility["duplicate_events_suppressed"] += 1
            else:
                compatibility["duplicate_events_suppressed"] += 1
        else:
            unkeyed_candidates.append(record)

    decisions = list(candidates_by_event_id.values()) + unkeyed_candidates
    decisions.sort(
        key=lambda record: (
            str(record.get("symbol") or ""),
            str(record.get("timeframe") or ""),
            int(record.get("candle_ts")) if isinstance(record.get("candle_ts"), int) and not isinstance(record.get("candle_ts"), bool) else -1,
            str(record.get("event_id") or ""),
        )
    )
    return decisions, _finalize_compatibility(compatibility, decisions)


def filter_decision_events(engine_events):
    decisions, _compatibility = normalize_decision_events(engine_events)
    return decisions


def extract_reject_reason(event):
    primary_reason = _text(event.get("primary_reject_reason"))
    if primary_reason:
        return primary_reason

    reasons = event.get("reject_reasons")
    if isinstance(reasons, list):
        cleaned = [str(reason) for reason in reasons if str(reason).strip()]
        if cleaned:
            return cleaned[0]

    reason = _text(event.get("reject_reason"))
    if reason:
        return reason

    data = _dict(event.get("data"))
    decision_object = _dict(data.get("decision_object"))
    canonical_reasons = _canonical_reject_reasons(data, decision_object)
    if canonical_reasons:
        return canonical_reasons[0]

    legacy_reasons = _legacy_reject_reasons(data)
    if legacy_reasons:
        return legacy_reasons[0]

    return UNKNOWN_VALUE


def compute_decision_distribution(decisions):
    stats = Counter({
        "total": 0,
        "PRE": 0,
        "CONFIRM": 0,
        "OPEN_NOW": 0,
        "REJECT": 0,
        "NO_SIGNAL": 0,
    })

    for decision in decisions:
        stats["total"] += 1
        kind = _text(decision.get("decision_kind")) or UNKNOWN_VALUE
        stats[kind] += 1

    return dict(stats)


def compute_reject_distribution(decisions):
    reasons = defaultdict(int)

    for decision in decisions:
        kind = _text(decision.get("decision_kind"))
        if kind != "REJECT":
            continue

        reasons[extract_reject_reason(decision)] += 1

    return dict(reasons)


def compute_reject_reason_occurrences(decisions):
    reasons = defaultdict(int)

    for decision in decisions:
        kind = _text(decision.get("decision_kind"))
        if kind != "REJECT":
            continue

        raw_reasons = decision.get("reject_reasons")
        reject_reasons = [str(reason) for reason in raw_reasons if str(reason).strip()] if isinstance(raw_reasons, list) else []
        if not reject_reasons:
            reject_reasons = [extract_reject_reason(decision)]

        for reason in reject_reasons:
            reasons[reason] += 1

    return dict(reasons)


def compute_symbol_activity(decisions):
    symbols = defaultdict(int)

    for decision in decisions:
        symbol = _text(decision.get("symbol"))
        if not symbol:
            continue
        symbols[symbol] += 1

    return dict(symbols)


def compute_average_score(decisions):
    scores = []

    for decision in decisions:
        score = _float_or_none(decision.get("score_total"))
        if score is not None:
            scores.append(score)

    if not scores:
        return {
            "avg": None,
            "min": None,
            "max": None,
        }

    return {
        "avg": sum(scores) / len(scores),
        "min": min(scores),
        "max": max(scores),
    }


def compute_heatmap(decisions, settings):
    buckets = settings["heatmap"]["score_buckets"]

    heatmap = {}

    for bucket in buckets:
        label = f"{bucket[0]}-{bucket[1]}"
        heatmap[label] = {
            "count": 0,
            "pre": 0,
            "confirms": 0,
            "rejects": 0,
            "opens": 0,
            "no_signal": 0,
            "other": 0,
        }

    for decision in decisions:
        score = _float_or_none(decision.get("score_total"))
        if score is None:
            continue

        for bucket in buckets:
            lower, upper = bucket
            in_bucket = lower <= score < upper or (score == upper and upper == buckets[-1][1])
            if not in_bucket:
                continue

            label = f"{lower}-{upper}"
            heatmap[label]["count"] += 1

            kind = _text(decision.get("decision_kind")) or UNKNOWN_VALUE
            if kind == "PRE":
                heatmap[label]["pre"] += 1
            elif kind == "CONFIRM":
                heatmap[label]["confirms"] += 1
            elif kind == "REJECT":
                heatmap[label]["rejects"] += 1
            elif kind == "OPEN_NOW":
                heatmap[label]["opens"] += 1
            elif kind == "NO_SIGNAL":
                heatmap[label]["no_signal"] += 1
            else:
                heatmap[label]["other"] += 1
            break

    return heatmap


def detect_bottleneck(reject_distribution, settings):
    if not reject_distribution:
        return None

    total = sum(reject_distribution.values())

    if total == 0:
        return None

    dominant = max(reject_distribution, key=reject_distribution.get)

    share = reject_distribution[dominant] / total

    threshold = settings["bottleneck_detection"]["dominant_reject_share_threshold"]

    if share >= threshold:
        return {
            "reason": dominant,
            "share": share,
        }

    return None


def compute_symbol_health(decisions, settings):
    per_symbol = defaultdict(list)

    for decision in decisions:
        symbol = _text(decision.get("symbol"))
        if not symbol:
            continue
        per_symbol[symbol].append(decision)

    result = {}

    healthy_min = settings["symbol_health"]["healthy_pre_rate_min"]
    starved_max = settings["symbol_health"]["starved_pre_rate_max"]
    blocked_share = settings["symbol_health"]["blocked_same_reason_share_min"]

    for symbol, symbol_decisions in per_symbol.items():
        total = len(symbol_decisions)
        if total == 0:
            continue

        pre = 0
        rejects = defaultdict(int)

        for decision in symbol_decisions:
            kind = _text(decision.get("decision_kind"))

            if kind == "PRE":
                pre += 1

            if kind == "REJECT":
                rejects[extract_reject_reason(decision)] += 1

        pre_rate = pre / total

        dominant_reason = None
        dominant_share = 0

        if rejects:
            dominant_reason = max(rejects, key=rejects.get)
            dominant_share = rejects[dominant_reason] / sum(rejects.values())

        status = "NORMAL"

        if pre_rate < starved_max:
            status = "STARVED"

        if dominant_share >= blocked_share:
            status = "BLOCKED"

        if pre_rate >= healthy_min:
            status = "HEALTHY"

        result[symbol] = {
            "total": total,
            "pre_rate": pre_rate,
            "dominant_reject": dominant_reason,
            "dominant_reject_share": dominant_share,
            "status": status,
        }

    return result


def _compatibility_limitations(
    engine_events: List[Dict[str, Any]],
    compatibility: Dict[str, Any],
) -> List[str]:
    limitations: List[str] = []

    if not engine_events:
        return ["No engine events found."]

    if compatibility["normalized_decisions"] == 0:
        if compatibility["unsupported_schema_versions"]:
            limitations.append(
                "Engine events exist, but recognized decision events used unsupported schema versions."
            )
        elif compatibility["canonical_v3_decision_events_seen"] > 0 or compatibility["legacy_decision_events_seen"] > 0:
            limitations.append(
                "Decision-like events were observed, but none were usable after canonical/legacy compatibility checks."
            )
        else:
            limitations.append(
                "Engine events exist, but no recognized canonical decision events were found."
            )

    if compatibility["legacy_decision_events_seen"] > 0:
        limitations.append("Legacy `decision` compatibility was used for part of the report input.")

    if compatibility["unsupported_schema_versions"]:
        limitations.append("Unsupported decision schema versions were observed and excluded from metrics.")

    if compatibility["malformed_or_unusable_decision_events"] > 0:
        limitations.append("Some decision events were malformed or unusable and were excluded from metrics.")

    if compatibility["conflicting_field_events"] > 0:
        limitations.append("Some normalized decisions contained conflicting field evidence; primary canonical precedence was applied.")

    return limitations


def build_report(
    events: Dict[str, Any],
    settings: Dict[str, Any],
    *,
    report_date: Optional[str] = None,
    scheduling_metadata: Optional[Dict[str, Any]] = None,
    analysis_window: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build the daily strategy audit report from loaded events.

    The report includes:
    - input_sources: number of valid and invalid records per source
    - period: the UTC date analyzed
    - findings derived only from valid, explicitly normalized decision events
    - Does not mutate runtime config or live strategy parameters.
    """
    decisions, compatibility = normalize_decision_events(events)

    decision_distribution = compute_decision_distribution(decisions)

    reject_distribution = compute_reject_distribution(decisions)
    reject_reason_occurrences = compute_reject_reason_occurrences(decisions)

    symbol_activity = compute_symbol_activity(decisions)

    score_stats = compute_average_score(decisions)

    heatmap = compute_heatmap(decisions, settings)

    bottleneck = detect_bottleneck(reject_distribution, settings)

    symbol_health = compute_symbol_health(decisions, settings)

    now = report_date or datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    invalid_counts = events.get("invalid_counts", {})

    limitations = _compatibility_limitations(events.get("engine", []), compatibility)
    if scheduling_metadata and scheduling_metadata.get("mode") == "scheduled":
        limitations = list(limitations)
        limitations.append(
            "Scheduled audit currently aggregates all available source history; "
            "analysis_window.scope=all_available_history."
        )

    report: Dict[str, Any] = {
        "date": now,
        "input_sources": {
            "engine_events": {
                "valid": len(events.get("engine", [])),
                "invalid": invalid_counts.get("engine", 0),
            },
            "fsm_events": {
                "valid": len(events.get("fsm", [])),
                "invalid": invalid_counts.get("fsm", 0),
            },
            "distribution_events": {
                "valid": len(events.get("distribution", [])),
                "invalid": invalid_counts.get("distribution", 0),
            },
            "error_events": {
                "valid": len(events.get("errors", [])),
                "invalid": invalid_counts.get("errors", 0),
            },
            "outcomes": {
                "valid": len(events.get("outcomes", [])),
                "invalid": invalid_counts.get("outcomes", 0),
            },
        },
        "event_compatibility": compatibility,
        "decisions": decision_distribution["total"],
        "decision_kind_counts": {
            key: value
            for key, value in decision_distribution.items()
            if key != "total"
        },
        "pre": decision_distribution["PRE"],
        "confirm": decision_distribution["CONFIRM"],
        "open_now": decision_distribution["OPEN_NOW"],
        "rejects": decision_distribution["REJECT"],
        "no_signal": decision_distribution["NO_SIGNAL"],
        "avg_score": score_stats["avg"],
        "min_score": score_stats["min"],
        "max_score": score_stats["max"],
        "top_reject_reasons": reject_distribution,
        "reject_reason_occurrences": reject_reason_occurrences,
        "symbol_activity": symbol_activity,
        "heatmap": heatmap,
        "bottleneck": bottleneck,
        "symbol_health": symbol_health,
        "limitations": limitations,
    }
    if analysis_window is not None:
        report["analysis_window"] = dict(analysis_window)
    if scheduling_metadata is not None:
        report["scheduling"] = dict(scheduling_metadata)

    return report


def resolve_reports_dir(settings: Optional[Dict[str, Any]] = None) -> str:
    if settings is not None:
        reports = dict(settings.get("reports", {}) or {})
        output_dir = reports.get("output_dir")
        if isinstance(output_dir, str) and output_dir.strip():
            return _clean_path(Path(output_dir))
    loaded = load_settings()
    return str(loaded["reports"]["output_dir"])


def report_paths_for_date(report_date: str, settings: Dict[str, Any]) -> Dict[str, str]:
    output_dir = resolve_reports_dir(settings)
    return {
        "json": os.path.join(output_dir, f"daily_strategy_audit_{report_date}.json"),
        "markdown": os.path.join(output_dir, f"daily_strategy_audit_{report_date}.md"),
    }


def _fsync_dir(dir_path: str) -> None:
    try:
        fd = os.open(dir_path, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception:
        pass


def _stage_atomic_bytes(path: str, data: bytes) -> str:
    import tempfile

    dir_path = os.path.dirname(path) or "."
    os.makedirs(dir_path, exist_ok=True)
    suffix = os.path.splitext(path)[1] or ".tmp"
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=suffix, dir=dir_path)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        return tmp_path
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        finally:
            pass
        raise


def _replace_staged_artifact(tmp_path: str, final_path: str) -> None:
    os.replace(tmp_path, final_path)
    _fsync_dir(os.path.dirname(final_path) or ".")


def _write_atomic_bytes(path: str, data: bytes) -> None:
    tmp_path = _stage_atomic_bytes(path, data)
    try:
        _replace_staged_artifact(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def _render_markdown_report(report: Dict[str, Any]) -> str:
    compatibility = report.get("event_compatibility", {})
    content_parts = [
        "# Strategy Audit\n\n",
        f"Date: {report['date']}\n\n",
        "## Event Compatibility\n\n",
        json.dumps({
            "primary_mode": compatibility.get("primary_mode"),
            "canonical_v3_decision_events_seen": compatibility.get("canonical_v3_decision_events_seen"),
            "legacy_decision_events_seen": compatibility.get("legacy_decision_events_seen"),
            "recognized_non_decision_event_counts": compatibility.get("recognized_non_decision_event_counts"),
            "normalized_decisions": compatibility.get("normalized_decisions"),
            "normalized_by_compatibility_mode": compatibility.get("normalized_by_compatibility_mode"),
            "normalized_decisions_with_warnings": compatibility.get("normalized_decisions_with_warnings"),
            "supporting_event_counts": compatibility.get("supporting_event_counts"),
            "unsupported_schema_versions": compatibility.get("unsupported_schema_versions"),
            "unsupported_event_types": compatibility.get("unsupported_event_types"),
            "malformed_or_unusable_decision_events": compatibility.get("malformed_or_unusable_decision_events"),
            "duplicate_events_suppressed": compatibility.get("duplicate_events_suppressed"),
        }, indent=2),
        "\n\n## Decision Distribution\n\n",
        json.dumps({
            "PRE": report["pre"],
            "CONFIRM": report["confirm"],
            "OPEN_NOW": report["open_now"],
            "REJECT": report["rejects"],
            "NO_SIGNAL": report["no_signal"],
            "OTHER_KINDS": {
                key: value for key, value in report.get("decision_kind_counts", {}).items()
                if key not in {"PRE", "CONFIRM", "OPEN_NOW", "REJECT", "NO_SIGNAL"}
            },
        }, indent=2),
        "\n\n## Top Reject Reasons\n\n",
        json.dumps(report["top_reject_reasons"], indent=2),
        "\n\n## Reject Reason Occurrences\n\n",
        json.dumps(report["reject_reason_occurrences"], indent=2),
        "\n\n## Heatmap\n\n",
        json.dumps(report["heatmap"], indent=2),
        "\n\n## Bottleneck\n\n",
        json.dumps(report["bottleneck"], indent=2),
        "\n\n## Symbol Health\n\n",
        json.dumps(report["symbol_health"], indent=2),
    ]
    if report.get("analysis_window") is not None:
        content_parts.extend([
            "\n\n## Analysis Window\n\n",
            json.dumps(report["analysis_window"], indent=2),
        ])
    if report.get("scheduling") is not None:
        content_parts.extend([
            "\n\n## Scheduling\n\n",
            json.dumps(report["scheduling"], indent=2),
        ])
    limitations = report.get("limitations") or []
    if limitations:
        content_parts.extend([
            "\n\n## Limitations\n\n",
            "\n".join(f"- {item}" for item in limitations),
        ])
    return "".join(content_parts)


def write_reports(report: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, str]:
    """
    Write report outputs atomically.

    - JSON report: written atomically via tempfile + os.replace to prevent
      partial overwrites. Failed write preserves the last valid report.
    - Markdown report: written atomically in the same manner.
    - Does not mutate runtime config or live strategy parameters.
    """
    reports = dict(settings.get("reports", {}) or {})
    if not _bool_setting(reports.get("enabled"), True):
        raise StrategyAuditorSettingsError("Strategy auditor report output is disabled.")
    write_json = _bool_setting(reports.get("write_json"), True)
    write_markdown = _bool_setting(reports.get("write_markdown"), True)
    if not write_json and not write_markdown:
        raise StrategyAuditorSettingsError(
            "At least one strategy auditor report output must be enabled."
        )

    output_dir = resolve_reports_dir(settings)
    os.makedirs(output_dir, exist_ok=True)
    cache_dir = reports.get("cache_dir")
    if isinstance(cache_dir, str) and cache_dir.strip():
        os.makedirs(cache_dir, exist_ok=True)

    date = str(report["date"])
    paths = report_paths_for_date(date, settings)
    staged: List[Tuple[str, str, str]] = []
    replaced: List[Tuple[str, bool, bytes]] = []
    written: Dict[str, str] = {}

    try:
        if write_markdown:
            md_content = _render_markdown_report(report).encode("utf-8")
            staged.append(("markdown", paths["markdown"], _stage_atomic_bytes(paths["markdown"], md_content)))
        if write_json:
            json_content = (json.dumps(report, indent=2) + "\n").encode("utf-8")
            staged.append(("json", paths["json"], _stage_atomic_bytes(paths["json"], json_content)))

        for artifact_type, final_path, tmp_path in staged:
            existed = os.path.exists(final_path)
            previous = b""
            if existed:
                with open(final_path, "rb") as f:
                    previous = f.read()
            _replace_staged_artifact(tmp_path, final_path)
            replaced.append((final_path, existed, previous))
            written[artifact_type] = final_path

        return written
    except Exception:
        for final_path, existed, previous in reversed(replaced):
            try:
                if existed:
                    _write_atomic_bytes(final_path, previous)
                elif os.path.exists(final_path):
                    os.remove(final_path)
                    _fsync_dir(os.path.dirname(final_path) or ".")
            except Exception:
                pass
        raise
    finally:
        for _artifact_type, _final_path, tmp_path in staged:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
