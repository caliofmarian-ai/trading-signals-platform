from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_EXAMPLE = REPO_ROOT / ".env.example"


def _load_env_example() -> tuple[str, dict[str, str]]:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        assert sep == "=", f"Malformed .env.example line: {raw_line!r}"
        assert key not in values, f"Duplicate .env.example key: {key}"
        values[key] = value
    return text, values


def test_env_example_preserves_safe_runtime_defaults_and_paths() -> None:
    _, values = _load_env_example()

    assert values["BINARYBOT_BASE_DIR"] == "/data"
    assert values["SHADOW_MODE"] == "true"
    assert values["ENABLE_BROKER_EXECUTION"] == "false"
    assert values["ENABLE_TELEGRAM"] == "false"

    assert values["ALGO_PARAMS_PATH"] == "/data/config/algo_params.json"
    assert values["ADMIN_ROLES_CONFIG"] == "/data/config/admin_roles.json"
    assert values["ADMIN_PERMISSIONS_CONFIG"] == "/data/config/admin_permissions.json"
    assert values["OBS_DIR"] == "/data/observability"
    assert values["OUTCOMES_LOG"] == "/data/outcomes/outcomes.jsonl"
    assert values["ANALYTICS_DIR"] == "/data/analytics"


def test_env_example_uses_current_event_and_entitlement_contracts() -> None:
    _, values = _load_env_example()

    assert values["EVENT_SCHEMA_VERSION"] == "3.0.0"
    assert values["FREE_LIMIT"] == "6"
    assert values["BASIC_LIMIT"] == "20"
    assert values["PRO_LIMIT"] == "50"
    assert values["ELITE_LIMIT"] == "UNLIMITED"


def test_env_example_documents_provider_bootstrap_without_provider_mixing() -> None:
    text, values = _load_env_example()
    lowered = text.lower()

    assert values["MARKET_DATA_PROVIDER"] == "FINNHUB"
    assert values["FINNHUB_API_KEY"] == "replace-me"
    assert values["FINNHUB_CANDLE_STORE"] == "/data/market_data/finnhub_eurusd.json"
    assert values["FINNHUB_MIN_CANDLES"] == "201"
    assert values["MARKET_DATA_FRESHNESS_SECONDS"] == "10"
    assert values["TWELVE_DATA_API_KEY"] == "replace-me"

    assert "deployment bootstrap only" in lowered
    assert "persisted owner selection" in lowered
    assert "fails closed" in lowered
    assert "exactly one provider is active at a time" in lowered
    assert "do not combine finnhub and twelve data in one evidence stream" in lowered


def test_env_example_contains_only_placeholders_for_provider_secrets() -> None:
    _, values = _load_env_example()

    assert values["FINNHUB_API_KEY"] == "replace-me"
    assert values["TWELVE_DATA_API_KEY"] == "replace-me"
    assert values["TELEGRAM_BOT_TOKEN"] == "replace-me"
