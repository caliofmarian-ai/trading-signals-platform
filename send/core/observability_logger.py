from __future__ import annotations

import json
import os
import socket
import time
import uuid
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Union

try:
    from . import storage  # type: ignore
except Exception:
    storage = None

try:
    from . import telegram_targets  # type: ignore
except Exception:
    telegram_targets = None

try:
    from . import telegram_publisher  # type: ignore
except Exception:
    telegram_publisher = None


SCHEMA_VERSION = os.getenv("EVENT_SCHEMA_VERSION", "3.0.0")
SERVICE_NAME = os.getenv("SERVICE_NAME", "binarybot")
ENV_NAME = os.getenv("BOT_ENV", "prod")
BOT_VERSION = os.getenv("BOT_VERSION", "0.0.0")
GIT_SHA = ""

PACKAGE_ROOT = os.path.dirname(os.path.dirname(__file__))
EVENT_SCHEMA_PATH = os.path.join(PACKAGE_ROOT, "schema", "event_schema.json")

OBS_DIR = os.getenv("OBS_DIR", "/opt/binarybot/observability")
ENGINE_LOG = os.getenv("ENGINE_EVENTS_LOG", os.path.join(OBS_DIR, "engine_events.jsonl"))
FSM_LOG = os.getenv("FSM_EVENTS_LOG", os.path.join(OBS_DIR, "fsm_events.jsonl"))
DIST_LOG = os.getenv("DIST_EVENTS_LOG", os.path.join(OBS_DIR, "distribution_events.jsonl"))
ADMIN_PROOFS_LOG = os.getenv("ADMIN_PROOFS_LOG", os.path.join(OBS_DIR, "admin_proofs.jsonl"))
ERROR_LOG = os.getenv("ERROR_EVENTS_LOG", os.path.join(OBS_DIR, "error_events.jsonl"))
OUTCOMES_LOG = os.getenv("OUTCOMES_LOG", os.path.join("/opt/binarybot/outcomes", "outcomes.jsonl"))

ADMIN_PROOF_CHAT_ID = os.getenv("ADMIN_PROOF_CHAT_ID", "")
ADMIN_PROOF_THREAD_ID = os.getenv("ADMIN_PROOF_THREAD_ID", "")

_SCHEMA_CACHE: Optional[Dict[str, Any]] = None
_INCIDENT_REMINDER_SECONDS = 300
_OPERATIONAL_INCIDENTS: Dict[str, Dict[str, Any]] = {}
_LOG_FAILURE_INCIDENTS: Dict[str, Dict[str, Any]] = {}


@dataclass
class RunContext:
    run_id: str
    hostname: str
    pid: int


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"", "replace-me", "unknown", "n/a", "na", "placeholder"}


def _resolve_git_sha() -> str:
    raw = os.getenv("GIT_SHA", "")
    return "" if _is_placeholder(raw) else raw.strip()


def _resolve_run_id() -> str:
    raw = os.getenv("RUN_ID", "")
    if not _is_placeholder(raw):
        return raw.strip()
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


GIT_SHA = _resolve_git_sha()

_RUN = RunContext(run_id=_resolve_run_id(), hostname=socket.gethostname(), pid=os.getpid())


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _epoch_ms() -> int:
    return int(time.time() * 1000)


def _now_ts() -> int:
    return int(time.time())


