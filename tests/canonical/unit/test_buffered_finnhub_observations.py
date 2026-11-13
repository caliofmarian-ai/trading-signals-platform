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


def test_future_ticks_wait_and_late_evidence_does_not_rewind_live_price(tmp_path):
    clock=[1006.1]
    _,feed=_feed(tmp_path,clock)
    _tick(feed,1005000,1.1)
    _tick(feed,1004000,7.0)
    assert feed.get_price_sample_at_or_after("EUR/USD",1004,0)["price"] == 7.0
    assert feed._last_tick_ms == 1005000 and feed._candles["M1"][0]["close"] == 1.1
    _tick(feed,1006900,2.0)
    assert feed.get_price_sample_at_or_after("EUR/USD",1006,1) is None
    clock[0]=1007
    assert feed.get_price_sample_at_or_after("EUR/USD",1006,1)["price"]==2.0


def test_saved_candles_never_backfill_the_live_quote_buffer(tmp_path):
    clock=[1006.0]
    module,feed=_feed(tmp_path,clock)
    _tick(feed,900000,1.0);_tick(feed,1005000,1.5)
    feed._quote_store.path.unlink()  # explicitly exercise a legacy candle-only store
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


def test_study_chart_evidence_excludes_ambiguous_and_post_expiry_prices(tmp_path):
    clock = [1202.25]
    _, feed = _feed(tmp_path, clock)
    for timestamp, price in (
        (1010000, 1.0), (1025125, 1.1), (1025999, 1.12), (1026000, 1.13),
        (1080125, 1.14), (1139500, 1.15), (1140125, 1.16), (1198000, 1.17),
        (1201000, 1.18), (1202500, 1.19), (1202501, 1.2),
    ):
        _tick(feed, timestamp, price)

    candles, ticks = feed.get_study_chart_evidence(1025, 1202.5)
    assert [candle["ts"] for candle in candles] == [1080, 1140]
    assert all(candle["complete"] for candle in candles)
    assert [tick["observed_ts"] for tick in ticks] == [
        1026, 1080.125, 1139.5, 1140.125, 1198, 1201,
    ]
    assert ticks[1] == {"observed_ts": 1080.125, "price": 1.14}

    candles[0]["high"] = 99
    ticks[0]["price"] = 99
    clock[0] = 1203
    candles, ticks = feed.get_study_chart_evidence(1025, 1202.5)
    assert candles[0]["high"] == 1.15
    assert ticks[0]["price"] == 1.13
    assert ticks[-1] == {"observed_ts": 1202.5, "price": 1.19}


def test_study_tick_evidence_preserves_exact_real_tick_provenance(tmp_path):
    clock = [1202.25]
    _, feed = _feed(tmp_path, clock)
    for timestamp, price in ((1025125, 1.1), (1025250, 1.11), (1199999, 1.12),
                             (1202250, 1.13), (1202501, 1.14)):
        _tick(feed, timestamp, price)
    ticks = feed.get_study_tick_evidence(1025.125, 1202.5)
    assert [tick["provider_tick_ms"] for tick in ticks] == [1025250, 1199999, 1202250]
    assert ticks[0]["observed_ts"] == 1025.25
    assert ticks[0]["source"] == "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1"
    assert all(tick["provider"] == "FINNHUB" and tick["symbol"] == "EUR/USD" for tick in ticks)


