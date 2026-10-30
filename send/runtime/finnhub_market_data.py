from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.market_history_integrity import inspect_history


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


class FinnhubInvalidHistory(FinnhubMarketDataUnavailable):
    pass


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise FinnhubConfigurationError(f"{name} missing")
    return value


def normalize_symbol(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper().replace("_", "/")
    if normalized == "EURUSD":
        normalized = SUPPORTED_SYMBOL
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
        self._store_load_state = "NOT_ATTEMPTED"
        self._store_write_state = "NOT_ATTEMPTED"
        self._restored_candle_counts: Dict[str, int] = {"M1": 0, "M5": 0}
        self._last_persisted_ts: Optional[int] = None
        self._stream_started = False
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        # Connection != subscription acceptance != actual EUR/USD price.
        # Only real provider ticks can advance strategy readiness.
        self._stream_state = "NOT_STARTED"
        self._subscription_state = "NOT_SENT"
        self._stream_connection_attempts = 0
        self._stream_failure_count = 0
        self._stream_last_failure_class: Optional[str] = None
        self._valid_trade_tick_count = 0
        self._last_stream_connected_ts: Optional[int] = None
        self._last_stream_evidence_emit_ts: Dict[str, int] = {}
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
            self._store_load_state = "EMPTY"
            return
        except (OSError, ValueError, TypeError):
            self._store_load_state = "ERROR"
            return
        if not isinstance(payload, dict) or payload.get("provider") != "FINNHUB":
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
            self._restored_candle_counts = {
                code: len(rows) for code, rows in loaded.items()
            }
            self._store_load_state = "LOADED"

    def _persist_store(self) -> None:
        with self._lock:
            payload = {
                "schema_version": "1.0.0",
                "provider": "FINNHUB",
                "symbol": self.symbol,
                "candles": self._candles,
            }
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            os.chmod(temporary, 0o600)
            temporary.replace(self.store_path)
        except OSError:
            self._store_write_state = "ERROR"
            raise
        self._store_write_state = "OK"
        self._last_persisted_ts = int(self.clock())

    def ingest_message(self, message: Any) -> None:
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        try:
            payload = json.loads(message) if isinstance(message, str) else message
        except (ValueError, TypeError):
            return
        if not isinstance(payload, dict):
            return
        if payload.get("type") == "error":
            # Never persist or print provider error text: it may contain secrets.
            raise FinnhubMarketDataUnavailable("Finnhub provider returned an error frame")
        if payload.get("type") != "trade":
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
                self._valid_trade_tick_count += 1
                self._stream_state = "RECEIVING_REAL_TICKS"
                self._subscription_state = "REAL_TICK_CONFIRMED"
                self._stream_last_failure_class = None
            changed = True
        if changed:
            self._persist_store()
            if self._valid_trade_tick_count == 1:
                self._emit_stream_observation("FIRST_REAL_TICK")

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

    def _emit_stream_observation(self, event: str) -> None:
        """One bounded Railway-only, price-free diagnostic per event / 5 minutes.

        A socket connect/subscribe event is NEVER interpreted as received data.
        This does not write historical files, bypass publishing or run new API requests.
        """
        now_ts = int(self.clock())
        with self._lock:
            last = self._last_stream_evidence_emit_ts.get(event)
            if last is not None and 0 <= now_ts - last < 300:
                return
            self._last_stream_evidence_emit_ts[event] = now_ts
            integrity = inspect_history(self._candles)
            head = integrity["contiguous_candle_counts"]
            tick_age = None if self._last_price_ts is None else now_ts - int(self._last_price_ts)
            usable = (
                integrity["state"] == "VALID"
                and int(head["M1"]) >= self.minimum_candles
                and int(head["M5"]) >= self.minimum_candles
                and self._valid_trade_tick_count > 0
                and tick_age is not None
                and 0 <= tick_age <= self.freshness_seconds
            )
            record = {
                "component": "finnhub_stream_readiness",
                "event": event,
                "symbol": "EUR/USD",
                "stream_state": self._stream_state,
                "subscription_state": self._subscription_state,
                "connection_attempts": self._stream_connection_attempts,
                "failure_count": self._stream_failure_count,
                "failure_class": self._stream_last_failure_class,
                "valid_trade_tick_count": self._valid_trade_tick_count,
                "last_real_tick_ts": self._last_price_ts,
                "M1_observed_candles": len(self._candles["M1"]),
                "M5_observed_candles": len(self._candles["M5"]),
                "M1_contiguous_head_count": int(head["M1"]),
                "M5_contiguous_head_count": int(head["M5"]),
                "history_integrity_state": integrity["state"],
                "history_continuity_state": integrity["temporal_continuity_state"],
                "usable_real_history_and_fresh_tick": usable,
                "required_candles_each": self.minimum_candles,
                "no_prices_or_trade_recommendations": True,
            }
        try:
            print("TSP_FINNHUB_STREAM_EVIDENCE " + json.dumps(record, sort_keys=True), flush=True)
        except Exception:
            # A diagnostic print must never block market-data collection.
            pass

    @staticmethod
    def _safe_transport_failure_class(exc: Exception) -> str:
        # Bounded allowlist: never propagate WebSocket exception messages/URLs
        # (the URL contains an API key).
        name = type(exc).__name__
        if isinstance(exc, FinnhubMarketDataUnavailable):
            return "PROVIDER_ERROR_FRAME"
        allowed = {
            "TimeoutError", "ConnectionError", "ConnectionRefusedError",
            "ConnectionResetError", "BrokenPipeError", "OSError",
            "WebSocketTimeoutException", "WebSocketConnectionClosedException",
            "WebSocketBadStatusException", "WebSocketProtocolException",
        }
        return name if name in allowed else "OTHER_TRANSPORT_ERROR"

    def _stream_forever(self) -> None:
        while not self._stop_event.is_set():
            socket = None
            try:
                with self._lock:
                    self._stream_connection_attempts += 1
                    self._stream_state = "CONNECTING"
                socket = self._connect()
                with self._lock:
                    self._last_stream_connected_ts = int(self.clock())
                    self._stream_state = "CONNECTED_NOT_SUBSCRIBED"
                socket.send(json.dumps({"type": "subscribe", "symbol": self.finnhub_symbol}))
                with self._lock:
                    self._subscription_state = "SENT_UNVERIFIED"
                    self._stream_state = "SUBSCRIBED_WAITING_REAL_TICK"
                self._emit_stream_observation("SUBSCRIBE_SENT_UNVERIFIED")
                while not self._stop_event.is_set():
                    frame = socket.recv()
                    if frame == "" or frame == b"":
                        # A clean close is not a market-data tick.
                        raise ConnectionError("Finnhub stream closed")
                    self.ingest_message(frame)
            except Exception as exc:
                with self._lock:
                    self._stream_failure_count += 1
                    self._stream_last_failure_class = self._safe_transport_failure_class(exc)
                    self._stream_state = "DISCONNECTED_RETRYING"
                    self._subscription_state = "UNVERIFIED_AFTER_DISCONNECT"
                self._emit_stream_observation("STREAM_RETRYING")
                if self._stop_event.wait(2.0):
                    return
            finally:
                if socket is not None:
                    try:
                        socket.close()
                    except Exception:
                        pass
                if self._stop_event.is_set():
                    with self._lock:
                        self._stream_state = "STOPPED"

    def start(self) -> None:
        with self._lock:
            if self._stream_started:
                return
            self._stream_started = True
            self._stream_state = "STARTING"
            self._stream_thread = threading.Thread(
                target=self._stream_forever,
                name="finnhub-eurusd-price-stream",
                daemon=True,
            )
            self._stream_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            self._stream_state = "STOPPED"

    def get_candles(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        normalize_symbol(symbol)
        code, _seconds = timeframe_code(timeframe)
        self.start()
        with self._lock:
            last_price_ts = self._last_price_ts
            candles = [dict(row) for row in self._candles[code]]
            integrity = inspect_history(self._candles)
        if last_price_ts is None:
            raise FinnhubMarketDataUnavailable("Finnhub live price has not been received yet")
        if integrity["state"] == "INVALID":
            raise FinnhubInvalidHistory(
                "Finnhub candle history failed integrity checks: "
                f"hard_errors={integrity['hard_error_count']}"
            )
        # Do not feed an old segment across a weekend or silent-tick gap into
        # temporal physics. A stored bar count is not a usable contiguous count.
        contiguous_count = int(integrity["contiguous_candle_counts"].get(code, 0))
        if contiguous_count < self.minimum_candles:
            raise FinnhubInsufficientHistory(
                f"Finnhub {code} history is still collecting: "
                f"{contiguous_count}/{self.minimum_candles} real candles contiguous "
                f"(stored={len(candles)})"
            )
        age_seconds = int(self.clock()) - int(last_price_ts)
        if age_seconds < 0 or age_seconds > self.freshness_seconds:
            raise FinnhubStaleMarketData(
                f"Finnhub live price is stale: age={age_seconds}s, limit={self.freshness_seconds}s"
            )
        # Return only the current consecutive real bars. Never synthesize bars
        # or let an older disjoint interval influence the strategy indicators.
        return candles[:contiguous_count]

    def health(self) -> Dict[str, Any]:
        with self._lock:
            last_price_ts = self._last_price_ts
            counts = {code: len(rows) for code, rows in self._candles.items()}
            restored_counts = dict(self._restored_candle_counts)
            load_state = self._store_load_state
            write_state = self._store_write_state
            last_persisted_ts = self._last_persisted_ts
            stream_state = self._stream_state
            subscription_state = self._subscription_state
            stream_connection_attempts = self._stream_connection_attempts
            stream_failure_count = self._stream_failure_count
            stream_last_failure_class = self._stream_last_failure_class
            valid_trade_tick_count = self._valid_trade_tick_count
            last_stream_connected_ts = self._last_stream_connected_ts
            integrity = inspect_history(self._candles)
        if load_state == "ERROR" or write_state == "ERROR":
            persistence_state = "ERROR"
        elif load_state == "LOADED" or write_state == "OK":
            persistence_state = "ACTIVE"
        elif load_state == "EMPTY":
            persistence_state = "EMPTY_READY"
        else:
            persistence_state = "UNKNOWN"
        age = None if last_price_ts is None else int(self.clock()) - int(last_price_ts)
        return {
            "provider": "FINNHUB",
            "symbol": self.symbol,
            "provider_symbol": self.finnhub_symbol,
            "last_price_ts": last_price_ts,
            "stream_state": stream_state,
            "subscription_state": subscription_state,
            "stream_connection_attempts": stream_connection_attempts,
            "stream_failure_count": stream_failure_count,
            "stream_last_failure_class": stream_last_failure_class,
            "valid_trade_tick_count": valid_trade_tick_count,
            "last_stream_connected_ts": last_stream_connected_ts,
            "price_age_seconds": age,
            "freshness_limit_seconds": self.freshness_seconds,
            "fresh": age is not None and 0 <= age <= self.freshness_seconds,
            "candle_counts": counts,
            "contiguous_candle_counts": dict(
                integrity.get("contiguous_candle_counts", {})
            ),
            "minimum_candles": self.minimum_candles,
            "history_ready": (
                integrity["state"] == "VALID"
                and all(
                    int(value) >= self.minimum_candles
                    for value in integrity["contiguous_candle_counts"].values()
                )
            ),
            "persistence_state": persistence_state,
            "store_load_state": load_state,
            "store_write_state": write_state,
            "restored_candle_counts": restored_counts,
            "last_persisted_ts": last_persisted_ts,
            "integrity_state": integrity["state"],
            "integrity_report": integrity,
        }
