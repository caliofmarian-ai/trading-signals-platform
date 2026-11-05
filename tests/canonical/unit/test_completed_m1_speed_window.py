"""Closed-interval regressions, using offline candles and no external services."""

from __future__ import annotations

import copy
import json

import pytest


NOW = 1_800_000_002


def _rows(count, step=60, *, flags=True):
    rows = []
    for i in range(count):
        close = 1.12 - i * 0.00003
        row = {"ts": 1_800_000_000 - i * step, "symbol": "EUR/USD",
               "timeframe": "M1" if step == 60 else "M5",
               "open": close - 0.00001, "close": close,
               "high": close + 0.0002, "low": close - 0.0001}
        if flags:
            row["complete"] = i > 0
        rows.append(row)
    return rows


def _params(root):
    return json.loads((root / "config" / "algo_params.json").read_text())


def test_adapter_preserves_closure_evidence_and_inputs():
    from core.candle_adapter import normalize, validate

    rows = _rows(22)
    before = copy.deepcopy(rows)
    normalized = normalize(rows, "EUR/USD", "M1")
    validate(normalized)
    assert [row["complete"] for row in normalized] == [False] + [True] * 21
    assert rows == before
    assert "complete" not in normalize(_rows(1, flags=False), "EUR/USD", "M1")[0]


@pytest.mark.parametrize("flag", ["false", "true", 0, 1, None])
def test_adapter_rejects_malformed_closure_instead_of_coercing(flag):
    from core.candle_adapter import normalize

    rows = _rows(22)
    rows[0]["complete"] = flag
    with pytest.raises(ValueError, match="complete must be boolean"):
        normalize(rows, "EUR/USD", "M1")


def test_forming_quote_cannot_change_closed_interval_speed(canonical_runtime_root):
    from core.candle_adapter import normalize
    from core.market_model import evaluate_market

    m1, m5 = _rows(22), _rows(201, 300)
    closed_before = copy.deepcopy(m1[1:])
    params = _params(canonical_runtime_root)
    first = evaluate_market(normalize(m1, "EUR/USD", "M1"), m5, params, observation_ts=NOW)
    m1[0]["close"] += 0.002
    m1[0]["high"] = m1[0]["close"] + 0.0001
    second = evaluate_market(normalize(m1, "EUR/USD", "M1"), m5, params, observation_ts=NOW)
    assert first.direction_bias == second.direction_bias == "BUY"
    assert m1[1:] == closed_before
    for field in ("price_speed", "directional_effective_speed", "weighted_gross_speed", "flow_efficiency"):
        assert getattr(first.context, field) == getattr(second.context, field)
    assert second.context.latest_price == m1[0]["close"]
    assert second.context.directional_effective_speed == pytest.approx(0.00003)
    window = second.evidence.m1_speed_window
    assert window.completed_candles == 21
    assert window.completed_intervals == 20
    assert window.first_open_ts == m1[21]["ts"]
    assert window.last_close_ts == m1[0]["ts"]
    assert window.last_close_ts - window.first_close_ts == 20 * 60
    assert window.completion_source == "PROVIDER_FLAGS_AND_OBSERVATION_TIME"


@pytest.mark.parametrize("flags", [True, False])
def test_21_raw_bars_with_forming_head_are_insufficient(canonical_runtime_root, flags):
    from core.market_model import MarketModelUnavailable, evaluate_market

    with pytest.raises(MarketModelUnavailable, match="21 completed real candles.*received 20"):
        evaluate_market(_rows(21, flags=flags), _rows(201, 300),
                        _params(canonical_runtime_root), observation_ts=NOW)


def test_21_already_closed_bars_need_no_extra_bar(canonical_runtime_root):
    from core.market_model import evaluate_market

    m1 = _rows(22)[1:]
    result = evaluate_market(m1, _rows(201, 300), _params(canonical_runtime_root), observation_ts=NOW)
    assert result.evidence.m1_speed_window.completed_intervals == 20


def test_timestamp_proof_for_provider_without_completion_flags(canonical_runtime_root):
    from core.market_model import evaluate_market

    result = evaluate_market(_rows(22, flags=False), _rows(201, 300),
                             _params(canonical_runtime_root), observation_ts=NOW)
    assert result.evidence.m1_speed_window.last_close_ts == 1_800_000_000
    assert result.evidence.m1_speed_window.completion_source == "OBSERVATION_TIME"


