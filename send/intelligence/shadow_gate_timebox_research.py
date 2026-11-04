"""Owner-requested preliminary gate test with an absolute two-hour deadline."""

from __future__ import annotations

from collections import Counter
import copy
from pathlib import Path

from core import storage
from intelligence import shadow_gate_sweep_research as sweep
from intelligence import shadow_model_time_research as source


PROTOCOL = "SHADOW_GATE_TIMEBOX_V1"
RUN_ID = "20261104T160500Z"
REQUEST_STARTED_AT = 1793808300.0  # Owner resumed the request: 2026-11-04T16:05:00Z
DEADLINE = 1793815500.0  # 2026-11-04T18:05:00Z, including setup time
REPORT_INTERVAL_SECONDS = 60.0
GAP_REASONS = {"ENTRY_OBSERVATION_MISSING", "EXPIRY_OBSERVATION_MISSING",
               "PROVIDER_CHANGED", "RESTART_MISSED_OBSERVATION"}
KINDS = {"PRE", "CONFIRM", "OPEN_NOW", "REJECT", "NO_SIGNAL"}
STAGES = {"PRE", "CONFIRM", "OPEN_NOW"}
FAMILIES = {"DUPLICATE", "IDENTITY", "LIFECYCLE", "STAGE_ACCEPTED",
            "INVALID_TRANSITION", "FSM_TRANSITION", "NON_ACTIONABLE", "COOLDOWN", "FOCUS"}
BLOCKERS = {"MARKET_ACTIVITY_NOT_ACTIVE", "MARKET_NOISE_UNSTABLE", "STRUCTURE_NOT_VALID",
            "TIME_NOT_FEASIBLE", "TRADE_PHYSICS_INSUFFICIENT_SPACE",
            *{"TRADE_PHYSICS_" + state for state in (
                "INVALID_EVIDENCE", "UNAVAILABLE_MISSING_STRUCTURE", "BLOCKED_UNSTABLE_MARKET",
                "UNAVAILABLE_MISSING_ATR", "UNAVAILABLE_MISSING_SPEED", "UNAVAILABLE_MISSING_TIME")}}
FALSE_FLAGS = (*sweep._FALSE_FLAGS, "execution_calibration_proven",
               "broker_quote_equivalence_proven", "authoritative_for_strategy_performance")


def enabled() -> bool:
    return source._on("SHADOW_GATE_TIMEBOX_RESEARCH_ENABLED") and source.enabled()


def _path(name: str) -> Path:
    directory = Path(storage.root_path("analytics", "shadow_gate_timebox_research", RUN_ID))
    if directory.is_symlink() or (directory / name).is_symlink():
        raise ValueError("timebox evidence cannot be symlinked")
    return directory / name


def _load_state() -> dict:
    state = sweep._read(_path("experiment.json"))
    if (set(state) != {"protocol", "request_started_at", "started_at", "deadline",
                       "baseline_signature", "diagnostics"}
        or state["protocol"] != PROTOCOL or state["request_started_at"] != REQUEST_STARTED_AT
        or state["deadline"] != DEADLINE
        or not REQUEST_STARTED_AT <= source._number(state["started_at"]) < DEADLINE
        or (state["baseline_signature"] is not None
            and not sweep._HASH.fullmatch(state["baseline_signature"]))
        or not _valid_diagnostics(state["diagnostics"])):
        raise ValueError("invalid fixed-window ledger; refusing to reset it")
    return state


def _empty_diagnostics() -> dict:
    return {"evaluations": 0, "first_evaluation_ts": None, "last_evaluation_ts": None,
            "decision_kinds": {}, "accepted_stages": {}, "fsm_reason_families": {},
            "blocker_counts": {}, "execution_expiry_available": 0,
            "execution_expiry_unavailable": 0}


def _valid_counts(value, allowed) -> bool:
    return (isinstance(value, dict) and set(value) <= allowed
            and all(type(n) is int and 0 <= n <= 1000000 for n in value.values()))


