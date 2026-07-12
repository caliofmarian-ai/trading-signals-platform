# SYSTEM_INVARIANTS_v2.0.0.md

BinaryBot — Non-Negotiable System Invariants  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/SYSTEM_INVARIANTS_v2.0.0.md

Linked Documents:
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 0. PURPOSE

This document defines the absolute, non-negotiable truths of the BinaryBot system.

An invariant is a rule that must not be violated by:
- runtime behavior
- operator actions
- admin mutations
- recovery logic
- analytics assumptions
- documentation drift
- deployment shortcuts

If an invariant is breached, the system must treat the breach as a governance-grade integrity event, not merely a local bug.

The legacy document already established a strong base:
- determinism
- documentation supremacy
- FSM hard limits
- signal gating discipline
- logging obligations
- risk gates
- deployment backups
- tier-limit enforcement
- outcome constraints
- traceability expectations
- freeze-mode requirement fileciteturn66file0

Those foundations remain valid.

However, the legacy version is no longer sufficient because:
- it still mixes older tier vocabulary with the newer route-governance direction
- linked references are outdated
- some invariant IDs collide numerically
- the newer architecture truths are not yet stated canonically enough
- decision audit, temporal telemetry, admin/control governance and recovery-state interaction need stronger invariant coverage fileciteturn66file0

This v2.0.0 preserves the legacy safety truths while upgrading the invariant layer to the current canonical stack.

---

## 1. INTERPRETATION RULE

If any lower-level document, code path, operational playbook or admin action conflicts with this document, this document wins.

No convenience exception exists unless this document itself explicitly provides one.

---

## 2. PHILOSOPHICAL / GOVERNANCE INVARIANTS

### INV-001 — Capital Protection First
No feature, tuning change, distribution expansion or operational shortcut may increase trade frequency at the expense of structural safety. This preserves the legacy capital-protection principle. fileciteturn66file0

### INV-002 — Determinism
Given materially identical:
- candles / market inputs
- algorithm version
- parameters
- governed state
- timing context used by the logic

the decision layer must produce materially identical outcomes.
No randomness is allowed in canonical decision logic. This preserves the legacy determinism rule. fileciteturn66file0

### INV-003 — Documentation Supremacy
If code and canonical documentation conflict, canonical documentation is the reference truth and the code path must be corrected. This preserves the legacy rule unchanged. fileciteturn66file0

### INV-004 — No Undocumented Change
Any material logic, governance, route, recovery, analytics or control change without canonical documentation alignment is a governance breach. This upgrades and preserves the legacy undocumented-change rule. fileciteturn66file0

### INV-005 — No Emotional Tuning
Parameter or policy changes must not be driven by frustration, fear, euphoria, revenge tuning or anecdotal loss streak reaction. This preserves the legacy no-emotional-tuning truth. fileciteturn66file0

---

## 3. ARCHITECTURE ORDER INVARIANTS

### INV-010 — DecisionObject Before FSM
DecisionObject must be produced before FSM/state transition handling for a candidate opportunity.
FSM may consume decision evidence; it may not replace the decision layer as the origin of trade candidacy.

### INV-011 — Corridor Engine Before Time Model
Corridor / structural actionability evaluation must precede the time model in the strategic pipeline.
Time feasibility evaluates a candidate already shaped by corridor/actionability context; it must not canonically invert that order.

### INV-012 — Route Governance Terminology Is Canonical
Where the architecture has migrated, route-governance terminology is canonical.
Legacy tier wording may still exist in deprecated documents or transition notes, but active canonical logic must not rely on ambiguous vocabulary.

---

## 4. DECISION / OPPORTUNITY INVARIANTS

### INV-020 — Threshold Hierarchy
PRE ≤ CONFIRM ≤ OPEN_NOW.
OPEN_NOW threshold must never be lower than PRE. This preserves the legacy threshold hierarchy rule. fileciteturn66file0

### INV-021 — No OPEN_NOW Without PRE Path
OPEN_NOW must only occur through the canonical lifecycle path and must not arise directly from IDLE-like discovery context. This preserves the legacy rule while using current naming. fileciteturn66file0

### INV-022 — OPEN_NOW Requires Valid Focus Qualification
A symbol may reach OPEN_NOW only if valid focus/watchlist qualification exists at emission time. Directional bias alone is insufficient. This preserves the legacy rule. fileciteturn66file0

### INV-023 — Buffer Reachability Required
OPEN_NOW is forbidden unless the required move/buffer traversal is realistically reachable before expiry. This preserves the legacy reachability requirement. fileciteturn66file0

