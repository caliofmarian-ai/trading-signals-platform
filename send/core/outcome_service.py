from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import requests

from core import observability_logger
from core import storage


OUTCOMES_JSONL = storage.root_path("outcomes", "outcomes.jsonl")
OPEN_REGISTRY_JSON = storage.root_path("outcomes", "open_now_registry.json")
OUTCOMES_INDEX_JSON = storage.root_path("outcomes", "outcomes_index.json")

VOTE_WINDOW_GRACE_SECONDS = 5 * 60
ALLOWED_OUTCOMES = {"WIN", "LOSE", "MISSED"}
_ALLOWED_MEMBER_STATUSES = {"member", "administrator", "creator"}


def _iso_utc(epoch_seconds: int) -> str:
    return datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


def _elite_channel_id() -> str:
    return os.getenv("ELITE_CHANNEL_ID", "").strip()


def _member_ref_salt() -> str:
    return os.getenv("COMMUNITY_FEEDBACK_SALT", "").strip()


def _config_ready() -> Tuple[bool, Optional[str]]:
    if not _bot_token():
        return False, "bot_token_missing"
    if not _elite_channel_id():
        return False, "elite_channel_id_missing"
    if not _member_ref_salt():
        return False, "community_feedback_salt_missing"
    return True, None


def _load_registry() -> Dict[str, Any]:
    registry = storage.load_json(OPEN_REGISTRY_JSON, default={})
    return registry if isinstance(registry, dict) else {}


def _save_registry(reg: Dict[str, Any]) -> None:
    storage.save_json_atomic(OPEN_REGISTRY_JSON, reg)


def _load_outcomes_index() -> Dict[str, Any]:
    index = storage.load_json(
        OUTCOMES_INDEX_JSON,
        default={"voted": {}, "processed_callbacks": {}},
    )
    if not isinstance(index, dict):
        return {"voted": {}, "processed_callbacks": {}}
    if not isinstance(index.get("voted"), dict):
        index["voted"] = {}
    if not isinstance(index.get("processed_callbacks"), dict):
        index["processed_callbacks"] = {}
    return index


def _save_outcomes_index(idx: Dict[str, Any]) -> None:
    storage.save_json_atomic(OUTCOMES_INDEX_JSON, idx)


def _member_ref(user_id: int) -> str:
    digest = hashlib.sha256(f"{int(user_id)}:{_member_ref_salt()}".encode("utf-8")).hexdigest().upper()
    return f"M-{digest[:8]}"


def _vote_key(signal_id: str, member_ref: str) -> str:
    return f"{signal_id}|{member_ref}"


def _callback_key(signal_id: str, member_ref: str, outcome: str, chat_id: Optional[int], message_id: Optional[int]) -> str:
    return f"{signal_id}|{member_ref}|{outcome}|{chat_id or 0}|{message_id or 0}"


def _parse_vote_payload(data: str) -> Tuple[bool, Dict[str, Any]]:
    cleaned = str(data or "").strip()
    if not cleaned:
        return False, {"reason": "missing_callback_payload"}
    if not cleaned.startswith("VOTE_"):
        return False, {"reason": "unknown_action"}
    parts = cleaned.split("|")
    if len(parts) != 3 or parts[0] != "VOTE_":
        return False, {"reason": "malformed_callback_payload"}

    signal_id = str(parts[1] or "").strip()
    outcome = str(parts[2] or "").strip().upper()
    if not signal_id:
        return False, {"reason": "missing_signal_id"}
    if outcome not in ALLOWED_OUTCOMES:
        return False, {"reason": "unknown_action" if outcome == "" else "invalid_outcome"}

    return True, {"signal_id": signal_id, "outcome": outcome}


