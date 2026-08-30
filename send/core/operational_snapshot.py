"""Evidence-backed operational status projection for human-facing surfaces.

The projection consumes runtime state, effective configuration, and persisted FSM
state. Missing evidence stays explicit. No UI caller should invent operational
values or maintain its own fallback state model.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping, Optional

from core import fsm_runtime
from runtime import runtime_status


UNKNOWN_NOT_REPORTED = "UNKNOWN (not reported)"


def optional_bool(value: Any) -> Optional[bool]:
    """Interpret explicit boolean evidence without inventing a default."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "enabled"}:
            return True
        if normalized in {"0", "false", "no", "off", "disabled"}:
            return False
    return None


def env_flag_observation(name: str) -> Optional[bool]:
    """Return configured evidence, or None when the variable is absent/invalid."""
    raw = os.getenv(name)
    return None if raw is None else optional_bool(raw)


def status_flag_observation(
    status: Mapping[str, Any],
    key: str,
    *,
    env_name: Optional[str] = None,
) -> Optional[bool]:
    if key in status:
        return optional_bool(status.get(key))
    return env_flag_observation(env_name) if env_name else None


def read_runtime_evidence() -> Dict[str, Any]:
    """Return the reported runtime mapping, or an empty mapping on unavailable evidence."""
    try:
        observed = runtime_status.read_status()
    except Exception:
        return {}
    return dict(observed) if isinstance(observed, dict) else {}


def observed_shadow_mode(
    status: Optional[Mapping[str, Any]] = None,
) -> Optional[bool]:
    """Read shadow mode from runtime evidence, then explicit configuration."""
    evidence = dict(status) if isinstance(status, Mapping) else read_runtime_evidence()
    return status_flag_observation(
        evidence,
        "shadow_mode",
        env_name="SHADOW_MODE",
    )


def _reported_upper(status: Mapping[str, Any], key: str) -> str:
    raw = status.get(key)
    if raw is None or not str(raw).strip():
        return UNKNOWN_NOT_REPORTED
    return str(raw).strip().upper()


def _reported_text(status: Mapping[str, Any], key: str, absent: str) -> str:
    raw = status.get(key)
    if raw is None or not str(raw).strip():
        return absent
    return str(raw).strip()


def _fsm_projection() -> str:
    try:
        state = fsm_runtime.load_state()
    except Exception:
        return "UNAVAILABLE (state not readable)"
    if not isinstance(state, dict):
        return "UNAVAILABLE (state payload invalid)"

    watchlist = state.get("watchlist")
    watchlist_count: object = (
        len(watchlist) if isinstance(watchlist, list) else "not reported"
    )
    raw_mode = state.get("mode")
    mode = (
        str(raw_mode).strip()
        if raw_mode is not None and str(raw_mode).strip()
        else UNKNOWN_NOT_REPORTED
    )
    return f"{mode} watchlist={watchlist_count}"


def build_status_snapshot(
    status: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one truthful status snapshot shared by every Telegram status surface."""
    evidence = dict(status) if isinstance(status, Mapping) else read_runtime_evidence()

    runtime_phase = _reported_upper(evidence, "phase")
    market_data_state = _reported_upper(evidence, "market_data_state")

    recovery_required = (
        optional_bool(evidence.get("recovery_required"))
        if "recovery_required" in evidence
        else None
    )
    raw_recovery_state = evidence.get("recovery_state")
    if raw_recovery_state is not None and str(raw_recovery_state).strip():
        recovery_state = str(raw_recovery_state).strip().upper()
    elif recovery_required is True:
        recovery_state = (
            "DEGRADED_SAFE (derived from reported recovery requirement)"
        )
    elif recovery_required is False:
        recovery_state = "NO RECOVERY REQUIRED (reported)"
    else:
        recovery_state = UNKNOWN_NOT_REPORTED

    telegram_enabled = status_flag_observation(
        evidence,
        "telegram_enabled",
        env_name="ENABLE_TELEGRAM",
    )
    telegram_polling_started = (
        optional_bool(evidence.get("telegram_polling_started"))
        if "telegram_polling_started" in evidence
        else None
    )
    if telegram_enabled is False:
        telegram_state = "DISABLED (reported/configured)"
    elif telegram_enabled is True and telegram_polling_started is True:
        telegram_state = "ENABLED (polling started)"
    elif telegram_enabled is True and telegram_polling_started is False:
        telegram_state = "ENABLED (polling not started)"
    elif telegram_enabled is True:
        telegram_state = "ENABLED (polling state not reported)"
    else:
        telegram_state = UNKNOWN_NOT_REPORTED

    raw_broker_state = evidence.get("broker_state")
    if raw_broker_state is not None and str(raw_broker_state).strip():
        broker_state = str(raw_broker_state).strip().upper()
    else:
        broker_enabled = status_flag_observation(
            evidence,
            "broker_execution_enabled",
            env_name="ENABLE_BROKER_EXECUTION",
        )
        if broker_enabled is False:
            broker_state = "DISABLED (configured)"
        elif broker_enabled is True:
            broker_state = (
                "ENABLED BY CONFIG; RUNTIME AVAILABILITY NOT REPORTED"
            )
        else:
            # Broker execution is fail-closed when configuration is absent.
            broker_state = (
                "DISABLED (effective fail-closed default; configuration absent)"
            )

    raw_overall_state = evidence.get("overall_state")
    if raw_overall_state is not None and str(raw_overall_state).strip():
        overall_state = str(raw_overall_state).strip().upper()
    elif runtime_phase == "BLOCKED":
        overall_state = "BLOCKED (derived from runtime phase)"
    elif market_data_state == "MARKET_DATA_LIMITED":
        overall_state = (
            "MARKET_DATA_LIMITED (derived from market-data state)"
        )
    elif runtime_phase == "RUNNING" and recovery_required is False:
        overall_state = "READY (derived from reported runtime evidence)"
    else:
        overall_state = "UNKNOWN (insufficient evidence)"

    shadow_observation = observed_shadow_mode(evidence)
    if shadow_observation is True:
        shadow_state = "ON"
    elif shadow_observation is False:
        shadow_state = "OFF"
    else:
        shadow_state = UNKNOWN_NOT_REPORTED

    return {
        "overall_state": overall_state,
        "runtime_phase": runtime_phase,
        "runtime_message": _reported_text(
            evidence,
            "message",
            "No runtime message reported.",
        ),
        "recovery_state": recovery_state,
        "market_data_state": market_data_state,
        "market_data_note": _reported_text(evidence, "market_data_note", ""),
        "telegram_state": telegram_state,
        "fsm_state": _fsm_projection(),
        "shadow_mode": shadow_state,
        "broker_state": broker_state,
    }
