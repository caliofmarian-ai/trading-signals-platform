from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from billing import payment_ledger, subscription_registry
from billing.contracts import (
    BillingContractError,
    get_plan,
    get_strategy_product,
    load_billing_contract,
)
from core import storage, telegram_publisher

NOTIFICATION_POINTS = (
    ("T_MINUS_3D", -3 * 24 * 60 * 60),
    ("T_MINUS_1D", -1 * 24 * 60 * 60),
    ("T0", 0),
    ("PLUS_24H", 24 * 60 * 60),
    ("PLUS_48H", 48 * 60 * 60),
)
CLIENT_ACTIONS = frozenset(
    {
        "KEEP_CURRENT_PLAN",
        "UPGRADE",
        "DOWNGRADE",
        "CANCEL",
        "PAYMENT_NOT_DETECTED",
        "SUPPORT",
    }
)
DELIVERY_RESULTS = frozenset({"SENT", "FAILED", "FAILED_TERMINAL"})
CALLBACK_PREFIX = "BILL:I:"
MAX_DELIVERY_ATTEMPTS = 5
RETRY_DELAYS_SECONDS = (60, 5 * 60, 15 * 60, 60 * 60, 4 * 60 * 60)
SCHEDULER_SCAN_INTERVAL_SECONDS = 60

EVENT_TARGET_BOUND = "BILLING_NOTIFICATION_TARGET_BOUND"
EVENT_DELIVERY = "BILLING_NOTIFICATION_DELIVERY"
EVENT_CLIENT_INTENT = "BILLING_CLIENT_INTENT_RECORDED"
EVENT_CLIENT_INTENT_HANDOFF = "BILLING_CLIENT_INTENT_PAYMENT_HANDOFF"
EVENT_DOWNGRADE_EVIDENCE = "BILLING_AUTO_DOWNGRADE_EVIDENCE"

_LOCK_NAME = "billing_notification_scheduler"
_EVENTS_RELATIVE = ("billing", "notification_events.jsonl")
_TIER_RANK = {"FREE": 0, "BASIC": 1, "PRO": 2, "ELITE": 3}
_LAST_SCAN_MONOTONIC = 0.0


class BillingNotificationError(RuntimeError):
    """Raised when notification/client-intent evidence is unsafe or inconsistent."""


def events_path() -> str:
    return storage.root_path(*_EVENTS_RELATIVE)


