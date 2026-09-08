# send/intelligence/research_engine.py
# BinaryBot — Research Engine (governed evidence, advisory only)

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from core import event_schema_migration
from core import storage
from core.jsonl_parser import iter_jsonl
from intelligence import evidence_contract


_OBS_DIR = os.getenv("OBS_DIR", storage.root_path("observability"))
_ENGINE_LOG = os.getenv("ENGINE_EVENTS_LOG", os.path.join(_OBS_DIR, "engine_events.jsonl"))
_ANALYTICS_BASE = os.getenv("ANALYTICS_DIR", storage.root_path("analytics"))
_RESEARCH_REPORT_PATH = os.path.join(_ANALYTICS_BASE, "research_report.json")

_ALLOWED_STAGES = {"PRE", "CONFIRM", "OPEN_NOW"}


def _classify_stage(stage: Optional[str]) -> str:
    if stage is None:
        return "MISSING"
    if stage in _ALLOWED_STAGES:
        return "SUPPORTED"
    return "UNSUPPORTED"


def compute_signal_funnel() -> Dict[str, Any]:
    """Count candidate lifecycle stages using v3 primary evidence first.

    Current v3 candidate existence is represented by the PRE_DISTRIBUTION
    `signal_execution_result` with `signal_event_available=true`. Historical
    `signal_event` rows remain a bounded fallback under their original identity.
    POST_DISTRIBUTION execution results are intentionally excluded so one
    execution attempt is not counted twice.

    Transition periods can contain both identities for the same logical
    candidate. A matching `(signal_id, stage)` legacy row is therefore
    suppressed whenever primary v3 evidence exists; unmatched legacy evidence
    remains countable as historical fallback and is never rewritten as v3.
    """

    counts: Dict[str, int] = {"PRE": 0, "CONFIRM": 0, "OPEN_NOW": 0}
    unsupported_stages: Dict[str, int] = {}
    invalid_count = 0
    primary_v3_count = 0
    legacy_fallback_count = 0
    legacy_duplicate_suppressed_count = 0
    historical_named_execution_count = 0
    seen_primary_attempts: set[str] = set()
    primary_candidate_keys: set[tuple[str, str]] = set()
    seen_legacy_event_ids: set[str] = set()
    legacy_candidates: list[tuple[str, str]] = []

    def _count_stage(stage: Any) -> None:
        nonlocal invalid_count
        stage_value = str(stage) if stage is not None else None
        classification = _classify_stage(stage_value)
        if classification == "SUPPORTED":
            counts[str(stage_value)] += 1
        elif classification == "UNSUPPORTED":
            unsupported_stages[str(stage_value)] = unsupported_stages.get(str(stage_value), 0) + 1
        else:
            invalid_count += 1

    try:
        for record, err in iter_jsonl(_ENGINE_LOG):
            if err is not None:
                invalid_count += 1
                continue

            event_type = record.get("event_type")
            if event_type == "signal_execution_result":
                identity_class = event_schema_migration.classify_event_identity(record)
                if identity_class != event_schema_migration.PRIMARY_V3:
                    historical_named_execution_count += 1
                    continue

                data = record.get("data") if isinstance(record.get("data"), dict) else {}
                if data.get("execution_phase") != "PRE_DISTRIBUTION":
                    continue
                if data.get("signal_event_available") is not True:
                    continue

                attempt_id = str(record.get("execution_attempt_id") or "").strip()
                if not attempt_id:
                    invalid_count += 1
                    continue
                if attempt_id in seen_primary_attempts:
                    continue
                seen_primary_attempts.add(attempt_id)

                signal_id = str(record.get("signal_id") or "").strip()
                stage = record.get("stage")
                stage_key = str(stage or "").strip()
                if signal_id and stage_key:
                    primary_candidate_keys.add((signal_id, stage_key))

                primary_v3_count += 1
                _count_stage(stage)
                continue

            if event_type != "signal_event":
                continue

            event_id = str(record.get("event_id") or "").strip()
            if event_id and event_id in seen_legacy_event_ids:
                continue
            if event_id:
                seen_legacy_event_ids.add(event_id)

            signal_id = str(record.get("signal_id") or "").strip()
            stage = str(record.get("stage") or "").strip()
            legacy_candidates.append((signal_id, stage))

    except FileNotFoundError:
        return {
            "no_data": True,
            "reason": "engine_log_not_found",
            "path": _ENGINE_LOG,
            "PRE": 0,
            "CONFIRM": 0,
            "OPEN_NOW": 0,
            "total_signal_events": 0,
            "primary_v3_count": 0,
            "legacy_fallback_count": 0,
            "legacy_duplicate_suppressed_count": 0,
            "historical_named_execution_count": 0,
            "invalid_count": 0,
            "unsupported_stages": {},
        }

    for signal_id, stage in legacy_candidates:
        if signal_id and stage and (signal_id, stage) in primary_candidate_keys:
            legacy_duplicate_suppressed_count += 1
            continue
        legacy_fallback_count += 1
        _count_stage(stage or None)

    total = sum(counts.values())
    return {
        "no_data": total == 0,
        **counts,
        "total_signal_events": total,
        "primary_v3_count": primary_v3_count,
        "legacy_fallback_count": legacy_fallback_count,
        "legacy_duplicate_suppressed_count": legacy_duplicate_suppressed_count,
        "historical_named_execution_count": historical_named_execution_count,
        "invalid_count": invalid_count,
        "unsupported_stages": unsupported_stages,
    }


