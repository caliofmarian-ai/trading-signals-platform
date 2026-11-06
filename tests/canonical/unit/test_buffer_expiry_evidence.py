"""Synthetic boundary/restart fixtures; no empirical efficacy claim."""
import copy
import importlib
import math

import pytest

from tests.canonical.unit.test_execution_expiry_calibration import (
    calibration, _entry, _capture, _advance, _synthetic_state,
)
from tests.canonical.unit.test_shadow_model_time_research import _sample


@pytest.mark.parametrize("direction,price,status,coverage", [
    ("BUY", 1.10001, "NOT_MET", 1/22),
    ("BUY", math.nextafter(1.10022,-math.inf), "NOT_MET", None),
    ("BUY", 1.10022, "MET", 1),
    ("BUY", 1.10030, "MET", 30/22),
    ("BUY", 1.10000, "NOT_MET", 0),
    ("BUY", 1.09999, "NOT_MET", -1/22),
    ("SELL", 1.09999, "NOT_MET", 1/22),
    ("SELL", math.nextafter(1.09978,math.inf), "NOT_MET", None),
    ("SELL", 1.09978, "MET", 1),
    ("SELL", 1.09970, "MET", 30/22),
    ("SELL", 1.10000, "NOT_MET", 0),
    ("SELL", 1.10001, "NOT_MET", -1/22),
])
def test_exact_buffer_boundary_is_separate_from_directional_result(calibration,direction,price,status,coverage):
    module,_=calibration
    evidence=importlib.import_module("intelligence.buffer_expiry_evidence")
    frozen=evidence.snapshot(0.00022,"a"*64)
    result=evidence.measure(direction,_sample(1001,1.1),_sample(1121,price),frozen)
    assert result["status"]==status
    if coverage is not None:
        assert result["buffer_coverage"]==pytest.approx(coverage)
    if result["buffer_coverage"]==1:
        assert result["buffer_margin_at_expiry"]==0
    if result["status"]=="MET":
        assert module.quotes._classify(direction,1.1,price)=="WIN"


def test_small_win_is_preserved_and_does_not_meet_buffer(calibration):
    module,params=calibration
    _capture(module,params,[_entry()]);_advance(module,1001)
    _advance(module,1121,1.10001)
    report=module.summary(now_ts=1121)
    counts=report["paired_expiry_observations"][0]
    assert counts["wins"]==1 and counts["win_rate"]==1
    assert counts["buffer_met"]==0 and counts["win_buffer_not_met"]==1
    assert counts["buffer_met_rate"]==0 and counts["buffer_unknown_fraction"]==0
    assert report["levels"][0]["buffer_expiry_observations"][0]["win_buffer_not_met"]==1
    assert "buffer_expiry_observations" not in module._compact(report)["levels"][0]


def test_snapshot_survives_restart_and_rejects_rewrite(calibration):
    module,params=calibration
    item=_entry(buffer_distance=0.00022)
    _capture(module,params,[item]);_advance(module,1001)
    before=module._path().read_bytes()
    # Mutating the caller's entry or current parameter file cannot change B.
    item["buffer_distance"]=0.5
    importlib.reload(module)
    assert module._path().read_bytes()==before
    with pytest.raises(ValueError,match="BUFFER_SNAPSHOT_REWRITE"):
        _capture(module,params,[item])
    assert module._path().read_bytes()==before
    _advance(module,1121,1.10022)
    assert module.summary(now_ts=1121)["paired_expiry_observations"][0]["buffer_met"]==1
    changed=copy.deepcopy(params);changed["buffer_atr_multiplier"]="fixture-only-drift"
    with pytest.raises(ValueError,match="SCOPE_CHANGED"):
        _capture(module,changed,[_entry(1300)])


@pytest.mark.parametrize("distance",[None,0,-1,True,float("nan"),float("inf")])
def test_unavailable_buffer_cannot_turn_real_win_into_buffer_success(calibration,distance):
    module,params=calibration
    _capture(module,params,[_entry(buffer_distance=distance)])
    _advance(module,1001);_advance(module,1121,1.2)
    counts=module.summary(now_ts=1121)["paired_expiry_observations"][0]
    assert counts["wins"]==1 and counts["buffer_unavailable"]==1
    assert counts["buffer_met"]==0 and counts["buffer_sample"]==0
    assert counts["buffer_met_rate"] is None and counts["buffer_unknown_fraction"]==1


def test_missing_expiry_never_becomes_buffer_failure_or_success(calibration):
    module,params=calibration
    _capture(module,params,[_entry()]);_advance(module,1001)
    module.advance(now_ts=1124,active_provider="FINNHUB",price_loader=lambda _:None)
    counts=module.summary(now_ts=1124)["paired_expiry_observations"][0]
    assert counts["unknown"]==1 and counts["buffer_unavailable"]==1
    assert counts["buffer_met"]==counts["buffer_not_met"]==0


