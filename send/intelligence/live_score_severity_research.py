"""Paired, isolated real-time score/FSM research at severities 0..20.

Reuses immutable upstream real-market evidence; no extra feed requests, live
parameter writes, SignalEvent, publisher, execution calibration or broker path.
"""

from collections import Counter
import json
import math
import os
from pathlib import Path
import re

from core import fsm_runtime, storage
from core.decision_assembly import assemble_decision
from core.runtime_execution_calibration import algo_params_sha256
from core.scoring_model import evaluate_score
from core.strategy_v2 import BinaryStrategyV2Evaluation
from core.v2_fsm_orchestrator import advance_persistent_fsm, current_opportunity_signal_id
from intelligence.signal_severity_scale import BASELINE_LEVEL, LEVELS, score_thresholds
from state_store.state_store import default_fsm_state


PROTOCOL = "LIVE_SCORE_SEVERITY_RESEARCH_V1"
DURATION_SECONDS = 7200
MAX_BYTES = 1024 * 1024
STAGES = ("PRE", "CONFIRM", "OPEN_NOW")
PAIRS = {"pre_to_confirm_seconds": ("PRE", "CONFIRM"),
         "confirm_to_open_seconds": ("CONFIRM", "OPEN_NOW"),
         "pre_to_open_seconds": ("PRE", "OPEN_NOW")}


def _path() -> Path | None:
    from core.owner_signal_delivery import destination
    session = os.getenv("OWNER_TIMING_SESSION_ID", "")
    if (destination() is None
        or os.getenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "").lower() not in {"true", "1", "yes", "on"}
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", session) is None):
        return None
    directory = Path(storage.root_path("analytics", "live_score_severity_research"))
    path = directory / (session + ".json")
    if directory.is_symlink() or path.is_symlink():
        raise ValueError("INVALID_SEVERITY_EVIDENCE_PATH")
    return path


