from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


SEND_ROOT = Path(__file__).resolve().parents[3] / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge() -> None:
    for name in list(sys.modules):
        if name == "core" or name.startswith("core.") or name == "state_store" or name.startswith("state_store."):
            sys.modules.pop(name, None)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "runtime"
    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "channel_config.json"
    config_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "FREE_CHANNEL_ID": 1001,
                "BASIC_CHANNEL_ID": None,
                "PRO_CHANNEL_ID": None,
                "ELITE_CHANNEL_ID": None,
                "ADMIN_GROUP_ID": None,
                "SIGNALS_LIVE_TOPIC_ID": None,
                "TZ": "Europe/London",
                "RESET_TIME": "23:59",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("OBS_DIR", str(root / "observability"))
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(root / "observability" / "engine_events.jsonl"))
    monkeypatch.setenv("FSM_EVENTS_LOG", str(root / "observability" / "fsm_events.jsonl"))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(root / "observability" / "distribution_events.jsonl"))
    monkeypatch.setenv("ADMIN_PROOFS_LOG", str(root / "observability" / "admin_proofs.jsonl"))
    monkeypatch.setenv("ERROR_EVENTS_LOG", str(root / "observability" / "error_events.jsonl"))
    monkeypatch.setenv("OUTCOMES_LOG", str(root / "outcomes" / "outcomes.jsonl"))
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "TWELVE_DATA")
    monkeypatch.delenv("FREE_LIMIT", raising=False)
    monkeypatch.delenv("BASIC_LIMIT", raising=False)
    monkeypatch.delenv("PRO_LIMIT", raising=False)
    monkeypatch.delenv("ELITE_LIMIT", raising=False)

    _purge()
    importlib.invalidate_caches()
    obs = importlib.import_module("core.observability_logger")
    legacy = importlib.import_module("core.distribution_router")
    router = importlib.import_module("core.distribution_router_v3")
    outcome = importlib.import_module("core.outcome_service")

    legacy.DIST_STATE_PATH = str(root / "state" / "dist_state.json")
    legacy.CHANNEL_CONFIG_PATHS = [str(config_path)]
    outcome.OUTCOMES_JSONL = str(root / "outcomes" / "outcomes.jsonl")
    outcome.OPEN_REGISTRY_JSON = str(root / "outcomes" / "open_now_registry.json")
    outcome.OUTCOMES_INDEX_JSON = str(root / "outcomes" / "outcomes_index.json")
    return root, obs, legacy, router, outcome


def _candidate(stage: str = "PRE", signal_id: str = "sig-v3-live", *, exact_expiry: float = 4.5) -> dict[str, Any]:
    event: dict[str, Any] = {
        "event_type": "SIGNAL_CANDIDATE",
        "schema_version": "3.0.0",
        "stage": stage,
        "signal_id": signal_id,
        "symbol": "EUR/USD",
        "timeframe": "M1",
        "direction": "BUY",
        "score_total": 88.5,
        "buffer_mode": "MEDIUM",
        "buffer_distance": 0.0008,
        "buffer_price": 0.0008,
        "model_expiry": 5.0,
        "execution_time_available": False,
        "confirm_expiry_min_minutes": None,
        "confirm_expiry_max_minutes": None,
        "open_now_expiry_minutes": None,
        "execution_calibration_source": None,
        "expiry_minutes": None,
        "candle_ts": 1_720_000_000,
        "created_ts": 1_720_000_005,
        "entry_price": 1.11234,
        "payload": {"trade_physics": {"TPS": 82.0}},
        "distribution_enabled": False,
    }
    if stage == "OPEN_NOW":
        event.update(
            execution_time_available=True,
            confirm_expiry_min_minutes=4.0,
            confirm_expiry_max_minutes=6.0,
            open_now_expiry_minutes=exact_expiry,
            execution_calibration_source="test-calibration-v1",
            expiry_minutes=exact_expiry,
        )
    return event


