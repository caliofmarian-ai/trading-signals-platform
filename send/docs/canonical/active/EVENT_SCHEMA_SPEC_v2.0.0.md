# EVENT_SCHEMA_SPEC_v2.0.0.md

BinaryBot — Canonical Event Envelope, Correlation & Domain Schema Specification  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md

Linked Documents:
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 0. PURPOSE

This document defines the canonical schema contract for structured events emitted by BinaryBot.

It governs:
- the common event envelope
- cross-domain correlation rules
- canonical event-family naming
- required versus optional fields
- privacy and integrity rules
- minimum schema obligations by observability domain

The older document correctly established several strong foundations:
- append-only structured JSONL logging
- common event envelope
- global unique event IDs
- stable signal identity across lifecycle stages
- dedup keys
- counter correctness constraints
- the principle that if it is not logged, it did not happen

Those foundations remain valid.

However, the older version is no longer sufficient because it is still framed around the older architecture:
- fixed tier vocabulary instead of governed route vocabulary
- flatter event taxonomy
- weaker separation between decision audit, telemetry, distribution, outcome and admin/control domains
- older linked-document references
- less explicit support for multi-truth analytics and governance-grade reconstruction

This v2.0.0 specification preserves the good invariants while upgrading the schema model to the current canonical stack.

---

## 1. CORE PRINCIPLES

1. Every materially relevant event must be structurally representable.
2. Every event must be reconstructable in context.
3. No silent mutation of governed state is allowed.
4. No ambiguous identity is allowed for signal-lifecycle events.
5. Schema must support forensic reconstruction, analytics and governance.
6. Schema must not leak secrets or unnecessary personal data.
7. Schema evolution requires versioning discipline.
8. Schema is a semantic contract, not merely a file-format convenience.

---

## 2. CANONICAL POSITION IN THE STACK

The event schema layer sits underneath observability and analytics as the common structural contract.

High-level relation:

`Runtime Behavior -> Structured Event Emission -> Persisted Observability -> Reconciliation -> Analytics -> Research / Intelligence / Governance`

This document does not define:
- which storage backend must be used
- which file names must exist
- how reports are rendered
- how dashboards look

It defines the shape and meaning of the events those layers depend on.

---

## 3. EVENT MODEL OVERVIEW

Every event is composed of:

1. **Common envelope**  
   Global fields shared by all event families.

2. **Correlation context**  
   Identity and linkage fields that allow reconstruction across domains.

3. **Domain payload**  
   Event-family-specific semantic fields.

4. **Integrity and privacy constraints**  
   Hard rules that govern what may and may not be emitted.

---

## 4. COMMON EVENT ENVELOPE

All canonical events must include a common envelope.

### 4.1 Required common fields

- `event_id` (string)  
  Globally unique event identifier. UUID4-style generation remains recommended.

- `event_type` (string)  
  Canonical semantic event family.

- `schema_version` (string)  
  Example: `"2.0.0"`.

- `ts_utc` (string, ISO 8601 UTC with `Z`)  
  Example: `"2026-03-15T10:15:12.345Z"`.

- `ts_epoch_ms` (integer)  
  Millisecond epoch timestamp.

- `service` (string)  
  Baseline value: `"binarybot"`.

- `env` (string)  
  Example families: `"prod"`, `"staging"`, `"dev"`.

- `run_id` (string)  
  Runtime/session identifier for the current process lifecycle.

- `source` (object)  
  Minimum expected fields:
  - `module` (string)
  - `function` (string)
  - `line` (integer, optional)

- `host` (object)  
  Minimum expected fields:
  - `hostname` (string)
  - `pid` (integer)
  - `app_version` (string)
  - `git_sha` (string, optional)

### 4.2 Recommended common fields

- `ts_local` (string, ISO 8601 with timezone offset)
- `trace_id` (string)
- `severity` (enum where applicable)
- `algo` (object) for strategy-related domains:
  - `algo_version` (string)
  - `params_hash` (string, optional)
  - `params_hash8` (string, optional)

### 4.3 Optional correlation-capable fields commonly reused across domains

