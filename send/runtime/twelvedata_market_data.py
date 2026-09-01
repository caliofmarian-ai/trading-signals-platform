from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


REST_URL = "https://api.twelvedata.com/time_series"
WS_URL = "wss://ws.twelvedata.com/v1/quotes/price"
MAX_CANDLES = 500
DEFAULT_MIN_CANDLES = 201
DEFAULT_PERSIST_INTERVAL_SECONDS = 5


class TwelveDataConfigurationError(RuntimeError):
    pass


class TwelveDataMarketDataUnavailable(RuntimeError):
    pass


class TwelveDataStaleMarketData(TwelveDataMarketDataUnavailable):
    pass


class TwelveDataInsufficientHistory(TwelveDataMarketDataUnavailable):
    pass


class TwelveDataStreamingUnavailable(TwelveDataMarketDataUnavailable):
    pass


class TwelveDataRateLimitError(RuntimeError):
    pass


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise TwelveDataConfigurationError(f"{name} missing")
    return value


def normalize_symbol(symbol: str) -> str:
    value = str(symbol or "").strip().upper().replace("_", "/")
    if not value or "/" not in value:
        raise TwelveDataConfigurationError(f"Invalid Twelve Data symbol: {symbol!r}")
    return value


def timeframe_code(timeframe: str) -> tuple[str, int, str]:
    value = str(timeframe or "").strip().upper()
    mapping = {
        "1MIN": ("M1", 60, "1min"),
        "M1": ("M1", 60, "1min"),
        "5MIN": ("M5", 300, "5min"),
        "M5": ("M5", 300, "5min"),
    }
    if value not in mapping:
        raise TwelveDataConfigurationError(
            f"Unsupported Twelve Data timeframe: {timeframe!r}"
        )
    return mapping[value]


def _default_store_path(symbol: str) -> Path:
    base = Path(os.getenv("BINARYBOT_BASE_DIR", "/data"))
    configured = os.getenv("TWELVE_DATA_CANDLE_STORE_DIR", "").strip()
    directory = Path(configured) if configured else base / "market_data"
    safe_symbol = normalize_symbol(symbol).replace("/", "_").lower()
    return directory / f"twelvedata_{safe_symbol}.json"


def _parse_datetime(value: str) -> int:
    parsed = datetime.fromisoformat(str(value).strip())
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return int(parsed.timestamp())


