from __future__ import annotations

import importlib

import pytest


class _Response:
    def __init__(self, status_code=200, payload=None, lines=None):
        self.status_code = status_code
        self._payload = payload or {}
        self._lines = lines or []

    def json(self):
        return self._payload

    def iter_lines(self):
        return iter(self._lines)


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def _history_payload():
    return {
        "candles": [
            {
                "complete": True,
                "volume": 10,
                "time": "2026-08-30T20:00:00.000000000Z",
                "mid": {"o": "1.1000", "h": "1.1010", "l": "1.0990", "c": "1.1005"},
            },
            {
                "complete": False,
                "volume": 4,
                "time": "2026-08-30T20:01:00.000000000Z",
                "mid": {"o": "1.1005", "h": "1.1020", "l": "1.1000", "c": "1.1015"},
            },
        ]
    }


def _price(ts="2026-08-30T20:01:04.000000000Z", bid="1.1014", ask="1.1016"):
    return {
        "type": "PRICE",
        "instrument": "EUR_USD",
        "time": ts,
        "bids": [{"price": bid}],
        "asks": [{"price": ask}],
    }


def test_oanda_requires_credentials_before_network(monkeypatch):
    monkeypatch.delenv("OANDA_API_TOKEN", raising=False)
    monkeypatch.delenv("OANDA_ACCOUNT_ID", raising=False)
    module = importlib.import_module("runtime.oanda_market_data")
    with pytest.raises(module.OandaConfigurationError, match="OANDA_API_TOKEN"):
        module.OandaPracticeFeed()


def test_oanda_history_is_normalized_newest_first():
    module = importlib.import_module("runtime.oanda_market_data")
    session = _Session([_Response(payload=_history_payload())])
    feed = module.OandaPracticeFeed(
        token="secret",
        account_id="practice-account",
        session=session,
        clock=lambda: 1_777_000_000,
    )

    candles = feed.fetch_history("1min", count=250)

    assert [row["ts"] for row in candles] == sorted(
        [row["ts"] for row in candles], reverse=True
    )
    assert candles[0]["provider"] == "OANDA_PRACTICE"
    assert candles[0]["timeframe"] == "M1"
    assert session.calls[0][1]["headers"]["Authorization"] == "Bearer secret"
    assert "secret" not in session.calls[0][0]


def test_live_tick_updates_m1_and_m5_from_same_present_price():
    module = importlib.import_module("runtime.oanda_market_data")
    feed = module.OandaPracticeFeed(
        token="secret",
        account_id="practice-account",
        session=_Session([]),
        clock=lambda: module._parse_oanda_ts("2026-08-30T20:01:06Z"),
    )
    feed._candles = {"M1": [], "M5": []}

    feed.ingest_price(_price())
    feed.ingest_price(_price("2026-08-30T20:01:05Z", "1.1010", "1.1012"))

    m1 = feed._candles["M1"][0]
    m5 = feed._candles["M5"][0]
    assert m1["open"] == pytest.approx(1.1015)
    assert m1["close"] == pytest.approx(1.1011)
    assert m1["high"] == pytest.approx(1.1015)
    assert m1["low"] == pytest.approx(1.1011)
    assert m5["close"] == pytest.approx(1.1011)
    assert m1["complete"] is False
    assert m5["complete"] is False


def test_stale_or_future_price_is_fail_closed(monkeypatch):
    module = importlib.import_module("runtime.oanda_market_data")
    now = module._parse_oanda_ts("2026-08-30T20:01:30Z")
    feed = module.OandaPracticeFeed(
        token="secret",
        account_id="practice-account",
        session=_Session([]),
        freshness_seconds=10,
        clock=lambda: now,
    )
    feed._stream_started = True
    feed._candles = {"M1": [], "M5": []}
    feed.ingest_price(_price("2026-08-30T20:01:04Z"))

    with pytest.raises(module.OandaStaleMarketData, match="stale"):
        feed.get_candles("EUR/USD", "M1")

    feed._last_price_ts = now + 1
    with pytest.raises(module.OandaStaleMarketData, match="stale"):
        feed.get_candles("EUR/USD", "M1")


def test_market_client_dispatches_oanda_without_exposing_token(
    canonical_runtime_root, fresh_imports, monkeypatch
):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "OANDA_PRACTICE")
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
            }

    market._OANDA_FEED = _Feed()
    candles = market.get_candles("EUR/USD", "1min")

    assert candles[0]["symbol"] == "EUR/USD"
    assert market.configured_symbols() == ["EUR/USD"]
    status = importlib.import_module("runtime.runtime_status").read_status()
    assert status["market_data_provider"] == "OANDA_PRACTICE"
    assert status["market_data_state"] == "READY"


def test_oanda_foundation_rejects_other_symbols():
    module = importlib.import_module("runtime.oanda_market_data")
    with pytest.raises(module.OandaConfigurationError, match="restricted"):
        module.normalize_symbol("GBP/USD")
