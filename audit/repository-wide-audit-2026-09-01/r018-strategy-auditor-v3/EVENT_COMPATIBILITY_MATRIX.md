# R-018 Event Compatibility Matrix

| Event family | Schema/version handling | Current producer | Auditor relevance | Normalization/report rule | Status |
|---|---|---|---|---|---|
| `decision_evaluated` | Canonical v3 primary (`3.0.0`) | `send/core/signal_engine.py` | Primary decision metric input | Normalize into one internal audit-decision record with authoritative field precedence, warning capture, and `event_id` dedup | PRIMARY |
| `decision` | Explicit legacy compatibility only | historical / legacy logs | Backward-compatible metric input | Normalize only through the legacy adapter; never outranks canonical v3 for the same `event_id` | LEGACY |
| `candidate_detected` | v3 supporting family | future/current runtime where materialized | Supporting evidence only | Count as supporting event family; never counted as a decision | SUPPORTED NON-METRIC |
| `decision_promoted` | v3 supporting family | future/current runtime where materialized | Supporting evidence only | Count as supporting event family; never counted as a decision | SUPPORTED NON-METRIC |
| `decision_rejected` | v3 supporting family | future/current runtime where materialized | Supporting evidence only | Count as supporting event family; never counted as a decision | SUPPORTED NON-METRIC |
| `decision_no_signal` | v3 supporting family | future/current runtime where materialized | Supporting evidence only | Count as supporting event family; never counted as a decision because `decision_evaluated` remains the metric authority | SUPPORTED NON-METRIC |
| `fsm_transition` | v3 supporting family | `send/core/signal_engine.py` / FSM log | Supporting evidence only | Surface in compatibility metadata only | SUPPORTED NON-METRIC |
| `signal_execution_result` | v3 supporting family | `send/core/signal_engine.py` | Supporting evidence only | Surface in compatibility metadata only | SUPPORTED NON-METRIC |
| `signal_stage_visible`, `route_publish_attempt`, `route_publish_result` | v3 supporting families | distribution runtime | Supporting evidence only | Surface in compatibility metadata only when present | SUPPORTED NON-METRIC |
| Unknown event families | Any | any | Not metric input | Never crash; record in `unsupported_event_types` | UNSUPPORTED SAFE |
| Unsupported decision schema versions | Any non-supported schema | any | Not metric input | Never coerce into v3/legacy truth; record in `unsupported_schema_versions` | UNSUPPORTED SAFE |
| Malformed decision evidence | Missing required normalization inputs or invalid authority state | any | Not metric input if unusable | Exclude from metrics, count in `malformed_or_unusable_decision_events`, retain sample reasons | FAIL-CLOSED |
