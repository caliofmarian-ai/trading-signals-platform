from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import contracts


CONTRACT_PATH = SEND_ROOT / "config" / "billing_contract.json"
STRATEGY_CATALOG_PATH = SEND_ROOT / "config" / "strategy_catalog.json"
CHANNEL_CONFIG_PATH = SEND_ROOT / "config" / "channel_config.json"


def _raw_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _strategy_catalog() -> dict:
    return json.loads(STRATEGY_CATALOG_PATH.read_text(encoding="utf-8"))


def _channel_config() -> dict:
    return json.loads(CHANNEL_CONFIG_PATH.read_text(encoding="utf-8"))


def test_contract_loads_and_exposes_one_current_binary_product() -> None:
    payload = contracts.load_billing_contract()

    assert payload["scope"]["current_strategy_product_ids"] == ["BINARY_TRADING"]
    assert payload["scope"]["future_strategy_products_allowed_in_current_runtime"] is False
    assert len(payload["strategy_products"]) == 1
    binary = contracts.get_strategy_product("BINARY_TRADING", payload)
    assert binary["strategy_catalog_ref"] == "binary_canonical"
    assert binary["trade_type"] == "BINARY_OPTIONS"
    assert binary["channel_membership_model"] == "EXCLUSIVE"


def test_plan_tiers_match_existing_distribution_tiers_without_copying_limits() -> None:
    payload = contracts.load_billing_contract()
    binary = contracts.get_strategy_product("BINARY_TRADING", payload)
    plans = binary["plans"]

    assert {plan["tier"] for plan in plans} == {"FREE", "BASIC", "PRO", "ELITE"}
    assert len({plan["plan_id"] for plan in plans}) == 4

    channel_config = _channel_config()
    for plan in plans:
        assert isinstance(plan["telegram_destination_ref"], str)
        assert plan["telegram_destination_ref"] in channel_config
        assert isinstance(plan["signal_limit_ref"], str)
        assert plan["signal_limit_ref"] in channel_config
        assert "channel_id" not in plan
        assert "signal_limit" not in plan


def test_paid_plan_prices_are_explicitly_unconfigured_not_invented() -> None:
    payload = contracts.load_billing_contract()
    binary = contracts.get_strategy_product("BINARY_TRADING", payload)

    free = next(plan for plan in binary["plans"] if plan["tier"] == "FREE")
    assert free["requires_payment"] is False
    assert free["billing_cadence"] is None
    assert free["pricing"] == {
        "status": "NOT_APPLICABLE",
        "amount_minor": None,
        "currency": None,
    }

    paid = [plan for plan in binary["plans"] if plan["tier"] != "FREE"]
    assert paid
    for plan in paid:
        assert plan["requires_payment"] is True
        assert plan["billing_cadence"] == "MONTHLY"
        assert plan["pricing"] == {
            "status": "NOT_CONFIGURED",
            "amount_minor": None,
            "currency": None,
        }


def test_future_unavailable_strategy_is_not_admitted_to_billing_scope() -> None:
    payload = contracts.load_billing_contract()
    strategy_catalog = _strategy_catalog()

    unavailable_ids = {
        row["id"]
        for row in strategy_catalog["strategies"]
        if row.get("availability") != "AVAILABLE"
    }
    billing_strategy_refs = {
        product["strategy_catalog_ref"] for product in payload["strategy_products"]
    }

    assert "forex_future" in unavailable_ids
    assert billing_strategy_refs.isdisjoint(unavailable_ids)


def test_shared_identifier_contract_contains_required_cross_lane_ids() -> None:
    payload = contracts.load_billing_contract()
    names = set(contracts.identifier_names(payload))

    assert {
        "subscriber_ref",
        "strategy_product_id",
        "plan_id",
        "subscription_id",
        "payment_intent_id",
        "provider_event_id",
        "provider_tx_ref",
        "case_id",
        "entitlement_id",
        "entitlement_version",
        "reconciliation_id",
        "audit_correlation_id",
    }.issubset(names)
    assert payload["identifier_contracts"]["entitlement_version"]["monotonic"] is True


def test_truth_layers_and_owner_approved_policy_names_remain_distinct() -> None:
    payload = contracts.load_billing_contract()

    assert set(payload["truth_layers"]) == {
        "PAYMENT",
        "SUBSCRIPTION",
        "ENTITLEMENT",
        "TELEGRAM_MEMBERSHIP",
    }
    assert set(contracts.enum_values("named_policy_state", payload)) == {
        "GRACE_HOLD",
        "INTENT_PAYMENT_PENDING",
        "CANCELED_AT_PERIOD_END",
        "CHARGEBACK_OPEN",
        "IN_SYNC",
        "ACCESS_LEAK_RISK",
    }


def test_contract_rejects_future_strategy_activation() -> None:
    payload = _raw_contract()
    payload["scope"]["current_strategy_product_ids"].append("FOREX_TRADING")
    payload["strategy_products"].append(
        {
            "strategy_product_id": "FOREX_TRADING",
            "strategy_catalog_ref": "forex_future",
            "trade_type": "FOREX",
            "channel_membership_model": "EXCLUSIVE",
            "plans": copy.deepcopy(payload["strategy_products"][0]["plans"]),
        }
    )

    with pytest.raises(contracts.BillingContractError):
        contracts.validate_billing_contract(
            payload,
            strategy_catalog=_strategy_catalog(),
            channel_config=_channel_config(),
        )


def test_contract_rejects_invented_price_when_status_is_not_configured() -> None:
    payload = _raw_contract()
    paid_plan = payload["strategy_products"][0]["plans"][1]
    paid_plan["pricing"]["amount_minor"] = 999
    paid_plan["pricing"]["currency"] = "EUR"

    with pytest.raises(contracts.BillingContractError):
        contracts.validate_billing_contract(
            payload,
            strategy_catalog=_strategy_catalog(),
            channel_config=_channel_config(),
        )


def test_contract_rejects_channel_id_copy_instead_of_config_reference() -> None:
    payload = _raw_contract()
    payload["strategy_products"][0]["plans"][0]["telegram_destination_ref"] = -1003510282695

    with pytest.raises(contracts.BillingContractError):
        contracts.validate_billing_contract(
            payload,
            strategy_catalog=_strategy_catalog(),
            channel_config=_channel_config(),
        )


def test_contract_rejects_secret_bearing_fields() -> None:
    payload = _raw_contract()
    payload["provider_api_key"] = "must-not-live-here"

    with pytest.raises(contracts.BillingContractError):
        contracts.validate_billing_contract(
            payload,
            strategy_catalog=_strategy_catalog(),
            channel_config=_channel_config(),
        )


def test_contract_rejects_missing_shared_identifier() -> None:
    payload = _raw_contract()
    payload["identifier_contracts"].pop("payment_intent_id")

    with pytest.raises(contracts.BillingContractError):
        contracts.validate_billing_contract(
            payload,
            strategy_catalog=_strategy_catalog(),
            channel_config=_channel_config(),
        )
