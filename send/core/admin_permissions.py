from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

from core.role_constants import (
    ROLE_OWNER,
    ROLE_PRIMARY_ADMIN,
    ROLE_STRATEGY_ADMIN,
    ROLE_RESEARCH_ADMIN,
    ROLE_AFFILIATE_ADMIN,
    ROLE_MODERATOR,
    ROLE_ANALYST,
    ROLE_USER,
    ALL_ROLES,
    ROLE_PRIORITY,
)

# Re-export so callers that imported these from admin_permissions continue to work.
__all__ = [
    "ROLE_OWNER",
    "ROLE_PRIMARY_ADMIN",
    "ROLE_STRATEGY_ADMIN",
    "ROLE_RESEARCH_ADMIN",
    "ROLE_AFFILIATE_ADMIN",
    "ROLE_MODERATOR",
    "ROLE_ANALYST",
    "ROLE_USER",
    "ALL_ROLES",
    "ROLE_PRIORITY",
]

ROLES_CONFIG_PATH = os.getenv("ADMIN_ROLES_CONFIG", "/opt/binarybot/config/admin_roles.json")

# Path to the permissions config file that maps permission names to allowed roles.
# When present, this file is merged with (and can extend) the hardcoded PERMISSION_MATRIX.
# Resolves GAP-012: previously this file existed on disk but was completely ignored.
PERMISSIONS_CONFIG_PATH = os.getenv(
    "ADMIN_PERMISSIONS_CONFIG", "/opt/binarybot/config/admin_permissions.json"
)

# Canonical permission surface for admin tier.
PERMISSION_MATRIX: Dict[str, Set[str]] = {
    ROLE_OWNER: {
        "admin.view",
        "engine.view",
        "engine.restart",
        "strategy.view",
        "strategy.thresholds.write",
        "strategy.sr.write",
        "strategy.spike.write",
        "strategy.symbols.write",
        "reports.view",
        "debug.view",
        "channels.view",
        "channels.test",
        "roles.view",
        "roles.write",
        "affiliate.view.any",
        "affiliate.view.own",
        "files.view",
        "diagnostics.view",
    },
    ROLE_PRIMARY_ADMIN: {
        "admin.view",
        "engine.view",
        "engine.restart",
        "strategy.view",
        "strategy.thresholds.write",
        "strategy.sr.write",
        "strategy.spike.write",
        "strategy.symbols.write",
        "reports.view",
        "debug.view",
        "channels.view",
        "channels.test",
        "roles.view",
        "affiliate.view.any",
        "files.view",
        "diagnostics.view",
    },
    ROLE_STRATEGY_ADMIN: {
        "admin.view",
        "engine.view",
        "strategy.view",
        "strategy.thresholds.write",
        "strategy.sr.write",
        "strategy.spike.write",
        "strategy.symbols.write",
        "reports.view",
        "debug.view",
        "files.view",
    },
    ROLE_RESEARCH_ADMIN: {
        "admin.view",
        "engine.view",
        "strategy.view",
        "reports.view",
        "debug.view",
        "files.view",
    },
    ROLE_ANALYST: {
        "admin.view",
        "engine.view",
        "strategy.view",
        "reports.view",
        "debug.view",
    },
    ROLE_MODERATOR: {
        "admin.view",
        "engine.view",
        "channels.view",
    },
    ROLE_AFFILIATE_ADMIN: {
        "admin.view",
        "affiliate.view.own",
    },
    ROLE_USER: set(),
}

# Mapping from lowercase role names in admin_permissions.json to canonical role constants.
# Used when loading the file-based permission config (GAP-012).
_ROLE_NAME_MAP: Dict[str, str] = {
    "owner": ROLE_OWNER,
    "primary_admin": ROLE_PRIMARY_ADMIN,
    "strategy_admin": ROLE_STRATEGY_ADMIN,
    "research_admin": ROLE_RESEARCH_ADMIN,
    "analyst": ROLE_ANALYST,
    "moderator": ROLE_MODERATOR,
    "affiliate_admin": ROLE_AFFILIATE_ADMIN,
    "user": ROLE_USER,
}


@dataclass(frozen=True)
class AffiliateScope:
    affiliate_code: str
    telegram_id: int
    referral_code: str = ""


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _load_json_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    if not raw:
        return {}

    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def load_permissions_config() -> Dict[str, Set[str]]:
    """
    Load role → permissions mapping from admin_permissions.json (GAP-012).

    File format (permissions block maps permission names to allowed role names):
      {
        "permissions": {
          "admin.view": ["owner", "primary_admin", ...],
          ...
        }
      }

    Returns a dict: {ROLE_CONSTANT: {permission_name, ...}}
    Returns an empty dict if the file is absent, empty, or malformed
    (callers then fall back to the hardcoded PERMISSION_MATRIX).
    """
    data = _load_json_file(PERMISSIONS_CONFIG_PATH)
    permissions_block = data.get("permissions", {})
    if not isinstance(permissions_block, dict) or not permissions_block:
        return {}

    result: Dict[str, Set[str]] = {}
    for perm_name, role_names in permissions_block.items():
        if not isinstance(perm_name, str) or not perm_name.strip():
            continue
        if not isinstance(role_names, list):
            continue
        for role_name in role_names:
            role_const = _ROLE_NAME_MAP.get(str(role_name).strip().lower())
            if role_const is None:
                continue
            result.setdefault(role_const, set()).add(perm_name.strip())

    return result


def reload_permissions_config() -> Dict[str, Set[str]]:
    load_permissions_config.cache_clear()
    return load_permissions_config()


