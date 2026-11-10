from __future__ import annotations

import json
import math
import os
from collections import deque
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.market_history_integrity import inspect_candles, inspect_history, summarize_gap_distribution
from runtime.observation_timing import WINDOW, distribution
from runtime.quote_window_diagnostics import MAX_REJECTED_TIMESTAMPS, QuoteWindowDiagnostics


FINNHUB_WS_URL = "wss://ws.finnhub.io"
SUPPORTED_SYMBOL = "EUR/USD"
FINNHUB_SYMBOL = "OANDA:EUR_USD"
MAX_CANDLES = 500
DEFAULT_MIN_CANDLES = 201
# M1 feeds RSI and the 20-interval directional-speed window; EMA200 uses M5.
DEFAULT_MIN_M1_CANDLES = 22  # 21 closed bars plus the currently forming M1 bar
MAX_BUFFERED_REAL_QUOTES = 20_000  # storage bound, not a market/strategy threshold
# Transport guardrails; these never replace quote freshness or history gates.
STREAM_READ_POLL_SECONDS = 5
STREAM_PING_INTERVAL_SECONDS = 20
STREAM_PONG_TIMEOUT_SECONDS = 10


class FinnhubConfigurationError(RuntimeError):
    pass


class FinnhubMarketDataUnavailable(RuntimeError):
    pass


