from __future__ import annotations

import json
import os
import socket
import time
import uuid
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from . import storage  # type: ignore
except Exception:
    storage = None

try:
    from . import telegram_publisher  # type: ignore
except Exception:
    telegram_publisher = None


SCHEMA_VERSION = os.getenv("EVENT_SCHEMA_VERSION", "1.0.0")
SERVICE_NAME = os.getenv("SERVICE_NAME", "binarybot")
ENV_NAME = os.getenv("BOT_ENV", "prod")
BOT_VERSION = os.getenv("BOT_VERSION", "0.0.0")
GIT_SHA = os.getenv("GIT_SHA", "")

OBS_DIR = os.getenv("OBS_DIR", "/opt/binarybot/observability")
ENGINE_LOG = os.getenv("ENGINE_EVENTS_LOG", os.path.join(OBS_DIR, "engine_events.jsonl"))
FSM_LOG = os.getenv("FSM_EVENTS_LOG", os.path.join(OBS_DIR, "fsm_events.jsonl"))
DIST_LOG = os.getenv("DIST_EVENTS_LOG", os.path.join(OBS_DIR, "distribution_events.jsonl"))
ADMIN_PROOFS_LOG = os.getenv("ADMIN_PROOFS_LOG", os.path.join(OBS_DIR, "admin_proofs.jsonl"))
ERROR_LOG = os.getenv("ERROR_EVENTS_LOG", os.path.join(OBS_DIR, "error_events.jsonl"))

ADMIN_PROOF_CHAT_ID = os.getenv("ADMIN_PROOF_CHAT_ID", "")
ADMIN_PROOF_THREAD_ID = os.getenv("ADMIN_PROOF_THREAD_ID", "")


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


def _append_jsonl(path: str, record: Dict[str, Any]) -> None:
    if storage and hasattr(storage, "append_jsonl"):
        storage.append_jsonl(path, record)  # type: ignore
    else:
        _append_jsonl_fallback(path, record)


def _host_obj() -> Dict[str, Any]:
    obj: Dict[str, Any] = {
        "hostname": _RUN.hostname,
        "pid": _RUN.pid,
        "version": BOT_VERSION,
    }
    if GIT_SHA:
        obj["git_sha"] = GIT_SHA
    return obj


def _base_envelope(source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    env: Dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "schema_version": SCHEMA_VERSION,
        "ts_utc": _iso_utc_now(),
        "ts_epoch_ms": _epoch_ms(),
        "service": SERVICE_NAME,
        "env": ENV_NAME,
        "run_id": _RUN.run_id,
        "host": _host_obj(),
    }
    if source:
        env["source"] = source
    return env


_ALLOWED_EVENT_TYPES = {
    "engine_start",
    "engine_stop",
    "signal_event",
    "decision",
    "fsm_transition",
    "tier_publish",
    "tier_reset",
    "admin_change",
    "user_outcome",
    "error",
}


def _validate_minimal(event: Dict[str, Any]) -> None:
    if "event_type" not in event:
        raise ValueError("event missing event_type")
    if event["event_type"] not in _ALLOWED_EVENT_TYPES:
        raise ValueError(f"invalid event_type: {event['event_type']}")
    for k in ("schema_version", "ts_utc", "ts_epoch_ms", "service", "env", "run_id", "host"):
        if k not in event:
            raise ValueError(f"event missing required field: {k}")
    if "data" not in event:
        raise ValueError("event missing data")


def _route_file(event_type: str) -> str:
    if event_type in ("engine_start", "engine_stop", "decision", "signal_event"):
        return ENGINE_LOG
    if event_type == "fsm_transition":
        return FSM_LOG
    if event_type in ("tier_publish", "tier_reset"):
        return DIST_LOG
    if event_type == "admin_change":
        return ADMIN_PROOFS_LOG
    if event_type == "user_outcome":
        return os.path.join("/opt/binarybot/outcomes", "outcomes.jsonl")
    if event_type == "error":
        return ERROR_LOG
    return ERROR_LOG


def build_event(
    event_type: str,
    data: Dict[str, Any],
    *,
    source: Optional[Dict[str, Any]] = None,
    correlation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    e = _base_envelope(source=source)
    e["event_type"] = event_type
    if correlation:
        for k, v in correlation.items():
            if v is not None:
                e[k] = v
    e["data"] = data
    return e


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

    # If it's already canonical enough, leave it alone.
    if "data" in event and "event_id" in event:
        return event

    source = event.get("source")
    if not isinstance(source, dict):
        source = None

    raw_data = dict(event)
    raw_data.pop("event_id", None)
    raw_data.pop("schema_version", None)
    raw_data.pop("ts_utc", None)
    raw_data.pop("ts_epoch_ms", None)
    raw_data.pop("service", None)
    raw_data.pop("env", None)
    raw_data.pop("run_id", None)
    raw_data.pop("host", None)
    raw_data.pop("source", None)
    raw_data.pop("event_type", None)
    raw_data.pop("data", None)

    if "data" in event and isinstance(event["data"], dict):
        data = event["data"]
    else:
        data = raw_data

    normalized = build_event(
        event_type=str(event_type),
        data=data,
        source=source,
    )

    # Preserve optional top-level correlation-ish fields if caller set them.
    for key in ("signal_id", "tier", "symbol", "timeframe"):
        if key in event and event[key] is not None:
            normalized[key] = event[key]

    return normalized


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
    if stack:
        data["stack"] = stack
    if context:
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
        _validate_minimal(normalized)
        path = _route_file(str(normalized["event_type"]))
        _append_jsonl(path, normalized)
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
            _append_jsonl(ERROR_LOG, err)
        except Exception:
            pass


def log_error(error: Dict[str, Any]) -> None:
    if error.get("event_type") != "error":
        error = build_error(
            severity="ERROR",
            error_type=str(error.get("error_type", "error")),
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
) -> None:
    e = build_error(
        severity="WARNING",
        error_type=warn_type,
        message=message,
        context=context,
        stack=None,
        source=source,
    )
    log_event(e)


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