@lru_cache(maxsize=1)
def load_roles_config() -> Dict[str, Any]:
    """
    Loads admin role configuration.

    Expected shape example:
    {
      "owner": [123],
      "primary_admin": [456],
      "strategy_admin": [789],
      "research_admin": [],
      "analyst": [],
      "moderator": [],
      "affiliate_admin": {
        "trader_x": {
          "telegram_id": 111,
          "referral_code": "TRADER_X"
        }
      }
    }
    """
    data = _load_json_file(ROLES_CONFIG_PATH)

    # Optional environment fallback for owner.
    owner_env = os.getenv("OWNER_TELEGRAM_ID", "").strip()
    owner_id = _safe_int(owner_env)
    if owner_id is not None:
        owners = data.get("owner", [])
        if not isinstance(owners, list):
            owners = []
        if owner_id not in owners:
            owners.append(owner_id)
        data["owner"] = owners

    return data


def reload_roles_config() -> Dict[str, Any]:
    load_roles_config.cache_clear()
    return load_roles_config()


def _ids_from_key(data: Dict[str, Any], key: str) -> Set[int]:
    raw = data.get(key, [])
    if not isinstance(raw, list):
        return set()

    result: Set[int] = set()
    for item in raw:
        value = _safe_int(item)
        if value is not None:
            result.add(value)
    return result


def _affiliate_scopes(data: Dict[str, Any]) -> Dict[int, AffiliateScope]:
    raw = data.get("affiliate_admin", {})
    if not isinstance(raw, dict):
        return {}

    result: Dict[int, AffiliateScope] = {}
    for affiliate_code, payload in raw.items():
        if not isinstance(payload, dict):
            continue

        telegram_id = _safe_int(payload.get("telegram_id"))
        if telegram_id is None:
            continue

        result[telegram_id] = AffiliateScope(
            affiliate_code=str(affiliate_code),
            telegram_id=telegram_id,
            referral_code=str(payload.get("referral_code", affiliate_code)),
        )
    return result


def get_user_roles(user_id: int) -> List[str]:
    data = load_roles_config()
    roles: List[str] = []

    if user_id in _ids_from_key(data, "owner"):
        roles.append(ROLE_OWNER)
    if user_id in _ids_from_key(data, "primary_admin"):
        roles.append(ROLE_PRIMARY_ADMIN)
    if user_id in _ids_from_key(data, "strategy_admin"):
        roles.append(ROLE_STRATEGY_ADMIN)
    if user_id in _ids_from_key(data, "research_admin"):
        roles.append(ROLE_RESEARCH_ADMIN)
    if user_id in _ids_from_key(data, "analyst"):
        roles.append(ROLE_ANALYST)
    if user_id in _ids_from_key(data, "moderator"):
        roles.append(ROLE_MODERATOR)
    if user_id in _affiliate_scopes(data):
        roles.append(ROLE_AFFILIATE_ADMIN)

    if not roles:
        roles.append(ROLE_USER)

    return sorted(roles, key=lambda r: ROLE_PRIORITY.get(r, 999))


def get_primary_role(user_id: int) -> str:
    roles = get_user_roles(user_id)
    return roles[0] if roles else ROLE_USER


def get_affiliate_scope(user_id: int) -> Optional[AffiliateScope]:
    data = load_roles_config()
    return _affiliate_scopes(data).get(user_id)


def is_owner(user_id: int) -> bool:
    return ROLE_OWNER in get_user_roles(user_id)


def is_primary_admin(user_id: int) -> bool:
    return ROLE_PRIMARY_ADMIN in get_user_roles(user_id) or is_owner(user_id)


def list_permissions_for_user(user_id: int) -> Set[str]:
    roles = get_user_roles(user_id)
    # Merge hardcoded PERMISSION_MATRIX with any additional entries from the config file.
    # The config file is authoritative for any permissions it defines; the hardcoded matrix
    # provides the baseline. GAP-012: admin_permissions.json is now actually loaded.
    file_matrix = load_permissions_config()  # empty dict if file absent or invalid
    permissions: Set[str] = set()
    for role in roles:
        permissions.update(PERMISSION_MATRIX.get(role, set()))
        permissions.update(file_matrix.get(role, set()))
    return permissions


def has_permission(user_id: int, permission: str, target_affiliate_code: Optional[str] = None) -> bool:
    """
    Permission rules:
    - OWNER bypasses everything.
    - PRIMARY_ADMIN inherits broad admin capabilities.
    - AFFILIATE_ADMIN may only view own affiliate scope.
    """
    if is_owner(user_id):
        return True

    permissions = list_permissions_for_user(user_id)
    if permission in permissions:
        return True

    # Scoped affiliate access:
    if permission == "affiliate.view":
        if "affiliate.view.any" in permissions:
            return True
        if "affiliate.view.own" in permissions:
            scope = get_affiliate_scope(user_id)
            if scope is None:
                return False
            if target_affiliate_code is None:
                return True
            return target_affiliate_code == scope.affiliate_code or target_affiliate_code == scope.referral_code

    return False


def require_permission(user_id: int, permission: str, target_affiliate_code: Optional[str] = None) -> Tuple[bool, str]:
    ok = has_permission(user_id, permission, target_affiliate_code=target_affiliate_code)
    if ok:
        return True, ""

    role = get_primary_role(user_id)
    return False, f"unauthorized: role={role} permission={permission}"


def debug_identity(user_id: int) -> Dict[str, Any]:
    scope = get_affiliate_scope(user_id)
    return {
        "user_id": user_id,
        "roles": get_user_roles(user_id),
        "primary_role": get_primary_role(user_id),
        "permissions": sorted(list_permissions_for_user(user_id)),
        "affiliate_scope": None if scope is None else {
            "affiliate_code": scope.affiliate_code,
            "referral_code": scope.referral_code,
        },
    }