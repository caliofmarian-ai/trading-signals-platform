"""Approximation reads only bounded real retained Finnhub source observations."""
from copy import deepcopy

import pytest

from runtime import market_client
from runtime.finnhub_market_data import FinnhubConfigurationError, FinnhubForexFeed


def feed(tmp_path, clock=None):
    clock = clock if clock is not None else [1100.0]
    result = FinnhubForexFeed(token="OFFLINE_TEST", clock=lambda: clock[0],
                             store_path=tmp_path / "candles.json", minimum_candles=2)
    result._stream_started = True
    return result


def tick(stream, ms, price=1.1):
    stream.ingest_message({"type": "trade", "data": [{"s": "OANDA:EUR_USD", "t": ms, "p": price}]})


def test_nearest_source_order_ignores_receipt_order_and_exact_expiry_tick(tmp_path):
    stream = feed(tmp_path)
    for ms, price in [(999500, 1.2), (1004000, 1.3), (998000, 8.0),
                      (999900, 1.25), (1002100, 1.35), (1000000, 9.0)]:
        tick(stream, ms, price)
    bracket = stream.get_expiry_quote_bracket("EURUSD", 1000.0)
    assert bracket["before"]["observed_ts"] == 999.9
    assert bracket["after"]["observed_ts"] == 1002.1
    assert bracket["before"]["price"] == 1.25
    assert bracket["after"]["price"] == 1.35
    assert bracket["before"]["provider_tick_ms"] == 999900
    assert bracket["after"]["received_ts"] == 1100.0
    assert bracket["before"]["provider_symbol"] == "OANDA:EUR_USD"


def test_same_source_timestamp_keeps_original_receipt_order(tmp_path):
    stream = feed(tmp_path)
    tick(stream, 999500, 1.2)
    tick(stream, 999500, 8.0)
    tick(stream, 1004000, 1.3)
    tick(stream, 1004000, 9.0)
    bracket = stream.get_expiry_quote_bracket("EUR/USD", 1000)
    assert bracket["before"]["price"] == 1.2
    assert bracket["after"]["price"] == 1.3


def test_bounds_are_sixty_seconds_per_side_and_can_be_tightened(tmp_path):
    stream = feed(tmp_path)
    for ms in (939999, 940000, 1060000, 1060001):
        tick(stream, ms)
    bracket = stream.get_expiry_quote_bracket("EUR/USD", 1000)
    assert bracket["before"]["observed_ts"] == 940
    assert bracket["after"]["observed_ts"] == 1060
    assert stream.get_expiry_quote_bracket("EUR/USD", 1000, 59.999) == {"before": None, "after": None}


def test_future_source_or_receipt_does_not_win_nearest_selection(tmp_path):
    clock = [1005.0]
    stream = feed(tmp_path, clock)
    tick(stream, 998000, 1.2)
    tick(stream, 999000, 9.0)
    stream._real_quote_buffer[-1]["_received_ts"] = 1006.0
    tick(stream, 1006000, 8.0)
    bracket = stream.get_expiry_quote_bracket("EUR/USD", 1000)
    assert bracket["before"]["price"] == 1.2
    assert bracket["after"] is None


@pytest.mark.parametrize("change", [
    {"provider": "TWELVE_DATA"}, {"symbol": "GBP/USD"},
    {"provider_symbol": "OTHER:EUR_USD"}, {"source": "LIVE_STREAM_CURRENT_M1_CLOSE"},
    {"source": []}, {"price": float("nan")}, {"price": 0},
    {"_provider_tick_ms": True}, {"_received_ts": float("nan")},
])
def test_corrupt_or_mismatched_retained_rows_are_not_promoted(tmp_path, change):
    stream = feed(tmp_path)
    tick(stream, 999000, 1.2)
    stream._real_quote_buffer[-1].update(change)
    tick(stream, 1004000, 1.3)
    bracket = stream.get_expiry_quote_bracket("EUR/USD", 1000)
    assert bracket["before"] is None and bracket["after"]["price"] == 1.3


def test_candle_or_incomplete_retained_metadata_never_substitutes_for_quote(tmp_path):
    stream = feed(tmp_path)
    tick(stream, 999000)
    stream._real_quote_buffer[-1].pop("_provider_tick_ms")
    tick(stream, 1004000)
    stream._real_quote_buffer[-1].pop("_received_ts")
    assert stream._candles["M1"]
    assert stream.get_expiry_quote_bracket("EUR/USD", 1000) == {"before": None, "after": None}


