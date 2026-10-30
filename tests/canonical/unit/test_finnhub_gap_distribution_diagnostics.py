"""P0 real-Finnhub history gap attribution, with offline timestamp-only fixtures."""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone

import pytest

from runtime.market_history_integrity import summarize_gap_distribution


def _bar(ts: int, timeframe: str, price: float = 1.12345) -> dict:
    return {
        "symbol": "EUR/USD",
        "timeframe": timeframe,
        "ts": ts,
        "open": price,
        "high": price,
        "low": price,
        "close": price,
        "volume": 0,
        "complete": True,
        "provider": "FINNHUB",
    }


def test_isolated_recent_gap_differs_from_sparse_intraday_m1():
    # Raw count 500, M1 head 3, but historical M1 longest run 497:
    # the data cannot establish *why* without a session/event cross-check.
    t = 1793390400  # exact minute and 5-minute boundary
    m1 = [_bar(t - i * 60, "M1") for i in range(3)]
    m1 += [_bar(t - (i + 5) * 60, "M1") for i in range(497)]
    m5 = [_bar(t - i * 300, "M5") for i in range(500)]
    data = summarize_gap_distribution({"M1": m1, "M5": m5})
    a, b = data["timeframes"]["M1"], data["timeframes"]["M5"]
    assert a["sample_bounded_rows"] == 500
    assert a["head_contiguous_count"] == 3
    assert a["longest_contiguous_run"] == 497
    assert a["gap_count"] == 1
    assert a["non_weekend_gap_count"] == 1
    assert a["total_non_weekend_missing_intervals"] == 2
    assert a["gap_size_histogram"]["two_to_four"] == 1
    assert b["head_contiguous_count"] == 500
    assert b["gap_count"] == 0
    serialized = json.dumps(data)
    assert "1.12345" not in serialized
    assert data["no_price_or_signal_content"] is True
    assert data["no_market_session_inference"] is True


def test_sparse_m1_minutes_identified_without_synthesizing_bars():
    t = 1793390400
    sparse = [_bar(t - i * 180, "M1") for i in range(8)]
    dense = [_bar(t - i * 300, "M5") for i in range(8)]
    original_ts = [row["ts"] for row in sparse]
    summary = summarize_gap_distribution({"M1": sparse, "M5": dense})
    a = summary["timeframes"]["M1"]
    assert a["sample_bounded_rows"] == 8
    assert a["head_contiguous_count"] == 1
    assert a["longest_contiguous_run"] == 1
    assert a["gap_count"] == 7
    assert a["total_non_weekend_missing_intervals"] == 14
    assert a["gap_size_histogram"] == {
        "one": 0, "two_to_four": 7, "five_to_29": 0, "30_plus": 0
    }
    assert [row["ts"] for row in sparse] == original_ts


def test_weekend_gap_separate_from_nonweekend_gap():
    fri = int(datetime(2026, 10, 30, 20, 55, tzinfo=timezone.utc).timestamp())
    sun = int(datetime(2026, 11, 1, 22, 5, tzinfo=timezone.utc).timestamp())
    summary = summarize_gap_distribution({
        "M1": [_bar(sun, "M1"), _bar(fri, "M1")],
        "M5": [_bar(sun, "M5"), _bar(fri, "M5")],
    })
    for code in ("M1", "M5"):
        a = summary["timeframes"][code]
        assert a["weekend_gap_count"] == 1
        assert a["non_weekend_gap_count"] == 0
        assert a["head_contiguous_count"] == 1
        assert a["longest_contiguous_run"] == 1


def test_untrusted_invalid_data_is_not_approved_by_gap_diagnostic():
    rows = [_bar(600, "M1"), _bar(540, "M1")]
    rows[0]["open"] = -1
    summary = summarize_gap_distribution({"M1": rows, "M5": []})
    a = summary["timeframes"]["M1"]
    assert a["source_integrity_state"] == "INVALID"
    assert a["longest_contiguous_run"] is None
    assert a["newest_candle_ts"] is None


def test_cap_and_invalid_limit_explicit():
    data = {
        "M1": [_bar(600 - 60 * i, "M1") for i in range(6)],
        "M5": [_bar(600 - 300 * i, "M5") for i in range(6)],
    }
    result = summarize_gap_distribution(data, max_rows_per_timeframe=3)
    assert result["timeframes"]["M1"]["sample_bounded_rows"] == 3
    assert result["timeframes"]["M1"]["sample_truncated"] is True
    for limit in (0, 501, True, "50"):
        with pytest.raises(ValueError):
            summarize_gap_distribution(data, max_rows_per_timeframe=limit)


def test_railway_notice_includes_gap_summary_without_prices_or_keys(tmp_path, capsys):
    mod = importlib.import_module("runtime.finnhub_market_data")
    feed = mod.FinnhubForexFeed(
        token="SENSITIVE-API-KEY",
        store_path=tmp_path / "market.json",
        clock=lambda: 1793390400,
        minimum_candles=2,
    )
    t = 1793390400
    feed._candles = {
        "M1": [_bar(t, "M1"), _bar(t - 60, "M1"), _bar(t - 180, "M1")],
        "M5": [_bar(t, "M5"), _bar(t - 300, "M5")],
    }
    feed._emit_stream_observation("SUBSCRIBE_SENT_UNVERIFIED")
    output = capsys.readouterr().out
    assert output.count("TSP_FINNHUB_STREAM_EVIDENCE ") == 1
    payload = json.loads(output.split(" ", 1)[1])
    a = payload["history_gap_diagnostics"]["timeframes"]["M1"]
    assert a["head_contiguous_count"] == 2
    assert a["longest_contiguous_run"] == 2
    assert a["gap_count"] == 1
    assert payload["valid_trade_tick_count"] == 0
    assert payload["usable_real_history_and_fresh_tick"] is False
    assert "SENSITIVE-API-KEY" not in output
    assert "1.12345" not in output
