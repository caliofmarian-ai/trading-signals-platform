"""Canonical internal strategy time model.

This module estimates time from observed price speed and established structural
evidence.  It does not create trader-facing expiry, telemetry schedules, scores,
signals, FSM transitions, or execution instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from typing import Any, Mapping

from .decision_object import TimeContext
from .market_model import MarketModelResult
from .sr_corridor_engine import CorridorResult


SCHEMA_VERSION = "1.0.0"


class TimeModelUnavailable(ValueError):
    """Raised when time configuration is invalid or incomplete."""


@dataclass(frozen=True)
class TimeModelEvidence:
    buffer_distance: float
    price_speed: float
    trend_adjustment: float
    structure_adjustment: float
    expiry_minimum: float
    expiry_maximum: float
    corridor_width: float | None
    available_distance: float | None


@dataclass(frozen=True)
class TimeModelResult:
    schema_version: str
    symbol: str
    evaluated_ts: int
    context: TimeContext
    temporally_feasible: bool
    explanation: str
    evidence: TimeModelEvidence


def _required_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TimeModelUnavailable(f"{name} configuration is required")
    return value


def _required_positive(mapping: Mapping[str, Any], key: str, name: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool):
        raise TimeModelUnavailable(f"{name}.{key} configuration is required")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TimeModelUnavailable(f"{name}.{key} configuration is required") from exc
    if not isfinite(number) or number <= 0:
        raise TimeModelUnavailable(f"{name}.{key} must be finite and positive")
    return number


def _unavailable(
    market: MarketModelResult,
    corridor: CorridorResult,
    *,
    explanation: str,
    trend_adjustment: float,
    structure_adjustment: float,
    expiry_minimum: float,
    expiry_maximum: float,
) -> TimeModelResult:
    return TimeModelResult(
        schema_version=SCHEMA_VERSION,
        symbol=market.symbol,
        evaluated_ts=market.evaluated_ts,
        context=TimeContext(
            t_needed=None,
            t_needed_adjusted=None,
            model_expiry=None,
            model_time_reach_ratio=None,
            corridor_time_pressure=None,
            time_state="UNAVAILABLE",
        ),
        temporally_feasible=False,
        explanation=explanation,
        evidence=TimeModelEvidence(
            buffer_distance=market.context.buffer_distance,
            price_speed=market.context.price_speed,
            trend_adjustment=trend_adjustment,
            structure_adjustment=structure_adjustment,
            expiry_minimum=expiry_minimum,
            expiry_maximum=expiry_maximum,
            corridor_width=corridor.structure.corridor_width,
            available_distance=corridor.structure.available_distance,
        ),
    )


def evaluate_time(
    market: MarketModelResult,
    corridor: CorridorResult,
    params: Mapping[str, Any],
) -> TimeModelResult:
    """Calculate canonical Model Time from upstream market and corridor truth."""

    if market.symbol != corridor.symbol or market.evaluated_ts != corridor.evaluated_ts:
        raise TimeModelUnavailable("market and corridor evidence do not describe the same evaluation")

    trend_adjustments = _required_mapping(params.get("trend_time_adjust"), "trend_time_adjust")
    trend_adjustment = _required_positive(
        trend_adjustments, market.context.trend_context, "trend_time_adjust"
    )
    structure_config = _required_mapping(params.get("structure_factor"), "structure_factor")
    structure_adjustment = _required_positive(structure_config, "mult", "structure_factor")
    expiry_limits = _required_mapping(params.get("expiry_limits_minutes"), "expiry_limits_minutes")
    expiry_minimum = _required_positive(expiry_limits, "min", "expiry_limits_minutes")
    expiry_maximum = _required_positive(expiry_limits, "max", "expiry_limits_minutes")
    if expiry_maximum < expiry_minimum:
        raise TimeModelUnavailable("expiry_limits_minutes.max must be at least min")

    if corridor.structure.feasibility_state != "VALID":
        return _unavailable(
            market,
            corridor,
            explanation="Model Time is blocked because complete and feasible corridor evidence is unavailable.",
            trend_adjustment=trend_adjustment,
            structure_adjustment=structure_adjustment,
            expiry_minimum=expiry_minimum,
            expiry_maximum=expiry_maximum,
        )

    price_speed = market.context.price_speed
    buffer_distance = market.context.buffer_distance
    if price_speed <= 0 or buffer_distance <= 0 or not all(isfinite(x) for x in (price_speed, buffer_distance)):
        return _unavailable(
            market,
            corridor,
            explanation="Model Time cannot be established without positive observed speed and buffer distance.",
            trend_adjustment=trend_adjustment,
            structure_adjustment=structure_adjustment,
            expiry_minimum=expiry_minimum,
            expiry_maximum=expiry_maximum,
        )

    t_needed = buffer_distance / price_speed
    t_needed_adjusted = t_needed * trend_adjustment * structure_adjustment
    model_expiry = float(ceil(min(max(t_needed_adjusted, expiry_minimum), expiry_maximum)))
    model_time_reach_ratio = t_needed_adjusted / model_expiry
    temporally_feasible = t_needed_adjusted <= model_expiry
    time_state = "READY" if temporally_feasible else "LATE"

    context = TimeContext(
        t_needed=t_needed,
        t_needed_adjusted=t_needed_adjusted,
        model_expiry=model_expiry,
        model_time_reach_ratio=model_time_reach_ratio,
        # The active canon requires corridor geometry in this metric but does
        # not define a calibrated formula.  None prevents invented precision.
        corridor_time_pressure=None,
        time_state=time_state,
    )
    explanation = (
        "The adjusted observed travel time fits inside the internal model window."
        if temporally_feasible
        else "The adjusted observed travel time exceeds the maximum internal model window."
    )
    return TimeModelResult(
        schema_version=SCHEMA_VERSION,
        symbol=market.symbol,
        evaluated_ts=market.evaluated_ts,
        context=context,
        temporally_feasible=temporally_feasible,
        explanation=explanation,
        evidence=TimeModelEvidence(
            buffer_distance=buffer_distance,
            price_speed=price_speed,
            trend_adjustment=trend_adjustment,
            structure_adjustment=structure_adjustment,
            expiry_minimum=expiry_minimum,
            expiry_maximum=expiry_maximum,
            corridor_width=corridor.structure.corridor_width,
            available_distance=corridor.structure.available_distance,
        ),
    )
