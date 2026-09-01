# FAILURE_RECOVERY_SPEC_v2.0.0.md

BinaryBot — Failure Recovery, Restart Safety, State Restoration & Degraded-Mode Governance  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/FAILURE_RECOVERY_SPEC_v2.0.0.md

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 0. PURPOSE

This document defines the canonical failure-recovery model for BinaryBot.

It governs:
- restart safety
- persisted-state restoration
- corruption handling
- degraded-mode operation
- idempotent recovery behavior
- fallback/backup restoration policy
- recovery observability requirements
- operational restrictions during impaired system states

The legacy document established an important operational base:
- restore state from disk on restart
- avoid duplicate sends after restart
- preserve counters and route state
- keep reset idempotent
- log failures append-only
- prefer fail-safe behavior over silent continuation
- use backup fallback when primary state is corrupted fileciteturn63file0

Those foundations remain correct.

However, the old version is no longer sufficient because it is still oriented around the older tier/channel framing and does not fully express the current canonical architecture:
- route-governance terminology is incomplete
- degraded-mode governance is not explicit enough
- recovery event semantics are weaker than the current observability stack
- invariant-breach escalation is under-specified
- admin/control implications during impaired operation are not fully defined
- linked references point to an older document graph fileciteturn63file0

This v2.0.0 specification preserves the strong legacy safeguards while aligning recovery behavior to the current canonical stack.

---

## 1. DESIGN PRINCIPLES

1. Recovery must prefer correctness over liveness.
2. No restart may silently create duplicate user-visible signals.
3. Persisted governed state must not be guessed when evidence is missing.
4. Corrupted critical state must trigger bounded safe behavior, not hidden continuation.
5. Recovery actions must be observable and reconstructable.
6. Degraded operation must be explicit, bounded and reviewable.
7. Recovery must be idempotent where repetition is plausible.
8. Backup restoration must never silently overwrite potentially newer valid state.
9. Failure domains must be isolated as much as practical.
10. Admins must be able to understand whether the system is healthy, degraded, or unsafe.

---

## 2. SCOPE

This document applies to runtime failure and recovery behavior for:
- process restarts
- crash recovery
- partial state corruption
- missing persisted files
- backup fallback use
- stale/ambiguous state restoration
- route/counter restoration
- watchlist/FSM restoration where applicable
- observability continuity across restart
- degraded mode when dependencies or state are impaired

This document does not define:
- business strategy rules
- signal scoring logic
- Telegram UX copy
- low-level storage implementation details beyond recovery obligations

---

## 3. CANONICAL RECOVERY OBJECTIVES

On restart or fault handling, the system must preserve the following goals in order:

1. Prevent unsafe duplicate external actions.
2. Restore trustworthy governed state.
3. Preserve route entitlement/counter correctness.
4. Preserve decision-lifecycle coherence where recoverable.
5. Emit sufficient recovery observability.
6. Resume normal operation only when safety gates pass.

---

## 4. FAILURE DOMAIN MODEL

BinaryBot failure handling must reason about at least these domains:

### 4.1 Process domain
Examples:
- process crash
- forced restart
- uncaught exception
- incomplete shutdown

### 4.2 Persistence domain
Examples:
- missing file
- truncated JSONL
- invalid JSON
- unreadable permissions
- incompatible schema snapshot
- stale backup ambiguity

### 4.3 Governed state domain
Examples:
- route counters missing
- route states missing
- reset reference missing
- dedup state missing
- signal lifecycle continuity uncertain

### 4.4 FSM / temporal state domain
Examples:
- focus watchlist missing
- cooldown timestamps inconsistent
- pending state transition evidence incomplete

### 4.5 Distribution dependency domain
Examples:
- Telegram send unavailable
- destination mapping unavailable
- channel configuration unreadable

### 4.6 Analytics / observability domain
Examples:
- event logs not writable
- recovery logs partially unavailable
- reconciliation inputs missing

### 4.7 Control domain
Examples:
- admin mutation attempted during unsafe degraded mode
- role/scope enforcement unavailable