def test_free_default_is_six_and_missing_routes_become_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, obs, legacy, router, _ = _setup(tmp_path, monkeypatch)
    sends: list[int] = []
    rendered: list[str] = []

    def _send_message(chat_id: int, text: str, reply_markup=None, thread_id=None):
        sends.append(chat_id)
        rendered.append(text)
        return {"ok": True, "result": {"message_id": 501}}

    monkeypatch.setattr(legacy.telegram_publisher, "send_message", _send_message)

    assert router._load_effective_config()["limits"]["FREE"] == 6
    summary = router.route(_candidate("PRE"), now_ts=1_720_000_100)

    assert sends == [1001]
    assert summary["published_count"] == 1
    assert summary["failed_count"] == 0
    assert summary["skipped_count"] == 3
    assert rendered and "Exp: None" not in rendered[0]
    assert "Exp:" not in rendered[0]

    state = legacy.load_state()
    assert state["tier_state"]["FREE"] == "ACTIVE"
    assert state["tier_state"]["BASIC"] == "DISABLED"
    assert state["tier_state"]["PRO"] == "DISABLED"
    assert state["tier_state"]["ELITE"] == "DISABLED"
    assert state["open_signals_today"]["FREE"] == 0

    events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    primary_results = [e for e in events if e["event_type"] == "route_publish_result"]
    visible = [e for e in events if e["event_type"] == "signal_stage_visible"]
    attempts = [e for e in events if e["event_type"] == "route_publish_attempt"]
    adapters = [e for e in events if e["event_type"] == "tier_publish"]

    assert len(primary_results) == 4
    assert len(attempts) == 4
    assert len(adapters) == 4
    assert len(visible) == 1
    assert visible[0]["signal_id"] == "sig-v3-live"
    assert visible[0]["stage"] == "PRE"
    assert any(
        e["route"] == "FREE" and e["data"]["publish_result"] == "PUBLISHED"
        for e in primary_results
    )
    assert all(obs.validate_event(event) == event for event in primary_results + visible + attempts)


def test_open_now_without_governed_execution_time_is_blocked_before_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    sends: list[int] = []
    monkeypatch.setattr(
        legacy.telegram_publisher,
        "send_message",
        lambda **kwargs: sends.append(kwargs["chat_id"]),
    )
    forged = _candidate("PRE", "sig-forged")
    forged["stage"] = "OPEN_NOW"
    forged["expiry_minutes"] = forged["model_expiry"]

    summary = router.route(forged, now_ts=1_720_000_100)

    assert summary["blocked"] is True
    assert summary["block_reason"] == "EXECUTION_TIME_UNAVAILABLE"
    assert sends == []


