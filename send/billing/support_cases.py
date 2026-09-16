from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from billing import notification_scheduler, payment_ledger
from core import admin_permissions, storage, telegram_publisher

CASE_STATES = frozenset(
    {
        "OPEN",
        "WAITING_FOR_CLIENT",
        "UNDER_REVIEW",
        "HOLD_ESCALATION",
        "VERIFIED",
        "REJECTED",
        "RESOLVED",
    }
)
REVIEW_ACTIONS = frozenset(
    {"REQUEST_MORE_INFO", "VERIFY", "REJECT", "ESCALATE", "RESOLVE"}
)
CLOSED_STATES = frozenset({"VERIFIED", "REJECTED", "RESOLVED"})

EVENT_CASE_OPENED = "BILLING_SUPPORT_CASE_OPENED"
EVENT_CLIENT_MESSAGE = "BILLING_SUPPORT_CLIENT_MESSAGE"
EVENT_ADMIN_MESSAGE = "BILLING_SUPPORT_ADMIN_MESSAGE"
EVENT_MESSAGE_DELIVERY = "BILLING_SUPPORT_MESSAGE_DELIVERY"
EVENT_PAYMENT_PROOF = "BILLING_SUPPORT_PAYMENT_PROOF"
EVENT_REVIEW = "BILLING_SUPPORT_REVIEW"
EVENT_CASE_REOPENED = "BILLING_SUPPORT_CASE_REOPENED"

PAYMENT_EVENT_MANUAL_VERIFICATION = "PAYMENT_MANUAL_VERIFICATION_EVIDENCE"
PAYMENT_EVENT_MANUAL_REVIEW_AUDIT = "PAYMENT_MANUAL_REVIEW_AUDIT"

_LOCK_NAME = "billing_support_cases"
_PAYMENT_LOCK_NAME = "billing_payment_ledger"
_EVENTS_RELATIVE = ("billing", "support_case_events.jsonl")


class BillingSupportError(RuntimeError):
    """Raised when support-case evidence is missing, unsafe or contradictory."""


def cases_path() -> str:
    return storage.root_path(*_EVENTS_RELATIVE)


def _now(value: float | int | None = None) -> int:
    return int(time.time() if value is None else value)


def _utc_iso(value: float | int | None = None) -> str:
    ts = float(time.time() if value is None else value)
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def _opaque_id() -> str:
    return str(uuid.uuid4())


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BillingSupportError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    return _nonempty(value, label="optional string")


def _positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise BillingSupportError(f"{label} must be a positive integer")
    try:
        result = int(value)
    except Exception as exc:
        raise BillingSupportError(f"{label} must be a positive integer") from exc
    if result <= 0:
        raise BillingSupportError(f"{label} must be a positive integer")
    return result


def _reason(value: Any) -> str:
    text = _nonempty(value, label="reason")
    if len(text) < 4:
        raise BillingSupportError("reason must contain meaningful review context")
    return text


def _sha256_hex(value: str) -> str:
    text = _nonempty(value, label="sha256").lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise BillingSupportError("sha256 must be a 64-character hexadecimal digest")
    return text


