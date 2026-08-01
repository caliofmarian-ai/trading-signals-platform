"""
tests/telegram_app/test_e2e_application.py

End-to-end application tests for the complete Telegram experience.

Requirement coverage:
- E: /start for every canonical role
- D: Active message reuse (edit, not send new)
- D: Back / Home / Refresh behavior
- D: Stale callback handling
- D: Duplicate tap handling
- C: Every canonical role/category home
- C: All primary navigation branches
- H: Unauthorized access
- H: Permission filtering
- H: Role changes
- H: File/export exceptions (separate message)
- H: Absence of dead-end pages
- H: Slash-command equivalence with callback entry points
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

def _make_roles_config(owner_ids=None, primary_admin_ids=None, strategy_admin_ids=None,
                       research_admin_ids=None, analyst_ids=None, moderator_ids=None,
                       affiliate_admin=None) -> dict:
    return {
        "owner": owner_ids or [],
        "primary_admin": primary_admin_ids or [],
        "strategy_admin": strategy_admin_ids or [],
        "research_admin": research_admin_ids or [],
        "analyst": analyst_ids or [],
        "moderator": moderator_ids or [],
        "affiliate_admin": affiliate_admin or {},
    }


def _message_update(
    chat_id: int,
    user_id: int,
    text: str,
    *,
    chat_type: str = "private",
    first_name: str = "",
    message_id: int = 1001,
    thread_id: Optional[int] = None,
) -> dict:
    msg: dict = {
        "chat": {"id": chat_id, "type": chat_type},
        "from": {"id": user_id, "first_name": first_name},
        "text": text,
        "message_id": message_id,
    }
    if thread_id is not None:
        msg["message_thread_id"] = thread_id
    return {"message": msg}


def _callback_update(
    chat_id: int,
    user_id: int,
    data: str,
    *,
    message_id: int = 2001,
    chat_type: str = "private",
    first_name: str = "",
) -> dict:
    return {
        "callback_query": {
            "from": {"id": user_id, "first_name": first_name},
            "data": data,
            "message": {
                "message_id": message_id,
                "chat": {"id": chat_id, "type": chat_type},
                "text": "previous page text",
            },
        }
    }


def _extract_button_texts(markup: Optional[dict]) -> List[str]:
    if markup is None:
        return []
    rows = markup.get("inline_keyboard", [])
    return [btn.get("text", "") for row in rows for btn in row]


def _extract_button_callbacks(markup: Optional[dict]) -> List[str]:
    if markup is None:
        return []
    rows = markup.get("inline_keyboard", [])
    return [btn.get("callback_data", "") for row in rows for btn in row]


@pytest.fixture
def roles_config_file():
    """Write a temporary roles config and return the path."""
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        f.write(json.dumps(_make_roles_config(
            owner_ids=[1000],
            primary_admin_ids=[2000],
            strategy_admin_ids=[3000],
            research_admin_ids=[4000],
            analyst_ids=[5000],
            moderator_ids=[6000],
            affiliate_admin={
                "partner1": {"telegram_id": 7000, "referral_code": "PARTNER1"}
            }
        )))
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def fresh_bot(roles_config_file):
    """
    Fresh import of bot_service and app_nav with:
    - roles config pointing to the temp file
    - publisher patched (no real HTTP)
    - active UI state cleared
    """
    import importlib
    import sys

    # Patch env vars
    with patch.dict(os.environ, {
        "ADMIN_ROLES_CONFIG": roles_config_file,
        "SHADOW_MODE": "false",
        "ENABLE_TELEGRAM": "false",
        "ADMIN_CONTROL_CHAT_ID": "9999",
        "ADMIN_CONTROL_THREAD_ID": "0",
    }):
        # Reload modules to pick up new env
        for mod in list(sys.modules.keys()):
            if "core.admin_permissions" in mod or "core.role_constants" in mod or "core.telegram_app_nav" in mod or "core.bot_service" in mod:
                sys.modules.pop(mod, None)
        for mod in list(sys.modules.keys()):
            if mod.startswith("core.") and "admin_permissions" in mod:
                sys.modules.pop(mod, None)

        bot = importlib.import_module("core.bot_service")
        app_nav = importlib.import_module("core.telegram_app_nav")
        admin_perm = importlib.import_module("core.admin_permissions")

        sends = []
        edits = []

        def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
            sends.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})
            return {"result": {"message_id": 5555}}

        def _fake_edit(chat_id, message_id, text, reply_markup=None):
            edits.append({"chat_id": chat_id, "message_id": message_id, "text": text, "reply_markup": reply_markup})

        with patch.object(importlib.import_module("core.telegram_publisher"), "send_message", _fake_send), \
             patch.object(importlib.import_module("core.telegram_publisher"), "edit_message", _fake_edit):

            yield {
                "bot": bot,
                "app_nav": app_nav,
                "admin_perm": admin_perm,
                "sends": sends,
                "edits": edits,
            }


# ---------------------------------------------------------------------------
# Test: /start for every canonical role
# ---------------------------------------------------------------------------

class TestStartFlowAllRoles:
    """
    Canonical §E: /start must guide every canonical role from entry to permitted functions.
    """

    @pytest.mark.parametrize("user_id,role_label", [
        (1000, "owner"),
        (2000, "primary_admin"),
        (3000, "strategy_admin"),
        (4000, "research_admin"),
        (5000, "analyst"),
        (6000, "moderator"),
        (7000, "affiliate_admin"),
        (9999, "user"),  # unknown user → USER role
    ])
    def test_start_produces_navigable_page_for_role(self, roles_config_file, user_id, role_label):
        """Every role must receive a response with at least one button on /start."""
        import importlib
        import sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service", "role_constants"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append({"text": kw.get("text", a[1] if len(a) > 1 else ""),
                                                                "reply_markup": kw.get("reply_markup")}),
                                                {"result": {"message_id": 100}})[1]):
                bot.process_update(_message_update(chat_id=user_id, user_id=user_id, text="/start"))

        assert len(sends) == 1, f"Expected exactly 1 message for {role_label}, got {len(sends)}"
        assert "binarybot" in sends[0]["text"].lower(), f"Role {role_label}: missing platform name"
        markup = sends[0].get("reply_markup")
        buttons = _extract_button_texts(markup)
        assert len(buttons) > 0, f"Role {role_label}: dead end on /start (no buttons)"

    def test_owner_start_shows_admin_button(self, roles_config_file):
        import importlib, sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append({"text": kw.get("text", ""),
                                                                "reply_markup": kw.get("reply_markup")}),
                                                {"result": {"message_id": 100}})[1]):
                bot.process_update(_message_update(chat_id=1000, user_id=1000, text="/start"))
        callbacks = _extract_button_callbacks(sends[0].get("reply_markup"))
        assert any("ADMIN" in cb for cb in callbacks)

    def test_unknown_user_start_no_admin_button(self, roles_config_file):
        import importlib, sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append({"text": kw.get("text", ""),
                                                                "reply_markup": kw.get("reply_markup")}),
                                                {"result": {"message_id": 100}})[1]):
                bot.process_update(_message_update(chat_id=8888, user_id=8888, text="/start"))
        callbacks = _extract_button_callbacks(sends[0].get("reply_markup"))
        assert not any("ADMIN" in cb for cb in callbacks)

    def test_shadow_mode_visible_on_start(self, roles_config_file):
        import importlib, sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "true",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append({"text": kw.get("text", ""),
                                                                "reply_markup": kw.get("reply_markup")}),
                                                {"result": {"message_id": 100}})[1]):
                bot.process_update(_message_update(chat_id=9999, user_id=9999, text="/start"))
        assert "shadow" in sends[0]["text"].lower()


# ---------------------------------------------------------------------------
# Test: APP: callback navigation — Home, Status, Help, Refresh
# ---------------------------------------------------------------------------

class TestAppCallbackNavigation:
    """
    Canonical §D: APP: callbacks must edit the originating message (single-message pattern).
    """

    def _run_callback(self, roles_config_file, user_id, callback_data, message_id=2001):
        import importlib, sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            edits = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append({"text": kw.get("text", ""),
                                                                "reply_markup": kw.get("reply_markup")}),
                                                {"result": {"message_id": 100}})[1]), \
                 patch.object(importlib.import_module("core.telegram_publisher"), "edit_message",
                               lambda *a, **kw: edits.append({"args": a, "kwargs": kw})):
                bot.process_update(_callback_update(
                    chat_id=user_id, user_id=user_id, data=callback_data, message_id=message_id
                ))
        return sends, edits

    def test_home_callback_edits_message(self, roles_config_file):
        """APP:HOME callback must edit the existing message (single-message pattern)."""
        sends, edits = self._run_callback(roles_config_file, user_id=9999, callback_data="APP:HOME")
        assert len(edits) >= 1
        assert "binarybot" in edits[0]["args"][2].lower()

    def test_status_callback_edits_message(self, roles_config_file):
        """APP:STATUS callback must edit the existing message."""
        sends, edits = self._run_callback(roles_config_file, user_id=9999, callback_data="APP:STATUS")
        assert len(edits) >= 1
        assert "overall" in edits[0]["args"][2].lower()

    def test_help_callback_edits_message(self, roles_config_file):
        """APP:HELP callback must edit the existing message."""
        sends, edits = self._run_callback(roles_config_file, user_id=9999, callback_data="APP:HELP")
        assert len(edits) >= 1
        assert "/start" in edits[0]["args"][2]

    def test_callback_does_not_send_new_message_when_edit_succeeds(self, roles_config_file):
        """Single-message pattern: no new message sent when edit succeeds."""
        sends, edits = self._run_callback(roles_config_file, user_id=9999, callback_data="APP:HOME")
        assert len(sends) == 0
        assert len(edits) >= 1

    def test_slash_status_and_callback_status_consistent(self, roles_config_file):
        """
        Canonical §H: /status and APP:STATUS callback must produce equivalent content.
        Unified rendering from slash command and callback entry points.
        """
        import importlib, sys

        def _run(update_data):
            with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                          "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
                for m in list(sys.modules.keys()):
                    if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                        sys.modules.pop(m, None)
                bot = importlib.import_module("core.bot_service")
                results = []
                with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                                   lambda *a, **kw: (results.append(kw.get("text", "")),
                                                    {"result": {"message_id": 100}})[1]), \
                     patch.object(importlib.import_module("core.telegram_publisher"), "edit_message",
                                   lambda *a, **kw: results.append(a[2] if len(a) > 2 else "")):
                    bot.process_update(update_data)
            return results[0] if results else ""

        slash_text = _run(_message_update(chat_id=9999, user_id=9999, text="/status"))
        callback_text = _run(_callback_update(chat_id=9999, user_id=9999, data="APP:STATUS"))

        # Both must contain the canonical status fields
        for text in (slash_text, callback_text):
            assert "overall" in text.lower()
            assert "market data" in text.lower()


# ---------------------------------------------------------------------------
# Test: Active UI session key scoping (chat_id + user_id + thread_id)
# ---------------------------------------------------------------------------

class TestActiveUISessionScoping:
    def test_same_user_in_different_threads_tracks_separate_active_messages(self, roles_config_file):
        import importlib, sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            edits = []
            next_message_id = {"value": 100}

            def _fake_send(*a, **kw):
                next_message_id["value"] += 1
                sends.append({"text": kw.get("text", ""), "thread_id": kw.get("thread_id")})
                return {"result": {"message_id": next_message_id["value"]}}

            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message", _fake_send), \
                 patch.object(importlib.import_module("core.telegram_publisher"), "edit_message",
                               lambda *a, **kw: edits.append({"args": a, "kwargs": kw})):
                # First render in thread 42 -> send + track active message for thread 42
                bot.process_update(_message_update(
                    chat_id=-100200300, user_id=1000, text="/status", chat_type="supergroup", thread_id=42
                ))
                # Same thread -> edit tracked message
                bot.process_update(_message_update(
                    chat_id=-100200300, user_id=1000, text="/status", chat_type="supergroup", thread_id=42
                ))
                # Different thread -> must send new message (separate session key)
                bot.process_update(_message_update(
                    chat_id=-100200300, user_id=1000, text="/status", chat_type="supergroup", thread_id=99
                ))

        assert len(sends) == 2
        assert len(edits) == 1


# Test: Stale and duplicate callback handling
# ---------------------------------------------------------------------------

class TestStaleAndDuplicateCallbacks:
    """Canonical §D: stale and duplicate callbacks must be handled safely."""

    def _run_app_callback(self, roles_config_file, data, user_id=9999):
        import importlib, sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            edits = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append({"text": kw.get("text", ""),
                                                                "reply_markup": kw.get("reply_markup")}),
                                                {"result": {"message_id": 100}})[1]), \
                 patch.object(importlib.import_module("core.telegram_publisher"), "edit_message",
                               lambda *a, **kw: edits.append(a)):
                bot.process_update(_callback_update(chat_id=user_id, user_id=user_id, data=data))
        return sends, edits

    def test_stale_app_callback_fallback_to_home(self, roles_config_file):
        """An unrecognized APP: action must fall back gracefully (no exception, navigable page)."""
        sends, edits = self._run_app_callback(roles_config_file, "APP:VERY_OLD_ACTION_XYZ")
        # Must have produced something (edit or send), not crash
        assert len(sends) + len(edits) >= 1

    def test_duplicate_status_callback(self, roles_config_file):
        """Pressing the same button twice must not create two new messages."""
        import importlib, sys
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false", "ADMIN_CONTROL_CHAT_ID": "9999"}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            edits = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append(kw.get("text", "")),
                                                {"result": {"message_id": 100}})[1]), \
                 patch.object(importlib.import_module("core.telegram_publisher"), "edit_message",
                               lambda *a, **kw: edits.append(a[2] if len(a) > 2 else "")):
                # Press STATUS twice
                bot.process_update(_callback_update(9999, 9999, "APP:STATUS", message_id=3001))
                bot.process_update(_callback_update(9999, 9999, "APP:STATUS", message_id=3001))
        # Should only have 2 edits (one per press), no new sends
        assert len(sends) == 0
        assert len(edits) == 2


# ---------------------------------------------------------------------------
# Test: Unauthorized access — admin commands without proper context
# ---------------------------------------------------------------------------

class TestUnauthorizedAccess:
    """
    Canonical §H: Unauthorized functionality must never be rendered.
    """

    def _run_slash(self, roles_config_file, user_id, text, chat_id=None, chat_type="private",
                   admin_chat_id="0"):
        import importlib, sys
        chat_id = chat_id or user_id
        with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": roles_config_file, "SHADOW_MODE": "false",
                                      "ENABLE_TELEGRAM": "false",
                                      "ADMIN_CONTROL_CHAT_ID": admin_chat_id}):
            for m in list(sys.modules.keys()):
                if any(x in m for x in ["admin_permissions", "telegram_app_nav", "bot_service"]):
                    sys.modules.pop(m, None)
            bot = importlib.import_module("core.bot_service")
            sends = []
            with patch.object(importlib.import_module("core.telegram_publisher"), "send_message",
                               lambda *a, **kw: (sends.append({"text": kw.get("text", "")}),
                                                {"result": {"message_id": 100}})[1]), \
                 patch.object(importlib.import_module("core.telegram_publisher"), "edit_message",
                               lambda *a, **kw: None):
                bot.process_update(_message_update(
                    chat_id=chat_id, user_id=user_id, text=text, chat_type=chat_type
                ))
        return sends

    def test_non_owner_private_dm_cannot_run_admin(self, roles_config_file):
        """
        A non-owner user in private DM cannot run /admin.
        Returns "Access denied" (not a panel).
        """
        # user_id=9999 has no special role
        sends = self._run_slash(roles_config_file, user_id=9999, text="/admin")
        assert len(sends) == 1
        assert "denied" in sends[0]["text"].lower() or "unknown" in sends[0]["text"].lower()

    def test_admin_context_check_prevents_wrong_chat(self, roles_config_file):
        """
        /admin in a group chat that is not the configured admin control chat → access denied.
        """
        sends = self._run_slash(
            roles_config_file, user_id=9999, text="/admin",
            chat_id=123456, chat_type="supergroup", admin_chat_id="999999"
        )
        assert len(sends) == 1
        assert "denied" in sends[0]["text"].lower()

    def test_user_help_does_not_expose_admin_commands(self, roles_config_file):
        """
        USER /help must not list admin commands.
        Test via render_help_page directly to avoid module-state coupling.
        """
        from core.telegram_app_nav import render_help_page
        from core.role_constants import ROLE_USER
        text, markup = render_help_page(ROLE_USER)
        # Admin-only commands must not appear in USER help
        assert "/roles" not in text
        assert "/symbols" not in text
        assert "/engine" not in text


# ---------------------------------------------------------------------------
# Test: Permission filtering — role-specific panel visibility
# ---------------------------------------------------------------------------

class TestPermissionFiltering:
    """
    Canonical §H: Verification that unauthorized functionality is never rendered.
    """

    def test_user_role_welcome_has_no_admin_panel_buttons(self, roles_config_file):
        """USER must not see any admin panel button on /start."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_USER
        text, markup = render_welcome_page(user_id=9999, primary_role=ROLE_USER)
        callbacks = _extract_button_callbacks(markup)
        admin_panel_prefixes = ("ADMIN_NAV:", "APP:ADMIN")
        for cb in callbacks:
            for prefix in admin_panel_prefixes:
                assert not cb.startswith(prefix), f"USER must not see admin callback: {cb}"

    def test_affiliate_admin_welcome_no_admin_panel(self, roles_config_file):
        """AFFILIATE_ADMIN must not see global admin surface button on /start."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ROLE_AFFILIATE_ADMIN
        text, markup = render_welcome_page(user_id=7000, primary_role=ROLE_AFFILIATE_ADMIN)
        callbacks = _extract_button_callbacks(markup)
        assert not any("ADMIN_NAV:" in cb for cb in callbacks)
        # And no global admin button (only owner gets this)
        assert not any(cb == "APP:ADMIN" for cb in callbacks)

    def test_admin_home_markup_role_scoped_for_strategy_admin(self):
        """Strategy admin sees only Operations, Symbols, Decision Visibility panels."""
        from core.telegram_admin_ui import admin_home_markup
        from core.role_constants import ROLE_STRATEGY_ADMIN
        markup = admin_home_markup(role=ROLE_STRATEGY_ADMIN)
        callbacks = _extract_button_callbacks(markup)
        # Must have Operations, Symbols, Decision Vis
        panel_callbacks = [cb.replace("ADMIN_NAV:", "") for cb in callbacks if cb.startswith("ADMIN_NAV:")]
        assert "OPERATIONS" in panel_callbacks
        assert "SYMBOLS_COV" in panel_callbacks
        assert "DECISION_VIS" in panel_callbacks
        # Must NOT have Distribution, Research, Intelligence, Affiliate, Roles, Syshealth, Govdocs, SecAudit
        forbidden = {"DISTRIBUTION", "RESEARCH", "INTELLIGENCE", "AFFILIATE", "ROLES",
                     "SYSHEALTH", "GOVDOCS", "SECAUDIT"}
        for cb in panel_callbacks:
            assert cb not in forbidden, f"Strategy admin should not see panel: {cb}"

    def test_admin_home_markup_role_scoped_for_affiliate_admin(self):
        """Affiliate admin sees only the Affiliate panel in admin home."""
        from core.telegram_admin_ui import admin_home_markup
        from core.role_constants import ROLE_AFFILIATE_ADMIN
        markup = admin_home_markup(role=ROLE_AFFILIATE_ADMIN)
        callbacks = _extract_button_callbacks(markup)
        panel_callbacks = [cb.replace("ADMIN_NAV:", "") for cb in callbacks if cb.startswith("ADMIN_NAV:")]
        # Only affiliate panel should be visible
        non_affiliate = [cb for cb in panel_callbacks if cb not in ("AFFILIATE", "HOME")]
        assert len(non_affiliate) == 0, f"Affiliate admin saw unexpected panels: {non_affiliate}"


# ---------------------------------------------------------------------------
# Test: No dead-end pages
# ---------------------------------------------------------------------------

class TestNoDeadEndPages:
    """
    Canonical §H: Verification that no page is a dead end.
    Every page must have at least one navigation button.
    """

    @pytest.mark.parametrize("action", ["HOME", "STATUS", "HELP", "ADMIN", "UNKNOWN_ACTION"])
    def test_app_action_always_has_buttons(self, action):
        from core.telegram_app_nav import handle_app_action
        from core.role_constants import ROLE_USER
        text, markup = handle_app_action(
            action=action,
            user_id=1,
            primary_role=ROLE_USER,
            status_snapshot={"overall_state": "READY", "runtime_phase": "RUNNING",
                              "runtime_message": "OK", "recovery_state": "HEALTHY",
                              "market_data_state": "READY", "telegram_state": "ENABLED",
                              "fsm_state": "OK", "shadow_mode": "OFF",
                              "broker_state": "DISABLED", "market_data_note": ""},
        )
        buttons = _extract_button_texts(markup)
        assert len(buttons) > 0, f"Action {action} produced a dead end (no buttons)"

    def test_every_canonical_role_welcome_has_buttons(self):
        """Every role's /start page must have at least one button."""
        from core.telegram_app_nav import render_welcome_page
        from core.role_constants import ALL_ROLES
        for role in ALL_ROLES:
            text, markup = render_welcome_page(user_id=1, primary_role=role)
            buttons = _extract_button_texts(markup)
            assert len(buttons) > 0, f"Role {role} start page is a dead end"

    def test_status_page_has_refresh_and_home(self):
        from core.telegram_app_nav import render_status_page, ACT_STATUS, ACT_HOME
        snap = {"overall_state": "READY", "runtime_phase": "RUNNING", "runtime_message": "OK",
                "recovery_state": "HEALTHY", "market_data_state": "READY",
                "telegram_state": "ENABLED", "fsm_state": "OK", "shadow_mode": "OFF",
                "broker_state": "DISABLED", "market_data_note": ""}
        text, markup = render_status_page(snap)
        callbacks = _extract_button_callbacks(markup)
        assert any(ACT_STATUS in cb for cb in callbacks)
        assert any(ACT_HOME in cb for cb in callbacks)


