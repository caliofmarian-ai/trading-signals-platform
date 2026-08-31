"""Canonical strategy stack orchestrator running exclusively in shadow mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Sequence

from .decision_assembly import assemble_decision
from .decision_object import DecisionObject
from .execution_model import ExecutionCalibration, ExecutionTimeResult, derive_execution_time
from .fsm_decision_adapter import FSMInterpretation, interpret_decision
from .market_model import MarketModelResult, evaluate_market
from .scoring_model import ScoringResult, evaluate_score
from .sr_corridor_engine import CorridorResult, evaluate_corridor
from .time_model import TimeModelResult, evaluate_time


SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class CanonicalStrategyEvaluation:
    schema_version: str
    cycle_id: str
    market: MarketModelResult
    corridor: CorridorResult
    time: TimeModelResult
    scoring: ScoringResult
    decision: DecisionObject
    fsm: FSMInterpretation
    execution_time: ExecutionTimeResult
    shadow_only: bool
    signal_handoff_ready: bool


def evaluate_canonical_strategy(
    candles_m1: Sequence[Mapping[str, Any]],
    candles_m5: Sequence[Mapping[str, Any]],
    params: Mapping[str, Any],
    *,
    cycle_id: str,
    timeframe: str = "M1",
    buffer_mode: str = "MEDIUM",
    runtime_blockers: Iterable[str] = (),
    execution_calibration: Optional[ExecutionCalibration] = None,
) -> CanonicalStrategyEvaluation:
    """Run one synchronized analysis without touching live strategy state."""

    market = evaluate_market(candles_m1, candles_m5, params, buffer_mode=buffer_mode)
    corridor = evaluate_corridor(candles_m5, market, params)
    time = evaluate_time(market, corridor, params)
    scoring = evaluate_score(market, corridor, time, params)
    decision = assemble_decision(
        market,
        corridor,
        time,
        scoring,
        timeframe=timeframe,
        cycle_id=cycle_id,
        source="canonical_strategy_v3_shadow",
    )
    fsm = interpret_decision(decision, runtime_blockers=runtime_blockers)
    execution_time = derive_execution_time(decision, fsm, execution_calibration)

    if fsm.signal_handoff_ready or execution_time.signal_handoff_ready:
        raise RuntimeError("canonical shadow pipeline must never authorize signal handoff")

    return CanonicalStrategyEvaluation(
        schema_version=SCHEMA_VERSION,
        cycle_id=decision.setup.cycle_id,
        market=market,
        corridor=corridor,
        time=time,
        scoring=scoring,
        decision=decision,
        fsm=fsm,
        execution_time=execution_time,
        shadow_only=True,
        signal_handoff_ready=False,
    )
