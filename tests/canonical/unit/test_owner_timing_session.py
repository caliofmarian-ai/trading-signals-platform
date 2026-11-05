from __future__ import annotations

import importlib
from types import SimpleNamespace


def _prepare(monkeypatch):
    monkeypatch.setenv("OWNER_SIGNAL_DELIVERY_ENABLED", "true")
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "123456789")
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    monkeypatch.setenv("OWNER_TIMING_SESSION_ID", "owner-20261105-two-hours")
    return importlib.import_module("intelligence.owner_timing_session")


def _observe(module, now, *, kind="REJECT", stage=None, params="a"*64):
    module.observe_evaluation(
        SimpleNamespace(kind=kind, reject=SimpleNamespace(hard_blockers=("STRUCTURE_NOT_VALID",))),
        SimpleNamespace(stage_handoff_ready=stage is not None, accepted_stage=stage),
        SimpleNamespace(available=False), now_ts=now, parameter_sha256=params,
    )


def test_two_hour_deadline_survives_reimport_and_preserves_real_zeroes(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    _observe(module, 1000)
    module = importlib.reload(module)
    _observe(module, 1050)
    _observe(module, 8200)
    report = module.summary(now_ts=8200)
    assert report["started_ts"] == 1000 and report["deadline_ts"] == 8200
    assert report["status"] == "COMPLETE" and report["evaluations"] == 2
    assert report["private_published_stages"] == {}
    assert report["api_request_p50_seconds"] is None
    assert report["execution_calibration_proven"] is False


def test_internal_stage_acceptance_is_separate_from_actual_delivery(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    _observe(module, 1000, kind="OPEN_NOW", stage="OPEN_NOW")
    report = module.summary(now_ts=1001)
    assert report["fsm_accepted_stage_evaluations"] == {"OPEN_NOW": 1}
    assert report["private_published_stages"] == {}
    module.observe_receipt({"stage": "PRE", "api_request_seconds": .25}, now_ts=1002)
    module.observe_receipt({"stage": "OPEN_NOW", "api_request_seconds": .5}, now_ts=8200)
    report = module.summary(now_ts=8200)
    assert report["private_published_stages"] == {"PRE": 1}
    assert report["api_request_p50_seconds"] == .25


def test_parameter_drift_pauses_without_renewing_or_auto_promoting(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    _observe(module, 1000)
    _observe(module, 1001, params="b"*64)
    _observe(module, 1002)
    report = module.summary(now_ts=1003)
    assert report["status"] == "PAUSED_BASELINE_CHANGED" and report["evaluations"] == 1
    assert report["deadline_ts"] == 8200
    assert report["parameters_changed"] is False and report["broker_executed"] is False


def test_progress_and_final_notifications_have_no_duplicate_slots(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    publisher = importlib.import_module("core.telegram_publisher")
    sent = []
    monkeypatch.setattr(publisher, "send_message", lambda **kw: sent.append(kw) or {"ok": True})
    _observe(module, 1000)
    assert module.report_if_due(now_ts=1001)["notification_api_accepted"] is True
    assert module.report_if_due(now_ts=1899) is None
    first = module.report_if_due(now_ts=1900)
    assert first["notification_api_accepted"] is True
    assert module.report_if_due(now_ts=1901) is None
    final = module.report_if_due(now_ts=8200)
    assert final["status"] == "COMPLETE"
    assert module.report_if_due(now_ts=9000) is None
    assert len(sent) == 3 and all(r["chat_id"] == 123456789 for r in sent)
    assert "remains unproven" in sent[-1]["text"]


def test_session_opt_in_and_safe_identity_are_required(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    monkeypatch.setenv("OWNER_TIMING_SESSION_ID", "../../escape")
    _observe(module, 1000)
    assert module.summary(now_ts=1001) is None
    monkeypatch.setenv("OWNER_TIMING_SESSION_ID", "owner-20261105-two-hours")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "true")
    _observe(module, 1000)
    assert module.summary(now_ts=1001) is None
    assert not list((canonical_runtime_root / "analytics").glob("owner_timing_sessions/*"))
