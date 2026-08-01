from __future__ import annotations

import contextlib
import importlib
import io
import os
import stat
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


SCRIPT_PREFIXES = ("scripts", "core", "runtime", "state_store", "monitoring", "snapshots", "intelligence", "tools")


def _purge_modules() -> None:
    for name in list(sys.modules):
        if any(name == prefix or name.startswith(prefix + ".") for prefix in SCRIPT_PREFIXES):
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _fresh_import(name: str):
    _purge_modules()
    return importlib.import_module(name)


def _set_base_env(monkeypatch: pytest.MonkeyPatch, base_dir: Path, *, enable_telegram: bool = False, token: str = "", market_key: str = "demo-market-key") -> None:
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(base_dir))
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM", "true" if enable_telegram else "false")
    if token:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", token)
    else:
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    if market_key:
        monkeypatch.setenv("TWELVE_DATA_API_KEY", market_key)
    else:
        monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for name in (
        "BINARYBOT_BASE_DIR",
        "SHADOW_MODE",
        "ENABLE_BROKER_EXECUTION",
        "ENABLE_TELEGRAM",
        "TELEGRAM_BOT_TOKEN",
        "TWELVE_DATA_API_KEY",
        "ADMIN_EVENTS_LOG",
        "OBS_DIR",
        "OUTCOMES_LOG",
        "ANALYTICS_DIR",
        "DIST_EVENTS_LOG",
        "FSM_EVENTS_LOG",
        "ENGINE_EVENTS_LOG",
        "ADMIN_PROOFS_LOG",
        "ERROR_EVENTS_LOG",
        "ALGO_PARAMS_PATH",
        "ADMIN_ROLES_CONFIG",
        "ADMIN_PERMISSIONS_CONFIG",
        "STRATEGY_AUDITOR_SETTINGS",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def railway_root(tmp_path: Path) -> Path:
    return tmp_path / "railway-data"


def test_init_module_import_has_no_side_effects(tmp_path: Path):
    before = list(tmp_path.iterdir())
    mod = _fresh_import("scripts.railway_init")
    assert hasattr(mod, "initialize_for_railway")
    assert list(tmp_path.iterdir()) == before


def test_initialize_creates_required_directories(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    mod = _fresh_import("scripts.railway_init")
    summary = mod.initialize_for_railway()
    expected = {
        railway_root,
        railway_root / "config",
        railway_root / "state",
        railway_root / "outcomes",
        railway_root / "observability",
        railway_root / "analytics",
        railway_root / "analytics" / "reports",
        railway_root / "analytics" / "cache",
        railway_root / "snapshots",
    }
    assert expected.issubset(set(map(Path, summary["created_dirs"])) | {p for p in expected if p.exists()})


def test_initialize_creates_required_runtime_files(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    mod = _fresh_import("scripts.railway_init")
    summary = mod.initialize_for_railway()
    expected = {
        railway_root / "observability" / "admin_events.jsonl",
        railway_root / "observability" / "admin_proofs.jsonl",
        railway_root / "observability" / "distribution_events.jsonl",
        railway_root / "observability" / "engine_events.jsonl",
        railway_root / "observability" / "error_events.jsonl",
        railway_root / "observability" / "fsm_events.jsonl",
        railway_root / "outcomes" / "outcomes.jsonl",
    }
    assert expected.issubset(set(map(Path, summary["created_files"])) | {p for p in expected if p.exists()})
    for path in expected:
        assert path.read_text(encoding="utf-8") == ""


def test_initialize_seeds_required_configs(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    mod = _fresh_import("scripts.railway_init")
    mod.initialize_for_railway()
    seeded = {p.name for p in (railway_root / "config").glob("*.json")}
    assert seeded == {
        "active_symbols.json",
        "admin_permissions.json",
        "admin_roles.json",
        "admin_settings.json",
        "algo_params.json",
        "channel_config.json",
        "intelligence_settings.json",
        "symbols.json",
    }


def test_initialize_is_idempotent(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    mod = _fresh_import("scripts.railway_init")
    first = mod.initialize_for_railway()
    second = mod.initialize_for_railway()
    assert first["seeded_files"]
    assert second["seeded_files"] == []
    assert len(second["preserved_files"]) == 8


def test_initialize_preserves_existing_valid_config(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    config_dir = railway_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    custom_path = config_dir / "admin_settings.json"
    custom_payload = '{"buffer_mode":"SMALL","engine_tick_interval":2,"feature_flags":{},"last_updated_ts":1}\n'
    custom_path.write_text(custom_payload, encoding="utf-8")
    mod = _fresh_import("scripts.railway_init")
    mod.initialize_for_railway()
    assert custom_path.read_text(encoding="utf-8") == custom_payload


def test_initialize_fails_on_invalid_existing_config(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    config_dir = railway_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "algo_params.json").write_text("{bad json", encoding="utf-8")
    mod = _fresh_import("scripts.railway_init")
    with pytest.raises(mod.RailwayInitError, match="algo params"):
        mod.initialize_for_railway()


def test_initialize_requires_base_dir(monkeypatch: pytest.MonkeyPatch):
    mod = _fresh_import("scripts.railway_init")
    with pytest.raises(ValueError, match="BINARYBOT_BASE_DIR"):
        mod.initialize_for_railway()


def test_initialize_supports_temporary_volume_root(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    mod = _fresh_import("scripts.railway_init")
    summary = mod.initialize_for_railway()
    assert summary["base_dir"] == str(railway_root)
    assert (railway_root / "state").is_dir()


def test_initialize_does_not_write_into_repository_when_volume_configured(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    repo_runtime_status = SEND_ROOT / "state" / "runtime_status.json"
    before_runtime_status = repo_runtime_status.read_text(encoding="utf-8") if repo_runtime_status.exists() else None
    before = {name: (SEND_ROOT / "config" / name).stat().st_mtime_ns for name in [
        "active_symbols.json",
        "admin_permissions.json",
        "admin_roles.json",
        "admin_settings.json",
        "algo_params.json",
        "channel_config.json",
        "intelligence_settings.json",
        "symbols.json",
    ]}
    mod = _fresh_import("scripts.railway_init")
    mod.initialize_for_railway()
    after = {name: (SEND_ROOT / "config" / name).stat().st_mtime_ns for name in before}
    assert before == after
    after_runtime_status = repo_runtime_status.read_text(encoding="utf-8") if repo_runtime_status.exists() else None
    assert before_runtime_status == after_runtime_status


def test_path_contract_derives_all_runtime_paths(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    common = _fresh_import("scripts.railway_common")
    env_map = common.apply_path_contract(railway_root)
    assert env_map["OBS_DIR"] == str(railway_root / "observability")
    assert env_map["ADMIN_EVENTS_LOG"] == str(railway_root / "observability" / "admin_events.jsonl")
    assert env_map["OUTCOMES_LOG"] == str(railway_root / "outcomes" / "outcomes.jsonl")
    assert env_map["ANALYTICS_DIR"] == str(railway_root / "analytics")
    assert env_map["ALGO_PARAMS_PATH"] == str(railway_root / "config" / "algo_params.json")
    assert env_map["STRATEGY_AUDITOR_SETTINGS"] == str(railway_root / "config" / "intelligence_settings.json")


def test_env_example_contains_required_sections_and_vars():
    content = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    for marker in (
        "# REQUIRED FOR BOOT",
        "# REQUIRED FOR TELEGRAM MODE",
        "# REQUIRED FOR MARKET DATA",
        "# OPTIONAL",
        "# DEVELOPMENT/TEST ONLY",
        "BINARYBOT_BASE_DIR=",
        "TELEGRAM_BOT_TOKEN=",
        "COMMUNITY_FEEDBACK_SALT=",
        "ELITE_CHANNEL_ID=",
        "TWELVE_DATA_API_KEY=",
    ):
        assert marker in content


def test_env_example_has_no_real_secrets_or_live_ids():
    content = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "7553887987" not in content
    assert "6766367444" not in content
    assert "-1003510282695" not in content
    assert "-1003776464915" not in content
    assert "replace-me" in content


def test_init_logs_do_not_expose_secrets(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root, enable_telegram=True, token="secret-telegram-token", market_key="secret-market-key")
    monkeypatch.setenv("COMMUNITY_FEEDBACK_SALT", "secret-community-salt")
    mod = _fresh_import("scripts.railway_init")
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        assert mod.main([]) == 0
    output = stdout.getvalue()
    assert "secret-telegram-token" not in output
    assert "secret-market-key" not in output
    assert "secret-community-salt" not in output


def test_readiness_succeeds_with_valid_fixture_state(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    report = health_mod.readiness_report()
    assert report["status"] == "ready"


def test_liveness_succeeds_with_running_status(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    status_mod = _fresh_import("runtime.runtime_status")
    status_mod.write_status("running", "ok")
    health_mod = _fresh_import("scripts.railway_healthcheck")
    report = health_mod.liveness_report()
    assert report["status"] == "live"
    assert report["pid"] == os.getpid()


def test_readiness_fails_on_invalid_required_config(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    (railway_root / "config" / "channel_config.json").write_text("[]\n", encoding="utf-8")
    health_mod = _fresh_import("scripts.railway_healthcheck")
    with pytest.raises(Exception, match="channel_config"):
        health_mod.readiness_report()


def test_readiness_fails_when_root_not_writable(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    railway_root.chmod(0o500)
    try:
        health_mod = _fresh_import("scripts.railway_healthcheck")
        with pytest.raises(Exception, match="not writable"):
            health_mod.readiness_report()
    finally:
        railway_root.chmod(0o700)


def test_shadow_mode_must_be_enabled(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    monkeypatch.setenv("SHADOW_MODE", "false")
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    with pytest.raises(Exception, match="SHADOW_MODE"):
        health_mod.readiness_report()


def test_broker_execution_must_remain_disabled(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "true")
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    with pytest.raises(Exception, match="ENABLE_BROKER_EXECUTION"):
        health_mod.readiness_report()


def test_telegram_disabled_mode_allows_missing_token(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root, enable_telegram=False, token="")
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    assert health_mod.readiness_report()["telegram_enabled"] is False


def test_telegram_enabled_mode_requires_token(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root, enable_telegram=True, token="")
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    with pytest.raises(Exception, match="TELEGRAM_BOT_TOKEN"):
        health_mod.readiness_report()


def test_market_data_key_is_required_for_readiness(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root, market_key="")
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    with pytest.raises(Exception, match="TWELVE_DATA_API_KEY"):
        health_mod.readiness_report()


def test_init_and_readiness_make_no_network_calls(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    calls: list[str] = []

    def _blocked(*_args, **_kwargs):
        calls.append("network")
        raise AssertionError("network call attempted")

    monkeypatch.setattr("requests.get", _blocked)
    monkeypatch.setattr("requests.post", _blocked)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    health_mod.readiness_report()
    assert calls == []


def test_startup_main_resolves_and_invokes_system_boot(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    _purge_modules()
    start_mod = importlib.import_module("scripts.railway_start")
    boot = importlib.import_module("runtime.system_boot")
    calls: list[str] = []
    monkeypatch.setattr(boot, "start_system", lambda: calls.append("started"))
    assert start_mod.main() == 0
    assert calls == ["started"]


def test_runtime_status_graceful_shutdown_updates_state(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    boot = _fresh_import("runtime.system_boot")
    status_mod = _fresh_import("runtime.runtime_status")
    monkeypatch.setattr(boot.snapshot_manager, "create_snapshot", lambda: None)
    monkeypatch.setattr(boot, "mark_graceful_shutdown", lambda: None)
    status_mod.write_status("running", "before")
    boot._SHUTDOWN_MARKED = False
    boot._mark_graceful_shutdown()
    assert status_mod.read_status()["phase"] == "stopped"


def test_strategy_auditor_settings_apply_runtime_path_contract(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    auditor = _fresh_import("tools.strategy_auditor_lib")
    settings = auditor.load_settings(path=str(railway_root / "config" / "intelligence_settings.json"))
    assert settings["reports"]["output_dir"] == str(railway_root / "analytics" / "reports")
    assert settings["sources"]["engine_events"] == str(railway_root / "observability" / "engine_events.jsonl")
    assert settings["sources"]["outcomes"] == str(railway_root / "outcomes" / "outcomes.jsonl")


def test_market_client_missing_key_fails_before_request(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def _blocked(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("should not reach network")

    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
    monkeypatch.setattr("requests.get", _blocked)
    mod = _fresh_import("runtime.market_client")
    with pytest.raises(RuntimeError, match="TWELVE_DATA_API_KEY"):
        mod.fetch_klines("EUR/USD", "1min")
    assert calls == []


def test_system_boot_skips_telegram_thread_when_disabled(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root, enable_telegram=False)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    boot = _fresh_import("runtime.system_boot")
    assert boot._should_start_telegram_thread() is False


def test_healthcheck_cli_json_success(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root)
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    health_mod = _fresh_import("scripts.railway_healthcheck")
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        assert health_mod.main(["--mode", "readiness", "--json"]) == 0
    assert '"status": "ready"' in stdout.getvalue()


def test_start_script_allows_telegram_disabled_shadow_boot(railway_root: Path, monkeypatch: pytest.MonkeyPatch):
    _set_base_env(monkeypatch, railway_root, enable_telegram=False, token="")
    init_mod = _fresh_import("scripts.railway_init")
    init_mod.initialize_for_railway()
    _purge_modules()
    start_mod = importlib.import_module("scripts.railway_start")
    boot = importlib.import_module("runtime.system_boot")
    monkeypatch.setattr(boot, "start_system", lambda: None)
    assert start_mod.main() == 0