def test_open_now_counts_only_success_and_silences_free_at_six(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    state = legacy._default_state()
    state["open_signals_today"]["FREE"] = 5
    legacy.save_state(state)
    rendered: list[str] = []

    def _send_message(**kwargs):
        rendered.append(kwargs["text"])
        return {"ok": True, "result": {"message_id": 601}}

    monkeypatch.setattr(legacy.telegram_publisher, "send_message", _send_message)

    summary = router.route(_candidate("OPEN_NOW", "sig-v3-open", exact_expiry=4.77), now_ts=1_720_000_100)
    final_state = legacy.load_state()

    assert summary["published_count"] == 1
    assert final_state["open_signals_today"]["FREE"] == 6
    assert final_state["tier_state"]["FREE"] == "SILENT"
    assert len(summary["publication_evidence"]) == 1
    assert summary["publication_evidence"][0]["route"] == "FREE"
    assert rendered and "Exp: 4.77m" in rendered[0]
    assert "Exp: 5m" not in rendered[0]


def test_distribution_rejects_mismatched_execution_expiry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    sends: list[int] = []
    monkeypatch.setattr(
        legacy.telegram_publisher,
        "send_message",
        lambda **kwargs: sends.append(kwargs["chat_id"]),
    )
    event = _candidate("OPEN_NOW", "sig-mismatch", exact_expiry=4.77)
    event["expiry_minutes"] = 5.0

    summary = router.route(event, now_ts=1_720_000_100)

    assert summary["blocked"] is True
    assert summary["block_reason"] == "EXECUTION_TIME_COMPATIBILITY_MISMATCH"
    assert sends == []


def test_failed_publication_never_creates_visibility_or_counter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _, legacy, router, _ = _setup(tmp_path, monkeypatch)

    def _fail(**kwargs):
        raise RuntimeError("telegram unavailable")

    monkeypatch.setattr(legacy.telegram_publisher, "send_message", _fail)
    summary = router.route(_candidate("OPEN_NOW", "sig-v3-fail"), now_ts=1_720_000_100)

    assert summary["published_count"] == 0
    assert summary["failed_count"] == 1
    assert legacy.load_state()["open_signals_today"]["FREE"] == 0
    events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    assert not [e for e in events if e["event_type"] == "signal_stage_visible"]
    free_result = [
        e
        for e in events
        if e["event_type"] == "route_publish_result" and e.get("route") == "FREE"
    ]
    assert len(free_result) == 1
    assert free_result[0]["data"]["publish_result"] == "FAILED"


def test_community_feedback_preserves_fractional_execution_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, obs, _, _, outcome = _setup(tmp_path, monkeypatch)
    result = outcome.register_open_now(
        signal_id="sig-feedback-v3",
        elite_chat_id=1004,
        open_message_id=700,
        open_now_ts=1_720_000_000,
        expiry_minutes=4.77,
        symbol="EUR/USD",
        direction="BUY",
        timeframe="M1",
    )
    meta = result["meta"]
    assert meta["expiry_minutes"] == pytest.approx(4.77)
    assert meta["expiry_ts"] - meta["open_now_ts"] == pytest.approx(4.77 * 60)
    assert meta["vote_end_ts"] - meta["activation_ts"] == pytest.approx(10 * 60)

    record = outcome._build_vote_record(
        signal_id="sig-feedback-v3",
        outcome="WIN",
        member_ref="M-TEST123",
        now_ts=int(meta["activation_ts"] + 1),
        meta=meta,
        callback_context={"route": "ELITE"},
    )
    assert record["truth_source"] == "COMMUNITY_SELF_REPORT"
    assert record["record_schema_version"] == "3.0.0"
    assert record["expiry_minutes"] == pytest.approx(4.77)

    event = obs.build_event(
        "user_outcome",
        {
            "outcome": "WIN",
            "truth_source": "COMMUNITY_SELF_REPORT",
            "policy": "LOCK_FIRST_WRITE_WINS",
            "accepted": True,
            "rejected_reason": None,
            "vote_window": {},
        },
        source={"module": "tests", "function": "community_truth"},
        correlation={"signal_id": "sig-feedback-v3", "tier": "ELITE", "user_id": "M-TEST123"},
    )
    assert obs.validate_event(event) == event


def test_post_distribution_emitted_requires_publication_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _, _, _, _ = _setup(tmp_path, monkeypatch)
    signal_engine = importlib.import_module("core.signal_engine")

    decision = SimpleNamespace(
        signal_id="sig-post-v3",
        kind="PRE",
        setup=SimpleNamespace(
            symbol="EUR/USD",
            timeframe="M1",
            cycle_id="cycle-post-v3",
        ),
        to_dict=lambda: {"score": {"trade_physics": {"TPS": 80.0}}},
    )
    persistent = SimpleNamespace(
        requested_stage="PRE",
        accepted_stage="PRE",
        signal_id="sig-post-v3",
        prior_state="IDLE",
        resulting_state="WATCHLIST",
        state_changed=True,
        reason="PRE_ACCEPTED",
        reason_family="LIFECYCLE",
        stage_handoff_ready=True,
        trade_execution_ready=False,
    )
    execution = SimpleNamespace(
        execution_attempt_id="attempt-post-v3",
        setup_correlation_id="cycle-post-v3",
        decision_id="decision-post-v3",
        decision_audit_id="decision-audit-post-v3",
        fsm_transition_id="fsm-post-v3",
        stage_handoff_ready=True,
        trade_execution_ready=False,
        execution_time_available=False,
        execution_calibration_source=None,
        execution_time_explanation="No trader-facing timing for PRE.",
        candidate=SimpleNamespace(schema_version="3.0.0"),
    )
    summary = {
        "published_count": 1,
        "failed_count": 0,
        "skipped_count": 3,
        "blocked": False,
        "publication_evidence": [
            {
                "event_id": "route-result-1",
                "route": "FREE",
                "publish_result": "PUBLISHED",
                "destination_id": 1001,
                "message_id": 501,
            }
        ],
        "route_results": [],
    }

    signal_engine._log_post_distribution(decision, persistent, execution, summary)
    events = _read_jsonl(root / "observability" / "engine_events.jsonl")
    post = [
        event
        for event in events
        if event["event_type"] == "signal_execution_result"
        and event["data"]["execution_phase"] == "POST_DISTRIBUTION"
    ]
    assert len(post) == 1
    assert post[0]["data"]["execution_outcome"] == "EMITTED"
    assert post[0]["data"]["destination_state"] == "PUBLISHED"
    assert post[0]["execution_attempt_id"] == "attempt-post-v3"
    assert post[0]["decision_id"] == "decision-post-v3"
    assert post[0]["decision_audit_id"] == "decision-audit-post-v3"
    assert post[0]["data"]["fsm_handoff"]["fsm_transition_id"] == "fsm-post-v3"
    assert post[0]["data"]["publication_evidence"]["published"][0]["event_id"] == "route-result-1"


def _personal(monkeypatch, router):
    monkeypatch.setenv("OWNER_SIGNAL_DELIVERY_ENABLED", "true")
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "123456789")
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    return router.owner_signal_delivery


