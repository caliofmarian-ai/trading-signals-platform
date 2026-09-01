from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone

import pytest


def _row(ts: int, price: float):
    return {
        "datetime": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "open": str(price),
        "high": str(price + 0.0004),
        "low": str(price - 0.0004),
        "close": str(price + 0.0001),
    }


class _Response:
    def __init__(self, rows, status_code=200):
        self.status_code = status_code
        self._rows = rows

    def json(self):
        return {"values": self._rows}


def _history_http(now_ts: int, calls: list):
    def http_get(url, params, timeout):
        calls.append((url, dict(params), timeout))
        step = 60 if params["interval"] == "1min" else 300
        rows = [
            _row(now_ts - step * 2, 1.1000),
            _row(now_ts - step * 3, 1.0990),
            _row(now_ts - step * 4, 1.0980),
        ]
        return _Response(rows)

    return http_get


def test_constructor_is_network_silent(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    calls = []

    def blocked(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("network must be lazy")

    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="secret",
        minimum_candles=2,
        store_path=tmp_path / "candles.json",
        http_get=blocked,
        websocket_connector=blocked,
    )

    assert calls == []
    assert feed.health()["bootstrap_state"] == "NOT_ATTEMPTED"
    assert feed.health()["stream_state"] == "NOT_STARTED"


def test_lazy_bootstrap_loads_real_m1_m5_and_persists_without_secret(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    now_ts = 1_800_000_120
    calls = []
    store = tmp_path / "candles.json"
    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="secret",
        minimum_candles=2,
        clock=lambda: now_ts,
        store_path=store,
        http_get=_history_http(now_ts, calls),
    )

    feed._ensure_history()

    assert [call[1]["interval"] for call in calls] == ["1min", "5min"]
    assert len(feed._candles["M1"]) == 3
    assert len(feed._candles["M5"]) == 3
    assert feed.health()["bootstrap_state"] == "READY"
    assert store.exists()
    assert "secret" not in store.read_text(encoding="utf-8")


def test_no_strategy_candles_until_fresh_live_price_arrives(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    now_ts = 1_800_000_120
    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="secret",
        minimum_candles=2,
        clock=lambda: now_ts,
        store_path=tmp_path / "candles.json",
        http_get=_history_http(now_ts, []),
    )
    feed._ensure_history()
    feed._stream_started = True

    with pytest.raises(module.TwelveDataMarketDataUnavailable, match="live price"):
        feed.get_candles("M1")


def test_live_price_updates_current_m1_m5_from_real_tick(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    now_ts = 1_800_000_120
    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="secret",
        minimum_candles=2,
        clock=lambda: now_ts,
        store_path=tmp_path / "candles.json",
        http_get=_history_http(now_ts, []),
        persist_interval_seconds=1,
    )
    feed._ensure_history()
    feed._stream_started = True

    feed.ingest_message(
        {"event": "price", "symbol": "EUR/USD", "timestamp": now_ts, "price": "1.1234"}
    )
    feed.ingest_message(
        {"event": "price", "symbol": "EUR/USD", "timestamp": now_ts + 1, "price": "1.1238"}
    )

    m1 = feed.get_candles("1min")[0]
    m5 = feed.get_candles("5min")[0]
    assert m1["provider"] == "TWELVE_DATA"
    assert m1["close"] == pytest.approx(1.1238)
    assert m1["high"] == pytest.approx(1.1238)
    assert m1["low"] == pytest.approx(1.1234)
    assert m5["close"] == pytest.approx(1.1238)
    assert feed.health()["stream_state"] == "LIVE"


def test_stale_and_future_live_price_fail_closed(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    now_ts = 1_800_000_120
    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="secret",
        minimum_candles=2,
        freshness_seconds=10,
        clock=lambda: now_ts,
        store_path=tmp_path / "candles.json",
        http_get=_history_http(now_ts, []),
    )
    feed._ensure_history()
    feed._stream_started = True
    feed.ingest_message(
        {"event": "price", "symbol": "EUR/USD", "timestamp": now_ts - 20, "price": "1.12"}
    )
    with pytest.raises(module.TwelveDataStaleMarketData, match="stale"):
        feed.get_candles("M1")

    feed._last_price_ts = now_ts + 1
    with pytest.raises(module.TwelveDataStaleMarketData, match="stale"):
        feed.get_candles("M1")


def test_subscription_failure_is_explicit_and_fail_closed(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    now_ts = 1_800_000_120
    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="secret",
        minimum_candles=2,
        clock=lambda: now_ts,
        store_path=tmp_path / "candles.json",
        http_get=_history_http(now_ts, []),
    )
    feed._ensure_history()
    feed._stream_started = True
    feed.ingest_message(
        {"event": "subscribe-status", "fails": [{"symbol": "EUR/USD"}], "success": []}
    )

    with pytest.raises(module.TwelveDataStreamingUnavailable, match="subscription failed"):
        feed.get_candles("M1")


def test_wrong_symbol_and_invalid_payload_never_mutate_live_price(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="secret",
        minimum_candles=2,
        store_path=tmp_path / "candles.json",
    )

    feed.ingest_message("not-json")
    feed.ingest_message({"event": "price", "symbol": "GBP/USD", "timestamp": 123, "price": 1.2})
    feed.ingest_message({"event": "price", "symbol": "EUR/USD", "timestamp": 123, "price": -1})

    assert feed._last_price_ts is None
    assert feed._candles == {"M1": [], "M5": []}


def test_corrupt_store_is_reported_not_used(tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    store = tmp_path / "candles.json"
    store.write_text(json.dumps({"provider": "TWELVE_DATA", "candles": {}}), encoding="utf-8")

    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD", token="secret", minimum_candles=2, store_path=store
    )

    assert feed.health()["store_load_state"] == "ERROR"
    assert feed._candles == {"M1": [], "M5": []}


def test_twelve_data_provider_preserves_configured_active_symbol_universe(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "TWELVE_DATA")
    monkeypatch.setenv("TWELVE_DATA_STREAMING_ENABLED", "1")
    market = fresh_imports("runtime.market_client")

    assert market.configured_symbols() is None


def test_non_stream_symbol_uses_bounded_rest_cache_not_stream_feed(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "TWELVE_DATA")
    monkeypatch.setenv("TWELVE_DATA_STREAMING_ENABLED", "1")
    monkeypatch.setenv("TWELVE_DATA_STREAM_SYMBOL", "EUR/USD")
    monkeypatch.setenv("TWELVE_DATA_REST_CACHE_SECONDS", "55")
    market = fresh_imports("runtime.market_client")
    calls = []

    monkeypatch.setattr(
        market,
        "fetch_klines",
        lambda symbol, timeframe, limit=50: calls.append((symbol, timeframe, limit))
        or [
            {"datetime": "2026-09-01 12:00:00", "open": "1", "high": "1.1", "low": "0.9", "close": "1"},
            {"datetime": "2026-09-01 11:59:00", "open": "1", "high": "1.1", "low": "0.9", "close": "1"},
        ],
    )
    monkeypatch.setattr(
        market,
        "_twelve_data_feed",
        lambda: (_ for _ in ()).throw(AssertionError("GBP/USD must not use EUR/USD stream")),
    )

    first = market.get_candles("GBP/USD", "1min")
    second = market.get_candles("GBP/USD", "1min")

    assert first == second
    assert calls == [("GBP/USD", "1min", 205)]


def test_designated_stream_symbol_uses_live_feed_without_rest_poll(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "TWELVE_DATA")
    monkeypatch.setenv("TWELVE_DATA_STREAMING_ENABLED", "1")
    monkeypatch.setenv("TWELVE_DATA_STREAM_SYMBOL", "EUR/USD")
    market = fresh_imports("runtime.market_client")

    class _Feed:
        def get_candles(self, timeframe):
            return [{"symbol": "EUR/USD", "timeframe": timeframe, "ts": 123}]

        def health(self):
            return {
                "symbol": "EUR/USD",
                "last_price_ts": 123,
                "price_age_seconds": 1,
                "freshness_limit_seconds": 10,
                "candle_counts": {"M1": 201, "M5": 201},
                "minimum_candles": 201,
                "history_ready": True,
                "stream_state": "LIVE",
                "bootstrap_state": "READY",
                "store_load_state": "LOADED",
                "store_write_state": "OK",
                "restored_candle_counts": {"M1": 201, "M5": 201},
                "last_persisted_ts": 123,
            }

    market._TWELVE_DATA_FEED = _Feed()
    monkeypatch.setattr(
        market,
        "fetch_klines",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("live pair must not poll REST")),
    )

    candles = market.get_candles("EUR/USD", "1min")
    assert candles[0]["symbol"] == "EUR/USD"
    status = importlib.import_module("runtime.runtime_status").read_status()
    assert status["market_data_state"] == "READY"
    assert status["market_data_stream_state"] == "LIVE"


def test_stream_subscription_failure_falls_back_to_bounded_rest_cache(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "TWELVE_DATA")
    monkeypatch.setenv("TWELVE_DATA_STREAMING_ENABLED", "1")
    monkeypatch.setenv("TWELVE_DATA_STREAM_SYMBOL", "EUR/USD")
    market = fresh_imports("runtime.market_client")
    td = importlib.import_module("runtime.twelvedata_market_data")

    class _Feed:
        def get_candles(self, timeframe):
            raise td.TwelveDataStreamingUnavailable("trial subscription unavailable")

    market._TWELVE_DATA_FEED = _Feed()
    fallback = [{"symbol": "EUR/USD", "timeframe": "1min", "ts": 321}]
    monkeypatch.setattr(market, "_cached_rest_candles", lambda symbol, timeframe: fallback)

    assert market.get_candles("EUR/USD", "1min") == fallback
    status = importlib.import_module("runtime.runtime_status").read_status()
    assert status["market_data_state"] == "READY"
    assert status["market_data_stream_state"] == "REST_FALLBACK"
