from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

import requests

from billing import payment_ledger
from core import storage

PROVIDER = "REVOLUT_MERCHANT"
DEFAULT_API_VERSION = "2026-04-20"
SANDBOX_BASE_URL = "https://sandbox-merchant.revolut.com"
PRODUCTION_BASE_URL = "https://merchant.revolut.com"
WEBHOOK_TOLERANCE_MS = 5 * 60 * 1000
MAX_RETRIES = 3

ORDER_STATE_TO_LEDGER = {
    "pending": "PENDING",
    "processing": "PENDING",
    "authorised": "PENDING",
    "completed": "SETTLED",
    "cancelled": "FAILED",
    "failed": "FAILED",
}
FINAL_ORDER_STATES = frozenset({"completed", "cancelled", "failed"})
SAVED_METHOD_TYPES = frozenset({"card", "revolut_pay"})

EVENT_ORDER_BOUND = "REVOLUT_ORDER_BOUND"
EVENT_ORDER_RECOVERED = "REVOLUT_ORDER_RECOVERED"
EVENT_WEBHOOK_VERIFIED = "REVOLUT_WEBHOOK_VERIFIED"
EVENT_WEBHOOK_UNMATCHED = "REVOLUT_WEBHOOK_UNMATCHED"
EVENT_RECONCILED = "REVOLUT_ORDER_RECONCILED"
EVENT_PROVIDER_UNAVAILABLE = "REVOLUT_PROVIDER_UNAVAILABLE"
EVENT_RECURRING_PAYMENT_INITIATED = "REVOLUT_RECURRING_PAYMENT_INITIATED"

_LOCK_NAME = "billing_revolut_merchant"
_EVENTS_RELATIVE = ("billing", "revolut_merchant_events.jsonl")
_SECRET_PATTERN = re.compile(r"\b(?:sk|wsk)_[A-Za-z0-9_\-]+\b")


class RevolutMerchantError(RuntimeError):
    """Raised when Revolut evidence or adapter configuration is unsafe."""


class RevolutProviderUnavailable(RevolutMerchantError):
    """Raised for retryable/transport/provider availability failures."""


def events_path() -> str:
    return storage.root_path(*_EVENTS_RELATIVE)


def _now(value: float | int | None = None) -> int:
    return int(time.time() if value is None else value)


def _opaque_id() -> str:
    return str(uuid.uuid4())


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RevolutMerchantError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    return _nonempty(value, label="optional text")


