from __future__ import annotations

import importlib
import json

import pytest


def _trade(ts_ms=1788120064000, price=1.1015, volume=0):
    return {
        "type": "trade",
        "data": [{"s": "OANDA:EUR_USD", "p": price, "t": ts_ms, "v": volume}],
    }


def test_finnhub_requires_api_key_before_connection(monkeypatch, tmp_path):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    module = importlib.import_module("runtime.finnhub_market_data")
    with pytest.raises(module.FinnhubConfigurationError, match="FINNHUB_API_KEY"):
        module.FinnhubForexFeed(store_path=tmp_path / "candles.json")


def test_live_ticks_build_real_m1_and_m5_and_persist(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")
    store = tmp_path / "candles.json"
    feed = module.FinnhubForexFeed(
        token="secret",
        store_path=store,
        minimum_candles=2,
        clock=lambda: 1788120066,
    )

    feed.ingest_message(_trade())
    feed.ingest_message(_trade(1788120065000, 1.1011, 2))

    m1 = feed._candles["M1"][0]
    m5 = feed._candles["M5"][0]
    assert m1["open"] == pytest.approx(1.1015)
    assert m1["close"] == pytest.approx(1.1011)
    assert m1["high"] == pytest.approx(1.1015)
    assert m1["low"] == pytest.approx(1.1011)
    assert m5["close"] == pytest.approx(1.1011)
    assert m1["provider"] == "FINNHUB"
    assert store.exists()
    assert "secret" not in store.read_text(encoding="utf-8")


def test_persisted_real_candles_survive_restart(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")
    store = tmp_path / "candles.json"
    first = module.FinnhubForexFeed(token="secret", store_path=store, minimum_candles=2)
    first.ingest_message(_trade())
    first.ingest_message(_trade(1788120124000, 1.1020))

    restored = module.FinnhubForexFeed(token="secret", store_path=store, minimum_candles=2)

    assert len(restored._candles["M1"]) == 2
    assert restored._candles["M1"][0]["close"] == pytest.approx(1.1020)
    assert restored._candles["M1"][1]["complete"] is True


def test_no_decision_data_until_live_price_and_real_history_are_ready(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(
        token="secret",
        store_path=tmp_path / "candles.json",
        minimum_candles=2,
        clock=lambda: 1788120126,
    )
    feed._stream_started = True

    with pytest.raises(module.FinnhubMarketDataUnavailable, match="not been received"):
        feed.get_candles("EUR/USD", "M1")

    feed.ingest_message(_trade(1788120124000, 1.1020))
    with pytest.raises(module.FinnhubInsufficientHistory, match="1/2 real candles"):
        feed.get_candles("EUR/USD", "M1")


def test_stale_or_future_price_is_fail_closed(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(
        token="secret",
        store_path=tmp_path / "candles.json",
        minimum_candles=2,
        freshness_seconds=10,
        clock=lambda: 1788120200,
    )
    feed._stream_started = True
    feed.ingest_message(_trade(1788120124000, 1.1020))

    with pytest.raises(module.FinnhubStaleMarketData, match="stale"):
        feed.get_candles("EUR/USD", "M1")

    feed._last_price_ts = 1788120201
    with pytest.raises(module.FinnhubStaleMarketData, match="stale"):
        feed.get_candles("EUR/USD", "M1")


def test_wrong_symbol_and_invalid_payload_do_not_create_market_data(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(
        token="secret", store_path=tmp_path / "candles.json", minimum_candles=2
    )
    feed.ingest_message("not-json")
    feed.ingest_message({"type": "trade", "data": [{"s": "BINANCE:BTCUSDT", "p": 1, "t": 1}]})
    feed.ingest_message({"type": "trade", "data": [{"s": "OANDA:EUR_USD", "p": -1, "t": 1}]})

    assert feed._last_price_ts is None
    assert feed._candles == {"M1": [], "M5": []}


def test_stream_subscribes_to_one_canonical_forex_symbol(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")

    class _Socket:
        def __init__(self):
            self.sent = []
            self.closed = False

        def send(self, value):
            self.sent.append(json.loads(value))

        def recv(self):
            feed._stop_event.set()
            return json.dumps(_trade())

        def close(self):
            self.closed = True

    socket = _Socket()
    seen_urls = []

    def connector(url, timeout):
        seen_urls.append((url, timeout))
        return socket

    feed = module.FinnhubForexFeed(
        token="secret",
        store_path=tmp_path / "candles.json",
        minimum_candles=2,
        websocket_connector=connector,
    )
    feed._stream_forever()

    assert socket.sent == [{"type": "subscribe", "symbol": "OANDA:EUR_USD"}]
    assert socket.closed is True
    assert seen_urls[0][0].startswith("wss://ws.finnhub.io?token=")


def test_market_client_dispatches_finnhub_without_exposing_key(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    market = fresh_imports("runtime.market_client")

    class _Feed:
        def get_candles(self, symbol, timeframe):
            return [{"symbol": symbol, "timeframe": timeframe, "ts": 123}]

        def health(self):
            return {
                "symbol": "EUR/USD",
                "last_price_ts": 123,
                "price_age_seconds": 1,
                "freshness_limit_seconds": 10,
                "candle_counts": {"M1": 201, "M5": 201},
                "minimum_candles": 201,
                "history_ready": True,
            }

    market._FINNHUB_FEED = _Feed()
    candles = market.get_candles("EUR/USD", "1min")

    assert candles[0]["symbol"] == "EUR/USD"
    assert market.configured_symbols() == ["EUR/USD"]
    status = importlib.import_module("runtime.runtime_status").read_status()
    assert status["market_data_provider"] == "FINNHUB"
    assert status["market_data_state"] == "READY"
    assert status["market_data_note"].endswith("real candles M1=201, M5=201")


def test_market_client_reports_history_collection_without_decision_data(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    market = fresh_imports("runtime.market_client")
    module = importlib.import_module("runtime.finnhub_market_data")

    class _Feed:
        def get_candles(self, symbol, timeframe):
            raise module.FinnhubInsufficientHistory(
                "Finnhub M5 history is still collecting: 12/201 real candles"
            )

        def health(self):
            return {
                "symbol": "EUR/USD",
                "last_price_ts": 123,
                "price_age_seconds": 1,
                "freshness_limit_seconds": 10,
                "candle_counts": {"M1": 60, "M5": 12},
                "minimum_candles": 201,
                "history_ready": False,
            }

    market._FINNHUB_FEED = _Feed()
    with pytest.raises(market.MarketDataUnavailableError, match="12/201 real candles"):
        market.get_candles("EUR/USD", "5min")

    status = importlib.import_module("runtime.runtime_status").read_status()
    assert status["market_data_state"] == "MARKET_DATA_COLLECTING"
    assert status["market_data_candle_counts"] == {"M1": 60, "M5": 12}


def test_finnhub_foundation_rejects_other_symbols():
    module = importlib.import_module("runtime.finnhub_market_data")
    with pytest.raises(module.FinnhubConfigurationError, match="restricted"):
        module.normalize_symbol("GBP/USD")
