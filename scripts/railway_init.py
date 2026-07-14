from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict

from scripts.railway_common import (
    CONFIG_SEED_FILES,
    SEND_ROOT,
    apply_path_contract,
    resolve_base_dir,
    runtime_paths,
)


class RailwayInitError(RuntimeError):
    pass


def _load_json_object(path: Path, *, label: str) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RailwayInitError(f"{label} is invalid JSON: {path}") from exc
    except OSError as exc:
        raise RailwayInitError(f"Unable to read {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RailwayInitError(f"{label} must be a JSON object: {path}")
    return payload


def _validate_config_tree(base_dir: Path) -> None:
    apply_path_contract(base_dir)

    from core import admin_permissions, distribution_router, params_loader
    from state_store import state_store as runtime_state_store
    from tools import strategy_auditor_lib

    paths = runtime_paths(base_dir)
    config_dir = paths["config"]

    required = {
        "algo_params": config_dir / "algo_params.json",
        "active_symbols": config_dir / "active_symbols.json",
        "admin_settings": config_dir / "admin_settings.json",
        "channel_config": config_dir / "channel_config.json",
        "admin_roles": config_dir / "admin_roles.json",
        "admin_permissions": config_dir / "admin_permissions.json",
        "intelligence_settings": config_dir / "intelligence_settings.json",
        "symbols": config_dir / "symbols.json",
    }
    for label, path in required.items():
        if not path.is_file():
            raise RailwayInitError(f"Required config file missing: {path}")

    params_loader.load_algo_params(path=str(required["algo_params"]))
    runtime_state_store.load_active_symbols(path=str(required["active_symbols"]))
    runtime_state_store.load_settings(path=str(required["admin_settings"]))
    _load_json_object(required["channel_config"], label="channel_config")
    _load_json_object(required["admin_roles"], label="admin_roles")
    _load_json_object(required["admin_permissions"], label="admin_permissions")
    _load_json_object(required["symbols"], label="symbols")
    strategy_auditor_lib.load_settings(path=str(required["intelligence_settings"]))
    admin_permissions.reload_roles_config()
    admin_permissions.reload_permissions_config()
    distribution_router.load_config()


def initialize_for_railway(*, base_dir: Path | None = None) -> Dict[str, Any]:
    base_dir = base_dir or resolve_base_dir(require_explicit=True)
    paths = runtime_paths(base_dir)
    apply_path_contract(base_dir)

    created_dirs: list[str] = []
    for key in ("base", "config", "state", "outcomes", "observability", "analytics", "snapshots"):
        path = paths[key]
        if not path.exists():
            created_dirs.append(str(path))
        path.mkdir(parents=True, exist_ok=True)

    for extra in (paths["analytics"] / "reports", paths["analytics"] / "cache"):
        if not extra.exists():
            created_dirs.append(str(extra))
        extra.mkdir(parents=True, exist_ok=True)

    seeded: list[str] = []
    preserved: list[str] = []
    source_config_dir = SEND_ROOT / "config"
    for name in CONFIG_SEED_FILES:
        source = source_config_dir / name
        destination = paths["config"] / name
        if not source.is_file():
            raise RailwayInitError(f"Seed source missing: {source}")
        if destination.exists():
            preserved.append(str(destination))
            continue
        shutil.copy2(source, destination)
        seeded.append(str(destination))

    try:
        _validate_config_tree(base_dir)
    except RailwayInitError:
        raise
    except Exception as exc:
        raise RailwayInitError(f"Railway init validation failed: {exc}") from exc

    return {
        "base_dir": str(base_dir),
        "created_dirs": created_dirs,
        "seeded_files": seeded,
        "preserved_files": preserved,
    }


def _print_summary(summary: Dict[str, Any]) -> None:
    print("Railway init ready")
    print(f"base_dir={summary['base_dir']}")
    print(f"created_dirs={len(summary['created_dirs'])}")
    print(f"seeded_files={len(summary['seeded_files'])}")
    print(f"preserved_files={len(summary['preserved_files'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Railway runtime directories and config.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary")
    args = parser.parse_args(argv)

    try:
        summary = initialize_for_railway()
    except Exception as exc:
        print(f"Railway init failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
