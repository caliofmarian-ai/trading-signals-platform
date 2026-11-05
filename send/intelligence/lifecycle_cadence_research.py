"""Paired cooldown-policy experiment on genuine canonical strategy evidence.

Only copied research FSM state has its cooldown duration changed. Production
FSM, strategy parameters, expiry calibration and all publication stay untouched.
"""
from collections import Counter
from copy import deepcopy
import json
import math
from pathlib import Path

from core import fsm_runtime, storage
from core.decision_assembly import assemble_decision
from core.runtime_execution_calibration import algo_params_sha256
from core.scoring_model import evaluate_score
from core.v2_fsm_orchestrator import advance_persistent_fsm, current_opportunity_signal_id
from intelligence import live_score_severity_research as severity
from intelligence import model_time_paper_trades as paper
from intelligence.signal_severity_scale import score_thresholds

PROTOCOL = "PAIRED_LIFECYCLE_COOLDOWN_RESEARCH_V1"
COOLDOWNS = (1, 30, 60, 120, 300)
REPORT_SECONDS = 60
_last_report = {}


def _path():
    from core.owner_signal_delivery import destination
    from intelligence.shadow_model_time_research import enabled
    if destination() is None or not enabled():
        return None
    path = Path(storage.root_path("analytics", "lifecycle_cadence_research", "state.json"))
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("INVALID_CADENCE_PATH")
    return path


def _read(path):
    state = severity._load(path)
    if state is None:
        return None
    rows = state.get("levels")
    if (state.get("protocol") != PROTOCOL or not isinstance(rows,list) or len(rows)!=len(COOLDOWNS)
        or [r.get("level") for r in rows] != list(range(len(COOLDOWNS)))
        or [r.get("cooldown_seconds") for r in rows] != list(COOLDOWNS)
        or type(state.get("baseline_changed")) is not bool):
        raise ValueError("INVALID_CADENCE_STATE")
    for row in rows:
        paper.validate(row["paper_trades"])
        fsm_runtime.enforce_invariants(deepcopy(row["fsm_state"]))
        if type(row["evaluations"]) is not int or row["evaluations"] < 0:
            raise ValueError("INVALID_CADENCE_COUNTER")
        for field in ("decision_kinds","blockers","fsm_reason_families","accepted_unique_stages"):
            if (not isinstance(row[field],dict) or any(type(n) is not int or n<0 for n in row[field].values())
                or (field in {"decision_kinds","fsm_reason_families"} and sum(row[field].values())!=row["evaluations"])):
                raise ValueError("INVALID_CADENCE_COUNTER")
        if (type(row["cooldown_policy_applications"]) is not int or row["cooldown_policy_applications"]<0
            or not isinstance(row["opportunities"],dict) or len(row["opportunities"])>128):
            raise ValueError("INVALID_CADENCE_EVIDENCE")
        severity._recover_archive(path,row)
    return state


def _new(params,evaluation,now,buffer_mode):
    template=severity._new(params,evaluation,now,buffer_mode)
    base=template["levels"][0]
    rows=[]
    for index,seconds in enumerate(COOLDOWNS):
        row=deepcopy(base)
        row.update(level=index,cooldown_seconds=seconds,cooldown_policy_applications=0)
        rows.append(row)
    template.update(protocol=PROTOCOL,levels=rows)
    return template


def apply_research_cooldown(before,after,*,now_ts,seconds):
    """Modify a copy of a NEW cooldown only; do not clear an existing block."""
    if type(seconds) is not int or seconds not in COOLDOWNS:
        raise ValueError("UNDECLARED_RESEARCH_COOLDOWN")
    result=deepcopy(after)
    changed=0
    for symbol,state in result.get("per_symbol",{}).items():
        prior=before.get("per_symbol",{}).get(symbol,{})
        if (state.get("state")=="COOLDOWN" and state.get("cooldown_until_ts") is not None
            and (prior.get("state")!="COOLDOWN" or prior.get("cooldown_until_ts")!=state["cooldown_until_ts"])):
            # Control must be byte-equivalent to the canonical default policy.
            if seconds != fsm_runtime.DEFAULT_COOLDOWN_SECONDS:
                state["cooldown_until_ts"]=int(now_ts)+seconds
            changed+=1
    fsm_runtime.enforce_invariants(result)
    return result,changed


