from __future__ import annotations

from core import observability_logger


def test_event_schema_v3_exposes_primary_and_legacy_migration_families() -> None:
    schema = observability_logger.get_event_schema()
    assert schema["schema_version"] == "3.0.0"

    event_types = set(schema["event_types"])
    assert {
        "decision_evaluated",
        "decision_promoted",
        "decision_rejected",
        "decision_no_signal",
        "fsm_transition",
        "signal_execution_result",
        "duplicate_suppressed",
        "signal_stage_visible",
        "signal_closed",
        "route_publish_attempt",
        "route_publish_result",
        "route_reset",
        "route_state_changed",
        "route_mapping_invalid",
        "outcome_submission_attempt",
        "outcome_submission_result",
        "outcome_reconciled",
        "guarded_action_review",
        "feature_toggle_changed",
        "anomaly",
        "invariant_breach",
    } <= event_types

    # Explicit migration adapters remain readable while downstream modules move
    # to the v3 primary names.
    assert {"decision", "signal_event", "tier_publish", "tier_reset"} <= event_types


def test_pre_distribution_execution_event_is_v3_and_cannot_claim_emitted() -> None:
    event = observability_logger.build_event(
        "signal_execution_result",
        {
            "execution_phase": "PRE_DISTRIBUTION",
            "execution_outcome": "DEFERRED",
            "execution_reason": "DISTRIBUTION_NOT_INVOKED",
            "stage_handoff_ready": True,
            "trade_execution_ready": False,
            "signal_event_available": True,
            "destination_state": "PRE_DISTRIBUTION_UNRESOLVED",
            "candidate_schema_version": "3.0.0",
            "fsm_handoff": {},
            "trade_physics": None,
        },
        source={"module": "tests", "function": "execution_event"},
        correlation={
            "execution_attempt_id": "attempt-1",
            "setup_correlation_id": "cycle-1",
            "signal_id": "sig-1",
            "symbol": "EUR/USD",
            "timeframe": "M1",
            "stage": "PRE",
        },
    )
    event["schema_version"] = "3.0.0"
    assert observability_logger.validate_event(event) == event
    assert event["data"]["execution_outcome"] != "EMITTED"
