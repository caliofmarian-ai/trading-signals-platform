from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

SEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT_PATH = SEND_ROOT / "config" / "billing_contract.json"
DEFAULT_STRATEGY_CATALOG_PATH = SEND_ROOT / "config" / "strategy_catalog.json"
DEFAULT_CHANNEL_CONFIG_PATH = SEND_ROOT / "config" / "channel_config.json"

_REQUIRED_IDENTIFIER_NAMES = frozenset(
    {
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
    }
)
_REQUIRED_TRUTH_LAYERS = frozenset(
    {"PAYMENT", "SUBSCRIPTION", "ENTITLEMENT", "TELEGRAM_MEMBERSHIP"}
)
_SECRET_KEY_MARKERS = ("secret", "token", "password", "api_key", "private_key")


class BillingContractError(RuntimeError):
    """Raised when the shared billing contract is absent, ambiguous, or unsafe."""


def _load_json_object(path: Path, *, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BillingContractError(f"Unable to read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise BillingContractError(f"{label} must be a JSON object: {path}")
    return payload


def _string_list(value: Any, *, label: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise BillingContractError(f"{label} must be a list")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise BillingContractError(f"{label} must contain non-empty strings")
        text = item.strip()
        if text in normalized:
            raise BillingContractError(f"{label} contains duplicate value: {text}")
        normalized.append(text)
    if not normalized and not allow_empty:
        raise BillingContractError(f"{label} must not be empty")
    return normalized


def _require_keys(payload: Mapping[str, Any], required: Iterable[str], *, label: str) -> None:
    missing = sorted(set(required) - set(payload))
    if missing:
        raise BillingContractError(f"{label} missing required keys: {missing}")


def _reject_secret_material(value: Any, *, path: str = "contract") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in _SECRET_KEY_MARKERS):
                raise BillingContractError(
                    f"Billing contract must not contain secret-bearing field: {path}.{key}"
                )
            _reject_secret_material(nested, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_secret_material(nested, path=f"{path}[{index}]")


def _enum_map(payload: Mapping[str, Any]) -> Dict[str, list[str]]:
    raw = payload.get("enums")
    if not isinstance(raw, dict) or not raw:
        raise BillingContractError("contract.enums must be a non-empty object")
    result: Dict[str, list[str]] = {}
    for name, values in raw.items():
        if not isinstance(name, str) or not name.strip():
            raise BillingContractError("contract.enums contains an invalid enum name")
        result[name] = _string_list(values, label=f"contract.enums.{name}")
    return result


def _validate_identifiers(payload: Mapping[str, Any]) -> None:
    raw = payload.get("identifier_contracts")
    if not isinstance(raw, dict):
        raise BillingContractError("contract.identifier_contracts must be an object")
    missing = sorted(_REQUIRED_IDENTIFIER_NAMES - set(raw))
    if missing:
        raise BillingContractError(f"Missing shared billing identifiers: {missing}")

    for name, spec in raw.items():
        if not isinstance(spec, dict):
            raise BillingContractError(f"identifier_contracts.{name} must be an object")
        _require_keys(spec, {"type", "required"}, label=f"identifier_contracts.{name}")
        if spec["type"] not in {"opaque_string", "enum_string", "positive_integer"}:
            raise BillingContractError(f"Unsupported identifier type for {name}: {spec['type']}")
        if not isinstance(spec["required"], bool):
            raise BillingContractError(f"identifier_contracts.{name}.required must be boolean")
        if spec["type"] == "positive_integer" and spec.get("monotonic") not in {None, True}:
            raise BillingContractError(
                f"identifier_contracts.{name}.monotonic may only be true when supplied"
            )


def _validate_strategy_product_refs(
    payload: Mapping[str, Any],
    *,
    strategy_catalog: Mapping[str, Any],
    channel_config: Mapping[str, Any],
    enums: Mapping[str, list[str]],
) -> None:
    scope = payload.get("scope")
    if not isinstance(scope, dict):
        raise BillingContractError("contract.scope must be an object")
    current_product_ids = _string_list(
        scope.get("current_strategy_product_ids"),
        label="contract.scope.current_strategy_product_ids",
    )
    if scope.get("future_strategy_products_allowed_in_current_runtime") is not False:
        raise BillingContractError(
            "future_strategy_products_allowed_in_current_runtime must remain false in current scope"
        )

    catalog_rows = strategy_catalog.get("strategies")
    if not isinstance(catalog_rows, list):
        raise BillingContractError("strategy_catalog.strategies must be a list")
    available_strategy_refs = {
        str(row.get("id")): row
        for row in catalog_rows
        if isinstance(row, dict) and row.get("availability") == "AVAILABLE"
    }

    products = payload.get("strategy_products")
    if not isinstance(products, list) or not products:
        raise BillingContractError("contract.strategy_products must be a non-empty list")

    seen_product_ids: set[str] = set()
    seen_plan_ids: set[str] = set()
    plan_tiers = set(enums.get("plan_tier") or [])
    cadence_values = set(enums.get("billing_cadence") or [])
    membership_models = set(enums.get("channel_membership_model") or [])
    pricing_statuses = set(enums.get("pricing_status") or [])

    if not plan_tiers:
        raise BillingContractError("plan_tier enum must be defined")

    for product in products:
        if not isinstance(product, dict):
            raise BillingContractError("Each strategy product must be an object")
        _require_keys(
            product,
            {
                "strategy_product_id",
                "strategy_catalog_ref",
                "trade_type",
                "channel_membership_model",
                "plans",
            },
            label="strategy_product",
        )
        product_id = str(product["strategy_product_id"])
        if product_id in seen_product_ids:
            raise BillingContractError(f"Duplicate strategy_product_id: {product_id}")
        seen_product_ids.add(product_id)
        if product_id not in current_product_ids:
            raise BillingContractError(
                f"Strategy product is outside current billing scope: {product_id}"
            )

        strategy_ref = str(product["strategy_catalog_ref"])
        strategy_row = available_strategy_refs.get(strategy_ref)
        if strategy_row is None:
            raise BillingContractError(
                f"Billing product must reference an AVAILABLE strategy catalog row: {strategy_ref}"
            )
        if str(strategy_row.get("trade_type")) != str(product["trade_type"]):
            raise BillingContractError(
                f"Trade type mismatch for {product_id}: billing={product['trade_type']} "
                f"strategy_catalog={strategy_row.get('trade_type')}"
            )
        if product["channel_membership_model"] not in membership_models:
            raise BillingContractError(
                f"Unknown channel membership model: {product['channel_membership_model']}"
            )

        plans = product.get("plans")
        if not isinstance(plans, list) or not plans:
            raise BillingContractError(f"{product_id}.plans must be a non-empty list")
        seen_tiers: set[str] = set()
        for plan in plans:
            if not isinstance(plan, dict):
                raise BillingContractError(f"{product_id} plan must be an object")
            _require_keys(
                plan,
                {
                    "plan_id",
                    "tier",
                    "billing_cadence",
                    "requires_payment",
                    "pricing",
                    "telegram_destination_ref",
                    "signal_limit_ref",
                },
                label=f"{product_id}.plan",
            )
            plan_id = str(plan["plan_id"])
            tier = str(plan["tier"])
            if plan_id in seen_plan_ids:
                raise BillingContractError(f"Duplicate plan_id: {plan_id}")
            seen_plan_ids.add(plan_id)
            if tier in seen_tiers:
                raise BillingContractError(f"Duplicate plan tier for {product_id}: {tier}")
            seen_tiers.add(tier)
            if tier not in plan_tiers:
                raise BillingContractError(f"Unknown plan tier: {tier}")

            destination_ref = plan["telegram_destination_ref"]
            limit_ref = plan["signal_limit_ref"]
            if not isinstance(destination_ref, str) or destination_ref not in channel_config:
                raise BillingContractError(
                    f"Unknown Telegram destination config reference for {plan_id}: {destination_ref}"
                )
            if not isinstance(limit_ref, str) or limit_ref not in channel_config:
                raise BillingContractError(
                    f"Unknown signal-limit config reference for {plan_id}: {limit_ref}"
                )
            if isinstance(destination_ref, (int, float)):
                raise BillingContractError("Plan catalog must reference channel config keys, not IDs")

            requires_payment = plan["requires_payment"]
            if not isinstance(requires_payment, bool):
                raise BillingContractError(f"{plan_id}.requires_payment must be boolean")
            cadence = plan["billing_cadence"]
            pricing = plan["pricing"]
            if not isinstance(pricing, dict):
                raise BillingContractError(f"{plan_id}.pricing must be an object")
            _require_keys(
                pricing,
                {"status", "amount_minor", "currency"},
                label=f"{plan_id}.pricing",
            )
            status = pricing["status"]
            if status not in pricing_statuses:
                raise BillingContractError(f"Unknown pricing status for {plan_id}: {status}")

            if requires_payment:
                if cadence not in cadence_values:
                    raise BillingContractError(
                        f"Paid plan {plan_id} must use a governed billing cadence"
                    )
                if status == "NOT_APPLICABLE":
                    raise BillingContractError(
                        f"Paid plan {plan_id} cannot have NOT_APPLICABLE pricing"
                    )
            else:
                if cadence is not None:
                    raise BillingContractError(
                        f"Non-payment plan {plan_id} must not carry a billing cadence"
                    )
                if status != "NOT_APPLICABLE":
                    raise BillingContractError(
                        f"Non-payment plan {plan_id} must use NOT_APPLICABLE pricing"
                    )

            if status in {"NOT_APPLICABLE", "NOT_CONFIGURED"}:
                if pricing["amount_minor"] is not None or pricing["currency"] is not None:
                    raise BillingContractError(
                        f"Unconfigured pricing for {plan_id} must not invent amount/currency"
                    )
            elif status == "CONFIGURED":
                amount = pricing["amount_minor"]
                currency = pricing["currency"]
                if not isinstance(amount, int) or amount < 0:
                    raise BillingContractError(
                        f"Configured pricing amount for {plan_id} must be a non-negative integer"
                    )
                if not isinstance(currency, str) or len(currency.strip()) != 3:
                    raise BillingContractError(
                        f"Configured pricing currency for {plan_id} must be a 3-letter code"
                    )

        if seen_tiers != plan_tiers:
            raise BillingContractError(
                f"{product_id} must define exactly one plan for every governed tier: "
                f"expected={sorted(plan_tiers)} actual={sorted(seen_tiers)}"
            )

    if seen_product_ids != set(current_product_ids):
        raise BillingContractError(
            "Current strategy product scope and product catalog must match exactly"
        )


def validate_billing_contract(
    payload: Mapping[str, Any],
    *,
    strategy_catalog: Mapping[str, Any] | None = None,
    channel_config: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate and return a detached billing-contract dictionary.

    Validation is deliberately fail-closed. The billing contract may reference
    current strategy/distribution configuration, but it must not duplicate live
    channel IDs, invent pricing, or admit unavailable future strategy families.
    """

    if not isinstance(payload, Mapping):
        raise BillingContractError("Billing contract must be a mapping")
    _require_keys(
        payload,
        {
            "schema_version",
            "contract_id",
            "scope",
            "truth_layers",
            "identifier_contracts",
            "enums",
            "strategy_products",
            "separation_invariants",
        },
        label="billing_contract",
    )
    if str(payload["contract_id"]) != "tsp-billing-shared-contracts":
        raise BillingContractError("Unexpected billing contract_id")
    if not str(payload["schema_version"]).strip():
        raise BillingContractError("schema_version must be non-empty")

    truth_layers = set(_string_list(payload["truth_layers"], label="contract.truth_layers"))
    if truth_layers != _REQUIRED_TRUTH_LAYERS:
        raise BillingContractError(
            f"Billing truth layers must remain separated: {sorted(_REQUIRED_TRUTH_LAYERS)}"
        )

    _validate_identifiers(payload)
    enums = _enum_map(payload)
    _string_list(
        payload["separation_invariants"],
        label="contract.separation_invariants",
    )
    _reject_secret_material(payload)

    strategy_catalog = strategy_catalog or _load_json_object(
        DEFAULT_STRATEGY_CATALOG_PATH, label="strategy_catalog"
    )
    channel_config = channel_config or _load_json_object(
        DEFAULT_CHANNEL_CONFIG_PATH, label="channel_config"
    )
    _validate_strategy_product_refs(
        payload,
        strategy_catalog=strategy_catalog,
        channel_config=channel_config,
        enums=enums,
    )
    return json.loads(json.dumps(payload))


def load_billing_contract(path: str | Path | None = None) -> Dict[str, Any]:
    contract_path = Path(path) if path is not None else DEFAULT_CONTRACT_PATH
    payload = _load_json_object(contract_path, label="billing_contract")
    return validate_billing_contract(payload)


def identifier_names(contract: Mapping[str, Any] | None = None) -> tuple[str, ...]:
    payload = contract or load_billing_contract()
    identifiers = payload.get("identifier_contracts")
    if not isinstance(identifiers, dict):
        raise BillingContractError("identifier_contracts unavailable")
    return tuple(identifiers.keys())


def enum_values(name: str, contract: Mapping[str, Any] | None = None) -> tuple[str, ...]:
    payload = contract or load_billing_contract()
    enums = payload.get("enums")
    if not isinstance(enums, dict) or name not in enums:
        raise BillingContractError(f"Unknown billing enum: {name}")
    return tuple(_string_list(enums[name], label=f"contract.enums.{name}"))


def get_strategy_product(
    strategy_product_id: str,
    contract: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    payload = contract or load_billing_contract()
    for product in payload.get("strategy_products", []):
        if isinstance(product, dict) and product.get("strategy_product_id") == strategy_product_id:
            return json.loads(json.dumps(product))
    raise BillingContractError(f"Unknown strategy_product_id: {strategy_product_id}")


def get_plan(plan_id: str, contract: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    payload = contract or load_billing_contract()
    for product in payload.get("strategy_products", []):
        if not isinstance(product, dict):
            continue
        for plan in product.get("plans", []):
            if isinstance(plan, dict) and plan.get("plan_id") == plan_id:
                return json.loads(json.dumps(plan))
    raise BillingContractError(f"Unknown plan_id: {plan_id}")
