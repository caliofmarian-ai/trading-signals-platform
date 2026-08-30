from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


FINNHUB_WS_URL = "wss://ws.finnhub.io"
SUPPORTED_SYMBOL = "EUR/USD"
FINNHUB_SYMBOL = "OANDA:EUR_USD"
MAX_CANDLES = 500
DEFAULT_MIN_CANDLES = 201


class FinnhubConfigurationError(RuntimeError):
    pass


class FinnhubMarketDataUnavailable(RuntimeError):
    pass


class FinnhubStaleMarketData(FinnhubMarketDataUnavailable):
    pass


class FinnhubInsufficientHistory(FinnhubMarketDataUnavailable):
    pass


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise FinnhubConfigurationError(f"{name} missing")
    return value


def normalize_symbol(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper().replace("_", "/")
    if normalized != SUPPORTED_SYMBOL:
        raise FinnhubConfigurationError(
            f"Finnhub foundation is restricted to {SUPPORTED_SYMBOL}; received {symbol!r}"
        )
    return normalized


def timeframe_code(timeframe: str) -> tuple[str, int]:
    value = str(timeframe or "").strip().upper()
    mapping = {
        "1MIN": ("M1", 60),
        "M1": ("M1", 60),
        "5MIN": ("M5", 300),
        "M5": ("M5", 300),
    }
    if value not in mapping:
        raise FinnhubConfigurationError(f"Unsupported Finnhub timeframe: {timeframe!r}")
    return mapping[value]


def _default_store_path() -> Path:
    base = Path(os.getenv("BINARYBOT_BASE_DIR", "/data"))
    configured = os.getenv("FINNHUB_CANDLE_STORE", "").strip()
    return Path(configured) if configured else base / "market_data" / "finnhub_eurusd.json"


class FinnhubForexFeed:
    """One-symbol live Finnhub feed that builds and persists real M1/M5 candles."""

    def __init__(
        self,
        *,
        token: Optional[str] = None,
        symbol: str = SUPPORTED_SYMBOL,
        freshness_seconds: Optional[int] = None,
        minimum_candles: Optional[int] = None,
        store_path: Optional[Path] = None,
        clock: Any = time.time,
        websocket_connector: Any = None,
    ) -> None:
        self.token = token or _required_env("FINNHUB_API_KEY")
        self.symbol = normalize_symbol(symbol)
        self.finnhub_symbol = FINNHUB_SYMBOL
        self.freshness_seconds = int(
            freshness_seconds
            if freshness_seconds is not None
            else os.getenv("MARKET_DATA_FRESHNESS_SECONDS", "10")
        )
        self.minimum_candles = int(
            minimum_candles
            if minimum_candles is not None
            else os.getenv("FINNHUB_MIN_CANDLES", str(DEFAULT_MIN_CANDLES))
        )
        if self.freshness_seconds < 1:
            raise FinnhubConfigurationError("MARKET_DATA_FRESHNESS_SECONDS must be positive")
        if self.minimum_candles < 2 or self.minimum_candles > MAX_CANDLES:
            raise FinnhubConfigurationError(
                f"FINNHUB_MIN_CANDLES must be between 2 and {MAX_CANDLES}"
            )
        self.store_path = Path(store_path) if store_path is not None else _default_store_path()
        self.clock = clock
        self.websocket_connector = websocket_connector
        self._lock = threading.RLock()
        self._candles: Dict[str, List[Dict[str, Any]]] = {"M1": [], "M5": []}
        self._last_price_ts: Optional[int] = None
        self._last_tick_ms: Optional[int] = None
        self._stream_started = False
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._load_store()

    def _connect(self):
        url = f"{FINNHUB_WS_URL}?token={self.token}"
        if self.websocket_connector is not None:
            return self.websocket_connector(url, timeout=30)
        try:
            import websocket
        except ImportError as exc:
            raise FinnhubConfigurationError("websocket-client dependency missing") from exc
        return websocket.create_connection(url, timeout=30)

    def _load_store(self) -> None:
        try:
            payload = json.loads(self.store_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(payload, dict) or payload.get("provider") != "FINNHUB":
            return
        loaded: Dict[str, List[Dict[str, Any]]] = {"M1": [], "M5": []}
        for code in loaded:
            rows = payload.get("candles", {}).get(code, [])
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                try:
                    normalized = {
                        "symbol": self.symbol,
                        "timeframe": code,
                        "ts": int(row["ts"]),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row.get("volume") or 0),
                        "complete": bool(row.get("complete")),
                        "provider": "FINNHUB",
                    }
                except (KeyError, TypeError, ValueError):
                    continue
                if normalized["low"] <= normalized["high"]:
                    loaded[code].append(normalized)
            loaded[code].sort(key=lambda item: item["ts"], reverse=True)
            del loaded[code][MAX_CANDLES:]
        with self._lock:
            self._candles = loaded

    def _persist_store(self) -> None:
        with self._lock:
            payload = {
                "schema_version": "1.0.0",
                "provider": "FINNHUB",
                "symbol": self.symbol,
                "candles": self._candles,
            }
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(self.store_path)

    def ingest_message(self, message: Any) -> None:
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        try:
            payload = json.loads(message) if isinstance(message, str) else message
        except (ValueError, TypeError):
            return
        if not isinstance(payload, dict) or payload.get("type") != "trade":
            return
        rows = payload.get("data")
        if not isinstance(rows, list):
            return
        changed = False
        for row in rows:
            if not isinstance(row, dict) or row.get("s") != self.finnhub_symbol:
                continue
            try:
                tick_ms = int(row["t"])
                price = float(row["p"])
                volume = float(row.get("v") or 0)
            except (KeyError, TypeError, ValueError):
                continue
            if tick_ms <= 0 or price <= 0:
                continue
            with self._lock:
                if self._last_tick_ms is not None and tick_ms < self._last_tick_ms:
                    continue
                self._last_tick_ms = tick_ms
                self._last_price_ts = tick_ms // 1000
                for code, seconds in (("M1", 60), ("M5", 300)):
                    self._upsert_tick(code, seconds, tick_ms // 1000, price, volume)
            changed = True
        if changed:
            self._persist_store()

    def _upsert_tick(
        self, code: str, seconds: int, ts: int, price: float, volume: float
    ) -> None:
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
                    "volume": volume,
                    "complete": False,
                    "provider": "FINNHUB",
                },
            )
        else:
            existing["high"] = max(float(existing["high"]), price)
            existing["low"] = min(float(existing["low"]), price)
            existing["close"] = price
            existing["volume"] = float(existing.get("volume") or 0) + volume
            existing["complete"] = False
        candles.sort(key=lambda item: int(item["ts"]), reverse=True)
        for older in candles[1:]:
            older["complete"] = True
        del candles[MAX_CANDLES:]

    def _stream_forever(self) -> None:
        while not self._stop_event.is_set():
            socket = None
            try:
                socket = self._connect()
                socket.send(json.dumps({"type": "subscribe", "symbol": self.finnhub_symbol}))
                while not self._stop_event.is_set():
                    self.ingest_message(socket.recv())
            except Exception:
                if self._stop_event.wait(2.0):
                    return
            finally:
                if socket is not None:
                    try:
                        socket.close()
                    except Exception:
                        pass

    def start(self) -> None:
        with self._lock:
            if self._stream_started:
                return
            self._stream_started = True
            self._stream_thread = threading.Thread(
                target=self._stream_forever,
                name="finnhub-eurusd-price-stream",
                daemon=True,
            )
            self._stream_thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def get_candles(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        normalize_symbol(symbol)
        code, _seconds = timeframe_code(timeframe)
        self.start()
        with self._lock:
            last_price_ts = self._last_price_ts
            candles = [dict(row) for row in self._candles[code]]
        if last_price_ts is None:
            raise FinnhubMarketDataUnavailable("Finnhub live price has not been received yet")
        if len(candles) < self.minimum_candles:
            raise FinnhubInsufficientHistory(
                f"Finnhub {code} history is still collecting: "
                f"{len(candles)}/{self.minimum_candles} real candles"
            )
        age_seconds = int(self.clock()) - int(last_price_ts)
        if age_seconds < 0 or age_seconds > self.freshness_seconds:
            raise FinnhubStaleMarketData(
                f"Finnhub live price is stale: age={age_seconds}s, limit={self.freshness_seconds}s"
            )
        return candles

    def health(self) -> Dict[str, Any]:
        with self._lock:
            last_price_ts = self._last_price_ts
            counts = {code: len(rows) for code, rows in self._candles.items()}
        age = None if last_price_ts is None else int(self.clock()) - int(last_price_ts)
        return {
            "provider": "FINNHUB",
            "symbol": self.symbol,
            "provider_symbol": self.finnhub_symbol,
            "last_price_ts": last_price_ts,
            "price_age_seconds": age,
            "freshness_limit_seconds": self.freshness_seconds,
            "fresh": age is not None and 0 <= age <= self.freshness_seconds,
            "candle_counts": counts,
            "minimum_candles": self.minimum_candles,
            "history_ready": all(value >= self.minimum_candles for value in counts.values()),
        }
