"""R-031 Research navigation / Telegram 4096-character transport budget.

There is still one canonical RESEARCH root. Data reports are read-only child
pages, with the same authorization and single-message editing path.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))


PAGES = (
    ("RESEARCH_PUBLICATIONS", "publication_evidence", "publication_snapshot", "render_publication_summary"),
    ("RESEARCH_LIFECYCLE", "lifecycle_funnel_evidence", "build_funnel", "render_funnel_summary"),
    ("RESEARCH_MARKET", "market_outcome_evidence", "build_market_snapshot", "render_market_summary"),
    ("RESEARCH_FOCUS", "focus_history_evidence", "build_focus_history", "render_focus_history"),
)


def _modules():
    import core

    modules = {
        "bot": importlib.import_module("core.bot_service"),
        "ui": importlib.import_module("core.telegram_admin_ui"),
        "perms": importlib.import_module("core.admin_permissions"),
    }
    for _, name, _, _ in PAGES:
        module = importlib.import_module(f"core.{name}")
        # Other repository tests re-import core modules; the handler uses
        # function-local package imports, which must see the same spy object.
        modules[name] = module
        setattr(core, name, module)
    return modules


def _message():
    return {
        "chat": {"id": -100999, "type": "supergroup"},
        "from": {"id": 12345},
        "message_id": 77,
    }


def _actions(markup):
    return {
        button["callback_data"]
        for row in markup["inline_keyboard"]
        for button in row
    }


def _utf16_units(text):
    return len(text.encode("utf-16-le")) // 2


def _authorized(monkeypatch, modules, role="OWNER"):
    monkeypatch.setattr(modules["bot"], "get_primary_role", lambda user_id: role)
    monkeypatch.setattr(
        modules["perms"],
        "has_permission",
        lambda user_id, permission: permission == "admin.view",
    )


def test_research_uses_only_one_canonical_root_and_short_bounded_callbacks():
    ui = importlib.import_module("core.telegram_admin_ui")
    assert ui.is_canonical_panel_action("RESEARCH")
    assert ui.CANONICAL_ADMIN_PARENT_MAP["RESEARCH"] == "HOME"
    assert not ui.is_research_subpage_action("RESEARCH")
    all_actions = {row[0] for row in PAGES}
    root_buttons = _actions(ui.research_markup())
    assert {"ADMIN_NAV:" + action for action in all_actions} <= root_buttons

    for action in all_actions:
        assert not ui.is_canonical_panel_action(action)
        assert ui.is_research_subpage_action(action)
        assert ui.CANONICAL_ADMIN_PARENT_MAP[action] == "RESEARCH"
        buttons = _actions(ui.research_subpage_markup(action))
        assert "ADMIN_NAV:RESEARCH" in buttons
        assert "ADMIN_NAV:HOME" in buttons
        assert "ADMIN_NAV:" + action in buttons
        assert all(len(c.encode("utf-8")) <= 64 for c in buttons)
    assert ui.is_research_subpage_action("not-a-page") is False


def test_research_overview_never_reads_every_report_source(monkeypatch):
    modules = _modules()
    _authorized(monkeypatch, modules)
    bot = modules["bot"]
    monkeypatch.setattr(bot, "_iter_recent_engine_events", lambda limit=500: [])
    monkeypatch.setattr(bot, "_find_latest_report_json", lambda: None)

    for _, name, builder, _ in PAGES:
        def forbid(*args, _name=name, **kwargs):
            raise AssertionError(f"root must not scan {_name}")

        monkeypatch.setattr(modules[name], builder, forbid)

    response = bot._handle_admin_navigation_action("RESEARCH", 12345, _message())
    assert "Research & Analytics" in response["text"]
    assert "Select a report to inspect" in response["text"]
    assert "Strategy Decisions: recent strategy evaluations" in response["text"]
    assert "ADMIN_NAV:RESEARCH_STRATEGY" in _actions(response["reply_markup"])
    assert _utf16_units(response["text"]) <= bot._RESEARCH_TELEGRAM_TEXT_BUDGET
    assert "ADMIN_NAV:RESEARCH_PUBLICATIONS" in _actions(response["reply_markup"])
    assert "ADMIN_NAV:RESEARCH_MARKET" in _actions(response["reply_markup"])


@pytest.mark.parametrize("action,name,builder,renderer", PAGES)
def test_each_detail_page_reads_only_its_one_source(
    monkeypatch, action, name, builder, renderer
):
    modules = _modules()
    _authorized(monkeypatch, modules, role="ANALYST")
    calls = []

    for _, source, reader, render in PAGES:
        def build(*args, _source=source, **kwargs):
            calls.append(_source)
            return {"name": _source}

        monkeypatch.setattr(modules[source], reader, build)
        monkeypatch.setattr(
            modules[source],
            render,
            lambda snapshot, _source=source: f"INDEPENDENT_{_source.upper()}",
        )

    response = modules["bot"]._handle_admin_navigation_action(action, 12345, _message())
    assert calls == [name]
    assert f"INDEPENDENT_{name.upper()}" in response["text"]
    assert _utf16_units(response["text"]) <= 3800
    actions = _actions(response["reply_markup"])
    assert "ADMIN_NAV:RESEARCH" in actions
    assert "ADMIN_NAV:" + action in actions


@pytest.mark.parametrize("action", [x[0] for x in PAGES])
@pytest.mark.parametrize("role", ["USER", "STRATEGY_ADMIN", "MODERATOR", "AFFILIATE_ADMIN"])
def test_forged_research_child_denied_at_existing_panel_role_ceiling(monkeypatch, action, role):
    modules = _modules()
    _authorized(monkeypatch, modules, role=role)
    response = modules["bot"]._handle_admin_navigation_action(action, 12345, _message())
    assert response["text"] == "Access denied (missing panel permission)."
    assert response["reply_markup"] is None


@pytest.mark.parametrize("action", [x[0] for x in PAGES])
@pytest.mark.parametrize("role", ["RESEARCH_ADMIN", "ANALYST"])
def test_non_owner_research_child_requires_admin_view_backend_permission(
    monkeypatch, action, role
):
    modules = _modules()
    monkeypatch.setattr(modules["bot"], "get_primary_role", lambda user_id: role)
    monkeypatch.setattr(modules["perms"], "has_permission", lambda *_args: False)
    response = modules["bot"]._handle_admin_navigation_action(action, 12345, _message())
    assert response["text"] == "Access denied (missing admin permission)."
    assert response["reply_markup"] is None


def test_research_message_budget_preserves_no_partial_or_fabricated_data():
    bot = importlib.import_module("core.bot_service")
    huge = "SENSITIVE_EVIDENCE_MARKER " + "X" * 8000
    output = bot._bounded_research_page("Research", huge)
    assert _utf16_units(output) <= bot._RESEARCH_TELEGRAM_TEXT_BUDGET
    assert "SENSITIVE_EVIDENCE_MARKER" not in output
    assert "UNAVAILABLE" in output
    assert "No partial data" in output
    assert "not be read as zero" in output


def test_emoji_are_counted_in_utf16_not_only_python_codepoints():
    bot = importlib.import_module("core.bot_service")
    output = bot._bounded_research_page("Research", "😀" * 2200)
    assert "UNAVAILABLE" in output
    assert _utf16_units(output) <= 3800


@pytest.mark.parametrize("action,name,builder,renderer", PAGES)
def test_oversized_individual_reports_fail_closed_without_truncation(
    monkeypatch, action, name, builder, renderer
):
    modules = _modules()
    _authorized(monkeypatch, modules, role="RESEARCH_ADMIN")
    marker = "VERY_LONG_REPORT_WITH_PRIVATE_ID"
    monkeypatch.setattr(modules[name], builder, lambda *args, **kwargs: {})
    monkeypatch.setattr(modules[name], renderer, lambda data: marker + "x" * 9000)
    response = modules["bot"]._handle_admin_navigation_action(action, 12345, _message())
    assert marker not in response["text"]
    assert "UNAVAILABLE" in response["text"]
    assert _utf16_units(response["text"]) <= 3800


def test_research_page_exception_is_unknown_not_fabricated_success(monkeypatch):
    modules = _modules()
    _authorized(monkeypatch, modules)
    monkeypatch.setattr(
        modules["market_outcome_evidence"],
        "build_market_snapshot",
        lambda **kwargs: (_ for _ in ()).throw(OSError("private output")),
    )
    response = modules["bot"]._handle_admin_navigation_action(
        "RESEARCH_MARKET", 12345, _message()
    )
    assert "UNKNOWN" in response["text"]
    assert "private output" not in response["text"]
    assert "ADMIN_NAV:RESEARCH" in _actions(response["reply_markup"])
