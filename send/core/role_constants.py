"""
send/core/role_constants.py

Canonical role identifier constants — single source of truth.

All modules that need role identifiers must import from here.
This resolves the duplication between admin_permissions.py and
telegram_admin_ui.py without creating circular import dependencies.

Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §3–§5
"""
from __future__ import annotations

from typing import Dict, FrozenSet

# ---------------------------------------------------------------------------
# Canonical role string constants
# Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5
# ---------------------------------------------------------------------------

ROLE_OWNER: str = "OWNER"
ROLE_PRIMARY_ADMIN: str = "PRIMARY_ADMIN"
ROLE_STRATEGY_ADMIN: str = "STRATEGY_ADMIN"
ROLE_RESEARCH_ADMIN: str = "RESEARCH_ADMIN"
ROLE_ANALYST: str = "ANALYST"
ROLE_MODERATOR: str = "MODERATOR"
ROLE_AFFILIATE_ADMIN: str = "AFFILIATE_ADMIN"
ROLE_USER: str = "USER"

# Complete set of all canonical roles
ALL_ROLES: FrozenSet[str] = frozenset({
    ROLE_OWNER,
    ROLE_PRIMARY_ADMIN,
    ROLE_STRATEGY_ADMIN,
    ROLE_RESEARCH_ADMIN,
    ROLE_ANALYST,
    ROLE_MODERATOR,
    ROLE_AFFILIATE_ADMIN,
    ROLE_USER,
})

# All roles with any admin-tier privilege
# Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §4 (hierarchy: Owner → … → User)
ADMIN_TIER_ROLES: FrozenSet[str] = frozenset({
    ROLE_OWNER,
    ROLE_PRIMARY_ADMIN,
    ROLE_STRATEGY_ADMIN,
    ROLE_RESEARCH_ADMIN,
    ROLE_ANALYST,
    ROLE_MODERATOR,
    ROLE_AFFILIATE_ADMIN,
})

# Higher index = lower governance authority
# Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §4
ROLE_PRIORITY: Dict[str, int] = {
    ROLE_OWNER: 0,
    ROLE_PRIMARY_ADMIN: 1,
    ROLE_STRATEGY_ADMIN: 2,
    ROLE_RESEARCH_ADMIN: 2,
    ROLE_ANALYST: 3,
    ROLE_MODERATOR: 4,
    ROLE_AFFILIATE_ADMIN: 4,
    ROLE_USER: 99,
}

# Human-readable labels for each canonical role
# Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5
ROLE_LABELS: Dict[str, str] = {
    ROLE_OWNER: "Owner",
    ROLE_PRIMARY_ADMIN: "Primary Admin",
    ROLE_STRATEGY_ADMIN: "Functional Admin (Operations)",
    ROLE_RESEARCH_ADMIN: "Functional Admin (Research)",
    ROLE_ANALYST: "Analyst",
    ROLE_MODERATOR: "Moderator",
    ROLE_AFFILIATE_ADMIN: "Affiliate Admin",
    ROLE_USER: "User",
}
