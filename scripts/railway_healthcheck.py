from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from scripts.railway_common import (
    apply_path_contract,
    broker_execution_enabled,
    resolve_base_dir,
    runtime_paths,
    shadow_mode_enabled,
    telegram_enabled,
)
from scripts.railway_init import RailwayInitError, _validate_config_tree


class RailwayHealthError(RuntimeError):
    pass


def _import_runtime_modules() -> None:
    __import__("core.storage")
    __import__("core.signal_engine")
    __import__("core.distribution_router")
    __import__("monitoring.restart_guard")
    __import__("runtime.system_boot")
    __import__("runtime.runtime_status")


def _check_writable(base_dir: Path) -> None:
    try:
        with tempfile.NamedTemporaryFile(dir=base_dir, prefix=".railway-write-", delete=True) as handle:
            handle.write(b"ok")
            handle.flush()
    except Exception as exc:
        raise RailwayHealthError(f"Persistent runtime root is not writable: {base_dir}") from exc


def _check_state_files(base_dir: Path) -> None:
    from state_store import state_store as runtime_state_store

    state_dir = runtime_paths(base_dir)["state"]
    validators = {
        "focus_state.json": runtime_state_store.load_fsm_state,
        "dist_state.json": runtime_state_store.load_dist_state,
        "restart_guard.json": runtime_state_store.load_restart_guard_state,
    }
    for name, loader in validators.items():
        path = state_dir / name
        if path.exists():
            loader(path=str(path))


def readiness_report(*, base_dir: Path | None = None) -> Dict[str, Any]:
    base_dir = base_dir or resolve_base_dir(require_explicit=True)
    apply_path_contract(base_dir)

    if not shadow_mode_enabled():
        raise RailwayHealthError("SHADOW_MODE must be true for the Railway shadow deployment")
    if broker_execution_enabled():
        raise RailwayHealthError("ENABLE_BROKER_EXECUTION must remain false in shadow mode")
    if not os.getenv("TWELVE_DATA_API_KEY", "").strip():
        raise RailwayHealthError("TWELVE_DATA_API_KEY is required for shadow-mode readiness")
    if telegram_enabled() and not os.getenv("TELEGRAM_BOT_TOKEN", "").strip():
        raise RailwayHealthError("TELEGRAM_BOT_TOKEN is required when ENABLE_TELEGRAM=true")

    _import_runtime_modules()
    _check_writable(base_dir)
    _validate_config_tree(base_dir)
    _check_state_files(base_dir)

    from monitoring import restart_guard

    if restart_guard.should_freeze():
        raise RailwayHealthError("Restart guard is in a fatal crash-loop state")

    return {
        "status": "ready",
        "base_dir": str(base_dir),
        "telegram_enabled": telegram_enabled(),
        "shadow_mode": True,
    }


def liveness_report(*, base_dir: Path | None = None) -> Dict[str, Any]:
    base_dir = base_dir or resolve_base_dir(require_explicit=True)
    apply_path_contract(base_dir)
    _import_runtime_modules()

    from runtime import runtime_status

    status = runtime_status.read_status()
    if not isinstance(status, dict) or not status:
        raise RailwayHealthError("runtime status file is missing")
    pid = status.get("pid")
    if not runtime_status.is_pid_alive(pid):
        raise RailwayHealthError("runtime process is not alive")
    phase = str(status.get("phase") or "").lower()
    if phase not in {"starting", "running"}:
        raise RailwayHealthError(f"runtime is not live: phase={phase or 'unknown'}")

    return {
        "status": "live",
        "pid": int(pid),
        "phase": phase,
        "base_dir": str(base_dir),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Railway shadow-mode health checks")
    parser.add_argument("--mode", choices=("liveness", "readiness"), default="readiness")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = readiness_report() if args.mode == "readiness" else liveness_report()
    except (RailwayHealthError, RailwayInitError, ValueError) as exc:
        payload = {"status": "error", "mode": args.mode, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Railway healthcheck failed ({args.mode}): {exc}")
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Railway healthcheck ok ({args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
