from __future__ import annotations

import datetime as _dt
import os
import threading
from typing import Any, Callable, Dict, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools import strategy_auditor_runtime as runtime


LOCAL_TIME_ENV = "STRATEGY_AUDITOR_DAILY_TIME"
TIMEZONE_ENV = "STRATEGY_AUDITOR_TIMEZONE"
LEGACY_UTC_TIME_ENV = "STRATEGY_AUDITOR_DAILY_TIME_UTC"
_LOCAL_PERIOD_LOCK = threading.RLock()
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def local_schedule_config_present() -> bool:
    return bool(os.getenv(LOCAL_TIME_ENV, "").strip() or os.getenv(TIMEZONE_ENV, "").strip())


def _parse_hhmm(raw: str) -> Optional[Tuple[int, int]]:
    value = raw.strip()
    if len(value) != 5 or value[2] != ":":
        return None
    digits = value[:2] + value[3:]
    if any(char not in "0123456789" for char in digits):
        return None
    hour = int(value[:2])
    minute = int(value[3:])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


def _enabled_flag() -> Tuple[bool, str]:
    raw = os.getenv("STRATEGY_AUDITOR_ENABLED")
    if raw is None or not raw.strip():
        return False, "ENV_NOT_ENABLED"
    normalized = raw.strip().lower()
    if normalized in _TRUTHY:
        return True, "ENABLED"
    if normalized in _FALSY:
        return False, "ENV_DISABLED"
    return False, "INVALID_ENABLED_FLAG"


def _zone(name: str) -> Optional[ZoneInfo]:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def runtime_worker_config() -> Dict[str, Any]:
    enabled, enabled_reason = _enabled_flag()
    local_time_raw = os.getenv(LOCAL_TIME_ENV, "").strip()
    timezone_raw = os.getenv(TIMEZONE_ENV, "").strip()
    legacy_utc_raw = os.getenv(LEGACY_UTC_TIME_ENV, "").strip()

    identity: Dict[str, Any] = {
        "source": f"{LOCAL_TIME_ENV}+{TIMEZONE_ENV}",
        "configured_time_local": local_time_raw or None,
        "timezone": timezone_raw or None,
        "status": "LOCAL_SCHEDULE_NOT_CONFIGURED",
    }
    result: Dict[str, Any] = {
        "component": "strategy_auditor",
        "status": "READY",
        "enabled": True,
        "enabled_reason": enabled_reason,
        "schedule_identity": identity,
        "worker_evaluation_interval_seconds": runtime.WORKER_EVALUATION_INTERVAL_SECONDS,
        "schedule_mode": "LOCAL_CIVIL_TIME",
    }

    if not enabled:
        status = "INVALID_ENABLED_FLAG" if enabled_reason == "INVALID_ENABLED_FLAG" else "DISABLED"
        result.update({"status": status, "enabled": False})
        return result

    if not local_time_raw and not timezone_raw:
        result.update({"status": "LOCAL_SCHEDULE_NOT_CONFIGURED", "enabled": False})
        return result
    if not local_time_raw or not timezone_raw:
        identity["status"] = "LOCAL_SCHEDULE_INCOMPLETE"
        result.update({"status": "LOCAL_SCHEDULE_INCOMPLETE", "enabled": False})
        return result
    if legacy_utc_raw:
        identity["status"] = "SCHEDULE_CONFIGURATION_CONFLICT"
        result.update({"status": "SCHEDULE_CONFIGURATION_CONFLICT", "enabled": False})
        return result

    parsed = _parse_hhmm(local_time_raw)
    if parsed is None:
        identity["status"] = "INVALID_LOCAL_SCHEDULE"
        result.update({"status": "INVALID_LOCAL_SCHEDULE", "enabled": False})
        return result

    zone = _zone(timezone_raw)
    if zone is None:
        identity["status"] = "INVALID_TIMEZONE"
        result.update({"status": "INVALID_TIMEZONE", "enabled": False})
        return result

    try:
        admin_enabled, admin_reason = runtime._admin_strategy_auditor_enabled()
    except Exception as exc:
        result.update(
            {
                "status": "ADMIN_SETTINGS_UNREADABLE",
                "enabled": False,
                "admin_reason": "ADMIN_SETTINGS_UNREADABLE",
                "error": runtime._sanitize_error(
                    exc,
                    operation="load_admin_settings",
                    path_label="config.admin_settings",
                ),
            }
        )
        return result

    result["admin_reason"] = admin_reason
    if not admin_enabled:
        result.update({"status": "DISABLED_BY_ADMIN_SETTING", "enabled": False})
        return result

    hour, minute = parsed
    identity.update(
        {
            "configured_time_local": f"{hour:02d}:{minute:02d}",
            "timezone": timezone_raw,
            "status": "CONFIGURED_LOCAL_TIME",
        }
    )
    return result


