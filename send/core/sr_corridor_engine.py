"""Canonical support/resistance and corridor interpretation layer.

The engine describes structural room only.  It does not calculate time,
scores, FSM states, signals, or execution instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Any, Mapping, Sequence

from .decision_object import StructureContext
from .market_model import MarketModelResult


SCHEMA_VERSION = "1.0.0"
LEGACY_STRUCTURE_LOOKBACK = 80
LEGACY_LEVEL_CLUSTER_TOLERANCE = 0.002
STRUCTURAL_PIVOT_SPAN = 2


class CorridorUnavailable(ValueError):
    """Raised when supplied structural evidence is invalid or insufficient."""


@dataclass(frozen=True)
class CorridorEvidence:
    support_levels: tuple[float, ...]
    resistance_levels: tuple[float, ...]
    distance_to_support: float | None
    distance_to_resistance: float | None
    required_distance: float
    room_ratio: float | None


@dataclass(frozen=True)
class CorridorResult:
    schema_version: str
    symbol: str
    evaluated_ts: int
    direction: str
    corridor_identity: str
    structure: StructureContext
    evidence: CorridorEvidence


def _validate_m5(candles: Sequence[Mapping[str, Any]]) -> None:
    if len(candles) < LEGACY_STRUCTURE_LOOKBACK:
        raise CorridorUnavailable(
            f"candles_m5 requires {LEGACY_STRUCTURE_LOOKBACK} real candles; received {len(candles)}"
        )
    previous_ts: int | None = None
    for index, candle in enumerate(candles[:LEGACY_STRUCTURE_LOOKBACK]):
        try:
            timestamp = int(candle["ts"])
            open_price, high, low, close = (float(candle[key]) for key in ("open", "high", "low", "close"))
        except (KeyError, TypeError, ValueError) as exc:
            raise CorridorUnavailable(f"candles_m5[{index}] is incomplete") from exc
        if timestamp <= 0 or not all(isfinite(value) for value in (open_price, high, low, close)):
            raise CorridorUnavailable(f"candles_m5[{index}] contains invalid evidence")
        if high < max(open_price, close) or low > min(open_price, close) or high < low:
            raise CorridorUnavailable(f"candles_m5[{index}] has invalid OHLC geometry")
        if previous_ts is not None and timestamp >= previous_ts:
            raise CorridorUnavailable("candles_m5 must be strictly newest-first")
        previous_ts = timestamp


def _cluster_levels(levels: Sequence[float], tolerance: float) -> tuple[float, ...]:
    clustered: list[float] = []
    for level in sorted(levels):
        if not clustered or abs(level - clustered[-1]) > tolerance:
            clustered.append(level)
    return tuple(clustered)


def _structural_levels(candles: Sequence[Mapping[str, Any]]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Return confirmed local swing levels, not every raw candle extreme.

    A raw high/low is not automatically a structural barrier.  Requiring two
    candles on both sides of a local extremum implements the canonical
    relevance rule and prevents the current candle's wick from manufacturing
    near-zero corridor room.
    """
    recent = candles[:LEGACY_STRUCTURE_LOOKBACK]
    highs = [float(candle["high"]) for candle in recent]
    lows = [float(candle["low"]) for candle in recent]
    observed_range = max(highs) - min(lows)
    tolerance = observed_range * LEGACY_LEVEL_CLUSTER_TOLERANCE if observed_range > 0 else 1e-9
    pivot_highs: list[float] = []
    pivot_lows: list[float] = []
    span = STRUCTURAL_PIVOT_SPAN
    for index in range(span, len(recent) - span):
        neighboring_highs = highs[index - span:index] + highs[index + 1:index + span + 1]
        neighboring_lows = lows[index - span:index] + lows[index + 1:index + span + 1]
        if highs[index] >= max(neighboring_highs) and any(
            highs[index] > value for value in neighboring_highs
        ):
            pivot_highs.append(highs[index])
        if lows[index] <= min(neighboring_lows) and any(
            lows[index] < value for value in neighboring_lows
        ):
            pivot_lows.append(lows[index])
    # A repeatedly tested horizontal boundary is structurally relevant even
    # when it forms a perfectly flat plateau with no single strict pivot.
    if not pivot_highs and max(highs) - min(highs) <= tolerance:
        pivot_highs.append(highs[0])
    if not pivot_lows and max(lows) - min(lows) <= tolerance:
        pivot_lows.append(lows[0])
    return _cluster_levels(pivot_lows, tolerance), _cluster_levels(pivot_highs, tolerance)


