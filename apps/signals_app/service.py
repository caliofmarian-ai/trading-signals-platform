from __future__ import annotations

from datetime import datetime, timedelta
import base64
import binascii
import hashlib
import math
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

    def record_private_study(self, item: dict, *, now: int | None = None) -> dict:
        """Store a prospective V3 study receipt privately, outside channel signals."""
        now = int(time.time()) if now is None else int(now)
        if not isinstance(item, dict) or item.get("protocol") != "PRIVATE_V3_STUDY_RECEIPT_V1":
            raise ValueError("A versioned private V3 study receipt is required.")
        allowed = {"protocol", "study_id", "phase", "created_ts", "signal_label", "text",
                   "provider", "symbol", "strategy_version", "decision_policy", "format",
                   "image_base64"}
        if set(item) - allowed:
            raise ValueError("Unexpected private study receipt fields.")
        study_id, phase = item.get("study_id"), item.get("phase")
        if not isinstance(study_id, str) or not 1 <= len(study_id) <= 128 or not study_id.strip():
            raise ValueError("A bounded study identity is required.")
        if phase not in {"entry", "result"}:
            raise ValueError("A valid study receipt phase is required.")
        created = item.get("created_ts")
        try:
            created_ts = float(created)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("A valid prospective creation timestamp is required.")
        if (isinstance(created, bool) or not isinstance(created, (int, float))
                or not math.isfinite(created_ts) or created_ts <= 0 or created_ts > now + 5):
            raise ValueError("A valid prospective creation timestamp is required.")
        if (item.get("provider") != "FINNHUB" or item.get("symbol") != "EUR/USD"
                or item.get("strategy_version") != "3.0.0"
                or item.get("decision_policy") != "PHYSICAL_ONLY_V3"):
            raise ValueError("The private study source or V3 policy is not authorized.")
        label, text = item.get("signal_label"), item.get("text")
        if not isinstance(label, str) or not 1 <= len(label) <= 120:
            raise ValueError("A bounded study label is required.")
        if not isinstance(text, str) or not text.strip() or len(text) > 20000:
            raise ValueError("Bounded study text is required.")
        fmt = item.get("format")
        if fmt not in {"TEXT", "PHOTO"}:
            raise ValueError("A supported study presentation is required.")
        image = None
        encoded_image = item.get("image_base64")
        if encoded_image is None:
            if fmt != "TEXT":
                raise ValueError("A photo receipt requires its image.")
        else:
            if fmt != "PHOTO" or not isinstance(encoded_image, str) or len(encoded_image) > 512 * 1024:
                raise ValueError("The study image exceeds the private receipt limit.")
            try:
                image = base64.b64decode(encoded_image, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ValueError("The study image is not valid base64.") from exc
            if not image or len(image) > 384 * 1024 or not image.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("A bounded PNG study image is required.")
        payload = {
            "protocol": "PRIVATE_V3_STUDY_RECEIPT_V1", "phase": phase,
            "created_ts": created_ts, "signal_label": label, "text": text,
            "provider": "FINNHUB", "symbol": "EUR/USD",
            "strategy_version": "3.0.0", "decision_policy": "PHYSICAL_ONLY_V3",
            "format": fmt,
        }
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        digest = hashlib.sha256(encoded.encode() + b"\0" + (image or b"")).hexdigest()
        receipt_id = "app-study-" + hashlib.sha256((study_id + ":" + phase).encode()).hexdigest()[:24]
        with self.store.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if phase == "result":
                entry = db.execute(
                    "SELECT 1 FROM private_studies WHERE study_id=? AND phase='entry'", (study_id,)
                ).fetchone()
                if not entry:
                    raise ValueError("A study result requires its previously accepted app entry.")
            existing = db.execute(
                "SELECT digest,receipt_id FROM private_studies WHERE study_id=? AND phase=?",
                (study_id, phase),
            ).fetchone()
            if existing:
                if existing["digest"] != digest:
                    raise ValueError("Conflicting immutable private study receipt.")
                return {"status": "API_ACCEPTED", "receipt_id": existing["receipt_id"],
                        "duplicate": True, "transport": "APP", "phone_receipt_proven": False}
            count = db.execute("SELECT COUNT(*) FROM private_studies").fetchone()[0]
            if count >= 512:
                raise ValueError("The bounded private study receipt capacity is full.")
            db.execute(
                """INSERT INTO private_studies(study_id,phase,receipt_id,payload,image,digest,created,received)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (study_id, phase, receipt_id, encoded, image, digest, created_ts, now),
            )
        self.store.audit("PRIVATE_V3_STUDY_ACCEPTED", "SOURCE", phase)
        return {"status": "API_ACCEPTED", "receipt_id": receipt_id,
                "duplicate": False, "transport": "APP", "phone_receipt_proven": False}

    def private_studies(self, *, limit: int = 8) -> list[dict]:
        limit = max(1, min(12, int(limit)))
        with self.store.db() as db:
            rows = db.execute(
                "SELECT payload,image,received,receipt_id FROM private_studies ORDER BY seq DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            item = json.loads(row["payload"])
            item["received_ts"] = row["received"]
            item["receipt_id"] = row["receipt_id"]
            item["image_base64"] = base64.b64encode(row["image"]).decode("ascii") if row["image"] else None
            item["phone_receipt_proven"] = False
            result.append(item)
        return result

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
        from .source import snapshot
        source = snapshot(self.store)
        return {"engine_state": source["state"], "source_reason": source["reason"],
                "last_engine_tick":source["heartbeat_at"],
                "last_market_data_at":source["last_market_data_at"],
                "last_signal_at":self.store.meta("last_signal_at"),
                "transport":"APP", "telegram_modified":False}