def _local_context(now_utc: _dt.datetime, config: Dict[str, Any]) -> Tuple[_dt.datetime, ZoneInfo, int, int]:
    identity = dict(config.get("schedule_identity") or {})
    timezone_name = str(identity.get("timezone") or "")
    zone = _zone(timezone_name)
    if zone is None:
        raise ValueError("invalid configured timezone")
    parsed = _parse_hhmm(str(identity.get("configured_time_local") or ""))
    if parsed is None:
        raise ValueError("invalid configured local schedule")
    hour, minute = parsed
    local_now = now_utc.astimezone(zone)
    return local_now, zone, hour, minute


def local_report_period(now: _dt.datetime, timezone_name: str) -> str:
    now_utc = runtime._aware_utc(now)
    zone = _zone(timezone_name)
    if zone is None:
        raise ValueError("invalid configured timezone")
    return now_utc.astimezone(zone).date().isoformat()


def local_due_utc(report_date: _dt.date, timezone_name: str, local_time: str) -> _dt.datetime:
    zone = _zone(timezone_name)
    parsed = _parse_hhmm(local_time)
    if zone is None or parsed is None:
        raise ValueError("invalid local schedule")
    hour, minute = parsed
    local_due = _dt.datetime(
        report_date.year,
        report_date.month,
        report_date.day,
        hour,
        minute,
        tzinfo=zone,
    )
    return local_due.astimezone(_dt.UTC)


def _schedule_identity_for_now(config: Dict[str, Any], local_now: _dt.datetime) -> Dict[str, Any]:
    identity = dict(config.get("schedule_identity") or {})
    offset = local_now.utcoffset()
    offset_seconds = int(offset.total_seconds()) if offset is not None else 0
    sign = "+" if offset_seconds >= 0 else "-"
    absolute = abs(offset_seconds)
    offset_h, remainder = divmod(absolute, 3600)
    offset_m = remainder // 60
    identity["effective_utc_offset"] = f"{sign}{offset_h:02d}:{offset_m:02d}"
    identity["local_report_period"] = local_now.date().isoformat()
    return identity


def _run_local_period(
    *,
    now_utc: _dt.datetime,
    zone: ZoneInfo,
    settings_path: Optional[str],
    schedule_identity: Dict[str, Any],
    mode: str,
) -> Dict[str, Any]:
    # R-019's durable transaction remains authoritative. This narrow adapter
    # changes only its report-period projection from UTC date to the configured
    # civil date while the transaction is executing. All normal entry points
    # select this adapter when local schedule configuration is present.
    with _LOCAL_PERIOD_LOCK:
        original_period = runtime._period

        def _period_in_configured_zone(value: _dt.datetime) -> str:
            return runtime._aware_utc(value).astimezone(zone).date().isoformat()

        runtime._period = _period_in_configured_zone
        try:
            return runtime.run_auditor(
                mode=mode,
                now=now_utc,
                settings_path=settings_path,
                schedule_identity=schedule_identity,
            )
        finally:
            runtime._period = original_period


def run_auditor(
    *,
    mode: str = "manual",
    now: Optional[_dt.datetime] = None,
    settings_path: Optional[str] = None,
) -> Dict[str, Any]:
    config = runtime_worker_config()
    if config.get("status") != "READY":
        if not local_schedule_config_present():
            return runtime.run_auditor(mode=mode, now=now, settings_path=settings_path)
        result = runtime._base_result(
            status=str(config.get("status") or "CONFIGURATION_ERROR"),
            mode=mode,
            now=now,
            schedule_identity=dict(config.get("schedule_identity") or {}),
        )
        result["enabled"] = bool(config.get("enabled"))
        if config.get("error"):
            result["error"] = config["error"]
        return runtime._guarded_status_or_stderr(result, settings_path=settings_path)

    now_utc = runtime._aware_utc(now)
    local_now, zone, _hour, _minute = _local_context(now_utc, config)
    identity = _schedule_identity_for_now(config, local_now)
    return _run_local_period(
        now_utc=now_utc,
        zone=zone,
        settings_path=settings_path,
        schedule_identity=identity,
        mode=mode,
    )


