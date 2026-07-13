from __future__ import annotations

import importlib


def test_callback_vote_parsing_delegates_without_network(monkeypatch):
    updates = importlib.import_module("runtime.telegram_updates")

    captured = {}

    monkeypatch.setattr(
        updates.outcome_service,
        "handle_vote_callback_data",
        lambda **kwargs: captured.setdefault("call", kwargs) or {"accepted": True, "reason": "ok"},
    )
    monkeypatch.setattr(updates, "_answer_callback_query", lambda callback_id, result: captured.setdefault("ack", (callback_id, result)))

    update = {
        "callback_query": {
            "id": "cb-1",
            "from": {"id": 77},
            "data": "VOTE_|sig-1|WIN",
            "message": {"chat": {"id": 1004}, "message_id": 9001},
        }
    }

    updates.process_update(update)

    assert captured["call"]["callback_data"] == "VOTE_|sig-1|WIN"
    assert captured["call"]["user_id"] == 77
    assert captured["call"]["chat_id"] == 1004
    assert captured["ack"][0] == "cb-1"
