"""Synthetic source ticks only; no network, execution or calibration claim."""
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Event

import pytest

from runtime.quote_evidence_store import PROTOCOL, RESTORED_SOURCE, QuoteEvidenceStore


def feed_at(tmp_path, clock):
    # Other canonical fixtures intentionally reload runtime modules. Resolve
    # the feed here so failure injection targets this instance's real module.
    from runtime.finnhub_market_data import FinnhubForexFeed
    feed = FinnhubForexFeed(token="PRIVATE_TEST_TOKEN", store_path=tmp_path / "market.json",
                           minimum_candles=2, clock=lambda: clock[0])
    feed._stream_started = True
    return feed


def tick(feed, ms, price=1.1):
    feed.ingest_message({"type": "trade", "data": [{"s": "OANDA:EUR_USD", "t": ms, "p": price}]})


def test_restart_recovers_original_tick_without_creating_live_readiness(tmp_path):
    clock = [1010.0]
    first = feed_at(tmp_path, clock)
    tick(first, 1001125, 1.1)
    tick(first, 1005000, 1.5)
    assert first._quote_store.flush()
    archive = json.loads(first._quote_store.path.read_text())
    assert archive["provider_symbol"] == "OANDA:EUR_USD"
    assert archive["quotes"][0] == {"provider_tick_ms": 1001125, "price": 1.1, "received_ts": 1010.0}
    assert first._quote_store.path.stat().st_mode & 0o777 == 0o600
    assert "PRIVATE_TEST_TOKEN" not in first._quote_store.path.read_text()

    restored = feed_at(tmp_path, clock)
    selected = restored.get_price_sample_at_or_after("EUR/USD", 1001, 2)
    assert selected == {"provider": "FINNHUB", "symbol": "EUR/USD", "price": 1.1,
                        "observed_ts": 1001.0, "source": RESTORED_SOURCE}
    assert restored.get_price_sample_at_or_after("EUR/USD", 1002, 2) is None
    assert restored._last_tick_ms is None and restored._last_price_ts is None
    health = restored.health()
    assert not health["fresh"] and health["valid_trade_tick_count"] == 0
    assert health["quote_evidence_store"]["restored_quote_count"] == 2
    assert health["quote_evidence_store"]["live_readiness_authority"] is False


def test_old_candle_store_alone_cannot_reconstruct_a_tick(tmp_path):
    clock = [1010.0]
    first = feed_at(tmp_path, clock)
    tick(first, 1001000)
    first._quote_store.path.unlink()
    restored = feed_at(tmp_path, clock)
    assert restored._candles["M1"]
    assert restored.get_price_sample_at_or_after("EUR/USD", 1001, 2) is None
    assert restored.health()["quote_evidence_store"]["load_state"] == "EMPTY"


def test_late_and_unsorted_rows_do_not_rewind_live_price_and_survive_restart(tmp_path):
    clock = [1010.0]
    first = feed_at(tmp_path, clock)
    first.ingest_message({"type": "trade", "data": [
        {"s": "OANDA:EUR_USD", "t": 1005125, "p": 1.5},
        {"s": "OANDA:EUR_USD", "t": 1001250, "p": 1.2},
        {"s": "OANDA:EUR_USD", "t": 1001125, "p": 1.1},
        {"s": "OANDA:EUR_USD", "t": 1001125, "p": 1.15},
    ]})
    assert first._last_tick_ms == 1005125
    assert first._candles["M1"][0]["close"] == 1.5
    assert first._out_of_order_tick_count == 3
    selected = first.get_price_sample_at_or_after("EUR/USD", 1001, 0)
    assert selected["price"] == 1.1 and selected["observed_ts"] == 1001
    assert not any(key.startswith("_") for key in selected)
    restored = feed_at(tmp_path, clock)
    assert restored.get_price_sample_at_or_after("EUR/USD", 1001, 0)["price"] == 1.1
    assert list(restored._real_quote_buffer)[2]["_received_ts"] == 1010


def test_future_tick_is_quarantined_without_poisoning_live_high_water(tmp_path):
    clock = [1005.0]
    feed = feed_at(tmp_path, clock)
    tick(feed, 1007000, 7.0)
    assert feed._last_tick_ms is None and not feed.health()["fresh"]
    assert feed.get_price_sample_at_or_after("EUR/USD", 1007, 0) is None
    tick(feed, 1005000, 1.1)
    assert feed._last_tick_ms == 1005000
    assert feed._candles["M1"][0]["close"] == 1.1
    assert feed.health()["future_tick_quarantined_count"] == 1
    clock[0] = 1008
    assert feed.get_price_sample_at_or_after("EUR/USD", 1007, 0)["price"] == 7.0
    assert feed._last_tick_ms == 1005000  # becoming historical evidence is not live readiness