- `signal_id` (string)
- `symbol` (string)
- `timeframe` (string)
- `candle_ts_utc` (string)
- `candle_ts_epoch` (integer)
- `route` (string)
- `destination_id` (int|string)
- `stage` (string)
- `user_id` (int|string)
- `admin_actor_id` (int|string)
- `message_id` (integer)
- `thread_id` (integer)

Not every event requires all of them, but any event must contain enough context to be interpreted correctly.

---

## 5. CANONICAL EVENT FAMILIES

The canonical schema layer recognizes the following major event families.

### 5.1 System lifecycle
- `engine_start`
- `engine_stop`
- `recovery_started`
- `recovery_completed`
- `dependency_degraded`
- `config_load_error`

### 5.2 Decision / strategy
- `decision_evaluated`
- `decision_promoted`
- `decision_rejected`
- `decision_no_signal`

### 5.3 Signal lifecycle / execution
- `signal_emitted`
- `signal_stage_visible`
- `signal_closed`
- `duplicate_suppressed`

### 5.4 FSM / state
- `fsm_transition`

### 5.5 Distribution / route governance
- `route_publish_attempt`
- `route_publish_result`
- `route_reset`
- `route_state_changed`
- `route_mapping_invalid`

### 5.6 Outcome / reconciliation
- `outcome_submission_attempt`
- `outcome_submission_result`
- `outcome_reconciled`
- `membership_verification_failed`

### 5.7 Admin / control
- `admin_change`
- `guarded_action_review`
- `feature_toggle_changed`

### 5.8 Warning / anomaly / error
- `warning`
- `anomaly`
- `error`
- `invariant_breach`

---

## 6. ENUMERATION BASELINES

This section defines the canonical baseline enums that other documents may narrow or extend.

### 6.1 Engine mode
- `WIDE_SCAN`
- `FOCUS_MODE`

### 6.2 Signal stage
- `PRE`
- `CONFIRM`
- `OPEN_NOW`

### 6.3 Decision result family
- `PRE`
- `CONFIRM`
- `OPEN_NOW`
- `REJECT`
- `NO_SIGNAL`

### 6.4 Route state
- `ACTIVE`
- `SILENT`
- `DISABLED`

### 6.5 Publish result
- `PUBLISHED`
- `SKIPPED_SILENT`
- `SKIPPED_LIMIT`
- `SKIPPED_DISABLED`
- `FAILED`
- `DUPLICATE_SUPPRESSED`

### 6.6 Outcome
- `WIN`
- `LOSE`
- `MISSED`

### 6.7 Severity
- `INFO`
- `WARN`
- `ERROR`
- `CRITICAL`

### 6.8 Session
- `ASIA`
- `LONDON`
- `NY`
- `UNKNOWN`

The baseline business route family remains:
- `FREE`
- `BASIC`
- `PRO`
- `ELITE`

However, schema fields should now prefer route-oriented naming over older tier-oriented naming wherever the architecture has already migrated.

---

## 7. CORRELATION RULES

### 7.1 Event identity
Every event must have a globally unique `event_id`.

### 7.2 Signal identity
The same trade idea must preserve the same `signal_id` across:
- PRE
- CONFIRM
- OPEN_NOW
- downstream distribution events
- outcome/reconciliation events where applicable

This remains a hard invariant from the older document and is preserved unchanged.

### 7.3 Trace identity
When multiple events belong to the same logical runtime flow, `trace_id` should be used to connect them.

### 7.4 Domain linkage
A visible Telegram delivery, for example, should be linkable to:
- upstream decision evidence
- route publish evidence
- any relevant timing evidence
- eventual outcome evidence

### 7.5 Minimum contextual sufficiency
If an event lacks enough fields to be interpreted or correlated, that is a schema quality failure even if the JSON itself is syntactically valid.

---

## 8. PRIVACY AND DATA-MINIMIZATION RULES

Hard rules:
- no secrets
- no tokens
- no API keys
- no raw credentials
- no usernames, personal names or phone numbers unless a future explicit policy allows it
- no public exposure of user-identifiable data

