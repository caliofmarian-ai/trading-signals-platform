from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from billing.contracts import BillingContractError, get_strategy_product, load_billing_contract
from core import storage

PAYMENT_STATES = frozenset(
    {
        "CREATED",
        "PENDING",
        "SETTLED",
        "FAILED",
        "EXPIRED",
        "REFUNDED",
        "CHARGEBACK",
        "UNKNOWN",
    }
)
PROVIDER_EVENT_STATES = PAYMENT_STATES - {"CREATED"}
RECONCILIATION_RESULTS = frozenset(
    {
        "NOT_APPLICABLE",
        "MATCHED",
        "UNMATCHED",
        "CONTRADICTORY",
        "DUPLICATE",
    }
)
EVENT_INTENT_CREATED = "PAYMENT_INTENT_CREATED"
EVENT_PROVIDER = "PROVIDER_PAYMENT_EVENT"
EVENT_RECONCILIATION = "PAYMENT_RECONCILIATION_EVIDENCE"
EVENT_REVERSAL = "PAYMENT_REVERSAL_EVENT"
_LOCK_NAME = "billing_payment_ledger"
_LEDGER_RELATIVE = ("billing", "payment_ledger.jsonl")


class PaymentLedgerError(RuntimeError):
    """Raised when payment evidence is invalid, contradictory, or corrupted."""


def ledger_path() -> str:
    return storage.root_path(*_LEDGER_RELATIVE)


def _utc_iso(ts: float | int | None = None) -> str:
    value = float(time.time() if ts is None else ts)
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _opaque_id() -> str:
    return str(uuid.uuid4())


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PaymentLedgerError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PaymentLedgerError("Optional text identifiers must be non-empty when supplied")
    return value.strip()


