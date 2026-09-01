from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.market_model import evaluate_market
from core.scoring_model import evaluate_score
from core.sr_corridor_engine import evaluate_corridor
from core.time_model import evaluate_time
from core.trade_physics import evaluate_trade_physics


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
    m1[0]["close"] = m1[0]["open"] + 0.00015
    for candle in m5:
        candle["high"], candle["low"] = 1.1015, 1.0985
    market = evaluate_market(m1, m5, params, buffer_mode="SMALL")
    corridor = evaluate_corridor(m5, market, params)
    time = evaluate_time(market, corridor, params)
    return params, market, corridor, time


def test_trade_physics_uses_active_deterministic_formula(canonical_runtime_root: Path) -> None:
    _, market, corridor, time = _inputs(canonical_runtime_root)
    result = evaluate_trade_physics(market, corridor, time)

    assert result.readiness_state == "READY"
    assert result.TPS is not None
    assert result.available_space == corridor.structure.available_distance
    assert result.required_space == market.context.buffer_distance
    assert result.space_to_buffer_ratio == pytest.approx(result.available_space / result.required_space)
    assert result.time_to_buffer_ratio == pytest.approx(time.context.model_expiry / time.context.t_needed_adjusted)
    assert result.atr_speed_reference == pytest.approx(market.evidence.atr_m5 / 5.0)
    assert result.directional_speed_ratio == pytest.approx(
        market.context.directional_effective_speed / result.atr_speed_reference
    )
    assert result.movement_stress == pytest.approx(result.required_space / market.evidence.atr_m5)
    assert result.S == pytest.approx(min(result.space_to_buffer_ratio, 3.0) / 3.0)
    assert result.T == pytest.approx(min(result.time_to_buffer_ratio, 2.0) / 2.0)
    assert result.P == pytest.approx(min(result.directional_speed_ratio, 2.0) / 2.0)
    assert result.V == pytest.approx(1.0 / (1.0 + result.movement_stress))
    assert result.TPS == pytest.approx(
        100.0 * (0.35 * result.S + 0.25 * result.T + 0.20 * result.P + 0.20 * result.V)
    )


def test_unstable_market_never_fabricates_tps(canonical_runtime_root: Path) -> None:
    _, market, corridor, time = _inputs(canonical_runtime_root)
    unstable = replace(market, context=replace(market.context, noise_context="UNSTABLE"))
    result = evaluate_trade_physics(unstable, corridor, time)

    assert result.readiness_state == "BLOCKED_UNSTABLE_MARKET"
    assert result.TPS is None
    assert result.interpretation_band is None


def test_missing_directional_speed_never_falls_back_to_gross_speed(canonical_runtime_root: Path) -> None:
    _, market, corridor, time = _inputs(canonical_runtime_root)
    no_directional_speed = replace(
        market,
        context=replace(
            market.context,
            price_speed=1.0,
            directional_effective_speed=0.0,
        ),
    )
    result = evaluate_trade_physics(no_directional_speed, corridor, time)

    assert result.readiness_state == "UNAVAILABLE_MISSING_SPEED"
    assert result.TPS is None


def test_scoring_keeps_classical_score_and_tps_as_separate_truths(canonical_runtime_root: Path) -> None:
    params, market, corridor, time = _inputs(canonical_runtime_root)
    scoring = evaluate_score(market, corridor, time, params)

    assert scoring.context.trade_physics is not None
    assert scoring.context.trade_physics.TPS == scoring.trade_physics.TPS
    assert scoring.context.total == pytest.approx(sum(scoring.context.components.values()))
    assert "TPS" not in scoring.context.components
