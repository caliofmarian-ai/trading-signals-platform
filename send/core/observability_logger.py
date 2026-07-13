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
    from . import telegram_publisher  # type: ignore
except Exception:
    telegram_publisher = None


SCHEMA_VERSION = os.getenv("EVENT_SCHEMA_VERSION", "2.0.0")
SERVICE_NAME = os.getenv("SERVICE_NAME", "binarybot")
ENV_NAME = os.getenv("BOT_ENV", "prod")
BOT_VERSION = os.getenv("BOT_VERSION", "0.0.0")
GIT_SHA = os.getenv("GIT_SHA", "")

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


@dataclass
class RunContext:
    run_id: str
    hostname: str
    pid: int


_RUN = RunContext(
    run_id=os.getenv("RUN_ID", f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"),
    hostname=socket.gethostname(),
    pid=os.getpid(),
)


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _epoch_ms() -> int:
    return int(time.time() * 1000)


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
        return dict(event)

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

    if preserved_envelope["event_type"] == "error" and "error_type" not in data and data.get("code") is not None:
        data["error_type"] = data.pop("code")

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
    except Exception:
        try:
            err = build_error(
                severity="ERROR",
                error_type="observability_log_failed",
                message="Failed to write event log",
                context={"original_event_type": event.get("event_type") if isinstance(event, dict) else None},
                stack=traceback.format_exc(),
                source={"module": "observability_logger", "function": "log_event"},
            )
            _append_jsonl(ERROR_LOG, err, sink="error")
        except Exception:
            pass


def log_error(error: Dict[str, Any]) -> None:
    if error.get("event_type") != "error":
        error = build_error(
            severity="ERROR",
            error_type=str(error.get("error_type", error.get("code", "error"))),
            message=str(error.get("message", error.get("error", "error"))),
            context=error.get("context"),
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

    if not telegram_publisher:
        return
    if not ADMIN_PROOF_CHAT_ID:
        return

    try:
        chat_id = int(ADMIN_PROOF_CHAT_ID)
        thread_id = int(ADMIN_PROOF_THREAD_ID) if ADMIN_PROOF_THREAD_ID else None
        title = f"🧾 PROOF: {kind}"
        summary = payload.get("summary") or ""
        txt = title + ("\n" + summary if summary else "")
        telegram_publisher.send_message(
            chat_id=chat_id,
            text=txt,
            reply_markup=None,
            thread_id=thread_id,
        )
    except Exception:
        pass
