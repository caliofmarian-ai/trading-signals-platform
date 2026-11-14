"""App-local evidence for the existing engine; never infer market health from a loop."""
from __future__ import annotations

import math
import time

STATES = {"NOT_CONNECTED", "STARTING", "OBSERVING", "SOURCE_WARMING",
          "SOURCE_UNAVAILABLE", "SOURCE_LIMITED", "PROVIDER_CONFIGURATION_REQUIRED"}
REASONS = {"NOT_STARTED", "STARTING", "READY", "COLLECTING_HISTORY", "RATE_LIMITED",
           "MARKET_DATA_UNAVAILABLE", "EVALUATION_NOT_READY", "WORKER_NOT_RESPONDING",
           "PROVIDER_NOT_CONFIGURED", "PROVIDER_NOT_AUTHORIZED", "INVALID_CONFIGURATION",
           "ENGINE_CYCLE_FAILED", "ENGINE_INITIALIZATION_FAILED"}
DECISIONS = {"PRE", "CONFIRM", "OPEN_NOW", "NO_SIGNAL", "REJECT"}


def timestamp(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value) if math.isfinite(value) and value > 0 else None


def snapshot(store, now=None, *, provider="TWELVE_DATA"):
    now = int(time.time()) if now is None else int(now)
    if provider not in {"TWELVE_DATA", "FINNHUB"}:
        raise ValueError("Unsupported source provider.")
    raw = store.meta("source_status" if provider == "TWELVE_DATA" else "source_status_finnhub", {})
    if not isinstance(raw, dict):
        raw = {}
    result = {"state": raw.get("state") if raw.get("state") in STATES else "NOT_CONNECTED",
              "reason": raw.get("reason") if raw.get("reason") in REASONS else "NOT_STARTED",
              "provider": raw.get("provider") if raw.get("provider") == provider else None,
              "symbols": [s for s in raw.get("symbols", []) if isinstance(s, str) and len(s) <= 20]
                         if isinstance(raw.get("symbols"), list) else [],
              "heartbeat_at": timestamp(raw.get("heartbeat_at")),
              "last_evaluation_at": timestamp(raw.get("last_evaluation_at")),
              "last_market_data_at": timestamp(raw.get("last_market_data_at")),
              "last_decision": raw.get("last_decision") if raw.get("last_decision") in DECISIONS else None,
              "evaluations": max(0, raw.get("evaluations", 0)) if type(raw.get("evaluations")) is int else 0,
              "execution_timing_available": raw.get("execution_timing_available") is True,
              "market_data_state": raw.get("market_data_state") if raw.get("market_data_state") in
                  {"READY", "MARKET_DATA_COLLECTING", "MARKET_DATA_LIMITED", "MARKET_DATA_UNAVAILABLE"} else "UNKNOWN"}
    pulse = result["heartbeat_at"]
    if result["state"] not in {"NOT_CONNECTED", "PROVIDER_CONFIGURATION_REQUIRED"} and (
            pulse is None or not 0 <= now-pulse <= 30):
        result.update(state="SOURCE_UNAVAILABLE", reason="WORKER_NOT_RESPONDING")
    if result["state"] == "OBSERVING":
        evaluation, market = result["last_evaluation_at"], result["last_market_data_at"]
        if evaluation is None or not 0 <= now-evaluation <= 90 or market is None or not 0 <= now-market <= 90:
            result.update(state="SOURCE_UNAVAILABLE", reason="MARKET_DATA_UNAVAILABLE")
    return result


class SourceMonitor:
    def __init__(self, store, symbols):
        self.store = store
        self.evaluation_failed = False
        self.data = {"state": "STARTING", "reason": "STARTING", "provider": "TWELVE_DATA",
                     "symbols": list(symbols), "evaluations": 0, "last_evaluation_at": None,
                     "last_market_data_at": None, "last_decision": None,
                     "execution_timing_available": False, "market_data_state": "UNKNOWN"}
        self.save()

    def save(self, now=None):
        self.data["heartbeat_at"] = int(time.time()) if now is None else int(now)
        self.store.set_meta("source_status", self.data)

    def evaluation(self, decision, *, now=None):
        self.evaluation_failed = False
        self.data["last_evaluation_at"] = int(time.time()) if now is None else int(now)
        self.data["evaluations"] += 1
        kind = getattr(decision, "kind", None)
        self.data["last_decision"] = kind if kind in DECISIONS else None

    def failure(self, reason, *, configuration=False, now=None):
        self.data.update(state="PROVIDER_CONFIGURATION_REQUIRED" if configuration else "SOURCE_UNAVAILABLE",
                         reason=reason if reason in REASONS else "ENGINE_CYCLE_FAILED")
        self.save(now)

    def cycle(self, runtime, calibration=(), *, now=None):
        now = int(time.time()) if now is None else int(now)
        market = runtime.get("market_data_state")
        self.data.update(market_data_state=market,
                         last_market_data_at=timestamp(runtime.get("last_market_data_success_ts")),
                         execution_timing_available=any(item.get("available") is True for item in calibration
                                                        if isinstance(item, dict)))
        evaluated = self.data.get("last_evaluation_at")
        observed = self.data.get("last_market_data_at")
        if self.evaluation_failed:
            self.data.update(state="SOURCE_UNAVAILABLE", reason="EVALUATION_NOT_READY")
        elif market == "MARKET_DATA_LIMITED":
            self.data.update(state="SOURCE_LIMITED", reason="RATE_LIMITED")
        elif market == "MARKET_DATA_COLLECTING":
            self.data.update(state="SOURCE_WARMING", reason="COLLECTING_HISTORY")
        # The unchanged wide scheduler evaluates an unfocused symbol once per minute.
        elif market == "READY" and evaluated and 0 <= now-evaluated <= 90 and observed and 0 <= now-observed <= 90:
            self.data.update(state="OBSERVING", reason="READY")
        else:
            self.data.update(state="SOURCE_UNAVAILABLE", reason="EVALUATION_NOT_READY" if market == "READY"
                             else "MARKET_DATA_UNAVAILABLE")
        self.save(now)
