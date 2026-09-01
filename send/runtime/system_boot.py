# /opt/binarybot/runtime/system_boot.py
# BinaryBot — System Boot Loader

from __future__ import annotations

import atexit
import os
import signal
import threading
import time
from pathlib import Path

from core import storage


def _load_env_file() -> None:
    """
    Load a runtime env file into os.environ before runtime imports.
    Does not override variables that already exist in the environment.
    """
    override = os.getenv("BINARYBOT_ENV_FILE", "").strip()
    if override:
        env_path = Path(override).expanduser()
        if not env_path.is_absolute():
            raise RuntimeError(f"BINARYBOT_ENV_FILE must be an absolute path: {override}")
        if not env_path.is_file():
            raise RuntimeError(f"BINARYBOT_ENV_FILE does not exist: {env_path}")
    else:
        candidates = [
            Path(storage.root_path(".env")),
            Path(storage.root_path("config", ".env")),
        ]
        env_path = next((candidate for candidate in candidates if candidate.is_file()), None)

    if env_path is None:
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()

from runtime.engine_loop import ENGINE_TICK_SECONDS, start_engine
from runtime.telegram_updates import poll_updates
from runtime.distribution_scheduler import scheduler_loop
from runtime.telemetry_market_worker import telemetry_market_loop
from runtime import runtime_status, startup_preflight
from core import fsm_runtime
from core import distribution_router
from core import telegram_app_nav
from core.observability_logger import build_event, log_event, log_warning, send_control_notification
from monitoring.restart_guard import mark_graceful_shutdown, record_start
from snapshots import snapshot_manager


_SHUTDOWN_MARKED = False


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _should_start_telegram_thread() -> bool:
    if not _env_flag("ENABLE_TELEGRAM", default=False):
        log_warning(
            warn_type="telegram_disabled",
            message="Telegram polling disabled by environment",
            context={"component": "telegram_polling", "reason": "disabled_by_env"},
            source={"module": "system_boot", "function": "_should_start_telegram_thread"},
        )
        return False
    if os.getenv("TELEGRAM_BOT_TOKEN", "").strip():
        return True
    log_warning(
        warn_type="telegram_token_missing",
        message="Telegram polling disabled because TELEGRAM_BOT_TOKEN is missing",
        context={"component": "telegram_polling", "reason": "token_missing"},
        source={"module": "system_boot", "function": "_should_start_telegram_thread"},
    )
    return False


def _mark_graceful_shutdown() -> None:
    global _SHUTDOWN_MARKED
    if _SHUTDOWN_MARKED:
        return
    _SHUTDOWN_MARKED = True
    try:
        runtime_status.write_status("stopping", "BinaryBot runtime stopping")
    except Exception:
        pass
    try:
        snapshot_manager.create_snapshot()
    except Exception as exc:
        log_event({
            "event_type": "error",
            "severity": "ERROR",
            "error_type": "SNAPSHOT_CREATE_FAILED",
            "message": "Failed to create shutdown snapshot",
            "context": {"error": str(exc)},
            "source": {"module": "system_boot", "function": "_mark_graceful_shutdown"},
        })
    try:
        mark_graceful_shutdown()
    except Exception as exc:
        log_event({
            "event_type": "error",
            "severity": "ERROR",
            "error_type": "GRACEFUL_SHUTDOWN_MARK_FAILED",
            "message": "Failed to persist graceful shutdown marker",
            "context": {"error": str(exc)},
            "source": {"module": "system_boot", "function": "_mark_graceful_shutdown"},
        })
    try:
        runtime_status.write_status("stopped", "BinaryBot runtime stopped gracefully")
    except Exception:
        pass
    send_control_notification("GRACEFUL SHUTDOWN", "BinaryBot runtime stopped gracefully")


def _handle_shutdown_signal(signum, _frame) -> None:
    log_event(build_event(
        "engine_stop",
        {"message": f"BinaryBot runtime stopping on signal {signum}"},
        source={"module": "system_boot", "function": "_handle_shutdown_signal"},
    ))
    _mark_graceful_shutdown()
    raise SystemExit(0)


def _register_shutdown_hooks() -> None:
    atexit.register(_mark_graceful_shutdown)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_shutdown_signal)