Each domain may degrade independently. Recovery policy must not assume all failures are equivalent.

---

## 5. RECOVERY STATES

The runtime must conceptually classify itself into one of the following recovery-health states:

### 5.1 `HEALTHY`
All critical persisted state and dependencies pass required safety checks.

### 5.2 `DEGRADED_SAFE`
Some components are impaired, but the bot can continue in a bounded mode without violating critical invariants.

### 5.3 `DEGRADED_RESTRICTED`
The bot may remain up for visibility/admin access, but selected operations must be blocked or partially disabled.

### 5.4 `UNSAFE_BLOCKED`
Critical invariants cannot be trusted; signal production and/or governed delivery must not continue until repaired.

The old document effectively contained this logic implicitly via fail-safe behaviors and startup refusal on grave corruption; v2.0.0 makes the runtime-state model explicit. fileciteturn63file0

---

## 6. STARTUP RECOVERY PHASES

On startup after restart, BinaryBot must conceptually perform the following phases in order.

### 6.1 Phase A — Recovery bootstrap
- initialize run context
- establish recovery trace context
- mark startup as recovery-aware until checks complete

### 6.2 Phase B — Persistence discovery
- inspect required state files/snapshots/logs
- detect absence, corruption, truncation, unreadable files, schema mismatch

### 6.3 Phase C — Primary restore attempt
Attempt restoration from primary canonical persisted state.

### 6.4 Phase D — Backup restore evaluation
If primary state is missing or untrustworthy, evaluate whether a governed backup fallback is permissible.

### 6.5 Phase E — Integrity reconciliation
Reconcile route states, counters, reset references, dedup memory, lifecycle state and FSM snapshots where applicable.

### 6.6 Phase F — Safety gating
Determine whether runtime status is `HEALTHY`, `DEGRADED_SAFE`, `DEGRADED_RESTRICTED`, or `UNSAFE_BLOCKED`.

### 6.7 Phase G — Recovery event emission
Emit recovery observability proving what was restored, skipped, inferred, blocked or repaired.

### 6.8 Phase H — Controlled activation
Only after gates pass may normal operational loops resume.

---

## 7. PRIMARY STATE RESTORATION RULES

### 7.1 Restore-from-primary is preferred
Primary canonical state is the first source of truth for restoration.

### 7.2 Partial success must not be mistaken for full success
If only some state domains restore correctly, the result must be marked partial.

### 7.3 No fabricated state
Missing critical values must not be silently invented merely to allow startup.

### 7.4 Schema-invalid state is untrusted
If persisted state cannot be interpreted under the current expected schema/contract, it must not be treated as authoritative.

### 7.5 Restore evidence is mandatory
For every materially relevant restored domain, observability must show:
- source used
- restore result
- integrity status
- any fallback or degradation applied

---

## 8. BACKUP FALLBACK POLICY

The legacy document correctly required backup fallback to be used carefully instead of silently continuing on corrupted state. fileciteturn63file0

v2.0.0 preserves that rule and strengthens it.

### 8.1 When backup fallback may be considered
Backup fallback may be considered when:
- primary state is missing
- primary state is unreadable
- primary state is structurally corrupt
- primary state is provably unusable for safety gating

### 8.2 When backup fallback must not auto-apply
Backup fallback must not silently auto-apply when:
- backup freshness is ambiguous
- backup may be older than known live state in a safety-critical way
- applying backup would risk duplicate governed actions
- the recovered state would violate current schema/governance expectations

### 8.3 Backup evaluation criteria
At minimum evaluate:
- file presence
- parseability
- schema compatibility
- freshness indicator
- last known reset reference where relevant
- counter plausibility
- route state plausibility
- dedup plausibility

### 8.4 Explicit observability
Whenever backup fallback is used, logs must explicitly show:
- that primary restore failed or was rejected
- why backup was accepted
- what risks remain
- whether the runtime entered degraded mode as a result

---

## 9. DEDUP RESTORATION RULES

The legacy document correctly treated dedup as critical to restart safety. fileciteturn63file0

