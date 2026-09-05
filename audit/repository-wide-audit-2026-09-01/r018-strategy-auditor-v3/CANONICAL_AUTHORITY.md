# R-018 Canonical Authority

The following active canonical files were inspected before implementation:

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

## Governing conclusions applied

- Canonical v3 event truth uses `decision_evaluated` as the primary pre-FSM strategy audit event.
- Event identity is `event_id`, not `signal_id`.
- `signal_id` remains lifecycle correlation and must not collapse distinct evaluations by itself.
- `REJECT` and `NO_SIGNAL` remain distinct decision outcomes.
- Rejection evidence must remain explicit and reconstructable.
- Signal execution and distribution events remain supporting evidence, not strategy-decision counts.
- Legacy generic event names may remain only through explicit compatibility adapters.
