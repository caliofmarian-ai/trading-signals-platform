from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))

from billing import (
    commercial_checkout,
    compliance_eligibility,
    revolut_merchant,
)


PRODUCT = "BINARY_TRADING"
PLAN = "BINARY_TRADING_BASIC"
PROVIDER = "REVOLUT_MERCHANT"


def _configured_contract(tmp_path: Path) -> Path:
    source = SEND_DIR / "config" / "billing_contract.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    product = payload["strategy_products"][0]
    plan = next(row for row in product["plans"] if row["plan_id"] == PLAN)
    plan["pricing"] = {
        "status": "CONFIGURED",
        "amount_minor": 1299,
        "currency": "EUR",
    }
    target = tmp_path / "billing_contract.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def _approved_eligibility(tmp_path: Path) -> Path:
    source = SEND_DIR / "config" / "compliance_eligibility.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    product = payload["products"][PRODUCT]
    for key in (
        "jurisdiction_scope",
        "product_eligibility",
        "commercial_catalog",
        "external_go_live_gate",
    ):
        product[key] = {
            "status": "APPROVED",
            "evidence_ref": f"test:{key}",
            "reason_code": "TEST_APPROVAL_EVIDENCE",
        }
    for provider in product["providers"].values():
        for key in ("business_eligibility", "provider_verification"):
            provider[key] = {
                "status": "APPROVED",
                "evidence_ref": f"test:{key}",
                "reason_code": "TEST_APPROVAL_EVIDENCE",
            }
    target = tmp_path / "compliance_eligibility.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def test_repository_default_is_fail_closed() -> None:
    decision = commercial_checkout.evaluate_commercial_checkout(
        strategy_product_id=PRODUCT,
        plan_id=PLAN,
        provider=PROVIDER,
        requested_amount_minor=1299,
        requested_currency="EUR",
    )

    assert decision["status"] == "BLOCKED"
    assert "CATALOG_PRICING_NOT_CONFIGURED" in decision["reason_codes"]
    assert decision["compliance"]["status"] == "BLOCKED"
    inputs = decision["compliance"]["inputs"]
    assert inputs["product_eligibility"]["status"] == "UNKNOWN"
    assert inputs["commercial_catalog"]["status"] == "BLOCKED"
    assert inputs["provider.business_eligibility"]["status"] == "UNKNOWN"


def test_eligibility_rejects_secret_bearing_configuration(tmp_path: Path) -> None:
    source = SEND_DIR / "config" / "compliance_eligibility.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["api_key"] = "must-never-be-here"
    target = tmp_path / "unsafe.json"
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        compliance_eligibility.ComplianceEligibilityError,
        match="secret-bearing",
    ):
        compliance_eligibility.load_eligibility_config(target)


def test_unknown_provider_fails_closed(tmp_path: Path) -> None:
    eligibility = _approved_eligibility(tmp_path)
    cfg = compliance_eligibility.load_eligibility_config(eligibility)
    result = compliance_eligibility.evaluate_paid_checkout(
        strategy_product_id=PRODUCT,
        provider="UNCONFIGURED_PROVIDER",
        config=cfg,
    )
    assert result["status"] == "BLOCKED"
    assert result["reason_codes"] == ["PROVIDER_ELIGIBILITY_NOT_CONFIGURED"]


def test_approved_gate_uses_governed_catalog_price(tmp_path: Path) -> None:
    contract = _configured_contract(tmp_path)
    eligibility = _approved_eligibility(tmp_path)
    payment_path = tmp_path / "billing" / "payment_ledger.jsonl"

    result = commercial_checkout.create_paid_payment_intent(
        subscriber_ref="subscriber-test",
        strategy_product_id=PRODUCT,
        plan_id=PLAN,
        provider=PROVIDER,
        payment_method="FIAT",
        idempotency_key="checkout:approved:1",
        requested_amount_minor=1299,
        requested_currency="EUR",
        payment_path=str(payment_path),
        contract_path=contract,
        eligibility_path=eligibility,
        now_ts=1_800_000_000,
    )

    assert result["status"] == "CREATED"
    assert result["checkout_decision"]["status"] == "APPROVED"
    assert result["record"]["amount_minor"] == 1299
    assert result["record"]["currency"] == "EUR"
    assert result["record"]["provider"] == PROVIDER


