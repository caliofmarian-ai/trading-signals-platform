from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest


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


def test_continuous_monitor_survives_reimport_and_preserves_real_zeroes(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    _observe(module, 1000)
    module = importlib.reload(module)
    _observe(module, 1050)
    _observe(module, 8200)
    report = module.summary(now_ts=8200)
    assert report["started_ts"] == 1000 and report["deadline_ts"] is None
    assert report["status"] == "OBSERVING" and report["evaluations"] == 3
    assert report["operating_mode"] == "CONTINUOUS" and report["automatic_stop_at"] is None
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
    assert report["private_published_stages"] == {"PRE": 1, "OPEN_NOW": 1}
    assert report["api_request_p50_seconds"] == .25


def test_parameter_drift_pauses_without_renewing_or_auto_promoting(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    _observe(module, 1000)
    _observe(module, 1001, params="b"*64)
    _observe(module, 1002)
    report = module.summary(now_ts=1003)
    assert report["status"] == "PAUSED_BASELINE_CHANGED" and report["evaluations"] == 1
    assert report["deadline_ts"] is None
    assert report["parameters_changed"] is False and report["broker_executed"] is False


def test_progress_notifications_continue_beyond_two_hours_without_duplicate_slots(canonical_runtime_root, monkeypatch):
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
    ongoing = module.report_if_due(now_ts=8200)
    assert ongoing["status"] == "OBSERVING"
    assert module.report_if_due(now_ts=9000) is None
    assert module.report_if_due(now_ts=9100)["status"] == "OBSERVING"
    assert len(sent) == 4 and all(r["chat_id"] == 123456789 for r in sent)
    assert all("Ends:" not in r["text"] and "/120" not in r["text"] for r in sent)
    assert "remains unproven" in sent[-1]["text"]


def test_continuous_monitor_ignores_session_identity_and_requires_owner_opt_in(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    monkeypatch.setenv("OWNER_TIMING_SESSION_ID", "../../escape")
    _observe(module, 1000)
    report = module.summary(now_ts=1001)
    assert report["evaluations"] == 1
    stable_path = module._path()
    monkeypatch.delenv("OWNER_TIMING_SESSION_ID")
    _observe(module, 9000)
    assert module._path() == stable_path and module.summary(now_ts=9001)["evaluations"] == 2
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "true")
    _observe(module, 1000)
    assert module.summary(now_ts=1001) is None
    assert not list((canonical_runtime_root / "analytics").glob("owner_timing_sessions/*"))


@pytest.mark.parametrize("samples,p50,p95", [
    ([], None, None),
    ([.07], .07, .07),
    ([.082255, .078538], .078538, .082255),
    ([.078538, .091372, .06053, .082255, .054034], .078538, .091372),
    ([value / 100 for value in range(1, 21)], .10, .19),
])
def test_observed_transport_percentiles_use_consistent_nearest_rank(
    canonical_runtime_root, monkeypatch, samples, p50, p95,
):
    module = _prepare(monkeypatch)
    _observe(module, 1000)
    for index, duration in enumerate(samples):
        module.observe_receipt({"stage": "PRE", "api_request_seconds": duration}, now_ts=1001+index)
    report = module.summary(now_ts=1100)
    assert report["api_timing_percentile_method"] == "NEAREST_RANK"
    assert report["api_timing_sample_scope"] == "LAST_512_SUCCESSFUL_PRIVATE_DELIVERIES"
    assert report["api_timing_sample_count"] == len(samples)
    assert report["api_request_p50_seconds"] == p50
    assert report["api_request_p95_seconds"] == p95
    if samples:
        assert report["api_request_p95_seconds"] >= report["api_request_p50_seconds"]


@pytest.mark.parametrize("invalid", [True, float("nan"), float("inf"), -.01, "0.1"])
def test_invalid_transport_evidence_never_produces_a_latency_claim(monkeypatch, invalid):
    module = _prepare(monkeypatch)
    state = module._new(1000, "a"*64)
    state["api_request_seconds"] = [invalid]
    with pytest.raises(ValueError, match="INVALID_TIMING_SAMPLES"):
        module._summary(state, 1001)


def test_progress_names_complete_margin_and_fragile_wins_separately(canonical_runtime_root, monkeypatch):
    module = _prepare(monkeypatch)
    from core import physical_params, telegram_publisher
    from intelligence import physical_expiry_calibration

    sent = []
    monkeypatch.setattr(physical_params, "physical_runtime_enabled", lambda: True)
    monkeypatch.setattr(telegram_publisher, "send_message", lambda **kw: sent.append(kw) or {"ok": True})
    monkeypatch.setattr(physical_expiry_calibration, "summary", lambda **kw: {
        "baseline_model_observations": {"wins": 3, "losses": 1, "unknown": 2,
            "buffer_met": 1, "buffer_not_met": 3, "buffer_unavailable": 2,
            "win_buffer_not_met": 2},
    })
    _observe(module, 1000)
    module.report_if_due(now_ts=1001)
    text = sent[0]["text"]
    assert "Marjă completă la expirare: DA 1, NU 3, indisponibilă 2" in text
    assert "WIN fragil (în buffer): 2" in text
    assert "Buffer: atins" not in text

