from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.canonical.fakes.fake_publisher import FakePublisher
from tests.canonical.helpers.builders import make_signal_event
from tests.canonical.helpers.io import read_jsonl


def _wire_outcome_paths(outcome, root: Path) -> None:
    outcome.OUTCOMES_JSONL = str(root / "outcomes" / "outcomes.jsonl")
    outcome.OPEN_REGISTRY_JSON = str(root / "outcomes" / "open_now_registry.json")
    outcome.OUTCOMES_INDEX_JSON = str(root / "outcomes" / "outcomes_index.json")


def test_successful_signal_lifecycle_offline(canonical_runtime_root: Path, monkeypatch):
    router = importlib.import_module("core.distribution_router")
    outcome = importlib.import_module("core.outcome_service")
    analytics = importlib.import_module("core.analytics_engine")
    research = importlib.import_module("intelligence.research_engine")

    _wire_outcome_paths(outcome, canonical_runtime_root)
    fake = FakePublisher()
    monkeypatch.setattr(router.telegram_publisher, "send_message", fake.send_message)
    monkeypatch.setattr(outcome, "_elite_membership_ok", lambda user_id: (True, "ok"))

    event = make_signal_event("sig-e2e-ok", created_ts=1720001000)
    router.route(event, now_ts=1720001000)

    registry = json.loads((canonical_runtime_root / "outcomes" / "open_now_registry.json").read_text(encoding="utf-8"))
    contexts = registry["sig-e2e-ok"]["callback_contexts"]
    context = contexts[0]

    vote = outcome.handle_vote_callback_data(
        callback_data="VOTE_|sig-e2e-ok|WIN",
        user_id=88,
        now_ts=1720001301,
        chat_id=context["chat_id"],
        message_id=context["message_id"],
    )
    assert vote["accepted"] is True

    aggregates = analytics.recompute(now_ts=1720001400)
    report = research.build_research_report()
    research.persist_research_report(report)

    assert aggregates["wins"] >= 1
    assert aggregates["distribution"]["PUBLISHED"] >= 1
    assert report["research"]["advisory_only"] is True


def test_rejected_signal_lifecycle_emits_observability_without_side_effects(canonical_runtime_root: Path):
    signal_engine = importlib.import_module("core.signal_engine")

    (canonical_runtime_root / "config" / "active_symbols.json").write_text(json.dumps({"symbols": []}), encoding="utf-8")
    signal_engine.run_once(now_ts=1720002000)

    engine_events = read_jsonl(canonical_runtime_root / "observability" / "error_events.jsonl")
    assert any(e.get("event_type") == "warning" for e in engine_events)
    assert not (canonical_runtime_root / "outcomes" / "open_now_registry.json").exists()


def test_failure_lifecycle_publisher_exception_has_no_false_success(canonical_runtime_root: Path, monkeypatch):
    router = importlib.import_module("core.distribution_router")

    fake = FakePublisher(fail=True)
    monkeypatch.setattr(router.telegram_publisher, "send_message", fake.send_message)

    router.route(make_signal_event("sig-e2e-fail", created_ts=1720003000), now_ts=1720003000)

    dist = [
        e
        for e in read_jsonl(canonical_runtime_root / "observability" / "distribution_events.jsonl")
        if e.get("event_type") == "tier_publish"
    ]
    assert any(e["data"]["publish_result"] == "FAILED" for e in dist)
    assert not any(e["data"]["publish_result"] == "PUBLISHED" and e.get("signal_id") == "sig-e2e-fail" for e in dist)


def test_restart_lifecycle_preserves_dedup_and_no_duplicate_irreversible_action(canonical_runtime_root: Path, monkeypatch):
    router = importlib.import_module("core.distribution_router")

    fake = FakePublisher()
    monkeypatch.setattr(router.telegram_publisher, "send_message", fake.send_message)

    event = make_signal_event("sig-e2e-restart", created_ts=1720004000)
    router.route(event, now_ts=1720004000)
    first_calls = len(fake.calls)

    importlib.invalidate_caches()
    router_reloaded = importlib.reload(router)
    monkeypatch.setattr(router_reloaded.telegram_publisher, "send_message", fake.send_message)
    router_reloaded.route(event, now_ts=1720004001)

    assert len(fake.calls) == first_calls
    dist = [e for e in read_jsonl(canonical_runtime_root / "observability" / "distribution_events.jsonl") if e.get("signal_id") == "sig-e2e-restart"]
    assert any(e["data"]["publish_result"] == "DUPLICATE_SUPPRESSED" for e in dist)


def test_unauthorized_admin_lifecycle_is_blocked(canonical_runtime_root: Path):
    admin = importlib.import_module("core.admin_commands")

    before = Path(admin._algo_params_path()).read_text(encoding="utf-8")
    response = admin.handle_admin_command("/thresholds PRE 15", user_id=12345)
    after = Path(admin._algo_params_path()).read_text(encoding="utf-8")

    assert before == after
    assert "Unauthorized" in response or "not authorized" in response.lower() or "❌" in response


def test_parameter_update_lifecycle_is_atomic_and_consumed(canonical_runtime_root: Path):
    admin = importlib.import_module("core.admin_commands")
    params_loader = importlib.import_module("core.params_loader")

    admin._algo_params_path = lambda: str(canonical_runtime_root / "config" / "algo_params.json")
    admin.has_permission = lambda user_id, permission: True
    admin.require_permission = lambda user_id, permission, target_affiliate_code=None: (True, "ok")

    response = admin.handle_admin_command("/thresholds PRE 66", user_id=7553887987)
    assert "Threshold PRE set to 66" in response or "✅" in response

    params = params_loader.load_algo_params(admin._algo_params_path())
    assert params["score_thresholds"]["PRE"] == 66