def _block_for_preflight_failure(start_info, exc: Exception) -> bool:
    runtime_status.write_status(
        "blocked",
        "Critical startup preflight failed",
        error=str(exc),
        recovery_required=bool(start_info["recovery_required"]),
        recovery_state="UNSAFE_BLOCKED",
        startup_preflight_state="UNSAFE_BLOCKED",
    )
    log_event(build_event(
        "recovery_completed",
        {
            "message": "BinaryBot startup preflight failed",
            "result": "UNSAFE_BLOCKED",
            "blocked": True,
            "restart_count": int(start_info["restart_count"]),
            "blocked_operations": ["engine_start", "scheduler_loop", "telemetry_market_loop"],
        },
        source={"module": "system_boot", "function": "start_system"},
    ))
    log_event({
        "event_type": "error",
        "severity": "CRITICAL",
        "error_type": "STARTUP_PREFLIGHT_FAILED",
        "message": "Critical startup preflight failed; live workers were not started",
        "context": {"error": str(exc)},
        "source": {"module": "system_boot", "function": "start_system"},
    })
    send_control_notification("STARTUP BLOCKED", "Critical startup preflight failed.")
    return False


def start_system() -> bool | None:
    _register_shutdown_hooks()
    try:
        start_info = record_start()
    except Exception as start_exc:
        log_event({
            "event_type": "error",
            "severity": "WARNING",
            "error_type": "RESTART_GUARD_LOAD_FAILED",
            "message": "record_start() failed; treating as degraded-safe start",
            "context": {"error": str(start_exc)},
            "source": {"module": "system_boot", "function": "start_system"},
        })
        start_info = {
            "crash_loop": False,
            "counted_restart": True,
            "recovery_required": True,
            "restart_count": 0,
            "window_seconds": 60,
            "max_restarts": 3,
            "previous_shutdown_kind": "unknown",
        }

    runtime_status.write_status(
        "starting",
        "BinaryBot runtime bootstrap starting",
        shadow_mode=_env_flag("SHADOW_MODE", default=False),
        readiness_evaluated=_env_flag("RAILWAY_READINESS_EVALUATED", default=False),
        recovery_required=bool(start_info["recovery_required"]),
        recovery_state="STARTING",
        market_data_state="UNKNOWN",
        startup_preflight_state="PENDING",
    )
    if start_info["recovery_required"]:
        send_control_notification("RECOVERY STARTED", "BinaryBot recovery bootstrap started.")
    log_event(build_event(
        "recovery_started",
        {
            "message": "BinaryBot recovery bootstrap started",
            "restart_count": int(start_info["restart_count"]),
            "window_seconds": int(start_info["window_seconds"]),
            "max_restarts": int(start_info["max_restarts"]),
            "previous_shutdown_kind": str(start_info["previous_shutdown_kind"]),
            "recovery_required": bool(start_info["recovery_required"]),
        },
        source={"module": "system_boot", "function": "start_system"},
    ))

    try:
        preflight = startup_preflight.run_startup_preflight(require_shadow_mode=False)
    except startup_preflight.StartupPreflightError as exc:
        return _block_for_preflight_failure(start_info, exc)

    runtime_status.update_status(
        startup_preflight_state="READY",
        startup_preflight_provider=preflight.get("active_provider"),
        startup_preflight_effective_symbols=list(preflight.get("effective_symbols") or []),
    )

    try:
        fsm_runtime.load_state()
        distribution_router.load_state()
    except Exception as exc:
        runtime_status.write_status(
            "blocked",
            "Runtime state validation failed during boot",
            error=str(exc),
            recovery_required=bool(start_info["recovery_required"]),
            recovery_state="UNSAFE_BLOCKED",
            startup_preflight_state="READY",
        )
        log_event(build_event(
            "recovery_completed",
            {
                "message": "BinaryBot recovery bootstrap failed",
                "result": "UNSAFE_BLOCKED",
                "blocked": True,
                "restart_count": int(start_info["restart_count"]),
                "blocked_operations": ["engine_start", "telegram_poll", "scheduler_loop", "telemetry_market_loop"],
            },
            source={"module": "system_boot", "function": "start_system"},
        ))
        log_event({
            "event_type": "error",
            "severity": "CRITICAL",
            "error_type": "RECOVERY_VALIDATION_FAILED",
            "message": "Runtime state validation failed during boot",
            "context": {"error": str(exc)},
            "source": {"module": "system_boot", "function": "start_system"},
        })
        send_control_notification("STARTUP BLOCKED", "Runtime state validation failed during boot.")
        return False

    if start_info["crash_loop"]:
        runtime_status.write_status(
            "blocked",
            "Runtime boot blocked by restart guard",
            crash_loop=True,
            recovery_required=bool(start_info["recovery_required"]),
            recovery_state="UNSAFE_BLOCKED",
            startup_preflight_state="READY",
        )
        log_event(build_event(
            "recovery_completed",
            {
                "message": "BinaryBot boot blocked by restart guard",
                "result": "UNSAFE_BLOCKED",
                "blocked": True,
                "restart_count": int(start_info["restart_count"]),
                "blocked_operations": ["engine_start", "telegram_poll", "scheduler_loop", "telemetry_market_loop"],
            },
            source={"module": "system_boot", "function": "start_system"},
        ))
        log_event({
            "event_type": "error",
            "severity": "CRITICAL",
            "message": "CRASH_LOOP_DETECTED — system boot blocked",
            "error_type": "CRASH_LOOP_DETECTED",
            "context": {
                "restart_count": int(start_info["restart_count"]),
                "window_seconds": int(start_info["window_seconds"]),
                "max_restarts": int(start_info["max_restarts"]),
            },
            "source": {"module": "system_boot", "function": "start_system"},
        })
        send_control_notification("STARTUP BLOCKED", "Runtime boot blocked by restart guard.")
        return False

    log_event(build_event(
        "recovery_completed",
        {
            "message": "BinaryBot recovery bootstrap completed",
            "result": "DEGRADED_SAFE" if start_info["recovery_required"] else "HEALTHY",
            "blocked": False,
            "restart_count": int(start_info["restart_count"]),
            "blocked_operations": [],
        },
        source={"module": "system_boot", "function": "start_system"},
    ))
    log_event({"event_type": "engine_start", "message": "BinaryBot runtime starting"})

    ui_init = telegram_app_nav.initialize_active_ui_state()
    log_warning(
        warn_type="telegram_ui_state_initialized",
        message="Telegram UI active-state initialization completed before polling startup",
        context={
            "initialized": ui_init.get("initialized"),
            "persistence_enabled": ui_init.get("persistence_enabled"),
            "runtime_path_ready": ui_init.get("runtime_path_ready"),
            "resolved_state_path": ui_init.get("resolved_state_path"),
            "load_result": ui_init.get("load_result"),
            "pid": ui_init.get("pid"),
            "deployment_id": ui_init.get("deployment_id"),
        },
        source={"module": "system_boot", "function": "start_system"},
    )

    engine_thread = threading.Thread(target=start_engine, daemon=True)
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    telemetry_thread = threading.Thread(target=telemetry_market_loop, daemon=True)

    telemetry_thread.start()
    engine_thread.start()
    telegram_enabled = _should_start_telegram_thread()
    if telegram_enabled:
        telegram_thread = threading.Thread(target=poll_updates, daemon=True)
        telegram_thread.start()
    scheduler_thread.start()
    runtime_status.write_status(
        "running",
        "BinaryBot runtime running",
        telegram_enabled=telegram_enabled,
        telegram_polling_started=telegram_enabled,
        engine_tick_seconds=ENGINE_TICK_SECONDS,
        telemetry_market_worker_started=True,
        shadow_mode=_env_flag("SHADOW_MODE", default=False),
        readiness_evaluated=_env_flag("RAILWAY_READINESS_EVALUATED", default=False),
        recovery_required=bool(start_info["recovery_required"]),
        recovery_state="DEGRADED_SAFE" if start_info["recovery_required"] else "HEALTHY",
        startup_preflight_state="READY",
        startup_preflight_provider=preflight.get("active_provider"),
        startup_preflight_effective_symbols=list(preflight.get("effective_symbols") or []),
    )
    if start_info["recovery_required"]:
        send_control_notification("RECOVERY COMPLETED", "BinaryBot recovery bootstrap completed.")
        send_control_notification("DEGRADED SAFE MODE", "BinaryBot resumed in degraded safe mode.")
    if _env_flag("RAILWAY_READINESS_EVALUATED", default=False):
        send_control_notification("BOT LIVE", "BinaryBot runtime is live.")

    _heartbeat_check_interval = 60
    _heartbeat_warn_logged = False
    while True:
        time.sleep(_heartbeat_check_interval)
        if telegram_enabled:
            from runtime.telegram_updates import is_poller_alive, get_poller_heartbeat_age
            alive = is_poller_alive()
            age = get_poller_heartbeat_age()
            if not alive:
                if not _heartbeat_warn_logged:
                    log_warning(
                        warn_type="poller_heartbeat_stalled",
                        message="Telegram poller heartbeat is stale or missing",
                        context={
                            "heartbeat_age_sec": age,
                            "heartbeat_timeout_sec": 120.0,
                            "pid": os.getpid(),
                        },
                        source={"module": "system_boot", "function": "start_system"},
                    )
                    _heartbeat_warn_logged = True
            else:
                _heartbeat_warn_logged = False


if __name__ == "__main__":
    start_system()
