"""Chronological, offline timing-readiness analysis of a personal audit export.

No network, publication, parameter writes, calibration activation or broker calls.
M1 snapshots support minute-resolution research only, not tick-level calibration.
Run: PYTHONPATH=send python -m scripts.analyze_owner_signal_timing AUDIT.json
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from core import candle_adapter, fsm_runtime, params_loader
from core.strategy_v2 import decide
from core.v2_fsm_orchestrator import advance_persistent_fsm, current_opportunity_signal_id
from state_store.state_store import default_fsm_state
from runtime.market_history_integrity import inspect_history


def analyze(audit: dict[str, Any]) -> dict[str, Any]:
    source = audit["owner_timing_calibration_evidence"]
    if source["status"] != "PERSONAL_RESEARCH_SNAPSHOT" or source["provider"] != "FINNHUB":
        raise ValueError("A genuine Owner personal-research snapshot is required")
    params = source["params"]
    params_loader.validate_algo_params(params)
    buffer_mode = source.get("buffer_mode")
    if buffer_mode is None:
        observed_modes = [(row.get("data") or {}).get("buffer_mode")
                          for row in audit.get("recent_engine_events", [])]
        buffer_mode = next((mode for mode in reversed(observed_modes) if mode in {"SMALL", "MEDIUM", "LARGE"}), None)
    if buffer_mode not in {"SMALL", "MEDIUM", "LARGE"}:
        raise ValueError("Observed current buffer mode is required")
    raw = source["candles"]
    if any(not isinstance(raw[k], list) or not 1 <= len(raw[k]) <= 500 for k in ("M1", "M5")):
        raise ValueError("Snapshot exceeds bounded candle window")
    if inspect_history(raw)["state"] != "VALID":
        raise ValueError("Snapshot has invalid market history")
    for frame in ("M1", "M5"):
        for row in raw[frame]:
            if row["provider"] != "FINNHUB" or row["symbol"] not in {"EUR/USD", "EURUSD"} or row["timeframe"] != frame:
                raise ValueError("Candle provenance/scope mismatch")
    observed_at = source["observed_at_ts"]
    m1 = [r for r in raw["M1"] if r["complete"] is True and r["ts"] + 60 <= observed_at]
    m5 = [r for r in raw["M5"] if r["complete"] is True and r["ts"] + 300 <= observed_at]
    state = default_fsm_state()
    kinds, blockers, fsm_reasons, errors = (Counter() for _ in range(4))
    accepted: dict[str, dict[str, float]] = {}
    opportunities = {}
    evaluations = 0
    for index in range(len(m1) - 21, -1, -1):
        # Historical observation occurs at this real M1 close. Every input M5
        # must have closed by then; a later final M5 is never backfilled.
        cutoff = m1[index]["ts"] + 60
        m5_window = [r for r in m5 if r["ts"] + 300 <= cutoff]
        if len(m5_window) < max(15, int(params["strategy_v2"]["ema_slow"]) + 1):
            continue
        try:
            state, _ = fsm_runtime.reconcile_state(state, cutoff, active_symbols=["EURUSD"])
            evaluation = decide(
                candle_adapter.normalize(m1[index:], symbol="EURUSD", timeframe="M1"),
                candle_adapter.normalize(m5_window, symbol="EURUSD", timeframe="M5"),
                params, buffer_mode=buffer_mode, observation_ts=cutoff,
                context={"decision_timeframe": "M1", "opportunity_signal_id": current_opportunity_signal_id(state, "EURUSD")},
            )
            decision = evaluation.decision
            handoff = advance_persistent_fsm(state, decision, now_ts=cutoff)
            state = handoff.next_state
        except Exception as exc:
            errors[type(exc).__name__] += 1
            continue
        evaluations += 1
        kinds[decision.kind] += 1
        blockers.update(decision.reject.hard_blockers)
        fsm_reasons[handoff.reason_family] += 1
        if handoff.stage_handoff_ready:
            accepted.setdefault(decision.signal_id, {}).setdefault(handoff.accepted_stage, cutoff)
            if handoff.accepted_stage == "OPEN_NOW" and decision.time.time_state == "READY":
                opportunities.setdefault(decision.signal_id, {
                    "cutoff": cutoff, "model_horizon_minutes": decision.time.model_expiry,
                })

    all_stage_observations = [v for v in accepted.values() if all(k in v for k in ("PRE", "CONFIRM", "OPEN_NOW"))]
    complete_chains = [v for v in all_stage_observations if v["PRE"] <= v["CONFIRM"] <= v["OPEN_NOW"]]
    gaps = {
        "pre_to_confirm_seconds": [row["CONFIRM"] - row["PRE"] for row in complete_chains],
        "confirm_to_open_seconds": [row["OPEN_NOW"] - row["CONFIRM"] for row in complete_chains],
        "pre_to_open_seconds": [row["OPEN_NOW"] - row["PRE"] for row in complete_chains],
    }
    # A high count alone is never calibration proof. Replaying minute closes
    # cannot recover the real intrabar transitions or precise expiry labels.
    return {
        "protocol": "OWNER_CHRONOLOGICAL_TIMING_READINESS_V1",
        "truth_domain": "OFFLINE_PERSONAL_RESEARCH",
        "parameter_sha256": hashlib.sha256(json.dumps(params, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
        "source_observed_at_ts": observed_at,
        "buffer_mode": buffer_mode,
        "activity_gate_model": "NORMALIZED_M1_RANGE_OVER_M5_ATR14_020",
        "completed_candles": {"M1": len(m1), "M5": len(m5)},
        "oldest_m1_open_ts": m1[-1]["ts"] if m1 else None,
        "newest_m1_close_ts": m1[0]["ts"] + 60 if m1 else None,
        "evaluations": evaluations, "decision_kinds": dict(kinds), "hard_blockers": dict(blockers),
        "fsm_reason_families": dict(fsm_reasons), "evaluation_errors": dict(errors),
        "accepted_unique_stages": {stage: sum(stage in row for row in accepted.values()) for stage in ("PRE", "CONFIRM", "OPEN_NOW")},
        "complete_lifecycle_count": len(complete_chains),
        "non_monotonic_lifecycle_count": len(all_stage_observations) - len(complete_chains),
        "fsm_accepted_model_ready_open_opportunities": len(opportunities),
        "historical_minute_resolution_stage_gaps": gaps,
        "calibration_status": "INSUFFICIENT_EXECUTABLE_OPPORTUNITIES" if len(opportunities) < 30 else "TICK_RESOLUTION_VALIDATION_REQUIRED",
        "execution_calibration_proven": False, "production_parameters_changed": False,
        "telegram_signals_published": 0, "broker_trades_executed": 0,
        "limitations": [
            "Minute-close replay cannot establish real PRE/CONFIRM/OPEN_NOW intrabar latency.",
            "Only bars already closed at each historical cutoff are used; no future M5 values.",
            "No invented expiry values, activation, outcome or win-rate claim.",
        ],
    }


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Expected one personal audit JSON file")
    path = Path(sys.argv[1])
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Audit file exceeds maximum input size")
    print(json.dumps(analyze(json.loads(path.read_text())), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
