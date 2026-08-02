"""
tests/telegram_app/test_real_navigation.py

Focused tests for Issue #38: real Back, Home, and Refresh navigation.

Coverage:
- ACT_BACK constant exists in telegram_app_nav
- Bounded navigation history (push, pop, can_go_back, clear)
- BACK action in handle_app_action: returns parent or falls back to Home
- Restart/state-loss: empty history returns Home (safe fallback)
- BACK is bounded (max depth prevents loops)
- HOME clears direction (fresh start from Home always works)
- Refresh (ACT_STATUS, ACT_HELP) does not modify history
- /start hard reset clears navigation history
- Admin markup parent_action parameter: strategy_markup Back → OPERATIONS
- symbols_toggle_markup(parent_action="HOME") Back → HOME
- symbols_toggle_markup(parent_action="STRATEGY") Back → STRATEGY and Refresh → SYMBOLS
- engine_markup(parent_action="OPERATIONS") Back → OPERATIONS
- engine_markup(parent_action="SYSHEALTH") Back → SYSHEALTH
- diagnose_markup(parent_action="OPERATIONS") Back → OPERATIONS
- diagnose_markup(parent_action="SYSHEALTH") Back → SYSHEALTH
- CANONICAL_ADMIN_PARENT_MAP covers all expected pages
- Role isolation: different sessions have independent history
- Cross-chat isolation: (chat_id, user_id, thread_id) session key
- No dead ends after BACK navigation
- Strategy-context Refresh (SYMBOLS) stays in strategy context
- SYMBOLS_COV-context Refresh (SYMBOLS_COV) stays in admin-home context
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import patch

# Ensure send/ is on the import path.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SEND_ROOT = _REPO_ROOT / "send"
if str(_SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_SEND_ROOT))

import importlib
import pytest
from typing import Dict, Any


def _purge():
    prefixes = ("core", "runtime", "state_store", "monitoring", "snapshots")
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _cbs(markup: Dict) -> list:
    """Flatten all callback_data values from an inline keyboard."""
    return [
        btn["callback_data"]
        for row in markup.get("inline_keyboard", [])
        for btn in row
    ]


def _texts(markup: Dict) -> list:
    """Flatten all button text values from an inline keyboard."""
    return [
        btn["text"]
        for row in markup.get("inline_keyboard", [])
        for btn in row
    ]


def _message_update(
    chat_id: int,
    user_id: int,
    text: str,
    *,
    chat_type: str = "private",
    message_id: int = 1001,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    message: Dict[str, Any] = {
        "chat": {"id": chat_id, "type": chat_type},
        "from": {"id": user_id, "first_name": "Alice"},
        "text": text,
        "message_id": message_id,
    }
    if thread_id is not None:
        message["message_thread_id"] = thread_id
    return {"message": message}


def _callback_update(
    chat_id: int,
    user_id: int,
    data: str,
    *,
    chat_type: str = "private",
    message_id: int = 2001,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    message: Dict[str, Any] = {
        "chat": {"id": chat_id, "type": chat_type},
        "message_id": message_id,
        "text": "previous page text",
    }
    if thread_id is not None:
        message["message_thread_id"] = thread_id
    return {
        "callback_query": {
            "id": f"cb-{message_id}",
            "from": {"id": user_id, "first_name": "Alice"},
            "data": data,
            "message": message,
        }
    }


def _find_callback(markup: Dict, needle: str) -> Optional[str]:
    for row in markup.get("inline_keyboard", []):
        for btn in row:
            callback = btn.get("callback_data", "")
            if needle in callback:
                return callback
    return None


class _FakePublisher:
    def __init__(self) -> None:
        self._next_id = 5000
        self.sends: list[Dict[str, Any]] = []
        self.edits: list[Dict[str, Any]] = []
        self.acks: list[str] = []

    def send_message(self, chat_id, text, reply_markup=None, thread_id=None):
        message_id = self._next_id
        self._next_id += 1
        self.sends.append({
            "chat_id": chat_id,
            "text": text,
            "reply_markup": reply_markup,
            "thread_id": thread_id,
            "message_id": message_id,
        })
        return {"ok": True, "result": {"message_id": message_id}}

    def edit_message(self, chat_id, message_id, text=None, reply_markup=None):
        self.edits.append({
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": reply_markup,
        })
        return {"ok": True, "result": {"message_id": message_id}}

    def answer_callback_query(self, callback_query_id, text="", show_alert=False):
        self.acks.append(callback_query_id)
        return {"ok": True}

    def delete_message(self, chat_id, message_id):
        return {
            "outcome": "deleted",
            "chat_id": chat_id,
            "message_id": message_id,
            "error_code": None,
            "description": None,
        }


# ---------------------------------------------------------------------------
# ACT_BACK constant
# ---------------------------------------------------------------------------

class TestActBackConstant:
    def test_act_back_constant_exists(self):
        _purge()
        from core.telegram_app_nav import ACT_BACK
        assert ACT_BACK == "BACK"

    def test_act_back_distinct_from_home(self):
        _purge()
        from core.telegram_app_nav import ACT_BACK, ACT_HOME
        assert ACT_BACK != ACT_HOME

    def test_make_callback_back(self):
        _purge()
        from core.telegram_app_nav import make_callback, ACT_BACK, APP_NAV_PREFIX
        cb = make_callback(ACT_BACK)
        assert cb == f"{APP_NAV_PREFIX}BACK"

    def test_parse_app_action_back(self):
        _purge()
        from core.telegram_app_nav import parse_app_action, APP_NAV_PREFIX, ACT_BACK
        assert parse_app_action(f"{APP_NAV_PREFIX}{ACT_BACK}") == ACT_BACK

    def test_parse_versioned_app_callback(self):
        _purge()
        from core.telegram_app_nav import parse_app_callback
        parsed = parse_app_callback("APP:7:STATUS")
        assert parsed == {"action": "STATUS", "generation": 7}


# ---------------------------------------------------------------------------
# Bounded navigation history
# ---------------------------------------------------------------------------

class TestBoundedNavHistory:
    """Canonical bounded Back history model."""

    def test_push_and_pop(self):
        _purge()
        from core.telegram_app_nav import push_nav_action, pop_nav_action, clear_nav_history
        clear_nav_history(1001, chat_id=1001)
        push_nav_action(1001, chat_id=1001, action="STATUS")
        assert pop_nav_action(1001, chat_id=1001) == "STATUS"

    def test_pop_empty_returns_none(self):
        _purge()
        from core.telegram_app_nav import pop_nav_action, clear_nav_history
        clear_nav_history(1002, chat_id=1002)
        assert pop_nav_action(1002, chat_id=1002) is None

    def test_can_go_back_true_after_push(self):
        _purge()
        from core.telegram_app_nav import push_nav_action, nav_can_go_back, clear_nav_history
        clear_nav_history(1003, chat_id=1003)
        push_nav_action(1003, chat_id=1003, action="HELP")
        assert nav_can_go_back(1003, chat_id=1003) is True

    def test_can_go_back_false_after_clear(self):
        _purge()
        from core.telegram_app_nav import push_nav_action, nav_can_go_back, clear_nav_history
        push_nav_action(1004, chat_id=1004, action="HELP")
        clear_nav_history(1004, chat_id=1004)
        assert nav_can_go_back(1004, chat_id=1004) is False

    def test_history_stack_is_lifo(self):
        _purge()
        from core.telegram_app_nav import push_nav_action, pop_nav_action, clear_nav_history
        clear_nav_history(1005, chat_id=1005)
        push_nav_action(1005, chat_id=1005, action="STATUS")
        push_nav_action(1005, chat_id=1005, action="HELP")
        # pop should return most recent first
        assert pop_nav_action(1005, chat_id=1005) == "HELP"
        assert pop_nav_action(1005, chat_id=1005) == "STATUS"
        assert pop_nav_action(1005, chat_id=1005) is None

    def test_duplicate_consecutive_entries_not_pushed(self):
        """Consecutive duplicate entries are suppressed to prevent trivial loops."""
        _purge()
        from core.telegram_app_nav import push_nav_action, pop_nav_action, clear_nav_history
        clear_nav_history(1006, chat_id=1006)
        push_nav_action(1006, chat_id=1006, action="STATUS")
        push_nav_action(1006, chat_id=1006, action="STATUS")  # duplicate
        assert pop_nav_action(1006, chat_id=1006) == "STATUS"
        assert pop_nav_action(1006, chat_id=1006) is None

    def test_history_bounded_at_max_depth(self):
        """History must never exceed _NAV_HISTORY_MAX_DEPTH entries."""
        _purge()
        from core.telegram_app_nav import (
            push_nav_action, pop_nav_action, clear_nav_history,
            _NAV_HISTORY_MAX_DEPTH,
        )
        clear_nav_history(1007, chat_id=1007)
        actions = [f"PAGE_{i}" for i in range(_NAV_HISTORY_MAX_DEPTH + 5)]
        for i, act in enumerate(actions):
            push_nav_action(1007, chat_id=1007, action=act)
        # Collect what's in the history
        collected = []
        while True:
            item = pop_nav_action(1007, chat_id=1007)
            if item is None:
                break
            collected.append(item)
        assert len(collected) <= _NAV_HISTORY_MAX_DEPTH

    def test_session_isolation_different_users(self):
        """Different users must have independent histories."""
        _purge()
        from core.telegram_app_nav import push_nav_action, pop_nav_action, clear_nav_history
        clear_nav_history(2001, chat_id=2001)
        clear_nav_history(2002, chat_id=2002)
        push_nav_action(2001, chat_id=2001, action="STATUS")
        push_nav_action(2002, chat_id=2002, action="HELP")
        assert pop_nav_action(2001, chat_id=2001) == "STATUS"
        assert pop_nav_action(2002, chat_id=2002) == "HELP"

    def test_session_isolation_different_chats(self):
        """Same user in different chats must have independent histories."""
        _purge()
        from core.telegram_app_nav import push_nav_action, pop_nav_action
        push_nav_action(3001, chat_id=100, action="STATUS")
        push_nav_action(3001, chat_id=200, action="HELP")
        assert pop_nav_action(3001, chat_id=100) == "STATUS"
        assert pop_nav_action(3001, chat_id=200) == "HELP"

    def test_session_isolation_different_thread_ids(self):
        """Same user+chat with different thread_ids must have independent histories."""
        _purge()
        from core.telegram_app_nav import push_nav_action, pop_nav_action
        push_nav_action(4001, chat_id=-100001, thread_id=10, action="STATUS")
        push_nav_action(4001, chat_id=-100001, thread_id=20, action="HELP")
        assert pop_nav_action(4001, chat_id=-100001, thread_id=10) == "STATUS"
        assert pop_nav_action(4001, chat_id=-100001, thread_id=20) == "HELP"


# ---------------------------------------------------------------------------
# handle_app_action — BACK behavior
# ---------------------------------------------------------------------------

class TestHandleAppActionBack:
    """ACT_BACK in handle_app_action."""

    def _call(self, nav_module, action, user_id=5001, role="USER", chat_id=None, thread_id=None, snapshot=None):
        """Call handle_app_action on an already-imported module (preserves history state)."""
        return nav_module.handle_app_action(
            action=action,
            user_id=user_id,
            primary_role=role,
            chat_id=chat_id,
            thread_id=thread_id,
            status_snapshot=snapshot or {},
        )

    def test_back_with_empty_history_returns_home(self):
        """State-loss/restart fallback: empty history returns Home page."""
        _purge()
        import core.telegram_app_nav as nav
        nav.clear_nav_history(5001, chat_id=5001)
        text, markup = self._call(nav, nav.ACT_BACK, user_id=5001, chat_id=5001)
        assert "binarybot" in text.lower()
        assert len(_texts(markup)) > 0

    def test_back_with_history_returns_parent(self):
        """BACK returns the pushed parent page."""
        _purge()
        import core.telegram_app_nav as nav
        nav.clear_nav_history(5002, chat_id=5002)
        nav.push_nav_action(5002, chat_id=5002, action=nav.ACT_STATUS)
        text, markup = self._call(nav, nav.ACT_BACK, user_id=5002, chat_id=5002, snapshot={})
        # Should render status page (parent was STATUS)
        assert "Status" in text or "Overall" in text

    def test_back_from_home_returns_home(self):
        """Back with HOME on stack → falls back to Home (HOME is root, not a real parent)."""
        _purge()
        import core.telegram_app_nav as nav
        nav.clear_nav_history(5003, chat_id=5003)
        nav.push_nav_action(5003, chat_id=5003, action=nav.ACT_HOME)
        text, markup = self._call(nav, nav.ACT_BACK, user_id=5003, chat_id=5003)
        assert "binarybot" in text.lower()

    def test_back_fallback_safe_without_chat_id(self):
        """If no chat_id provided, BACK safely falls back to Home."""
        _purge()
        import core.telegram_app_nav as nav
        text, markup = self._call(nav, nav.ACT_BACK, user_id=5004, chat_id=None)
        assert "binarybot" in text.lower()
        assert len(_texts(markup)) > 0

    def test_back_result_has_no_dead_end(self):
        """BACK result always has at least one button (no dead ends, canonical §F)."""
        _purge()
        import core.telegram_app_nav as nav
        nav.clear_nav_history(5005, chat_id=5005)
        text, markup = self._call(nav, nav.ACT_BACK, user_id=5005, chat_id=5005)
        assert len(_texts(markup)) > 0

    def test_multiple_back_presses_bounded(self):
        """Repeated Back presses eventually reach Home; no infinite loop."""
        _purge()
        import core.telegram_app_nav as nav
        nav.clear_nav_history(5006, chat_id=5006)
        for act in [nav.ACT_STATUS, nav.ACT_HELP, nav.ACT_STATUS, nav.ACT_HELP, nav.ACT_STATUS]:
            nav.push_nav_action(5006, chat_id=5006, action=act)

        for _ in range(10):
            text, markup = nav.handle_app_action(
                nav.ACT_BACK, user_id=5006, primary_role="USER",
                chat_id=5006, status_snapshot={},
            )
            assert len(_texts(markup)) > 0  # Never a dead end


# ---------------------------------------------------------------------------
# /start hard reset clears navigation history
# ---------------------------------------------------------------------------

class TestStartHardResetClearsHistory:
    def test_prepare_start_hard_reset_clears_nav_history(self):
        """prepare_start_hard_reset must clear navigation history for the session."""
        _purge()
        import core.telegram_app_nav as nav
        import os
        os.environ["TELEGRAM_UI_PERSISTENCE"] = "disabled"
        try:
            nav.push_nav_action(6001, chat_id=6001, action="STATUS")
            assert nav.nav_can_go_back(6001, chat_id=6001)
            nav.prepare_start_hard_reset(chat_id=6001, user_id=6001)
            assert not nav.nav_can_go_back(6001, chat_id=6001)
        finally:
            os.environ.pop("TELEGRAM_UI_PERSISTENCE", None)


# ---------------------------------------------------------------------------
# Admin markup: parent_action parameter
# ---------------------------------------------------------------------------

class TestAdminMarkupParentAction:
    """Canonical parent navigation for admin tree markup functions."""

    def test_strategy_markup_back_to_operations(self):
        """strategy_markup Back must navigate to OPERATIONS (immediate parent)."""
        _purge()
        from core.telegram_admin_ui import strategy_markup, CALLBACK_PREFIX
        markup = strategy_markup()
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}OPERATIONS" in cbs, (
            "strategy_markup Back must target OPERATIONS, not Admin Home"
        )
        assert f"{CALLBACK_PREFIX}HOME" not in cbs, (
            "strategy_markup must not have a direct HOME button (use OPERATIONS as parent)"
        )

    def test_symbols_toggle_default_parent_home(self):
        """symbols_toggle_markup with default parent_action='HOME' Back → admin Home."""
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup, CALLBACK_PREFIX
        markup = symbols_toggle_markup(["EURUSD"], [], parent_action="HOME")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}HOME" in cbs
        assert f"{CALLBACK_PREFIX}STRATEGY" not in cbs

    def test_symbols_toggle_strategy_parent(self):
        """symbols_toggle_markup(parent_action='STRATEGY') Back → STRATEGY."""
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup, CALLBACK_PREFIX
        markup = symbols_toggle_markup(["EURUSD"], [], parent_action="STRATEGY")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}STRATEGY" in cbs
        assert f"{CALLBACK_PREFIX}HOME" not in cbs

    def test_symbols_toggle_strategy_refresh_targets_symbols(self):
        """When parent is STRATEGY, Refresh should target SYMBOLS (stays in strategy context)."""
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup, CALLBACK_PREFIX
        markup = symbols_toggle_markup(["EURUSD"], [], parent_action="STRATEGY")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}SYMBOLS" in cbs

    def test_symbols_toggle_home_refresh_targets_symbols_cov(self):
        """When parent is HOME, Refresh should target SYMBOLS_COV (preserves admin-home context)."""
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup, CALLBACK_PREFIX
        markup = symbols_toggle_markup(["EURUSD"], [], parent_action="HOME")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}SYMBOLS_COV" in cbs

    def test_engine_markup_default_parent_home(self):
        """engine_markup with default parent Back → admin Home."""
        _purge()
        from core.telegram_admin_ui import engine_markup, CALLBACK_PREFIX
        markup = engine_markup(include_roles_reload=False, parent_action="HOME")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}HOME" in cbs

    def test_engine_markup_operations_parent(self):
        """engine_markup(parent_action='OPERATIONS') Back → OPERATIONS."""
        _purge()
        from core.telegram_admin_ui import engine_markup, CALLBACK_PREFIX
        markup = engine_markup(include_roles_reload=False, parent_action="OPERATIONS")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}OPERATIONS" in cbs
        assert f"{CALLBACK_PREFIX}HOME" not in cbs

    def test_engine_markup_syshealth_parent(self):
        """engine_markup(parent_action='SYSHEALTH') Back → SYSHEALTH."""
        _purge()
        from core.telegram_admin_ui import engine_markup, CALLBACK_PREFIX
        markup = engine_markup(include_roles_reload=False, parent_action="SYSHEALTH")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}SYSHEALTH" in cbs
        assert f"{CALLBACK_PREFIX}HOME" not in cbs

    def test_diagnose_markup_default_parent_home(self):
        """diagnose_markup with default parent Back → admin Home."""
        _purge()
        from core.telegram_admin_ui import diagnose_markup, CALLBACK_PREFIX
        markup = diagnose_markup(parent_action="HOME")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}HOME" in cbs

    def test_diagnose_markup_operations_parent(self):
        """diagnose_markup(parent_action='OPERATIONS') Back → OPERATIONS (OPS_DIAGNOSE context)."""
        _purge()
        from core.telegram_admin_ui import diagnose_markup, CALLBACK_PREFIX
        markup = diagnose_markup(parent_action="OPERATIONS")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}OPERATIONS" in cbs
        assert f"{CALLBACK_PREFIX}HOME" not in cbs

    def test_diagnose_markup_syshealth_parent(self):
        """diagnose_markup(parent_action='SYSHEALTH') Back → SYSHEALTH (SH_DIAGNOSE context)."""
        _purge()
        from core.telegram_admin_ui import diagnose_markup, CALLBACK_PREFIX
        markup = diagnose_markup(parent_action="SYSHEALTH")
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}SYSHEALTH" in cbs
        assert f"{CALLBACK_PREFIX}HOME" not in cbs

    def test_diagnose_markup_operations_audit_is_contextual(self):
        _purge()
        from core.telegram_admin_ui import diagnose_markup, CALLBACK_PREFIX
        markup = diagnose_markup(parent_action="OPERATIONS")
        assert f"{CALLBACK_PREFIX}OPS_AUDIT" in _cbs(markup)

    def test_diagnose_markup_syshealth_audit_is_contextual(self):
        _purge()
        from core.telegram_admin_ui import diagnose_markup, CALLBACK_PREFIX
        markup = diagnose_markup(parent_action="SYSHEALTH")
        assert f"{CALLBACK_PREFIX}DIAG_SH_AUDIT" in _cbs(markup)

    def test_all_markup_functions_no_dead_end(self):
        """All markup functions must produce at least one button (no dead ends, canonical §F)."""
        _purge()
        from core.telegram_admin_ui import (
            strategy_markup, symbols_markup, engine_markup, diagnose_markup,
            operations_markup, decision_visibility_markup, distribution_markup,
            research_markup, intelligence_markup, roles_identity_markup,
            system_health_markup, governance_docs_markup, security_audit_markup,
            files_home_markup, standard_back_markup,
        )
        fns = [
            (strategy_markup, []),
            (symbols_markup, []),
            (lambda: engine_markup(include_roles_reload=False), []),
            (lambda: engine_markup(include_roles_reload=False, parent_action="OPERATIONS"), []),
            (lambda: engine_markup(include_roles_reload=False, parent_action="SYSHEALTH"), []),
            (lambda: diagnose_markup(parent_action="HOME"), []),
            (lambda: diagnose_markup(parent_action="OPERATIONS"), []),
            (lambda: diagnose_markup(parent_action="SYSHEALTH"), []),
            (operations_markup, []),
            (decision_visibility_markup, []),
            (distribution_markup, []),
            (lambda: research_markup(), []),
            (intelligence_markup, []),
            (lambda: roles_identity_markup(can_reload=False), []),
            (system_health_markup, []),
            (lambda: governance_docs_markup([]), []),
            (security_audit_markup, []),
            (files_home_markup, []),
            (standard_back_markup, []),
        ]
        for fn, _ in fns:
            markup = fn()
            btns = _texts(markup)
            assert len(btns) > 0, f"{fn} produced a dead end"


# ---------------------------------------------------------------------------
# Canonical admin parent map
# ---------------------------------------------------------------------------

class TestCanonicalAdminParentMap:
    """CANONICAL_ADMIN_PARENT_MAP covers the expected admin tree pages."""

    def test_parent_map_exists(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert isinstance(CANONICAL_ADMIN_PARENT_MAP, dict)
        assert len(CANONICAL_ADMIN_PARENT_MAP) > 0

    def test_strategy_parent_is_operations(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert CANONICAL_ADMIN_PARENT_MAP.get("STRATEGY") == "OPERATIONS"

    def test_symbols_parent_is_strategy(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert CANONICAL_ADMIN_PARENT_MAP.get("SYMBOLS") == "STRATEGY"

    def test_operations_parent_is_home(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert CANONICAL_ADMIN_PARENT_MAP.get("OPERATIONS") == "HOME"

    def test_ops_engine_parent_is_operations(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert CANONICAL_ADMIN_PARENT_MAP.get("OPS_ENGINE") == "OPERATIONS"

    def test_sh_engine_parent_is_syshealth(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert CANONICAL_ADMIN_PARENT_MAP.get("SH_ENGINE") == "SYSHEALTH"

    def test_ops_diagnose_parent_is_operations(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert CANONICAL_ADMIN_PARENT_MAP.get("OPS_DIAGNOSE") == "OPERATIONS"

    def test_sh_diagnose_parent_is_syshealth(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        assert CANONICAL_ADMIN_PARENT_MAP.get("SH_DIAGNOSE") == "SYSHEALTH"

    def test_all_panel_pages_have_home_parent(self):
        _purge()
        from core.telegram_admin_ui import CANONICAL_ADMIN_PARENT_MAP
        direct_home_children = [
            "OPERATIONS", "SYMBOLS_COV", "DECISION_VIS", "DISTRIBUTION",
            "RESEARCH", "INTELLIGENCE", "AFFILIATE", "ROLES",
            "SYSHEALTH", "GOVDOCS", "SECAUDIT",
        ]
        for page in direct_home_children:
            assert CANONICAL_ADMIN_PARENT_MAP.get(page) == "HOME", (
                f"{page} should have HOME as parent (direct child of admin root)"
            )


# ---------------------------------------------------------------------------
# Refresh: does not add to history, re-renders same page
# ---------------------------------------------------------------------------

class TestRefreshBehavior:
    """Refresh re-renders the current page without modifying navigation history."""

    def test_status_refresh_preserves_history(self):
        """ACT_STATUS (Refresh on status page) does not pop or modify history."""
        _purge()
        import core.telegram_app_nav as nav
        nav.clear_nav_history(7001, chat_id=7001)
        nav.push_nav_action(7001, chat_id=7001, action=nav.ACT_HELP)
        # Simulate Refresh on status page (does not affect history)
        nav.handle_app_action(
            nav.ACT_STATUS, user_id=7001, primary_role="USER",
            chat_id=7001, status_snapshot={},
        )
        # History should still have HELP as last entry (not modified by refresh)
        # (Refresh doesn't push/pop in handle_app_action itself)
        item = nav.pop_nav_action(7001, chat_id=7001)
        assert item == nav.ACT_HELP

    def test_diagnose_refresh_button_is_diagnose(self):
        """diagnose_markup Refresh targets DIAGNOSE (re-renders current page)."""
        _purge()
        from core.telegram_admin_ui import diagnose_markup, CALLBACK_PREFIX
        markup = diagnose_markup()
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}DIAGNOSE" in cbs

    def test_decision_vis_refresh_is_self(self):
        """decision_visibility_markup Refresh targets DECISION_VIS."""
        _purge()
        from core.telegram_admin_ui import decision_visibility_markup, CALLBACK_PREFIX
        markup = decision_visibility_markup()
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}DECISION_VIS" in cbs

    def test_distribution_refresh_is_self(self):
        _purge()
        from core.telegram_admin_ui import distribution_markup, CALLBACK_PREFIX
        markup = distribution_markup()
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}DISTRIBUTION" in cbs

    def test_research_refresh_is_self(self):
        _purge()
        from core.telegram_admin_ui import research_markup, CALLBACK_PREFIX
        markup = research_markup()
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}RESEARCH" in cbs

    def test_intelligence_refresh_is_self(self):
        _purge()
        from core.telegram_admin_ui import intelligence_markup, CALLBACK_PREFIX
        markup = intelligence_markup()
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}INTELLIGENCE" in cbs

    def test_engine_refresh_is_self(self):
        _purge()
        from core.telegram_admin_ui import engine_markup, CALLBACK_PREFIX
        markup = engine_markup(include_roles_reload=False)
        cbs = _cbs(markup)
        assert f"{CALLBACK_PREFIX}ENGINE" in cbs

    def test_status_refresh_is_self_app_nav(self):
        """APP: render_status_page Refresh targets ACT_STATUS (re-renders current page)."""
        _purge()
        from core.telegram_app_nav import render_status_page, make_callback, ACT_STATUS
        text, markup = render_status_page({})
        cbs = _cbs(markup)
        assert make_callback(ACT_STATUS) in cbs


# ---------------------------------------------------------------------------
# Home navigation: always returns to role-scoped welcome page
# ---------------------------------------------------------------------------

class TestHomeNavigation:
    """Home returns to the role-scoped welcome page for all roles."""

    def test_home_returns_welcome_page(self):
        _purge()
        from core.telegram_app_nav import handle_app_action, ACT_HOME
        text, markup = handle_app_action(
            ACT_HOME, user_id=8001, primary_role="USER",
        )
        assert "binarybot" in text.lower()
        assert len(_texts(markup)) > 0

    def test_app_nav_status_page_has_home_button(self):
        _purge()
        from core.telegram_app_nav import render_status_page, make_callback, ACT_HOME
        _, markup = render_status_page({})
        cbs = _cbs(markup)
        assert make_callback(ACT_HOME) in cbs

    def test_app_nav_help_page_has_home_button(self):
        _purge()
        from core.telegram_app_nav import render_help_page, make_callback, ACT_HOME
        _, markup = render_help_page("USER")
        cbs = _cbs(markup)
        assert make_callback(ACT_HOME) in cbs

    def test_admin_home_markup_has_home_callback(self):
        """Admin home markup includes the APP:HOME button when home_button_callback is provided."""
        _purge()
        from core.telegram_admin_ui import admin_home_markup
        from core.telegram_app_nav import make_callback, ACT_HOME
        home_cb = make_callback(ACT_HOME)
        markup = admin_home_markup(home_button_callback=home_cb)
        cbs = _cbs(markup)
        assert home_cb in cbs

    def test_admin_home_markup_without_home_callback(self):
        """Admin home markup without home_button_callback has no HOME button."""
        _purge()
        from core.telegram_admin_ui import admin_home_markup
        from core.telegram_app_nav import make_callback, ACT_HOME
        markup = admin_home_markup()
        cbs = _cbs(markup)
        assert make_callback(ACT_HOME) not in cbs


# ---------------------------------------------------------------------------
# Admin Home distinct from App Home
# ---------------------------------------------------------------------------

class TestAdminHomeDistinct:
    """Admin Home (ADMIN_NAV:HOME) is distinct from App Home (APP:HOME)."""

    def test_admin_nav_prefix_distinct_from_app_prefix(self):
        _purge()
        from core.telegram_admin_ui import CALLBACK_PREFIX as ADMIN_PREFIX
        from core.telegram_app_nav import APP_NAV_PREFIX
        assert ADMIN_PREFIX != APP_NAV_PREFIX

    def test_admin_home_callback_uses_admin_prefix(self):
        _purge()
        from core.telegram_admin_ui import CALLBACK_PREFIX
        home_cb = f"{CALLBACK_PREFIX}HOME"
        assert home_cb.startswith(CALLBACK_PREFIX)
        assert home_cb == "ADMIN_NAV:HOME"

    def test_app_home_callback_uses_app_prefix(self):
        _purge()
        from core.telegram_app_nav import make_callback, ACT_HOME
        home_cb = make_callback(ACT_HOME)
        assert home_cb == "APP:HOME"

    def test_panel_pages_back_to_admin_home(self):
        """Direct children of Admin Home have Back → ADMIN_NAV:HOME."""
        _purge()
        from core.telegram_admin_ui import (
            operations_markup, decision_visibility_markup, distribution_markup,
            CALLBACK_PREFIX,
        )
        for markup_fn in (operations_markup, decision_visibility_markup, distribution_markup):
            markup = markup_fn()
            cbs = _cbs(markup)
            assert f"{CALLBACK_PREFIX}HOME" in cbs, (
                f"{markup_fn.__name__} should have Admin Home Back button"
            )


class TestRolesReloadNavigation:
    def test_reload_confirm_cancel_returns_to_roles(self):
        _purge()
        from core.telegram_admin_ui import reload_confirm_markup, CALLBACK_PREFIX
        markup = reload_confirm_markup(cancel_action="ROLES")
        assert f"{CALLBACK_PREFIX}ROLES" in _cbs(markup)


class TestProcessUpdateNavigationIntegration:
    def _load_modules(self, tmp_path: Path, monkeypatch, *, owner_ids: Optional[list[int]] = None):
        roles_file = tmp_path / "roles.json"
        roles_file.write_text(json.dumps({
            "owner": list(owner_ids or []),
            "primary_admin": [],
            "strategy_admin": [],
            "research_admin": [],
            "analyst": [],
            "moderator": [],
            "affiliate_admin": {},
        }), encoding="utf-8")
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps({"phase": "running"}), encoding="utf-8")
        monkeypatch.setenv("ADMIN_ROLES_CONFIG", str(roles_file))
        monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
        monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-100555000")
        monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "77")
        monkeypatch.setenv("ENABLE_TELEGRAM", "false")
        monkeypatch.setenv("SHADOW_MODE", "false")
        _purge()
        bot = importlib.import_module("core.bot_service")
        nav = importlib.import_module("core.telegram_app_nav")
        pub = _FakePublisher()
        monkeypatch.setattr(bot, "telegram_publisher", pub)
        return bot, nav, pub

    def test_home_status_back_round_trip_uses_real_history(self, tmp_path, monkeypatch):
        bot, nav, pub = self._load_modules(tmp_path, monkeypatch)
        bot.process_update(_message_update(9001, 9001, "/start"))
        start_markup = pub.sends[-1]["reply_markup"]
        active_id = pub.sends[-1]["message_id"]
        status_cb = _find_callback(start_markup, "STATUS")
        assert status_cb and status_cb.startswith("APP:")

        bot.process_update(_callback_update(9001, 9001, status_cb, message_id=active_id))
        assert len(pub.sends) == 1
        assert len(pub.edits) == 1
        status_markup = pub.edits[-1]["reply_markup"]
        back_cb = _find_callback(status_markup, "BACK")
        home_cb = _find_callback(status_markup, "HOME")
        assert back_cb is not None
        assert home_cb is not None
        assert nav.get_current_nav_action(9001, 9001) == nav.ACT_STATUS
        assert nav.nav_can_go_back(9001, chat_id=9001) is True

        bot.process_update(_callback_update(9001, 9001, back_cb, message_id=active_id))
        assert "binarybot" in pub.edits[-1]["text"].lower()
        assert nav.get_current_nav_action(9001, 9001) == nav.ACT_HOME
        assert nav.nav_can_go_back(9001, chat_id=9001) is False

    def test_help_back_and_refresh_do_not_grow_history(self, tmp_path, monkeypatch):
        bot, nav, pub = self._load_modules(tmp_path, monkeypatch)
        bot.process_update(_message_update(9002, 9002, "/start"))
        active_id = pub.sends[-1]["message_id"]
        help_cb = _find_callback(pub.sends[-1]["reply_markup"], "HELP")
        assert help_cb is not None

        bot.process_update(_callback_update(9002, 9002, help_cb, message_id=active_id))
        help_markup = pub.edits[-1]["reply_markup"]
        back_cb = _find_callback(help_markup, "BACK")
        status_cb = _find_callback(help_markup, "STATUS")
        assert back_cb is not None
        assert status_cb is not None

        bot.process_update(_callback_update(9002, 9002, status_cb, message_id=active_id))
        status_markup = pub.edits[-1]["reply_markup"]
        back_from_status = _find_callback(status_markup, "BACK")
        assert back_from_status is not None

        bot.process_update(_callback_update(9002, 9002, back_from_status, message_id=active_id))
        assert "/start" in pub.edits[-1]["text"]
        bot.process_update(_callback_update(9002, 9002, back_cb, message_id=active_id))
        assert "binarybot" in pub.edits[-1]["text"].lower()
        assert nav.nav_can_go_back(9002, chat_id=9002) is False

    def test_start_resets_generation_and_invalidates_stale_callbacks(self, tmp_path, monkeypatch):
        bot, nav, pub = self._load_modules(tmp_path, monkeypatch)
        bot.process_update(_message_update(9003, 9003, "/start"))
        first_status_cb = _find_callback(pub.sends[-1]["reply_markup"], "STATUS")
        first_generation = nav.get_navigation_generation(9003, 9003)
        assert first_generation == 1

        bot.process_update(_message_update(9003, 9003, "/start", message_id=1002))
        second_generation = nav.get_navigation_generation(9003, 9003)
        assert second_generation == 2
        active_id = nav.get_active_message(9003, chat_id=9003)

        bot.process_update(_callback_update(9003, 9003, first_status_cb, message_id=active_id))
        latest_text = (pub.edits[-1]["text"] if pub.edits else pub.sends[-1]["text"]).lower()
        assert "binarybot" in latest_text
        assert nav.get_current_nav_action(9003, 9003) == nav.ACT_HOME

    def test_app_callbacks_use_real_chat_and_thread_session(self, tmp_path, monkeypatch):
        bot, nav, pub = self._load_modules(tmp_path, monkeypatch, owner_ids=[9100])
        chat_id = -100777000
        thread_a = 41
        thread_b = 42

        bot.process_update(_message_update(chat_id, 9100, "/start", chat_type="supergroup", thread_id=thread_a))
        status_cb_a = _find_callback(pub.sends[-1]["reply_markup"], "STATUS")
        active_a = pub.sends[-1]["message_id"]
        bot.process_update(_message_update(chat_id, 9100, "/start", chat_type="supergroup", message_id=1002, thread_id=thread_b))
        status_cb_b = _find_callback(pub.sends[-1]["reply_markup"], "STATUS")
        active_b = pub.sends[-1]["message_id"]

        bot.process_update(_callback_update(chat_id, 9100, status_cb_a, chat_type="supergroup", message_id=active_a, thread_id=thread_a))
        bot.process_update(_callback_update(chat_id, 9100, status_cb_b, chat_type="supergroup", message_id=active_b, thread_id=thread_b))

        assert nav.get_current_nav_action(chat_id, 9100, thread_a) == nav.ACT_STATUS
        assert nav.get_current_nav_action(chat_id, 9100, thread_b) == nav.ACT_STATUS
        assert nav.get_active_message(9100, chat_id=chat_id, thread_id=thread_a) == active_a
        assert nav.get_active_message(9100, chat_id=chat_id, thread_id=thread_b) == active_b
        assert all(edit["message_id"] in {active_a, active_b} for edit in pub.edits)

    def test_slash_and_callback_entries_produce_equivalent_state(self, tmp_path, monkeypatch):
        bot, nav, pub = self._load_modules(tmp_path, monkeypatch)
        bot.process_update(_message_update(9004, 9004, "/start"))
        active_id = pub.sends[-1]["message_id"]
        status_cb = _find_callback(pub.sends[-1]["reply_markup"], "STATUS")

        bot.process_update(_message_update(9004, 9004, "/status", message_id=1002))
        slash_back = _find_callback(pub.edits[-1]["reply_markup"], "BACK")
        slash_generation = nav.get_navigation_generation(9004, 9004)
        assert slash_back is not None
        assert nav.get_current_nav_action(9004, 9004) == nav.ACT_STATUS

        bot.process_update(_message_update(9004, 9004, "/start", message_id=1003))
        active_id = nav.get_active_message(9004, chat_id=9004)
        current_status_cb = _find_callback(pub.sends[-1]["reply_markup"], "STATUS")
        bot.process_update(_callback_update(9004, 9004, current_status_cb, message_id=active_id))
        callback_back = _find_callback(pub.edits[-1]["reply_markup"], "BACK")
        callback_generation = nav.get_navigation_generation(9004, 9004)
        assert callback_back is not None
        assert slash_generation != callback_generation
        assert nav.get_current_nav_action(9004, 9004) == nav.ACT_STATUS

    def test_owner_admin_entry_exposes_real_app_back_button(self, tmp_path, monkeypatch):
        bot, nav, pub = self._load_modules(tmp_path, monkeypatch, owner_ids=[9006])
        bot.process_update(_message_update(9006, 9006, "/start"))
        active_id = pub.sends[-1]["message_id"]
        admin_cb = _find_callback(pub.sends[-1]["reply_markup"], "ADMIN")
        assert admin_cb is not None

        bot.process_update(_callback_update(9006, 9006, admin_cb, message_id=active_id))
        admin_markup = pub.edits[-1]["reply_markup"]
        back_cb = _find_callback(admin_markup, "BACK")
        home_cb = _find_callback(admin_markup, "HOME")
        assert back_cb is not None
        assert home_cb is not None

        bot.process_update(_callback_update(9006, 9006, back_cb, message_id=active_id))
        assert "binarybot" in pub.edits[-1]["text"].lower()
        assert nav.get_current_nav_action(9006, 9006) == nav.ACT_HOME

    def test_back_without_history_falls_back_safely_via_dispatcher(self, tmp_path, monkeypatch):
        bot, nav, pub = self._load_modules(tmp_path, monkeypatch)
        generation = nav.begin_navigation_generation(9005, 9005)
        bot.process_update(_callback_update(9005, 9005, f"APP:{generation}:BACK", message_id=2222))
        assert "binarybot" in pub.edits[-1]["text"].lower()
        assert nav.get_current_nav_action(9005, 9005) == nav.ACT_HOME
