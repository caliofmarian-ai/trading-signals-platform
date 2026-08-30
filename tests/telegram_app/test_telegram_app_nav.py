"""
tests/telegram_app/test_telegram_app_nav.py

Unit tests for telegram_app_nav.py.

Requirement coverage:
- D: Single active UI message tracking
- E: /start guided entry per canonical role
- F: Page contract — title, description, authorized buttons, navigation
- C: Role-specific home pages for every canonical role
- C: Non-admin USER experience
- C: AFFILIATE_ADMIN experience
"""
from __future__ import annotations

import pytest
from typing import Dict, Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(**kwargs) -> Dict[str, Any]:
    defaults = {
        "overall_state": "READY",
        "runtime_phase": "RUNNING",
        "runtime_message": "OK",
        "recovery_state": "HEALTHY",
        "market_data_state": "READY",
        "telegram_state": "ENABLED",
        "fsm_state": "TRADING watchlist=3",
        "shadow_mode": "OFF",
        "broker_state": "DISABLED",
        "market_data_note": "",
    }
    defaults.update(kwargs)
    return defaults


def _extract_button_texts(markup: Dict) -> list:
    """Flatten all inline keyboard button texts."""
    rows = markup.get("inline_keyboard", [])
    texts = []
    for row in rows:
        for btn in row:
            texts.append(btn.get("text", ""))
    return texts


def _extract_button_callbacks(markup: Dict) -> list:
    """Flatten all inline keyboard callback_data values."""
    rows = markup.get("inline_keyboard", [])
    cbs = []
    for row in rows:
        for btn in row:
            cbs.append(btn.get("callback_data", ""))
    return cbs


# ---------------------------------------------------------------------------
# parse_app_action
# ---------------------------------------------------------------------------

class TestParseAppAction:
    def test_parses_valid_app_prefix(self):
        from core.telegram_app_nav import parse_app_action
        assert parse_app_action("APP:HOME") == "HOME"
        assert parse_app_action("APP:STATUS") == "STATUS"
        assert parse_app_action("APP:HELP") == "HELP"
        assert parse_app_action("APP:ADMIN") == "ADMIN"

    def test_returns_none_for_other_prefix(self):
        from core.telegram_app_nav import parse_app_action
        assert parse_app_action("ADMIN_NAV:HOME") is None
        assert parse_app_action("VOTE_|abc|WIN") is None
        assert parse_app_action("") is None
        assert parse_app_action(None) is None

    def test_returns_none_for_empty_action(self):
        from core.telegram_app_nav import parse_app_action
        assert parse_app_action("APP:") is None
        assert parse_app_action("APP:   ") is None


# ---------------------------------------------------------------------------
# Active message state
# ---------------------------------------------------------------------------

