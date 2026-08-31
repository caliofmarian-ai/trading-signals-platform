from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))

from core.admin_views import render_strategy_comparison
from core.strategy_catalog import load_strategy_catalog, render_future_forex, render_strategy_choice
from core.telegram_admin_ui import CALLBACK_PREFIX, decision_visibility_markup, strategy_choice_markup


def _callbacks(markup: dict) -> set[str]:
    return {
        button["callback_data"]
        for row in markup["inline_keyboard"]
        for button in row
    }


def _snapshot(**overrides):
    payload = {
        "observed_ts": 1_800_000_000,
        "symbol": "EUR/USD",
        "live_kind": "CONFIRM",
        "canonical_outcome": "PREPARE",
        "live_direction": "BUY",
        "canonical_direction": "BUY",
        "live_score": 76.0,
        "canonical_score": 73.5,
        "score_difference": -2.5,
        "live_expiry_minutes": 5.0,
        "canonical_model_expiry_minutes": 4.0,
        "direction_agrees": True,
        "stage_agrees": False,
        "canonical_execution_time_available": False,
        "canonical_shadow_only": True,
        "signal_handoff_ready": False,
    }
    payload.update(overrides)
    return payload


def test_decision_visibility_exposes_choose_strategy_button() -> None:
    assert f"{CALLBACK_PREFIX}STRATEGY_CHOOSE" in _callbacks(decision_visibility_markup())
    assert f"{CALLBACK_PREFIX}STRATEGY_COMPARE" not in _callbacks(decision_visibility_markup())


def test_strategy_choice_page_has_selection_refresh_back_and_home() -> None:
    callbacks = _callbacks(strategy_choice_markup())
    assert f"{CALLBACK_PREFIX}STRATEGY_CHOOSE" in callbacks
    assert f"{CALLBACK_PREFIX}STRATEGY_FOREX_FUTURE" in callbacks
    assert f"{CALLBACK_PREFIX}DECISION_VIS" in callbacks
    assert f"{CALLBACK_PREFIX}HOME" in callbacks


def test_catalog_has_selected_binary_and_future_forex_strategy() -> None:
    catalog = load_strategy_catalog()
    assert len(catalog.strategies) == 2
    assert catalog.selected.id == "binary_canonical"
    assert catalog.selected.name == "Binary Trading"
    assert catalog.selected.trade_type == "BINARY_OPTIONS"
    assert catalog.selected.availability == "AVAILABLE"
    forex = next(strategy for strategy in catalog.strategies if strategy.id == "forex_future")
    assert forex.availability == "UNAVAILABLE"
    text = render_strategy_choice(catalog)
    assert "Selected: Binary Trading" in text
    assert "Forex Strategy" in text
    assert "Forex Strategy: NOT AVAILABLE YET" in text


def test_future_forex_page_is_explicitly_blocked() -> None:
    text = render_future_forex(load_strategy_catalog())
    assert "Availability: NOT AVAILABLE YET" in text
    assert "Selection: BLOCKED" in text
    assert "copy-trading" in text
    assert "No Forex decision logic" in text


def test_current_comparison_is_explained_in_plain_language() -> None:
    text = render_strategy_comparison(_snapshot(), now_ts=1_800_000_004)

    assert "CURRENT — updated 4 seconds ago" in text
    assert "Current engine says: CONFIRM" in text
    assert "New strategy says: PREPARE" in text
    assert "Direction: both strategies agree" in text
    assert "Decision stage: the strategies disagree" in text
    assert "cannot send a signal" in text
    assert "does not guarantee that a trade will win" in text


def test_missing_invalid_and_stale_snapshots_remain_explicit() -> None:
    assert "NOT AVAILABLE YET" in render_strategy_comparison(None, now_ts=1_800_000_000)
    assert "incomplete or invalid" in render_strategy_comparison({"symbol": "EUR/USD"}, now_ts=1_800_000_000)
    stale = render_strategy_comparison(_snapshot(), now_ts=1_800_000_020)
    assert "STALE — last comparison is 20 seconds old" in stale
    assert "strategy values are hidden" in stale
    assert "Current engine says" not in stale
    assert "New strategy says" not in stale