def test_blocked_then_failing_quote_disk_does_not_block_receiver(tmp_path, monkeypatch):
    from runtime import quote_evidence_store as module

    clock = [1010.0]
    feed = feed_at(tmp_path, clock)
    entered, release = Event(), Event()

    def failing_fsync(_fd):
        entered.set()
        assert release.wait(5)
        raise OSError("PRIVATE_PATH_AND_TOKEN")

    monkeypatch.setattr(module.os, "fsync", failing_fsync)
    feed._quote_store.start()
    try:
        tick(feed, 1001000, 1.1)
        assert entered.wait(3)
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(tick, feed, 1002000, 1.2)
            result.result(timeout=2)  # must return while disk remains blocked
        assert not release.is_set()
        assert feed._last_tick_ms == 1002000
        assert feed.get_price_sample_at_or_after("EUR/USD", 1002, 0)["price"] == 1.2
    finally:
        release.set()
        assert feed._quote_store.close() is False
    status = feed.health()["quote_evidence_store"]
    assert status["failure_count"] >= 1 and status["pending_quote_generations"] == 2
    assert "PRIVATE_PATH_AND_TOKEN" not in json.dumps(status)


def test_quote_writer_start_failure_keeps_receiver_live_without_sync_fallback(tmp_path, monkeypatch):
    from runtime import quote_evidence_store as module

    feed = feed_at(tmp_path, [1010.0])

    class FailedWriter:
        def __init__(self, callback):
            pass

        def start(self):
            raise RuntimeError("PRIVATE_THREAD_START_DETAILS")

    monkeypatch.setattr(module, "CandleStoreWriter", FailedWriter)
    monkeypatch.setattr(feed._quote_store, "persist", lambda: pytest.fail("live synchronous disk fallback"))
    observed = []

    def receive():
        tick(feed, 1005000, 1.5)
        observed.append(feed._last_tick_ms)
        assert feed._store_writer.summary()["running"]

    monkeypatch.setattr(feed, "_run_stream", receive)
    feed._stream_forever()
    assert observed == [1005000]
    assert not feed._store_writer.summary()["running"]  # candle worker was drained
    assert feed.get_price_sample_at_or_after("EUR/USD", 1005, 0)["price"] == 1.5
    status = feed.health()["quote_evidence_store"]
    assert status["start_failure_count"] == status["request_failure_count"] == 1
    assert status["mode"] == "ASYNCHRONOUS_COALESCED" and not status["writer_available"]
    assert status["pending_quote_generations"] == 1
    assert "PRIVATE_THREAD_START_DETAILS" not in json.dumps(status)


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(provider="OTHER"),
    lambda p: p.update(provider_symbol="OTHER:EUR_USD"),
    lambda p: p.update(symbol="GBP/USD"),
    lambda p: p["quotes"][0].update(price=float("nan")),
    lambda p: p["quotes"][0].update(provider_tick_ms=True),
    lambda p: p["quotes"][0].update(received_ts=2000),
    lambda p: p["quotes"][0].update(extra="untrusted"),
])
def test_invalid_or_foreign_archive_is_isolated_from_live_ingestion(tmp_path, mutation):
    clock = [1010.0]
    first = feed_at(tmp_path, clock)
    tick(first, 1001000)
    payload = json.loads(first._quote_store.path.read_text())
    mutation(payload)
    first._quote_store.path.write_text(json.dumps(payload))
    restored = feed_at(tmp_path, clock)
    assert restored.health()["quote_evidence_store"]["load_state"] == "UNAVAILABLE"
    assert restored.get_price_sample_at_or_after("EUR/USD", 1001, 0) is None
    tick(restored, 1005000, 1.5)
    assert restored._last_tick_ms == 1005000
    assert restored.get_price_sample_at_or_after("EUR/USD", 1005, 0)["price"] == 1.5


def test_archive_is_bounded_and_reports_evictions_without_fabricating_old_ticks(tmp_path):
    path = tmp_path / "archive.json"
    store = QuoteEvidenceStore(path, max_quotes=2, now_ts=1010)
    for stamp in (1000000, 1001000, 1002000):
        store.record(tick_ms=stamp, price=1.1, received_ts=1010.0)
    store.request()
    assert store.summary()["evicted_quote_count"] == 1
    assert store.summary()["retained_quote_count"] == 2
    assert store.summary()["persisted_quote_generation"] == 3
    restored = QuoteEvidenceStore(path, max_quotes=2, now_ts=1010)
    assert [row["observed_ts"] for row in restored.restored_samples()] == [1001, 1002]
    assert json.loads(path.read_text())["protocol"] == PROTOCOL


def test_symlink_or_corrupt_archive_does_not_supply_quotes(tmp_path):
    target = tmp_path / "external.json"
    target.write_text("not-json")
    path = tmp_path / "archive.json"
    path.symlink_to(target)
    store = QuoteEvidenceStore(path, max_quotes=2, now_ts=1010)
    assert store.summary()["load_state"] == "UNAVAILABLE"
    assert store.restored_samples() == []
    store.record(tick_ms=1000000, price=1.1, received_ts=1010)
    store.request()
    assert store.summary()["failure_count"] == 1
    assert target.read_text() == "not-json"


def test_deeply_nested_corrupt_archive_cannot_abort_live_feed_initialization(tmp_path):
    archive = tmp_path / "market.quotes.json"
    archive.write_text("[" * 20_000 + "]" * 20_000)
    feed = feed_at(tmp_path, [1010.0])
    status = feed.health()["quote_evidence_store"]
    assert status["load_state"] == "UNAVAILABLE" and status["restored_quote_count"] == 0
    assert feed.get_price_sample_at_or_after("EUR/USD", 1001, 0) is None
    tick(feed, 1005000, 1.5)
    assert feed._last_tick_ms == 1005000
    assert feed.get_price_sample_at_or_after("EUR/USD", 1005, 0)["price"] == 1.5
