from __future__ import annotations

from typing import Any


def make_signal_event(signal_id: str = "sig-001", stage: str = "OPEN_NOW", **overrides: Any) -> dict[str, Any]:
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
        "expiry_minutes": 5,
        "candle_ts": 1720000000,
        "created_ts": 1720000001,
        "payload": {"price": 1.1001},
    }
    event.update(overrides)
    return event


def make_candles(symbol: str = "EURUSD", timeframe: str = "M1") -> list[dict[str, Any]]:
    candles = []
    for i in range(30):
        ts = 1720000000 + i * 60
        base = 1.1000 + (i * 0.0002)
        candles.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "ts": ts,
                "open": base,
                "high": base + 0.0004,
                "low": base - 0.0002,
                "close": base + 0.0003,
                "volume": 100 + i,
            }
        )
    return candles
