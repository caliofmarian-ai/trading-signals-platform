from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.market_model import evaluate_market
from core.sr_corridor_engine import evaluate_corridor
from core.time_model import TimeModelUnavailable, evaluate_time


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int) -> list[dict]:
    chronological = []
    for index in range(count):
        wave = 0.0 if index == count - 1 else ((index % 20) - 10) * 0.00008
        base = 1.1000 + wave
        chronological.append({
            "symbol": "EUR/USD",
            "timeframe": timeframe,
            "ts": 1_720_000_000 + index * step,
            "open": base,
            "high": base + 0.00035,
            "low": base - 0.00035,
            "close": base + 0.00002,
            "volume": 100 + index,
        })
    return list(reversed(chronological))


def _inputs(runtime_root: Path):
    params = _params(runtime_root)
    m1 = _candles(220, timeframe="M1", step=60)
    m5 = _candles(220, timeframe="M5", step=300)
    for candle in m5:
        candle["high"] = 1.1015
        candle["low"] = 1.0985
    market = evaluate_market(m1, m5, params, buffer_mode="SMALL")
    corridor = evaluate_corridor(m5, market, params)
    return params, m1, m5, market, corridor


def test_time_model_calculates_canonical_internal_metrics(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    result = evaluate_time(market, corridor, params)

    expected_raw = market.context.buffer_distance / market.context.price_speed
    expected_adjusted = (
        expected_raw
        * params["trend_time_adjust"][market.context.trend_context]
        * params["structure_factor"]["mult"]
    )
    assert result.context.t_needed == pytest.approx(expected_raw)
    assert result.context.t_needed_adjusted == pytest.approx(expected_adjusted)
    assert result.context.model_time_reach_ratio == pytest.approx(
        expected_adjusted / result.context.model_expiry
    )
    assert result.context.time_state in {"READY", "LATE"}


def test_corridor_pressure_remains_unavailable_without_calibrated_formula(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    result = evaluate_time(market, corridor, params)

    assert result.context.corridor_time_pressure is None
    assert not hasattr(result, "signal")
    assert not hasattr(result, "score")
    assert not hasattr(result, "execution_expiry")


def test_expiry_is_clamped_to_existing_versioned_limits(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    slow_context = replace(market.context, price_speed=0.000001)
    slow = evaluate_time(replace(market, context=slow_context), corridor, params)
    assert slow.context.model_expiry == params["expiry_limits_minutes"]["max"]
    assert slow.context.time_state == "LATE"
    assert slow.temporally_feasible is False

    fast_context = replace(market.context, price_speed=1.0)
    fast = evaluate_time(replace(market, context=fast_context), corridor, params)
    assert fast.context.model_expiry == params["expiry_limits_minutes"]["min"]
    assert fast.context.time_state == "READY"


def test_non_valid_corridor_blocks_time_instead_of_being_cosmetized(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    blocked_structure = replace(corridor.structure, feasibility_state="CONSTRAINED")
    result = evaluate_time(market, replace(corridor, structure=blocked_structure), params)

    assert result.context.time_state == "UNAVAILABLE"
    assert result.context.t_needed is None
    assert result.temporally_feasible is False
    assert "blocked" in result.explanation


def test_zero_observed_speed_is_explicitly_unavailable(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    stopped = replace(market, context=replace(market.context, price_speed=0.0))
    result = evaluate_time(stopped, corridor, params)

    assert result.context.time_state == "UNAVAILABLE"
    assert result.context.model_expiry is None
    assert result.context.model_time_reach_ratio is None


def test_mismatched_upstream_evidence_is_rejected(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    with pytest.raises(TimeModelUnavailable, match="same evaluation"):
        evaluate_time(market, replace(corridor, evaluated_ts=corridor.evaluated_ts + 1), params)


def test_missing_configuration_is_not_defaulted(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    del params["trend_time_adjust"][market.context.trend_context]
    with pytest.raises(TimeModelUnavailable, match="configuration is required"):
        evaluate_time(market, corridor, params)


def test_time_result_is_deterministic_and_immutable(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor = _inputs(canonical_runtime_root)
    first = evaluate_time(market, corridor, params)
    second = evaluate_time(market, corridor, params)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.temporally_feasible = False  # type: ignore[misc]


def test_matches_existing_strategy_time_math(canonical_runtime_root: Path) -> None:
    from core.strategy_v2 import decide

    params, m1, m5, market, corridor = _inputs(canonical_runtime_root)
    result = evaluate_time(market, corridor, params)
    legacy = decide(m1, m5, params, "SMALL", False, context={"decision_timeframe": "M1"})

    assert result.context.t_needed_adjusted == pytest.approx(legacy["debug"]["expiry"]["t_needed_adj"])
    assert result.context.model_expiry == pytest.approx(legacy["debug"]["expiry"]["selected"])