class FinnhubPingTimeout(FinnhubMarketDataUnavailable):
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
        minimum_m1_candles: Optional[int] = None,
        store_path: Optional[Path] = None,
        clock: Any = time.time,
        websocket_connector: Any = None,
        physical_params: Optional[Dict[str, Any]] = None,
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
        self.minimum_m1_candles = int(
            minimum_m1_candles
            if minimum_m1_candles is not None
            else minimum_candles
            if minimum_candles is not None
            else os.getenv("FINNHUB_MIN_M1_CANDLES", str(DEFAULT_MIN_M1_CANDLES))
        )
        if self.freshness_seconds < 1:
            raise FinnhubConfigurationError("MARKET_DATA_FRESHNESS_SECONDS must be positive")
        if self.minimum_candles < 2 or self.minimum_candles > MAX_CANDLES:
            raise FinnhubConfigurationError(
                f"FINNHUB_MIN_CANDLES must be between 2 and {MAX_CANDLES}"
            )
        if self.minimum_m1_candles < 2 or self.minimum_m1_candles > MAX_CANDLES:
            raise FinnhubConfigurationError(
                f"FINNHUB_MIN_M1_CANDLES must be between 2 and {MAX_CANDLES}"
            )
        # Retain the explicit constructor override for existing offline callers.
        # The legacy environment setting now governs M5 only, so an existing
        # FINNHUB_MIN_CANDLES=201 cannot reintroduce the excessive M1 wait.
        self.minimum_candles_by_timeframe = {
            "M1": self.minimum_m1_candles,
            "M5": self.minimum_candles,
        }
        self.history_policy = "STRICT_CONTIGUOUS_CONTEXT"
        self.minimum_contiguous_candles_by_timeframe = dict(self.minimum_candles_by_timeframe)
        if physical_params is not None:
            from core.market_history_policy import requirements
            policy = requirements(physical_params)
            self.history_policy = policy["policy"]
            self.minimum_candles_by_timeframe = {
                code: max(count, self.minimum_candles_by_timeframe[code])
                for code, count in policy["context"].items()
            }
            self.minimum_contiguous_candles_by_timeframe = policy["recent_contiguous"]
            self.minimum_contiguous_candles_by_timeframe["M1"] = self.minimum_candles_by_timeframe["M1"]
        self.store_path = Path(store_path) if store_path is not None else _default_store_path()
        self.clock = clock
        self.websocket_connector = websocket_connector
        self._lock = threading.RLock()
        self._candles: Dict[str, List[Dict[str, Any]]] = {"M1": [], "M5": []}
        self._last_price_ts: Optional[int] = None
        self._last_tick_ms: Optional[int] = None
        self._tick_intervals = deque(maxlen=WINDOW)
        self._tick_receive_ages = deque(maxlen=WINDOW)
        self._real_quote_buffer = deque(maxlen=MAX_BUFFERED_REAL_QUOTES)
        self._quote_window_diagnostics = QuoteWindowDiagnostics()
        self._recent_out_of_order_tick_ms = deque(maxlen=MAX_REJECTED_TIMESTAMPS)
        self._out_of_order_tick_count = 0
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
        self._recovery_after_tick_ms: Optional[int] = None
        self._transport_clock = time.monotonic
        self._transport_state = "NOT_CONNECTED"
        self._transport_idle_read_count = 0
        self._transport_ping_count = 0
        self._transport_pong_count = 0
        self._last_transport_pong_ts: Optional[int] = None
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
        first_trade_seen = False
        for row in rows:
            if not isinstance(row, dict) or row.get("s") != self.finnhub_symbol:
                continue
            if any(isinstance(row.get(key),bool) for key in ("t","p","v")):
                continue
            try:
                tick_ms = int(row["t"])
                price = float(row["p"])
                volume = float(row.get("v") or 0)
            except (KeyError, TypeError, ValueError, OverflowError):
                continue
            if (not 0<tick_ms<2**53 or not math.isfinite(price) or price<=0
                    or not math.isfinite(volume) or volume<0):
                continue
            with self._lock:
                if self._last_tick_ms is not None and tick_ms < self._last_tick_ms:
                    # Evidence only: preserve the existing chronological rejection.
                    self._recent_out_of_order_tick_ms.append(tick_ms)
                    self._out_of_order_tick_count += 1
                    continue
                if self._last_tick_ms is not None and tick_ms > self._last_tick_ms:
                    self._tick_intervals.append((tick_ms-self._last_tick_ms)/1000)
                receive_age=float(self.clock())-tick_ms/1000
                if math.isfinite(receive_age):
                    self._tick_receive_ages.append(receive_age)
                first_trade_seen = first_trade_seen or self._valid_trade_tick_count == 0
                self._last_tick_ms = tick_ms
                self._last_price_ts = tick_ms // 1000
                for code, seconds in (("M1", 60), ("M5", 300)):
                    self._upsert_tick(code, seconds, tick_ms // 1000, price, volume)
                self._real_quote_buffer.append({
                    "provider": "FINNHUB", "symbol": self.symbol, "price": price,
                    "observed_ts": float(tick_ms // 1000),
                    "source": "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1",
                    "_provider_tick_ms": tick_ms,
                })
                self._valid_trade_tick_count += 1
                self._stream_state = "RECEIVING_REAL_TICKS"
                self._subscription_state = "REAL_TICK_CONFIRMED"
                self._stream_last_failure_class = None
            changed = True
        if changed:
            self._persist_store()
            stream_event = "FIRST_REAL_TICK" if first_trade_seen else None
            with self._lock:
                # A reconnect/subscribe alone is not recovery. Require a quote
                # newer than the previous session and fresh at observation.
                # Leave the boundary pending after duplicate/stale/future data.
                if (self._recovery_after_tick_ms is not None
                    and self._last_tick_ms is not None
                    and self._last_tick_ms > self._recovery_after_tick_ms
                    and 0 <= int(self.clock()) - int(self._last_price_ts) <= self.freshness_seconds):
                    stream_event = "REAL_TICK_RESUMED"
                    self._recovery_after_tick_ms = None
            if stream_event is not None:
                self._emit_stream_observation(stream_event)

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
        """Bounded Railway-only, price-free state-change observations.

        A socket connect/subscribe event is NEVER interpreted as received data.
        This does not write historical files, bypass publishing or run new API requests.
        Ordinary diagnostics are throttled to one per event / five minutes.
        Recovery is emitted once per subscription, including rapid reconnects.
        """
        now_ts = int(self.clock())
        with self._lock:
            last = self._last_stream_evidence_emit_ts.get(event)
            if event != "REAL_TICK_RESUMED" and last is not None and 0 <= now_ts - last < 300:
                return
            self._last_stream_evidence_emit_ts[event] = now_ts
            integrity = inspect_history(self._candles)
            head = integrity["contiguous_candle_counts"]
            tick_age = None if self._last_price_ts is None else now_ts - int(self._last_price_ts)
            usable = (
                integrity["state"] == "VALID"
                and self._history_windows_ready(integrity)
                and self._valid_trade_tick_count > 0
                and tick_age is not None
                and 0 <= tick_age <= self.freshness_seconds
            )
            record = {
                "component": "finnhub_stream_readiness",
                "event": event,
                "observed_at": now_ts,
                "price_age_seconds": tick_age,
                "freshness_limit_seconds": self.freshness_seconds,
                "symbol": "EUR/USD",
                "stream_state": self._stream_state,
                "subscription_state": self._subscription_state,
                "connection_attempts": self._stream_connection_attempts,
                "failure_count": self._stream_failure_count,
                "failure_class": self._stream_last_failure_class,
                "transport_state": self._transport_state,
                "transport_idle_read_count": self._transport_idle_read_count,
                "transport_ping_count": self._transport_ping_count,
                "transport_pong_count": self._transport_pong_count,
                "last_transport_pong_ts": self._last_transport_pong_ts,
                "valid_trade_tick_count": self._valid_trade_tick_count,
                "last_real_tick_ts": self._last_price_ts,
                "M1_observed_candles": len(self._candles["M1"]),
                "M5_observed_candles": len(self._candles["M5"]),
                "M1_contiguous_head_count": int(head["M1"]),
                "M5_contiguous_head_count": int(head["M5"]),
                "history_integrity_state": integrity["state"],
                "history_continuity_state": integrity["temporal_continuity_state"],
                "usable_real_history_and_fresh_tick": usable,
                "history_gap_diagnostics": summarize_gap_distribution(self._candles),
                "required_candles_each": (
                    self.minimum_candles
                    if self.minimum_m1_candles == self.minimum_candles else None
                ),
                "required_candles_by_timeframe": dict(self.minimum_candles_by_timeframe),
                "recent_contiguous_required_by_timeframe": dict(self.minimum_contiguous_candles_by_timeframe),
                "history_policy": self.history_policy,
                "no_prices_or_trade_recommendations": True,
                **self._observation_timing(),
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
        if isinstance(exc, FinnhubPingTimeout):
            return "PING_RESPONSE_TIMEOUT"
        if isinstance(exc, FinnhubMarketDataUnavailable):
            return "PROVIDER_ERROR_FRAME"
        allowed = {
            "TimeoutError", "ConnectionError", "ConnectionRefusedError",
            "ConnectionResetError", "BrokenPipeError", "OSError",
            "WebSocketTimeoutException", "WebSocketConnectionClosedException",
            "WebSocketBadStatusException", "WebSocketProtocolException",
        }
        return name if name in allowed else "OTHER_TRANSPORT_ERROR"

    def _receive_stream(self, socket: Any) -> None:
        """Keep transport alive without turning a quiet feed into fresh prices.

        recv_data preserves websocket-client's fragmentation and automatic
        peer-Ping handling while exposing Pongs. Only a matching timely Pong
        confirms our probe; neither it nor a read timeout is a market tick.
        """
        from websocket import ABNF, WebSocketTimeoutException

        last_ping_at = self._transport_clock()
        pending_ping: Optional[bytes] = None
        while not self._stop_event.is_set():
            now = self._transport_clock()
            if pending_ping is not None and now - last_ping_at >= STREAM_PONG_TIMEOUT_SECONDS:
                raise FinnhubPingTimeout("Finnhub WebSocket probe expired")
            if pending_ping is None and now - last_ping_at >= STREAM_PING_INTERVAL_SECONDS:
                pending_ping = os.urandom(8)
                socket.ping(pending_ping)
                last_ping_at = self._transport_clock()
                with self._lock:
                    self._transport_ping_count += 1
                    self._transport_state = "WAITING_PONG"
            # A read must not extend the pending probe's deadline.
            budget = STREAM_PONG_TIMEOUT_SECONDS if pending_ping is not None else STREAM_PING_INTERVAL_SECONDS
            socket.settimeout(min(STREAM_READ_POLL_SECONDS,
                                  max(0.001, last_ping_at + budget - self._transport_clock())))
            try:
                opcode, frame = socket.recv_data(control_frame=True)
            except WebSocketTimeoutException:
                with self._lock:
                    self._transport_idle_read_count += 1
                continue
            if pending_ping is not None and self._transport_clock() - last_ping_at >= STREAM_PONG_TIMEOUT_SECONDS:
                raise FinnhubPingTimeout("Finnhub WebSocket probe expired")
            if opcode == ABNF.OPCODE_CLOSE:
                raise ConnectionError("Finnhub stream closed")
            if opcode == ABNF.OPCODE_PONG:
                if pending_ping is not None and frame == pending_ping:
                    pending_ping = None
                    with self._lock:
                        self._transport_pong_count += 1
                        self._last_transport_pong_ts = int(self.clock())
                        self._transport_state = "PONG_CONFIRMED"
                    self._emit_stream_observation("TRANSPORT_PONG_CONFIRMED")
                continue
            if opcode in (ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY):
                self.ingest_message(frame)

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
                    self._transport_state = "CONNECTED_UNVERIFIED"
                socket.send(json.dumps({"type": "subscribe", "symbol": self.finnhub_symbol}))
                with self._lock:
                    self._subscription_state = "SENT_UNVERIFIED"
                    self._stream_state = "SUBSCRIBED_WAITING_REAL_TICK"
                    self._recovery_after_tick_ms = self._last_tick_ms
                self._emit_stream_observation("SUBSCRIBE_SENT_UNVERIFIED")
                self._receive_stream(socket)
            except Exception as exc:
                with self._lock:
                    self._stream_failure_count += 1
                    self._stream_last_failure_class = self._safe_transport_failure_class(exc)
                    self._stream_state = "DISCONNECTED_RETRYING"
                    self._subscription_state = "UNVERIFIED_AFTER_DISCONNECT"
                    self._transport_state = "DISCONNECTED"
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
                        self._transport_state = "STOPPED"

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
        # Speed and ATR require recent exact-cadence evidence. Older validated
        # M5 bars remain observed context for EMA and confirmed S/R; they must
        # not be presented as a continuous temporal measurement window.
        contiguous_count = int(integrity["contiguous_candle_counts"].get(code, 0))
        context_minimum = self.minimum_candles_by_timeframe[code]
        if len(candles) < context_minimum:
            raise FinnhubInsufficientHistory(
                f"Finnhub {code} saved context is still collecting: {len(candles)}/{context_minimum} real candles"
            )
        minimum = self.minimum_contiguous_candles_by_timeframe[code]
        if contiguous_count < minimum:
            raise FinnhubInsufficientHistory(
                f"Finnhub {code} history is still collecting: "
                f"{contiguous_count}/{minimum} real candles contiguous "
                f"(stored={len(candles)})"
            )
        age_seconds = int(self.clock()) - int(last_price_ts)
        if age_seconds < 0 or age_seconds > self.freshness_seconds:
            raise FinnhubStaleMarketData(
                f"Finnhub live price is stale: age={age_seconds}s, limit={self.freshness_seconds}s"
            )
        if code == "M5" and self.history_policy != "STRICT_CONTIGUOUS_CONTEXT":
            return candles  # all genuine context; the model bounds temporal math separately
        return candles[:contiguous_count]

    def _history_windows_ready(self, integrity, counts=None) -> bool:
        counts = counts if counts is not None else {code: len(rows) for code, rows in self._candles.items()}
        return all(
            counts[code] >= self.minimum_candles_by_timeframe[code]
            and int(integrity["contiguous_candle_counts"].get(code, 0)) >= minimum
            for code, minimum in self.minimum_contiguous_candles_by_timeframe.items()
        )

    def get_latest_price_sample(self, symbol: str) -> Dict[str, Any]:
        """Read one coherent price/timestamp pair under the ingestion lock.

        Retain existing real-history/freshness checks and second-resolution
        timestamps. Restored candles alone can never become a live sample.
        """
        normalized=normalize_symbol(symbol)
        with self._lock:
            self.get_candles(normalized,"M1")
            newest=self._candles["M1"][0]
            if not newest["ts"]<=self._last_price_ts<newest["ts"]+60:
                raise FinnhubMarketDataUnavailable("Finnhub live observation does not match current M1 candle")
            return {"provider":"FINNHUB","symbol":normalized,"price":float(newest["close"]),
                    "observed_ts":float(self._last_price_ts),"source":"LIVE_STREAM_CURRENT_M1_CLOSE"}

    def _observation_timing(self):
        # Caller holds the same lock as ingestion; no price or raw tick history.
        return {"quote_sample_contract":"ATOMIC_REAL_TICK_PRICE_TIMESTAMP_V1",
                "buffered_real_quote_count":len(self._real_quote_buffer),
                "out_of_order_tick_count":self._out_of_order_tick_count,
                "tick_timing_scope":"LAST_128_POSITIVE_PROVIDER_TIMESTAMP_STEPS_AND_ACCEPTED_TICK_RECEIVE_AGES_IN_THIS_PROCESS",
                "provider_tick_interval_seconds":distribution(self._tick_intervals),
                "provider_tick_receive_age_seconds":distribution(self._tick_receive_ages),
                "provider_tick_intervals_gt_2s":sum(value>2 for value in self._tick_intervals)}

    def get_price_sample_at_or_after(self, symbol, target_ts, max_delay):
        """Earliest retained actual tick in a declared window, never a candle substitute.

        Preserve the existing source-second convention. A late worker may read
        an earlier genuine observation; future ticks and missing windows are
        never replaced with the current price. No provider request is made.
        """
        normalize_symbol(symbol)
        if (type(target_ts) not in (int, float) or type(max_delay) not in (int, float)
            or not math.isfinite(target_ts) or not math.isfinite(max_delay)
            or target_ts <= 0 or max_delay < 0):
            raise ValueError("invalid quote observation window")
        now = float(self.clock())
        selected = diagnostic = None
        with self._lock:
            for sample in self._real_quote_buffer:
                if (target_ts <= sample["observed_ts"] <= min(target_ts + max_delay, now)
                    and sample["_provider_tick_ms"] <= now * 1000):
                    selected = sample
                    break
            result = ({key: value for key, value in selected.items() if key != "_provider_tick_ms"}
                      if selected is not None else None)
            try:
                diagnostic = self._quote_window_diagnostics.observe(
                    samples=self._real_quote_buffer,
                    rejected_tick_ms=self._recent_out_of_order_tick_ms,
                    target_ts=target_ts, max_delay=max_delay, now_ts=now,
                    selected=selected, accepted_tick_count=self._valid_trade_tick_count,
                )
            except Exception:
                pass  # Diagnostic failure must not erase a valid selected quote.
        if diagnostic is not None:
            try:
                # Never print while holding the ingestion lock.
                print("TSP_QUOTE_WINDOW_EVIDENCE " + json.dumps(diagnostic, sort_keys=True), flush=True)
            except Exception:
                pass
        return result

    def get_study_chart_evidence(self, entry_ts, expiry_ts):
        """Read bounded, already retained EUR/USD observations for an expiry chart."""
        if (type(entry_ts) not in (int, float) or type(expiry_ts) not in (int, float)
                or not math.isfinite(entry_ts) or not math.isfinite(expiry_ts)
                or entry_ts <= 0 or expiry_ts <= entry_ts):
            raise ValueError("invalid study chart window")

        # Study entry quotes have second-resolution timestamps. A raw tick from
        # that same second cannot establish a subsequent touch of the buffer.
        first_tick_ts = entry_ts + 1.0
        with self._lock:
            end_ts = min(expiry_ts, float(self.clock()))
            candles = [dict(candle) for candle in self._candles["M1"]
                       if candle["complete"] and entry_ts <= candle["ts"] <= end_ts - 60]
            ticks = []
            for sample in self._real_quote_buffer:
                observed_ts = sample["_provider_tick_ms"] / 1000
                if first_tick_ts <= observed_ts <= end_ts:
                    ticks.append({"observed_ts": observed_ts, "price": sample["price"]})

        if inspect_candles(candles, 60)["state"] == "INVALID":
            candles = []
        return list(reversed(candles)), ticks

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
            transport = {
                "transport_state": self._transport_state,
                "transport_idle_read_count": self._transport_idle_read_count,
                "transport_ping_count": self._transport_ping_count,
                "transport_pong_count": self._transport_pong_count,
                "last_transport_pong_ts": self._last_transport_pong_ts,
            }
            integrity = inspect_history(self._candles)
            observation_timing=self._observation_timing()
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
            **transport,
            "price_age_seconds": age,
            "freshness_limit_seconds": self.freshness_seconds,
            "fresh": age is not None and 0 <= age <= self.freshness_seconds,
            "candle_counts": counts,
            "contiguous_candle_counts": dict(
                integrity.get("contiguous_candle_counts", {})
            ),
            "minimum_candles": self.minimum_candles,
            "minimum_candles_by_timeframe": dict(self.minimum_candles_by_timeframe),
            "minimum_contiguous_candles_by_timeframe": dict(self.minimum_contiguous_candles_by_timeframe),
            "history_policy": self.history_policy,
            "history_ready": (
                integrity["state"] == "VALID"
                and self._history_windows_ready(integrity, counts)
            ),
            "persistence_state": persistence_state,
            "store_load_state": load_state,
            "store_write_state": write_state,
            "restored_candle_counts": restored_counts,
            "last_persisted_ts": last_persisted_ts,
            "integrity_state": integrity["state"],
            "integrity_report": integrity,
            **observation_timing,
        }