def _summary(state,now):
    elapsed=max(0,now-state["started_ts"])
    return {"protocol":PROTOCOL,"truth_domain":"LIVE_POLICY_COUNTERFACTUAL_RESEARCH",
        "status":"PAUSED_BASELINE_CHANGED" if state["baseline_changed"] else "OBSERVING",
        "started_ts":state["started_ts"],"last_evaluation_ts":state["last_evaluation_ts"],
        "parameter_sha256":state["parameter_sha256"],"buffer_mode":state["buffer_mode"],
        "score_severity":0,"control_cooldown_seconds":300,"minimum_pre_lead_seconds":30,
        "tested_dimension":"RESEARCH_COOLDOWN_DURATION_ONLY_FIXED_SCORE_SEVERITY_0",
        "policies":[{"cooldown_seconds":row["cooldown_seconds"],"evaluations":row["evaluations"],
            "accepted_unique_stages":row["accepted_unique_stages"],"complete_ordered_chains":row["complete_ordered_chains"],
            "cooldown_blocked_evaluations":row["fsm_reason_families"].get("COOLDOWN",0),
            "cooldown_policy_applications":row["cooldown_policy_applications"],
            "hard_blockers":row["blockers"],
            "paper_trades":severity._paper_summary(row),
            "observed_chain_rate_per_hour":row["complete_ordered_chains"]*3600/elapsed if elapsed>0 else None,
            "stage_gap_samples":row["stage_gap_samples"]} for row in state["levels"]],
        "production_parameters_changed":False,"production_cooldown_changed":False,
        "execution_calibration_proven":False,"actual_telegram_publications":0,"broker_executed":False,
        "automatic_selection_allowed":False,
        "limitations":["Research-only copied FSM cooldown policy; no active strategy approval.",
            "All policies retain the same canonical hard gates and the 30-second PRE lead.",
            "Overlapping policies are correlated and their sample counts must not be summed.",
            "Model Time paper outcomes are not calibrated Execution Time or broker outcomes.",
            "A short observed rate or a higher stage count does not establish 30 signals/hour or 80% efficacy."]}


def observe(evaluation,params,*,now_ts,provider,buffer_mode):
    path=_path()
    if path is None or provider!="FINNHUB" or evaluation.market.symbol.replace("/","")!="EURUSD":
        return
    if type(now_ts) not in {int,float} or not math.isfinite(now_ts) or now_ts<=0:
        raise ValueError("INVALID_CADENCE_TIME")
    with storage.with_lock("lifecycle_cadence_research",timeout_sec=.2):
        state=_read(path) or _new(params,evaluation,now_ts,buffer_mode)
        if state["last_evaluation_ts"] is not None and now_ts<=state["last_evaluation_ts"]:
            return
        if (state["parameter_sha256"]!=algo_params_sha256(params) or state["buffer_mode"]!=buffer_mode
            or state["strategy_version"]!=evaluation.strategy_version or state["canonical_spec"]!=evaluation.canonical_spec):
            state["baseline_changed"]=True
        severity._archive_finalized(path,state)
        if not state["baseline_changed"]:
            variant={**params,"score_thresholds":score_thresholds(params,0)}
            score=evaluate_score(evaluation.market,evaluation.corridor,evaluation.time,variant)
            for row in state["levels"]:
                before=row["fsm_state"]
                fsm,_=fsm_runtime.reconcile_state(deepcopy(before),int(now_ts),active_symbols=[evaluation.market.symbol])
                fsm,n=apply_research_cooldown(before,fsm,now_ts=now_ts,seconds=row["cooldown_seconds"])
                row["cooldown_policy_applications"]+=n
                decision=assemble_decision(evaluation.market,evaluation.corridor,evaluation.time,score,
                    timeframe=evaluation.decision.setup.timeframe,cycle_id=evaluation.cycle_id,
                    source="lifecycle_cadence_research",opportunity_signal_id=current_opportunity_signal_id(fsm,evaluation.market.symbol),
                    maximum_stage=severity._maximum_stage(row,fsm,evaluation.market.symbol,now_ts,evaluation.market.direction_bias))
                handoff=advance_persistent_fsm(fsm,decision,now_ts=int(now_ts))
                next_state,n=apply_research_cooldown(fsm,handoff.next_state,now_ts=now_ts,seconds=row["cooldown_seconds"])
                row["cooldown_policy_applications"]+=n
                row["fsm_state"]=next_state
                row["evaluations"]+=1
                for field,items in (("decision_kinds",[decision.kind]),("blockers",decision.reject.hard_blockers),
                                    ("fsm_reason_families",[handoff.reason_family])):
                    counts=Counter(row[field]);counts.update(items);row[field]=dict(counts)
                severity._observe_accepted_stage(row,decision,handoff,now_ts)
            state["last_evaluation_ts"]=now_ts
        severity._save(path,state)
    _report_if_due(path,state,now_ts)


def _report_if_due(path,state,now):
    slot=int(now//REPORT_SECONDS)
    if _last_report.get(str(path),-1)<slot:
        report=_summary(state,now)
        print("TSP_LIFECYCLE_CADENCE_RESEARCH "+json.dumps(report,sort_keys=True),flush=True)
        _last_report[str(path)]=slot
        return report


def advance(*,now_ts,active_provider,price_loader):
    path=_path()
    if path is None:
        return
    with storage.with_lock("lifecycle_cadence_research",timeout_sec=.2):
        state=_read(path)
        if state is None:
            return
        severity._archive_finalized(path,state)
        sample=None
        if active_provider=="FINNHUB" and any(paper.pending(row["paper_trades"]) for row in state["levels"]):
            try: sample=price_loader("EUR/USD")
            except Exception: pass
        changed=False
        for row in state["levels"]:
            changed=paper.advance(row["paper_trades"],sample,now_ts=now_ts,active_provider=active_provider) or changed
        if changed:
            severity._save(path,state)
    return _report_if_due(path,state,now_ts)


def summary(*,now_ts):
    path=_path()
    if path is None:
        return None
    with storage.with_lock("lifecycle_cadence_research",timeout_sec=.2):
        state=_read(path)
    return _summary(state,now_ts) if state else None
