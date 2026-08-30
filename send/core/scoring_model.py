"""Canonical transparent strategic scoring model.

Scoring aggregates upstream evidence.  It does not decide FSM state, emit a
signal, choose execution timing, or place a trade.  Hard blockers remain
visible even when the arithmetic score is high.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Iterator, Mapping

from .decision_object import ScoreContext
from .market_model import MarketModelResult
from .sr_corridor_engine import CorridorResult
from .time_model import TimeModelResult


SCHEMA_VERSION = "1.0.0"


class ScoringUnavailable(ValueError):
    """Raised when synchronized evidence or scoring configuration is invalid."""


class FrozenScores(Mapping[str, float]):
    """Small immutable mapping that remains safe for dataclass serialization."""

    __slots__ = ("_items",)

    def __init__(self, values: Mapping[str, float]) -> None:
        object.__setattr__(self, "_items", tuple(values.items()))

    def __getitem__(self, key: str) -> float:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __deepcopy__(self, memo: dict[int, Any]) -> "FrozenScores":
        return self


@dataclass(frozen=True)
class ScoringEvidence:
    rsi: float
    rsi_target: float
    body_ratio: float
    structural_room_ratio: float | None
    time_reach_ratio: float | None
    component_maxima: Mapping[str, float]


@dataclass(frozen=True)
class ScoringResult:
    schema_version: str
    symbol: str
    evaluated_ts: int
    context: ScoreContext
    eligible: bool
    hard_blockers: tuple[str, ...]
    explanation: str
    evidence: ScoringEvidence


def _required_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ScoringUnavailable(f"{name} configuration is required")
    return value


def _required_number(mapping: Mapping[str, Any], key: str, name: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool):
        raise ScoringUnavailable(f"{name}.{key} configuration is required")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ScoringUnavailable(f"{name}.{key} configuration is required") from exc
    if not isfinite(number):
        raise ScoringUnavailable(f"{name}.{key} must be finite")
    return number


def _clamp(value: float, lower: float, upper: float) -> float:
    return lower if value < lower else upper if value > upper else value


def evaluate_score(
    market: MarketModelResult,
    corridor: CorridorResult,
    time: TimeModelResult,
    params: Mapping[str, Any],
) -> ScoringResult:
    """Aggregate canonical upstream evidence using established score math."""

    identities = {(market.symbol, market.evaluated_ts), (corridor.symbol, corridor.evaluated_ts), (time.symbol, time.evaluated_ts)}
    if len(identities) != 1:
        raise ScoringUnavailable("market, corridor and time evidence must describe the same evaluation")

    strategy = _required_mapping(params.get("strategy_v2"), "strategy_v2")
    rsi_call = _required_number(strategy, "rsi_call", "strategy_v2")
    rsi_put = _required_number(strategy, "rsi_put", "strategy_v2")
    thresholds = _required_mapping(params.get("score_thresholds"), "score_thresholds")
    threshold_pre = _required_number(thresholds, "PRE", "score_thresholds")
    threshold_confirm = _required_number(thresholds, "CONFIRM", "score_thresholds")
    threshold_open = _required_number(thresholds, "OPEN", "score_thresholds")
    if not (0 <= threshold_pre <= threshold_confirm <= threshold_open <= 100):
        raise ScoringUnavailable("score thresholds must satisfy 0 <= PRE <= CONFIRM <= OPEN <= 100")

    if market.context.trend_context == "WITH_TREND":
        trend_score = 30.0
    elif market.context.trend_context == "FLAT":
        trend_score = 15.0
    elif market.context.trend_context == "COUNTER_TREND":
        trend_score = 0.0
    else:
        raise ScoringUnavailable("market trend context is not recognized")

    rsi_value = market.evidence.rsi
    if market.direction_bias == "BUY":
        rsi_target = rsi_call
        if rsi_value >= rsi_call:
            rsi_score = 20.0
        elif rsi_value <= 50:
            rsi_score = 0.0
        else:
            rsi_score = 20.0 * ((rsi_value - 50.0) / max(rsi_call - 50.0, 1e-9))
    elif market.direction_bias == "SELL":
        rsi_target = rsi_put
        if rsi_value <= rsi_put:
            rsi_score = 20.0
        elif rsi_value >= 50:
            rsi_score = 0.0
        else:
            rsi_score = 20.0 * ((50.0 - rsi_value) / max(50.0 - rsi_put, 1e-9))
    else:
        raise ScoringUnavailable("market direction must be BUY or SELL")

    average_body = market.evidence.average_body_last_10
    body_ratio = market.evidence.latest_body / max(average_body, 1e-9)
    body_score = 0.0 if body_ratio <= 1.0 else 15.0 * _clamp((body_ratio - 1.0) / 0.4, 0.0, 1.0)

    room_ratio = corridor.evidence.room_ratio
    structure_score = 0.0 if room_ratio is None else 20.0 * _clamp(room_ratio, 0.0, 1.0)

    time_ratio = time.context.model_time_reach_ratio
    if time_ratio is None:
        feasibility_score = 0.0
    elif time_ratio <= 0.8:
        feasibility_score = 15.0
    elif time_ratio <= 1.0:
        feasibility_score = 15.0 * _clamp((1.0 - time_ratio) / 0.2, 0.0, 1.0)
    else:
        feasibility_score = 0.0

    components = FrozenScores({
        "context_trend": trend_score,
        "momentum_rsi": rsi_score,
        "candle_body_expansion": body_score,
        "structure_corridor": structure_score,
        "time_feasibility": feasibility_score,
    })
    total = _clamp(sum(components.values()), 0.0, 100.0)

    blockers: list[str] = []
    if market.context.volatility_state != "ACTIVE":
        blockers.append("MARKET_ACTIVITY_NOT_ACTIVE")
    if market.context.noise_context != "STABLE":
        blockers.append("MARKET_NOISE_UNSTABLE")
    if corridor.structure.feasibility_state != "VALID":
        blockers.append("STRUCTURE_NOT_VALID")
    if time.context.time_state != "READY" or not time.temporally_feasible:
        blockers.append("TIME_NOT_FEASIBLE")
    eligible = not blockers

    if not eligible:
        tier = "BLOCKED"
        explanation = "The arithmetic score is informational only because one or more strategic gates are blocked."
    elif total >= threshold_open:
        tier, explanation = "SCORE_OPEN_BAND", "The eligible score reached the configured OPEN band."
    elif total >= threshold_confirm:
        tier, explanation = "SCORE_CONFIRM_BAND", "The eligible score reached the configured CONFIRM band."
    elif total >= threshold_pre:
        tier, explanation = "SCORE_PRE_BAND", "The eligible score reached the configured PRE band."
    else:
        tier, explanation = "BELOW_PRE", "The eligible score remains below the configured PRE band."

    context = ScoreContext(
        total=total,
        normalized=total / 100.0,
        components=components,
        penalties=FrozenScores({}),
        tier=tier,
    )
    return ScoringResult(
        schema_version=SCHEMA_VERSION,
        symbol=market.symbol,
        evaluated_ts=market.evaluated_ts,
        context=context,
        eligible=eligible,
        hard_blockers=tuple(blockers),
        explanation=explanation,
        evidence=ScoringEvidence(
            rsi=rsi_value,
            rsi_target=rsi_target,
            body_ratio=body_ratio,
            structural_room_ratio=room_ratio,
            time_reach_ratio=time_ratio,
            component_maxima=FrozenScores({
                "context_trend": 30.0,
                "momentum_rsi": 20.0,
                "candle_body_expansion": 15.0,
                "structure_corridor": 20.0,
                "time_feasibility": 15.0,
            }),
        ),
    )