Allowed where operationally necessary:
- Telegram numeric IDs such as `user_id`, `admin_actor_id`, `destination_id`

These IDs must remain in governed private observability paths only.

---

## 9. SCHEMA EVOLUTION RULES

Schema changes require:
- version bump
- explicit migration awareness
- updated linked-document references where relevant
- preservation or documented supersession of prior invariants

Additive evolution is preferred over breaking ambiguity.
If semantic meaning changes, versioning must make that visible.

---

## 10. DOMAIN PAYLOAD CONTRACTS

This section defines the minimum payload expectations for the major event families.

---

## 11. SYSTEM LIFECYCLE EVENTS

### 11.1 `engine_start`
Required payload examples:
- `engine_mode`
- `loop_interval_ms`
- `symbols_selected_count`
- `buffer_mode`
- `config_loaded` or equivalent configuration-health summary
- `startup_snapshot` (recommended)

### 11.2 `engine_stop`
Required payload examples:
- `reason`
- `uptime_sec`
- `last_engine_mode`

### 11.3 `recovery_started` / `recovery_completed`
Required payload examples:
- `recovery_scope`
- `reason`
- `result`
- `degraded_components` where relevant

---

## 12. DECISION EVENTS

### 12.1 `decision_evaluated`
Required contextual fields:
- `symbol`
- `timeframe`
- candle context (`candle_ts_utc` and/or `candle_ts_epoch`)

Required payload examples:
- `decision_result`
- `score_total` where relevant
- `buffer_mode`
- `expiry_min` where relevant
- `session`
- gate objects or equivalent structured evaluation evidence
- dedup context

### 12.2 `decision_promoted`
Used when a candidate is promoted into PRE, CONFIRM or OPEN_NOW.
Required payload examples:
- `decision_result`
- `signal_id`
- `score_total`
- `promotion_reason` or equivalent structured context

### 12.3 `decision_rejected`
Required payload examples:
- `rejection_reason`
- `rejection_class`
- relevant gate evidence
- optional score context

### 12.4 `decision_no_signal`
Used when evaluation completes with no signal and without a meaningful rejection class.

---

## 13. SIGNAL LIFECYCLE EVENTS

### 13.1 `signal_emitted`
Required contextual fields:
- `signal_id`
- `symbol`
- `timeframe`
- candle context

Required payload examples:
- `stage`
- `direction`
- `buffer_mode`
- `buffer_value`
- `expiry_min`
- `score_total`
- `engine_mode`
- dedup object

### 13.2 `signal_stage_visible`
Used when a lifecycle stage becomes externally visible via governed delivery.

Required payload examples:
- `signal_id`
- `stage`
- `route`
- `destination_id`
- `message_id` where successful
- `visibility_result`

### 13.3 `signal_closed`
Used when the lifecycle is operationally closed.

Required payload examples:
- `signal_id`
- `close_reason`
- `close_ts_utc`

---

## 14. FSM / STATE EVENTS

### 14.1 `fsm_transition`
Required payload examples:
- `from_state`
- `to_state`
- `reason`
- `watchlist_size` where relevant
- `focus_symbols` where relevant
- `cooldown_until_utc` where relevant
- invariant checks or equivalent state-safety evidence
- `persisted` where relevant

---

## 15. DISTRIBUTION / ROUTE EVENTS

### 15.1 `route_publish_attempt`
Required contextual fields:
- `route`
- `signal_id`
- `stage`
- `destination_id`

Required payload examples:
- `route_state_before`
- `counter_before`
- `limit`
- destination mapping status
- dedup context

### 15.2 `route_publish_result`
Required payload examples:
- `publish_result`
- `route_state_before`
- `route_state_after`
- `counter_before`
- `counter_after`
- `counted`
- transport result object
- dedup object

### 15.3 `route_reset`
Required payload examples:
- `reset_reference`
- `effective_date`
- per-route before/after counters and states
- `idempotent`
- `persisted`

### 15.4 `route_state_changed`
Required payload examples:
- `route`
- `from_state`
- `to_state`
- `reason`

### 15.5 `route_mapping_invalid`
Required payload examples:
- `route`
- `mapping_status`
- `reason`

