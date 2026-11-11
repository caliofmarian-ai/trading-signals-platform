"""Continuous, restart-safe Owner timing monitoring, never parameter promotion.

The module name remains compatible with existing callers. Diagnostic session
identities and reporting intervals cannot limit the signal engine's lifetime.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
from typing import Any

from core import storage


PROTOCOL = "OWNER_TIMING_CONTINUOUS_V2"
REPORT_SECONDS = 15 * 60
MAX_BYTES = 64 * 1024


def _path() -> Path | None:
    from core.owner_signal_delivery import destination
    if destination() is None:
        return None
    from core.physical_params import physical_runtime_enabled
    folder = "owner_timing_physical_v3" if physical_runtime_enabled() else "owner_timing_continuous"
    if physical_runtime_enabled():
        from core.market_history_policy import HISTORY_POLICY
        params = storage.load_json(storage.config_path("algo_params.json"), default={})
        if params.get("history_policy") == HISTORY_POLICY:
            folder = "owner_timing_physical_v3_recent_history"
    path = Path(storage.root_path("analytics", folder, "state.json"))
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("INVALID_TIMING_SOURCE")
    return path


def _read(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        if path.parent.name in {"owner_timing_physical_v3", "owner_timing_physical_v3_recent_history"}:
            return None
        session = os.getenv("OWNER_TIMING_SESSION_ID", "")
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", session) is None:
            return None
        legacy = Path(storage.root_path("analytics", "owner_timing_sessions", session + ".json"))
        if not legacy.exists():
            return None
        path = legacy
    if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
        raise ValueError("INVALID_SESSION_SOURCE")
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("SESSION_SOURCE_TOO_LARGE")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("INVALID_SESSION_STATE")
    if result.get("protocol") == "OWNER_TIMING_SESSION_V1":
        if result.get("deadline_ts", 0) - result.get("started_ts", 0) != 7200:
            raise ValueError("INVALID_LEGACY_TIMING_STATE")
        result.update(protocol=PROTOCOL, deadline_ts=None, operating_mode="CONTINUOUS", last_report_slot=-1)
        result["continued_from_protocol"] = "OWNER_TIMING_SESSION_V1"
    if (result.get("protocol") != PROTOCOL or result.get("deadline_ts") is not None
        or result.get("operating_mode") != "CONTINUOUS"):
        raise ValueError("INVALID_CONTINUOUS_TIMING_STATE")
    return result


def _new(now_ts: float, parameter_sha256: str) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL, "operating_mode": "CONTINUOUS", "started_ts": now_ts,
        "deadline_ts": None, "evaluations": 0,
        "decision_kinds": {}, "blockers": {}, "fsm_accepted_stage_evaluations": {},
        "private_published_stages": {}, "execution_expiry_available": 0,
        "api_request_seconds": [], "last_report_slot": -1,
        "last_evaluation_ts": None, "last_publication_ts": None,
        "parameter_sha256": parameter_sha256, "baseline_changed": False,
        "activity_gate_model": "NORMALIZED_M1_RANGE_OVER_M5_ATR14_020",
    }


def observe_evaluation(decision, handoff, execution_time, *, now_ts: float, parameter_sha256: str) -> None:
    path = _path()
    if path is None:
        return
    with storage.with_lock("owner_timing_session"):
        state = _read(path) or _new(now_ts, parameter_sha256)
        if getattr(decision, "fsm_inputs", {}).get("decision_policy") == "PHYSICAL_ONLY_V3":
            state["decision_policy"] = "PHYSICAL_ONLY_V3"
        if now_ts < state["started_ts"] or (state["last_evaluation_ts"] is not None
                                          and now_ts <= state["last_evaluation_ts"]):
            return
        if state["parameter_sha256"] != parameter_sha256:
            state["baseline_changed"] = True
            storage.save_json_atomic(str(path), state)
            return
        if state["baseline_changed"]:
            return
        state["evaluations"] += 1
        kinds = Counter(state["decision_kinds"])
        kinds[decision.kind] += 1
        state["decision_kinds"] = dict(kinds)
        blockers = Counter(state["blockers"])
        blockers.update(decision.reject.hard_blockers)
        state["blockers"] = dict(blockers)
        if handoff.stage_handoff_ready:
            stages = Counter(state["fsm_accepted_stage_evaluations"])
            stages[handoff.accepted_stage] += 1
            state["fsm_accepted_stage_evaluations"] = dict(stages)
        state["execution_expiry_available"] += int(execution_time.available)
        state["last_evaluation_ts"] = now_ts
        if decision.kind in {"PRE", "CONFIRM", "OPEN_NOW"} and not getattr(handoff, "stage_handoff_ready", False):
            reason = getattr(handoff, "reason", "OTHER")
            if reason not in {"cooldown_active", "watchlist_full", "DUPLICATE_STAGE_CANDLE",
                "SIGNAL_ID_CONTINUITY_REQUIRED", "PHYSICAL_LIFECYCLE_ORDER_REQUIRED", "CANONICAL_PRE_PATH_REQUIRED"}:
                reason = "OTHER"
            reasons = Counter(state.get("fsm_non_handoff_reasons", {}))
            reasons[reason] += 1
            state["fsm_non_handoff_reasons"] = dict(reasons)
        storage.save_json_atomic(str(path), state)


def observe_receipt(evidence: dict[str, Any], *, now_ts: float) -> None:
    path = _path()
    if path is None:
        return
    with storage.with_lock("owner_timing_session"):
        state = _read(path)
        if state is None or state["baseline_changed"] or now_ts < state["started_ts"]:
            return
        stages = Counter(state["private_published_stages"])
        stages[evidence["stage"]] += 1
        state["private_published_stages"] = dict(stages)
        # Bounded transport samples; the totals above are not truncated.
        state["api_request_seconds"] = (state["api_request_seconds"] + [evidence["api_request_seconds"]])[-512:]
        state["last_publication_ts"] = now_ts
        storage.save_json_atomic(str(path), state)


def _summary(state: dict[str, Any], now_ts: float) -> dict[str, Any]:
    samples = state["api_request_seconds"]
    if (not isinstance(samples, list) or len(samples) > 512
        or any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value) or value < 0 for value in samples)):
        raise ValueError("INVALID_TIMING_SAMPLES")
    times = sorted(samples)
    # Use one empirical nearest-rank convention for both percentiles. The
    # previous mixed indexes could put p95 below p50 with two observations,
    # and understate the observed tail for small samples.
    def percentile(fraction: float) -> float | None:
        return times[math.ceil(fraction * len(times)) - 1] if times else None

    return {
        **{k: state[k] for k in ("protocol", "started_ts", "deadline_ts", "evaluations",
                                "decision_kinds", "blockers", "fsm_accepted_stage_evaluations",
                                "private_published_stages", "execution_expiry_available",
                                "last_evaluation_ts", "last_publication_ts", "parameter_sha256",
                                "baseline_changed", "activity_gate_model")},
        **({"decision_policy": state["decision_policy"]} if "decision_policy" in state else {}),
        "fsm_non_handoff_reasons": state.get("fsm_non_handoff_reasons", {}),
        "status": "PAUSED_BASELINE_CHANGED" if state["baseline_changed"] else "OBSERVING",
        "operating_mode": "CONTINUOUS", "automatic_stop_at": None,
        "api_timing_sample_count": len(times),
        "api_timing_percentile_method": "NEAREST_RANK",
        "api_timing_sample_scope": "LAST_512_SUCCESSFUL_PRIVATE_DELIVERIES",
        "api_request_p50_seconds": percentile(.50),
        "api_request_p95_seconds": percentile(.95),
        "execution_calibration_proven": False, "parameters_changed": False,
        "broker_executed": False, "phone_receipt_proven": False,
    }


def summary(*, now_ts: float) -> dict[str, Any] | None:
    path = _path()
    if path is None:
        return None
    state = _read(path)
    return _summary(state, now_ts) if state is not None else None


def report_if_due(*, now_ts: float) -> dict[str, Any] | None:
    path = _path()
    if path is None:
        return None
    with storage.with_lock("owner_timing_session"):
        state = _read(path)
        if state is None or now_ts < state["started_ts"]:
            return None
        slot = int((now_ts - state["started_ts"]) // REPORT_SECONDS)
        if slot <= state["last_report_slot"]:
            return None
        # Reserve before transport. A restart cannot repeatedly send the same
        # progress slot; a failed notification is not signal publication.
        state["last_report_slot"] = slot
        storage.save_json_atomic(str(path), state)
        report = _summary(state, now_ts)
    from core import telegram_publisher
    from core.owner_signal_delivery import destination
    counts = report["private_published_stages"]
    text = ("Continuous signal monitoring"
            + "\nRunning since: " + datetime.fromtimestamp(report["started_ts"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            + f"\nReal evaluations: {report['evaluations']}"
            + f"\nPrivate deliveries: PRE {counts.get('PRE', 0)}, CONFIRM {counts.get('CONFIRM', 0)}, OPEN_NOW {counts.get('OPEN_NOW', 0)}"
            + "\nExecution-expiry calibration remains unproven. No automatic parameter change.")
    if report["baseline_changed"]:
        text += "\nObservation paused after a parameter change; samples were not mixed."
    from core.physical_params import physical_runtime_enabled
    if physical_runtime_enabled():
        try:
            from intelligence import physical_expiry_calibration
            observed = physical_expiry_calibration.summary(now_ts=now_ts)
            report["physical_study_progress"] = {key: observed.get(key) for key in
                ("unique_entry_experiments", "finalized_entry_experiments",
                 "study_open_now_api_accepted", "study_results_api_accepted")}
            if "prospective_cohort" in observed:
                report["physical_study_cohort"] = observed["prospective_cohort"]
                historical = observed["historical_delivery_counts"]
                report["historical_physical_study_deliveries"] = historical
                text += ("\nCohorta prospectivă V3 după corectarea spațiului direcțional."
                         f" Cohorta anterioară: {historical['study_open_now_api_accepted']} OPEN STUDIU,"
                         f" {historical['study_results_api_accepted']} rezultate acceptate de API.")
            from core import confirmed_study_duration as durations
            from intelligence.study_progress_presentation import render_published_study_progress
            report["study_results_by_duration_policy"] = observed.get("published_study_results_by_duration_policy")
            report["study_results_by_quote_recovery_policy"] = observed.get("published_study_results_by_quote_recovery_policy")
            report["study_expiry_estimates"] = observed.get("published_study_expiry_estimates")
            # Published results only: never substitute independent calibration
            # observations, omit draws or label historical totals current.
            text += "\n" + render_published_study_progress(
                observed, active_policy=durations.POLICY,
                legacy_policy=durations.LEGACY_POLICY,
                legacy_open_policy=durations.LEGACY_OPEN_POLICY,
                recovery_policy=physical_expiry_calibration.QUOTE_RECOVERY_POLICY,
                legacy_recovery_policy=physical_expiry_calibration.LEGACY_QUOTE_RECOVERY_POLICY,
            )
        except Exception:
            text += "\nStudy progress is temporarily unavailable."
    result = telegram_publisher.send_message(chat_id=destination(), text=text)
    report["notification_api_accepted"] = result.get("ok") is True
    print("TSP_OWNER_TIMING_SESSION " + json.dumps(report, sort_keys=True), flush=True)
    return report
