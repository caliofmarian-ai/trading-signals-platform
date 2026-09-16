from __future__ import annotations

import json
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from billing import payment_ledger
from billing.contracts import BillingContractError, get_plan, get_strategy_product, load_billing_contract
from core import storage

GRACE_HOLD_SECONDS = 48 * 60 * 60
AUTO_DOWNGRADE_SECONDS = 72 * 60 * 60
INTENT_PAYMENT_PENDING_SECONDS = 24 * 60 * 60

SUBSCRIPTION_STATES = frozenset(
    {
        "ACTIVE",
        "PAYMENT_DUE",
        "PAYMENT_FAILED",
        "EXPIRED",
        "GRACE_HOLD",
        "INTENT_PAYMENT_PENDING",
        "CANCELED_AT_PERIOD_END",
        "CHARGEBACK_OPEN",
        "REFUND_HOLD",
    }
)
ENTITLEMENT_ACCESS_STATES = frozenset(
    {"ACTIVE", "SUSPENDED", "HOLD", "FREE_FALLBACK"}
)

EVENT_FREE_BOOTSTRAP = "FREE_ENTITLEMENT_BOOTSTRAPPED"
EVENT_ACTIVATED = "SUBSCRIPTION_ACTIVATED"
EVENT_RENEWED = "SUBSCRIPTION_RENEWED"
EVENT_UPGRADED = "SUBSCRIPTION_UPGRADED"
EVENT_DOWNGRADE_SCHEDULED = "SUBSCRIPTION_DOWNGRADE_SCHEDULED"
EVENT_DOWNGRADE_EFFECTIVE = "SUBSCRIPTION_DOWNGRADE_EFFECTIVE"
EVENT_CANCELED = "SUBSCRIPTION_CANCELED_AT_PERIOD_END"
EVENT_PAYMENT_DUE = "SUBSCRIPTION_PAYMENT_DUE"
EVENT_PAYMENT_FAILED = "SUBSCRIPTION_PAYMENT_FAILED"
EVENT_INTENT_PENDING = "SUBSCRIPTION_PAYMENT_INTENT_PENDING"
EVENT_INTENT_EXPIRED = "SUBSCRIPTION_PAYMENT_INTENT_EXPIRED"
EVENT_GRACE_STARTED = "SUBSCRIPTION_GRACE_HOLD_STARTED"
EVENT_AUTO_DOWNGRADED = "SUBSCRIPTION_AUTO_DOWNGRADED_FREE"
EVENT_CHARGEBACK_HOLD = "SUBSCRIPTION_CHARGEBACK_HOLD"
EVENT_REFUND_HOLD = "SUBSCRIPTION_REFUND_HOLD"

_LOCK_NAME = "billing_subscription_registry"
_EVENTS_RELATIVE = ("billing", "subscription_events.jsonl")
_TIER_RANK = {"FREE": 0, "BASIC": 1, "PRO": 2, "ELITE": 3}
_SNAPSHOT_FIELDS = (
    "subscription_id",
    "entitlement_id",
    "subscriber_ref",
    "strategy_product_id",
    "plan_id",
    "tier",
    "state",
    "starts_at_epoch",
    "expires_at_epoch",
    "grace_until_epoch",
    "auto_downgrade_at_epoch",
    "scheduled_plan_id",
    "pending_plan_id",
    "pending_payment_intent_id",
    "intent_pending_until_epoch",
    "resume_state_after_intent",
    "last_payment_intent_id",
    "last_payment_ledger_event_id",
    "proration_evidence",
    "last_downgrade_evidence_id",
)


class SubscriptionRegistryError(RuntimeError):
    """Raised when subscription/entitlement evidence is invalid or contradictory."""


def events_path() -> str:
    return storage.root_path(*_EVENTS_RELATIVE)


def _now(value: float | int | None = None) -> int:
    return int(time.time() if value is None else value)


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SubscriptionRegistryError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    return _nonempty(value, label="optional string")