def _valid_diagnostics(value) -> bool:
    if (not isinstance(value, dict) or set(value) != set(_empty_diagnostics())
        or type(value["evaluations"]) is not int or not 0 <= value["evaluations"] <= 1000000):
        return False
    for field, allowed in (("decision_kinds", KINDS), ("accepted_stages", STAGES),
                           ("fsm_reason_families", FAMILIES), ("blocker_counts", BLOCKERS)):
        if not _valid_counts(value[field], allowed):
            return False
    n = value["evaluations"]
    if sum(value["decision_kinds"].values()) != n or sum(value["fsm_reason_families"].values()) != n:
        return False
    if sum(value["accepted_stages"].values()) > n:
        return False
    for field in ("execution_expiry_available", "execution_expiry_unavailable"):
        if type(value[field]) is not int or not 0 <= value[field] <= n:
            return False
    if value["execution_expiry_available"] + value["execution_expiry_unavailable"] > n:
        return False
    first, last = value["first_evaluation_ts"], value["last_evaluation_ts"]
    return ((first is None and last is None) if n == 0 else
            REQUEST_STARTED_AT <= source._number(first) <= source._number(last) < DEADLINE)


def observe_evaluation(decision, handoff, execution_time, *, now_ts: float) -> None:
    """Persist bounded counters, never a candidate, quote or signal identity."""
    if not enabled() or not REQUEST_STARTED_AT <= now_ts < DEADLINE:
        return
    with storage.with_lock("shadow_gate_timebox_research", timeout_sec=0.2):
        if not _path("experiment.json").exists():
            return  # Worker must establish the prospective boundary first.
        state = _load_state()
        if now_ts < state["started_at"] or _path("final.json").exists():
            return
        if decision.kind not in KINDS or handoff.reason_family not in FAMILIES:
            raise ValueError("unrecognized diagnostic classification")
        value = state["diagnostics"]
        value["evaluations"] += 1
        value["first_evaluation_ts"] = value["first_evaluation_ts"] or now_ts
        value["last_evaluation_ts"] = now_ts
        def count(field, key):
            value[field][key] = value[field].get(key, 0) + 1
        count("decision_kinds", decision.kind)
        count("fsm_reason_families", handoff.reason_family)
        if handoff.accepted_stage in STAGES and handoff.stage_handoff_ready:
            count("accepted_stages", handoff.accepted_stage)
        for code in set(decision.reject.hard_blockers):
            if code not in BLOCKERS:
                raise ValueError("unrecognized strategic blocker")
            count("blocker_counts", code)
        if decision.kind in {"CONFIRM", "OPEN_NOW"}:
            value["execution_expiry_available" if execution_time.available
                  else "execution_expiry_unavailable"] += 1
        if not _valid_diagnostics(value):
            raise ValueError("inconsistent diagnostic counters")
        sweep._save(_path("experiment.json"), state)


def _metrics(rows: list[dict], *, detail_limit: int = 0) -> dict:
    metrics = sweep._metrics(rows)
    reasons, pending = Counter(), Counter()
    details = []
    for row in rows:
        if row["state"] != "FINAL":
            pending[row["state"]] += 1
        elif row["outcome"] == "UNKNOWN":
            reason = row.get("outcome_reason")
            if reason not in GAP_REASONS:
                raise ValueError("unrecognized missing-observation cause")
            reasons[reason] += 1
            if len(details) < detail_limit:
                details.append({"reason": reason, "registered_at": row["created_ts"],
                                "finalized_at": row["finalized_ts"]})
    return {**metrics, "missing_observation_causes": dict(reasons),
            "pending_states": dict(pending), "gap_details": details,
            "gap_details_truncated": sum(reasons.values()) > len(details)}


