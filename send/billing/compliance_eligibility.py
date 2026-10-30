from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

SEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = SEND_ROOT / "config" / "compliance_eligibility.json"

GATE_STATES = frozenset({"UNKNOWN", "BLOCKED", "APPROVED"})
AUTHORITY = "EXTERNAL_EVIDENCE_ONLY"

_REQUIRED_PRODUCT_GATES = (
    "jurisdiction_scope",
    "product_eligibility",
    "commercial_catalog",
    "external_go_live_gate",
)
_REQUIRED_PROVIDER_GATES = (
    "business_eligibility",
    "provider_verification",
)
_SECRET_MARKERS = ("secret", "password", "token", "api_key", "private_key")


class ComplianceEligibilityError(RuntimeError):
    """Raised when compliance eligibility evidence is absent, ambiguous or unsafe."""


def config_path() -> Path:
    """Return the repository-versioned eligibility authority.

    Production eligibility is intentionally not environment-overridable: an
    APPROVED transition must arrive through a reviewed repository config change.
    Explicit path arguments remain available to deterministic tests only.
    """
    return DEFAULT_CONFIG_PATH


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComplianceEligibilityError(f"{label} must be a non-empty string")
    return value.strip()


def _reject_secret_material(value: Any, *, path: str = "eligibility") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in _SECRET_MARKERS):
                raise ComplianceEligibilityError(
                    f"Compliance eligibility must not contain secret-bearing field: {path}.{key}"
                )
            _reject_secret_material(nested, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_secret_material(nested, path=f"{path}[{index}]")


def _gate_entry(value: Any, *, label: str) -> Dict[str, str]:
    if not isinstance(value, Mapping):
        raise ComplianceEligibilityError(f"{label} must be an object")
    status = _nonempty(value.get("status"), label=f"{label}.status").upper()
    if status not in GATE_STATES:
        raise ComplianceEligibilityError(f"Unsupported {label}.status: {status}")
    evidence_ref = str(value.get("evidence_ref") or "").strip()
    reason_code = str(value.get("reason_code") or "").strip()
    if status in {"BLOCKED", "APPROVED"} and not evidence_ref:
        raise ComplianceEligibilityError(
            f"{label}.evidence_ref is required when status={status}"
        )
    if status in {"BLOCKED", "APPROVED"} and not reason_code:
        raise ComplianceEligibilityError(
            f"{label}.reason_code is required when status={status}"
        )
    return {
        "status": status,
        "evidence_ref": evidence_ref,
        "reason_code": reason_code,
    }


def _validate(payload: Mapping[str, Any]) -> Dict[str, Any]:
    _reject_secret_material(payload)
    if str(payload.get("authority") or "") != AUTHORITY:
        raise ComplianceEligibilityError(
            f"authority must be {AUTHORITY}"
        )
    states = payload.get("gate_states")
    if not isinstance(states, list) or set(states) != set(GATE_STATES):
        raise ComplianceEligibilityError(
            "gate_states must contain exactly UNKNOWN/BLOCKED/APPROVED"
        )
    products = payload.get("products")
    if not isinstance(products, Mapping) or not products:
        raise ComplianceEligibilityError("products must be a non-empty object")

    normalized_products: Dict[str, Any] = {}
    for raw_product_id, raw_product in products.items():
        product_id = _nonempty(raw_product_id, label="strategy_product_id")
        if not isinstance(raw_product, Mapping):
            raise ComplianceEligibilityError(
                f"products.{product_id} must be an object"
            )
        missing = sorted(set(_REQUIRED_PRODUCT_GATES) - set(raw_product))
        if missing:
            raise ComplianceEligibilityError(
                f"products.{product_id} missing required gates: {missing}"
            )
        providers = raw_product.get("providers")
        if not isinstance(providers, Mapping) or not providers:
            raise ComplianceEligibilityError(
                f"products.{product_id}.providers must be a non-empty object"
            )
        normalized: Dict[str, Any] = {
            name: _gate_entry(
                raw_product.get(name),
                label=f"products.{product_id}.{name}",
            )
            for name in _REQUIRED_PRODUCT_GATES
        }
        normalized_providers: Dict[str, Any] = {}
        for raw_provider, raw_provider_cfg in providers.items():
            provider = _nonempty(raw_provider, label="provider").upper()
            if not isinstance(raw_provider_cfg, Mapping):
                raise ComplianceEligibilityError(
                    f"products.{product_id}.providers.{provider} must be an object"
                )
            provider_missing = sorted(
                set(_REQUIRED_PROVIDER_GATES) - set(raw_provider_cfg)
            )
            if provider_missing:
                raise ComplianceEligibilityError(
                    f"products.{product_id}.providers.{provider} missing required gates: "
                    f"{provider_missing}"
                )
            normalized_providers[provider] = {
                name: _gate_entry(
                    raw_provider_cfg.get(name),
                    label=f"products.{product_id}.providers.{provider}.{name}",
                )
                for name in _REQUIRED_PROVIDER_GATES
            }
        normalized["providers"] = normalized_providers
        normalized_products[product_id] = normalized

    return {
        "schema_version": _nonempty(
            payload.get("schema_version"), label="schema_version"
        ),
        "authority": AUTHORITY,
        "gate_states": sorted(GATE_STATES),
        "products": normalized_products,
    }


def load_eligibility_config(path: str | Path | None = None) -> Dict[str, Any]:
    target = Path(path) if path is not None else config_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ComplianceEligibilityError(
            f"Unable to read compliance eligibility config: {target}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise ComplianceEligibilityError(
            f"Compliance eligibility config must be an object: {target}"
        )
    return _validate(payload)


def evaluate_paid_checkout(
    *,
    strategy_product_id: str,
    provider: str,
    config: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    product_id = _nonempty(
        strategy_product_id, label="strategy_product_id"
    )
    provider_id = _nonempty(provider, label="provider").upper()
    payload = _validate(config) if config is not None else load_eligibility_config()

    product = payload["products"].get(product_id)
    if not isinstance(product, Mapping):
        return {
            "status": "BLOCKED",
            "authority": AUTHORITY,
            "strategy_product_id": product_id,
            "provider": provider_id,
            "reason_codes": ["PRODUCT_ELIGIBILITY_NOT_CONFIGURED"],
            "inputs": {},
        }

    provider_cfg = product.get("providers", {}).get(provider_id)
    if not isinstance(provider_cfg, Mapping):
        return {
            "status": "BLOCKED",
            "authority": AUTHORITY,
            "strategy_product_id": product_id,
            "provider": provider_id,
            "reason_codes": ["PROVIDER_ELIGIBILITY_NOT_CONFIGURED"],
            "inputs": {
                name: dict(product[name]) for name in _REQUIRED_PRODUCT_GATES
            },
        }

    inputs: Dict[str, Dict[str, str]] = {
        name: dict(product[name]) for name in _REQUIRED_PRODUCT_GATES
    }
    inputs.update(
        {
            f"provider.{name}": dict(provider_cfg[name])
            for name in _REQUIRED_PROVIDER_GATES
        }
    )

    blocked = [
        name for name, row in inputs.items() if row.get("status") == "BLOCKED"
    ]
    unknown = [
        name for name, row in inputs.items() if row.get("status") == "UNKNOWN"
    ]
    approved = [
        name for name, row in inputs.items() if row.get("status") == "APPROVED"
    ]

    if not blocked and not unknown and len(approved) == len(inputs):
        status = "APPROVED"
        reasons = ["ALL_REQUIRED_EXTERNAL_EVIDENCE_APPROVED"]
    else:
        status = "BLOCKED"
        reasons = []
        if blocked:
            reasons.append("EXPLICIT_BLOCKING_EVIDENCE")
        if unknown:
            reasons.append("REQUIRED_EVIDENCE_UNKNOWN")
        reasons.extend(
            sorted(
                {
                    str(row.get("reason_code") or "")
                    for row in inputs.values()
                    if row.get("status") != "APPROVED"
                    and str(row.get("reason_code") or "").strip()
                }
            )
        )

    return {
        "status": status,
        "authority": AUTHORITY,
        "strategy_product_id": product_id,
        "provider": provider_id,
        "reason_codes": reasons,
        "inputs": inputs,
    }
