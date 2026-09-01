from __future__ import annotations

import copy
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.market_model import evaluate_market
from core.sr_corridor_engine import CorridorUnavailable, evaluate_corridor


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int, latest_price: float = 1.1000) -> list[dict]:
    chronological = []
    for index in range(count):
        wave = ((index % 20) - 10) * 0.00008
        base = latest_price + wave
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
    market = evaluate_market(m1, m5, params)
    return params, m1, m5, market


def test_corridor_produces_structural_truth_only(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    result = evaluate_corridor(m5, market, params)

    assert result.schema_version == "1.0.0"
    assert result.structure.support < market.context.latest_price < result.structure.resistance
    assert result.structure.corridor_width == pytest.approx(result.structure.resistance - result.structure.support)
    assert result.structure.position == "INTERIOR"
    assert result.structure.feasibility_state in {"VALID", "CONSTRAINED"}
    assert not hasattr(result, "score")
    assert not hasattr(result, "signal")
    assert not hasattr(result, "expiry")


def test_direction_selects_the_relevant_available_distance(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    buy = evaluate_corridor(m5, replace(market, direction_bias="BUY"), params)
    sell = evaluate_corridor(m5, replace(market, direction_bias="SELL"), params)

    assert buy.structure.available_distance == pytest.approx(buy.evidence.distance_to_resistance)
    assert sell.structure.available_distance == pytest.approx(sell.evidence.distance_to_support)


def test_current_wick_is_not_misclassified_as_a_structural_barrier(
    canonical_runtime_root: Path,
) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    price = market.context.latest_price
    # A raw wick immediately above price is not a confirmed swing.  The prior
    # confirmed M5 pivot must remain the relevant resistance.
    m5[0]["open"] = price
    m5[0]["close"] = price
    m5[0]["high"] = price + 0.000005
    m5[0]["low"] = price - 0.000005

    result = evaluate_corridor(m5, replace(market, direction_bias="BUY"), params)

    assert result.structure.resistance != pytest.approx(price + 0.000005)
    assert result.structure.available_distance > 0.000005


def test_required_room_comes_from_buffer_and_versioned_multiplier(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    result = evaluate_corridor(m5, market, params)

    assert result.evidence.required_distance == pytest.approx(
        market.context.buffer_distance * params["sr_required_multiplier"]
    )
    assert result.evidence.room_ratio == pytest.approx(
        result.structure.available_distance / result.evidence.required_distance
    )


def test_numerically_equal_room_is_not_falsely_constrained(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    required = market.context.buffer_distance * params["sr_required_multiplier"]
    resistance = market.context.latest_price + required - 1e-16
    for candle in m5:
        candle["open"] = market.context.latest_price
        candle["close"] = market.context.latest_price
        candle["high"] = resistance
        candle["low"] = market.context.latest_price - required
    result = evaluate_corridor(m5, replace(market, direction_bias="BUY"), params)

    assert result.structure.feasibility_state == "VALID"
    assert "INSUFFICIENT_DIRECTIONAL_ROOM" not in result.structure.conflicts


def test_insufficient_directional_room_is_explicit(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    enlarged_context = replace(market.context, buffer_distance=0.01)
    constrained = evaluate_corridor(m5, replace(market, context=enlarged_context, direction_bias="BUY"), params)

    assert constrained.structure.feasibility_state == "CONSTRAINED"
    assert "INSUFFICIENT_DIRECTIONAL_ROOM" in constrained.structure.conflicts
    assert "too close to resistance" in constrained.structure.explanation


def test_missing_boundary_is_unavailable_not_infinite(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    above_all = replace(market.context, latest_price=max(c["high"] for c in m5) + 0.01)
    result = evaluate_corridor(m5, replace(market, context=above_all, direction_bias="BUY"), params)

    assert result.structure.resistance is None
    assert result.structure.available_distance is None
    assert result.evidence.room_ratio is None
    assert result.structure.feasibility_state == "UNAVAILABLE"
    assert "RESISTANCE_UNAVAILABLE" in result.structure.conflicts


def test_invalid_or_partial_evidence_is_rejected(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    with pytest.raises(CorridorUnavailable, match="requires 80 real candles"):
        evaluate_corridor(m5[:79], market, params)
    with pytest.raises(CorridorUnavailable, match="newest-first"):
        evaluate_corridor(list(reversed(m5)), market, params)

    invalid = copy.deepcopy(m5)
    invalid[0]["low"] = invalid[0]["high"] + 1
    with pytest.raises(CorridorUnavailable, match="OHLC"):
        evaluate_corridor(invalid, market, params)


def test_missing_sr_parameter_is_not_defaulted(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    del params["sr_required_multiplier"]
    with pytest.raises(CorridorUnavailable, match="sr_required_multiplier configuration is required"):
        evaluate_corridor(m5, market, params)


def test_corridor_is_deterministic_immutable_and_preserves_inputs(canonical_runtime_root: Path) -> None:
    params, _, m5, market = _inputs(canonical_runtime_root)
    before = copy.deepcopy(m5)
    first = evaluate_corridor(m5, market, params)
    second = evaluate_corridor(m5, market, params)

    assert first == second
    assert m5 == before
    with pytest.raises(FrozenInstanceError):
        first.direction = "SELL"  # type: ignore[misc]