def test_missing_comparison_shows_real_collection_progress() -> None:
    text = render_strategy_comparison(
        None,
        now_ts=1_800_000_000,
        status_snapshot={
            "market_data_candle_counts": {"M1": 37, "M5": 9},
            "market_data_minimum_candles": 201,
            "market_data_persistence_state": "ACTIVE",
        },
    )
    assert "M1: 37/201 real candles — 164 still required" in text
    assert "M5: 9/201 real candles — 192 still required" in text
    assert "Persistent history: ACTIVE" in text
    assert "Action required: none" in text


def test_missing_comparison_does_not_invent_collection_progress() -> None:
    text = render_strategy_comparison(None, now_ts=1_800_000_000, status_snapshot={})
    assert "History progress: UNAVAILABLE" in text
    assert "M1:" not in text


def test_invalid_boolean_or_negative_counts_remain_unavailable() -> None:
    for counts in ({"M1": True, "M5": 9}, {"M1": 37, "M5": -1}):
        text = render_strategy_comparison(
            None,
            now_ts=1_800_000_000,
            status_snapshot={
                "market_data_candle_counts": counts,
                "market_data_minimum_candles": 201,
            },
        )
        assert "History progress: UNAVAILABLE" in text
        assert "real candles" not in text

    boolean_minimum = render_strategy_comparison(
        None,
        now_ts=1_800_000_000,
        status_snapshot={
            "market_data_candle_counts": {"M1": 1, "M5": 1},
            "market_data_minimum_candles": True,
        },
    )
    assert "History progress: UNAVAILABLE" in boolean_minimum


def test_future_comparison_time_is_blocked() -> None:
    text = render_strategy_comparison(_snapshot(), now_ts=1_799_999_999)
    assert "Comparison: UNAVAILABLE" in text
    assert "claims to come from the future" in text
    assert "Current engine says" not in text


def test_unproven_shadow_isolation_is_not_presented_as_safe() -> None:
    text = render_strategy_comparison(
        _snapshot(signal_handoff_ready=True), now_ts=1_800_000_001
    )
    assert "Safety: UNAVAILABLE" in text


def test_choose_strategy_navigation_returns_catalog_page(monkeypatch) -> None:
    from core import bot_service

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)

    result = bot_service._handle_admin_navigation_action(
        "STRATEGY_CHOOSE", 1, {"chat": {"id": 1}, "from": {"id": 1}}
    )

    assert result["text"].startswith("🧭 Choose Strategy")
    assert "Selected: Binary Trading" in result["text"]
    callbacks = _callbacks(result["reply_markup"])
    assert f"{CALLBACK_PREFIX}STRATEGY_CHOOSE" in callbacks
    assert f"{CALLBACK_PREFIX}DECISION_VIS" in callbacks


def test_old_compare_callback_recovers_to_choose_strategy(monkeypatch) -> None:
    from core import bot_service

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)

    result = bot_service._handle_admin_navigation_action(
        "STRATEGY_COMPARE", 1, {"chat": {"id": 1}, "from": {"id": 1}}
    )

    assert result["text"].startswith("🧭 Choose Strategy")
    assert "Selected: Binary Trading" in result["text"]


def test_future_forex_callback_cannot_select_or_activate_it(monkeypatch) -> None:
    from core import bot_service

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)
    result = bot_service._handle_admin_navigation_action(
        "STRATEGY_FOREX_FUTURE", 1, {"chat": {"id": 1}, "from": {"id": 1}}
    )
    assert result["text"].startswith("🌍 Forex Strategy")
    assert "Selection: BLOCKED" in result["text"]
    assert "No Forex decision logic" in result["text"]
    callbacks = _callbacks(result["reply_markup"])
    assert f"{CALLBACK_PREFIX}STRATEGY_CHOOSE" in callbacks
