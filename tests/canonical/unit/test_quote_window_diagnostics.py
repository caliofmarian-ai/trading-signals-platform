"""Synthetic quote-gap evidence; no network and no calibration/efficacy claim."""
from copy import deepcopy
import json

import pytest

from runtime.finnhub_market_data import FinnhubForexFeed
from runtime.quote_window_diagnostics import (
    MAX_EVENTS_PER_MINUTE, MAX_REJECTED_TIMESTAMPS, MAX_TRACKED_WINDOWS,
    QuoteWindowDiagnostics,
)


def _sample(ms, price=1.1):
    return {"observed_ts": float(ms // 1000), "_provider_tick_ms": ms,
            "price": price, "provider": "FINNHUB", "symbol": "EUR/USD",
            "source": "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1"}


def _observe(probe, samples, *, target=1000, delay=2, now=1006, selected=None, rejected=(), count=None):
    return probe.observe(samples=samples, rejected_tick_ms=rejected, target_ts=target,
                         max_delay=delay, now_ts=now, selected=selected,
                         accepted_tick_count=len(samples) if count is None else count)


def _feed(tmp_path, clock):
    feed = FinnhubForexFeed(token="OFFLINE_ONLY_NOT_A_SECRET", clock=lambda: clock[0],
                           store_path=tmp_path / "quotes.json", minimum_candles=2)
    feed._stream_started = True
    return feed


def _tick(feed, ms, price=1.1):
    feed.ingest_message({"type": "trade", "data": [{"s": "OANDA:EUR_USD", "t": ms, "p": price}]})


def _records(capsys):
    prefix = "TSP_QUOTE_WINDOW_EVIDENCE "
    return [json.loads(line[len(prefix):]) for line in capsys.readouterr().out.splitlines()
            if line.startswith(prefix)]


def test_bracketing_source_gap_is_price_free_and_not_a_terminal_outcome():
    samples = [_sample(999900, 999.123), _sample(1003050, 888.321)]
    samples[0]["token"] = "MUST_NOT_BE_LOGGED"
    before = deepcopy(samples)
    record = _observe(QuoteWindowDiagnostics(), samples)
    assert record["reason"] == "BRACKETED_WITHOUT_ELIGIBLE_TICK"
    assert (record["nearest_before_source_ts"], record["nearest_after_source_ts"]) == (999, 1003)
    assert record["bracketing_gap_seconds"] == 4
    assert record["lookup_after_window_seconds"] == 4
    assert record["terminal_outcome"] is False and record["changes_sampling_policy"] is False
    serialized = json.dumps(record, allow_nan=False)
    assert all(value not in serialized for value in ("999.123", "888.321", "MUST_NOT_BE_LOGGED"))
    assert samples == before


@pytest.mark.parametrize("samples,reason", [
    ([], "NO_RETAINED_REAL_TICKS"),
    ([_sample(999000)], "NO_TICK_REACHED_WINDOW"),
    ([_sample(1004000)], "WINDOW_BEFORE_RETAINED_TICKS"),
])
def test_missing_causes_are_not_conflated_with_provider_outage(samples, reason):
    record = _observe(QuoteWindowDiagnostics(), samples)
    assert record["reason"] == reason
    assert "outage" not in json.dumps(record).lower()


def test_eviction_is_a_count_not_an_invented_reason_for_every_missing_window():
    record = _observe(QuoteWindowDiagnostics(), [_sample(1004000)], count=20)
    assert record["evicted_quote_count_in_process"] == 19
    assert record["reason"] == "WINDOW_BEFORE_RETAINED_TICKS"


def test_no_missing_event_before_end_and_no_noise_for_normal_success():
    probe = QuoteWindowDiagnostics()
    assert _observe(probe, [], now=1001.9) is None
    sample = _sample(1001000)
    assert _observe(probe, [sample], selected=sample) is None
    assert not probe.windows


def test_missing_reason_transition_and_observation_found_are_reported_once():
    probe = QuoteWindowDiagnostics()
    assert _observe(probe, [_sample(999000)], now=1002)["reason"] == "NO_TICK_REACHED_WINDOW"
    assert _observe(probe, [_sample(999000)], now=1003) is None
    samples = [_sample(999000), _sample(1004000)]
    assert _observe(probe, samples, now=1004)["reason"] == "BRACKETED_WITHOUT_ELIGIBLE_TICK"
    found = _sample(1001000)
    record = _observe(probe, samples + [found], now=1005, selected=found)
    assert record["reason"] == "OBSERVATION_FOUND_AFTER_MISS"
    assert record["first_missing_lookup_ts"] == 1002
    assert record["selected_source_ts"] == 1001
    assert record["terminal_outcome"] is False
    assert _observe(probe, samples + [found], now=1006, selected=found) is None


def test_future_tick_is_not_treated_as_missing_provider_data_or_used_early():
    sample = _sample(1000900)
    probe = QuoteWindowDiagnostics()
    record = _observe(probe, [sample], target=1000, delay=0, now=1000.1)
    assert record["reason"] == "FUTURE_TICK_NOT_YET_ELIGIBLE"
    assert record["future_ticks_in_window"] == 1 and record["eligible_retained_count"] == 0
    record = _observe(probe, [sample], target=1000, delay=0, now=1001, selected=sample)
    assert record["reason"] == "OBSERVATION_FOUND_AFTER_MISS"


def test_out_of_order_rejections_are_diagnosed_but_not_promoted_into_quotes():
    record = _observe(QuoteWindowDiagnostics(), [_sample(1004000)], rejected=[1001000])
    assert record["reason"] == "OUT_OF_ORDER_REJECTION_IN_WINDOW"
    assert record["recent_out_of_order_ticks_in_window"] == 1
    assert record["selected_source_ts"] is None


def test_rate_and_memory_bounds_also_hold_when_clock_moves_backwards():
    probe = QuoteWindowDiagnostics()
    emitted = [_observe(probe, [], target=index + 1, delay=0, now=1200)
               for index in range(MAX_TRACKED_WINDOWS + 20)]
    assert sum(item is not None for item in emitted) == MAX_EVENTS_PER_MINUTE
    assert len(probe.windows) == MAX_TRACKED_WINDOWS
    assert probe.suppressed_events == MAX_TRACKED_WINDOWS + 20 - MAX_EVENTS_PER_MINUTE
    assert _observe(probe, [], target=600, now=1199) is None
    resumed = _observe(probe, [], target=601, now=1260)
    assert resumed is not None and resumed["suppressed_diagnostic_events"] > 0
    assert len(probe.windows) == MAX_TRACKED_WINDOWS


@pytest.mark.parametrize("field,value", [
    ("target_ts", True), ("target_ts", 0), ("target_ts", float("nan")),
    ("max_delay", -1), ("max_delay", float("inf")), ("now_ts", float("nan")),
    ("now_ts", 0), ("target_ts", "1000"),
])
def test_invalid_diagnostic_times_are_rejected(field, value):
    args = dict(samples=[], rejected_tick_ms=[], target_ts=1000, max_delay=2,
                now_ts=1006, selected=None, accepted_tick_count=0)
    args[field] = value
    with pytest.raises(ValueError):
        QuoteWindowDiagnostics().observe(**args)


def test_actual_feed_preserves_missing_quote_and_logs_neighbors(tmp_path, capsys):
    feed = _feed(tmp_path, [1006])
    _tick(feed, 999000, 1.2)
    _tick(feed, 1004000, 1.3)
    frozen = deepcopy(list(feed._real_quote_buffer))
    assert feed.get_price_sample_at_or_after("EURUSD", 1000, 2) is None
    assert feed.get_price_sample_at_or_after("EUR/USD", 1000, 2) is None
    records = _records(capsys)
    assert len(records) == 1 and records[0]["reason"] == "BRACKETED_WITHOUT_ELIGIBLE_TICK"
    assert list(feed._real_quote_buffer) == frozen


def test_feed_keeps_out_of_order_rejection_and_records_only_timestamps(tmp_path, capsys):
    feed = _feed(tmp_path, [1006])
    _tick(feed, 1005000, 1.1)
    _tick(feed, 1004000, 7.0)
    assert feed.get_price_sample_at_or_after("EUR/USD", 1004, 0) is None
    records = _records(capsys)
    assert records[0]["reason"] == "OUT_OF_ORDER_REJECTION_IN_WINDOW"
    assert feed._last_tick_ms == 1005000
    assert feed._candles["M1"][0]["close"] == 1.1
    assert len(feed._real_quote_buffer) == 1
    assert list(feed._recent_out_of_order_tick_ms) == [1004000]
    assert feed.health()["out_of_order_tick_count"] == 1


def test_rejection_timestamp_storage_is_bounded(tmp_path):
    feed = _feed(tmp_path, [1006])
    _tick(feed, 1005000)
    for _ in range(MAX_REJECTED_TIMESTAMPS + 20):
        _tick(feed, 1004000)
    assert len(feed._recent_out_of_order_tick_ms) == MAX_REJECTED_TIMESTAMPS
    assert feed._out_of_order_tick_count == MAX_REJECTED_TIMESTAMPS + 20


def test_diagnostic_failure_cannot_erase_a_real_quote_or_create_one(tmp_path, monkeypatch):
    feed = _feed(tmp_path, [1006])
    _tick(feed, 1001000, 1.2)
    def fail(**kwargs):
        raise RuntimeError("synthetic diagnostic failure")
    monkeypatch.setattr(feed._quote_window_diagnostics, "observe", fail)
    found = feed.get_price_sample_at_or_after("EUR/USD", 1000, 2)
    assert found["observed_ts"] == 1001 and found["price"] == 1.2
    assert "_provider_tick_ms" not in found
    found["price"] = 7
    assert feed.get_price_sample_at_or_after("EUR/USD", 1000, 2)["price"] == 1.2
    assert feed.get_price_sample_at_or_after("EUR/USD", 1004, 0) is None


def test_logging_is_outside_feed_lock_and_print_failure_does_not_change_lookup(tmp_path, monkeypatch):
    feed = _feed(tmp_path, [1006])
    _tick(feed, 999000)
    attempts = []
    def fail_print(*args, **kwargs):
        assert not feed._lock._is_owned()
        attempts.append(args[0])
        raise OSError("synthetic unavailable log sink")
    monkeypatch.setattr("builtins.print", fail_print)
    assert feed.get_price_sample_at_or_after("EUR/USD", 1000, 2) is None
    assert len(attempts) == 1


def test_future_selection_and_existing_observation_grace_are_unchanged(tmp_path, capsys):
    clock = [1000.1]
    feed = _feed(tmp_path, clock)
    _tick(feed, 1000900, 1.1)
    assert feed.get_price_sample_at_or_after("EUR/USD", 1000, 0) is None
    clock[0] = 1001
    assert feed.get_price_sample_at_or_after("EUR/USD", 1000, 0)["price"] == 1.1
    records = _records(capsys)
    assert [r["reason"] for r in records] == [
        "FUTURE_TICK_NOT_YET_ELIGIBLE", "OBSERVATION_FOUND_AFTER_MISS"]


def test_restart_does_not_reconstruct_tick_evidence_from_saved_candles(tmp_path, capsys):
    feed = _feed(tmp_path, [1006])
    _tick(feed, 1001000, 1.2)
    restored = _feed(tmp_path, [1006])
    assert restored._candles["M1"]
    assert restored.get_price_sample_at_or_after("EUR/USD", 1000, 2) is None
    assert _records(capsys)[-1]["reason"] == "NO_RETAINED_REAL_TICKS"


@pytest.mark.parametrize("now", [1000.1, 1003.5, 1010, 1200])
def test_diagnostics_do_not_change_reference_selector_for_many_windows(tmp_path, now):
    clock = [1000]
    feed = _feed(tmp_path, clock)
    for ms in (999500, 1000900, 1003000, 1002000, 1006500, 1007000, 1007000):
        _tick(feed, ms)
    clock[0] = now
    # Independent frozen contract: first accepted source-second observation
    # in the inclusive caller window, additionally excluding future raw ticks.
    for target in (999, 1000, 1000.5, 1001, 1003, 1005, 1007, 1010):
        for delay in (0, .5, 2, 10):
            expected = next(({k: v for k, v in row.items() if k != "_provider_tick_ms"}
                             for row in feed._real_quote_buffer
                             if target <= row["observed_ts"] <= min(target + delay, now)
                             and row["_provider_tick_ms"] <= now * 1000), None)
            assert feed.get_price_sample_at_or_after("EUR/USD", target, delay) == expected
