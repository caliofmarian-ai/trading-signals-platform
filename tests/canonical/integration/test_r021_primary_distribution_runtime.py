from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest


SEND_ROOT = Path(__file__).resolve().parents[3] / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge() -> None:
    for name in list(sys.modules):
        if (
            name == "core"
            or name.startswith("core.")
            or name == "runtime.engine_loop"
            or name == "runtime.distribution_scheduler"
            or name == "state_store"
            or name.startswith("state_store.")
        ):
            sys.modules.pop(name, None)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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
    monkeypatch.setenv(
        "ENGINE_EVENTS_LOG", str(root / "observability" / "engine_events.jsonl")
    )
    monkeypatch.setenv(
        "FSM_EVENTS_LOG", str(root / "observability" / "fsm_events.jsonl")
    )
    monkeypatch.setenv(
        "DIST_EVENTS_LOG", str(root / "observability" / "distribution_events.jsonl")
    )
    monkeypatch.setenv(
        "ADMIN_PROOFS_LOG", str(root / "observability" / "admin_proofs.jsonl")
    )
    monkeypatch.setenv(
        "ERROR_EVENTS_LOG", str(root / "observability" / "error_events.jsonl")
    )
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
    router = importlib.import_module("core.distribution_router_primary_v3")

    legacy.DIST_STATE_PATH = str(root / "state" / "dist_state.json")
    legacy.CHANNEL_CONFIG_PATHS = [str(config_path)]
    return root, obs, legacy, router


def _candidate() -> dict[str, Any]:
    return {
        "event_type": "SIGNAL_CANDIDATE",
        "schema_version": "3.0.0",
        "stage": "PRE",
        "signal_id": "sig-r021-primary",
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


def test_primary_runtime_route_writes_no_legacy_distribution_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, obs, legacy, router = _setup(tmp_path, monkeypatch)

    monkeypatch.setattr(
        legacy.telegram_publisher,
        "send_message",
        lambda **kwargs: {"ok": True, "result": {"message_id": 501}},
    )

    summary = router.route(_candidate(), now_ts=1_720_000_100)

    assert summary["published_count"] == 1
    events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    event_types = [event["event_type"] for event in events]
    assert event_types.count("route_publish_attempt") == 4
    assert event_types.count("route_publish_result") == 4
    assert event_types.count("signal_stage_visible") == 1
    assert "tier_publish" not in event_types
    assert "tier_reset" not in event_types
    assert all(obs.validate_event(event) == event for event in events)


def test_primary_reset_writes_route_reset_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _, legacy, router = _setup(tmp_path, monkeypatch)

    state = legacy._default_state()
    state["open_signals_today"]["FREE"] = 3
    state["last_reset_london_date"] = "2024-06-30"
    legacy.save_state(state)

    # The test config resets at 23:59 Europe/London. Use a deterministic local
    # timestamp after that boundary on the following day.
    ts = int(
        datetime(2024, 7, 1, 23, 59, 30, tzinfo=ZoneInfo("Europe/London")).timestamp()
    )
    changed = router.reset_daily_counters(now_ts=ts)

    assert changed is True
    events = _read_jsonl(root / "observability" / "distribution_events.jsonl")
    event_types = [event["event_type"] for event in events]
    assert event_types.count("route_reset") == 4
    assert "tier_reset" not in event_types
    final_state = legacy.load_state()
    assert final_state["open_signals_today"]["FREE"] == 0
    assert final_state["last_reset_london_date"] == "2024-07-01"


def test_live_engine_and_scheduler_bind_primary_v3_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch)

    engine_loop = importlib.import_module("runtime.engine_loop")
    scheduler = importlib.import_module("runtime.distribution_scheduler")

    assert engine_loop.signal_engine.distribution_router.__name__ == (
        "core.distribution_router_primary_v3"
    )
    assert scheduler.distribution_router.__name__ == (
        "core.distribution_router_primary_v3"
    )
