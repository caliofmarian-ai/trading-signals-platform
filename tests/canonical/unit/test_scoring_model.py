from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path

import pytest

from core.market_model import evaluate_market
from core.scoring_model import ScoringUnavailable, evaluate_score
from core.sr_corridor_engine import evaluate_corridor
from core.time_model import evaluate_time


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int) -> list[dict]:
    chronological = []
    for index in range(count):
        wave = 0.0 if index == count - 1 else ((index % 20) - 10) * 0.00008
        base = 1.1000 + wave
        chronological.append({
            "symbol": "EUR/USD", "timeframe": timeframe, "ts": 1_720_000_000 + index * step,
            "open": base, "high": base + 0.00035, "low": base - 0.00035,
            "close": base + 0.00002, "volume": 100 + index,
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
    return params, m1, m5, market, corridor, time


def test_scoring_exposes_all_established_components(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor, time = _inputs(canonical_runtime_root)
    result = evaluate_score(market, corridor, time, params)

    assert set(result.context.components) == {
        "context_trend", "momentum_rsi", "candle_body_expansion",
        "structure_corridor", "time_feasibility",
    }
    assert sum(result.evidence.component_maxima.values()) == 100
    assert result.context.total == pytest.approx(sum(result.context.components.values()))
    assert result.context.normalized == pytest.approx(result.context.total / 100)
    assert not hasattr(result, "signal")
    assert not hasattr(result, "fsm_state")


def test_high_arithmetic_score_cannot_hide_a_hard_blocker(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor, time = _inputs(canonical_runtime_root)
    unstable = replace(market, context=replace(market.context, noise_context="UNSTABLE"))
    result = evaluate_score(unstable, corridor, time, params)

    assert result.eligible is False
    assert result.context.tier == "BLOCKED"
    assert "MARKET_NOISE_UNSTABLE" in result.hard_blockers
    assert result.context.total >= 0


def test_structure_and_time_blockers_remain_explicit(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor, time = _inputs(canonical_runtime_root)
    blocked_corridor = replace(corridor, structure=replace(corridor.structure, feasibility_state="CONSTRAINED"))
    blocked_time = replace(time, context=replace(time.context, time_state="LATE"), temporally_feasible=False)
    result = evaluate_score(market, blocked_corridor, blocked_time, params)

    assert result.eligible is False
    assert "STRUCTURE_NOT_VALID" in result.hard_blockers
    assert "TIME_NOT_FEASIBLE" in result.hard_blockers


def test_tier_uses_versioned_thresholds_without_becoming_fsm(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor, time = _inputs(canonical_runtime_root)
    params["score_thresholds"] = {"PRE": 0, "CONFIRM": 0, "OPEN": 0}
    result = evaluate_score(market, corridor, time, params)

    assert result.eligible is True
    assert result.context.tier == "SCORE_OPEN_BAND"
    assert result.context.tier != "OPEN_NOW"


def test_mismatched_evidence_and_bad_thresholds_are_rejected(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor, time = _inputs(canonical_runtime_root)
    with pytest.raises(ScoringUnavailable, match="same evaluation"):
        evaluate_score(market, corridor, replace(time, evaluated_ts=time.evaluated_ts + 1), params)

    params["score_thresholds"] = {"PRE": 80, "CONFIRM": 70, "OPEN": 60}
    with pytest.raises(ScoringUnavailable, match="thresholds"):
        evaluate_score(market, corridor, time, params)


def test_missing_configuration_is_not_defaulted(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor, time = _inputs(canonical_runtime_root)
    del params["strategy_v2"]["rsi_call"]
    with pytest.raises(ScoringUnavailable, match="configuration is required"):
        evaluate_score(market, corridor, time, params)


def test_result_is_deterministic_and_deeply_immutable(canonical_runtime_root: Path) -> None:
    params, _, _, market, corridor, time = _inputs(canonical_runtime_root)
    first = evaluate_score(market, corridor, time, params)
    second = evaluate_score(market, corridor, time, params)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.eligible = False  # type: ignore[misc]
    with pytest.raises(TypeError):
        first.context.components["context_trend"] = 0  # type: ignore[index]
    assert dict(asdict(first.context)["components"]) == dict(first.context.components)
