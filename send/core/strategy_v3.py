"""Active scoreless V3: physical eligibility and an ordered opportunity lifecycle.

No classical score, TPS, weighted components or score thresholds are consumed.
The V2 module remains available exclusively for historical replay.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional

from .decision_assembly import FrozenInputs, assemble_decision
from .decision_object import ScoreContext
from .execution_model import derive_execution_time
from .fsm_decision_adapter import interpret_decision
from .market_model import evaluate_market
from .sr_corridor_engine import evaluate_corridor
from .time_model import evaluate_time
from .trade_physics import evaluate_trade_physics
from .market_history_policy import HISTORY_POLICY

STRATEGY_VERSION = "3.0.0"
CANONICAL_SPEC = "V3_SCORELESS_OWNER_AMENDMENT_v1.1.0"
DECISION_POLICY = "PHYSICAL_ONLY_V3"
MIN_PRE_LEAD_SECONDS = 30


@dataclass(frozen=True)
class PhysicalEligibility:
    symbol: str
    evaluated_ts: int
    context: ScoreContext
    eligible: bool
    hard_blockers: tuple[str, ...]
    explanation: str
    trade_physics: Any


@dataclass(frozen=True)
class PhysicalV3Evaluation:
    strategy_version: str
    canonical_spec: str
    cycle_id: str
    market: Any
    corridor: Any
    time: Any
    scoring: PhysicalEligibility  # typed compatibility; no numerical score
    trade_physics: Any
    decision: Any
    fsm: Any
    execution_time: Any
    signal_handoff_ready: bool = False


def lifecycle_context(state: Mapping[str, Any], symbol: str, *, now_ts: float,
                      owner_pre_ts: Optional[float] = None, owner_confirm_ts: Optional[float] = None,
                      require_owner_receipts: bool = False) -> dict[str, Any]:
    """Select an operational stage from persisted, accepted V3 observations."""
    row = (state.get("per_symbol") or {}).get(symbol, {})
    current_id = row.get("current_signal_id")
    bound = (row.get("physical_signal_id") == current_id and isinstance(current_id, str)
             and row.get("physical_closed_signal_id") != current_id
             and row.get("physical_history_policy") == HISTORY_POLICY
             and current_id.startswith("sig-v3-") and row.get("state") in {"WATCHLIST", "CONFIRMED"})
    if not bound or row.get("physical_pre_ts") is None:
        return {"physical_stage": "PRE", "decision_timeframe": "M1"}
    stage = "CONFIRM"
    if require_owner_receipts and owner_pre_ts is None:
        stage = "PRE"
    pre_ts = row["physical_pre_ts"]
    if owner_pre_ts is not None:
        pre_ts = max(pre_ts, owner_pre_ts)
    if (row.get("physical_confirm_ts") is not None and now_ts - pre_ts >= MIN_PRE_LEAD_SECONDS
        and (not require_owner_receipts or (owner_pre_ts is not None and owner_confirm_ts is not None))):
        stage = "OPEN_NOW"
    return {"physical_stage": stage, "opportunity_signal_id": current_id,
            "opportunity_direction": row.get("physical_direction"), "decision_timeframe": "M1"}


def decide(candles_m1, candles_m5, params, buffer_mode="MEDIUM", want_open_now=False,
           context=None, *, cycle_id=None, runtime_blockers=(), execution_calibration=None,
           observation_ts=None):
    del want_open_now
    if (params.get("algo_version") != STRATEGY_VERSION or "score_thresholds" in params
        or params.get("history_policy") != HISTORY_POLICY):
        raise ValueError("active V3 requires a validated scoreless parameter bundle")
    supplied = dict(context or {})
    resolved_cycle_id = str(cycle_id or supplied.get("cycle_id") or
                            f"{candles_m1[0].get('symbol', 'UNKNOWN')}:{candles_m1[0].get('ts', 0)}")
    market = evaluate_market(candles_m1, candles_m5, params, buffer_mode=buffer_mode,
                             observation_ts=observation_ts)
    corridor = evaluate_corridor(candles_m5, market, params)
    timing = evaluate_time(market, corridor, params)
    physical = evaluate_trade_physics(market, corridor, timing, include_scores=False)
    physical = replace(physical, formula_version="V3_PHYSICAL_ONLY_1.0.0",
                       schema_version="2.0.0", weights_version="NOT_APPLICABLE")
    blockers = []
    if market.context.volatility_state != "ACTIVE":
        blockers.append("MARKET_ACTIVITY_NOT_ACTIVE")
    if market.context.noise_context != "STABLE":
        blockers.append("MARKET_NOISE_UNSTABLE")
    if corridor.structure.feasibility_state != "VALID":
        blockers.append("STRUCTURE_NOT_VALID")
    if timing.context.time_state != "READY" or not timing.temporally_feasible:
        blockers.append("TIME_NOT_FEASIBLE")
    if not physical.ready:
        blockers.append(f"TRADE_PHYSICS_{physical.readiness_state}")
    elif physical.physically_constrained:
        blockers.append("TRADE_PHYSICS_INSUFFICIENT_SPACE")
    stage = supplied.get("physical_stage", "PRE")
    opportunity_id = supplied.get("opportunity_signal_id")
    if opportunity_id and supplied.get("opportunity_direction") != market.direction_bias:
        # Changing direction invalidates the existing opportunity; it cannot
        # inherit a prior PRE/CONFIRM or establish a new PRE while in focus.
        blockers.append("OPPORTUNITY_DIRECTION_CHANGED")
    eligibility = PhysicalEligibility(
        market.symbol, market.evaluated_ts,
        ScoreContext(None, None, FrozenInputs({}), penalties=FrozenInputs({}),
                     tier="PHYSICAL_BLOCKED" if blockers else "PHYSICAL_READY",
                     trade_physics=physical.to_context()),
        not blockers, tuple(blockers),
        "All physical gates pass." if not blockers else "Physical eligibility blocked: " + ", ".join(blockers),
        physical,
    )
    decision = assemble_decision(market, corridor, timing, eligibility,
        timeframe=supplied.get("decision_timeframe", "M1"), cycle_id=resolved_cycle_id,
        source="binary_strategy_v3", opportunity_signal_id=opportunity_id, physical_stage=stage)
    # A live observation clock is required for the new prospective policy.
    # Historical replay without that clock retains its original timing contract.
    if observation_ts is not None:
        from .confirmed_study_duration import annotate_decision
        decision = annotate_decision(decision, params)
    fsm = interpret_decision(decision, runtime_blockers=runtime_blockers)
    execution = derive_execution_time(decision, fsm, execution_calibration)
    return PhysicalV3Evaluation(STRATEGY_VERSION, CANONICAL_SPEC, decision.setup.cycle_id,
        market, corridor, timing, eligibility, physical, decision, fsm, execution)