def _read_events_unlocked(path: str) -> list[Dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise BillingSupportError(f"Unable to read support-case event log: {target}") from exc

    records: list[Dict[str, Any]] = []
    global_seq: set[int] = set()
    event_ids: set[str] = set()
    versions: Dict[str, int] = {}
    previous_ids: Dict[str, str] = {}

    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BillingSupportError(
                f"Support-case JSON corruption at line {line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise BillingSupportError(
                f"Support-case record at line {line_number} is not an object"
            )
        event_id = _nonempty(record.get("case_event_id"), label="case_event_id")
        if event_id in event_ids:
            raise BillingSupportError(f"Duplicate case_event_id: {event_id}")
        event_ids.add(event_id)
        seq = record.get("case_seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise BillingSupportError(f"Invalid case_seq at line {line_number}")
        if seq in global_seq:
            raise BillingSupportError(f"Duplicate case_seq: {seq}")
        global_seq.add(seq)

        case_id = _nonempty(record.get("case_id"), label="case_id")
        version = record.get("case_version")
        if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
            raise BillingSupportError(f"Invalid case_version at line {line_number}")
        expected_version = versions.get(case_id, 0) + 1
        if version != expected_version:
            raise BillingSupportError(
                f"Non-contiguous case_version for {case_id}: "
                f"expected={expected_version} actual={version}"
            )
        versions[case_id] = version
        expected_previous = previous_ids.get(case_id)
        if record.get("previous_case_event_id") != expected_previous:
            raise BillingSupportError(
                f"Broken support-case event chain for {case_id} at line {line_number}"
            )
        previous_ids[case_id] = event_id
        if record.get("case_state") not in CASE_STATES:
            raise BillingSupportError(
                f"Unsupported case_state at line {line_number}: {record.get('case_state')}"
            )
        records.append(record)

    if records:
        actual = [int(row["case_seq"]) for row in records]
        expected = list(range(1, len(records) + 1))
        if actual != expected:
            raise BillingSupportError(
                f"Support-case sequence is non-contiguous: expected={expected} actual={actual}"
            )
    return records


def load_case_events(path: str | None = None) -> list[Dict[str, Any]]:
    return _read_events_unlocked(path or cases_path())


def _latest_by_case(records: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for record in records:
        latest[str(record["case_id"])] = dict(record)
    return latest


def current_case(case_id: str, path: str | None = None) -> Optional[Dict[str, Any]]:
    target_id = _nonempty(case_id, label="case_id")
    return _latest_by_case(load_case_events(path)).get(target_id)


def case_history(case_id: str, path: str | None = None) -> list[Dict[str, Any]]:
    target_id = _nonempty(case_id, label="case_id")
    return [
        dict(row)
        for row in load_case_events(path)
        if row.get("case_id") == target_id
    ]


def _find_idempotency(
    records: Iterable[Mapping[str, Any]], key: str
) -> Optional[Mapping[str, Any]]:
    for record in records:
        if record.get("idempotency_key") == key:
            return record
    return None


def _append_case_event_unlocked(
    *,
    path: str,
    records: list[Dict[str, Any]],
    previous: Optional[Mapping[str, Any]],
    case_id: str,
    event_type: str,
    case_state: str,
    idempotency_key: str,
    occurred_at_epoch: int,
    payload: Mapping[str, Any],
) -> tuple[Dict[str, Any], bool]:
    if case_state not in CASE_STATES:
        raise BillingSupportError(f"Unsupported case_state: {case_state}")
    existing = _find_idempotency(records, idempotency_key)
    if existing is not None:
        if existing.get("case_id") != case_id or existing.get("event_type") != event_type:
            raise BillingSupportError(
                "Support idempotency key was reused for a different case event"
            )
        return dict(existing), False

    record = dict(payload)
    record.update(
        {
            "case_event_id": _opaque_id(),
            "case_seq": len(records) + 1,
            "case_id": case_id,
            "case_version": int(previous.get("case_version") or 0) + 1 if previous else 1,
            "previous_case_event_id": previous.get("case_event_id") if previous else None,
            "event_type": event_type,
            "case_state": case_state,
            "occurred_at_epoch": occurred_at_epoch,
            "idempotency_key": idempotency_key,
        }
    )
    storage.append_jsonl(path, record)
    return record, True


def _notification_intent(client_intent_id: str, notification_path: str | None) -> Dict[str, Any]:
    intent_id = _nonempty(client_intent_id, label="client_intent_id")
    matches = [
        row
        for row in notification_scheduler.load_events(notification_path)
        if row.get("client_intent_id") == intent_id
        and row.get("event_type")
        in {
            notification_scheduler.EVENT_CLIENT_INTENT,
            notification_scheduler.EVENT_CLIENT_INTENT_HANDOFF,
        }
    ]
    if not matches:
        raise BillingSupportError(f"Unknown client_intent_id: {intent_id}")
    return dict(matches[-1])


def open_case_from_client_intent(
    *,
    client_intent_id: str,
    now_ts: float | int | None = None,
    path: str | None = None,
    notification_path: str | None = None,
) -> Dict[str, Any]:
    intent = _notification_intent(client_intent_id, notification_path)
    action = str(intent.get("client_action") or "")
    if action not in {"SUPPORT", "PAYMENT_NOT_DETECTED"}:
        return {"status": "NOT_SUPPORT_INTENT", "appended": False, "record": None}
    subscriber = _nonempty(intent.get("subscriber_ref"), label="subscriber_ref")
    product = _nonempty(intent.get("strategy_product_id"), label="strategy_product_id")
    now = _now(now_ts)
    target = path or cases_path()
    idem = f"case-from-client-intent:{client_intent_id}"

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {"status": "EXISTS", "appended": False, "record": dict(existing)}
        case_id = _opaque_id()
        state = "WAITING_FOR_CLIENT" if action == "PAYMENT_NOT_DETECTED" else "OPEN"
        record, appended = _append_case_event_unlocked(
            path=target,
            records=records,
            previous=None,
            case_id=case_id,
            event_type=EVENT_CASE_OPENED,
            case_state=state,
            idempotency_key=idem,
            occurred_at_epoch=now,
            payload={
                "subscriber_ref": subscriber,
                "strategy_product_id": product,
                "subscription_id": intent.get("subscription_id"),
                "client_intent_id": client_intent_id,
                "origin_action": action,
                "payment_intent_id": intent.get("payment_intent_id"),
                "reopened_from_case_id": None,
                "audit_correlation_id": intent.get("audit_correlation_id") or _opaque_id(),
            },
        )
        return {"status": "OPENED", "appended": appended, "record": record}


def open_case(
    *,
    subscriber_ref: str,
    strategy_product_id: str = "BINARY_TRADING",
    subscription_id: str | None = None,
    payment_intent_id: str | None = None,
    reason: str,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    why = _reason(reason)
    now = _now(now_ts)
    target = path or cases_path()
    case_id = _opaque_id()
    idem = f"open-case:{case_id}"
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        record, appended = _append_case_event_unlocked(
            path=target,
            records=records,
            previous=None,
            case_id=case_id,
            event_type=EVENT_CASE_OPENED,
            case_state="OPEN",
            idempotency_key=idem,
            occurred_at_epoch=now,
            payload={
                "subscriber_ref": subscriber,
                "strategy_product_id": product,
                "subscription_id": _optional_text(subscription_id),
                "client_intent_id": None,
                "origin_action": "DIRECT_SUPPORT",
                "payment_intent_id": _optional_text(payment_intent_id),
                "opening_reason": why,
                "reopened_from_case_id": None,
                "audit_correlation_id": _opaque_id(),
            },
        )
        return {"status": "OPENED", "appended": appended, "record": record}


def active_cases_for_subscriber(
    subscriber_ref: str,
    strategy_product_id: str = "BINARY_TRADING",
    path: str | None = None,
) -> list[Dict[str, Any]]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product = _nonempty(strategy_product_id, label="strategy_product_id")
    latest = _latest_by_case(load_case_events(path))
    return [
        row
        for row in latest.values()
        if row.get("subscriber_ref") == subscriber
        and row.get("strategy_product_id") == product
        and row.get("case_state") not in CLOSED_STATES
    ]


def _append_case_message(
    *,
    case_id: str,
    actor_type: str,
    actor_ref: str,
    text: str,
    now_ts: float | int | None,
    idempotency_key: str,
    path: str | None,
) -> Dict[str, Any]:
    message = _nonempty(text, label="message text")
    if len(message) > 4000:
        raise BillingSupportError("Support message exceeds 4000 characters")
    now = _now(now_ts)
    target = path or cases_path()
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_by_case(records).get(case_id)
        if current is None:
            raise BillingSupportError(f"Unknown case_id: {case_id}")
        if current.get("case_state") in CLOSED_STATES:
            raise BillingSupportError("Closed support case cannot accept new messages")
        next_state = "UNDER_REVIEW" if actor_type == "CLIENT" else str(current["case_state"])
        event_type = EVENT_CLIENT_MESSAGE if actor_type == "CLIENT" else EVENT_ADMIN_MESSAGE
        record, appended = _append_case_event_unlocked(
            path=target,
            records=records,
            previous=current,
            case_id=case_id,
            event_type=event_type,
            case_state=next_state,
            idempotency_key=idempotency_key,
            occurred_at_epoch=now,
            payload={
                **{
                    key: value
                    for key, value in current.items()
                    if key
                    not in {
                        "case_event_id",
                        "case_seq",
                        "case_version",
                        "previous_case_event_id",
                        "event_type",
                        "case_state",
                        "occurred_at_epoch",
                        "idempotency_key",
                    }
                },
                "message_id": _opaque_id(),
                "message_actor_type": actor_type,
                "message_actor_ref": actor_ref,
                "message_text": message,
                "message_sensitive": True,
            },
        )
        return {"status": "RECORDED", "appended": appended, "record": record}


def record_client_message(
    *,
    case_id: str,
    subscriber_ref: str,
    text: str,
    client_message_id: str,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    target_case = _nonempty(case_id, label="case_id")
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    current = current_case(target_case, path)
    if current is None or current.get("subscriber_ref") != subscriber:
        raise BillingSupportError("Client identity does not match support case")
    external_id = _nonempty(client_message_id, label="client_message_id")
    return _append_case_message(
        case_id=target_case,
        actor_type="CLIENT",
        actor_ref=subscriber,
        text=text,
        now_ts=now_ts,
        idempotency_key=f"client-message:{target_case}:{external_id}",
        path=path,
    )


def _require_reviewer(user_id: int) -> None:
    try:
        authorized = admin_permissions.is_primary_admin(int(user_id))
    except Exception:
        authorized = False
    if not authorized:
        raise BillingSupportError("Reviewer is not OWNER/PRIMARY_ADMIN")


def record_admin_reply(
    *,
    case_id: str,
    reviewer_user_id: int,
    text: str,
    admin_message_id: str,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    _require_reviewer(reviewer_user_id)
    reviewer = str(_positive_int(reviewer_user_id, label="reviewer_user_id"))
    external_id = _nonempty(admin_message_id, label="admin_message_id")
    return _append_case_message(
        case_id=_nonempty(case_id, label="case_id"),
        actor_type="ADMIN",
        actor_ref=reviewer,
        text=text,
        now_ts=now_ts,
        idempotency_key=f"admin-message:{case_id}:{external_id}",
        path=path,
    )


def _payment_intent_creation(payment_intent_id: str, payment_path: str | None) -> Dict[str, Any]:
    try:
        history = payment_ledger.payment_history(payment_intent_id, payment_path)
    except payment_ledger.PaymentLedgerError as exc:
        raise BillingSupportError(str(exc)) from exc
    matches = [
        row for row in history if row.get("event_type") == payment_ledger.EVENT_INTENT_CREATED
    ]
    if len(matches) != 1:
        raise BillingSupportError(
            f"Payment intent must have exactly one creation record: {payment_intent_id}"
        )
    return dict(matches[0])


def add_payment_proof(
    *,
    case_id: str,
    subscriber_ref: str,
    payment_intent_id: str,
    content_bytes: bytes,
    telegram_file_id: str,
    telegram_file_unique_id: str,
    file_name: str | None,
    mime_type: str | None,
    declared_amount_minor: int,
    declared_currency: str,
    file_size: int | None = None,
    caption: str | None = None,
    now_ts: float | int | None = None,
    path: str | None = None,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    case_key = _nonempty(case_id, label="case_id")
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    intent_id = _nonempty(payment_intent_id, label="payment_intent_id")
    if not isinstance(content_bytes, (bytes, bytearray)) or not content_bytes:
        raise BillingSupportError("Payment proof bytes are required to compute hash evidence")
    file_id = _nonempty(telegram_file_id, label="telegram_file_id")
    unique_id = _nonempty(telegram_file_unique_id, label="telegram_file_unique_id")
    amount = _positive_int(declared_amount_minor, label="declared_amount_minor")
    currency = _nonempty(declared_currency, label="declared_currency").upper()
    if len(currency) != 3 or not currency.isalpha():
        raise BillingSupportError("declared_currency must be a three-letter code")
    proof_hash = hashlib.sha256(bytes(content_bytes)).hexdigest()
    intent = _payment_intent_creation(intent_id, payment_path)
    if intent.get("subscriber_ref") != subscriber:
        raise BillingSupportError("Payment proof subscriber does not match payment intent")
    if amount != intent.get("amount_minor") or currency != intent.get("currency"):
        raise BillingSupportError(
            "Declared payment proof amount/currency does not match payment intent"
        )

    now = _now(now_ts)
    target = path or cases_path()
    idem = f"payment-proof:{case_key}:{proof_hash}"
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_by_case(records).get(case_key)
        if current is None:
            raise BillingSupportError(f"Unknown case_id: {case_key}")
        if current.get("subscriber_ref") != subscriber:
            raise BillingSupportError("Payment proof subscriber does not match support case")
        if current.get("case_state") in CLOSED_STATES:
            raise BillingSupportError("Closed support case cannot accept payment proof")
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {"status": "DUPLICATE", "appended": False, "record": dict(existing)}
        record, appended = _append_case_event_unlocked(
            path=target,
            records=records,
            previous=current,
            case_id=case_key,
            event_type=EVENT_PAYMENT_PROOF,
            case_state="UNDER_REVIEW",
            idempotency_key=idem,
            occurred_at_epoch=now,
            payload={
                **{
                    key: value
                    for key, value in current.items()
                    if key
                    not in {
                        "case_event_id",
                        "case_seq",
                        "case_version",
                        "previous_case_event_id",
                        "event_type",
                        "case_state",
                        "occurred_at_epoch",
                        "idempotency_key",
                    }
                },
                "payment_intent_id": intent_id,
                "proof_id": _opaque_id(),
                "proof_sha256": proof_hash,
                "proof_file_unique_id": unique_id,
                "restricted_telegram_file_id": file_id,
                "proof_file_name": _optional_text(file_name),
                "proof_mime_type": _optional_text(mime_type),
                "proof_file_size": int(file_size) if file_size is not None else len(content_bytes),
                "proof_declared_amount_minor": amount,
                "proof_declared_currency": currency,
                "proof_caption": _optional_text(caption),
                "proof_restricted": True,
            },
        )
        return {"status": "PROOF_RECORDED", "appended": appended, "record": record}


def _latest_proof(case_id: str, records: Iterable[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    proofs = [
        dict(row)
        for row in records
        if row.get("case_id") == case_id and row.get("event_type") == EVENT_PAYMENT_PROOF
    ]
    return proofs[-1] if proofs else None


def _contradictory_payment_evidence(payment_intent_id: str, payment_path: str | None) -> list[Dict[str, Any]]:
    return [
        dict(row)
        for row in payment_ledger.payment_history(payment_intent_id, payment_path)
        if row.get("reconciliation_result") == "CONTRADICTORY"
    ]


def _append_payment_record_unlocked(
    *,
    path: str,
    records: list[Dict[str, Any]],
    payload: Mapping[str, Any],
) -> Dict[str, Any]:
    record = dict(payload)
    record["ledger_event_id"] = _opaque_id()
    record["ledger_seq"] = len(records) + 1
    storage.append_jsonl(path, record)
    return record


def _manual_payment_verification_evidence(
    *,
    case: Mapping[str, Any],
    proof: Mapping[str, Any],
    reviewer_user_id: int,
    review_reason: str,
    now: int,
    payment_path: str | None,
) -> Dict[str, Any]:
    intent_id = _nonempty(proof.get("payment_intent_id"), label="payment_intent_id")
    intent = _payment_intent_creation(intent_id, payment_path)
    target = payment_path or payment_ledger.ledger_path()
    proof_hash = _sha256_hex(str(proof.get("proof_sha256") or ""))
    idem = f"manual-verification:{case['case_id']}:{intent_id}:{proof_hash}"

    with storage.with_lock(_PAYMENT_LOCK_NAME):
        records = payment_ledger.load_ledger(target)
        existing_idem = next(
            (row for row in records if row.get("idempotency_key") == idem), None
        )
        if existing_idem is not None:
            return {"status": "DUPLICATE", "record": dict(existing_idem)}

        contradictions = [
            row
            for row in records
            if row.get("payment_intent_id") == intent_id
            and row.get("reconciliation_result") == "CONTRADICTORY"
        ]
        if contradictions:
            raise BillingSupportError(
                "Contradictory provider/payment evidence requires HOLD_ESCALATION"
            )

        matched_settlements = [
            row
            for row in records
            if row.get("payment_intent_id") == intent_id
            and row.get("payment_state") == "SETTLED"
            and row.get("reconciliation_result") == "MATCHED"
        ]
        if len(matched_settlements) > 1:
            raise BillingSupportError(
                "Payment ledger contains multiple matched settlements"
            )

        common = {
            "payment_intent_id": intent_id,
            "provider": intent.get("provider"),
            "provider_event_id": None,
            "provider_tx_ref": None,
            "wallet_tx_id": None,
            "subscriber_ref": intent.get("subscriber_ref"),
            "strategy_product_id": intent.get("strategy_product_id"),
            "plan_id": intent.get("plan_id"),
            "amount_minor": intent.get("amount_minor"),
            "currency": intent.get("currency"),
            "payment_method": intent.get("payment_method"),
            "provider_state": "MANUAL_SUPPORT_REVIEW",
            "received_at": _utc_iso(now),
            "raw_event_hash": proof_hash,
            "idempotency_key": idem,
            "audit_correlation_id": case.get("audit_correlation_id") or _opaque_id(),
            "reversal_of_ledger_event_id": None,
            "case_id": case["case_id"],
            "reviewer_user_id": int(reviewer_user_id),
            "review_reason": review_reason,
            "evidence_source": "MANUAL_PAYMENT_PROOF_REVIEW",
        }

        if matched_settlements:
            existing = matched_settlements[0]
            record = _append_payment_record_unlocked(
                path=target,
                records=records,
                payload={
                    **common,
                    "event_type": PAYMENT_EVENT_MANUAL_REVIEW_AUDIT,
                    "payment_state": "UNKNOWN",
                    "settled_at": None,
                    "reconciliation_result": "DUPLICATE",
                    "existing_settlement_ledger_event_id": existing["ledger_event_id"],
                },
            )
            return {
                "status": "ALREADY_SETTLED_REVIEW_AUDITED",
                "record": record,
                "settlement_record": dict(existing),
            }

        record = _append_payment_record_unlocked(
            path=target,
            records=records,
            payload={
                **common,
                "event_type": PAYMENT_EVENT_MANUAL_VERIFICATION,
                "payment_state": "SETTLED",
                "settled_at": _utc_iso(now),
                "reconciliation_result": "MATCHED",
                "existing_settlement_ledger_event_id": None,
            },
        )
        return {
            "status": "MANUAL_SETTLEMENT_RECORDED",
            "record": record,
            "settlement_record": record,
        }


def review_case(
    *,
    case_id: str,
    reviewer_user_id: int,
    action: str,
    reason: str,
    now_ts: float | int | None = None,
    path: str | None = None,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    _require_reviewer(reviewer_user_id)
    case_key = _nonempty(case_id, label="case_id")
    normalized_action = _nonempty(action, label="action").upper()
    if normalized_action not in REVIEW_ACTIONS:
        raise BillingSupportError(f"Unsupported review action: {normalized_action}")
    why = _reason(reason)
    reviewer = _positive_int(reviewer_user_id, label="reviewer_user_id")
    now = _now(now_ts)
    target = path or cases_path()

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        current = _latest_by_case(records).get(case_key)
        if current is None:
            raise BillingSupportError(f"Unknown case_id: {case_key}")
        if current.get("case_state") == "RESOLVED":
            raise BillingSupportError("Resolved support case cannot be reviewed")
        idem = f"review:{case_key}:{current['case_version']}:{normalized_action}"
        existing = _find_idempotency(records, idem)
        if existing is not None:
            return {"status": "DUPLICATE", "appended": False, "record": dict(existing)}
        proof = _latest_proof(case_key, records)

    ledger_result: Dict[str, Any] | None = None
    state_by_action = {
        "REQUEST_MORE_INFO": "WAITING_FOR_CLIENT",
        "REJECT": "REJECTED",
        "ESCALATE": "HOLD_ESCALATION",
        "RESOLVE": "RESOLVED",
    }
    target_state = state_by_action.get(normalized_action)

    if normalized_action == "VERIFY":
        if proof is None:
            raise BillingSupportError("VERIFY requires payment proof evidence")
        intent_id = _nonempty(proof.get("payment_intent_id"), label="payment_intent_id")
        contradictions = _contradictory_payment_evidence(intent_id, payment_path)
        if contradictions:
            normalized_action = "ESCALATE"
            target_state = "HOLD_ESCALATION"
            why = f"{why}; contradictory provider evidence present"
        else:
            try:
                ledger_result = _manual_payment_verification_evidence(
                    case=current,
                    proof=proof,
                    reviewer_user_id=reviewer,
                    review_reason=why,
                    now=now,
                    payment_path=payment_path,
                )
            except BillingSupportError as exc:
                if "HOLD_ESCALATION" not in str(exc):
                    raise
                normalized_action = "ESCALATE"
                target_state = "HOLD_ESCALATION"
                why = f"{why}; {exc}"
            else:
                target_state = "VERIFIED"

    if normalized_action == "RESOLVE" and current.get("case_state") not in {
        "VERIFIED",
        "REJECTED",
        "HOLD_ESCALATION",
    }:
        raise BillingSupportError(
            "RESOLVE requires a reviewed VERIFIED/REJECTED/HOLD_ESCALATION case"
        )

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        latest = _latest_by_case(records).get(case_key)
        if latest is None:
            raise BillingSupportError(f"Unknown case_id: {case_key}")
        if latest.get("case_version") != current.get("case_version"):
            raise BillingSupportError(
                "Support case changed concurrently; reviewer must re-read before mutation"
            )
        idem = f"review:{case_key}:{latest['case_version']}:{normalized_action}"
        record, appended = _append_case_event_unlocked(
            path=target,
            records=records,
            previous=latest,
            case_id=case_key,
            event_type=EVENT_REVIEW,
            case_state=_nonempty(target_state, label="target_state"),
            idempotency_key=idem,
            occurred_at_epoch=now,
            payload={
                **{
                    key: value
                    for key, value in latest.items()
                    if key
                    not in {
                        "case_event_id",
                        "case_seq",
                        "case_version",
                        "previous_case_event_id",
                        "event_type",
                        "case_state",
                        "occurred_at_epoch",
                        "idempotency_key",
                    }
                },
                "review_action": normalized_action,
                "reviewer_user_id": reviewer,
                "review_reason": why,
                "reviewed_at_epoch": now,
                "payment_ledger_event_id": (
                    ledger_result.get("record", {}).get("ledger_event_id")
                    if ledger_result
                    else None
                ),
                "settlement_ledger_event_id": (
                    ledger_result.get("settlement_record", {}).get("ledger_event_id")
                    if ledger_result
                    else None
                ),
            },
        )
        return {
            "status": target_state,
            "appended": appended,
            "record": record,
            "payment_ledger_result": ledger_result,
        }


def reopen_case(
    *,
    prior_case_id: str,
    reviewer_user_id: int,
    reason: str,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    _require_reviewer(reviewer_user_id)
    prior_id = _nonempty(prior_case_id, label="prior_case_id")
    why = _reason(reason)
    prior = current_case(prior_id, path)
    if prior is None:
        raise BillingSupportError(f"Unknown prior_case_id: {prior_id}")
    if prior.get("case_state") not in CLOSED_STATES:
        raise BillingSupportError("Only a closed case may be reopened as a new case")
    now = _now(now_ts)
    target = path or cases_path()
    new_case_id = _opaque_id()
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        record, appended = _append_case_event_unlocked(
            path=target,
            records=records,
            previous=None,
            case_id=new_case_id,
            event_type=EVENT_CASE_REOPENED,
            case_state="OPEN",
            idempotency_key=f"reopen:{prior_id}:{new_case_id}",
            occurred_at_epoch=now,
            payload={
                "subscriber_ref": prior.get("subscriber_ref"),
                "strategy_product_id": prior.get("strategy_product_id"),
                "subscription_id": prior.get("subscription_id"),
                "client_intent_id": None,
                "origin_action": "REOPENED_SUPPORT",
                "payment_intent_id": prior.get("payment_intent_id"),
                "opening_reason": why,
                "reopened_from_case_id": prior_id,
                "reviewer_user_id": int(reviewer_user_id),
                "audit_correlation_id": _opaque_id(),
            },
        )
        return {"status": "OPENED", "appended": appended, "record": record}


def _latest_private_target(subscriber_ref: str, notification_path: str | None) -> Optional[Dict[str, Any]]:
    matches = [
        row
        for row in notification_scheduler.load_events(notification_path)
        if row.get("event_type") == notification_scheduler.EVENT_TARGET_BOUND
        and row.get("subscriber_ref") == subscriber_ref
    ]
    return dict(matches[-1]) if matches else None


def relay_admin_reply_to_client(
    *,
    case_id: str,
    reviewer_user_id: int,
    text: str,
    admin_message_id: str,
    send_fn: Callable[..., Any] = telegram_publisher.send_message,
    now_ts: float | int | None = None,
    path: str | None = None,
    notification_path: str | None = None,
) -> Dict[str, Any]:
    reply = record_admin_reply(
        case_id=case_id,
        reviewer_user_id=reviewer_user_id,
        text=text,
        admin_message_id=admin_message_id,
        now_ts=now_ts,
        path=path,
    )
    case = reply["record"]
    target = _latest_private_target(str(case["subscriber_ref"]), notification_path)
    if target is None:
        return {**reply, "delivery_result": "FAILED_NO_PRIVATE_TARGET"}
    try:
        send_fn(
            chat_id=int(target["telegram_chat_id"]),
            text=f"Support case {case_id}:\n{text}",
            reply_markup=None,
            thread_id=None,
        )
        delivery = "SENT"
    except Exception:
        delivery = "FAILED"
    return {**reply, "delivery_result": delivery}


def relay_client_message_to_admin(
    *,
    case_id: str,
    subscriber_ref: str,
    text: str,
    client_message_id: str,
    admin_chat_id: int | None = None,
    admin_thread_id: int | None = None,
    send_fn: Callable[..., Any] = telegram_publisher.send_message,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    message = record_client_message(
        case_id=case_id,
        subscriber_ref=subscriber_ref,
        text=text,
        client_message_id=client_message_id,
        now_ts=now_ts,
        path=path,
    )
    chat_id = admin_chat_id
    if chat_id is None:
        raw = os.getenv("ADMIN_CONTROL_CHAT_ID", "").strip()
        try:
            chat_id = int(raw)
        except Exception:
            chat_id = None
    if chat_id is None:
        return {**message, "delivery_result": "FAILED_ADMIN_DESTINATION_MISSING"}
    thread_id = admin_thread_id
    if thread_id is None:
        raw_thread = os.getenv("ADMIN_CONTROL_THREAD_ID", "").strip()
        try:
            thread_id = int(raw_thread) if raw_thread else None
        except Exception:
            thread_id = None
    try:
        send_fn(
            chat_id=int(chat_id),
            thread_id=thread_id,
            text=(
                f"Billing support case {case_id}\n"
                f"Subscriber ref: {hashlib.sha256(subscriber_ref.encode('utf-8')).hexdigest()[:12]}\n"
                f"Client message:\n{text}"
            ),
            reply_markup=None,
        )
        delivery = "SENT"
    except Exception:
        delivery = "FAILED"
    return {**message, "delivery_result": delivery}


def restricted_case_view(
    *, case_id: str, reviewer_user_id: int, path: str | None = None
) -> Dict[str, Any]:
    _require_reviewer(reviewer_user_id)
    history = case_history(case_id, path)
    if not history:
        raise BillingSupportError(f"Unknown case_id: {case_id}")
    return {"case": history[-1], "history": history}


def client_safe_case_view(
    *, case_id: str, subscriber_ref: str, path: str | None = None
) -> Dict[str, Any]:
    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    history = case_history(case_id, path)
    if not history or history[-1].get("subscriber_ref") != subscriber:
        raise BillingSupportError("Client identity does not match support case")

    sensitive = {
        "restricted_telegram_file_id",
        "proof_file_unique_id",
        "reviewer_user_id",
        "payment_ledger_event_id",
        "settlement_ledger_event_id",
    }
    safe_history: list[Dict[str, Any]] = []
    for row in history:
        safe_history.append({key: value for key, value in row.items() if key not in sensitive})
    return {"case": safe_history[-1], "history": safe_history}
