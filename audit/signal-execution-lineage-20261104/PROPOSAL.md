# Repair execution-event lineage placement

CHANGE_ID: 20261104-SIGNAL-EXECUTION-LINEAGE-01  
TYPE: PATCH — producer alignment with the existing schema, no schema relaxation  
OWNER: Semnale Trading / BinaryBot  
REQUESTED_BY: Owner continuation of the real strategy / signal validation work  
DATE: 2026-11-04

## Evidence and canonical contract

A private runtime audit generated at `2026-11-04T08:24:15Z` from main `023f6e54ec2bfd25ce21da6005f88f659f5611a6` includes post-deployment signal-engine errors at 08:18:46Z and 08:18:51Z:

`event.data contains unknown fields: ['decision_audit_id', 'decision_id', 'execution_attempt_id', 'fsm_transition_id', 'setup_correlation_id']`

The input contains confidential runtime/market material and is not committed. Its bounded latest 50 decision rows are all REJECT; this is a recent cohort, not an all-history result or a statement that actionable stages never occurred. All 50 include the activity blocker; 41 include structural/time blockers. These observations do not justify reducing strategy gates.

`SignalExecutionGateResult.to_event_data()` carries lineage fields, but `_log_signal_execution` sends that map unchanged to the strict `signal_execution_result.data` validator. The existing schema permits setup/decision/audit/attempt correlation in the envelope and structured FSM references inside `fsm_handoff`. The exception occurs before Distribution, after FSM persistence. Gate-only tests and mocked logging do not exercise this boundary.

Active authority: Master Index v2; Event Schema v3 §§3,7,10–11; Signal Engine v3 §§6–11,24–27; Decision Audit v3. Preserve identity and truth-domain separation. No active canonical/schema change is needed.

TARGET_CODE: `send/core/signal_engine.py` and integration regressions.  
RATIONALE: A valid accepted lifecycle stage must be loggable without terminating the cycle before governed routing.  
EXPECTED_IMPACT: Envelope carries the four existing correlation fields; `fsm_handoff` carries its stable transition reference. Decision/FSM/pre/post events preserve matching decision lineage.  
RISK / BLAST_RADIUS: Event construction only. Keep the existing evidence projection API and every strategy, stage, calibration, provider, publication and broker gate.  
VALIDATION_METHOD: First reproduce the actual strict-schema failure; test PRE/CONFIRM/OPEN_NOW construction and persisted events without mocking logging; exercise actual `run_once` through the unchanged Finnhub publication block; full suite and exact-head CI; post-deployment fresh audit for actual persisted execution events/errors.  
ROLLBACK_PLAN: Revert this patch; preserve all existing logs.  
DEPLOYMENT_PLAN: CI-gated main deployment; no config or parameter writes.  
MONITORING_WINDOW: Verify deployed SHA, real feed readiness, fresh runtime evidence and unchanged calibration/research state. Actual actionable-stage proof remains conditional on real evidence; do not force a signal.  
SUCCESS_CRITERIA: Strict schema accepts the actual producer, correlation survives pre/post, and no publication is inferred from candidate/logging success.  
FAILURE_TRIGGERS: Dropped lineage, weaker schema, false EMITTED, altered strategy gates, provider/broker changes, deployment/feed failure.  
APPROVAL_STATUS: Bounded correctness repair within the Owner's existing continuation/testing authorization. No approval of numeric calibration or signal distribution is inferred.
