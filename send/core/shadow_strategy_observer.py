"""Observe canonical-vs-live strategy results without changing live behavior."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Any, Mapping, Sequence

from . import storage
from .strategy_engine_v3 import CanonicalStrategyEvaluation, evaluate_canonical_strategy


SCHEMA_VERSION = "1.0.0"
DEFAULT_SNAPSHOT_PATH = storage.root_path("observability", "canonical_shadow_snapshot.json")


@dataclass(frozen=True)
class ShadowComparison:
    schema_version: str
    observed_ts: int
    symbol: str
    candle_ts: int
    cycle_id: str
    live_kind: str
    canonical_outcome: str
    live_direction: str
    canonical_direction: str
    live_score: float | None
    canonical_score: float
    live_expiry_minutes: float | None
    canonical_model_expiry_minutes: float | None
    direction_agrees: bool
    stage_agrees: bool
    score_difference: float | None
    canonical_execution_time_available: bool
    canonical_shadow_only: bool
    signal_handoff_ready: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _optional_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def _normalize_live_stage(value: Any) -> str:
    stage = str(value or "NO_SIGNAL").strip().upper()
    return {"NO_SIGNAL": "WAIT", "PRE": "PREPARE"}.get(stage, stage)


def compare_with_live_decision(
    canonical: CanonicalStrategyEvaluation,
    live_decision: Mapping[str, Any],
    *,
    observed_ts: int,
) -> ShadowComparison:
    if isinstance(observed_ts, bool) or not isinstance(observed_ts, int) or observed_ts <= 0:
        raise ValueError("observed_ts must be a positive integer")
    live_score = _optional_number(live_decision.get("score_total"))
    canonical_score = float(canonical.decision.score.total)
    live_direction = str(live_decision.get("direction") or "NONE").strip().upper()
    live_stage = _normalize_live_stage(live_decision.get("kind"))

    return ShadowComparison(
        schema_version=SCHEMA_VERSION,
        observed_ts=observed_ts,
        symbol=canonical.decision.setup.symbol,
        candle_ts=canonical.decision.setup.evaluated_ts,
        cycle_id=canonical.cycle_id,
        live_kind=str(live_decision.get("kind") or "NO_SIGNAL").strip().upper(),
        canonical_outcome=canonical.fsm.outcome,
        live_direction=live_direction,
        canonical_direction=canonical.decision.setup.direction,
        live_score=live_score,
        canonical_score=canonical_score,
        live_expiry_minutes=_optional_number(live_decision.get("expiry_minutes")),
        canonical_model_expiry_minutes=_optional_number(canonical.decision.time.model_expiry),
        direction_agrees=live_direction == canonical.decision.setup.direction,
        stage_agrees=live_stage == canonical.fsm.outcome,
        score_difference=None if live_score is None else canonical_score - live_score,
        canonical_execution_time_available=canonical.execution_time.available,
        canonical_shadow_only=canonical.shadow_only,
        signal_handoff_ready=False,
    )


def observe_and_persist(
    candles_m1: Sequence[Mapping[str, Any]],
    candles_m5: Sequence[Mapping[str, Any]],
    params: Mapping[str, Any],
    live_decision: Mapping[str, Any],
    *,
    observed_ts: int,
    buffer_mode: str,
    output_path: str = DEFAULT_SNAPSHOT_PATH,
) -> ShadowComparison:
    symbol = str(live_decision.get("symbol") or candles_m1[0].get("symbol") or "UNKNOWN")
    candle_ts = int(candles_m1[0]["ts"])
    cycle_id = f"shadow:{symbol}:{candle_ts}:{observed_ts}"
    canonical = evaluate_canonical_strategy(
        candles_m1,
        candles_m5,
        params,
        cycle_id=cycle_id,
        timeframe="M1",
        buffer_mode=buffer_mode,
    )
    comparison = compare_with_live_decision(canonical, live_decision, observed_ts=observed_ts)
    storage.save_json_atomic(output_path, comparison.to_dict())
    return comparison
