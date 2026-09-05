# R-018 Canonical Authority

The following active canonical files were re-inspected for the hardening pass:

- `send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md`
- `send/docs/canonical/active/EVENT_SCHEMA_SPEC_v3.0.0.md`
- `send/docs/canonical/active/DECISION_AUDIT_SPEC_v3.0.0.md`
- `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `send/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `send/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `send/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `send/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `send/docs/canonical/active/OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `send/docs/canonical/active/SYSTEM_INVARIANTS_v3.0.0.md`
- `send/schema/event_schema.json`
- `send/core/observability_logger.py`
- `send/core/signal_engine.py`
- `send/core/strategy_v2.py`

## Governing conclusions applied

- Canonical v3 decision truth remains `decision_evaluated`.
- Schema-recognized event families must be distinguished from truly unknown event types even when the auditor does not count them as decisions.
- Event identity for auditor deduplication remains `event_id`, not `signal_id`.
- `signal_id` remains lifecycle correlation and must not collapse distinct evaluations.
- `REJECT` and `NO_SIGNAL` remain distinct decision outcomes.
- Backward-compatible reject analytics continue to use one deterministic primary reason per rejected decision.
- Full blocker/reason multiplicity must remain separately visible.
- Legacy generic event names remain explicit compatibility only and are not primary truth.
