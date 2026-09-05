# R-018 Event Compatibility Matrix

| Event family | Schema/version handling | Current producer | Auditor relevance | Normalization/report rule | Status |
|---|---|---|---|---|---|
| `decision_evaluated` | Canonical v3 primary (`3.0.0`) | `send/core/signal_engine.py` | Primary decision metric input | Normalize into one internal audit-decision record with authoritative field precedence, warning capture, deterministic primary reject reason, full reject multiplicity preservation, and `event_id` dedup | PRIMARY |
| `decision` | Explicit legacy compatibility only | historical / legacy logs | Backward-compatible metric input | Normalize only through the legacy adapter; never outranks canonical v3 for the same `event_id` | LEGACY |
| Any schema-defined non-decision event family (for example `engine_start`, `engine_stop`, `dependency_degraded`, `duplicate_suppressed`, `fsm_transition`, `signal_execution_result`, `signal_closed`, `tier_publish`, `tier_reset`, route/admin/outcome/error families) | Recognized from `send/schema/event_schema.json` using supported schema versions | runtime-specific | Non-decision evidence only | Count in `recognized_non_decision_event_counts` / `supporting_event_counts`; never increment `decisions`; never mark as unknown only because the auditor ignores it for decision metrics | RECOGNIZED NON-DECISION |
| Unknown event families absent from current schema | Any | any | Not metric input | Never crash; record in `unsupported_event_types` | UNSUPPORTED SAFE |
| Unsupported schema versions on decision or recognized non-decision events | Any non-supported schema | any | Not metric input | Never coerce into current truth; record in `unsupported_schema_versions` | UNSUPPORTED SAFE |
| Malformed decision evidence | Missing required normalization inputs or invalid authority state | any | Not metric input if unusable | Exclude from metrics, count in `malformed_or_unusable_decision_events`, retain sample reasons | FAIL-CLOSED |
