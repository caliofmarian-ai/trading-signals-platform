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
PERMISSIONS_CONFIG_PATH = os.getenv(
    "ADMIN_PERMISSIONS_CONFIG", "/opt/binarybot/config/admin_permissions.json"
)

# Governed maximum authority for each role. File-based permission configuration
# may restrict these grants, but may never widen them. Owner recovery remains a
# separate explicit bypass in has_permission()/require_permission().
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

_CONFIGURABLE_PERMISSIONS = frozenset(
    permission
    for permissions in PERMISSION_MATRIX.values()
    for permission in permissions
)
_SCOPED_SYNTHETIC_PERMISSIONS = frozenset({"affiliate.view"})


class PermissionConfigurationError(RuntimeError):
    """Permission authority is missing, malformed, or attempts to widen access."""


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
    """Best-effort role loader.

    Role resolution remains fail-closed for non-Owner users because malformed
    role state resolves to no privileged roles. OWNER_TELEGRAM_ID is handled as
    an explicit recovery source in load_roles_config(). Permission authority uses
    the stricter loader below and never falls back silently.
    """
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    except (OSError, UnicodeError):
        return {}

    if not raw:
        return {}

    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_permission_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise PermissionConfigurationError(f"Permission config is missing: {path}")
    if not os.path.isfile(path):
        raise PermissionConfigurationError(f"Permission config path is not a file: {path}")

    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read().strip()
    except UnicodeError as exc:
        raise PermissionConfigurationError(
            f"Permission config is not valid UTF-8: {path}"
        ) from exc
    except OSError as exc:
        raise PermissionConfigurationError(
            f"Permission config cannot be read: {path}: {exc}"
        ) from exc

    if not raw:
        raise PermissionConfigurationError(f"Permission config is empty: {path}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PermissionConfigurationError(
            f"Permission config is invalid JSON: {path}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise PermissionConfigurationError(
            f"Permission config must be a JSON object: {path}"
        )
    return data


@lru_cache(maxsize=1)
def load_permissions_config() -> Dict[str, Set[str]]:
    """Load explicit effective grants bounded by PERMISSION_MATRIX.

    `admin_permissions.json` is the effective non-Owner grant authority.
    `PERMISSION_MATRIX` is the governed maximum ceiling. A file grant may keep or
    remove a baseline permission, but it cannot invent a permission, grant a
    permission to a role outside that ceiling, or directly grant a synthetic
    scoped permission such as `affiliate.view`.

    Missing or malformed permission authority raises PermissionConfigurationError.
    Callers that authorize non-Owner actions must deny on that error. Owner access
    is recovered only through the explicit Owner bypass, never through fallback.
    """
    data = _load_permission_json(PERMISSIONS_CONFIG_PATH)
    permissions_block = data.get("permissions")
    if not isinstance(permissions_block, dict) or not permissions_block:
        raise PermissionConfigurationError(
            "admin_permissions.permissions must be a non-empty object"
        )

    result: Dict[str, Set[str]] = {}
    for raw_perm_name, role_names in permissions_block.items():
        if not isinstance(raw_perm_name, str) or not raw_perm_name.strip():
            raise PermissionConfigurationError(
                "admin_permissions contains an invalid permission name"
            )
        perm_name = raw_perm_name.strip()

        if perm_name in _SCOPED_SYNTHETIC_PERMISSIONS:
            raise PermissionConfigurationError(
                f"Synthetic scoped permission cannot be granted directly: {perm_name}"
            )
        if perm_name not in _CONFIGURABLE_PERMISSIONS:
            raise PermissionConfigurationError(
                f"Permission is outside the governed baseline: {perm_name}"
            )
        if not isinstance(role_names, list):
            raise PermissionConfigurationError(
                f"admin_permissions.{perm_name} must map to a role list"
            )

        seen_roles: Set[str] = set()
        for role_name in role_names:
            normalized_role = str(role_name).strip().lower()
            role_const = _ROLE_NAME_MAP.get(normalized_role)
            if role_const is None:
                raise PermissionConfigurationError(
                    f"admin_permissions.{perm_name} contains unknown role: {role_name!r}"
                )
            if normalized_role in seen_roles:
                raise PermissionConfigurationError(
                    f"admin_permissions.{perm_name} contains duplicate role: {normalized_role}"
                )
            seen_roles.add(normalized_role)

            if perm_name not in PERMISSION_MATRIX.get(role_const, set()):
                raise PermissionConfigurationError(
                    "Permission grant exceeds governed baseline: "
                    f"role={normalized_role} permission={perm_name}"
                )
            result.setdefault(role_const, set()).add(perm_name)

    return result


