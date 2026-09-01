# TEST_PLAN_v2.0.0

Version: 2.0.0  
Status: Active Canonical  
Path: /opt/binarybot/docs/canonical/active/TEST_PLAN_v2.0.0.md

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- DEPLOYMENT_PROTOCOL_v2.0.0.md
- STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v2.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- DEPLOYMENT_PROTOCOL_v2.0.0.md

Code Alignment:
- core/strategy_v2.py
- core/signal_engine.py
- core/fsm_runtime.py
- core/distribution_router.py
- core/telegram_publisher.py
- core/observability_logger.py
- core/outcome_service.py
- core/analytics_engine.py
- core/storage.py
- candle_adapter.py
- params_loader.py
- bot_service.py
- config surfaces
- replay / regression harnesses
- audit/export scripts
- restart wrappers
- test fixtures and recorded datasets

## 0. Purpose

This document defines the canonical system validation, behavioral verification, replay validation, and regression protocol for BinaryBot / DROPi Signals.

Its role is to ensure that:
- system behavior is testable before runtime trust is granted
- canonical architecture is validated rather than assumed
- invariants are checked explicitly
- replay and determinism discipline are preserved
- restarts, persistence, distribution, outcome tracking, analytics, and observability are verified systematically
- no production-affecting mutation is treated as trustworthy without proof

This document does not define strategy formulas, commercial policy, payout logic, or deployment execution steps themselves. It defines how the approved system truth must be validated.

## 1. Canonical Position

This document sits at the validation boundary between:
- architecture
- module contracts
- strategy behavior
- FSM lifecycle integrity
- distribution behavior
- Telegram UX behavior
- observability completeness
- outcome integrity
- analytics correctness
- restart safety
- recovery behavior
- deployment readiness

It exists to answer eight questions:

1. What must be tested before production trust is granted.
2. What categories of behavior must be validated.
3. What failures require immediate halt or rejection.
4. What replay and determinism guarantees must be proven.
5. What runtime and persistence behaviors must survive restart.
6. How distribution, outcomes, analytics, and observability must be validated.
7. What production-ready means operationally.
8. How validation evidence must relate to governance and deployment.

If observed runtime behavior conflicts with the expectations defined here, the system must be treated as unproven until the mismatch is resolved canonically.

## 2. Final Principle

No system behavior is trusted merely because it runs.

Behavior becomes canonically trusted only when it is:
- explicitly testable
- reproducible where required
- invariant-safe
- observable
- restart-safe
- distribution-safe
- outcome-safe
- aligned with the active canonical architecture

Testing is non-canonical if it is reduced to superficial smoke checks while critical invariants, replay guarantees, persistence integrity, or distribution truth remain unverified.

## 3. Validation Authority Rule

This document is the canonical validation protocol for BinaryBot / DROPi Signals.

Governance decides whether a change is allowed.  
Deployment protocol decides how an approved change reaches runtime safely.  
This test plan decides what evidence is required to trust the resulting behavior.

No production activation is valid if the relevant tests defined by this document have not been executed and passed at the depth appropriate to the change class.

## 4. Scope of Validation

This plan applies to:
- architecture-aligned runtime behavior
- strategy and decision behavior
- FSM lifecycle behavior
- persistence behavior
- cooldown and watchlist behavior
- distribution and tier-state behavior
- Telegram publication behavior
- observability and audit trail behavior
- outcome capture behavior
- analytics and research computation behavior
- recovery behavior
- replay and regression behavior
- deployment readiness verification

This plan applies to both narrow patches and broader releases.
Change size may affect depth and prioritization, but does not remove the obligation to validate.

## 5. Validation Environments

### 5.1 Canonical Environments

The canonical validation environments are:
- DEV
- STAGING
- PROD

Rule:
- behavioral validation must pass in DEV or STAGING before production trust is granted in PROD, except for tightly bounded live-only smoke checks that do not replace the full validation requirement

### 5.2 Test Channel Rule

Dedicated Telegram test channels, topics, or equivalent isolated delivery surfaces must be used for distribution, routing, and UX validation.

Representative test surfaces should mirror the canonical tier model:
- FREE_TEST
- BASIC_TEST
- PRO_TEST
- ELITE_TEST

