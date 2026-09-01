from __future__ import annotations

import importlib
import json
import sys
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
    assert post[0]["data"]["publication_evidence"]["published"][0]["event_id"] == "route-result-1"
