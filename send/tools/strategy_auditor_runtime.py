from __future__ import annotations

import datetime as _dt
import copy
import json
import os
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from core import observability_logger, storage
from tools import strategy_auditor_lib as auditor_lib


WORKER_EVALUATION_INTERVAL_SECONDS = 30
MAX_ATTEMPTS_PER_PERIOD = 3
RETRY_BACKOFF_SECONDS = 300
STATUS_OVERLAY_MAX_AGE_SECONDS = 2 * 24 * 60 * 60
JOURNAL_THROTTLE_SECONDS = 300

_STATE_VERSION = 1
_THREAD_LOCK = threading.Lock()
_JOURNAL_LOCK = threading.Lock()
_JOURNAL_LAST_EMITTED: Dict[Tuple[str, str], float] = {}
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


class StrategyAuditorRuntimeError(RuntimeError):
    pass


class StrategyAuditorDuplicateRun(StrategyAuditorRuntimeError):
    pass


class StrategyAuditorStateCorrupt(StrategyAuditorRuntimeError):
    pass


class StrategyAuditorPathError(StrategyAuditorRuntimeError):
    def __init__(self, code: str, path_label: str) -> None:
        super().__init__(code)
        self.code = code
        self.path_label = path_label


def state_path() -> str:
    return storage.state_path("strategy_auditor_state.json")


def status_path() -> str:
    return storage.state_path("strategy_auditor_status.json")


def lock_path() -> str:
    return storage.state_path("strategy_auditor.lock")


def journal_path() -> str:
    return storage.root_path("observability", "strategy_auditor_events.jsonl")


def _utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.UTC)


def _aware_utc(value: Optional[_dt.datetime]) -> _dt.datetime:
    candidate = value if value is not None else _utc_now()
    if candidate.tzinfo is None or candidate.utcoffset() is None:
        raise ValueError("naive datetime is not accepted")
    return candidate.astimezone(_dt.UTC)


