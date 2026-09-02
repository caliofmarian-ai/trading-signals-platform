from __future__ import annotations

import json
from pathlib import Path

import pytest

from core import admin_permissions
from runtime import startup_preflight


OWNER = 1001
PRIMARY = 2002
STRATEGY = 3003
RESEARCH = 4004
ANALYST = 5005
MODERATOR = 6006
AFFILIATE = 7007
USER = 9999


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _roles_payload() -> dict:
    return {
        "owner": [OWNER],
        "primary_admin": [PRIMARY],
        "strategy_admin": [STRATEGY],
        "research_admin": [RESEARCH],
        "analyst": [ANALYST],
        "moderator": [MODERATOR],
        "affiliate_admin": {
            "AFF001": {
                "telegram_id": AFFILIATE,
                "referral_code": "REF001",
            }
        },
    }


def _configure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    permissions_payload,
    *,
    raw_permissions: str | None = None,
) -> tuple[Path, Path]:
    roles_path = tmp_path / "config" / "admin_roles.json"
    permissions_path = tmp_path / "config" / "admin_permissions.json"
    _write_json(roles_path, _roles_payload())
    permissions_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_permissions is not None:
        permissions_path.write_text(raw_permissions, encoding="utf-8")
    elif permissions_payload is not None:
        _write_json(permissions_path, permissions_payload)

    monkeypatch.setattr(admin_permissions, "ROLES_CONFIG_PATH", str(roles_path))
    monkeypatch.setattr(admin_permissions, "PERMISSIONS_CONFIG_PATH", str(permissions_path))
    monkeypatch.delenv("OWNER_TELEGRAM_ID", raising=False)
    admin_permissions.load_roles_config.cache_clear()
    admin_permissions.load_permissions_config.cache_clear()
    return roles_path, permissions_path


@pytest.fixture(autouse=True)
def _clear_permission_caches():
    admin_permissions.load_roles_config.cache_clear()
    admin_permissions.load_permissions_config.cache_clear()
    yield
    admin_permissions.load_roles_config.cache_clear()
    admin_permissions.load_permissions_config.cache_clear()


def test_malformed_permission_state_denies_non_owner_but_preserves_owner_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(tmp_path, monkeypatch, None, raw_permissions="{bad json")

    with pytest.raises(admin_permissions.PermissionConfigurationError, match="invalid JSON"):
        admin_permissions.reload_permissions_config()

    assert admin_permissions.has_permission(OWNER, "roles.write") is True
    assert admin_permissions.has_permission(PRIMARY, "admin.view") is False
    ok, reason = admin_permissions.require_permission(PRIMARY, "admin.view")
    assert ok is False
    assert "permission configuration invalid" in reason

    owner_identity = admin_permissions.debug_identity(OWNER)
    assert owner_identity["permission_config_status"] == "BLOCKED"
    assert "invalid JSON" in owner_identity["permission_config_error"]


def test_permission_config_cannot_broaden_governed_role_ceiling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(
        tmp_path,
        monkeypatch,
        {"permissions": {"roles.write": ["primary_admin"]}},
    )

    with pytest.raises(
        admin_permissions.PermissionConfigurationError,
        match="exceeds governed baseline",
    ):
        admin_permissions.reload_permissions_config()

    assert admin_permissions.has_permission(PRIMARY, "roles.write") is False
    assert admin_permissions.has_permission(OWNER, "roles.write") is True


def test_valid_config_is_effective_grant_authority_below_baseline_ceiling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(
        tmp_path,
        monkeypatch,
        {
            "permissions": {
                "admin.view": ["primary_admin", "strategy_admin"],
                "strategy.view": ["strategy_admin"],
            }
        },
    )
    loaded = admin_permissions.reload_permissions_config()

    assert "admin.view" in loaded[admin_permissions.ROLE_PRIMARY_ADMIN]
    assert admin_permissions.has_permission(PRIMARY, "admin.view") is True
    # Baseline contains engine.restart for PRIMARY_ADMIN, but omission from the
    # effective config is an explicit restriction rather than a fallback grant.
    assert admin_permissions.has_permission(PRIMARY, "engine.restart") is False
    assert admin_permissions.has_permission(STRATEGY, "strategy.view") is True
    assert admin_permissions.has_permission(ANALYST, "admin.view") is False
    assert admin_permissions.has_permission(USER, "admin.view") is False


def test_synthetic_affiliate_view_cannot_be_granted_directly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(
        tmp_path,
        monkeypatch,
        {"permissions": {"affiliate.view": ["affiliate_admin"]}},
    )

    with pytest.raises(
        admin_permissions.PermissionConfigurationError,
        match="Synthetic scoped permission",
    ):
        admin_permissions.reload_permissions_config()
    assert admin_permissions.has_permission(AFFILIATE, "affiliate.view") is False


def test_affiliate_access_is_resolved_through_own_and_any_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(
        tmp_path,
        monkeypatch,
        {
            "permissions": {
                "affiliate.view.any": ["primary_admin"],
                "affiliate.view.own": ["affiliate_admin"],
            }
        },
    )
    admin_permissions.reload_permissions_config()

    assert admin_permissions.has_permission(
        AFFILIATE, "affiliate.view", target_affiliate_code="AFF001"
    )
    assert admin_permissions.has_permission(
        AFFILIATE, "affiliate.view", target_affiliate_code="REF001"
    )
    assert not admin_permissions.has_permission(
        AFFILIATE, "affiliate.view", target_affiliate_code="OTHER"
    )
    assert admin_permissions.has_permission(
        PRIMARY, "affiliate.view", target_affiliate_code="OTHER"
    )
    assert not admin_permissions.has_permission(
        ANALYST, "affiliate.view", target_affiliate_code="AFF001"
    )


def test_unknown_permission_and_unknown_role_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(
        tmp_path,
        monkeypatch,
        {"permissions": {"root.shell": ["primary_admin"]}},
    )
    with pytest.raises(admin_permissions.PermissionConfigurationError, match="outside the governed baseline"):
        admin_permissions.reload_permissions_config()

    _configure(
        tmp_path,
        monkeypatch,
        {"permissions": {"admin.view": ["super_admin"]}},
    )
    with pytest.raises(admin_permissions.PermissionConfigurationError, match="unknown role"):
        admin_permissions.reload_permissions_config()


def test_startup_preflight_rejects_permission_broadening_with_same_loader_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roles_path, permissions_path = _configure(
        tmp_path,
        monkeypatch,
        {"permissions": {"roles.write": ["primary_admin"]}},
    )

    def _config_path(filename: str) -> str:
        if filename == "admin_roles.json":
            return str(roles_path)
        if filename == "admin_permissions.json":
            return str(permissions_path)
        return str(tmp_path / "config" / filename)

    monkeypatch.setattr(startup_preflight.storage, "config_path", _config_path)

    with pytest.raises(
        startup_preflight.StartupPreflightError,
        match="exceeds governed baseline",
    ):
        startup_preflight._validate_admin_control_config()
