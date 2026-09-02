from __future__ import annotations

from typing import Any


def make_signal_event(signal_id: str = "sig-001", stage: str = "OPEN_NOW", **overrides: Any) -> dict[str, Any]:
    open_now = stage == "OPEN_NOW"
    event = {
        "event_type": "signal_event",
        "stage": stage,
        "signal_id": signal_id,
        "symbol": "EURUSD",
        "timeframe": "M1",
        "direction": "BUY",
        "score_total": 88.0,
        "buffer_mode": "MEDIUM",
        "buffer_price": 0.0006,
        "model_expiry": 5.0,
        "execution_time_available": open_now,
        "confirm_expiry_min_minutes": 4.0 if open_now else None,
        "confirm_expiry_max_minutes": 6.0 if open_now else None,
        "open_now_expiry_minutes": 5.0 if open_now else None,
        "execution_calibration_source": "test-calibration-v1" if open_now else None,
        "expiry_minutes": 5.0 if open_now else None,
        "candle_ts": 1720000000,
        "created_ts": 1720000001,
        "entry_price": 1.1001,
        "payload": {
            "price": 1.1001,
            "cycle_id": "cycle-test-001",
            "strategy_version": "2.0.0",
            "canonical_specification": "ALGO_SPEC_v3.0.0",
        },
    }
    event.update(overrides)
    return event


def make_candles(symbol: str = "EURUSD", timeframe: str = "M1", count: int = 30) -> list[dict[str, Any]]:
    """Build canonical newest-first candles at the declared timeframe cadence."""
    normalized_timeframe = str(timeframe).strip().upper()
    cadence_seconds = {
        "M1": 60,
        "1MIN": 60,
        "M5": 300,
        "5MIN": 300,
    }.get(normalized_timeframe)
    if cadence_seconds is None:
        raise ValueError(f"Unsupported canonical candle timeframe: {timeframe!r}")

    candles = []
    for i in range(count):
        ts = 1720000000 + i * cadence_seconds
        base = 1.1000 + (i * 0.0002)
        candles.append(
            {
                "symbol": symbol,
                "timeframe": normalized_timeframe,
                "ts": ts,
                "open": base,
                "high": base + 0.0004,
                "low": base - 0.0002,
                "close": base + 0.0003,
                "volume": 100 + i,
            }
        )
    return list(reversed(candles))
