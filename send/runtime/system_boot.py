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

        if not line:
            continue
        if line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


# IMPORTANT:
# Load env BEFORE importing modules that read os.getenv() at import time.
_load_env_file()

from runtime.engine_loop import start_engine
from runtime.telegram_updates import poll_updates
from runtime.distribution_scheduler import scheduler_loop
from core import fsm_runtime
from core import distribution_router
from core.observability_logger import build_event, log_event
from monitoring.restart_guard import mark_graceful_shutdown, record_start
from snapshots import snapshot_manager


_SHUTDOWN_MARKED = False


def _mark_graceful_shutdown() -> None:
    global _SHUTDOWN_MARKED
    if _SHUTDOWN_MARKED:
        return
    _SHUTDOWN_MARKED = True
    try:
        snapshot_manager.create_snapshot()
    except Exception as exc:
        log_event(
            {
                "event_type": "error",
                "severity": "ERROR",
                "error_type": "SNAPSHOT_CREATE_FAILED",
                "message": "Failed to create shutdown snapshot",
                "context": {"error": str(exc)},
                "source": {"module": "system_boot", "function": "_mark_graceful_shutdown"},
            }
        )
    try:
        mark_graceful_shutdown()
    except Exception as exc:
        log_event(
            {
                "event_type": "error",
                "severity": "ERROR",
                "error_type": "GRACEFUL_SHUTDOWN_MARK_FAILED",
                "message": "Failed to persist graceful shutdown marker",
                "context": {"error": str(exc)},
                "source": {"module": "system_boot", "function": "_mark_graceful_shutdown"},
            }
        )


def _handle_shutdown_signal(signum, _frame) -> None:
    log_event(
        build_event(
            "engine_stop",
            {"message": f"BinaryBot runtime stopping on signal {signum}"},
            source={"module": "system_boot", "function": "_handle_shutdown_signal"},
        )
    )
    _mark_graceful_shutdown()
    raise SystemExit(0)


def _register_shutdown_hooks() -> None:
    atexit.register(_mark_graceful_shutdown)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_shutdown_signal)


def start_system() -> None:
    _register_shutdown_hooks()

    start_info = record_start()
    log_event(
        build_event(
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
        )
    )

    try:
        fsm_runtime.load_state()
        distribution_router.load_state()
    except Exception as exc:
        log_event(
            build_event(
                "recovery_completed",
                {
                    "message": "BinaryBot recovery bootstrap failed",
                    "result": "UNSAFE_BLOCKED",
                    "blocked": True,
                    "restart_count": int(start_info["restart_count"]),
                    "blocked_operations": ["engine_start", "telegram_poll", "scheduler_loop"],
                },
                source={"module": "system_boot", "function": "start_system"},
            )
        )
        log_event(
            {
                "event_type": "error",
                "severity": "CRITICAL",
                "error_type": "RECOVERY_VALIDATION_FAILED",
                "message": "Runtime state validation failed during boot",
                "context": {"error": str(exc)},
                "source": {"module": "system_boot", "function": "start_system"},
            }
        )
        return

    if start_info["crash_loop"]:
        log_event(
            build_event(
                "recovery_completed",
                {
                    "message": "BinaryBot boot blocked by restart guard",
                    "result": "UNSAFE_BLOCKED",
                    "blocked": True,
                    "restart_count": int(start_info["restart_count"]),
                    "blocked_operations": ["engine_start", "telegram_poll", "scheduler_loop"],
                },
                source={"module": "system_boot", "function": "start_system"},
            )
        )
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
        return

    log_event(
        build_event(
            "recovery_completed",
            {
                "message": "BinaryBot recovery bootstrap completed",
                "result": "DEGRADED_SAFE" if start_info["recovery_required"] else "HEALTHY",
                "blocked": False,
                "restart_count": int(start_info["restart_count"]),
                "blocked_operations": [],
            },
            source={"module": "system_boot", "function": "start_system"},
        )
    )

    log_event({
        "event_type": "engine_start",
        "message": "BinaryBot runtime starting",
    })

    # engine thread
    engine_thread = threading.Thread(target=start_engine, daemon=True)

    # telegram polling thread
    telegram_thread = threading.Thread(target=poll_updates, daemon=True)

    # scheduler thread
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)

    engine_thread.start()
    telegram_thread.start()
    scheduler_thread.start()

    # keep main thread alive
    while True:
        time.sleep(60)


if __name__ == "__main__":
    start_system()