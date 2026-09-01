"""Deterministic Trade Physics submodel for Binary Strategy V2.

The module consumes synchronized Market, Corridor and Time evidence and computes
the canonical physical-feasibility components S/T/P/V plus deterministic TPS.
It does not own lifecycle thresholds, FSM transitions, signal execution,
distribution, learned probability, or broker execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional

from .decision_object import TradePhysicsContext
from .market_model import MarketModelResult
from .sr_corridor_engine import CorridorResult
from .time_model import TimeModelResult


SCHEMA_VERSION = "1.0.0"
FORMULA_VERSION = "TRADE_PHYSICS_MODEL_SPEC_v1.0.0"
WEIGHTS_VERSION = "1.0.0"
WEIGHT_SPACE = 0.35
WEIGHT_TIME = 0.25
WEIGHT_SPEED = 0.20
WEIGHT_VOLATILITY = 0.20
SPACE_CAP = 3.0
TIME_CAP = 2.0
SPEED_CAP = 2.0
ATR_REFERENCE_MINUTES = 5.0


@dataclass(frozen=True)
class TradePhysicsResult:
    schema_version: str
    symbol: str
    evaluated_ts: int
    readiness_state: str
    available_space: Optional[float]
    required_space: Optional[float]
    space_to_buffer_ratio: Optional[float]
    trade_space_margin_atr: Optional[float]
    time_to_buffer_ratio: Optional[float]
    directional_effective_speed: Optional[float]
    weighted_gross_speed: Optional[float]
    flow_efficiency: Optional[float]
    atr_speed_reference: Optional[float]
    directional_speed_ratio: Optional[float]
    movement_stress: Optional[float]
    S: Optional[float]
    T: Optional[float]
    P: Optional[float]
    V: Optional[float]
    TPS: Optional[float]
    interpretation_band: Optional[str]
    formula_version: str
    weights_version: str
    explanation: str

    @property
    def ready(self) -> bool:
        return self.readiness_state == "READY"

    @property
    def physically_constrained(self) -> bool:
        return (
            self.available_space is not None
            and self.required_space is not None
            and self.available_space < self.required_space
        )

    def to_context(self) -> TradePhysicsContext:
        return TradePhysicsContext(
            readiness_state=self.readiness_state,
            available_space=self.available_space,
            required_space=self.required_space,
            space_to_buffer_ratio=self.space_to_buffer_ratio,
            trade_space_margin_atr=self.trade_space_margin_atr,
            time_to_buffer_ratio=self.time_to_buffer_ratio,
            directional_effective_speed=self.directional_effective_speed,
            weighted_gross_speed=self.weighted_gross_speed,
            flow_efficiency=self.flow_efficiency,
            atr_speed_reference=self.atr_speed_reference,
            directional_speed_ratio=self.directional_speed_ratio,
            movement_stress=self.movement_stress,
            S=self.S,
            T=self.T,
            P=self.P,
            V=self.V,
            TPS=self.TPS,
            interpretation_band=self.interpretation_band,
            formula_version=self.formula_version,
            feature_schema_version=self.schema_version,
            explanation=self.explanation,
        )


def _clamp(value: float, lower: float, upper: float) -> float:
    return lower if value < lower else upper if value > upper else value


def _band(tps: float) -> str:
    if tps < 30:
        return "PHYSICALLY_WEAK"
    if tps < 50:
        return "WEAK"
    if tps < 65:
        return "MODERATE"
    if tps < 80:
        return "STRONG"
    return "EXCELLENT"


def _unavailable(
    market: MarketModelResult,
    state: str,
    explanation: str,
    *,
    available_space: Optional[float] = None,
    required_space: Optional[float] = None,
    time_to_buffer_ratio: Optional[float] = None,
) -> TradePhysicsResult:
    return TradePhysicsResult(
        schema_version=SCHEMA_VERSION,
        symbol=market.symbol,
        evaluated_ts=market.evaluated_ts,
        readiness_state=state,
        available_space=available_space,
        required_space=required_space,
        space_to_buffer_ratio=None,
        trade_space_margin_atr=None,
        time_to_buffer_ratio=time_to_buffer_ratio,
        directional_effective_speed=market.context.directional_effective_speed,
        weighted_gross_speed=market.context.weighted_gross_speed,
        flow_efficiency=market.context.flow_efficiency,
        atr_speed_reference=None,
        directional_speed_ratio=None,
        movement_stress=None,
        S=None,
        T=None,
        P=None,
        V=None,
        TPS=None,
        interpretation_band=None,
        formula_version=FORMULA_VERSION,
        weights_version=WEIGHTS_VERSION,
        explanation=explanation,
    )


def evaluate_trade_physics(
    market: MarketModelResult,
    corridor: CorridorResult,
    time: TimeModelResult,
) -> TradePhysicsResult:
    """Compute deterministic TPS from canonical synchronized upstream evidence."""

    identities = {
        (market.symbol, market.evaluated_ts),
        (corridor.symbol, corridor.evaluated_ts),
        (time.symbol, time.evaluated_ts),
    }
    if len(identities) != 1 or corridor.direction != market.direction_bias:
        return _unavailable(
            market,
            "INVALID_EVIDENCE",
            "Trade Physics evidence is not synchronized to one symbol, direction and evaluation.",
        )

    required_space = market.context.buffer_distance
    available_space = corridor.structure.available_distance
    if available_space is None or not isfinite(available_space) or available_space < 0:
        return _unavailable(
            market,
            "UNAVAILABLE_MISSING_STRUCTURE",
            "Directional structural space is unavailable.",
            required_space=required_space,
        )

    if market.context.noise_context != "STABLE":
        return _unavailable(
            market,
            "BLOCKED_UNSTABLE_MARKET",
            "Trade Physics is blocked because synchronized market evidence is unstable.",
            available_space=available_space,
            required_space=required_space,
            time_to_buffer_ratio=time.context.time_to_buffer_ratio,
        )

    atr_m5 = market.evidence.atr_m5
    if not isfinite(atr_m5) or atr_m5 <= 0:
        return _unavailable(
            market,
            "UNAVAILABLE_MISSING_ATR",
            "Positive M5 ATR evidence is required for Trade Physics.",
            available_space=available_space,
            required_space=required_space,
            time_to_buffer_ratio=time.context.time_to_buffer_ratio,
        )

    directional_speed = market.context.directional_effective_speed
    weighted_gross_speed = market.context.weighted_gross_speed
    flow_efficiency = market.context.flow_efficiency
    if (
        directional_speed is None
        or not isfinite(directional_speed)
        or directional_speed <= 0
        or weighted_gross_speed is None
        or not isfinite(weighted_gross_speed)
        or weighted_gross_speed <= 0
        or flow_efficiency is None
        or not isfinite(flow_efficiency)
    ):
        return _unavailable(
            market,
            "UNAVAILABLE_MISSING_SPEED",
            "Canonical directional effective speed and flow evidence are required for Trade Physics.",
            available_space=available_space,
            required_space=required_space,
            time_to_buffer_ratio=time.context.time_to_buffer_ratio,
        )

    time_to_buffer_ratio = time.context.time_to_buffer_ratio
    if time_to_buffer_ratio is None:
        if (
            time.context.model_expiry is not None
            and time.context.t_needed_adjusted is not None
            and time.context.model_expiry > 0
            and time.context.t_needed_adjusted > 0
        ):
            time_to_buffer_ratio = time.context.model_expiry / time.context.t_needed_adjusted
        else:
            return _unavailable(
                market,
                "UNAVAILABLE_MISSING_TIME",
                "Canonical model time evidence is unavailable for Trade Physics.",
                available_space=available_space,
                required_space=required_space,
            )
    if not isfinite(time_to_buffer_ratio) or time_to_buffer_ratio <= 0:
        return _unavailable(
            market,
            "UNAVAILABLE_MISSING_TIME",
            "Trade Physics time-to-buffer ratio must be finite and positive.",
            available_space=available_space,
            required_space=required_space,
        )

    if required_space <= 0 or not isfinite(required_space):
        return _unavailable(
            market,
            "INVALID_EVIDENCE",
            "Canonical buffer distance must be finite and positive.",
            available_space=available_space,
        )

    space_to_buffer_ratio = available_space / required_space
    trade_space_margin_atr = (available_space - required_space) / atr_m5
    atr_speed_reference = atr_m5 / ATR_REFERENCE_MINUTES
    directional_speed_ratio = directional_speed / atr_speed_reference
    movement_stress = required_space / atr_m5

    S = _clamp(space_to_buffer_ratio, 0.0, SPACE_CAP) / SPACE_CAP
    T = _clamp(time_to_buffer_ratio, 0.0, TIME_CAP) / TIME_CAP
    P = _clamp(directional_speed_ratio, 0.0, SPEED_CAP) / SPEED_CAP
    V = 1.0 / (1.0 + movement_stress)
    tps_raw = (
        WEIGHT_SPACE * S
        + WEIGHT_TIME * T
        + WEIGHT_SPEED * P
        + WEIGHT_VOLATILITY * V
    )
    tps = 100.0 * _clamp(tps_raw, 0.0, 1.0)
    interpretation_band = _band(tps)

    constraint_note = (
        " Structural space is physically constrained and remains a hard blocker."
        if available_space < required_space
        else " Structural space is sufficient for the canonical required move."
    )
    return TradePhysicsResult(
        schema_version=SCHEMA_VERSION,
        symbol=market.symbol,
        evaluated_ts=market.evaluated_ts,
        readiness_state="READY",
        available_space=available_space,
        required_space=required_space,
        space_to_buffer_ratio=space_to_buffer_ratio,
        trade_space_margin_atr=trade_space_margin_atr,
        time_to_buffer_ratio=time_to_buffer_ratio,
        directional_effective_speed=directional_speed,
        weighted_gross_speed=weighted_gross_speed,
        flow_efficiency=flow_efficiency,
        atr_speed_reference=atr_speed_reference,
        directional_speed_ratio=directional_speed_ratio,
        movement_stress=movement_stress,
        S=S,
        T=T,
        P=P,
        V=V,
        TPS=tps,
        interpretation_band=interpretation_band,
        formula_version=FORMULA_VERSION,
        weights_version=WEIGHTS_VERSION,
        explanation=(
            f"Deterministic Trade Physics is READY with TPS band {interpretation_band}."
            + constraint_note
        ),
    )
