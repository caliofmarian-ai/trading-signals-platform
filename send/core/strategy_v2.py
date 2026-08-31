"""Binary Strategy V2 — the canonical binary-trading decision engine.

The engine follows ALGO_SPEC_v2.0.0 in the required order:
market model -> corridor -> time -> score -> DecisionObject -> FSM.
It is deterministic and has no file, Telegram, distribution, or broker access.
"""

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


STRATEGY_VERSION = "2.0.0"
CANONICAL_SPEC = "ALGO_SPEC_v2.0.0"


@dataclass(frozen=True)
class BinaryStrategyV2Evaluation:
    strategy_version: str
    canonical_spec: str
    cycle_id: str
    market: MarketModelResult
    corridor: CorridorResult
    time: TimeModelResult
    scoring: ScoringResult
    decision: DecisionObject
    fsm: FSMInterpretation
    execution_time: ExecutionTimeResult
    signal_handoff_ready: bool


def decide(
    candles_m1: Sequence[Mapping[str, Any]],
    candles_m5: Sequence[Mapping[str, Any]],
    params: Mapping[str, Any],
    buffer_mode: str = "MEDIUM",
    want_open_now: bool = False,
    context: Optional[Mapping[str, Any]] = None,
    *,
    cycle_id: Optional[str] = None,
    runtime_blockers: Iterable[str] = (),
    execution_calibration: Optional[ExecutionCalibration] = None,
) -> BinaryStrategyV2Evaluation:
    """Evaluate one complete V2 decision cycle from real candle evidence.

    ``want_open_now`` is accepted only to preserve the public call boundary
    during migration. It cannot force or promote an outcome; V2 derives the
    outcome exclusively from the canonical evidence and FSM.
    """

    del want_open_now
    supplied_context = dict(context or {})
    resolved_cycle_id = str(
        cycle_id
        or supplied_context.get("cycle_id")
        or f"{str(candles_m1[0].get('symbol', 'UNKNOWN')).upper()}:{int(candles_m1[0].get('ts', 0))}"
    ).strip()
    timeframe = str(supplied_context.get("decision_timeframe") or "M1").strip().upper()

    market = evaluate_market(candles_m1, candles_m5, params, buffer_mode=buffer_mode)
    corridor = evaluate_corridor(candles_m5, market, params)
    time_result = evaluate_time(market, corridor, params)
    scoring = evaluate_score(market, corridor, time_result, params)
    decision = assemble_decision(
        market,
        corridor,
        time_result,
        scoring,
        timeframe=timeframe,
        cycle_id=resolved_cycle_id,
        source="binary_strategy_v2",
        opportunity_signal_id=supplied_context.get("opportunity_signal_id"),
    )
    fsm = interpret_decision(decision, runtime_blockers=runtime_blockers)
    execution_time = derive_execution_time(decision, fsm, execution_calibration)

    if fsm.signal_handoff_ready or execution_time.signal_handoff_ready:
        raise RuntimeError("Binary Strategy V2 cannot bypass the signal execution contract")

    return BinaryStrategyV2Evaluation(
        strategy_version=STRATEGY_VERSION,
        canonical_spec=CANONICAL_SPEC,
        cycle_id=decision.setup.cycle_id,
        market=market,
        corridor=corridor,
        time=time_result,
        scoring=scoring,
        decision=decision,
        fsm=fsm,
        execution_time=execution_time,
        signal_handoff_ready=False,
    )
