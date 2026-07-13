from __future__ import annotations

import importlib
from pathlib import Path

from tests.canonical.fakes.fake_publisher import FakePublisher
from tests.canonical.helpers.builders import make_signal_event
from tests.canonical.helpers.io import read_jsonl


def test_fsm_and_distribution_open_now_flow(canonical_runtime_root: Path, monkeypatch):
    fsm = importlib.import_module("core.fsm_runtime")
    router = importlib.import_module("core.distribution_router")

    fake = FakePublisher()
    monkeypatch.setattr(router.telegram_publisher, "send_message", fake.send_message)

    state = fsm.load_state()
    decision = {
        "kind": "PRE",
        "signal_id": "sig-int",
        "symbol": "EURUSD",
        "candle_ts": 1720000000,
        "score_total": 80,
        "expiry_minutes": 5,
    }
    state, event = fsm.apply_transition(state, decision, now_ts=1720000001)
    assert event["new_state"] == "WATCHLIST"

    state, event = fsm.apply_transition(state, {**decision, "kind": "OPEN_NOW"}, now_ts=1720000002)
    assert event["new_state"] == "LIVE_SENT"

    router.route(make_signal_event("sig-int"), now_ts=1720000002)

    dist = read_jsonl(canonical_runtime_root / "observability" / "distribution_events.jsonl")
    assert any(ev.get("data", {}).get("publish_result") == "PUBLISHED" for ev in dist)
    assert fake.calls


def test_outcome_flow_records_vote_and_deduplicates(canonical_runtime_root: Path, monkeypatch):
    outcome = importlib.import_module("core.outcome_service")

    monkeypatch.setattr(outcome, "_elite_membership_ok", lambda user_id: (True, "ok"))

    now_ts = 1720000100
    reg = outcome.register_open_now(
        signal_id="sig-outcome",
        elite_chat_id=1004,
        open_message_id=700,
        open_now_ts=now_ts,
        expiry_minutes=1,
    )
    assert reg["status"] == "registered"

    result = outcome.handle_vote_callback_data(
        callback_data="VOTE_|sig-outcome|WIN",
        user_id=42,
        now_ts=now_ts + 61,
        chat_id=1004,
        message_id=700,
    )
    duplicate = outcome.handle_vote_callback_data(
        callback_data="VOTE_|sig-outcome|WIN",
        user_id=42,
        now_ts=now_ts + 62,
        chat_id=1004,
        message_id=700,
    )

    assert result["accepted"] is True
    assert duplicate["accepted"] is True
    assert duplicate["reason"] in {"already_processed", "already_voted"}

    records = read_jsonl(canonical_runtime_root / "outcomes" / "outcomes.jsonl")
    assert len([r for r in records if r.get("signal_id") == "sig-outcome"]) == 1