def _context_match(meta: Dict[str, Any], chat_id: Optional[int], message_id: Optional[int]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    if chat_id is None or message_id is None:
        return True, None
    contexts = meta.get("callback_contexts") or []
    for context in contexts:
        if not isinstance(context, dict):
            continue
        if int(context.get("chat_id", 0)) == int(chat_id) and int(context.get("message_id", 0)) == int(message_id):
            return True, context
    return False, None


def _elite_membership_ok(user_id: int) -> Tuple[bool, str]:
    config_ok, failure = _config_ready()
    if not config_ok:
        return False, str(failure)

    try:
        url = f"https://api.telegram.org/bot{_bot_token()}/getChatMember"
        response = requests.get(
            url,
            params={"chat_id": _elite_channel_id(), "user_id": int(user_id)},
            timeout=10,
        )
        data = response.json()

        if not data.get("ok"):
            return False, "telegram_getChatMember_failed"

        status = (data.get("result") or {}).get("status")
        if status in _ALLOWED_MEMBER_STATUSES:
            return True, "ok"
        return False, f"not_elite_member:{status}"
    except Exception:
        return False, "telegram_getChatMember_exception"


def _build_vote_record(
    *,
    signal_id: str,
    outcome: str,
    member_ref: str,
    now_ts: int,
    meta: Dict[str, Any],
    callback_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "event_type": "user_outcome_record",
        "signal_id": signal_id,
        "tier": "ELITE",
        "user_id": member_ref,
        "member_ref": member_ref,
        "outcome": outcome,
        "voted_ts": int(now_ts),
        "voted_ts_utc": _iso_utc(now_ts),
        "open_now_ts": int(meta.get("open_now_ts", 0)),
        "open_now_ts_utc": meta.get("open_now_ts_utc"),
        "expiry_minutes": int(meta.get("expiry_minutes", 0)),
        "expiry_ts": int(meta.get("expiry_ts", 0)),
        "expiry_ts_utc": meta.get("expiry_ts_utc"),
        "vote_window": {
            "activation_ts": int(meta.get("activation_ts", 0)),
            "activation_ts_utc": meta.get("activation_ts_utc"),
            "vote_end_ts": int(meta.get("vote_end_ts", 0)),
            "vote_end_ts_utc": meta.get("vote_end_ts_utc"),
        },
        "telemetry_trade_id": str(meta.get("telemetry_trade_id") or signal_id),
        "symbol": meta.get("symbol"),
        "direction": meta.get("direction"),
        "timeframe": meta.get("timeframe"),
        "submission_channel": (callback_context or {}).get("route", "ELITE"),
    }
    return record


def _log_user_outcome_event(
    *,
    signal_id: str,
    member_ref: str,
    outcome: str,
    accepted: bool,
    rejected_reason: Optional[str],
    vote_window: Optional[Dict[str, Any]],
    source_function: str,
) -> None:
    try:
        event = observability_logger.build_event(
            "user_outcome",
            {
                "outcome": outcome,
                "policy": "LOCK_FIRST_WRITE_WINS",
                "accepted": accepted,
                "rejected_reason": rejected_reason,
                "vote_window": vote_window or {},
            },
            source={"module": "outcome_service", "function": source_function},
            correlation={"signal_id": signal_id, "tier": "ELITE", "user_id": member_ref},
        )
        observability_logger.log_event(event)
    except Exception:
        pass


def _log_rejection_warning(
    *,
    warn_type: str,
    user_id: int,
    signal_id: str,
    failure_reason: str,
    route: str,
    source_function: str,
) -> None:
    try:
        observability_logger.log_warning(
            warn_type=warn_type,
            message="Outcome submission rejected",
            context={
                "user_id": int(user_id),
                "signal_id": signal_id,
                "failure_reason": failure_reason,
                "route": route,
            },
            source={"module": "outcome_service", "function": source_function},
            correlation={"signal_id": signal_id, "tier": "ELITE"},
        )
    except Exception:
        pass


def register_open_now(
    signal_id: str,
    elite_chat_id: int,
    open_message_id: int,
    open_now_ts: int,
    expiry_minutes: int,
    *,
    symbol: Optional[str] = None,
    direction: Optional[str] = None,
    timeframe: Optional[str] = None,
    telemetry_trade_id: Optional[str] = None,
    callback_route: str = "ELITE",
) -> Dict[str, Any]:
    signal_id = str(signal_id).strip()
    if not signal_id:
        raise ValueError("signal_id is required")

    open_now_ts = int(open_now_ts)
    expiry_minutes = int(expiry_minutes)
    if open_now_ts <= 0:
        raise ValueError("open_now_ts must be positive")
    if expiry_minutes <= 0:
        raise ValueError("expiry_minutes must be positive")

    expiry_sec = expiry_minutes * 60
    activation_ts = open_now_ts + expiry_sec
    vote_end_ts = activation_ts + VOTE_WINDOW_GRACE_SECONDS
    callback_context = {
        "chat_id": int(elite_chat_id),
        "message_id": int(open_message_id),
        "route": str(callback_route or "ELITE"),
    }
    immutable = {
        "signal_id": signal_id,
        "open_now_ts": int(open_now_ts),
        "expiry_minutes": int(expiry_minutes),
        "expiry_ts": int(open_now_ts + expiry_sec),
        "symbol": symbol,
        "direction": direction,
        "timeframe": timeframe,
        "telemetry_trade_id": telemetry_trade_id or signal_id,
    }

    with storage.with_lock("outcome_open_registry"):
        reg = _load_registry()
        existing = reg.get(signal_id)

        if existing is not None and not isinstance(existing, dict):
            raise ValueError(f"invalid open registry record for {signal_id}")

        if existing:
            existing_immutable = {
                key: existing.get(key)
                for key in immutable.keys()
            }
            if existing_immutable != immutable:
                raise ValueError(f"conflicting OPEN_NOW callback registration for {signal_id}")
            contexts = existing.setdefault("callback_contexts", [])
            if callback_context not in contexts:
                contexts.append(callback_context)
            reg[signal_id] = existing
            _save_registry(reg)
            status = "updated_context"
            meta = existing
        else:
            meta = {
                **immutable,
                "open_now_ts_utc": _iso_utc(open_now_ts),
                "activation_ts": int(activation_ts),
                "activation_ts_utc": _iso_utc(activation_ts),
                "vote_end_ts": int(vote_end_ts),
                "vote_end_ts_utc": _iso_utc(vote_end_ts),
                "created_ts": int(time.time()),
                "callback_contexts": [callback_context],
                "elite_chat_id": int(elite_chat_id),
                "open_message_id": int(open_message_id),
            }
            reg[signal_id] = meta
            _save_registry(reg)
            status = "registered"

    try:
        observability_logger.log_event(
            observability_logger.build_event(
                "outcome_panel_enabled",
                {
                    "elite_chat_id": int(elite_chat_id),
                    "open_message_id": int(open_message_id),
                    "open_now_ts": int(open_now_ts),
                    "expiry_minutes": int(expiry_minutes),
                    "activation_ts": int(activation_ts),
                    "vote_end_ts": int(vote_end_ts),
                },
                source={"module": "outcome_service", "function": "register_open_now"},
                correlation={
                    "signal_id": signal_id,
                    "tier": "ELITE",
                    "destination_id": int(elite_chat_id),
                    "message_id": int(open_message_id),
                },
            )
        )
    except Exception:
        pass
    return {"status": status, "meta": dict(meta)}


def schedule_activation(signal_id: str) -> None:
    return


def handle_vote_callback(
    user_id: int,
    signal_id: str,
    outcome: str,
    now_ts: int,
    *,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
) -> Dict[str, Any]:
    signal_id = str(signal_id).strip()
    outcome = str(outcome).strip().upper()
    now_ts = int(now_ts)

    if not signal_id:
        return {"accepted": False, "reason": "missing_signal_id"}
    if outcome not in ALLOWED_OUTCOMES:
        return {"accepted": False, "reason": "invalid_outcome"}

    callback_context: Optional[Dict[str, Any]] = None
    member_ok, member_reason = _elite_membership_ok(int(user_id))
    if not member_ok:
        if member_reason in {"bot_token_missing", "elite_channel_id_missing", "community_feedback_salt_missing"}:
            _log_rejection_warning(
                warn_type="outcome_security_config_missing",
                user_id=int(user_id),
                signal_id=signal_id,
                failure_reason=member_reason,
                route="ELITE",
                source_function="handle_vote_callback",
            )
            return {"accepted": False, "reason": member_reason}
        _log_rejection_warning(
            warn_type="membership_verification_failed",
            user_id=int(user_id),
            signal_id=signal_id,
            failure_reason=member_reason,
            route="ELITE",
            source_function="handle_vote_callback",
        )
        return {"accepted": False, "reason": "elite_membership_required"}

    reg = _load_registry()
    meta = reg.get(signal_id)
    if not isinstance(meta, dict):
        _log_rejection_warning(
            warn_type="unknown_signal_id",
            user_id=int(user_id),
            signal_id=signal_id,
            failure_reason="unknown_signal_id",
            route="ELITE",
            source_function="handle_vote_callback",
        )
        return {"accepted": False, "reason": "unknown_signal_id"}

    context_ok, callback_context = _context_match(meta, chat_id, message_id)
    if not context_ok:
        _log_rejection_warning(
            warn_type="unauthorized_callback_context",
            user_id=int(user_id),
            signal_id=signal_id,
            failure_reason="unauthorized_callback_context",
            route="ELITE",
            source_function="handle_vote_callback",
        )
        return {"accepted": False, "reason": "unauthorized_callback_context"}

    config_ok, config_reason = _config_ready()
    if not config_ok:
        _log_rejection_warning(
            warn_type="outcome_security_config_missing",
            user_id=int(user_id),
            signal_id=signal_id,
            failure_reason=str(config_reason),
            route=(callback_context or {}).get("route", "ELITE"),
            source_function="handle_vote_callback",
        )
        return {"accepted": False, "reason": str(config_reason)}

    activation_ts = int(meta.get("activation_ts", 0))
    vote_end_ts = int(meta.get("vote_end_ts", 0))
    if now_ts < activation_ts:
        _log_user_outcome_event(
            signal_id=signal_id,
            member_ref=_member_ref(int(user_id)),
            outcome=outcome,
            accepted=False,
            rejected_reason="too_early",
            vote_window={
                "activation_ts": activation_ts,
                "vote_end_ts": vote_end_ts,
                "ts_clicked": now_ts,
            },
            source_function="handle_vote_callback",
        )
        return {"accepted": False, "reason": "too_early"}
    if vote_end_ts and now_ts > vote_end_ts:
        _log_user_outcome_event(
            signal_id=signal_id,
            member_ref=_member_ref(int(user_id)),
            outcome=outcome,
            accepted=False,
            rejected_reason="vote_window_closed",
            vote_window={
                "activation_ts": activation_ts,
                "vote_end_ts": vote_end_ts,
                "ts_clicked": now_ts,
            },
            source_function="handle_vote_callback",
        )
        return {"accepted": False, "reason": "vote_window_closed"}

    member_ref = _member_ref(int(user_id))
    callback_key = _callback_key(signal_id, member_ref, outcome, chat_id, message_id)
    vote_key = _vote_key(signal_id, member_ref)
    duplicate_vote_reason: Optional[str] = None
    prior_outcome: Optional[str] = None
    persistence_failed = False

    with storage.with_lock("outcomes"):
        idx = _load_outcomes_index()
        processed_callbacks = idx.setdefault("processed_callbacks", {})
        voted = idx.setdefault("voted", {})

        if callback_key in processed_callbacks:
            prior = processed_callbacks[callback_key]
            stats = compute_signal_stats(signal_id)
            return {
                "accepted": True,
                "reason": "already_processed",
                "duplicate": True,
                "stats": stats,
                "outcome": prior.get("outcome"),
            }

        if vote_key in voted:
            prior = voted[vote_key]
            duplicate_vote_reason = "already_voted"
            prior_outcome = str(prior.get("outcome") or "")
        else:
            try:
                record = _build_vote_record(
                    signal_id=signal_id,
                    outcome=outcome,
                    member_ref=member_ref,
                    now_ts=now_ts,
                    meta=meta,
                    callback_context=callback_context,
                )
                storage.append_jsonl(OUTCOMES_JSONL, record)
                voted[vote_key] = {"outcome": outcome, "ts": int(now_ts), "user_id": member_ref}
                processed_callbacks[callback_key] = {"outcome": outcome, "ts": int(now_ts), "user_id": member_ref}
                _save_outcomes_index(idx)
            except Exception:
                persistence_failed = True

    if persistence_failed:
        _log_rejection_warning(
            warn_type="outcome_persistence_failed",
            user_id=int(user_id),
            signal_id=signal_id,
            failure_reason="persistence_failed",
            route=(callback_context or {}).get("route", "ELITE"),
            source_function="handle_vote_callback",
        )
        return {"accepted": False, "reason": "persistence_failed"}

    if duplicate_vote_reason is not None:
        _log_user_outcome_event(
            signal_id=signal_id,
            member_ref=member_ref,
            outcome=outcome,
            accepted=False,
            rejected_reason=duplicate_vote_reason,
            vote_window={
                "activation_ts": activation_ts,
                "vote_end_ts": vote_end_ts,
                "ts_clicked": now_ts,
            },
            source_function="handle_vote_callback",
        )
        return {
            "accepted": False,
            "reason": duplicate_vote_reason,
            "outcome": prior_outcome,
        }

    _log_user_outcome_event(
        signal_id=signal_id,
        member_ref=member_ref,
        outcome=outcome,
        accepted=True,
        rejected_reason=None,
        vote_window={
            "activation_ts": activation_ts,
            "vote_end_ts": vote_end_ts,
            "ts_clicked": now_ts,
        },
        source_function="handle_vote_callback",
    )
    stats = compute_signal_stats(signal_id)
    return {"accepted": True, "reason": "ok", "stats": stats, "member_ref": member_ref}


def handle_vote_callback_data(
    *,
    callback_data: str,
    user_id: int,
    now_ts: int,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
) -> Dict[str, Any]:
    ok, parsed = _parse_vote_payload(callback_data)
    if not ok:
        reason = str(parsed["reason"])
        signal_id = str(parsed.get("signal_id") or "")
        if signal_id:
            _log_rejection_warning(
                warn_type="invalid_outcome_callback",
                user_id=int(user_id),
                signal_id=signal_id,
                failure_reason=reason,
                route="ELITE",
                source_function="handle_vote_callback_data",
            )
        return {"accepted": False, "reason": reason}

    return handle_vote_callback(
        user_id=int(user_id),
        signal_id=parsed["signal_id"],
        outcome=parsed["outcome"],
        now_ts=int(now_ts),
        chat_id=chat_id,
        message_id=message_id,
    )


def compute_signal_stats(signal_id: str) -> Dict[str, Any]:
    signal_id = str(signal_id).strip()
    wins = loses = missed = 0

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
        "win_rate_percent": round(win_rate, 2),
    }
