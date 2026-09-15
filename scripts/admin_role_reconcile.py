from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from scripts.railway_common import SEND_ROOT, env_flag, runtime_paths

_SYNC_FLAG = "ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE"


class AdminRoleReconcileError(RuntimeError):
    pass


def _load_json_object(path: Path, *, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AdminRoleReconcileError(f"Unable to read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise AdminRoleReconcileError(f"{label} must be a JSON object: {path}")
    return payload


def _validated_primary_admin(payload: Dict[str, Any], *, label: str) -> list[int]:
    raw = payload.get("primary_admin")
    if not isinstance(raw, list) or not raw:
        raise AdminRoleReconcileError(f"{label}.primary_admin must be a non-empty list")

    normalized: list[int] = []
    for value in raw:
        try:
            user_id = int(value)
        except Exception as exc:
            raise AdminRoleReconcileError(
                f"{label}.primary_admin contains a non-integer identity"
            ) from exc
        if user_id <= 0:
            raise AdminRoleReconcileError(
                f"{label}.primary_admin identities must be positive integers"
            )
        if user_id not in normalized:
            normalized.append(user_id)
    return normalized


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def reconcile_primary_admin_from_source(
    *,
    base_dir: Path,
    source_roles_path: Path | None = None,
) -> Dict[str, Any]:
    """Optionally reconcile only PRIMARY_ADMIN identity into persistent config.

    Railway intentionally preserves the Owner-controlled role file on `/data`.
    This migration hook is disabled by default. When explicitly enabled with
    `ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE=true`, it copies only the
    `primary_admin` list from the repository role config into the persistent
    role config. All other roles, affiliate records, and permission grants are
    preserved byte-for-semantics.
    """

    if not env_flag(_SYNC_FLAG, default=False):
        return {"enabled": False, "changed": False, "reason": "sync_disabled"}

    source_path = source_roles_path or (SEND_ROOT / "config" / "admin_roles.json")
    destination_path = runtime_paths(base_dir)["admin_roles"]

    source_payload = _load_json_object(source_path, label="source_admin_roles")
    destination_payload = _load_json_object(
        destination_path, label="persistent_admin_roles"
    )

    desired = _validated_primary_admin(source_payload, label="source_admin_roles")
    current = _validated_primary_admin(
        destination_payload, label="persistent_admin_roles"
    )

    if current == desired:
        return {
            "enabled": True,
            "changed": False,
            "reason": "already_reconciled",
            "primary_admin_count": len(desired),
        }

    destination_payload["primary_admin"] = desired
    _write_json_atomic(destination_path, destination_payload)

    # initialize_for_railway() may already have imported and cached the role
    # configuration. Refresh it immediately so this process sees the migrated
    # identity before Telegram/runtime boot continues.
    from core import admin_permissions

    admin_permissions.reload_roles_config()

    return {
        "enabled": True,
        "changed": True,
        "reason": "primary_admin_reconciled_from_source",
        "primary_admin_count": len(desired),
    }
