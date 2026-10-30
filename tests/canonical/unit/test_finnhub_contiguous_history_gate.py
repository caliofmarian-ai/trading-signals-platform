"""P0: Only consecutive real M1/M5 bars may enter strategy calculations.

Weekend and missing-tick gaps remain explicit provider evidence, never
filled by interpolation or silently treated as regular 1/5-minute movement.
These are isolated offline fixtures, not proof of production ticks.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone

import pytest


def _bar(ts: int, timeframe: str):
    return {
        "symbol": "EUR/USD",
        "timeframe": timeframe,
        "ts": ts,
        "open": 1.11,
        "high": 1.12,
        "low": 1.10,
        "close": 1.11,
        "volume": 0,
        "complete": True,
        "provider": "FINNHUB",
    }


def _feed(tmp_path, *, minimum=2, now=602):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(
        token="offline",
        store_path=tmp_path / "market.json",
        minimum_candles=minimum,
        clock=lambda: now,
    )
    feed._stream_started = True
    return module, feed


def test_stored_count_does_not_overrule_missing_m1_interval(tmp_path):
    module, feed = _feed(tmp_path)
    feed._last_price_ts = 600
    feed._candles = {
        "M1": [_bar(600, "M1"), _bar(480, "M1")],
        "M5": [_bar(600, "M5"), _bar(300, "M5")],
    }
    health = feed.health()
    assert health["candle_counts"] == {"M1": 2, "M5": 2}
    assert health["contiguous_candle_counts"] == {"M1": 1, "M5": 2}
    assert health["integrity_state"] == "VALID"
    assert health["integrity_report"]["temporal_continuity_state"] == "GAPPED"
    assert health["history_ready"] is False

    with pytest.raises(module.FinnhubInsufficientHistory, match=r"1/2 real candles contiguous"):
        feed.get_candles("EUR/USD", "M1")


def test_trailing_disjoint_bars_do_not_enter_decision_input(tmp_path):
    _, feed = _feed(tmp_path)
    feed._last_price_ts = 600
    feed._candles = {
        "M1": [_bar(600, "M1"), _bar(540, "M1"), _bar(420, "M1")],
        "M5": [_bar(600, "M5"), _bar(300, "M5")],
    }
    assert feed.health()["history_ready"] is True
    real_current_segment = feed.get_candles("EURUSD", "1min")
    assert [bar["ts"] for bar in real_current_segment] == [600, 540]
    assert 420 not in [bar["ts"] for bar in real_current_segment]


def test_weekend_gap_requires_new_contiguous_m5_segment(tmp_path):
    friday = int(datetime(2026, 10, 30, 20, 55, tzinfo=timezone.utc).timestamp())
    sunday = int(datetime(2026, 11, 1, 22, 5, tzinfo=timezone.utc).timestamp())
    module, feed = _feed(tmp_path, now=sunday + 2)
    feed._last_price_ts = sunday
    feed._candles = {
        "M1": [_bar(sunday, "M1"), _bar(sunday - 60, "M1")],
        "M5": [_bar(sunday, "M5"), _bar(friday, "M5")],
    }
    h = feed.health()
    assert h["candle_counts"]["M5"] == 2
    assert h["contiguous_candle_counts"]["M5"] == 1
    assert h["integrity_report"]["weekend_gap_count"] >= 1
    assert h["history_ready"] is False

    with pytest.raises(module.FinnhubInsufficientHistory, match=r"1/2 real candles contiguous"):
        feed.get_candles("EUR/USD", "5min")


def test_201_consecutive_m1_m5_bar_inputs_exclude_older_gap(tmp_path):
    _, feed = _feed(tmp_path, minimum=201, now=120002)
    feed._last_price_ts = 120000
    feed._candles = {
        "M1": [_bar(120000 - i * 60, "M1") for i in range(201)]
        + [_bar(120000 - 202 * 60, "M1")],
        "M5": [_bar(120000 - i * 300, "M5") for i in range(201)]
        + [_bar(120000 - 202 * 300, "M5")],
    }
    health = feed.health()
    assert health["candle_counts"] == {"M1": 202, "M5": 202}
    assert health["contiguous_candle_counts"] == {"M1": 201, "M5": 201}
    assert health["history_ready"] is True
    m1 = feed.get_candles("EURUSD", "M1")
    m5 = feed.get_candles("EUR_USD", "M5")
    assert len(m1) == 201
    assert len(m5) == 201
    assert m1[-1]["ts"] == 120000 - 200 * 60
    assert m5[-1]["ts"] == 120000 - 200 * 300


def test_invalid_ohlc_remains_fail_closed_before_contiguous_check(tmp_path):
    module, feed = _feed(tmp_path)
    feed._last_price_ts = 600
    bad = _bar(600, "M1")
    bad["open"] = 2.0
    feed._candles = {
        "M1": [bad, _bar(540, "M1")],
        "M5": [_bar(600, "M5"), _bar(300, "M5")],
    }
    with pytest.raises(module.FinnhubInvalidHistory, match="integrity"):
        feed.get_candles("EURUSD", "M1")
    assert feed.health()["history_ready"] is False


def test_observability_does_not_claim_live_ready_from_restored_history_alone(
    tmp_path, capsys
):
    import json

    _, feed = _feed(tmp_path)
    feed._candles = {
        "M1": [_bar(600, "M1"), _bar(540, "M1")],
        "M5": [_bar(600, "M5"), _bar(300, "M5")],
    }
    # Raw stored history can be valid while the restarted process has not
    # observed a single actual, new EUR/USD tick.
    assert feed.health()["history_ready"] is True
    feed._emit_stream_observation("SUBSCRIBE_SENT_UNVERIFIED")
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1
    message = json.loads(out[0].split(" ", 1)[1])
    assert message["M1_contiguous_head_count"] == 2
    assert message["M5_contiguous_head_count"] == 2
    assert message["history_continuity_state"] == "CONTIGUOUS"
    assert message["usable_real_history_and_fresh_tick"] is False
    assert message["last_real_tick_ts"] is None
    assert "open_now" not in out[0].lower()
