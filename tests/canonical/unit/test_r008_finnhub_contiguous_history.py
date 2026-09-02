from __future__ import annotations

import importlib
import json


def _row(ts: int, price: float = 1.1) -> dict:
    return {
        "ts": ts,
        "open": price,
        "high": price + 0.0002,
        "low": price - 0.0002,
        "close": price + 0.0001,
        "volume": 1,
        "complete": True,
    }


def _write_store(path, *, m1: list[dict], m5: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "provider": "FINNHUB",
                "candles": {"M1": m1, "M5": m5},
            }
        ),
        encoding="utf-8",
    )


def test_finnhub_exposes_recent_continuity_gap_without_fabricating_rows(tmp_path) -> None:
    module = importlib.import_module("runtime.finnhub_market_data")
    store = tmp_path / "candles.json"
    _write_store(
        store,
        m1=[_row(600), _row(480), _row(420)],
        m5=[_row(600), _row(300)],
    )
    feed = module.FinnhubForexFeed(
        token="secret",
        store_path=store,
        minimum_candles=2,
        freshness_seconds=10,
        clock=lambda: 601,
    )
    feed._last_price_ts = 600
    feed._stream_started = True

    candles = feed.get_candles("EUR/USD", "M1")
    health = feed.health()

    assert [candle["ts"] for candle in candles] == [600, 480, 420]
    assert health["candle_counts"]["M1"] == 3
    assert health["contiguous_candle_counts"] == {"M1": 1, "M5": 2}
    assert health["history_ready"] is True
    assert health["integrity_report"]["temporal_continuity_state"] == "GAPPED"
    assert health["integrity_report"]["gap_count"] == 1


def test_finnhub_reports_new_contiguous_segment_separately_from_older_gap(tmp_path) -> None:
    module = importlib.import_module("runtime.finnhub_market_data")
    store = tmp_path / "candles.json"
    _write_store(
        store,
        m1=[_row(600), _row(540), _row(420)],
        m5=[_row(600), _row(300)],
    )
    feed = module.FinnhubForexFeed(
        token="secret",
        store_path=store,
        minimum_candles=2,
        freshness_seconds=10,
        clock=lambda: 601,
    )
    feed._last_price_ts = 600
    feed._stream_started = True

    candles = feed.get_candles("EUR/USD", "M1")
    health = feed.health()

    assert [candle["ts"] for candle in candles] == [600, 540, 420]
    assert health["contiguous_candle_counts"] == {"M1": 2, "M5": 2}
    assert health["history_ready"] is True
    assert health["integrity_report"]["gap_count"] == 1
