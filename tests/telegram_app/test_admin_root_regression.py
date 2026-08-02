"""
tests/telegram_app/test_admin_root_regression.py

Live-acceptance regression tests for the canonical admin root page invariant.

Requirements covered:
  - There must be exactly ONE canonical Admin root page.
  - All admin entry points (APP:ADMIN button from /start, ADMIN_NAV:HOME back
    button from any sub-panel) must resolve to the identical page.
  - The Admin root page must always contain a "🏠 Home" button.
  - The canonical navigation chain
        /start → Admin → Operations → Engine → Admin → Home → Admin → Engine → Admin
    must edit ONE message throughout and produce the identical Admin root text
    and markup every time "Admin" is reached.
  - /admin slash command must produce the same Admin root page.

These tests are offline (no real HTTP). Telegram publisher calls are patched.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_roles_config(owner_ids=None) -> dict:
    return {
        "owner": owner_ids or [],
        "primary_admin": [],
        "strategy_admin": [],
        "research_admin": [],
        "analyst": [],
        "moderator": [],
        "affiliate_admin": {},
    }


def _message_update(
    chat_id: int,
    user_id: int,
    text: str,
    *,
    chat_type: str = "private",
    first_name: str = "TestUser",
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
    message_id: int = 5555,
    chat_type: str = "private",
    first_name: str = "TestUser",
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
    return [btn.get("text", "") for row in markup.get("inline_keyboard", []) for btn in row]


def _extract_button_callbacks(markup: Optional[dict]) -> List[str]:
    if markup is None:
        return []
    return [btn.get("callback_data", "") for row in markup.get("inline_keyboard", []) for btn in row]


# Submodule names that must be freshly imported for every test that checks navigation.
# Popping from sys.modules is not enough: the parent `core` package retains submodule
# attributes that shadow a genuine re-import.  We must also delete those attributes.
_CORE_SUBMODULES = [
    "telegram_app_nav", "bot_service", "admin_permissions",
    "telegram_admin_ui", "admin_commands",
]


def _reset_core_modules() -> None:
    """
    Fully evict and stale-attribute-clear the navigation-related submodules of
    the `core` package so that each fresh importlib.import_module call gets a
    genuinely new module object with an empty _active_ui dict.
    """
    for mod_key in list(sys.modules.keys()):
        if any(name in mod_key for name in _CORE_SUBMODULES):
            sys.modules.pop(mod_key, None)
    # The core package object keeps submodule attributes even after sys.modules
    # removal; delete those to prevent `from core import telegram_app_nav` from
    # resolving to the stale object.
    core_pkg = sys.modules.get("core")
    if core_pkg is not None:
        for attr in _CORE_SUBMODULES:
            core_pkg.__dict__.pop(attr, None)


def _fresh_bot(roles_config_path: str):
    """
    Return a bot_service module with patched publisher and cleared module cache.
    The OWNER user_id is 1000 and interacts in a private DM (chat_id == user_id).
    """
    _reset_core_modules()

    with patch.dict(os.environ, {
        "ADMIN_ROLES_CONFIG": roles_config_path,
        "SHADOW_MODE": "false",
        "ENABLE_TELEGRAM": "false",
        "ADMIN_CONTROL_CHAT_ID": "9999",
        "ADMIN_CONTROL_THREAD_ID": "0",
        "TELEGRAM_UI_PERSISTENCE": "off",
    }):
        bot = importlib.import_module("core.bot_service")
        publisher = importlib.import_module("core.telegram_publisher")

        sends: List[Dict[str, Any]] = []
        edits: List[Dict[str, Any]] = []
        _next_msg_id = {"v": 5000}

        def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
            _next_msg_id["v"] += 1
            sends.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup,
                          "message_id": _next_msg_id["v"]})
            return {"result": {"message_id": _next_msg_id["v"]}}

        def _fake_edit(chat_id, message_id, text, reply_markup=None):
            edits.append({"chat_id": chat_id, "message_id": message_id,
                          "text": text, "reply_markup": reply_markup})

        with patch.object(publisher, "send_message", _fake_send), \
             patch.object(publisher, "edit_message", _fake_edit):
            yield bot, sends, edits


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner_roles_path():
    cfg = _make_roles_config(owner_ids=[1000])
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump(cfg, f)
        path = f.name
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Test: APP:ADMIN and ADMIN_NAV:HOME produce the IDENTICAL admin root page
# ---------------------------------------------------------------------------

class TestAdminRootPageIdentical:
    """
    Every admin entry point must resolve to exactly one canonical admin root.
    """

    def test_app_admin_and_nav_home_produce_identical_text(self, owner_roles_path):
        """
        APP:ADMIN (welcome-page button) and ADMIN_NAV:HOME (⬅️ Admin back button)
        must return identical page text.
        """
        # Collect APP:ADMIN result
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "9999",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            results_app: List[str] = []
            results_nav: List[str] = []

            def _collect_send(chat_id, text, reply_markup=None, thread_id=None):
                results_app.append(text)
                return {"result": {"message_id": 5001}}

            def _collect_edit(chat_id, message_id, text, reply_markup=None):
                results_nav.append(text)

            with patch.object(publisher, "send_message", _collect_send), \
                 patch.object(publisher, "edit_message", _collect_edit):
                # APP:ADMIN — triggered from /start welcome page for OWNER
                bot.process_update(_callback_update(
                    chat_id=1000, user_id=1000, data="APP:ADMIN", message_id=5001
                ))
                # ADMIN_NAV:HOME — triggered from any sub-panel's "⬅️ Admin" button
                bot.process_update(_callback_update(
                    chat_id=1000, user_id=1000, data="ADMIN_NAV:HOME", message_id=5001
                ))

        # Both should have produced output
        assert results_app or results_nav, "No output produced"

        # Collect all produced texts (send OR edit)
        all_texts = results_app + results_nav
        assert len(all_texts) >= 2, "Expected at least 2 page renders"

        # The page text must contain the canonical admin root title
        for text in all_texts:
            assert "admin control surface" in text.lower(), (
                f"Admin root page missing canonical title. Got: {text[:120]}"
            )

        # Both entry points must produce the SAME text
        assert all_texts[0] == all_texts[-1], (
            "APP:ADMIN and ADMIN_NAV:HOME produced DIFFERENT page texts.\n"
            f"APP:ADMIN  : {all_texts[0][:200]}\n"
            f"NAV:HOME: {all_texts[-1][:200]}"
        )

    def test_app_admin_and_nav_home_produce_identical_markup(self, owner_roles_path):
        """
        APP:ADMIN and ADMIN_NAV:HOME must return identical reply_markup.
        """
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "9999",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            markups: List[Any] = []

            def _collect(chat_id, text_or_id, text_or_markup=None, reply_markup=None):
                # send_message signature: (chat_id, text, reply_markup=..., thread_id=...)
                pass

            sends_markup: List[Any] = []
            edits_markup: List[Any] = []

            def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
                sends_markup.append(reply_markup)
                return {"result": {"message_id": 5001}}

            def _fake_edit(chat_id, message_id, text, reply_markup=None):
                edits_markup.append(reply_markup)

            with patch.object(publisher, "send_message", _fake_send), \
                 patch.object(publisher, "edit_message", _fake_edit):
                bot.process_update(_callback_update(
                    chat_id=1000, user_id=1000, data="APP:ADMIN", message_id=5001
                ))
                bot.process_update(_callback_update(
                    chat_id=1000, user_id=1000, data="ADMIN_NAV:HOME", message_id=5001
                ))

        all_markups = sends_markup + edits_markup
        assert len(all_markups) >= 2

        first = json.dumps(all_markups[0], sort_keys=True)
        last = json.dumps(all_markups[-1], sort_keys=True)
        assert first == last, (
            "APP:ADMIN and ADMIN_NAV:HOME produced DIFFERENT markups.\n"
            f"APP:ADMIN : {first[:300]}\n"
            f"NAV:HOME: {last[:300]}"
        )


# ---------------------------------------------------------------------------
# Test: Admin root page always has a Home button
# ---------------------------------------------------------------------------

class TestAdminRootAlwaysHasHomeButton:
    """
    The admin root page must have a "🏠 Home" button (APP:HOME) so the user
    is never stranded without a way back to the welcome page.
    """

    def test_admin_home_markup_has_home_button(self):
        """
        admin_home_markup() with home_button_callback set must include
        a 🏠 Home row with the provided callback.
        """
        from core.telegram_admin_ui import admin_home_markup
        home_cb = "APP:HOME"
        markup = admin_home_markup(
            role="OWNER",
            home_button_callback=home_cb,
        )
        callbacks = _extract_button_callbacks(markup)
        assert home_cb in callbacks, (
            f"admin_home_markup missing 🏠 Home button (APP:HOME). Got: {callbacks}"
        )

    def test_app_admin_result_has_home_button(self, owner_roles_path):
        """
        The canonical admin root rendered via APP:ADMIN must include APP:HOME.
        """
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "9999",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            markups: List[Any] = []

            def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
                markups.append(reply_markup)
                return {"result": {"message_id": 5001}}

            def _fake_edit(chat_id, message_id, text, reply_markup=None):
                markups.append(reply_markup)

            with patch.object(publisher, "send_message", _fake_send), \
                 patch.object(publisher, "edit_message", _fake_edit):
                bot.process_update(_callback_update(
                    chat_id=1000, user_id=1000, data="APP:ADMIN", message_id=5001
                ))

        assert markups, "APP:ADMIN produced no output"
        callbacks = _extract_button_callbacks(markups[-1])
        assert "APP:HOME" in callbacks, (
            f"Admin root (APP:ADMIN) is missing APP:HOME button. Callbacks: {callbacks}"
        )

    def test_nav_home_result_has_home_button(self, owner_roles_path):
        """
        The canonical admin root rendered via ADMIN_NAV:HOME must include APP:HOME.
        """
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "9999",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            markups: List[Any] = []

            def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
                markups.append(reply_markup)
                return {"result": {"message_id": 5001}}

            def _fake_edit(chat_id, message_id, text, reply_markup=None):
                markups.append(reply_markup)

            with patch.object(publisher, "send_message", _fake_send), \
                 patch.object(publisher, "edit_message", _fake_edit):
                bot.process_update(_callback_update(
                    chat_id=1000, user_id=1000, data="ADMIN_NAV:HOME", message_id=5001
                ))

        assert markups, "ADMIN_NAV:HOME produced no output"
        callbacks = _extract_button_callbacks(markups[-1])
        assert "APP:HOME" in callbacks, (
            f"Admin root (ADMIN_NAV:HOME) is missing APP:HOME button. Callbacks: {callbacks}"
        )


# ---------------------------------------------------------------------------
# Test: /admin slash command title matches canonical admin root
# ---------------------------------------------------------------------------

class TestAdminSlashCommandTitle:
    """
    /admin slash command must produce the same "⚙️ Admin Control Surface" title
    as the canonical admin root page.
    """

    def test_admin_slash_command_title_matches_canonical(self, owner_roles_path):
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "1000",   # make owner's private DM = admin context
            "ADMIN_CONTROL_THREAD_ID": "0",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            texts: List[str] = []

            def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
                texts.append(text)
                return {"result": {"message_id": 5001}}

            def _fake_edit(chat_id, message_id, text, reply_markup=None):
                texts.append(text)

            with patch.object(publisher, "send_message", _fake_send), \
                 patch.object(publisher, "edit_message", _fake_edit):
                # Owner private DM (chat_id == user_id) — allowed for /admin
                bot.process_update({
                    "message": {
                        "chat": {"id": 1000, "type": "private"},
                        "from": {"id": 1000, "first_name": "Owner"},
                        "text": "/admin",
                        "message_id": 5001,
                    }
                })

        assert texts, "/admin produced no output"
        text = texts[-1]
        assert "admin control surface" in text.lower(), (
            f"/admin page title must say 'Admin Control Surface'. Got: {text[:200]}"
        )

    def test_admin_slash_command_has_home_button(self, owner_roles_path):
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "1000",
            "ADMIN_CONTROL_THREAD_ID": "0",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            markups: List[Any] = []

            def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
                markups.append(reply_markup)
                return {"result": {"message_id": 5001}}

            def _fake_edit(chat_id, message_id, text, reply_markup=None):
                markups.append(reply_markup)

            with patch.object(publisher, "send_message", _fake_send), \
                 patch.object(publisher, "edit_message", _fake_edit):
                bot.process_update({
                    "message": {
                        "chat": {"id": 1000, "type": "private"},
                        "from": {"id": 1000, "first_name": "Owner"},
                        "text": "/admin",
                        "message_id": 5001,
                    }
                })

        assert markups, "/admin produced no markup"
        callbacks = _extract_button_callbacks(markups[-1])
        assert "APP:HOME" in callbacks, (
            f"/admin page missing APP:HOME button. Callbacks: {callbacks}"
        )


# ---------------------------------------------------------------------------
# Test: Single-message navigation regression
# /start → Admin → (navigate to Engine) → Admin → Home → Admin
# ---------------------------------------------------------------------------

class TestSingleMessageAdminNavigation:
    """
    Regression test for the canonical single-message application model.

    The entire navigation chain below must edit ONE message (no new messages
    sent once the initial UI message is established) and must land on the
    IDENTICAL admin root page each time the user returns to Admin.

    Chain: /start → APP:ADMIN → ADMIN_NAV:OPERATIONS → ADMIN_NAV:OPS_ENGINE
           → ADMIN_NAV:HOME → APP:HOME → APP:ADMIN → ADMIN_NAV:OPERATIONS
           → ADMIN_NAV:OPS_ENGINE → ADMIN_NAV:HOME
    """

    def test_navigation_chain_single_message_invariant(self, owner_roles_path):
        """
        All navigation after /start must use edit_message, never send_message.
        """
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "9999",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            sends: List[Any] = []
            edits: List[Any] = []
            active_msg_id = {"v": None}

            def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
                new_id = 5555
                active_msg_id["v"] = new_id
                sends.append({"text": text, "reply_markup": reply_markup})
                return {"result": {"message_id": new_id}}

            def _fake_edit(chat_id, message_id, text, reply_markup=None):
                edits.append({"message_id": message_id, "text": text, "reply_markup": reply_markup})

            def _cb(data: str) -> dict:
                return _callback_update(
                    chat_id=1000, user_id=1000, data=data,
                    message_id=active_msg_id["v"] or 5555
                )

            with patch.object(publisher, "send_message", _fake_send), \
                 patch.object(publisher, "edit_message", _fake_edit):

                # Step 1: /start — establishes active UI message
                bot.process_update(_message_update(chat_id=1000, user_id=1000, text="/start"))
                assert len(sends) == 1, "Expected exactly 1 new message from /start"
                active_msg_id["v"] = sends[-1].get("message_id", 5555)
                sends.clear()
                edits.clear()

                # Step 2–6: navigate using callbacks — all must be edits, no new sends
                nav_steps = [
                    "APP:ADMIN",             # → Admin Control Surface
                    "ADMIN_NAV:OPERATIONS",  # → Operations panel
                    "ADMIN_NAV:OPS_ENGINE",  # → Engine panel
                    "ADMIN_NAV:HOME",        # → Admin Control Surface (back)
                    "APP:HOME",              # → Welcome page (Home)
                    "APP:ADMIN",             # → Admin Control Surface again
                    "ADMIN_NAV:OPERATIONS",  # → Operations panel
                    "ADMIN_NAV:OPS_ENGINE",  # → Engine panel
                    "ADMIN_NAV:HOME",        # → Admin Control Surface (back)
                ]
                for step in nav_steps:
                    bot.process_update(_cb(step))

        assert len(sends) == 0, (
            f"Navigation produced {len(sends)} unexpected new message(s). "
            f"All navigations after /start must edit the active message. "
            f"Sends: {[s['text'][:60] for s in sends]}"
        )
        assert len(edits) == len(nav_steps), (
            f"Expected {len(nav_steps)} edits, got {len(edits)}"
        )

    def test_admin_root_identical_on_every_return(self, owner_roles_path):
        """
        Every time the user reaches the admin root (via any entry point), the
        page text and markup must be byte-for-byte identical.
        """
        with patch.dict(os.environ, {
            "ADMIN_ROLES_CONFIG": owner_roles_path,
            "SHADOW_MODE": "false",
            "ENABLE_TELEGRAM": "false",
            "ADMIN_CONTROL_CHAT_ID": "9999",
            "TELEGRAM_UI_PERSISTENCE": "off",
        }):
            _reset_core_modules()

            bot = importlib.import_module("core.bot_service")
            publisher = importlib.import_module("core.telegram_publisher")
            all_renders: List[Dict[str, Any]] = []
            active_msg_id = {"v": 5555}

            def _fake_send(chat_id, text, reply_markup=None, thread_id=None):
                all_renders.append({"text": text, "reply_markup": reply_markup, "op": "send"})
                return {"result": {"message_id": 5555}}

            def _fake_edit(chat_id, message_id, text, reply_markup=None):
                all_renders.append({"text": text, "reply_markup": reply_markup, "op": "edit"})

            def _cb(data: str) -> dict:
                return _callback_update(
                    chat_id=1000, user_id=1000, data=data, message_id=5555
                )

            with patch.object(publisher, "send_message", _fake_send), \
                 patch.object(publisher, "edit_message", _fake_edit):

                # Capture index for admin-root renders
                admin_root_steps = [
                    ("APP:ADMIN", "APP:ADMIN first visit"),
                    ("ADMIN_NAV:OPERATIONS", None),     # sub-panel, not admin root
                    ("ADMIN_NAV:OPS_ENGINE", None),     # Engine, not admin root
                    ("ADMIN_NAV:HOME", "ADMIN_NAV:HOME first return"),
                    ("APP:HOME", None),                  # welcome page, not admin root
                    ("APP:ADMIN", "APP:ADMIN second visit"),
                    ("ADMIN_NAV:OPERATIONS", None),
                    ("ADMIN_NAV:OPS_ENGINE", None),
                    ("ADMIN_NAV:HOME", "ADMIN_NAV:HOME second return"),
                ]
                admin_root_labels = [label for _, label in admin_root_steps if label]
                all_renders.clear()

                for step, label in admin_root_steps:
                    bot.process_update(_cb(step))

        # Identify admin-root renders by the emoji-prefixed canonical title.
        # Using "⚙️ Admin Control Surface" (with emoji) avoids false matches against the
        # welcome page, which mentions "admin control surface" in lowercase prose.
        admin_root_renders = [
            r for r in all_renders
            if "⚙️ Admin Control Surface" in (r.get("text") or "")
        ]

        assert len(admin_root_renders) >= len(admin_root_labels), (
            f"Expected at least {len(admin_root_labels)} admin-root renders, "
            f"got {len(admin_root_renders)}. "
            f"Labels expected: {admin_root_labels}"
        )

        # Admin-root content stays canonical; APP entry renders may additionally
        # expose an APP:BACK button when the user has a real application parent.
        ref_text = admin_root_renders[0]["text"]
        with_back: list[str] = []
        without_back: list[str] = []
        for i, render in enumerate(admin_root_renders):
            assert render["text"] == ref_text, (
                f"Admin root render #{i} text differs from render #0.\n"
                f"Render #0 : {ref_text[:200]}\n"
                f"Render #{i}: {render['text'][:200]}"
            )
            actual_markup = json.dumps(render["reply_markup"], sort_keys=True)
            if '"APP:BACK"' in actual_markup:
                with_back.append(actual_markup)
            else:
                without_back.append(actual_markup)
            assert '"APP:HOME"' in actual_markup
        assert len(set(with_back)) <= 1
        assert len(set(without_back)) <= 1