def _amount(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PaymentLedgerError("amount_minor must be a non-negative integer")
    return value


def _currency(value: Any) -> str:
    text = _nonempty(value, label="currency").upper()
    if len(text) != 3 or not text.isalpha():
        raise PaymentLedgerError("currency must be a three-letter alphabetic code")
    return text


def _validate_raw_event_hash(value: Any) -> str:
    text = _nonempty(value, label="raw_event_hash").lower()
    if len(text) < 16:
        raise PaymentLedgerError("raw_event_hash must be a stable non-trivial digest/reference")
    return text


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_product_plan(strategy_product_id: str, plan_id: str) -> Dict[str, Any]:
    try:
        contract = load_billing_contract()
        product = get_strategy_product(strategy_product_id, contract)
    except BillingContractError as exc:
        raise PaymentLedgerError(str(exc)) from exc

    for plan in product.get("plans", []):
        if isinstance(plan, dict) and plan.get("plan_id") == plan_id:
            if plan.get("requires_payment") is not True:
                raise PaymentLedgerError(f"Plan does not require payment: {plan_id}")
            return dict(plan)
    raise PaymentLedgerError(
        f"plan_id {plan_id} is not owned by strategy_product_id {strategy_product_id}"
    )


def _read_ledger_unlocked(path: str) -> list[Dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    records: list[Dict[str, Any]] = []
    event_ids: set[str] = set()
    sequences: set[int] = set()
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise PaymentLedgerError(f"Unable to read payment ledger: {target}") from exc

    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PaymentLedgerError(
                f"Payment ledger JSON corruption at line {line_number}"
            ) from exc
        if not isinstance(record, dict):
            raise PaymentLedgerError(
                f"Payment ledger record at line {line_number} is not an object"
            )
        event_id = _nonempty(record.get("ledger_event_id"), label="ledger_event_id")
        if event_id in event_ids:
            raise PaymentLedgerError(f"Duplicate ledger_event_id detected: {event_id}")
        event_ids.add(event_id)
        seq = record.get("ledger_seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise PaymentLedgerError(f"Invalid ledger_seq at line {line_number}")
        if seq in sequences:
            raise PaymentLedgerError(f"Duplicate ledger_seq detected: {seq}")
        sequences.add(seq)
        records.append(record)

    if records:
        expected = list(range(1, len(records) + 1))
        actual = [int(record["ledger_seq"]) for record in records]
        if actual != expected:
            raise PaymentLedgerError(
                f"Payment ledger sequence is non-contiguous: expected={expected} actual={actual}"
            )
    return records


def load_ledger(path: str | None = None) -> list[Dict[str, Any]]:
    return _read_ledger_unlocked(path or ledger_path())


def _append_record_unlocked(path: str, records: list[Dict[str, Any]], record: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(record)
    payload["ledger_event_id"] = _opaque_id()
    payload["ledger_seq"] = len(records) + 1
    storage.append_jsonl(path, payload)
    return payload


def _same_fields(record: Mapping[str, Any], expected: Mapping[str, Any], fields: Iterable[str]) -> bool:
    return all(record.get(field) == expected.get(field) for field in fields)


def _find_by_idempotency(records: Iterable[Mapping[str, Any]], idempotency_key: str) -> Optional[Mapping[str, Any]]:
    for record in records:
        if record.get("idempotency_key") == idempotency_key:
            return record
    return None


def _intent_record(records: Iterable[Mapping[str, Any]], payment_intent_id: str) -> Optional[Mapping[str, Any]]:
    matches = [
        record
        for record in records
        if record.get("event_type") == EVENT_INTENT_CREATED
        and record.get("payment_intent_id") == payment_intent_id
    ]
    if len(matches) > 1:
        raise PaymentLedgerError(
            f"Corrupt ledger: multiple intent-creation records for {payment_intent_id}"
        )
    return matches[0] if matches else None


def payment_history(payment_intent_id: str, path: str | None = None) -> list[Dict[str, Any]]:
    intent_id = _nonempty(payment_intent_id, label="payment_intent_id")
    return [
        dict(record)
        for record in load_ledger(path)
        if record.get("payment_intent_id") == intent_id
    ]


def settled_payment_record(payment_intent_id: str, path: str | None = None) -> Optional[Dict[str, Any]]:
    matched = [
        record
        for record in payment_history(payment_intent_id, path)
        if record.get("payment_state") == "SETTLED"
        and record.get("reconciliation_result") == "MATCHED"
    ]
    if len(matched) > 1:
        raise PaymentLedgerError(
            f"Corrupt ledger: multiple matched settlements for {payment_intent_id}"
        )
    return matched[0] if matched else None


def create_payment_intent(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    plan_id: str,
    amount_minor: int,
    currency: str,
    payment_method: str,
    provider: str,
    idempotency_key: str,
    payment_intent_id: str | None = None,
    audit_correlation_id: str | None = None,
    now_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    contract = load_billing_contract()
    method_values = set(contract.get("enums", {}).get("payment_method", []))
    method = _nonempty(payment_method, label="payment_method").upper()
    if method not in method_values:
        raise PaymentLedgerError(f"Unsupported payment_method: {method}")

    subscriber = _nonempty(subscriber_ref, label="subscriber_ref")
    product_id = _nonempty(strategy_product_id, label="strategy_product_id")
    plan = _nonempty(plan_id, label="plan_id")
    _validate_product_plan(product_id, plan)
    amount = _amount(amount_minor)
    ccy = _currency(currency)
    provider_name = _nonempty(provider, label="provider")
    idem = _nonempty(idempotency_key, label="idempotency_key")
    intent_id = _optional_text(payment_intent_id) or _opaque_id()
    correlation_id = _optional_text(audit_correlation_id) or _opaque_id()
    received_at = _utc_iso(now_ts)

    target = path or ledger_path()
    candidate = {
        "event_type": EVENT_INTENT_CREATED,
        "payment_state": "CREATED",
        "payment_intent_id": intent_id,
        "provider": provider_name,
        "provider_event_id": None,
        "provider_tx_ref": None,
        "wallet_tx_id": None,
        "subscriber_ref": subscriber,
        "strategy_product_id": product_id,
        "plan_id": plan,
        "amount_minor": amount,
        "currency": ccy,
        "payment_method": method,
        "provider_state": None,
        "received_at": received_at,
        "settled_at": None,
        "raw_event_hash": None,
        "idempotency_key": idem,
        "reconciliation_result": "NOT_APPLICABLE",
        "audit_correlation_id": correlation_id,
        "reversal_of_ledger_event_id": None,
    }
    identity_fields = (
        "event_type",
        "subscriber_ref",
        "strategy_product_id",
        "plan_id",
        "amount_minor",
        "currency",
        "payment_method",
        "provider",
    )

    with storage.with_lock(_LOCK_NAME):
        records = _read_ledger_unlocked(target)
        existing_idem = _find_by_idempotency(records, idem)
        if existing_idem is not None:
            if _same_fields(existing_idem, candidate, identity_fields):
                return {"status": "DUPLICATE", "appended": False, "record": dict(existing_idem)}
            raise PaymentLedgerError(
                "idempotency_key was already used with different payment-intent evidence"
            )
        existing_intent = _intent_record(records, intent_id)
        if existing_intent is not None:
            raise PaymentLedgerError(f"payment_intent_id already exists: {intent_id}")
        record = _append_record_unlocked(target, records, candidate)
        return {"status": "CREATED", "appended": True, "record": record}


def _conflict_key(source_idempotency_key: str, evidence: Mapping[str, Any]) -> str:
    return f"reconciliation:{source_idempotency_key}:{_canonical_hash(evidence)[:24]}"


def _append_reconciliation_unlocked(
    *,
    path: str,
    records: list[Dict[str, Any]],
    evidence: Dict[str, Any],
    result: str,
    reason: str,
) -> Dict[str, Any]:
    conflict_key = _conflict_key(str(evidence["idempotency_key"]), evidence)
    existing = _find_by_idempotency(records, conflict_key)
    if existing is not None:
        return dict(existing)
    record = dict(evidence)
    record.update(
        {
            "event_type": EVENT_RECONCILIATION,
            "payment_state": "UNKNOWN",
            "idempotency_key": conflict_key,
            "source_idempotency_key": evidence["idempotency_key"],
            "reconciliation_result": result,
            "reconciliation_reason": reason,
            "settled_at": None,
            "reversal_of_ledger_event_id": None,
        }
    )
    return _append_record_unlocked(path, records, record)


def ingest_provider_event(
    *,
    payment_intent_id: str,
    provider: str,
    payment_state: str,
    provider_state: str,
    amount_minor: int,
    currency: str,
    raw_event_hash: str,
    idempotency_key: str,
    provider_event_id: str | None = None,
    provider_tx_ref: str | None = None,
    wallet_tx_id: str | None = None,
    settled_at_ts: float | int | None = None,
    audit_correlation_id: str | None = None,
    received_at_ts: float | int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    intent_id = _nonempty(payment_intent_id, label="payment_intent_id")
    provider_name = _nonempty(provider, label="provider")
    normalized_state = _nonempty(payment_state, label="payment_state").upper()
    if normalized_state not in PROVIDER_EVENT_STATES:
        raise PaymentLedgerError(f"Unsupported provider payment_state: {normalized_state}")
    raw_provider_state = _nonempty(provider_state, label="provider_state")
    amount = _amount(amount_minor)
    ccy = _currency(currency)
    raw_hash = _validate_raw_event_hash(raw_event_hash)
    idem = _nonempty(idempotency_key, label="idempotency_key")
    provider_event = _optional_text(provider_event_id)
    provider_tx = _optional_text(provider_tx_ref)
    wallet_tx = _optional_text(wallet_tx_id)
    if not any((provider_event, provider_tx, wallet_tx)):
        raise PaymentLedgerError(
            "Provider evidence requires provider_event_id, provider_tx_ref, or wallet_tx_id"
        )
    correlation_id = _optional_text(audit_correlation_id) or _opaque_id()
    received_at = _utc_iso(received_at_ts)
    settled_at = _utc_iso(settled_at_ts) if normalized_state == "SETTLED" else None
    if normalized_state == "SETTLED" and settled_at_ts is None:
        settled_at = received_at

    target = path or ledger_path()
    base_evidence = {
        "event_type": EVENT_PROVIDER,
        "payment_state": normalized_state,
        "payment_intent_id": intent_id,
        "provider": provider_name,
        "provider_event_id": provider_event,
        "provider_tx_ref": provider_tx,
        "wallet_tx_id": wallet_tx,
        "subscriber_ref": None,
        "strategy_product_id": None,
        "plan_id": None,
        "amount_minor": amount,
        "currency": ccy,
        "payment_method": None,
        "provider_state": raw_provider_state,
        "received_at": received_at,
        "settled_at": settled_at,
        "raw_event_hash": raw_hash,
        "idempotency_key": idem,
        "reconciliation_result": "MATCHED",
        "audit_correlation_id": correlation_id,
        "reversal_of_ledger_event_id": None,
    }
    duplicate_fields = (
        "payment_intent_id",
        "provider",
        "payment_state",
        "provider_state",
        "amount_minor",
        "currency",
        "raw_event_hash",
        "provider_event_id",
        "provider_tx_ref",
        "wallet_tx_id",
    )

    with storage.with_lock(_LOCK_NAME):
        records = _read_ledger_unlocked(target)
        existing_idem = _find_by_idempotency(records, idem)
        if existing_idem is not None:
            if _same_fields(existing_idem, base_evidence, duplicate_fields):
                return {"status": "DUPLICATE", "appended": False, "record": dict(existing_idem)}
            conflict = _append_reconciliation_unlocked(
                path=target,
                records=records,
                evidence=base_evidence,
                result="CONTRADICTORY",
                reason="IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_EVIDENCE",
            )
            return {"status": "CONTRADICTORY", "appended": True, "record": conflict}

        intent = _intent_record(records, intent_id)
        if intent is None:
            unmatched = _append_reconciliation_unlocked(
                path=target,
                records=records,
                evidence=base_evidence,
                result="UNMATCHED",
                reason="PAYMENT_INTENT_NOT_FOUND",
            )
            return {"status": "UNMATCHED", "appended": True, "record": unmatched}

        attributed = dict(base_evidence)
        attributed.update(
            {
                "subscriber_ref": intent.get("subscriber_ref"),
                "strategy_product_id": intent.get("strategy_product_id"),
                "plan_id": intent.get("plan_id"),
                "payment_method": intent.get("payment_method"),
            }
        )
        mismatches: list[str] = []
        if provider_name != intent.get("provider"):
            mismatches.append("provider")
        if amount != intent.get("amount_minor"):
            mismatches.append("amount_minor")
        if ccy != intent.get("currency"):
            mismatches.append("currency")
        if mismatches:
            contradiction = _append_reconciliation_unlocked(
                path=target,
                records=records,
                evidence=attributed,
                result="CONTRADICTORY",
                reason="INTENT_EVIDENCE_MISMATCH:" + ",".join(mismatches),
            )
            return {"status": "CONTRADICTORY", "appended": True, "record": contradiction}

        settled = [
            record
            for record in records
            if record.get("payment_intent_id") == intent_id
            and record.get("payment_state") == "SETTLED"
            and record.get("reconciliation_result") == "MATCHED"
        ]
        if len(settled) > 1:
            raise PaymentLedgerError(
                f"Corrupt ledger: multiple matched settlements for {intent_id}"
            )

        if normalized_state == "SETTLED" and settled:
            existing_settlement = settled[0]
            if _same_fields(existing_settlement, attributed, duplicate_fields):
                return {
                    "status": "DUPLICATE_SETTLEMENT",
                    "appended": False,
                    "record": dict(existing_settlement),
                }
            contradiction = _append_reconciliation_unlocked(
                path=target,
                records=records,
                evidence=attributed,
                result="CONTRADICTORY",
                reason="SECOND_SETTLEMENT_ATTEMPT_FOR_INTENT",
            )
            return {"status": "CONTRADICTORY", "appended": True, "record": contradiction}

        if settled and normalized_state not in {"REFUNDED", "CHARGEBACK"}:
            contradiction = _append_reconciliation_unlocked(
                path=target,
                records=records,
                evidence=attributed,
                result="CONTRADICTORY",
                reason="NON_REVERSAL_EVENT_AFTER_SETTLEMENT",
            )
            return {"status": "CONTRADICTORY", "appended": True, "record": contradiction}

        if normalized_state in {"REFUNDED", "CHARGEBACK"}:
            if not settled:
                contradiction = _append_reconciliation_unlocked(
                    path=target,
                    records=records,
                    evidence=attributed,
                    result="CONTRADICTORY",
                    reason="REVERSAL_WITHOUT_MATCHED_SETTLEMENT",
                )
                return {"status": "CONTRADICTORY", "appended": True, "record": contradiction}
            attributed["event_type"] = EVENT_REVERSAL
            attributed["reversal_of_ledger_event_id"] = settled[0]["ledger_event_id"]

        record = _append_record_unlocked(target, records, attributed)
        return {"status": normalized_state, "appended": True, "record": record}
