"""Assemble synchronized strategy layers into the canonical DecisionObject."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from typing import Any, Iterator, Mapping, Optional

from .decision_object import (
    DecisionObject,
    RejectContext,
    SetupContext,
    StrategicFlags,
)
from .market_model import MarketModelResult
from .scoring_model import ScoringResult
from .sr_corridor_engine import CorridorResult
from .time_model import TimeModelResult


class DecisionAssemblyUnavailable(ValueError):
    """Raised when layer outputs cannot form one trustworthy evaluation."""


class FrozenInputs(Mapping[str, Any]):
    """Immutable semantic inputs that remain compatible with serialization."""

    __slots__ = ("_items",)

    def __init__(self, values: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_items", tuple(values.items()))

    def __getitem__(self, key: str) -> Any:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __deepcopy__(self, memo: dict[int, Any]) -> "FrozenInputs":
        return self


_TIER_TO_DECISION_KIND = {
    "BELOW_PRE": "NO_SIGNAL",
    "SCORE_PRE_BAND": "PRE",
    "SCORE_CONFIRM_BAND": "CONFIRM",
    "SCORE_OPEN_BAND": "OPEN_NOW",
}


def _decision_kind(scoring: ScoringResult) -> str:
    if not scoring.eligible or scoring.hard_blockers:
        return "REJECT"
    try:
        return _TIER_TO_DECISION_KIND[scoring.context.tier]
    except KeyError as exc:
        raise DecisionAssemblyUnavailable("score tier cannot form a canonical decision kind") from exc


def _stable_signal_id(*, symbol: str, timeframe: str, candle_ts: int) -> str:
    identity = f"binary-strategy-v2|{symbol.upper()}|{timeframe.upper()}|{candle_ts}"
    return f"sig-v2-{sha256(identity.encode('utf-8')).hexdigest()[:24]}"


def assemble_decision(
    market: MarketModelResult,
    corridor: CorridorResult,
    time: TimeModelResult,
    scoring: ScoringResult,
    *,
    timeframe: str,
    cycle_id: str,
    source: str = "binary_strategy_v2",
    opportunity_signal_id: Optional[str] = None,
) -> DecisionObject:
    """Create the standardized pre-FSM contract without making an FSM decision."""

    identities = {
        (market.symbol, market.evaluated_ts),
        (corridor.symbol, corridor.evaluated_ts),
        (time.symbol, time.evaluated_ts),
        (scoring.symbol, scoring.evaluated_ts),
        (scoring.trade_physics.symbol, scoring.trade_physics.evaluated_ts),
    }
    if len(identities) != 1:
        raise DecisionAssemblyUnavailable("all strategy layers must describe the same evaluation")
    if not isinstance(timeframe, str) or not timeframe.strip():
        raise DecisionAssemblyUnavailable("timeframe is required")
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise DecisionAssemblyUnavailable("cycle_id is required")
    if corridor.direction != market.direction_bias:
        raise DecisionAssemblyUnavailable("market and corridor direction disagree")
    if opportunity_signal_id is not None and (
        not isinstance(opportunity_signal_id, str) or not opportunity_signal_id.strip()
    ):
        raise DecisionAssemblyUnavailable("opportunity_signal_id must be non-empty text")

    trade_physics = scoring.trade_physics
    valid_structure = corridor.structure.feasibility_state == "VALID"
    feasible_time = time.temporally_feasible and time.context.time_state == "READY"
    unstable_market = (
        market.context.volatility_state != "ACTIVE" or market.context.noise_context != "STABLE"
    )
    rejectable = not scoring.eligible
    low_confidence = scoring.context.tier == "BELOW_PRE"
    borderline = scoring.context.tier in {"SCORE_PRE_BAND", "SCORE_CONFIRM_BAND"}
    degraded_setup = False

    blockers = tuple(scoring.hard_blockers)
    reject = RejectContext(
        reason="; ".join(blockers) if blockers else None,
        category="STRATEGIC_GATE" if blockers else None,
        stage="PRE_FSM" if blockers else None,
        hard_blockers=blockers,
        soft_blockers=(),
    )
    flags = StrategicFlags(
        valid_structure=valid_structure,
        feasible_time=feasible_time,
        degraded_setup=degraded_setup,
        unstable_market=unstable_market,
        low_confidence=low_confidence,
        rejectable=rejectable,
        borderline=borderline,
        trade_physics_ready=trade_physics.ready,
        physically_constrained=trade_physics.physically_constrained,
    )

    explanations = (
        f"Market context: trend={market.context.trend_context}, activity={market.context.volatility_state}, noise={market.context.noise_context}.",
        corridor.structure.explanation,
        time.explanation,
        scoring.explanation,
        trade_physics.explanation,
        "No strategic hard blocker is present." if not blockers else f"Hard blockers: {', '.join(blockers)}.",
        "Corridor time pressure is unavailable until a calibrated canonical formula exists."
        if time.context.corridor_time_pressure is None else
        f"Corridor time pressure: {time.context.corridor_time_pressure}.",
    )

    fsm_inputs = FrozenInputs({
        "strategy_eligible": scoring.eligible,
        "score_total": scoring.context.total,
        "score_tier": scoring.context.tier,
        "valid_structure": valid_structure,
        "feasible_time": feasible_time,
        "unstable_market": unstable_market,
        "trade_physics_readiness": trade_physics.readiness_state,
        "TPS": trade_physics.TPS,
        "physically_constrained": trade_physics.physically_constrained,
        "hard_blockers": blockers,
    })
    kind = _decision_kind(scoring)
    normalized_timeframe = timeframe.strip().upper()
    signal_id = (
        opportunity_signal_id.strip() if opportunity_signal_id is not None else _stable_signal_id(
            symbol=market.symbol,
            timeframe=normalized_timeframe,
            candle_ts=market.evaluated_ts,
        )
        if kind in {"PRE", "CONFIRM", "OPEN_NOW"}
        else None
    )
    return DecisionObject(
        kind=kind,
        signal_id=signal_id,
        setup=SetupContext(
            symbol=market.symbol,
            direction=market.direction_bias,
            evaluated_ts=market.evaluated_ts,
            timeframe=normalized_timeframe,
            cycle_id=cycle_id.strip(),
            source=source,
        ),
        market_context=replace(
            market.context,
            target_distance=corridor.structure.available_distance,
        ),
        structure=corridor.structure,
        time=time.context,
        score=scoring.context,
        strategic_flags=flags,
        reject=reject,
        fsm_inputs=fsm_inputs,
        explanations=explanations,
        producer="binary_strategy_v2_decision_assembly",
        compatibility_mode=False,
    )
