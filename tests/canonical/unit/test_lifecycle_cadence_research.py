"""Synthetic fixtures verify mechanics, never actual market calibration efficacy."""
from copy import deepcopy
from dataclasses import replace
import importlib
import json
import pytest
from tests.canonical.unit.test_live_score_severity_research import _prepare
from tests.canonical.unit.test_shadow_model_time_research import _sample


@pytest.fixture
def cadence(canonical_runtime_root,monkeypatch):
    severity,evaluation,params=_prepare(canonical_runtime_root,monkeypatch)
    module=importlib.import_module("intelligence.lifecycle_cadence_research")
    module._last_report.clear()
    return module,severity,evaluation,params


def _observe(module,evaluation,params,stamp):
    module.observe(evaluation,params,now_ts=stamp,provider="FINNHUB",buffer_mode="SMALL")


def _chain(module,evaluation,params):
    now=evaluation.market.evaluated_ts+1
    for stamp in (now,now+2,now+10,now+30):_observe(module,evaluation,params,stamp)
    return now


@pytest.mark.parametrize("seconds",[1,30,60,120,300])
def test_only_new_copied_cooldown_is_adjusted(cadence,seconds):
    module,_,evaluation,params=cadence
    from state_store.state_store import default_fsm_state
    before=default_fsm_state()
    after=deepcopy(before)
    after["per_symbol"]["EURUSD"]={"state":"COOLDOWN","cooldown_until_ts":1300}
    result,n=module.apply_research_cooldown(before,after,now_ts=1000,seconds=seconds)
    assert n==1 and result["per_symbol"]["EURUSD"]["cooldown_until_ts"]==1000+seconds
    assert after["per_symbol"]["EURUSD"]["cooldown_until_ts"]==1300
    again,n=module.apply_research_cooldown(result,result,now_ts=1001,seconds=seconds)
    assert n==0 and again==result


def test_control_matches_canonical_fsm_and_original_study_is_unchanged(cadence):
    module,severity,evaluation,params=cadence
    now=evaluation.market.evaluated_ts+1
    for stamp in (now,now+2,now+30):
        severity.observe(evaluation,params,now_ts=stamp,provider="FINNHUB",buffer_mode="SMALL")
        old=severity._path().read_bytes()
        _observe(module,evaluation,params,stamp)
        assert severity._path().read_bytes()==old
    control=module._read(module._path())["levels"][-1]
    original=severity._read(severity._path())["levels"][0]
    assert control["fsm_state"]==original["fsm_state"]
    assert control["accepted_unique_stages"]==original["accepted_unique_stages"]
    assert control["paper_trades"]["trades"].keys()==original["paper_trades"]["trades"].keys()
    for identity,trade in control["paper_trades"]["trades"].items():
        reference=original["paper_trades"]["trades"][identity]
        provenance={"decision_id","decision_audit_id","fsm_transition_id"}
        assert {k:v for k,v in trade.items() if k not in provenance}=={k:v for k,v in reference.items() if k not in provenance}
        assert all(trade[k] for k in provenance)


def test_all_policies_keep_pre_lead_and_real_quote_contract(cadence):
    module,_,evaluation,params=cadence
    now=_chain(module,evaluation,params)
    report=module.summary(now_ts=now+31)
    assert report["score_severity"]==0 and report["production_cooldown_changed"] is False
    assert [r["cooldown_seconds"] for r in report["policies"]]==[1,30,60,120,300]
    assert all(r["complete_ordered_chains"]==1 for r in report["policies"])
    assert all(r["stage_gap_samples"][0]["pre_to_open_seconds"]==30 for r in report["policies"])
    module.advance(now_ts=now+31,active_provider="FINNHUB",price_loader=lambda _:_sample(now+31))
    end=now+31+evaluation.time.context.model_expiry*60
    module.advance(now_ts=end,active_provider="FINNHUB",price_loader=lambda _:_sample(end,1.2))
    report=module.summary(now_ts=end+1)
    assert all(r["paper_trades"]["outcomes"]["WIN"]==1 for r in report["policies"])
    assert report["actual_telegram_publications"]==0 and report["broker_executed"] is False