@pytest.mark.parametrize("stage", ["PRE", "CONFIRM", "OPEN_NOW"])
def test_finnhub_personal_stages_only_reach_owner_never_channels(tmp_path, monkeypatch, stage):
    root, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    calls = []
    monkeypatch.setenv("ADMIN_GROUP_ID", "-100111111")
    monkeypatch.setenv("SIGNALS_LIVE_TOPIC_ID", "7")
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **kw: (
        calls.append(kw) or {"ok": True, "result": {"message_id": 42, "date": 1720000100}}
    ))
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **_: pytest.fail("expected a photo"))
    candidate = _candidate(stage, "personal-lifecycle")
    if stage in {"CONFIRM", "OPEN_NOW"}:
        owner.record_acceptance(_candidate("PRE", "personal-lifecycle"), {"ok": True},
                                started_ts=time.time()-61, accepted_ts=time.time()-60, transport_seconds=0.1)
    if stage == "OPEN_NOW":
        owner.record_acceptance(_candidate("CONFIRM", "personal-lifecycle"), {"ok": True},
                                started_ts=time.time()-6, accepted_ts=time.time()-5, transport_seconds=0.1)
    summary = router.route(candidate, now_ts=1720000100)
    assert summary["published_count"] == 1
    assert len(summary["route_results"]) == 1
    assert summary["route_results"][0]["route"] == "OWNER_PRIVATE"
    assert calls[0]["chat_id"] == 123456789
    assert calls[0]["thread_id"] is None and calls[0]["reply_markup"] is None
    assert calls[0]["photo"].startswith(b"\x89PNG\r\n\x1a\n")
    assert "OBSERVARE PRIVATĂ" in calls[0]["caption"]
    label = router.owner_signal_number.lookup_lifecycle(candidate["signal_id"])
    assert label and label.endswith(" · nr. 0")
    assert "#0" in calls[0]["caption"] and candidate["signal_id"] not in calls[0]["caption"]
    assert legacy.load_state()["open_signals_today"]["FREE"] == 0
    assert owner.audit_evidence(987654321) == {"status": "PERSONAL_DELIVERY_NOT_ENABLED_FOR_OWNER"}
    assert (root / "state" / "owner_signal_timing.json").is_file()
    repeated = router.route(candidate, now_ts=1720000102)
    assert repeated["published_count"] == 0 and len(calls) == 1