### INV-024 — Expiry Feasibility Required
OPEN_NOW is forbidden unless the expected move remains operationally feasible inside the remaining expiry window. This preserves the legacy rule. fileciteturn66file0

### INV-025 — Focus Context Governs Actionability
Wide scan may discover PRE opportunities.
CONFIRM and OPEN_NOW require valid focus/watchlist context for actionable execution. This preserves the legacy separation between discovery and actionability. fileciteturn66file0

### INV-026 — Same Opportunity Must Not Be Fully Recomputed On Every Tick
The same underlying opportunity must not be treated as a brand-new full decision candidate on every scheduler tick unless material context changed. This preserves the legacy anti-redundant-recompute rule. fileciteturn66file0

### INV-027 — Decision Identity Must Be Stable
A decision opportunity must have stable operational identity from canonical fields such as symbol, candle timestamp, direction and stage/context. This preserves the legacy decision identity rule. fileciteturn66file0

### INV-028 — Decision Freeze Window Required
After evaluation, a bounded freeze window must suppress redundant full recomputation for the same opportunity unless material context changes. This preserves the legacy freeze-window rule. fileciteturn66file0

### INV-029 — Material Context Change Reopens Evaluation
Reevaluation is allowed only when material context changes, such as new candle, direction flip, focus-context change, meaningful score delta, feasibility change or canonical stage upgrade path. This preserves the legacy reopen condition. fileciteturn66file0

### INV-030 — Rejection Evidence Must Exist
A materially rejected opportunity must produce auditable rejection evidence sufficient for later forensic and analytics interpretation.
No meaningful rejection may disappear as an unobservable non-event.

---

## 5. FSM / FOCUS / WATCHLIST INVARIANTS

### INV-040 — Max Watchlist Size
Watchlist size must remain ≤ 2 at all times. This preserves the legacy hard limit. fileciteturn66file0

### INV-041 — Focus Capacity Hard Limit
No more than 2 focus/watchlist symbols may be active simultaneously.
Replacement is allowed only if capacity remains ≤ 2 and the change is auditable. This preserves the legacy rule. fileciteturn66file0

### INV-042 — No LIVE Outside Valid Focus Context
OPEN_NOW must not occur for a symbol outside valid focus/watchlist context. This preserves the legacy rule with current stage wording. fileciteturn66file0

### INV-043 — Cooldown Absolute Block
If a symbol is in cooldown, it must not emit PRE, CONFIRM or OPEN_NOW. This preserves the legacy rule. fileciteturn66file0

### INV-044 — Deterministic Focus Slot Release
A focus symbol must be released when canonical focus exit conditions occur.
Stuck focus without lifecycle support is an invariant breach. This preserves the legacy rule. fileciteturn66file0

### INV-045 — Focus Lease Mandatory
Any symbol entering focus/watchlist context must receive a bounded operational lease with enter time, TTL and expiry reason. This preserves the legacy lease concept. fileciteturn66file0

### INV-046 — Forced Focus Eviction Outside Active Universe
A symbol outside the active symbol universe must be forcibly evicted from focus/watchlist context. This preserves the legacy rule. fileciteturn66file0

### INV-047 — Forced Focus Eviction On Lease Expiry
Expired focus must not remain resident by inertia. This preserves the legacy rule. fileciteturn66file0

### INV-048 — Watchlist Residency Must Match Operational Eligibility
A symbol may remain in focus/watchlist only while operational eligibility remains true. This preserves the legacy rule. fileciteturn66file0

### INV-049 — Focus Must Not Fully Starve Wide Scan
Focus may receive priority, but it must not eliminate ongoing wide scan coverage. This preserves the legacy rule. fileciteturn66file0

---

## 6. SIGNAL LIFECYCLE INVARIANTS

### INV-060 — One OPEN_NOW Per Symbol-Candle Opportunity
For a given symbol and candle opportunity, only one OPEN_NOW may become externally visible.
Duplicate detection failure is a critical breach. This preserves and modernizes the legacy one-live-per-candle rule. fileciteturn66file0

### INV-061 — Signal Identity Must Remain Stable Across Lifecycle
The same trade idea must preserve a stable signal identity across PRE, CONFIRM, OPEN_NOW, governed distribution and outcome/reconciliation where applicable.

### INV-062 — No Hidden Signal Events
A signal must never become visible externally without corresponding structured observability. This preserves the legacy no-hidden-signal truth. fileciteturn66file0

### INV-063 — Telegram and Logs Must Match
If Telegram shows a governed signal stage, corresponding decision/FSM/distribution evidence must exist.
If logs claim externally visible signal delivery that did not actually occur, this is a critical inconsistency. This preserves the legacy matching rule. fileciteturn66file0

