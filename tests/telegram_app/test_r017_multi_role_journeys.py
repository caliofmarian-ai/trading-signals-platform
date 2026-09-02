from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

ADMIN_CHAT_ID = -100700017
ADMIN_THREAD_ID = 77

ROLE_USERS = {
    "PRIMARY_ADMIN": 2000,
    "STRATEGY_ADMIN": 3000,
    "RESEARCH_ADMIN": 4000,
    "ANALYST": 5000,
    "MODERATOR": 6000,
    "AFFILIATE_ADMIN": 7000,
    "USER": 9000,
}

EXPECTED_PANELS = {
    "PRIMARY_ADMIN": {
        "OPERATIONS", "SYMBOLS_COV", "DECISION_VIS", "DISTRIBUTION", "RESEARCH",
        "INTELLIGENCE", "AFFILIATE", "ROLES", "SYSHEALTH", "GOVDOCS", "SECAUDIT",
    },
    "STRATEGY_ADMIN": {"OPERATIONS", "SYMBOLS_COV", "DECISION_VIS"},
    "RESEARCH_ADMIN": {"DECISION_VIS", "RESEARCH", "INTELLIGENCE"},
    "ANALYST": {"DECISION_VIS", "RESEARCH", "INTELLIGENCE"},
    "MODERATOR": {"SYSHEALTH"},
    "AFFILIATE_ADMIN": {"AFFILIATE"},
}

ALLOWED_PANEL_SAMPLE = {
    "PRIMARY_ADMIN": "ROLES",
    "STRATEGY_ADMIN": "OPERATIONS",
    "RESEARCH_ADMIN": "RESEARCH",
    "ANALYST": "DECISION_VIS",
    "MODERATOR": "SYSHEALTH",
    "AFFILIATE_ADMIN": "AFFILIATE",
}


def _roles_payload() -> dict:
    return {
        "owner": [1000],
        "primary_admin": [ROLE_USERS["PRIMARY_ADMIN"]],
        "strategy_admin": [ROLE_USERS["STRATEGY_ADMIN"]],
        "research_admin": [ROLE_USERS["RESEARCH_ADMIN"]],
        "analyst": [ROLE_USERS["ANALYST"]],
        "moderator": [ROLE_USERS["MODERATOR"]],
        "affiliate_admin": {
            "partner1": {
                "telegram_id": ROLE_USERS["AFFILIATE_ADMIN"],
                "referral_code": "PARTNER1",
            }
        },
    }


def _purge_runtime_modules() -> None:
    exact = {
        "core.admin_permissions",
        "core.bot_service",
        "core.telegram_admin_ui",
        "core.telegram_app_nav",
        "core.telegram_runtime",
        "core.telegram_targets",
    }
    for name in list(sys.modules):
        if name in exact:
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


