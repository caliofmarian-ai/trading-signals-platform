from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import count
from pathlib import Path

import pytest

from core import focus_history_evidence as focus


NOW = int(datetime(2026, 10, 30, 10, 0, tzinfo=timezone.utc).timestamp())
_IDS = count(1)


def _row(
    trigger: str,
    *,
    symbol: str = "EUR/USD",
    ts: int = NOW - 100,
    prev_state: str | None = None,
    new_state: str | None = None,
    version: str = "3.0.0",
    event_id: str | None = None,
) -> dict:
    if new_state is None:
        new_state = (
            "WATCHLIST"
            if trigger in {"watchlist_added", "watchlist_replaced", "watchlist_refreshed"}
            else "IDLE" if trigger == "focus_evicted_inactive" else "COOLDOWN"
        )
    if prev_state is None:
        prev_state = "IDLE" if trigger in {"watchlist_added", "watchlist_replaced"} else "WATCHLIST"
    return {
        "event_id": event_id or f"FSM-{next(_IDS)}",
        "event_type": "fsm_transition",
        "schema_version": version,
        "ts_epoch_ms": ts * 1000,
        "symbol": symbol,
        "data": {
            "symbol": symbol,
            "prev_state": prev_state,
            "new_state": new_state,
            "trigger": trigger,
            "signal_id": f"PRIVATE-SIGNAL-{symbol}",
            "candle_ts": ts,
        },
    }


