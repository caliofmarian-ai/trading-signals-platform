from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.market_model import evaluate_market
from core.sr_corridor_engine import evaluate_corridor
from core.time_model import evaluate_time


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int) -> list[dict]:
    chronological: list[dict] = []
    for index in range(count):
        wave = 0.0 if index == count - 1 else ((index % 20) - 10) * 0.00008
        base = 1.1000 + wave
        chronological.append(
            {
                "symbol": "EUR/USD",
                "timeframe": timeframe,
                "ts": 1_720_000_000 + index * step,
                "open": base,
                "high": base + 0.00035,
                "low": base - 0.00035,
                "close": base + 0.00002,
                "volume": 100 + index,
            }
        )
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
    return params, market, corridor


def _evaluate_at_adjusted_minutes(runtime_root: Path, adjusted_minutes: float):
    params, market, corridor = _inputs(runtime_root)
    trend_adjustment = float(params["trend_time_adjust"][market.context.trend_context])
    structure_adjustment = float(params["structure_factor"]["mult"])
    directional_speed = (
        market.context.buffer_distance * trend_adjustment * structure_adjustment / adjusted_minutes
    )
    controlled_market = replace(
        market,
        context=replace(
            market.context,
            directional_effective_speed=directional_speed,
        ),
    )
    result = evaluate_time(controlled_market, corridor, params)
    assert result.context.t_needed_adjusted == pytest.approx(adjusted_minutes)
    return result


def test_current_model_window_minute_boundary_is_explicitly_characterized(
    canonical_runtime_root: Path,
) -> None:
    """R-010 characterizes the existing v2 compatibility behavior without redefining canon."""

    below = _evaluate_at_adjusted_minutes(canonical_runtime_root, 4.999)
    exact = _evaluate_at_adjusted_minutes(canonical_runtime_root, 5.000)
    above = _evaluate_at_adjusted_minutes(canonical_runtime_root, 5.001)

    assert below.context.model_expiry == 5.0
    assert exact.context.model_expiry == 5.0
    assert above.context.model_expiry == 6.0

    assert below.context.model_time_reach_ratio == pytest.approx(4.999 / 5.0)
    assert exact.context.model_time_reach_ratio == pytest.approx(1.0)
    assert above.context.model_time_reach_ratio == pytest.approx(5.001 / 6.0)

    # The discontinuity is deliberately visible: a tiny increase in required
    # time currently creates a new integer internal window. R-010 does not
    # silently smooth this because no active canon defines a replacement
    # model-expiry derivation.
    assert above.context.model_time_reach_ratio < below.context.model_time_reach_ratio
    assert above.context.time_to_buffer_ratio > exact.context.time_to_buffer_ratio
    assert below.context.time_state == "READY"
    assert exact.context.time_state == "READY"
    assert above.context.time_state == "READY"


def test_maximum_model_window_boundary_fails_closed_without_extension(
    canonical_runtime_root: Path,
) -> None:
    params = _params(canonical_runtime_root)
    maximum = float(params["expiry_limits_minutes"]["max"])

    exact = _evaluate_at_adjusted_minutes(canonical_runtime_root, maximum)
    above = _evaluate_at_adjusted_minutes(canonical_runtime_root, maximum + 0.001)

    assert exact.context.model_expiry == maximum
    assert exact.context.model_time_reach_ratio == pytest.approx(1.0)
    assert exact.temporally_feasible is True
    assert exact.context.time_state == "READY"

    assert above.context.model_expiry == maximum
    assert above.context.model_time_reach_ratio > 1.0
    assert above.temporally_feasible is False
    assert above.context.time_state == "LATE"


def test_model_time_boundary_evidence_remains_internal_strategy_truth(
    canonical_runtime_root: Path,
) -> None:
    result = _evaluate_at_adjusted_minutes(canonical_runtime_root, 5.001)

    assert result.context.model_expiry == 6.0
    assert not hasattr(result.context, "expiry_minutes")
    assert not hasattr(result.context, "open_now_expiry_minutes")
    assert not hasattr(result, "execution_expiry")
