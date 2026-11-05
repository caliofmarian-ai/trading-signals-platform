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
    path = Path(storage.root_path("analytics", "owner_timing_continuous", "state.json"))
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("INVALID_TIMING_SOURCE")
    return path


def _read(path: Path) -> dict[str, Any] | None:
    if not path.exists():
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
    result = telegram_publisher.send_message(chat_id=destination(), text=text)
    report["notification_api_accepted"] = result.get("ok") is True
    print("TSP_OWNER_TIMING_SESSION " + json.dumps(report, sort_keys=True), flush=True)
    return report