@pytest.mark.parametrize("setting,value", [
    ("OWNER_SIGNAL_DELIVERY_ENABLED", "false"), ("OWNER_TELEGRAM_ID", "-100123"),
    ("OWNER_TELEGRAM_ID", "0"), ("OWNER_TELEGRAM_ID", "someone"),
    ("OWNER_TELEGRAM_ID", "1" * 5000), ("SHADOW_MODE", "false"),
    ("ENABLE_BROKER_EXECUTION", "true"),
])
def test_personal_delivery_fails_closed_for_invalid_scope(tmp_path, monkeypatch, setting, value):
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    _personal(monkeypatch, router)
    monkeypatch.setenv(setting, value)
    calls = []
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **kw: calls.append(kw))
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **kw: calls.append(kw))
    summary = router.route(_candidate("PRE"), now_ts=1720000100)
    assert summary["blocked"] and summary["block_reason"] == "FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED"
    assert not calls


def test_personal_route_preserves_open_now_expiry_gate(tmp_path, monkeypatch):
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    _personal(monkeypatch, router)
    calls = []
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **kw: calls.append(kw))
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **kw: calls.append(kw))
    candidate = _candidate("PRE")
    candidate["stage"] = "OPEN_NOW"
    summary = router.route(candidate, now_ts=1720000100)
    assert summary["block_reason"] == "EXECUTION_TIME_UNAVAILABLE" and not calls
    assert router.owner_signal_number.lookup(candidate["signal_id"]) is None


def test_owner_open_with_unavailable_number_ledger_never_sends(tmp_path, monkeypatch):
    root, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    signal_id = "private-number-unavailable"
    for stage, age in (("PRE", 60), ("CONFIRM", 5)):
        owner.record_acceptance(_candidate(stage, signal_id), {"ok": True},
                                started_ts=time.time()-age-1, accepted_ts=time.time()-age, transport_seconds=.1)
    (root / "state" / "owner_signal_numbers.json").write_text("{corrupt}")
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **_: pytest.fail("OPEN was sent"))
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **_: pytest.fail("OPEN was sent"))

    summary = router.route(_candidate("OPEN_NOW", signal_id), now_ts=1720000100)

    assert summary["published_count"] == 0 and summary["failed_count"] == 1


def test_owner_timing_uses_first_successful_stage_and_preserves_missing_gaps(tmp_path, monkeypatch):
    _, _, _, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    response = {"ok": True, "result": {"date": 1720000100}}
    candidate = _candidate("PRE", "real-shared-identity")
    first = owner.record_acceptance(candidate, response, started_ts=1720000100,
                                    accepted_ts=1720000100.2, transport_seconds=0.2)
    assert first["pre_to_open_seconds"] is None
    owner.record_acceptance(candidate, response, started_ts=1720000110,
                            accepted_ts=1720000110.4, transport_seconds=0.4)
    candidate["stage"] = "CONFIRM"
    confirm = owner.record_acceptance(candidate, response, started_ts=1720000130,
                                      accepted_ts=1720000130.2, transport_seconds=0.2)
    assert confirm["pre_to_confirm_seconds"] == 30
    assert confirm["confirm_to_open_seconds"] is None
    candidate["stage"] = "OPEN_NOW"
    opened = owner.record_acceptance(candidate, response, started_ts=1720000150,
                                     accepted_ts=1720000150.5, transport_seconds=0.5)
    assert opened["pre_to_open_seconds"] == 50.3
    assert opened["confirm_to_open_seconds"] == 20.3
    assert opened["phone_receipt_proven"] is False
    with pytest.raises(ValueError):
        owner.record_acceptance(candidate, {"ok": False}, started_ts=1,
                                accepted_ts=2, transport_seconds=1)


def test_supplemental_timing_failure_never_resends_published_stage(tmp_path, monkeypatch):
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    monkeypatch.setattr(owner, "record_acceptance", lambda *a, **kw: (_ for _ in ()).throw(ValueError()))
    calls = []
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **kw: (
        calls.append(kw) or {"ok": True, "result": {"message_id": 42}}
    ))
    first = router.route(_candidate("PRE"), now_ts=1720000100)
    second = router.route(_candidate("PRE"), now_ts=1720000102)
    assert first["published_count"] == 1 and first["failed_count"] == 0
    assert second["published_count"] == 0 and len(calls) == 1
    assert first["telemetry_errors"] == [{"route": "OWNER_PRIVATE", "error": "OWNER_TIMING_UNAVAILABLE"}]


