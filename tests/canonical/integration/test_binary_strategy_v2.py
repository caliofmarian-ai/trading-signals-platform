from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.execution_model import ExecutionCalibration
from core.strategy_v2 import CANONICAL_SPEC, STRATEGY_VERSION, decide


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int) -> list[dict]:
    candles = []
    for index in range(count):
        wave = 0.0 if index == count - 1 else ((index % 20) - 10) * 0.00008
        base = 1.1000 + wave
        candles.append({
            "symbol": "EUR/USD", "timeframe": timeframe, "ts": 1_720_000_000 + index * step,
            "open": base, "high": base + 0.00035, "low": base - 0.00035,
            "close": base + 0.00002, "volume": 100 + index,
        })
    return list(reversed(candles))


def _inputs(runtime_root: Path):
    m1 = _candles(220, timeframe="M1", step=60)
    m1[0]["close"] = m1[0]["open"] + 0.00015
    m5 = _candles(220, timeframe="M5", step=300)
    for candle in m5:
        candle["high"], candle["low"] = 1.1015, 1.0985
    return m1, m5, _params(runtime_root)


def test_v2_pipeline_preserves_one_real_evaluation(canonical_runtime_root: Path) -> None:
    m1, m5, params = _inputs(canonical_runtime_root)
    result = decide(m1, m5, params, cycle_id="cycle-full", buffer_mode="SMALL")

    identity = (result.market.symbol, result.market.evaluated_ts)
    assert (result.corridor.symbol, result.corridor.evaluated_ts) == identity
    assert (result.time.symbol, result.time.evaluated_ts) == identity
    assert (result.scoring.symbol, result.scoring.evaluated_ts) == identity
    assert (result.trade_physics.symbol, result.trade_physics.evaluated_ts) == identity
    assert result.decision.setup.cycle_id == "cycle-full"
    assert result.decision.setup.source == "binary_strategy_v2"
    assert result.decision.compatibility_mode is False
    assert result.decision.kind in {"NO_SIGNAL", "PRE", "CONFIRM", "OPEN_NOW", "REJECT"}
    assert result.strategy_version == STRATEGY_VERSION == "2.0.0"
    assert result.canonical_spec == CANONICAL_SPEC == "ALGO_SPEC_v3.0.0"
    assert result.signal_handoff_ready is False


def test_v2_pipeline_is_deterministic_and_immutable(canonical_runtime_root: Path) -> None:
    m1, m5, params = _inputs(canonical_runtime_root)
    first = decide(m1, m5, params, cycle_id="cycle-repeat", buffer_mode="SMALL")
    second = decide(m1, m5, params, cycle_id="cycle-repeat", buffer_mode="SMALL")
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.signal_handoff_ready = True


def test_runtime_blocker_stops_even_a_complete_v2_pipeline(canonical_runtime_root: Path) -> None:
    m1, m5, params = _inputs(canonical_runtime_root)
    result = decide(
        m1, m5, params, cycle_id="cycle-blocked", buffer_mode="SMALL",
        runtime_blockers=("market_data_stale",),
    )
    assert result.fsm.outcome == "BLOCKED"
    assert result.execution_time.available is False
    assert result.signal_handoff_ready is False


def test_calibration_cannot_bypass_v2_signal_contract(canonical_runtime_root: Path) -> None:
    m1, m5, params = _inputs(canonical_runtime_root)
    # Zero pressure bias keeps the downstream execution candidate inside the
    # canonical CONFIRM interval for any valid clamped model_expiry. The point
    # of this test is the handoff boundary, not calibration quality.
    calibration = ExecutionCalibration(1.0, 0.0, 2.0, 15.0, "integration-test")
    result = decide(
        m1, m5, params, cycle_id="cycle-calibrated", buffer_mode="SMALL",
        execution_calibration=calibration,
    )
    assert result.signal_handoff_ready is False
    assert result.execution_time.signal_handoff_ready is False