def _amount(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RevolutMerchantError("amount_minor must be a non-negative integer")
    return value


def _currency(value: Any) -> str:
    text = _nonempty(value, label="currency").upper()
    if len(text) != 3 or not text.isalpha():
        raise RevolutMerchantError("currency must be a three-letter code")
    return text


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _redact(value: Any, *secrets: str) -> str:
    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return _SECRET_PATTERN.sub("[REDACTED]", text)


def _utc_iso(ts: float | int | None = None) -> str:
    value = float(time.time() if ts is None else ts)
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def _parse_iso_epoch(value: Any) -> Optional[int]:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def _read_events_unlocked(path: str) -> list[Dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise RevolutMerchantError(f"Unable to read Revolut adapter log: {target}") from exc

    records: list[Dict[str, Any]] = []
    event_ids: set[str] = set()
    sequences: set[int] = set()
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RevolutMerchantError(
                f"Revolut adapter JSON corruption at line {line_number}"
            ) from exc
        if not isinstance(row, dict):
            raise RevolutMerchantError(
                f"Revolut adapter record at line {line_number} is not an object"
            )
        event_id = _nonempty(row.get("revolut_event_id"), label="revolut_event_id")
        if event_id in event_ids:
            raise RevolutMerchantError(f"Duplicate revolut_event_id: {event_id}")
        event_ids.add(event_id)
        seq = row.get("revolut_seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise RevolutMerchantError(f"Invalid revolut_seq at line {line_number}")
        if seq in sequences:
            raise RevolutMerchantError(f"Duplicate revolut_seq: {seq}")
        sequences.add(seq)
        records.append(row)

    if records:
        expected = list(range(1, len(records) + 1))
        actual = [int(row["revolut_seq"]) for row in records]
        if actual != expected:
            raise RevolutMerchantError(
                f"Revolut adapter sequence is non-contiguous: expected={expected} actual={actual}"
            )
    return records


def load_events(path: str | None = None) -> list[Dict[str, Any]]:
    return _read_events_unlocked(path or events_path())


def _find_idempotency(
    records: Iterable[Mapping[str, Any]], key: str
) -> Optional[Mapping[str, Any]]:
    for row in records:
        if row.get("idempotency_key") == key:
            return row
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
    record["revolut_event_id"] = _opaque_id()
    record["revolut_seq"] = len(records) + 1
    if idempotency_key:
        record["idempotency_key"] = idempotency_key
    storage.append_jsonl(path, record)
    return record, True


def _intent_creation(
    payment_intent_id: str,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    intent_id = _nonempty(payment_intent_id, label="payment_intent_id")
    rows = [
        row
        for row in payment_ledger.payment_history(intent_id, payment_path)
        if row.get("event_type") == payment_ledger.EVENT_INTENT_CREATED
    ]
    if len(rows) != 1:
        raise RevolutMerchantError(
            f"Payment intent must have exactly one creation record: {intent_id}"
        )
    row = dict(rows[0])
    if row.get("provider") != PROVIDER:
        raise RevolutMerchantError(
            f"Payment intent provider is not {PROVIDER}: {intent_id}"
        )
    if row.get("payment_method") != "FIAT":
        raise RevolutMerchantError("Revolut Merchant adapter requires FIAT payment_method")
    return row


def _binding_for_intent(
    records: Iterable[Mapping[str, Any]], payment_intent_id: str
) -> Optional[Dict[str, Any]]:
    matches = [
        dict(row)
        for row in records
        if row.get("event_type") in {EVENT_ORDER_BOUND, EVENT_ORDER_RECOVERED}
        and row.get("payment_intent_id") == payment_intent_id
    ]
    order_ids = {str(row.get("revolut_order_id")) for row in matches}
    if len(order_ids) > 1:
        raise RevolutMerchantError(
            f"Multiple Revolut orders bound to one payment intent: {payment_intent_id}"
        )
    return matches[-1] if matches else None


def _binding_for_order(
    records: Iterable[Mapping[str, Any]], revolut_order_id: str
) -> Optional[Dict[str, Any]]:
    matches = [
        dict(row)
        for row in records
        if row.get("event_type") in {EVENT_ORDER_BOUND, EVENT_ORDER_RECOVERED}
        and row.get("revolut_order_id") == revolut_order_id
    ]
    intent_ids = {str(row.get("payment_intent_id")) for row in matches}
    if len(intent_ids) > 1:
        raise RevolutMerchantError(
            f"One Revolut order is bound to multiple payment intents: {revolut_order_id}"
        )
    return matches[-1] if matches else None


def _safe_environment(value: Any) -> str:
    env = str(value or "sandbox").strip().lower()
    if env not in {"sandbox", "production"}:
        raise RevolutMerchantError("REVOLUT_MERCHANT_ENV must be sandbox or production")
    return env


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class RevolutMerchantClient:
    """Server-side Merchant API client with explicit sandbox/production boundary."""

    def __init__(
        self,
        *,
        secret_key: str,
        environment: str = "sandbox",
        api_version: str = DEFAULT_API_VERSION,
        request_fn: Callable[..., Any] = requests.request,
        sleep_fn: Callable[[float], None] = time.sleep,
        max_retries: int = 2,
        allow_production: bool = False,
    ) -> None:
        self._secret_key = _nonempty(secret_key, label="Revolut Merchant secret key")
        self.environment = _safe_environment(environment)
        self.api_version = _nonempty(api_version, label="Revolut-Api-Version")
        if self.environment == "production" and not allow_production:
            raise RevolutMerchantError(
                "Production Revolut Merchant calls require explicit allow_production"
            )
        if isinstance(max_retries, bool) or not isinstance(max_retries, int):
            raise RevolutMerchantError("max_retries must be an integer")
        self.max_retries = max(0, min(max_retries, MAX_RETRIES))
        self._request_fn = request_fn
        self._sleep_fn = sleep_fn
        self.base_url = (
            SANDBOX_BASE_URL
            if self.environment == "sandbox"
            else PRODUCTION_BASE_URL
        )

    @classmethod
    def from_env(
        cls,
        *,
        request_fn: Callable[..., Any] = requests.request,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> "RevolutMerchantClient":
        retries_raw = os.getenv("REVOLUT_MERCHANT_MAX_RETRIES", "2").strip()
        try:
            retries = int(retries_raw)
        except ValueError as exc:
            raise RevolutMerchantError(
                "REVOLUT_MERCHANT_MAX_RETRIES must be an integer"
            ) from exc
        return cls(
            secret_key=os.getenv("REVOLUT_MERCHANT_SECRET_KEY", ""),
            environment=os.getenv("REVOLUT_MERCHANT_ENV", "sandbox"),
            api_version=os.getenv(
                "REVOLUT_MERCHANT_API_VERSION", DEFAULT_API_VERSION
            ),
            request_fn=request_fn,
            sleep_fn=sleep_fn,
            max_retries=retries,
            allow_production=_env_flag(
                "REVOLUT_MERCHANT_ALLOW_PRODUCTION", default=False
            ),
        )

    def safe_config(self) -> Dict[str, Any]:
        return {
            "provider": PROVIDER,
            "environment": self.environment,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "max_retries": self.max_retries,
            "secret_configured": True,
        }

    def _headers(self, *, has_body: bool) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._secret_key}",
            "Revolut-Api-Version": self.api_version,
            "Accept": "application/json",
        }
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        last_error: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._request_fn(
                    method,
                    f"{self.base_url}{path}",
                    headers=self._headers(has_body=json_body is not None),
                    json=dict(json_body) if json_body is not None else None,
                    params=dict(params) if params is not None else None,
                    timeout=15,
                )
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    self._sleep_fn(min(0.25 * (2**attempt), 1.0))
                    continue
                raise RevolutProviderUnavailable(
                    f"Revolut transport unavailable: {_redact(exc, self._secret_key)}"
                ) from exc

            status = int(getattr(response, "status_code", 0) or 0)
            try:
                data = response.json()
            except Exception:
                data = None

            if status == 429 or status >= 500 or status == 0:
                last_error = RevolutProviderUnavailable(
                    f"Revolut provider unavailable: http={status}"
                )
                if attempt < self.max_retries:
                    self._sleep_fn(min(0.25 * (2**attempt), 1.0))
                    continue
                raise last_error

            if status < 200 or status >= 300:
                detail = ""
                if isinstance(data, dict):
                    detail = str(
                        data.get("message")
                        or data.get("error")
                        or data.get("description")
                        or ""
                    )
                raise RevolutMerchantError(
                    f"Revolut API rejected request: http={status} "
                    f"detail={_redact(detail, self._secret_key)[:300]}"
                )

            if not isinstance(data, dict):
                raise RevolutMerchantError("Revolut API returned a non-object JSON response")
            return dict(data)

        raise RevolutProviderUnavailable(
            f"Revolut provider unavailable: {_redact(last_error, self._secret_key)}"
        )

    def create_order(
        self,
        *,
        amount_minor: int,
        currency: str,
        merchant_reference: str,
        customer_id: str | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "amount": _amount(amount_minor),
            "currency": _currency(currency),
            "merchant_order_data": {
                "reference": _nonempty(
                    merchant_reference, label="merchant_order_data.reference"
                )
            },
        }
        customer = _optional_text(customer_id)
        if customer is not None:
            payload["customer_id"] = customer
        return self._request("POST", "/api/orders", json_body=payload)

    def retrieve_order(self, revolut_order_id: str) -> Dict[str, Any]:
        order_id = _nonempty(revolut_order_id, label="revolut_order_id")
        return self._request("GET", f"/api/orders/{order_id}")

    def find_orders_by_reference(self, merchant_reference: str) -> list[Dict[str, Any]]:
        reference = _nonempty(merchant_reference, label="merchant_reference")
        data = self._request(
            "GET",
            "/api/orders",
            params={"merchant_order_data_reference": reference, "limit": 10},
        )
        orders = data.get("orders")
        if not isinstance(orders, list):
            raise RevolutMerchantError("Retrieve order list response is missing orders")
        return [dict(order) for order in orders if isinstance(order, dict)]

    def pay_saved_method(
        self,
        *,
        revolut_order_id: str,
        saved_payment_method_id: str,
        saved_payment_method_type: str,
    ) -> Dict[str, Any]:
        order_id = _nonempty(revolut_order_id, label="revolut_order_id")
        method_id = _nonempty(
            saved_payment_method_id, label="saved_payment_method_id"
        )
        method_type = _nonempty(
            saved_payment_method_type, label="saved_payment_method_type"
        ).lower()
        if method_type not in SAVED_METHOD_TYPES:
            raise RevolutMerchantError(
                f"Unsupported saved payment method type for merchant initiation: {method_type}"
            )
        return self._request(
            "POST",
            f"/api/orders/{order_id}/payments",
            json_body={
                "saved_payment_method": {
                    "type": method_type,
                    "id": method_id,
                    "initiator": "merchant",
                }
            },
        )


def verify_webhook_signature(
    *,
    raw_body: bytes,
    timestamp_header: str,
    signature_header: str,
    signing_secret: str,
    now_ms: int | None = None,
) -> Dict[str, Any]:
    if not isinstance(raw_body, (bytes, bytearray)):
        raise RevolutMerchantError("raw_body must be bytes")
    timestamp = _nonempty(timestamp_header, label="Revolut-Request-Timestamp")
    secret = _nonempty(signing_secret, label="Revolut webhook signing secret")
    signatures = [part.strip() for part in _nonempty(
        signature_header, label="Revolut-Signature"
    ).split(",") if part.strip().startswith("v1=")]
    if not signatures:
        raise RevolutMerchantError("Revolut-Signature contains no v1 signature")
    try:
        timestamp_ms = int(timestamp)
    except ValueError as exc:
        raise RevolutMerchantError("Revolut webhook timestamp is not an integer") from exc
    current_ms = int(time.time() * 1000) if now_ms is None else int(now_ms)
    if abs(current_ms - timestamp_ms) > WEBHOOK_TOLERANCE_MS:
        raise RevolutMerchantError("Revolut webhook timestamp is outside 5-minute tolerance")

    payload = b"v1." + timestamp.encode("utf-8") + b"." + bytes(raw_body)
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    expected = f"v1={digest}"
    if not any(hmac.compare_digest(expected, supplied) for supplied in signatures):
        raise RevolutMerchantError("Revolut webhook signature verification failed")
    return {
        "verified": True,
        "timestamp_ms": timestamp_ms,
        "raw_event_hash": _sha256_bytes(bytes(raw_body)),
    }


def _header(headers: Mapping[str, Any], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return str(value)
    return ""


def _parse_webhook(raw_body: bytes) -> Dict[str, Any]:
    try:
        payload = json.loads(bytes(raw_body).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RevolutMerchantError("Revolut webhook payload is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise RevolutMerchantError("Revolut webhook payload must be an object")
    order_id = _nonempty(payload.get("order_id"), label="webhook.order_id")
    event = _nonempty(payload.get("event"), label="webhook.event")
    return {**payload, "order_id": order_id, "event": event}


def _order_reference(order: Mapping[str, Any]) -> Optional[str]:
    merchant_data = order.get("merchant_order_data")
    if isinstance(merchant_data, dict):
        reference = merchant_data.get("reference")
        if isinstance(reference, str) and reference.strip():
            return reference.strip()
    legacy = order.get("merchant_order_ext_ref")
    if isinstance(legacy, str) and legacy.strip():
        return legacy.strip()
    return None


def _order_amount_currency(order: Mapping[str, Any]) -> tuple[int, str]:
    amount = order.get("amount")
    currency = order.get("currency")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise RevolutMerchantError("Retrieved Revolut order is missing valid amount")
    return amount, _currency(currency)


def _payment_reference(order: Mapping[str, Any]) -> str:
    payments = order.get("payments")
    if isinstance(payments, list):
        captured = [
            payment
            for payment in payments
            if isinstance(payment, dict)
            and str(payment.get("state") or "").lower() == "captured"
            and isinstance(payment.get("id"), str)
            and payment.get("id").strip()
        ]
        if captured:
            return str(captured[-1]["id"]).strip()
        valid = [
            payment
            for payment in payments
            if isinstance(payment, dict)
            and isinstance(payment.get("id"), str)
            and payment.get("id").strip()
        ]
        if valid:
            return str(valid[-1]["id"]).strip()
    return _nonempty(order.get("id"), label="order.id")


def _normalize_order_state(order: Mapping[str, Any]) -> tuple[str, str]:
    state = _nonempty(order.get("state"), label="order.state").lower()
    return ORDER_STATE_TO_LEDGER.get(state, "UNKNOWN"), state


def _record_adapter_event(
    *,
    path: str,
    payload: Mapping[str, Any],
    idempotency_key: str | None = None,
) -> Dict[str, Any]:
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(path)
        row, _ = _append_unlocked(
            path=path,
            records=records,
            payload=payload,
            idempotency_key=idempotency_key,
        )
    return row


def _validate_recovered_order(
    order: Mapping[str, Any], intent: Mapping[str, Any]
) -> str:
    order_id = _nonempty(order.get("id"), label="recovered order.id")
    amount, currency = _order_amount_currency(order)
    if amount != intent.get("amount_minor") or currency != intent.get("currency"):
        raise RevolutMerchantError(
            "Recovered Revolut order conflicts with payment-intent amount/currency"
        )
    reference = _order_reference(order)
    if reference != intent.get("payment_intent_id"):
        raise RevolutMerchantError(
            "Recovered Revolut order reference does not match payment_intent_id"
        )
    return order_id


def create_order_for_intent(
    *,
    payment_intent_id: str,
    client: RevolutMerchantClient,
    customer_id: str | None = None,
    path: str | None = None,
    payment_path: str | None = None,
    now_ts: float | int | None = None,
) -> Dict[str, Any]:
    intent = _intent_creation(payment_intent_id, payment_path)
    intent_id = str(intent["payment_intent_id"])
    target = path or events_path()
    now = _now(now_ts)

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        existing = _binding_for_intent(records, intent_id)
        if existing is not None:
            return {"status": "EXISTS", "appended": False, "record": existing}

    # Query by merchant reference before creation. If a previous process created
    # the provider order but crashed before local persistence, recover it instead
    # of creating a second chargeable order.
    existing_orders = client.find_orders_by_reference(intent_id)
    if len(existing_orders) > 1:
        raise RevolutMerchantError(
            f"Multiple Revolut orders exist for merchant reference {intent_id}"
        )
    if existing_orders:
        order = existing_orders[0]
        order_id = _validate_recovered_order(order, intent)
        event_type = EVENT_ORDER_RECOVERED
        status = "RECOVERED"
    else:
        order = client.create_order(
            amount_minor=int(intent["amount_minor"]),
            currency=str(intent["currency"]),
            merchant_reference=intent_id,
            customer_id=customer_id,
        )
        order_id = _nonempty(order.get("id"), label="created order.id")
        if order.get("amount") is not None or order.get("currency") is not None:
            _validate_recovered_order(order, intent)
        event_type = EVENT_ORDER_BOUND
        status = "CREATED"

    customer = _optional_text(customer_id)
    payload = {
        "event_type": event_type,
        "provider": PROVIDER,
        "environment": client.environment,
        "api_version": client.api_version,
        "payment_intent_id": intent_id,
        "revolut_order_id": order_id,
        "provider_order_state": str(order.get("state") or "unknown").lower(),
        "amount_minor": intent["amount_minor"],
        "currency": intent["currency"],
        "customer_id_sha256": _sha256_text(customer) if customer else None,
        "occurred_at_epoch": now,
    }
    idem = f"revolut-order-binding:{intent_id}:{order_id}"
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        existing = _binding_for_intent(records, intent_id)
        if existing is not None:
            if existing.get("revolut_order_id") != order_id:
                raise RevolutMerchantError(
                    "Concurrent Revolut order binding conflict for payment intent"
                )
            return {"status": "EXISTS", "appended": False, "record": existing}
        record, appended = _append_unlocked(
            path=target,
            records=records,
            payload=payload,
            idempotency_key=idem,
        )
    return {"status": status, "appended": appended, "record": record, "order": order}


def create_payment_intent_and_order(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    plan_id: str,
    amount_minor: int,
    currency: str,
    idempotency_key: str,
    client: RevolutMerchantClient,
    payment_intent_id: str | None = None,
    audit_correlation_id: str | None = None,
    customer_id: str | None = None,
    path: str | None = None,
    payment_path: str | None = None,
    now_ts: float | int | None = None,
) -> Dict[str, Any]:
    intent_result = payment_ledger.create_payment_intent(
        subscriber_ref=subscriber_ref,
        strategy_product_id=strategy_product_id,
        plan_id=plan_id,
        amount_minor=amount_minor,
        currency=currency,
        payment_method="FIAT",
        provider=PROVIDER,
        idempotency_key=idempotency_key,
        payment_intent_id=payment_intent_id,
        audit_correlation_id=audit_correlation_id,
        now_ts=now_ts,
        path=payment_path,
    )
    intent_id = str(intent_result["record"]["payment_intent_id"])
    order_result = create_order_for_intent(
        payment_intent_id=intent_id,
        client=client,
        customer_id=customer_id,
        path=path,
        payment_path=payment_path,
        now_ts=now_ts,
    )
    return {
        "status": "READY",
        "payment_intent": intent_result,
        "revolut_order": order_result,
    }


def _reconciliation_provider_event_id(
    order: Mapping[str, Any], order_state: str, raw_hash: str
) -> str:
    updated = str(order.get("updated_at") or order.get("completed_at") or "").strip()
    suffix = _sha256_text(updated)[:12] if updated else raw_hash[:12]
    return f"revolut-order:{order.get('id')}:{order_state}:{suffix}"


def reconcile_order(
    *,
    payment_intent_id: str,
    client: RevolutMerchantClient,
    trigger: str = "POLL",
    path: str | None = None,
    payment_path: str | None = None,
    now_ts: float | int | None = None,
) -> Dict[str, Any]:
    intent = _intent_creation(payment_intent_id, payment_path)
    intent_id = str(intent["payment_intent_id"])
    target = path or events_path()
    now = _now(now_ts)
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        binding = _binding_for_intent(records, intent_id)
    if binding is None:
        raise RevolutMerchantError(
            f"No Revolut order binding exists for payment intent: {intent_id}"
        )
    order_id = str(binding["revolut_order_id"])

    try:
        order = client.retrieve_order(order_id)
    except RevolutProviderUnavailable as exc:
        record = _record_adapter_event(
            path=target,
            payload={
                "event_type": EVENT_PROVIDER_UNAVAILABLE,
                "provider": PROVIDER,
                "payment_intent_id": intent_id,
                "revolut_order_id": order_id,
                "trigger": trigger,
                "occurred_at_epoch": now,
                "error": _redact(exc),
            },
        )
        return {
            "status": "PROVIDER_UNAVAILABLE",
            "ledger_appended": False,
            "record": record,
        }

    returned_id = _nonempty(order.get("id"), label="retrieved order.id")
    if returned_id != order_id:
        raise RevolutMerchantError("Retrieved Revolut order ID conflicts with binding")
    amount, currency = _order_amount_currency(order)
    payment_state, provider_state = _normalize_order_state(order)
    raw_hash = _canonical_hash(order)
    provider_event_id = _reconciliation_provider_event_id(
        order, provider_state, raw_hash
    )
    provider_tx_ref = _payment_reference(order)
    completed_epoch = _parse_iso_epoch(order.get("completed_at"))

    ledger_result = payment_ledger.ingest_provider_event(
        payment_intent_id=intent_id,
        provider=PROVIDER,
        payment_state=payment_state,
        provider_state=provider_state,
        amount_minor=amount,
        currency=currency,
        raw_event_hash=raw_hash,
        idempotency_key=provider_event_id,
        provider_event_id=provider_event_id,
        provider_tx_ref=provider_tx_ref,
        settled_at_ts=(completed_epoch or now) if payment_state == "SETTLED" else None,
        audit_correlation_id=str(intent.get("audit_correlation_id") or _opaque_id()),
        received_at_ts=now,
        path=payment_path,
    )
    record = _record_adapter_event(
        path=target,
        payload={
            "event_type": EVENT_RECONCILED,
            "provider": PROVIDER,
            "payment_intent_id": intent_id,
            "revolut_order_id": order_id,
            "provider_order_state": provider_state,
            "normalized_payment_state": payment_state,
            "provider_tx_ref": provider_tx_ref,
            "provider_event_id": provider_event_id,
            "provider_order_hash": raw_hash,
            "ledger_status": ledger_result.get("status"),
            "trigger": trigger,
            "occurred_at_epoch": now,
        },
        idempotency_key=f"revolut-reconcile:{provider_event_id}",
    )
    return {
        "status": str(ledger_result.get("status")),
        "ledger_appended": bool(ledger_result.get("appended")),
        "ledger_result": ledger_result,
        "record": record,
        "order": order,
    }


def charge_saved_payment_method(
    *,
    payment_intent_id: str,
    customer_id: str,
    saved_payment_method_id: str,
    saved_payment_method_type: str,
    consent_reference: str,
    client: RevolutMerchantClient,
    path: str | None = None,
    payment_path: str | None = None,
    now_ts: float | int | None = None,
) -> Dict[str, Any]:
    consent = _nonempty(consent_reference, label="consent_reference")
    customer = _nonempty(customer_id, label="customer_id")
    method_id = _nonempty(saved_payment_method_id, label="saved_payment_method_id")
    method_type = _nonempty(
        saved_payment_method_type, label="saved_payment_method_type"
    ).lower()
    if method_type not in SAVED_METHOD_TYPES:
        raise RevolutMerchantError(
            f"Unsupported saved payment method type: {method_type}"
        )

    order_result = create_order_for_intent(
        payment_intent_id=payment_intent_id,
        client=client,
        customer_id=customer,
        path=path,
        payment_path=payment_path,
        now_ts=now_ts,
    )
    binding = order_result["record"]
    expected_customer_hash = _sha256_text(customer)
    if binding.get("customer_id_sha256") != expected_customer_hash:
        raise RevolutMerchantError(
            "Existing Revolut order was not created for the supplied customer_id"
        )
    order_id = str(binding["revolut_order_id"])
    payment = client.pay_saved_method(
        revolut_order_id=order_id,
        saved_payment_method_id=method_id,
        saved_payment_method_type=method_type,
    )
    payment_id = _nonempty(payment.get("id"), label="payment.id")
    provider_payment_state = str(payment.get("state") or "unknown").lower()
    target = path or events_path()
    record = _record_adapter_event(
        path=target,
        payload={
            "event_type": EVENT_RECURRING_PAYMENT_INITIATED,
            "provider": PROVIDER,
            "payment_intent_id": payment_intent_id,
            "revolut_order_id": order_id,
            "revolut_payment_id": payment_id,
            "provider_payment_state": provider_payment_state,
            "saved_payment_method_type": method_type,
            "saved_payment_method_id_sha256": _sha256_text(method_id),
            "customer_id_sha256": expected_customer_hash,
            "consent_reference_sha256": _sha256_text(consent),
            "occurred_at_epoch": _now(now_ts),
        },
        idempotency_key=(
            f"revolut-recurring-payment:{payment_intent_id}:{payment_id}"
        ),
    )
    # The payment response is not payment truth. Retrieve the order and feed
    # only provider-reconciled state into #159.
    reconciliation = reconcile_order(
        payment_intent_id=payment_intent_id,
        client=client,
        trigger="SAVED_METHOD_PAYMENT",
        path=path,
        payment_path=payment_path,
        now_ts=now_ts,
    )
    return {
        "status": "PAYMENT_INITIATED",
        "record": record,
        "reconciliation": reconciliation,
    }


def process_verified_webhook(
    *,
    raw_body: bytes,
    headers: Mapping[str, Any],
    client: RevolutMerchantClient,
    signing_secret: str | None = None,
    now_ms: int | None = None,
    path: str | None = None,
    payment_path: str | None = None,
) -> Dict[str, Any]:
    secret = signing_secret or os.getenv("REVOLUT_MERCHANT_WEBHOOK_SECRET", "")
    verified = verify_webhook_signature(
        raw_body=raw_body,
        timestamp_header=_header(headers, "Revolut-Request-Timestamp"),
        signature_header=_header(headers, "Revolut-Signature"),
        signing_secret=secret,
        now_ms=now_ms,
    )
    webhook = _parse_webhook(raw_body)
    order_id = str(webhook["order_id"])
    raw_hash = str(verified["raw_event_hash"])
    target = path or events_path()
    now = int((now_ms if now_ms is not None else int(time.time() * 1000)) / 1000)
    webhook_key = f"revolut-webhook:{raw_hash}"

    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        existing = _find_idempotency(records, webhook_key)
        binding = _binding_for_order(records, order_id)
        if existing is None:
            payload = {
                "event_type": (
                    EVENT_WEBHOOK_VERIFIED if binding is not None else EVENT_WEBHOOK_UNMATCHED
                ),
                "provider": PROVIDER,
                "webhook_event": webhook.get("event"),
                "revolut_order_id": order_id,
                "payment_intent_id": (
                    binding.get("payment_intent_id") if binding is not None else None
                ),
                "raw_event_hash": raw_hash,
                "webhook_timestamp_ms": verified["timestamp_ms"],
                "occurred_at_epoch": now,
            }
            webhook_record, _ = _append_unlocked(
                path=target,
                records=records,
                payload=payload,
                idempotency_key=webhook_key,
            )
        else:
            webhook_record = dict(existing)

    if binding is None:
        reference = webhook.get("merchant_order_ext_ref")
        if isinstance(reference, str) and reference.strip():
            with storage.with_lock(_LOCK_NAME):
                records = _read_events_unlocked(target)
                candidate = _binding_for_intent(records, reference.strip())
                if candidate is not None and candidate.get("revolut_order_id") == order_id:
                    binding = candidate
    if binding is None:
        return {
            "status": "UNMATCHED_WEBHOOK",
            "verified": True,
            "ledger_appended": False,
            "record": webhook_record,
        }

    reconciliation = reconcile_order(
        payment_intent_id=str(binding["payment_intent_id"]),
        client=client,
        trigger=f"WEBHOOK:{webhook.get('event')}",
        path=target,
        payment_path=payment_path,
        now_ts=now,
    )
    return {
        "status": "RECONCILED",
        "verified": True,
        "record": webhook_record,
        "reconciliation": reconciliation,
    }


def reconcile_pending_orders(
    *,
    client: RevolutMerchantClient,
    path: str | None = None,
    payment_path: str | None = None,
    now_ts: float | int | None = None,
) -> list[Dict[str, Any]]:
    target = path or events_path()
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(target)
        bindings: Dict[str, Dict[str, Any]] = {}
        for row in records:
            if row.get("event_type") in {EVENT_ORDER_BOUND, EVENT_ORDER_RECOVERED}:
                bindings[str(row.get("payment_intent_id"))] = dict(row)
    results: list[Dict[str, Any]] = []
    for intent_id in sorted(bindings):
        history = payment_ledger.payment_history(intent_id, payment_path)
        final = [
            row
            for row in history
            if row.get("payment_state") in {
                "SETTLED",
                "FAILED",
                "REFUNDED",
                "CHARGEBACK",
            }
            and row.get("reconciliation_result") == "MATCHED"
        ]
        if final:
            continue
        results.append(
            reconcile_order(
                payment_intent_id=intent_id,
                client=client,
                trigger="RECOVERY_POLL",
                path=target,
                payment_path=payment_path,
                now_ts=now_ts,
            )
        )
    return results


def webhook_transport_status() -> Dict[str, Any]:
    """Expose the deliberate boundary: verification exists, HTTP ingress does not."""
    return {
        "signature_verifier": "IMPLEMENTED",
        "webhook_handler": "IMPLEMENTED",
        "inbound_http_transport": "NOT_CONFIGURED",
        "reason": (
            "Current Railway deployment is a worker-style process without a governed "
            "public HTTP webhook ingress. Poll reconciliation remains available."
        ),
    }
