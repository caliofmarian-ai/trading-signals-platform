"""Bounded observation of V3 lifecycle failures; never an execution authority."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import time

from core import owner_signal_delivery as owner, storage
from core.market_history_policy import HISTORY_POLICY
from core.runtime_execution_calibration import algo_params_sha256
from intelligence import shadow_model_time_research as research

PROTOCOL = "PHYSICAL_V3_OPPORTUNITY_TRACE_V1"
MAX_RECORDS = 32
MAX_BYTES = 256 * 1024
_last_report = {}


def _number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def _path(parameter_hash):
    path = Path(storage.root_path("analytics", "physical_v3_opportunity_trace", parameter_hash + ".json"))
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("INVALID_TRACE_PATH")
    return path


def _read(path, parameter_hash):
    if not path.exists():
        return {"protocol": PROTOCOL, "parameter_sha256": parameter_hash,
                "history_policy": HISTORY_POLICY, "records": {}, "event_totals": {},
                "exit_blockers": {}, "exit_noise_reasons": {}, "exit_structure_conflicts": {}}
    if not path.is_file() or path.is_symlink():
        raise ValueError("INVALID_TRACE_PATH")
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("TRACE_SIZE_LIMIT")
    state = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_TRACE")))
    if (not isinstance(state, dict) or state.get("protocol") != PROTOCOL or state.get("parameter_sha256") != parameter_hash
        or state.get("history_policy") != HISTORY_POLICY
        or not isinstance(state.get("records"), dict) or len(state["records"]) > MAX_RECORDS):
        raise ValueError("INVALID_TRACE_SCOPE")
    return state


def _snapshot(evaluation, handoff, decision_ts, observed_at, signal_id):
    decision = evaluation.decision
    indicators = evaluation.market.evidence
    pre_api = owner.pre_receipt_ts(signal_id)
    pre_available = pre_api is not None and pre_api <= decision_ts
    row = handoff.next_state["per_symbol"][decision.setup.symbol]
    buffer = _number(decision.market_context.buffer_distance)
    distance = _number(decision.structure.available_distance)
    return {"decision_ts": decision_ts, "observed_at": observed_at,
            "candle_ts": decision.setup.evaluated_ts,
            "evaluation_candle_age_seconds": decision_ts - decision.setup.evaluated_ts,
            "decision_kind": decision.kind, "direction": decision.setup.direction,
            "fsm_prior_state": handoff.prior_state, "fsm_resulting_state": handoff.resulting_state,
            "fsm_reason": handoff.reason, "physical_pre_ts": _number(row.get("physical_pre_ts")),
            "pre_api_accepted_ts": pre_api, "pre_receipt_available_at_evaluation": pre_available,
            "pre_api_age_seconds": decision_ts - pre_api if pre_available else None,
            "remaining_pre_lead_seconds": max(0., 30 - (decision_ts - pre_api)) if pre_available else None,
            "cooldown_remaining_seconds": max(0., row["cooldown_until_ts"] - decision_ts)
                if _number(row.get("cooldown_until_ts")) is not None else 0.,
            "hard_blockers": list(decision.reject.hard_blockers),
            "noise_reasons": list(evaluation.market.noise_reasons),
            "structure_state": decision.structure.feasibility_state,
            "structure_conflicts": list(decision.structure.conflicts),
            "room_over_buffer": _number(distance / buffer) if distance is not None and buffer and buffer > 0 else None,
            "time_state": decision.time.time_state,
            "model_minutes": _number(decision.time.model_expiry),
            "needed_adjusted_minutes": _number(decision.time.t_needed_adjusted),
            "trend_context": decision.market_context.trend_context,
            "activity_state": decision.market_context.volatility_state,
            "noise_state": decision.market_context.noise_context,
            **{key: _number(getattr(indicators, source, None)) for key, source in
               (("wick_body_ratio", "wick_body_ratio"), ("range_deviation_sigma", "range_z_score"),
                ("jump_vs_atr", "jump_vs_atr"), ("activity_ratio", "activity_ratio"))}}


def observe(evaluation, handoff, params, *, decision_ts, provider, observed_at=None):
    if (params.get("decision_policy") != "PHYSICAL_ONLY_V3" or provider != "FINNHUB"
        or owner.destination() is None or not research.enabled()):
        return
    now = time.time() if observed_at is None else observed_at
    if (_number(now) is None or _number(decision_ts) is None or not 0 < decision_ts <= now):
        raise ValueError("INVALID_TRACE_TIME")
    decision = evaluation.decision
    if (decision.setup.symbol.replace("/", "") != "EURUSD"
        or decision.fsm_inputs.get("decision_policy") != "PHYSICAL_ONLY_V3"):
        return
    row = handoff.next_state["per_symbol"][decision.setup.symbol]
    signal_id = row.get("physical_signal_id")
    if (not isinstance(signal_id, str) or not signal_id.startswith("sig-v3-")
        or row.get("physical_history_policy") != HISTORY_POLICY):
        return
    identity = sha256(signal_id.encode()).hexdigest()
    parameter_hash = algo_params_sha256(params)
    path, emitted = _path(parameter_hash), []
    with storage.with_lock("physical_v3_opportunity_trace", timeout_sec=.2):
        state = _read(path, parameter_hash)
        records = state["records"]
        trace = records.get(identity)
        stage = handoff.accepted_stage if handoff.stage_handoff_ready else None
        if stage in {"PRE", "CONFIRM", "OPEN_NOW"} and (
            decision.kind != stage or decision.signal_id != signal_id or handoff.signal_id != signal_id
        ):
            raise ValueError("TRACE_SOURCE_IDENTITY_MISMATCH")
        if trace is None and stage == "PRE":
            # Never manufacture PRE history for a chain begun before tracing.
            trace = {"events": {}, "closed": False}
            records[identity] = trace
        event = None
        if trace is not None and not trace["closed"]:
            times = [v["decision_ts"] for v in trace["events"].values()]
            if times and decision_ts < max(times):
                return  # retain the original chronology after a clock rollback
            if stage in {"PRE", "CONFIRM", "OPEN_NOW"} and stage not in trace["events"]:
                event = stage
            elif (decision.kind == "REJECT" and handoff.prior_state in {"WATCHLIST", "CONFIRMED"}
                  and handoff.resulting_state in {"COOLDOWN", "WATCHLIST"}
                  and (handoff.transition_event or {}).get("trigger") == "reject_released"):
                event = "EXIT"
                trace["closed"] = True
        if event is not None:
            snapshot = _snapshot(evaluation, handoff, decision_ts, now, signal_id)
            snapshot["since_first_observed_pre_seconds"] = decision_ts - trace["events"].get("PRE", snapshot)["decision_ts"]
            confirm = trace["events"].get("CONFIRM")
            snapshot["since_first_observed_confirm_seconds"] = (decision_ts - confirm["decision_ts"]
                if confirm is not None else 0. if event == "CONFIRM" else None)
            trace["events"][event] = snapshot
            label = event
            if event == "EXIT":
                label = "EXIT_AFTER_OPEN" if "OPEN_NOW" in trace["events"] else "EXIT_BEFORE_OPEN"
                if label == "EXIT_BEFORE_OPEN":
                    for key, values in (("exit_blockers", snapshot["hard_blockers"]),
                                        ("exit_noise_reasons", snapshot["noise_reasons"]),
                                        ("exit_structure_conflicts", snapshot["structure_conflicts"])):
                        counts = Counter(state[key]); counts.update(values); state[key] = dict(counts)
            counts = Counter(state["event_totals"]); counts[label] += 1; state["event_totals"] = dict(counts)
            emitted.append({"event": label, "opportunity_hash": identity[:12], **snapshot})
            def stored_size():
                return len((json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False,
                                       allow_nan=False) + "\n").encode())
            while len(records) > MAX_RECORDS or stored_size() > MAX_BYTES:
                if len(records) <= 1:
                    raise ValueError("TRACE_SIZE_LIMIT")
                oldest = min(records, key=lambda key: min(e["decision_ts"] for e in records[key]["events"].values()))
                del records[oldest]
            storage.save_json_atomic(str(path), state)
    for payload in emitted:
        print("TSP_PHYSICAL_V3_OPPORTUNITY_TRACE " + json.dumps({
            "protocol": PROTOCOL, "parameter_sha256": parameter_hash,
            "truth_domain": "LIFECYCLE_OBSERVATION_ONLY", "broker_executed": False,
            **payload}, sort_keys=True, allow_nan=False), flush=True)
    slot = int(now // 60)
    if _last_report.get(str(path), -1) < slot:
        print("TSP_PHYSICAL_V3_OPPORTUNITY_DIAGNOSTICS " + json.dumps({
            "protocol": PROTOCOL, "observed_at": now, "parameter_sha256": parameter_hash,
            "retained_episodes": len(state["records"]), "event_totals": state["event_totals"],
            "retained_unclosed_before_open": sum(not row["closed"] and "OPEN_NOW" not in row["events"]
                                                   for row in state["records"].values()),
            **{key: state[key] for key in ("exit_blockers", "exit_noise_reasons", "exit_structure_conflicts")},
            "no_historical_backfill": True, "execution_authority": False,
            "broker_executed": False}, sort_keys=True), flush=True)
        _last_report[str(path)] = slot