Destructive or noisy validation must never be performed in real subscriber channels.

### 5.3 Test Data Rule

Approved test data sources may include:
- recorded candle datasets
- simulated candle sequences
- synthetic edge-case fixtures
- production-like datasets sanitized for replay use
- bounded live data for smoke validation only

Recorded and replayable datasets are preferred wherever determinism matters.

## 6. Validation Evidence Rule

Validation is not complete unless evidence is exportable and reviewable.

Validation packages should include, where relevant:
- test run identifier
- environment
- dataset or fixture reference
- version or commit reference
- parameter/config reference
- before/after evidence if state mutation occurs
- emitted event summary
- failure summary if any
- pass/fail result per category
- replay comparison evidence where applicable

Validation output should be retained in auditable form, not only as transient terminal text.

## 7. Canonical Test Categories

The system must be capable of passing the following validation categories where relevant:

1. Structural and boot validation  
2. State persistence and restart validation  
3. Strategy and gate validation  
4. Decision-object and pipeline-order validation  
5. FSM lifecycle and invariant validation  
6. Telegram UX and routing validation  
7. Distribution and tier-state validation  
8. Outcome capture and integrity validation  
9. Observability and audit-trail validation  
10. Analytics and research validation  
11. Stress and load validation  
12. Replay and regression validation  
13. Failure recovery validation  
14. Production-readiness validation

No category should be treated as optional if the corresponding surface is affected by a change.

## 8. Structural and Boot Validation

### 8.1 Config Integrity Validation

Targets include config loaders, parameter surfaces, required keys, types, defaults, and validation guards.

Expected proof:
- valid configuration loads successfully
- invalid configuration is rejected explicitly
- missing keys fail safely
- invalid types fail safely
- unknown or malformed structures do not slip into runtime silently
- startup does not proceed into trusted scanning behavior when configuration is invalid

Failure examples:
- engine starts with invalid config
- hardcoded constants bypass canonical parameter control
- validation logs are missing or incomplete

### 8.2 Distribution Surface Integrity Validation

Targets include channel or topic configuration, tier routing surfaces, entitlement-linked destinations, and disabled-state handling.

Expected proof:
- missing or invalid distribution targets are detected explicitly
- disabled or missing targets do not receive publish attempts
- unaffected tiers continue correctly where canonically allowed
- routing state does not pretend success for disabled surfaces

### 8.3 File System and State Surface Integrity Validation

Targets include state files, log directories, append-only event files, proof outputs, and permissions.

Expected proof:
- required directories exist or are created safely
- read/write capability is verified
- permission failures surface as explicit errors
- no partial-trust runtime continues when persistence-critical surfaces are unavailable

### 8.4 Startup State Summary Validation

On startup, the system must produce an auditable summary of relevant runtime state.

Expected startup evidence may include:
- version identity
- parameter checksum or equivalent config reference
- active symbol count
- watchlist size
- cooldown count
- distribution counters and states
- restart context where relevant
- last reset reference where relevant

Missing startup truth weakens runtime trust.

## 9. State Persistence and Restart Validation

### 9.1 Restart During Watchlist State

Expected proof:
- watchlist entries survive restart where canonically required
- no duplicate PRE stage is emitted after restart for the same preserved state
- resumed behavior remains aligned with canonical dedup and lifecycle rules

### 9.2 Restart During Live-Sent State

Expected proof:
- live-sent state survives restart where relevant
- duplicate OPEN_NOW publication does not occur after restart
- dedup and state persistence remain strong enough to prevent replay spam

### 9.3 Restart During Cooldown

Expected proof:
- cooldown state survives restart
- cooldown remains an absolute block where canonically required
- no restart gap allows forbidden re-entry into signal flow

### 9.4 Restart With Tier Counters Near Limits

Expected proof:
- counters survive restart correctly
- silence transitions still occur at the correct threshold
- restart does not implicitly grant extra daily capacity

### 9.5 Atomic Persistence Validation

State-bearing writes must be validated for atomicity or equivalent corruption protection.

Expected proof:
- partial write scenarios do not leave the system in an unrecoverable or trust-ambiguous state
- last known valid state remains loadable when write interruption occurs