def _iso_from_ts(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _append_jsonl_fallback(path: str, record: Dict[str, Any]) -> None:
    _ensure_dir(path)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def _load_schema() -> Dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(EVENT_SCHEMA_PATH, "r", encoding="utf-8") as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def get_event_schema() -> Dict[str, Any]:
    return _load_schema()


def _event_sinks() -> Dict[str, str]:
    return {
        "engine": ENGINE_LOG,
        "fsm": FSM_LOG,
        "distribution": DIST_LOG,
        "admin_proofs": ADMIN_PROOFS_LOG,
        "error": ERROR_LOG,
        "outcomes": OUTCOMES_LOG,
    }


def _append_jsonl(path: str, record: Dict[str, Any], *, sink: str) -> None:
    lock_name = "outcomes" if sink == "outcomes" else f"observability_{sink}"
    if storage and hasattr(storage, "with_lock"):
        with storage.with_lock(lock_name):  # type: ignore[attr-defined]
            if storage and hasattr(storage, "append_jsonl"):
                storage.append_jsonl(path, record)  # type: ignore[attr-defined]
            else:
                _append_jsonl_fallback(path, record)
        return
    _append_jsonl_fallback(path, record)


def _host_obj() -> Dict[str, Any]:
    obj: Dict[str, Any] = {
        "hostname": _RUN.hostname,
        "pid": _RUN.pid,
        "app_version": BOT_VERSION,
    }
    if GIT_SHA:
        obj["git_sha"] = GIT_SHA
    return obj


def _schema_field_specs() -> Dict[str, Any]:
    return dict(_load_schema().get("common_correlation_fields", {}))


def _normalize_source(source: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if source is None:
        return {"module": "unknown", "function": "unknown"}
    if not isinstance(source, dict):
        raise ValueError("source must be a dict")

    unknown = set(source.keys()) - {"module", "function", "line"}
    if unknown:
        raise ValueError(f"unknown source fields: {sorted(unknown)}")

    module = str(source.get("module") or "unknown")
    function = str(source.get("function") or "unknown")
    normalized: Dict[str, Any] = {"module": module, "function": function}
    if source.get("line") is not None:
        normalized["line"] = int(source["line"])
    return normalized


def _canonicalize_error_data(event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(data)
    context = normalized.get("context")
    context_obj = dict(context) if isinstance(context, dict) else {}

    if normalized.get("trace") is not None and normalized.get("stack") is None:
        normalized["stack"] = normalized.pop("trace")
    else:
        normalized.pop("trace", None)

    if not normalized.get("severity"):
        normalized["severity"] = str(event.get("severity") or "ERROR")
    if not normalized.get("error_type"):
        normalized["error_type"] = str(
            normalized.pop("code", None)
            or event.get("error_type")
            or event.get("code")
            or event.get("module")
            or "error"
        )
    else:
        normalized.pop("code", None)
    if not normalized.get("message"):
        normalized["message"] = str(
            normalized.pop("error", None)
            or event.get("message")
            or event.get("error")
            or "error"
        )
    else:
        normalized.pop("error", None)

    for key in list(normalized.keys()):
        if key in {"severity", "error_type", "message", "stack", "context"}:
            continue
        context_obj[key] = normalized.pop(key)

    if context_obj:
        normalized["context"] = context_obj
    else:
        normalized.pop("context", None)

    return normalized


def _base_envelope(source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "",
        "schema_version": SCHEMA_VERSION,
        "ts_utc": _iso_utc_now(),
        "ts_epoch_ms": _epoch_ms(),
        "service": SERVICE_NAME,
        "env": ENV_NAME,
        "run_id": _RUN.run_id,
        "source": _normalize_source(source),
        "host": _host_obj(),
        "data": {},
    }


def _allowed_correlation_fields() -> set[str]:
    return set(_schema_field_specs().keys())


def _merge_correlation_fields(event: Dict[str, Any], correlation: Optional[Dict[str, Any]]) -> None:
    if correlation is None:
        return
    if not isinstance(correlation, dict):
        raise ValueError("correlation must be a dict")

    unknown = set(correlation.keys()) - _allowed_correlation_fields()
    if unknown:
        raise ValueError(f"unsupported correlation fields: {sorted(unknown)}")

    for key, value in correlation.items():
        if value is not None:
            event[key] = value


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "null":
        return value is None
    return False


def _type_label(spec: Dict[str, Any]) -> str:
    expected = spec.get("type", "value")
    if isinstance(expected, list):
        return " or ".join(expected)
    return str(expected)


def _validate_value(value: Any, spec: Dict[str, Any], *, path: str) -> None:
    expected: Union[str, Iterable[str]] = spec.get("type", "object")
    allowed_types = [expected] if isinstance(expected, str) else list(expected)

    if not any(_matches_type(value, type_name) for type_name in allowed_types):
        raise ValueError(f"{path} must be {_type_label(spec)}")

    if "enum" in spec and value not in spec["enum"]:
        raise ValueError(f"{path} must be one of {spec['enum']}")

    if value is None:
        return

    if isinstance(value, dict):
        if "required" not in spec and "optional" not in spec:
            return
        _validate_object(value, spec, path=path)
        return

    if isinstance(value, list):
        item_spec = spec.get("items")
        if item_spec is None:
            return
        for index, item in enumerate(value):
            _validate_value(item, item_spec, path=f"{path}[{index}]")


def _validate_object(obj: Dict[str, Any], spec: Dict[str, Any], *, path: str) -> None:
    required = dict(spec.get("required", {}))
    optional = dict(spec.get("optional", {}))
    known_fields = set(required.keys()) | set(optional.keys())

    missing = [field for field in required if field not in obj]
    if missing:
        raise ValueError(f"{path} missing required fields: {missing}")

    unknown = sorted(set(obj.keys()) - known_fields)
    if unknown:
        raise ValueError(f"{path} contains unknown fields: {unknown}")

    for field_name, field_spec in required.items():
        _validate_value(obj[field_name], field_spec, path=f"{path}.{field_name}")
    for field_name, field_spec in optional.items():
        if field_name in obj:
            _validate_value(obj[field_name], field_spec, path=f"{path}.{field_name}")


def supported_event_types() -> list[str]:
    return sorted(_load_schema().get("event_types", {}).keys())


def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("event must be a dict")

    schema = _load_schema()
    event_type = event.get("event_type")
    if not isinstance(event_type, str) or not event_type:
        raise ValueError("event missing event_type")

    event_specs = schema.get("event_types", {})
    if event_type not in event_specs:
        raise ValueError(f"unsupported event_type: {event_type}")

    required = dict(schema["envelope"]["required"])
    required["event_type"] = {"type": "string", "enum": [event_type]}
    required["data"] = {"type": "object"}

    optional = dict(schema["envelope"].get("optional", {}))
    optional.update(_schema_field_specs())

    event_spec = event_specs[event_type]
    required.update(event_spec.get("top_level_required", {}))
    optional.update(event_spec.get("top_level_optional", {}))

    _validate_object(event, {"required": required, "optional": optional}, path="event")
    _validate_object(event["source"], schema["source"], path="event.source")
    _validate_object(event["host"], schema["host"], path="event.host")
    _validate_object(event["data"], event_spec["data"], path="event.data")
    return event


def build_event(
    event_type: str,
    data: Dict[str, Any],
    *,
    source: Optional[Dict[str, Any]] = None,
    correlation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("data must be a dict")

    event = _base_envelope(source=source)
    event["event_type"] = event_type
    event["data"] = dict(data)
    _merge_correlation_fields(event, correlation)
    return validate_event(event)


def _normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accept both:
    1) already-built canonical events
    2) raw shorthand events from older modules
    """
    if not isinstance(event, dict):
        raise ValueError("event must be a dict")

    event_type = event.get("event_type")
    if not event_type:
        raise ValueError("event missing event_type")

    if "data" in event and "event_id" in event:
        canonical = dict(event)
        if canonical.get("event_type") == "error" and isinstance(canonical.get("data"), dict):
            canonical["data"] = _canonicalize_error_data(canonical, dict(canonical["data"]))
        return canonical

    source = event.get("source")
    if not isinstance(source, dict):
        source = {
            "module": str(event.get("module") or "unknown"),
            "function": str(event.get("function") or "unknown"),
        }

    preserved_envelope = _base_envelope(source=source)
    for key in ("event_id", "schema_version", "ts_utc", "ts_epoch_ms", "service", "env", "run_id", "host"):
        if key in event and event[key] is not None:
            preserved_envelope[key] = event[key]

    raw_data = dict(event)
    for key in (
        "event_id",
        "event_type",
        "schema_version",
        "ts_utc",
        "ts_epoch_ms",
        "service",
        "env",
        "run_id",
        "source",
        "host",
        "module",
        "function",
        "data",
    ):
        raw_data.pop(key, None)

    correlation: Dict[str, Any] = {}
    for key in _allowed_correlation_fields():
        if key in raw_data:
            correlation[key] = raw_data.pop(key)

    if isinstance(event.get("data"), dict):
        data = dict(raw_data)
        data.update(event["data"])
    else:
        data = raw_data

    if preserved_envelope["event_type"] == "error":
        data = _canonicalize_error_data(event, data)

    preserved_envelope["event_type"] = str(event_type)
    preserved_envelope["data"] = data
    _merge_correlation_fields(preserved_envelope, correlation)
    return preserved_envelope


def _route_file(event_type: str) -> tuple[str, str]:
    schema = _load_schema()
    sink = schema["event_types"][event_type]["sink"]
    sinks = _event_sinks()
    if sink not in sinks:
        raise ValueError(f"unsupported sink: {sink}")
    return sink, sinks[sink]


def build_error(
    *,
    severity: str,
    error_type: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    stack: Optional[str] = None,
    source: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "severity": severity,
        "error_type": error_type,
        "message": message,
    }
    if stack is not None:
        data["stack"] = stack
    if context is not None:
        data["context"] = context
    return build_event("error", data, source=source)


def _resolve_target(kind: str):
    if not telegram_targets:
        return None
    if kind == "control":
        return telegram_targets.control_target()
    if kind == "proof":
        return telegram_targets.proof_target()
    return None


def _send_telegram_text(kind: str, text: str) -> bool:
    target = _resolve_target(kind)
    if not telegram_publisher or target is None:
        return False
    try:
        telegram_publisher.send_message(
            chat_id=target.chat_id,
            text=text,
            reply_markup=None,
            thread_id=target.thread_id,
        )
        return True
    except Exception:
        return False


def send_control_notification(title: str, message: str) -> bool:
    body = title.strip() if not message.strip() else f"{title.strip()}\n{message.strip()}"
    return _send_telegram_text("control", body.strip())


def send_admin_proof_telegram(kind: str, payload: Dict[str, Any], now_ts: int) -> bool:
    summary = str(payload.get("summary") or payload.get("command") or payload.get("result") or "").strip()
    details = f"user_id={payload.get('user_id')}" if payload.get("user_id") is not None else ""
    lines = [f"🧾 PROOF: {kind}"]
    if summary:
        lines.append(summary)
    if details:
        lines.append(details)
    lines.append(f"ts={_iso_from_ts(now_ts)}")
    return _send_telegram_text("proof", "\n".join(lines))


def record_operational_incident(
    *,
    incident_type: str,
    component: str,
    runtime_state: str,
    operator_action: str,
    severity: str = "CRITICAL",
    reminder_window_seconds: int = _INCIDENT_REMINDER_SECONDS,
    now_ts: Optional[int] = None,
) -> Dict[str, Any]:
    now_ts = int(now_ts if now_ts is not None else _now_ts())
    key = f"{incident_type}:{component}"
    incident = _OPERATIONAL_INCIDENTS.get(key) or {
        "incident_type": incident_type,
        "component": component,
        "first_seen_ts": now_ts,
        "last_notified_ts": 0,
        "count": 0,
    }
    incident["latest_seen_ts"] = now_ts
    incident["count"] = int(incident.get("count", 0)) + 1
    incident["runtime_state"] = runtime_state
    incident["operator_action"] = operator_action
    should_notify = incident["count"] == 1 or (now_ts - int(incident.get("last_notified_ts", 0))) >= reminder_window_seconds
    if should_notify:
        text = "\n".join(
            [
                f"🚨 {severity}: {incident_type}",
                f"component={component}",
                f"runtime_state={runtime_state}",
                f"first_seen={_iso_from_ts(int(incident['first_seen_ts']))}",
                f"latest_seen={_iso_from_ts(int(incident['latest_seen_ts']))}",
                f"count={incident['count']}",
                f"operator_action={operator_action}",
            ]
        )
        _send_telegram_text("proof", text)
        incident["last_notified_ts"] = now_ts
    _OPERATIONAL_INCIDENTS[key] = incident
    return dict(incident)


def clear_operational_incident(
    *,
    incident_type: str,
    component: str,
    runtime_state: str,
    operator_action: str,
    now_ts: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    key = f"{incident_type}:{component}"
    incident = _OPERATIONAL_INCIDENTS.pop(key, None)
    if not incident:
        return None
    now_ts = int(now_ts if now_ts is not None else _now_ts())
    _send_telegram_text(
        "proof",
        "\n".join(
            [
                f"✅ RECOVERED: {incident_type}",
                f"component={component}",
                f"runtime_state={runtime_state}",
                f"first_seen={_iso_from_ts(int(incident['first_seen_ts']))}",
                f"latest_seen={_iso_from_ts(int(incident.get('latest_seen_ts', now_ts)))}",
                f"count={incident.get('count', 0)}",
                f"operator_action={operator_action}",
            ]
        ),
    )
    return dict(incident)


def _record_log_failure(event: Dict[str, Any], stack: str) -> None:
    event_type = event.get("event_type") if isinstance(event, dict) else None
    key = f"{event_type or 'unknown'}:{stack.splitlines()[-1] if stack else 'unknown'}"
    now_ts = _now_ts()
    incident = _LOG_FAILURE_INCIDENTS.get(key) or {"first_seen_ts": now_ts, "last_written_ts": 0, "count": 0}
    incident["latest_seen_ts"] = now_ts
    incident["count"] = int(incident.get("count", 0)) + 1
    should_write = incident["count"] == 1 or (now_ts - int(incident.get("last_written_ts", 0))) >= _INCIDENT_REMINDER_SECONDS
    if should_write:
        err = build_error(
            severity="ERROR",
            error_type="observability_log_failed",
            message="Failed to write event log",
            context={
                "original_event_type": event_type,
                "first_seen_ts": incident["first_seen_ts"],
                "latest_seen_ts": incident["latest_seen_ts"],
                "count": incident["count"],
            },
            stack=stack,
            source={"module": "observability_logger", "function": "log_event"},
        )
        _append_jsonl(ERROR_LOG, err, sink="error")
        incident["last_written_ts"] = now_ts
    _LOG_FAILURE_INCIDENTS[key] = incident


def _runtime_phase_for_incidents() -> str:
    try:
        from runtime import runtime_status  # type: ignore

        status = runtime_status.read_status()
        return str(status.get("phase") or "unknown").upper()
    except Exception:
        return "UNKNOWN"


def _route_critical_error_incident(event: Dict[str, Any]) -> None:
    if event.get("event_type") != "error":
        return
    data = event.get("data")
    if not isinstance(data, dict):
        return
    if str(data.get("severity") or "").upper() != "CRITICAL":
        return
    source = event.get("source")
    component = "unknown"
    if isinstance(source, dict):
        component = str(source.get("module") or component)
    record_operational_incident(
        incident_type=str(data.get("error_type") or "CRITICAL_ERROR"),
        component=component,
        runtime_state=_runtime_phase_for_incidents(),
        operator_action="Inspect recent runtime status and observability logs before retrying.",
        severity="CRITICAL",
    )


def log_event(event: Dict[str, Any]) -> None:
    """
    Writes any canonical event to the correct JSONL file.
    Accepts both canonical and shorthand events.
    Fail-open: never crash engine.
    """
    try:
        normalized = _normalize_event(event)
        validate_event(normalized)
        sink, path = _route_file(str(normalized["event_type"]))
        _append_jsonl(path, normalized, sink=sink)
        _route_critical_error_incident(normalized)
    except Exception:
        try:
            _record_log_failure(event if isinstance(event, dict) else {}, traceback.format_exc())
        except Exception:
            pass


def log_error(error: Dict[str, Any]) -> None:
    data = error.get("data") if isinstance(error.get("data"), dict) else None
    has_required_error_fields = isinstance(data, dict) and all(data.get(field) for field in ("severity", "error_type", "message"))
    if error.get("event_type") != "error" or not has_required_error_fields:
        context = dict(error.get("context")) if isinstance(error.get("context"), dict) else {}
        for key, value in error.items():
            if key in {"event_type", "severity", "error_type", "code", "message", "error", "context", "stack", "trace", "source", "module", "function", "data"}:
                continue
            context[key] = value
        error = build_error(
            severity=str(error.get("severity", (data or {}).get("severity", "ERROR"))),
            error_type=str(error.get("error_type", (data or {}).get("error_type", error.get("code", error.get("module", "error"))))),
            message=str(error.get("message", (data or {}).get("message", error.get("error", "error")))),
            context=context or None,
            stack=error.get("stack") or error.get("trace"),
            source=error.get("source") or {
                "module": str(error.get("module", "unknown")),
                "function": str(error.get("function", "unknown")),
            },
        )
    log_event(error)


def log_warning(
    *,
    warn_type: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    source: Optional[Dict[str, Any]] = None,
    correlation: Optional[Dict[str, Any]] = None,
) -> None:
    data: Dict[str, Any] = {
        "severity": "WARNING",
        "code": warn_type,
        "message": message,
        "context": context or {},
    }
    event = build_event("warning", data, source=source, correlation=correlation)
    log_event(event)


def proof(kind: str, payload: Dict[str, Any], now_ts: int) -> None:
    source = {"module": "observability_logger", "function": "proof"}
    data = {
        "kind": kind,
        "payload": payload,
        "now_ts_epoch": now_ts,
    }
    ev = build_event(
        "admin_change",
        data,
        source=source,
        correlation={"tier": payload.get("tier"), "signal_id": payload.get("signal_id")},
    )
    log_event(ev)
    send_admin_proof_telegram(kind, payload, now_ts)
