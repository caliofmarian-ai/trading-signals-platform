# send/intelligence/risk_monitor.py
# BinaryBot — evidence-quality risk monitor

from __future__ import annotations

from typing import Any, Dict

from intelligence import research_engine
from core import observability_logger


def evaluate_risk() -> Dict[str, Any]:
    """Evaluate evidence readiness without inventing a performance-risk threshold.

    The former implementation treated a hardcoded 40% win-rate value as a
    canonical minimum. No such authority is established for this module, so
    strategy-performance risk remains unclassified until a governed threshold
    exists. Data-quality/readiness problems remain observable.
    """
    report = research_engine.build_research_report()
    market = report.get("strategy_performance") or {}
    readiness = (report.get("research") or {}).get("readiness") or {}

    if market.get("no_data") or market.get("insufficient_sample", True):
        return {
            "risk_level": "UNKNOWN",
            "assessment_status": "INSUFFICIENT_MARKET_TRUTH",
            "truth_domain": "MARKET_TRUTH",
            "market_win_rate_percent": market.get("market_win_rate_percent"),
            "decisive_sample": market.get("decisive_sample", 0),
            "production_action_authorized": False,
        }

    evidence_issues = int(market.get("invalid_count", 0) or 0) + int(market.get("excluded_incomplete", 0) or 0)
    if evidence_issues > 0:
        try:
            observability_logger.log_warning(
                warn_type="MARKET_TRUTH_EVIDENCE_QUALITY",
                message="Risk monitor observed incomplete or invalid objective market evidence",
                context={
                    "truth_domain": "MARKET_TRUTH",
                    "invalid_count": market.get("invalid_count", 0),
                    "excluded_incomplete": market.get("excluded_incomplete", 0),
                    "decisive_sample": market.get("decisive_sample", 0),
                },
                source={"module": "risk_monitor", "function": "evaluate_risk"},
            )
        except Exception:
            pass

    return {
        "risk_level": "UNCLASSIFIED",
        "assessment_status": "NO_GOVERNED_PERFORMANCE_RISK_THRESHOLD",
        "truth_domain": "MARKET_TRUTH",
        "market_win_rate_percent": market.get("market_win_rate_percent"),
        "decisive_sample": market.get("decisive_sample", 0),
        "evidence_quality_issues": evidence_issues,
        "descriptive_research_status": readiness.get("descriptive_research_status"),
        "production_action_authorized": False,
    }
