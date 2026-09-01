from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

OWNER_ID = 818181


def _purge() -> None:
    # Remove both sys.modules entries and cached package attributes. Python can
    # otherwise return runtime.market_client from the package object after the
    # module entry itself was deleted, which defeats test isolation.
    runtime_package = sys.modules.get("runtime")
    if runtime_package is not None and hasattr(runtime_package, "market_client"):
        delattr(runtime_package, "market_client")

    core_package = sys.modules.get("core")
    if core_package is not None:
        for attr in (
            "market_data_provider_control",
            "admin_commands",
            "admin_permissions",
            "telegram_admin_ui",
        ):
            if hasattr(core_package, attr):
                delattr(core_package, attr)

    for name in [
        "core.market_data_provider_control",
        "core.admin_commands",
        "core.admin_permissions",
        "core.telegram_admin_ui",
        "runtime.market_client",
    ]:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _env(tmp_path: Path, *, twelve_key: str = "td-test-key") -> dict[str, str]:
    config = tmp_path / "config"
    config.mkdir(parents=True, exist_ok=True)
    roles = tmp_path / "roles.json"
    _write(
        roles,
        {
            "owner": [OWNER_ID],
            "primary_admin": [],
            "strategy_admin": [],
            "research_admin": [],
            "analyst": [],
            "moderator": [],
            "affiliate_admin": {},
        },
    )
    _write(
        config / "active_symbols.json",
        {"forex": ["EUR/USD", "GBP/USD"], "crypto": ["BTC/USD"]},
    )
    _write(
        config / "symbol_universe.json",
        {"forex": ["EUR/USD", "GBP/USD"], "crypto": ["BTC/USD"]},
    )
    return {
        "BINARYBOT_BASE_DIR": str(tmp_path),
        "OWNER_TELEGRAM_ID": str(OWNER_ID),
        "ADMIN_ROLES_CONFIG": str(roles),
        "MARKET_DATA_PROVIDER": "TWELVE_DATA",
        "FINNHUB_API_KEY": "fh-test-key",
        "TWELVE_DATA_API_KEY": twelve_key,
    }


class _FakeFeed:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def test_telegram_selection_is_exclusive_and_finnhub_locks_symbols(tmp_path):
    env = _env(tmp_path)
    _purge()
    with patch.dict(os.environ, env, clear=False):
        import core.admin_permissions as permissions
        permissions.load_roles_config.cache_clear()
        with patch("core.admin_commands.observability_logger"):
            from core.admin_commands import handle_symbols_toggle, _load_active_symbols
            from core.market_data_provider_control import get_active_provider
            from runtime import market_client

            before = _load_active_symbols()
            result = handle_symbols_toggle("PROVIDER_FINNHUB", OWNER_ID)

            assert "Finnhub activated" in result
            assert get_active_provider() == "FINNHUB"
            assert market_client.configured_provider() == "FINNHUB"
            assert market_client.configured_symbols() == ["EUR/USD"]
            assert _load_active_symbols() == before

            locked = handle_symbols_toggle("GBP/USD", OWNER_ID)
            assert "EUR/USD only" in locked
            assert _load_active_symbols() == before


def test_twelve_data_restores_multi_symbol_controls_without_rewriting_selection(tmp_path):
    env = _env(tmp_path)
    _purge()
    with patch.dict(os.environ, env, clear=False):
        import core.admin_permissions as permissions
        permissions.load_roles_config.cache_clear()
        with patch("core.admin_commands.observability_logger"):
            from core.admin_commands import handle_symbols_toggle, _load_active_symbols
            from core.market_data_provider_control import get_active_provider
            from runtime import market_client

            original = _load_active_symbols()
            handle_symbols_toggle("PROVIDER_FINNHUB", OWNER_ID)
            result = handle_symbols_toggle("PROVIDER_TWELVE_DATA", OWNER_ID)

            assert "Twelve Data activated" in result
            assert get_active_provider() == "TWELVE_DATA"
            assert market_client.configured_provider() == "TWELVE_DATA"
            assert market_client.configured_symbols() is None
            assert _load_active_symbols() == original

            toggled = handle_symbols_toggle("GBP/USD", OWNER_ID)
            assert "Removed symbol GBP/USD" in toggled
            assert "GBP/USD" not in _load_active_symbols()


