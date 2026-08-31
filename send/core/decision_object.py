from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "1.0.0"
ALLOWED_DIRECTIONS = frozenset({"BUY", "SELL", "NONE"})
ALLOWED_DECISION_KINDS = frozenset({"NO_SIGNAL", "PRE", "CONFIRM", "OPEN_NOW", "REJECT"})
ACTIONABLE_DECISION_KINDS = frozenset({"PRE", "CONFIRM", "OPEN_NOW"})
ALLOWED_TIME_STATES = frozenset({"EARLY", "BUILDING", "READY", "CRITICAL", "LATE", "EXPIRED", "UNAVAILABLE"})
ALLOWED_STRUCTURE_STATES = frozenset({"VALID", "CONSTRAINED", "DEGRADED", "CONFLICTED", "INVALID", "UNAVAILABLE"})


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

    def __post_init__(self) -> None:
        _finite_non_negative(self.latest_price, "market_context.latest_price")
        if float(self.latest_price) == 0:
            raise ValueError("market_context.latest_price must be positive")
        _finite_non_negative(self.price_speed, "market_context.price_speed")
        _finite_non_negative(self.buffer_distance, "market_context.buffer_distance")
        _optional_finite(self.target_distance, "market_context.target_distance")
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

    def __post_init__(self) -> None:
        for name in ("t_needed", "t_needed_adjusted", "model_expiry", "model_time_reach_ratio", "corridor_time_pressure"):
            value = getattr(self, name)
            _optional_finite(value, f"time.{name}")
            if value is not None and value < 0:
                raise ValueError(f"time.{name} must be non-negative")
        if self.time_state not in ALLOWED_TIME_STATES:
            raise ValueError("time.time_state is not canonical")


@dataclass(frozen=True)
class ScoreContext:
    total: float
    normalized: float
    components: Mapping[str, float]
    penalties: Mapping[str, float] = field(default_factory=dict)
    tier: str = "UNAVAILABLE"

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
