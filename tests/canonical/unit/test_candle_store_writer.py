"""Offline concurrency regressions; no market, transport or efficacy claims."""
from copy import deepcopy
import json
from pathlib import Path
import threading
import time

import pytest
from websocket import ABNF

from runtime.candle_store_writer import CandleStoreWriter, PROTOCOL
from runtime.finnhub_market_data import FinnhubForexFeed


def wait_for(predicate, timeout=1):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("condition did not become true")
        time.sleep(.001)


def message(stamp, price=1.1):
    return {"type": "trade", "data": [{"s": "OANDA:EUR_USD", "t": stamp, "p": price, "v": 1}]}


def feed_at(tmp_path, clock=1005):
    return FinnhubForexFeed(token="OFFLINE-ONLY", clock=lambda: clock,
                            store_path=tmp_path / "quotes.json", minimum_candles=2)


def test_idle_start_is_idempotent_and_does_not_write():
    calls = []
    writer = CandleStoreWriter(lambda: calls.append(True))
    writer.start()
    thread = writer._thread
    writer.start()
    assert writer._thread is thread
    assert writer.flush(0) and writer.close()
    assert calls == []


def test_request_requires_started_writer_and_close_prevents_reuse():
    writer = CandleStoreWriter(lambda: None)
    with pytest.raises(RuntimeError):
        writer.request()
    assert writer.close(0)
    with pytest.raises(RuntimeError):
        writer.request()
    with pytest.raises(RuntimeError):
        writer.start()


def test_burst_is_coalesced_without_an_unbounded_payload_queue():
    entered, release = threading.Event(), threading.Event()
    observed = []
    current = [0]

    def persist():
        observed.append(current[0])
        if len(observed) == 1:
            entered.set()
            assert release.wait(2)

    writer = CandleStoreWriter(persist)
    writer.start()
    try:
        writer.request()
        assert entered.wait(1)
        for value in range(1, 10001):
            current[0] = value
            writer.request()
        summary = writer.summary()
        assert summary["pending_generations"] == 10001
        assert summary["market_payload_queue_size"] == 0
        assert summary["successful_writes"] == 0
        assert writer.flush(0) is False
        release.set()
        assert writer.flush()
        assert observed == [0, 10000]
        summary = writer.summary()
        assert summary["persisted_generation"] == 10001
        assert summary["pending_generations"] == 0
        assert summary["successful_writes"] == 2
    finally:
        release.set()
        assert writer.close()


def test_failure_retries_without_new_quote_and_never_logs_exception_contents(monkeypatch):
    import runtime.candle_store_writer as module
    monkeypatch.setattr(module, "RETRY_SECONDS", .01)
    calls = []

    def persist():
        calls.append(True)
        if len(calls) == 1:
            raise OSError("PRIVATE_TOKEN_IN_A_PATH")

    writer = CandleStoreWriter(persist)
    writer.start()
    try:
        writer.request()
        assert writer.flush()
        summary = writer.summary()
        assert summary["failure_count"] == 1
        assert summary["successful_writes"] == 1
        assert summary["last_failure_class"] is None
        assert "PRIVATE_TOKEN" not in json.dumps(summary)
        assert summary["write_seconds"]["sample"] == 2
    finally:
        assert writer.close()


def test_failed_write_is_not_marked_persisted_and_shutdown_does_not_retry_forever():
    def fail():
        raise ValueError("unserializable secret value")

    writer = CandleStoreWriter(fail)
    writer.start()
    writer.request()
    wait_for(lambda: writer.summary()["failure_count"] == 1)
    assert writer.close(1) is False
    summary = writer.summary()
    assert summary["running"] is False
    assert summary["pending_generations"] == 1
    assert summary["persisted_generation"] == 0
    assert summary["last_failure_class"] == "SERIALIZATION_OR_CALLBACK_ERROR"
    assert summary["failure_count"] <= 2
    assert "secret" not in json.dumps(summary)


def test_tick_burst_cannot_defeat_failure_retry_backoff(monkeypatch):
    import runtime.candle_store_writer as module
    monkeypatch.setattr(module, "RETRY_SECONDS", 10)
    writer = CandleStoreWriter(lambda: (_ for _ in ()).throw(OSError()))
    writer.start()
    writer.request()
    wait_for(lambda: writer.summary()["failure_count"] == 1)
    for _ in range(1000):
        writer.request()
    assert writer.flush(.03) is False
    assert writer.summary()["failure_count"] == 1
    assert writer.close(1) is False  # one final attempt, not ten seconds of retry
    assert writer.summary()["failure_count"] == 2


def test_stuck_disk_has_bounded_shutdown_and_truthful_pending_state():
    entered, release = threading.Event(), threading.Event()

    def stuck():
        entered.set()
        assert release.wait(2)

    writer = CandleStoreWriter(stuck)
    writer.start()
    writer.request()
    try:
        assert entered.wait(1)
        assert writer.close(0) is False
        assert writer.summary()["pending_generations"] == 1
        assert writer.summary()["running"] is True
        with pytest.raises(RuntimeError):
            writer.request()
    finally:
        release.set()
        assert writer.close(1)


