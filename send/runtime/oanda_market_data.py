from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests


PRACTICE_REST_URL = "https://api-fxpractice.oanda.com"
PRACTICE_STREAM_URL = "https://stream-fxpractice.oanda.com"
SUPPORTED_SYMBOL = "EUR/USD"
MAX_CANDLES = 500


class OandaConfigurationError(RuntimeError):
    pass


class OandaMarketDataUnavailable(RuntimeError):
    pass


class OandaStaleMarketData(OandaMarketDataUnavailable):
    pass


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise OandaConfigurationError(f"{name} missing")
    return value


def normalize_symbol(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper().replace("_", "/")
    if normalized != SUPPORTED_SYMBOL:
        raise OandaConfigurationError(
            f"OANDA foundation is restricted to {SUPPORTED_SYMBOL}; received {symbol!r}"
        )
    return normalized


def instrument_name(symbol: str) -> str:
    return normalize_symbol(symbol).replace("/", "_")


def granularity(timeframe: str) -> tuple[str, int]:
    value = str(timeframe or "").strip().upper()
    mapping = {
        "1MIN": ("M1", 60),
        "M1": ("M1", 60),
        "5MIN": ("M5", 300),
        "M5": ("M5", 300),
    }
    if value not in mapping:
        raise OandaConfigurationError(f"Unsupported OANDA timeframe: {timeframe!r}")
    return mapping[value]


def _parse_oanda_ts(value: str) -> int:
    cleaned = str(value).strip().replace("Z", "+00:00")
    return int(datetime.fromisoformat(cleaned).timestamp())


def _mid_price(price: Dict[str, Any]) -> float:
    bids = price.get("bids") if isinstance(price.get("bids"), list) else []
    asks = price.get("asks") if isinstance(price.get("asks"), list) else []
    if not bids or not asks:
        raise OandaMarketDataUnavailable("OANDA price is missing bid or ask")
    bid = float(bids[0]["price"])
    ask = float(asks[0]["price"])
    return (bid + ask) / 2.0


class OandaPracticeFeed:
    """One-symbol OANDA Practice feed with local M1/M5 candle construction."""

    def __init__(
        self,
        *,
        token: Optional[str] = None,
        account_id: Optional[str] = None,
        symbol: str = SUPPORTED_SYMBOL,
        freshness_seconds: Optional[int] = None,
        session: Any = requests,
        clock: Any = time.time,
    ) -> None:
        self.token = token or _required_env("OANDA_API_TOKEN")
        self.account_id = account_id or _required_env("OANDA_ACCOUNT_ID")
        self.symbol = normalize_symbol(symbol)
        self.freshness_seconds = int(
            freshness_seconds
            if freshness_seconds is not None
            else os.getenv("MARKET_DATA_FRESHNESS_SECONDS", "10")
        )
        if self.freshness_seconds < 1:
            raise OandaConfigurationError("MARKET_DATA_FRESHNESS_SECONDS must be positive")
        self.session = session
        self.clock = clock
        self._lock = threading.RLock()
        self._candles: Dict[str, List[Dict[str, Any]]] = {"M1": [], "M5": []}
        self._last_price_ts: Optional[int] = None
        self._stream_started = False
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _historical_url(self) -> str:
        return f"{PRACTICE_REST_URL}/v3/instruments/{instrument_name(self.symbol)}/candles"

    def _stream_url(self) -> str:
        return f"{PRACTICE_STREAM_URL}/v3/accounts/{self.account_id}/pricing/stream"

    def fetch_history(self, timeframe: str, count: int = 250) -> List[Dict[str, Any]]:
        code, _seconds = granularity(timeframe)
        bounded_count = max(1, min(int(count), MAX_CANDLES))
        response = self.session.get(
            self._historical_url(),
            headers=self.headers,
            params={
                "price": "M",
                "granularity": code,
                "count": bounded_count,
                "smooth": "false",
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise OandaMarketDataUnavailable(
                f"OANDA candles request failed with HTTP {response.status_code}"
            )
        payload = response.json()
        rows = payload.get("candles") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise OandaMarketDataUnavailable("OANDA candles response is invalid")

        candles: List[Dict[str, Any]] = []
        for row in rows:
            mid = row.get("mid") if isinstance(row, dict) else None
            if not isinstance(mid, dict):
                continue
            candles.append(
                {
                    "symbol": self.symbol,
                    "timeframe": code,
                    "ts": _parse_oanda_ts(row["time"]),
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": float(row.get("volume") or 0),
                    "complete": bool(row.get("complete")),
                    "provider": "OANDA_PRACTICE",
                }
            )
        candles.sort(key=lambda item: item["ts"], reverse=True)
        if not candles:
            raise OandaMarketDataUnavailable("OANDA returned no usable candles")
        return candles

    def bootstrap(self, count: int = 250) -> None:
        histories = {
            "M1": self.fetch_history("M1", count=count),
            "M5": self.fetch_history("M5", count=count),
        }
        with self._lock:
            self._candles = histories

    def ingest_price(self, price_event: Dict[str, Any]) -> None:
        if str(price_event.get("type") or "").upper() != "PRICE":
            return
        if instrument_name(self.symbol) != str(price_event.get("instrument") or ""):
            return
        ts = _parse_oanda_ts(price_event["time"])
        price = _mid_price(price_event)
        with self._lock:
            if self._last_price_ts is not None and ts < self._last_price_ts:
                return
            self._last_price_ts = ts
            for code, seconds in (("M1", 60), ("M5", 300)):
                self._upsert_tick(code, seconds, ts, price)

    def _upsert_tick(self, code: str, seconds: int, ts: int, price: float) -> None:
        bucket_ts = ts - (ts % seconds)
        candles = self._candles.setdefault(code, [])
        existing = next((row for row in candles if int(row["ts"]) == bucket_ts), None)
        if existing is None:
            candles.insert(
                0,
                {
                    "symbol": self.symbol,
                    "timeframe": code,
                    "ts": bucket_ts,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 0.0,
                    "complete": False,
                    "provider": "OANDA_PRACTICE",
                },
            )
        else:
            existing["high"] = max(float(existing["high"]), price)
            existing["low"] = min(float(existing["low"]), price)
            existing["close"] = price
            existing["complete"] = False
        candles.sort(key=lambda item: int(item["ts"]), reverse=True)
        for older in candles[1:]:
            older["complete"] = True
        del candles[MAX_CANDLES:]

    def _iter_stream_lines(self) -> Iterable[bytes]:
        response = self.session.get(
            self._stream_url(),
            headers=self.headers,
            params={"instruments": instrument_name(self.symbol), "snapshot": "true"},
            timeout=(10, 90),
            stream=True,
        )
        if response.status_code != 200:
            raise OandaMarketDataUnavailable(
                f"OANDA pricing stream failed with HTTP {response.status_code}"
            )
        return response.iter_lines()

    def _stream_forever(self) -> None:
        while not self._stop_event.is_set():
            try:
                for raw_line in self._iter_stream_lines():
                    if self._stop_event.is_set():
                        return
                    if not raw_line:
                        continue
                    payload = json.loads(raw_line.decode("utf-8"))
                    self.ingest_price(payload)
            except Exception:
                if self._stop_event.wait(2.0):
                    return

    def start(self) -> None:
        with self._lock:
            if self._stream_started:
                return
            if not self._candles["M1"] or not self._candles["M5"]:
                self.bootstrap()
            self._stream_started = True
            self._stream_thread = threading.Thread(
                target=self._stream_forever,
                name="oanda-practice-price-stream",
                daemon=True,
            )
            self._stream_thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def get_candles(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        normalize_symbol(symbol)
        code, _seconds = granularity(timeframe)
        self.start()
        with self._lock:
            last_price_ts = self._last_price_ts
            candles = [dict(row) for row in self._candles[code]]
        if last_price_ts is None:
            raise OandaMarketDataUnavailable("OANDA live price has not been received yet")
        age_seconds = int(self.clock()) - int(last_price_ts)
        if age_seconds < 0 or age_seconds > self.freshness_seconds:
            raise OandaStaleMarketData(
                f"OANDA live price is stale: age={age_seconds}s, limit={self.freshness_seconds}s"
            )
        return candles

    def health(self) -> Dict[str, Any]:
        with self._lock:
            last_price_ts = self._last_price_ts
        age = None if last_price_ts is None else int(self.clock()) - int(last_price_ts)
        return {
            "provider": "OANDA_PRACTICE",
            "symbol": self.symbol,
            "last_price_ts": last_price_ts,
            "price_age_seconds": age,
            "freshness_limit_seconds": self.freshness_seconds,
            "fresh": age is not None and 0 <= age <= self.freshness_seconds,
        }
