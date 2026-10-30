"""Finnhub transport evidence is not a claim of live EUR/USD data or strategy readiness.

All tests use synthetic OFFLINE fixtures. Real-market proof must come from the
production stream and validated real M1/M5 candles during an open FX session.
"""

from __future__ import annotations

import importlib
import json

import pytest


def _trade():
    return {
        "type": "trade",
        "data": [{"s": "OANDA:EUR_USD", "p": 1.12, "t": 1788120064000, "v": 0}],
    }


def test_new_feed_does_not_invent_connection_or_ticks(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(token="PRIVATE", store_path=tmp_path / "market.json")
    health = feed.health()
    assert health["stream_state"] == "NOT_STARTED"
    assert health["subscription_state"] == "NOT_SENT"
    assert health["stream_connection_attempts"] == 0
    assert health["stream_failure_count"] == 0
    assert health["valid_trade_tick_count"] == 0
    assert health["candle_counts"] == {"M1": 0, "M5": 0}
    assert health["history_ready"] is False
    assert "PRIVATE" not in json.dumps(health)


def test_subscribe_sent_does_not_claim_real_tick_without_trade(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")

    class Socket:
        def send(self, msg):
            assert json.loads(msg) == {
                "type": "subscribe", "symbol": "OANDA:EUR_USD"
            }

        def recv(self):
            feed._stop_event.set()
            return json.dumps({"type": "ping"})

        def close(self):
            pass

    feed = module.FinnhubForexFeed(
        token="PRIVATE",
        store_path=tmp_path / "market.json",
        websocket_connector=lambda *args, **kwargs: Socket(),
    )
    feed._stream_forever()
    health = feed.health()
    assert health["stream_connection_attempts"] == 1
    assert health["stream_failure_count"] == 0
    assert health["valid_trade_tick_count"] == 0
    assert health["subscription_state"] == "SENT_UNVERIFIED"
    assert health["stream_state"] == "STOPPED"
    assert health["history_ready"] is False


def test_real_tick_sets_evidence_without_claiming_full_m1_m5_history(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(
        token="PRIVATE",
        store_path=tmp_path / "market.json",
        minimum_candles=2,
        clock=lambda: 1788120066,
    )
    feed.ingest_message(_trade())
    health = feed.health()
    assert health["stream_state"] == "RECEIVING_REAL_TICKS"
    assert health["subscription_state"] == "REAL_TICK_CONFIRMED"
    assert health["valid_trade_tick_count"] == 1
    assert health["candle_counts"] == {"M1": 1, "M5": 1}
    assert health["history_ready"] is False
    assert "PRIVATE" not in json.dumps(health)


def test_transport_error_is_classified_without_provider_key(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")

    def fail(_url, timeout):
        assert timeout == 30
        raise RuntimeError("wss://ws.finnhub.io?token=SENSITIVE-API-KEY")

    feed = module.FinnhubForexFeed(
        token="SENSITIVE-API-KEY",
        store_path=tmp_path / "market.json",
        websocket_connector=fail,
    )
    # Stop after the first attempt, independent of real sleep/network.
    feed._stop_event.wait = lambda _delay: True
    feed._stream_forever()
    health = feed.health()
    assert health["stream_connection_attempts"] == 1
    assert health["stream_failure_count"] == 1
    assert health["stream_last_failure_class"] == "OTHER_TRANSPORT_ERROR"
    assert health["valid_trade_tick_count"] == 0
    assert health["stream_state"] == "DISCONNECTED_RETRYING"
    assert "SENSITIVE-API-KEY" not in json.dumps(health)


def test_error_frame_is_not_ingested_as_price_and_does_not_expose_message(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")

    class Socket:
        def send(self, _message):
            pass

        def recv(self):
            return json.dumps({
                "type": "error",
                "msg": "secret-token=SENSITIVE-API-KEY no permission",
            })

        def close(self):
            pass

    feed = module.FinnhubForexFeed(
        token="SENSITIVE-API-KEY",
        store_path=tmp_path / "market.json",
        websocket_connector=lambda *args, **kwargs: Socket(),
    )
    feed._stop_event.wait = lambda _delay: True
    feed._stream_forever()
    h = feed.health()
    assert h["stream_last_failure_class"] == "PROVIDER_ERROR_FRAME"
    assert h["valid_trade_tick_count"] == 0
    assert h["candle_counts"] == {"M1": 0, "M5": 0}
    assert "secret-token" not in json.dumps(h)
    assert "SENSITIVE-API-KEY" not in json.dumps(h)


def test_socket_eof_retries_instead_of_busy_loop(tmp_path):
    module = importlib.import_module("runtime.finnhub_market_data")

    class Socket:
        def send(self, _message):
            pass

        def recv(self):
            return ""

        def close(self):
            pass

    feed = module.FinnhubForexFeed(
        token="PRIVATE",
        store_path=tmp_path / "market.json",
        websocket_connector=lambda *args, **kwargs: Socket(),
    )
    feed._stop_event.wait = lambda _delay: True
    feed._stream_forever()
    h = feed.health()
    assert h["stream_last_failure_class"] == "ConnectionError"
    assert h["stream_failure_count"] == 1
    assert h["valid_trade_tick_count"] == 0


def test_market_client_status_carries_stream_evidence_on_missing_history(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    market = fresh_imports("runtime.market_client")
    module = importlib.import_module("runtime.finnhub_market_data")

    class Feed:
        def get_candles(self, symbol, timeframe):
            raise module.FinnhubInsufficientHistory("real M5 7/201")

        def health(self):
            return {
                "symbol": "EUR/USD",
                "last_price_ts": None,
                "price_age_seconds": None,
                "freshness_limit_seconds": 10,
                "candle_counts": {"M1": 12, "M5": 7},
                "minimum_candles": 201,
                "history_ready": False,
                "stream_state": "SUBSCRIBED_WAITING_REAL_TICK",
                "subscription_state": "SENT_UNVERIFIED",
                "stream_connection_attempts": 1,
                "stream_failure_count": 0,
                "stream_last_failure_class": None,
                "valid_trade_tick_count": 0,
                "last_stream_connected_ts": 123,
                "persistence_state": "EMPTY_READY",
                "store_load_state": "EMPTY",
                "store_write_state": "NOT_ATTEMPTED",
                "restored_candle_counts": {"M1": 0, "M5": 0},
                "last_persisted_ts": None,
                "integrity_state": "EMPTY",
                "integrity_report": {},
            }

    market._FINNHUB_FEED = Feed()
    with pytest.raises(market.MarketDataUnavailableError):
        market.get_candles("EURUSD", "5min")
    status = importlib.import_module("runtime.runtime_status").read_status()
    assert status["market_data_provider"] == "FINNHUB"
    assert status["market_data_state"] == "MARKET_DATA_COLLECTING"
    assert status["market_data_stream_state"] == "SUBSCRIBED_WAITING_REAL_TICK"
    assert status["market_data_stream_connection_attempts"] == 1
    assert status["market_data_valid_trade_tick_count"] == 0


def test_railway_evidence_is_bounded_price_free_and_not_trading_signal(
    tmp_path, capsys
):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(
        token="SENSITIVE-API-KEY",
        store_path=tmp_path / "market.json",
        clock=lambda: 1788120066,
    )
    feed._stream_state = "SUBSCRIBED_WAITING_REAL_TICK"
    feed._subscription_state = "SENT_UNVERIFIED"
    feed._emit_stream_observation("SUBSCRIBE_SENT_UNVERIFIED")
    feed._emit_stream_observation("SUBSCRIBE_SENT_UNVERIFIED")
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 1
    assert output[0].startswith("TSP_FINNHUB_STREAM_EVIDENCE ")
    payload = json.loads(output[0].split(" ", 1)[1])
    assert payload["event"] == "SUBSCRIBE_SENT_UNVERIFIED"
    assert payload["valid_trade_tick_count"] == 0
    assert payload["M5_observed_candles"] == 0
    assert payload["no_prices_or_trade_recommendations"] is True
    assert "SENSITIVE-API-KEY" not in output[0]
    assert "open_now" not in output[0].lower()