### INV-064 — Signal Lifecycle Must Be Traceable
Each signal must produce a reconstructable chain across decision, state transition, governed distribution and outcome/reconciliation where applicable. This preserves the legacy traceability rule. fileciteturn66file0

---

## 7. RISK / ACTIONABILITY INVARIANTS

### INV-070 — SR Space Must Exceed Required Buffer
If support/resistance space is smaller than the required actionability buffer, the trade must be rejected. No override allowed. This preserves the legacy rule. fileciteturn66file0

### INV-071 — Feasibility Must Hold
If required movement time exceeds available expiry, the trade must be rejected. This preserves the legacy feasibility rule. fileciteturn66file0

### INV-072 — Spike Active Blocks Trade
If spike filter / instability filter triggers, the trade must be rejected unless a future canonical spec explicitly defines a tightly governed exception. The current legacy truth remains reject-by-default. fileciteturn66file0

### INV-073 — Timing Decay Cannot Be Ignored
A candidate that was once feasible but is no longer feasible because of temporal decay must not remain actionable merely due to stale prior qualification.

---

## 8. PARAMETER / VERSION INVARIANTS

### INV-080 — No Hardcoded Adjustable Constants
Adjustable behavior must be parameterized. Hardcoded operational thresholds are forbidden. This preserves the legacy rule. fileciteturn66file0

### INV-081 — Version Must Match Behavior
Displayed or emitted algorithm version must reflect actual materially deployed behavior. Mismatch is a governance breach. This preserves the legacy rule. fileciteturn66file0

### INV-082 — Material Parameter Change Requires Version Bump
Changing thresholds, multipliers, timing/expiry gates, route-affecting logic or materially relevant gate policy requires version increment. This preserves and expands the legacy rule. fileciteturn66file0

---

## 9. OBSERVABILITY / SCHEMA INVARIANTS

### INV-090 — Every Externally Material Signal Stage Must Be Logged
Each materially relevant PRE / CONFIRM / OPEN_NOW stage must emit the required structured evidence. This preserves the legacy logging requirement in modern wording. fileciteturn66file0

### INV-091 — Errors Must Never Be Silent
Exceptions and materially relevant faults must produce observable error evidence. Silent crash/failure is a critical integrity failure. This preserves the legacy rule. fileciteturn66file0

### INV-092 — Log Format Must Follow Canonical Event Schema
Structured logs must follow the canonical event schema contract.
Malformed or semantically noncanonical logs are observability failures. This preserves the legacy schema rule. fileciteturn66file0

### INV-093 — Governed State Mutation Must Be Observable
Changes to route state, counters, entitlement-relevant state, admin-governed settings or recovery-relevant corrections must not occur silently.

### INV-094 — If It Is Not Logged, It Did Not Happen
For governance-grade interpretation, an unlogged material event has no canonical evidentiary standing.

---

## 10. DISTRIBUTION / ROUTE GOVERNANCE INVARIANTS

### INV-100 — Route Limits Must Be Enforced
Governed distribution must enforce configured route limits and route state rules. This preserves the legacy tier-limit truth in route wording. fileciteturn66file0

### INV-101 — Silent Route Blocks All Stages
If a route is in SILENT state, PRE, CONFIRM and OPEN_NOW must not be published to that route. This preserves the legacy silent-mode rule. fileciteturn66file0

### INV-102 — Unlimited Route Must Not Be Improperly Limited
Unlimited / ELITE-like routes must not be constrained by limited-route counters when canonical policy says they are unrestricted. This preserves the legacy ELITE rule while future-proofing terminology. fileciteturn66file0

### INV-103 — Reset Must Occur Exactly Once Per Canonical Boundary
Route-limit reset must occur exactly once for the defined canonical reset boundary.
Duplicate reset or missed reset is an invariant breach. This preserves the legacy once-daily reset truth while allowing the exact boundary to live in linked specs. fileciteturn66file0

### INV-104 — Counter Consumption Requires Successful Governed Publication
Entitlement/counter consumption may occur only for a successful governed publication under the canonical conditions defined by distribution policy.

### INV-105 — Duplicate Suppression Must Be Visible
If publication is suppressed as duplicate, the suppression must be observable.

---

## 11. OUTCOME / RECONCILIATION INVARIANTS

### INV-110 — One Outcome Submission Per User Per Signal
Each eligible user may submit only one governed outcome per signal unless a future canonical policy explicitly allows a superseding workflow. The current baseline remains one submission. This preserves the legacy rule. fileciteturn66file0

### INV-111 — Outcome Window Must Be Limited
Outcome interaction must be allowed only during the canonical voting/eligibility window. This preserves the legacy rule. fileciteturn66file0