@pytest.mark.parametrize("value", [-1, True, float("nan"), float("inf"), "1", None])
@pytest.mark.parametrize("method", ["flush", "close"])
def test_invalid_timeout_cannot_turn_shutdown_into_an_unbounded_wait(value, method):
    writer = CandleStoreWriter(lambda: None)
    with pytest.raises(ValueError):
        getattr(writer, method)(value)


def test_timing_samples_are_bounded_and_callback_runs_without_worker_lock():
    writer = None

    def persist():
        assert not writer._condition._is_owned()
        writer.summary()  # must not deadlock callback or concurrent health checks

    writer = CandleStoreWriter(persist)
    writer.start()
    try:
        for _ in range(150):
            writer.request()
            assert writer.flush()
        summary = writer.summary()
        assert summary["write_seconds"]["sample"] == 128
        assert summary["successful_writes"] == 150
        assert summary["protocol"] == PROTOCOL
    finally:
        assert writer.close()


def test_thread_start_failure_does_not_poison_retry(monkeypatch):
    writer = CandleStoreWriter(lambda: None)
    start = threading.Thread.start
    with monkeypatch.context() as patch:
        patch.setattr(threading.Thread, "start", lambda _: (_ for _ in ()).throw(RuntimeError("synthetic")))
        with pytest.raises(RuntimeError):
            writer.start()
        assert writer._thread is None
    writer.start()
    writer.request()
    assert writer.close()


def test_receiver_consumes_next_tick_while_first_disk_write_is_blocked(tmp_path, monkeypatch):
    """Regression: old ingest called persist synchronously before recv_data again."""
    feed = feed_at(tmp_path)
    entered, release, consumed = threading.Event(), threading.Event(), threading.Event()
    persist = feed._persist_store
    writes = []

    def slow_disk():
        writes.append(True)
        if len(writes) == 1:
            entered.set()
            assert release.wait(3)
        persist()

    monkeypatch.setattr(feed, "_persist_store", slow_disk)

    class Socket:
        reads = 0
        closed = False
        def send(self, value):
            assert json.loads(value) == {"type": "subscribe", "symbol": "OANDA:EUR_USD"}
        def settimeout(self, value):
            pass
        def recv_data(self, **kwargs):
            self.reads += 1
            if self.reads == 1:
                return ABNF.OPCODE_TEXT, json.dumps(message(1000000, 1.1))
            if self.reads == 2:
                assert entered.wait(1)
                return ABNF.OPCODE_TEXT, json.dumps(message(1001000, 1.2))
            consumed.set()
            feed.stop()
            return ABNF.OPCODE_PONG, b"not-a-price"
        def close(self):
            self.closed = True

    socket = Socket()
    feed.websocket_connector = lambda *args, **kwargs: socket
    thread = threading.Thread(target=feed._stream_forever)
    thread.start()
    try:
        assert consumed.wait(1), "second frame was blocked by candle persistence"
        assert not release.is_set()
        assert feed._valid_trade_tick_count == 2
        assert feed.get_price_sample_at_or_after("EURUSD", 1001, 0)["price"] == 1.2
        assert feed._store_writer.summary()["pending_generations"] == 2
    finally:
        release.set()
        thread.join(3)
        assert not thread.is_alive()
    assert socket.closed
    assert json.loads(feed.store_path.read_text())["candles"]["M1"][0]["close"] == 1.2
    assert feed._store_writer.summary()["pending_generations"] == 0


def test_snapshot_is_frozen_before_serializing_and_does_not_hold_quote_lock(tmp_path, monkeypatch):
    feed = feed_at(tmp_path)
    feed.ingest_message(message(1000000, 1.1))
    writer = CandleStoreWriter(feed._persist_store)
    writer.start()
    feed._store_writer = writer
    entered, release = threading.Event(), threading.Event()
    snapshots = []
    real_dumps = json.dumps

    def delayed_dumps(payload, *args, **kwargs):
        if isinstance(payload, dict) and "candles" in payload:
            assert not feed._lock._is_owned()
            if not snapshots:
                snapshots.append(payload)
                entered.set()
                assert release.wait(2)
            else:
                snapshots.append(payload)
        return real_dumps(payload, *args, **kwargs)

    monkeypatch.setattr(json, "dumps", delayed_dumps)
    try:
        writer.request()
        assert entered.wait(1)
        feed.ingest_message(message(1001000, 1.2))
        assert snapshots[0]["candles"]["M1"][0]["close"] == 1.1
        assert feed._candles["M1"][0]["close"] == 1.2
        release.set()
        assert writer.flush()
        assert json.loads(feed.store_path.read_text())["candles"]["M1"][0]["close"] == 1.2
    finally:
        release.set()
        assert writer.close()


