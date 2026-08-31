"""Validated Binary Strategy V2 engine-to-distribution contract.

This module only constructs an internal semantic object.  It does not route,
format, publish, register an outcome, or execute a trade.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil, isfinite
from typing import Any, Dict, Mapping, Tuple

from .decision_object import ACTIONABLE_DECISION_KINDS, DecisionObject


SIGNAL_EVENT_SCHEMA_VERSION = "2.0.0"
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
    expiry_minutes: int
    candle_ts: int
    created_ts: int
    entry_price: float
    payload: Mapping[str, Any]
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
        _positive_number(self.entry_price, "entry_price")
        _positive_int(self.expiry_minutes, "expiry_minutes")
        _positive_int(self.candle_ts, "candle_ts")
        _positive_int(self.created_ts, "created_ts")
        if not isinstance(self.payload, Mapping):
            raise SignalEventUnavailable("payload must be a mapping")
        if self.distribution_enabled:
            raise SignalEventUnavailable("distribution cannot be enabled by SignalEvent")

    @property
    def buffer_price(self) -> float:
        """Legacy interface alias; the V2 strategic truth is buffer_distance."""

        return self.buffer_distance

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # MODULE_INTERFACE_SPEC still exposes this legacy field.  Keep it only
        # as an explicit compatibility alias, never as the strategic truth.
        result["buffer_price"] = self.buffer_price
        result["payload"] = dict(self.payload)
        return result


def _semantic_payload(decision: DecisionObject) -> Dict[str, Any]:
    return {
        "strategy": "Binary Trading",
        "strategy_version": "2.0.0",
        "canonical_specification": "ALGO_SPEC_v2.0.0",
        "latest_price": float(decision.market_context.latest_price),
        "price_speed": float(decision.market_context.price_speed),
        "target_distance": decision.market_context.target_distance,
        "time_state": decision.time.time_state,
        "t_needed": decision.time.t_needed,
        "t_needed_adjusted": decision.time.t_needed_adjusted,
        "model_time_reach_ratio": decision.time.model_time_reach_ratio,
        "structure_state": decision.structure.feasibility_state,
        "structure_position": decision.structure.position,
        "score_tier": decision.score.tier,
        "explanations": tuple(decision.explanations),
        "source": decision.setup.source,
        "cycle_id": decision.setup.cycle_id,
    }


def build_signal_event(
    decision: DecisionObject, *, buffer_mode: str, created_ts: int
) -> SignalEvent:
    """Build a complete internal candidate from real V2 decision evidence."""

    if not isinstance(decision, DecisionObject):
        raise TypeError("decision must be a DecisionObject")
    if decision.kind not in ACTIONABLE_DECISION_KINDS:
        raise SignalEventUnavailable("only actionable decisions can form SignalEvent")
    if decision.time.model_expiry is None:
        raise SignalEventUnavailable("real model_expiry is required")
    expiry_minutes = int(ceil(_positive_number(decision.time.model_expiry, "model_expiry")))
    normalized_buffer_mode = _text(buffer_mode, "buffer_mode").upper()
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
        expiry_minutes=expiry_minutes,
        candle_ts=decision.setup.evaluated_ts,
        created_ts=created_ts,
        entry_price=float(decision.market_context.latest_price),
        payload=_semantic_payload(decision),
        distribution_enabled=False,
    )

