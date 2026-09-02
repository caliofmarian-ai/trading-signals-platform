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


_LEGACY_AFFILIATE_PERMISSION = "affiliate.view"
_LEGACY_AFFILIATE_ROLE_TARGETS = {
    "owner": ("affiliate.view.any", "affiliate.view.own"),
    "primary_admin": ("affiliate.view.any",),
    "affiliate_admin": ("affiliate.view.own",),
}


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


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.migration.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        try:
            if temporary.exists():
                temporary.unlink()
        except OSError:
            pass


def _migrate_legacy_admin_permissions(path: Path) -> Dict[str, Any]:
    """Conservatively migrate the pre-R016 synthetic affiliate permission.

    Railway intentionally preserves Owner-controlled configuration on the
    persistent volume. R-016 split the old synthetic ``affiliate.view`` grant
    into explicit any-scope and own-scope grants, so a preserved pre-R016 file
    must be migrated before strict permission validation can run.

    Only the known legacy key is changed. Unexpected roles fail closed rather
    than being guessed, and all unrelated permission customizations are kept.
    """
    payload = _load_json_object(path, label="admin_permissions")
    permissions = payload.get("permissions")
    if not isinstance(permissions, dict):
        return {
            "migrated": False,
            "reason": "permissions_block_not_migratable",
            "legacy_permission": _LEGACY_AFFILIATE_PERMISSION,
        }

    if _LEGACY_AFFILIATE_PERMISSION not in permissions:
        return {
            "migrated": False,
            "reason": "legacy_permission_absent",
            "legacy_permission": _LEGACY_AFFILIATE_PERMISSION,
        }

    legacy_roles = permissions.get(_LEGACY_AFFILIATE_PERMISSION)
    if not isinstance(legacy_roles, list):
        raise RailwayInitError(
            f"admin_permissions.{_LEGACY_AFFILIATE_PERMISSION} must map to a role list"
        )

    target_additions: Dict[str, list[str]] = {}
    seen_legacy_roles: set[str] = set()
    for raw_role in legacy_roles:
        normalized_role = str(raw_role).strip().lower()
        if not normalized_role:
            raise RailwayInitError(
                f"admin_permissions.{_LEGACY_AFFILIATE_PERMISSION} contains an empty role"
            )
        if normalized_role in seen_legacy_roles:
            continue
        seen_legacy_roles.add(normalized_role)

        targets = _LEGACY_AFFILIATE_ROLE_TARGETS.get(normalized_role)
        if targets is None:
            raise RailwayInitError(
                "Legacy affiliate permission contains an unsupported role; "
                f"refusing unsafe migration: {normalized_role}"
            )
        for target_permission in targets:
            target_additions.setdefault(target_permission, []).append(normalized_role)

    for target_permission, additions in target_additions.items():
        existing = permissions.get(target_permission, [])
        if not isinstance(existing, list):
            raise RailwayInitError(
                f"admin_permissions.{target_permission} must map to a role list"
            )
        existing_normalized = {str(role).strip().lower() for role in existing}
        merged = list(existing)
        for role_name in additions:
            if role_name not in existing_normalized:
                merged.append(role_name)
                existing_normalized.add(role_name)
        permissions[target_permission] = merged

    permissions.pop(_LEGACY_AFFILIATE_PERMISSION, None)
    _write_json_atomic(path, payload)
    return {
        "migrated": True,
        "reason": "legacy_affiliate_permission_split",
        "legacy_permission": _LEGACY_AFFILIATE_PERMISSION,
        "legacy_roles": sorted(seen_legacy_roles),
        "target_permissions": sorted(target_additions.keys()),
    }


def _validate_config_tree(base_dir: Path) -> None:
    apply_path_contract(base_dir)

    from core import admin_permissions, distribution_router, runtime_param_gate
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

    runtime_param_gate.load_runtime_algo_params(path=str(required["algo_params"]))
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

    created_files: list[str] = []
    for key in (
        "admin_events_log",
        "admin_proofs_log",
        "dist_events_log",
        "engine_events_log",
        "error_events_log",
        "fsm_events_log",
        "outcomes_log",
    ):
        path = paths[key]
        if not path.exists():
            created_files.append(str(path))
            path.touch()

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

    permission_migration = _migrate_legacy_admin_permissions(
        paths["config"] / "admin_permissions.json"
    )

    try:
        _validate_config_tree(base_dir)
    except RailwayInitError:
        raise
    except Exception as exc:
        raise RailwayInitError(f"Railway init validation failed: {exc}") from exc

    return {
        "base_dir": str(base_dir),
        "created_dirs": created_dirs,
        "created_files": created_files,
        "seeded_files": seeded,
        "preserved_files": preserved,
        "admin_permissions_migration": permission_migration,
    }


def _print_summary(summary: Dict[str, Any]) -> None:
    print("Railway init ready")
    print(f"base_dir={summary['base_dir']}")
    print(f"created_dirs={len(summary['created_dirs'])}")
    print(f"seeded_files={len(summary['seeded_files'])}")
    print(f"preserved_files={len(summary['preserved_files'])}")
    migration = summary.get("admin_permissions_migration") or {}
    print(f"admin_permissions_migrated={bool(migration.get('migrated'))}")


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
