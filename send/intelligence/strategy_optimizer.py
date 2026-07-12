# /opt/binarybot/intelligence/strategy_optimizer.py
# BinaryBot — Strategy Optimizer

from __future__ import annotations

from typing import Dict, Any

from intelligence import research_engine
from intelligence import adaptive_params
from core import observability_logger


def optimize_strategy() -> Dict[str, Any]:

    research = research_engine.build_research_report()

    funnel = research.get("signal_funnel", {})
    outcomes = research.get("outcomes", {})

    pre = funnel.get("pre", 0)
    confirm = funnel.get("confirm", 0)
    open_now = funnel.get("open_now", 0)

    win_rate = outcomes.get("win_rate", 0)

    suggestions = []

    if confirm < pre * 0.4 and pre > 10:
        suggestions.append("CONFIRM threshold may be too strict")

    if open_now < confirm * 0.5 and confirm > 10:
        suggestions.append("OPEN threshold may be too strict")

    if win_rate < 45:
        suggestions.append("Strategy underperforming")

    new_params = adaptive_params.adjust_parameters()

    observability_logger.log_event({
        "event_type": "strategy_optimizer",
        "data": {
            "suggestions": suggestions,
            "win_rate": win_rate
        }
    })

    return {
        "suggestions": suggestions,
        "new_params": new_params
    }