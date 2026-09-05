from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from tools import strategy_auditor_local_time as local_time


def _runtime_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "runtime"
    for directory in ("config", "observability", "outcomes", "analytics", "state"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / "config" / "admin_settings.json").write_text(
        json.dumps({"feature_flags": {"strategy_auditor_enabled": True}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    return root


def _set_bucharest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME", "00:15")
    monkeypatch.setenv("STRATEGY_AUDITOR_TIMEZONE", "Europe/Bucharest")
    monkeypatch.delenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", raising=False)


def test_bucharest_0015_tracks_summer_and_winter_offsets() -> None:
    summer_due = local_time.local_due_utc(dt.date(2026, 7, 15), "Europe/Bucharest", "00:15")
    winter_due = local_time.local_due_utc(dt.date(2026, 12, 15), "Europe/Bucharest", "00:15")

    assert summer_due == dt.datetime(2026, 7, 14, 21, 15, tzinfo=dt.UTC)
    assert winter_due == dt.datetime(2026, 12, 14, 22, 15, tzinfo=dt.UTC)


def test_local_report_period_uses_bucharest_civil_date() -> None:
    assert local_time.local_report_period(
        dt.datetime(2026, 7, 14, 21, 15, tzinfo=dt.UTC),
        "Europe/Bucharest",
    ) == "2026-07-15"
    assert local_time.local_report_period(
        dt.datetime(2026, 12, 14, 22, 15, tzinfo=dt.UTC),
        "Europe/Bucharest",
    ) == "2026-12-15"


def test_runtime_worker_config_accepts_bucharest_local_schedule(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _runtime_root(tmp_path, monkeypatch)
    _set_bucharest(monkeypatch)

    config = local_time.runtime_worker_config()

    assert config["status"] == "READY"
    assert config["enabled"] is True
    assert config["schedule_mode"] == "LOCAL_CIVIL_TIME"
    assert config["schedule_identity"]["configured_time_local"] == "00:15"
    assert config["schedule_identity"]["timezone"] == "Europe/Bucharest"
    assert config["schedule_identity"]["status"] == "CONFIGURED_LOCAL_TIME"


def test_local_and_legacy_utc_schedule_conflict_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _runtime_root(tmp_path, monkeypatch)
    _set_bucharest(monkeypatch)
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "21:15")

    config = local_time.runtime_worker_config()

    assert config["status"] == "INVALID_SCHEDULE"
    assert config["enabled"] is False
    assert config["schedule_identity"]["status"] == "SCHEDULE_CONFIGURATION_CONFLICT"


@pytest.mark.parametrize(
    ("local_value", "timezone_value", "reason"),
    [
        ("", "Europe/Bucharest", "LOCAL_SCHEDULE_INCOMPLETE"),
        ("00:15", "", "LOCAL_SCHEDULE_INCOMPLETE"),
        ("24:15", "Europe/Bucharest", "INVALID_LOCAL_SCHEDULE"),
        ("00:15", "Europe/Not-A-Real-Zone", "INVALID_TIMEZONE"),
    ],
)
def test_invalid_local_schedule_configuration_is_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    local_value: str,
    timezone_value: str,
    reason: str,
) -> None:
    _runtime_root(tmp_path, monkeypatch)
    monkeypatch.setenv("STRATEGY_AUDITOR_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_AUDITOR_DAILY_TIME", local_value)
    monkeypatch.setenv("STRATEGY_AUDITOR_TIMEZONE", timezone_value)
    monkeypatch.delenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", raising=False)

    config = local_time.runtime_worker_config()

    assert config["status"] == "INVALID_SCHEDULE"
    assert config["enabled"] is False
    assert config["schedule_identity"]["status"] == reason


def test_tools_package_selects_local_backend_when_local_schedule_is_present() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SEND_ROOT)
    env["STRATEGY_AUDITOR_DAILY_TIME"] = "00:15"
    env["STRATEGY_AUDITOR_TIMEZONE"] = "Europe/Bucharest"
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from tools import strategy_auditor_runtime; print(strategy_auditor_runtime.__name__)",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "tools.strategy_auditor_local_time"


def test_tools_package_preserves_legacy_backend_without_local_schedule() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SEND_ROOT)
    env.pop("STRATEGY_AUDITOR_DAILY_TIME", None)
    env.pop("STRATEGY_AUDITOR_TIMEZONE", None)
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from tools import strategy_auditor_runtime; print(strategy_auditor_runtime.__name__)",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "tools.strategy_auditor_runtime"