@pytest.fixture
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    roles_path = tmp_path / "admin_roles.json"
    permissions_path = tmp_path / "admin_permissions.json"
    roles_path.write_text(json.dumps(_roles_payload(), indent=2), encoding="utf-8")
    permissions_path.write_text(
        (SEND_ROOT / "config" / "admin_permissions.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    monkeypatch.setenv("ADMIN_ROLES_CONFIG", str(roles_path))
    monkeypatch.setenv("ADMIN_PERMISSIONS_CONFIG", str(permissions_path))
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", str(ADMIN_CHAT_ID))
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", str(ADMIN_THREAD_ID))
    monkeypatch.setenv("ENABLE_TELEGRAM", "false")
    monkeypatch.setenv("SHADOW_MODE", "false")
    monkeypatch.delenv("OWNER_TELEGRAM_ID", raising=False)

    _purge_runtime_modules()
    permissions = importlib.import_module("core.admin_permissions")
    bot = importlib.import_module("core.bot_service")
    admin_ui = importlib.import_module("core.telegram_admin_ui")
    yield permissions, bot, admin_ui
    _purge_runtime_modules()


def _message(chat_id: int, user_id: int, *, chat_type: str, thread_id: int | None = None) -> dict:
    message = {
        "chat": {"id": chat_id, "type": chat_type},
        "from": {"id": user_id},
        "text": "/admin",
        "message_id": 500,
    }
    if thread_id is not None:
        message["message_thread_id"] = thread_id
    return message


def _panel_callbacks(markup: dict | None) -> set[str]:
    if not isinstance(markup, dict):
        return set()
    callbacks: set[str] = set()
    for row in markup.get("inline_keyboard", []):
        for button in row:
            value = str(button.get("callback_data") or "")
            if value.startswith("ADMIN_NAV:"):
                action = value.split(":", 1)[1]
                if not action.startswith("INFO:"):
                    callbacks.add(action)
    return callbacks


@pytest.mark.parametrize("role", [
    "PRIMARY_ADMIN", "STRATEGY_ADMIN", "RESEARCH_ADMIN", "ANALYST", "MODERATOR", "AFFILIATE_ADMIN"
])
def test_non_owner_private_dm_admin_command_is_context_denied(runtime, role: str) -> None:
    _permissions, bot, _admin_ui = runtime
    user_id = ROLE_USERS[role]
    message = _message(user_id, user_id, chat_type="private")
    assert bot._can_run_admin_command(message, user_id, "/admin") is False


@pytest.mark.parametrize("role", [
    "PRIMARY_ADMIN", "STRATEGY_ADMIN", "RESEARCH_ADMIN", "ANALYST", "MODERATOR", "AFFILIATE_ADMIN"
])
def test_non_owner_admin_topic_context_is_accepted(runtime, role: str) -> None:
    permissions, bot, _admin_ui = runtime
    user_id = ROLE_USERS[role]
    message = _message(
        ADMIN_CHAT_ID,
        user_id,
        chat_type="supergroup",
        thread_id=ADMIN_THREAD_ID,
    )
    assert bot._can_run_admin_command(message, user_id, "/admin") is True
    assert permissions.has_permission(user_id, "admin.view") is True


def test_wrong_admin_thread_fails_closed(runtime) -> None:
    _permissions, bot, _admin_ui = runtime
    user_id = ROLE_USERS["PRIMARY_ADMIN"]
    wrong_thread = _message(ADMIN_CHAT_ID, user_id, chat_type="supergroup", thread_id=999)
    assert bot._can_run_admin_command(wrong_thread, user_id, "/admin") is False


@pytest.mark.parametrize("role,expected", sorted(EXPECTED_PANELS.items()))
def test_admin_home_panel_visibility_is_exact_for_non_owner_roles(runtime, role: str, expected: set[str]) -> None:
    _permissions, _bot, admin_ui = runtime
    callbacks = _panel_callbacks(admin_ui.admin_home_markup(role=role))
    assert callbacks == expected


def test_primary_admin_can_view_roles_but_cannot_mutate_roles(runtime) -> None:
    permissions, _bot, _admin_ui = runtime
    user_id = ROLE_USERS["PRIMARY_ADMIN"]
    assert permissions.has_permission(user_id, "roles.view") is True
    assert permissions.has_permission(user_id, "roles.write") is False


def test_strategy_mutation_authority_is_not_inherited_by_read_only_roles(runtime) -> None:
    permissions, _bot, _admin_ui = runtime
    strategy_admin = ROLE_USERS["STRATEGY_ADMIN"]
    assert permissions.has_permission(strategy_admin, "strategy.view") is True
    assert permissions.has_permission(strategy_admin, "strategy.thresholds.write") is True
    assert permissions.has_permission(strategy_admin, "strategy.sr.write") is True
    assert permissions.has_permission(strategy_admin, "strategy.spike.write") is True
    assert permissions.has_permission(strategy_admin, "strategy.symbols.write") is True

    for role in ("RESEARCH_ADMIN", "ANALYST", "MODERATOR", "AFFILIATE_ADMIN", "USER"):
        user_id = ROLE_USERS[role]
        assert permissions.has_permission(user_id, "strategy.thresholds.write") is False
        assert permissions.has_permission(user_id, "roles.write") is False


def test_research_and_analyst_are_read_oriented(runtime) -> None:
    permissions, _bot, _admin_ui = runtime
    for role in ("RESEARCH_ADMIN", "ANALYST"):
        user_id = ROLE_USERS[role]
        assert permissions.has_permission(user_id, "reports.view") is True
        assert permissions.has_permission(user_id, "debug.view") is True
        assert permissions.has_permission(user_id, "strategy.view") is True
        assert permissions.has_permission(user_id, "strategy.thresholds.write") is False
        assert permissions.has_permission(user_id, "roles.view") is False


def test_moderator_remains_support_and_health_scoped(runtime) -> None:
    permissions, _bot, _admin_ui = runtime
    user_id = ROLE_USERS["MODERATOR"]
    assert permissions.has_permission(user_id, "admin.view") is True
    assert permissions.has_permission(user_id, "engine.view") is True
    assert permissions.has_permission(user_id, "channels.view") is True
    assert permissions.has_permission(user_id, "strategy.view") is False
    assert permissions.has_permission(user_id, "affiliate.view") is False
    assert permissions.has_permission(user_id, "roles.view") is False


def test_affiliate_admin_is_own_scope_only(runtime) -> None:
    permissions, _bot, _admin_ui = runtime
    affiliate_id = ROLE_USERS["AFFILIATE_ADMIN"]
    assert permissions.has_permission(affiliate_id, "affiliate.view", target_affiliate_code="partner1") is True
    assert permissions.has_permission(affiliate_id, "affiliate.view", target_affiliate_code="PARTNER1") is True
    assert permissions.has_permission(affiliate_id, "affiliate.view", target_affiliate_code="partner2") is False
    assert permissions.has_permission(affiliate_id, "affiliate.view.any") is False

    primary_id = ROLE_USERS["PRIMARY_ADMIN"]
    assert permissions.has_permission(primary_id, "affiliate.view", target_affiliate_code="partner2") is True


def test_user_is_public_only_even_inside_admin_topic(runtime) -> None:
    permissions, bot, admin_ui = runtime
    user_id = ROLE_USERS["USER"]
    message = _message(ADMIN_CHAT_ID, user_id, chat_type="supergroup", thread_id=ADMIN_THREAD_ID)
    # Context alone is not authorization. The downstream permission gate must deny USER.
    assert bot._can_run_admin_command(message, user_id, "/admin") is True
    assert permissions.has_permission(user_id, "admin.view") is False
    assert _panel_callbacks(admin_ui.admin_home_markup(role="USER")) == set()


@pytest.mark.parametrize("role", [
    "PRIMARY_ADMIN", "STRATEGY_ADMIN", "RESEARCH_ADMIN", "ANALYST", "MODERATOR", "AFFILIATE_ADMIN"
])
def test_private_admin_callback_is_rejected_for_non_owner(runtime, role: str) -> None:
    _permissions, bot, _admin_ui = runtime
    user_id = ROLE_USERS[role]
    result = bot.handle_callback(
        chat_id=user_id,
        user_id=user_id,
        data="ADMIN_NAV:HOME",
        message_id=800,
    )
    assert result.get("__callback_recovery__") == "unauthorized"
    assert "denied" in str(result.get("text") or "").lower()


@pytest.mark.parametrize("role,action", sorted(ALLOWED_PANEL_SAMPLE.items()))
def test_allowed_role_panel_callback_works_in_admin_topic(runtime, role: str, action: str) -> None:
    _permissions, bot, _admin_ui = runtime
    user_id = ROLE_USERS[role]
    result = bot.handle_callback(
        chat_id=ADMIN_CHAT_ID,
        user_id=user_id,
        data=f"ADMIN_NAV:{action}",
        message_id=801,
        message_thread_id=ADMIN_THREAD_ID,
    )
    assert result.get("__callback_recovery__") != "unauthorized"
    assert "denied" not in str(result.get("text") or "").lower()
    assert isinstance(result.get("reply_markup"), dict)


@pytest.mark.parametrize("role", ["STRATEGY_ADMIN", "RESEARCH_ADMIN", "ANALYST", "MODERATOR", "AFFILIATE_ADMIN", "USER"])
def test_roles_panel_callback_is_denied_when_role_cannot_view_roles(runtime, role: str) -> None:
    _permissions, bot, _admin_ui = runtime
    user_id = ROLE_USERS[role]
    result = bot.handle_callback(
        chat_id=ADMIN_CHAT_ID,
        user_id=user_id,
        data="ADMIN_NAV:ROLES",
        message_id=802,
        message_thread_id=ADMIN_THREAD_ID,
    )
    assert "denied" in str(result.get("text") or "").lower() or result.get("__callback_recovery__") == "unauthorized"