def test_activation_receipt_is_explicitly_not_a_signal(tmp_path, monkeypatch, capsys):
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    calls = []
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **kw: (
        calls.append(kw) or {"ok": True, "result": {"message_id": 42}}
    ))
    owner.send_activation_receipt()
    assert calls[0]["chat_id"] == 123456789 and "not a signal" in calls[0]["text"]
    assert '"accepted": true' in capsys.readouterr().out


def test_personal_delivery_preserves_tier_limits_states_and_reset(tmp_path, monkeypatch):
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    _personal(monkeypatch, router)
    state = legacy._default_state()
    state["tier_state"]["FREE"] = "SILENT"
    state["open_signals_today"]["FREE"] = 6
    state["last_reset_london_date"] = "2024-01-01"
    legacy.save_state(state)
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **kw: {"ok": True, "result": {"message_id": 3}})
    router.route(_candidate("PRE"), now_ts=1720000100)
    after = legacy.load_state()
    assert after["tier_state"] == state["tier_state"]
    assert after["open_signals_today"] == state["open_signals_today"]
    assert after["last_reset_london_date"] == "2024-01-01"


def test_photo_lifecycle_reuses_one_number_and_preserves_real_stage_timing(tmp_path, monkeypatch):
    root, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    _personal(monkeypatch, router)
    clock = [1_794_259_800.0]
    monkeypatch.setattr(router.time, "time", lambda: clock[0])
    calls = []
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **kw: (
        calls.append(kw) or {"ok": True, "result": {"message_id": len(calls)}}
    ))
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **_: pytest.fail("expected photo"))
    labels = []
    for stage, offset in (("PRE", 0), ("CONFIRM", 3), ("OPEN_NOW", 35)):
        clock[0] = 1_794_259_800.0 + offset
        candidate = _candidate(stage, "one-daily-trade", exact_expiry=4.77)
        candidate.update(created_ts=int(clock[0]), direction="SELL")
        candidate["payload"]["decision_policy"] = "PHYSICAL_ONLY_V3"
        candidate.pop("score_total")
        summary = router.route(candidate, now_ts=int(clock[0]))
        assert summary["published_count"] == 1
        labels.append(router.owner_signal_number.lookup_lifecycle(candidate["signal_id"]))

    assert len(set(labels)) == 1 and labels[0].endswith("nr. 0")
    assert all("#0" in call["caption"] and "one-daily-trade" not in call["caption"] for call in calls)
    assert all(call["photo"].startswith(b"\x89PNG") for call in calls)
    assert "4.77" in calls[-1]["caption"]
    timing = json.loads((root / "state" / "owner_signal_timing.json").read_text())
    stages = next(iter(timing["opportunities"].values()))
    assert {record["format"] for record in stages.values()} == {"PHOTO"}
    assert {record["signal_label"] for record in stages.values()} == {labels[0]}
    assert stages["OPEN_NOW"]["api_accepted_ts"] - stages["PRE"]["api_accepted_ts"] == 35


def test_card_render_failure_uses_short_same_number_text_before_transport(tmp_path, monkeypatch):
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    _personal(monkeypatch, router)
    from core import signal_card

    monkeypatch.setattr(signal_card, "render_signal_card", lambda *a, **kw: (_ for _ in ()).throw(OSError()))
    calls = []
    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", lambda **_: pytest.fail("render failed"))
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **kw: (
        calls.append(kw) or {"ok": True, "result": {"message_id": 42}}
    ))
    summary = router.route(_candidate("PRE", "private-long-id"), now_ts=1720000100)
    assert summary["published_count"] == 1 and len(calls) == 1
    assert "#0" in calls[0]["text"] and "private-long-id" not in calls[0]["text"]
    assert "Imagine indisponibilă" in calls[0]["text"]