def _iso(value: _dt.datetime) -> str:
    return value.astimezone(_dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _period(value: _dt.datetime) -> str:
    return value.astimezone(_dt.UTC).date().isoformat()


def _epoch(value: _dt.datetime) -> int:
    return int(value.astimezone(_dt.UTC).timestamp())


def _deployment_id() -> str:
    for key in ("RAILWAY_DEPLOYMENT_ID", "RAILWAY_SERVICE_ID", "RUN_ID"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


def _default_state() -> Dict[str, Any]:
    return {"schema_version": _STATE_VERSION, "periods": {}, "last_seen_period": None}


def _read_json_strict(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("json root must be object")
    return data


def _load_state() -> Dict[str, Any]:
    path = state_path()
    if not os.path.exists(path):
        return _default_state()
    try:
        state = _read_json_strict(path)
    except Exception as exc:
        raise StrategyAuditorStateCorrupt("state json is corrupt") from exc
    _validate_state_schema(state)
    return state


def _valid_period_key(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = _dt.date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _validate_report_paths(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise StrategyAuditorStateCorrupt(f"{label} must be an object")
    for key, path in value.items():
        if key not in {"json", "markdown"} or not isinstance(path, str) or not path:
            raise StrategyAuditorStateCorrupt(f"{label} contains invalid report path metadata")


def _validate_attempt(value: Any, *, period: str) -> None:
    if not isinstance(value, dict):
        raise StrategyAuditorStateCorrupt(f"period {period} contains a non-object attempt")
    if not isinstance(value.get("attempt_id"), str) or not value["attempt_id"]:
        raise StrategyAuditorStateCorrupt(f"period {period} attempt is missing attempt_id")
    status = value.get("status")
    if status not in {"STARTED", "INTERRUPTED", "FAILED", "COMPLETED"}:
        raise StrategyAuditorStateCorrupt(f"period {period} attempt status is invalid")
    if not isinstance(value.get("started_at"), str) or not value["started_at"]:
        raise StrategyAuditorStateCorrupt(f"period {period} attempt is missing started_at")
    if not isinstance(value.get("started_epoch"), int) or isinstance(value.get("started_epoch"), bool):
        raise StrategyAuditorStateCorrupt(f"period {period} attempt is missing started_epoch")
    if value.get("completed_at") is not None and not isinstance(value.get("completed_at"), str):
        raise StrategyAuditorStateCorrupt(f"period {period} attempt completed_at is invalid")
    if value.get("decision_count") is not None and (
        not isinstance(value.get("decision_count"), int) or isinstance(value.get("decision_count"), bool)
    ):
        raise StrategyAuditorStateCorrupt(f"period {period} attempt decision_count is invalid")
    if value.get("report_paths") is not None:
        _validate_report_paths(value["report_paths"], label=f"period {period} attempt report_paths")
    if value.get("schedule_identity") is not None and not isinstance(value.get("schedule_identity"), dict):
        raise StrategyAuditorStateCorrupt(f"period {period} attempt schedule_identity is invalid")
    if value.get("policy") is not None and not isinstance(value.get("policy"), dict):
        raise StrategyAuditorStateCorrupt(f"period {period} attempt policy is invalid")
    if value.get("error") is not None and not isinstance(value.get("error"), dict):
        raise StrategyAuditorStateCorrupt(f"period {period} attempt error is invalid")


def _validate_period_record(period: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise StrategyAuditorStateCorrupt(f"period {period} record must be an object")
    if set(value) - {
        "attempts",
        "completed",
        "completed_attempt_id",
        "completed_at",
        "decision_count",
        "report_paths",
    }:
        raise StrategyAuditorStateCorrupt(f"period {period} contains unknown fields")
    if not isinstance(value.get("completed"), bool):
        raise StrategyAuditorStateCorrupt(f"period {period} completed must be boolean")
    attempts = value.get("attempts")
    if not isinstance(attempts, list):
        raise StrategyAuditorStateCorrupt(f"period {period} attempts must be a list")
    for attempt in attempts:
        _validate_attempt(attempt, period=period)
    if value["completed"]:
        completed_attempt_id = value.get("completed_attempt_id")
        if not isinstance(completed_attempt_id, str) or not completed_attempt_id:
            raise StrategyAuditorStateCorrupt(f"period {period} missing completed_attempt_id")
        if not isinstance(value.get("completed_at"), str) or not value["completed_at"]:
            raise StrategyAuditorStateCorrupt(f"period {period} missing completed_at")
        if value.get("decision_count") is not None and (
            not isinstance(value.get("decision_count"), int) or isinstance(value.get("decision_count"), bool)
        ):
            raise StrategyAuditorStateCorrupt(f"period {period} decision_count is invalid")
        _validate_report_paths(value.get("report_paths"), label=f"period {period} report_paths")
        if not any(
            isinstance(attempt, dict)
            and attempt.get("attempt_id") == completed_attempt_id
            and attempt.get("status") == "COMPLETED"
            for attempt in attempts
        ):
            raise StrategyAuditorStateCorrupt(f"period {period} completed attempt is missing")


def _validate_state_schema(state: Dict[str, Any]) -> None:
    if state.get("schema_version") != _STATE_VERSION:
        raise StrategyAuditorStateCorrupt("state schema_version is unsupported")
    last_seen = state.get("last_seen_period")
    if last_seen is not None and not _valid_period_key(last_seen):
        raise StrategyAuditorStateCorrupt("state last_seen_period is invalid")
    periods = state.get("periods")
    if not isinstance(periods, dict):
        raise StrategyAuditorStateCorrupt("state periods are corrupt")
    if set(state) - {"schema_version", "periods", "last_seen_period"}:
        raise StrategyAuditorStateCorrupt("state contains unknown fields")
    for period, record in periods.items():
        if not _valid_period_key(period):
            raise StrategyAuditorStateCorrupt("state contains invalid period key")
        _validate_period_record(period, record)


def _save_state(state: Dict[str, Any]) -> None:
    storage.save_json_atomic(state_path(), state)


def _canonical_path(path: str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _same_or_child(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return path == root


def _paths_overlap(a: Path, b: Path) -> bool:
    return _same_or_child(a, b) or _same_or_child(b, a)


def _required_outputs(settings: Dict[str, Any], *, mode: str) -> List[str]:
    reports = dict(settings.get("reports", {}) or {})
    write_json = auditor_lib._bool_setting(reports.get("write_json"), True)
    write_markdown = auditor_lib._bool_setting(reports.get("write_markdown"), True)
    if not write_json or not write_markdown:
        raise auditor_lib.StrategyAuditorSettingsError(
            "Runtime strategy auditor requires both JSON and Markdown report outputs."
        )
    return ["json", "markdown"]


def _reports_enabled(settings: Dict[str, Any]) -> bool:
    reports = dict(settings.get("reports", {}) or {})
    return auditor_lib._bool_setting(reports.get("enabled"), True)


def _guard_path_aliases(settings: Dict[str, Any], report_period: str) -> None:
    sources = dict(settings.get("sources", {}) or {})
    source_paths = {key: _canonical_path(str(path)) for key, path in sources.items()}
    report_paths = auditor_lib.report_paths_for_date(report_period, settings)
    reports = dict(settings.get("reports", {}) or {})

    protected_files = {
        "state": _canonical_path(state_path()),
        "status": _canonical_path(status_path()),
        "lock": _canonical_path(lock_path()),
        "journal": _canonical_path(journal_path()),
        "report_json": _canonical_path(report_paths["json"]),
        "report_markdown": _canonical_path(report_paths["markdown"]),
    }
    protected_dirs = {
        "state_dir": _canonical_path(os.path.dirname(state_path())),
        "reports.output_dir": _canonical_path(auditor_lib.resolve_reports_dir(settings)),
    }
    cache_dir = reports.get("cache_dir")
    if isinstance(cache_dir, str) and cache_dir.strip():
        protected_dirs["reports.cache_dir"] = _canonical_path(cache_dir)

    for source_key, source_path in source_paths.items():
        for label, protected in protected_files.items():
            if source_path == protected:
                raise StrategyAuditorPathError("SOURCE_ALIASES_WRITE_FILE", f"sources.{source_key}->{label}")
        for label, protected_dir in protected_dirs.items():
            if _same_or_child(source_path, protected_dir):
                raise StrategyAuditorPathError("SOURCE_ALIASES_WRITE_DIRECTORY", f"sources.{source_key}->{label}")

    write_dirs = list(protected_dirs.items())
    for idx, (left_label, left_path) in enumerate(write_dirs):
        for right_label, right_path in write_dirs[idx + 1:]:
            if _paths_overlap(left_path, right_path):
                raise StrategyAuditorPathError("WRITE_DIRECTORIES_OVERLAP", f"{left_label}->{right_label}")


def _env_source_paths() -> Dict[str, str]:
    paths: Dict[str, str] = {}
    obs_dir = os.getenv("OBS_DIR", "").strip()
    if obs_dir:
        paths["OBS_DIR.engine_events"] = os.path.join(obs_dir, "engine_events.jsonl")
        paths["OBS_DIR.fsm_events"] = os.path.join(obs_dir, "fsm_events.jsonl")
        paths["OBS_DIR.distribution_events"] = os.path.join(obs_dir, "distribution_events.jsonl")
        paths["OBS_DIR.error_events"] = os.path.join(obs_dir, "error_events.jsonl")
    for key, env_name in auditor_lib._SOURCE_ENV_OVERRIDES.items():
        raw = os.getenv(env_name, "").strip()
        if raw:
            paths[env_name] = raw
    return paths


def _guard_env_source_aliases(report_period: str) -> None:
    try:
        base_dir = Path(storage.base_dir()).resolve(strict=False)
    except Exception:
        base_dir = Path.cwd().resolve(strict=False)
    protected_files = {
        "state": _canonical_path(state_path()),
        "status": _canonical_path(status_path()),
        "lock": _canonical_path(lock_path()),
        "journal": _canonical_path(journal_path()),
    }
    analytics_dir = os.getenv("ANALYTICS_DIR", "").strip()
    reports_root = _canonical_path(analytics_dir) / "reports" if analytics_dir else base_dir / "analytics" / "reports"
    protected_dirs = {
        "state_dir": _canonical_path(os.path.dirname(state_path())),
        "reports.output_dir": _canonical_path(str(reports_root)),
    }
    protected_files["report_json"] = _canonical_path(str(reports_root / f"daily_strategy_audit_{report_period}.json"))
    protected_files["report_markdown"] = _canonical_path(str(reports_root / f"daily_strategy_audit_{report_period}.md"))

    for label, raw in _env_source_paths().items():
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            raise StrategyAuditorPathError("SOURCE_ENV_PATH_NOT_ABSOLUTE", label)
        if any(part == ".." for part in candidate.parts):
            raise StrategyAuditorPathError("SOURCE_ENV_PATH_TRAVERSAL", label)
        source_path = candidate.resolve(strict=False)
        for protected_label, protected in protected_files.items():
            if source_path == protected:
                raise StrategyAuditorPathError("SOURCE_ALIASES_WRITE_FILE", f"{label}->{protected_label}")
        for protected_label, protected_dir in protected_dirs.items():
            if _same_or_child(source_path, protected_dir):
                raise StrategyAuditorPathError("SOURCE_ALIASES_WRITE_DIRECTORY", f"{label}->{protected_label}")


def _ensure_runtime_dirs(settings: Dict[str, Any]) -> None:
    reports = dict(settings.get("reports", {}) or {})
    os.makedirs(os.path.dirname(state_path()), exist_ok=True)
    os.makedirs(os.path.dirname(journal_path()), exist_ok=True)
    os.makedirs(auditor_lib.resolve_reports_dir(settings), exist_ok=True)
    cache_dir = reports.get("cache_dir")
    if isinstance(cache_dir, str) and cache_dir.strip():
        os.makedirs(cache_dir, exist_ok=True)


def _sanitize_value(value: Any, depth: int = 0, *, max_depth: int = 4) -> Any:
    if depth > max_depth:
        return "<bounded>"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:160]
    if isinstance(value, list):
        return [_sanitize_value(item, depth + 1, max_depth=max_depth) for item in value[:10]]
    if isinstance(value, dict):
        return {
            str(key)[:80]: _sanitize_value(val, depth + 1, max_depth=max_depth)
            for key, val in list(value.items())[:20]
        }
    return type(value).__name__


def _sanitize_error(exc: BaseException, *, operation: str, path_label: Optional[str] = None) -> Dict[str, Any]:
    error: Dict[str, Any] = {
        "error_type": type(exc).__name__,
        "message": "Strategy auditor operation failed.",
        "operation": operation,
    }
    if path_label:
        error["path_label"] = path_label
    if isinstance(exc, StrategyAuditorPathError):
        error["code"] = exc.code
        error["path_label"] = exc.path_label
    return error


def _stderr_fallback(payload: Dict[str, Any]) -> None:
    try:
        print(json.dumps(_sanitize_value(payload), sort_keys=True), file=sys.stderr, flush=True)
    except Exception:
        print('{"component":"strategy_auditor","status":"LOGGING_FAILED"}', file=sys.stderr, flush=True)


def _history_attempt_status(status: Any) -> str:
    return "SUCCESS" if status == "COMPLETED" else str(status or "UNKNOWN")


def _status_history_from_state() -> Dict[str, Dict[str, Any]]:
    try:
        state = _load_state()
    except Exception:
        return {}

    history: Dict[str, Dict[str, Any]] = {}
    attempts_seen: List[Tuple[int, str, str, Dict[str, Any]]] = []
    successes_seen: List[Tuple[str, str, Dict[str, Any]]] = []
    periods = state.get("periods") if isinstance(state, dict) else {}
    if not isinstance(periods, dict):
        return history

    for period, record in periods.items():
        if not isinstance(period, str) or not isinstance(record, dict):
            continue
        attempts = record.get("attempts")
        if isinstance(attempts, list):
            for attempt in attempts:
                if not isinstance(attempt, dict):
                    continue
                started_epoch = attempt.get("started_epoch")
                attempt_id = attempt.get("attempt_id")
                if isinstance(started_epoch, int) and isinstance(attempt_id, str):
                    attempts_seen.append((started_epoch, period, attempt_id, attempt))
        if record.get("completed") is True and isinstance(record.get("completed_at"), str):
            completed_attempt_id = record.get("completed_attempt_id")
            if isinstance(completed_attempt_id, str) and completed_attempt_id:
                successes_seen.append((str(record["completed_at"]), period, record))

    if attempts_seen:
        _epoch_seen, period, _attempt_id, attempt = max(attempts_seen, key=lambda item: (item[0], item[1], item[2]))
        last_attempt = {
            "attempt_id": attempt.get("attempt_id"),
            "status": _history_attempt_status(attempt.get("status")),
            "report_period": period,
            "started_at": attempt.get("started_at"),
            "completed_at": attempt.get("completed_at"),
        }
        if isinstance(attempt.get("report_paths"), dict):
            last_attempt["report_paths"] = dict(attempt["report_paths"])
        history["last_attempt"] = last_attempt

    if successes_seen:
        _completed_at, period, record = max(successes_seen, key=lambda item: (item[0], item[1]))
        history["last_success"] = {
            "attempt_id": record.get("completed_attempt_id"),
            "report_period": period,
            "completed_at": record.get("completed_at"),
            "decision_count": record.get("decision_count"),
            "report_paths": dict(record.get("report_paths") or {}),
        }

    return history


def _with_status_history(payload: Dict[str, Any]) -> Dict[str, Any]:
    status = dict(payload)
    attempt_id = status.get("attempt_id")
    current_status = status.get("status")
    if attempt_id and current_status in {"SUCCESS", "FAILED"}:
        status["last_attempt"] = {
            "attempt_id": attempt_id,
            "status": current_status,
            "report_period": status.get("report_period"),
            "started_at": status.get("started_at"),
            "completed_at": status.get("completed_at"),
        }
    if current_status in {"SUCCESS", "ALREADY_COMPLETED"}:
        status["last_success"] = {
            "attempt_id": attempt_id,
            "report_period": status.get("report_period"),
            "completed_at": status.get("completed_at"),
            "decision_count": status.get("decision_count"),
            "report_paths": dict(status.get("report_paths") or {}),
        }
    ledger_history = _status_history_from_state()
    for key in ("last_attempt", "last_success"):
        if key not in status and isinstance(ledger_history.get(key), dict):
            status[key] = ledger_history[key]
    try:
        existing = _read_json_strict(status_path())
    except Exception:
        existing = {}
    for key in ("last_attempt", "last_success"):
        if key not in status and isinstance(existing.get(key), dict):
            status[key] = existing[key]
    return status


def _write_status(payload: Dict[str, Any]) -> None:
    status = _with_status_history(payload)
    now = _utc_now()
    status.setdefault("component", "strategy_auditor")
    status["updated_at"] = _iso(now)
    status["updated_epoch"] = _epoch(now)
    try:
        storage.save_json_atomic(status_path(), _sanitize_value(status, max_depth=5))
    except Exception:
        _stderr_fallback({"component": "strategy_auditor", "status": "STATUS_WRITE_FAILED"})


def read_auditor_status(*, max_age_seconds: Optional[int] = None) -> Dict[str, Any]:
    path = status_path()
    if not os.path.exists(path):
        return {}
    try:
        status = _read_json_strict(path)
    except Exception:
        return {"component": "strategy_auditor", "status": "STATUS_CORRUPT"}
    if max_age_seconds is not None:
        updated_epoch = status.get("updated_epoch")
        if isinstance(updated_epoch, int) and int(time.time()) - updated_epoch > max_age_seconds:
            bounded = {
                "component": "strategy_auditor",
                "status": "STALE",
                "last_status": status.get("status"),
                "updated_at": status.get("updated_at"),
            }
            for key in ("last_attempt", "last_success"):
                if isinstance(status.get(key), dict):
                    bounded[key] = status[key]
            return bounded
    return status


def _journal_throttle_key(code: str, context: Dict[str, Any]) -> Tuple[str, str]:
    scope = context.get("report_period") or context.get("status") or context.get("mode") or ""
    return code, str(scope)


def _should_emit_journal(code: str, context: Dict[str, Any], *, throttle: bool) -> bool:
    if not throttle:
        return True
    key = _journal_throttle_key(code, context)
    now_epoch = time.time()
    with _JOURNAL_LOCK:
        last = _JOURNAL_LAST_EMITTED.get(key)
        if last is not None and now_epoch - last < JOURNAL_THROTTLE_SECONDS:
            return False
        _JOURNAL_LAST_EMITTED[key] = now_epoch
    return True


def _journal_event(
    event_type: str,
    code: str,
    message: str,
    context: Dict[str, Any],
    *,
    throttle: bool = False,
) -> None:
    if not _should_emit_journal(code, context, throttle=throttle):
        return
    try:
        if event_type == "warning":
            event = observability_logger.build_event(
                "warning",
                {
                    "severity": "WARNING",
                    "code": code,
                    "message": message,
                    "context": _sanitize_value(context),
                },
                source={"module": "strategy_auditor_runtime", "function": "_journal_event"},
            )
        else:
            event = observability_logger.build_event(
                "error",
                {
                    "severity": "ERROR",
                    "error_type": code,
                    "message": message,
                    "context": _sanitize_value(context),
                },
                source={"module": "strategy_auditor_runtime", "function": "_journal_event"},
            )
        observability_logger.validate_event(event)
        storage.append_jsonl(journal_path(), event)
    except Exception:
        _stderr_fallback({
            "component": "strategy_auditor",
            "status": "JOURNAL_WRITE_FAILED",
            "event_type": event_type,
            "code": code,
        })


def _diagnostic_guard_error(
    report_period: Optional[str] = None,
    *,
    settings_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    try:
        now_period = report_period or _period(_utc_now())
        _guard_env_source_aliases(now_period)
        settings = auditor_lib.load_settings(settings_path)
        _guard_path_aliases(settings, now_period)
    except StrategyAuditorPathError as exc:
        return _sanitize_error(exc, operation="diagnostic_write_guard")
    except Exception as exc:
        return _sanitize_error(exc, operation="diagnostic_write_guard", path_label="settings.strategy_auditor")
    return None


def _guarded_status_or_stderr(
    result: Dict[str, Any],
    *,
    report_period: Optional[str] = None,
    settings_path: Optional[str] = None,
) -> Dict[str, Any]:
    guard_error = _diagnostic_guard_error(report_period, settings_path=settings_path)
    if guard_error is not None:
        guarded = dict(result)
        guarded["status"] = "CONFIGURATION_ERROR"
        if guard_error.get("code") or not guarded.get("error"):
            guarded["error"] = guard_error
        else:
            guarded["diagnostic_write_blocked"] = guard_error
        _stderr_fallback(guarded)
        return guarded
    _write_status(result)
    return result


def _guarded_journal_event(
    event_type: str,
    code: str,
    message: str,
    context: Dict[str, Any],
    *,
    report_period: Optional[str] = None,
    settings_path: Optional[str] = None,
    throttle: bool = False,
) -> None:
    if _diagnostic_guard_error(report_period, settings_path=settings_path) is not None:
        _stderr_fallback({
            "component": "strategy_auditor",
            "status": "JOURNAL_SKIPPED_BY_DIAGNOSTIC_GUARD",
            "code": code,
        })
        return
    _journal_event(event_type, code, message, context, throttle=throttle)


def record_diagnostic(
    *,
    status: str,
    code: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    severity: str = "WARNING",
) -> None:
    payload = {
        "component": "strategy_auditor",
        "status": status,
        "error": {
            "error_type": code,
            "message": message,
            "operation": "optional_runtime_validation",
        },
    }
    if context:
        payload["context"] = _sanitize_value(context)
    guard_error = _diagnostic_guard_error()
    if guard_error is not None:
        payload["status"] = "CONFIGURATION_ERROR"
        payload["error"] = guard_error
        _stderr_fallback(payload)
        return
    _write_status(payload)
    _journal_event(
        "error" if severity.upper() == "ERROR" else "warning",
        code,
        message,
        context or {},
    )


def _base_result(
    *,
    status: str,
    mode: str,
    now: Optional[_dt.datetime] = None,
    report_period: Optional[str] = None,
    schedule_identity: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        started = _aware_utc(now)
    except Exception:
        started = _utc_now()
    period = report_period or _period(started)
    return {
        "component": "strategy_auditor",
        "status": status,
        "mode": mode,
        "report_period": period,
        "date": period,
        "timezone": "UTC",
        "schedule_identity": schedule_identity or {"status": "SCHEDULE_NOT_CONFIGURED", "timezone": "UTC"},
        "attempt_id": None,
        "started_at": _iso(started),
        "completed_at": None,
        "decision_count": None,
        "report_paths": {},
        "error": None,
        "policy": {
            "max_attempts_per_period": MAX_ATTEMPTS_PER_PERIOD,
            "retry_backoff_seconds": RETRY_BACKOFF_SECONDS,
            "worker_evaluation_interval_seconds": WORKER_EVALUATION_INTERVAL_SECONDS,
            "policy_kind": "engineering_runtime_guardrail",
        },
    }


def _parse_schedule(raw: Optional[str] = None) -> Tuple[Optional[_dt.time], Dict[str, Any]]:
    configured = (raw if raw is not None else os.getenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "")).strip()
    identity = {
        "source": "STRATEGY_AUDITOR_DAILY_TIME_UTC",
        "configured_time_utc": None,
        "timezone": "UTC",
    }
    if not configured:
        identity["status"] = "SCHEDULE_NOT_CONFIGURED"
        return None, identity
    identity["configured_time_present"] = True
    ascii_digits = "0123456789"
    if (
        len(configured) != 5
        or configured[2] != ":"
        or any(char not in ascii_digits for char in configured[:2] + configured[3:])
    ):
        identity["status"] = "INVALID_SCHEDULE"
        return None, identity
    hour, minute = int(configured[:2]), int(configured[3:])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        identity["status"] = "INVALID_SCHEDULE"
        return None, identity
    normalized = f"{hour:02d}:{minute:02d}"
    identity["configured_time_utc"] = normalized
    identity["status"] = "CONFIGURED"
    return _dt.time(hour=hour, minute=minute, tzinfo=_dt.UTC), identity


def _env_enabled_flag() -> Tuple[bool, str]:
    raw = os.getenv("STRATEGY_AUDITOR_ENABLED")
    if raw is None or not raw.strip():
        return False, "ENV_NOT_ENABLED"
    normalized = raw.strip().lower()
    if normalized in _TRUTHY:
        return True, "ENABLED"
    if normalized in _FALSY:
        return False, "ENV_DISABLED"
    return False, "INVALID_ENABLED_FLAG"


def _admin_strategy_auditor_enabled() -> Tuple[bool, str]:
    try:
        path = Path(storage.base_dir()) / "config" / "admin_settings.json"
    except Exception:
        raise
    if not path.exists():
        path = Path(__file__).resolve().parents[1] / "config" / "admin_settings.json"
    if not path.exists():
        return True, "ADMIN_SETTING_MISSING"
    try:
        data = _read_json_strict(str(path))
    except Exception as exc:
        raise auditor_lib.StrategyAuditorSettingsError("admin settings are invalid") from exc
    feature_flags = data.get("feature_flags")
    if not isinstance(feature_flags, dict):
        feature_flags = data.get("features")
    if not isinstance(feature_flags, dict):
        return True, "ADMIN_SETTING_ABSENT"
    value = feature_flags.get("strategy_auditor_enabled")
    if value is False:
        return False, "ADMIN_SETTING_DISABLED"
    return True, "ADMIN_SETTING_ALLOWS"


def runtime_worker_config() -> Dict[str, Any]:
    enabled, enabled_reason = _env_enabled_flag()
    schedule_time, schedule_identity = _parse_schedule()
    result = {
        "component": "strategy_auditor",
        "status": "READY",
        "enabled": True,
        "enabled_reason": enabled_reason,
        "schedule_identity": schedule_identity,
        "worker_evaluation_interval_seconds": WORKER_EVALUATION_INTERVAL_SECONDS,
    }
    if not enabled:
        status = "INVALID_ENABLED_FLAG" if enabled_reason == "INVALID_ENABLED_FLAG" else "DISABLED"
        result.update({"status": status, "enabled": False})
        return result
    try:
        admin_enabled, admin_reason = _admin_strategy_auditor_enabled()
    except Exception as exc:
        error = _sanitize_error(exc, operation="load_admin_settings", path_label="config.admin_settings")
        result.update({
            "status": "ADMIN_SETTINGS_UNREADABLE",
            "enabled": False,
            "admin_reason": "ADMIN_SETTINGS_UNREADABLE",
            "error": error,
        })
        return result
    result["admin_reason"] = admin_reason
    if not admin_enabled:
        result.update({"status": "DISABLED_BY_ADMIN_SETTING", "enabled": False})
        return result
    if schedule_time is None:
        result.update({"status": schedule_identity["status"], "enabled": False})
        return result
    return result


@contextmanager
def _auditor_transaction_lock() -> Iterator[None]:
    if not _THREAD_LOCK.acquire(blocking=False):
        raise StrategyAuditorDuplicateRun("in-process strategy auditor lock is held")
    lock_file = None
    try:
        try:
            import fcntl
        except Exception as exc:
            raise StrategyAuditorRuntimeError("POSIX flock is unavailable") from exc

        os.makedirs(os.path.dirname(lock_path()), exist_ok=True)
        lock_file = open(lock_path(), "a+", encoding="utf-8")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise StrategyAuditorDuplicateRun("cross-process strategy auditor lock is held") from exc
        except OSError as exc:
            raise StrategyAuditorRuntimeError("POSIX flock failed") from exc

        lock_file.seek(0)
        lock_file.truncate()
        lock_file.write(
            "component=strategy_auditor "
            f"pid={os.getpid()} "
            f"started={time.time():.3f} "
            f"deployment={_deployment_id()}\n"
        )
        lock_file.flush()
        os.fsync(lock_file.fileno())
        yield
    finally:
        try:
            if lock_file is not None:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            if lock_file is not None:
                lock_file.close()
        finally:
            _THREAD_LOCK.release()


def _period_record(state: Dict[str, Any], report_period: str) -> Dict[str, Any]:
    periods = state.setdefault("periods", {})
    if report_period not in periods:
        periods[report_period] = {"attempts": [], "completed": False}
    return periods[report_period]


def _last_attempt_epoch(record: Dict[str, Any]) -> Optional[int]:
    attempts = record.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return None
    for attempt in reversed(attempts):
        if isinstance(attempt, dict) and isinstance(attempt.get("started_epoch"), int):
            return int(attempt["started_epoch"])
    return None


def _mark_interrupted_attempts(record: Dict[str, Any], now_iso: str) -> bool:
    changed = False
    attempts = record.get("attempts")
    if not isinstance(attempts, list):
        return False
    for attempt in attempts:
        if isinstance(attempt, dict) and attempt.get("status") == "STARTED":
            attempt["status"] = "INTERRUPTED"
            attempt["interrupted_at"] = now_iso
            changed = True
    return changed


def _artifact_reconciles_attempt(
    record: Dict[str, Any],
    report_period: str,
    settings: Dict[str, Any],
    required_outputs: List[str],
) -> Optional[Dict[str, Any]]:
    if "json" not in required_outputs:
        return None
    paths = auditor_lib.report_paths_for_date(report_period, settings)
    for output in required_outputs:
        if not os.path.isfile(paths[output]):
            return None
    try:
        report = _read_json_strict(paths["json"])
    except Exception:
        return None
    metadata = report.get("runtime_auditor")
    if not isinstance(metadata, dict):
        metadata = report.get("scheduling") if isinstance(report.get("scheduling"), dict) else {}
    attempt_id = metadata.get("attempt_id") if isinstance(metadata, dict) else None
    if not isinstance(attempt_id, str):
        return None
    attempts = record.get("attempts")
    if not isinstance(attempts, list):
        return None
    for attempt in attempts:
        if isinstance(attempt, dict) and attempt.get("attempt_id") == attempt_id:
            return {
                "attempt": attempt,
                "decision_count": report.get("decisions"),
                "report_paths": {key: paths[key] for key in required_outputs},
            }
    return None


def _apply_artifact_reconciliation(
    state: Dict[str, Any],
    record: Dict[str, Any],
    report_period: str,
    settings: Dict[str, Any],
    required_outputs: List[str],
    now_iso: str,
) -> bool:
    if record.get("completed"):
        return False
    reconciled = _artifact_reconciles_attempt(record, report_period, settings, required_outputs)
    if not reconciled:
        return False
    attempt = reconciled["attempt"]
    attempt["status"] = "COMPLETED"
    attempt["completed_at"] = now_iso
    attempt["decision_count"] = reconciled["decision_count"]
    attempt["report_paths"] = reconciled["report_paths"]
    record["completed"] = True
    record["completed_attempt_id"] = attempt.get("attempt_id")
    record["completed_at"] = now_iso
    record["decision_count"] = reconciled["decision_count"]
    record["report_paths"] = reconciled["report_paths"]
    state["last_seen_period"] = max(str(state.get("last_seen_period") or report_period), report_period)
    return True


def _build_attempt(
    *,
    attempt_id: str,
    mode: str,
    now: _dt.datetime,
    schedule_identity: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "attempt_id": attempt_id,
        "status": "STARTED",
        "mode": mode,
        "started_at": _iso(now),
        "started_epoch": _epoch(now),
        "timezone": "UTC",
        "schedule_identity": schedule_identity,
        "pid": os.getpid(),
        "deployment_id": _deployment_id(),
        "policy": {
            "max_attempts_per_period": MAX_ATTEMPTS_PER_PERIOD,
            "retry_backoff_seconds": RETRY_BACKOFF_SECONDS,
        },
    }


def _complete_from_record(base: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    result["status"] = "ALREADY_COMPLETED"
    result["attempt_id"] = record.get("completed_attempt_id")
    result["completed_at"] = record.get("completed_at")
    result["decision_count"] = record.get("decision_count")
    result["report_paths"] = dict(record.get("report_paths") or {})
    return result


def run_auditor(
    *,
    mode: str = "manual",
    now: Optional[_dt.datetime] = None,
    settings_path: Optional[str] = None,
    schedule_identity: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        start_now = _aware_utc(now)
    except Exception as exc:
        result = _base_result(status="INVALID_CLOCK", mode=mode, now=_utc_now(), schedule_identity=schedule_identity)
        result["error"] = _sanitize_error(exc, operation="validate_clock")
        return _guarded_status_or_stderr(result, settings_path=settings_path)

    report_period = _period(start_now)
    result = _base_result(
        status="STARTED",
        mode=mode,
        now=start_now,
        report_period=report_period,
        schedule_identity=schedule_identity,
    )

    try:
        settings = auditor_lib.load_settings(settings_path)
        _guard_path_aliases(settings, report_period)
        if not _reports_enabled(settings):
            result["status"] = "DISABLED_BY_REPORTS_SETTING"
            result["enabled"] = False
            result = _guarded_status_or_stderr(result, report_period=report_period, settings_path=settings_path)
            _guarded_journal_event(
                "warning",
                "STRATEGY_AUDITOR_REPORTS_DISABLED",
                "Strategy auditor reports are disabled by settings.",
                {"report_period": report_period, "mode": mode},
                report_period=report_period,
                settings_path=settings_path,
                throttle=True,
            )
            return result
        required_outputs = _required_outputs(settings, mode=mode)
    except Exception as exc:
        result["status"] = "CONFIGURATION_ERROR"
        result["error"] = _sanitize_error(exc, operation="load_or_validate_settings")
        if isinstance(exc, StrategyAuditorPathError):
            _stderr_fallback(result)
            return result
        result = _guarded_status_or_stderr(result, report_period=report_period, settings_path=settings_path)
        if result.get("error", {}).get("operation") == "diagnostic_write_guard":
            return result
        _guarded_journal_event(
            "error",
            "STRATEGY_AUDITOR_CONFIGURATION_ERROR",
            "Strategy auditor configuration is invalid.",
            {"status": result["status"], "error": result["error"]},
            report_period=report_period,
            settings_path=settings_path,
        )
        return result

    try:
        _ensure_runtime_dirs(settings)
        with _auditor_transaction_lock():
            state = _load_state()
            last_seen = state.get("last_seen_period")
            if isinstance(last_seen, str) and last_seen and report_period < last_seen:
                result["status"] = "CLOCK_ROLLBACK_DETECTED"
                result["error"] = {
                    "error_type": "ClockRollbackDetected",
                    "message": "Strategy auditor refused to run for an earlier UTC period.",
                    "operation": "period_guard",
                }
                _write_status(result)
                _journal_event(
                    "warning",
                    "STRATEGY_AUDITOR_CLOCK_ROLLBACK",
                    "Strategy auditor refused an earlier UTC period.",
                    {"report_period": report_period, "last_seen_period": last_seen},
                )
                return result

            record = _period_record(state, report_period)
            now_iso = _iso(start_now)
            if _apply_artifact_reconciliation(state, record, report_period, settings, required_outputs, now_iso):
                _save_state(state)
                completed = _complete_from_record(result, record)
                _write_status(completed)
                _journal_event(
                    "warning",
                    "STRATEGY_AUDITOR_PERIOD_ALREADY_COMPLETED",
                    "Strategy auditor period already has completed artifacts.",
                    {"report_period": report_period, "attempt_id": completed.get("attempt_id")},
                    throttle=True,
                )
                return completed

            if record.get("completed"):
                completed = _complete_from_record(result, record)
                _write_status(completed)
                _journal_event(
                    "warning",
                    "STRATEGY_AUDITOR_PERIOD_ALREADY_COMPLETED",
                    "Strategy auditor period is already complete.",
                    {"report_period": report_period, "attempt_id": completed.get("attempt_id")},
                    throttle=True,
                )
                return completed

            if _mark_interrupted_attempts(record, now_iso):
                _save_state(state)

            attempts = record.get("attempts")
            if not isinstance(attempts, list):
                raise StrategyAuditorStateCorrupt("period attempts are corrupt")

            last_epoch = _last_attempt_epoch(record)
            if last_epoch is not None and _epoch(start_now) - last_epoch < RETRY_BACKOFF_SECONDS:
                result["status"] = "RETRY_COOLDOWN"
                result["error"] = {
                    "error_type": "RetryCooldownActive",
                    "message": "Strategy auditor retry backoff is active.",
                    "operation": "retry_policy",
                }
                _write_status(result)
                _journal_event(
                    "warning",
                    "STRATEGY_AUDITOR_RETRY_COOLDOWN",
                    "Strategy auditor retry backoff is active.",
                    {"report_period": report_period},
                    throttle=True,
                )
                return result

            if len(attempts) >= MAX_ATTEMPTS_PER_PERIOD:
                result["status"] = "RETRY_LIMIT_REACHED"
                result["error"] = {
                    "error_type": "RetryLimitReached",
                    "message": "Strategy auditor retry limit reached for this UTC period.",
                    "operation": "retry_policy",
                }
                _write_status(result)
                _journal_event(
                    "error",
                    "STRATEGY_AUDITOR_RETRY_LIMIT_REACHED",
                    "Strategy auditor retry limit reached.",
                    {"report_period": report_period, "attempts": len(attempts)},
                    throttle=True,
                )
                return result

            attempt_id = f"{report_period}-{uuid.uuid4().hex[:12]}"
            attempt = _build_attempt(
                attempt_id=attempt_id,
                mode=mode,
                now=start_now,
                schedule_identity=result["schedule_identity"],
            )
            attempts.append(attempt)
            state["last_seen_period"] = max(str(state.get("last_seen_period") or report_period), report_period)
            _save_state(state)
            _journal_event(
                "warning",
                "STRATEGY_AUDITOR_RUN_STARTED",
                "Strategy auditor run started.",
                {"report_period": report_period, "attempt_id": attempt_id, "mode": mode},
            )

            result["attempt_id"] = attempt_id
            try:
                events = auditor_lib.load_all_events(settings)
                analysis_window = {
                    "scope": "all_available_history",
                    "report_period_utc": report_period,
                    "source_history": "all_available_source_records",
                }
                scheduling = {
                    "mode": mode,
                    "timezone": "UTC",
                    "report_period_utc": report_period,
                    "attempt_id": attempt_id,
                    "started_at": result["started_at"],
                    "schedule_identity": result["schedule_identity"],
                    "policy": result["policy"],
                }
                report = auditor_lib.build_report(
                    events,
                    settings,
                    report_date=report_period,
                    scheduling_metadata=scheduling,
                    analysis_window=analysis_window,
                )
                report["runtime_auditor"] = {
                    "attempt_id": attempt_id,
                    "report_period_utc": report_period,
                    "timezone": "UTC",
                    "state_path_authority": "core.storage.state_path",
                }
                report_paths = auditor_lib.write_reports(report, settings)
                completed_at = _iso(_utc_now())
                completed_state = copy.deepcopy(state)
                completed_record = completed_state["periods"][report_period]
                completed_attempt = completed_record["attempts"][-1]
                completed_attempt["status"] = "COMPLETED"
                completed_attempt["completed_at"] = completed_at
                completed_attempt["decision_count"] = report.get("decisions")
                completed_attempt["report_paths"] = dict(report_paths)
                completed_record["completed"] = True
                completed_record["completed_attempt_id"] = attempt_id
                completed_record["completed_at"] = completed_at
                completed_record["decision_count"] = report.get("decisions")
                completed_record["report_paths"] = dict(report_paths)
                _save_state(completed_state)
                result["status"] = "SUCCESS"
                result["completed_at"] = completed_at
                result["decision_count"] = report.get("decisions")
                result["report_paths"] = dict(report_paths)
                _write_status(result)
                _journal_event(
                    "warning",
                    "STRATEGY_AUDITOR_RUN_COMPLETED",
                    "Strategy auditor run completed.",
                    {
                        "report_period": report_period,
                        "attempt_id": attempt_id,
                        "decision_count": report.get("decisions"),
                    },
                )
                return result
            except Exception as exc:
                failed_at = _iso(_utc_now())
                attempt["status"] = "FAILED"
                attempt["completed_at"] = failed_at
                attempt["error"] = _sanitize_error(exc, operation="build_or_write_report")
                _save_state(state)
                result["status"] = "FAILED"
                result["completed_at"] = failed_at
                result["error"] = attempt["error"]
                _write_status(result)
                _journal_event(
                    "error",
                    "STRATEGY_AUDITOR_RUN_FAILED",
                    "Strategy auditor run failed.",
                    {"report_period": report_period, "attempt_id": attempt_id, "error": result["error"]},
                    throttle=True,
                )
                return result
    except StrategyAuditorDuplicateRun:
        result["status"] = "DUPLICATE_IN_PROGRESS"
        _write_status(result)
        _journal_event(
            "warning",
            "STRATEGY_AUDITOR_DUPLICATE_SUPPRESSED",
            "Strategy auditor duplicate invocation was suppressed.",
            {"report_period": report_period, "mode": mode},
            throttle=True,
        )
        return result
    except StrategyAuditorStateCorrupt as exc:
        result["status"] = "STATE_CORRUPT"
        result["error"] = _sanitize_error(exc, operation="load_state", path_label="state.strategy_auditor_state")
        _write_status(result)
        _journal_event(
            "error",
            "STRATEGY_AUDITOR_STATE_CORRUPT",
            "Strategy auditor state is corrupt.",
            {"report_period": report_period, "error": result["error"]},
        )
        return result
    except Exception as exc:
        result["status"] = "FAILED"
        result["error"] = _sanitize_error(exc, operation="runtime_transaction")
        _write_status(result)
        _journal_event(
            "error",
            "STRATEGY_AUDITOR_RUNTIME_FAILED",
            "Strategy auditor runtime transaction failed.",
            {"report_period": report_period, "error": result["error"]},
        )
        return result


def evaluate_scheduled_once(
    *,
    now: Optional[_dt.datetime] = None,
    settings_path: Optional[str] = None,
) -> Dict[str, Any]:
    config = runtime_worker_config()
    schedule_identity = dict(config.get("schedule_identity") or {})
    if config.get("status") != "READY":
        result = _base_result(
            status=str(config.get("status")),
            mode="scheduled",
            now=now,
            schedule_identity=schedule_identity,
        )
        result["enabled"] = bool(config.get("enabled"))
        if config.get("error"):
            result["error"] = config["error"]
        try:
            guard_period = _period(_aware_utc(now))
        except Exception:
            guard_period = None
        result = _guarded_status_or_stderr(result, report_period=guard_period, settings_path=settings_path)
        if result["status"] == "CONFIGURATION_ERROR":
            return result
        if result["status"] not in {"DISABLED"}:
            _guarded_journal_event(
                "warning",
                f"STRATEGY_AUDITOR_{result['status']}",
                "Strategy auditor scheduler is not active.",
                {"status": result["status"], "schedule_identity": schedule_identity},
                report_period=guard_period,
                settings_path=settings_path,
            )
        return result

    try:
        now_utc = _aware_utc(now)
    except Exception as exc:
        result = _base_result(status="INVALID_CLOCK", mode="scheduled", now=_utc_now(), schedule_identity=schedule_identity)
        result["error"] = _sanitize_error(exc, operation="validate_clock")
        return _guarded_status_or_stderr(result, settings_path=settings_path)

    schedule_time, _identity = _parse_schedule(str(schedule_identity.get("configured_time_utc") or ""))
    if schedule_time is None:
        result = _base_result(status="SCHEDULE_NOT_CONFIGURED", mode="scheduled", now=now_utc, schedule_identity=schedule_identity)
        result = _guarded_status_or_stderr(result, report_period=_period(now_utc), settings_path=settings_path)
        return result

    due_time = now_utc.timetz()
    if due_time < schedule_time:
        result = _base_result(status="NOT_DUE", mode="scheduled", now=now_utc, schedule_identity=schedule_identity)
        result["next_due_date"] = _period(now_utc)
        result = _guarded_status_or_stderr(result, report_period=_period(now_utc), settings_path=settings_path)
        _guarded_journal_event(
            "warning",
            "STRATEGY_AUDITOR_NOT_DUE",
            "Strategy auditor scheduled run is not due yet.",
            {"report_period": _period(now_utc), "status": "NOT_DUE"},
            report_period=_period(now_utc),
            settings_path=settings_path,
            throttle=True,
        )
        return result

    return run_auditor(
        mode="scheduled",
        now=now_utc,
        settings_path=settings_path,
        schedule_identity=schedule_identity,
    )


def worker_loop(
    stop_event: threading.Event,
    *,
    now_provider: Optional[Callable[[], _dt.datetime]] = None,
) -> None:
    while not stop_event.is_set():
        try:
            evaluate_scheduled_once(now=now_provider() if now_provider else None)
        except Exception as exc:
            result = _base_result(status="FAILED", mode="scheduled")
            result["error"] = _sanitize_error(exc, operation="worker_loop")
            result = _guarded_status_or_stderr(result)
            _guarded_journal_event(
                "error",
                "STRATEGY_AUDITOR_WORKER_FAILED",
                "Strategy auditor worker evaluation failed.",
                {"error": result["error"]},
            )
        stop_event.wait(WORKER_EVALUATION_INTERVAL_SECONDS)


def start_worker(
    stop_event: Optional[threading.Event] = None,
    *,
    now_provider: Optional[Callable[[], _dt.datetime]] = None,
) -> Dict[str, Any]:
    config = runtime_worker_config()
    result = {
        "component": "strategy_auditor",
        "status": config.get("status"),
        "worker_started": False,
        "enabled": config.get("enabled"),
        "schedule_identity": config.get("schedule_identity"),
    }
    if config.get("error"):
        result["error"] = config["error"]
    if config.get("status") != "READY":
        result = _guarded_status_or_stderr(result)
        if result["status"] == "CONFIGURATION_ERROR":
            return result
        if result["status"] not in {"DISABLED"}:
            _guarded_journal_event(
                "warning",
                f"STRATEGY_AUDITOR_{result['status']}",
                "Strategy auditor worker was not started.",
                {"status": result["status"], "schedule_identity": result.get("schedule_identity")},
            )
        return result

    try:
        settings = auditor_lib.load_settings()
    except Exception:
        settings = None
    if isinstance(settings, dict) and not _reports_enabled(settings):
        result.update({"status": "DISABLED_BY_REPORTS_SETTING", "worker_started": False, "enabled": False})
        result = _guarded_status_or_stderr(result)
        if result["status"] != "CONFIGURATION_ERROR":
            _guarded_journal_event(
                "warning",
                "STRATEGY_AUDITOR_REPORTS_DISABLED",
                "Strategy auditor worker was not started because reports are disabled.",
                {"status": result["status"], "schedule_identity": result.get("schedule_identity")},
                throttle=True,
            )
        return result
    if isinstance(settings, dict):
        try:
            _required_outputs(settings, mode="scheduled")
        except Exception as exc:
            result.update({
                "status": "CONFIGURATION_ERROR",
                "worker_started": False,
                "enabled": False,
                "error": _sanitize_error(exc, operation="load_or_validate_settings"),
            })
            result = _guarded_status_or_stderr(result)
            if result["status"] != "CONFIGURATION_ERROR" or result.get("diagnostic_write_blocked") is None:
                _guarded_journal_event(
                    "error",
                    "STRATEGY_AUDITOR_CONFIGURATION_ERROR",
                    "Strategy auditor worker output configuration is invalid.",
                    {"status": result["status"], "error": result.get("error")},
                )
            return result

    guard_error = _diagnostic_guard_error()
    if guard_error is not None:
        result.update({"status": "CONFIGURATION_ERROR", "worker_started": False, "error": guard_error})
        _stderr_fallback(result)
        return result

    event = stop_event or threading.Event()
    thread = threading.Thread(
        target=worker_loop,
        kwargs={"stop_event": event, "now_provider": now_provider},
        name="strategy-auditor",
        daemon=True,
    )
    result.update({"status": "WORKER_STARTED", "worker_started": True, "thread": thread, "stop_event": event})
    _write_status({key: value for key, value in result.items() if key not in {"thread", "stop_event"}})
    thread.start()
    return result


def exit_code_for_result(result: Dict[str, Any]) -> int:
    status = str(result.get("status") or "")
    if status in {
        "SUCCESS",
        "ALREADY_COMPLETED",
        "DUPLICATE_IN_PROGRESS",
        "RETRY_COOLDOWN",
        "NOT_DUE",
        "DISABLED",
        "DISABLED_BY_REPORTS_SETTING",
    }:
        return 0
    return 1


def result_for_cli(result: Dict[str, Any]) -> Dict[str, Any]:
    return _sanitize_value({key: value for key, value in result.items() if key not in {"thread", "stop_event"}})