class TwelveDataRealtimeFeed:
    """Real Twelve Data history + live-price feed for one configured symbol.

    Historical M1/M5 candles are bootstrapped lazily from /time_series. Live
    price events then update the current M1/M5 candles locally so the engine
    does not need to poll both REST intervals every scan cycle.
    """

    def __init__(
        self,
        *,
        symbol: str,
        token: Optional[str] = None,
        freshness_seconds: Optional[int] = None,
        minimum_candles: Optional[int] = None,
        store_path: Optional[Path] = None,
        clock: Any = time.time,
        websocket_connector: Any = None,
        http_get: Any = requests.get,
        persist_interval_seconds: int = DEFAULT_PERSIST_INTERVAL_SECONDS,
    ) -> None:
        self.token = token or _required_env("TWELVE_DATA_API_KEY")
        self.symbol = normalize_symbol(symbol)
        self.freshness_seconds = int(
            freshness_seconds
            if freshness_seconds is not None
            else os.getenv("MARKET_DATA_FRESHNESS_SECONDS", "10")
        )
        self.minimum_candles = int(
            minimum_candles
            if minimum_candles is not None
            else os.getenv("TWELVE_DATA_MIN_CANDLES", str(DEFAULT_MIN_CANDLES))
        )
        if self.freshness_seconds < 1:
            raise TwelveDataConfigurationError(
                "MARKET_DATA_FRESHNESS_SECONDS must be positive"
            )
        if self.minimum_candles < 2 or self.minimum_candles > MAX_CANDLES:
            raise TwelveDataConfigurationError(
                f"TWELVE_DATA_MIN_CANDLES must be between 2 and {MAX_CANDLES}"
            )
        self.store_path = Path(store_path) if store_path is not None else _default_store_path(self.symbol)
        self.clock = clock
        self.websocket_connector = websocket_connector
        self.http_get = http_get
        self.persist_interval_seconds = max(1, int(persist_interval_seconds))

        self._lock = threading.RLock()
        self._candles: Dict[str, List[Dict[str, Any]]] = {"M1": [], "M5": []}
        self._last_price_ts: Optional[int] = None
        self._last_persisted_ts: Optional[int] = None
        self._bootstrap_state = "NOT_ATTEMPTED"
        self._stream_state = "NOT_STARTED"
        self._stream_error: Optional[str] = None
        self._store_load_state = "NOT_ATTEMPTED"
        self._store_write_state = "NOT_ATTEMPTED"
        self._restored_candle_counts: Dict[str, int] = {"M1": 0, "M5": 0}
        self._stream_started = False
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._load_store()

    def _load_store(self) -> None:
        try:
            payload = json.loads(self.store_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self._store_load_state = "EMPTY"
            return
        except (OSError, ValueError, TypeError):
            self._store_load_state = "ERROR"
            return
        if not isinstance(payload, dict) or payload.get("provider") != "TWELVE_DATA":
            self._store_load_state = "ERROR"
            return
        stored_symbol = payload.get("symbol")
        try:
            stored_symbol = normalize_symbol(stored_symbol)
        except TwelveDataConfigurationError:
            self._store_load_state = "ERROR"
            return
        if stored_symbol != self.symbol:
            self._store_load_state = "ERROR"
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
                        "provider": "TWELVE_DATA",
                    }
                except (KeyError, TypeError, ValueError):
                    continue
                if (
                    normalized["ts"] > 0
                    and normalized["open"] > 0
                    and normalized["low"] > 0
                    and normalized["low"] <= normalized["high"]
                ):
                    loaded[code].append(normalized)
            loaded[code].sort(key=lambda item: int(item["ts"]), reverse=True)
            del loaded[code][MAX_CANDLES:]

        with self._lock:
            self._candles = loaded
            self._restored_candle_counts = {
                code: len(rows) for code, rows in loaded.items()
            }
            self._store_load_state = "LOADED"

    def _persist_store(self, *, force: bool = False) -> None:
        now_ts = int(self.clock())
        if (
            not force
            and self._last_persisted_ts is not None
            and now_ts - int(self._last_persisted_ts) < self.persist_interval_seconds
        ):
            return
        with self._lock:
            payload = {
                "schema_version": "1.0.0",
                "provider": "TWELVE_DATA",
                "symbol": self.symbol,
                "candles": self._candles,
            }
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(payload, separators=(",", ":")), encoding="utf-8"
            )
            os.chmod(temporary, 0o600)
            temporary.replace(self.store_path)
        except OSError:
            self._store_write_state = "ERROR"
            raise
        self._store_write_state = "OK"
        self._last_persisted_ts = now_ts

    def _fetch_history(self, interval: str, code: str, seconds: int) -> List[Dict[str, Any]]:
        response = self.http_get(
            REST_URL,
            params={
                "symbol": self.symbol,
                "interval": interval,
                "outputsize": min(MAX_CANDLES, max(self.minimum_candles + 5, 50)),
                "timezone": "UTC",
                "order": "desc",
                "apikey": self.token,
            },
            timeout=20,
        )
        if response.status_code == 429:
            raise TwelveDataRateLimitError("Twelve Data HTTP 429 during history bootstrap")
        if response.status_code != 200:
            raise TwelveDataMarketDataUnavailable(
                f"Twelve Data history HTTP {response.status_code}"
            )
        payload = response.json()
        rows = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            message = payload.get("message") if isinstance(payload, dict) else payload
            raise TwelveDataMarketDataUnavailable(
                f"Twelve Data history unavailable: {message}"
            )

        now_ts = int(self.clock())
        current_bucket = now_ts - (now_ts % seconds)
        candles: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                ts = _parse_datetime(row["datetime"])
                candle = {
                    "symbol": self.symbol,
                    "timeframe": code,
                    "ts": ts,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0),
                    "complete": ts < current_bucket,
                    "provider": "TWELVE_DATA",
                }
            except (KeyError, TypeError, ValueError):
                continue
            if (
                candle["ts"] > 0
                and candle["open"] > 0
                and candle["low"] > 0
                and candle["low"] <= candle["high"]
            ):
                candles.append(candle)
        candles.sort(key=lambda item: int(item["ts"]), reverse=True)
        del candles[MAX_CANDLES:]
        return candles

    def _ensure_history(self) -> None:
        with self._lock:
            if all(len(rows) >= self.minimum_candles for rows in self._candles.values()):
                if self._bootstrap_state == "NOT_ATTEMPTED":
                    self._bootstrap_state = "RESTORED_READY"
                return
        self._bootstrap_state = "IN_PROGRESS"
        try:
            m1 = self._fetch_history("1min", "M1", 60)
            m5 = self._fetch_history("5min", "M5", 300)
        except TwelveDataRateLimitError:
            self._bootstrap_state = "RATE_LIMITED"
            raise
        except Exception:
            self._bootstrap_state = "ERROR"
            raise
        with self._lock:
            self._candles["M1"] = m1
            self._candles["M5"] = m5
        if len(m1) < self.minimum_candles or len(m5) < self.minimum_candles:
            self._bootstrap_state = "INSUFFICIENT"
            raise TwelveDataInsufficientHistory(
                "Twelve Data history bootstrap returned insufficient real candles: "
                f"M1={len(m1)}, M5={len(m5)}, required={self.minimum_candles}"
            )
        self._bootstrap_state = "READY"
        self._persist_store(force=True)

    def _connect(self):
        url = f"{WS_URL}?apikey={self.token}"
        if self.websocket_connector is not None:
            return self.websocket_connector(url, timeout=30)
        try:
            import websocket
        except ImportError as exc:
            raise TwelveDataConfigurationError(
                "websocket-client dependency missing"
            ) from exc
        return websocket.create_connection(url, timeout=30)

    def ingest_message(self, message: Any) -> None:
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        try:
            payload = json.loads(message) if isinstance(message, str) else message
        except (ValueError, TypeError):
            return
        if not isinstance(payload, dict):
            return

        event = str(payload.get("event") or "").strip().lower()
        if event == "subscribe-status":
            failures = payload.get("fails")
            if isinstance(failures, list):
                failed_symbols = {
                    normalize_symbol(item.get("symbol"))
                    for item in failures
                    if isinstance(item, dict) and item.get("symbol")
                }
                if self.symbol in failed_symbols:
                    self._stream_state = "SUBSCRIPTION_FAILED"
                    self._stream_error = f"Twelve Data WebSocket subscription failed for {self.symbol}"
            successes = payload.get("success")
            if isinstance(successes, list):
                successful_symbols = {
                    normalize_symbol(item.get("symbol"))
                    for item in successes
                    if isinstance(item, dict) and item.get("symbol")
                }
                if self.symbol in successful_symbols:
                    self._stream_state = "SUBSCRIBED"
                    self._stream_error = None
            return

        if event != "price":
            return
        try:
            symbol = normalize_symbol(payload["symbol"])
            ts = int(payload["timestamp"])
            price = float(payload["price"])
        except (KeyError, TypeError, ValueError, TwelveDataConfigurationError):
            return
        if symbol != self.symbol or ts <= 0 or price <= 0:
            return

        with self._lock:
            if self._last_price_ts is not None and ts < self._last_price_ts:
                return
            self._last_price_ts = ts
            self._stream_state = "LIVE"
            self._stream_error = None
            self._upsert_tick("M1", 60, ts, price)
            self._upsert_tick("M5", 300, ts, price)
        self._persist_store()

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
                    "provider": "TWELVE_DATA",
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

    def _stream_forever(self) -> None:
        while not self._stop_event.is_set():
            socket = None
            try:
                self._stream_state = "CONNECTING"
                socket = self._connect()
                socket.send(
                    json.dumps(
                        {"action": "subscribe", "params": {"symbols": self.symbol}}
                    )
                )
                self._stream_state = "SUBSCRIBING"
                last_heartbeat = int(self.clock())
                while not self._stop_event.is_set():
                    message = socket.recv()
                    self.ingest_message(message)
                    now_ts = int(self.clock())
                    if now_ts - last_heartbeat >= 10:
                        socket.send(json.dumps({"action": "heartbeat"}))
                        last_heartbeat = now_ts
                    if self._stream_state == "SUBSCRIPTION_FAILED":
                        raise TwelveDataStreamingUnavailable(
                            self._stream_error or "Twelve Data WebSocket subscription failed"
                        )
            except Exception as exc:
                self._stream_state = "ERROR"
                self._stream_error = str(exc)
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
                name=f"twelvedata-{self.symbol.replace('/', '').lower()}-price-stream",
                daemon=True,
            )
            self._stream_thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def get_candles(self, timeframe: str) -> List[Dict[str, Any]]:
        code, _seconds, _interval = timeframe_code(timeframe)
        self._ensure_history()
        self.start()
        with self._lock:
            candles = [dict(row) for row in self._candles[code]]
            last_price_ts = self._last_price_ts
            stream_state = self._stream_state
            stream_error = self._stream_error
        if stream_state in {"SUBSCRIPTION_FAILED", "ERROR"} and last_price_ts is None:
            raise TwelveDataStreamingUnavailable(
                stream_error or "Twelve Data WebSocket is unavailable"
            )
        if len(candles) < self.minimum_candles:
            raise TwelveDataInsufficientHistory(
                f"Twelve Data {code} history is insufficient: "
                f"{len(candles)}/{self.minimum_candles} real candles"
            )
        if last_price_ts is None:
            raise TwelveDataMarketDataUnavailable(
                "Twelve Data live price has not been received yet"
            )
        age_seconds = int(self.clock()) - int(last_price_ts)
        if age_seconds < 0 or age_seconds > self.freshness_seconds:
            raise TwelveDataStaleMarketData(
                f"Twelve Data live price is stale: age={age_seconds}s, "
                f"limit={self.freshness_seconds}s"
            )
        return candles

    def health(self) -> Dict[str, Any]:
        with self._lock:
            last_price_ts = self._last_price_ts
            counts = {code: len(rows) for code, rows in self._candles.items()}
            restored = dict(self._restored_candle_counts)
            stream_state = self._stream_state
            stream_error = self._stream_error
        age = None if last_price_ts is None else int(self.clock()) - int(last_price_ts)
        return {
            "provider": "TWELVE_DATA",
            "symbol": self.symbol,
            "last_price_ts": last_price_ts,
            "price_age_seconds": age,
            "freshness_limit_seconds": self.freshness_seconds,
            "fresh": age is not None and 0 <= age <= self.freshness_seconds,
            "candle_counts": counts,
            "minimum_candles": self.minimum_candles,
            "history_ready": all(value >= self.minimum_candles for value in counts.values()),
            "bootstrap_state": self._bootstrap_state,
            "stream_state": stream_state,
            "stream_error": stream_error,
            "store_load_state": self._store_load_state,
            "store_write_state": self._store_write_state,
            "restored_candle_counts": restored,
            "last_persisted_ts": self._last_persisted_ts,
        }
