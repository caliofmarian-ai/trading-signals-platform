from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import railway_init


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_permission_config_is_noop(tmp_path: Path):
    source = Path("send/config/admin_permissions.json")
    path = tmp_path / "admin_permissions.json"
    path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    result = railway_init._migrate_legacy_admin_permissions(path)

    assert result["migrated"] is False
    assert result["reason"] == "legacy_permission_absent"
    assert path.read_text(encoding="utf-8") == before


def test_legacy_affiliate_permission_is_split_conservatively(tmp_path: Path):
    path = tmp_path / "admin_permissions.json"
    _write(
        path,
        {
            "permissions": {
                "admin.view": ["owner", "primary_admin", "affiliate_admin"],
                "affiliate.view": ["owner", "primary_admin", "affiliate_admin"],
                "strategy.view": ["owner"],
            }
        },
    )

    result = railway_init._migrate_legacy_admin_permissions(path)
    payload = _read(path)
    permissions = payload["permissions"]

    assert result["migrated"] is True
    assert "affiliate.view" not in permissions
    assert permissions["affiliate.view.any"] == ["owner", "primary_admin"]
    assert permissions["affiliate.view.own"] == ["owner", "affiliate_admin"]
    assert permissions["admin.view"] == ["owner", "primary_admin", "affiliate_admin"]
    assert permissions["strategy.view"] == ["owner"]


def test_migration_preserves_existing_scoped_grants_without_duplicates(tmp_path: Path):
    path = tmp_path / "admin_permissions.json"
    _write(
        path,
        {
            "permissions": {
                "affiliate.view": ["owner", "primary_admin", "affiliate_admin"],
                "affiliate.view.any": ["owner"],
                "affiliate.view.own": ["owner"],
            }
        },
    )

    railway_init._migrate_legacy_admin_permissions(path)
    permissions = _read(path)["permissions"]

    assert permissions["affiliate.view.any"] == ["owner", "primary_admin"]
    assert permissions["affiliate.view.own"] == ["owner", "affiliate_admin"]


def test_migration_is_idempotent(tmp_path: Path):
    path = tmp_path / "admin_permissions.json"
    _write(
        path,
        {"permissions": {"affiliate.view": ["owner", "affiliate_admin"]}},
    )

    first = railway_init._migrate_legacy_admin_permissions(path)
    after_first = path.read_text(encoding="utf-8")
    second = railway_init._migrate_legacy_admin_permissions(path)

    assert first["migrated"] is True
    assert second["migrated"] is False
    assert second["reason"] == "legacy_permission_absent"
    assert path.read_text(encoding="utf-8") == after_first


def test_unexpected_legacy_role_fails_closed_without_rewriting_file(tmp_path: Path):
    path = tmp_path / "admin_permissions.json"
    _write(
        path,
        {"permissions": {"affiliate.view": ["owner", "analyst"]}},
    )
    before = path.read_text(encoding="utf-8")

    with pytest.raises(railway_init.RailwayInitError, match="unsupported role"):
        railway_init._migrate_legacy_admin_permissions(path)

    assert path.read_text(encoding="utf-8") == before


def test_initialize_migrates_preserved_permission_before_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    base_dir = tmp_path / "data"
    permissions_path = base_dir / "config" / "admin_permissions.json"
    _write(
        permissions_path,
        {"permissions": {"affiliate.view": ["owner", "primary_admin", "affiliate_admin"]}},
    )

    observed: dict = {}

    def _validate(base: Path) -> None:
        observed.update(_read(base / "config" / "admin_permissions.json"))

    monkeypatch.setattr(railway_init, "_validate_config_tree", _validate)

    summary = railway_init.initialize_for_railway(base_dir=base_dir)

    assert summary["admin_permissions_migration"]["migrated"] is True
    permissions = observed["permissions"]
    assert "affiliate.view" not in permissions
    assert permissions["affiliate.view.any"] == ["owner", "primary_admin"]
    assert permissions["affiliate.view.own"] == ["owner", "affiliate_admin"]