---

## 16. OUTCOME EVENTS

### 16.1 `outcome_submission_attempt`
Required contextual fields:
- `signal_id`
- `user_id`
- route or entitlement context where relevant

Required payload examples:
- `outcome`
- `vote_window` or outcome-eligibility window
- `submission_channel`
- `membership_check_result` where relevant

### 16.2 `outcome_submission_result`
Required payload examples:
- `accepted`
- `rejected_reason` where relevant
- policy context
- aggregate-after snapshot where relevant

### 16.3 `outcome_reconciled`
Required payload examples:
- `signal_id`
- `operational_outcome`
- `telemetry_outcome` where available
- `discrepancy_status`
- `reconciliation_result`

### 16.4 `membership_verification_failed`
Required payload examples:
- `route`
- `user_id`
- `failure_reason`

---

## 17. ADMIN / CONTROL EVENTS

### 17.1 `admin_change`
Required contextual fields:
- `admin_actor_id`

Required payload examples:
- `action`
- `before`
- `after`
- `scope`
- proof object
- `persisted`

### 17.2 `guarded_action_review`
Required payload examples:
- `action`
- `requested_by`
- `review_result`
- `reason`

### 17.3 `feature_toggle_changed`
Required payload examples:
- `toggle_name`
- `before`
- `after`
- `scope`
- `persisted`

---

## 18. WARNING / ANOMALY / ERROR EVENTS

### 18.1 `warning`
Required payload examples:
- `severity`
- `code`
- `message`
- `context`

### 18.2 `anomaly`
Required payload examples:
- `code`
- `message`
- `suspected_impact`
- `context`

### 18.3 `error`
Required payload examples:
- `severity`
- `error_type`
- `message`
- `stack` where available
- `context`

### 18.4 `invariant_breach`
Required payload examples:
- `invariant_name`
- `breach_reason`
- `context`
- `severity`

---

## 19. DEDUPLICATION RULES

Canonical dedup baselines:
- engine-side dedup: `symbol + candle_ts + stage`
- distribution-side dedup: `route + signal_id + stage`

Every dedup-relevant event should record:
- dedup key or dedup class
- whether duplicate was detected
- action taken

Duplicate suppression must be visible.

---

## 20. COUNTER / ENTITLEMENT INTEGRITY RULE

Only successful OPEN_NOW publication to a limited governed route may consume entitlement.

Schema fields involved in proving this should include:
- `stage`
- `publish_result`
- `counted`
- `counter_before`
- `counter_after`
- `route`

---

## 21. PERSISTENCE / STORAGE COMPATIBILITY

JSONL append-only storage split by domain remains an acceptable implementation pattern.

However, this schema document does not require a specific file split.
It only requires that whichever storage or stream is used:
- preserves append-style reconstruction where needed
- does not silently erase historical evidence
- keeps domain meaning structurally intact

---

## 22. INTEGRITY RULES

Hard rules preserved and expanded:

1. `signal_id` must remain stable across the same trade idea lifecycle.
2. Dedup logic must be observable.
3. Entitlement/counter mutation must be provable.
4. Persisted events must not be silently rewritten.
5. Governed state mutations must be reconstructable.
6. Schema-invalid events must not be treated as trustworthy canonical evidence.

---

## 23. MIGRATION NOTES FROM THE LEGACY VERSION

The legacy `EVENT_SCHEMA_SPEC.md` established an excellent structural base:
- common event envelope
- required event IDs and timestamps
- explicit enums
- core event families
- append-only JSONL discipline
- signal identity stability
- dedup rules
- counter correctness constraints
- privacy limits around user data

This v2.0.0 specification preserves those strengths while upgrading the schema layer to match the new canonical architecture by:
- moving from tier-first terminology toward route-governance terminology
- aligning event families with decision audit, temporal telemetry, distribution governance and admin control
- supporting multi-truth analytics
- improving support for reconciliation and governance-grade reconstruction
- updating linked canonical references to the v2 document stack

---

End of EVENT_SCHEMA_SPEC_v2.0.0.md
