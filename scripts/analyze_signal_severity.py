"""Compare Owner-requested severities 0..20 on one chronological audit.

This research grid changes only copied classical score thresholds. It replays
the full existing strategy and independent FSM for every level, including
rejected/no-signal windows. It cannot publish, activate parameters, approve
expiry calibration or execute a broker trade.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

from scripts.analyze_owner_signal_timing import analyze


from intelligence.signal_severity_scale import BASELINE_LEVEL, LEVELS, score_thresholds

PROTOCOL = "CHRONOLOGICAL_SCORE_SEVERITY_LADDER_V1"


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def analyze_ladder(audit: dict) -> dict:
    """Offline paired research: every level receives exactly the same bars."""
    source = audit["owner_timing_calibration_evidence"]
    baseline = source["params"]
    # Validate the genuine source through the unchanged chronological reader
    # before evaluating copied counterfactual parameter bundles.
    control = analyze(audit)
    rows = []
    for level in LEVELS:
        thresholds = score_thresholds(baseline, level)
        if level == BASELINE_LEVEL:
            result = control
        else:
            candidate = copy.deepcopy(audit)
            candidate["owner_timing_calibration_evidence"]["params"]["score_thresholds"] = thresholds
            result = analyze(candidate)
        rows.append({
            "level": level, "score_thresholds": thresholds,
            "is_observed_baseline": level == BASELINE_LEVEL,
            **{key: result[key] for key in (
                "parameter_sha256", "evaluations", "decision_kinds", "hard_blockers",
                "fsm_reason_families", "evaluation_errors", "accepted_unique_stages",
                "complete_lifecycle_count", "non_monotonic_lifecycle_count",
                "fsm_accepted_model_ready_open_opportunities",
                "historical_minute_resolution_stage_gaps",
            )},
        })
    return {
        "protocol": PROTOCOL, "truth_domain": "OFFLINE_COUNTERFACTUAL_RESEARCH",
        "input_audit_sha256": _digest(audit), "source_parameter_sha256": _digest(baseline),
        "source_observed_at_ts": control["source_observed_at_ts"],
        "baseline_level": BASELINE_LEVEL,
        "tested_dimension": "CLASSICAL_SCORE_THRESHOLDS_ONLY",
        "threshold_mapping": "STAGE_GAP_PRESERVING_TRANSLATION_ANCHORED_AT_14",
        "completed_candles": control["completed_candles"],
        "oldest_m1_open_ts": control["oldest_m1_open_ts"],
        "newest_m1_close_ts": control["newest_m1_close_ts"],
        "buffer_mode": control["buffer_mode"], "levels": rows,
        "production_parameters_changed": False, "execution_calibration_proven": False,
        "telegram_signals_published": 0, "broker_trades_executed": 0,
        "automatic_selection_allowed": False, "selected_level": None,
        "limitations": [
            "These are historical minute-close FSM observations, not actual delivered signals.",
            "All levels retain the same data, structure, activity, noise, time and Trade Physics requirements.",
            "Lower score thresholds cannot repair missing structure or approved execution expiry.",
            "Monotone thresholds need not yield monotone lifecycle counts because each FSM has independent history.",
            "No outcome, win rate, broker compatibility or best-performing level is inferred from stage counts.",
            "The existing accepted-OPEN TPS sweep is a different experiment and is not relabelled.",
        ],
    }


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Expected one genuine Owner audit JSON file")
    path = Path(sys.argv[1])
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Audit file exceeds maximum input size")
    print(json.dumps(analyze_ladder(json.loads(path.read_text())), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
