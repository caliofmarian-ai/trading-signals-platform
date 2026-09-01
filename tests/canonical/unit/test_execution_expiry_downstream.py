from __future__ import annotations

import json

import pytest

from core import distribution_router_v3, outcome_service, trade_temporal_telemetry


def _governed_event(*, stage: str = "OPEN_NOW", expiry: float = 2.01) -> dict:
    event = {
        "event_type": "SIGNAL_CANDIDATE",
        "stage": stage,
        "signal_id": "sig-exact-expiry",
        "symbol": "EUR/USD",
        "timeframe": "M1",
        "direction": "BUY",
        "score_total": 86.0,
        "buffer_mode": "MEDIUM",
        "buffer_distance": 0.0008,
        "buffer_price": 0.0008,
        "model_expiry": 2.01,
        "candle_ts": 1_720_000_000,
        "created_ts": 1_720_000_002,
        "entry_price": 1.11234,
        "payload": {"latest_price": 1.11234},
        "execution_time_available": stage in {"CONFIRM", "OPEN_NOW"},
        "confirm_expiry_min_minutes": 1.5 if stage in {"CONFIRM", "OPEN_NOW"} else None,
        "confirm_expiry_max_minutes": 3.0 if stage in {"CONFIRM", "OPEN_NOW"} else None,
        "open_now_expiry_minutes": expiry if stage == "OPEN_NOW" else None,
        "execution_calibration_source": "test-governed-calibration" if stage in {"CONFIRM", "OPEN_NOW"} else None,
    }
    event["expiry_minutes"] = expiry if stage == "OPEN_NOW" else None
    return event


def test_distribution_rejects_legacy_open_now_expiry_without_execution_truth() -> None:
    event = _governed_event()
    event.pop("execution_time_available")
    event.pop("open_now_expiry_minutes")
    event.pop("confirm_expiry_min_minutes")
    event.pop("confirm_expiry_max_minutes")
    event.pop("execution_calibration_source")

    with pytest.raises(ValueError, match="governed Execution Time"):
        distribution_router_v3._validate_open_now_execution_time(event, "OPEN_NOW")


def test_distribution_preserves_exact_fractional_expiry_and_formats_only_execution_truth() -> None:
    open_event = _governed_event(expiry=2.01)
    exact = distribution_router_v3._validate_open_now_execution_time(open_event, "OPEN_NOW")
    assert exact == pytest.approx(2.01)
    text = distribution_router_v3._render_signal_text(open_event, "ELITE")
    assert "Expiry: 2.01m" in text
    assert "3m" not in text

    pre_event = _governed_event(stage="PRE")
    pre_text = distribution_router_v3._render_signal_text(pre_event, "ELITE")
    assert "Expiry:" not in pre_text
    assert "None" not in pre_text

    confirm_event = _governed_event(stage="CONFIRM")
    confirm_text = distribution_router_v3._render_signal_text(confirm_event, "ELITE")
    assert "Execution window: 1.5-3m" in confirm_text
    assert "Expiry:" not in confirm_text


def test_distribution_rejects_conflicting_compatibility_alias() -> None:
    event = _governed_event(expiry=2.01)
    event["expiry_minutes"] = 3
    with pytest.raises(ValueError, match="conflicts"):
        distribution_router_v3._validate_open_now_execution_time(event, "OPEN_NOW")


def test_outcome_window_preserves_fractional_execution_minutes(tmp_path, monkeypatch) -> None:
    outcome_service.OPEN_REGISTRY_JSON = str(tmp_path / "open_now_registry.json")
    outcome_service.OUTCOMES_JSONL = str(tmp_path / "outcomes.jsonl")
    outcome_service.OUTCOMES_INDEX_JSON = str(tmp_path / "outcomes_index.json")
    monkeypatch.setattr(outcome_service.observability_logger, "log_event", lambda *a, **k: None)

    result = outcome_service.register_open_now(
        signal_id="sig-exact-expiry",
        elite_chat_id=1004,
        open_message_id=808,
        open_now_ts=1_720_000_002,
        expiry_minutes=2.01,
        symbol="EUR/USD",
        direction="BUY",
        timeframe="M1",
    )

    assert result["meta"]["expiry_minutes"] == pytest.approx(2.01)
    assert result["meta"]["expiry_ts"] == pytest.approx(1_720_000_122.6)
    saved = json.loads((tmp_path / "open_now_registry.json").read_text(encoding="utf-8"))
    assert saved["sig-exact-expiry"]["expiry_minutes"] == pytest.approx(2.01)
    assert saved["sig-exact-expiry"]["expiry_ts"] == pytest.approx(1_720_000_122.6)


def test_temporal_telemetry_preserves_governed_fractional_expiry(tmp_path, monkeypatch) -> None:
    trade_temporal_telemetry.OPEN_TRADES_REGISTRY_JSON = str(tmp_path / "open_trades_registry.json")
    monkeypatch.setattr(trade_temporal_telemetry.observability_logger, "log_event", lambda *a, **k: None)
    event = _governed_event(expiry=2.01)

    result = trade_temporal_telemetry.register_open_now_trade(event, now_ts=1_720_000_002)
    record = result["record"]

    assert record["expiry_minutes"] == pytest.approx(2.01)
    assert record["expiry_ts"] == pytest.approx(1_720_000_122.6)
    assert record["mid_expiry_ts"] == pytest.approx(1_720_000_062.3)
    assert record["entry_price"] == pytest.approx(1.11234)
    assert record["execution_calibration_source"] == "test-governed-calibration"