def _valid_metrics(value) -> bool:
    base = set(sweep._metrics([]))
    extra = {"missing_observation_causes", "pending_states", "gap_details", "gap_details_truncated"}
    if not isinstance(value, dict) or set(value) != base | extra:
        return False
    if (not sweep._valid_metrics({k: value[k] for k in base})
        or not _valid_counts(value["missing_observation_causes"], GAP_REASONS)
        or sum(value["missing_observation_causes"].values()) != value["outcomes"]["UNKNOWN"]
        or not _valid_counts(value["pending_states"], {"WAITING_ENTRY", "WAITING_EXPIRY"})
        or sum(value["pending_states"].values()) != value["pending"]):
        return False
    details = value["gap_details"]
    if not isinstance(details, list) or len(details) > min(20, value["outcomes"]["UNKNOWN"]):
        return False
    for item in details:
        if (not isinstance(item, dict) or set(item) != {"reason", "registered_at", "finalized_at"}
            or item["reason"] not in GAP_REASONS
            or not source._number(item["registered_at"]) <= source._number(item["finalized_at"])):
            return False
    return value["gap_details_truncated"] is (value["outcomes"]["UNKNOWN"] > len(details))


def _feed(now: float, price_loader, active_provider: str) -> dict:
    if active_provider != "FINNHUB":
        return {"status": "PROVIDER_CHANGED", "sample_observed_at": None, "age_seconds": None}
    try:
        sample = source._sample(price_loader("EUR/USD"), now)
        if sample is not None:
            return {"status": "FRESH_REAL_SAMPLE", "sample_observed_at": sample["observed_ts"],
                    "age_seconds": now - sample["observed_ts"]}
        return {"status": "SAMPLE_FAILED_FRESHNESS_OR_SOURCE_CHECK", "sample_observed_at": None, "age_seconds": None}
    except Exception:
        return {"status": "CURRENT_SAMPLE_UNAVAILABLE", "sample_observed_at": None, "age_seconds": None}