def test_requested_price_mismatch_blocks_before_ledger_write(tmp_path: Path) -> None:
    contract = _configured_contract(tmp_path)
    eligibility = _approved_eligibility(tmp_path)
    payment_path = tmp_path / "billing" / "payment_ledger.jsonl"

    with pytest.raises(commercial_checkout.CommercialCheckoutBlocked) as exc:
        commercial_checkout.create_paid_payment_intent(
            subscriber_ref="subscriber-test",
            strategy_product_id=PRODUCT,
            plan_id=PLAN,
            provider=PROVIDER,
            payment_method="FIAT",
            idempotency_key="checkout:mismatch:1",
            requested_amount_minor=999,
            requested_currency="EUR",
            payment_path=str(payment_path),
            contract_path=contract,
            eligibility_path=eligibility,
        )

    assert "REQUEST_AMOUNT_DIFFERS_FROM_GOVERNED_CATALOG" in exc.value.decision[
        "reason_codes"
    ]
    assert not payment_path.exists()


class _ForbiddenProvider:
    environment = "sandbox"
    api_version = "2026-04-20"

    def find_orders_by_reference(self, _reference):
        raise AssertionError("Provider must not be called before compliance approval")

    def create_order(self, **_kwargs):
        raise AssertionError("Provider must not be called before compliance approval")


class _ApprovedProvider:
    environment = "sandbox"
    api_version = "2026-04-20"

    def __init__(self):
        self.created = 0

    def find_orders_by_reference(self, _reference):
        return []

    def create_order(self, *, amount_minor, currency, merchant_reference, customer_id=None):
        self.created += 1
        return {
            "id": "order-approved-1",
            "state": "pending",
            "amount": amount_minor,
            "currency": currency,
            "merchant_order_ext_ref": merchant_reference,
            "customer_id": customer_id,
        }


def test_revolut_convenience_path_cannot_bypass_default_gate(tmp_path: Path) -> None:
    payment_path = tmp_path / "billing" / "payment_ledger.jsonl"
    adapter_path = tmp_path / "billing" / "revolut_events.jsonl"

    with pytest.raises(commercial_checkout.CommercialCheckoutBlocked):
        revolut_merchant.create_payment_intent_and_order(
            subscriber_ref="subscriber-test",
            strategy_product_id=PRODUCT,
            plan_id=PLAN,
            amount_minor=1299,
            currency="EUR",
            idempotency_key="revolut:blocked:1",
            client=_ForbiddenProvider(),
            path=str(adapter_path),
            payment_path=str(payment_path),
        )

    assert not payment_path.exists()
    assert not adapter_path.exists()


def test_revolut_convenience_path_proceeds_only_after_explicit_approval(
    tmp_path: Path,
) -> None:
    contract = _configured_contract(tmp_path)
    eligibility = _approved_eligibility(tmp_path)
    payment_path = tmp_path / "billing" / "payment_ledger.jsonl"
    adapter_path = tmp_path / "billing" / "revolut_events.jsonl"
    provider = _ApprovedProvider()

    result = revolut_merchant.create_payment_intent_and_order(
        subscriber_ref="subscriber-test",
        strategy_product_id=PRODUCT,
        plan_id=PLAN,
        amount_minor=1299,
        currency="EUR",
        idempotency_key="revolut:approved:1",
        client=provider,
        path=str(adapter_path),
        payment_path=str(payment_path),
        contract_path=contract,
        eligibility_path=eligibility,
        now_ts=1_800_000_000,
    )

    assert result["status"] == "READY"
    assert provider.created == 1
    assert result["payment_intent"]["checkout_decision"]["status"] == "APPROVED"
    assert result["payment_intent"]["record"]["amount_minor"] == 1299
    assert result["revolut_order"]["record"]["revolut_order_id"] == "order-approved-1"