def reload_permissions_config() -> Dict[str, Set[str]]:
    load_permissions_config.cache_clear()
    return load_permissions_config()


@lru_cache(maxsize=1)
def load_roles_config() -> Dict[str, Any]:
    """Load role assignments with explicit Owner environment recovery."""
    data = _load_json_file(ROLES_CONFIG_PATH)

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
    if ROLE_OWNER in roles:
        return set(PERMISSION_MATRIX[ROLE_OWNER])

    file_matrix = load_permissions_config()
    permissions: Set[str] = set()
    for role in roles:
        permissions.update(file_matrix.get(role, set()))
    return permissions


def _evaluate_non_owner_permission(
    user_id: int,
    permission: str,
    target_affiliate_code: Optional[str] = None,
) -> bool:
    permissions = list_permissions_for_user(user_id)

    # `affiliate.view` is synthetic and always requires scoped resolution. It is
    # intentionally evaluated before generic membership checks so a direct grant
    # can never short-circuit target scope even if bad state somehow reaches here.
    if permission == "affiliate.view":
        if "affiliate.view.any" in permissions:
            return True
        if "affiliate.view.own" in permissions:
            scope = get_affiliate_scope(user_id)
            if scope is None:
                return False
            if target_affiliate_code is None:
                return True
            return target_affiliate_code in {
                scope.affiliate_code,
                scope.referral_code,
            }
        return False

    return permission in permissions


def has_permission(
    user_id: int,
    permission: str,
    target_affiliate_code: Optional[str] = None,
) -> bool:
    """Return an authorization decision; unsafe non-Owner config always denies."""
    if is_owner(user_id):
        return True

    try:
        return _evaluate_non_owner_permission(
            user_id,
            permission,
            target_affiliate_code=target_affiliate_code,
        )
    except PermissionConfigurationError:
        return False


def require_permission(
    user_id: int,
    permission: str,
    target_affiliate_code: Optional[str] = None,
) -> Tuple[bool, str]:
    if is_owner(user_id):
        return True, ""

    try:
        ok = _evaluate_non_owner_permission(
            user_id,
            permission,
            target_affiliate_code=target_affiliate_code,
        )
    except PermissionConfigurationError as exc:
        return False, f"unauthorized: permission configuration invalid: {exc}"

    if ok:
        return True, ""

    role = get_primary_role(user_id)
    return False, f"unauthorized: role={role} permission={permission}"


def debug_identity(user_id: int) -> Dict[str, Any]:
    scope = get_affiliate_scope(user_id)
    config_status = "VALID"
    config_error: Optional[str] = None
    try:
        # Validate permission authority even for Owner so recovery diagnostics can
        # surface the blocked non-Owner state while Owner access remains intact.
        load_permissions_config()
        permissions = list_permissions_for_user(user_id)
    except PermissionConfigurationError as exc:
        config_status = "BLOCKED"
        config_error = str(exc)
        permissions = (
            set(PERMISSION_MATRIX[ROLE_OWNER]) if is_owner(user_id) else set()
        )

    return {
        "user_id": user_id,
        "roles": get_user_roles(user_id),
        "primary_role": get_primary_role(user_id),
        "permissions": sorted(permissions),
        "permission_config_status": config_status,
        "permission_config_error": config_error,
        "affiliate_scope": None
        if scope is None
        else {
            "affiliate_code": scope.affiliate_code,
            "referral_code": scope.referral_code,
        },
    }
