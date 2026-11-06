"""Controlled real-feed object fixtures; no actual provider connection."""
import copy
import importlib
import json
import threading

import pytest


def _tick(feed,stamp,price=1.1001,volume=0):
    feed.ingest_message({"type":"trade","data":[{"s":"OANDA:EUR_USD","t":stamp,"p":price,"v":volume}]})


def _feed(tmp_path,clock=lambda:1001.75):
    module=importlib.import_module("runtime.finnhub_market_data")
    feed=module.FinnhubForexFeed(token="offline-secret",store_path=tmp_path/"candles.json",
                               minimum_candles=2,clock=clock)
    feed._stream_started=True
    _tick(feed,900000,1.1000);_tick(feed,1000500,1.1001)
    return module,feed


def test_public_reader_does_not_pair_candle_snapshot_with_later_health(canonical_runtime_root,monkeypatch,tmp_path):
    _,feed=_feed(tmp_path)
    market=importlib.import_module("runtime.market_client")
    original_health=feed.health
    def interleaved_health():
        _tick(feed,1001000,1.2000)
        return original_health()
    # The previous public API returned 1.1001 with timestamp 1001 here, which
    # belonged to 1.2000. An atomic read must never call the separate health API.
    monkeypatch.setattr(feed,"health",interleaved_health)
    monkeypatch.setattr(market,"_finnhub_feed",lambda:feed)
    monkeypatch.setattr(market,"configured_provider",lambda:"FINNHUB")
    assert market.get_latest_price_sample("EUR/USD")=={
        "provider":"FINNHUB","symbol":"EUR/USD","price":1.1001,"observed_ts":1000.0,
        "source":"LIVE_STREAM_CURRENT_M1_CLOSE"}


def test_ingestion_cannot_interleave_with_price_timestamp_snapshot(canonical_runtime_root,monkeypatch,tmp_path):
    _,feed=_feed(tmp_path)
    market=importlib.import_module("runtime.market_client")
    monkeypatch.setattr(market,"_finnhub_feed",lambda:feed)
    monkeypatch.setattr(market,"configured_provider",lambda:"FINNHUB")
    ready,attempted,updated=threading.Event(),threading.Event(),threading.Event()
    def update():
        if ready.wait(2):
            attempted.set()
            _tick(feed,1001000,1.2000)
            updated.set()
    thread=threading.Thread(target=update,daemon=True)
    original=feed.get_candles
    def snapshot_then_interleave(*args):
        result=original(*args)
        ready.set()
        assert attempted.wait(2)
        # In the old reader the writer completed here. It must now wait for the
        # outer sample lock; no wait-for-completion deadlock is introduced.
        updated.wait(.1)
        return result
    monkeypatch.setattr(feed,"get_candles",snapshot_then_interleave)
    thread.start()
    sample=market.get_latest_price_sample("EUR/USD")
    assert sample["price"]==1.1001 and sample["observed_ts"]==1000
    assert updated.wait(2)
    thread.join(2)
    sample=market.get_latest_price_sample("EUR/USD")
    assert sample["price"]==1.2000 and sample["observed_ts"]==1001


@pytest.mark.parametrize("field,value",[("p",float("nan")),("p",float("inf")),("p",float("-inf")),
    ("p",True),("v",float("nan")),("v",float("inf")),("v",-1),("v",True),
    ("t",float("inf")),("t",True),("t",2**53),("t",-1)])
def test_invalid_ticks_cannot_poison_history_or_observation(canonical_runtime_root,tmp_path,field,value):
    _,feed=_feed(tmp_path)
    before=copy.deepcopy(feed._candles)
    counters=feed._valid_trade_tick_count
    row={"s":"OANDA:EUR_USD","t":1001000,"p":1.2,"v":0,field:value}
    feed.ingest_message({"type":"trade","data":[row]})
    assert feed._candles==before and feed._valid_trade_tick_count==counters
    assert feed.get_latest_price_sample("EUR/USD")["observed_ts"]==1000
    _tick(feed,1001000,1.2000)
    assert feed.get_latest_price_sample("EUR/USD")["price"]==1.2000


def test_atomic_sample_keeps_history_freshness_and_restart_gates(canonical_runtime_root,tmp_path):
    clock=[1001.75]
    module,feed=_feed(tmp_path,clock=lambda:clock[0])
    assert feed.get_latest_price_sample("EURUSD")["observed_ts"]==1000  # Existing whole-second convention.
    feed.minimum_candles_by_timeframe["M1"]=3
    with pytest.raises(module.FinnhubInsufficientHistory):
        feed.get_latest_price_sample("EUR/USD")
    feed.minimum_candles_by_timeframe["M1"]=2
    clock[0]=1020
    with pytest.raises(module.FinnhubStaleMarketData):
        feed.get_latest_price_sample("EUR/USD")
    restored=module.FinnhubForexFeed(token="offline",store_path=tmp_path/"candles.json",
                                   minimum_candles=2,clock=lambda:1001.75)
    restored._stream_started=True
    with pytest.raises(module.FinnhubMarketDataUnavailable,match="not been received"):
        restored.get_latest_price_sample("EUR/USD")
    clock[0]=1061.75
    feed._last_price_ts=1061
    with pytest.raises(module.FinnhubMarketDataUnavailable,match="does not match"):
        feed.get_latest_price_sample("EUR/USD")


def test_tick_timing_is_bounded_and_contains_no_prices(canonical_runtime_root,tmp_path,capsys):
    clock=[1001.75]
    _,feed=_feed(tmp_path,clock=lambda:clock[0])
    for index in range(300):
        stamp=1001000+index*3000
        clock[0]=stamp/1000+.5
        _tick(feed,stamp,1.123456789)
    health=feed.health()
    assert health["provider_tick_interval_seconds"]["sample"]==128
    assert health["provider_tick_interval_seconds"]["min"]==3
    assert health["provider_tick_intervals_gt_2s"]==128
    assert health["provider_tick_receive_age_seconds"]["p95"]==.5
    assert health["quote_sample_contract"]=="ATOMIC_REAL_TICK_PRICE_TIMESTAMP_V1"
    feed._emit_stream_observation("TEST_TIMING")
    output=capsys.readouterr().out
    line=[line for line in output.splitlines() if line.startswith("TSP_FINNHUB_STREAM_EVIDENCE ")][-1]
    public=json.loads(line.split(" ",1)[1])
    assert public["provider_tick_interval_seconds"]["sample"]==128
    assert "1.123456789" not in line and "offline-secret" not in line
