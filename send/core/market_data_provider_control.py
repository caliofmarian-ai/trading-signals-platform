from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

from core import storage

PROVIDER_FINNHUB = "FINNHUB"
PROVIDER_TWELVE_DATA = "TWELVE_DATA"
SUPPORTED_PROVIDERS = frozenset({PROVIDER_FINNHUB, PROVIDER_TWELVE_DATA})
FINNHUB_EFFECTIVE_SYMBOLS = ("EUR/USD",)
STATE_FILENAME = "market_data_provider.json"


class MarketDataProviderControlError(RuntimeError):
    pass


class MarketDataProviderUnavailable(MarketDataProviderControlError):
    pass


def _state_path() -> str:
    return storage.root_path("config", STATE_FILENAME)


def _normalize_provider(provider: str) -> str:
    value = str(provider or "").strip().upper().replace(" ", "_")
    aliases = {
        "TWELVEDATA": PROVIDER_TWELVE_DATA,
        "TWELVE_DATA": PROVIDER_TWELVE_DATA,
        "FINNHUB": PROVIDER_FINNHUB,
    }
    normalized = aliases.get(value, value)
    if normalized not in SUPPORTED_PROVIDERS:
        raise MarketDataProviderControlError(f"Unsupported market data provider: {provider!r}")
    return normalized


def _load_persisted_state() -> Optional[Dict[str, Any]]:
    path = _state_path()
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    provider = str(payload.get("active_provider") or "").strip().upper()
    if provider not in SUPPORTED_PROVIDERS:
        return None
    return payload


def provider_ready(provider: str) -> tuple[bool, str]:
    normalized = _normalize_provider(provider)
    if normalized == PROVIDER_FINNHUB:
        value = os.getenv("FINNHUB_API_KEY", "").strip()
        if not value or value == "replace-me":
            return False, "FINNHUB_API_KEY is not configured."
        return True, "READY"

    value = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not value or value == "replace-me":
        return False, "TWELVE_DATA_API_KEY is not configured."
    return True, "READY"


def get_active_provider() -> str:
    """Return the single effective provider and synchronize the process env.

    Persisted owner selection wins over the deployment environment. The
    deployment environment remains the bootstrap source before the first
    Telegram selection. The historical TWELVE_DATA fallback is preserved only
    for compatibility when no explicit deployment or owner selection exists;
    production can and currently does select FINNHUB explicitly.
    """
    persisted = _load_persisted_state()
    if persisted is not None:
        provider = _normalize_provider(str(persisted["active_provider"]))
        os.environ["MARKET_DATA_PROVIDER"] = provider
        return provider

    raw_env = os.getenv("MARKET_DATA_PROVIDER", PROVIDER_TWELVE_DATA)
    provider = _normalize_provider(raw_env)
    os.environ["MARKET_DATA_PROVIDER"] = provider
    return provider


def selection_source() -> str:
    state = _load_persisted_state()
    if state is not None:
        return str(state.get("selection_source") or "PERSISTED_OWNER_SELECTION")
    return "DEPLOYMENT_ENVIRONMENT"


def set_active_provider(provider: str, *, selected_by: Optional[int] = None) -> Dict[str, Any]:
    """Persist one exclusive provider selection and apply it immediately.

    Selection is refused when the target provider has no configured API key;
    the previous provider remains effective. Provider switching never changes
    strategy parameters or the persisted Twelve Data symbol selection.
    """
    normalized = _normalize_provider(provider)
    ready, reason = provider_ready(normalized)
    if not ready:
        raise MarketDataProviderUnavailable(reason)

    now_ts = int(time.time())
    payload: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "active_provider": normalized,
        "mode": "EXCLUSIVE",
        "selection_source": "TELEGRAM_ADMIN",
        "selected_by": selected_by,
        "updated_at_ts": now_ts,
        "finnhub_effective_symbols": list(FINNHUB_EFFECTIVE_SYMBOLS),
        "twelve_data_symbol_policy": "ACTIVE_SYMBOLS_CONFIG",
    }

    path = _state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with storage.with_lock("market_data_provider"):
        storage.save_json_atomic(path, payload)

    os.environ["MARKET_DATA_PROVIDER"] = normalized
    return payload


def provider_summary() -> Dict[str, Any]:
    provider = get_active_provider()
    ready, reason = provider_ready(provider)
    return {
        "active_provider": provider,
        "mode": "EXCLUSIVE",
        "ready": ready,
        "readiness_reason": reason,
        "selection_source": selection_source(),
        "symbol_policy": (
            "EUR/USD_ONLY"
            if provider == PROVIDER_FINNHUB
            else "ACTIVE_SYMBOLS_CONFIG"
        ),
        "effective_symbols": (
            list(FINNHUB_EFFECTIVE_SYMBOLS)
            if provider == PROVIDER_FINNHUB
            else None
        ),
    }
