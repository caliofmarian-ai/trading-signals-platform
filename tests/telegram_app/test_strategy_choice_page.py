from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))

from core.strategy_catalog import (
    CATALOG_PATH,
    StrategyCatalogError,
    load_strategy_catalog,
    render_future_forex,
    render_strategy_choice,
)
from core.telegram_admin_ui import CALLBACK_PREFIX, decision_visibility_markup, strategy_choice_markup


def _callbacks(markup: dict) -> set[str]:
    return {button["callback_data"] for row in markup["inline_keyboard"] for button in row}


def test_decision_visibility_exposes_choose_strategy_button() -> None:
    assert f"{CALLBACK_PREFIX}STRATEGY_CHOOSE" in _callbacks(decision_visibility_markup())
    assert f"{CALLBACK_PREFIX}STRATEGY_COMPARE" not in _callbacks(decision_visibility_markup())


def test_choice_page_exposes_binary_and_future_forex() -> None:
    callbacks = _callbacks(strategy_choice_markup())
    assert f"{CALLBACK_PREFIX}STRATEGY_CHOOSE" in callbacks
    assert f"{CALLBACK_PREFIX}STRATEGY_FOREX_FUTURE" in callbacks
    assert f"{CALLBACK_PREFIX}DECISION_VIS" in callbacks
    assert f"{CALLBACK_PREFIX}HOME" in callbacks


def test_catalog_identifies_binary_strategy_family_with_active_canonical_authority() -> None:
    catalog = load_strategy_catalog()
    assert len(catalog.strategies) == 2
    assert catalog.selected.id == "binary_canonical"
    assert catalog.selected.name == "Binary Trading"
    assert catalog.selected.implementation == "ALGO_SPEC_v3.0.0"
    assert catalog.selected.canonical_spec_version == "3.0.0"
    assert catalog.selected.availability == "AVAILABLE"
    forex = next(strategy for strategy in catalog.strategies if strategy.id == "forex_future")
    assert forex.availability == "UNAVAILABLE"
    assert forex.implementation == "NOT_IMPLEMENTED"
    assert forex.canonical_spec_version is None

    text = render_strategy_choice(catalog)
    assert "Selected: Binary Trading" in text
    assert "Canonical specification: ALGO_SPEC_v3.0.0" in text
    assert "Canonical specification version: 3.0.0" in text
    assert "Strategy version: 2.0.0" not in text
    assert "Forex Strategy: NOT AVAILABLE YET" in text


def test_available_strategy_requires_versioned_canonical_specification(tmp_path: Path) -> None:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    payload["strategies"][0]["implementation"] = "ALGO_SPEC_CURRENT.md"
    path = tmp_path / "strategy_catalog.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(StrategyCatalogError, match="versioned canonical specification"):
        load_strategy_catalog(path)


def test_future_forex_page_is_explicitly_blocked() -> None:
    text = render_future_forex(load_strategy_catalog())
    assert "Availability: NOT AVAILABLE YET" in text
    assert "Selection: BLOCKED" in text
    assert "copy-trading" in text
    assert "No Forex decision logic" in text


def test_strategy_pages_use_selection_explanation_not_parameter_explanation(monkeypatch) -> None:
    from core import bot_service

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)
    message = {"chat": {"id": 1}, "from": {"id": 1}}

    for action in ("STRATEGY_CHOOSE", "STRATEGY_FOREX_FUTURE"):
        result = bot_service._handle_admin_navigation_action(action, 1, message)
        assert "governed selection surface for installed trading-strategy families" in result["text"]
        assert "adjustable decision parameters" not in result["text"]


def test_choose_strategy_navigation_returns_active_canonical_authority(monkeypatch) -> None:
    from core import bot_service

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)
    result = bot_service._handle_admin_navigation_action(
        "STRATEGY_CHOOSE", 1, {"chat": {"id": 1}, "from": {"id": 1}}
    )
    assert result["text"].startswith("🧭 Choose Strategy")
    assert "Selected: Binary Trading" in result["text"]
    assert "Canonical specification: ALGO_SPEC_v3.0.0" in result["text"]
    assert "Canonical specification version: 3.0.0" in result["text"]
    assert "Strategy version: 2.0.0" not in result["text"]


def test_old_compare_callback_only_recovers_to_choose_strategy(monkeypatch) -> None:
    from core import bot_service

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)
    result = bot_service._handle_admin_navigation_action(
        "STRATEGY_COMPARE", 1, {"chat": {"id": 1}, "from": {"id": 1}}
    )
    assert result["text"].startswith("🧭 Choose Strategy")
    assert "Strategy Comparison" not in result["text"]


def test_future_forex_callback_cannot_select_or_activate_it(monkeypatch) -> None:
    from core import bot_service

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)
    result = bot_service._handle_admin_navigation_action(
        "STRATEGY_FOREX_FUTURE", 1, {"chat": {"id": 1}, "from": {"id": 1}}
    )
    assert "Selection: BLOCKED" in result["text"]
    assert "No Forex decision logic" in result["text"]
