"""All quotes here are synthetic fixtures, never calibration/activation evidence."""
import copy
import importlib
import json
import pytest

from tests.canonical.unit.test_shadow_model_time_research import _sample


@pytest.fixture
def calibration(canonical_runtime_root, monkeypatch):
    for key,value in {"OWNER_SIGNAL_DELIVERY_ENABLED":"true", "OWNER_TELEGRAM_ID":"123456789",
                      "SHADOW_MODE":"true", "ENABLE_BROKER_EXECUTION":"false",
                      "SHADOW_MODEL_TIME_RESEARCH_ENABLED":"true"}.items():
        monkeypatch.setenv(key,value)
    module=importlib.import_module("intelligence.execution_expiry_calibration")
    module._last_report.clear()
    params=json.loads((canonical_runtime_root/"config/algo_params.json").read_text())
    return module,params


def _entry(stamp=1000, level=0, **changes):
    return {"level":level,"direction":"BUY","created_ts":stamp,"pre_ts":stamp-35,
            "confirm_ts":stamp-30,"open_ts":stamp,"confirm_model_seconds":120,
            "model_seconds":120,"adjusted_seconds":90,**changes}


def _capture(module,params,entries):
    module.capture(entries, params=params,buffer_mode="MEDIUM",strategy_version="2.0.0",
                   canonical_spec="TEST-ONLY",now_ts=max(e["created_ts"] for e in entries))


def _advance(module,stamp,price=1.1,provider="FINNHUB"):
    return module.advance(now_ts=stamp,active_provider=provider,price_loader=lambda _:_sample(stamp,price))


def test_paired_expiries_are_predeclared_exact_and_observed(calibration):
    module,params=calibration
    _capture(module,params,[_entry()])
    before=module._read(module._path())
    row=next(iter(before["records"].values()))
    assert row["entry"] is None
    assert [c["horizon_seconds"] for c in row["candidates"]] == [120,114,108,102,96,90]
    _advance(module,1001)
    for horizon in (90,96,102,108,114,120):
        _advance(module,1001+horizon,1.2 if horizon!=114 else 1.0)
    row=next(iter(module._read(module._path())["records"].values()))
    assert row["state"]=="FINAL"
    assert [c["outcome"] for c in row["candidates"]]==["WIN","LOSS","WIN","WIN","WIN","WIN"]
    assert row["candidates"][1]["quote"]["observed_ts"]==1115
    report=module.summary(now_ts=1200)
    assert report["execution_calibration_proven"] is False
    assert report["levels"][0]["training_selected_bias"] is None
    assert report["levels"][0]["timing_seconds"]["pre_to_open"]["p95"]==35


def test_shared_level_entries_are_not_multiplied(calibration):
    module,params=calibration
    _capture(module,params,[_entry(level=0),_entry(level=1),_entry(level=2)])
    _capture(module,params,[_entry(level=0)])
    report=module.summary(now_ts=1001)
    assert report["unique_entry_experiments"]==1
    assert [r["unique_entries"] for r in report["levels"][:4]]==[1,1,1,0]


def test_missing_entry_and_expiry_become_unknown_never_loss(calibration):
    module,params=calibration
    _capture(module,params,[_entry()])
    module.advance(now_ts=1011,active_provider="FINNHUB",price_loader=lambda _:None)
    row=next(iter(module._read(module._path())["records"].values()))
    assert row["state"]=="FINAL"
    assert all(c["outcome"]=="UNKNOWN" for c in row["candidates"])
    _capture(module,params,[_entry(1300)])
    _advance(module,1301)
    module.advance(now_ts=1424,active_provider="FINNHUB",price_loader=lambda _:None)
    row=list(module._read(module._path())["records"].values())[-1]
    assert all(c["outcome"]=="UNKNOWN" for c in row["candidates"])


def test_infeasible_shortening_is_excluded(calibration):
    module,params=calibration
    _capture(module,params,[_entry(adjusted_seconds=115)])
    row=next(iter(module._read(module._path())["records"].values()))
    assert row["candidates"][0]["outcome"]=="PENDING"
    assert all(c["outcome"]=="INFEASIBLE" for c in row["candidates"][1:])


