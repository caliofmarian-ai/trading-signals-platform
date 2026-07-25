"""
tests/telegram_app/test_role_constants.py

Tests for the canonical role constants module (role_constants.py).

Requirement coverage:
- G: Role constant single source of truth (no duplication)
- G: UI role resolution uses the authoritative role model
"""
from __future__ import annotations

import pytest


class TestRoleConstantsModule:
    """role_constants.py must define all canonical roles."""

    def test_all_canonical_roles_defined(self):
        from core.role_constants import (
            ROLE_OWNER,
            ROLE_PRIMARY_ADMIN,
            ROLE_STRATEGY_ADMIN,
            ROLE_RESEARCH_ADMIN,
            ROLE_ANALYST,
            ROLE_MODERATOR,
            ROLE_AFFILIATE_ADMIN,
            ROLE_USER,
        )
        assert ROLE_OWNER == "OWNER"
        assert ROLE_PRIMARY_ADMIN == "PRIMARY_ADMIN"
        assert ROLE_STRATEGY_ADMIN == "STRATEGY_ADMIN"
        assert ROLE_RESEARCH_ADMIN == "RESEARCH_ADMIN"
        assert ROLE_ANALYST == "ANALYST"
        assert ROLE_MODERATOR == "MODERATOR"
        assert ROLE_AFFILIATE_ADMIN == "AFFILIATE_ADMIN"
        assert ROLE_USER == "USER"

    def test_all_roles_collection(self):
        from core.role_constants import ALL_ROLES, ROLE_USER, ROLE_OWNER
        assert ROLE_USER in ALL_ROLES
        assert ROLE_OWNER in ALL_ROLES
        assert len(ALL_ROLES) == 8

    def test_admin_tier_roles_excludes_user(self):
        from core.role_constants import ADMIN_TIER_ROLES, ROLE_USER, ROLE_OWNER
        assert ROLE_USER not in ADMIN_TIER_ROLES
        assert ROLE_OWNER in ADMIN_TIER_ROLES

    def test_role_priority_ordering(self):
        from core.role_constants import ROLE_PRIORITY, ROLE_OWNER, ROLE_PRIMARY_ADMIN, ROLE_USER
        assert ROLE_PRIORITY[ROLE_OWNER] < ROLE_PRIORITY[ROLE_PRIMARY_ADMIN]
        assert ROLE_PRIORITY[ROLE_PRIMARY_ADMIN] < ROLE_PRIORITY[ROLE_USER]

    def test_role_labels_cover_all_roles(self):
        from core.role_constants import ALL_ROLES, ROLE_LABELS
        for role in ALL_ROLES:
            assert role in ROLE_LABELS
            assert isinstance(ROLE_LABELS[role], str)
            assert len(ROLE_LABELS[role]) > 0


class TestRoleConstantsConsistencyAcrossModules:
    """
    Canonical §G: UI role resolution must use the authoritative role model.
    Role constants in telegram_admin_ui must match those in admin_permissions.
    Both must derive from role_constants.
    """

    def test_telegram_admin_ui_uses_canonical_role_constants(self):
        """telegram_admin_ui must import its role values from role_constants."""
        import importlib
        import core.telegram_admin_ui as ui
        from core.role_constants import (
            ROLE_OWNER,
            ROLE_PRIMARY_ADMIN,
            ROLE_STRATEGY_ADMIN,
            ROLE_RESEARCH_ADMIN,
            ROLE_ANALYST,
            ROLE_MODERATOR,
            ROLE_AFFILIATE_ADMIN,
        )
        # The _ROLE_* aliases in telegram_admin_ui must equal the canonical constants
        assert ui._ROLE_OWNER == ROLE_OWNER
        assert ui._ROLE_PRIMARY_ADMIN == ROLE_PRIMARY_ADMIN
        assert ui._ROLE_STRATEGY_ADMIN == ROLE_STRATEGY_ADMIN
        assert ui._ROLE_RESEARCH_ADMIN == ROLE_RESEARCH_ADMIN
        assert ui._ROLE_ANALYST == ROLE_ANALYST
        assert ui._ROLE_MODERATOR == ROLE_MODERATOR
        assert ui._ROLE_AFFILIATE_ADMIN == ROLE_AFFILIATE_ADMIN

    def test_admin_permissions_uses_canonical_role_constants(self):
        """admin_permissions must expose the same role constants as role_constants."""
        import core.admin_permissions as ap
        from core.role_constants import (
            ROLE_OWNER,
            ROLE_PRIMARY_ADMIN,
            ROLE_STRATEGY_ADMIN,
            ROLE_RESEARCH_ADMIN,
            ROLE_ANALYST,
            ROLE_MODERATOR,
            ROLE_AFFILIATE_ADMIN,
            ROLE_USER,
        )
        assert ap.ROLE_OWNER == ROLE_OWNER
        assert ap.ROLE_PRIMARY_ADMIN == ROLE_PRIMARY_ADMIN
        assert ap.ROLE_STRATEGY_ADMIN == ROLE_STRATEGY_ADMIN
        assert ap.ROLE_RESEARCH_ADMIN == ROLE_RESEARCH_ADMIN
        assert ap.ROLE_ANALYST == ROLE_ANALYST
        assert ap.ROLE_MODERATOR == ROLE_MODERATOR
        assert ap.ROLE_AFFILIATE_ADMIN == ROLE_AFFILIATE_ADMIN
        assert ap.ROLE_USER == ROLE_USER

    def test_no_divergence_between_modules(self):
        """Role string values must be identical across all three modules."""
        import core.role_constants as rc
        import core.admin_permissions as ap
        import core.telegram_admin_ui as ui

        # Confirm exact same string values — no subtle differences
        assert rc.ROLE_OWNER == ap.ROLE_OWNER == ui._ROLE_OWNER
        assert rc.ROLE_PRIMARY_ADMIN == ap.ROLE_PRIMARY_ADMIN == ui._ROLE_PRIMARY_ADMIN
        assert rc.ROLE_USER == ap.ROLE_USER
