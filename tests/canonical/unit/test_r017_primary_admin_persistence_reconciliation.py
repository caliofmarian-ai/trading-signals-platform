from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from scripts import admin_role_reconcile


LIVE_PRIMARY_ADMIN_ID = 6766369444
STALE_PRIMARY_ADMIN_ID = 6766367444


def _payload(primary_admin: list[int]) -> dict:
    return {
        "owner": [7553887987],
        "primary_admin": primary_admin,
        "strategy_admin": [],
        "research_admin": [],
        "analyst": [],
        "moderator": [],
        "affiliate_admin": {
            "AFF001": {
                "telegram_id": 0,
                "display_name": "Example Affiliate",
                "commission_percent": 30,
                "channels": ["VIP_SIGNALS", "FOREX_SIGNALS"],
            }
        },
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _purge_admin_permissions() -> None:
    sys.modules.pop("core.admin_permissions", None)
    importlib.invalidate_caches()


def test_repository_role_config_uses_verified_live_primary_admin_identity():
    payload = json.loads(
        (SEND_ROOT / "config" / "admin_roles.json").read_text(encoding="utf-8")
    )
    assert payload["primary_admin"] == [LIVE_PRIMARY_ADMIN_ID]
    assert STALE_PRIMARY_ADMIN_ID not in payload["primary_admin"]


def test_sync_disabled_preserves_persistent_primary_admin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source_roles = tmp_path / "source" / "config" / "admin_roles.json"
    persistent_roles = tmp_path / "data" / "config" / "admin_roles.json"
    _write(source_roles, _payload([LIVE_PRIMARY_ADMIN_ID]))
    _write(persistent_roles, _payload([STALE_PRIMARY_ADMIN_ID]))

    monkeypatch.delenv("ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE", raising=False)
    result = admin_role_reconcile.reconcile_primary_admin_from_source(
        base_dir=tmp_path / "data",
        source_roles_path=source_roles,
    )

    assert result == {"enabled": False, "changed": False, "reason": "sync_disabled"}
    assert json.loads(persistent_roles.read_text(encoding="utf-8"))["primary_admin"] == [
        STALE_PRIMARY_ADMIN_ID
    ]


def test_enabled_sync_changes_only_primary_admin_and_refreshes_runtime_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source_roles = tmp_path / "source" / "config" / "admin_roles.json"
    persistent_roles = tmp_path / "data" / "config" / "admin_roles.json"
    source_payload = _payload([LIVE_PRIMARY_ADMIN_ID])
    persistent_payload = _payload([STALE_PRIMARY_ADMIN_ID])
    persistent_payload["moderator"] = [8123]
    persistent_payload["affiliate_admin"]["AFF001"]["display_name"] = "Persisted Partner"
    _write(source_roles, source_payload)
    _write(persistent_roles, persistent_payload)

    monkeypatch.setenv("ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE", "true")
    monkeypatch.setenv("ADMIN_ROLES_CONFIG", str(persistent_roles))
    _purge_admin_permissions()

    result = admin_role_reconcile.reconcile_primary_admin_from_source(
        base_dir=tmp_path / "data",
        source_roles_path=source_roles,
    )

    stored = json.loads(persistent_roles.read_text(encoding="utf-8"))
    assert result["enabled"] is True
    assert result["changed"] is True
    assert result["reason"] == "primary_admin_reconciled_from_source"
    assert stored["primary_admin"] == [LIVE_PRIMARY_ADMIN_ID]
    assert stored["moderator"] == [8123]
    assert stored["affiliate_admin"]["AFF001"]["display_name"] == "Persisted Partner"

    permissions = importlib.import_module("core.admin_permissions")
    assert permissions.get_primary_role(LIVE_PRIMARY_ADMIN_ID) == "PRIMARY_ADMIN"
    assert permissions.get_primary_role(STALE_PRIMARY_ADMIN_ID) == "USER"
    _purge_admin_permissions()


def test_enabled_sync_fails_closed_on_invalid_source_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source_roles = tmp_path / "source" / "config" / "admin_roles.json"
    persistent_roles = tmp_path / "data" / "config" / "admin_roles.json"
    source_payload = _payload([LIVE_PRIMARY_ADMIN_ID])
    source_payload["primary_admin"] = [0]
    _write(source_roles, source_payload)
    _write(persistent_roles, _payload([STALE_PRIMARY_ADMIN_ID]))

    monkeypatch.setenv("ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE", "true")

    with pytest.raises(admin_role_reconcile.AdminRoleReconcileError):
        admin_role_reconcile.reconcile_primary_admin_from_source(
            base_dir=tmp_path / "data",
            source_roles_path=source_roles,
        )

    assert json.loads(persistent_roles.read_text(encoding="utf-8"))["primary_admin"] == [
        STALE_PRIMARY_ADMIN_ID
    ]