def test_restart_preserves_pending_exact_quotes_and_horizons(calibration):
    module,params=calibration
    _capture(module,params,[_entry()]);_advance(module,1001)
    before=module._path().read_bytes()
    importlib.reload(module)
    assert module._path().read_bytes()==before
    _advance(module,1091,1.2)
    row=next(iter(module._read(module._path())["records"].values()))
    assert row["candidates"][-1]["outcome"]=="WIN"
    assert row["candidates"][0]["outcome"]=="PENDING"


def test_future_and_stale_quotes_are_not_backfilled(calibration):
    module,params=calibration
    _capture(module,params,[_entry()])
    module.advance(now_ts=1001,active_provider="FINNHUB",price_loader=lambda _:_sample(1002))
    assert next(iter(module._read(module._path())["records"].values()))["entry"] is None
    module.advance(now_ts=1011,active_provider="FINNHUB",price_loader=lambda _:_sample(1001))
    assert next(iter(module._read(module._path())["records"].values()))["state"]=="FINAL"


def test_provider_change_cannot_supply_result(calibration):
    module,params=calibration
    _capture(module,params,[_entry()]);_advance(module,1001)
    _advance(module,1091,1.2,provider="TWELVE_DATA")
    row=next(iter(module._read(module._path())["records"].values()))
    assert all(c["outcome"]=="UNKNOWN" and c["reason"]=="PROVIDER_CHANGED" for c in row["candidates"])


def test_corrupt_or_drifted_source_is_not_reset(calibration):
    module,params=calibration
    _capture(module,params,[_entry()])
    before=module._path().read_bytes()
    changed=copy.deepcopy(params);changed["score_thresholds"]["OPEN"]+=1
    with pytest.raises(ValueError,match="SCOPE_CHANGED"):_capture(module,changed,[_entry(1300)])
    assert module._path().read_bytes()==before
    module._path().write_text('{"bad":true}')
    with pytest.raises(ValueError):_capture(module,params,[_entry(1300)])
    assert module._path().read_text()=='{"bad":true}'


def _synthetic_state(module,params,n=120,train_outcome="WIN",holdout_outcome="WIN"):
    _capture(module,params,[_entry()]);_advance(module,1001)
    state=module._read(module._path());base=next(iter(state["records"].values()))
    state["records"]={}
    for i in range(n):
        row=copy.deepcopy(base);stamp=1000+i*200
        row.update(created_ts=stamp,state="FINAL",entry=_sample(stamp+1))
        row["levels"]={"0":{"pre_ts":stamp-35,"confirm_ts":stamp-30,"open_ts":stamp,"confirm_model_seconds":120}}
        for j,candidate in enumerate(row["candidates"]):
            outcome=train_outcome if i<60 else holdout_outcome
            # Only candidate .05 wins in training; never choose by holdout.
            if j!=1:outcome="LOSS" if i<60 else "WIN"
            candidate.update(outcome=outcome,reason="TEST_ONLY",quote=_sample(stamp+1+candidate["horizon_seconds"],1.2 if outcome=="WIN" else 1.0))
        identity=module._digest({**{k:row[k] for k in ("direction","created_ts","model_seconds","adjusted_seconds")},"scope":state["scope"]})
        state["records"][identity]=row
    module.validate(state)
    return state


def test_training_selection_cannot_peek_at_holdout(calibration):
    module,params=calibration
    state=_synthetic_state(module,params,holdout_outcome="LOSS")
    report=module.analyze(state,now_ts=30000)
    row=report["levels"][0]
    assert row["training_selected_bias"]==.05
    assert row["untouched_holdout"]["win_rate"]==0
    assert row["status"]=="EFFICACY_TARGET_NOT_MET"
    assert "proposal_only" not in row


def test_fixed_holdout_and_interval_gate_before_proposal(calibration):
    module,params=calibration
    state=_synthetic_state(module,params)
    report=module.analyze(state,now_ts=30000)
    row=report["levels"][0]
    assert row["status"]=="READY_FOR_REVIEW"
    assert row["proposal_only"]["pressure_bias"]==.05
    # A reviewable proposal still cannot write or activate any runtime artifact.
    assert report["execution_calibration_proven"] is False
    assert report["automatic_activation_allowed"] is False
    assert not (module._path().parents[2]/"config/execution_calibration.json").exists()
    # Out-of-training CONFIRM forecast drift violates its held-out duration band.
    list(state["records"].values())[-1]["levels"]["0"]["confirm_model_seconds"]=300
    row=module.analyze(state,now_ts=30000)["levels"][0]
    assert row["holdout_confirm_interval_violations"]==1 and row["status"]!="READY_FOR_REVIEW"
    partial=_synthetic_state(module,params,n=119)
    assert module.analyze(partial,now_ts=30000)["levels"][0]["status"]!="READY_FOR_REVIEW"