@pytest.mark.parametrize("observed", [1_799_999_999, 1_800_000_000, 1_800_000_059])
def test_a_flag_cannot_close_a_future_interval(canonical_runtime_root, observed):
    from core.market_model import MarketModelUnavailable, evaluate_market

    m1 = _rows(22)
    m1[0]["complete"] = True
    with pytest.raises(MarketModelUnavailable, match="after observation_ts|before its interval ended"):
        evaluate_market(m1, _rows(201, 300), _params(canonical_runtime_root), observation_ts=observed)


def test_exact_close_boundary_allows_the_completed_bar(canonical_runtime_root):
    from core.market_model import evaluate_market

    m1 = _rows(21)
    m1[0]["complete"] = True
    result = evaluate_market(m1, _rows(201, 300), _params(canonical_runtime_root),
                             observation_ts=1_800_000_060)
    assert result.evidence.m1_speed_window.last_close_ts == 1_800_000_060


@pytest.mark.parametrize("index", [1, 10, 21])
def test_unfinished_historical_bar_cannot_be_replaced_by_older_data(canonical_runtime_root, index):
    from core.market_model import MarketModelUnavailable, evaluate_market

    m1 = _rows(60)
    m1[index]["complete"] = False
    with pytest.raises(MarketModelUnavailable, match="unfinished historical interval"):
        evaluate_market(m1, _rows(201, 300), _params(canonical_runtime_root), observation_ts=NOW)


def test_gap_in_last_closed_endpoint_is_not_hidden(canonical_runtime_root):
    from core.market_model import MarketModelUnavailable, evaluate_market

    m1 = _rows(60)
    del m1[21]
    with pytest.raises(MarketModelUnavailable, match="21 completed real candles.*received 20"):
        evaluate_market(m1, _rows(201, 300), _params(canonical_runtime_root), observation_ts=NOW)


@pytest.mark.parametrize("observed", [True, 0, -1, float("nan"), float("inf"), "bad"])
def test_invalid_observation_clock_is_rejected(canonical_runtime_root, observed):
    from core.market_model import MarketModelUnavailable, evaluate_market

    with pytest.raises(MarketModelUnavailable, match="positive finite timestamp"):
        evaluate_market(_rows(22), _rows(201, 300), _params(canonical_runtime_root), observation_ts=observed)


@pytest.mark.parametrize("direction", ["BUY", "SELL"])
def test_closed_window_preserves_exact_20_recency_weights(canonical_runtime_root, direction):
    from core.market_model import _completed_m1_speed_window, _directional_movement

    m1 = _rows(22)
    chronological = list(reversed(m1[1:]))
    deltas = [(i if i % 3 else -i) * 0.000001 for i in range(1, 21)]
    for i, delta in enumerate(deltas, 1):
        chronological[i]["close"] = chronological[i - 1]["close"] + delta
    window, evidence = _completed_m1_speed_window(m1, NOW)
    closes = [row["close"] for row in reversed(window)]
    directional, gross, efficiency = _directional_movement(closes, direction)
    signed = 1 if direction == "BUY" else -1
    assert directional == pytest.approx(sum(i * max(signed * d, 0) for i, d in enumerate(deltas, 1)) / 210)
    assert gross == pytest.approx(sum(i * abs(d) for i, d in enumerate(deltas, 1)) / 210)
    assert efficiency == pytest.approx(directional / gross)
    assert evidence.completed_intervals == 20


def test_strategy_propagates_clock_and_runtime_evidence_is_bounded(canonical_runtime_root, capsys):
    from core import signal_engine
    from core.strategy_v2 import decide

    result = decide(_rows(22, flags=False), _rows(201, 300),
                    _params(canonical_runtime_root), observation_ts=NOW)
    assert result.market.evidence.m1_speed_window.observation_ts == NOW
    signal_engine._LAST_M1_SPEED_EVIDENCE_TS.clear()
    signal_engine._emit_m1_speed_window_evidence(result)
    signal_engine._emit_m1_speed_window_evidence(result)
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 1
    marker, payload = lines[0].split(" ", 1)
    data = json.loads(payload)
    assert marker == "TSP_M1_COMPLETED_SPEED_EVIDENCE"
    assert data["window"]["completed_intervals"] == 20
    assert data["forming_candle_included"] is False
    assert data["no_prices_scores_or_trade_recommendations"] is True
    assert "latest_price" not in payload and "decision_id" not in payload