### INV-112 — Outcome UI Must Expire
Outcome UI must be removed, disabled or rendered non-actionable after the window ends. This preserves the legacy rule. fileciteturn66file0

### INV-113 — Outcome Storage Must Be Append-Only
Outcome evidence must be append-only; editing historical outcome evidence is forbidden. This preserves the legacy rule. fileciteturn66file0

### INV-114 — Multi-Truth Reconciliation Must Not Collapse Distinct Evidence Sources
Operational outcome truth, telemetry truth and user-reported truth must not be silently conflated when they materially differ.

---

## 12. PERFORMANCE / ANALYTICS INVARIANTS

### INV-120 — No Drift Without Detection
If materially relevant performance deviates beyond governed tolerance, the system must emit anomaly or equivalent evidence. This preserves the legacy rule. fileciteturn66file0

### INV-121 — No Frequency Explosion Without Causal Explanation
Signal frequency must not drastically increase without a documented causal basis such as versioned parameter or universe change. This preserves the legacy rule. fileciteturn66file0

### INV-122 — Analytics Must Not Invent Missing Truth
Analytics may aggregate, infer and summarize, but must not fabricate unobserved evidence or silently treat unknown as known.

---

## 13. RECOVERY / FAILURE INVARIANTS

### INV-130 — No Recovery Path May Waive Core Safety Invariants
Recovery logic must remain subordinate to invariant safety and may not silently bypass dedup, entitlement correctness, route governance or observability obligations.

### INV-131 — Severe Corruption Must Block Unsafe Continuation
If critical governed state cannot be restored safely, runtime must refuse unsafe continuation. This preserves the legacy recovery truth. fileciteturn66file0

### INV-132 — Backup Fallback Must Not Silently Overwrite Trust
Backup fallback may be used only under governed conditions and must never silently replace potentially newer trustworthy state.

### INV-133 — Degraded Mode Must Be Explicit
If the system is degraded, that degraded status must be operationally and observably explicit.

---

## 14. DEPLOYMENT / CHANGE CONTROL INVARIANTS

### INV-140 — No Deployment Without Backup
All materially modified files or governed state at deployment risk must be backed up before restart or rollout. This preserves the legacy rule. fileciteturn66file0

### INV-141 — No Mixed Version State
Persisted state and deployed logic must remain version-compatible enough for safe operation. Version mismatch that threatens correctness must halt deployment or startup. This preserves the legacy rule. fileciteturn66file0

### INV-142 — Canonical Change Requires Auditability
Material change must be explainable through documentation, observability and deploy/restart audit evidence.

---

## 15. ADMIN / CONTROL INVARIANTS

### INV-150 — No Silent Governed Admin Mutation
Admin actions that affect route state, permissions, thresholds, recovery state, observability posture or governed bot behavior must be auditable.

### INV-151 — Permission Boundaries Must Hold
No admin/control path may exceed the canonical role and permission model.

### INV-152 — Unsafe Override Must Not Be Casual
Any future override-capable control must be tightly governed, explicitly observable and exceptional by design.

---

## 16. SYSTEM FREEZE / SAFETY SWITCH

### INV-160 — Freeze Capability Must Exist
If a critical invariant is violated, the system must support an immediate freeze/safe-stop mode that halts unsafe forward behavior while preserving evidence.
This preserves the legacy freeze-mode truth. fileciteturn66file0

### INV-161 — Freeze Must Preserve Evidence
Safety stop must not erase or hide the evidence that caused it.

---

## 17. PRIORITY ORDER

If multiple components or obligations conflict, the default priority order is:

1. Risk / safety invariants
2. Signal integrity and actionability invariants
3. FSM / focus invariants
4. Distribution / entitlement invariants
5. Observability / schema invariants
6. Recovery / deployment invariants
7. Performance / analytics invariants
8. UX convenience

This preserves the spirit of the legacy priority rule while making signal integrity and observability more explicit. fileciteturn66file0

---

## 18. BREACH CONSEQUENCE MODEL

A material invariant breach must support, as appropriate:
- observable breach evidence
- severity classification
- operational restriction or freeze
- audit trail
- remediation path
- post-incident review

An invariant without breach consequence handling is only a slogan, not a governed invariant.

---

## 19. GUARANTEE STATEMENT

If these invariants are respected, BinaryBot remains structurally governed against:
- uncontrolled behavior
- silent drift
- duplicate visible signal spam
- hidden state mutation
- accidental entitlement corruption
- undocumented architecture drift
- unsafe recovery continuation

This extends the legacy guarantee to the modern canonical stack. fileciteturn66file0

---

End of SYSTEM_INVARIANTS_v2.0.0.md
