"""Bounded source-time evidence for missing quotes; never outcome authority.

The caller owns the quote-selection policy and holds the feed lock. Only time
fields are projected. A lookup miss is not a terminal UNKNOWN: a genuine tick
may still arrive during the existing caller-owned grace period.
"""
from __future__ import annotations

from collections import OrderedDict
from math import isfinite
from typing import Any, Iterable, Mapping


PROTOCOL = "RETAINED_QUOTE_WINDOW_DIAGNOSTIC_V1"
MAX_TRACKED_WINDOWS = 512
MAX_EVENTS_PER_MINUTE = 32
MAX_REJECTED_TIMESTAMPS = 512


class QuoteWindowDiagnostics:
    """Observe misses/recovery without selecting, requesting or changing quotes."""

    def __init__(self) -> None:
        self.windows: OrderedDict[tuple[float, float], tuple[str, float]] = OrderedDict()
        self.precision_windows: OrderedDict[tuple[float, float], str] = OrderedDict()
        self.report_slot: int | None = None
        self.slot_events = 0
        self.suppressed_events = 0

    def observe(
        self, *, samples: Iterable[Mapping[str, Any]], rejected_tick_ms: Iterable[int],
        target_ts: float, max_delay: float, now_ts: float,
        selected: Mapping[str, Any] | None, accepted_tick_count: int,
    ) -> dict[str, Any] | None:
        for value in (target_ts, max_delay, now_ts):
            if type(value) not in (int, float) or not isfinite(value):
                raise ValueError("invalid diagnostic observation time")
        end = target_ts + max_delay
        if target_ts <= 0 or now_ts <= 0 or max_delay < 0 or not isfinite(end):
            raise ValueError("invalid diagnostic observation window")
        key = (float(target_ts), float(max_delay))
        prior = self.windows.get(key)
        if selected is not None and prior is None:
            return None  # Normal successful lookups produce no diagnostic noise.
        if selected is None and now_ts < end:
            return None  # A source window not yet elapsed is not a missing quote.
        if prior is not None and prior[0] == "OBSERVATION_FOUND_AFTER_MISS":
            return None

        first = last = before = after = None
        retained = eligible = future = 0
        for row in samples:
            retained += 1
            stamp = row["observed_ts"]
            if row["_provider_tick_ms"] > now_ts * 1000 or stamp > now_ts:
                future += int(target_ts <= stamp <= end)
                continue
            eligible += 1
            first = stamp if first is None else min(first, stamp)
            last = stamp if last is None else max(last, stamp)
            if stamp < target_ts:
                before = stamp if before is None else max(before, stamp)
            if stamp > end:
                after = stamp if after is None else min(after, stamp)
        rejected = sum(target_ts <= tick // 1000 <= end and tick <= now_ts * 1000
                       for tick in rejected_tick_ms)
        if selected is not None:
            reason = "OBSERVATION_FOUND_AFTER_MISS"
        elif rejected:
            reason = "OUT_OF_ORDER_REJECTION_IN_WINDOW"
        elif future:
            reason = "FUTURE_TICK_NOT_YET_ELIGIBLE"
        elif first is None:
            reason = "NO_RETAINED_REAL_TICKS"
        elif first > end:
            reason = "WINDOW_BEFORE_RETAINED_TICKS"
        elif last < target_ts:
            reason = "NO_TICK_REACHED_WINDOW"
        elif before is not None and after is not None:
            reason = "BRACKETED_WITHOUT_ELIGIBLE_TICK"
        else:
            reason = "NO_ELIGIBLE_TICK_AT_LOOKUP"
        if prior is not None and prior[0] == reason:
            return None
        first_miss = prior[1] if prior is not None else now_ts
        self.windows[key] = (reason, first_miss)
        self.windows.move_to_end(key)
        while len(self.windows) > MAX_TRACKED_WINDOWS:
            self.windows.popitem(last=False)

        if not self._take_report_slot(now_ts):
            return None
        received_ts = selected.get("_received_ts") if selected is not None else None
        if type(received_ts) not in (int, float) or not isfinite(received_ts) or received_ts <= 0:
            received_ts = None
        receive_age = (received_ts - selected["_provider_tick_ms"] / 1000
                       if received_ts is not None else None)
        # Do not spread provider dictionaries into logs: prices/credentials are
        # deliberately absent, including when extra keys exist on a test input.
        return {
            "protocol": PROTOCOL, "provider": "FINNHUB", "symbol": "EUR/USD",
            "reason": reason, "target_ts": target_ts, "window_end_ts": end,
            "max_delay_seconds": max_delay, "lookup_ts": now_ts,
            "lookup_after_window_seconds": max(0.0, now_ts - end),
            "first_missing_lookup_ts": first_miss,
            "first_retained_source_ts": first, "last_retained_source_ts": last,
            "nearest_before_source_ts": before, "nearest_after_source_ts": after,
            "bracketing_gap_seconds": after - before if before is not None and after is not None else None,
            "buffered_real_quote_count": retained, "eligible_retained_count": eligible,
            "evicted_quote_count_in_process": max(0, accepted_tick_count - retained),
            "future_ticks_in_window": future,
            "recent_out_of_order_ticks_in_window": rejected,
            "rejection_evidence_capacity": MAX_REJECTED_TIMESTAMPS,
            "selected_source_ts": selected["observed_ts"] if selected is not None else None,
            "selected_provider_tick_ms": selected["_provider_tick_ms"] if selected is not None else None,
            "selected_received_ts": received_ts,
            "selected_receive_age_seconds": receive_age,
            "suppressed_diagnostic_events": self.suppressed_events,
            "source_time_convention": "EXISTING_PROVIDER_SECOND_BUCKET",
            "scope": "CURRENT_PROCESS_RETAINED_TIMESTAMPS_AT_LOOKUP",
            "terminal_outcome": False, "changes_sampling_policy": False,
            "no_prices_or_credentials": True,
        }

    def _take_report_slot(self, now_ts: float) -> bool:
        slot = int(now_ts // 60)
        if self.report_slot is None or slot > self.report_slot:
            self.report_slot, self.slot_events = slot, 0
        if self.slot_events >= MAX_EVENTS_PER_MINUTE:
            self.suppressed_events += 1
            return False
        self.slot_events += 1
        return True

    def observe_precision(
        self, *, target_ts: float, max_delay: float, now_ts: float,
        bucket_quote: Mapping[str, Any] | None, exact_quote: Mapping[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Compare candidates from one retained snapshot without changing selection."""
        if bucket_quote is exact_quote:
            return None
        if bucket_quote is None:
            reason = "ONLY_EXACT"
        elif exact_quote is None:
            reason = "ONLY_SECOND_BUCKET"
        else:
            reason = "DIFFERENT_FIRST_TICK"
        key = (target_ts, max_delay)
        if self.precision_windows.get(key) == reason:
            return None
        if not self._take_report_slot(now_ts):
            return None
        self.precision_windows[key] = reason
        self.precision_windows.move_to_end(key)
        while len(self.precision_windows) > MAX_TRACKED_WINDOWS:
            self.precision_windows.popitem(last=False)
        return {
            "protocol": "RETAINED_SOURCE_TIME_PRECISION_COMPARISON_V1",
            "reason": reason,
            "target_ts": target_ts,
            "max_delay_seconds": max_delay,
            "lookup_ts": now_ts,
            "second_bucket_provider_tick_ms": bucket_quote["_provider_tick_ms"] if bucket_quote else None,
            "exact_provider_tick_ms": exact_quote["_provider_tick_ms"] if exact_quote else None,
            "terminal_outcome": False,
            "changes_sampling_policy": False,
        }
