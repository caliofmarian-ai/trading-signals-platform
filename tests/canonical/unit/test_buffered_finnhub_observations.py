"""Actual ingestion-path fixtures, synthetic quotes, no network or calibration claim."""
import importlib

import pytest


def _tick(feed, ms, price):
    feed.ingest_message({"type":"trade", "data":[{"s":"OANDA:EUR_USD", "t":ms, "p":price}]})


def _feed(tmp_path, clock):
    module=importlib.import_module("runtime.finnhub_market_data")
    feed=module.FinnhubForexFeed(token="OFFLINE_TEST_ONLY", clock=lambda:clock[0],
        store_path=tmp_path/"real_candle_fixture.json", minimum_candles=2)
    feed._stream_started=True
    return module,feed


def test_retained_first_quote_is_not_overwritten_by_later_price(tmp_path):
    clock=[1006.0]
    _,feed=_feed(tmp_path,clock)
    for ms,price in ((900000,1.0),(1000500,1.1),(1001000,1.15),(1001800,1.25),(1005000,1.5)):
        _tick(feed,ms,price)
    selected=feed.get_price_sample_at_or_after("EUR/USD",1001,2)
    assert selected["price"]==1.15 and selected["observed_ts"]==1001
    assert selected["source"]=="LIVE_STREAM_PROVIDER_TICK_BUFFER_V1"
    assert feed.get_latest_price_sample("EUR/USD")["price"]==1.5
    selected["price"]=999
    assert feed.get_price_sample_at_or_after("EUR/USD",1001,2)["price"]==1.15
    assert feed.get_price_sample_at_or_after("EUR/USD",1002,2) is None


def test_future_and_out_of_order_provider_ticks_do_not_create_earlier_evidence(tmp_path):
    clock=[1006.1]
    _,feed=_feed(tmp_path,clock)
    _tick(feed,1005000,1.1)
    _tick(feed,1004000,7.0)
    assert feed.get_price_sample_at_or_after("EUR/USD",1004,0) is None
    _tick(feed,1006900,2.0)
    assert feed.get_price_sample_at_or_after("EUR/USD",1006,1) is None
    clock[0]=1007
    assert feed.get_price_sample_at_or_after("EUR/USD",1006,1)["price"]==2.0


def test_saved_candles_never_backfill_the_live_quote_buffer(tmp_path):
    clock=[1006.0]
    module,feed=_feed(tmp_path,clock)
    _tick(feed,900000,1.0);_tick(feed,1005000,1.5)
    restored=module.FinnhubForexFeed(token="OFFLINE_TEST_ONLY", clock=lambda:clock[0],
        store_path=feed.store_path, minimum_candles=2)
    assert restored._candles["M1"]
    assert restored.get_price_sample_at_or_after("EUR/USD",1005,2) is None


def test_storage_bound_drops_evidence_instead_of_inventing_a_quote(tmp_path,monkeypatch):
    clock=[1006.0]
    module=importlib.import_module("runtime.finnhub_market_data")
    monkeypatch.setattr(module,"MAX_BUFFERED_REAL_QUOTES",2)
    _,feed=_feed(tmp_path,clock)
    _tick(feed,1000000,1.0);_tick(feed,1001000,1.1);_tick(feed,1002000,1.2)
    assert len(feed._real_quote_buffer)==2
    assert feed.get_price_sample_at_or_after("EUR/USD",1000,0) is None
    assert feed.get_price_sample_at_or_after("EUR/USD",1001,0)["price"]==1.1


@pytest.mark.parametrize("target,delay",[(True,2),(1000,False),(float("nan"),2),(1000,-1),(0,2)])
def test_invalid_sampling_windows_are_rejected(tmp_path,target,delay):
    _,feed=_feed(tmp_path,[1006.0])
    with pytest.raises(ValueError): feed.get_price_sample_at_or_after("EUR/USD",target,delay)


def test_provider_switch_cannot_fall_back_to_finnhub_cache(monkeypatch):
    market=importlib.import_module("runtime.market_client")
    monkeypatch.setattr(market,"configured_provider",lambda:"TWELVE_DATA")
    monkeypatch.setattr(market,"_finnhub_feed",lambda:pytest.fail("cross-provider cache access"))
    with pytest.raises(market.MarketDataUnavailableError):
        market.get_price_sample_at_or_after("EUR/USD",1000,2)


def test_concurrent_finnhub_consumers_share_the_same_feed(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from core import physical_params
    from runtime import finnhub_market_data, market_client

    first_entered = Event()
    second_started = Event()
    duplicate_entered = Event()
    release = Event()
    feeds = []

    def build_feed():
        feed = object()
        feeds.append(feed)
        if len(feeds) == 1:
            first_entered.set()
            assert release.wait(5)
        else:
            duplicate_entered.set()
        return feed

    def second_consumer():
        second_started.set()
        return market_client._finnhub_feed()

    monkeypatch.setattr(market_client, "_FINNHUB_FEED", None)
    monkeypatch.setattr(physical_params, "physical_runtime_enabled", lambda: False)
    monkeypatch.setattr(finnhub_market_data, "FinnhubForexFeed", build_feed)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(market_client._finnhub_feed)
        try:
            assert first_entered.wait(5)
            second = executor.submit(second_consumer)
            assert second_started.wait(5)
            assert not duplicate_entered.wait(0.5)
        finally:
            release.set()

        assert first.result(timeout=5) is second.result(timeout=5)
    assert len(feeds) == 1
