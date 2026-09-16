from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Protocol

import requests

from billing import notification_scheduler, subscription_registry
from core import distribution_router, observability_logger, storage, telegram_publisher

TIERS = ("FREE", "BASIC", "PRO", "ELITE")
PAID_TIERS = frozenset({"BASIC", "PRO", "ELITE"})
RECONCILIATION_STATES = frozenset(
    {
        "IN_SYNC",
        "INVITE_REQUIRED",
        "REMOVE_REQUIRED",
        "ACCESS_LEAK_RISK",
        "ACTION_FAILED",
        "UNKNOWN",
    }
)
MEMBER_STATUSES = frozenset({"creator", "administrator", "member"})
DEFAULT_INVITE_TTL_SECONDS = 15 * 60
MAX_INVITE_TTL_SECONDS = 60 * 60

EVENT_OBSERVED = "TELEGRAM_MEMBERSHIP_OBSERVED"
EVENT_REMOVAL = "TELEGRAM_MEMBERSHIP_REMOVAL"
EVENT_UNBAN = "TELEGRAM_MEMBERSHIP_TARGET_UNBAN"
EVENT_INVITE = "TELEGRAM_MEMBERSHIP_INVITE"
EVENT_FINAL = "TELEGRAM_MEMBERSHIP_RECONCILIATION"
EVENT_CHAT_MEMBER_UPDATE = "TELEGRAM_CHAT_MEMBER_UPDATE_EVIDENCE"

_LOCK_NAME = "billing_membership_reconciler"
_EVENTS_RELATIVE = ("billing", "membership_reconciliation_events.jsonl")


class MembershipReconciliationError(RuntimeError):
    """Raised when Telegram membership truth cannot be handled safely."""


class MembershipAPI(Protocol):
    def get_chat_member(self, chat_id: int, user_id: int) -> Dict[str, Any]: ...
    def ban_chat_member(self, chat_id: int, user_id: int) -> Dict[str, Any]: ...
    def unban_chat_member(self, chat_id: int, user_id: int) -> Dict[str, Any]: ...
    def create_chat_invite_link(
        self,
        chat_id: int,
        *,
        expire_date: int,
        member_limit: int,
        name: str,
    ) -> Dict[str, Any]: ...


def events_path() -> str:
    return storage.root_path(*_EVENTS_RELATIVE)


def _now(value: float | int | None = None) -> int:
    return int(time.time() if value is None else value)


