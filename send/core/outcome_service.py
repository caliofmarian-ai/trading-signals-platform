# /opt/binarybot/core/outcome_service.py
# BinaryBot — Outcome Service (ELITE feedback: WIN/LOSE/MISSED)

from __future__ import annotations

import os
import time
import requests
from typing import Any, Dict, Optional, Tuple

from core import storage
from core import observability_logger


OUTCOMES_JSONL = "/opt/binarybot/outcomes/outcomes.jsonl"
OPEN_REGISTRY_JSON = "/opt/binarybot/outcomes/open_now_registry.json"
OUTCOMES_INDEX_JSON = "/opt/binarybot/outcomes/outcomes_index.json"

VOTE_WINDOW_GRACE_SECONDS = 5 * 60  # expiry + 5 minutes (canonical)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ELITE_CHANNEL_ID = os.getenv("ELITE_CHANNEL_ID", "").strip()

_ALLOWED_MEMBER_STATUSES = {"member", "administrator", "creator"}


# -----------------------------
# Registry: OPEN_NOW -> metadata
# -----------------------------

def _load_registry() -> Dict[str, Any]:
    return storage.load_json(OPEN_REGISTRY_JSON, default={})  # signal_id -> meta


def _save_registry(reg: Dict[str, Any]) -> None:
    storage.save_json_atomic(OPEN_REGISTRY_JSON, reg)


def register_open_now(
    signal_id: str,
    elite_chat_id: int,
    open_message_id: int,
    open_now_ts: int,
    expiry_minutes: int
) -> None:
    """
    Called when OPEN_NOW is published to ELITE (and/or admin mirror).
    Stores mapping needed for voting window enforcement and stats.
    """
    reg = _load_registry()

    expiry_sec = int(expiry_minutes) * 60
    activation_ts = int(open_now_ts) + expiry_sec
    vote_end_ts = activation_ts + VOTE_WINDOW_GRACE_SECONDS

    reg[str(signal_id)] = {
        "signal_id": str(signal_id),
        "elite_chat_id": int(elite_chat_id),
        "open_message_id": int(open_message_id),
        "open_now_ts": int(open_now_ts),
        "expiry_minutes": int(expiry_minutes),
        "activation_ts": int(activation_ts),
        "vote_end_ts": int(vote_end_ts),
        "created_ts": int(time.time()),
    }

    _save_registry(reg)

    observability_logger.log_event({
        "event_type": "outcome_register_open_now",
        "signal_id": str(signal_id),
        "tier": "ELITE",
        "data": {
            "elite_chat_id": int(elite_chat_id),
            "open_message_id": int(open_message_id),
            "open_now_ts": int(open_now_ts),
            "expiry_minutes": int(expiry_minutes),
            "activation_ts": int(activation_ts),
            "vote_end_ts": int(vote_end_ts),
        }
    })


def schedule_activation(signal_id: str) -> None:
    """
    Optional hook. In your current architecture, buttons are already attached at publish time.
    Activation/disable is enforced server-side in handle_vote_callback().
    """
    return


# -----------------------------
# Membership check (ELITE only)
# -----------------------------

def _elite_membership_ok(user_id: int) -> Tuple[bool, str]:
    if not BOT_TOKEN:
        return False, "bot_token_missing"
    if not ELITE_CHANNEL_ID:
        return False, "elite_channel_id_missing"

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        r = requests.get(url, params={"chat_id": ELITE_CHANNEL_ID, "user_id": int(user_id)}, timeout=10)
        data = r.json()

        if not data.get("ok"):
            return False, "telegram_getChatMember_failed"

        status = (data.get("result") or {}).get("status")
        if status in _ALLOWED_MEMBER_STATUSES:
            return True, "ok"
        return False, f"not_elite_member:{status}"

    except Exception:
        return False, "telegram_getChatMember_exception"


# -----------------------------
# Vote locking (first write wins)
# -----------------------------

def _load_outcomes_index() -> Dict[str, Any]:
    """
    Index format:
      {
        "voted": {
          "signal_id|user_id": {"outcome":"WIN","ts":...}
        }
      }
    """
    return storage.load_json(OUTCOMES_INDEX_JSON, default={"voted": {}})


def _save_outcomes_index(idx: Dict[str, Any]) -> None:
    storage.save_json_atomic(OUTCOMES_INDEX_JSON, idx)


def _vote_key(signal_id: str, user_id: int) -> str:
    return f"{signal_id}|{int(user_id)}"


def _has_voted(idx: Dict[str, Any], signal_id: str, user_id: int) -> bool:
    voted = idx.get("voted") or {}
    return _vote_key(signal_id, user_id) in voted


def _mark_voted(idx: Dict[str, Any], signal_id: str, user_id: int, outcome: str, now_ts: int) -> None:
    idx.setdefault("voted", {})
    idx["voted"][_vote_key(signal_id, user_id)] = {"outcome": str(outcome), "ts": int(now_ts)}


