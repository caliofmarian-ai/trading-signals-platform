from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from intelligence import model_time_paper_trades as paper
from tests.canonical.unit.test_shadow_model_time_research import _opportunity, _sample


def _register(ledger, *, horizon=2.0, direction="BUY", signal_id="paper-one", now=1062):
    decision, handoff = _opportunity(direction=direction, signal_id=signal_id)
    decision = replace(decision, time=replace(decision.time, model_expiry=horizon))
    handoff = replace(handoff, decision_id=decision.decision_id, decision_audit_id=decision.decision_audit_id)
    assert paper.register(ledger, decision, handoff, now_ts=now)
    paper.validate(ledger)
    return decision, handoff


@pytest.mark.parametrize("direction,price,outcome", [
    ("BUY", 1.2, "WIN"), ("BUY", 1.0, "LOSS"), ("BUY", 1.1, "DRAW"),
    ("SELL", 1.2, "LOSS"), ("SELL", 1.0, "WIN"), ("SELL", 1.1, "DRAW"),
])
def test_paper_outcomes_need_only_canonical_model_time_and_prospective_ticks(direction, price, outcome):
    ledger = paper.new_ledger()
    decision, handoff = _register(ledger, direction=direction)
    assert not paper.register(ledger, decision, handoff, now_ts=1063)
    paper.advance(ledger, _sample(1063), now_ts=1063, active_provider="FINNHUB")
    paper.advance(ledger, _sample(1183, price), now_ts=1183, active_provider="FINNHUB")
    paper.validate(ledger)
    trade = ledger["trades"][decision.signal_id]
    assert trade["outcome"] == outcome
    final = copy.deepcopy(ledger)
    assert not paper.advance(ledger, _sample(1200, 2), now_ts=1200, active_provider="FINNHUB")
    assert ledger == final
    result = paper.summary(ledger)
    assert result["outcomes"][outcome] == 1
    assert result["execution_calibration_required"] is False
    assert result["broker_executed"] is False and result["actual_telegram_publications"] == 0
    assert "price" not in str(result) and decision.signal_id not in str(result)


def test_different_opportunities_keep_their_market_derived_durations_without_rounding():
    ledger = paper.new_ledger()
    _register(ledger, horizon=2.25, signal_id="short")
    _register(ledger, horizon=4.75, signal_id="long")
    paper.advance(ledger, _sample(1063), now_ts=1063, active_provider="FINNHUB")
    paper.advance(ledger, _sample(1198, 1.2), now_ts=1198, active_provider="FINNHUB")
    assert ledger["trades"]["short"]["outcome"] == "WIN"
    assert ledger["trades"]["long"]["state"] == "WAITING_EXPIRY"
    paper.advance(ledger, _sample(1348, 1.0), now_ts=1348, active_provider="FINNHUB")
    paper.validate(ledger)
    assert ledger["trades"]["long"]["outcome"] == "LOSS"
    assert paper.summary(ledger)["horizon_seconds_counts"] == {"135.0": 1, "285.0": 1}


@pytest.mark.parametrize("bad", [
    None, _sample(1061), _sample(1065), _sample(1063, provider="TWELVE_DATA"),
    _sample(1063, price=float("nan")), _sample(1063, source="HISTORICAL_CANDLE"),
])
def test_missing_past_future_cross_provider_and_synthetic_entry_are_unknown(bad):
    ledger = paper.new_ledger()
    _register(ledger)
    paper.advance(ledger, bad, now_ts=1063, active_provider="FINNHUB")
    assert ledger["trades"]["paper-one"]["state"] == "WAITING_ENTRY"
    paper.advance(ledger, None, now_ts=1073, active_provider="FINNHUB")
    paper.validate(ledger)
    assert ledger["trades"]["paper-one"]["outcome"] == "UNKNOWN"


@pytest.mark.parametrize("provider,stamp", [("FINNHUB", 1200), ("TWELVE_DATA", 1070)])
def test_missed_expiry_or_changed_provider_never_fabricates_result(provider, stamp):
    ledger = paper.new_ledger()
    _register(ledger)
    paper.advance(ledger, _sample(1063), now_ts=1063, active_provider="FINNHUB")
    paper.advance(ledger, _sample(stamp, 1.2), now_ts=stamp, active_provider=provider)
    paper.validate(ledger)
    assert ledger["trades"]["paper-one"]["outcome"] == "UNKNOWN"


@pytest.mark.parametrize("change", ["no_stage", "lineage", "blocker", "physics", "infeasible"])
def test_paper_registration_retains_canonical_hard_gates_and_fsm_lineage(change):
    ledger = paper.new_ledger()
    decision, handoff = _opportunity()
    if change == "no_stage":
        handoff = replace(handoff, stage_handoff_ready=False)
    elif change == "lineage":
        handoff = replace(handoff, decision_id="other-evaluation")
    elif change == "blocker":
        decision = replace(decision, reject=replace(decision.reject, reason="STRUCTURE_NOT_VALID",
                                                   hard_blockers=("STRUCTURE_NOT_VALID",)))
    elif change == "physics":
        decision = replace(decision, strategic_flags=replace(decision.strategic_flags, trade_physics_ready=False))
    else:
        decision = replace(decision, strategic_flags=replace(decision.strategic_flags, feasible_time=False))
    assert not paper.register(ledger, decision, handoff, now_ts=1062)
    assert not ledger["trades"]


def test_tampered_horizon_or_outcome_is_rejected_without_resetting_history():
    ledger = paper.new_ledger()
    _register(ledger)
    paper.advance(ledger, _sample(1063), now_ts=1063, active_provider="FINNHUB")
    paper.advance(ledger, _sample(1183, 1.2), now_ts=1183, active_provider="FINNHUB")
    for field, value in (("horizon_seconds", 121), ("outcome", "LOSS"), ("expiry_ts", 1184)):
        dirty = copy.deepcopy(ledger)
        dirty["trades"]["paper-one"][field] = value
        with pytest.raises(ValueError):
            paper.validate(dirty)


def test_capacity_is_bounded_and_existing_evidence_remains_unchanged(monkeypatch):
    ledger = paper.new_ledger()
    _register(ledger)
    original = copy.deepcopy(ledger["trades"])
    monkeypatch.setattr(paper, "MAX_TRADES", 1)
    decision, handoff = _opportunity(signal_id="second")
    assert not paper.register(ledger, decision, handoff, now_ts=1062)
    assert ledger["capacity_rejections"] == 1 and ledger["trades"] == original