def _write(path: Path, records: list[dict], *, malformed: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [json.dumps(x) for x in records]
    if malformed:
        payload.insert(1, "{invalid-json")
    path.write_text("\n".join(payload) + "\n", encoding="utf-8")
    return str(path)


def _history(tmp_path: Path, rows: list[dict], *, days: int = 7, malformed: bool = False):
    path = _write(tmp_path / "fsm_events.jsonl", rows, malformed=malformed)
    return focus.build_focus_history(range_days=days, now_ts=NOW, path=path)


def test_entry_refresh_and_explicit_exit_use_real_fsm_events(tmp_path: Path):
    h = _history(
        tmp_path,
        [
            _row("watchlist_added", ts=NOW - 350),
            _row("watchlist_refreshed", ts=NOW - 290),
            _row("focus_lease_expired", ts=NOW - 170),
        ],
    )
    assert h["status"] == "OBSERVED"
    assert h["truth_domain"] == "FSM_OPERATIONAL_TRUTH"
    assert (h["focus_entries"], h["focus_exits"], h["focus_refreshes"]) == (1, 1, 1)
    assert h["paired_explicit_entry_exit_count"] == 1
    assert h["median_observed_focus_seconds"] == 180.0
    assert h["unmatched_entry_count"] == 0
    assert h["unmatched_exit_count"] == 0
    assert [x["action"] for x in h["recent_events"]] == ["ENTER", "REFRESH", "EXIT"]


def test_replacement_reports_missing_victim_exit_without_backfill(tmp_path: Path):
    h = _history(
        tmp_path,
        [
            _row("watchlist_added", symbol="EUR/USD", ts=NOW - 600),
            _row("watchlist_replaced", symbol="GBP/USD", ts=NOW - 300),
            _row("focus_lease_expired", symbol="GBP/USD", ts=NOW - 100),
        ],
    )
    assert h["focus_entries"] == 2
    assert h["focus_exits"] == 1
    assert h["replacement_entries_without_victim_exit"] == 1
    assert h["unmatched_entry_count"] == 1
    assert h["paired_explicit_entry_exit_count"] == 1
    assert h["median_observed_focus_seconds"] == 200
    assert h["history_coverage"] == "PARTIAL_EXPLICIT_FSM_EVENTS_ONLY"


def test_exit_without_observed_entry_does_not_create_fake_duration(tmp_path: Path):
    h = _history(tmp_path, [_row("reject_released")])
    assert h["status"] == "OBSERVED"
    assert h["focus_exits"] == 1
    assert h["unmatched_exit_count"] == 1
    assert h["paired_explicit_entry_exit_count"] == 0
    assert h["median_observed_focus_seconds"] is None


def test_non_focus_fsm_transitions_are_not_falsely_promoted(tmp_path: Path):
    h = _history(tmp_path, [_row("confirm_seen", new_state="CONFIRMED")])
    assert h["status"] == "UNKNOWN"
    assert h["reason"] == "NO_VALID_PRIMARY_V3_FOCUS_EVENTS_IN_WINDOW"
    assert h["focus_entries"] is None
    assert h["quality"]["primary_fsm_rows"] == 1


def test_legacy_and_missing_source_are_unknown_not_zero(tmp_path: Path):
    legacy = _history(
        tmp_path, [_row("watchlist_added", version="2.0.0")],
    )
    assert legacy["status"] == "UNKNOWN"
    assert legacy["quality"]["historical_excluded"] == 1
    missing = focus.build_focus_history(now_ts=NOW, path=str(tmp_path / "missing"))
    assert missing["status"] == "UNKNOWN"
    assert missing["focus_entries"] is None
    assert "UNKNOWN — not zero" in focus.render_focus_history(missing)


def test_duplicate_event_id_counted_once_and_conflict_fails_closed(tmp_path: Path):
    enter = _row("watchlist_added", event_id="SAME")
    duplicate = dict(enter)
    h = _history(tmp_path, [enter, duplicate])
    assert h["focus_entries"] == 1
    assert h["quality"]["duplicate_event_ids"] == 1
    conflicting = _row("focus_lease_expired", event_id="SAME")
    collision = _history(tmp_path, [enter, conflicting])
    assert collision["status"] == "UNKNOWN"
    assert collision["reason"] == "CONFLICTING_FSM_EVENT_ID"
    assert collision["focus_entries"] is None


def test_out_of_order_appends_sorted_by_timestamp_not_file_position(tmp_path: Path):
    h = _history(
        tmp_path, [
            _row("focus_lease_expired", ts=NOW - 120),
            _row("watchlist_added", ts=NOW - 420),
        ]
    )
    assert h["paired_explicit_entry_exit_count"] == 1
    assert h["median_observed_focus_seconds"] == 300


def test_ambiguous_second_entry_does_not_create_false_pair(tmp_path: Path):
    h = _history(
        tmp_path,
        [
            _row("watchlist_added", ts=NOW - 450),
            _row("watchlist_replaced", ts=NOW - 380),
            _row("reject_released", ts=NOW - 160),
        ],
    )
    assert h["ambiguous_reentry_count"] == 1
    assert h["paired_explicit_entry_exit_count"] == 0
    assert h["unmatched_exit_count"] == 1


def test_unsupported_focus_states_not_reported_as_real_changes(tmp_path: Path):
    fake_entry = _row("watchlist_added", new_state="IDLE")
    fake_exit = _row("focus_evicted_inactive", new_state="WATCHLIST")
    h = _history(tmp_path, [fake_entry, fake_exit, _row("watchlist_added")])
    assert h["focus_entries"] == 1
    assert h["focus_exits"] == 0
    assert h["quality"]["unsupported_focus_transitions"] == 2


def test_malformed_json_and_symbol_identity_are_excluded(tmp_path: Path):
    unsafe = _row("watchlist_added", symbol="SECRET\nTOKEN")
    inconsistent = _row("watchlist_added", symbol="GBP/USD")
    inconsistent["symbol"] = "EUR/USD"
    h = _history(tmp_path, [unsafe, inconsistent, _row("watchlist_added")], malformed=True)
    assert h["status"] == "OBSERVED"
    assert h["focus_entries"] == 1
    assert h["quality"]["invalid_rows"] == 3
    s = focus.render_focus_history(h)
    assert "TOKEN" not in s
    assert "PRIVATE-SIGNAL" not in s


def test_window_boundaries_and_future_rows_not_inferred(tmp_path: Path):
    h = _history(
        tmp_path,
        [
            _row("watchlist_added", ts=NOW - 86400),
            _row("watchlist_added", symbol="GBP/USD", ts=NOW),
            _row("watchlist_added", symbol="USD/JPY", ts=NOW - 86401),
            _row("watchlist_added", symbol="AUD/USD", ts=NOW + 1),
        ],
        days=1,
    )
    assert h["focus_entries"] == 2
    assert h["quality"]["out_of_window"] == 2
    assert h["window_start_utc"] == "2026-10-29T10:00:00Z"
    assert h["window_end_utc"] == "2026-10-30T10:00:00Z"


def test_oversized_log_fails_closed_instead_of_blocking_telegram(tmp_path: Path):
    huge = tmp_path / "fsm.jsonl"
    with huge.open("wb") as f:
        f.truncate(focus.MAX_INTERACTIVE_BYTES + 1)
    h = focus.build_focus_history(path=str(huge), now_ts=NOW)
    assert h["status"] == "UNKNOWN"
    assert h["reason"] == "SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN"
    assert h["focus_event_count"] is None


def test_reader_is_read_only_and_does_not_modify_log(tmp_path: Path):
    source = tmp_path / "fsm.jsonl"
    _write(source, [_row("watchlist_added"), _row("focus_lease_expired")])
    before = source.read_bytes()
    result = focus.build_focus_history(path=str(source), now_ts=NOW)
    assert result["status"] == "OBSERVED"
    assert source.read_bytes() == before


@pytest.mark.parametrize("window", [0, 31, -1, True, 2.5, "7"])
def test_invalid_range_fails_closed(window):
    with pytest.raises(ValueError):
        focus.build_focus_history(range_days=window)


@pytest.mark.parametrize("clock", [0, -10, True, 1.5, "2026-10-30"])
def test_invalid_time_fails_closed(clock):
    with pytest.raises(ValueError):
        focus.build_focus_history(now_ts=clock)


def test_analytics_get_focus_history_replaces_placeholder(tmp_path: Path, monkeypatch):
    import core
    from core import analytics_engine

    source = _write(tmp_path / "fsm.jsonl", [_row("watchlist_added")])
    monkeypatch.setenv("FSM_EVENTS_LOG", source)
    monkeypatch.setattr(core, "focus_history_evidence", focus, raising=False)

    result = analytics_engine.get_focus_history(7)
    assert result["status"] == "OBSERVED"
    assert result["focus_entries"] == 1
    assert result["source"] == "PRIMARY_V3_FSM_TRANSITION"


def test_research_panel_focus_history_requires_admin_permission(tmp_path: Path, monkeypatch):
    import core
    from core import admin_permissions, bot_service, publication_evidence
    from core import lifecycle_funnel_evidence, market_outcome_evidence
    from core.role_constants import ROLE_OWNER, ROLE_USER

    source = _write(tmp_path / "fsm.jsonl", [_row("watchlist_added")])
    monkeypatch.setenv("FSM_EVENTS_LOG", source)
    for key, value in (
        ("focus_history_evidence", focus),
        ("publication_evidence", publication_evidence),
        ("lifecycle_funnel_evidence", lifecycle_funnel_evidence),
        ("market_outcome_evidence", market_outcome_evidence),
    ):
        monkeypatch.setattr(core, key, value, raising=False)
    monkeypatch.setattr(bot_service, "_iter_recent_engine_events", lambda limit=500: [])
    monkeypatch.setattr(
        admin_permissions, "has_permission",
        lambda _user_id, permission: permission == "admin.view",
    )
    monkeypatch.setattr(bot_service, "get_primary_role", lambda _: ROLE_OWNER)
    response = bot_service._handle_admin_navigation_action(
        "RESEARCH_FOCUS", 123,
        {"chat": {"id": -100456, "type": "supergroup"}, "from": {"id": 123}},
    )
    assert "FSM Focus / Watchlist History" in response["text"]
    assert "Entries / exits / refreshes: 1 / 0 / 0" in response["text"]
    monkeypatch.setattr(bot_service, "get_primary_role", lambda _: ROLE_USER)
    forbidden = bot_service._handle_admin_navigation_action(
        "RESEARCH_FOCUS", 123,
        {"chat": {"id": -100456, "type": "supergroup"}, "from": {"id": 123}},
    )
    assert forbidden["text"] == "Access denied (missing panel permission)."