def test_photo_transport_exception_has_no_immediate_text_fallback(tmp_path, monkeypatch):
    _, _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    _personal(monkeypatch, router)
    calls = []

    def timeout(**kwargs):
        calls.append(kwargs)
        raise TimeoutError("photo acceptance unknown")

    monkeypatch.setattr(legacy.telegram_publisher, "send_photo", timeout)
    monkeypatch.setattr(legacy.telegram_publisher, "send_message", lambda **_: pytest.fail("duplicate transport"))
    summary = router.route(_candidate("PRE"), now_ts=1720000100)
    assert summary["published_count"] == 0 and summary["failed_count"] == 1
    assert len(calls) == 1


def test_owner_audit_exports_allowlisted_real_candles_only(tmp_path, monkeypatch):
    root, _, _, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    params = json.loads((SEND_ROOT / "config" / "algo_params.json").read_text())
    (root / "config" / "algo_params.json").write_text(json.dumps(params))
    store = root / "market_data" / "finnhub_eurusd.json"
    store.parent.mkdir()
    monkeypatch.setenv("FINNHUB_CANDLE_STORE", str(store))
    candles = {}
    for frame, seconds in (("M1", 60), ("M5", 300)):
        candles[frame] = [{"ts": 1793872800-i*seconds, "open": 1.1, "high": 1.11,
                           "low": 1.09, "close": 1.1, "complete": True,
                           "provider": "FINNHUB", "symbol": "EUR/USD", "timeframe": frame,
                           "arbitrary_secret": "must-not-export"} for i in range(25)]
    store.write_text(json.dumps({"provider": "FINNHUB", "candles": candles, "api_key": "never-export"}))
    evidence = owner.audit_evidence(123456789)
    assert evidence["status"] == "PERSONAL_RESEARCH_SNAPSHOT"
    assert evidence["params"] == params
    assert len(evidence["candles"]["M1"]) == 25
    assert evidence["model_time_research_evidence"]["status"] == "VALIDATED_PRIVATE_RESEARCH"
    assert "secret" not in json.dumps(evidence) and "never-export" not in json.dumps(evidence)
    assert "candles" not in owner.audit_evidence(987654321)
    store.write_text(json.dumps({"provider": "OTHER", "candles": candles}))
    assert owner.audit_evidence(123456789)["status"] == "SOURCE_UNAVAILABLE_OR_INVALID"


def test_private_research_export_is_not_invoked_for_another_user(tmp_path, monkeypatch):
    _, _, _, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    from intelligence import shadow_model_time_research
    monkeypatch.setattr(shadow_model_time_research, "private_calibration_evidence",
                        lambda: pytest.fail("non-owner invoked private research export"))
    assert owner.audit_evidence(987654321) == {"status": "PERSONAL_DELIVERY_NOT_ENABLED_FOR_OWNER"}


def test_owner_stage_order_and_30_second_pre_advance(tmp_path, monkeypatch):
    _, _, _, router, _ = _setup(tmp_path, monkeypatch)
    owner = _personal(monkeypatch, router)
    now = 1720000100
    event = _candidate("OPEN_NOW", "timed-stage")
    assert owner.stage_block_reason(event, now_ts=now) == "OWNER_STAGE_TIMING_UNAVAILABLE"
    owner.record_acceptance(_candidate("PRE", "timed-stage"), {"ok": True},
                            started_ts=now-1, accepted_ts=now, transport_seconds=0.1)
    assert owner.stage_block_reason(event, now_ts=now+20) == "OWNER_CONFIRM_RECEIPT_REQUIRED"
    owner.record_acceptance(_candidate("CONFIRM", "timed-stage"), {"ok": True},
                            started_ts=now+1, accepted_ts=now+2, transport_seconds=0.1)
    assert owner.stage_block_reason(event, now_ts=now+29.999) == "OWNER_PRE_LEAD_TIME_NOT_MET"
    assert owner.stage_block_reason(event, now_ts=now+30) is None
    assert owner.stage_block_reason(event, now_ts=now-1) == "OWNER_STAGE_TIME_ORDER_INVALID"
    assert owner.stage_block_reason(_candidate("PRE", "another"), now_ts=now) is None
