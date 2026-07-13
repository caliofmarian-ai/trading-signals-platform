from __future__ import annotations

import importlib
import json
import socket
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch: pytest.MonkeyPatch):
    def _blocked(*_args, **_kwargs):
        raise AssertionError("external network access is blocked in canonical offline tests")

    monkeypatch.setattr("requests.get", _blocked)
    monkeypatch.setattr("requests.post", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


@pytest.fixture
def canonical_runtime_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "runtime"
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)
    (root / "observability").mkdir(parents=True, exist_ok=True)
    (root / "outcomes").mkdir(parents=True, exist_ok=True)
    (root / "analytics").mkdir(parents=True, exist_ok=True)
    (root / "snapshots").mkdir(parents=True, exist_ok=True)

    config_dir = SEND_ROOT / "config"
    for name in [
        "active_symbols.json",
        "admin_permissions.json",
        "admin_roles.json",
        "admin_settings.json",
        "algo_params.json",
        "channel_config.json",
    ]:
        src = config_dir / name
        dst = root / "config" / name
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("OBS_DIR", str(root / "observability"))
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(root / "observability" / "engine_events.jsonl"))
    monkeypatch.setenv("FSM_EVENTS_LOG", str(root / "observability" / "fsm_events.jsonl"))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(root / "observability" / "distribution_events.jsonl"))
    monkeypatch.setenv("ADMIN_PROOFS_LOG", str(root / "observability" / "admin_proofs.jsonl"))
    monkeypatch.setenv("ERROR_EVENTS_LOG", str(root / "observability" / "error_events.jsonl"))
    monkeypatch.setenv("OUTCOMES_LOG", str(root / "outcomes" / "outcomes.jsonl"))
    monkeypatch.setenv("ANALYTICS_DIR", str(root / "analytics"))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "offline-token")
    monkeypatch.setenv("ELITE_CHANNEL_ID", "1004")
    monkeypatch.setenv("COMMUNITY_FEEDBACK_SALT", "offline-salt")
    monkeypatch.setenv("TZ", "UTC")

    return root


@pytest.fixture
def fresh_imports():
    def _fresh(module_name: str):
        purge_prefixes = ("core", "runtime", "state_store", "monitoring", "snapshots", "intelligence")
        for name in list(sys.modules.keys()):
            if name == module_name or name.startswith(purge_prefixes):
                sys.modules.pop(name, None)
        importlib.invalidate_caches()
        return importlib.import_module(module_name)

    return _fresh


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
