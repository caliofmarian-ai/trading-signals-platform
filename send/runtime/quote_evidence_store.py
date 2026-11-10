"""Bounded durable evidence of genuine received Finnhub ticks.

An archive is historical observation evidence only. It cannot establish live
readiness, current price or candle history. Live writes use a single coalescing
worker: the receiver only appends bounded memory and signals a generation.
"""
from __future__ import annotations

from collections import deque
import json
import math
import os
from pathlib import Path
import tempfile
import threading
from typing import Any

from runtime.candle_store_writer import CandleStoreWriter

PROTOCOL = "DURABLE_FINNHUB_QUOTE_EVIDENCE_V1"
RESTORED_SOURCE = "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1"
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024


def _valid_quote(row: Any, now_ts: float) -> bool:
    return (
        isinstance(row, dict) and set(row) == {"provider_tick_ms", "price", "received_ts"}
        and type(row["provider_tick_ms"]) is int and 0 < row["provider_tick_ms"] < 2**53
        and type(row["price"]) in (int, float) and math.isfinite(row["price"]) and row["price"] > 0
        and type(row["received_ts"]) in (int, float) and math.isfinite(row["received_ts"])
        and 0 < row["received_ts"] <= now_ts
    )


class QuoteEvidenceStore:
    def __init__(self, path: Path, *, max_quotes: int, now_ts: float) -> None:
        if type(max_quotes) is not int or max_quotes <= 0:
            raise ValueError("invalid quote archive bound")
        self.path = Path(path)
        self.max_quotes = max_quotes
        self._lock = threading.Lock()
        self._io_lock = threading.Lock()
        self._quotes: deque[dict] = deque(maxlen=max_quotes)
        self._writer: CandleStoreWriter | None = None
        self._async_requested = False
        self._load_state = "EMPTY"
        self._restored = self._received = self._evicted = 0
        self._generation = self._persisted_generation = 0
        self._writes = self._write_failures = self._request_failures = self._start_failures = 0
        self._last_failure: str | None = None
        self._load(float(now_ts))

    def _load(self, now_ts: float) -> None:
        try:
            if self.path.is_symlink() or self.path.parent.is_symlink():
                raise ValueError("invalid archive path")
            with self.path.open("rb") as handle:
                raw = handle.read(MAX_ARCHIVE_BYTES + 1)
            if len(raw) > MAX_ARCHIVE_BYTES:
                raise ValueError("archive size limit")
            payload = json.loads(raw)
            if (not isinstance(payload, dict)
                    or set(payload) != {"protocol", "provider", "provider_symbol", "symbol", "quotes"}
                    or payload["protocol"] != PROTOCOL or payload["provider"] != "FINNHUB"
                    or payload["provider_symbol"] != "OANDA:EUR_USD"
                    or payload["symbol"] != "EUR/USD" or not isinstance(payload["quotes"], list)
                    or len(payload["quotes"]) > self.max_quotes
                    or not all(_valid_quote(row, now_ts) for row in payload["quotes"])):
                raise ValueError("invalid quote archive")
            self._quotes.extend(dict(row) for row in payload["quotes"])
            self._restored = len(self._quotes)
            self._load_state = "LOADED"
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, OverflowError, RecursionError):
            self._load_state = "UNAVAILABLE"

    def restored_samples(self) -> list[dict]:
        with self._lock:
            return [{"provider": "FINNHUB", "symbol": "EUR/USD", "price": row["price"],
                     "observed_ts": float(row["provider_tick_ms"] // 1000),
                     "source": RESTORED_SOURCE, "_provider_tick_ms": row["provider_tick_ms"],
                     "_received_ts": row["received_ts"]} for row in self._quotes]

    def record(self, *, tick_ms: int, price: float, received_ts: float) -> None:
        row = {"provider_tick_ms": tick_ms, "price": price, "received_ts": received_ts}
        if not _valid_quote(row, received_ts):
            raise ValueError("invalid received quote")
        with self._lock:
            self._evicted += int(len(self._quotes) == self.max_quotes)
            self._quotes.append(row)
            self._received += 1
            self._generation += 1

    def start(self) -> None:
        with self._lock:
            # This mode is sticky even if thread creation fails. A live receiver
            # must never fall back to synchronous filesystem work on that path.
            self._async_requested = True
            if self._writer is None:
                try:
                    writer = CandleStoreWriter(self.persist)
                    writer.start()
                    self._writer = writer
                except Exception:
                    self._start_failures += 1
                    self._last_failure = "WRITER_START_FAILED"

    def request(self) -> None:
        """Isolate archive failures from live ingestion and current market data."""
        writer = self._writer
        if writer is None:
            with self._lock:
                if self._async_requested:
                    self._request_failures += 1
                    self._last_failure = "WRITER_UNAVAILABLE"
                    return
            try:
                self.persist()  # deterministic direct/offline ingestion only
            except Exception:
                pass
        else:
            try:
                writer.request()
            except Exception:
                with self._lock:
                    self._request_failures += 1
                    self._last_failure = "WRITER_UNAVAILABLE"

    def persist(self) -> None:
        temporary = None
        with self._io_lock:
            with self._lock:
                generation = self._generation
                payload = {"protocol": PROTOCOL, "provider": "FINNHUB", "provider_symbol": "OANDA:EUR_USD", "symbol": "EUR/USD",
                           "quotes": [dict(row) for row in self._quotes]}
            try:
                if self.path.is_symlink() or self.path.parent.is_symlink():
                    raise ValueError("invalid archive path")
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                                 prefix=self.path.name + ".", suffix=".tmp", delete=False) as handle:
                    temporary = Path(handle.name)
                    os.fchmod(handle.fileno(), 0o600)
                    json.dump(payload, handle, separators=(",", ":"), allow_nan=False)
                    handle.flush()
                    os.fsync(handle.fileno())
                temporary.replace(self.path)
                temporary = None
                directory_fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except Exception as exc:
                with self._lock:
                    self._write_failures += 1
                    self._last_failure = "OS_ERROR" if isinstance(exc, OSError) else "INVALID_ARCHIVE"
                raise
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink()
                    except OSError:
                        pass
            with self._lock:
                self._persisted_generation = generation
                self._writes += 1
                self._last_failure = None

    def flush(self, timeout: float = 2.0) -> bool:
        writer = self._writer
        if writer is not None and not writer.flush(timeout):
            return False
        with self._lock:
            return self._persisted_generation == self._generation

    def close(self, timeout: float = 2.0) -> bool:
        writer = self._writer
        return writer.close(timeout) if writer is not None else self.flush(timeout)

    def summary(self) -> dict:
        with self._lock:
            result = {"protocol": PROTOCOL, "load_state": self._load_state,
                      "restored_quote_count": self._restored, "received_quote_count": self._received,
                      "retained_quote_count": len(self._quotes), "evicted_quote_count": self._evicted,
                      "persisted_quote_generation": self._persisted_generation,
                      "pending_quote_generations": self._generation - self._persisted_generation,
                      "successful_writes": self._writes,
                      "failure_count": self._write_failures + self._request_failures + self._start_failures,
                      "start_failure_count": self._start_failures, "request_failure_count": self._request_failures,
                      "last_failure_class": self._last_failure,
                      "mode": "ASYNCHRONOUS_COALESCED" if self._async_requested else "SYNCHRONOUS_DIRECT_INGEST",
                      "writer_available": self._writer is not None,
                      "live_readiness_authority": False}
            writer = self._writer
        if writer is not None:
            result["writer"] = writer.summary()
        return result