def compute_outcome_stats() -> Dict[str, Any]:
    """Compatibility surface: strategy-performance outcome stats are MARKET_TRUTH only.

    The generic function name is retained for callers, but its payload is explicitly
    labeled and can never source its rate from community votes.
    """
    snapshot = evidence_contract.build_truth_snapshot()
    market = dict(snapshot["market_truth"])
    market["legacy_compatibility_only"] = True
    market["win_rate"] = market.get("market_win_rate_percent")
    market["win_rate_truth_domain"] = evidence_contract.TRUTH_MARKET
    return market


def compute_distribution_summary() -> Dict[str, Any]:
    snapshot = evidence_contract.build_truth_snapshot()
    distribution = snapshot.get("distribution")
    return dict(distribution) if isinstance(distribution, dict) else {"no_data": True}


def _market_observations(market: Dict[str, Any], observations: List[str], limitations: List[str]) -> None:
    if market.get("no_data"):
        observations.append("No finalized objective MARKET_TRUTH sample is available.")
        limitations.append("Strategy-performance research requires objective MARKET_TRUTH; community feedback is not a substitute.")
        return

    observations.append(
        "Objective MARKET_TRUTH: "
        f"WIN={market.get('wins', 0)}, LOSS={market.get('losses', 0)}, "
        f"DRAW={market.get('draws', 0)}, decisive_sample={market.get('decisive_sample', 0)}."
    )
    if market.get("insufficient_sample"):
        limitations.append(
            "Objective MARKET_TRUTH exists but the descriptive sample is insufficient for a stable rate under the analytics contract."
        )
    elif market.get("market_win_rate_percent") is not None:
        observations.append(
            f"Descriptive Market WR={market['market_win_rate_percent']}% from MARKET_TRUTH only."
        )

    if market.get("excluded_incomplete", 0):
        limitations.append(
            f"{market.get('excluded_incomplete', 0)} incomplete telemetry record(s) were excluded from MARKET_TRUTH performance metrics."
        )
    if market.get("invalid_count", 0):
        limitations.append(
            f"{market.get('invalid_count', 0)} invalid MARKET_TRUTH record(s) were excluded."
        )


