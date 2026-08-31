from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))

from core.admin_views import render_strategy_comparison
from core.telegram_admin_ui import CALLBACK_PREFIX, decision_visibility_markup, strategy_comparison_markup


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


def test_decision_visibility_exposes_comparison_button() -> None:
    assert f"{CALLBACK_PREFIX}STRATEGY_COMPARE" in _callbacks(decision_visibility_markup())


def test_comparison_page_has_refresh_back_and_home() -> None:
    callbacks = _callbacks(strategy_comparison_markup())
    assert f"{CALLBACK_PREFIX}STRATEGY_COMPARE" in callbacks
    assert f"{CALLBACK_PREFIX}DECISION_VIS" in callbacks
    assert f"{CALLBACK_PREFIX}HOME" in callbacks


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


def test_navigation_action_reads_snapshot_and_returns_live_page(monkeypatch) -> None:
    from core import bot_service, storage

    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)
    monkeypatch.setattr(storage, "load_json", lambda *_args, **_kwargs: _snapshot())
    monkeypatch.setattr(bot_service.time, "time", lambda: 1_800_000_004)

    result = bot_service._handle_admin_navigation_action(
        "STRATEGY_COMPARE", 1, {"chat": {"id": 1}, "from": {"id": 1}}
    )

    assert result["text"].startswith("⚖️ Strategy Comparison")
    assert "Current engine says: CONFIRM" in result["text"]
    callbacks = _callbacks(result["reply_markup"])
    assert f"{CALLBACK_PREFIX}STRATEGY_COMPARE" in callbacks
    assert f"{CALLBACK_PREFIX}DECISION_VIS" in callbacks
