"""Shared fail-closed startup validation for production runtime workers.

This module performs deterministic, offline validation only. It proves that
critical governed configuration and persisted runtime state are safe enough to
start the strategy/distribution workers; it does not contact market providers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

from core import admin_permissions
from core import distribution_router
from core import market_data_provider_control
from core import runtime_param_gate
from core import storage
from state_store import state_store as runtime_state_store


class StartupPreflightError(RuntimeError):
    """Raised when critical startup state is unsafe for live workers."""


_ROLE_LIST_FIELDS = (
    "owner",
    "primary_admin",
    "strategy_admin",
    "research_admin",
    "analyst",
    "moderator",
)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_json_object(path: str, *, label: str) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_file():
        raise StartupPreflightError(f"Required {label} file is missing: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StartupPreflightError(f"{label} is invalid JSON: {file_path}: {exc.msg}") from exc
    except OSError as exc:
        raise StartupPreflightError(f"Unable to read {label}: {file_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise StartupPreflightError(f"{label} must be a JSON object: {file_path}")
    return payload


def _configured_symbols(payload: Dict[str, Any]) -> Tuple[str, ...]:
    raw: list[Any] = []
    if isinstance(payload.get("symbols"), list):
        raw.extend(payload["symbols"])
    else:
        for key in ("forex", "crypto"):
            value = payload.get(key)
            if isinstance(value, list):
                raw.extend(value)

    normalized: list[str] = []
    for item in raw:
        value = str(item).strip().upper().replace("_", "/")
        if value and value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _validate_provider_state_file() -> Dict[str, Any] | None:
    path = storage.config_path(market_data_provider_control.STATE_FILENAME)
    if not os.path.exists(path):
        return None

    state = _load_json_object(path, label="market_data_provider")
    provider = str(state.get("active_provider") or "").strip().upper()
    if provider not in market_data_provider_control.SUPPORTED_PROVIDERS:
        raise StartupPreflightError(
            f"Persisted market provider is unsupported or missing: {provider or '<empty>'}"
        )
    mode = str(state.get("mode") or "").strip().upper()
    if mode != "EXCLUSIVE":
        raise StartupPreflightError(
            f"Persisted market provider mode must be EXCLUSIVE, got {mode or '<empty>'}"
        )
    return state


def _validate_provider(active_symbols: Tuple[str, ...]) -> Dict[str, Any]:
    persisted = _validate_provider_state_file()
    try:
        provider = market_data_provider_control.get_active_provider()
        ready, reason = market_data_provider_control.provider_ready(provider)
    except Exception as exc:
        raise StartupPreflightError(f"Market provider selection is invalid: {exc}") from exc

    if not ready:
        raise StartupPreflightError(
            f"Active market provider {provider} is not configured: {reason}"
        )

    if provider == market_data_provider_control.PROVIDER_FINNHUB:
        required = set(market_data_provider_control.FINNHUB_EFFECTIVE_SYMBOLS)
        effective = tuple(symbol for symbol in active_symbols if symbol in required)
        if not effective:
            raise StartupPreflightError(
                "FINNHUB startup requires EUR/USD in the active symbol universe"
            )
    else:
        effective = active_symbols

    if not effective:
        raise StartupPreflightError("Active market symbol universe is empty")

    return {
        "active_provider": provider,
        "selection_source": market_data_provider_control.selection_source(),
        "persisted_selection": persisted is not None,
        "mode": "EXCLUSIVE",
        "effective_symbols": list(effective),
    }


def _validate_admin_control_config() -> Dict[str, int]:
    roles_path = storage.config_path("admin_roles.json")
    permissions_path = storage.config_path("admin_permissions.json")
    roles = _load_json_object(roles_path, label="admin_roles")
    permissions = _load_json_object(permissions_path, label="admin_permissions")

    for field in _ROLE_LIST_FIELDS:
        if field not in roles:
            raise StartupPreflightError(f"admin_roles missing required role field: {field}")
        if not isinstance(roles[field], list):
            raise StartupPreflightError(f"admin_roles.{field} must be a list")

    if "affiliate_admin" not in roles or not isinstance(roles["affiliate_admin"], dict):
        raise StartupPreflightError("admin_roles.affiliate_admin must be an object")

    permissions_block = permissions.get("permissions")
    if not isinstance(permissions_block, dict) or not permissions_block:
        raise StartupPreflightError("admin_permissions.permissions must be a non-empty object")

    recognized_roles = set(getattr(admin_permissions, "_ROLE_NAME_MAP", {}).keys())
    if not recognized_roles:
        raise StartupPreflightError("Admin permission role registry is unavailable")

    for permission_name, role_names in permissions_block.items():
        if not isinstance(permission_name, str) or not permission_name.strip():
            raise StartupPreflightError("admin_permissions contains an invalid permission name")
        if not isinstance(role_names, list):
            raise StartupPreflightError(
                f"admin_permissions.{permission_name} must map to a role list"
            )
        unknown_roles = [
            str(role_name)
            for role_name in role_names
            if str(role_name).strip().lower() not in recognized_roles
        ]
        if unknown_roles:
            raise StartupPreflightError(
                f"admin_permissions.{permission_name} contains unknown roles: {unknown_roles}"
            )

    try:
        admin_permissions.reload_roles_config()
        admin_permissions.reload_permissions_config()
    except Exception as exc:
        raise StartupPreflightError(f"Admin permission configuration failed to load: {exc}") from exc

    return {
        "role_fields": len(_ROLE_LIST_FIELDS) + 1,
        "permission_count": len(permissions_block),
    }


def _validate_distribution_config() -> None:
    _load_json_object(storage.config_path("channel_config.json"), label="channel_config")
    try:
        config = distribution_router.load_config()
    except Exception as exc:
        raise StartupPreflightError(f"Distribution configuration failed to load: {exc}") from exc
    if not isinstance(config, dict):
        raise StartupPreflightError("Distribution configuration did not resolve to an object")


def _validate_runtime_state() -> Dict[str, Any]:
    try:
        settings = runtime_state_store.load_settings()
        fsm_state = runtime_state_store.load_fsm_state()
        dist_state = runtime_state_store.load_dist_state()
        restart_state = runtime_state_store.load_restart_guard_state()
    except Exception as exc:
        raise StartupPreflightError(f"Persisted runtime state validation failed: {exc}") from exc

    return {
        "settings": settings,
        "fsm_state": fsm_state,
        "dist_state": dist_state,
        "restart_state": restart_state,
    }


def run_startup_preflight(
    *,
    require_shadow_mode: bool = False,
    require_deployment_inputs: bool | None = None,
) -> Dict[str, Any]:
    """Validate critical startup inputs without network access or live mutations.

    Governed Railway/shadow startup always validates provider readiness plus
    Admin/distribution configuration. Generic test/development boot still cannot
    bypass governed algo params, active symbols, broker safety or persisted-state
    validation. Callers can explicitly force deployment-level validation.
    """

    if require_deployment_inputs is None:
        require_deployment_inputs = bool(
            require_shadow_mode
            or _env_flag("RAILWAY_READINESS_EVALUATED", default=False)
            or _env_flag("SHADOW_MODE", default=False)
        )

    try:
        if require_shadow_mode and not _env_flag("SHADOW_MODE", default=False):
            raise StartupPreflightError(
                "SHADOW_MODE must be true for the governed Railway deployment"
            )
        if _env_flag("ENABLE_BROKER_EXECUTION", default=False):
            raise StartupPreflightError("ENABLE_BROKER_EXECUTION must remain false")
        if _env_flag("ENABLE_TELEGRAM", default=False) and not os.getenv(
            "TELEGRAM_BOT_TOKEN", ""
        ).strip():
            raise StartupPreflightError(
                "TELEGRAM_BOT_TOKEN is required when ENABLE_TELEGRAM=true"
            )

        try:
            params = runtime_param_gate.load_runtime_algo_params(
                storage.config_path("algo_params.json")
            )
        except Exception as exc:
            raise StartupPreflightError(f"Algorithm parameter validation failed: {exc}") from exc

        state = _validate_runtime_state()
        active_symbols = _configured_symbols(runtime_state_store.load_active_symbols())
        if not active_symbols:
            raise StartupPreflightError("Active market symbol universe is empty")

        provider: Dict[str, Any]
        admin_control: Dict[str, int]
        if require_deployment_inputs:
            provider = _validate_provider(active_symbols)
            admin_control = _validate_admin_control_config()
            _validate_distribution_config()
        else:
            provider = {
                "active_provider": None,
                "selection_source": "NOT_EVALUATED_NON_DEPLOYMENT",
                "mode": "NOT_EVALUATED_NON_DEPLOYMENT",
                "effective_symbols": list(active_symbols),
            }
            admin_control = {"permission_count": 0}

        return {
            "status": "ready",
            "algo_version": str(params.get("algo_version")),
            "buffer_mode": state["settings"].get("buffer_mode"),
            "active_symbol_count": len(active_symbols),
            "active_provider": provider["active_provider"],
            "provider_selection_source": provider["selection_source"],
            "provider_mode": provider["mode"],
            "effective_symbols": provider["effective_symbols"],
            "permissions_valid": bool(require_deployment_inputs),
            "permission_count": admin_control["permission_count"],
            "persistent_state_valid": True,
            "fsm_watchlist_count": len(state["fsm_state"].get("watchlist", [])),
            "distribution_state_valid": isinstance(state["dist_state"], dict),
            "restart_state_valid": isinstance(state["restart_state"], dict),
            "shadow_mode_required": bool(require_shadow_mode),
            "deployment_inputs_required": bool(require_deployment_inputs),
        }
    except StartupPreflightError:
        raise
    except Exception as exc:
        raise StartupPreflightError(f"Startup preflight failed: {exc}") from exc
