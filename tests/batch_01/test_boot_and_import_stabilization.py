from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _fresh_import(module_name: str):
    purge = [
        "core.storage",
        "core.signal_engine",
        "core.telegram_publisher",
        "core.distribution_router",
        "core.bot_service",
        "core.outcome_service",
        "runtime.engine_loop",
        "runtime.system_boot",
        "runtime.telegram_updates",
        module_name,
    ]
    for name in purge:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()
    return importlib.import_module(module_name)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for name in (
        "BINARYBOT_BASE_DIR",
        "BINARYBOT_ENV_FILE",
        "TELEGRAM_BOT_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)


def test_storage_imports_successfully():
    storage = _fresh_import("core.storage")
    assert storage is not None


def test_config_path_is_repo_relative_and_deterministic():
    storage = _fresh_import("core.storage")
    expected = SEND_ROOT / "config" / "active_symbols.json"
    assert Path(storage.config_path("active_symbols.json")) == expected
    assert expected.is_file()


def test_config_path_supports_explicit_base_dir_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    base_dir = tmp_path / "runtime-root"
    config_dir = base_dir / "config"
    config_dir.mkdir(parents=True)
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(base_dir))

    storage = _fresh_import("core.storage")

    assert Path(storage.config_path("algo_params.json")) == config_dir / "algo_params.json"


def test_invalid_base_dir_override_fails_clearly(monkeypatch: pytest.MonkeyPatch):
    missing_dir = Path("/tmp/does-not-exist-batch-01")
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(missing_dir))

    storage = _fresh_import("core.storage")

    with pytest.raises(storage.StoragePathError, match="BINARYBOT_BASE_DIR does not exist"):
        storage.config_path("active_symbols.json")


def test_core_runtime_imports_are_side_effect_free(monkeypatch: pytest.MonkeyPatch):
    network_calls: list[tuple[str, str]] = []

    def _fail_get(*args, **kwargs):
        network_calls.append(("get", args[0] if args else ""))
        raise AssertionError("network call during import")

    def _fail_post(*args, **kwargs):
        network_calls.append(("post", args[0] if args else ""))
        raise AssertionError("network call during import")

    def _fail_thread(*args, **kwargs):
        raise AssertionError("thread started during import")

    monkeypatch.setattr("requests.get", _fail_get)
    monkeypatch.setattr("requests.post", _fail_post)
    monkeypatch.setattr("threading.Thread", _fail_thread)

    assert _fresh_import("core.signal_engine") is not None
    assert _fresh_import("runtime.engine_loop") is not None
    assert _fresh_import("runtime.system_boot") is not None
    assert network_calls == []


def test_existing_supported_config_files_resolve_from_clean_environment():
    storage = _fresh_import("core.storage")

    for name in (
        "active_symbols.json",
        "admin_permissions.json",
        "admin_roles.json",
        "admin_settings.json",
        "algo_params.json",
        "channel_config.json",
        "intelligence_settings.json",
        "symbols.json",
    ):
        assert Path(storage.config_path(name)).is_file(), name


def test_params_loader_behavior_is_unchanged():
    params_loader = _fresh_import("core.params_loader")
    params = params_loader.load_algo_params(path=str(SEND_ROOT / "config" / "algo_params.json"))

    assert set(params) == {"algo_version", "thresholds", "weights", "expiry", "buffer", "gates"}

    with pytest.raises(params_loader.ParamsValidationError, match="algo params missing top-level keys"):
        params_loader.validate_algo_params(
            {
                "algo_version": "1.0.0",
                "thresholds": {"pre": 1, "confirm": 2, "open": 3},
                "weights": {},
                "expiry": {"min_minutes": 1, "max_minutes": 2},
                "buffer": {"modes": {"SMALL": {"atr_mult": 1}, "MEDIUM": {"atr_mult": 1}, "LARGE": {"atr_mult": 1}}},
            }
        )
