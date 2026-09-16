"""Shared billing-domain contract access.

The machine-readable authority lives in ``send/config/billing_contract.json``.
Billing implementation lanes must consume that contract rather than redefining
shared identifiers, enums, product IDs, plan IDs, or catalog mappings.
"""

from billing.contracts import (
    BillingContractError,
    enum_values,
    get_plan,
    get_strategy_product,
    identifier_names,
    load_billing_contract,
    validate_billing_contract,
)

__all__ = [
    "BillingContractError",
    "enum_values",
    "get_plan",
    "get_strategy_product",
    "identifier_names",
    "load_billing_contract",
    "validate_billing_contract",
]