def _identity(symbol: str, support: float | None, resistance: float | None) -> str:
    lower = "UNAVAILABLE" if support is None else format(support, ".12g")
    upper = "UNAVAILABLE" if resistance is None else format(resistance, ".12g")
    return f"{symbol}:{lower}:{upper}"


def evaluate_corridor(
    candles_m5: Sequence[Mapping[str, Any]],
    market: MarketModelResult,
    params: Mapping[str, Any],
) -> CorridorResult:
    """Interpret the active corridor around the Market Model's latest price."""

    _validate_m5(candles_m5)
    if market.direction_bias not in {"BUY", "SELL"}:
        raise CorridorUnavailable("market direction must be BUY or SELL")

    # Canonical Trade Physics v1 owns required_space and defines it exactly as
    # buffer_distance.  Keep params in the public interface for pipeline
    # compatibility, but do not let the legacy sr_required_multiplier tighten
    # or relax this hard structural-feasibility gate.
    _ = params
    required_distance = float(market.context.buffer_distance)
    if not isfinite(required_distance) or required_distance <= 0:
        raise CorridorUnavailable("required structural distance cannot be established")

    price = market.context.latest_price
    support_levels, resistance_levels = _structural_levels(candles_m5)
    support_candidates = [level for level in support_levels if level < price]
    resistance_candidates = [level for level in resistance_levels if level > price]
    support = max(support_candidates) if support_candidates else None
    resistance = min(resistance_candidates) if resistance_candidates else None
    distance_to_support = price - support if support is not None else None
    distance_to_resistance = resistance - price if resistance is not None else None

    corridor_width = resistance - support if support is not None and resistance is not None else None
    available_distance = distance_to_resistance if market.direction_bias == "BUY" else distance_to_support
    room_ratio = available_distance / required_distance if available_distance is not None else None

    conflicts: list[str] = []
    if support is None:
        conflicts.append("SUPPORT_UNAVAILABLE")
    if resistance is None:
        conflicts.append("RESISTANCE_UNAVAILABLE")

    if support is None or resistance is None or available_distance is None:
        feasibility = "UNAVAILABLE"
        position = "UNBOUNDED"
        explanation = "A complete corridor cannot be established from the observed M5 structure."
    elif available_distance < required_distance and not isclose(
        available_distance, required_distance, rel_tol=1e-12, abs_tol=1e-12
    ):
        feasibility = "CONSTRAINED"
        position = "INTERIOR"
        conflicts.append("INSUFFICIENT_DIRECTIONAL_ROOM")
        if corridor_width is not None and corridor_width < required_distance:
            conflicts.append("CORRIDOR_COMPRESSED")
        boundary = "resistance" if market.direction_bias == "BUY" else "support"
        explanation = f"The setup is too close to {boundary} for the canonical required distance."
    else:
        feasibility = "VALID"
        position = "INTERIOR"
        explanation = "The observed corridor provides the canonical required structural room in the evaluated direction."

    structure = StructureContext(
        support=support,
        resistance=resistance,
        lower_boundary=support,
        upper_boundary=resistance,
        corridor_width=corridor_width,
        available_distance=available_distance,
        position=position,
        feasibility_state=feasibility,
        conflicts=tuple(conflicts),
        explanation=explanation,
    )
    return CorridorResult(
        schema_version=SCHEMA_VERSION,
        symbol=market.symbol,
        evaluated_ts=market.evaluated_ts,
        direction=market.direction_bias,
        corridor_identity=_identity(market.symbol, support, resistance),
        structure=structure,
        evidence=CorridorEvidence(
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            distance_to_support=distance_to_support,
            distance_to_resistance=distance_to_resistance,
            required_distance=required_distance,
            room_ratio=room_ratio,
        ),
    )