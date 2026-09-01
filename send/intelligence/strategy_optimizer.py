# send/intelligence/strategy_optimizer.py
# BinaryBot — Strategy Optimizer (advisory evidence consumer)

from __future__ import annotations

from typing import Any, Dict, List

from intelligence import adaptive_params
from intelligence import research_engine
from core import observability_logger


def optimize_strategy() -> Dict[str, Any]:
    """Produce a governed advisory bundle without mutating strategy parameters."""
    research = research_engine.build_research_report()
    funnel = research.get("signal_funnel") or {}
    market = research.get("strategy_performance") or {}
    readiness = (research.get("research") or {}).get("readiness") or {}

    suggestions: List[str] = []

    if funnel.get("no_data"):
        suggestions.append(
            "[ADVISORY] Signal-funnel evidence is unavailable; do not infer threshold strictness from missing data."
        )
    elif funnel.get("OPEN_NOW", 0) == 0:
        suggestions.append(
            "[ADVISORY] No OPEN_NOW lifecycle events are present; verify pipeline/instrumentation before strategy tuning."
        )

    if market.get("no_data") or market.get("insufficient_sample", True):
        suggestions.append(
            "[ADVISORY] Objective MARKET_TRUTH is insufficient for strategy-performance recommendations."
        )
    else:
        suggestions.append(
            "[ADVISORY] Descriptive MARKET_TRUTH is available; create a governed hypothesis/experiment before proposing parameter changes."
        )

    parameter_recommendation = adaptive_params.adjust_parameters()

    try:
        observability_logger.log_event(
            {
                "event_type": "strategy_optimizer",
                "data": {
                    "advisory_only": True,
                    "auto_apply": False,
                    "production_mutation_authorized": False,
                    "truth_domain": "MARKET_TRUTH",
                    "suggestions": suggestions,
                    "descriptive_research_status": readiness.get("descriptive_research_status"),
                    "evolution_readiness": readiness.get("evolution_readiness", "NOT_READY"),
                    "market_win_rate_percent": market.get("market_win_rate_percent"),
                    "decisive_sample": market.get("decisive_sample", 0),
                },
            }
        )
    except Exception:
        pass

    return {
        "advisory_only": True,
        "auto_apply": False,
        "production_mutation_authorized": False,
        "truth_domain": "MARKET_TRUTH",
        "suggestions": suggestions,
        "readiness": readiness,
        "parameter_recommendation": parameter_recommendation,
        # Bounded compatibility: old callers can see that automatic new params are disabled.
        "new_params": None,
        "new_params_status": "DISABLED_NO_GOVERNED_MUTATION",
    }
