from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _fresh_preflight(fresh_imports):
    return fresh_imports("runtime.startup_preflight")


def test_preflight_accepts_valid_twelve_data_runtime(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "TWELVE_DATA")
    monkeypatch.setenv("TWELVE_DATA_API_KEY", "offline-twelve-key")
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)

    preflight = _fresh_preflight(fresh_imports)
    report = preflight.run_startup_preflight(require_shadow_mode=True)

    assert report["status"] == "ready"
    assert report["active_provider"] == "TWELVE_DATA"
    assert report["provider_mode"] == "EXCLUSIVE"
    assert report["effective_symbols"]
    assert report["persistent_state_valid"] is True
    assert report["permissions_valid"] is True


def test_preflight_accepts_finnhub_without_twelve_data_key(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("FINNHUB_API_KEY", "offline-finnhub-key")
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)

    preflight = _fresh_preflight(fresh_imports)
    report = preflight.run_startup_preflight(require_shadow_mode=True)

    assert report["active_provider"] == "FINNHUB"
    assert report["effective_symbols"] == ["EUR/USD"]


def test_preflight_requires_only_active_provider_key(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    monkeypatch.setenv("TWELVE_DATA_API_KEY", "inactive-provider-key")

    preflight = _fresh_preflight(fresh_imports)
    with pytest.raises(preflight.StartupPreflightError, match="FINNHUB_API_KEY"):
        preflight.run_startup_preflight()


def test_corrupt_persisted_provider_state_blocks_instead_of_falling_back(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("FINNHUB_API_KEY", "offline-finnhub-key")
    (canonical_runtime_root / "config" / "market_data_provider.json").write_text(
        "{bad json", encoding="utf-8"
    )

    preflight = _fresh_preflight(fresh_imports)
    with pytest.raises(preflight.StartupPreflightError, match="market_data_provider is invalid JSON"):
        preflight.run_startup_preflight()


def test_finnhub_effective_universe_must_include_eur_usd(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("FINNHUB_API_KEY", "offline-finnhub-key")
    _write_json(
        canonical_runtime_root / "config" / "active_symbols.json",
        {"symbols": ["GBP/USD"]},
    )

    preflight = _fresh_preflight(fresh_imports)
    with pytest.raises(preflight.StartupPreflightError, match="EUR/USD"):
        preflight.run_startup_preflight()


def test_empty_active_symbol_universe_blocks_startup(
    canonical_runtime_root: Path,
    fresh_imports,
) -> None:
    _write_json(
        canonical_runtime_root / "config" / "active_symbols.json",
        {"symbols": []},
    )

    preflight = _fresh_preflight(fresh_imports)
    with pytest.raises(preflight.StartupPreflightError, match="symbol universe is empty"):
        preflight.run_startup_preflight()


def test_runtime_incompatible_algo_version_blocks_startup(
    canonical_runtime_root: Path,
    fresh_imports,
) -> None:
    path = canonical_runtime_root / "config" / "algo_params.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["algo_version"] = "999.0.0"
    _write_json(path, payload)

    preflight = _fresh_preflight(fresh_imports)
    with pytest.raises(preflight.StartupPreflightError, match="incompatible"):
        preflight.run_startup_preflight()


def test_malformed_permissions_block_startup(
    canonical_runtime_root: Path,
    fresh_imports,
) -> None:
    _write_json(
        canonical_runtime_root / "config" / "admin_permissions.json",
        {"permissions": {"admin.view": "owner"}},
    )

    preflight = _fresh_preflight(fresh_imports)
    with pytest.raises(preflight.StartupPreflightError, match="role list"):
        preflight.run_startup_preflight()


def test_corrupt_persisted_fsm_state_blocks_startup(
    canonical_runtime_root: Path,
    fresh_imports,
) -> None:
    (canonical_runtime_root / "state" / "focus_state.json").write_text(
        "{bad json", encoding="utf-8"
    )

    preflight = _fresh_preflight(fresh_imports)
    with pytest.raises(preflight.StartupPreflightError, match="Persisted runtime state validation failed"):
        preflight.run_startup_preflight()


def test_preflight_rejects_broker_execution_even_outside_railway_wrapper(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "true")
    preflight = _fresh_preflight(fresh_imports)

    with pytest.raises(preflight.StartupPreflightError, match="ENABLE_BROKER_EXECUTION"):
        preflight.run_startup_preflight(require_shadow_mode=False)


def test_system_boot_preflight_failure_creates_zero_live_threads(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boot = fresh_imports("runtime.system_boot")
    created_threads: list[object] = []
    notifications: list[tuple[str, str]] = []

    monkeypatch.setattr(boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(
        boot,
        "record_start",
        lambda: {
            "restart_count": 0,
            "window_seconds": 60,
            "max_restarts": 3,
            "previous_shutdown_kind": "graceful",
            "recovery_required": False,
            "crash_loop": False,
        },
    )
    monkeypatch.setattr(
        boot.startup_preflight,
        "run_startup_preflight",
        lambda **_kwargs: (_ for _ in ()).throw(
            boot.startup_preflight.StartupPreflightError("unsafe startup fixture")
        ),
    )
    monkeypatch.setattr(
        boot.threading,
        "Thread",
        lambda *args, **kwargs: created_threads.append((args, kwargs)),
    )
    monkeypatch.setattr(
        boot,
        "send_control_notification",
        lambda title, message: notifications.append((title, message)),
    )

    result = boot.start_system()

    assert result is False
    assert created_threads == []
    assert notifications[-1][0] == "STARTUP BLOCKED"
    assert boot.runtime_status.read_status()["phase"] == "blocked"
    assert boot.runtime_status.read_status()["startup_preflight_state"] == "UNSAFE_BLOCKED"


def test_system_boot_valid_preflight_occurs_before_worker_creation(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boot = fresh_imports("runtime.system_boot")
    order: list[str] = []

    monkeypatch.setattr(boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(
        boot,
        "record_start",
        lambda: {
            "restart_count": 0,
            "window_seconds": 60,
            "max_restarts": 3,
            "previous_shutdown_kind": "graceful",
            "recovery_required": False,
            "crash_loop": False,
        },
    )
    monkeypatch.setattr(
        boot.startup_preflight,
        "run_startup_preflight",
        lambda **_kwargs: order.append("preflight")
        or {
            "active_provider": "TWELVE_DATA",
            "effective_symbols": ["EUR/USD"],
        },
    )
    monkeypatch.setattr(boot.fsm_runtime, "load_state", lambda: {})
    monkeypatch.setattr(boot.distribution_router, "load_state", lambda: {})
    monkeypatch.setattr(
        boot.telegram_app_nav,
        "initialize_active_ui_state",
        lambda: {
            "initialized": True,
            "persistence_enabled": True,
            "runtime_path_ready": True,
            "resolved_state_path": "/tmp/ui.json",
            "load_result": {"status": "ok"},
            "pid": 1,
            "deployment_id": "test",
        },
    )
    monkeypatch.setattr(boot, "send_control_notification", lambda *args, **kwargs: None)

    class _Thread:
        def __init__(self, target=None, daemon=None):
            assert order and order[0] == "preflight"
            self.target = target
            order.append(f"created:{getattr(target, '__name__', 'worker')}")

        def start(self):
            order.append(f"started:{getattr(self.target, '__name__', 'worker')}")

    monkeypatch.setattr(boot.threading, "Thread", _Thread)
    monkeypatch.setattr(
        boot.time,
        "sleep",
        lambda _seconds: (_ for _ in ()).throw(SystemExit(0)),
    )

    with pytest.raises(SystemExit):
        boot.start_system()

    assert order[0] == "preflight"
    assert any(item.startswith("started:telemetry_market_loop") for item in order)
    assert any(item.startswith("started:start_engine") for item in order)
    assert any(item.startswith("started:scheduler_loop") for item in order)


def test_railway_entry_propagates_blocked_system_boot_as_failure(
    canonical_runtime_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("scripts.railway_start", "scripts.railway_healthcheck", "scripts.railway_init"):
        sys.modules.pop(name, None)
    start_mod = importlib.import_module("scripts.railway_start")
    boot = importlib.import_module("runtime.system_boot")
    notifications: list[tuple[str, str]] = []

    monkeypatch.setattr(start_mod, "initialize_for_railway", lambda base_dir=None: {"ok": True})
    monkeypatch.setattr(start_mod, "readiness_report", lambda base_dir=None: {"status": "ready"})
    monkeypatch.setattr(start_mod, "send_control_notification", lambda title, message: notifications.append((title, message)))
    monkeypatch.setattr(boot, "start_system", lambda: False)

    assert start_mod.main() == 1
    assert notifications[0][0] == "BOT STARTING"
    assert notifications[-1][0] == "STARTUP BLOCKED"


def test_railway_readiness_accepts_finnhub_without_twelve_data_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_dir = tmp_path / "railway"
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(base_dir))
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM", "false")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("FINNHUB_API_KEY", "offline-finnhub-key")
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)

    for name in list(sys.modules):
        if name.startswith(("core", "runtime", "state_store", "monitoring", "scripts.railway_")):
            sys.modules.pop(name, None)
    importlib.invalidate_caches()

    init_mod = importlib.import_module("scripts.railway_init")
    init_mod.initialize_for_railway(base_dir=base_dir)
    health_mod = importlib.import_module("scripts.railway_healthcheck")
    report = health_mod.readiness_report(base_dir=base_dir)

    assert report["status"] == "ready"
    assert report["active_provider"] == "FINNHUB"
    assert report["effective_symbols"] == ["EUR/USD"]