def test_provider_switch_is_rejected_when_target_api_key_is_missing(tmp_path):
    env = _env(tmp_path, twelve_key="")
    env["MARKET_DATA_PROVIDER"] = "FINNHUB"
    _purge()
    with patch.dict(os.environ, env, clear=False):
        import core.admin_permissions as permissions
        permissions.load_roles_config.cache_clear()
        with patch("core.admin_commands.observability_logger"):
            from core.admin_commands import handle_symbols_toggle
            from core.market_data_provider_control import get_active_provider

            result = handle_symbols_toggle("PROVIDER_TWELVE_DATA", OWNER_ID)
            assert "cannot be activated" in result
            assert get_active_provider() == "FINNHUB"


def test_symbols_markup_changes_with_active_provider(tmp_path):
    env = _env(tmp_path)
    _purge()
    with patch.dict(os.environ, env, clear=False):
        from core.market_data_provider_control import set_active_provider
        from core.telegram_admin_ui import symbols_toggle_markup

        set_active_provider("FINNHUB", selected_by=OWNER_ID)
        markup = symbols_toggle_markup(
            ["EUR/USD", "GBP/USD", "BTC/USD"],
            ["EUR/USD", "GBP/USD", "BTC/USD"],
        )
        texts = [button["text"] for row in markup["inline_keyboard"] for button in row]
        callbacks = [button["callback_data"] for row in markup["inline_keyboard"] for button in row]
        assert any("✅ Finnhub" in text for text in texts)
        assert any("Twelve Data" in text for text in texts)
        assert any("EUR/USD only" in text for text in texts)
        assert not any("GBP/USD" in text for text in texts)
        assert any("PROVIDER_FINNHUB" in callback for callback in callbacks)
        assert any("PROVIDER_TWELVE_DATA" in callback for callback in callbacks)

        set_active_provider("TWELVE_DATA", selected_by=OWNER_ID)
        markup = symbols_toggle_markup(
            ["EUR/USD", "GBP/USD", "BTC/USD"],
            ["EUR/USD", "GBP/USD"],
        )
        texts = [button["text"] for row in markup["inline_keyboard"] for button in row]
        assert any("✅ Twelve Data" in text for text in texts)
        assert any("GBP/USD" in text for text in texts)
        assert any("BTC/USD" in text for text in texts)


def test_switch_stops_inactive_provider_streams_and_clears_stale_twelve_cache(tmp_path):
    env = _env(tmp_path)
    _purge()
    with patch.dict(os.environ, env, clear=False):
        from core.market_data_provider_control import set_active_provider
        from runtime import market_client

        finnhub_feed = _FakeFeed()
        twelve_feed_a = _FakeFeed()
        twelve_feed_b = _FakeFeed()
        market_client._FINNHUB_FEED = finnhub_feed
        market_client._TWELVE_DATA_FEEDS = {
            "EUR/USD": twelve_feed_a,
            "GBP/USD": twelve_feed_b,
        }
        market_client._TWELVE_DATA_REST_CACHE = {
            ("EUR/USD", "1min"): {"fetched_ts": 1, "candles": []}
        }

        set_active_provider("FINNHUB", selected_by=OWNER_ID)
        assert twelve_feed_a.stopped is True
        assert twelve_feed_b.stopped is True
        assert market_client._TWELVE_DATA_FEEDS == {}
        assert market_client._TWELVE_DATA_REST_CACHE == {}
        assert finnhub_feed.stopped is False

        set_active_provider("TWELVE_DATA", selected_by=OWNER_ID)
        assert finnhub_feed.stopped is True
        assert market_client._FINNHUB_FEED is None