def _read(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("SEVERITY_EVIDENCE_TOO_LARGE")
    value = json.loads(raw)
    json.dumps(value, allow_nan=False)
    if not isinstance(value, dict):
        raise ValueError("INVALID_SEVERITY_EVIDENCE")
    levels = value.get("levels")
    if (value.get("protocol") != PROTOCOL
        or not isinstance(levels, list) or len(levels) != len(LEVELS)
        or any(not isinstance(row, dict) for row in levels)
        or [row.get("level") for row in levels] != list(LEVELS)
        or type(value.get("baseline_changed")) is not bool
        or not 0 < value["started_ts"] < value["deadline_ts"]
        or value["deadline_ts"] - value["started_ts"] != DURATION_SECONDS):
        raise ValueError("INVALID_SEVERITY_EVIDENCE")
    if (not isinstance(value.get("parameter_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", value["parameter_sha256"]) is None):
        raise ValueError("INVALID_SEVERITY_BASELINE")
    for row in value["levels"]:
        n = row["evaluations"]
        if type(n) is not int or not 0 <= n <= 100000:
            raise ValueError("INVALID_SEVERITY_COUNTER")
        for key in ("decision_kinds", "blockers", "fsm_reason_families", "accepted_unique_stages"):
            counts = row[key]
            if (not isinstance(counts, dict) or len(counts) > 32
                or any(not isinstance(k, str) or re.fullmatch(r"[A-Z][A-Z0-9_]{0,80}", k) is None
                       or type(v) is not int or not 0 <= v <= n for k, v in counts.items())):
                raise ValueError("INVALID_SEVERITY_COUNTER")
        if (sum(row["decision_kinds"].values()) != n
            or sum(row["fsm_reason_families"].values()) != n
            or set(row["accepted_unique_stages"]) - set(STAGES)
            or type(row["complete_ordered_chains"]) is not int
            or not 0 <= row["complete_ordered_chains"] <= n
            or not isinstance(row["opportunities"], dict) or len(row["opportunities"]) > 128
            or not isinstance(row["stage_gap_samples"], list) or len(row["stage_gap_samples"]) > 32):
            raise ValueError("INCONSISTENT_SEVERITY_EVIDENCE")
        for gaps in row["stage_gap_samples"]:
            if (set(gaps) != {"pre_to_confirm_seconds", "confirm_to_open_seconds", "pre_to_open_seconds"}
                or any(type(x) not in {int, float} or not math.isfinite(x) or x < 0 for x in gaps.values())
                or not math.isclose(gaps["pre_to_open_seconds"], gaps["pre_to_confirm_seconds"] + gaps["confirm_to_open_seconds"])):
                raise ValueError("INVALID_SEVERITY_TIMING_EVIDENCE")
        pairs = row["stage_pair_gap_samples"]
        if (not isinstance(pairs, dict) or set(pairs) != set(PAIRS)
            or any(not isinstance(samples, list) or len(samples) > 32
                   or any(type(x) not in {int, float} or not math.isfinite(x) or not 0 <= x <= DURATION_SECONDS
                          for x in samples) for samples in pairs.values())):
            raise ValueError("INVALID_SEVERITY_PAIR_TIMING")
    return value


def _save(path: Path, value: dict) -> None:
    if len((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()) > MAX_BYTES:
        raise ValueError("SEVERITY_EVIDENCE_TOO_LARGE")
    storage.save_json_atomic(str(path), value)


def _new(params, evaluation, now: float, buffer_mode: str) -> dict:
    return {"protocol": PROTOCOL, "started_ts": now, "deadline_ts": now + DURATION_SECONDS,
            "parameter_sha256": algo_params_sha256(params), "baseline_changed": False,
            "strategy_version": evaluation.strategy_version, "canonical_spec": evaluation.canonical_spec,
            "buffer_mode": buffer_mode,
            "last_evaluation_ts": None, "last_report_slot": -1,
            "levels": [{"level": level, "score_thresholds": score_thresholds(params, level),
                        "evaluations": 0, "decision_kinds": {}, "blockers": {},
                        "fsm_reason_families": {}, "accepted_unique_stages": {},
                        "complete_ordered_chains": 0, "stage_gap_samples": [],
                        "stage_pair_gap_samples": {name: [] for name in PAIRS},
                        "fsm_state": default_fsm_state(), "opportunities": {}}
                       for level in LEVELS]}


def _summary(state: dict, now: float) -> dict:
    return {"protocol": PROTOCOL, "truth_domain": "LIVE_COUNTERFACTUAL_RESEARCH",
            "status": "PAUSED_BASELINE_CHANGED" if state["baseline_changed"] else
                      "COMPLETE" if now >= state["deadline_ts"] else "OBSERVING",
            **{key: state[key] for key in ("started_ts", "deadline_ts", "parameter_sha256",
                                          "baseline_changed", "last_evaluation_ts")},
            "baseline_level": BASELINE_LEVEL, "tested_dimension": "CLASSICAL_SCORE_THRESHOLDS_ONLY",
            "provider": "FINNHUB", "symbol": "EUR/USD", "buffer_mode": state["buffer_mode"],
            "levels": [{key: row[key] for key in (
                "level", "score_thresholds", "evaluations", "decision_kinds", "blockers",
                "fsm_reason_families", "accepted_unique_stages", "complete_ordered_chains", "stage_gap_samples",
                "stage_pair_gap_samples"
            )} for row in state["levels"]],
            "stage_gap_sample_scope": "LAST_32_COMPLETE_RESEARCH_CHAINS_PER_LEVEL",
            "stage_pair_gap_sample_scope": "LAST_32_FIRST_ACCEPTED_STAGE_PAIRS_PER_LEVEL_INCLUDING_INCOMPLETE_CHAINS",
            "actual_telegram_publications": 0, "broker_executed": False,
            "execution_calibration_proven": False, "production_parameters_changed": False,
            "automatic_selection_allowed": False,
            "limitations": ["Independent research FSM histories are not actual production deliveries.",
                            "Score severity leaves all non-score hard gates unchanged.",
                            "No outcome or efficacy is inferred from stage counts."]}


def summary(*, now_ts: float) -> dict | None:
    path = _path()
    state = _read(path) if path is not None else None
    return _summary(state, now_ts) if state is not None else None


def _observe_accepted_stage(row, decision, handoff, now_ts: float) -> None:
    if handoff.stage_handoff_ready and handoff.accepted_stage in STAGES:
        opportunities = row["opportunities"]
        stages = opportunities.setdefault(decision.signal_id, {})
        stage = handoff.accepted_stage
        if stage not in stages:
            stages[stage] = now_ts
            row["accepted_unique_stages"][stage] = row["accepted_unique_stages"].get(stage, 0) + 1
            for name, (before, after) in PAIRS.items():
                if stage == after and before in stages and stages[before] <= now_ts:
                    row["stage_pair_gap_samples"][name] = (
                        row["stage_pair_gap_samples"][name] + [now_ts - stages[before]])[-32:]
            if all(key in stages for key in STAGES) and stages["PRE"] <= stages["CONFIRM"] <= stages["OPEN_NOW"]:
                row["complete_ordered_chains"] += 1
                gaps = {"pre_to_confirm_seconds": stages["CONFIRM"] - stages["PRE"],
                        "confirm_to_open_seconds": stages["OPEN_NOW"] - stages["CONFIRM"],
                        "pre_to_open_seconds": stages["OPEN_NOW"] - stages["PRE"]}
                row["stage_gap_samples"] = (row["stage_gap_samples"] + [gaps])[-32:]
        while len(opportunities) > 128:
            del opportunities[next(iter(opportunities))]


def observe(evaluation: BinaryStrategyV2Evaluation, params: dict, *, now_ts: float, provider: str, buffer_mode: str) -> None:
    path = _path()
    if path is None or provider != "FINNHUB" or evaluation.market.symbol.replace("/", "") != "EURUSD":
        return
    if type(now_ts) not in {int, float} or not math.isfinite(now_ts) or now_ts <= 0:
        raise ValueError("INVALID_SEVERITY_OBSERVATION_TIME")
    if buffer_mode not in {"SMALL", "MEDIUM", "LARGE"}:
        raise ValueError("INVALID_SEVERITY_BUFFER_MODE")
    with storage.with_lock("live_score_severity_research", timeout_sec=0.2):
        loaded = _read(path)
        state = loaded or _new(params, evaluation, now_ts, buffer_mode)
        if now_ts < state["started_ts"] or (
            state["last_evaluation_ts"] is not None and now_ts <= state["last_evaluation_ts"]):
            return
        drift = now_ts < state["deadline_ts"] and (state["parameter_sha256"] != algo_params_sha256(params)
                 or state["strategy_version"] != evaluation.strategy_version
                 or state["canonical_spec"] != evaluation.canonical_spec
                 or state["buffer_mode"] != buffer_mode)
        newly_paused = drift and not state["baseline_changed"]
        if drift:
            state["baseline_changed"] = True
        observed = False
        if not state["baseline_changed"] and now_ts < state["deadline_ts"]:
            for row in state["levels"]:
                variant = {**params, "score_thresholds": row["score_thresholds"]}
                score = evaluate_score(evaluation.market, evaluation.corridor, evaluation.time, variant)
                fsm, _ = fsm_runtime.reconcile_state(row["fsm_state"], int(now_ts), active_symbols=[evaluation.market.symbol])
                decision = assemble_decision(
                    evaluation.market, evaluation.corridor, evaluation.time, score,
                    timeframe=evaluation.decision.setup.timeframe,
                    cycle_id=evaluation.cycle_id, source="live_score_severity_research",
                    opportunity_signal_id=current_opportunity_signal_id(fsm, evaluation.market.symbol))
                handoff = advance_persistent_fsm(fsm, decision, now_ts=int(now_ts))
                row["fsm_state"] = handoff.next_state
                row["evaluations"] += 1
                for key, items in (("decision_kinds", [decision.kind]),
                                   ("blockers", decision.reject.hard_blockers),
                                   ("fsm_reason_families", [handoff.reason_family])):
                    counts = Counter(row[key])
                    counts.update(items)
                    row[key] = dict(counts)
                _observe_accepted_stage(row, decision, handoff, now_ts)
            state["last_evaluation_ts"] = now_ts
            observed = True
        slot = min(8, int((now_ts - state["started_ts"]) // 900))
        report = slot > state["last_report_slot"]
        if loaded is not None and not (observed or newly_paused or report):
            return
        state["last_report_slot"] = max(slot, state["last_report_slot"])
        _save(path, state)
    if report:
        print("TSP_LIVE_SCORE_SEVERITY " + json.dumps(_summary(state, now_ts), sort_keys=True), flush=True)
