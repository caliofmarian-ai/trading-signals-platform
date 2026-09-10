"""Primary-v3 distribution runtime boundary for R-021.

The existing ``distribution_router_v3`` contains the canonical v3 routing
mechanics but also retains migration-era writers for ``tier_publish`` and
``tier_reset``.  R-021 keeps those old mechanics importable for bounded
historical compatibility tests while ensuring the active runtime path produces
only primary v3 distribution evidence.

This module deliberately changes no route, entitlement, limit, Telegram,
feedback, deduplication, or publication semantics.  It replaces only the two
legacy event-writing hooks used by the implementation module.
"""

from __future__ import annotations

import time
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from core import distribution_router_v3 as _implementation


TIERS = _implementation.TIERS
LIMITED_TIERS = _implementation.LIMITED_TIERS
SCHEMA_VERSION = _implementation.SCHEMA_VERSION
legacy = _implementation.legacy
observability_logger = _implementation.observability_logger


def _discard_legacy_publish_adapter(**_: Any) -> None:
    """Bounded migration hook: current primary runtime never writes tier_publish."""

    return None


def _primary_maybe_daily_reset(
    state: Dict[str, Any], cfg: Dict[str, Any], now_ts: int
) -> tuple[Dict[str, Any], bool]:
    """Perform the existing v3 reset while emitting primary route events only."""

    reset_cfg = cfg.get("reset") or {}
    timezone_name = str(reset_cfg.get("timezone") or legacy.DEFAULT_RESET_TZ)
    try:
        reset_tz = ZoneInfo(timezone_name)
    except Exception:
        reset_tz = ZoneInfo(legacy.DEFAULT_RESET_TZ)
    hour = int(reset_cfg.get("hour", 8))
    minute = int(reset_cfg.get("minute", 10))
    now_local = datetime.fromtimestamp(int(now_ts), tz=reset_tz)
    today = now_local.date().isoformat()

    if (now_local.hour, now_local.minute) < (hour, minute):
        return state, False
    if state.get("last_reset_london_date") == today:
        return state, False

    before = deepcopy(state)
    state["last_reset_london_date"] = today
    state["open_signals_today"] = {tier: 0 for tier in TIERS}
    for tier in TIERS:
        state["tier_state"][tier] = (
            "ACTIVE"
            if _implementation._route_is_configured(cfg, tier)
            else "DISABLED"
        )
    legacy.save_state(state)

    for tier in TIERS:
        prior = str(before.get("tier_state", {}).get(tier) or "ACTIVE")
        after = str(state["tier_state"].get(tier) or "ACTIVE")
        _implementation._log_event(
            "route_reset",
            {
                "route": tier,
                "reason": f"DAILY_RESET_{hour:02d}:{minute:02d}_{reset_tz.key}",
                "before": {
                    "state": prior,
                    "counter": int(
                        before.get("open_signals_today", {}).get(tier, 0)
                    ),
                },
                "after": {"state": after, "counter": 0},
            },
            source_function="_primary_maybe_daily_reset",
        )
        _implementation._log_route_state_change(
            tier, prior, after, "DAILY_RESET"
        )

    return state, True


# Patch only the migration-era write hooks used by the implementation module.
# Python resolves these globals when route() executes, so the routing mechanics
# remain exactly the existing v3 implementation while legacy writes are bounded
# out of the active primary runtime.
_implementation._legacy_publish_adapter = _discard_legacy_publish_adapter
_implementation._maybe_daily_reset = _primary_maybe_daily_reset


def route(event: Dict[str, Any], now_ts: Optional[int] = None) -> Dict[str, Any]:
    """Route through the existing v3 mechanics with primary-only event writes."""

    return _implementation.route(event, now_ts=now_ts)


def reset_daily_counters(now_ts: Optional[int] = None) -> bool:
    """Run the governed daily reset through the primary-v3 evidence path."""

    effective_now = int(now_ts or time.time())
    cfg = _implementation._load_effective_config()
    state = legacy.load_state()
    state = _implementation._sync_config_states(state, cfg)
    _, changed = _primary_maybe_daily_reset(state, cfg, effective_now)
    return changed


def __getattr__(name: str) -> Any:
    """Delegate read-only/helper compatibility to the underlying v3 module."""

    return getattr(_implementation, name)
