"""R-032: Research overview is scan-free; Strategy Decisions uses bounded JSONL tail.

This test suite deliberately avoids touching runtime trading state or Telegram
network transport. Live Admin-topic acceptance remains a separate gate.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SEND = ROOT / "send"
if str(SEND) not in sys.path:
    sys.path.insert(0, str(SEND))


def _bot():
    return importlib.import_module("core.bot_service")


def _ui():
    return importlib.import_module("core.telegram_admin_ui")


def _message():
    return {
        "chat": {"id": -100999, "type": "supergroup"},
        "from": {"id": 12345},
        "message_id": 77,
    }


def _buttons(markup):
    return {
        button["callback_data"]
        for row in markup.get("inline_keyboard", [])
        for button in row
    }


def _authorized(monkeypatch, role="OWNER", admin_view=True):
    bot = _bot()
    perms = importlib.import_module("core.admin_permissions")
    monkeypatch.setattr(bot, "get_primary_role", lambda user_id: role)
    monkeypatch.setattr(
        perms, "has_permission",
        lambda user_id, perm: perm == "admin.view" and admin_view,
    )
    return bot


def _write(path: Path, rows: list) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def test_research_root_is_navigation_only_and_does_not_read_engine_events(monkeypatch):
    bot = _authorized(monkeypatch)
    monkeypatch.setattr(bot, "_find_latest_report_json", lambda: None)

    def blocked_read(*args, **kwargs):
        raise AssertionError("Research root must never open engine event files")

    monkeypatch.setattr(bot, "_iter_recent_engine_events", blocked_read)
    res = bot._handle_admin_navigation_action("RESEARCH", 12345, _message())
    assert "Select a report" in res["text"]
    assert "Strategy Decisions: recent strategy evaluations" in res["text"]
    assert "ADMIN_NAV:RESEARCH_STRATEGY" in _buttons(res["reply_markup"])
    assert "PRE: " not in res["text"]
    assert len(res["text"].encode("utf-16-le")) // 2 <= 3800


def test_strategy_subpage_is_not_new_canonical_root_and_back_is_safe():
    ui = _ui()
    assert ui.is_canonical_panel_action("RESEARCH")
    assert not ui.is_canonical_panel_action("RESEARCH_STRATEGY")
    assert ui.is_research_subpage_action("RESEARCH_STRATEGY")
    assert ui.CANONICAL_ADMIN_PARENT_MAP["RESEARCH_STRATEGY"] == "RESEARCH"
    root = _buttons(ui.research_markup())
    child = _buttons(ui.research_subpage_markup("RESEARCH_STRATEGY"))
    assert "ADMIN_NAV:RESEARCH_STRATEGY" in root
    assert {"ADMIN_NAV:RESEARCH_STRATEGY", "ADMIN_NAV:RESEARCH", "ADMIN_NAV:HOME"} <= child
    assert all(len(cb.encode("utf-8")) <= 64 for cb in child)


def test_strategy_reader_returns_latest_records_with_original_identity(tmp_path: Path, monkeypatch):
    bot = _bot()
    path = _write(
        tmp_path / "engine.jsonl",
        [
            {
                "event_id": f"E-{i}",
                "schema_version": "3.0.0" if i % 2 else "2.0.0",
                "event_type": "decision_evaluated",
                "data": {"decision_kind": "PRE"},
            }
            for i in range(20)
        ],
    )
    monkeypatch.setattr(bot, "ENGINE_EVENTS_PATH", str(path))
    result = bot._iter_recent_engine_events(limit=5)
    assert len(result) == 5
    assert [r["event_id"] for r in result] == [f"E-{i}" for i in range(15, 20)]
    assert result[0]["schema_version"] == "3.0.0"
    assert result[1]["schema_version"] == "2.0.0"


def test_strategy_tail_reads_only_small_recent_section_of_large_file(tmp_path: Path, monkeypatch):
    bot = _bot()
    path = tmp_path / "long_history.jsonl"
    # Valid append-only JSONL > 8 MiB; reading its last 5 small records must
    # not require loading/decoding historical contents.
    padding = "x" * 8500
    with path.open("w", encoding="utf-8") as handle:
        for i in range(1120):
            handle.write(json.dumps({"event_id": f"OLD-{i}", "padding": padding}) + "\n")
        for i in range(10):
            handle.write(json.dumps({"event_id": f"RECENT-{i}"}) + "\n")
    assert path.stat().st_size > bot._RESEARCH_STRATEGY_TAIL_MAX_BYTES
    monkeypatch.setattr(bot, "ENGINE_EVENTS_PATH", str(path))
    out = bot._iter_recent_engine_events(limit=5)
    assert [row["event_id"] for row in out] == [f"RECENT-{i}" for i in range(5, 10)]


def test_incomplete_tail_is_unknown_not_silent_partial_report(tmp_path: Path, monkeypatch):
    bot = _bot()
    path = _write(tmp_path / "engine.jsonl", [{"event_id": "1"}, {"event_id": "2"}])
    path.write_text(path.read_text() + '{"event_id": ', encoding="utf-8")
    monkeypatch.setattr(bot, "ENGINE_EVENTS_PATH", str(path))
    assert bot._iter_recent_engine_events(limit=3) is None


def test_unsupported_jsonl_record_returns_unknown(tmp_path: Path, monkeypatch):
    bot = _bot()
    source = _write(tmp_path / "engine.jsonl", [{"event_id": "1"}, ["not", "an", "event"]])
    monkeypatch.setattr(bot, "ENGINE_EVENTS_PATH", str(source))
    assert bot._iter_recent_engine_events(limit=50) is None


def test_missing_empty_and_oversized_single_record_are_distinguished(tmp_path: Path, monkeypatch):
    bot = _bot()
    monkeypatch.setattr(bot, "ENGINE_EVENTS_PATH", str(tmp_path / "missing"))
    assert bot._iter_recent_engine_events(limit=50) is None

    empty = tmp_path / "empty"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(bot, "ENGINE_EVENTS_PATH", str(empty))
    assert bot._iter_recent_engine_events(limit=50) == []

    huge = tmp_path / "oversized_line.jsonl"
    huge.write_text(
        json.dumps({"event_id": "LARGE", "payload": "A" * (bot._RESEARCH_STRATEGY_TAIL_MAX_BYTES + 10)})
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(bot, "ENGINE_EVENTS_PATH", str(huge))
    assert bot._iter_recent_engine_events(limit=5) is None


@pytest.mark.parametrize("limit", [0, -1, 501, True, 3.14, "500"])
def test_reader_limit_validation_fails_closed(limit):
    assert _bot()._iter_recent_engine_events(limit=limit) is None


def test_authorized_strategy_page_renders_recent_evidence(monkeypatch):
    bot = _authorized(monkeypatch, role="ANALYST")
    monkeypatch.setattr(
        bot, "_iter_recent_engine_events",
        lambda limit=500: [
            {
                "event_type": "decision_evaluated",
                "symbol": "EUR/USD",
                "timeframe": "M1",
                "data": {
                    "candle_ts": 1720000000,
                    "decision_kind": "PRE",
                    "score_total": 80.0,
                },
            }
        ],
    )
    response = bot._handle_admin_navigation_action(
        "RESEARCH_STRATEGY", 12345, _message()
    )
    assert "📋 Strategy Decisions" in response["text"]
    assert "PRE: 1" in response["text"]
    assert "No threshold or production-strategy change" in response["text"]
    assert "ADMIN_NAV:RESEARCH" in _buttons(response["reply_markup"])
    assert len(response["text"].encode("utf-16-le")) // 2 <= 3800


@pytest.mark.parametrize("role", ["USER", "STRATEGY_ADMIN", "MODERATOR", "AFFILIATE_ADMIN"])
def test_forged_strategy_report_action_denied_before_reader(monkeypatch, role):
    bot = _authorized(monkeypatch, role=role)
    def forbidden(*args, **kwargs):
        raise AssertionError("forged role must not read engine log")
    monkeypatch.setattr(bot, "_iter_recent_engine_events", forbidden)
    response = bot._handle_admin_navigation_action(
        "RESEARCH_STRATEGY", 12345, _message()
    )
    assert response["text"] == "Access denied (missing panel permission)."
    assert response["reply_markup"] is None


@pytest.mark.parametrize("role", ["RESEARCH_ADMIN", "ANALYST"])
def test_backend_admin_view_is_still_required_for_non_owner(monkeypatch, role):
    bot = _authorized(monkeypatch, role=role, admin_view=False)
    response = bot._handle_admin_navigation_action(
        "RESEARCH_STRATEGY", 12345, _message()
    )
    assert response["text"] == "Access denied (missing admin permission)."


def test_bounded_engine_source_failure_is_explicitly_unavailable(monkeypatch):
    bot = _authorized(monkeypatch, role="RESEARCH_ADMIN")
    monkeypatch.setattr(bot, "_iter_recent_engine_events", lambda limit=500: None)
    response = bot._handle_admin_navigation_action(
        "RESEARCH_STRATEGY", 12345, _message()
    )
    assert "UNAVAILABLE (engine event log absent or invalid)" in response["text"]
    assert "PRE: 0" not in response["text"]
