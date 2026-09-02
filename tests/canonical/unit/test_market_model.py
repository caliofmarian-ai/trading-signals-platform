from __future__ import annotations

import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.market_model import MarketModelUnavailable, evaluate_market


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int, rising: bool = True) -> list[dict]:
    chronological = []
    for index in range(count):
        movement = index * 0.00003 * (1 if rising else -1)
        base = 1.10000 + movement
        chronological.append({
            "symbol": "EUR/USD",
            "timeframe": timeframe,
            "ts": 1_720_000_000 + index * step,
            "open": base,
            "high": base + 0.00020,
            "low": base - 0.00010,
            "close": base + 0.00010,
            "volume": 100 + index,
        })
    return list(reversed(chronological))


def test_market_model_describes_evidence_without_emitting_a_signal(canonical_runtime_root: Path) -> None:
    result = evaluate_market(
        _candles(220, timeframe="M1", step=60),
        _candles(220, timeframe="M5", step=300),
        _params(canonical_runtime_root),
    )

    assert result.schema_version == "2.0.0"
    assert result.symbol == "EUR/USD"
    assert result.direction_bias == "BUY"
    assert result.context.trend_context == "WITH_TREND"
    assert result.context.price_speed > 0
    assert result.context.directional_effective_speed is not None
    assert result.context.directional_effective_speed > 0
    assert result.context.weighted_gross_speed is not None
    assert result.context.weighted_gross_speed >= result.context.directional_effective_speed
    assert result.context.flow_efficiency == pytest.approx(
        result.context.directional_effective_speed / result.context.weighted_gross_speed
    )
    assert 0 <= result.context.flow_efficiency <= 1
    assert result.context.buffer_distance > 0
    assert result.context.target_distance is None
    assert not hasattr(result, "signal")
    assert not hasattr(result, "score")


def test_directional_speed_uses_only_intended_direction_with_recency_weights(canonical_runtime_root: Path) -> None:
    params = _params(canonical_runtime_root)
    m1 = _candles(220, timeframe="M1", step=60, rising=True)
    m5 = _candles(220, timeframe="M5", step=300, rising=True)
    result = evaluate_market(m1, m5, params)

    assert result.direction_bias == "BUY"
    assert result.context.directional_effective_speed == pytest.approx(0.00003)
    assert result.context.weighted_gross_speed == pytest.approx(0.00003)
    assert result.context.flow_efficiency == pytest.approx(1.0)


def test_result_is_deterministic_immutable_and_preserves_inputs(canonical_runtime_root: Path) -> None:
    m1 = _candles(220, timeframe="M1", step=60)
    m5 = _candles(220, timeframe="M5", step=300)
    before = copy.deepcopy((m1, m5))
    first = evaluate_market(m1, m5, _params(canonical_runtime_root))
    second = evaluate_market(m1, m5, _params(canonical_runtime_root))

    assert first == second
    assert (m1, m5) == before
    with pytest.raises(FrozenInstanceError):
        first.direction_bias = "SELL"  # type: ignore[misc]


def test_buffer_distance_uses_selected_versioned_multiplier(canonical_runtime_root: Path) -> None:
    params = _params(canonical_runtime_root)
    m1 = _candles(220, timeframe="M1", step=60)
    m5 = _candles(220, timeframe="M5", step=300)
    small = evaluate_market(m1, m5, params, buffer_mode="SMALL")
    large = evaluate_market(m1, m5, params, buffer_mode="LARGE")

    assert small.context.buffer_distance == pytest.approx(small.evidence.atr_m5 * params["buffer_multipliers"]["SMALL"])
    assert large.context.buffer_distance == pytest.approx(large.evidence.atr_m5 * params["buffer_multipliers"]["LARGE"])
    assert large.context.buffer_distance > small.context.buffer_distance


def test_partial_real_history_is_rejected_instead_of_fabricated(canonical_runtime_root: Path) -> None:
    with pytest.raises(MarketModelUnavailable, match="requires 201 real candles"):
        evaluate_market(
            _candles(220, timeframe="M1", step=60),
            _candles(200, timeframe="M5", step=300),
            _params(canonical_runtime_root),
        )


def test_wrong_order_duplicate_and_invalid_ohlc_are_rejected(canonical_runtime_root: Path) -> None:
    params = _params(canonical_runtime_root)
    m1 = _candles(220, timeframe="M1", step=60)
    m5 = _candles(220, timeframe="M5", step=300)
    with pytest.raises(MarketModelUnavailable, match="newest-first"):
        evaluate_market(list(reversed(m1)), m5, params)

    duplicate = copy.deepcopy(m1)
    duplicate[5]["ts"] = duplicate[4]["ts"]
    with pytest.raises(MarketModelUnavailable, match="newest-first"):
        evaluate_market(duplicate, m5, params)

    invalid = copy.deepcopy(m1)
    invalid[0]["high"] = invalid[0]["low"] - 1
    with pytest.raises(MarketModelUnavailable, match="OHLC"):
        evaluate_market(invalid, m5, params)


def test_recent_m1_gap_blocks_directional_speed_instead_of_compressing_time(canonical_runtime_root: Path) -> None:
    params = _params(canonical_runtime_root)
    m1 = _candles(220, timeframe="M1", step=60)
    m5 = _candles(220, timeframe="M5", step=300)
    del m1[10]

    with pytest.raises(MarketModelUnavailable, match=r"contiguous real candles at 60s cadence"):
        evaluate_market(m1, m5, params)


def test_recent_m5_gap_blocks_atr_and_time_evidence_instead_of_compressing_time(canonical_runtime_root: Path) -> None:
    params = _params(canonical_runtime_root)
    m1 = _candles(220, timeframe="M1", step=60)
    m5 = _candles(220, timeframe="M5", step=300)
    del m5[100]

    with pytest.raises(MarketModelUnavailable, match=r"contiguous real candles at 300s cadence"):
        evaluate_market(m1, m5, params)


def test_older_gap_is_excluded_when_newest_segment_alone_satisfies_required_history(canonical_runtime_root: Path) -> None:
    params = _params(canonical_runtime_root)
    m1 = _candles(230, timeframe="M1", step=60)
    m5 = _candles(230, timeframe="M5", step=300)
    expected = evaluate_market(m1, m5[:210], params)

    gapped_m5 = copy.deepcopy(m5)
    del gapped_m5[210]
    actual = evaluate_market(m1, gapped_m5, params)

    assert actual == expected


def test_missing_operational_parameter_is_rejected_not_defaulted(canonical_runtime_root: Path) -> None:
    params = _params(canonical_runtime_root)
    del params["buffer_multipliers"]["MEDIUM"]
    with pytest.raises(MarketModelUnavailable, match="MEDIUM configuration is required"):
        evaluate_market(
            _candles(220, timeframe="M1", step=60),
            _candles(220, timeframe="M5", step=300),
            params,
        )


def test_spike_evidence_marks_noise_unstable(canonical_runtime_root: Path) -> None:
    m1 = _candles(220, timeframe="M1", step=60)
    m5 = _candles(220, timeframe="M5", step=300)
    m1[0].update(open=1.1000, close=1.100001, high=1.1100, low=1.0900)
    result = evaluate_market(m1, m5, _params(canonical_runtime_root))

    assert result.context.noise_context == "UNSTABLE"
    assert "WICK_BODY_RATIO" in result.noise_reasons
