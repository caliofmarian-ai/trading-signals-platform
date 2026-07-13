# /opt/binarybot/runtime/system_boot.py
# BinaryBot — System Boot Loader

from __future__ import annotations

import os
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
from core.observability_logger import log_event
from monitoring.restart_guard import record_start, should_freeze as restart_loop_detected


def start_system() -> None:
    # record restart early
    record_start()

    # crash-loop protection (boot-level)
    if restart_loop_detected():
        log_event({
            "event_type": "error",
            "severity": "CRITICAL",
            "message": "CRASH_LOOP_DETECTED — system boot blocked",
        })
        return

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