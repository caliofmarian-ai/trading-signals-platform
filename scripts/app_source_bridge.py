"""Opt-in status export from the existing runtime to its companion app.

Reuses the existing Finnhub stream. No market requests, signals, account writes,
strategy changes, or broker/Telegram actions are made by this module.
"""
from __future__ import annotations

import json
import os
import threading
import time
from urllib.parse import urlsplit

import requests


def status_payload(raw, *, now=None, pid=None, execution_available=False):
    now = int(time.time()) if now is None else int(now)
    pid = os.getpid() if pid is None else pid
    def epoch(key):
        value = raw.get(key)
        return value if type(value) is int and 0 < value <= now+5 else None
    updated = epoch("updated_ts")
    current = (raw.get("pid") == pid and str(raw.get("phase", "")).upper() == "RUNNING"
               and updated is not None and 0 <= now-updated <= 30
               and raw.get("market_data_provider") == "FINNHUB")
    count = raw.get("strategy_evaluation_count", 0)
    count = count if type(count) is int and count >= 0 else 0
    return {"provider": "FINNHUB", "source_id": "calibration-runtime", "symbols": ["EUR/USD"],
            "observed_at": now, "runtime_current": current,
            "market_data_state": raw.get("market_data_state") if current else "MARKET_DATA_UNAVAILABLE",
            "last_market_data_at": epoch("last_market_data_success_ts") if current else None,
            "last_evaluation_at": epoch("last_strategy_evaluation_ts") if current else None,
            "evaluations": count if current else 0,
            "last_decision": raw.get("last_strategy_decision_kind") if current else None,
            "execution_timing_available": current and execution_available is True}


def start_bridge():
    if os.getenv("APP_SOURCE_BRIDGE_ENABLED", "0").strip().lower() not in {"1", "true", "on"}:
        return None
    origin = os.getenv("APP_SOURCE_BRIDGE_ORIGIN", "").rstrip("/")
    token = os.getenv("APP_SOURCE_BRIDGE_TOKEN", "")
    parsed = urlsplit(origin)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment or len(token) < 32):
        print('TSP_APP_SOURCE_BRIDGE {"status":"INVALID_CONFIGURATION"}', flush=True)
        return None

    def export():
        from runtime.runtime_status import _read_status_file
        from core import signal_engine
        previous = None
        while True:
            try:
                calibration = getattr(signal_engine, "_LAST_CALIBRATION_STATE", {})
                available = any(value.get("available") is True for value in calibration.values()
                                if isinstance(value, dict))
                payload = status_payload(_read_status_file(), execution_available=available)
                response = requests.post(origin+"/api/internal/source-status", json=payload,
                    headers={"Authorization": "Bearer "+token}, timeout=3, allow_redirects=False)
                response.raise_for_status()
                # A redirect must never forward the machine credential elsewhere.
                if response.status_code != 200:
                    raise ValueError("Unexpected bridge response")
                result = response.json()
                state = ("ACCEPTED", result.get("state"))
            except Exception as exc:
                # Exception messages and HTTP request objects can contain secrets.
                state = ("UNAVAILABLE", type(exc).__name__)
            if state != previous:
                print("TSP_APP_SOURCE_BRIDGE "+json.dumps({"status": state[0], "source_state": state[1],
                    "provider": "FINNHUB"}), flush=True)
                previous = state
            time.sleep(5)

    thread = threading.Thread(target=export, name="app-source-status", daemon=True)
    thread.start()
    return thread