class TestActiveMessageState:
    """Canonical §D: Single active UI message per chat/user/thread session."""

    def test_set_and_get_active_message(self):
        from core.telegram_app_nav import set_active_message, get_active_message, clear_active_message
        clear_active_message(99001, chat_id=100)
        set_active_message(99001, chat_id=100, message_id=200)
        result = get_active_message(99001, chat_id=100)
        assert result == 200

    def test_get_returns_none_for_unknown_user(self):
        from core.telegram_app_nav import get_active_message, clear_active_message
        clear_active_message(99002, chat_id=100)
        assert get_active_message(99002, chat_id=100) is None

    def test_clear_removes_entry(self):
        from core.telegram_app_nav import set_active_message, get_active_message, clear_active_message
        set_active_message(99003, chat_id=100, message_id=300)
        clear_active_message(99003, chat_id=100)
        assert get_active_message(99003, chat_id=100) is None

    def test_overwrite_updates_message_id(self):
        from core.telegram_app_nav import set_active_message, get_active_message, clear_active_message
        clear_active_message(99004, chat_id=100)
        set_active_message(99004, chat_id=100, message_id=400)
        set_active_message(99004, chat_id=100, message_id=500)
        assert get_active_message(99004, chat_id=100) == 500

    def test_different_users_are_independent(self):
        from core.telegram_app_nav import set_active_message, get_active_message, clear_active_message
        clear_active_message(99005, chat_id=10)
        clear_active_message(99006, chat_id=20)
        set_active_message(99005, chat_id=10, message_id=11)
        set_active_message(99006, chat_id=20, message_id=22)
        assert get_active_message(99005, chat_id=10) == 11
        assert get_active_message(99006, chat_id=20) == 22

    def test_same_user_different_chats_are_independent(self):
        from core.telegram_app_nav import set_active_message, get_active_message
        set_active_message(99007, chat_id=101, message_id=701)
        set_active_message(99007, chat_id=202, message_id=702)
        assert get_active_message(99007, chat_id=101) == 701
        assert get_active_message(99007, chat_id=202) == 702

    def test_same_chat_user_different_threads_are_independent(self):
        from core.telegram_app_nav import set_active_message, get_active_message
        set_active_message(99008, chat_id=-10001, thread_id=42, message_id=801)
        set_active_message(99008, chat_id=-10001, thread_id=99, message_id=802)
        assert get_active_message(99008, chat_id=-10001, thread_id=42) == 801
        assert get_active_message(99008, chat_id=-10001, thread_id=99) == 802


# ---------------------------------------------------------------------------
# render_welcome_page — /start guided entry for each canonical role
# ---------------------------------------------------------------------------

