from __future__ import annotations

from typing import Any, Dict, List

from core import analytics_engine


TRUTH_MARKET = "MARKET_TRUTH"
TRUTH_OPERATIONAL = "OPERATIONAL_TRUTH"
TRUTH_COMMUNITY = "COMMUNITY_TRUTH"


def _invalid_market_snapshot(reason: str, raw: Any = None) -> Dict[str, Any]:
    return {
        "truth_domain": TRUTH_MARKET,
        "authoritative_for_strategy_performance": True,
        "no_data": True,
        "invalid_evidence": True,
        "reason": reason,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "total": 0,
        "decisive_sample": 0,
        "market_win_rate_percent": None,
        "insufficient_sample": True,
        "invalid_source_snapshot": raw,
    }


def _validated_market_snapshot(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return _invalid_market_snapshot("market_truth_snapshot_not_object", raw)
    if raw.get("truth_domain") != TRUTH_MARKET:
        return _invalid_market_snapshot("strategy_performance_truth_domain_mismatch", raw)
    if raw.get("authoritative_for_strategy_performance") is not True:
        return _invalid_market_snapshot("market_truth_not_authoritative_for_strategy_performance", raw)
    return dict(raw)


def _validated_labeled_snapshot(raw: Any, expected_domain: str) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "truth_domain": expected_domain,
            "no_data": True,
            "invalid_evidence": True,
            "reason": f"{expected_domain.lower()}_snapshot_not_object",
        }
    if raw.get("truth_domain") != expected_domain:
        return {
            "truth_domain": expected_domain,
            "no_data": True,
            "invalid_evidence": True,
            "reason": f"{expected_domain.lower()}_truth_domain_mismatch",
            "invalid_source_snapshot": dict(raw),
        }
    return dict(raw)


def build_truth_snapshot() -> Dict[str, Any]:
    """Build the intelligence input only from the R-003 truth-separated analytics loaders.

    This function is deliberately read-only. It does not call analytics_engine.recompute(),
    does not persist reports, and does not mutate strategy/runtime parameters.
    """
    market_raw = analytics_engine._load_market_truth(analytics_engine._MARKET_TELEMETRY_LOG)
    operational_raw = analytics_engine._load_operational_truth(analytics_engine._OPERATIONAL_OUTCOMES_LOG)
    community_raw = analytics_engine._load_community_truth(analytics_engine._OUTCOMES_LOG)
    distribution = analytics_engine._load_distribution_metrics(analytics_engine._DIST_LOG)

    market = _validated_market_snapshot(market_raw)
    operational = _validated_labeled_snapshot(operational_raw, TRUTH_OPERATIONAL)
    community = _validated_labeled_snapshot(community_raw, TRUTH_COMMUNITY)

    return {
        "schema_version": "1.0.0",
        "truth_separation_enforced": True,
        "strategy_performance_truth_domain": TRUTH_MARKET,
        "market_truth": market,
        "operational_truth": operational,
        "community_truth": community,
        "distribution": distribution if isinstance(distribution, dict) else {"no_data": True},
    }


def assess_readiness(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Assess evidence readiness without inventing production-mutation authority."""
    market = snapshot.get("market_truth") or {}
    reasons: List[str] = []

    if snapshot.get("truth_separation_enforced") is not True:
        reasons.append("truth_separation_not_enforced")
    if snapshot.get("strategy_performance_truth_domain") != TRUTH_MARKET:
        reasons.append("strategy_performance_truth_domain_not_market_truth")
    if market.get("truth_domain") != TRUTH_MARKET:
        reasons.append("market_truth_domain_invalid")
    if market.get("authoritative_for_strategy_performance") is not True:
        reasons.append("market_truth_authority_invalid")
    if market.get("invalid_evidence"):
        reasons.append(str(market.get("reason") or "invalid_market_evidence"))
    if market.get("no_data"):
        reasons.append("objective_market_truth_unavailable")
    if market.get("insufficient_sample", True):
        reasons.append("objective_market_truth_sample_insufficient")

    descriptive_ready = not reasons

    # The active canon requires additional experiment, provenance, leakage,
    # validation, approval and rollback gates before any mutation. This compact
    # offline intelligence layer does not prove those gates, so mutation remains
    # fail-closed even when descriptive market evidence is available.
    mutation_blockers = list(reasons)
    mutation_blockers.extend(
        [
            "governed_hypothesis_and_experiment_not_proven",
            "production_change_approval_not_proven",
            "rollback_readiness_not_proven",
        ]
    )

    return {
        "descriptive_research_status": (
            "DESCRIPTIVE_MARKET_EVIDENCE_AVAILABLE" if descriptive_ready else "INSUFFICIENT_OR_INVALID_EVIDENCE"
        ),
        "descriptive_research_ready": descriptive_ready,
        "evolution_readiness": "NOT_READY",
        "production_mutation_authorized": False,
        "auto_apply": False,
        "reasons": reasons,
        "mutation_blockers": mutation_blockers,
    }