def evaluate_scheduled_once(
    *,
    now: Optional[_dt.datetime] = None,
    settings_path: Optional[str] = None,
) -> Dict[str, Any]:
    config = runtime_worker_config()
    identity = dict(config.get("schedule_identity") or {})
    if config.get("status") != "READY":
        result = runtime._base_result(
            status=str(config.get("status") or "CONFIGURATION_ERROR"),
            mode="scheduled",
            now=now,
            schedule_identity=identity,
        )
        result["enabled"] = bool(config.get("enabled"))
        if config.get("error"):
            result["error"] = config["error"]
        result = runtime._guarded_status_or_stderr(result, settings_path=settings_path)
        if result.get("status") not in {"DISABLED"}:
            runtime._guarded_journal_event(
                "warning",
                f"STRATEGY_AUDITOR_{result['status']}",
                "Strategy auditor local-time scheduler is not active.",
                {"status": result["status"], "schedule_identity": identity},
                settings_path=settings_path,
                throttle=True,
            )
        return result

    try:
        now_utc = runtime._aware_utc(now)
        local_now, zone, hour, minute = _local_context(now_utc, config)
    except Exception as exc:
        result = runtime._base_result(
            status="INVALID_CLOCK",
            mode="scheduled",
            now=runtime._utc_now(),
            schedule_identity=identity,
        )
        result["error"] = runtime._sanitize_error(exc, operation="validate_local_clock")
        return runtime._guarded_status_or_stderr(result, settings_path=settings_path)

    identity = _schedule_identity_for_now(config, local_now)
    local_period = local_now.date().isoformat()
    if (local_now.hour, local_now.minute) < (hour, minute):
        result = runtime._base_result(
            status="NOT_DUE",
            mode="scheduled",
            now=now_utc,
            report_period=local_period,
            schedule_identity=identity,
        )
        result["next_due_local"] = f"{local_period}T{hour:02d}:{minute:02d}"
        return runtime._guarded_status_or_stderr(
            result,
            report_period=local_period,
            settings_path=settings_path,
        )

    return _run_local_period(
        now_utc=now_utc,
        zone=zone,
        settings_path=settings_path,
        schedule_identity=identity,
        mode="scheduled",
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
            runtime.record_diagnostic(
                status="FAILED",
                code="STRATEGY_AUDITOR_LOCAL_TIME_WORKER_FAILED",
                message="Strategy auditor local-time worker evaluation failed.",
                context={"error_type": type(exc).__name__},
                severity="ERROR",
            )
        stop_event.wait(runtime.WORKER_EVALUATION_INTERVAL_SECONDS)


def start_worker(
    stop_event: Optional[threading.Event] = None,
    *,
    now_provider: Optional[Callable[[], _dt.datetime]] = None,
) -> Dict[str, Any]:
    config = runtime_worker_config()
    result: Dict[str, Any] = {
        "component": "strategy_auditor",
        "status": config.get("status"),
        "worker_started": False,
        "enabled": config.get("enabled"),
        "schedule_identity": config.get("schedule_identity"),
        "schedule_mode": "LOCAL_CIVIL_TIME",
    }
    if config.get("error"):
        result["error"] = config["error"]
    if config.get("status") != "READY":
        runtime._guarded_status_or_stderr(result)
        return result

    event = stop_event or threading.Event()
    thread = threading.Thread(
        target=worker_loop,
        kwargs={"stop_event": event, "now_provider": now_provider},
        name="strategy-auditor-local-time",
        daemon=True,
    )
    result.update({"status": "WORKER_STARTED", "worker_started": True, "thread": thread, "stop_event": event})
    runtime._write_status({key: value for key, value in result.items() if key not in {"thread", "stop_event"}})
    thread.start()
    return result