## 10. Strategy and Gate Validation

This document does not define the strategy formulas themselves, but it defines the requirement that they be behaviorally validated.

### 10.1 Spike Rejection Validation

Expected proof:
- extreme abnormal candles trigger spike rejection where canonically required
- rejection reason is observable
- no PRE, CONFIRM, or OPEN_NOW is emitted for rejected spike cases

### 10.2 Support/Resistance Compression Validation

Expected proof:
- insufficient available space relative to canonical SR rules causes rejection
- rejection reason is visible in the decision/audit path
- compressed conditions do not emit trusted signal stages

### 10.3 Feasibility Failure Validation

Expected proof:
- infeasible market movement conditions are rejected
- feasibility failure is observable
- the system does not emit a signal that cannot plausibly complete inside canonical constraints

### 10.4 Trend-Regime Adjustment Validation

Expected proof:
- trend-aligned conditions adjust behavior consistently with canonical strategy truth
- flat conditions adjust behavior consistently with canonical strategy truth
- counter-trend conditions adjust behavior consistently with canonical strategy truth

This includes validation of any bounded differences in:
- buffers
- confidence treatment
- timing assumptions
- expiry assumptions
- score interpretation
provided those are canonically defined elsewhere.

### 10.5 Threshold Hierarchy Validation

Expected proof:
- threshold ordering remains canonically valid
- later/stronger stages are not produced under weaker standards than earlier/weaker stages
- threshold inversion is prevented or detected

### 10.6 Determinism Validation for Strategy Outputs

Expected proof:
- identical inputs, params, and relevant state produce materially identical decision outputs where determinism is expected
- unexplained output drift is treated as a regression concern

## 11. Decision-Object and Pipeline-Order Validation

The pipeline must be tested against the active canonical ordering truths.

### 11.1 DecisionObject Before FSM Validation

Expected proof:
- DecisionObject or equivalent canonical decision payload is formed before FSM processing
- FSM does not become the hidden origin of strategic truth
- audit or event outputs reflect the correct ownership order

### 11.2 Corridor Before Time-Model Validation

Expected proof:
- corridor engine or equivalent corridor logic is applied before time model influence where that canonical truth is active
- pipeline ordering is observable, reconstructable, or inferable from emitted evidence
- no silent inversion of ownership occurs

### 11.3 Decision-Audit Completeness Validation

Expected proof:
- rejected, shortlisted, and emitted decisions all produce sufficient decision-audit evidence where canonically required
- reason traces are reconstructable at the required level of fidelity

## 12. FSM Lifecycle and Invariant Validation

### 12.1 PRE Entry Validation

Expected proof:
- PRE-eligible decisions create the correct watchlist or pre-live state
- transition is logged
- duplicate PRE emission is prevented according to canonical dedup rules

### 12.2 CONFIRM Path Validation

Expected proof:
- CONFIRM behavior matches canonical lifecycle expectations
- stage transitions or persistent state changes remain valid
- CONFIRM does not duplicate or corrupt stage sequencing

### 12.3 OPEN_NOW Transition Validation

Expected proof:
- OPEN_NOW is emitted once per canonically allowed opportunity
- lifecycle state advances correctly
- SIGNAL_ID or equivalent continuity is preserved across stages

### 12.4 Live-to-Cooldown Validation

Expected proof:
- live state exits correctly into cooldown when canonical conditions are met
- cooldown start is persisted
- symbol state is cleaned up without corruption

### 12.5 Cooldown Block Validation

Expected proof:
- cooldown blocks all forbidden signal attempts
- attempted violations are observable
- no hidden bypass exists

### 12.6 Watchlist Capacity Validation

Expected proof:
- maximum watchlist size is enforced where canonically defined
- over-capacity candidates do not silently corrupt state

### 12.7 One-Open-Per-Candle Validation

Expected proof:
- duplicate OPEN_NOW attempts on the same candle are blocked
- dedup behavior is explicit and observable

### 12.8 No-Live-in-Forbidden-Mode Validation

Expected proof:
- modes such as wide-scan or equivalent restricted states do not emit LIVE/OPEN_NOW where forbidden canonically
- violation attempts are logged

