"""Persistent app-only REST caps; no subscription or billing operations."""
from __future__ import annotations

import json
import os
import time


class FreeTierBudgetExceeded(RuntimeError):
    pass


class TwelveDataBudget:
    KEY = "twelve_data_request_budget"

    def __init__(self, store, *, daily_limit=None, minute_limit=None, clock=time.time):
        self.store, self.clock = store, clock
        self.daily_limit = max(1, min(800, int(daily_limit if daily_limit is not None else
            os.getenv("SIGNALS_APP_TWELVE_DATA_DAILY_LIMIT", "700"))))
        self.minute_limit = max(1, min(8, int(minute_limit if minute_limit is not None else
            os.getenv("TWELVE_DATA_REST_REQUESTS_PER_MINUTE", "8"))))

    def _current(self, raw, now):
        day = now // 86400
        if not isinstance(raw, dict) or raw.get("utc_day") != day:
            return {"utc_day": day, "reserved": 0, "recent": []}
        return {"utc_day": day, "reserved": max(0, int(raw.get("reserved", 0))),
                "recent": [ts for ts in raw.get("recent", []) if type(ts) is int and now-60 < ts <= now]}

    def summary(self, *, now=None):
        now = int(self.clock()) if now is None else int(now)
        raw = self._current(self.store.meta(self.KEY), now)
        return {"scope": "APP_LOCAL_REQUEST_CAP_NOT_ACCOUNT_BILLING", "daily_limit": self.daily_limit,
                "reserved_today": raw["reserved"], "remaining_today": max(0, self.daily_limit-raw["reserved"]),
                "minute_limit": self.minute_limit, "reset_at": (now//86400+1)*86400,
                "daily_limit_reached": raw["reserved"] >= self.daily_limit,
                "account_plan": "NOT_VERIFIED"}

    def reserve(self):
        now = int(self.clock())
        # The ledger survives worker/deployment restarts and serializes both
        # shared-client REST calls and live-feed history bootstrap requests.
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT value FROM meta WHERE key=?", (self.KEY,)).fetchone()
            raw = self._current(json.loads(row[0]) if row else None, now)
            if raw["reserved"] >= self.daily_limit:
                raise FreeTierBudgetExceeded("DAILY_LIMIT_REACHED")
            if len(raw["recent"]) >= self.minute_limit:
                raise FreeTierBudgetExceeded("MINUTE_LIMIT_REACHED")
            raw["reserved"] += 1
            raw["recent"].append(now)
            db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)", (self.KEY, json.dumps(raw)))