def update(*, now_ts: float, price_loader, active_provider: str = "FINNHUB") -> dict:
    if not enabled():
        return {"status": "DISABLED"}
    now = source._number(now_ts)
    if now < REQUEST_STARTED_AT:
        return {"status": "BEFORE_REQUEST_WINDOW"}
    with storage.with_lock("shadow_gate_timebox_research", timeout_sec=0.2):
        if _path("final.json").exists():
            final = sweep._read(_path("final.json"))
            if not _valid_report(final) or final["status"] != "TIMEBOX_COMPLETE":
                raise ValueError("invalid final report; refusing to overwrite")
            return final
        if _path("experiment.json").exists():
            state = _load_state()
        elif now >= DEADLINE:
            return {"status": "EXPIRED_BEFORE_ACTIVATION", "protocol": PROTOCOL,
                    "request_started_at": REQUEST_STARTED_AT, "deadline": DEADLINE}
        else:
            state = {"protocol": PROTOCOL, "request_started_at": REQUEST_STARTED_AT,
                     "started_at": now, "deadline": DEADLINE, "baseline_signature": None,
                     "diagnostics": _empty_diagnostics()}
            sweep._save(_path("experiment.json"), state)
        if now < state["started_at"]:
            raise ValueError("clock precedes actual activation")
        cutoff = min(now, DEADLINE)
        excluded = {"before_activation": 0, "after_deadline": 0,
                    "missing_provenance_or_tps": 0, "baseline_changed": 0}
        rows = []
        for original in sorted(source.snapshot_records(), key=lambda r: (r["created_ts"], r["record_id"])):
            row = copy.deepcopy(original)
            if row["created_ts"] < state["started_at"]:
                excluded["before_activation"] += 1
                continue
            if row["created_ts"] >= DEADLINE:
                excluded["after_deadline"] += 1
                continue
            if row["created_ts"] > now or (row["state"] == "FINAL" and row["finalized_ts"] > now):
                raise ValueError("future source evidence")
            features = sweep._features(row)
            if features is None:
                excluded["missing_provenance_or_tps"] += 1
                continue
            signature, tps = features
            state["baseline_signature"] = state["baseline_signature"] or signature
            if signature != state["baseline_signature"]:
                excluded["baseline_changed"] += 1
                continue
            if row["state"] == "FINAL" and row["finalized_ts"] > cutoff:
                row["state"] = "WAITING_EXPIRY" if row.get("entry_sample") and row["entry_sample"]["observed_ts"] <= cutoff else "WAITING_ENTRY"
                row["outcome"], row["finalized_ts"] = None, None
            row["research_tps"] = tps
            rows.append(row)
        common = sweep._nonoverlapping(rows)
        duration = DEADLINE - state["started_at"]
        table = []
        for level in sweep.LEVELS:
            start = state["started_at"] + duration * level / len(sweep.LEVELS)
            end = state["started_at"] + duration * (level + 1) / len(sweep.LEVELS)
            selected = [r for r in rows if r["research_tps"] >= sweep.threshold(level)]
            independent = [r for r in common if r["research_tps"] >= sweep.threshold(level)]
            table.append({"level": level, "minimum_tps": sweep.threshold(level),
                          "paired": _metrics(selected), "common_nonoverlapping": _metrics(independent),
                          "slot_started_at": start, "slot_ends_at": end,
                          "sequential": _metrics([r for r in independent if start <= r["created_ts"] < end])})
        metrics = _metrics(rows, detail_limit=20)
        elapsed = min(21, int((cutoff - state["started_at"]) * 21 / duration))
        level = elapsed if elapsed < 21 else None
        incomplete = metrics["outcomes"]["UNKNOWN"] + metrics["pending"] + sum(excluded[k] for k in ("missing_provenance_or_tps", "baseline_changed"))
        report = {"protocol": PROTOCOL, "truth_domain": "HYPOTHETICAL_RESEARCH",
                  "horizon_source": "UNCALIBRATED_MODEL_TIME", "cohort": "FSM_ACCEPTED_OPEN_ONLY",
                  "status": "TIMEBOX_COMPLETE" if now >= DEADLINE else "RUNNING",
                  "assessment": "PAUSED_BASELINE_CHANGED" if excluded["baseline_changed"] else
                  "INCOMPLETE_EVIDENCE" if incomplete else "NO_ELIGIBLE_OBSERVATIONS" if not rows else "PRELIMINARY_ONLY",
                  "request_started_at": REQUEST_STARTED_AT, "started_at": state["started_at"],
                  "deadline": DEADLINE, "evidence_cutoff_at": cutoff,
                  "active_level": level, "elapsed_slot_count": elapsed,
                  "active_metrics": table[level]["sequential"] if level is not None else _metrics([]),
                  "metrics": metrics, "levels": table, "excluded": excluded,
                  "diagnostics": state["diagnostics"], "feed": _feed(now, price_loader, active_provider),
                  "evidence_complete": bool(rows) and not incomplete,
                  **{flag: False for flag in FALSE_FLAGS}}
        if not _valid_report(report):
            raise ValueError("inconsistent timebox report")
        sweep._save(_path("experiment.json"), state)
        sweep._save(_path("summary.json"), report)
        if now >= DEADLINE:
            sweep._save(_path("final.json"), report)
        return report


