"""Evidence-backed operational status projection for human-facing surfaces.

The projection consumes runtime state, effective configuration, and persisted FSM
state. Missing evidence stays explicit. No UI caller should invent operational
values or maintain its own fallback state model.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from core import fsm_runtime
from runtime import runtime_status


UNKNOWN_NOT_REPORTED = "UNKNOWN (not reported)"
UNAVAILABLE_INVALID = "UNAVAILABLE (reported evidence invalid)"


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
    if key not in status or status.get(key) is None:
        return UNKNOWN_NOT_REPORTED
    raw = status.get(key)
    if not isinstance(raw, str):
        return UNAVAILABLE_INVALID
    value = raw.strip()
    return value.upper() if value else UNKNOWN_NOT_REPORTED


def _reported_optional_upper(
    status: Mapping[str, Any],
    key: str,
) -> Optional[str]:
    if key not in status or status.get(key) is None:
        return None
    raw = status.get(key)
    if not isinstance(raw, str):
        return UNAVAILABLE_INVALID
    value = raw.strip()
    return value.upper() if value else None


def _reported_text(status: Mapping[str, Any], key: str, absent: str) -> str:
    if key not in status or status.get(key) is None:
        return absent
    raw = status.get(key)
    if not isinstance(raw, str):
        return UNAVAILABLE_INVALID
    value = raw.strip()
    return value if value else absent


def _fsm_projection() -> str:
    state_path = Path(str(fsm_runtime.STATE_PATH))
    if not state_path.is_file():
        return "UNAVAILABLE (persisted FSM state absent)"
    try:
        raw_text = state_path.read_text(encoding="utf-8")
        raw_state = json.loads(raw_text)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "UNAVAILABLE (persisted FSM state invalid or unreadable)"
    if not isinstance(raw_state, dict):
        return "UNAVAILABLE (persisted FSM state payload invalid)"
    if not isinstance(raw_state.get("mode"), str) or not str(
        raw_state.get("mode")
    ).strip():
        return "UNAVAILABLE (persisted FSM mode not reported)"
    if not isinstance(raw_state.get("watchlist"), list):
        return "UNAVAILABLE (persisted FSM watchlist not reported)"
    try:
        state = fsm_runtime.load_state()
    except Exception:
        return "UNAVAILABLE (state not readable)"
    # ``load_state`` may synthesize the canonical default when the artifact
    # disappears between the existence check and the read.  A synthesized
    # WIDE_SCAN state is not persisted operational evidence.
    if not state_path.is_file():
        return "UNAVAILABLE (persisted FSM state absent)"
    try:
        if state_path.read_text(encoding="utf-8") != raw_text:
            return "UNAVAILABLE (persisted FSM state changed during observation)"
    except (OSError, UnicodeError):
        return "UNAVAILABLE (persisted FSM state unreadable after validation)"
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
    return f"{mode} watchlist={watchlist_count} (persisted FSM state)"


def _reported_positive_seconds(status: Mapping[str, Any], key: str) -> str:
    if key not in status or status.get(key) is None:
        return UNKNOWN_NOT_REPORTED
    raw = status.get(key)
    if isinstance(raw, str) and not raw.strip():
        return UNKNOWN_NOT_REPORTED
    if isinstance(raw, bool):
        return UNAVAILABLE_INVALID
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        return UNAVAILABLE_INVALID
    if not math.isfinite(seconds) or seconds <= 0:
        return "UNAVAILABLE (reported interval invalid)"
    rendered = str(int(seconds)) if seconds.is_integer() else str(seconds)
    return f"{rendered} seconds (reported runtime evidence)"


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
    reported_recovery_state = _reported_optional_upper(evidence, "recovery_state")
    if reported_recovery_state is not None:
        recovery_state = reported_recovery_state
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

    reported_broker_state = _reported_optional_upper(evidence, "broker_state")
    if reported_broker_state is not None:
        broker_state = reported_broker_state
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

    reported_overall_state = _reported_optional_upper(evidence, "overall_state")
    if reported_overall_state is not None:
        overall_state = reported_overall_state
    elif runtime_phase == "BLOCKED":
        overall_state = "BLOCKED (derived from runtime phase)"
    elif market_data_state in {"MARKET_DATA_LIMITED", "MARKET_DATA_UNAVAILABLE"}:
        overall_state = (
            f"{market_data_state} (derived from market-data state)"
        )
    elif (
        runtime_phase == "RUNNING"
        and recovery_required is False
        and market_data_state == "READY"
    ):
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
        "engine_tick_seconds": _reported_positive_seconds(
            evidence,
            "engine_tick_seconds",
        ),
        "recovery_state": recovery_state,
        "market_data_state": market_data_state,
        "market_data_note": _reported_text(evidence, "market_data_note", ""),
        "market_data_provider": _reported_upper(evidence, "market_data_provider"),
        "market_data_symbol": _reported_upper(evidence, "market_data_symbol"),
        "market_data_age_seconds": evidence.get("market_data_age_seconds"),
        "market_data_freshness_limit_seconds": evidence.get(
            "market_data_freshness_limit_seconds"
        ),
        "telegram_state": telegram_state,
        "fsm_state": _fsm_projection(),
        "shadow_mode": shadow_state,
        "broker_state": broker_state,
    }