def test_neighbors_do_not_change_observed_expiry_selection(tmp_path):
    stream = feed(tmp_path)
    tick(stream, 999900, 1.2)
    tick(stream, 1003000, 1.3)
    assert stream.get_price_sample_at_or_after("EUR/USD", 1000, 2) is None
    bracket = stream.get_expiry_quote_bracket("EUR/USD", 1000)
    assert bracket["before"] and bracket["after"]
    assert stream.get_price_sample_at_or_after("EUR/USD", 1000, 2) is None


def test_archive_restart_preserves_genuine_quotes_without_live_authority(tmp_path):
    first = feed(tmp_path)
    tick(first, 999900, 1.2)
    tick(first, 1004123, 1.3)
    restarted = feed(tmp_path)
    assert restarted._valid_trade_tick_count == 0
    bracket = restarted.get_expiry_quote_bracket("EUR/USD", 1000)
    assert bracket["before"]["source"] == "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1"
    assert bracket["after"]["source"] == "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1"
    assert bracket["after"]["observed_ts"] == 1004.123
    assert bracket["after"]["received_ts"] == 1100
    assert restarted._valid_trade_tick_count == 0


def test_snapshot_copies_under_ingestion_lock_and_processes_outside_it(tmp_path, monkeypatch):
    from intelligence import expiry_price_estimate

    stream = feed(tmp_path)
    tick(stream, 999000, 1.2)
    tick(stream, 1004000, 1.3)
    original = deepcopy(list(stream._real_quote_buffer))

    class GuardedRows(list):
        def __iter__(self):
            assert stream._lock._is_owned()
            return super().__iter__()

    normalize = expiry_price_estimate.normalize_quote

    def outside_lock(*args, **kwargs):
        assert not stream._lock._is_owned()
        return normalize(*args, **kwargs)

    stream._real_quote_buffer = GuardedRows(original)
    monkeypatch.setattr(expiry_price_estimate, "normalize_quote", outside_lock)
    bracket = stream.get_expiry_quote_bracket("EUR/USD", 1000)
    bracket["before"]["price"] = 8.0
    assert stream._real_quote_buffer[0]["price"] == 1.2


def test_getter_never_starts_feed_or_falls_back_to_network(tmp_path, monkeypatch):
    stream = feed(tmp_path)
    tick(stream, 999000)
    tick(stream, 1004000)

    def forbidden(*args, **kwargs):
        raise AssertionError("network/feed creation is forbidden")

    monkeypatch.setattr(stream, "start", forbidden)
    monkeypatch.setattr(market_client, "_finnhub_feed", forbidden)
    monkeypatch.setattr(market_client, "_twelve_data_feed", forbidden)
    monkeypatch.setattr(market_client, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(market_client, "_FINNHUB_FEED", stream)
    assert market_client.get_expiry_quote_bracket("EUR/USD", 1000)["before"]
    monkeypatch.setattr(market_client, "_FINNHUB_FEED", None)
    with pytest.raises(market_client.MarketDataUnavailableError, match="not initialized"):
        market_client.get_expiry_quote_bracket("EUR/USD", 1000)
    monkeypatch.setattr(market_client, "_FINNHUB_FEED", stream)
    monkeypatch.setattr(market_client, "configured_provider", lambda: "TWELVE_DATA")
    with pytest.raises(market_client.MarketDataUnavailableError, match="active Finnhub"):
        market_client.get_expiry_quote_bracket("EUR/USD", 1000)


@pytest.mark.parametrize("target,side_bound", [
    (True, 60), (0, 60), (float("nan"), 60), (float("inf"), 60),
    (1000, True), (1000, 0), (1000, -1), (1000, 60.001), (1000, float("nan")),
])
def test_invalid_or_expanded_lookup_bounds_rejected(tmp_path, target, side_bound):
    with pytest.raises(ValueError):
        feed(tmp_path).get_expiry_quote_bracket("EUR/USD", target, side_bound)


def test_unsupported_symbol_and_wrong_provider_instrument_fail_closed(tmp_path):
    stream = feed(tmp_path)
    tick(stream, 999000)
    tick(stream, 1004000)
    with pytest.raises(FinnhubConfigurationError):
        stream.get_expiry_quote_bracket("GBP/USD", 1000)
    stream.finnhub_symbol = "OTHER:EUR_USD"
    assert stream.get_expiry_quote_bracket("EUR/USD", 1000) == {"before": None, "after": None}