def test_historical_rows_are_preserved_and_never_reused_for_buffer_fit(calibration):
    module,params=calibration
    state=_synthetic_state(module,params)
    for row in state["records"].values():
        del row["buffer_snapshot"],row["buffer_snapshot_sha256"]
    del state["buffer_objective"],state["buffer_collection_started_ts"]
    module._save(module._path(),state)
    old_records=copy.deepcopy(state["records"])
    module.advance(now_ts=30000,active_provider="FINNHUB",price_loader=lambda _:pytest.fail("No pending quotes"))
    saved=module._read(module._path())
    assert saved["records"]==old_records
    assert saved["started_ts"]==state["started_ts"]
    assert saved["buffer_collection_started_ts"]==30000
    # Replaying today's buffer for the same old entry cannot backfill it.
    _capture(module,params,[_entry()])
    assert module._read(module._path())["records"]==old_records
    report=module.summary(now_ts=30000)
    assert report["legacy_directional_only_entries"]==120 and report["prospective_buffer_entries"]==0
    assert report["levels"][0]["train_entries"]==0 and report["ready_levels"]==[]
    assert report["paired_expiry_observations"][0]["legacy_buffer_unavailable"]==120


def test_training_selects_buffer_margin_and_never_direction_only_win(calibration):
    module,params=calibration
    state=_synthetic_state(module,params)
    for i,row in enumerate(state["records"].values()):
        for j,candidate in enumerate(row["candidates"]):
            price=1.2 if j==2 else 1.10001
            candidate.update(outcome="WIN",quote=_sample(row["created_ts"]+1+candidate["horizon_seconds"],price))
    module.validate(state)
    report=module.analyze(state,now_ts=30000)
    row=report["levels"][0]
    assert row["training_selected_bias"]==.1  # Every candidate has 100% directional WIN.
    assert row["status"]=="READY_FOR_REVIEW"
    assert row["proposal_only"]["objective_contract"]=="BUFFER_MET_AT_EXPIRY_V1"
    assert row["untouched_holdout"]["buffer_familywise_95_lower"]>=.8


def test_directional_holdout_success_alone_cannot_produce_proposal(calibration):
    module,params=calibration
    state=_synthetic_state(module,params)
    for i,row in enumerate(state["records"].values()):
        if i>=60:
            candidate=row["candidates"][1]
            candidate["quote"]=_sample(row["created_ts"]+1+candidate["horizon_seconds"],1.10001)
    report=module.analyze(state,now_ts=30000)
    row=report["levels"][0]
    assert row["untouched_holdout"]["win_rate"]==1 and row["untouched_holdout"]["buffer_met_rate"]==0
    assert row["status"]=="BUFFER_TARGET_NOT_MET" and "proposal_only" not in row
    assert report["ready_levels"]==[]


def test_missing_buffer_is_counted_in_holdout_quality_instead_of_dropped(calibration):
    module,params=calibration
    state=_synthetic_state(module,params)
    for row in list(state["records"].values())[60:67]:
        frozen=module.buffer_evidence.snapshot(None,state["scope"]["parameter_sha256"])
        row.update(buffer_snapshot=frozen,buffer_snapshot_sha256=module._digest(frozen))
    report=module.analyze(state,now_ts=30000)
    row=report["levels"][0]
    assert row["untouched_holdout"]["buffer_unavailable"]==7
    assert row["untouched_holdout"]["buffer_unknown_fraction"]==7/60
    assert row["status"]=="HOLDOUT_BUFFER_DATA_QUALITY_FAILED"


def test_draw_is_buffer_failure_and_snapshot_corruption_is_rejected(calibration):
    module,params=calibration
    _capture(module,params,[_entry()]);_advance(module,1001);_advance(module,1121,1.1)
    counts=module.summary(now_ts=1121)["paired_expiry_observations"][0]
    assert counts["draws"]==1 and counts["buffer_not_met"]==1 and counts["buffer_sample"]==1
    state=module._read(module._path())
    next(iter(state["records"].values()))["buffer_snapshot"]["buffer_distance"]=0.00001
    with pytest.raises(ValueError,match="BUFFER_SNAPSHOT_CHANGED"):
        module.validate(state)


def test_old_pending_quotes_still_settle_without_backfilled_buffer(calibration):
    module,params=calibration
    _capture(module,params,[_entry()]);_advance(module,1001)
    state=module._read(module._path())
    row=next(iter(state["records"].values()))
    del row["buffer_snapshot"],row["buffer_snapshot_sha256"]
    module._save(module._path(),state)
    _advance(module,1121,1.10022)
    saved=module._read(module._path())
    row=next(iter(saved["records"].values()))
    assert row["candidates"][0]["outcome"]=="WIN" and "buffer_snapshot" not in row
    counts=module.summary(now_ts=1121)["paired_expiry_observations"][0]
    assert counts["wins"]==counts["legacy_buffer_unavailable"]==counts["win_buffer_unavailable"]==1
    assert counts["buffer_sample"]==0
