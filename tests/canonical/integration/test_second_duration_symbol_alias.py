"""Exercise the actual EURUSD runtime spelling through the normalized study."""
from dataclasses import replace

from tests.canonical.integration.test_second_duration_pipeline import (
    BASE, _advance, _capture, _step, seconds_pipeline,
)


def test_eurusd_alias_keeps_same_seconds_plan_through_real_pipeline(seconds_pipeline, monkeypatch):
    ctx = seconds_pipeline
    from tests.canonical.unit import test_confirmed_execution_duration as fixture
    original = fixture._decision

    def runtime_alias(*args, **kwargs):
        value = original(*args, **kwargs)
        return replace(value, setup=replace(value.setup, symbol="EURUSD"))

    monkeypatch.setattr(fixture, "_decision", runtime_alias)
    _step(ctx, "PRE", 0)
    _step(ctx, "CONFIRM", 3)
    event = ctx["events"][-1]
    plan = ctx["state"]["per_symbol"]["EURUSD"][ctx["plans"].PLAN_FIELD]
    assert event["symbol"] == plan["symbol"] == "EURUSD"
    assert event["study_duration_seconds"] == 516
    captured = _capture(ctx, needed=8.5)
    assert captured["study_observation"]["duration_plan"] == plan
    saved = _advance(ctx, BASE + 36, 1.1)
    projected = ctx["delivery"]._entry_event(saved)
    assert projected["symbol"] == "EUR/USD"
    assert projected["study_duration_seconds"] == event["study_duration_seconds"]
    assert projected["study_plan_id"] == event["study_plan_id"]
    assert len(ctx["photos"]) == 3
    expiry = BASE + 36 + 516
    saved = _advance(ctx, expiry, 1.1025)
    assert saved["study_observation"]["outcome"] == "WIN"
    assert saved["study_observation"]["duration_plan"] == plan
    assert len(ctx["photos"]) == 4
    assert all("#0" in call["caption"] or "nr. 0" in call["caption"] for call in ctx["photos"])
    assert "8 MIN 36 S" in ctx["photos"][-1]["caption"]
    report = ctx["study"].summary(now_ts=expiry)
    assert report["published_study_results_by_duration_policy"][ctx["plans"].POLICY]["wins"] == 1
    assert not report["execution_calibration_proven"] and not report["broker_executed"]
