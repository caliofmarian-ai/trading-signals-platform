# /opt/binarybot/core/candle_adapter.py
# BinaryBot — Candle Adapter (normalize + validate)
# Canonical helper to convert external candle payloads into internal Candle dicts.

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _to_int(x: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        if x is None:
            return default
        return int(float(x))
    except Exception:
        return default


def _to_float(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _pick(d: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def normalize(raw: Any, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
    """
    Normalize external candle feed into internal Candle objects (dicts).

    Output candle schema (as per MODULE_INTERFACE_SPEC.md):
      {
        "symbol": str,
        "timeframe": str,
        "ts": int,              # epoch seconds UTC
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": float|None
      }

    Ordering: newest-first (candles[0] is newest).
    """
    if raw is None:
        return []

    # Accept common shapes:
    # - list[dict]
    # - dict with "candles"/"data"/"result"/"items"
    items = raw
    if isinstance(raw, dict):
        items = (
            raw.get("candles")
            or raw.get("data")
            or raw.get("result")
            or raw.get("items")
            or raw.get("history")
            or []
        )

    if not isinstance(items, list):
        return []

    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue

        # Time keys seen in the wild: ts, time, timestamp, t, openTime, closeTime
        ts = _to_int(_pick(it, ["ts", "time", "timestamp", "t", "openTime", "closeTime"]))
        o = _to_float(_pick(it, ["open", "o"]))
        h = _to_float(_pick(it, ["high", "h"]))
        l = _to_float(_pick(it, ["low", "l"]))
        c = _to_float(_pick(it, ["close", "c"]))
        v = _to_float(_pick(it, ["volume", "v", "vol"]), default=None)

        # Some APIs deliver ms timestamps
        if ts is not None and ts > 10_000_000_000:  # > ~year 2286 in seconds => probably ms
            ts = int(ts / 1000)

        if ts is None or o is None or h is None or l is None or c is None:
            continue

        out.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "ts": ts,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v,
            }
        )

    # Ensure newest-first
    out.sort(key=lambda x: x["ts"], reverse=True)
    return out


def validate(candles: List[Dict[str, Any]]) -> None:
    """
    Validate candle ordering and required fields.
    Raises ValueError on failure.
    """
    if candles is None:
        raise ValueError("candles is None")

    # Empty is allowed (engine can decide NO_SIGNAL)
    if len(candles) == 0:
        return

    req = ["symbol", "timeframe", "ts", "open", "high", "low", "close"]
    for i, c in enumerate(candles):
        if not isinstance(c, dict):
            raise ValueError(f"candle[{i}] not dict")
        for k in req:
            if k not in c or c[k] is None:
                raise ValueError(f"candle[{i}] missing field {k}")

    # Newest-first
    for i in range(1, len(candles)):
        if int(candles[i]["ts"]) > int(candles[i - 1]["ts"]):
            raise ValueError("candles ordering invalid: expected newest-first")