"""Prospective timing of the first *observed* real-tick buffer hit.

This diagnostic never changes a decision, duration, expiry result or execution
authority.  A missing crossing between sparse provider ticks is not inferred.
"""
from __future__ import annotations

import math

from intelligence import buffer_expiry_evidence


CONTRACT = "BUFFER_FIRST_OBSERVED_HIT_TIME_V1"
HORIZON_SOURCE = "CONFIRM_MODEL_TIME"
ARRIVAL_GRACE_SECONDS = 15.0
_SOURCES = {
    "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1",
    "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1",
}
_FINAL = {"OBSERVED_HIT", "NO_OBSERVED_HIT", "UNAVAILABLE"}


def _number(value, *, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("INVALID_BUFFER_HIT_TIME_NUMBER")
    value = float(value)
    if positive and value <= 0:
        raise ValueError("INVALID_BUFFER_HIT_TIME_NUMBER")
    return value


def pending(*, horizon_seconds, captured_ts):
    return {
        "contract": CONTRACT,
        "status": "PENDING",
        "horizon_source": HORIZON_SOURCE,
        "horizon_seconds": _number(horizon_seconds, positive=True),
        "captured_ts": _number(captured_ts, positive=True),
        "settled_ts": None,
        "reason": None,
        "first_hit": None,
        "seconds_from_entry": None,
        "horizon_fraction": None,
        "observed_tick_count": None,
        "max_tick_gap_seconds": None,
        "execution_authority": False,
        "publication_authority": False,
        "calibration_authority": False,
        "no_historical_backfill": True,
    }


def _quote(raw, *, entry_ts, expiry_ts, now_ts):
    if (not isinstance(raw, dict) or raw.get("provider") != "FINNHUB"
            or str(raw.get("symbol", "")).replace("/", "") != "EURUSD"
            or raw.get("source") not in _SOURCES):
        return None
    try:
        tick_ms = raw.get("provider_tick_ms")
        observed = _number(raw.get("observed_ts"), positive=True)
        received = _number(raw.get("received_ts"), positive=True)
        price = _number(raw.get("price"), positive=True)
    except ValueError:
        return None
    if (type(tick_ms) is not int or tick_ms <= 0 or tick_ms / 1000 != observed
            or received > now_ts or not entry_ts < observed <= expiry_ts):
        return None
    return {
        "provider": "FINNHUB",
        "symbol": "EUR/USD",
        "price": price,
        "observed_ts": observed,
        "source": raw["source"],
        "provider_tick_ms": tick_ms,
        "received_ts": received,
    }


def _finish(observation, *, status, reason, now_ts, tick_count=None,
            max_gap=None, first_hit=None, seconds=None):
    observation.update(
        status=status,
        reason=reason,
        settled_ts=float(now_ts),
        first_hit=first_hit,
        seconds_from_entry=seconds,
        horizon_fraction=(seconds / observation["horizon_seconds"] if seconds is not None else None),
        observed_tick_count=tick_count,
        max_tick_gap_seconds=max_gap,
    )
    return True


def settle(observation, row, *, now_ts, active_provider, ticks=None,
           evidence_loader_available=True, terminal_reason=None):
    """Freeze one diagnostic after the declared horizon and arrival grace.

    ``ticks`` must already be retained genuine provider ticks.  The earliest
    source-time crossing wins; prices between ticks are never reconstructed.
    """
    validate(observation, row, allow_pending=True)
    if observation["status"] != "PENDING":
        return False
    now = _number(now_ts, positive=True)
    if terminal_reason is not None:
        return _finish(observation, status="UNAVAILABLE", reason=terminal_reason, now_ts=now)
    if active_provider != "FINNHUB":
        return _finish(observation, status="UNAVAILABLE", reason="PROVIDER_CHANGED", now_ts=now)
    entry = row.get("entry")
    if entry is None:
        return False
    entry_ts = _number(entry.get("observed_ts"), positive=True)
    expiry_ts = entry_ts + observation["horizon_seconds"]
    if now <= expiry_ts + ARRIVAL_GRACE_SECONDS:
        return False
    if not evidence_loader_available:
        return _finish(observation, status="UNAVAILABLE", reason="PATH_EVIDENCE_LOADER_UNAVAILABLE",
                       now_ts=now)
    eligible = []
    for raw in ticks or ():
        quote = _quote(raw, entry_ts=entry_ts, expiry_ts=expiry_ts, now_ts=now)
        if quote is not None:
            eligible.append(quote)
    eligible.sort(key=lambda quote: (quote["provider_tick_ms"], quote["received_ts"]))
    stamps = [entry_ts, *(quote["observed_ts"] for quote in eligible), expiry_ts]
    max_gap = max((after - before for before, after in zip(stamps, stamps[1:])), default=None)
    if not eligible:
        return _finish(observation, status="UNAVAILABLE", reason="PATH_OBSERVATION_MISSING",
                       now_ts=now, tick_count=0, max_gap=max_gap)
    first = next((quote for quote in eligible
                  if buffer_expiry_evidence.measure(
                      row["direction"], entry, quote, row["buffer_snapshot"]
                  )["buffer_met_at_expiry"] is True), None)
    if first is None:
        return _finish(observation, status="NO_OBSERVED_HIT",
                       reason="NO_OBSERVED_BUFFER_HIT", now_ts=now,
                       tick_count=len(eligible), max_gap=max_gap)
    seconds = first["observed_ts"] - entry_ts
    return _finish(observation, status="OBSERVED_HIT", reason="OBSERVED_BUFFER_HIT",
                   now_ts=now, tick_count=len(eligible), max_gap=max_gap,
                   first_hit=first, seconds=seconds)


def validate(observation, row, *, allow_pending=False):
    expected = {
        "contract", "status", "horizon_source", "horizon_seconds", "captured_ts",
        "settled_ts", "reason", "first_hit", "seconds_from_entry", "horizon_fraction",
        "observed_tick_count", "max_tick_gap_seconds", "execution_authority",
        "publication_authority", "calibration_authority", "no_historical_backfill",
    }
    if (not isinstance(observation, dict) or set(observation) != expected
            or observation.get("contract") != CONTRACT
            or observation.get("horizon_source") != HORIZON_SOURCE
            or observation.get("status") not in ({"PENDING"} | _FINAL)
            or any(observation.get(key) is not False for key in (
                "execution_authority", "publication_authority", "calibration_authority"))
            or observation.get("no_historical_backfill") is not True):
        raise ValueError("INVALID_BUFFER_HIT_TIME_OBSERVATION")
    horizon = _number(observation["horizon_seconds"], positive=True)
    _number(observation["captured_ts"], positive=True)
    published = row.get("study_observation")
    if not isinstance(published, dict) or horizon != _number(published.get("horizon_seconds"), positive=True):
        raise ValueError("BUFFER_HIT_TIME_HORIZON_CHANGED")
    status = observation["status"]
    if status == "PENDING":
        if not allow_pending:
            allow_pending = True
        if any(observation[key] is not None for key in (
            "settled_ts", "reason", "first_hit", "seconds_from_entry", "horizon_fraction",
            "observed_tick_count", "max_tick_gap_seconds"
        )):
            raise ValueError("INVALID_PENDING_BUFFER_HIT_TIME")
        return observation
    _number(observation["settled_ts"], positive=True)
    if not isinstance(observation.get("reason"), str) or not observation["reason"]:
        raise ValueError("INVALID_FINAL_BUFFER_HIT_TIME")
    count = observation.get("observed_tick_count")
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError("INVALID_BUFFER_HIT_TICK_COUNT")
    gap = observation.get("max_tick_gap_seconds")
    if gap is not None:
        _number(gap)
    if status == "OBSERVED_HIT":
        entry = row.get("entry")
        if entry is None:
            raise ValueError("BUFFER_HIT_WITHOUT_ENTRY")
        expiry_ts = _number(entry["observed_ts"], positive=True) + horizon
        hit = _quote(observation.get("first_hit"), entry_ts=entry["observed_ts"],
                     expiry_ts=expiry_ts, now_ts=observation["settled_ts"])
        seconds = _number(observation.get("seconds_from_entry"), positive=True)
        fraction = _number(observation.get("horizon_fraction"), positive=True)
        if (hit != observation["first_hit"] or seconds != hit["observed_ts"] - entry["observed_ts"]
                or not math.isclose(fraction, seconds / horizon, rel_tol=0, abs_tol=1e-12)
                or buffer_expiry_evidence.measure(
                    row["direction"], entry, hit, row["buffer_snapshot"]
                )["buffer_met_at_expiry"] is not True):
            raise ValueError("INVALID_OBSERVED_BUFFER_HIT")
    elif any(observation[key] is not None for key in (
        "first_hit", "seconds_from_entry", "horizon_fraction"
    )):
        raise ValueError("UNOBSERVED_BUFFER_HIT_HAS_QUOTE")
    return observation
