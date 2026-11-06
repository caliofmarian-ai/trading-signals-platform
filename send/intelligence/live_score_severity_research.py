"""Continuous, restart-safe paper observation at severities 0..20.

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
from intelligence import model_time_paper_trades as paper
from state_store.state_store import default_fsm_state


PROTOCOL = "LIVE_SCORE_SEVERITY_CONTINUOUS_V3"
LEGACY_PROTOCOL = "LIVE_SCORE_SEVERITY_RESEARCH_V2"
MAX_BYTES = 4 * 1024 * 1024
REPORT_SECONDS = 60
MIN_PRE_LEAD_SECONDS = 30
STAGES = ("PRE", "CONFIRM", "OPEN_NOW")
PAIRS = {"pre_to_confirm_seconds": ("PRE", "CONFIRM"),
         "confirm_to_open_seconds": ("CONFIRM", "OPEN_NOW"),
         "pre_to_open_seconds": ("PRE", "OPEN_NOW")}


def _path() -> Path | None:
    from core.owner_signal_delivery import destination
    if (destination() is None
        or os.getenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "").lower() not in {"true", "1", "yes", "on"}):
        return None
    # A stable runtime identity: restarting or renaming a diagnostic session
    # cannot stop collection, reset the FSM or forget an outstanding expiry.
    directory = Path(storage.root_path("analytics", "live_score_severity_continuous"))
    path = directory / "state.json"
    if directory.is_symlink() or path.is_symlink():
        raise ValueError("INVALID_SEVERITY_EVIDENCE_PATH")
    return path


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
        raise ValueError("INVALID_SEVERITY_EVIDENCE_PATH")
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("SEVERITY_EVIDENCE_TOO_LARGE")
    value = json.loads(raw)
    json.dumps(value, allow_nan=False)
    if not isinstance(value, dict):
        raise ValueError("INVALID_SEVERITY_EVIDENCE")
    return value


def _archived_new() -> dict:
    return {"batches": 0, "registered": 0, "outcomes": {key: 0 for key in paper.OUTCOMES}}


def _read(path: Path) -> dict | None:
    value = _load(path)
    if value is None:
        # One-time continuation of the installed V2 state, including pending
        # trades and exact-stage FSM history. The original file is never edited.
        session = os.getenv("OWNER_TIMING_SESSION_ID", "")
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", session):
            legacy = Path(storage.root_path("analytics", "live_score_severity_research_v2", session + ".json"))
            value = _load(legacy)
            if value is not None:
                if (value.get("protocol") != LEGACY_PROTOCOL
                    or value.get("deadline_ts", 0) - value.get("started_ts", 0) != 7200):
                    raise ValueError("INVALID_LEGACY_SEVERITY_EVIDENCE")
                value.update(protocol=PROTOCOL, deadline_ts=None, operating_mode="CONTINUOUS", last_report_slot=-1)
                value["continued_from_protocol"] = LEGACY_PROTOCOL
                for row in value.get("levels", []):
                    row["archived_paper"] = _archived_new()
    if value is None:
        return None
    levels = value.get("levels")
    if (value.get("protocol") != PROTOCOL or value.get("operating_mode") != "CONTINUOUS"
        or not isinstance(levels, list) or len(levels) != len(LEVELS)
        or any(not isinstance(row, dict) for row in levels)
        or [row.get("level") for row in levels] != list(LEVELS)
        or type(value.get("baseline_changed")) is not bool
        or type(value.get("started_ts")) not in {int, float}
        or not math.isfinite(value["started_ts"]) or value["started_ts"] <= 0
        or value.get("deadline_ts") is not None):
        raise ValueError("INVALID_SEVERITY_EVIDENCE")
    if (not isinstance(value.get("parameter_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", value["parameter_sha256"]) is None):
        raise ValueError("INVALID_SEVERITY_BASELINE")
    for row in value["levels"]:
        paper.validate(row["paper_trades"])
        n = row["evaluations"]
        if type(n) is not int or not 0 <= n < 2**53:
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
                   or any(type(x) not in {int, float} or not math.isfinite(x) or x < 0
                          for x in samples) for samples in pairs.values())):
            raise ValueError("INVALID_SEVERITY_PAIR_TIMING")
        archived = row.get("archived_paper")
        if (not isinstance(archived, dict) or set(archived) != {"batches", "registered", "outcomes"}
            or any(type(archived[key]) is not int or archived[key] < 0 for key in ("batches", "registered"))
            or not isinstance(archived["outcomes"], dict) or set(archived["outcomes"]) != set(paper.OUTCOMES)
            or any(type(n) is not int or n < 0 for n in archived["outcomes"].values())
            or sum(archived["outcomes"].values()) != archived["registered"]):
            raise ValueError("INVALID_ARCHIVED_PAPER_TOTALS")
        _recover_archive(path, row)
    return value


def _archive_path(path: Path, row: dict) -> Path:
    directory = path.parent / "finalized" / f"level-{row['level']:02d}"
    target = directory / f"{row['archived_paper']['batches'] + 1:012d}.json"
    if any(part.is_symlink() for part in (path.parent, directory.parent, directory, target)):
        raise ValueError("INVALID_PAPER_ARCHIVE_PATH")
    return target


def _recover_archive(path: Path, row: dict) -> None:
    """Recover a durable archive whose following state save was interrupted."""
    archive = _load(_archive_path(path, row))
    if archive is None:
        return
    ledger = archive.get("ledger")
    paper.validate(ledger)
    if (archive.get("protocol") != "CONTINUOUS_PAPER_ARCHIVE_V1"
        or archive.get("level") != row["level"] or archive.get("previous_totals") != row["archived_paper"]
        or not ledger["trades"] or any(t["state"] != "FINAL" for t in ledger["trades"].values())
        or any(row["paper_trades"]["trades"].get(key) != trade for key, trade in ledger["trades"].items())):
        raise ValueError("PAPER_ARCHIVE_CHECKPOINT_MISMATCH")
    for key, trade in ledger["trades"].items():
        del row["paper_trades"]["trades"][key]
        row["archived_paper"]["registered"] += 1
        row["archived_paper"]["outcomes"][trade["outcome"]] += 1
    row["archived_paper"]["batches"] += 1


def _archive_finalized(path: Path, state: dict) -> None:
    # Bounded hot state must not become a lifetime limit of 64 opportunities.
    # Only FINAL records move; pending expiries and FSM state stay in place.
    for row in state["levels"]:
        ledger = row["paper_trades"]
        final = {key: trade for key, trade in ledger["trades"].items() if trade["state"] == "FINAL"}
        if not final or (len(final) < max(1, paper.MAX_TRADES // 2) and len(ledger["trades"]) < paper.MAX_TRADES):
            continue
        archive = {"protocol": "CONTINUOUS_PAPER_ARCHIVE_V1", "level": row["level"],
                   "previous_totals": row["archived_paper"], "parameter_sha256": state["parameter_sha256"],
                   "strategy_version": state["strategy_version"], "canonical_spec": state["canonical_spec"],
                   "buffer_mode": state["buffer_mode"],
                   "ledger": {"protocol": paper.PROTOCOL, "trades": final, "capacity_rejections": 0}}
        storage.save_json_atomic(str(_archive_path(path, row)), archive)
        _recover_archive(path, row)


def _paper_summary(row: dict) -> dict:
    result = paper.summary(row["paper_trades"])
    result["registered"] += row["archived_paper"]["registered"]
    for key, count in row["archived_paper"]["outcomes"].items():
        result["outcomes"][key] += count
    result["decisive_sample"] = result["outcomes"]["WIN"] + result["outcomes"]["LOSS"]
    result["hypothetical_win_rate_percent"] = (100 * result["outcomes"]["WIN"] / result["decisive_sample"]
                                              if result["decisive_sample"] else None)
    result["archived_registered"] = row["archived_paper"]["registered"]
    result["horizon_seconds_counts_scope"] = "UNARCHIVED_TRADES_ONLY; EXACT_OLDER_HORIZONS_RETAINED_IN_ARCHIVES"
    return result


def _save(path: Path, value: dict) -> None:
    if len((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()) > MAX_BYTES:
        raise ValueError("SEVERITY_EVIDENCE_TOO_LARGE")
    storage.save_json_atomic(str(path), value)


def _new(params, evaluation, now: float, buffer_mode: str) -> dict:
    return {"protocol": PROTOCOL, "operating_mode": "CONTINUOUS", "started_ts": now, "deadline_ts": None,
            "parameter_sha256": algo_params_sha256(params), "baseline_changed": False,
            "strategy_version": evaluation.strategy_version, "canonical_spec": evaluation.canonical_spec,
            "buffer_mode": buffer_mode,
            "last_evaluation_ts": None, "last_report_slot": -1,
            "levels": [{"level": level, "score_thresholds": score_thresholds(params, level),
                        "evaluations": 0, "decision_kinds": {}, "blockers": {},
                        "fsm_reason_families": {}, "accepted_unique_stages": {},
                        "complete_ordered_chains": 0, "stage_gap_samples": [],
                        "stage_pair_gap_samples": {name: [] for name in PAIRS},
                        "paper_trades": paper.new_ledger(), "archived_paper": _archived_new(),
                        "fsm_state": default_fsm_state(), "opportunities": {}}
                       for level in LEVELS]}


def _summary(state: dict, now: float) -> dict:
    return {"protocol": PROTOCOL, "truth_domain": "LIVE_COUNTERFACTUAL_RESEARCH",
            "status": "PAUSED_BASELINE_CHANGED" if state["baseline_changed"] else "OBSERVING",
            "operating_mode": "CONTINUOUS", "automatic_stop_at": None,
            **{key: state[key] for key in ("started_ts", "deadline_ts", "parameter_sha256",
                                          "baseline_changed", "last_evaluation_ts")},
            "baseline_level": BASELINE_LEVEL, "tested_dimension": "CLASSICAL_SCORE_THRESHOLDS_ONLY",
            "stage_request_policy": "SCORE_CEILING_THEN_PRE_CONFIRM_OPEN_WITH_30S_PRE_LEAD",
            "outcome_observation_policy": "PROSPECTIVE_MARKET_TICKS_AT_CANONICAL_MODEL_TIME",
            "provider": "FINNHUB", "symbol": "EUR/USD", "buffer_mode": state["buffer_mode"],
            "levels": [{**{key: row[key] for key in (
                "level", "score_thresholds", "evaluations", "decision_kinds", "blockers",
                "fsm_reason_families", "accepted_unique_stages", "complete_ordered_chains", "stage_gap_samples",
                "stage_pair_gap_samples"
            )}, "paper_trades": _paper_summary(row)} for row in state["levels"]],
            "stage_gap_sample_scope": "LAST_32_COMPLETE_RESEARCH_CHAINS_PER_LEVEL",
            "stage_pair_gap_sample_scope": "LAST_32_FIRST_ACCEPTED_STAGE_PAIRS_PER_LEVEL_INCLUDING_INCOMPLETE_CHAINS",
            "actual_telegram_publications": 0, "broker_executed": False,
            "execution_calibration_proven": False, "production_parameters_changed": False,
            "automatic_selection_allowed": False,
            "limitations": ["Independent research FSM histories are not actual production deliveries.",
                            "Score severity leaves all non-score hard gates unchanged.",
                            "Paper results use real market ticks and Model Time, not calibrated Execution Time.",
                            "Stage counts alone do not establish efficacy; paired levels share correlated observations."]}


def summary(*, now_ts: float) -> dict | None:
    path = _path()
    state = _read(path) if path is not None else None
    return _summary(state, now_ts) if state is not None else None


def _observe_accepted_stage(row, decision, handoff, now_ts: float) -> dict | None:
    calibration_entry = None
    if handoff.stage_handoff_ready and handoff.accepted_stage in STAGES:
        opportunities = row["opportunities"]
        stages = opportunities.setdefault(decision.signal_id, {"direction": decision.setup.direction})
        stage = handoff.accepted_stage
        if stage not in stages:
            stages[stage] = now_ts
            model = decision.time.model_expiry
            if type(model) in {int, float} and math.isfinite(model) and model > 0:
                stages.setdefault("model_time_by_stage", {})[stage] = model * 60
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
                if stage == "OPEN_NOW" and stages["direction"] == decision.setup.direction:
                    if paper.register(row["paper_trades"], decision, handoff, now_ts=now_ts):
                        calibration_entry = {"level":row["level"], "direction":decision.setup.direction,
                            "created_ts":now_ts, "pre_ts":stages["PRE"], "confirm_ts":stages["CONFIRM"],
                            "open_ts":stages["OPEN_NOW"], "model_seconds":model * 60,
                            "adjusted_seconds":decision.time.t_needed_adjusted * 60,
                            "confirm_model_seconds":stages.get("model_time_by_stage", {}).get("CONFIRM"),
                            "buffer_distance":decision.market_context.buffer_distance,
                            "open_decision_id":decision.decision_id,
                            "open_decision_audit_id":decision.decision_audit_id}
        while len(opportunities) > 128:
            del opportunities[next(iter(opportunities))]
    return calibration_entry


def _maximum_stage(row: dict, fsm: dict, symbol: str, now_ts: float, direction: str) -> str:
    """Request a scored stage in order; the canonical FSM still accepts it.

    Score thresholds are eligibility floors, not an instruction to skip PRE
    when the first observation already exceeds the OPEN threshold. All levels
    use the same prospective policy. Production callers keep their defaults.
    """
    identity = current_opportunity_signal_id(fsm, symbol)
    stages = row["opportunities"].get(identity, {})
    symbol_state = (fsm.get("per_symbol") or {}).get(symbol, {})
    if (symbol_state.get("state") not in {"WATCHLIST", "CONFIRMED"} or "PRE" not in stages
        or stages.get("direction") != direction):
        return "PRE"
    if "CONFIRM" not in stages or now_ts < stages["PRE"] + MIN_PRE_LEAD_SECONDS:
        return "CONFIRM"
    return "OPEN_NOW"


def advance_paper_trades(*, now_ts: float, active_provider: str, price_loader) -> dict | None:
    """Continuously settle pending ideas, including recovery after restart."""
    path = _path()
    if path is None:
        return None
    if type(now_ts) not in {int, float} or not math.isfinite(now_ts) or now_ts <= 0:
        raise ValueError("INVALID_PAPER_OBSERVATION_TIME")
    with storage.with_lock("live_score_severity_research", timeout_sec=0.2):
        state = _read(path)
        if state is None or not any(paper.pending(row["paper_trades"]) for row in state["levels"]):
            return None
        sample = None
        if active_provider == "FINNHUB":
            try:
                sample = price_loader("EUR/USD")
            except Exception:
                pass  # A missed observation becomes UNKNOWN at its deadline.
        _archive_finalized(path, state)
        changed = False
        for row in state["levels"]:
            changed = paper.advance(row["paper_trades"], sample, now_ts=now_ts,
                                    active_provider=active_provider) or changed
        if not changed:
            return None
        _save(path, state)
        report = _summary(state, now_ts)
    print("TSP_LIVE_SCORE_PAPER_TRADES " + json.dumps(report, sort_keys=True), flush=True)
    return report


def observe(evaluation: BinaryStrategyV2Evaluation, params: dict, *, now_ts: float, provider: str, buffer_mode: str) -> None:
    path = _path()
    if path is None or provider != "FINNHUB" or evaluation.market.symbol.replace("/", "") != "EURUSD":
        return
    if type(now_ts) not in {int, float} or not math.isfinite(now_ts) or now_ts <= 0:
        raise ValueError("INVALID_SEVERITY_OBSERVATION_TIME")
    if buffer_mode not in {"SMALL", "MEDIUM", "LARGE"}:
        raise ValueError("INVALID_SEVERITY_BUFFER_MODE")
    calibration_entries = []
    with storage.with_lock("live_score_severity_research", timeout_sec=0.2):
        loaded = _read(path)
        state = loaded or _new(params, evaluation, now_ts, buffer_mode)
        if now_ts < state["started_ts"] or (
            state["last_evaluation_ts"] is not None and now_ts <= state["last_evaluation_ts"]):
            return
        _archive_finalized(path, state)
        drift = (state["parameter_sha256"] != algo_params_sha256(params)
                 or state["strategy_version"] != evaluation.strategy_version
                 or state["canonical_spec"] != evaluation.canonical_spec
                 or state["buffer_mode"] != buffer_mode)
        newly_paused = drift and not state["baseline_changed"]
        if drift:
            state["baseline_changed"] = True
        observed = False
        if not state["baseline_changed"]:
            for row in state["levels"]:
                variant = {**params, "score_thresholds": row["score_thresholds"]}
                score = evaluate_score(evaluation.market, evaluation.corridor, evaluation.time, variant)
                fsm, _ = fsm_runtime.reconcile_state(row["fsm_state"], int(now_ts), active_symbols=[evaluation.market.symbol])
                decision = assemble_decision(
                    evaluation.market, evaluation.corridor, evaluation.time, score,
                    timeframe=evaluation.decision.setup.timeframe,
                    cycle_id=evaluation.cycle_id, source="live_score_severity_research",
                    opportunity_signal_id=current_opportunity_signal_id(fsm, evaluation.market.symbol),
                    maximum_stage=_maximum_stage(row, fsm, evaluation.market.symbol, now_ts,
                                                 evaluation.market.direction_bias))
                handoff = advance_persistent_fsm(fsm, decision, now_ts=int(now_ts))
                row["fsm_state"] = handoff.next_state
                row["evaluations"] += 1
                for key, items in (("decision_kinds", [decision.kind]),
                                   ("blockers", decision.reject.hard_blockers),
                                   ("fsm_reason_families", [handoff.reason_family])):
                    counts = Counter(row[key])
                    counts.update(items)
                    row[key] = dict(counts)
                calibration_entry = _observe_accepted_stage(row, decision, handoff, now_ts)
                if calibration_entry is not None:
                    calibration_entries.append(calibration_entry)
            state["last_evaluation_ts"] = now_ts
            observed = True
        slot = int((now_ts - state["started_ts"]) // REPORT_SECONDS)
        report = slot > state["last_report_slot"]
        if loaded is not None and not (observed or newly_paused or report):
            return
        state["last_report_slot"] = max(slot, state["last_report_slot"])
        _save(path, state)
    if report:
        print("TSP_LIVE_SCORE_SEVERITY " + json.dumps(_summary(state, now_ts), sort_keys=True), flush=True)
    if calibration_entries:
        from intelligence import execution_expiry_calibration
        execution_expiry_calibration.capture(calibration_entries, params=params, buffer_mode=buffer_mode,
            strategy_version=evaluation.strategy_version, canonical_spec=evaluation.canonical_spec, now_ts=now_ts)