def build_research_report() -> Dict[str, Any]:
    """Build a truth-layer-aware, advisory-only research report.

    Research consumes the R-003 analytics truth contract. It does not blend
    community/operational evidence into strategy performance, does not apply
    thresholds, and does not mutate production parameters.
    """
    snapshot = evidence_contract.build_truth_snapshot()
    readiness = evidence_contract.assess_readiness(snapshot)
    funnel = compute_signal_funnel()
    market = dict(snapshot["market_truth"])
    operational = dict(snapshot["operational_truth"])
    community = dict(snapshot["community_truth"])
    distribution = dict(snapshot.get("distribution") or {})

    observations: List[str] = []
    hypotheses: List[str] = []
    recommendations: List[str] = []
    limitations: List[str] = []

    if funnel.get("no_data"):
        observations.append("No candidate lifecycle records found in the engine log.")
    else:
        observations.append(
            f"Signal funnel: PRE={funnel.get('PRE', 0)}, CONFIRM={funnel.get('CONFIRM', 0)}, "
            f"OPEN_NOW={funnel.get('OPEN_NOW', 0)}."
        )
        if funnel.get("unsupported_stages"):
            limitations.append(f"Unsupported signal stages observed: {funnel['unsupported_stages']}.")

    _market_observations(market, observations, limitations)

    if not operational.get("no_data"):
        observations.append(
            "Operational truth is available as a separate execution/reconciliation domain; "
            "it is not used as objective strategy-performance truth."
        )
    if not community.get("no_data"):
        observations.append(
            "Community feedback is available as COMMUNITY_TRUTH and remains non-authoritative for strategy performance."
        )

    if distribution.get("no_data"):
        observations.append("No distribution events are available for this research snapshot.")
    else:
        observations.append(
            f"Distribution: PUBLISHED={distribution.get('PUBLISHED', 0)}, "
            f"FAILED={distribution.get('FAILED', 0)}, "
            f"DUPLICATE_SUPPRESSED={distribution.get('DUPLICATE_SUPPRESSED', 0)}."
        )

    if readiness["descriptive_research_ready"]:
        hypotheses.append(
            "Objective MARKET_TRUTH is available for descriptive hypothesis formation. "
            "No parameter or formula conclusion is authorized without a governed hypothesis, experiment, validation, and approval chain."
        )
    else:
        limitations.append(
            "Objective evidence is not ready for strategy-performance conclusions; continue evidence collection and data-quality review."
        )

    if distribution.get("FAILED", 0) > 0:
        recommendations.append(
            "[ADVISORY] Distribution FAILED events exist; investigate distribution evidence independently of strategy quality."
        )
    if not funnel.get("no_data") and funnel.get("OPEN_NOW", 0) == 0:
        recommendations.append(
            "[ADVISORY] No OPEN_NOW lifecycle events are present; verify instrumentation/pipeline operation before parameter research."
        )
    if readiness["descriptive_research_ready"]:
        recommendations.append(
            "[ADVISORY] Form a versioned hypothesis and controlled experiment before proposing any strategy-parameter change."
        )
    else:
        recommendations.append(
            "[ADVISORY] Do not propose strategy-parameter changes from the current evidence state."
        )

    report = {
        "schema_version": "3.0.0",
        "truth_separation_enforced": True,
        "strategy_performance_truth_domain": evidence_contract.TRUTH_MARKET,
        "signal_funnel": funnel,
        "strategy_performance": market,
        # Bounded compatibility for older readers: `outcomes` is MARKET_TRUTH only.
        "outcomes": {
            **market,
            "legacy_compatibility_only": True,
            "win_rate": market.get("market_win_rate_percent"),
            "win_rate_truth_domain": evidence_contract.TRUTH_MARKET,
        },
        "operational_truth": operational,
        "community_truth": community,
        "distribution": distribution,
        "research": {
            "observations": observations,
            "hypotheses": hypotheses,
            "recommendations": recommendations,
            "limitations": limitations,
            "validation_status": (
                "DESCRIPTIVE_ONLY" if readiness["descriptive_research_ready"] else "INSUFFICIENT_OR_INVALID_EVIDENCE"
            ),
            "confidence": "DESCRIPTIVE_ONLY",
            "readiness": readiness,
            "advisory_only": True,
            "auto_apply": False,
            "production_mutation_authorized": False,
        },
    }
    return report


def persist_research_report(report: Dict[str, Any]) -> None:
    """Persist an advisory research artifact; this does not mutate live strategy state."""
    storage.save_json_atomic(_RESEARCH_REPORT_PATH, report)
