# SYSTEM_INVARIANTS.md
BinaryBot — Non-Negotiable System Invariants
Version: 1.1.0
Status: Canonical

Linked Documents:
- ALGO_SPEC.md
- FSM_SPEC.md
- RISK_MODEL.md
- TELEGRAM_UX.md
- OBSERVABILITY_LOGGING_SPEC.md
- SIGNAL_DISTRIBUTION_SPEC.md
- EVENT_SCHEMA_SPEC.md
- ARCHITECTURE_CODE_MAPPING.md
- FAILURE_RECOVERY_SPEC.md
- DEPLOYMENT_PROTOCOL.md
- GOVERNANCE_AND_CHANGE_CONTROL.md
- PERFORMANCE_ANALYTICS_SPEC.md

---

# 1. PURPOSE

This document defines the absolute, non-negotiable truths of the BinaryBot system.

An invariant is a rule that must never be violated.

If any invariant is broken:

→ The system is considered compromised  
→ Trading must stop  
→ Immediate audit required

These invariants override convenience, speed, or experimentation.

---

# 2. CORE PHILOSOPHICAL INVARIANTS

INV-01 — Capital Protection First

No feature, parameter change, or structural modification may increase trade frequency at the expense of structural safety.

If trade frequency increases but rejection layers weaken → invariant violated.

---

INV-02 — Determinism

Given identical inputs:

- Candles
- Parameters
- State

The engine must produce identical outputs.

No randomness allowed in decision logic.

---

INV-03 — Documentation Supremacy

If code and documentation conflict:

Documentation is correct.  
Code must be corrected.

---

# 3. FSM INVARIANTS

INV-10 — Max Watchlist Size

WATCHLIST size ≤ 2 at all times.

If > 2 → system integrity failure.

---

INV-11 — One LIVE Per Candle

For a given symbol and candle timestamp:

Only one OPEN_NOW may be sent.

Duplicate detection failure = critical breach.

---

INV-12 — No LIVE Outside Valid Focus Context

OPEN_NOW may only occur for symbols currently inside valid WATCHLIST / focus context.

If LIVE occurs for a symbol outside valid focus/watchlist context → invariant violated.

---

INV-13 — Cooldown Absolute Block

If symbol in COOLDOWN:

No PRE  
No CONFIRM  
No OPEN_NOW

Cooldown bypass is a critical error.

---

INV-14 — Deterministic Focus Slot Release

A focus symbol must be released when canonical focus exit conditions occur.

Canonical release conditions include:

- score drops below PRE
- setup invalidates
- expiry / validity window expires
- OPEN_NOW lifecycle completes
- cooldown requires release
- stronger candidate replaces it under canonical policy

If a symbol remains stuck in focus without valid lifecycle support → invariant violated.

---

INV-15 — Focus Capacity Hard Limit

No more than 2 focus/watchlist symbols may be active simultaneously.

Replacement is allowed only if:

- capacity remains ≤ 2 after replacement
- replacement is explicitly logged / auditable

---

INV-16 — Focus Must Not Fully Starve Wide Scan

Wide scan coverage must continue while focus is active.

Focus may receive majority priority, but it must not fully eliminate ongoing wide scan coverage.

If focus monopolizes runtime attention so that active non-focus symbols stop receiving ongoing scan coverage → invariant violated.

# 4. SIGNAL INVARIANTS

INV-20 — Threshold Hierarchy

PRE ≤ CONFIRM ≤ OPEN

OPEN threshold must never be lower than PRE.

---

INV-21 — No OPEN Without PRE Path

OPEN_NOW must only occur after PRE lifecycle path.

Direct OPEN from IDLE is forbidden.

---

INV-22 — OPEN Requires Valid Focus Qualification

A symbol may reach OPEN_NOW only if:

- it has valid focus/watchlist qualification
- focus context remains valid at emission time
- final execution timing remains acceptable

Directional bias alone is insufficient.

---

INV-23 — Buffer Reachability Required

OPEN_NOW must not be emitted unless the engine considers the required buffer traversal realistically achievable before expiry.