### 9.1 Engine dedup continuity
If engine dedup continuity cannot be trusted, startup must err on the side of preventing unsafe duplicate signal emission.

### 9.2 Distribution dedup continuity
If route-level publish dedup continuity cannot be trusted, the system must not assume prior sends are safe to repeat.

### 9.3 Unknown dedup state
If dedup state is unknown:
- visible signal production may need to pause
- route publish may need to be restricted
- runtime may enter degraded or blocked mode depending on the blast radius

### 9.4 Dedup reconstruction from evidence
Reconstruction from durable observability may be allowed where sufficiently trustworthy, but inferred reconstruction must be explicitly marked as inferred, not primary.

---

## 10. ROUTE / COUNTER RESTORATION RULES

The legacy document correctly prioritized restoration of counters, route state and idempotent reset semantics. fileciteturn63file0

### 10.1 Route-state restoration
Governed routes must restore with explicit state evidence:
- route identifier
- restored state
- source of restoration
- confidence/trust level

### 10.2 Counter restoration
Counters must restore with before/after proof or source proof sufficient to show:
- current used count
- applicable limit
- reset reference
- bounded consistency

### 10.3 Idempotent reset continuity
Recovery must preserve idempotent reset semantics.
A restart must not accidentally double-reset or fail to respect a reset already applied.

### 10.4 Unknown entitlement correctness
If counter correctness cannot be trusted for limited routes, those routes must be restricted or blocked until corrected.

### 10.5 ELITE / unlimited routes
Unlimited routes may still require route-state validation, but entitlement uncertainty has different blast radius and does not erase the need for delivery safety.

---

## 11. FSM / WATCHLIST / TEMPORAL STATE RESTORATION

Where these domains exist, recovery must evaluate them separately.

### 11.1 FSM restoration
If FSM state is persisted and trusted, it may be restored.
If not trusted, the system may need to re-enter a safe baseline state rather than pretend continuity.

### 11.2 Watchlist restoration
Watchlist state may be restored only if its persistence evidence is trustworthy.

### 11.3 Cooldown restoration
Cooldown timestamps must not be silently discarded if doing so could change runtime behavior materially.

### 11.4 Temporal ambiguity
If temporal state becomes ambiguous across restart, recovery must prefer conservative behavior.

---

## 12. DEGRADATION POLICY

### 12.1 Allowed degraded operation
Degraded operation is allowed only when critical invariants remain protected.

### 12.2 Restricted operations in degraded modes
Depending on the impaired domain, the runtime may restrict:
- signal promotion
- OPEN_NOW publication
- limited-route publication
- outcome acceptance
- admin mutations affecting governed state
- analytics writes that would falsely imply trustworthy completeness

### 12.3 Degraded mode is not silent normal mode
Degraded mode must be visible to operators and observable in logs.

### 12.4 Escalation
If degradation worsens or crosses invariant boundaries, runtime state must escalate to `DEGRADED_RESTRICTED` or `UNSAFE_BLOCKED`.

---

## 13. UNSAFE-BLOCK CONDITIONS

Runtime must be able to refuse or block unsafe operation when any of the following hold:

- critical governed state is corrupted and cannot be safely restored
- route entitlement correctness for limited routes is untrustworthy
- dedup continuity is sufficiently broken that duplicate visible actions cannot be bounded
- route mapping/configuration is broken in a way that makes governed publication unsafe
- event persistence is so impaired that critical safety events would become unobservable
- invariant-breach severity reaches a level defined by `SYSTEM_INVARIANTS_v2.0.0.md`

The legacy document’s refusal-to-start behavior on severe corruption remains canonical; this section formalizes it more explicitly. fileciteturn63file0

---

## 14. RECOVERY OBSERVABILITY REQUIREMENTS

Recovery must be first-class observable behavior, not a hidden implementation detail.

At minimum, observability must support these event families:
- `recovery_started`
- `recovery_completed`
- `dependency_degraded`
- `config_load_error`
- `warning`
- `error`
- `invariant_breach`

