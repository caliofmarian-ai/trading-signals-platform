"""Owner diagnostics for two independent sources; never publishes a signal."""
from __future__ import annotations

import time

from .provider_budget import TwelveDataBudget
from .source import DECISIONS, snapshot, timestamp


def receive_finnhub_status(store, data, *, now=None):
    now = int(time.time()) if now is None else int(now)
    if data.get("provider") != "FINNHUB" or data.get("source_id") != "calibration-runtime":
        raise ValueError("The existing FINNHUB calibration source is required.")
    observed = timestamp(data.get("observed_at"))
    if observed is None or not 0 <= now-observed <= 30:
        raise ValueError("Current source evidence is required.")
    previous = store.meta("source_status_finnhub", {})
    if not isinstance(previous, dict):
        previous = {}
    if previous.get("heartbeat_at", 0) > observed:
        raise ValueError("Source evidence cannot move backwards.")
    count = data.get("evaluations")
    decision = data.get("last_decision")
    decision = decision if isinstance(decision, str) and decision in DECISIONS else None
    if type(count) is not int or count < 0 or data.get("symbols") != ["EUR/USD"]:
        raise ValueError("Invalid source evaluation evidence.")
    market, evaluation = timestamp(data.get("last_market_data_at")), timestamp(data.get("last_evaluation_at"))
    if any(ts is not None and ts > now+5 for ts in (market, evaluation)):
        raise ValueError("Future source evidence is not accepted.")
    state = data.get("market_data_state")
    if state not in {"READY", "MARKET_DATA_COLLECTING", "MARKET_DATA_LIMITED", "MARKET_DATA_UNAVAILABLE"}:
        state = "MARKET_DATA_UNAVAILABLE"
    runtime_current = data.get("runtime_current") is True
    ready = (runtime_current and state == "READY" and count > 0 and market and evaluation
             and 0 <= now-market <= 10 and 0 <= now-evaluation <= 90)
    result = {"provider": "FINNHUB", "symbols": ["EUR/USD"], "heartbeat_at": observed,
              "received_at": now, "market_data_state": state, "evaluations": count,
              "last_market_data_at": market, "last_evaluation_at": evaluation,
              "last_decision": decision,
              "execution_timing_available": runtime_current and data.get("execution_timing_available") is True,
              "state": "OBSERVING" if ready else "SOURCE_UNAVAILABLE",
              "reason": "READY" if ready else "EVALUATION_NOT_READY"}
    if not ready and state == "MARKET_DATA_COLLECTING" and runtime_current:
        result.update(state="SOURCE_WARMING", reason="COLLECTING_HISTORY")
    if not ready and state == "MARKET_DATA_LIMITED" and runtime_current:
        result.update(state="SOURCE_LIMITED", reason="RATE_LIMITED")
    # Persist only the allowlist above: no prices, credentials, runtime paths,
    # user identities, raw exceptions, or member-distribution evidence.
    store.set_meta("source_status_finnhub", result)
    return {"ok": True, "provider": "FINNHUB", "state": result["state"]}


def sources(store, *, now=None):
    now = int(time.time()) if now is None else int(now)
    app = snapshot(store, now=now)
    app.update(provider="TWELVE_DATA", purpose="Application engine", scope="APP_ENGINE",
               request_budget=TwelveDataBudget(store).summary(now=now))
    raw = store.meta("source_status_finnhub", {})
    calibration = {**snapshot(store, now=now, provider="FINNHUB"), "provider": "FINNHUB",
                   "purpose": "Owner calibration", "scope": "OWNER_CALIBRATION_STATUS_ONLY"}
    if calibration["state"] == "OBSERVING" and (
            not raw.get("received_at") or not 0 <= now-raw["received_at"] <= 30 or
            not calibration["last_market_data_at"] or not 0 <= now-calibration["last_market_data_at"] <= 10):
        calibration.update(state="SOURCE_UNAVAILABLE", reason="MARKET_DATA_UNAVAILABLE")
    return [calibration, app]