If direction appears favorable but buffer traversal is not realistically reachable → OPEN_NOW is forbidden.

---

INV-24 — Expiry Feasibility Required

OPEN_NOW must not be emitted unless the expected move is still feasible inside the remaining expiry window.

If timing decay invalidates completion probability → OPEN_NOW is forbidden.

---

INV-25 — Focus Context Governs Actionability

PRE may be discovered in wide scan coverage.

CONFIRM and OPEN_NOW require valid focus/watchlist context for actionable execution.

This keeps discovery separate from final action permission.


INV-26 — Focus Lease Mandatory

Any symbol entering valid focus/watchlist context must receive a bounded operational lease.

A focus lease must include:

- focus_enter_ts
- focus_ttl_sec
- focus_expire_reason

Focus is not indefinite.
Focus must always be time-bounded and operationally revocable.

---

INV-27 — Forced Focus Eviction Outside Active Universe

If a symbol is no longer part of the active symbol universe, it must be forcibly removed from focus/watchlist context even if prior focus qualification existed.

This forced eviction overrides passive focus persistence.

A symbol outside the active universe may not continue to consume focus resources.

---

INV-28 — Forced Focus Eviction On Lease Expiry

If focus lease lifetime expires before the symbol reaches a valid continuation path, the symbol must leave focus/watchlist context automatically.

Expired focus must not remain resident by inertia.

---

INV-29 — Watchlist Residency Must Match Operational Eligibility

A symbol may remain in watchlist/focus only while all of the following remain true:

- symbol remains in active universe
- focus lease remains valid
- focus lifecycle remains operationally valid
- no stronger canonical replacement forces eviction

If any of these conditions fail, watchlist residency must be revoked.

---

INV-30 — Same Opportunity Must Not Be Fully Recomputed On Every Tick

The engine must distinguish between:

- a genuinely new opportunity
- repeated observation of the same opportunity

The same opportunity must not be treated as a new full decision candidate on every scheduler tick unless material context has changed.

---

INV-31 — Decision Identity Must Be Stable

A decision opportunity must be identifiable through a stable operational identity composed from canonical fields such as:

- symbol
- candle_ts
- direction
- stage / context

This identity is required so repeated evaluations can be recognized as the same opportunity rather than separate events.

---

INV-32 — Decision Freeze Window Required

Once an opportunity has been evaluated, a bounded freeze window must suppress redundant full recomputation for that same opportunity unless material context has changed.

This does not forbid monitoring.
It forbids redundant full decision reprocessing without meaningful change.

---

INV-33 — Material Context Change Reopens Evaluation

A frozen opportunity may be reevaluated only when material context changes, for example:

- new candle
- direction flip
- focus context change
- meaningful score delta
- expiry feasibility deterioration or improvement
- canonical stage upgrade path (e.g. PRE → CONFIRM)


# 5. PARAMETER INVARIANTS

INV-30 — No Hardcoded Constants

All adjustable behavior must be parameterized.

Hardcoded thresholds are forbidden.

---

INV-31 — Version Must Match Behavior

Displayed algo_version must reflect actual logic version.

Mismatch = governance breach.

---

INV-32 — Parameter Change Requires Version Bump

Changing:

- Thresholds
- Multipliers
- Expiry limits
- Gate ratios

Requires version increment.

---

# 6. LOGGING INVARIANTS

INV-40 — Every Signal Must Be Logged

Each PRE / CONFIRM / OPEN must have:

- decision event
- FSM transition event
- distribution event

Missing log = observability failure.

---

INV-41 — Errors Must Never Be Silent

All exceptions must produce:

- error log event
- optional Telegram alert

Silent crash = critical failure.

---

# 7. RISK INVARIANTS

INV-50 — SR Space Must Exceed Buffer

If SR space < required buffer multiple:

Trade must be rejected.

No override allowed.

---

INV-51 — Feasibility Must Hold

If required movement time > expiry:

Trade must be rejected.

---

INV-52 — Spike Active Blocks Trade

If spike filter triggers:

Trade must be rejected.

No override allowed.

---

# 8. PERFORMANCE INVARIANTS

INV-60 — No Drift Without Detection

If performance deviates beyond tolerance:

System must log anomaly.

No silent degradation allowed.

---

INV-61 — No Frequency Explosion

Signal frequency cannot increase drastically without parameter change.

If frequency doubles unexpectedly → drift suspected.

---

# 9. DEPLOYMENT INVARIANTS

INV-70 — No Deployment Without Backup

All modified files must be backed up before restart.

---

INV-71 — No Mixed Version State

State files must be compatible with deployed logic.

Version mismatch must halt deployment.

---

# 10. GOVERNANCE INVARIANTS

INV-80 — No Undocumented Change

If code changes without documentation update:

System governance breach.

---

INV-81 — No Emotional Tuning

Parameter changes must be data-driven.

Loss streak is not a valid tuning trigger.

---

# 11. OBSERVABILITY INVARIANTS

INV-90 — Telegram and Logs Must Match

If Telegram shows signal:

There must be corresponding log entries:

- decision event
- FSM transition event
- distribution event

If log shows OPEN but Telegram did not:

Critical inconsistency.

---

# 12. DISTRIBUTION INVARIANTS

INV-100 — Tier Limits Must Be Enforced

Distribution router must enforce tier limits defined in:

SIGNAL_DISTRIBUTION_SPEC.md

Violation occurs if:

signals exceed configured limits  
tier silent mode ignored

---

INV-101 — Silent Mode Blocks All Stages

If a tier is in SILENT mode:

PRE must not be published  
CONFIRM must not be published  
OPEN_NOW must not be published

Silent mode bypass = invariant violation.

---

INV-102 — ELITE Tier Unrestricted

ELITE tier must not be limited by signal counters.

ELITE must receive all signals.

---

INV-103 — Tier Reset Must Occur Exactly Once

Tier reset must occur once daily at:

08:10 Europe/London

Duplicate reset or missed reset = invariant breach.

---

# 13. OUTCOME SYSTEM INVARIANTS

INV-110 — One Outcome Per User Per Signal

Each user may submit only one outcome per SIGNAL_ID.

Subsequent submissions must be rejected.

---

INV-111 — Outcome Window Must Be Limited

Outcome voting must only be allowed during the vote window:

expiry + configured window duration.

Votes outside window must be rejected.

---

INV-112 — Outcome Buttons Must Expire

Outcome UI must be removed or disabled after vote window ends.

Stale voting UI must never remain active.

---

INV-113 — Outcome Storage Must Be Append-Only

Outcome logs must be append-only.

Editing past results is forbidden.

---

# 14. OBSERVABILITY CONSISTENCY INVARIANTS

INV-120 — Signal Lifecycle Must Be Traceable

Each signal must produce a complete event chain:

decision → FSM transition → distribution → outcome (optional)

Missing event stages indicate system inconsistency.

---

INV-121 — Log Format Must Follow EVENT_SCHEMA_SPEC

All structured logs must follow the schema defined in:

EVENT_SCHEMA_SPEC.md

Unstructured or malformed logs are considered observability failures.

---

INV-122 — No Hidden Signal Events

A signal must never appear in Telegram without corresponding logs.

Any signal without log trace = critical anomaly.

---

# 15. SYSTEM SAFETY SWITCH

If any invariant is violated:

System must support immediate freeze mode:

- stop scanning
- stop signals
- preserve state
- log reason

Manual audit required before restart.

---

# 16. INVARIANT PRIORITY

If two components conflict:

Priority order:

1. Risk invariants
2. FSM invariants
3. Distribution invariants
4. Logging invariants
5. Performance invariants
6. UX invariants

Risk protection always overrides convenience.

---

# 17. INVARIANT GUARANTEE

If all invariants are respected:

- no structural corruption
- no uncontrolled behavior
- no silent drift
- no duplicate signal spam
- no hidden logic
- no accidental risk escalation

The system remains institutionally stable.

---

End of SYSTEM_INVARIANTS.md