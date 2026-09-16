from __future__ import annotations

import hashlib
import hmac
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import payment_ledger, revolut_merchant

SUBSCRIBER = "revolut-test-subscriber"
PRODUCT = "BINARY_TRADING"
PLAN = "BINARY_TRADING_BASIC"
AMOUNT = 1200
CURRENCY = "EUR"
BASE = 1_700_000_000
NOW_MS = BASE * 1000
SECRET = "sandbox-secret-not-real"
WEBHOOK_SECRET = "webhook-secret-not-real"


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    return {
        "adapter": tmp_path / "billing" / "revolut_merchant_events.jsonl",
        "payment": tmp_path / "billing" / "payment_ledger.jsonl",
    }


def _create_intent(payment_path: Path, intent_id: str = "intent-revolut-1") -> dict:
    return payment_ledger.create_payment_intent(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        plan_id=PLAN,
        amount_minor=AMOUNT,
        currency=CURRENCY,
        payment_method="FIAT",
        provider=revolut_merchant.PROVIDER,
        idempotency_key=f"create:{intent_id}",
        payment_intent_id=intent_id,
        audit_correlation_id=f"audit:{intent_id}",
        now_ts=BASE,
        path=str(payment_path),
    )["record"]


class FakeProvider:
    def __init__(self) -> None:
        self.environment = "sandbox"
        self.api_version = revolut_merchant.DEFAULT_API_VERSION
        self.orders_by_reference: list[dict] = []
        self.created: list[dict] = []
        self.retrieved: dict[str, dict] = {}
        self.payments: list[dict] = []
        self.raise_unavailable = False

    def find_orders_by_reference(self, reference: str):
        return [dict(row) for row in self.orders_by_reference]

    def create_order(self, **kwargs):
        self.created.append(dict(kwargs))
        intent_id = kwargs["merchant_reference"]
        return {
            "id": "order-1",
            "state": "pending",
            "amount": kwargs["amount_minor"],
            "currency": kwargs["currency"],
            "merchant_order_data": {"reference": intent_id},
        }

    def retrieve_order(self, order_id: str):
        if self.raise_unavailable:
            raise revolut_merchant.RevolutProviderUnavailable("provider unavailable")
        return dict(self.retrieved[order_id])

    def pay_saved_method(self, **kwargs):
        self.payments.append(dict(kwargs))
        return {
            "id": "payment-saved-1",
            "order_id": kwargs["revolut_order_id"],
            "state": "captured",
            "payment_method": {
                "id": kwargs["saved_payment_method_id"],
                "type": kwargs["saved_payment_method_type"],
            },
        }


def _bind(paths, provider: FakeProvider, intent_id="intent-revolut-1", customer_id=None):
    _create_intent(paths["payment"], intent_id)
    return revolut_merchant.create_order_for_intent(
        payment_intent_id=intent_id,
        client=provider,
        customer_id=customer_id,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        now_ts=BASE,
    )


def _completed_order(order_id="order-1", *, amount=AMOUNT, currency=CURRENCY):
    return {
        "id": order_id,
        "state": "completed",
        "amount": amount,
        "currency": currency,
        "updated_at": "2026-09-16T12:00:00Z",
        "completed_at": "2026-09-16T12:00:00Z",
        "merchant_order_data": {"reference": "intent-revolut-1"},
        "payments": [
            {
                "id": "payment-captured-1",
                "state": "captured",
                "amount": amount,
                "currency": currency,
            }
        ],
    }


def _signature(raw: bytes, timestamp: str, secret: str = WEBHOOK_SECRET) -> str:
    signed = b"v1." + timestamp.encode("utf-8") + b"." + raw
    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"v1={digest}"


class FakeResponse:
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


def test_client_defaults_to_sandbox_and_sends_versioned_bearer_headers() -> None:
    calls: list[dict] = []

    def request(method, url, **kwargs):
        calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse(200, {"orders": []})

    client = revolut_merchant.RevolutMerchantClient(
        secret_key=SECRET,
        request_fn=request,
        sleep_fn=lambda _seconds: None,
    )
    assert client.base_url == revolut_merchant.SANDBOX_BASE_URL
    assert client.safe_config()["secret_configured"] is True
    assert SECRET not in json.dumps(client.safe_config())
    client.find_orders_by_reference("intent-1")
    assert calls[0]["url"] == f"{revolut_merchant.SANDBOX_BASE_URL}/api/orders"
    assert calls[0]["headers"]["Authorization"] == f"Bearer {SECRET}"
    assert calls[0]["headers"]["Revolut-Api-Version"] == "2026-04-20"
    assert calls[0]["params"]["merchant_order_data_reference"] == "intent-1"


