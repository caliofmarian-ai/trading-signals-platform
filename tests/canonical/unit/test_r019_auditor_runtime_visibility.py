from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"


def test_local_time_alias_preserves_runtime_status_overlay_and_presence(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    (runtime_root / "state").mkdir(parents=True)

    env = dict(os.environ)
    env.update(
        {
            "PYTHONPATH": str(SEND_ROOT),
            "BINARYBOT_BASE_DIR": str(runtime_root),
            "STRATEGY_AUDITOR_ENABLED": "true",
            "STRATEGY_AUDITOR_DAILY_TIME": "00:15",
            "STRATEGY_AUDITOR_TIMEZONE": "Europe/Bucharest",
        }
    )
    env.pop("STRATEGY_AUDITOR_DAILY_TIME_UTC", None)

    code = r'''
import importlib
from runtime import runtime_status
from tools import strategy_auditor_runtime as selected_runtime

assert selected_runtime.__name__ == "tools.strategy_auditor_local_time"
runtime_status.write_status("running", "BinaryBot runtime running")
base_runtime = importlib.import_module("tools.strategy_auditor_runtime")
base_runtime._write_status({
    "component": "strategy_auditor",
    "status": "WORKER_STARTED",
    "worker_started": True,
    "schedule_mode": "LOCAL_CIVIL_TIME",
    "schedule_identity": {
        "configured_time_local": "00:15",
        "timezone": "Europe/Bucharest",
        "status": "CONFIGURED_LOCAL_TIME",
    },
})
observed = runtime_status.read_status()
assert observed["phase"] == "running"
assert observed["strategy_auditor"]["status"] == "WORKER_STARTED"
assert observed["strategy_auditor"]["schedule_mode"] == "LOCAL_CIVIL_TIME"
assert observed["strategy_auditor"]["schedule_identity"]["configured_time_local"] == "00:15"
assert observed["strategy_auditor"]["schedule_identity"]["timezone"] == "Europe/Bucharest"
presence = observed["strategy_auditor_env_presence"]
assert presence["STRATEGY_AUDITOR_ENABLED"] is True
assert presence["STRATEGY_AUDITOR_DAILY_TIME"] is True
assert presence["STRATEGY_AUDITOR_TIMEZONE"] is True
assert presence["STRATEGY_AUDITOR_DAILY_TIME_UTC"] is False
'''

    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