def _now(value: float | int | None = None) -> int:
    return int(time.time() if value is None else value)


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BillingNotificationError(f"{label} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise BillingNotificationError(f"{label} must be a positive integer")
    try:
        result = int(value)
    except Exception as exc:
        raise BillingNotificationError(f"{label} must be a positive integer") from exc
    if result <= 0:
        raise BillingNotificationError(f"{label} must be a positive integer")
    return result


def _opaque_id() -> str:
    return str(uuid.uuid4())


def _stable_token(value: str, *, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _contract() -> Dict[str, Any]:
    try:
        return load_billing_contract()
    except BillingContractError as exc:
        raise BillingNotificationError(str(exc)) from exc


def _product(strategy_product_id: str) -> Dict[str, Any]:
    try:
        return get_strategy_product(strategy_product_id, _contract())
    except BillingContractError as exc:
        raise BillingNotificationError(str(exc)) from exc


def _plan(strategy_product_id: str, plan_id: str) -> Dict[str, Any]:
    try:
        plan = get_plan(plan_id, _contract())
    except BillingContractError as exc:
        raise BillingNotificationError(str(exc)) from exc
    product = _product(strategy_product_id)
    owned = {
        str(row.get("plan_id"))
        for row in product.get("plans", [])
        if isinstance(row, dict)
    }
    if plan_id not in owned:
        raise BillingNotificationError(
            f"plan_id {plan_id} is not owned by strategy_product_id {strategy_product_id}"
        )
    return dict(plan)


def _read_events_unlocked(path: str) -> list[Dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise BillingNotificationError(
            f"Unable to read notification event log: {target}"
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
            raise BillingNotificationError(
                f"Notification event log JSON corruption at line {line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise BillingNotificationError(
                f"Notification event at line {line_number} is not an object"
            )
        event_id = _nonempty(
            record.get("billing_notification_event_id"),
            label="billing_notification_event_id",
        )
        if event_id in ids:
            raise BillingNotificationError(
                f"Duplicate billing_notification_event_id: {event_id}"
            )
        ids.add(event_id)
        seq = record.get("billing_notification_seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise BillingNotificationError(
                f"Invalid billing_notification_seq at line {line_number}"
            )
        if seq in seqs:
            raise BillingNotificationError(f"Duplicate billing_notification_seq: {seq}")
        seqs.add(seq)
        records.append(record)

    if records:
        actual = [int(record["billing_notification_seq"]) for record in records]
        expected = list(range(1, len(records) + 1))
        if actual != expected:
            raise BillingNotificationError(
                "Notification event sequence is non-contiguous: "
                f"expected={expected} actual={actual}"
            )
    return records


def load_events(path: str | None = None) -> list[Dict[str, Any]]:
    return _read_events_unlocked(path or events_path())


def _append_unlocked(
    path: str,
    records: list[Dict[str, Any]],
    payload: Mapping[str, Any],
) -> Dict[str, Any]:
    record = dict(payload)
    record.pop("billing_notification_event_id", None)
    record.pop("billing_notification_seq", None)
    record["billing_notification_event_id"] = _opaque_id()
    record["billing_notification_seq"] = len(records) + 1
    storage.append_jsonl(path, record)
    return record


def _find_idempotency(
    records: Iterable[Mapping[str, Any]], key: str
) -> Optional[Mapping[str, Any]]:
    for record in records:
        if record.get("idempotency_key") == key:
            return record
    return None


def bind_private_delivery_target(
    *,
    subscriber_ref: str,
    telegram_user_id: int,
    telegram_chat_id: int,
    strategy_product_id: str = "BINARY_TRADING",
    audit_correlation_id: str | None = None,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    """Bind an explicit private-DM address to a commercial subscriber identity."""

    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    _product(product)
    user_id = _positive_int(telegram_user_id, label="telegram_user_id")
    chat_id = _positive_int(telegram_chat_id, label="telegram_chat_id")
    if user_id != chat_id:
        raise BillingNotificationError(
            "Billing notifications require an explicit private Telegram chat "
            "where chat_id == user_id"
        )
    now = _now(now_ts)
    target = path or events_path()
    idem = f"delivery-target:{subscriber}:{product}:{user_id}:{chat_id}"

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {
                "status": "DUPLICATE",
                "appended": False,
                "record": dict(existing),
            }
        record = _append_unlocked(
            target,
            records,
            {
                "event_type": EVENT_TARGET_BOUND,
                "subscriber_ref": subscriber,
                "strategy_product_id": product,
                "telegram_user_id": user_id,
                "telegram_chat_id": chat_id,
                "occurred_at_epoch": now,
                "idempotency_key": idem,
                "audit_correlation_id": audit_correlation_id or _opaque_id(),
            },
        )
        return {"status": "BOUND", "appended": True, "record": record}


def _latest_target(
    records: Iterable[Mapping[str, Any]],
    subscriber_ref: str,
    strategy_product_id: str,
) -> Optional[Dict[str, Any]]:
    matches = [
        record
        for record in records
        if record.get("event_type") == EVENT_TARGET_BOUND
        and record.get("subscriber_ref") == subscriber_ref
        and record.get("strategy_product_id") == strategy_product_id
    ]
    return dict(matches[-1]) if matches else None


def _notification_key(subscription: Mapping[str, Any], point: str) -> str:
    return (
        f"{subscription['subscription_id']}:"
        f"{subscription.get('expires_at_epoch')}:{point}"
    )


def _callback_token(notification_key: str) -> str:
    return _stable_token(f"billing-intent:{notification_key}")


def _client_intent_id(subscription: Mapping[str, Any]) -> str:
    seed = (
        f"billing-client-intent:{subscription['subscription_id']}:"
        f"{subscription.get('expires_at_epoch')}"
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def _latest_subscription_rows(
    subscription_path: str | None = None,
) -> list[Dict[str, Any]]:
    events = subscription_registry.load_subscription_events(subscription_path)
    latest: Dict[tuple[str, str], Dict[str, Any]] = {}
    for record in events:
        key = (
            str(record.get("subscriber_ref")),
            str(record.get("strategy_product_id")),
        )
        latest[key] = dict(record)
    return list(latest.values())


def _plan_choices(subscription: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    product_id = str(subscription["strategy_product_id"])
    current_tier = str(subscription["tier"])
    rank = _TIER_RANK.get(current_tier)
    if rank is None:
        raise BillingNotificationError(f"Unsupported current tier: {current_tier}")
    product = _product(product_id)
    upgrades: list[str] = []
    downgrades: list[str] = []
    for plan in product.get("plans", []):
        if not isinstance(plan, dict):
            continue
        tier = str(plan.get("tier") or "")
        plan_id = str(plan.get("plan_id") or "")
        if tier not in _TIER_RANK or not plan_id:
            continue
        if _TIER_RANK[tier] > rank:
            upgrades.append(plan_id)
        elif 0 < _TIER_RANK[tier] < rank:
            downgrades.append(plan_id)
    return upgrades, downgrades


def _callback_data(
    token: str,
    action: str,
    strategy_product_id: str,
    plan_id: str | None = None,
) -> str:
    action_codes = {
        "KEEP_CURRENT_PLAN": "K",
        "UPGRADE": "U",
        "DOWNGRADE": "D",
        "CANCEL": "C",
        "PAYMENT_NOT_DETECTED": "N",
        "SUPPORT": "S",
    }
    code = action_codes[action]
    suffix = ""
    if plan_id is not None:
        tier = str(_plan(strategy_product_id, plan_id).get("tier") or "")
        if tier not in _TIER_RANK:
            raise BillingNotificationError(
                f"Unsupported callback target tier: {tier}"
            )
        suffix = f":{tier}"
    callback = f"{CALLBACK_PREFIX}{token}:{code}{suffix}"
    if len(callback.encode("utf-8")) > 64:
        raise BillingNotificationError(
            "Billing callback_data exceeds Telegram 64-byte limit"
        )
    return callback


def _render_notification(
    subscription: Mapping[str, Any], point: str, token: str
) -> tuple[str, Dict[str, Any]]:
    product_id = str(subscription["strategy_product_id"])
    tier = str(subscription["tier"])
    expires = int(subscription["expires_at_epoch"])
    point_label = {
        "T_MINUS_3D": "3-day renewal reminder",
        "T_MINUS_1D": "1-day renewal reminder",
        "T0": "subscription period ended",
        "PLUS_24H": "24 hours after expiry",
        "PLUS_48H": "48 hours after expiry",
    }[point]
    text = (
        f"Billing update — {point_label}.\n"
        f"Current plan: {tier}.\n"
        f"Period end (UTC epoch): {expires}.\n\n"
        "Choose what you want to do. A button records your intent only; "
        "payment, entitlement and Telegram membership remain separate truths."
    )
    upgrades, downgrades = _plan_choices(subscription)
    rows: list[list[Dict[str, str]]] = [
        [
            {
                "text": "Keep current plan",
                "callback_data": _callback_data(
                    token, "KEEP_CURRENT_PLAN", product_id
                ),
            }
        ]
    ]
    for plan_id in upgrades:
        tier_name = str(_plan(product_id, plan_id)["tier"])
        rows.append(
            [
                {
                    "text": f"Upgrade to {tier_name}",
                    "callback_data": _callback_data(
                        token, "UPGRADE", product_id, plan_id
                    ),
                }
            ]
        )
    for plan_id in downgrades:
        tier_name = str(_plan(product_id, plan_id)["tier"])
        rows.append(
            [
                {
                    "text": f"Downgrade to {tier_name}",
                    "callback_data": _callback_data(
                        token, "DOWNGRADE", product_id, plan_id
                    ),
                }
            ]
        )
    rows.extend(
        [
            [
                {
                    "text": "Cancel at period end",
                    "callback_data": _callback_data(
                        token, "CANCEL", product_id
                    ),
                }
            ],
            [
                {
                    "text": "Payment not detected",
                    "callback_data": _callback_data(
                        token, "PAYMENT_NOT_DETECTED", product_id
                    ),
                },
                {
                    "text": "Support",
                    "callback_data": _callback_data(
                        token, "SUPPORT", product_id
                    ),
                },
            ],
        ]
    )
    return text, {"inline_keyboard": rows}


def _delivery_attempts(
    records: Iterable[Mapping[str, Any]], notification_key: str
) -> list[Dict[str, Any]]:
    return [
        dict(record)
        for record in records
        if record.get("event_type") == EVENT_DELIVERY
        and record.get("notification_key") == notification_key
    ]


def _retry_due(attempts: list[Mapping[str, Any]], now: int) -> bool:
    if not attempts:
        return True
    latest = attempts[-1]
    if latest.get("delivery_result") in {"SENT", "FAILED_TERMINAL"}:
        return False
    next_retry = latest.get("next_retry_at_epoch")
    return next_retry is not None and now >= int(next_retry)


def _notification_due(
    subscription: Mapping[str, Any], point_offset: int, now: int
) -> bool:
    expires = subscription.get("expires_at_epoch")
    if expires is None:
        return False
    starts = subscription.get("starts_at_epoch")
    due_at = int(expires) + point_offset
    if starts is not None and due_at < int(starts):
        return False
    return now >= due_at


def _append_delivery_result(
    *,
    path: str,
    records: list[Dict[str, Any]],
    subscription: Mapping[str, Any],
    target: Mapping[str, Any],
    point: str,
    due_at: int,
    notification_key: str,
    callback_token: str,
    attempt_number: int,
    delivery_result: str,
    telegram_message_id: int | None,
    error: str | None,
    occurred_at: int,
) -> Dict[str, Any]:
    if delivery_result not in DELIVERY_RESULTS:
        raise BillingNotificationError(
            f"Unsupported delivery_result: {delivery_result}"
        )
    next_retry: int | None = None
    if delivery_result == "FAILED" and attempt_number < MAX_DELIVERY_ATTEMPTS:
        delay_index = min(
            attempt_number - 1, len(RETRY_DELAYS_SECONDS) - 1
        )
        next_retry = occurred_at + RETRY_DELAYS_SECONDS[delay_index]
    idem = f"delivery:{notification_key}:attempt:{attempt_number}"
    existing = _find_idempotency(records, idem)
    if existing is not None:
        return dict(existing)
    return _append_unlocked(
        path,
        records,
        {
            "event_type": EVENT_DELIVERY,
            "subscriber_ref": subscription["subscriber_ref"],
            "strategy_product_id": subscription["strategy_product_id"],
            "subscription_id": subscription["subscription_id"],
            "source_subscription_event_id": subscription[
                "subscription_event_id"
            ],
            "entitlement_version": subscription["entitlement_version"],
            "plan_id": subscription["plan_id"],
            "tier": subscription["tier"],
            "period_expires_at_epoch": subscription["expires_at_epoch"],
            "notification_point": point,
            "notification_due_at_epoch": due_at,
            "notification_key": notification_key,
            "callback_token": callback_token,
            "attempt_number": attempt_number,
            "delivery_result": delivery_result,
            "telegram_user_id": target["telegram_user_id"],
            "telegram_chat_id": target["telegram_chat_id"],
            "telegram_message_id": telegram_message_id,
            "next_retry_at_epoch": next_retry,
            "error": error,
            "occurred_at_epoch": occurred_at,
            "idempotency_key": idem,
            "audit_correlation_id": _opaque_id(),
        },
    )


def _send_one_notification(
    *,
    subscription: Mapping[str, Any],
    target: Mapping[str, Any],
    point: str,
    point_offset: int,
    records: list[Dict[str, Any]],
    path: str,
    now: int,
    send_fn: Callable[..., Any],
) -> Optional[Dict[str, Any]]:
    expires = int(subscription["expires_at_epoch"])
    due_at = expires + point_offset
    key = _notification_key(subscription, point)
    attempts = _delivery_attempts(records, key)
    if not _retry_due(attempts, now):
        return None
    attempt_number = len(attempts) + 1
    if attempt_number > MAX_DELIVERY_ATTEMPTS:
        return None
    token = _callback_token(key)
    text, markup = _render_notification(subscription, point, token)
    try:
        result = send_fn(
            chat_id=int(target["telegram_chat_id"]),
            text=text,
            reply_markup=markup,
            thread_id=None,
        )
        message_id: int | None = None
        if isinstance(result, dict):
            raw = (result.get("result") or {}).get("message_id")
            if raw is not None:
                try:
                    message_id = int(raw)
                except Exception:
                    message_id = None
        return _append_delivery_result(
            path=path,
            records=records,
            subscription=subscription,
            target=target,
            point=point,
            due_at=due_at,
            notification_key=key,
            callback_token=token,
            attempt_number=attempt_number,
            delivery_result="SENT",
            telegram_message_id=message_id,
            error=None,
            occurred_at=now,
        )
    except Exception as exc:
        result_name = (
            "FAILED_TERMINAL"
            if attempt_number >= MAX_DELIVERY_ATTEMPTS
            else "FAILED"
        )
        return _append_delivery_result(
            path=path,
            records=records,
            subscription=subscription,
            target=target,
            point=point,
            due_at=due_at,
            notification_key=key,
            callback_token=token,
            attempt_number=attempt_number,
            delivery_result=result_name,
            telegram_message_id=None,
            error=telegram_publisher._sanitize(str(exc)),
            occurred_at=now,
        )


def _required_notification_keys(
    subscription: Mapping[str, Any]
) -> list[str]:
    expires = subscription.get("expires_at_epoch")
    starts = subscription.get("starts_at_epoch")
    if expires is None:
        return []
    required: list[str] = []
    for point, offset in NOTIFICATION_POINTS:
        due_at = int(expires) + offset
        if starts is not None and due_at < int(starts):
            continue
        required.append(_notification_key(subscription, point))
    return required


def _sent_delivery_for_key(
    records: Iterable[Mapping[str, Any]], key: str
) -> Optional[Dict[str, Any]]:
    matches = [
        dict(record)
        for record in records
        if record.get("event_type") == EVENT_DELIVERY
        and record.get("notification_key") == key
        and record.get("delivery_result") == "SENT"
    ]
    return matches[-1] if matches else None


def _latest_intent_events(
    records: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for record in records:
        intent_id = record.get("client_intent_id")
        if intent_id:
            latest[str(intent_id)] = dict(record)
    return latest


def _active_client_intents_for_subscription(
    records: Iterable[Mapping[str, Any]],
    subscription: Mapping[str, Any],
) -> list[Dict[str, Any]]:
    latest = _latest_intent_events(records)
    active: list[Dict[str, Any]] = []
    for record in latest.values():
        if record.get("subscription_id") != subscription.get("subscription_id"):
            continue
        if record.get("period_expires_at_epoch") != subscription.get(
            "expires_at_epoch"
        ):
            continue
        if record.get("client_intent_status") in {
            "RECORDED",
            "PAYMENT_PENDING",
            "SUPPORT_REQUIRED",
        }:
            active.append(record)
    return active


def _consumed_settlement_ids(
    subscription: Mapping[str, Any],
    subscription_path: str | None,
) -> set[str]:
    consumed: set[str] = set()
    for record in subscription_registry.load_subscription_events(
        subscription_path
    ):
        if record.get("subscriber_ref") != subscription.get("subscriber_ref"):
            continue
        if record.get("strategy_product_id") != subscription.get(
            "strategy_product_id"
        ):
            continue
        ledger_id = record.get("last_payment_ledger_event_id")
        if isinstance(ledger_id, str) and ledger_id:
            consumed.add(ledger_id)
    return consumed


def _unconsumed_settled_payment_exists(
    subscription: Mapping[str, Any],
    payment_path: str | None,
    subscription_path: str | None,
) -> bool:
    consumed = _consumed_settlement_ids(subscription, subscription_path)
    for record in payment_ledger.load_ledger(payment_path):
        if record.get("subscriber_ref") != subscription.get("subscriber_ref"):
            continue
        if record.get("strategy_product_id") != subscription.get(
            "strategy_product_id"
        ):
            continue
        if (
            record.get("payment_state") != "SETTLED"
            or record.get("reconciliation_result") != "MATCHED"
        ):
            continue
        if record.get("ledger_event_id") not in consumed:
            return True
    return False


def build_auto_downgrade_evidence(
    *,
    subscription: Mapping[str, Any],
    now_ts: float | int | None = None,
    path: str | None = None,
    payment_path: str | None = None,
    subscription_path: str | None = None,
) -> Dict[str, Any]:
    """Build the #163 proof required by #162 before +72h FREE downgrade."""

    now = _now(now_ts)
    if subscription.get("tier") == "FREE":
        return {"ready": False, "reason": "ALREADY_FREE"}
    auto_at = subscription.get("auto_downgrade_at_epoch")
    if auto_at is None or now < int(auto_at):
        return {"ready": False, "reason": "PLUS_72H_NOT_REACHED"}
    target = path or events_path()
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        required_keys = _required_notification_keys(subscription)
        deliveries: list[Dict[str, Any]] = []
        missing: list[str] = []
        for key in required_keys:
            delivery = _sent_delivery_for_key(records, key)
            if delivery is None:
                missing.append(key)
            else:
                deliveries.append(delivery)
        if missing:
            return {
                "ready": False,
                "reason": "REQUIRED_DELIVERY_EVIDENCE_MISSING",
                "missing_notification_keys": missing,
            }
        active_intents = _active_client_intents_for_subscription(
            records, subscription
        )
        if active_intents:
            return {
                "ready": False,
                "reason": "RECORDED_CLIENT_INTENT_ACTIVE",
                "client_intent_ids": [
                    row["client_intent_id"] for row in active_intents
                ],
            }
        if _unconsumed_settled_payment_exists(
            subscription, payment_path, subscription_path
        ):
            return {
                "ready": False,
                "reason": "UNCONSUMED_SETTLED_PAYMENT_EXISTS",
            }

        digest_source = "|".join(
            [
                str(subscription["subscription_id"]),
                str(subscription["expires_at_epoch"]),
            ]
            + [
                str(row["billing_notification_event_id"])
                for row in deliveries
            ]
        )
        evidence_id = (
            "notif-"
            + hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:24]
        )
        idem = f"auto-downgrade-evidence:{evidence_id}"
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {
                "ready": True,
                "reason": "READY",
                "downgrade_evidence_id": evidence_id,
                "record": dict(existing),
            }
        record = _append_unlocked(
            target,
            records,
            {
                "event_type": EVENT_DOWNGRADE_EVIDENCE,
                "subscriber_ref": subscription["subscriber_ref"],
                "strategy_product_id": subscription[
                    "strategy_product_id"
                ],
                "subscription_id": subscription["subscription_id"],
                "source_subscription_event_id": subscription[
                    "subscription_event_id"
                ],
                "period_expires_at_epoch": subscription[
                    "expires_at_epoch"
                ],
                "required_notification_keys": required_keys,
                "delivery_event_ids": [
                    row["billing_notification_event_id"]
                    for row in deliveries
                ],
                "downgrade_evidence_id": evidence_id,
                "occurred_at_epoch": now,
                "idempotency_key": idem,
                "audit_correlation_id": _opaque_id(),
            },
        )
        return {
            "ready": True,
            "reason": "READY",
            "downgrade_evidence_id": evidence_id,
            "record": record,
        }


def run_notification_cycle(
    *,
    now_ts: float | int | None = None,
    path: str | None = None,
    subscription_path: str | None = None,
    payment_path: str | None = None,
    send_fn: Callable[..., Any] = telegram_publisher.send_message,
) -> Dict[str, Any]:
    now = _now(now_ts)
    target_path = path or events_path()
    deliveries: list[Dict[str, Any]] = []
    deadline_results: list[Dict[str, Any]] = []

    for subscription in _latest_subscription_rows(subscription_path):
        if (
            subscription.get("tier") == "FREE"
            or subscription.get("expires_at_epoch") is None
        ):
            continue
        subscriber = str(subscription["subscriber_ref"])
        product = str(subscription["strategy_product_id"])

        deadline = subscription_registry.evaluate_deadlines(
            subscriber_ref=subscriber,
            strategy_product_id=product,
            now_ts=now,
            path=subscription_path,
        )
        if deadline.get("record"):
            subscription = dict(deadline["record"])
        deadline_results.append(deadline)

        appended_for_subscription: list[Dict[str, Any]] = []
        with storage.with_lock(_LOCK_NAME):
            records = _read_events_unlocked(target_path)
            delivery_target = _latest_target(records, subscriber, product)
            if delivery_target is not None:
                for point, offset in NOTIFICATION_POINTS:
                    if not _notification_due(subscription, offset, now):
                        continue
                    result = _send_one_notification(
                        subscription=subscription,
                        target=delivery_target,
                        point=point,
                        point_offset=offset,
                        records=records + appended_for_subscription,
                        path=target_path,
                        now=now,
                        send_fn=send_fn,
                    )
                    if result is not None:
                        appended_for_subscription.append(result)
                        deliveries.append(result)

        latest = subscription_registry.current_subscription(
            subscriber, product, subscription_path
        )
        if latest is None:
            continue
        evidence = build_auto_downgrade_evidence(
            subscription=latest,
            now_ts=now,
            path=target_path,
            payment_path=payment_path,
            subscription_path=subscription_path,
        )
        if evidence.get("ready"):
            deadline_results.append(
                subscription_registry.evaluate_deadlines(
                    subscriber_ref=subscriber,
                    strategy_product_id=product,
                    now_ts=now,
                    downgrade_evidence_id=str(
                        evidence["downgrade_evidence_id"]
                    ),
                    path=subscription_path,
                )
            )

    return {
        "status": "OK",
        "now_epoch": now,
        "delivery_events": deliveries,
        "deadline_results": deadline_results,
    }


def maybe_run_notification_cycle() -> Optional[Dict[str, Any]]:
    global _LAST_SCAN_MONOTONIC
    current = time.monotonic()
    if (
        _LAST_SCAN_MONOTONIC
        and current - _LAST_SCAN_MONOTONIC
        < SCHEDULER_SCAN_INTERVAL_SECONDS
    ):
        return None
    _LAST_SCAN_MONOTONIC = current
    return run_notification_cycle()


def _notification_by_token(
    records: Iterable[Mapping[str, Any]], token: str
) -> Optional[Dict[str, Any]]:
    matches = [
        dict(record)
        for record in records
        if record.get("event_type") == EVENT_DELIVERY
        and record.get("delivery_result") == "SENT"
        and record.get("callback_token") == token
    ]
    return matches[-1] if matches else None


def _plan_id_for_tier(strategy_product_id: str, tier: str) -> str:
    product = _product(strategy_product_id)
    matches = [
        str(row.get("plan_id"))
        for row in product.get("plans", [])
        if isinstance(row, dict) and row.get("tier") == tier
    ]
    if len(matches) != 1:
        raise BillingNotificationError(
            f"Expected exactly one {tier} plan for {strategy_product_id}"
        )
    return matches[0]


def parse_callback(data: str) -> tuple[str, str, Optional[str]]:
    text = _nonempty(data, label="callback_data")
    parts = text.split(":")
    if len(parts) not in {4, 5} or parts[0:2] != ["BILL", "I"]:
        raise BillingNotificationError("Malformed billing callback")
    token = _nonempty(parts[2], label="callback_token")
    code = _nonempty(parts[3], label="action_code")
    action_by_code = {
        "K": "KEEP_CURRENT_PLAN",
        "U": "UPGRADE",
        "D": "DOWNGRADE",
        "C": "CANCEL",
        "N": "PAYMENT_NOT_DETECTED",
        "S": "SUPPORT",
    }
    action = action_by_code.get(code)
    if action is None:
        raise BillingNotificationError("Unknown billing callback action")
    tier = parts[4] if len(parts) == 5 else None
    if action in {"UPGRADE", "DOWNGRADE"} and tier is None:
        raise BillingNotificationError(
            "Plan-changing billing callback is missing target tier"
        )
    if action not in {"UPGRADE", "DOWNGRADE"} and tier is not None:
        raise BillingNotificationError(
            "Unexpected target tier in billing callback"
        )
    return token, action, tier


def handle_telegram_callback(
    *,
    telegram_user_id: int,
    telegram_chat_id: int,
    callback_data: str,
    now_ts: float | int | None = None,
    path: str | None = None,
    subscription_path: str | None = None,
) -> Dict[str, Any]:
    user_id = _positive_int(telegram_user_id, label="telegram_user_id")
    chat_id = _positive_int(telegram_chat_id, label="telegram_chat_id")
    token, action, target_tier = parse_callback(callback_data)
    now = _now(now_ts)
    target_path = path or events_path()

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target_path)
        notification = _notification_by_token(records, token)
        if notification is None:
            return {
                "accepted": False,
                "reason": "UNKNOWN_OR_STALE_NOTIFICATION",
                "ack_text": "This billing action is no longer available.",
            }
        subscriber = str(notification["subscriber_ref"])
        product = str(notification["strategy_product_id"])
        current_target = _latest_target(records, subscriber, product)
        if current_target is None:
            return {
                "accepted": False,
                "reason": "DELIVERY_TARGET_NOT_BOUND",
                "ack_text": "Billing action denied.",
            }
        expected_user = int(current_target.get("telegram_user_id") or 0)
        expected_chat = int(current_target.get("telegram_chat_id") or 0)
        if (
            expected_user != user_id
            or expected_chat != chat_id
            or int(notification.get("telegram_user_id") or 0) != user_id
            or int(notification.get("telegram_chat_id") or 0) != chat_id
        ):
            return {
                "accepted": False,
                "reason": "CALLBACK_IDENTITY_MISMATCH",
                "ack_text": "Billing action denied.",
            }

        current = subscription_registry.current_subscription(
            subscriber, product, subscription_path
        )
        if current is None:
            return {
                "accepted": False,
                "reason": "SUBSCRIPTION_NOT_FOUND",
                "ack_text": "Subscription context is unavailable.",
            }
        if (
            current.get("subscription_id")
            != notification.get("subscription_id")
            or current.get("expires_at_epoch")
            != notification.get("period_expires_at_epoch")
        ):
            return {
                "accepted": False,
                "reason": "STALE_SUBSCRIPTION_CONTEXT",
                "ack_text": (
                    "Subscription changed. Open the latest billing message."
                ),
            }

        requested_plan_id: str | None = None
        if target_tier is not None:
            if target_tier not in _TIER_RANK:
                return {
                    "accepted": False,
                    "reason": "UNKNOWN_TARGET_TIER",
                    "ack_text": "Unknown billing plan.",
                }
            requested_plan_id = _plan_id_for_tier(product, target_tier)
            current_rank = _TIER_RANK[str(current["tier"])]
            target_rank = _TIER_RANK[target_tier]
            if action == "UPGRADE" and target_rank <= current_rank:
                return {
                    "accepted": False,
                    "reason": "INVALID_UPGRADE_TARGET",
                    "ack_text": (
                        "That is not an upgrade from your current plan."
                    ),
                }
            if action == "DOWNGRADE" and (
                target_rank >= current_rank or target_tier == "FREE"
            ):
                return {
                    "accepted": False,
                    "reason": "INVALID_DOWNGRADE_TARGET",
                    "ack_text": (
                        "That paid plan is not a valid downgrade target."
                    ),
                }
        elif action == "KEEP_CURRENT_PLAN":
            requested_plan_id = str(current["plan_id"])

        client_intent_id = _client_intent_id(current)
        idem = (
            f"client-intent:{client_intent_id}:{action}:"
            f"{requested_plan_id or 'none'}"
        )
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {
                "accepted": True,
                "reason": "ALREADY_RECORDED",
                "ack_text": "Your billing choice was already recorded.",
                "client_intent_id": existing.get("client_intent_id"),
            }

        status = "RECORDED"
        if action in {"PAYMENT_NOT_DETECTED", "SUPPORT"}:
            status = "SUPPORT_REQUIRED"
        intent = _append_unlocked(
            target_path,
            records,
            {
                "event_type": EVENT_CLIENT_INTENT,
                "client_intent_id": client_intent_id,
                "client_intent_status": status,
                "client_action": action,
                "subscriber_ref": subscriber,
                "strategy_product_id": product,
                "subscription_id": current["subscription_id"],
                "source_subscription_event_id": current[
                    "subscription_event_id"
                ],
                "entitlement_version": current["entitlement_version"],
                "current_plan_id": current["plan_id"],
                "current_tier": current["tier"],
                "requested_plan_id": requested_plan_id,
                "period_expires_at_epoch": current.get(
                    "expires_at_epoch"
                ),
                "notification_key": notification["notification_key"],
                "source_delivery_event_id": notification[
                    "billing_notification_event_id"
                ],
                "telegram_user_id": user_id,
                "telegram_chat_id": chat_id,
                "occurred_at_epoch": now,
                "idempotency_key": idem,
                "audit_correlation_id": _opaque_id(),
            },
        )

    transition: Dict[str, Any] | None = None
    try:
        if action == "CANCEL":
            transition = subscription_registry.cancel_at_period_end(
                subscriber_ref=subscriber,
                strategy_product_id=product,
                now_ts=now,
                audit_correlation_id=str(intent["audit_correlation_id"]),
                path=subscription_path,
            )
        elif action == "DOWNGRADE" and requested_plan_id is not None:
            transition = subscription_registry.request_downgrade(
                subscriber_ref=subscriber,
                strategy_product_id=product,
                target_plan_id=requested_plan_id,
                now_ts=now,
                audit_correlation_id=str(intent["audit_correlation_id"]),
                path=subscription_path,
            )
    except subscription_registry.SubscriptionRegistryError as exc:
        return {
            "accepted": True,
            "reason": "INTENT_RECORDED_TRANSITION_REQUIRES_FOLLOW_UP",
            "ack_text": (
                "Your choice was recorded; billing follow-up is required."
            ),
            "client_intent_id": client_intent_id,
            "transition_error": str(exc),
        }

    ack = {
        "KEEP_CURRENT_PLAN": (
            "Keep-current-plan intent recorded. Payment is not yet verified."
        ),
        "UPGRADE": (
            "Upgrade intent recorded. Payment is required before access changes."
        ),
        "DOWNGRADE": (
            "Downgrade intent recorded for the governed next-period flow."
        ),
        "CANCEL": "Cancellation intent recorded for period end.",
        "PAYMENT_NOT_DETECTED": (
            "Payment-not-detected report recorded for support."
        ),
        "SUPPORT": "Support request recorded.",
    }[action]
    return {
        "accepted": True,
        "reason": "RECORDED",
        "ack_text": ack,
        "client_intent_id": client_intent_id,
        "subscription_transition": transition,
    }


def _payment_intent_creation(
    payment_intent_id: str, payment_path: str | None
) -> Dict[str, Any]:
    try:
        history = payment_ledger.payment_history(
            payment_intent_id, payment_path
        )
    except payment_ledger.PaymentLedgerError as exc:
        raise BillingNotificationError(str(exc)) from exc
    matches = [
        row
        for row in history
        if row.get("event_type") == payment_ledger.EVENT_INTENT_CREATED
    ]
    if len(matches) != 1:
        raise BillingNotificationError(
            "Payment intent must have exactly one creation record"
        )
    return dict(matches[0])


def handoff_payment_intent(
    *,
    client_intent_id: str,
    payment_intent_id: str,
    now_ts: float | int | None = None,
    path: str | None = None,
    subscription_path: str | None = None,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    intent_id = _nonempty(client_intent_id, label="client_intent_id")
    payment_id = _nonempty(payment_intent_id, label="payment_intent_id")
    now = _now(now_ts)
    target = path or events_path()

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        latest = _latest_intent_events(records).get(intent_id)
        if latest is None:
            raise BillingNotificationError(
                f"Unknown client_intent_id: {intent_id}"
            )
        if latest.get("client_action") not in {
            "KEEP_CURRENT_PLAN",
            "UPGRADE",
            "DOWNGRADE",
        }:
            raise BillingNotificationError(
                "Client intent does not own a paid-plan payment handoff"
            )
        idem = f"client-intent-payment-handoff:{intent_id}:{payment_id}"
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {
                "status": "DUPLICATE",
                "appended": False,
                "record": dict(existing),
            }

    current = subscription_registry.current_subscription(
        str(latest["subscriber_ref"]),
        str(latest["strategy_product_id"]),
        subscription_path,
    )
    if current is None:
        raise BillingNotificationError("Subscription context disappeared")
    if (
        current.get("subscription_id") != latest.get("subscription_id")
        or current.get("expires_at_epoch")
        != latest.get("period_expires_at_epoch")
    ):
        raise BillingNotificationError(
            "Client intent belongs to a stale subscription period"
        )

    creation = _payment_intent_creation(payment_id, payment_path)
    expected_plan = latest.get("requested_plan_id")
    if (
        creation.get("subscriber_ref") != latest.get("subscriber_ref")
        or creation.get("strategy_product_id")
        != latest.get("strategy_product_id")
        or creation.get("plan_id") != expected_plan
    ):
        raise BillingNotificationError(
            "Payment intent does not match recorded client intent"
        )

    pending = subscription_registry.record_payment_intent_pending(
        payment_intent_id=payment_id,
        now_ts=now,
        audit_correlation_id=str(
            latest.get("audit_correlation_id") or _opaque_id()
        ),
        path=subscription_path,
        payment_path=payment_path,
    )

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {
                "status": "DUPLICATE",
                "appended": False,
                "record": dict(existing),
                "subscription_transition": pending,
            }
        record = _append_unlocked(
            target,
            records,
            {
                **dict(latest),
                "event_type": EVENT_CLIENT_INTENT_HANDOFF,
                "client_intent_status": "PAYMENT_PENDING",
                "payment_intent_id": payment_id,
                "occurred_at_epoch": now,
                "idempotency_key": idem,
                "audit_correlation_id": (
                    latest.get("audit_correlation_id") or _opaque_id()
                ),
            },
        )
        return {
            "status": "PAYMENT_PENDING",
            "appended": True,
            "record": record,
            "subscription_transition": pending,
        }
