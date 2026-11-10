"""Approximate expiry direction from two genuine neighboring source quotes.

The two prices are endpoints, never bounds on the unobserved price path. Even
when both favor a trade, the result is only an estimate: no expiry quote, price,
probability or verified trade outcome is manufactured by this module.
"""
from __future__ import annotations

from decimal import Decimal
import math


CONTRACT = "ADJACENT_SOURCE_QUOTES_ESTIMATE_V1"
TRUTH_DOMAIN = "APPROXIMATION_ONLY"
MAX_SIDE_SECONDS = 60.0
PROVIDER = "FINNHUB"
SYMBOL = "EUR/USD"
PROVIDER_SYMBOL = "OANDA:EUR_USD"
RETAINED_SOURCES = frozenset({
    "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1",
    "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1",
})
_FIELDS = frozenset({
    "contract", "truth_domain", "expiry_ts", "estimated_at", "before", "after",
    "lower_price", "upper_price", "gap_seconds", "estimated_outcome", "reason",
    "max_side_seconds",
})


def _positive(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        return False


def normalize_quote(quote, *, expiry_ts, observed_at, side,
                    max_side_seconds=MAX_SIDE_SECONDS):
    """Return a bounded, copied genuine endpoint, or None for invalid evidence.

Raw retained samples use private millisecond/receipt fields. The public shape
preserves that millisecond time instead of labeling a rounded second as exact.
Receipt time is optional for already normalized historical evidence; absence
is preserved and never filled with the time of this lookup.
    """
    if (not isinstance(side, str) or side not in {"before", "after"} or not isinstance(quote, dict)
            or not _positive(expiry_ts) or not _positive(observed_at)
            or not _positive(max_side_seconds) or max_side_seconds > MAX_SIDE_SECONDS
            or quote.get("provider") != PROVIDER or quote.get("symbol") != SYMBOL
            or not isinstance(quote.get("source"), str) or quote["source"] not in RETAINED_SOURCES
            or quote.get("provider_symbol", PROVIDER_SYMBOL) != PROVIDER_SYMBOL
            or not _positive(quote.get("price"))):
        return None

    stamp = quote.get("observed_ts")
    if not _positive(stamp):
        return None
    has_ms = "provider_tick_ms" in quote or "_provider_tick_ms" in quote
    tick_ms = quote.get("provider_tick_ms", quote.get("_provider_tick_ms"))
    if has_ms:
        if (type(tick_ms) is not int or not 0 < tick_ms < 2**53
                or any(type(quote[key]) is not int or not 0 < quote[key] < 2**53
                       for key in ("provider_tick_ms", "_provider_tick_ms") if key in quote)
                or ("provider_tick_ms" in quote and "_provider_tick_ms" in quote
                    and quote["provider_tick_ms"] != quote["_provider_tick_ms"])):
            return None
        source_stamp = tick_ms / 1000.0
        # Raw retained quotes carry the original second bucket. Public endpoint
        # evidence carries the more precise provider millisecond timestamp.
        if stamp not in (tick_ms // 1000, source_stamp):
            return None
        stamp = source_stamp
    if stamp > observed_at:
        return None
    distance = expiry_ts - stamp if side == "before" else stamp - expiry_ts
    if not 0 < distance <= max_side_seconds:
        return None

    normalized = {
        "provider": PROVIDER, "symbol": SYMBOL, "provider_symbol": PROVIDER_SYMBOL,
        "price": quote["price"], "observed_ts": float(stamp), "source": quote["source"],
    }
    if has_ms:
        normalized["provider_tick_ms"] = tick_ms
    if "received_ts" in quote or "_received_ts" in quote:
        received = quote.get("received_ts", quote.get("_received_ts"))
        if (not _positive(received) or received > observed_at
                or any(not _positive(quote[key]) or quote[key] > observed_at
                       for key in ("received_ts", "_received_ts") if key in quote)
                or ("received_ts" in quote and "_received_ts" in quote
                    and quote["received_ts"] != quote["_received_ts"])):
            return None
        normalized["received_ts"] = float(received)
    return normalized


def build_estimate(*, direction, entry, expiry_ts, bracket, observed_at):
    """Classify only the neighboring endpoints; observed results stay separate.

An entry may contain just its genuine price and source timestamp (e.g. chart
inputs). Optional entry provenance is checked when present, never fabricated.
Invalid/missing endpoints become explicit missing sides, with no midpoint.
    """
    if (not isinstance(direction, str) or direction not in {"BUY", "SELL"} or not _positive(expiry_ts)
            or not _positive(observed_at) or observed_at < expiry_ts
            or not isinstance(entry, dict) or not _positive(entry.get("price"))
            or not _positive(entry.get("observed_ts"))
            or entry["observed_ts"] >= expiry_ts
            or entry.get("provider", PROVIDER) != PROVIDER
            or entry.get("symbol", SYMBOL) != SYMBOL
            or entry.get("provider_symbol", PROVIDER_SYMBOL) != PROVIDER_SYMBOL):
        raise ValueError("INVALID_EXPIRY_ESTIMATE_CONTEXT")

    bracket = bracket if isinstance(bracket, dict) else {}
    before, after = [normalize_quote(bracket.get(side), expiry_ts=expiry_ts,
                                    observed_at=observed_at, side=side)
                     for side in ("before", "after")]
    result = {
        "contract": CONTRACT, "truth_domain": TRUTH_DOMAIN,
        "expiry_ts": float(expiry_ts), "estimated_at": float(observed_at),
        "before": before, "after": after, "lower_price": None, "upper_price": None,
        "gap_seconds": None, "estimated_outcome": "UNAVAILABLE",
        "reason": "BOTH_QUOTES_UNAVAILABLE", "max_side_seconds": MAX_SIDE_SECONDS,
    }
    if before is None or after is None:
        if before is not None:
            result["reason"] = "AFTER_QUOTE_UNAVAILABLE"
        elif after is not None:
            result["reason"] = "BEFORE_QUOTE_UNAVAILABLE"
        return result

    # Compare the exact serialized input decimals, with no rounding tolerance.
    reference = Decimal(str(entry["price"]))
    prices = [Decimal(str(quote["price"])) for quote in (before, after)]
    favorable = [price > reference if direction == "BUY" else price < reference
                 for price in prices]
    adverse = [price < reference if direction == "BUY" else price > reference
               for price in prices]
    if all(favorable):
        outcome, reason = "WIN", "ENDPOINTS_FAVORABLE"
    elif all(adverse):
        outcome, reason = "LOSS", "ENDPOINTS_ADVERSE"
    else:
        outcome, reason = "INCONCLUSIVE", "ENDPOINTS_STRADDLE_OR_TOUCH_ENTRY"
    low, high = sorted((before, after), key=lambda quote: Decimal(str(quote["price"])))
    result.update(lower_price=low["price"], upper_price=high["price"],
                  gap_seconds=after["observed_ts"] - before["observed_ts"],
                  estimated_outcome=outcome, reason=reason)
    return result


def validate_estimate(estimate, *, direction, entry, expiry_ts):
    """Recompute all stored fields; reject forged outcomes, ranges or provenance."""
    if (not isinstance(estimate, dict) or set(estimate) != _FIELDS
            or not _positive(estimate.get("expiry_ts"))
            or not _positive(estimate.get("estimated_at"))
            or any(estimate.get(key) is not None and not _positive(estimate[key])
                   for key in ("lower_price", "upper_price", "gap_seconds"))):
        raise ValueError("INVALID_EXPIRY_ESTIMATE")
    expected = build_estimate(direction=direction, entry=entry, expiry_ts=expiry_ts,
                              bracket={side: estimate[side] for side in ("before", "after")},
                              observed_at=estimate["estimated_at"])
    if estimate != expected:
        raise ValueError("INVALID_EXPIRY_ESTIMATE")
