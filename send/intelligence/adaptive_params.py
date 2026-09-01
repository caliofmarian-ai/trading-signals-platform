# send/intelligence/adaptive_params.py
# BinaryBot — governed parameter recommendation boundary

from __future__ import annotations

from typing import Any, Dict

from core import params_loader
from intelligence import research_engine


def adjust_parameters() -> Dict[str, Any]:
    """Compatibility entry point that never adjusts production parameters automatically.

    The previous implementation created threshold changes from ungoverned win-rate
    heuristics and a legacy `thresholds` schema. Active canon requires evidence,
    experiment governance, approval, and rollback readiness before any mutation.
    Therefore this function now returns a recommendation/readiness bundle only.
    """
    params = params_loader.load_algo_params()
    research = research_engine.build_research_report()
    market = research.get("strategy_performance") or {}
    readiness = (research.get("research") or {}).get("readiness") or {}

    return {
        "action": "NO_AUTOMATIC_PARAMETER_CHANGE",
        "advisory_only": True,
        "auto_apply": False,
        "production_mutation_authorized": False,
        "truth_domain": "MARKET_TRUTH",
        "current_algo_version": params.get("algo_version"),
        "current_params_checksum": params_loader.compute_checksum(params),
        "market_evidence": {
            "no_data": market.get("no_data", True),
            "decisive_sample": market.get("decisive_sample", 0),
            "market_win_rate_percent": market.get("market_win_rate_percent"),
            "insufficient_sample": market.get("insufficient_sample", True),
        },
        "readiness": readiness,
        "proposed_changes": [],
        "reason": (
            "Automatic or heuristic parameter adjustment is not authorized. "
            "Create a governed hypothesis/experiment and obtain required approval before any parameter change."
        ),
    }


def propose_parameter_adjustments() -> Dict[str, Any]:
    """Explicitly named advisory alias for new callers."""
    return adjust_parameters()