def _valid_report(report) -> bool:
    expected = {"protocol", "truth_domain", "horizon_source", "cohort", "status", "assessment",
                "request_started_at", "started_at", "deadline", "evidence_cutoff_at", "active_level",
                "elapsed_slot_count", "active_metrics", "metrics", "levels", "excluded", "diagnostics",
                "feed", "evidence_complete", *FALSE_FLAGS}
    if (not isinstance(report, dict) or set(report) != expected or report["protocol"] != PROTOCOL
        or report["truth_domain"] != "HYPOTHETICAL_RESEARCH" or report["horizon_source"] != "UNCALIBRATED_MODEL_TIME"
        or report["cohort"] != "FSM_ACCEPTED_OPEN_ONLY" or any(report[k] is not False for k in FALSE_FLAGS)
        or report["request_started_at"] != REQUEST_STARTED_AT or report["deadline"] != DEADLINE
        or not REQUEST_STARTED_AT <= source._number(report["started_at"]) <= source._number(report["evidence_cutoff_at"]) <= DEADLINE
        or report["started_at"] >= DEADLINE or not _valid_diagnostics(report["diagnostics"])
        or not _valid_metrics(report["metrics"]) or not _valid_metrics(report["active_metrics"])
        or not isinstance(report["levels"], list) or len(report["levels"]) != 21
        or not _valid_counts(report["excluded"], {"before_activation", "after_deadline", "missing_provenance_or_tps", "baseline_changed"})):
        return False
    duration = DEADLINE - report["started_at"]
    elapsed = min(21, int((report["evidence_cutoff_at"] - report["started_at"]) * 21 / duration))
    level = elapsed if elapsed < 21 else None
    if (report["elapsed_slot_count"] != elapsed or report["active_level"] != level
        or report["status"] != ("TIMEBOX_COMPLETE" if elapsed == 21 else "RUNNING")):
        return False
    for index, row in enumerate(report["levels"]):
        if (not isinstance(row, dict) or set(row) != {"level", "minimum_tps", "paired", "common_nonoverlapping", "slot_started_at", "slot_ends_at", "sequential"}
            or type(row["level"]) is not int or row["level"] != index or row["minimum_tps"] != sweep.threshold(index)
            or row["slot_started_at"] != report["started_at"] + duration * index / 21
            or row["slot_ends_at"] != report["started_at"] + duration * (index + 1) / 21
            or any(not _valid_metrics(row[k]) for k in ("paired", "common_nonoverlapping", "sequential"))):
            return False
    if report["active_metrics"] != (report["levels"][level]["sequential"] if level is not None else _metrics([])):
        return False
    incomplete = report["metrics"]["outcomes"]["UNKNOWN"] + report["metrics"]["pending"] + sum(report["excluded"].get(k, 0) for k in ("missing_provenance_or_tps", "baseline_changed"))
    has_rows = bool(sum(report["metrics"]["outcomes"].values()) + report["metrics"]["pending"])
    assessment = ("PAUSED_BASELINE_CHANGED" if report["excluded"].get("baseline_changed") else
                  "INCOMPLETE_EVIDENCE" if incomplete else "NO_ELIGIBLE_OBSERVATIONS" if not has_rows else "PRELIMINARY_ONLY")
    if report["assessment"] != assessment or report["evidence_complete"] is not (has_rows and not incomplete):
        return False
    feed = report["feed"]
    if not isinstance(feed, dict) or set(feed) != {"status", "sample_observed_at", "age_seconds"}:
        return False
    if feed["status"] == "FRESH_REAL_SAMPLE":
        return (type(feed["age_seconds"]) in {int, float} and 0 <= feed["age_seconds"] <= source.MAX_SAMPLE_AGE_SECONDS
                and source._number(feed["sample_observed_at"]) > 0)
    return (feed["status"] in {"SAMPLE_FAILED_FRESHNESS_OR_SOURCE_CHECK", "CURRENT_SAMPLE_UNAVAILABLE", "PROVIDER_CHANGED"}
            and feed["sample_observed_at"] is None and feed["age_seconds"] is None)


def read_summary_status() -> dict | None:
    try:
        report = sweep._read(_path("summary.json"))
        return report if _valid_report(report) else None
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return None


def evidence_summary(report: dict) -> dict:
    if report.get("status") == "EXPIRED_BEFORE_ACTIVATION":
        return report
    keys = ("protocol", "truth_domain", "horizon_source", "cohort", "status", "assessment",
            "request_started_at", "started_at", "deadline", "evidence_cutoff_at", "active_level",
            "elapsed_slot_count", "active_metrics", "metrics", "excluded", "diagnostics", "feed",
            "evidence_complete", *FALSE_FLAGS)
    return {**{k: report[k] for k in keys}, "levels": [
        {"level": row["level"], "minimum_tps": row["minimum_tps"],
         **{k: row["paired"][k] for k in ("outcomes", "pending", "decisive_sample", "hypothetical_win_rate_percent")}}
        for row in report["levels"]]}
