from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
SEND_ROOT = REPO_ROOT / "send"

CONFIG_SEED_FILES = (
    "active_symbols.json",
    "admin_permissions.json",
    "admin_roles.json",
    "admin_settings.json",
    "algo_params.json",
    "channel_config.json",
    "intelligence_settings.json",
    "symbols.json",
)


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def resolve_base_dir(*, require_explicit: bool = True) -> Path:
    raw = os.getenv("BINARYBOT_BASE_DIR", "").strip()
    if not raw:
        if require_explicit:
            raise ValueError(
                "BINARYBOT_BASE_DIR must be set to an absolute Railway volume path"
            )
        return SEND_ROOT

    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        raise ValueError(f"BINARYBOT_BASE_DIR must be absolute: {raw}")
    return candidate


def runtime_paths(base_dir: Path) -> Dict[str, Path]:
    config_dir = base_dir / "config"
    state_dir = base_dir / "state"
    outcomes_dir = base_dir / "outcomes"
    observability_dir = base_dir / "observability"
    analytics_dir = base_dir / "analytics"
    snapshots_dir = base_dir / "snapshots"
    return {
        "base": base_dir,
        "config": config_dir,
        "state": state_dir,
        "outcomes": outcomes_dir,
        "observability": observability_dir,
        "analytics": analytics_dir,
        "snapshots": snapshots_dir,
        "admin_events_log": observability_dir / "admin_events.jsonl",
        "outcomes_log": outcomes_dir / "outcomes.jsonl",
        "engine_events_log": observability_dir / "engine_events.jsonl",
        "fsm_events_log": observability_dir / "fsm_events.jsonl",
        "dist_events_log": observability_dir / "distribution_events.jsonl",
        "admin_proofs_log": observability_dir / "admin_proofs.jsonl",
        "error_events_log": observability_dir / "error_events.jsonl",
        "algo_params": config_dir / "algo_params.json",
        "admin_roles": config_dir / "admin_roles.json",
        "admin_permissions": config_dir / "admin_permissions.json",
        "strategy_auditor_settings": config_dir / "intelligence_settings.json",
    }


def apply_path_contract(base_dir: Path | None = None) -> Dict[str, str]:
    base_dir = base_dir or resolve_base_dir(require_explicit=True)
    paths = runtime_paths(base_dir)
    defaults = {
        "BINARYBOT_BASE_DIR": str(paths["base"]),
        "OBS_DIR": str(paths["observability"]),
        "ADMIN_EVENTS_LOG": str(paths["admin_events_log"]),
        "OUTCOMES_LOG": str(paths["outcomes_log"]),
        "ANALYTICS_DIR": str(paths["analytics"]),
        "DIST_EVENTS_LOG": str(paths["dist_events_log"]),
        "FSM_EVENTS_LOG": str(paths["fsm_events_log"]),
        "ENGINE_EVENTS_LOG": str(paths["engine_events_log"]),
        "ADMIN_PROOFS_LOG": str(paths["admin_proofs_log"]),
        "ERROR_EVENTS_LOG": str(paths["error_events_log"]),
        "ALGO_PARAMS_PATH": str(paths["algo_params"]),
        "ADMIN_ROLES_CONFIG": str(paths["admin_roles"]),
        "ADMIN_PERMISSIONS_CONFIG": str(paths["admin_permissions"]),
        "STRATEGY_AUDITOR_SETTINGS": str(paths["strategy_auditor_settings"]),
    }
    effective: Dict[str, str] = {}
    for key, value in defaults.items():
        resolved = os.getenv(key, "").strip() or value
        os.environ[key] = resolved
        effective[key] = resolved
    return effective


def shadow_mode_enabled() -> bool:
    return env_flag("SHADOW_MODE", default=False)


def broker_execution_enabled() -> bool:
    return env_flag("ENABLE_BROKER_EXECUTION", default=False)


def telegram_enabled() -> bool:
    return env_flag("ENABLE_TELEGRAM", default=False)
