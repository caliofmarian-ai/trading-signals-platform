from runtime.market_history_integrity import inspect_candles, inspect_history


def _candle(ts: int, *, open_price: float = 1.1, high: float = 1.2, low: float = 1.0, close: float = 1.15):
    return {"ts": ts, "open": open_price, "high": high, "low": low, "close": close}


def test_valid_newest_first_history_passes() -> None:
    report = inspect_candles([_candle(600), _candle(540), _candle(480)], 60)

    assert report["state"] == "VALID"
    assert report["hard_error_count"] == 0
    assert report["gap_count"] == 0


def test_impossible_ohlc_is_invalid() -> None:
    report = inspect_candles([
        _candle(600, open_price=1.3, high=1.2),
        _candle(540),
    ], 60)

    assert report["state"] == "INVALID"
    assert report["invalid_ohlc"] == 1


def test_duplicate_reversed_and_unaligned_timestamps_are_invalid() -> None:
    report = inspect_candles([_candle(601), _candle(601), _candle(660)], 60)

    assert report["state"] == "INVALID"
    assert report["duplicate_timestamps"] == 1
    assert report["out_of_order"] >= 1
    assert report["unaligned_timestamps"] == 2


def test_market_gaps_are_observed_but_not_invented_as_corruption() -> None:
    report = inspect_candles([_candle(600), _candle(420)], 60)

    assert report["state"] == "VALID"
    assert report["gap_count"] == 1
    assert report["hard_error_count"] == 0


def test_combined_history_fails_if_one_timeframe_is_invalid() -> None:
    report = inspect_history({
        "M1": [_candle(600), _candle(540)],
        "M5": [_candle(600), _candle(600)],
    })

    assert report["state"] == "INVALID"
    assert report["hard_error_count"] > 0