## 13. Telegram UX and Routing Validation

### 13.1 Required Field Validation

Signal messages must include the fields canonically required by the active Telegram UX and distribution documents.

Typical examples may include:
- stage label
- symbol
- direction
- expiry
- buffer or buffer mode
- confidence or score field where canonically required
- SIGNAL_ID or equivalent signal continuity reference

### 13.2 Topic/Surface Routing Validation

Expected proof:
- public or subscriber-facing messages go to the correct signal surfaces
- debug material goes only to approved debug/admin surfaces
- system alerts go only to approved alert surfaces
- proof logs go only to approved administrative surfaces

### 13.3 Admin Command Validation

Where admin commands affect runtime behavior, validation should prove:
- valid commands mutate the intended settings only
- invalid commands fail safely
- before/after proof is emitted where canonically required
- changes affect future behavior only where appropriate

### 13.4 Symbol Selection and Admin UX Validation

Expected proof:
- symbol changes persist atomically
- UI-driven changes are reflected in runtime behavior correctly
- partial writes or partial state mutations do not occur

## 14. Distribution and Tier-State Validation

### 14.1 Active Delivery Validation

For each active tier, the system must prove correct delivery of canonically allowed stages.

### 14.2 OPEN_NOW Counting Validation

Expected proof:
- only successful OPEN_NOW delivery increments the relevant daily counter where canonical counting uses successful live delivery
- PRE and CONFIRM do not accidentally count as OPEN_NOW capacity usage

### 14.3 Silent-Mode Full-Block Validation

Expected proof:
- once a tier becomes silent, all canonically blocked stages remain blocked for that tier
- other tiers continue according to canonical rules
- top tiers that are exempt remain exempt only if canonically defined

### 14.4 Publish Failure Non-Increment Validation

Expected proof:
- failed publication attempts do not increment successful delivery counters
- tier state remains honest

### 14.5 Reset Validation

Expected proof:
- daily reset clears counters and restores active state correctly
- reset occurs once per reset window
- duplicate reset invocation remains idempotent
- DST-sensitive timing remains correct where the canonical reset timezone matters

### 14.6 Dedup per Tier/Signal/Stage Validation

Expected proof:
- duplicate publication of the same stage for the same tier and same signal is blocked
- dedup behavior is logged

## 15. Outcome Capture and Integrity Validation

### 15.1 Outcome Linkage Validation

Expected proof:
- outcome interactions point to the correct OPEN_NOW signal identity
- signal/outcome mismatch does not occur

### 15.2 Timing Gate Validation

Expected proof:
- outcomes cannot be submitted before the canonically valid window
- outcomes are accepted during the valid window
- late outcomes are rejected where required

### 15.3 Single-Vote Lock Validation

Expected proof:
- one user can submit only one valid outcome per signal where that invariant applies
- repeated submissions do not corrupt data or produce misleading state

### 15.4 Outcome UI State Validation

Expected proof:
- buttons, markup, or outcome UI state behaves correctly after vote and after close
- no false affordance remains after the allowed window expires

### 15.5 Public Aggregate Validation

Expected proof:
- aggregated outcome statistics are correct
- public aggregates do not leak private user identity data

### 15.6 Outcome Storage Integrity Validation

Expected proof:
- stored outcome records include canonical required fields
- append behavior remains reliable
- per-user/per-signal dedup remains effective

## 16. Observability and Audit-Trail Validation

### 16.1 Signal-to-Log Completeness Validation

For every canonical signal stage, expected evidence must exist for:
- decision or equivalent decision-audit event
- FSM transition or equivalent lifecycle event
- publication attempts and results
- failure evidence where publication fails

### 16.2 No-Silent-Error Validation

Expected proof:
- critical failures emit explicit error events
- admin/system alert surfaces are informed where canonically required
- stack or trace summaries are retained appropriately

### 16.3 Admin Proof Validation

Expected proof:
- admin-driven state changes generate proof logs
- before/after context exists where required
- actor identity is attributable where canonically required

### 16.4 Crash-Loop Detection Validation

Expected proof:
- repeated restart or crash patterns trigger critical detection
- the system does not silently thrash while appearing healthy

## 17. Analytics and Research Va