from __future__ import annotations

import importlib
import json
from pathlib import Path


def _wire_outcome_paths(outcome, root: Path) -> None:
    outcome.OUTCOMES_JSONL = str(root / "outcomes" / "outcomes.jsonl")
    outcome.OPEN_REGISTRY_JSON = str(root / "outcomes" / "open_now_registry.json")
    outcome.OUTCOMES_INDEX_JSON = str(root / "outcomes" / "outcomes_index.json")


def test_outcome_service_fails_closed_when_security_config_missing(canonical_runtime_root: Path, monkeypatch):
    outcome = importlib.import_module("core.outcome_service")
    _wire_outcome_paths(outcome, canonical_runtime_root)

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(outcome, "_elite_membership_ok", lambda user_id: (True, "ok"))

    result = outcome.handle_vote_callback(
        user_id=7,
        signal_id="sig-missing-config",
        outcome="WIN",
        now_ts=1720000500,
    )
    assert result["accepted"] is False
    assert result["reason"] in {"bot_token_missing", "outcome_security_config_missing", "unknown_signal_id"}


def test_unauthorized_admin_command_cannot_mutate_config(canonical_runtime_root: Path):
    admin = importlib.import_module("core.admin_commands")

    params_path = Path(admin._algo_params_path())
    before = json.loads(params_path.read_text(encoding="utf-8"))

    response = admin.handle_admin_command("/thresholds PRE 10", user_id=999999)

    after = json.loads(params_path.read_text(encoding="utf-8"))
    assert "Unauthorized" in response or "not authorized" in response.lower() or "❌" in response
    assert before == after


def test_outcome_rejects_unauthorized_callback_context(canonical_runtime_root: Path, monkeypatch):
    outcome = importlib.import_module("core.outcome_service")
    _wire_outcome_paths(outcome, canonical_runtime_root)

    monkeypatch.setattr(outcome, "_elite_membership_ok", lambda user_id: (True, "ok"))

    now_ts = 1720000600
    outcome.register_open_now(
        signal_id="sig-context",
        elite_chat_id=1004,
        open_message_id=701,
        open_now_ts=now_ts,
        expiry_minutes=1,
    )

    result = outcome.handle_vote_callback_data(
        callback_data="VOTE_|sig-context|WIN",
        user_id=9,
        now_ts=now_ts + 61,
        chat_id=2002,
        message_id=701,
    )

    assert result["accepted"] is False
    assert result["reason"] == "unauthorized_callback_context"