def _positive_epoch(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SubscriptionRegistryError(f"{label} must be a numeric epoch timestamp")
    result = int(value)
    if result <= 0:
        raise SubscriptionRegistryError(f"{label} must be positive")
    return result


def _opaque_id() -> str:
    return str(uuid.uuid4())


def _stable_free_entitlement_id(subscriber_ref: str, strategy_product_id: str) -> str:
    seed = f"tsp-free-entitlement:{subscriber_ref}:{strategy_product_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def _contract() -> Dict[str, Any]:
    try:
        return load_billing_contract()
    except BillingContractError as exc:
        raise SubscriptionRegistryError(str(exc)) from exc


def _product(strategy_product_id: str) -> Dict[str, Any]:
    try:
        return get_strategy_product(strategy_product_id, _contract())
    except BillingContractError as exc:
        raise SubscriptionRegistryError(str(exc)) from exc


def _plan(plan_id: str) -> Dict[str, Any]:
    try:
        return get_plan(plan_id, _contract())
    except BillingContractError as exc:
        raise SubscriptionRegistryError(str(exc)) from exc


def _plan_for_product(strategy_product_id: str, plan_id: str) -> Dict[str, Any]:
    product = _product(strategy_product_id)
    matches = [
        plan
        for plan in product.get("plans", [])
        if isinstance(plan, dict) and plan.get("plan_id") == plan_id
    ]
    if len(matches) != 1:
        raise SubscriptionRegistryError(
            f"plan_id {plan_id} is not owned by strategy_product_id {strategy_product_id}"
        )
    return dict(matches[0])


def _free_plan_id(strategy_product_id: str) -> str:
    product = _product(strategy_product_id)
    free = [
        plan
        for plan in product.get("plans", [])
        if isinstance(plan, dict) and plan.get("tier") == "FREE"
    ]
    if len(free) != 1:
        raise SubscriptionRegistryError(
            f"Strategy product {strategy_product_id} must expose exactly one FREE plan"
        )
    return str(free[0]["plan_id"])


def _tier_for_product_plan(strategy_product_id: str, plan_id: str) -> str:
    tier = str(_plan_for_product(strategy_product_id, plan_id).get("tier") or "")
    if tier not in _TIER_RANK:
        raise SubscriptionRegistryError(f"Unsupported plan tier: {tier}")
    return tier


def _is_paid_product_plan(strategy_product_id: str, plan_id: str) -> bool:
    return bool(_plan_for_product(strategy_product_id, plan_id).get("requires_payment"))


def _read_events_unlocked(path: str) -> list[Dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise SubscriptionRegistryError(
            f"Unable to read subscription registry: {target}"
        ) from exc

    records: list[Dict[str, Any]] = []
    event_ids: set[str] = set()
    seqs: set[int] = set()
    subscription_versions: Dict[str, int] = {}
    previous_ids: Dict[str, str] = {}

    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SubscriptionRegistryError(
                f"Subscription registry JSON corruption at line {line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise SubscriptionRegistryError(
                f"Subscription registry record at line {line_number} is not an object"
            )

        event_id = _nonempty(
            record.get("subscription_event_id"), label="subscription_event_id"
        )
        if event_id in event_ids:
            raise SubscriptionRegistryError(
                f"Duplicate subscription_event_id: {event_id}"
            )
        event_ids.add(event_id)

        seq = record.get("subscription_seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise SubscriptionRegistryError(
                f"Invalid subscription_seq at line {line_number}"
            )
        if seq in seqs:
            raise SubscriptionRegistryError(f"Duplicate subscription_seq: {seq}")
        seqs.add(seq)

        subscription_id = _nonempty(
            record.get("subscription_id"), label="subscription_id"
        )
        version = record.get("entitlement_version")
        if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
            raise SubscriptionRegistryError(
                f"Invalid entitlement_version at line {line_number}"
            )
        expected_version = subscription_versions.get(subscription_id, 0) + 1
        if version != expected_version:
            raise SubscriptionRegistryError(
                f"Non-contiguous entitlement_version for {subscription_id}: "
                f"expected={expected_version} actual={version}"
            )
        subscription_versions[subscription_id] = version

        expected_previous = previous_ids.get(subscription_id)
        actual_previous = record.get("previous_subscription_event_id")
        if actual_previous != expected_previous:
            raise SubscriptionRegistryError(
                f"Broken subscription event chain for {subscription_id} "
                f"at line {line_number}"
            )
        previous_ids[subscription_id] = event_id

        state = record.get("state")
        if state not in SUBSCRIPTION_STATES:
            raise SubscriptionRegistryError(
                f"Unsupported subscription state in ledger: {state}"
            )
        for field in (
            "subscriber_ref",
            "strategy_product_id",
            "plan_id",
            "tier",
            "entitlement_id",
        ):
            _nonempty(record.get(field), label=field)
        _plan_for_product(
            str(record["strategy_product_id"]), str(record["plan_id"])
        )
        if _tier_for_product_plan(
            str(record["strategy_product_id"]), str(record["plan_id"])
        ) != str(record["tier"]):
            raise SubscriptionRegistryError(
                f"Plan/tier mismatch in subscription ledger at line {line_number}"
            )
        records.append(record)

    if records:
        expected = list(range(1, len(records) + 1))
        actual = [int(record["subscription_seq"]) for record in records]
        if actual != expected:
            raise SubscriptionRegistryError(
                f"Subscription sequence is non-contiguous: "
                f"expected={expected} actual={actual}"
            )
    return records


def load_subscription_events(path: str | None = None) -> list[Dict[str, Any]]:
    return _read_events_unlocked(path or events_path())


def _latest_for_pair(
    records: Iterable[Mapping[str, Any]],
    subscriber_ref: str,
    strategy_product_id: str,
) -> Optional[Mapping[str, Any]]:
    matches = [
        record
        for record in records
        if record.get("subscriber_ref") == subscriber_ref
        and record.get("strategy_product_id") == strategy_product_id
    ]
    if not matches:
        return None
    subscription_ids = {str(record.get("subscription_id")) for record in matches}
    if len(subscription_ids) != 1:
        raise SubscriptionRegistryError(
            "Multiple subscription identities exist for one subscriber/product pair"
        )
    return matches[-1]


def current_subscription(
    subscriber_ref: str,
    strategy_product_id: str,
    path: str | None = None,
) -> Optional[Dict[str, Any]]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    _product(product)
    record = _latest_for_pair(load_subscription_events(path), subscriber, product)
    return dict(record) if record is not None else None


def _snapshot(record: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if record is None:
        return {field: None for field in _SNAPSHOT_FIELDS}
    return {field: record.get(field) for field in _SNAPSHOT_FIELDS}


def _find_idempotency(
    records: Iterable[Mapping[str, Any]], idempotency_key: str
) -> Optional[Mapping[str, Any]]:
    for record in records:
        if record.get("idempotency_key") == idempotency_key:
            return record
    return None


def _append_event_unlocked(
    *,
    path: str,
    records: list[Dict[str, Any]],
    previous: Optional[Mapping[str, Any]],
    changes: Mapping[str, Any],
    event_type: str,
    idempotency_key: str,
    occurred_at_epoch: int,
    reason: str,
    audit_correlation_id: str,
) -> tuple[Dict[str, Any], bool]:
    idem = _nonempty(idempotency_key, label="idempotency_key")
    existing = _find_idempotency(records, idem)
    expected_subscription_id = changes.get(
        "subscription_id", previous.get("subscription_id") if previous else None
    )
    if existing is not None:
        same_identity = (
            existing.get("event_type") == event_type
            and existing.get("subscription_id") == expected_subscription_id
        )
        if not same_identity:
            raise SubscriptionRegistryError(
                "Subscription idempotency key was reused for a different transition"
            )
        return dict(existing), False

    payload = _snapshot(previous)
    payload.update(dict(changes))
    subscription_id = _nonempty(
        payload.get("subscription_id"), label="subscription_id"
    )
    payload["entitlement_id"] = _nonempty(
        payload.get("entitlement_id"), label="entitlement_id"
    )
    payload["subscriber_ref"] = _nonempty(
        payload.get("subscriber_ref"), label="subscriber_ref"
    )
    payload["strategy_product_id"] = _nonempty(
        payload.get("strategy_product_id"), label="strategy_product_id"
    )
    payload["plan_id"] = _nonempty(payload.get("plan_id"), label="plan_id")
    payload["tier"] = _nonempty(payload.get("tier"), label="tier")
    _plan_for_product(payload["strategy_product_id"], payload["plan_id"])
    if _tier_for_product_plan(
        payload["strategy_product_id"], payload["plan_id"]
    ) != payload["tier"]:
        raise SubscriptionRegistryError("Subscription plan/tier mismatch")
    state = payload.get("state")
    if state not in SUBSCRIPTION_STATES:
        raise SubscriptionRegistryError(f"Unsupported subscription state: {state}")

    previous_version = int(previous.get("entitlement_version") or 0) if previous else 0
    record = dict(payload)
    record.update(
        {
            "subscription_event_id": _opaque_id(),
            "subscription_seq": len(records) + 1,
            "event_type": event_type,
            "entitlement_version": previous_version + 1,
            "previous_subscription_event_id": (
                previous.get("subscription_event_id") if previous else None
            ),
            "idempotency_key": idem,
            "occurred_at_epoch": occurred_at_epoch,
            "reason": reason,
            "audit_correlation_id": audit_correlation_id,
        }
    )
    storage.append_jsonl(path, record)
    return record, True


def _base_free_snapshot(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    subscription_id: str | None = None,
    entitlement_id: str | None = None,
    starts_at_epoch: int,
) -> Dict[str, Any]:
    free_plan = _free_plan_id(strategy_product_id)
    return {
        "subscription_id": subscription_id or _opaque_id(),
        "entitlement_id": entitlement_id
        or _stable_free_entitlement_id(subscriber_ref, strategy_product_id),
        "subscriber_ref": subscriber_ref,
        "strategy_product_id": strategy_product_id,
        "plan_id": free_plan,
        "tier": "FREE",
        "state": "ACTIVE",
        "starts_at_epoch": starts_at_epoch,
        "expires_at_epoch": None,
        "grace_until_epoch": None,
        "auto_downgrade_at_epoch": None,
        "scheduled_plan_id": None,
        "pending_plan_id": None,
        "pending_payment_intent_id": None,
        "intent_pending_until_epoch": None,
        "resume_state_after_intent": None,
        "last_payment_intent_id": None,
        "last_payment_ledger_event_id": None,
        "proration_evidence": None,
        "last_downgrade_evidence_id": None,
    }


def ensure_free_entitlement(
    *,
    subscriber_ref: str,
    strategy_product_id: str = "BINARY_TRADING",
    now_ts: float | int | None = None,
    audit_correlation_id: str | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    _product(product)
    now = _now(now_ts)
    target = path or events_path()
    idem = (
        "free-bootstrap:"
        f"{uuid.uuid5(uuid.NAMESPACE_URL, subscriber + ':' + product)}"
    )
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_for_pair(records, subscriber, product)
        if current is not None:
            return {
                "status": "EXISTS",
                "appended": False,
                "record": dict(current),
            }
        base = _base_free_snapshot(
            subscriber_ref=subscriber,
            strategy_product_id=product,
            starts_at_epoch=now,
        )
        record, appended = _append_event_unlocked(
            path=target,
            records=records,
            previous=None,
            changes=base,
            event_type=EVENT_FREE_BOOTSTRAP,
            idempotency_key=idem,
            occurred_at_epoch=now,
            reason="FREE_BASELINE",
            audit_correlation_id=audit_correlation_id or _opaque_id(),
        )
        return {"status": "CREATED", "appended": appended, "record": record}


def _payment_intent_creation(
    payment_intent_id: str, payment_path: str | None
) -> Dict[str, Any]:
    try:
        history = payment_ledger.payment_history(payment_intent_id, payment_path)
    except payment_ledger.PaymentLedgerError as exc:
        raise SubscriptionRegistryError(str(exc)) from exc
    matches = [
        record
        for record in history
        if record.get("event_type") == payment_ledger.EVENT_INTENT_CREATED
    ]
    if len(matches) != 1:
        raise SubscriptionRegistryError(
            f"Payment intent must have exactly one creation record: {payment_intent_id}"
        )
    return dict(matches[0])


def _verified_settlement(
    payment_intent_id: str, payment_path: str | None
) -> Dict[str, Any]:
    try:
        settled = payment_ledger.settled_payment_record(payment_intent_id, payment_path)
    except payment_ledger.PaymentLedgerError as exc:
        raise SubscriptionRegistryError(str(exc)) from exc
    if settled is None:
        raise SubscriptionRegistryError(
            f"Payment intent is not uniquely SETTLED + MATCHED: {payment_intent_id}"
        )
    return dict(settled)


def _validate_period(start_ts: Any, end_ts: Any) -> tuple[int, int]:
    start = _positive_epoch(start_ts, label="period_start_ts")
    end = _positive_epoch(end_ts, label="period_end_ts")
    if end <= start:
        raise SubscriptionRegistryError("period_end_ts must be after period_start_ts")
    return start, end


def calculate_proration(
    *,
    source_period_price_minor: int,
    target_period_price_minor: int,
    period_start_ts: float | int,
    period_end_ts: float | int,
    effective_at_ts: float | int,
    currency: str,
) -> Dict[str, Any]:
    if (
        isinstance(source_period_price_minor, bool)
        or not isinstance(source_period_price_minor, int)
        or source_period_price_minor < 0
    ):
        raise SubscriptionRegistryError(
            "source_period_price_minor must be a non-negative integer"
        )
    if (
        isinstance(target_period_price_minor, bool)
        or not isinstance(target_period_price_minor, int)
        or target_period_price_minor < 0
    ):
        raise SubscriptionRegistryError(
            "target_period_price_minor must be a non-negative integer"
        )
    start, end = _validate_period(period_start_ts, period_end_ts)
    effective = _positive_epoch(effective_at_ts, label="effective_at_ts")
    if not (start <= effective < end):
        raise SubscriptionRegistryError(
            "Upgrade effective_at_ts must fall inside the current period"
        )
    ccy = _nonempty(currency, label="currency").upper()
    if len(ccy) != 3 or not ccy.isalpha():
        raise SubscriptionRegistryError("currency must be a three-letter code")

    period_seconds = end - start
    remaining_seconds = end - effective

    def prorated(full_price: int) -> int:
        value = (
            Decimal(full_price)
            * Decimal(remaining_seconds)
            / Decimal(period_seconds)
        )
        return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    source_credit = prorated(source_period_price_minor)
    target_charge = prorated(target_period_price_minor)
    net_due = max(target_charge - source_credit, 0)
    return {
        "source_period_price_minor": source_period_price_minor,
        "target_period_price_minor": target_period_price_minor,
        "source_credit_minor": source_credit,
        "target_prorated_charge_minor": target_charge,
        "net_due_minor": net_due,
        "currency": ccy,
        "period_start_epoch": start,
        "period_end_epoch": end,
        "effective_at_epoch": effective,
        "period_seconds": period_seconds,
        "remaining_seconds": remaining_seconds,
        "rounding": "ROUND_HALF_UP_MINOR_UNIT",
    }


def _configured_price_if_any(
    strategy_product_id: str, plan_id: str
) -> tuple[Optional[int], Optional[str]]:
    pricing = _plan_for_product(strategy_product_id, plan_id).get("pricing")
    if not isinstance(pricing, dict) or pricing.get("status") != "CONFIGURED":
        return None, None
    amount = pricing.get("amount_minor")
    currency = pricing.get("currency")
    if isinstance(amount, int) and isinstance(currency, str):
        return amount, currency.upper()
    raise SubscriptionRegistryError(
        f"Configured plan pricing is malformed: {plan_id}"
    )


def _validate_upgrade_proration(
    *,
    current: Mapping[str, Any],
    target_plan_id: str,
    settlement: Mapping[str, Any],
    effective_at: int,
    evidence: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    if not isinstance(evidence, Mapping):
        raise SubscriptionRegistryError(
            "Mid-period upgrade requires proration_evidence"
        )
    required = {
        "source_period_price_minor",
        "target_period_price_minor",
        "currency",
    }
    missing = sorted(required - set(evidence))
    if missing:
        raise SubscriptionRegistryError(
            f"proration_evidence missing keys: {missing}"
        )
    start = current.get("starts_at_epoch")
    end = current.get("expires_at_epoch")
    if start is None or end is None:
        raise SubscriptionRegistryError(
            "Current paid period is missing start/end timestamps"
        )
    calculation = calculate_proration(
        source_period_price_minor=evidence["source_period_price_minor"],
        target_period_price_minor=evidence["target_period_price_minor"],
        period_start_ts=start,
        period_end_ts=end,
        effective_at_ts=effective_at,
        currency=evidence["currency"],
    )
    if calculation["net_due_minor"] != settlement.get("amount_minor"):
        raise SubscriptionRegistryError(
            "Settled upgrade payment does not equal governed prorated net due"
        )
    if calculation["currency"] != str(settlement.get("currency") or "").upper():
        raise SubscriptionRegistryError(
            "Proration currency does not match settlement currency"
        )

    product_id = str(current["strategy_product_id"])
    source_configured, source_ccy = _configured_price_if_any(
        product_id, str(current["plan_id"])
    )
    target_configured, target_ccy = _configured_price_if_any(
        product_id, target_plan_id
    )
    if source_configured is not None:
        if (
            source_configured != calculation["source_period_price_minor"]
            or source_ccy != calculation["currency"]
        ):
            raise SubscriptionRegistryError(
                "Proration source price conflicts with configured catalog price"
            )
    if target_configured is not None:
        if (
            target_configured != calculation["target_period_price_minor"]
            or target_ccy != calculation["currency"]
        ):
            raise SubscriptionRegistryError(
                "Proration target price conflicts with configured catalog price"
            )
    return calculation


def activate_from_settled_payment(
    *,
    payment_intent_id: str,
    period_start_ts: float | int,
    period_end_ts: float | int,
    effective_at_ts: float | int | None = None,
    subscription_id: str | None = None,
    proration_evidence: Mapping[str, Any] | None = None,
    audit_correlation_id: str | None = None,
    path: str | None = None,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    intent_id = _nonempty(payment_intent_id, label="payment_intent_id")
    intent = _payment_intent_creation(intent_id, payment_path)
    settlement = _verified_settlement(intent_id, payment_path)
    subscriber = _nonempty(intent.get("subscriber_ref"), label="subscriber_ref")
    product_id = _nonempty(
        intent.get("strategy_product_id"), label="strategy_product_id"
    )
    target_plan = _nonempty(intent.get("plan_id"), label="plan_id")
    target_plan_row = _plan_for_product(product_id, target_plan)
    if (
        settlement.get("subscriber_ref") != subscriber
        or settlement.get("strategy_product_id") != product_id
        or settlement.get("plan_id") != target_plan
    ):
        raise SubscriptionRegistryError(
            "Settlement attribution does not match payment intent"
        )
    if target_plan_row.get("requires_payment") is not True:
        raise SubscriptionRegistryError("Paid activation requires a paid plan")

    start, end = _validate_period(period_start_ts, period_end_ts)
    effective = _now(effective_at_ts)
    if effective < start:
        raise SubscriptionRegistryError(
            "Activation cannot occur before the paid period starts"
        )
    target_tier = str(target_plan_row.get("tier") or "")
    if target_tier not in _TIER_RANK:
        raise SubscriptionRegistryError(f"Unsupported target tier: {target_tier}")
    target_path = path or events_path()
    idem = f"payment-activation:{settlement['ledger_event_id']}"

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target_path)
        existing_idem = _find_idempotency(records, idem)
        if existing_idem is not None:
            return {
                "status": "DUPLICATE",
                "appended": False,
                "record": dict(existing_idem),
            }
        current = _latest_for_pair(records, subscriber, product_id)
        if (
            current is not None
            and subscription_id is not None
            and current.get("subscription_id") != subscription_id
        ):
            raise SubscriptionRegistryError(
                "subscription_id conflicts with existing subscriber/product subscription"
            )

        transition = EVENT_ACTIVATED
        reason = "VERIFIED_PAYMENT_ACTIVATION"
        proration = None
        previous: Optional[Mapping[str, Any]]

        if current is None:
            previous = None
            base = _base_free_snapshot(
                subscriber_ref=subscriber,
                strategy_product_id=product_id,
                subscription_id=subscription_id,
                entitlement_id=_opaque_id(),
                starts_at_epoch=effective,
            )
        else:
            previous = current
            base = _snapshot(current)
            current_tier = str(current["tier"])
            current_rank = _TIER_RANK[current_tier]
            target_rank = _TIER_RANK[target_tier]
            state = str(current["state"])
            if state in {"CHARGEBACK_OPEN", "REFUND_HOLD"}:
                raise SubscriptionRegistryError(
                    "Payment hold must be resolved before a new paid activation"
                )

            current_expires = current.get("expires_at_epoch")
            active_paid_period = (
                current_tier != "FREE"
                and state != "EXPIRED"
                and current_expires is not None
                and effective < int(current_expires)
            )

            if active_paid_period:
                if target_rank > current_rank:
                    if (
                        start != int(current.get("starts_at_epoch"))
                        or end != int(current_expires)
                    ):
                        raise SubscriptionRegistryError(
                            "Mid-period upgrade must preserve current period boundaries"
                        )
                    proration = _validate_upgrade_proration(
                        current=current,
                        target_plan_id=target_plan,
                        settlement=settlement,
                        effective_at=effective,
                        evidence=proration_evidence,
                    )
                    transition = EVENT_UPGRADED
                    reason = "VERIFIED_PAYMENT_PRORATED_UPGRADE"
                elif target_rank == current_rank:
                    raise SubscriptionRegistryError(
                        "Same-plan renewal cannot become effective before current period end"
                    )
                else:
                    raise SubscriptionRegistryError(
                        "Downgrade cannot become effective before current billing period end"
                    )
            elif current_tier == "FREE":
                transition = EVENT_ACTIVATED
                reason = "VERIFIED_PAYMENT_ACTIVATION_FROM_FREE"
            else:
                if current_expires is not None and start < int(current_expires):
                    raise SubscriptionRegistryError(
                        "New paid period overlaps the previous paid period"
                    )
                if target_rank == current_rank:
                    transition = EVENT_RENEWED
                    reason = "VERIFIED_PAYMENT_RENEWAL"
                elif target_rank < current_rank:
                    if current.get("scheduled_plan_id") == target_plan:
                        transition = EVENT_DOWNGRADE_EFFECTIVE
                        reason = "VERIFIED_PAYMENT_SCHEDULED_DOWNGRADE"
                    else:
                        transition = EVENT_ACTIVATED
                        reason = "VERIFIED_PAYMENT_POST_EXPIRY_LOWER_TIER_ACTIVATION"
                else:
                    transition = EVENT_ACTIVATED
                    reason = "VERIFIED_PAYMENT_NEW_PERIOD_UPGRADE"

        changes = dict(base)
        changes.update(
            {
                "subscription_id": (
                    base.get("subscription_id")
                    or subscription_id
                    or _opaque_id()
                ),
                "entitlement_id": base.get("entitlement_id") or _opaque_id(),
                "plan_id": target_plan,
                "tier": target_tier,
                "state": "ACTIVE",
                "starts_at_epoch": start,
                "expires_at_epoch": end,
                "grace_until_epoch": end + GRACE_HOLD_SECONDS,
                "auto_downgrade_at_epoch": end + AUTO_DOWNGRADE_SECONDS,
                "scheduled_plan_id": None,
                "pending_plan_id": None,
                "pending_payment_intent_id": None,
                "intent_pending_until_epoch": None,
                "resume_state_after_intent": None,
                "last_payment_intent_id": intent_id,
                "last_payment_ledger_event_id": settlement["ledger_event_id"],
                "proration_evidence": proration,
                "last_downgrade_evidence_id": None,
            }
        )
        record, appended = _append_event_unlocked(
            path=target_path,
            records=records,
            previous=previous,
            changes=changes,
            event_type=transition,
            idempotency_key=idem,
            occurred_at_epoch=effective,
            reason=reason,
            audit_correlation_id=(
                audit_correlation_id
                or str(settlement.get("audit_correlation_id") or _opaque_id())
            ),
        )
        return {"status": transition, "appended": appended, "record": record}


def record_payment_intent_pending(
    *,
    payment_intent_id: str,
    now_ts: float | int | None = None,
    audit_correlation_id: str | None = None,
    path: str | None = None,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    intent_id = _nonempty(payment_intent_id, label="payment_intent_id")
    intent = _payment_intent_creation(intent_id, payment_path)
    try:
        settled = payment_ledger.settled_payment_record(intent_id, payment_path)
    except payment_ledger.PaymentLedgerError as exc:
        raise SubscriptionRegistryError(str(exc)) from exc
    if settled is not None:
        raise SubscriptionRegistryError(
            "Settled payment cannot enter INTENT_PAYMENT_PENDING"
        )
    subscriber = _nonempty(intent.get("subscriber_ref"), label="subscriber_ref")
    product_id = _nonempty(
        intent.get("strategy_product_id"), label="strategy_product_id"
    )
    pending_plan = _nonempty(intent.get("plan_id"), label="plan_id")
    if not _is_paid_product_plan(product_id, pending_plan):
        raise SubscriptionRegistryError(
            "INTENT_PAYMENT_PENDING requires a paid target plan"
        )
    now = _now(now_ts)
    target = path or events_path()
    idem = f"intent-pending:{intent_id}"

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {
                "status": "DUPLICATE",
                "appended": False,
                "record": dict(existing),
            }
        current = _latest_for_pair(records, subscriber, product_id)
        if current is None:
            base = _base_free_snapshot(
                subscriber_ref=subscriber,
                strategy_product_id=product_id,
                starts_at_epoch=now,
            )
            previous: Optional[Mapping[str, Any]] = None
            resume_state = "ACTIVE"
        else:
            if current.get("state") in {"CHARGEBACK_OPEN", "REFUND_HOLD"}:
                raise SubscriptionRegistryError(
                    "Payment intent cannot bypass an unresolved payment hold"
                )
            base = _snapshot(current)
            previous = current
            resume_state = str(current.get("state") or "ACTIVE")
        changes = dict(base)
        changes.update(
            {
                "state": "INTENT_PAYMENT_PENDING",
                "pending_plan_id": pending_plan,
                "pending_payment_intent_id": intent_id,
                "intent_pending_until_epoch": now + INTENT_PAYMENT_PENDING_SECONDS,
                "resume_state_after_intent": resume_state,
            }
        )
        record, appended = _append_event_unlocked(
            path=target,
            records=records,
            previous=previous,
            changes=changes,
            event_type=EVENT_INTENT_PENDING,
            idempotency_key=idem,
            occurred_at_epoch=now,
            reason="RECORDED_PAID_PLAN_PAYMENT_INTENT",
            audit_correlation_id=audit_correlation_id or _opaque_id(),
        )
        return {
            "status": "INTENT_PAYMENT_PENDING",
            "appended": appended,
            "record": record,
        }


def request_downgrade(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    target_plan_id: str,
    now_ts: float | int | None = None,
    audit_correlation_id: str | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    target_plan = _nonempty(target_plan_id, label="target_plan_id")
    target_tier = _tier_for_product_plan(product, target_plan)
    now = _now(now_ts)
    target = path or events_path()

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_for_pair(records, subscriber, product)
        if current is None or current.get("tier") == "FREE":
            raise SubscriptionRegistryError(
                "Downgrade requires an existing paid subscription"
            )
        if current.get("state") in {
            "EXPIRED",
            "CHARGEBACK_OPEN",
            "REFUND_HOLD",
        }:
            raise SubscriptionRegistryError(
                "Downgrade cannot be scheduled from the current state"
            )
        if _TIER_RANK[target_tier] >= _TIER_RANK[str(current["tier"])]:
            raise SubscriptionRegistryError("target_plan_id is not a lower tier")
        expires = current.get("expires_at_epoch")
        if expires is None or now >= int(expires):
            raise SubscriptionRegistryError(
                "Downgrade must be scheduled before period expiry"
            )
        idem = (
            f"downgrade:{current['subscription_id']}:{target_plan}:{expires}"
        )
        record, appended = _append_event_unlocked(
            path=target,
            records=records,
            previous=current,
            changes={"scheduled_plan_id": target_plan},
            event_type=EVENT_DOWNGRADE_SCHEDULED,
            idempotency_key=idem,
            occurred_at_epoch=now,
            reason="DOWNGRADE_EFFECTIVE_NEXT_BILLING_PERIOD",
            audit_correlation_id=audit_correlation_id or _opaque_id(),
        )
        return {
            "status": "DOWNGRADE_SCHEDULED",
            "appended": appended,
            "record": record,
        }


def cancel_at_period_end(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    now_ts: float | int | None = None,
    audit_correlation_id: str | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    now = _now(now_ts)
    target = path or events_path()

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_for_pair(records, subscriber, product)
        if current is None or current.get("tier") == "FREE":
            raise SubscriptionRegistryError(
                "Cancellation requires an existing paid subscription"
            )
        expires = current.get("expires_at_epoch")
        if expires is None or now >= int(expires):
            raise SubscriptionRegistryError(
                "Cancellation-at-period-end must be scheduled before expiry"
            )
        free_plan = _free_plan_id(product)
        idem = f"cancel-period-end:{current['subscription_id']}:{expires}"
        record, appended = _append_event_unlocked(
            path=target,
            records=records,
            previous=current,
            changes={
                "state": "CANCELED_AT_PERIOD_END",
                "scheduled_plan_id": free_plan,
            },
            event_type=EVENT_CANCELED,
            idempotency_key=idem,
            occurred_at_epoch=now,
            reason="CANCELED_AT_PERIOD_END",
            audit_correlation_id=audit_correlation_id or _opaque_id(),
        )
        return {
            "status": "CANCELED_AT_PERIOD_END",
            "appended": appended,
            "record": record,
        }


def record_payment_status(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    state: str,
    payment_intent_id: str | None = None,
    reason: str,
    now_ts: float | int | None = None,
    audit_correlation_id: str | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    if state not in {"PAYMENT_DUE", "PAYMENT_FAILED"}:
        raise SubscriptionRegistryError(
            "record_payment_status supports PAYMENT_DUE/PAYMENT_FAILED only"
        )
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    why = _nonempty(reason, label="reason")
    now = _now(now_ts)
    target = path or events_path()
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_for_pair(records, subscriber, product)
        if current is None or current.get("tier") == "FREE":
            raise SubscriptionRegistryError(
                "Payment state requires an existing paid subscription"
            )
        idem = (
            f"payment-state:{current['subscription_id']}:{state}:"
            f"{payment_intent_id or 'none'}:{why}"
        )
        record, appended = _append_event_unlocked(
            path=target,
            records=records,
            previous=current,
            changes={"state": state},
            event_type=(
                EVENT_PAYMENT_DUE if state == "PAYMENT_DUE" else EVENT_PAYMENT_FAILED
            ),
            idempotency_key=idem,
            occurred_at_epoch=now,
            reason=why,
            audit_correlation_id=audit_correlation_id or _opaque_id(),
        )
        return {"status": state, "appended": appended, "record": record}


def apply_payment_reversal(
    *,
    payment_intent_id: str,
    now_ts: float | int | None = None,
    audit_correlation_id: str | None = None,
    path: str | None = None,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    intent_id = _nonempty(payment_intent_id, label="payment_intent_id")
    try:
        history = payment_ledger.payment_history(intent_id, payment_path)
    except payment_ledger.PaymentLedgerError as exc:
        raise SubscriptionRegistryError(str(exc)) from exc
    intent = _payment_intent_creation(intent_id, payment_path)
    reversals = [
        record
        for record in history
        if record.get("event_type") == payment_ledger.EVENT_REVERSAL
        and record.get("reconciliation_result") == "MATCHED"
        and record.get("payment_state") in {"REFUNDED", "CHARGEBACK"}
    ]
    if len(reversals) != 1:
        raise SubscriptionRegistryError(
            "Payment reversal must have exactly one matched ledger reversal record"
        )
    reversal = reversals[0]
    subscriber = _nonempty(intent.get("subscriber_ref"), label="subscriber_ref")
    product = _nonempty(
        intent.get("strategy_product_id"), label="strategy_product_id"
    )
    now = _now(now_ts)
    target = path or events_path()

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_for_pair(records, subscriber, product)
        if current is None or current.get("tier") == "FREE":
            raise SubscriptionRegistryError(
                "Payment reversal has no current paid subscription"
            )
        if current.get("last_payment_intent_id") != intent_id:
            raise SubscriptionRegistryError(
                "Reversal does not target the payment currently backing subscription"
            )
        reversal_state = str(reversal["payment_state"])
        state = (
            "CHARGEBACK_OPEN"
            if reversal_state == "CHARGEBACK"
            else "REFUND_HOLD"
        )
        event_type = (
            EVENT_CHARGEBACK_HOLD
            if reversal_state == "CHARGEBACK"
            else EVENT_REFUND_HOLD
        )
        idem = f"payment-reversal:{reversal['ledger_event_id']}"
        record, appended = _append_event_unlocked(
            path=target,
            records=records,
            previous=current,
            changes={"state": state},
            event_type=event_type,
            idempotency_key=idem,
            occurred_at_epoch=now,
            reason=f"MATCHED_PAYMENT_{reversal_state}",
            audit_correlation_id=(
                audit_correlation_id
                or str(reversal.get("audit_correlation_id") or _opaque_id())
            ),
        )
        return {"status": state, "appended": appended, "record": record}


def _append_deadline_event(
    *,
    target: str,
    records: list[Dict[str, Any]],
    current: Mapping[str, Any],
    state: str,
    event_type: str,
    occurred_at: int,
    reason: str,
    idempotency_suffix: str,
    changes: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    delta = {"state": state}
    if changes:
        delta.update(dict(changes))
    idem = f"deadline:{current['subscription_id']}:{idempotency_suffix}"
    record, _ = _append_event_unlocked(
        path=target,
        records=records,
        previous=current,
        changes=delta,
        event_type=event_type,
        idempotency_key=idem,
        occurred_at_epoch=occurred_at,
        reason=reason,
        audit_correlation_id=_opaque_id(),
    )
    return record


def evaluate_deadlines(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    now_ts: float | int | None = None,
    downgrade_evidence_id: str | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    """Persist deterministic lifecycle deadlines without inventing policy proof.

    The +72h boundary is necessary but not sufficient for automatic FREE
    downgrade. Issue #163 owns mandatory notification/delivery evidence. Until
    that lane supplies a non-empty ``downgrade_evidence_id``, the paid plan
    remains PAYMENT_DUE/PAYMENT_FAILED with paid access SUSPENDED.
    """

    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    _product(product)
    now = _now(now_ts)
    evidence_id = _optional_text(downgrade_evidence_id)
    target = path or events_path()
    appended_events: list[Dict[str, Any]] = []

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_for_pair(records, subscriber, product)
        if current is None:
            return {
                "status": "NO_SUBSCRIPTION",
                "appended": False,
                "events": [],
            }

        for _ in range(10):
            state = str(current["state"])
            tier = str(current["tier"])
            expires = current.get("expires_at_epoch")
            grace_until = current.get("grace_until_epoch")
            auto_at = current.get("auto_downgrade_at_epoch")
            occurred = int(current.get("occurred_at_epoch") or 0)

            # Pending intent is processed first, including FREE subscribers.
            if state == "INTENT_PAYMENT_PENDING":
                pending_until = current.get("intent_pending_until_epoch")
                if pending_until is None or now < int(pending_until):
                    break
                resume = str(current.get("resume_state_after_intent") or "ACTIVE")
                next_state = resume if resume in SUBSCRIPTION_STATES else "ACTIVE"

                if tier == "FREE":
                    next_state = "ACTIVE"
                elif resume == "EXPIRED":
                    next_state = "EXPIRED"
                elif resume == "CANCELED_AT_PERIOD_END":
                    next_state = "CANCELED_AT_PERIOD_END"
                elif expires is not None and int(pending_until) >= int(expires):
                    if grace_until is not None and int(pending_until) >= int(grace_until):
                        next_state = "PAYMENT_DUE"
                    else:
                        next_state = "GRACE_HOLD"

                current = _append_deadline_event(
                    target=target,
                    records=records + appended_events,
                    current=current,
                    state=next_state,
                    event_type=EVENT_INTENT_EXPIRED,
                    occurred_at=int(pending_until),
                    reason="INTENT_PAYMENT_PENDING_MAX_24H_EXPIRED",
                    idempotency_suffix=(
                        "intent-expired:"
                        f"{current.get('pending_payment_intent_id')}:{pending_until}"
                    ),
                    changes={
                        "pending_plan_id": None,
                        "pending_payment_intent_id": None,
                        "intent_pending_until_epoch": None,
                        "resume_state_after_intent": None,
                    },
                )
                appended_events.append(current)
                continue

            if tier == "FREE" or state in {
                "EXPIRED",
                "CHARGEBACK_OPEN",
                "REFUND_HOLD",
            }:
                break

            if expires is None:
                raise SubscriptionRegistryError(
                    "Paid subscription is missing expires_at_epoch"
                )
            expires_int = int(expires)

            # Explicit cancellation/downgrade-to-FREE is user intent, not the
            # no-response auto-downgrade policy and therefore needs no #163 proof.
            if state == "CANCELED_AT_PERIOD_END" and now >= expires_int:
                current = _append_deadline_event(
                    target=target,
                    records=records + appended_events,
                    current=current,
                    state="EXPIRED",
                    event_type=EVENT_AUTO_DOWNGRADED,
                    occurred_at=expires_int,
                    reason="CANCELLATION_EFFECTIVE_AT_PERIOD_END",
                    idempotency_suffix=f"canceled-expired:{expires_int}",
                    changes={
                        "scheduled_plan_id": None,
                        "last_downgrade_evidence_id": None,
                    },
                )
                appended_events.append(current)
                continue

            scheduled = current.get("scheduled_plan_id")
            if scheduled == _free_plan_id(product) and now >= expires_int:
                current = _append_deadline_event(
                    target=target,
                    records=records + appended_events,
                    current=current,
                    state="EXPIRED",
                    event_type=EVENT_AUTO_DOWNGRADED,
                    occurred_at=expires_int,
                    reason="SCHEDULED_DOWNGRADE_TO_FREE_EFFECTIVE",
                    idempotency_suffix=f"scheduled-free:{expires_int}",
                    changes={
                        "scheduled_plan_id": None,
                        "last_downgrade_evidence_id": None,
                    },
                )
                appended_events.append(current)
                continue

            if (
                state in {"ACTIVE", "PAYMENT_DUE", "PAYMENT_FAILED"}
                and occurred < expires_int
                and now >= expires_int
            ):
                current = _append_deadline_event(
                    target=target,
                    records=records + appended_events,
                    current=current,
                    state="GRACE_HOLD",
                    event_type=EVENT_GRACE_STARTED,
                    occurred_at=expires_int,
                    reason="PAID_PERIOD_EXPIRED_GRACE_HOLD_48H",
                    idempotency_suffix=f"grace:{expires_int}",
                )
                appended_events.append(current)
                continue

            if (
                state == "GRACE_HOLD"
                and grace_until is not None
                and now >= int(grace_until)
            ):
                current = _append_deadline_event(
                    target=target,
                    records=records + appended_events,
                    current=current,
                    state="PAYMENT_DUE",
                    event_type=EVENT_PAYMENT_DUE,
                    occurred_at=int(grace_until),
                    reason="GRACE_HOLD_48H_COMPLETED_NO_SETTLED_PAYMENT",
                    idempotency_suffix=f"grace-ended:{grace_until}",
                )
                appended_events.append(current)
                continue

            if (
                state in {"PAYMENT_DUE", "PAYMENT_FAILED"}
                and auto_at is not None
                and now >= int(auto_at)
            ):
                if evidence_id is None:
                    break
                current = _append_deadline_event(
                    target=target,
                    records=records + appended_events,
                    current=current,
                    state="EXPIRED",
                    event_type=EVENT_AUTO_DOWNGRADED,
                    occurred_at=int(auto_at),
                    reason=(
                        "NO_SETTLED_PAYMENT_OR_ACTIVE_INTENT_AT_PLUS_72H_"
                        "WITH_NOTIFICATION_POLICY_EVIDENCE"
                    ),
                    idempotency_suffix=f"auto-free:{auto_at}:{evidence_id}",
                    changes={
                        "scheduled_plan_id": None,
                        "last_downgrade_evidence_id": evidence_id,
                    },
                )
                appended_events.append(current)
                continue
            break

    return {
        "status": str(current["state"]),
        "appended": bool(appended_events),
        "events": appended_events,
        "record": dict(current),
        "downgrade_blocked_pending_evidence": bool(
            current.get("tier") != "FREE"
            and current.get("state") in {"PAYMENT_DUE", "PAYMENT_FAILED"}
            and current.get("auto_downgrade_at_epoch") is not None
            and now >= int(current["auto_downgrade_at_epoch"])
            and evidence_id is None
        ),
    }


def _time_aware_access(
    record: Mapping[str, Any], now: int
) -> tuple[str, str, str, str]:
    product = str(record["strategy_product_id"])
    free_plan = _free_plan_id(product)
    tier = str(record["tier"])
    plan_id = str(record["plan_id"])
    state = str(record["state"])

    if state in {"CHARGEBACK_OPEN", "REFUND_HOLD"}:
        return plan_id, tier, "HOLD", "PAYMENT_REVERSAL_HOLD"
    if state == "EXPIRED":
        return free_plan, "FREE", "FREE_FALLBACK", "SUBSCRIPTION_EXPIRED"

    expires = record.get("expires_at_epoch")
    if state == "CANCELED_AT_PERIOD_END" and expires is not None and now >= int(expires):
        return (
            free_plan,
            "FREE",
            "FREE_FALLBACK",
            "CANCELLATION_PERIOD_ENDED",
        )

    if state == "INTENT_PAYMENT_PENDING":
        resume = str(record.get("resume_state_after_intent") or "ACTIVE")
        if tier == "FREE":
            return free_plan, "FREE", "ACTIVE", "FREE_WITH_PAYMENT_INTENT_PENDING"
        if resume == "EXPIRED":
            return (
                free_plan,
                "FREE",
                "FREE_FALLBACK",
                "EXPIRED_WITH_NEW_PAYMENT_INTENT_PENDING",
            )
        if expires is not None and now >= int(expires):
            return (
                plan_id,
                tier,
                "SUSPENDED",
                "PAID_EXPIRED_WITH_PAYMENT_INTENT_PENDING",
            )
        return plan_id, tier, "ACTIVE", "PAID_ACTIVE_WITH_PAYMENT_INTENT_PENDING"

    if tier == "FREE":
        return free_plan, "FREE", "ACTIVE", "FREE_ENTITLEMENT"
    if expires is not None and now >= int(expires):
        return plan_id, tier, "SUSPENDED", "PAID_PERIOD_EXPIRED"
    return plan_id, tier, "ACTIVE", "PAID_PERIOD_ACTIVE"


def resolve_entitlement(
    *,
    subscriber_ref: str,
    strategy_product_id: str = "BINARY_TRADING",
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    _product(product)
    now = _now(now_ts)
    current = current_subscription(subscriber, product, path)
    if current is None:
        free_plan = _free_plan_id(product)
        return {
            "entitlement_id": _stable_free_entitlement_id(subscriber, product),
            "entitlement_version": 0,
            "subscriber_ref": subscriber,
            "strategy_product_id": product,
            "subscription_id": None,
            "subscription_state": "NO_SUBSCRIPTION",
            "plan_id": free_plan,
            "tier": "FREE",
            "access_state": "FREE_FALLBACK",
            "source_subscription_event_id": None,
            "reason": "NO_SUBSCRIPTION_FREE_BASELINE",
        }

    plan_id, tier, access, reason = _time_aware_access(current, now)
    if access not in ENTITLEMENT_ACCESS_STATES:
        raise SubscriptionRegistryError(
            f"Unsupported entitlement access state: {access}"
        )
    auto_at = current.get("auto_downgrade_at_epoch")
    if (
        tier != "FREE"
        and access == "SUSPENDED"
        and current.get("state") in {"PAYMENT_DUE", "PAYMENT_FAILED"}
        and auto_at is not None
        and now >= int(auto_at)
    ):
        reason = "AUTO_DOWNGRADE_BLOCKED_PENDING_NOTIFICATION_EVIDENCE"

    return {
        "entitlement_id": current["entitlement_id"],
        "entitlement_version": current["entitlement_version"],
        "subscriber_ref": subscriber,
        "strategy_product_id": product,
        "subscription_id": current["subscription_id"],
        "subscription_state": current["state"],
        "plan_id": plan_id,
        "tier": tier,
        "access_state": access,
        "source_subscription_event_id": current["subscription_event_id"],
        "expires_at_epoch": current.get("expires_at_epoch"),
        "grace_until_epoch": current.get("grace_until_epoch"),
        "auto_downgrade_at_epoch": auto_at,
        "pending_payment_intent_id": current.get("pending_payment_intent_id"),
        "pending_plan_id": current.get("pending_plan_id"),
        "scheduled_plan_id": current.get("scheduled_plan_id"),
        "last_downgrade_evidence_id": current.get("last_downgrade_evidence_id"),
        "reason": reason,
    }
