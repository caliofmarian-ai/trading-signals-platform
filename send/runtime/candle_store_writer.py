"""One bounded candle-snapshot writer, independent of real-time price receipt.

Requests are monotonically numbered, not queued with market payloads. A single
worker persists the newest available snapshot and loops if a request arrived
in flight. Persistence never supplies a market quote or changes expiry policy.
"""
from __future__ import annotations

from collections import deque
from math import isfinite
import threading
import time
from typing import Callable

from runtime.observation_timing import WINDOW, distribution


PROTOCOL = "COALESCED_CANDLE_STORE_WRITER_V1"
RETRY_SECONDS = 1.0
SHUTDOWN_TIMEOUT_SECONDS = 2.0


class CandleStoreWriter:
    def __init__(self, persist: Callable[[], None]) -> None:
        self._persist = persist
        self._condition = threading.Condition()
        self._closing = False
        self._requested = 0
        self._completed = 0
        self._writes = 0
        self._failures = 0
        self._last_failure: str | None = None
        self._write_seconds: deque[float] = deque(maxlen=WINDOW)
        self._in_flight = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        with self._condition:
            if self._closing:
                raise RuntimeError("candle writer is closed")
            if self._thread is not None:
                return
            thread = threading.Thread(target=self._run, name="finnhub-candle-store", daemon=True)
            # Publish the handle only after successful start. The worker cannot
            # acquire the condition until this block is released.
            thread.start()
            self._thread = thread

    def request(self) -> int:
        """Schedule the latest state without waiting for disk or copying candles."""
        with self._condition:
            if self._closing or self._thread is None or not self._thread.is_alive():
                raise RuntimeError("candle writer is not accepting requests")
            self._requested += 1
            self._condition.notify_all()
            return self._requested

    def flush(self, timeout: float = SHUTDOWN_TIMEOUT_SECONDS) -> bool:
        """Wait only for requests present on entry, with an explicit timeout."""
        if type(timeout) not in (int, float) or not isfinite(timeout) or timeout < 0:
            raise ValueError("invalid candle writer timeout")
        deadline = time.monotonic() + timeout
        with self._condition:
            target = self._requested
            while self._completed < target:
                if self._thread is None or not self._thread.is_alive():
                    return False
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(remaining)
            return True

    def close(self, timeout: float = SHUTDOWN_TIMEOUT_SECONDS) -> bool:
        """Drain pending state once; a stuck disk cannot hang the receiver exit.

        Failure or timeout is not reported as durability. A blocking OS write
        cannot be cancelled safely; the one daemon may finish later, but a new
        writer is never started over it by this instance.
        """
        if type(timeout) not in (int, float) or not isfinite(timeout) or timeout < 0:
            raise ValueError("invalid candle writer timeout")
        with self._condition:
            self._closing = True
            self._condition.notify_all()
            thread = self._thread
        if thread is not None:
            thread.join(timeout)
        with self._condition:
            return (thread is None or not thread.is_alive()) and self._completed == self._requested

    def summary(self) -> dict:
        with self._condition:
            return {
                "protocol": PROTOCOL,
                "mode": "ASYNCHRONOUS_COALESCED",
                "running": self._thread is not None and self._thread.is_alive(),
                "closing": self._closing,
                "requested_generation": self._requested,
                "persisted_generation": self._completed,
                "pending_generations": self._requested - self._completed,
                "write_in_flight": self._in_flight,
                "successful_writes": self._writes,
                "failure_count": self._failures,
                "last_failure_class": self._last_failure,
                "write_seconds": distribution(self._write_seconds),
                "timing_scope": "LAST_128_WRITE_ATTEMPTS_IN_THIS_PROCESS",
                "market_payload_queue_size": 0,
            }

    def _run(self) -> None:
        retry_at = 0.0
        try:
            while True:
                with self._condition:
                    while self._requested == self._completed and not self._closing:
                        self._condition.wait()
                    if self._requested == self._completed:
                        return
                    # New requests cannot defeat the error backoff. Closing
                    # permits one immediate final attempt, never an infinite retry.
                    remaining = retry_at - time.monotonic()
                    if remaining > 0 and not self._closing:
                        self._condition.wait(remaining)
                        continue
                    generation = self._requested
                    self._in_flight = True
                started = time.monotonic()
                error = None
                try:
                    self._persist()
                except Exception as exc:
                    # Allowlisted types only: exception text may contain a path,
                    # token or raw payload and is never retained or logged.
                    error = "OS_ERROR" if isinstance(exc, OSError) else "SERIALIZATION_OR_CALLBACK_ERROR"
                elapsed = max(0.0, time.monotonic() - started)
                with self._condition:
                    self._write_seconds.append(elapsed)
                    self._in_flight = False
                    if error is None:
                        self._completed = generation
                        self._writes += 1
                        self._last_failure = None
                        retry_at = 0.0
                    else:
                        self._failures += 1
                        self._last_failure = error
                        retry_at = time.monotonic() + RETRY_SECONDS
                    self._condition.notify_all()
                    if error is not None and self._closing:
                        return
        finally:
            with self._condition:
                self._in_flight = False
                self._condition.notify_all()
