from __future__ import annotations

from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import threading
import time
import uuid
from zoneinfo import ZoneInfo

from . import canonical
from .store import Store


class AppService:
    """APP transport and access projection; no Telegram membership/payment writes."""

    def __init__(self, store: Store, *, subscription_path: Path | None = None,
                 snapshot_max_age: int = 300):
        self.store = store
        self.subscription_path = subscription_path or store.directory / "subscription_events.jsonl"
        self.snapshot_max_age = snapshot_max_age
        self.snapshot_lock = threading.RLock()
        self.channels = canonical.channels()
        config = json.loads((canonical.SEND / "config/channel_config.json").read_text())
        self.reset_zone = ZoneInfo(config.get("TZ", "Europe/London"))
        hour, minute = map(int, config.get("RESET_TIME", "08:10").split(":"))
        self.reset_delta = timedelta(hours=hour, minutes=minute)

    def entitlement(self, user: dict, now: int | None = None) -> dict:
        now = int(time.time()) if now is None else now
        subscriber = user.get("subscriber_ref")
        if not subscriber:
            return {"tier": "FREE", "access_state": "ACTIVE", "connected": False,
                    "reason": "FREE_BASELINE", "subscription_state": "NO_SUBSCRIPTION",
                    "expires_at_epoch": None}
        with self.snapshot_lock:
            heartbeat = self.store.meta("subscription_snapshot_at", 0)
            if not heartbeat or not 0 <= now - heartbeat <= self.snapshot_max_age:
                return {"tier": None, "access_state": "UNAVAILABLE", "connected": True,
                        "reason": "SUBSCRIPTION_SYNC_REQUIRED", "expires_at_epoch": None}
            try:
                result = canonical.resolve_entitlement(
                    subscriber_ref=subscriber, path=str(self.subscription_path), now_ts=now)
            except (OSError, ValueError, RuntimeError):
                return {"tier": None, "access_state": "UNAVAILABLE", "connected": True,
                        "reason": "SUBSCRIPTION_SOURCE_UNAVAILABLE", "expires_at_epoch": None}
        # Do not expose another surface's subscriber, payment or evidence identifiers.
        return {key: result.get(key) for key in
                ("tier", "access_state", "subscription_state", "expires_at_epoch", "reason")} | {"connected": True}

    def can_read(self, user: dict, channel: str) -> bool:
        if channel not in {item["id"] for item in self.channels}:
            return False
        if user["role"] == "OWNER":
            return True
        access = self.entitlement(user)
        return access["access_state"] in {"ACTIVE", "FREE_FALLBACK"} and access["tier"] == channel

    def verify_subscriber(self, subscriber_ref: str) -> dict:
        result = self.entitlement({"subscriber_ref": subscriber_ref})
        if result["access_state"] not in {"ACTIVE", "FREE_FALLBACK"}:
            raise ValueError("Refresh the existing subscription evidence before connecting this member.")
        return result

    def import_subscriptions(self, records: list[dict], generated_at: int):
        now = int(time.time())
        if isinstance(generated_at, bool) or not isinstance(generated_at, int) or not 0 <= now-generated_at <= 60:
            raise ValueError("A current canonical subscription snapshot is required.")
        if not isinstance(records, list) or len(records) > 20000:
            raise ValueError("Invalid subscription snapshot.")
        with self.snapshot_lock:
            if generated_at < self.store.meta("subscription_snapshot_at", 0):
                raise ValueError("Subscription snapshots cannot move backwards.")
            temporary = self.store.directory / ("subscription-import-"+uuid.uuid4().hex+".jsonl")
            try:
                temporary.write_text("".join(json.dumps(row, allow_nan=False)+"\n" for row in records))
                temporary.chmod(0o600)
                try:
                    verified = canonical.load_subscription_events(str(temporary))
                    previous = canonical.load_subscription_events(str(self.subscription_path))
                except (ValueError,RuntimeError,OSError) as exc:
                    raise ValueError("The canonical subscription snapshot is invalid or unavailable.") from exc
                if len(verified)<len(previous) or verified[:len(previous)] != previous:
                    raise ValueError("Canonical subscription history cannot be truncated or rewritten.")
                temporary.replace(self.subscription_path)
                self.store.set_meta("subscription_snapshot_at", generated_at)
            finally:
                temporary.unlink(missing_ok=True)
        self.store.audit("SUBSCRIPTIONS_SYNCED", "SOURCE", str(len(records)))

    def publish(self, candidate: dict, *, provider: str, now: int | None = None) -> dict:
        """Called only after the original engine's FSM/execution gate, or authenticated ingest.

        APP publication evidence is separate from Telegram delivery evidence.
        The original provider's personal-use restriction is preserved here.
        """
        now = int(time.time()) if now is None else now
        summary = {"published_count": 0, "failed_count": 0, "skipped_count": 0,
                   "blocked": False, "block_reason": None, "route_results": [],
                   "publication_evidence": [], "transport": "APP"}
        if provider != "TWELVE_DATA":
            summary.update(blocked=True, block_reason="PROVIDER_MEMBER_DISTRIBUTION_NOT_AUTHORIZED")
            return summary
        obj = canonical.signal(candidate)
        if obj.created_ts > now+5:
            raise ValueError("Future-dated signals cannot be published.")
        payload = canonical.public_signal(obj)
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        quota_day = (datetime.fromtimestamp(now, self.reset_zone)-self.reset_delta).date().isoformat()
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            for channel in self.channels:
                tier = channel["id"]
                previous = db.execute("SELECT payload FROM signals WHERE channel=? AND signal_id=? AND stage=?",
                                      (tier,obj.signal_id,obj.stage)).fetchone()
                if previous:
                    if previous[0] != encoded:
                        raise ValueError("Conflicting immutable signal stage.")
                    summary["skipped_count"] += 1
                    continue
                limit = channel["daily_limit"]
                used = db.execute("SELECT COUNT(*) FROM signals WHERE channel=? AND stage='OPEN_NOW' AND quota_day=?",
                                  (tier,quota_day)).fetchone()[0]
                if isinstance(limit,int) and used >= limit:
                    summary["skipped_count"] += 1
                    continue
                event_id = "app-"+uuid.uuid4().hex
                db.execute("""INSERT INTO signals(event_id,channel,signal_id,stage,payload,created,published,quota_day)
                    VALUES (?,?,?,?,?,?,?,?)""",(event_id,tier,obj.signal_id,obj.stage,encoded,obj.created_ts,now,quota_day))
                result = {"event_id":event_id,"route":tier,"publish_result":"PUBLISHED",
                          "destination_id":"APP:"+tier,"message_id":None,"transport":"APP"}
                summary["published_count"] += 1
                summary["route_results"].append(result)
                summary["publication_evidence"].append(result)
                # Historical records remain visible as history, never urgent notifications.
                if 0 <= now-obj.created_ts <= 30 and (not payload["expires_at"] or payload["expires_at"] > now):
                    db.execute("""INSERT OR IGNORE INTO pushes(event_id,endpoint,next_attempt)
                        SELECT ?,endpoint,? FROM devices""", (event_id,now))
        self.store.set_meta("last_signal_at", now)
        return summary

    def feed(self, channel: str, *, before: int | None = None, limit: int = 40) -> list[dict]:
        with self.store.db() as db:
            rows = db.execute("""SELECT * FROM signals WHERE channel=? AND seq<?
                ORDER BY seq DESC LIMIT ?""", (channel,before or 2**62,limit)).fetchall()
        return [dict(json.loads(row["payload"]), seq=row["seq"],event_id=row["event_id"],
                     channel=row["channel"],published_at=row["published"]) for row in rows]

    def metrics(self) -> dict:
        with self.store.db() as db:
            stages = dict(db.execute("SELECT stage,COUNT(DISTINCT signal_id) FROM signals GROUP BY stage"))
            results = dict(db.execute("SELECT result,COUNT(*) FROM outcomes GROUP BY result"))
            reports = dict(db.execute("SELECT result,COUNT(*) FROM feedback GROUP BY result"))
            members = db.execute("SELECT COUNT(*) FROM users WHERE role='MEMBER'").fetchone()[0]
        settled = results.get("WIN",0)+results.get("LOSE",0)
        return {"stages": stages,"members":members,"market_outcomes":results,
                "settled_market_sample":settled,
                "market_win_rate":results.get("WIN",0)/settled if settled else None,
                "community_reports":reports,"community_truth":"SELF_REPORT",
                "period":"ALL_RECORDED_HISTORY", "strategy_changes":"NONE"}

    def status(self) -> dict:
        tick = self.store.meta("last_engine_tick", 0)
        age = int(time.time())-tick if tick else None
        return {"engine_state": "OBSERVING" if age is not None and age < 15 else
                self.store.meta("engine_state","NOT_CONNECTED"),
                "last_engine_tick":tick or None,
                "last_signal_at":self.store.meta("last_signal_at"),
                "transport":"APP", "telegram_modified":False}
