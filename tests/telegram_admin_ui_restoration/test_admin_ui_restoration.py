"""
Telegram Admin UI Restoration Tests
====================================

Covers the requirements from:
  audit/telegram-auth-and-ui-forensic-audit-01/CANONICAL_UI_RESTORATION_PLAN.md

Test categories:
  AUTH-*   Authorization — owner private DM, wrong user, admin topic, callbacks
  UI-*     Admin home layout, role visibility, navigation, confirmation flows
  SYM-*    Symbol management — toggle, ALL, NONE, permissions
  PROF-*   Strategy profile selector — mapping, confirmation, Admin Proof
  FILE-*   File security — allowed paths, traversal, extension, secret, size, symlink
  DIAG-*   Diagnostics — diagnose, audit_runtime, no secrets
  RATE-*   Rate limiting
  REG-*    Regression — existing commands, startup, distribution, outcome callbacks, polling
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _purge(*extra: str) -> None:
    to_purge = list(extra) + [
        "core.admin_permissions", "core.admin_commands", "core.admin_views",
        "core.bot_service", "core.telegram_admin_ui", "core.telegram_runtime",
        "core.telegram_targets", "core.params_loader", "core.storage",
    ]
    for name in to_purge:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _make_roles_config(owner_ids=None) -> Dict:
    return {
        "owner": list(owner_ids or []),
        "primary_admin": [],
        "strategy_admin": [],
        "research_admin": [],
        "analyst": [],
        "moderator": [],
        "affiliate_admin": {},
    }


def _make_algo_params() -> Dict:
    return {
        "algo_version": "2.0.0",
        "score_thresholds": {"PRE": 55, "CONFIRM": 65, "OPEN": 70},
        "expiry_limits_minutes": {"min": 1, "max": 15},
        "buffer_multipliers": {"SMALL": 0.8, "MEDIUM": 1.0, "LARGE": 1.2},
        "sr_required_multiplier": 1.5,
        "spike_filters": {
            "wick_body_ratio_max": 2.0,
            "range_z_max": 3.0,
            "jump_vs_atr_max": 1.5,
        },
    }


def _ensure_dirs(tmp_path: Path) -> None:
    """Create all required directories under tmp_path for tests."""
    for subdir in ["config", "observability", "outcomes", "analytics/reports", "docs", "audit", "snapshots", "state"]:
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)


def _make_private_message(chat_id: int, user_id: int) -> Dict:
    return {
        "chat": {"id": chat_id, "type": "private"},
        "from": {"id": user_id},
    }


def _make_group_message(chat_id: int, user_id: int, thread_id: Optional[int] = None) -> Dict:
    msg: Dict = {
        "chat": {"id": chat_id, "type": "supergroup"},
        "from": {"id": user_id},
    }
    if thread_id is not None:
        msg["message_thread_id"] = thread_id
    return msg


# ---------------------------------------------------------------------------
# AUTH-001: Owner private DM is allowed for all _OWNER_PRIVATE_COMMANDS
# ---------------------------------------------------------------------------

class TestOwnerPrivateDM:
    OWNER_ID = 111111
    OTHER_ID = 999999
    ADMIN_CHAT_ID = -100123456789

    def _make_env(self, tmp_path: Path) -> Dict[str, str]:
        _ensure_dirs(tmp_path)
        roles = _make_roles_config(owner_ids=[self.OWNER_ID])
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        return {
            "OWNER_TELEGRAM_ID": str(self.OWNER_ID),
            "ADMIN_ROLES_CONFIG": str(rc),
            "ADMIN_CONTROL_CHAT_ID": str(self.ADMIN_CHAT_ID),
            "BINARYBOT_BASE_DIR": str(tmp_path),
        }

    def test_owner_private_is_allowed_for_admin(self, tmp_path):
        env = self._make_env(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.bot_service import _is_owner_private_context, _OWNER_PRIVATE_COMMANDS
            msg = _make_private_message(self.OWNER_ID, self.OWNER_ID)
            assert _is_owner_private_context(msg, self.OWNER_ID) is True
            for cmd in _OWNER_PRIVATE_COMMANDS:
                from core.bot_service import _can_run_admin_command
                assert _can_run_admin_command(msg, self.OWNER_ID, cmd) is True, f"Expected {cmd} allowed"

    def test_owner_private_new_commands_in_allowlist(self, tmp_path):
        env = self._make_env(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            from core.bot_service import _OWNER_PRIVATE_COMMANDS
            for cmd in {"/files", "/docs", "/download", "/log", "/diagnose", "/audit_runtime"}:
                assert cmd in _OWNER_PRIVATE_COMMANDS, f"{cmd} missing from _OWNER_PRIVATE_COMMANDS"

    def test_wrong_user_denied_in_private_dm(self, tmp_path):
        env = self._make_env(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.bot_service import _is_owner_private_context
            msg = _make_private_message(self.OTHER_ID, self.OTHER_ID)
            assert _is_owner_private_context(msg, self.OTHER_ID) is False

    def test_missing_owner_id_fails_closed(self, tmp_path):
        roles = _make_roles_config(owner_ids=[])
        rc = tmp_path / "roles_empty.json"
        _write_json(rc, roles)
        env = {
            "OWNER_TELEGRAM_ID": "",
            "ADMIN_ROLES_CONFIG": str(rc),
            "ADMIN_CONTROL_CHAT_ID": str(self.ADMIN_CHAT_ID),
            "BINARYBOT_BASE_DIR": str(tmp_path),
        }
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.bot_service import _is_owner_private_context
            msg = _make_private_message(self.OWNER_ID, self.OWNER_ID)
            assert _is_owner_private_context(msg, self.OWNER_ID) is False

    def test_roles_reload_blocked_in_private_dm(self, tmp_path):
        env = self._make_env(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.bot_service import _can_run_admin_command, _OWNER_PRIVATE_COMMANDS
            msg = _make_private_message(self.OWNER_ID, self.OWNER_ID)
            assert "/roles_reload" not in _OWNER_PRIVATE_COMMANDS

    def test_admin_topic_context_allowed(self, tmp_path):
        env = self._make_env(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            from core.bot_service import in_admin_context
            assert in_admin_context(self.ADMIN_CHAT_ID) is True
            assert in_admin_context(self.OWNER_ID) is False

    def test_callback_owner_private_allowed(self, tmp_path):
        env = self._make_env(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.bot_service import _can_use_admin_callback
            msg = _make_private_message(self.OWNER_ID, self.OWNER_ID)
            assert _can_use_admin_callback(msg, self.OWNER_ID) is True

    def test_callback_wrong_user_denied(self, tmp_path):
        env = self._make_env(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.bot_service import _can_use_admin_callback
            msg = _make_private_message(self.OTHER_ID, self.OTHER_ID)
            assert _can_use_admin_callback(msg, self.OTHER_ID) is False

    def test_malformed_owner_id_fails_closed(self, tmp_path):
        roles = _make_roles_config()
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        for bad_val in ["not-a-number", "@username", "0x123"]:
            env = {
                "OWNER_TELEGRAM_ID": bad_val,
                "ADMIN_ROLES_CONFIG": str(rc),
                "ADMIN_CONTROL_CHAT_ID": str(self.ADMIN_CHAT_ID),
                "BINARYBOT_BASE_DIR": str(tmp_path),
            }
            _purge()
            with patch.dict(os.environ, env, clear=False):
                import core.admin_permissions as ap
                ap.load_roles_config.cache_clear()
                from core.bot_service import _is_owner_private_context
                msg = _make_private_message(12345, 12345)
                assert _is_owner_private_context(msg, 12345) is False


# ---------------------------------------------------------------------------
# UI-001: Admin home markup layout
# ---------------------------------------------------------------------------

class TestAdminHomeMarkup:
    def test_admin_home_has_canonical_tree_buttons(self):
        """Canonical admin home must render the canonical tree nodes."""
        _purge()
        from core.telegram_admin_ui import admin_home_markup, CALLBACK_PREFIX
        markup = admin_home_markup(include_roles_reload=True)
        flat_texts = [btn["text"] for row in markup["inline_keyboard"] for btn in row]
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]

        # Default (no role specified) shows all 11 canonical panels.
        canonical_labels = [
            "Operations", "Symbols & Coverage", "Decision Visibility",
            "Distribution", "Research & Analytics", "Intelligence",
            "Affiliate", "Roles & Identity", "System Health",
            "Governance & Docs", "Security & Audit",
        ]
        for label in canonical_labels:
            assert any(label in t for t in flat_texts), f"Canonical panel '{label}' missing from admin home"

        # Canonical callback actions must be present.
        canonical_actions = [
            "OPERATIONS", "SYMBOLS_COV", "DECISION_VIS", "DISTRIBUTION",
            "RESEARCH", "INTELLIGENCE", "AFFILIATE", "ROLES",
            "SYSHEALTH", "GOVDOCS", "SECAUDIT",
        ]
        for action in canonical_actions:
            assert any(f"{CALLBACK_PREFIX}{action}" in d for d in flat_data), \
                f"Canonical action '{action}' missing from admin home"

        # Reload Roles button present when include_roles_reload=True.
        assert any("RELOAD_ROLES_CONFIRM" in d for d in flat_data)

    def test_admin_home_without_reload(self):
        _purge()
        from core.telegram_admin_ui import admin_home_markup
        markup = admin_home_markup(include_roles_reload=False)
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert not any("RELOAD_ROLES_CONFIRM" in d for d in flat_data)

    def test_admin_home_role_scoped_owner_sees_all(self):
        """Owner role must see all 11 canonical panels."""
        _purge()
        from core.telegram_admin_ui import admin_home_markup, CALLBACK_PREFIX
        markup = admin_home_markup(role="OWNER", include_roles_reload=False)
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        for action in ["OPERATIONS", "SYMBOLS_COV", "DECISION_VIS", "DISTRIBUTION",
                       "RESEARCH", "INTELLIGENCE", "AFFILIATE", "ROLES",
                       "SYSHEALTH", "GOVDOCS", "SECAUDIT"]:
            assert any(action in d for d in flat_data), f"Owner missing panel '{action}'"

    def test_admin_home_role_scoped_strategy_admin(self):
        """Strategy Admin (Functional Admin / Operations) sees only Operations, Symbols & Coverage, Decision Visibility."""
        _purge()
        from core.telegram_admin_ui import admin_home_markup, CALLBACK_PREFIX
        markup = admin_home_markup(role="STRATEGY_ADMIN", include_roles_reload=False)
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        allowed = {"OPERATIONS", "SYMBOLS_COV", "DECISION_VIS"}
        not_allowed = {"DISTRIBUTION", "RESEARCH", "INTELLIGENCE", "AFFILIATE",
                       "ROLES", "SYSHEALTH", "GOVDOCS", "SECAUDIT"}
        for a in allowed:
            assert any(a in d for d in flat_data), f"STRATEGY_ADMIN missing allowed panel '{a}'"
        for a in not_allowed:
            assert not any(a in d for d in flat_data), f"STRATEGY_ADMIN should not see panel '{a}'"

    def test_admin_home_role_scoped_affiliate_admin(self):
        """Affiliate Admin sees only the Affiliate / Partner panel."""
        _purge()
        from core.telegram_admin_ui import admin_home_markup
        markup = admin_home_markup(role="AFFILIATE_ADMIN", include_roles_reload=False)
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert any("AFFILIATE" in d for d in flat_data), "AFFILIATE_ADMIN missing Affiliate panel"
        not_allowed = ["OPERATIONS", "SYMBOLS_COV", "DECISION_VIS", "DISTRIBUTION",
                       "RESEARCH", "INTELLIGENCE", "ROLES", "SYSHEALTH", "GOVDOCS", "SECAUDIT"]
        for a in not_allowed:
            assert not any(a in d for d in flat_data), f"AFFILIATE_ADMIN should not see panel '{a}'"

    def test_callback_prefix_all_admin_nav(self):
        _purge()
        from core.telegram_admin_ui import admin_home_markup, CALLBACK_PREFIX
        markup = admin_home_markup(include_roles_reload=True)
        for row in markup["inline_keyboard"]:
            for btn in row:
                assert btn["callback_data"].startswith(CALLBACK_PREFIX)

    def test_parse_action_strips_prefix(self):
        _purge()
        from core.telegram_admin_ui import parse_action, CALLBACK_PREFIX
        assert parse_action(f"{CALLBACK_PREFIX}STATUS") == "STATUS"
        assert parse_action(f"{CALLBACK_PREFIX}SYM_TOGGLE:EURUSD") == "SYM_TOGGLE:EURUSD"
        assert parse_action("VOTE_|abc|OK") is None
        assert parse_action("") is None

    def test_back_navigation_buttons_present(self):
        _purge()
        from core.telegram_admin_ui import strategy_markup, standard_back_markup, CALLBACK_PREFIX
        # strategy_markup Back navigates to Operations (immediate parent, canonical §6.2)
        markup = strategy_markup()
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert f"{CALLBACK_PREFIX}OPERATIONS" in flat_data, (
            "strategy_markup Back should return to Operations (immediate parent), not Admin Home"
        )

        # standard_back_markup retains the ADMIN_NAV:HOME shortcut for generic use
        markup2 = standard_back_markup()
        flat_data2 = [btn["callback_data"] for row in markup2["inline_keyboard"] for btn in row]
        assert f"{CALLBACK_PREFIX}HOME" in flat_data2


# ---------------------------------------------------------------------------
# UI-002: Symbol toggle markup
# ---------------------------------------------------------------------------

class TestSymbolToggleMarkup:
    def test_symbols_toggle_shows_checkboxes(self):
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup
        all_syms = ["EURUSD", "GBPUSD", "BTCUSD"]
        active = ["EURUSD"]
        markup = symbols_toggle_markup(all_syms, active)
        flat = [btn["text"] for row in markup["inline_keyboard"] for btn in row]
        assert any("✅" in t and "EURUSD" in t for t in flat)
        assert any("⬜" in t and "GBPUSD" in t for t in flat)

    def test_symbols_toggle_has_all_none_refresh(self):
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup, CALLBACK_PREFIX
        # Default parent_action="HOME" → refresh targets SYMBOLS_COV (admin-home panel entry)
        markup = symbols_toggle_markup(["EURUSD"], [])
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert f"{CALLBACK_PREFIX}SYMBOLS_ALL" in flat_data
        assert f"{CALLBACK_PREFIX}SYMBOLS_NONE" in flat_data
        # Refresh action present (SYMBOLS_COV for admin-home context)
        assert f"{CALLBACK_PREFIX}SYMBOLS_COV" in flat_data

        # When parent_action="STRATEGY" → refresh targets SYMBOLS (strategy sub-page)
        markup2 = symbols_toggle_markup(["EURUSD"], [], parent_action="STRATEGY")
        flat_data2 = [btn["callback_data"] for row in markup2["inline_keyboard"] for btn in row]
        assert f"{CALLBACK_PREFIX}SYMBOLS" in flat_data2

    def test_symbols_toggle_3_per_row_max(self):
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup
        all_syms = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
        markup = symbols_toggle_markup(all_syms, [])
        for i, row in enumerate(markup["inline_keyboard"]):
            # Control rows (ALL/NONE/Refresh and Back) may have 3 or 1
            sym_btns = [b for b in row if "SYM_TOGGLE" in b["callback_data"]]
            if sym_btns:
                assert len(sym_btns) <= 3

    def test_sym_toggle_callback_format(self):
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup, CALLBACK_PREFIX
        markup = symbols_toggle_markup(["EURUSD"], [])
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert f"{CALLBACK_PREFIX}SYM_TOGGLE:EURUSD" in flat_data

    def test_callback_data_within_64_chars(self):
        _purge()
        from core.telegram_admin_ui import symbols_toggle_markup
        all_syms = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "ETHUSD"]
        markup = symbols_toggle_markup(all_syms, ["EURUSD"])
        for row in markup["inline_keyboard"]:
            for btn in row:
                assert len(btn["callback_data"].encode()) <= 64, f"Callback too long: {btn['callback_data']!r}"


# ---------------------------------------------------------------------------
# UI-003: Strategy profile markup
# ---------------------------------------------------------------------------

class TestStrategyQuickMarkup:
    def test_profile_surface_has_no_legacy_mutation_buttons(self):
        _purge()
        from core.telegram_admin_ui import strategy_quick_markup
        markup = strategy_quick_markup(None)
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert not any("PROFILE_CONFIRM:" in data for data in flat_data)
        assert not any("PROFILE_EXEC:" in data for data in flat_data)
        assert any("PROFILE_HOME" in data for data in flat_data)

    def test_profile_surface_is_read_only_navigation(self):
        _purge()
        from core.telegram_admin_ui import strategy_quick_markup
        markup = strategy_quick_markup("BALANCED")
        flat = [btn["text"] for row in markup["inline_keyboard"] for btn in row]
        assert any("Refresh" in text for text in flat)
        assert not any("MIC / SMALL" in text for text in flat)
        assert not any("MEDIU / MEDIUM" in text for text in flat)
        assert not any("MARE / LARGE" in text for text in flat)

    def test_stale_confirmation_markup_has_no_execute_action(self):
        _purge()
        from core.telegram_admin_ui import strategy_profile_confirm_markup
        markup = strategy_profile_confirm_markup("CONSERVATIVE")
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert not any("PROFILE_EXEC:" in data for data in flat_data)
        assert any("PROFILE_HOME" in data for data in flat_data)


# ---------------------------------------------------------------------------
# SYM-001: Symbol mutation handlers
# ---------------------------------------------------------------------------

class TestSymbolMutationHandlers:
    OWNER_ID = 222222

    def _setup(self, tmp_path: Path) -> Dict[str, str]:
        _ensure_dirs(tmp_path)
        roles = _make_roles_config(owner_ids=[self.OWNER_ID])
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        syms_file = tmp_path / "config" / "active_symbols.json"
        _write_json(syms_file, ["EURUSD", "GBPUSD"])
        return {
            "OWNER_TELEGRAM_ID": str(self.OWNER_ID),
            "ADMIN_ROLES_CONFIG": str(rc),
            "BINARYBOT_BASE_DIR": str(tmp_path),
        }

    def test_toggle_add(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_symbols_toggle, _load_active_symbols
                result = handle_symbols_toggle("USDJPY", self.OWNER_ID)
                assert "OK" in result or "Added" in result
                assert "USDJPY" in _load_active_symbols()

    def test_toggle_remove(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_symbols_toggle, _load_active_symbols
                result = handle_symbols_toggle("EURUSD", self.OWNER_ID)
                assert "OK" in result or "Removed" in result
                assert "EURUSD" not in _load_active_symbols()

    def test_symbols_all(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_symbols_all, _load_active_symbols, get_all_known_symbols
                result = handle_symbols_all(self.OWNER_ID)
                assert "OK" in result
                active = set(_load_active_symbols())
                assert active == set(get_all_known_symbols())

    def test_symbols_none(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_symbols_none, _load_active_symbols
                result = handle_symbols_none(self.OWNER_ID)
                assert "OK" in result
                assert _load_active_symbols() == []

    def test_toggle_invalid_symbol_rejected(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import handle_symbols_toggle
            result = handle_symbols_toggle("../../etc/passwd", self.OWNER_ID)
            assert "Error" in result or "Invalid" in result

    def test_toggle_unauthorized(self, tmp_path):
        env = self._setup(tmp_path)
        NON_OWNER = 555555
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import handle_symbols_toggle
            result = handle_symbols_toggle("EURUSD", NON_OWNER)
            assert "unauthorized" in result.lower() or "Error" in result

    def test_admin_proof_emitted_on_toggle(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger") as mock_obs:
                from core.admin_commands import handle_symbols_toggle
                handle_symbols_toggle("USDJPY", self.OWNER_ID)
                mock_obs.send_admin_proof_telegram.assert_called()


# ---------------------------------------------------------------------------
# PROF-001: Strategy profile fail-closed reconciliation
# ---------------------------------------------------------------------------

class TestStrategyProfileHandlers:
    OWNER_ID = 333333

    def _setup(self, tmp_path: Path) -> Dict[str, str]:
        _ensure_dirs(tmp_path)
        roles = _make_roles_config(owner_ids=[self.OWNER_ID])
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        params = _make_algo_params()
        params_file = tmp_path / "config" / "algo_params.json"
        _write_json(params_file, params)
        return {
            "OWNER_TELEGRAM_ID": str(self.OWNER_ID),
            "ADMIN_ROLES_CONFIG": str(rc),
            "BINARYBOT_BASE_DIR": str(tmp_path),
        }

    def test_legacy_named_profiles_are_not_live_bundles(self):
        _purge()
        from core.admin_commands import STRATEGY_PROFILES
        assert STRATEGY_PROFILES == {}

    def test_authorized_legacy_profile_request_does_not_mutate_params(self, tmp_path):
        env = self._setup(tmp_path)
        params_path = tmp_path / "config" / "algo_params.json"
        before = json.loads(params_path.read_text(encoding="utf-8"))
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_strategy_profile
                for profile in ("CONSERVATIVE", "BALANCED", "AGGRESSIVE"):
                    result = handle_strategy_profile(profile, self.OWNER_ID)
                    assert "NOT AVAILABLE" in result
                    after = json.loads(params_path.read_text(encoding="utf-8"))
                    assert after == before

    def test_profile_request_preserves_thresholds_and_legacy_sr_value(self, tmp_path):
        env = self._setup(tmp_path)
        params_path = tmp_path / "config" / "algo_params.json"
        before = json.loads(params_path.read_text(encoding="utf-8"))
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_strategy_profile
                handle_strategy_profile("AGGRESSIVE", self.OWNER_ID)
        after = json.loads(params_path.read_text(encoding="utf-8"))
        assert after["score_thresholds"] == before["score_thresholds"]
        assert after.get("sr_required_multiplier") == before.get("sr_required_multiplier")

    def test_unknown_profile_is_also_non_mutating(self, tmp_path):
        env = self._setup(tmp_path)
        params_path = tmp_path / "config" / "algo_params.json"
        before = params_path.read_text(encoding="utf-8")
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_strategy_profile
                result = handle_strategy_profile("UNKNOWN_PROFILE", self.OWNER_ID)
                assert "NOT AVAILABLE" in result
        assert params_path.read_text(encoding="utf-8") == before

    def test_profile_unauthorized(self, tmp_path):
        env = self._setup(tmp_path)
        NON_OWNER = 777777
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import handle_strategy_profile
            result = handle_strategy_profile("BALANCED", NON_OWNER)
            assert "unauthorized" in result.lower() or "Error" in result

    def test_authorized_rejected_profile_emits_admin_proof(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger") as mock_obs:
                from core.admin_commands import handle_strategy_profile
                handle_strategy_profile("BALANCED", self.OWNER_ID)
                mock_obs.send_admin_proof_telegram.assert_called()

    def test_current_profile_is_explicitly_not_available(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import (
                get_current_strategy_profile,
                get_current_strategy_profile_observation,
            )
            assert get_current_strategy_profile() is None
            assert "NOT AVAILABLE" in get_current_strategy_profile_observation()


# ---------------------------------------------------------------------------
# FILE-001: File security
# ---------------------------------------------------------------------------

class TestFileSecurity:
    OWNER_ID = 444444

    def _setup(self, tmp_path: Path) -> Dict[str, str]:
        _ensure_dirs(tmp_path)
        roles = _make_roles_config(owner_ids=[self.OWNER_ID])
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        # Create an obs directory with a test file
        obs_dir = tmp_path / "observability"
        obs_dir.mkdir(parents=True, exist_ok=True)
        test_file = obs_dir / "test_log.log"
        test_file.write_text("test log content", encoding="utf-8")
        return {
            "OWNER_TELEGRAM_ID": str(self.OWNER_ID),
            "ADMIN_ROLES_CONFIG": str(rc),
            "BINARYBOT_BASE_DIR": str(tmp_path),
        }

    def test_allowed_file_returns_path(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", "test_log.log", self.OWNER_ID)
                assert err == "", f"Unexpected error: {err}"
                assert path is not None
                assert path.endswith("test_log.log")

    def test_traversal_rejected(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", "../../../etc/passwd", self.OWNER_ID)
                assert path is None
                assert err

    def test_unsupported_extension_rejected(self, tmp_path):
        env = self._setup(tmp_path)
        obs_dir = tmp_path / "observability"
        (obs_dir / "secret.py").write_text("code", encoding="utf-8")
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", "secret.py", self.OWNER_ID)
                assert path is None

    def test_env_file_rejected(self, tmp_path):
        env = self._setup(tmp_path)
        obs_dir = tmp_path / "observability"
        (obs_dir / ".env").write_text("SECRET=abc", encoding="utf-8")
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", ".env", self.OWNER_ID)
                assert path is None

    def test_token_filename_rejected(self, tmp_path):
        env = self._setup(tmp_path)
        obs_dir = tmp_path / "observability"
        (obs_dir / "token.txt").write_text("mytoken", encoding="utf-8")
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", "token.txt", self.OWNER_ID)
                assert path is None

    def test_file_too_large_rejected(self, tmp_path):
        env = {**self._setup(tmp_path), "MAX_DELIVERY_FILE_SIZE": "10"}
        obs_dir = tmp_path / "observability"
        big_file = obs_dir / "big.log"
        big_file.write_bytes(b"x" * 100)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", "big.log", self.OWNER_ID)
                assert path is None
                assert "large" in err.lower() or "size" in err.lower()

    def test_unauthorized_access_denied(self, tmp_path):
        env = self._setup(tmp_path)
        NON_OWNER = 888888
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", "test_log.log", NON_OWNER)
                assert path is None

    def test_symlink_escape_rejected(self, tmp_path):
        env = self._setup(tmp_path)
        obs_dir = tmp_path / "observability"
        # Create a file outside allowed root
        outside = tmp_path / "outside" / "secret.txt"
        outside.parent.mkdir(parents=True)
        outside.write_text("secrets", encoding="utf-8")
        # Create a symlink inside obs pointing to outside
        link = obs_dir / "link.txt"
        link.symlink_to(str(outside))
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_file_download_path
                path, err = handle_file_download_path("obs", "link.txt", self.OWNER_ID)
                assert path is None

    def test_download_audit_every_request(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger") as mock_obs, \
                 patch("core.admin_commands._append_jsonl") as mock_append:
                from core.admin_commands import handle_file_download_path
                handle_file_download_path("obs", "test_log.log", self.OWNER_ID)
                # _append_jsonl called for audit events
                assert mock_append.call_count >= 1

    def test_files_list_pagination(self, tmp_path):
        env = self._setup(tmp_path)
        obs_dir = tmp_path / "observability"
        # Create 15 files
        for i in range(15):
            (obs_dir / f"log_{i:02d}.log").write_text(f"log {i}", encoding="utf-8")
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_files_list
                info_p0 = handle_files_list(self.OWNER_ID, "obs", page=0)
                assert info_p0["error"] is None
                assert info_p0["total_pages"] > 1
                info_p1 = handle_files_list(self.OWNER_ID, "obs", page=1)
                assert info_p1["page"] == 1
                # Pages should be different
                assert info_p0["filenames"] != info_p1["filenames"]


# ---------------------------------------------------------------------------
# DIAG-001: Diagnostics
# ---------------------------------------------------------------------------

class TestDiagnostics:
    OWNER_ID = 555555

    def _setup(self, tmp_path: Path) -> Dict[str, str]:
        _ensure_dirs(tmp_path)
        roles = _make_roles_config(owner_ids=[self.OWNER_ID])
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        return {
            "OWNER_TELEGRAM_ID": str(self.OWNER_ID),
            "ADMIN_ROLES_CONFIG": str(rc),
            "BINARYBOT_BASE_DIR": str(tmp_path),
            "OBS_DIR": str(tmp_path / "observability"),
        }

    def test_diagnose_returns_text(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import handle_diagnose
            result = handle_diagnose(self.OWNER_ID)
            assert "Diagnosis" in result or "Runtime" in result.lower() or "phase" in result.lower()

    def test_diagnose_no_secret_values(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "my_secret_token_abc"}):
                from core.admin_commands import handle_diagnose
                result = handle_diagnose(self.OWNER_ID)
                assert "my_secret_token_abc" not in result

    def test_diagnose_unauthorized(self, tmp_path):
        env = self._setup(tmp_path)
        NON_OWNER = 999998
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import handle_diagnose
            result = handle_diagnose(NON_OWNER)
            assert "unauthorized" in result.lower() or "Error" in result

    def test_audit_runtime_produces_file(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_audit_runtime
                path, err = handle_audit_runtime(self.OWNER_ID)
                assert err == ""
                assert path is not None
                assert os.path.exists(path)
                # Clean up
                os.unlink(path)

    def test_audit_runtime_no_secret_values(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch.dict(os.environ, {
                "TELEGRAM_BOT_TOKEN": "SECRET_TOKEN_12345",
                "TWELVE_DATA_API_KEY": "SECRET_API_KEY_ABCDE",
            }):
                with patch("core.admin_commands.observability_logger"):
                    from core.admin_commands import handle_audit_runtime
                    path, err = handle_audit_runtime(self.OWNER_ID)
                    assert path is not None
                    content = open(path, encoding="utf-8").read()
                    assert "SECRET_TOKEN_12345" not in content
                    assert "SECRET_API_KEY_ABCDE" not in content
                    os.unlink(path)

    def test_audit_runtime_env_matrix_presence_only(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_audit_runtime
                path, _ = handle_audit_runtime(self.OWNER_ID)
                artifact = json.loads(open(path, encoding="utf-8").read())
                matrix = artifact.get("env_presence_matrix", {})
                # All values must be booleans (presence only)
                for k, v in matrix.items():
                    assert isinstance(v, bool), f"Key {k} has non-boolean value: {v!r}"
                os.unlink(path)

    def test_audit_runtime_bounded_size(self, tmp_path):
        env = self._setup(tmp_path)
        # Create many log lines to ensure bounding works
        obs_dir = tmp_path / "observability"
        obs_dir.mkdir(parents=True, exist_ok=True)
        engine_log = obs_dir / "engine_events.jsonl"
        with engine_log.open("w", encoding="utf-8") as f:
            for i in range(1000):
                f.write(json.dumps({"event_type": "decision", "i": i}) + "\n")
        _purge()
        with patch.dict(os.environ, {**env, "OBS_DIR": str(obs_dir)}, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_audit_runtime, AUDIT_MAX_LINES_PER_FILE
                path, _ = handle_audit_runtime(self.OWNER_ID)
                artifact = json.loads(open(path, encoding="utf-8").read())
                assert len(artifact.get("recent_engine_events", [])) <= AUDIT_MAX_LINES_PER_FILE
                os.unlink(path)

    def test_log_export_produces_file(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_log_export
                path, err = handle_log_export(self.OWNER_ID)
                assert err == ""
                assert path is not None
                assert os.path.exists(path)
                os.unlink(path)

    def test_log_export_no_secrets(self, tmp_path):
        env = self._setup(tmp_path)
        obs_dir = tmp_path / "observability"
        obs_dir.mkdir(parents=True, exist_ok=True)
        eng_log = obs_dir / "engine_events.jsonl"
        eng_log.write_text(
            json.dumps({"event_type": "decision", "token": "REAL_SECRET_TOKEN"}) + "\n",
            encoding="utf-8",
        )
        _purge()
        with patch.dict(os.environ, {**env, "OBS_DIR": str(obs_dir)}, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_log_export
                path, _ = handle_log_export(self.OWNER_ID)
                content = open(path, encoding="utf-8").read()
                assert "REAL_SECRET_TOKEN" not in content
                os.unlink(path)


# ---------------------------------------------------------------------------
# RATE-001: Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_rate_limit_allows_within_window(self):
        _purge()
        from core.bot_service import _check_rate_limit, _RATE_STORE
        _RATE_STORE.clear()
        for _ in range(5):
            assert _check_rate_limit(12345, "diagnose") is True

    def test_rate_limit_blocks_over_limit(self):
        _purge()
        from core.bot_service import _check_rate_limit, _RATE_STORE, _RATE_LIMITS_CONFIG
        _RATE_STORE.clear()
        max_calls, _ = _RATE_LIMITS_CONFIG["audit_runtime"]
        for _ in range(max_calls):
            _check_rate_limit(99999, "audit_runtime")
        # One more should be blocked
        assert _check_rate_limit(99999, "audit_runtime") is False

    def test_rate_limit_resets_after_window(self):
        _purge()
        from core.bot_service import _check_rate_limit, _RATE_STORE
        _RATE_STORE.clear()
        uid = 11111
        # Exhaust the audit_runtime limit
        from core.bot_service import _RATE_LIMITS_CONFIG
        max_calls, window = _RATE_LIMITS_CONFIG["audit_runtime"]
        for _ in range(max_calls):
            _check_rate_limit(uid, "audit_runtime")
        # Simulate window expiry by backdating the entry
        key = f"{uid}:audit_runtime"
        _RATE_STORE[key]["window_start"] -= window + 1
        assert _check_rate_limit(uid, "audit_runtime") is True


# ---------------------------------------------------------------------------
# REG-001: Regression — existing commands and flows
# ---------------------------------------------------------------------------

class TestRegression:
    OWNER_ID = 666666
    ADMIN_CHAT_ID = -100987654321

    def _setup(self, tmp_path: Path) -> Dict[str, str]:
        _ensure_dirs(tmp_path)
        roles = _make_roles_config(owner_ids=[self.OWNER_ID])
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        params = _make_algo_params()
        params_file = tmp_path / "config" / "algo_params.json"
        _write_json(params_file, params)
        syms_file = tmp_path / "config" / "active_symbols.json"
        _write_json(syms_file, ["EURUSD"])
        return {
            "OWNER_TELEGRAM_ID": str(self.OWNER_ID),
            "ADMIN_ROLES_CONFIG": str(rc),
            "ADMIN_CONTROL_CHAT_ID": str(self.ADMIN_CHAT_ID),
            "BINARYBOT_BASE_DIR": str(tmp_path),
        }

    def test_existing_admin_commands_still_work(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_admin_command
                for cmd in ["/admin", "/strategy", "/engine", "/symbols", "/debug", "/report"]:
                    result = handle_admin_command(cmd, self.OWNER_ID)
                    assert result, f"Empty result for {cmd}"
                    assert "error" not in result.lower() or "Error\n\nunauthorized" in result

    def test_thresholds_mutation_still_works(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_admin_command
                result = handle_admin_command("/thresholds PRE 58", self.OWNER_ID)
                assert "OK" in result

    def test_roles_command_works(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import handle_admin_command
            result = handle_admin_command("/roles", self.OWNER_ID)
            assert "Role" in result

    def test_callback_vote_still_works(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.outcome_service.handle_vote_callback") as mock_vote:
                mock_vote.return_value = {"accepted": True, "reason": "ok"}
                from core.bot_service import handle_callback
                res = handle_callback(123, 456, "VOTE_|sig1|WIN", message_id=1)
                mock_vote.assert_called_once()

    def test_parse_action_unknown_returns_none(self):
        _purge()
        from core.telegram_admin_ui import parse_action
        assert parse_action("RANDOM_DATA") is None
        assert parse_action("") is None
        assert parse_action(None) is None

    def test_in_admin_context_fail_closed_when_unconfigured(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, {**env, "ADMIN_CONTROL_CHAT_ID": "0"}, clear=False):
            from core.bot_service import in_admin_context
            # When ADMIN_CONTROL_CHAT_ID == 0, any chat is denied
            assert in_admin_context(-100123456789) is False
            assert in_admin_context(0) is False

    def test_admin_command_names_includes_new_commands(self):
        _purge()
        from core.telegram_runtime import admin_command_names
        names = admin_command_names()
        for cmd in {"/files", "/docs", "/download", "/log", "/diagnose", "/audit_runtime"}:
            assert cmd in names, f"{cmd} missing from admin_command_names"

    def test_help_text_includes_new_commands(self):
        _purge()
        from core.telegram_runtime import render_help_text
        help_text = render_help_text()
        for cmd in ["/files", "/docs", "/log", "/diagnose", "/audit_runtime"]:
            assert cmd in help_text, f"{cmd} missing from help text"

    def test_strategy_markup_has_profile_button(self):
        _purge()
        from core.telegram_admin_ui import strategy_markup, CALLBACK_PREFIX
        markup = strategy_markup()
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert f"{CALLBACK_PREFIX}PROFILE_HOME" in flat_data

    def test_topic_routing_functions_available(self):
        _purge()
        from core.telegram_targets import alerts_target, errors_target, reports_target
        with patch.dict(os.environ, {
            "ADMIN_CONTROL_CHAT_ID": "",
            "ADMIN_PROOF_CHAT_ID": "",
        }, clear=False):
            # Without a valid chat_id configured, all targets should return None
            # (env_chat_id returns None for empty string)
            assert alerts_target() is None
            assert errors_target() is None
            assert reports_target() is None

    def test_topic_routing_uses_thread_id_when_set(self):
        _purge()
        with patch.dict(os.environ, {
            "ADMIN_CONTROL_CHAT_ID": "-100100200300",
            "ADMIN_ALERTS_THREAD_ID": "42",
        }, clear=False):
            from core.telegram_targets import alerts_target
            target = alerts_target()
            assert target is not None
            assert target.thread_id == 42