class TestRenderWelcomePage:
    """
    Canonical §E: /start must present role-scoped guided entry.
    Canonical §F: Page contract — identifiable title, description, buttons, navigation.
    Canonical §C: Complete role-specific experiences.
    """

    def test_unknown_user_gets_platform_intro(self):
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_USER
        text, markup = render_welcome_page(user_id=1, primary_role=ROLE_USER)
        assert "binarybot" in text.lower()
        buttons = _extract_button_texts(markup)
        assert any("status" in b.lower() for b in buttons)

    def test_user_role_no_admin_buttons(self):
        """USER must not see admin control surface button."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_USER
        text, markup = render_welcome_page(user_id=1, primary_role=ROLE_USER)
        callbacks = _extract_button_callbacks(markup)
        # No admin action callback for USER
        assert not any("ADMIN" in cb for cb in callbacks)

    def test_owner_gets_admin_button(self):
        """OWNER must see admin control surface button."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_OWNER
        text, markup = render_welcome_page(user_id=99, primary_role=ROLE_OWNER)
        callbacks = _extract_button_callbacks(markup)
        assert any("ADMIN" in cb for cb in callbacks)

    def test_non_owner_admin_role_no_admin_button(self):
        """Non-owner admin roles in private DM: no admin surface button (security boundary)."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_STRATEGY_ADMIN, ROLE_ANALYST, ROLE_MODERATOR
        for role in (ROLE_STRATEGY_ADMIN, ROLE_ANALYST, ROLE_MODERATOR):
            text, markup = render_welcome_page(user_id=50, primary_role=role)
            callbacks = _extract_button_callbacks(markup)
            assert not any("ADMIN" in cb for cb in callbacks), f"Role {role} should not get admin button in DM"

    def test_affiliate_admin_role_no_admin_button(self):
        """AFFILIATE_ADMIN must not see global admin surface button."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_AFFILIATE_ADMIN
        text, markup = render_welcome_page(user_id=60, primary_role=ROLE_AFFILIATE_ADMIN)
        callbacks = _extract_button_callbacks(markup)
        assert not any("ADMIN" in cb for cb in callbacks)

    def test_shadow_mode_notice_present_when_active(self):
        """Shadow mode must be surfaced on /start when active (canonical §E requirement)."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_USER
        text, markup = render_welcome_page(user_id=1, primary_role=ROLE_USER, shadow_mode=True)
        assert "shadow" in text.lower()

    def test_shadow_mode_not_shown_when_inactive(self):
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_USER
        text, markup = render_welcome_page(user_id=1, primary_role=ROLE_USER, shadow_mode=False)
        assert "shadow mode is active" not in text.lower()

    def test_first_name_used_when_provided(self):
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_USER
        text, markup = render_welcome_page(user_id=1, primary_role=ROLE_USER, first_name="Alice")
        assert "Alice" in text

    def test_all_canonical_roles_produce_markup(self):
        """Every canonical role must produce a navigable page (no dead ends, canonical §F)."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ALL_ROLES
        for role in ALL_ROLES:
            text, markup = render_welcome_page(user_id=1, primary_role=role)
            assert isinstance(text, str) and len(text) > 0
            buttons = _extract_button_texts(markup)
            assert len(buttons) > 0, f"Role {role} must have at least one button (no dead end)"

    def test_button_does_not_grant_role(self):
        """
        Canonical §E: Buttons must never grant privileged roles.
        A USER must not be able to get OWNER access by pressing a button.
        No button callback should grant or assign a role.
        """
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_USER
        text, markup = render_welcome_page(user_id=1, primary_role=ROLE_USER)
        callbacks = _extract_button_callbacks(markup)
        # None of the callbacks should contain role-granting keywords
        suspicious = ["GRANT", "SET_ROLE", "BECOME", "ELEVATE", "PROMOTE"]
        for cb in callbacks:
            for kw in suspicious:
                assert kw not in cb.upper(), f"Suspicious role-granting callback: {cb}"

    def test_owner_page_contains_role_label(self):
        """OWNER welcome page must identify the role (canonical §F: identifiable title)."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_OWNER
        text, markup = render_welcome_page(user_id=99, primary_role=ROLE_OWNER)
        # Should mention "owner" or the canonical label
        assert "owner" in text.lower()

    def test_primary_admin_page(self):
        """PRIMARY_ADMIN welcome page must identify admin tier."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_PRIMARY_ADMIN
        text, markup = render_welcome_page(user_id=99, primary_role=ROLE_PRIMARY_ADMIN)
        assert "admin" in text.lower()

    def test_affiliate_admin_page(self):
        """AFFILIATE_ADMIN welcome page must be distinct."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_AFFILIATE_ADMIN
        text, markup = render_welcome_page(user_id=60, primary_role=ROLE_AFFILIATE_ADMIN)
        assert isinstance(text, str)
        buttons = _extract_button_texts(markup)
        assert len(buttons) > 0


# ---------------------------------------------------------------------------
# render_status_page
# ---------------------------------------------------------------------------

class TestRenderStatusPage:
    """Canonical §F: Status page contract — all relevant fields, refresh button, home button."""

    def test_status_fields_present(self):
        from core.telegram_app_nav import render_status_page
        snap = _make_snapshot()
        text, markup = render_status_page(snap)
        assert "Overall: READY" in text
        assert "Market data: READY" in text
        assert "Broker execution: DISABLED" in text

    def test_status_market_note_shown(self):
        from core.telegram_app_nav import render_status_page
        snap = _make_snapshot(market_data_note="HTTP 429 active")
        text, markup = render_status_page(snap)
        assert "429" in text

    def test_status_explains_finnhub_collection_progress(self):
        from core.telegram_app_nav import render_status_page
        snap = _make_snapshot(
            overall_state="MARKET_DATA_COLLECTING",
            market_data_state="MARKET_DATA_COLLECTING",
            market_data_provider="FINNHUB",
            market_data_symbol="EUR/USD",
            market_data_age_seconds=12,
            market_data_freshness_limit_seconds=10,
            market_data_candle_counts={"M1": 7, "M5": 2},
            market_data_minimum_candles=201,
            market_data_history_ready=False,
            recovery_state="DEGRADED_SAFE",
            shadow_mode="ON",
            broker_state="DISABLED (configured)",
        )
        text, _markup = render_status_page(snap)
        assert "Real history: M1 7/201; M5 2/201" in text
        assert "Strategy history: COLLECTING — decisions remain blocked" in text
        assert "Market information: real history is still being prepared; decisions are blocked." in text
        assert "Real trading: impossible; the bot can observe and calculate only." in text
        assert "Required action: none; the bot is protecting itself" in text

    def test_status_warns_plainly_when_execution_is_enabled(self):
        from core.telegram_app_nav import render_status_page
        snap = _make_snapshot(shadow_mode="OFF", broker_state="ENABLED")

        text, _markup = render_status_page(snap)

        assert "Real trading: broker execution is enabled; owner attention is required." in text
        assert "Required action: inspect execution safety settings before continuing." in text

    def test_status_never_calls_unknown_evidence_healthy(self):
        from core.telegram_app_nav import render_status_page
        snap = _make_snapshot(
            runtime_phase=None,
            market_data_state=None,
            market_data_history_ready=None,
            shadow_mode=None,
            broker_state=None,
        )

        text, _markup = render_status_page(snap)

        assert "current operating state is not reported" in text
        assert "has not reported enough evidence" in text
        assert "safety state cannot be fully confirmed" in text


def test_operational_snapshot_preserves_market_collection_evidence():
    from core.operational_snapshot import build_status_snapshot

    snapshot = build_status_snapshot({
        "phase": "RUNNING",
        "market_data_state": "MARKET_DATA_COLLECTING",
        "market_data_candle_counts": {"M1": 7, "M5": 2},
        "market_data_minimum_candles": 201,
        "market_data_history_ready": False,
    })

    assert snapshot["overall_state"].startswith("MARKET_DATA_COLLECTING")
    assert snapshot["market_data_candle_counts"] == {"M1": 7, "M5": 2}
    assert snapshot["market_data_minimum_candles"] == 201
    assert snapshot["market_data_history_ready"] is False

    def test_status_has_refresh_button(self):
        from core.telegram_app_nav import render_status_page, ACT_STATUS
        snap = _make_snapshot()
        text, markup = render_status_page(snap)
        callbacks = _extract_button_callbacks(markup)
        assert any(ACT_STATUS in cb for cb in callbacks)

    def test_status_has_home_button(self):
        """No dead end: status page must have a Home button."""
        from core.telegram_app_nav import render_status_page, ACT_HOME
        snap = _make_snapshot()
        text, markup = render_status_page(snap)
        callbacks = _extract_button_callbacks(markup)
        assert any(ACT_HOME in cb for cb in callbacks)


# ---------------------------------------------------------------------------
# render_help_page
# ---------------------------------------------------------------------------

class TestRenderHelpPage:
    """Canonical §F: Help page contract — public commands always listed."""

    def test_user_role_help_shows_public_commands(self):
        from core.telegram_app_nav import render_help_page
        from core.role_constants import ROLE_USER
        text, markup = render_help_page(ROLE_USER)
        assert "/start" in text
        assert "/status" in text
        assert "/help" in text

    def test_admin_role_help_shows_admin_hint(self):
        from core.telegram_app_nav import render_help_page
        from core.role_constants import ROLE_OWNER
        text, markup = render_help_page(ROLE_OWNER)
        assert "/admin" in text

    def test_user_role_help_no_admin_commands(self):
        """USER must not see admin command listing."""
        from core.telegram_app_nav import render_help_page
        from core.role_constants import ROLE_USER
        text, markup = render_help_page(ROLE_USER)
        # Admin commands should not be listed for USER
        assert "/roles" not in text
        assert "/symbols" not in text

    def test_help_has_home_button(self):
        """No dead end: help page must have Home navigation."""
        from core.telegram_app_nav import render_help_page, ACT_HOME
        from core.role_constants import ROLE_USER
        text, markup = render_help_page(ROLE_USER)
        callbacks = _extract_button_callbacks(markup)
        assert any(ACT_HOME in cb for cb in callbacks)

    def test_help_has_status_button(self):
        from core.telegram_app_nav import render_help_page, ACT_STATUS
        from core.role_constants import ROLE_USER
        text, markup = render_help_page(ROLE_USER)
        callbacks = _extract_button_callbacks(markup)
        assert any(ACT_STATUS in cb for cb in callbacks)


# ---------------------------------------------------------------------------
# handle_app_action dispatcher
# ---------------------------------------------------------------------------

class TestHandleAppAction:
    """
    Canonical §D+E+F: Application callback dispatcher.
    All actions produce a navigable page. No dead ends.
    """

    def _call(self, action, role="USER", user_id=1, shadow=False, snapshot=None):
        from core.telegram_app_nav import handle_app_action
        return handle_app_action(
            action=action,
            user_id=user_id,
            primary_role=role,
            shadow_mode=shadow,
            status_snapshot=snapshot,
        )

    def test_home_action_returns_welcome_page(self):
        from core.telegram_app_nav import ACT_HOME
        text, markup = self._call(ACT_HOME)
        assert "binarybot" in text.lower()

    def test_status_action_returns_status_page(self):
        from core.telegram_app_nav import ACT_STATUS
        snap = _make_snapshot()
        text, markup = self._call(ACT_STATUS, snapshot=snap)
        assert "Overall" in text
        assert "Market data" in text

    def test_help_action_returns_help_page(self):
        from core.telegram_app_nav import ACT_HELP
        text, markup = self._call(ACT_HELP)
        assert "/start" in text

    def test_admin_action_owner_gets_admin_page(self):
        from core.telegram_app_nav import ACT_ADMIN
        from core.role_constants import ROLE_OWNER
        text, markup = self._call(ACT_ADMIN, role=ROLE_OWNER)
        assert "admin" in text.lower()

    def test_admin_action_non_owner_gets_redirect_page(self):
        from core.telegram_app_nav import ACT_ADMIN
        from core.role_constants import ROLE_USER
        text, markup = self._call(ACT_ADMIN, role=ROLE_USER)
        # Non-owner should not get admin surface; gets a redirect/info message
        buttons = _extract_button_texts(markup)
        assert len(buttons) > 0  # No dead end

    def test_unknown_action_falls_back_to_home(self):
        """Unknown action must not produce a dead end (canonical §F: no dead ends)."""
        text, markup = self._call("NONEXISTENT_ACTION_XYZ")
        assert "binarybot" in text.lower()
        buttons = _extract_button_texts(markup)
        assert len(buttons) > 0

    def test_stale_callback_handled_safely(self):
        """
        Canonical §D: stale callbacks must be handled safely.
        The dispatcher must not raise; it returns a navigable page.
        """
        for stale_action in ("", "   ", "OLD_ACTION", "UNDEFINED"):
            text, markup = self._call(stale_action)
            # Must return something navigable, no exception
            assert isinstance(text, str)
            buttons = _extract_button_texts(markup)
            assert len(buttons) > 0

    def test_duplicate_tap_same_action_no_crash(self):
        """
        Canonical §D: repeated button presses must not create duplicate panels
        or crash. Calling the same action twice must return same-shape response.
        """
        from core.telegram_app_nav import ACT_STATUS
        snap = _make_snapshot()
        text1, markup1 = self._call(ACT_STATUS, snapshot=snap)
        text2, markup2 = self._call(ACT_STATUS, snapshot=snap)
        # Same shape (no accumulation of UI)
        assert text1 == text2
        buttons1 = _extract_button_callbacks(markup1)
        buttons2 = _extract_button_callbacks(markup2)
        assert buttons1 == buttons2

    def test_all_actions_produce_non_empty_markup(self):
        """Every action must produce a non-empty keyboard (no dead ends, canonical §F)."""
        from core.telegram_app_nav import ACT_HOME, ACT_STATUS, ACT_HELP, ACT_ADMIN
        snap = _make_snapshot()
        for action in (ACT_HOME, ACT_STATUS, ACT_HELP, ACT_ADMIN):
            text, markup = self._call(action, snapshot=snap)
            buttons = _extract_button_texts(markup)
            assert len(buttons) > 0, f"Action {action} produced a dead end"
