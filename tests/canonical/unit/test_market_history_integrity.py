from datetime import datetime, timezone

from runtime.market_history_integrity import inspect_candles, inspect_history


def _candle(ts: int, *, open_price: float = 1.1, high: float = 1.2, low: float = 1.0, close: float = 1.15):
    return {"ts": ts, "open": open_price, "high": high, "low": low, "close": close}


def _ts(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=timezone.utc).timestamp())


def test_valid_newest_first_history_passes() -> None:
    report = inspect_candles([_candle(600), _candle(540), _candle(480)], 60)

    assert report["state"] == "VALID"
    assert report["temporal_continuity_state"] == "CONTIGUOUS"
    assert report["contiguous_head_count"] == 3
    assert report["hard_error_count"] == 0
    assert report["gap_count"] == 0


def test_impossible_ohlc_is_invalid() -> None:
    report = inspect_candles([
        _candle(600, open_price=1.3, high=1.2),
        _candle(540),
    ], 60)

    assert report["state"] == "INVALID"
    assert report["temporal_continuity_state"] == "INVALID"
    assert report["contiguous_head_count"] == 0
    assert report["invalid_ohlc"] == 1


def test_duplicate_reversed_and_unaligned_timestamps_are_invalid() -> None:
    report = inspect_candles([_candle(601), _candle(601), _candle(660)], 60)

    assert report["state"] == "INVALID"
    assert report["duplicate_timestamps"] == 1
    assert report["out_of_order"] >= 1
    assert report["unaligned_timestamps"] == 2


def test_market_gaps_are_observed_without_fabricating_missing_candles() -> None:
    report = inspect_candles([_candle(600), _candle(540), _candle(360)], 60)

    assert report["state"] == "VALID"
    assert report["temporal_continuity_state"] == "GAPPED"
    assert report["contiguous_head_count"] == 2
    assert report["gap_count"] == 1
    assert report["non_weekend_gap_count"] == 1
    assert report["weekend_gap_count"] == 0
    assert report["hard_error_count"] == 0
    assert report["gap_details"] == [
        {
            "newer_ts": 540,
            "older_ts": 360,
            "delta_seconds": 180,
            "missing_intervals": 2,
            "classification": "NON_WEEKEND_GAP",
        }
    ]


def test_weekend_discontinuity_is_classified_without_inventing_session_hours() -> None:
    monday = _ts(2026, 8, 31, 0, 0)
    friday = _ts(2026, 8, 28, 21, 0)
    report = inspect_candles([_candle(monday), _candle(friday)], 60)

    assert report["state"] == "VALID"
    assert report["temporal_continuity_state"] == "GAPPED"
    assert report["contiguous_head_count"] == 1
    assert report["gap_count"] == 1
    assert report["weekend_gap_count"] == 1
    assert report["non_weekend_gap_count"] == 0
    assert report["gap_details"][0]["classification"] == "WEEKEND_DISCONTINUITY"


def test_combined_history_exposes_per_timeframe_contiguous_counts() -> None:
    report = inspect_history({
        "M1": [_candle(600), _candle(540), _candle(360)],
        "M5": [_candle(600), _candle(300)],
    })

    assert report["state"] == "VALID"
    assert report["temporal_continuity_state"] == "GAPPED"
    assert report["contiguous_candle_counts"] == {"M1": 2, "M5": 2}
    assert report["gap_count"] == 1


def test_combined_history_fails_if_one_timeframe_is_invalid() -> None:
    report = inspect_history({
        "M1": [_candle(600), _candle(540)],
        "M5": [_candle(600), _candle(600)],
    })

    assert report["state"] == "INVALID"
    assert report["temporal_continuity_state"] == "INVALID"
    assert report["hard_error_count"] > 0