def test_overlap_is_removed_before_looking_at_outcomes(calibration):
    module,params=calibration
    _capture(module,params,[_entry(),_entry(1001),_entry(1002)])
    row=module.summary(now_ts=1005)["levels"][0]
    assert row["unique_entries"]==3 and row["nonoverlapping_entries"]==1


def test_capacity_preserves_old_evidence_and_settles_pending(calibration,monkeypatch):
    module,params=calibration
    monkeypatch.setattr(module,"MAX_RECORDS",1)
    _capture(module,params,[_entry()]);_capture(module,params,[_entry(1300)])
    report=module.summary(now_ts=1300)
    assert report["unique_entry_experiments"]==1 and report["capacity_rejections"]==1
    _advance(module,1301)
    assert module.summary(now_ts=1301)["pending"]==0


def test_public_status_has_no_raw_prices_or_signal_identifiers(calibration,capsys):
    module,params=calibration
    _capture(module,params,[_entry()]);_advance(module,1001,1.123456789)
    text=capsys.readouterr().out
    assert "1.123456789" not in text and '"entry"' not in text and '"quote"' not in text
    assert "TSP_EXECUTION_EXPIRY_CALIBRATION" in text


def test_disabled_research_cannot_create_state_or_request_price(calibration,monkeypatch):
    module,params=calibration
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION","true")
    _capture(module,params,[_entry()])
    assert module.advance(now_ts=1001,active_provider="FINNHUB",price_loader=lambda _:pytest.fail("Unexpected provider request")) is None


def test_live_pipeline_registers_only_complete_first_stage_chains(canonical_runtime_root,monkeypatch):
    from tests.canonical.unit.test_live_score_severity_research import _prepare
    severity,evaluation,params=_prepare(canonical_runtime_root,monkeypatch)
    module=importlib.import_module("intelligence.execution_expiry_calibration")
    now=evaluation.market.evaluated_ts+1
    for stamp in (now,now+2):
        severity.observe(evaluation,params,now_ts=stamp,provider="FINNHUB",buffer_mode="SMALL")
    assert not module._path().exists()
    severity.observe(evaluation,params,now_ts=now+30,provider="FINNHUB",buffer_mode="SMALL")
    report=module.summary(now_ts=now+31)
    assert report["unique_entry_experiments"]==1
    assert report["levels"][0]["unique_entries"]==1
    row=next(iter(module._read(module._path())["records"].values()))
    assert row["levels"]["0"]["confirm_model_seconds"]==evaluation.time.context.model_expiry*60
    assert row["levels"]["0"]["open_ts"]-row["levels"]["0"]["pre_ts"]==30


def test_calibration_failure_preserves_existing_severity_checkpoint(canonical_runtime_root,monkeypatch):
    from tests.canonical.unit.test_live_score_severity_research import _prepare
    severity,evaluation,params=_prepare(canonical_runtime_root,monkeypatch)
    module=importlib.import_module("intelligence.execution_expiry_calibration")
    now=evaluation.market.evaluated_ts+1
    for stamp in (now,now+2):
        severity.observe(evaluation,params,now_ts=stamp,provider="FINNHUB",buffer_mode="SMALL")
    def unavailable(*a,**k):raise ValueError("TEST_ONLY_UNAVAILABLE")
    monkeypatch.setattr(module,"capture",unavailable)
    with pytest.raises(ValueError,match="TEST_ONLY_UNAVAILABLE"):
        severity.observe(evaluation,params,now_ts=now+30,provider="FINNHUB",buffer_mode="SMALL")
    row=severity.summary(now_ts=now+31)["levels"][0]
    assert row["accepted_unique_stages"]["OPEN_NOW"]==1 and row["paper_trades"]["registered"]==1


@pytest.mark.parametrize("field,value",[("model_seconds",float('nan')),("adjusted_seconds",121),("pre_ts",999),("level",21)])
def test_invalid_chain_does_not_reach_persistent_state(calibration,field,value):
    module,params=calibration
    with pytest.raises((ValueError,TypeError)):_capture(module,params,[_entry(**{field:value})])
    assert not module._path().exists()
