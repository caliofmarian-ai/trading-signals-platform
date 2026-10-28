from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from billing import compliance_eligibility, contracts, payment_ledger


class CommercialCheckoutError(RuntimeError):
    """Raised when paid commercial checkout cannot proceed safely."""


class CommercialCheckoutBlocked(CommercialCheckoutError):
    """Raised when checkout is fail-closed by governed eligibility/catalog evidence."""

    def __init__(self, decision: Mapping[str, Any]):
        self.decision = dict(decision)
        reasons = ",".join(str(x) for x in decision.get("reason_codes", []))
        super().__init__(
            "Paid commercial checkout is blocked"
            + (f": {reasons}" if reasons else "")
        )


def _product_plan(
    *,
    strategy_product_id: str,
    plan_id: str,
    contract: Mapping[str, Any],
) -> Dict[str, Any]:
    try:
        product = contracts.get_strategy_product(strategy_product_id, contract)
    except contracts.BillingContractError as exc:
        raise CommercialCheckoutError(str(exc)) from exc
    matches = [
        plan
        for plan in product.get("plans", [])
        if isinstance(plan, Mapping) and plan.get("plan_id") == plan_id
    ]
    if len(matches) != 1:
        raise CommercialCheckoutError(
            f"plan_id {plan_id} is not owned by strategy_product_id {strategy_product_id}"
        )
    return dict(matches[0])


def _catalog_pricing(plan: Mapping[str, Any]) -> Dict[str, Any]:
    pricing = plan.get("pricing")
    if not isinstance(pricing, Mapping):
        return {
            "status": "NOT_CONFIGURED",
            "amount_minor": None,
            "currency": None,
        }
    status = str(pricing.get("status") or "NOT_CONFIGURED").upper()
    amount = pricing.get("amount_minor")
    currency = pricing.get("currency")
    return {
        "status": status,
        "amount_minor": amount,
        "currency": currency,
    }


def evaluate_commercial_checkout(
    *,
    strategy_product_id: str,
    plan_id: str,
    provider: str,
    requested_amount_minor: int | None = None,
    requested_currency: str | None = None,
    contract_path: str | Path | None = None,
    eligibility_path: str | Path | None = None,
) -> Dict[str, Any]:
    contract = contracts.load_billing_contract(contract_path)
    plan = _product_plan(
        strategy_product_id=strategy_product_id,
        plan_id=plan_id,
        contract=contract,
    )
    if not bool(plan.get("requires_payment")):
        return {
            "status": "BLOCKED",
            "strategy_product_id": strategy_product_id,
            "plan_id": plan_id,
            "provider": str(provider or "").upper(),
            "reason_codes": ["PAID_CHECKOUT_REQUIRES_PAID_PLAN"],
            "catalog_pricing": _catalog_pricing(plan),
            "compliance": None,
        }

    compliance_cfg = compliance_eligibility.load_eligibility_config(
        eligibility_path
    )
    compliance = compliance_eligibility.evaluate_paid_checkout(
        strategy_product_id=strategy_product_id,
        provider=provider,
        config=compliance_cfg,
    )
    pricing = _catalog_pricing(plan)

    reasons = list(compliance.get("reason_codes") or [])
    if pricing["status"] != "CONFIGURED":
        reasons.append("CATALOG_PRICING_NOT_CONFIGURED")
    amount = pricing.get("amount_minor")
    currency = pricing.get("currency")
    if pricing["status"] == "CONFIGURED":
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            reasons.append("CATALOG_AMOUNT_INVALID")
        if not isinstance(currency, str) or not currency.strip():
            reasons.append("CATALOG_CURRENCY_INVALID")
        elif requested_currency is not None and (
            str(requested_currency).strip().upper() != currency.strip().upper()
        ):
            reasons.append("REQUEST_CURRENCY_DIFFERS_FROM_GOVERNED_CATALOG")
        if requested_amount_minor is not None and requested_amount_minor != amount:
            reasons.append("REQUEST_AMOUNT_DIFFERS_FROM_GOVERNED_CATALOG")

    reasons = list(dict.fromkeys(reasons))
    status = (
        "APPROVED"
        if compliance.get("status") == "APPROVED"
        and pricing["status"] == "CONFIGURED"
        and not reasons
        else "BLOCKED"
    )

    return {
        "status": status,
        "strategy_product_id": strategy_product_id,
        "plan_id": plan_id,
        "provider": str(provider or "").strip().upper(),
        "reason_codes": reasons,
        "catalog_pricing": pricing,
        "compliance": compliance,
    }


def create_paid_payment_intent(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    plan_id: str,
    provider: str,
    payment_method: str,
    idempotency_key: str,
    requested_amount_minor: int | None = None,
    requested_currency: str | None = None,
    payment_intent_id: str | None = None,
    audit_correlation_id: str | None = None,
    now_ts: float | int | None = None,
    payment_path: str | None = None,
    contract_path: str | Path | None = None,
    eligibility_path: str | Path | None = None,
) -> Dict[str, Any]:
    decision = evaluate_commercial_checkout(
        strategy_product_id=strategy_product_id,
        plan_id=plan_id,
        provider=provider,
        requested_amount_minor=requested_amount_minor,
        requested_currency=requested_currency,
        contract_path=contract_path,
        eligibility_path=eligibility_path,
    )
    if decision["status"] != "APPROVED":
        raise CommercialCheckoutBlocked(decision)

    pricing = decision["catalog_pricing"]
    result = payment_ledger.create_payment_intent(
        subscriber_ref=subscriber_ref,
        strategy_product_id=strategy_product_id,
        plan_id=plan_id,
        amount_minor=int(pricing["amount_minor"]),
        currency=str(pricing["currency"]),
        payment_method=payment_method,
        provider=provider,
        idempotency_key=idempotency_key,
        payment_intent_id=payment_intent_id,
        audit_correlation_id=audit_correlation_id,
        now_ts=now_ts,
        path=payment_path,
    )
    return {
        **result,
        "checkout_decision": decision,
    }