def test_research_short_cooldown_never_skips_a_canonical_cooldown_block(cadence):
    module,_,evaluation,params=cadence
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from core.decision_assembly import assemble_decision
    now=_chain(module,evaluation,params)
    row=module._read(module._path())["levels"][0]
    state=deepcopy(row["fsm_state"])
    from core.decision_object import RejectContext
    rejected=replace(evaluation.decision,kind="REJECT",signal_id=None,
        strategic_flags=replace(evaluation.decision.strategic_flags,rejectable=True),
        reject=RejectContext(reason="TEST_ONLY_REJECTION",hard_blockers=("STRUCTURE_NOT_VALID",)))
    release=advance_persistent_fsm(state,rejected,now_ts=int(now+40))
    short,_=module.apply_research_cooldown(state,release.next_state,now_ts=now+40,seconds=1)
    assert short["per_symbol"][evaluation.market.symbol]["state"]=="COOLDOWN"
    pre=assemble_decision(evaluation.market,evaluation.corridor,evaluation.time,evaluation.scoring,
        timeframe="M1",cycle_id=evaluation.cycle_id,maximum_stage="PRE")
    pre=replace(pre,signal_id="test-only-next-research-opportunity")
    blocked=advance_persistent_fsm(short,pre,now_ts=int(now+40))
    assert blocked.reason_family=="COOLDOWN" and blocked.stage_handoff_ready is False
    from core import fsm_runtime
    recovered,_=fsm_runtime.reconcile_state(deepcopy(short),int(now+42),active_symbols=[evaluation.market.symbol])
    accepted=advance_persistent_fsm(recovered,pre,now_ts=int(now+42))
    assert accepted.accepted_stage=="PRE" and accepted.stage_handoff_ready is True
    baseline,_=module.apply_research_cooldown(state,release.next_state,now_ts=now+40,seconds=300)
    baseline,_=fsm_runtime.reconcile_state(baseline,int(now+42),active_symbols=[evaluation.market.symbol])
    assert advance_persistent_fsm(baseline,pre,now_ts=int(now+42)).reason_family=="COOLDOWN"


def test_focus_lease_expiry_uses_each_declared_policy(cadence):
    module,_,evaluation,params=cadence
    from core import fsm_runtime
    now=evaluation.market.evaluated_ts+1
    _observe(module,evaluation,params,now)
    before=module._read(module._path())["levels"][0]["fsm_state"]
    symbol=evaluation.market.symbol
    before["per_symbol"][symbol]["focus_ttl_seconds"]=60
    after,_=fsm_runtime.reconcile_state(deepcopy(before),int(now+61),active_symbols=[symbol])
    for seconds in module.COOLDOWNS:
        result,n=module.apply_research_cooldown(before,after,now_ts=now+61,seconds=seconds)
        assert n==1 and result["per_symbol"][symbol]["cooldown_until_ts"]==int(now+61)+seconds


def test_missing_quote_is_unknown_and_restart_preserves_pending(cadence):
    module,_,evaluation,params=cadence
    now=_chain(module,evaluation,params)
    before=module._path().read_bytes()
    module=importlib.reload(module)
    assert module._path().read_bytes()==before
    module.advance(now_ts=now+41,active_provider="FINNHUB",price_loader=lambda _:None)
    report=module.summary(now_ts=now+42)
    assert all(r["paper_trades"]["outcomes"]["UNKNOWN"]==1 for r in report["policies"])
    assert all(r["paper_trades"]["outcomes"]["LOSS"]==0 for r in report["policies"])


def test_source_drift_pauses_new_decisions_without_erasing_history(cadence):
    module,_,evaluation,params=cadence
    now=_chain(module,evaluation,params)
    changed=deepcopy(params);changed["score_thresholds"]["OPEN"]+=1
    _observe(module,evaluation,changed,now+31)
    report=module.summary(now_ts=now+32)
    assert report["status"]=="PAUSED_BASELINE_CHANGED"
    assert all(r["complete_ordered_chains"]==1 for r in report["policies"])
    assert all(r["evaluations"]==4 for r in report["policies"])


def test_corruption_is_not_reset_and_invalid_policy_is_rejected(cadence):
    module,_,evaluation,params=cadence
    now=evaluation.market.evaluated_ts+1
    _observe(module,evaluation,params,now)
    state=module._read(module._path());state["levels"][0]["cooldown_seconds"]=0
    module._path().write_text(json.dumps(state));raw=module._path().read_bytes()
    with pytest.raises(ValueError):_observe(module,evaluation,params,now+2)
    assert module._path().read_bytes()==raw


def test_disabled_research_and_other_provider_cannot_create_state(cadence,monkeypatch):
    module,_,evaluation,params=cadence
    module.observe(evaluation,params,now_ts=1000,provider="TWELVE_DATA",buffer_mode="SMALL")
    assert not module._path().exists()
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION","true")
    _observe(module,evaluation,params,1000)
    assert module._path() is None


def test_short_cooldown_cannot_pass_an_invalid_structure(cadence):
    module,_,evaluation,params=cadence
    invalid=replace(evaluation,corridor=replace(evaluation.corridor,
        structure=replace(evaluation.corridor.structure,feasibility_state="UNAVAILABLE")))
    _observe(module,invalid,params,evaluation.market.evaluated_ts+1)
    report=module.summary(now_ts=evaluation.market.evaluated_ts+2)
    assert all(r["hard_blockers"]["STRUCTURE_NOT_VALID"]==1 for r in report["policies"])
    assert all(not r["accepted_unique_stages"] for r in report["policies"])


def test_private_audit_isolates_invalid_cadence_source(cadence,monkeypatch):
    module,_,_,_=cadence
    from core import owner_signal_delivery
    def invalid(**kwargs):raise RuntimeError("TEST_ONLY_INVALID_FSM_SOURCE")
    monkeypatch.setattr(module,"summary",invalid)
    result=owner_signal_delivery.audit_evidence(123456789)
    assert result["lifecycle_cadence_research"]["status"]=="SOURCE_UNAVAILABLE_OR_INVALID"