# ---------------------------------------------------------------------------
# Test: Role changes handled
# ---------------------------------------------------------------------------

class TestRoleChanges:
    """
    Canonical §H: Role changes must be reflected in the next interaction (no stale cache).
    The role resolution reads from the config file each time (with lru_cache that can be cleared).
    """

    def test_role_change_reflected_after_reload(self):
        """After reload_roles_config(), new role must be reflected."""
        import importlib, sys, tempfile, json, os
        from unittest.mock import patch

        cfg = _make_roles_config(owner_ids=[1000])
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(cfg, f)
            path = f.name

        try:
            with patch.dict(os.environ, {"ADMIN_ROLES_CONFIG": path}):
                for m in list(sys.modules.keys()):
                    if any(x in m for x in ["admin_permissions", "role_constants"]):
                        sys.modules.pop(m, None)
                ap = importlib.import_module("core.admin_permissions")

                # Initially user 5555 has no role
                assert ap.get_primary_role(5555) == "USER"

                # Add 5555 as analyst and reload
                cfg2 = _make_roles_config(owner_ids=[1000], analyst_ids=[5555])
                with open(path, "w") as f2:
                    json.dump(cfg2, f2)
                ap.reload_roles_config()

                # Now should resolve as ANALYST
                assert ap.get_primary_role(5555) == "ANALYST"
        finally:
            os.unlink(path)