def test_study_chart_uses_only_existing_active_finnhub_feed(monkeypatch):
    market = importlib.import_module("runtime.market_client")

    class CachedFeed:
        def get_study_chart_evidence(self, entry_ts, expiry_ts):
            assert (entry_ts, expiry_ts) == (1000, 1100)
            return [], [{"observed_ts": 1060.25, "price": 1.1}]

    monkeypatch.setattr(market, "_finnhub_feed", lambda: pytest.fail("must not create a feed"))
    monkeypatch.setattr(market, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(market, "_FINNHUB_FEED", None)
    assert market.get_finnhub_study_chart_evidence(1000, 1100) == ([], [])

    monkeypatch.setattr(market, "_FINNHUB_FEED", CachedFeed())
    assert market.get_finnhub_study_chart_evidence(1000, 1100) == (
        [], [{"observed_ts": 1060.25, "price": 1.1}],
    )

    monkeypatch.setattr(market, "configured_provider", lambda: "TWELVE_DATA")
    assert market.get_finnhub_study_chart_evidence(1000, 1100) == ([], [])


@pytest.mark.parametrize("restored", [False, True])
@pytest.mark.parametrize("window", [2, 10])
@pytest.mark.parametrize("late,reason", [
    (False, "ONLY_EXACT"),
    (True, "ONLY_SECOND_BUCKET"),
])
def test_source_precision_comparison_preserves_current_selection(
    tmp_path, capsys, restored, window, late, reason
):
    import json

    clock = [1012.0]
    module, feed = _feed(tmp_path, clock)
    tick_ms = 1000900 + window * 1000 if late else 1000500
    _tick(feed, tick_ms, 1.234567)
    if restored:
        feed = module.FinnhubForexFeed(token="OFFLINE_TEST_ONLY", clock=lambda: clock[0],
            store_path=feed.store_path, minimum_candles=2)

    for _ in range(2):
        selected = feed.get_price_sample_at_or_after("EUR/USD", 1000.25, window)
        assert (selected is not None) == late
    prefix = "TSP_QUOTE_WINDOW_PRECISION_COMPARISON "
    lines = [line.removeprefix(prefix) for line in capsys.readouterr().out.splitlines()
             if line.startswith(prefix)]
    assert len(lines) == 1
    evidence = json.loads(lines[0])
    assert evidence["reason"] == reason
    assert evidence["second_bucket_provider_tick_ms"] == (tick_ms if late else None)
    assert evidence["exact_provider_tick_ms"] == (None if late else tick_ms)
    assert evidence["changes_sampling_policy"] is False
    assert "1.234567" not in lines[0]


@pytest.mark.parametrize("restored", [False, True])
def test_precise_selector_uses_original_source_and_receipt_time(tmp_path, restored):
    clock = [1006.0]
    module, feed = _feed(tmp_path, clock)
    for timestamp, price in ((1000249, 1.1), (1000250, 1.2), (1002250, 1.3), (1002456, 1.4)):
        _tick(feed, timestamp, price)
    if restored:
        feed = module.FinnhubForexFeed(token="OFFLINE_TEST_ONLY", clock=lambda: clock[0],
            store_path=feed.store_path, minimum_candles=2)
    def precise(target, delay):
        return feed.get_price_sample_at_or_after("EUR/USD", target, delay, exact_source_time=True)
    first = precise(1000.25, 2)
    assert (first["observed_ts"], first["provider_tick_ms"], first["received_ts"]) == (1000.25, 1000250, 1006)
    assert first["source"] == ("DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1" if restored
                               else "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1")
    assert precise(1000.251, 1.999)["provider_tick_ms"] == 1002250
    assert precise(1002.251, 0.204) is None
    assert feed.get_price_sample_at_or_after("EUR/USD", 1000.25, 2)["observed_ts"] == 1002


@pytest.mark.parametrize("restored", [False, True])
def test_precise_selector_keeps_first_receipt_for_equal_source_timestamp(tmp_path, restored):
    clock = [1006.0]
    module, feed = _feed(tmp_path, clock)
    _tick(feed, 1000250, 1.11)
    clock[0] = 1006.1
    _tick(feed, 1000250, 1.22)

    if restored:
        feed = module.FinnhubForexFeed(token="OFFLINE_TEST_ONLY", clock=lambda: clock[0],
            store_path=feed.store_path, minimum_candles=2)

    selected = feed.get_price_sample_at_or_after(
        "EUR/USD", 1000.25, 2, exact_source_time=True
    )
    assert (selected["price"], selected["provider_tick_ms"], selected["received_ts"]) == (
        1.11, 1000250, 1006.0
    )
    assert selected["source"] == ("DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1" if restored
                                  else "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1")
