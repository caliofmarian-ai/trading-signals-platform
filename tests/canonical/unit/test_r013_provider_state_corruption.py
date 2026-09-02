from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

OWNER_ID = 919191


def _purge() -> None:
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

    for name in (
        "core.market_data_provider_control",
        "core.admin_commands",
        "core.admin_permissions",
        "core.telegram_admin_ui",
        "runtime.market_client",
    ):
        sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _env(tmp_path: Path) -> dict[str, str]:
    return {
        "BINARYBOT_BASE_DIR": str(tmp_path),
        "MARKET_DATA_PROVIDER": "TWELVE_DATA",
        "FINNHUB_API_KEY": "fh-r013-key",
        "TWELVE_DATA_API_KEY": "td-r013-key",
    }


def _state_path(tmp_path: Path) -> Path:
    path = tmp_path / "config" / "market_data_provider.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_state(tmp_path: Path, payload: object) -> Path:
    path = _state_path(tmp_path)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_absent_persisted_state_allows_deployment_bootstrap(tmp_path: Path) -> None:
    _purge()
    env = _env(tmp_path)
    env["MARKET_DATA_PROVIDER"] = "FINNHUB"
    with patch.dict(os.environ, env, clear=False):
        from core import market_data_provider_control as control

        assert control.get_active_provider() == "FINNHUB"
        assert control.selection_source() == "DEPLOYMENT_ENVIRONMENT"
        summary = control.provider_summary()
        assert summary["state_status"] == "VALID"
        assert summary["persisted_state_present"] is False


def test_invalid_json_never_falls_back_to_environment_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _purge()
    env = _env(tmp_path)
    path = _state_path(tmp_path)
    path.write_text("{bad json", encoding="utf-8")
    with patch.dict(os.environ, env, clear=False):
        from core import market_data_provider_control as control

        applied: list[str] = []
        monkeypatch.setattr(control, "_apply_provider", lambda provider: applied.append(provider) or provider)
        with pytest.raises(control.MarketDataProviderStateError, match="invalid JSON"):
            control.get_active_provider()
        with pytest.raises(control.MarketDataProviderStateError, match="invalid JSON"):
            control.selection_source()
        assert applied == []


@pytest.mark.parametrize(
    "payload, expected",
    [
        (["FINNHUB"], "JSON object"),
        ({"mode": "EXCLUSIVE"}, "unsupported or missing"),
        ({"active_provider": "UNKNOWN", "mode": "EXCLUSIVE"}, "unsupported or missing"),
        ({"active_provider": "FINNHUB", "mode": "SHARED"}, "must be EXCLUSIVE"),
    ],
)
def test_existing_invalid_state_is_blocking_not_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
    expected: str,
) -> None:
    _purge()
    _write_state(tmp_path, payload)
    with patch.dict(os.environ, _env(tmp_path), clear=False):
        from core import market_data_provider_control as control

        applied: list[str] = []
        monkeypatch.setattr(control, "_apply_provider", lambda provider: applied.append(provider) or provider)
        with pytest.raises(control.MarketDataProviderStateError, match=expected):
            control.get_active_provider()
        assert applied == []
        summary = control.provider_summary()
        assert summary["active_provider"] is None
        assert summary["mode"] == "BLOCKED"
        assert summary["ready"] is False
        assert summary["selection_source"] == "PERSISTED_STATE_INVALID"
        assert summary["state_status"] == "BLOCKED"
        assert summary["persisted_state_present"] is True


def test_explicit_ready_owner_selection_recovers_corrupt_state(tmp_path: Path) -> None:
    _purge()
    path = _state_path(tmp_path)
    path.write_text("{bad json", encoding="utf-8")
    with patch.dict(os.environ, _env(tmp_path), clear=False):
        from core import market_data_provider_control as control

        saved = control.set_active_provider("FINNHUB", selected_by=OWNER_ID)
        assert saved["active_provider"] == "FINNHUB"
        assert saved["mode"] == "EXCLUSIVE"
        assert control.get_active_provider() == "FINNHUB"
        assert control.selection_source() == "TELEGRAM_ADMIN"
        persisted = json.loads(path.read_text(encoding="utf-8"))
        assert persisted["active_provider"] == "FINNHUB"
        assert persisted["selected_by"] == OWNER_ID


def test_unready_recovery_target_cannot_overwrite_corrupt_state(tmp_path: Path) -> None:
    _purge()
    path = _state_path(tmp_path)
    original = "{bad json"
    path.write_text(original, encoding="utf-8")
    env = _env(tmp_path)
    env["FINNHUB_API_KEY"] = ""
    with patch.dict(os.environ, env, clear=False):
        from core import market_data_provider_control as control

        with pytest.raises(control.MarketDataProviderUnavailable, match="FINNHUB_API_KEY"):
            control.set_active_provider("FINNHUB", selected_by=OWNER_ID)
        assert path.read_text(encoding="utf-8") == original
        assert control.provider_summary()["state_status"] == "BLOCKED"


def test_telegram_selector_stays_recoverable_but_hides_symbol_mutations_when_blocked(tmp_path: Path) -> None:
    _purge()
    _state_path(tmp_path).write_text("{bad json", encoding="utf-8")
    with patch.dict(os.environ, _env(tmp_path), clear=False):
        from core.telegram_admin_ui import symbols_toggle_markup

        markup = symbols_toggle_markup(
            ["EUR/USD", "GBP/USD", "BTC/USD"],
            ["EUR/USD", "GBP/USD"],
        )
        texts = [button["text"] for row in markup["inline_keyboard"] for button in row]
        callbacks = [button["callback_data"] for row in markup["inline_keyboard"] for button in row]
        assert any("Finnhub" in text for text in texts)
        assert any("Twelve Data" in text for text in texts)
        assert any("BLOCKED" in text for text in texts)
        assert not any("GBP/USD" in text for text in texts)
        assert not any(text in {"✅ All", "⬜ None"} for text in texts)
        assert any("PROVIDER_FINNHUB" in callback for callback in callbacks)
        assert any("PROVIDER_TWELVE_DATA" in callback for callback in callbacks)


def test_admin_provider_action_can_recover_but_symbol_toggle_is_blocked_before_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _purge()
    _state_path(tmp_path).write_text("{bad json", encoding="utf-8")
    with patch.dict(os.environ, _env(tmp_path), clear=False):
        from core import admin_commands
        from core import market_data_provider_control as control

        monkeypatch.setattr(admin_commands, "require_permission", lambda *_args, **_kwargs: (True, ""))
        monkeypatch.setattr(admin_commands, "_audit", lambda *_args, **_kwargs: None)

        blocked = admin_commands.handle_symbols_toggle("GBP/USD", OWNER_ID)
        assert "BLOCKED" in blocked
        assert control.provider_summary()["active_provider"] is None

        recovered = admin_commands.handle_symbols_toggle("PROVIDER_FINNHUB", OWNER_ID)
        assert "Finnhub activated" in recovered
        assert control.get_active_provider() == "FINNHUB"