Recovery observability must record, where relevant:
- recovery trace/run identifiers
- startup phase
- state domain affected
- source used for restoration
- primary vs backup decision
- degradation state assigned
- blocked operations
- unresolved risk notes
- final recovery result

This aligns recovery with the current event and observability stack rather than the older minimal failure logging stance. fileciteturn63file0

---

## 15. ADMIN / CONTROL GOVERNANCE DURING IMPAIRED STATES

The older document did not sufficiently define how admin/control actions interact with recovery and degraded operation. v2.0.0 does.

### 15.1 Read visibility should remain available where possible
Operators should still be able to inspect health, state and recovery evidence during degraded conditions.

### 15.2 Governed mutations may be restricted
If the system is in `DEGRADED_RESTRICTED` or `UNSAFE_BLOCKED`, certain admin mutations may need to be blocked or specially reviewed.

### 15.3 No hidden repair
Manual or admin-triggered repairs affecting governed state must be logged as governed changes, not performed silently.

### 15.4 Recovery-related admin actions require observability
Any manual restore, counter correction, route-state correction, force-unblock or recovery bypass must emit auditable control evidence.

---

## 16. IDEMPOTENCY RULES

The legacy document correctly emphasized idempotent reset and duplicate-prevention behavior. fileciteturn63file0

v2.0.0 expands that principle.

Operations that should be idempotent where feasible:
- startup recovery classification
- reset application
- backup evaluation
- certain state restoration writes
- guarded repair operations

Repeated execution of the same recovery step should not create inconsistent governed state.

---

## 17. FAIL-SAFE DEFAULTS

When certainty is insufficient, the runtime should default to safer behavior such as:
- refusing limited-route publication
- suppressing externally visible duplicate-prone actions
- remaining available only for health/admin inspection
- entering blocked mode pending repair

Fail-safe must not mean silent failure. It must remain observable and reviewable.

---

## 18. MINIMUM PERSISTED ARTIFACT EXPECTATIONS

Implementation may vary, but the recovery model assumes persistence exists for the domains that matter operationally, such as:
- route state / counters
- reset reference or equivalent daily/periodic boundary evidence
- dedup-relevant state or durable reconstructable evidence
- FSM/watchlist state where materially required
- append-only observability logs for forensic reconstruction

This does not mandate exact filenames, but it does require that the architecture provide durable evidence sufficient for safe recovery.

---

## 19. INVARIANT ALIGNMENT

Failure and recovery behavior must remain subordinate to `SYSTEM_INVARIANTS_v2.0.0.md`.

In particular:
- recovery cannot waive signal identity invariants
- recovery cannot silently waive entitlement correctness
- recovery cannot silently waive observability of governed state changes
- recovery cannot turn unknown state into assumed safe state

If recovery logic conflicts with an invariant, the invariant wins.

---

## 20. TEST / VALIDATION EXPECTATIONS

Canonical recovery behavior should be validated against scenarios such as:
- clean restart
- restart after crash during publish
- missing primary state
- corrupted primary with valid backup
- corrupted primary and stale/invalid backup
- missing route counters
- ambiguous dedup state
- invalid route mapping on startup
- impaired event-log sink
- manual admin repair after blocked startup

This document defines the required behavior class, even if exact test implementation lives elsewhere.

---

## 21. MIGRATION NOTES FROM THE LEGACY VERSION

The legacy `FAILURE_RECOVERY_SPEC.md` established strong operational truths:
- restart safety matters
- dedup must survive restart
- route/tier counters and states must be restored
- reset semantics must be idempotent
- append-only failure logging matters
- backup fallback exists
- severe corruption may justify startup refusal fileciteturn63file0

This v2.0.0 specification preserves those truths while upgrading the model to:
- explicit recovery-health states
- route-governance terminology
- stronger degraded-mode governance
- better admin/control integration
- canonical recovery event families
- more explicit invariant alignment
- cleaner linkage to the modern v2 document stack

---

End of FAILURE_RECOVERY_SPEC_v2.0.0.md