@pytest.mark.parametrize("recover", [False, True])
def test_disk_error_does_not_reconnect_socket_or_discard_next_frame(tmp_path, monkeypatch, recover):
    feed = feed_at(tmp_path)
    error_seen = threading.Event()
    write = Path.write_text
    attempts = []

    def failing_disk(path, *args, **kwargs):
        if path.suffix == ".tmp":
            attempts.append(True)
            if len(attempts) == 1 or not recover:
                error_seen.set()
                raise OSError("PRIVATE_DISK_PATH")
        return write(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", failing_disk)

    class Socket:
        reads = 0
        def send(self, value):
            pass
        def settimeout(self, value):
            pass
        def recv_data(self, **kwargs):
            self.reads += 1
            if self.reads == 1:
                return ABNF.OPCODE_TEXT, json.dumps(message(1000000))
            if self.reads == 2:
                assert error_seen.wait(1)
                return ABNF.OPCODE_TEXT, json.dumps(message(1001000, 1.2))
            feed.stop()
            return ABNF.OPCODE_PONG, b"ignore"
        def close(self):
            pass

    socket = Socket()
    connections = []
    def connect(*args, **kwargs):
        connections.append(True)
        assert len(connections) == 1
        return socket
    feed.websocket_connector = connect
    feed._stream_forever()
    assert feed._valid_trade_tick_count == 2
    assert feed._stream_failure_count == 0
    health = feed.health()
    assert health["candle_store_writer"]["failure_count"] >= 1
    assert health["candle_store_writer"]["pending_generations"] == (0 if recover else 2)
    assert health["store_write_state"] == ("OK" if recover else "ERROR")
    assert "PRIVATE_DISK_PATH" not in json.dumps(health)
    assert feed.get_price_sample_at_or_after("EUR/USD", 1001, 0)["price"] == 1.2


def test_atomic_failure_preserves_previous_saved_history(tmp_path, monkeypatch):
    feed = feed_at(tmp_path)
    feed.ingest_message(message(1000000, 1.1))
    before = feed.store_path.read_bytes()
    feed._candles["M1"][0]["close"] = 1.2
    monkeypatch.setattr(Path, "replace", lambda *args: (_ for _ in ()).throw(OSError()))
    writer = CandleStoreWriter(feed._persist_store)
    writer.start()
    writer.request()
    assert writer.close(1) is False
    assert feed.store_path.read_bytes() == before
    assert feed._store_write_state == "ERROR"


def test_direct_ingest_stays_synchronous_and_saved_candles_are_not_live_ticks(tmp_path):
    feed = feed_at(tmp_path)
    feed.ingest_message(message(1000000, 1.1))
    assert feed.store_path.exists()
    assert feed.store_path.stat().st_mode & 0o777 == 0o600
    assert feed.health()["candle_store_writer"] == {"mode": "SYNCHRONOUS_DIRECT_INGEST"}
    restored = feed_at(tmp_path)
    assert restored._candles["M1"]
    assert restored._last_price_ts is None
    assert restored.get_price_sample_at_or_after("EUR/USD", 1000, 2) is None


def test_async_persistence_does_not_change_quote_selection_or_reject_policy(tmp_path):
    feed = feed_at(tmp_path)
    writer = CandleStoreWriter(feed._persist_store)
    writer.start()
    feed._store_writer = writer
    try:
        for stamp, price in ((999900, 1.1), (1000900, 1.2), (999950, 1.3), (1007000, 1.4)):
            feed.ingest_message(message(stamp, price))
        before = deepcopy(list(feed._real_quote_buffer))
        for target in (999, 1000, 1000.5, 1001, 1003, 1007):
            for delay in (0, .5, 2, 10):
                expected = next(({k: v for k, v in row.items() if k != "_provider_tick_ms"}
                                 for row in before if target <= row["observed_ts"] <= min(target + delay, 1005)
                                 and row["_provider_tick_ms"] <= 1005000), None)
                assert feed.get_price_sample_at_or_after("EUR/USD", target, delay) == expected
        assert writer.flush()
        assert list(feed._real_quote_buffer) == before
        assert feed._out_of_order_tick_count == 1
        assert feed.get_price_sample_at_or_after("EUR/USD", 1003, 2) is None
        assert feed.get_price_sample_at_or_after("EUR/USD", 1007, 0) is None  # raw future tick
    finally:
        assert writer.close()


def test_feed_never_starts_a_second_writer_over_an_existing_instance(tmp_path, monkeypatch):
    feed = feed_at(tmp_path)
    writer = CandleStoreWriter(feed._persist_store)
    writer.start()
    feed._store_writer = writer
    monkeypatch.setattr(feed, "_connect", lambda: pytest.fail("duplicate socket"))
    try:
        with pytest.raises(RuntimeError, match="already been started"):
            feed._stream_forever()
    finally:
        assert writer.close()
