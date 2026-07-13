# /opt/binarybot/intelligence/risk_monitor.py
# BinaryBot — Risk Monitoring Engine

from __future__ import annotations

from typing import Dict, Any

from intelligence import research_engine
from core import observability_logger


LOSS_STREAK_LIMIT = 5
WIN_RATE_MIN = 40


def evaluate_risk() -> Dict[str, Any]:

    report = research_engine.build_research_report()

    outcomes = report.get("outcomes", {})

    wins = outcomes.get("wins", 0)
    loses = outcomes.get("loses", 0)
    missed = outcomes.get("missed", 0)

    total = wins + loses + missed

    if total == 0:
        return {"risk_level": "UNKNOWN"}

    win_rate = outcomes.get("win_rate", 0)

    if win_rate < WIN_RATE_MIN:

        observability_logger.log_warning(
            warn_type="LOW_WIN_RATE",
            message="Risk monitor detected win rate below the canonical minimum",
            context={
                "reason": "low_win_rate",
                "win_rate": win_rate,
                "win_rate_min": WIN_RATE_MIN,
                "total_outcomes": total,
            },
            source={"module": "risk_monitor", "function": "evaluate_risk"},
        )

        return {
            "risk_level": "HIGH",
            "reason": "LOW_WIN_RATE"
        }

    return {
        "risk_level": "NORMAL"
    }