# -----------------------------
# Vote handling
# -----------------------------

def handle_vote_callback(
    user_id: int,
    signal_id: str,
    outcome: str,
    now_ts: int
) -> Dict[str, Any]:
    """
    Enforces:
    - ELITE membership (CHANNEL_CONFIG_SPEC)
    - vote window: [activation_ts, vote_end_ts]
    - LOCK: first write wins per (signal_id, user_id)
    """
    signal_id = str(signal_id).strip()
    outcome = str(outcome).strip().upper()

    if outcome not in ("WIN", "LOSE", "MISSED"):
        return {"accepted": False, "reason": "invalid_outcome"}

    # Membership check (ELITE only)
    ok_member, member_reason = _elite_membership_ok(int(user_id))
    if not ok_member:
        observability_logger.log_warning({
            "event_type": "warning",
            "module": "outcome_service",
            "warning": "OUTCOME_REJECTED_NOT_ELITE",
            "user_id": int(user_id),
            "signal_id": signal_id,
            "data": {"reason": member_reason}
        })
        return {"accepted": False, "reason": "elite_membership_required"}

    reg = _load_registry()
    meta = reg.get(signal_id)

    if not meta:
        return {"accepted": False, "reason": "unknown_signal_id"}

    activation_ts = int(meta.get("activation_ts", 0))
    vote_end_ts = int(meta.get("vote_end_ts", 0))

    if int(now_ts) < activation_ts:
        return {"accepted": False, "reason": "too_early"}

    if vote_end_ts and int(now_ts) > vote_end_ts:
        return {"accepted": False, "reason": "vote_window_closed"}

    # LOCK: first write wins
    with storage.with_lock("outcomes"):
        idx = _load_outcomes_index()

        if _has_voted(idx, signal_id, int(user_id)):
            observability_logger.log_event({
                "event_type": "user_outcome",
                "tier": "ELITE",
                "signal_id": signal_id,
                "user_id": int(user_id),
                "data": {
                    "outcome": outcome,
                    "policy": "LOCK_FIRST_WRITE_WINS",
                    "accepted": False,
                    "rejected_reason": "already_voted"
                }
            })
            return {"accepted": False, "reason": "already_voted"}

        record = {
            "event_type": "user_outcome",
            "signal_id": signal_id,
            "tier": "ELITE",
            "user_id": int(user_id),
            "outcome": outcome,
            "voted_ts": int(now_ts),
            "open_now_ts": int(meta.get("open_now_ts", 0)),
            "expiry_minutes": int(meta.get("expiry_minutes", 0)),
            "vote_window": {
                "activation_ts": activation_ts,
                "vote_end_ts": vote_end_ts
            }
        }

        storage.append_jsonl(OUTCOMES_JSONL, record)
        _mark_voted(idx, signal_id, int(user_id), outcome, int(now_ts))
        _save_outcomes_index(idx)

    # Log structured event (observability)
    observability_logger.log_event({
        "event_type": "user_outcome",
        "tier": "ELITE",
        "signal_id": signal_id,
        "user_id": int(user_id),
        "data": {
            "outcome": outcome,
            "policy": "LOCK_FIRST_WRITE_WINS",
            "accepted": True,
            "rejected_reason": None,
            "vote_window": {
                "activation_ts": activation_ts,
                "vote_end_ts": vote_end_ts,
                "ts_clicked": int(now_ts)
            }
        }
    })

    # Return updated aggregates (optional)
    stats = compute_signal_stats(signal_id)
    return {"accepted": True, "reason": "ok", "stats": stats}


# -----------------------------
# Aggregates
# -----------------------------

def compute_signal_stats(signal_id: str) -> Dict[str, Any]:
    """
    Computes aggregate stats for a signal from outcomes.jsonl.
    (Simple scan; ok for now. If needed later, we can add cached aggregates.)
    """
    signal_id = str(signal_id).strip()
    wins = loses = missed = 0

    # outcomes.jsonl may not exist yet
    try:
        with open(OUTCOMES_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    import json
                    obj = json.loads(line)
                except Exception:
                    continue

                if obj.get("signal_id") != signal_id:
                    continue

                out = str(obj.get("outcome", "")).upper()
                if out == "WIN":
                    wins += 1
                elif out == "LOSE":
                    loses += 1
                elif out == "MISSED":
                    missed += 1
    except FileNotFoundError:
        pass

    total = wins + loses + missed
    win_rate = (wins / total * 100.0) if total > 0 else 0.0

    return {
        "signal_id": signal_id,
        "win_count": wins,
        "lose_count": loses,
        "missed_count": missed,
        "total": total,
        "win_rate_percent": round(win_rate, 2)
    }