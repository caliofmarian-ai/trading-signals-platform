"""Validated Binary Strategy V2 engine-to-distribution candidate contract.

This module constructs an internal semantic object only after exact-stage FSM
acceptance. Model Time remains internal evidence. Trader-facing expiry fields
may come only from a governed ExecutionTimeResult; this module never rounds or
copies ``model_expiry`` into an external expiry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Dict, Mapping, Optional

from .decision_object import ACTIONABLE_DECISION_KINDS, DecisionObject
from .execution_model import ExecutionTimeResult


SIGNAL_EVENT_SCHEMA_VERSION = "3.1.0"
ALLOWED_BUFFER_MODES = frozenset({"SMALL", "MEDIUM", "LARGE"})


class SignalEventUnavailable(ValueError):
    """Raised when real V2 evidence cannot form a complete SignalEvent."""


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SignalEventUnavailable(f"{name} is required")
    return value.strip()


def _positive_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SignalEventUnavailable(f"{name} must be a number")
    result = float(value)
    if not isfinite(result) or result <= 0:
        raise SignalEventUnavailable(f"{name} must be finite and positive")
    return result


def _non_negative_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SignalEventUnavailable(f"{name} must be a number")
    result = float(value)
    if not isfinite(result) or result < 0:
        raise SignalEventUnavailable(f"{name} must be finite and non-negative")
    return result


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SignalEventUnavailable(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True)
class SignalEvent:
    event_type: str
    stage: str
    signal_id: str
    symbol: str
    timeframe: str
    direction: str
    score_total: float
    buffer_mode: str
    buffer_distance: float
    model_expiry: float
    candle_ts: int
    created_ts: int
    entry_price: float
    payload: Mapping[str, Any]
    execution_time_available: bool = False
    confirm_expiry_min_minutes: Optional[float] = None
    confirm_expiry_max_minutes: Optional[float] = None
    open_now_expiry_minutes: Optional[float] = None
    execution_calibration_source: Optional[str] = None
    schema_version: str = SIGNAL_EVENT_SCHEMA_VERSION
    distribution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.event_type != "SIGNAL_CANDIDATE":
            raise SignalEventUnavailable("event_type must be SIGNAL_CANDIDATE")
        if self.stage not in ACTIONABLE_DECISION_KINDS:
            raise SignalEventUnavailable("stage must be PRE, CONFIRM, or OPEN_NOW")
        for name in ("signal_id", "symbol", "timeframe", "schema_version"):
            _text(getattr(self, name), name)
        if self.direction not in {"BUY", "SELL"}:
            raise SignalEventUnavailable("direction must be BUY or SELL")
        if self.buffer_mode not in ALLOWED_BUFFER_MODES:
            raise SignalEventUnavailable("buffer_mode must be SMALL, MEDIUM, or LARGE")
        _non_negative_number(self.score_total, "score_total")
        _non_negative_number(self.buffer_distance, "buffer_distance")
        _positive_number(self.model_expiry, "model_expiry")
        _positive_number(self.entry_price, "entry_price")
        _positive_int(self.candle_ts, "candle_ts")
        _positive_int(self.created_ts, "created_ts")
        if not isinstance(self.payload, Mapping):
            raise SignalEventUnavailable("payload must be a mapping")
        if self.distribution_enabled:
            raise SignalEventUnavailable("distribution cannot be enabled by SignalEvent")

        execution_values = (
            self.confirm_expiry_min_minutes,
            self.confirm_expiry_max_minutes,
            self.open_now_expiry_minutes,
            self.execution_calibration_source,
        )
        if not self.execution_time_available:
            if any(value is not None for value in execution_values):
                raise SignalEventUnavailable(
                    "execution-time fields require execution_time_available=true"
                )
            if self.stage == "OPEN_NOW":
                raise SignalEventUnavailable(
                    "OPEN_NOW requires governed execution-time expiry"
                )
            return

        if self.stage not in {"CONFIRM", "OPEN_NOW"}:
            raise SignalEventUnavailable(
                "execution-time fields are valid only for CONFIRM or OPEN_NOW"
            )
        confirm_min = _positive_number(
            self.confirm_expiry_min_minutes, "confirm_expiry_min_minutes"
        )
        confirm_max = _positive_number(
            self.confirm_expiry_max_minutes, "confirm_expiry_max_minutes"
        )
        if confirm_min > confirm_max:
            raise SignalEventUnavailable("CONFIRM execution interval is inverted")
        _text(self.execution_calibration_source, "execution_calibration_source")

        if self.stage == "CONFIRM":
            if self.open_now_expiry_minutes is not None:
                raise SignalEventUnavailable(
                    "CONFIRM must not expose an exact OPEN_NOW expiry"
                )
            return

        open_now = _positive_number(
            self.open_now_expiry_minutes, "open_now_expiry_minutes"
        )
        if not confirm_min <= open_now <= confirm_max:
            raise SignalEventUnavailable(
                "OPEN_NOW execution expiry violates CONFIRM interval"
            )

    @property
    def buffer_price(self) -> float:
        """Legacy interface alias; canonical truth is buffer_distance."""
        return self.buffer_distance

    @property
    def expiry_minutes(self) -> Optional[float]:
        """Compatibility alias for exact governed OPEN_NOW execution expiry.

        It deliberately returns ``None`` for PRE/CONFIRM and never derives a
        value from Model Time. No rounding is performed.
        """
        return self.open_now_expiry_minutes if self.stage == "OPEN_NOW" else None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["buffer_price"] = self.buffer_price
        result["expiry_minutes"] = self.expiry_minutes
        result["payload"] = dict(self.payload)
        return result


def _trade_physics_payload(decision: DecisionObject) -> Dict[str, Any] | None:
    trade_physics = decision.score.trade_physics
    if trade_physics is None:
        return None
    return {
        "readiness_state": trade_physics.readiness_state,
        "available_space": trade_physics.available_space,
        "required_space": trade_physics.required_space,
        "space_to_buffer_ratio": trade_physics.space_to_buffer_ratio,
        "trade_space_margin_atr": trade_physics.trade_space_margin_atr,
        "time_to_buffer_ratio": trade_physics.time_to_buffer_ratio,
        "directional_effective_speed": trade_physics.directional_effective_speed,
        "weighted_gross_speed": trade_physics.weighted_gross_speed,
        "flow_efficiency": trade_physics.flow_efficiency,
        "atr_speed_reference": trade_physics.atr_speed_reference,
        "directional_speed_ratio": trade_physics.directional_speed_ratio,
        "movement_stress": trade_physics.movement_stress,
        "S": trade_physics.S,
        "T": trade_physics.T,
        "P": trade_physics.P,
        "V": trade_physics.V,
        "TPS": trade_physics.TPS,
        "interpretation_band": trade_physics.interpretation_band,
        "formula_version": trade_physics.formula_version,
        "feature_schema_version": trade_physics.feature_schema_version,
    }


def _semantic_payload(decision: DecisionObject) -> Dict[str, Any]:
    return {
        "strategy": "Binary Trading",
        "strategy_version": "2.0.0",
        "canonical_specification": "ALGO_SPEC_v3.0.0",
        "decision_object_schema_version": decision.schema_version,
        "latest_price": float(decision.market_context.latest_price),
        "price_speed": float(decision.market_context.price_speed),
        "directional_effective_speed": decision.market_context.directional_effective_speed,
        "weighted_gross_speed": decision.market_context.weighted_gross_speed,
        "flow_efficiency": decision.market_context.flow_efficiency,
        "target_distance": decision.market_context.target_distance,
        "time_state": decision.time.time_state,
        "t_needed": decision.time.t_needed,
        "t_needed_adjusted": decision.time.t_needed_adjusted,
        "model_expiry": decision.time.model_expiry,
        "model_time_reach_ratio": decision.time.model_time_reach_ratio,
        "time_to_buffer_ratio": decision.time.time_to_buffer_ratio,
        "structure_state": decision.structure.feasibility_state,
        "structure_position": decision.structure.position,
        "score_tier": decision.score.tier,
        "trade_physics": _trade_physics_payload(decision),
        "explanations": tuple(decision.explanations),
        "source": decision.setup.source,
        "cycle_id": decision.setup.cycle_id,
    }


def _execution_fields(
    decision: DecisionObject,
    execution_time: Optional[ExecutionTimeResult],
) -> Dict[str, Any]:
    if execution_time is None or not execution_time.available:
        if decision.kind == "OPEN_NOW":
            raise SignalEventUnavailable(
                "OPEN_NOW requires available governed Execution Time"
            )
        return {
            "execution_time_available": False,
            "confirm_expiry_min_minutes": None,
            "confirm_expiry_max_minutes": None,
            "open_now_expiry_minutes": None,
            "execution_calibration_source": None,
        }

    if execution_time.symbol != decision.setup.symbol:
        raise SignalEventUnavailable("Execution Time symbol must match DecisionObject")
    if execution_time.cycle_id != decision.setup.cycle_id:
        raise SignalEventUnavailable("Execution Time cycle must match DecisionObject")
    if execution_time.fsm_outcome != decision.kind:
        raise SignalEventUnavailable("Execution Time stage must match DecisionObject")

    if decision.kind == "PRE":
        raise SignalEventUnavailable("PRE must not expose Execution Time")
    if decision.kind == "OPEN_NOW" and execution_time.open_now_expiry_minutes is None:
        raise SignalEventUnavailable("OPEN_NOW exact execution expiry is required")

    return {
        "execution_time_available": True,
        "confirm_expiry_min_minutes": execution_time.confirm_expiry_min_minutes,
        "confirm_expiry_max_minutes": execution_time.confirm_expiry_max_minutes,
        "open_now_expiry_minutes": execution_time.open_now_expiry_minutes,
        "execution_calibration_source": execution_time.calibration_source,
    }


def build_signal_event(
    decision: DecisionObject,
    *,
    buffer_mode: str,
    created_ts: int,
    execution_time: Optional[ExecutionTimeResult] = None,
) -> SignalEvent:
    """Build a complete internal candidate from real strategy and execution evidence."""

    if not isinstance(decision, DecisionObject):
        raise TypeError("decision must be a DecisionObject")
    if decision.kind not in ACTIONABLE_DECISION_KINDS:
        raise SignalEventUnavailable("only actionable decisions can form SignalEvent")
    if decision.time.model_expiry is None:
        raise SignalEventUnavailable("real model_expiry is required")
    model_expiry = _positive_number(decision.time.model_expiry, "model_expiry")
    normalized_buffer_mode = _text(buffer_mode, "buffer_mode").upper()
    execution_fields = _execution_fields(decision, execution_time)

    return SignalEvent(
        event_type="SIGNAL_CANDIDATE",
        stage=decision.kind,
        signal_id=_text(decision.signal_id, "signal_id"),
        symbol=decision.setup.symbol,
        timeframe=decision.setup.timeframe,
        direction=decision.setup.direction,
        score_total=float(decision.score.total),
        buffer_mode=normalized_buffer_mode,
        buffer_distance=float(decision.market_context.buffer_distance),
        model_expiry=model_expiry,
        candle_ts=decision.setup.evaluated_ts,
        created_ts=created_ts,
        entry_price=float(decision.market_context.latest_price),
        payload=_semantic_payload(decision),
        distribution_enabled=False,
        **execution_fields,
    )