def test_production_client_requires_explicit_opt_in() -> None:
    with pytest.raises(revolut_merchant.RevolutMerchantError, match="explicit allow_production"):
        revolut_merchant.RevolutMerchantClient(
            secret_key=SECRET,
            environment="production",
        )
    client = revolut_merchant.RevolutMerchantClient(
        secret_key=SECRET,
        environment="production",
        allow_production=True,
    )
    assert client.base_url == revolut_merchant.PRODUCTION_BASE_URL


def test_transport_failure_redacts_secret_and_retries_bounded() -> None:
    calls = 0

    def request(_method, url, **_kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError(f"network error using {SECRET} at {url}")

    client = revolut_merchant.RevolutMerchantClient(
        secret_key=SECRET,
        request_fn=request,
        sleep_fn=lambda _seconds: None,
        max_retries=2,
    )
    with pytest.raises(revolut_merchant.RevolutProviderUnavailable) as exc:
        client.retrieve_order("order-1")
    assert calls == 3
    assert SECRET not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


def test_webhook_signature_validates_raw_bytes_multiple_signatures_and_timestamp() -> None:
    raw = b'{"event":"ORDER_COMPLETED","order_id":"order-1"}'
    timestamp = str(NOW_MS)
    valid = _signature(raw, timestamp)
    result = revolut_merchant.verify_webhook_signature(
        raw_body=raw,
        timestamp_header=timestamp,
        signature_header=f"v1={'0' * 64},{valid}",
        signing_secret=WEBHOOK_SECRET,
        now_ms=NOW_MS,
    )
    assert result["verified"] is True
    assert result["raw_event_hash"] == hashlib.sha256(raw).hexdigest()

    with pytest.raises(revolut_merchant.RevolutMerchantError, match="signature"):
        revolut_merchant.verify_webhook_signature(
            raw_body=raw + b" ",
            timestamp_header=timestamp,
            signature_header=valid,
            signing_secret=WEBHOOK_SECRET,
            now_ms=NOW_MS,
        )

    with pytest.raises(revolut_merchant.RevolutMerchantError, match="5-minute"):
        revolut_merchant.verify_webhook_signature(
            raw_body=raw,
            timestamp_header=timestamp,
            signature_header=valid,
            signing_secret=WEBHOOK_SECRET,
            now_ms=NOW_MS + revolut_merchant.WEBHOOK_TOLERANCE_MS + 1,
        )


def test_create_order_is_bound_once_and_uses_governed_intent_amount(paths) -> None:
    provider = FakeProvider()
    first = _bind(paths, provider)
    replay = revolut_merchant.create_order_for_intent(
        payment_intent_id="intent-revolut-1",
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        now_ts=BASE + 1,
    )
    assert first["status"] == "CREATED"
    assert replay["status"] == "EXISTS"
    assert len(provider.created) == 1
    assert provider.created[0]["amount_minor"] == AMOUNT
    assert provider.created[0]["currency"] == CURRENCY
    assert provider.created[0]["merchant_reference"] == "intent-revolut-1"
    assert len(revolut_merchant.load_events(str(paths["adapter"]))) == 1


def test_crash_recovery_reuses_provider_order_by_merchant_reference(paths) -> None:
    _create_intent(paths["payment"])
    provider = FakeProvider()
    provider.orders_by_reference = [
        {
            "id": "recovered-order",
            "state": "pending",
            "amount": AMOUNT,
            "currency": CURRENCY,
            "merchant_order_data": {"reference": "intent-revolut-1"},
        }
    ]
    result = revolut_merchant.create_order_for_intent(
        payment_intent_id="intent-revolut-1",
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        now_ts=BASE,
    )
    assert result["status"] == "RECOVERED"
    assert result["record"]["revolut_order_id"] == "recovered-order"
    assert provider.created == []


def test_multiple_recovered_orders_fail_closed(paths) -> None:
    _create_intent(paths["payment"])
    provider = FakeProvider()
    provider.orders_by_reference = [
        {
            "id": "order-a",
            "state": "pending",
            "amount": AMOUNT,
            "currency": CURRENCY,
            "merchant_order_data": {"reference": "intent-revolut-1"},
        },
        {
            "id": "order-b",
            "state": "pending",
            "amount": AMOUNT,
            "currency": CURRENCY,
            "merchant_order_data": {"reference": "intent-revolut-1"},
        },
    ]
    with pytest.raises(revolut_merchant.RevolutMerchantError, match="Multiple Revolut orders"):
        revolut_merchant.create_order_for_intent(
            payment_intent_id="intent-revolut-1",
            client=provider,
            path=str(paths["adapter"]),
            payment_path=str(paths["payment"]),
        )


def test_completed_order_becomes_exactly_one_settled_ledger_event(paths) -> None:
    provider = FakeProvider()
    _bind(paths, provider)
    provider.retrieved["order-1"] = _completed_order()
    first = revolut_merchant.reconcile_order(
        payment_intent_id="intent-revolut-1",
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        now_ts=BASE + 10,
    )
    replay = revolut_merchant.reconcile_order(
        payment_intent_id="intent-revolut-1",
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        now_ts=BASE + 20,
    )
    assert first["status"] == "SETTLED"
    assert replay["status"] in {"DUPLICATE", "DUPLICATE_PROVIDER_EVENT", "DUPLICATE_SETTLEMENT"}
    settlement = payment_ledger.settled_payment_record(
        "intent-revolut-1", str(paths["payment"])
    )
    assert settlement is not None
    assert settlement["provider_tx_ref"] == "payment-captured-1"
    matched = [
        row
        for row in payment_ledger.payment_history(
            "intent-revolut-1", str(paths["payment"])
        )
        if row.get("payment_state") == "SETTLED"
        and row.get("reconciliation_result") == "MATCHED"
    ]
    assert len(matched) == 1


def test_webhook_is_only_trigger_and_provider_pending_does_not_settle(paths) -> None:
    provider = FakeProvider()
    _bind(paths, provider)
    provider.retrieved["order-1"] = {
        "id": "order-1",
        "state": "processing",
        "amount": AMOUNT,
        "currency": CURRENCY,
        "updated_at": "2026-09-16T11:59:00Z",
        "payments": [{"id": "payment-pending", "state": "authorisation_started"}],
    }
    raw = b'{"event":"ORDER_COMPLETED","order_id":"order-1","merchant_order_ext_ref":"intent-revolut-1"}'
    timestamp = str(NOW_MS)
    result = revolut_merchant.process_verified_webhook(
        raw_body=raw,
        headers={
            "Revolut-Request-Timestamp": timestamp,
            "Revolut-Signature": _signature(raw, timestamp),
        },
        client=provider,
        signing_secret=WEBHOOK_SECRET,
        now_ms=NOW_MS,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert result["status"] == "RECONCILED"
    assert result["reconciliation"]["status"] == "PENDING"
    assert payment_ledger.settled_payment_record(
        "intent-revolut-1", str(paths["payment"])
    ) is None

    provider.retrieved["order-1"] = _completed_order()
    recovered = revolut_merchant.reconcile_order(
        payment_intent_id="intent-revolut-1",
        client=provider,
        trigger="RECOVERY_POLL",
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        now_ts=BASE + 100,
    )
    assert recovered["status"] == "SETTLED"


def test_duplicate_webhook_cannot_duplicate_settlement(paths) -> None:
    provider = FakeProvider()
    _bind(paths, provider)
    provider.retrieved["order-1"] = _completed_order()
    raw = b'{"event":"ORDER_COMPLETED","order_id":"order-1"}'
    timestamp = str(NOW_MS)
    headers = {
        "Revolut-Request-Timestamp": timestamp,
        "Revolut-Signature": _signature(raw, timestamp),
    }
    revolut_merchant.process_verified_webhook(
        raw_body=raw,
        headers=headers,
        client=provider,
        signing_secret=WEBHOOK_SECRET,
        now_ms=NOW_MS,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    revolut_merchant.process_verified_webhook(
        raw_body=raw,
        headers=headers,
        client=provider,
        signing_secret=WEBHOOK_SECRET,
        now_ms=NOW_MS,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    matched = [
        row
        for row in payment_ledger.payment_history(
            "intent-revolut-1", str(paths["payment"])
        )
        if row.get("payment_state") == "SETTLED"
        and row.get("reconciliation_result") == "MATCHED"
    ]
    assert len(matched) == 1
    webhook_rows = [
        row
        for row in revolut_merchant.load_events(str(paths["adapter"]))
        if row.get("event_type") == revolut_merchant.EVENT_WEBHOOK_VERIFIED
    ]
    assert len(webhook_rows) == 1


def test_unmatched_verified_webhook_never_creates_payment_truth(paths) -> None:
    provider = FakeProvider()
    raw = b'{"event":"ORDER_COMPLETED","order_id":"unknown-order"}'
    timestamp = str(NOW_MS)
    result = revolut_merchant.process_verified_webhook(
        raw_body=raw,
        headers={
            "Revolut-Request-Timestamp": timestamp,
            "Revolut-Signature": _signature(raw, timestamp),
        },
        client=provider,
        signing_secret=WEBHOOK_SECRET,
        now_ms=NOW_MS,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert result["status"] == "UNMATCHED_WEBHOOK"
    assert result["ledger_appended"] is False
    assert not paths["payment"].exists()


def test_provider_outage_records_adapter_unknown_without_fabricated_ledger_state(paths) -> None:
    provider = FakeProvider()
    _bind(paths, provider)
    provider.raise_unavailable = True
    before = len(payment_ledger.payment_history("intent-revolut-1", str(paths["payment"])))
    result = revolut_merchant.reconcile_order(
        payment_intent_id="intent-revolut-1",
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    after = len(payment_ledger.payment_history("intent-revolut-1", str(paths["payment"])))
    assert result["status"] == "PROVIDER_UNAVAILABLE"
    assert result["ledger_appended"] is False
    assert after == before


def test_provider_amount_mismatch_routes_to_ledger_contradiction(paths) -> None:
    provider = FakeProvider()
    _bind(paths, provider)
    provider.retrieved["order-1"] = _completed_order(amount=AMOUNT + 1)
    result = revolut_merchant.reconcile_order(
        payment_intent_id="intent-revolut-1",
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert result["status"] == "CONTRADICTORY"
    assert payment_ledger.settled_payment_record(
        "intent-revolut-1", str(paths["payment"])
    ) is None


def test_failed_and_cancelled_orders_are_not_settled(paths) -> None:
    for index, state in enumerate(("failed", "cancelled"), start=1):
        payment_path = paths["payment"].with_name(f"payment_{index}.jsonl")
        adapter_path = paths["adapter"].with_name(f"adapter_{index}.jsonl")
        provider = FakeProvider()
        intent_id = f"intent-{state}"
        _create_intent(payment_path, intent_id)
        revolut_merchant.create_order_for_intent(
            payment_intent_id=intent_id,
            client=provider,
            path=str(adapter_path),
            payment_path=str(payment_path),
        )
        provider.retrieved["order-1"] = {
            "id": "order-1",
            "state": state,
            "amount": AMOUNT,
            "currency": CURRENCY,
            "updated_at": f"2026-09-16T12:0{index}:00Z",
        }
        result = revolut_merchant.reconcile_order(
            payment_intent_id=intent_id,
            client=provider,
            path=str(adapter_path),
            payment_path=str(payment_path),
        )
        assert result["status"] == "FAILED"
        assert payment_ledger.settled_payment_record(intent_id, str(payment_path)) is None


def test_saved_method_recurring_requires_consent_and_stores_only_hashes(paths) -> None:
    provider = FakeProvider()
    _create_intent(paths["payment"])
    provider.retrieved["order-1"] = _completed_order()
    customer_id = "customer-opaque-id"
    method_id = "saved-method-opaque-id"
    consent = "consent-record-opaque-id"

    with pytest.raises(revolut_merchant.RevolutMerchantError, match="consent_reference"):
        revolut_merchant.charge_saved_payment_method(
            payment_intent_id="intent-revolut-1",
            customer_id=customer_id,
            saved_payment_method_id=method_id,
            saved_payment_method_type="card",
            consent_reference="",
            client=provider,
            path=str(paths["adapter"]),
            payment_path=str(paths["payment"]),
        )

    result = revolut_merchant.charge_saved_payment_method(
        payment_intent_id="intent-revolut-1",
        customer_id=customer_id,
        saved_payment_method_id=method_id,
        saved_payment_method_type="card",
        consent_reference=consent,
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        now_ts=BASE + 20,
    )
    assert result["status"] == "PAYMENT_INITIATED"
    assert provider.payments[0]["saved_payment_method_type"] == "card"
    assert result["reconciliation"]["status"] == "SETTLED"
    raw = paths["adapter"].read_text(encoding="utf-8")
    assert customer_id not in raw
    assert method_id not in raw
    assert consent not in raw
    assert hashlib.sha256(method_id.encode()).hexdigest() in raw


def test_recovery_poll_skips_final_intents_and_reconciles_nonfinal(paths) -> None:
    provider = FakeProvider()
    _bind(paths, provider)
    provider.retrieved["order-1"] = {
        "id": "order-1",
        "state": "pending",
        "amount": AMOUNT,
        "currency": CURRENCY,
        "updated_at": "2026-09-16T12:00:00Z",
    }
    first = revolut_merchant.reconcile_pending_orders(
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert len(first) == 1
    assert first[0]["status"] == "PENDING"

    provider.retrieved["order-1"] = _completed_order()
    second = revolut_merchant.reconcile_pending_orders(
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert len(second) == 1
    assert second[0]["status"] == "SETTLED"
    third = revolut_merchant.reconcile_pending_orders(
        client=provider,
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert third == []


def test_webhook_transport_truthfully_reports_not_configured() -> None:
    status = revolut_merchant.webhook_transport_status()
    assert status["signature_verifier"] == "IMPLEMENTED"
    assert status["webhook_handler"] == "IMPLEMENTED"
    assert status["inbound_http_transport"] == "NOT_CONFIGURED"