def _opaque_id() -> str:
    return str(uuid.uuid4())


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MembershipReconciliationError(f"{label} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise MembershipReconciliationError(f"{label} must be a positive integer")
    try:
        result = int(value)
    except Exception as exc:
        raise MembershipReconciliationError(f"{label} must be a positive integer") from exc
    if result <= 0:
        raise MembershipReconciliationError(f"{label} must be a positive integer")
    return result


def _safe_error(exc: BaseException) -> str:
    return telegram_publisher._sanitize(str(exc))[:500]


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_events_unlocked(path: str) -> list[Dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise MembershipReconciliationError(
            f"Unable to read membership reconciliation log: {target}"
        ) from exc

    records: list[Dict[str, Any]] = []
    ids: set[str] = set()
    seqs: set[int] = set()
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MembershipReconciliationError(
                f"Membership reconciliation JSON corruption at line {line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise MembershipReconciliationError(
                f"Membership event at line {line_number} is not an object"
            )
        event_id = _nonempty(
            record.get("membership_event_id"), label="membership_event_id"
        )
        if event_id in ids:
            raise MembershipReconciliationError(
                f"Duplicate membership_event_id: {event_id}"
            )
        ids.add(event_id)
        seq = record.get("membership_seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise MembershipReconciliationError(
                f"Invalid membership_seq at line {line_number}"
            )
        if seq in seqs:
            raise MembershipReconciliationError(f"Duplicate membership_seq: {seq}")
        seqs.add(seq)
        state = record.get("reconciliation_state")
        if state is not None and state not in RECONCILIATION_STATES:
            raise MembershipReconciliationError(
                f"Unsupported reconciliation_state at line {line_number}: {state}"
            )
        records.append(record)

    if records:
        actual = [int(record["membership_seq"]) for record in records]
        expected = list(range(1, len(records) + 1))
        if actual != expected:
            raise MembershipReconciliationError(
                f"Membership sequence is non-contiguous: expected={expected} actual={actual}"
            )
    return records


def load_events(path: str | None = None) -> list[Dict[str, Any]]:
    return _read_events_unlocked(path or events_path())


def _find_idempotency(
    records: Iterable[Mapping[str, Any]], key: str
) -> Optional[Mapping[str, Any]]:
    for record in records:
        if record.get("idempotency_key") == key:
            return record
    return None


def _append_unlocked(
    *,
    path: str,
    records: list[Dict[str, Any]],
    payload: Mapping[str, Any],
    idempotency_key: str | None = None,
) -> tuple[Dict[str, Any], bool]:
    if idempotency_key:
        existing = _find_idempotency(records, idempotency_key)
        if existing is not None:
            return dict(existing), False
    record = dict(payload)
    record.pop("membership_event_id", None)
    record.pop("membership_seq", None)
    record["membership_event_id"] = _opaque_id()
    record["membership_seq"] = len(records) + 1
    if idempotency_key:
        record["idempotency_key"] = idempotency_key
    storage.append_jsonl(path, record)
    return record, True


def _latest_delivery_binding(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    notification_path: str | None,
) -> Optional[Dict[str, Any]]:
    events = notification_scheduler.load_events(notification_path)
    latest_by_pair: Dict[tuple[str, str], Dict[str, Any]] = {}
    for row in events:
        if row.get("event_type") != notification_scheduler.EVENT_TARGET_BOUND:
            continue
        key = (str(row.get("subscriber_ref")), str(row.get("strategy_product_id")))
        latest_by_pair[key] = dict(row)
    target = latest_by_pair.get((subscriber_ref, strategy_product_id))
    if target is None:
        return None
    user_id = target.get("telegram_user_id")
    chat_id = target.get("telegram_chat_id")
    try:
        user = _positive_int(user_id, label="telegram_user_id")
        chat = _positive_int(chat_id, label="telegram_chat_id")
    except MembershipReconciliationError:
        return None
    if user != chat:
        return None

    # One Telegram identity cannot safely represent two current commercial
    # subscribers for the same strategy product.
    collisions = [
        row
        for (subscriber, product), row in latest_by_pair.items()
        if product == strategy_product_id
        and subscriber != subscriber_ref
        and int(row.get("telegram_user_id") or 0) == user
        and int(row.get("telegram_chat_id") or 0) == chat
    ]
    if collisions:
        return None
    return {**target, "telegram_user_id": user, "telegram_chat_id": chat}


def _configured_channels() -> Dict[str, int]:
    raw = distribution_router.load_config().get("channels") or {}
    channels: Dict[str, int] = {}
    missing: list[str] = []
    for tier in TIERS:
        value = raw.get(tier) if isinstance(raw, dict) else None
        try:
            channels[tier] = _positive_int(value, label=f"{tier}_CHANNEL_ID")
        except MembershipReconciliationError:
            missing.append(tier)
    if missing:
        raise MembershipReconciliationError(
            "Membership reconciliation requires all EXCLUSIVE tier channels; "
            f"missing/invalid={','.join(missing)}"
        )
    if len(set(channels.values())) != len(channels):
        raise MembershipReconciliationError(
            "EXCLUSIVE tier channels must have distinct Telegram chat IDs"
        )
    return channels


def _is_member(result: Mapping[str, Any]) -> bool:
    status = str(result.get("status") or "").lower()
    if status in MEMBER_STATUSES:
        return True
    if status == "restricted":
        return bool(result.get("is_member"))
    return False


def _normalize_member(result: Mapping[str, Any]) -> Dict[str, Any]:
    status = str(result.get("status") or "").lower()
    if not status:
        raise MembershipReconciliationError("getChatMember result is missing status")
    return {
        "status": status,
        "is_member": _is_member(result),
    }


class TelegramMembershipAPI:
    """Minimal Telegram Bot API adapter with sanitized failures."""

    def __init__(self, *, request_post=requests.post) -> None:
        self._post = request_post

    def _call(self, method: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        try:
            response = self._post(
                f"{telegram_publisher._base_url()}/{method}",
                json=dict(payload),
                timeout=15,
            )
            data = response.json()
        except Exception as exc:
            raise MembershipReconciliationError(
                f"Telegram {method} transport failed: {_safe_error(exc)}"
            ) from exc
        if not isinstance(data, dict) or data.get("ok") is not True:
            error_code = data.get("error_code") if isinstance(data, dict) else None
            description = (
                telegram_publisher._sanitize(str(data.get("description") or "unknown"))
                if isinstance(data, dict)
                else "invalid response"
            )
            raise MembershipReconciliationError(
                f"Telegram {method} failed: code={error_code} description={description}"
            )
        result = data.get("result")
        if result is True:
            return {"ok": True}
        if not isinstance(result, dict):
            raise MembershipReconciliationError(
                f"Telegram {method} returned an invalid result"
            )
        return dict(result)

    def get_chat_member(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        return self._call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    def ban_chat_member(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        return self._call(
            "banChatMember",
            {"chat_id": chat_id, "user_id": user_id, "revoke_messages": False},
        )

    def unban_chat_member(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        return self._call(
            "unbanChatMember",
            {"chat_id": chat_id, "user_id": user_id, "only_if_banned": True},
        )

    def create_chat_invite_link(
        self,
        chat_id: int,
        *,
        expire_date: int,
        member_limit: int,
        name: str,
    ) -> Dict[str, Any]:
        return self._call(
            "createChatInviteLink",
            {
                "chat_id": chat_id,
                "expire_date": expire_date,
                "member_limit": member_limit,
                "name": name[:32],
            },
        )


def _entitlement_target(entitlement: Mapping[str, Any]) -> Optional[str]:
    access_state = str(entitlement.get("access_state") or "")
    tier = str(entitlement.get("tier") or "")
    if access_state in {"ACTIVE", "FREE_FALLBACK"}:
        if tier not in TIERS:
            raise MembershipReconciliationError(
                f"Unsupported entitlement tier for membership: {tier}"
            )
        return tier
    if access_state in {"SUSPENDED", "HOLD"}:
        return None
    raise MembershipReconciliationError(
        f"Unsupported entitlement access_state for membership: {access_state}"
    )


def _observe_memberships(
    *,
    api: MembershipAPI,
    channels: Mapping[str, int],
    user_id: int,
) -> Dict[str, Dict[str, Any]]:
    observations: Dict[str, Dict[str, Any]] = {}
    for tier in TIERS:
        row = api.get_chat_member(int(channels[tier]), user_id)
        observations[tier] = _normalize_member(row)
    return observations


def _state_from_observation(
    observations: Mapping[str, Mapping[str, Any]], target_tier: Optional[str]
) -> tuple[str, list[str], bool]:
    stale = [
        tier
        for tier in TIERS
        if observations[tier].get("is_member")
        and (target_tier is None or tier != target_tier)
    ]
    target_missing = bool(
        target_tier is not None and not observations[target_tier].get("is_member")
    )
    if stale:
        return "REMOVE_REQUIRED", stale, target_missing
    if target_missing:
        return "INVITE_REQUIRED", [], True
    return "IN_SYNC", [], False


def _base_event(
    *,
    reconciliation_id: str,
    subscriber_ref: str,
    strategy_product_id: str,
    entitlement: Mapping[str, Any],
    telegram_user_id: int,
    target_tier: Optional[str],
    occurred_at: int,
) -> Dict[str, Any]:
    return {
        "reconciliation_id": reconciliation_id,
        "subscriber_ref": subscriber_ref,
        "strategy_product_id": strategy_product_id,
        "subscription_id": entitlement.get("subscription_id"),
        "entitlement_id": entitlement.get("entitlement_id"),
        "entitlement_version": entitlement.get("entitlement_version"),
        "entitlement_access_state": entitlement.get("access_state"),
        "entitlement_tier": entitlement.get("tier"),
        "source_subscription_event_id": entitlement.get("source_subscription_event_id"),
        "telegram_user_id": telegram_user_id,
        "target_tier": target_tier,
        "occurred_at_epoch": occurred_at,
    }


def _critical_access_leak(
    *, subscriber_ref: str, tier: str, channel_id: int, reason: str
) -> None:
    observability_logger.log_error(
        {
            "event_type": "error",
            "module": "membership_reconciler",
            "function": "reconcile_membership",
            "severity": "CRITICAL",
            "error_type": "telegram_paid_access_leak_risk",
            "subscriber_ref_hash": _hash_text(subscriber_ref)[:16],
            "tier": tier,
            "channel_id": channel_id,
            "reason": reason,
        }
    )


def _active_invite_event(
    records: Iterable[Mapping[str, Any]],
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    entitlement_version: int,
    target_channel_id: int,
    now: int,
) -> Optional[Dict[str, Any]]:
    matches = [
        row
        for row in records
        if row.get("event_type") == EVENT_INVITE
        and row.get("subscriber_ref") == subscriber_ref
        and row.get("strategy_product_id") == strategy_product_id
        and row.get("entitlement_version") == entitlement_version
        and row.get("target_channel_id") == target_channel_id
        and row.get("invite_delivery_result") == "SENT"
        and int(row.get("invite_expires_at_epoch") or 0) > now
    ]
    return dict(matches[-1]) if matches else None


def _record_final(
    *,
    path: str,
    records: list[Dict[str, Any]],
    base: Mapping[str, Any],
    state: str,
    now: int,
    details: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    if state not in RECONCILIATION_STATES:
        raise MembershipReconciliationError(f"Unsupported final state: {state}")
    payload = {
        **dict(base),
        "event_type": EVENT_FINAL,
        "reconciliation_state": state,
        "occurred_at_epoch": now,
        "details": dict(details or {}),
    }
    record, _ = _append_unlocked(path=path, records=records, payload=payload)
    return record


def reconcile_membership(
    *,
    subscriber_ref: str,
    strategy_product_id: str = "BINARY_TRADING",
    now_ts: float | int | None = None,
    apply_actions: bool = False,
    invite_ttl_seconds: int = DEFAULT_INVITE_TTL_SECONDS,
    api: MembershipAPI | None = None,
    send_fn=telegram_publisher.send_message,
    path: str | None = None,
    subscription_path: str | None = None,
    notification_path: str | None = None,
) -> Dict[str, Any]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    now = _now(now_ts)
    ttl = _positive_int(invite_ttl_seconds, label="invite_ttl_seconds")
    if ttl > MAX_INVITE_TTL_SECONDS:
        raise MembershipReconciliationError(
            f"invite_ttl_seconds exceeds {MAX_INVITE_TTL_SECONDS}"
        )
    target_path = path or events_path()
    adapter: MembershipAPI = api or TelegramMembershipAPI()
    reconciliation_id = _opaque_id()

    try:
        entitlement = subscription_registry.resolve_entitlement(
            subscriber_ref=subscriber,
            strategy_product_id=product,
            now_ts=now,
            path=subscription_path,
        )
        target_tier = _entitlement_target(entitlement)
        channels = _configured_channels()
        binding = _latest_delivery_binding(
            subscriber_ref=subscriber,
            strategy_product_id=product,
            notification_path=notification_path,
        )
        if binding is None:
            raise MembershipReconciliationError(
                "No unique private Telegram binding exists for subscriber/product"
            )
        user_id = int(binding["telegram_user_id"])
        observations = _observe_memberships(
            api=adapter, channels=channels, user_id=user_id
        )
    except Exception as exc:
        # Unknown evidence must be persisted; never fabricate an IN_SYNC state.
        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            payload = {
                "event_type": EVENT_FINAL,
                "reconciliation_id": reconciliation_id,
                "subscriber_ref": subscriber,
                "strategy_product_id": product,
                "reconciliation_state": "UNKNOWN",
                "occurred_at_epoch": now,
                "error": _safe_error(exc),
            }
            record, _ = _append_unlocked(
                path=target_path, records=records, payload=payload
            )
        return {
            "state": "UNKNOWN",
            "reconciliation_id": reconciliation_id,
            "record": record,
            "actions_applied": False,
        }

    entitlement_version = int(entitlement.get("entitlement_version") or 0)
    base = _base_event(
        reconciliation_id=reconciliation_id,
        subscriber_ref=subscriber,
        strategy_product_id=product,
        entitlement=entitlement,
        telegram_user_id=user_id,
        target_tier=target_tier,
        occurred_at=now,
    )
    state, stale, target_missing = _state_from_observation(
        observations, target_tier
    )

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target_path)
        observed_record, _ = _append_unlocked(
            path=target_path,
            records=records,
            payload={
                **base,
                "event_type": EVENT_OBSERVED,
                "reconciliation_state": state,
                "channel_observations": observations,
                "stale_tiers": stale,
                "target_missing": target_missing,
            },
        )
        records.append(observed_record)
        if not apply_actions or state == "IN_SYNC":
            final = _record_final(
                path=target_path,
                records=records,
                base=base,
                state=state,
                now=now,
                details={
                    "dry_run": not apply_actions,
                    "stale_tiers": stale,
                    "target_missing": target_missing,
                },
            )
            return {
                "state": state,
                "reconciliation_id": reconciliation_id,
                "record": final,
                "observations": observations,
                "actions_applied": False,
            }

    # Mutating actions run outside the event-log lock because Telegram calls may
    # block; each resulting action is appended atomically afterwards.
    for stale_tier in stale:
        channel_id = channels[stale_tier]
        try:
            adapter.ban_chat_member(channel_id, user_id)
            verified = _normalize_member(
                adapter.get_chat_member(channel_id, user_id)
            )
            if verified["is_member"]:
                raise MembershipReconciliationError(
                    "Removal request completed but getChatMember still reports membership"
                )
            action_state = "REMOVE_REQUIRED"
            action_error = None
        except Exception as exc:
            action_error = _safe_error(exc)
            action_state = (
                "ACCESS_LEAK_RISK" if stale_tier in PAID_TIERS else "ACTION_FAILED"
            )

        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            action_record, _ = _append_unlocked(
                path=target_path,
                records=records,
                payload={
                    **base,
                    "event_type": EVENT_REMOVAL,
                    "reconciliation_state": action_state,
                    "removed_tier": stale_tier,
                    "channel_id": channel_id,
                    "verified_absent": action_error is None,
                    "error": action_error,
                    "occurred_at_epoch": now,
                },
                idempotency_key=(
                    f"membership-remove:{subscriber}:{product}:"
                    f"{entitlement_version}:{channel_id}"
                ),
            )
        if action_error is not None:
            if action_state == "ACCESS_LEAK_RISK":
                _critical_access_leak(
                    subscriber_ref=subscriber,
                    tier=stale_tier,
                    channel_id=channel_id,
                    reason=action_error,
                )
            with storage.with_lock(_LOCK_NAME):
                records = _read_events_unlocked(target_path)
                final = _record_final(
                    path=target_path,
                    records=records,
                    base=base,
                    state=action_state,
                    now=now,
                    details={"failed_tier": stale_tier, "error": action_error},
                )
            return {
                "state": action_state,
                "reconciliation_id": reconciliation_id,
                "record": final,
                "actions_applied": True,
            }

    # Suspended/HOLD entitlements have no target channel. Verified removals are
    # sufficient to become IN_SYNC.
    if target_tier is None:
        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            final = _record_final(
                path=target_path,
                records=records,
                base=base,
                state="IN_SYNC",
                now=now,
                details={"target_channel": None, "removed_tiers": stale},
            )
        return {
            "state": "IN_SYNC",
            "reconciliation_id": reconciliation_id,
            "record": final,
            "actions_applied": bool(stale),
        }

    target_channel = channels[target_tier]
    try:
        current_target = _normalize_member(
            adapter.get_chat_member(target_channel, user_id)
        )
    except Exception as exc:
        error = _safe_error(exc)
        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            final = _record_final(
                path=target_path,
                records=records,
                base=base,
                state="UNKNOWN",
                now=now,
                details={"error": error, "phase": "target_recheck"},
            )
        return {
            "state": "UNKNOWN",
            "reconciliation_id": reconciliation_id,
            "record": final,
            "actions_applied": bool(stale),
        }

    if current_target["is_member"]:
        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            final = _record_final(
                path=target_path,
                records=records,
                base=base,
                state="IN_SYNC",
                now=now,
                details={"target_channel": target_channel, "join_verified": True},
            )
        return {
            "state": "IN_SYNC",
            "reconciliation_id": reconciliation_id,
            "record": final,
            "actions_applied": bool(stale),
        }

    # A prior removal leaves Telegram status `kicked`; unban only when this
    # channel is once again the currently entitled target.
    if current_target["status"] == "kicked":
        try:
            adapter.unban_chat_member(target_channel, user_id)
            after_unban = _normalize_member(
                adapter.get_chat_member(target_channel, user_id)
            )
            if after_unban["status"] == "kicked":
                raise MembershipReconciliationError(
                    "Target channel remains banned after unbanChatMember"
                )
            unban_error = None
        except Exception as exc:
            unban_error = _safe_error(exc)
        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            unban_record, _ = _append_unlocked(
                path=target_path,
                records=records,
                payload={
                    **base,
                    "event_type": EVENT_UNBAN,
                    "reconciliation_state": (
                        "INVITE_REQUIRED" if unban_error is None else "ACTION_FAILED"
                    ),
                    "target_channel_id": target_channel,
                    "unban_verified": unban_error is None,
                    "error": unban_error,
                    "occurred_at_epoch": now,
                },
                idempotency_key=(
                    f"membership-unban:{subscriber}:{product}:"
                    f"{entitlement_version}:{target_channel}"
                ),
            )
        if unban_error is not None:
            with storage.with_lock(_LOCK_NAME):
                records = _read_events_unlocked(target_path)
                final = _record_final(
                    path=target_path,
                    records=records,
                    base=base,
                    state="ACTION_FAILED",
                    now=now,
                    details={"phase": "target_unban", "error": unban_error},
                )
            return {
                "state": "ACTION_FAILED",
                "reconciliation_id": reconciliation_id,
                "record": final,
                "actions_applied": True,
            }

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target_path)
        existing_invite = _active_invite_event(
            records,
            subscriber_ref=subscriber,
            strategy_product_id=product,
            entitlement_version=entitlement_version,
            target_channel_id=target_channel,
            now=now,
        )
    if existing_invite is not None:
        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            final = _record_final(
                path=target_path,
                records=records,
                base=base,
                state="INVITE_REQUIRED",
                now=now,
                details={
                    "target_channel": target_channel,
                    "active_invite_until": existing_invite.get(
                        "invite_expires_at_epoch"
                    ),
                    "invite_rotated": False,
                },
            )
        return {
            "state": "INVITE_REQUIRED",
            "reconciliation_id": reconciliation_id,
            "record": final,
            "actions_applied": bool(stale),
            "active_invite": True,
        }

    expires = now + ttl
    try:
        invite = adapter.create_chat_invite_link(
            target_channel,
            expire_date=expires,
            member_limit=1,
            name=f"billing-{reconciliation_id[:16]}",
        )
        invite_link = _nonempty(invite.get("invite_link"), label="invite_link")
        try:
            send_fn(
                chat_id=int(binding["telegram_chat_id"]),
                text=(
                    f"Your {target_tier} access is ready. Join the entitled "
                    f"channel with this single-use bounded link:\n{invite_link}\n\n"
                    "The link is not proof of membership; access is verified separately."
                ),
                reply_markup=None,
            )
            delivery_result = "SENT"
            delivery_error = None
        except Exception as exc:
            delivery_result = "FAILED"
            delivery_error = _safe_error(exc)
    except Exception as exc:
        invite_link = None
        delivery_result = "NOT_SENT"
        delivery_error = _safe_error(exc)

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target_path)
        invite_record, _ = _append_unlocked(
            path=target_path,
            records=records,
            payload={
                **base,
                "event_type": EVENT_INVITE,
                "reconciliation_state": (
                    "INVITE_REQUIRED"
                    if invite_link is not None and delivery_result == "SENT"
                    else "ACTION_FAILED"
                ),
                "target_channel_id": target_channel,
                "invite_link_sha256": (
                    _hash_text(invite_link) if invite_link is not None else None
                ),
                "invite_expires_at_epoch": expires,
                "invite_member_limit": 1,
                "invite_delivery_result": delivery_result,
                "error": delivery_error,
                "occurred_at_epoch": now,
            },
        )
        records.append(invite_record)
        final_state = (
            "INVITE_REQUIRED"
            if invite_link is not None and delivery_result == "SENT"
            else "ACTION_FAILED"
        )
        final = _record_final(
            path=target_path,
            records=records,
            base=base,
            state=final_state,
            now=now,
            details={
                "target_channel": target_channel,
                "invite_expires_at": expires,
                "invite_delivery_result": delivery_result,
            },
        )
    return {
        "state": final_state,
        "reconciliation_id": reconciliation_id,
        "record": final,
        "actions_applied": True,
        # Raw invite capability is returned to the immediate caller only; it is
        # never persisted in the reconciliation log.
        "invite_link": invite_link,
    }


def record_chat_member_update(
    *,
    telegram_update_id: int,
    chat_id: int,
    telegram_user_id: int,
    old_status: str,
    new_status: str,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    """Persist ChatMemberUpdated evidence without treating it as entitlement truth."""
    update_id = _positive_int(telegram_update_id, label="telegram_update_id")
    chat = _positive_int(chat_id, label="chat_id")
    user = _positive_int(telegram_user_id, label="telegram_user_id")
    old = _nonempty(old_status, label="old_status").lower()
    new = _nonempty(new_status, label="new_status").lower()
    now = _now(now_ts)
    target_path = path or events_path()
    idem = f"chat-member-update:{update_id}:{chat}:{user}"
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target_path)
        record, appended = _append_unlocked(
            path=target_path,
            records=records,
            payload={
                "event_type": EVENT_CHAT_MEMBER_UPDATE,
                "telegram_update_id": update_id,
                "chat_id": chat,
                "telegram_user_id": user,
                "old_status": old,
                "new_status": new,
                "occurred_at_epoch": now,
            },
            idempotency_key=idem,
        )
    return {"status": "RECORDED" if appended else "DUPLICATE", "record": record}


def reconcile_all_known_subscribers(
    *,
    apply_actions: bool = False,
    now_ts: float | int | None = None,
    api: MembershipAPI | None = None,
    send_fn=telegram_publisher.send_message,
    path: str | None = None,
    subscription_path: str | None = None,
    notification_path: str | None = None,
) -> list[Dict[str, Any]]:
    latest: Dict[tuple[str, str], Dict[str, Any]] = {}
    for row in subscription_registry.load_subscription_events(subscription_path):
        key = (str(row.get("subscriber_ref")), str(row.get("strategy_product_id")))
        latest[key] = dict(row)
    results: list[Dict[str, Any]] = []
    for subscriber, product in sorted(latest):
        results.append(
            reconcile_membership(
                subscriber_ref=subscriber,
                strategy_product_id=product,
                now_ts=now_ts,
                apply_actions=apply_actions,
                api=api,
                send_fn=send_fn,
                path=path,
                subscription_path=subscription_path,
                notification_path=notification_path,
            )
        )
    return results


def automatic_reconciliation_enabled() -> bool:
    return os.getenv("BILLING_MEMBERSHIP_RECONCILER_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
