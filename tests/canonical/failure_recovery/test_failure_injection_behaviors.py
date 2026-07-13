from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.canonical.fakes.fake_publisher import FakePublisher
from tests.canonical.helpers.builders import make_signal_event
from tests.canonical.helpers.io import read_jsonl


def test_distribution_publisher_failure_has_no_false_success(canonical_runtime_root: Path, monkeypatch):
    router = importlib.import_module("core.distribution_router")

    fake = FakePublisher(fail=True)
    monkeypatch.setattr(router.telegram_publisher, "send_message", fake.send_message)

    router.route(make_signal_event("sig-failure"), now_ts=1720000700)

    events = read_jsonl(canonical_runtime_root / "observability" / "distribution_events.jsonl")
    free = [e for e in events if e.get("route") == "FREE"]
    assert free
    assert all(e["data"]["publish_result"] == "FAILED" for e in free)
    assert all(e["data"]["counted"] is False for e in free)


def test_outcome_persistence_failure_returns_explicit_error(canonical_runtime_root: Path, monkeypatch):
    outcome = importlib.import_module("core.outcome_service")
    storage = importlib.import_module("core.storage")

    monkeypatch.setattr(outcome, "_elite_membership_ok", lambda user_id: (True, "ok"))
    monkeypatch.setattr(storage, "append_jsonl", lambda path, record: (_ for _ in ()).throw(OSError("disk full")))

    now_ts = 1720000800
    outcome.register_open_now(
        signal_id="sig-out-fail",
        elite_chat_id=1004,
        open_message_id=702,
        open_now_ts=now_ts,
        expiry_minutes=1,
    )

    result = outcome.handle_vote_callback_data(
        callback_data="VOTE_|sig-out-fail|WIN",
        user_id=50,
        now_ts=now_ts + 61,
        chat_id=1004,
        message_id=702,
    )

    assert result["accepted"] is False
    assert result["reason"] == "persistence_failed"


def test_atomic_json_write_preserves_last_valid_state(tmp_path: Path):
    storage = importlib.import_module("core.storage")
    path = tmp_path / "state.json"

    storage.save_json_atomic(str(path), {"version": 1})
    before = json.loads(path.read_text(encoding="utf-8"))

    with pytest.raises(OSError):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(storage.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("replace failed")))
            storage.save_json_atomic(str(path), {"version": 2})

    after = json.loads(path.read_text(encoding="utf-8"))
    assert before == after
