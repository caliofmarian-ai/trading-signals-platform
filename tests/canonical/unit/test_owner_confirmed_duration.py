from __future__ import annotations

from types import SimpleNamespace

import pytest


def _owner(monkeypatch):
    monkeypatch.setenv("OWNER_SIGNAL_DELIVERY_ENABLED", "true")
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "12345")
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    from core import owner_signal_delivery
    return owner_signal_delivery


def _event(stage, *, study=False, exact=False):
    value = {"stage": stage, "signal_id": "sig-v3-timing", "symbol": "EUR/USD",
             "direction": "BUY", "created_ts": 1800000003,
             "execution_time_available": False,
             "payload": {"decision_policy": "PHYSICAL_ONLY_V3"}}
    if study:
        value.update(study_duration_minutes=3.45, study_confirmed_ts=1800000003,
                     study_duration_source="CONFIRM_MODEL_TIME")
    if exact:
        value.update(execution_time_available=True, confirm_expiry_minutes=3.45,
                     confirm_expiry_min_minutes=3.0, confirm_expiry_max_minutes=4.0,
                     execution_calibration_source="approved-source")
        if stage == "OPEN_NOW":
            value["open_now_expiry_minutes"] = 3.45
    return value


def _receipt(owner, event, stamp):
    owner.record_acceptance(event, {"ok": True, "result": {"message_id": 1}},
                            started_ts=stamp, accepted_ts=stamp,
                            transport_seconds=0, delivery_format="PHOTO")


def test_projection_uses_persisted_confirm_horizon_not_later_model(canonical_runtime_root, monkeypatch):
    owner = _owner(monkeypatch)
    event = _event("CONFIRM")
    event["model_expiry"] = 9.0
    row = {"physical_signal_id": event["signal_id"], "physical_direction": "BUY",
           "physical_confirm_model_seconds": 207.0, "physical_confirm_ts": 1800000003,
           "physical_confirm_execution_status": "UNAVAILABLE"}
    handoff = SimpleNamespace(next_state={"per_symbol": {"EUR/USD": row}})
    projected = owner.project_confirmed_study(event, handoff)
    assert projected["study_duration_minutes"] == 3.45
    assert projected["study_confirmed_ts"] == 1800000003
    assert projected["study_duration_source"] == "CONFIRM_MODEL_TIME"
    assert "study_duration_minutes" not in event
    row["physical_confirm_execution_status"] = "FROZEN"
    assert owner.project_confirmed_study(event, handoff) == event
    row["physical_confirm_execution_status"] = "UNAVAILABLE"
    row["physical_signal_id"] = "another-opportunity"
    assert owner.project_confirmed_study(event, handoff) == event


def test_physical_confirm_requires_exact_disclosed_duration(canonical_runtime_root, monkeypatch):
    owner = _owner(monkeypatch)
    _receipt(owner, _event("PRE"), 1800000000)
    assert owner.stage_block_reason(_event("CONFIRM"), now_ts=1800000003) == "OWNER_CONFIRM_DURATION_REQUIRED"
    assert owner.stage_block_reason(_event("CONFIRM", study=True), now_ts=1800000003) is None
    assert owner.stage_block_reason(_event("CONFIRM", exact=True), now_ts=1800000003) is None
    invalid = _event("CONFIRM", exact=True)
    invalid["confirm_expiry_minutes"] = 4.5
    assert owner.stage_block_reason(invalid, now_ts=1800000003) == "OWNER_CONFIRM_DURATION_REQUIRED"


@pytest.mark.parametrize("study", [True, False])
def test_open_reuses_delivered_duration_and_rejects_silent_change(canonical_runtime_root, monkeypatch, study):
    owner = _owner(monkeypatch)
    _receipt(owner, _event("PRE"), 1800000000)
    _receipt(owner, _event("CONFIRM", study=study, exact=not study), 1800000003)
    opened = _event("OPEN_NOW", study=study, exact=not study)
    assert owner.stage_block_reason(opened, now_ts=1800000035) is None
    opened["study_duration_minutes" if study else "open_now_expiry_minutes"] = 3.5
    assert owner.stage_block_reason(opened, now_ts=1800000035) == "OWNER_CONFIRMED_DURATION_CHANGED"
    opened = _event("OPEN_NOW", study=study, exact=not study)
    opened["study_confirmed_ts" if study else "execution_calibration_source"] = "changed"
    expected = "OWNER_CONFIRMED_STUDY_DURATION_REQUIRED" if study else "OWNER_CONFIRMED_EXECUTION_DURATION_REQUIRED"
    assert owner.stage_block_reason(opened, now_ts=1800000035) == expected


def test_legacy_confirm_receipt_cannot_claim_new_exact_study(canonical_runtime_root, monkeypatch):
    owner = _owner(monkeypatch)
    _receipt(owner, _event("PRE"), 1800000000)
    _receipt(owner, _event("CONFIRM"), 1800000003)
    assert owner.stage_block_reason(_event("OPEN_NOW", study=True), now_ts=1800000035) == "OWNER_CONFIRMED_STUDY_DURATION_REQUIRED"


def test_calibrated_confirm_cannot_be_relabelled_as_study(canonical_runtime_root, monkeypatch):
    owner = _owner(monkeypatch)
    _receipt(owner, _event("PRE"), 1800000000)
    _receipt(owner, _event("CONFIRM", exact=True), 1800000003)
    assert owner.stage_block_reason(_event("OPEN_NOW", study=True), now_ts=1800000035) == "OWNER_CONFIRMED_STUDY_DURATION_REQUIRED"
