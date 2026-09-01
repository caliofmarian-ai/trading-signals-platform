from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "2.0.0"
ALLOWED_DIRECTIONS = frozenset({"BUY", "SELL", "NONE"})
ALLOWED_DECISION_KINDS = frozenset({"NO_SIGNAL", "PRE", "CONFIRM", "OPEN_NOW", "REJECT"})
ACTIONABLE_DECISION_KINDS = frozenset({"PRE", "CONFIRM", "OPEN_NOW"})
ALLOWED_TIME_STATES = frozenset({"EARLY", "BUILDING", "READY", "CRITICAL", "LATE", "EXPIRED", "UNAVAILABLE"})
ALLOWED_STRUCTURE_STATES = frozenset({"VALID", "CONSTRAINED", "DEGRADED", "CONFLICTED", "INVALID", "UNAVAILABLE"})
ALLOWED_TRADE_PHYSICS_STATES = frozenset({
    "READY",
    "UNAVAILABLE_MISSING_STRUCTURE",
    "UNAVAILABLE_MISSING_TIME",
    "UNAVAILABLE_MISSING_ATR",
    "UNAVAILABLE_MISSING_SPEED",
    "BLOCKED_UNSTABLE_MARKET",
    "INVALID_EVIDENCE",
})


def _required_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _finite_non_negative(value: float, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not isfinite(float(value)) or float(value) < 0:
        raise ValueError(f"{name} must be finite and non-negative")


def _optional_finite(value: Optional[float], name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise ValueError(f"{name} must be finite when available")


def _optional_non_negative(value: Optional[float], name: str) -> None:
    _optional_finite(value, name)
    if value is not None and value < 0:
        raise ValueError(f"{name} must be non-negative when available")


def _plain(value: Any) -> Any:
    """Convert semantic mapping/tuple values into JSON-ready primitives."""
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class SetupContext:
    symbol: str
    direction: str
    evaluated_ts: int
    timeframe: str
    cycle_id: str
    source: str

    def __post_init__(self) -> None:
        for name in ("symbol", "timeframe", "cycle_id", "source"):
            _required_text(getattr(self, name), f"setup.{name}")
        if self.direction not in ALLOWED_DIRECTIONS:
            raise ValueError("setup.direction must be BUY, SELL, or NONE")
        if isinstance(self.evaluated_ts, bool) or not isinstance(self.evaluated_ts, int) or self.evaluated_ts <= 0:
            raise ValueError("setup.evaluated_ts must be a positive integer")


@dataclass(frozen=True)
class MarketContext:
    latest_price: float
    price_speed: float
    buffer_distance: float
    trend_context: str
    volatility_state: str
    noise_context: str
    target_distance: Optional[float] = None
    directional_effective_speed: Optional[float] = None
    weighted_gross_speed: Optional[float] = None
    flow_efficiency: Optional[float] = None

    def __post_init__(self) -> None:
        _finite_non_negative(self.latest_price, "market_context.latest_price")
        if float(self.latest_price) == 0:
            raise ValueError("market_context.latest_price must be positive")
        _finite_non_negative(self.price_speed, "market_context.price_speed")
        _finite_non_negative(self.buffer_distance, "market_context.buffer_distance")
        _optional_finite(self.target_distance, "market_context.target_distance")
        _optional_non_negative(self.directional_effective_speed, "market_context.directional_effective_speed")
        _optional_non_negative(self.weighted_gross_speed, "market_context.weighted_gross_speed")
        _optional_non_negative(self.flow_efficiency, "market_context.flow_efficiency")
        if self.flow_efficiency is not None and self.flow_efficiency > 1:
            raise ValueError("market_context.flow_efficiency must be between 0 and 1")
        for name in ("trend_context", "volatility_state", "noise_context"):
            _required_text(getattr(self, name), f"market_context.{name}")


@dataclass(frozen=True)
class StructureContext:
    support: Optional[float]
    resistance: Optional[float]
    lower_boundary: Optional[float]
    upper_boundary: Optional[float]
    corridor_width: Optional[float]
    available_distance: Optional[float]
    position: str
    feasibility_state: str
    conflicts: Tuple[str, ...] = ()
    explanation: str = ""

    def __post_init__(self) -> None:
        for name in ("support", "resistance", "lower_boundary", "upper_boundary", "corridor_width", "available_distance"):
            _optional_finite(getattr(self, name), f"structure.{name}")
        if self.corridor_width is not None and self.corridor_width < 0:
            raise ValueError("structure.corridor_width must be non-negative")
        if self.available_distance is not None and self.available_distance < 0:
            raise ValueError("structure.available_distance must be non-negative")
        if self.lower_boundary is not None and self.upper_boundary is not None and self.lower_boundary > self.upper_boundary:
            raise ValueError("structure boundaries are reversed")
        _required_text(self.position, "structure.position")
        if self.feasibility_state not in ALLOWED_STRUCTURE_STATES:
            raise ValueError("structure.feasibility_state is not canonical")


@dataclass(frozen=True)
class TimeContext:
    t_needed: Optional[float]
    t_needed_adjusted: Optional[float]
    model_expiry: Optional[float]
    model_time_reach_ratio: Optional[float]
    corridor_time_pressure: Optional[float]
    time_state: str
    time_to_buffer_ratio: Optional[float] = None

    def __post_init__(self) -> None:
        for name in (
            "t_needed",
            "t_needed_adjusted",
            "model_expiry",
            "model_time_reach_ratio",
            "corridor_time_pressure",
            "time_to_buffer_ratio",
        ):
            value = getattr(self, name)
            _optional_finite(value, f"time.{name}")
            if value is not None and value < 0:
                raise ValueError(f"time.{name} must be non-negative")
        if self.time_state not in ALLOWED_TIME_STATES:
            raise ValueError("time.time_state is not canonical")


@dataclass(frozen=True)
class TradePhysicsContext:
    readiness_state: str
    available_space: Optional[float] = None
    required_space: Optional[float] = None
    space_to_buffer_ratio: Optional[float] = None
    trade_space_margin_atr: Optional[float] = None
    time_to_buffer_ratio: Optional[float] = None
    directional_effective_speed: Optional[float] = None
    weighted_gross_speed: Optional[float] = None
    flow_efficiency: Optional[float] = None
    atr_speed_reference: Optional[float] = None
    directional_speed_ratio: Optional[float] = None
    movement_stress: Optional[float] = None
    S: Optional[float] = None
    T: Optional[float] = None
    P: Optional[float] = None
    V: Optional[float] = None
    TPS: Optional[float] = None
    interpretation_band: Optional[str] = None
    formula_version: str = "TRADE_PHYSICS_MODEL_SPEC_v1.0.0"
    feature_schema_version: str = "1.0.0"
    explanation: str = ""

    def __post_init__(self) -> None:
        if self.readiness_state not in ALLOWED_TRADE_PHYSICS_STATES:
            raise ValueError("trade_physics.readiness_state is not canonical")
        for name in (
            "available_space",
            "required_space",
            "space_to_buffer_ratio",
            "time_to_buffer_ratio",
            "directional_effective_speed",
            "weighted_gross_speed",
            "flow_efficiency",
            "atr_speed_reference",
            "directional_speed_ratio",
            "movement_stress",
            "S",
            "T",
            "P",
            "V",
            "TPS",
        ):
            _optional_non_negative(getattr(self, name), f"trade_physics.{name}")
        _optional_finite(self.trade_space_margin_atr, "trade_physics.trade_space_margin_atr")
        if self.flow_efficiency is not None and self.flow_efficiency > 1:
            raise ValueError("trade_physics.flow_efficiency must be between 0 and 1")
        for name in ("S", "T", "P", "V"):
            value = getattr(self, name)
            if value is not None and value > 1:
                raise ValueError(f"trade_physics.{name} must be between 0 and 1")
        if self.TPS is not None and self.TPS > 100:
            raise ValueError("trade_physics.TPS must be between 0 and 100")
        if self.readiness_state == "READY" and self.TPS is None:
            raise ValueError("READY Trade Physics requires TPS")
        if self.readiness_state != "READY" and self.TPS is not None:
            raise ValueError("non-READY Trade Physics must not expose authoritative TPS")
        _required_text(self.formula_version, "trade_physics.formula_version")
        _required_text(self.feature_schema_version, "trade_physics.feature_schema_version")


@dataclass(frozen=True)
class ScoreContext:
    total: float
    normalized: float
    components: Mapping[str, float]
    penalties: Mapping[str, float] = field(default_factory=dict)
    tier: str = "UNAVAILABLE"
    trade_physics: Optional[TradePhysicsContext] = None

    def __post_init__(self) -> None:
        _finite_non_negative(self.total, "score.total")
        _finite_non_negative(self.normalized, "score.normalized")
        if self.normalized > 1:
            raise ValueError("score.normalized must be between 0 and 1")
        _required_text(self.tier, "score.tier")
        for family, value in {**dict(self.components), **dict(self.penalties)}.items():
            _required_text(family, "score component name")
            _finite_non_negative(value, f"score component {family}")


@dataclass(frozen=True)
class StrategicFlags:
    valid_structure: bool
    feasible_time: bool
    degraded_setup: bool
    unstable_market: bool
    low_confidence: bool
    rejectable: bool
    borderline: bool
    trade_physics_ready: bool = False
    physically_constrained: bool = False


@dataclass(frozen=True)
class RejectContext:
    reason: Optional[str] = None
    category: Optional[str] = None
    stage: Optional[str] = None
    hard_blockers: Tuple[str, ...] = ()
    soft_blockers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.hard_blockers and not self.reason:
            raise ValueError("reject.reason is required when hard blockers exist")


@dataclass(frozen=True)
class DecisionObject:
    kind: str
    signal_id: Optional[str]
    setup: SetupContext
    market_context: MarketContext
    structure: StructureContext
    time: TimeContext
    score: ScoreContext
    strategic_flags: StrategicFlags
    reject: RejectContext
    fsm_inputs: Mapping[str, Any]
    explanations: Tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    producer: str = "binary_strategy_v2"
    compatibility_mode: bool = False

    def __post_init__(self) -> None:
        if self.kind not in ALLOWED_DECISION_KINDS:
            raise ValueError("kind is not canonical")
        if self.kind in ACTIONABLE_DECISION_KINDS:
            _required_text(self.signal_id, "signal_id")
            if self.setup.direction not in {"BUY", "SELL"}:
                raise ValueError("an actionable decision requires BUY or SELL direction")
        elif self.signal_id is not None:
            raise ValueError("non-actionable decisions must not expose signal_id")
        if self.strategic_flags.rejectable and self.kind != "REJECT":
            raise ValueError("rejectable strategic evidence requires REJECT kind")
        if self.kind == "REJECT" and not self.strategic_flags.rejectable:
            raise ValueError("REJECT kind requires rejectable strategic evidence")
        _required_text(self.schema_version, "schema_version")
        _required_text(self.producer, "producer")
        if self.strategic_flags.rejectable and not (self.reject.reason or self.reject.hard_blockers):
            raise ValueError("reject semantics are required for a rejectable decision")
        if not self.explanations:
            raise ValueError("at least one decision explanation is required")

    def to_dict(self) -> Dict[str, Any]:
        return _plain(asdict(self))
