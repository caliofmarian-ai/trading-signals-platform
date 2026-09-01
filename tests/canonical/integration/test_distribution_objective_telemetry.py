from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest


SEND_ROOT = Path(__file__).resolve().parents[3] / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge() -> None:
    for name in list(sys.modules):
        if name == "core" or name.startswith("core.") or name == "runtime" or name.startswith("runtime."):
            sys.modules.pop(name, None)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "runtime"
    config = root / "config"
    config.mkdir(parents=True)
    config_path = config / "channel_config.json"
    config_path.write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "FREE_CHANNEL_ID": 1001,
            "BASIC_CHANNEL_ID": None,
            "PRO_CHANNEL_ID": None,
            "ELITE_CHANNEL_ID": None,
            "ADMIN_GROUP_ID": None,
            "SIGNALS_LIVE_TOPIC_ID": None,
            "FREE_LIMIT": 6,
            "TZ": "Europe/London",
            "RESET_TIME": "23:59",
        }),
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

    _purge()
    importlib.invalidate_caches()
    legacy = importlib.import_module("core.distribution_router")
    router = importlib.import_module("core.distribution_router_v3")
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    legacy.DIST_STATE_PATH = str(root / "state" / "dist_state.json")
    legacy.CHANNEL_CONFIG_PATHS = [str(config_path)]
    return root, legacy, router, telemetry


def _candidate(signal_id: str) -> dict[str, Any]:
    return {
        "event_type": "SIGNAL_CANDIDATE",
        "schema_version": "3.0.0",
        "stage": "OPEN_NOW",
        "signal_id": signal_id,
        "symbol": "EUR/USD",
        "timeframe": "M1",
        "direction": "BUY",
        "score_total": 88.5,
        "buffer_mode": "MEDIUM",
        "buffer_distance": 0.0008,
        "buffer_price": 0.0008,
        "model_expiry": 5.0,
        "execution_time_available": True,
        "confirm_expiry_min_minutes": 4.0,
        "confirm_expiry_max_minutes": 6.0,
        "open_now_expiry_minutes": 4.5,
        "execution_calibration_source": "test-calibration-v1",
        "expiry_minutes": 4.5,
        "candle_ts": 1_720_000_000,
        "created_ts": 1_720_000_005,
        "entry_price": 1.11234,
        "payload": {
            "cycle_id": "cycle-distribution-telemetry",
            "strategy_version": "2.0.0",
            "canonical_specification": "ALGO_SPEC_v3.0.0",
            "trade_physics": {"TPS": 82.0},
        },
        "distribution_enabled": False,
    }


def test_failed_publication_cannot_create_market_truth_registration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, legacy, router, _ = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(
        legacy.telegram_publisher,
        "send_message",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("telegram unavailable")),
    )

    summary = router.route(_candidate("sig-telemetry-fail"), now_ts=1_720_000_100)

    assert summary["published_count"] == 0
    assert summary["failed_count"] == 1
    assert summary["telemetry_errors"] == []
    registry_path = root / "observability" / "open_trades_registry.json"
    assert not registry_path.exists()


def test_successful_visibility_registers_one_market_truth_chain_with_event_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, legacy, router, telemetry = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(
        legacy.telegram_publisher,
        "send_message",
        lambda **kwargs: {"ok": True, "result": {"message_id": 501}},
    )

    summary = router.route(_candidate("sig-telemetry-success"), now_ts=1_720_000_100)

    assert summary["published_count"] == 1
    assert summary["telemetry_errors"] == []
    record = telemetry.get_open_trade("sig-telemetry-success")
    assert record is not None
    assert record["truth_domain"] == "MARKET_TRUTH"
    assert record["market_provider"] == "TWELVE_DATA"
    assert record["entry_price"] == pytest.approx(1.11234)
    assert len(record["publication_evidence"]) == 1

    evidence = record["publication_evidence"][0]
    events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    route_results = {event["event_id"]: event for event in events if event["event_type"] == "route_publish_result"}
    visibility = {event["event_id"]: event for event in events if event["event_type"] == "signal_stage_visible"}
    assert evidence["route_result_event_id"] in route_results
    assert evidence["visibility_event_id"] in visibility
    assert route_results[evidence["route_result_event_id"]]["data"]["publish_result"] == "PUBLISHED"
    assert visibility[evidence["visibility_event_id"]]["data"]["visibility_result"] == "PUBLISHED"


def test_telemetry_persistence_failure_does_not_rewrite_successful_publication_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, legacy, router, _ = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(
        legacy.telegram_publisher,
        "send_message",
        lambda **kwargs: {"ok": True, "result": {"message_id": 777}},
    )
    monkeypatch.setattr(
        router.trade_temporal_telemetry,
        "register_open_now_trade",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("telemetry disk unavailable")),
    )

    summary = router.route(_candidate("sig-telemetry-storage-fail"), now_ts=1_720_000_100)

    assert summary["published_count"] == 1
    assert summary["failed_count"] == 0
    assert len(summary["publication_evidence"]) == 1
    assert len(summary["telemetry_errors"]) == 1
    assert "telemetry disk unavailable" in summary["telemetry_errors"][0]["error"]
