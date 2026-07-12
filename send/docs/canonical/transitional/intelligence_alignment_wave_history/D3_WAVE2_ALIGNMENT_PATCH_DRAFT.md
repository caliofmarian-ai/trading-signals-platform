# D3_WAVE2_ALIGNMENT_PATCH_DRAFT.md

## STEP 112Q.D3-WAVE2 — DECISION / TELEMETRY / LEARNING ALIGNMENT PATCH
**Status:** Draft for canonical review  
**Scope:** D3 set only  
**Objective:** Eliminate old-strategy logic from research / learning / audit / telemetry documents and align all downstream intelligence documents to the new canonical strategy model.

---

# 1. PURPOSE

This patch defines the canonical alignment rules for the D3 document family:

- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`
- `STRATEGY_INTELLIGENCE_SYSTEM.md`
- `DECISION_AUDIT_SPEC_v2.0.0.md`
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

The purpose of this patch is to prevent downstream documents from remaining logically attached to the old strategy model after the canonical strategy stack has already changed.

This patch does **not** redefine the main strategy engine itself.  
Instead, it defines how all audit, learning, telemetry, analytics, intelligence, and evolution layers must interpret the new strategy canon.

---

# 2. PROBLEM STATEMENT

The uploaded D3 documents contain valuable material, but they are not yet fully aligned to the current canonical strategy architecture.

Several of them still carry assumptions from the old model, especially:

- treating `focus_history.jsonl` as a central learning truth
- treating Telegram stage emissions (`PRE_SENT`, `CONFIRM_SENT`, `OPEN_NOW_SENT`) as the main strategic lifecycle
- mixing operator outcome truth with market truth
- treating trial tracking as if it were equivalent to decision causality
- under-defining rejection analytics as a first-class strategic intelligence layer
- blurring the boundary between engine decisions, distribution decisions, admin actions, and later AI analysis

If these assumptions remain, the project risks documenting a new strategy with old mental models.

---

# 3. CANONICAL STRATEGY TRUTHS THAT MUST CONTROL THIS PATCH

The following truths are already fixed at project level and must dominate all D3 documents:

## 3.1 DecisionObject truth
`DecisionObject` is produced **before** FSM.

This means:

- the strategic evaluation result exists before Telegram stage logic
- FSM does not create the strategic truth
- FSM manages stage progression, lifecycle handling, and operational transitions
- downstream analytics must not describe FSM as the origin of the decision itself

## 3.2 Corridor truth
`Corridor Engine` is positioned **before** `Time Model` in the strategy pipeline.

Therefore:

- structural feasibility is upstream of temporal modeling
- time analysis cannot be documented as if it independently defines feasibility first
- all learning and rejection analytics must respect corridor-first ordering

## 3.3 Audit truth
The system must be able to explain:

- why a signal advanced
- why a signal stalled
- why a signal was rejected
- why a signal died after earlier eligibility
- why a signal was not distributed
- why market outcome and operator outcome may differ

This means rejection and death reasons are not secondary metadata.  
They are part of the canonical intelligence model.

## 3.4 Distribution truth
Telegram emission is not the strategy itself.

Telegram is a downstream distribution layer.  
The canonical strategic lifecycle exists even when nothing is sent to Telegram.

## 3.5 Multi-truth outcome truth
The project must separate:

1. **Decision truth**  
   Why the signal advanced, stalled, was rejected, or died.

2. **Market truth**  
   What the market objectively did after the signal became actionable.

3. **Operator truth**  
   What admin/operator/user execution or outcome marking recorded in the system.

These truths are related, but they are not the same thing.

---

# 4. NEW CANONICAL D3 STACK

All D3 documents must align to the following downstream stack:

```text
Engine / Corridor / Time / DecisionObject / FSM / Distribution
    ↓
Observability
    ↓
Decision Audit
    ↓
Market Truth Telemetry
    ↓
Operator Outcome Tracking
    ↓
Performance Analytics
    ↓
Research & Learning
    ↓
Strategy Intelligence
    ↓
Autonomous Evolution / AI Recommendation Layer
```

This ordering is mandatory.

No D3 document may invert this relationship.

In particular:

- analytics cannot be upstream of audit truth
- AI recommendation cannot be upstream of canonical decision evidence
- Telegram stage logs cannot replace the decision layer
- admin outcome cannot replace market telemetry
- legacy focus logs cannot replace decision audit

---

# 5. DOCUMENT-BY-DOCUMENT ALIGNMENT RULES

---

## 5.1 DECISION_AUDIT_SPEC_v2.0.0.md
**Target status:** Primary canonical root of D3

This document is the strongest foundation in the uploaded D3 family and must become the primary source of truth for downstream learning and analysis.

### It must define the canonical answer to:
- why a candidate was evaluated
- why it passed or failed
- which gate killed it
- whether it entered focus
- whether it progressed in lifecycle
- whether distribution occurred or was suppressed
- how later market and operator outcomes are linked back to the decision

### It must remain the root for:
- rejection taxonomy
- stage death taxonomy
- promotion / suppression explanations
- audit event classes
- strategic explainability
- learning-ready causality records

### Mandatory rule
No other D3 document may define an alternative primary causality source that competes with `decision_audit.jsonl`.

### Canonical note to insert conceptually
`focus_history.jsonl`, stage emissions, and operator outcomes may enrich analytics, but they do not replace `decision_audit.jsonl` as the canonical causality layer.

---

## 5.2 TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
**Target status:** Canonical market-truth layer

This document must be preserved, but explicitly positioned as the objective market evaluation layer.

### It must define:
- what happened in the market after `OPEN_NOW`
- whether the signal would have won/lost/drawn at expiry
- whether post-expiry continuation existed
- whether expiry duration appears too short
- whether early move vs late move patterns indicate timing issues

### Mandatory boundary
This layer does **not** explain why the signal was produced.  
It explains what the market did **after** the signal became actionable.

### Mandatory boundary
This layer is independent from:
- Telegram user feedback
- manual admin interpretation
- manual reporting
- operator marking

### Mandatory canonical statement
Trade Temporal Telemetry is the **objective market truth layer**, not the strategic causality layer and not the operator truth layer.

---

## 5.3 OUTCOME_TRACKING_SPEC_v2.0.0.md
**Target status:** Canonical operator/admin truth layer

This document remains valid, but only if it is explicitly bounded.

### It must define:
- admin/operator-recorded execution result
- user-facing or operator-facing outcome marking
- manual or operational classification such as executed / missed / won / lost

### It must **not** claim:
- to be the objective market truth
- to be the canonical reason why a signal existed
- to be the source of rejection causality

### Mandatory canonical statement
Outcome tracking records what the operator/admin side did or recorded.  
It does not replace market truth telemetry or decision causality.

### Required relation
Every operator outcome should be linkable to:
- decision audit record
- market telemetry record
where applicable.

---

## 5.4 PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
**Target status:** Secondary downstream analytics consumer

This document is useful, but it still carries old-model assumptions.

### Main required patch
It must stop behaving as if performance analytics starts from Telegram event history or focus history alone.

### New dependency order
Performance analytics must consume:

1. decision audit
2. market truth telemetry
3. operator outcome tracking
4. optional stage / focus / distribution logs

in that order of authority.

### Mandatory rule
Analytics must distinguish:
- structural rejection
- temporal rejection
- focus-stage death
- distribution suppression
- market failure after valid open
- operator miss or execution mismatch

### What must be deprecated conceptually
Any framing where:
- `PRE_SENT / CONFIRM_SENT / OPEN_NOW_SENT` are treated as the primary strategic lifecycle
- `focus_history.jsonl` is treated as the master truth
- trials alone are treated as equivalent to decision learning

### New role
Performance Analytics becomes the layer that aggregates truth, not the layer that invents it.

---

## 5.5 RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md
**Target status:** Downstream learning framework, not truth source

This document contains important ideas, but it is one of the clearest carriers of old-strategy logic.

### Main problem
It still over-centers:
- `focus_history.jsonl`
- `trials.jsonl`
- Telegram stage events
as if these define the strategic learning universe.

### Required conceptual rewrite
Research and Learning must be redefined as consuming canonical truth layers rather than generating them.

### New learning inputs must be:
- decision audit
- telemetry
- operator outcome
- performance analytics
- optional focus/stage history as supplementary context only

### Mandatory learning questions
The framework must be able to answer:
- Which rejections are most frequent by symbol / timeframe / session?
- Which rejected candidates were correctly rejected?
- Which killed signals would have recovered if lifecycle policy were different?
- Which market losses were actually timing / expiry failures?
- Which operator misses distort perceived performance?
- Which structural filters improve long-term expectancy?
- Which distribution policies suppress too many valid opportunities?

### Mandatory conceptual deprecation
`focus_history.jsonl` and `trials.jsonl` may remain datasets, but they must not be described as the canonical learning foundation of the new strategy.

---

## 5.6 STRATEGY_INTELLIGENCE_SYSTEM.md
**Target status:** Explainability and intelligence synthesis layer

This document is valuable but too broad.  
It currently mixes strategic intelligence with operational control tendencies.

### Required narrowing
It must become a synthesis layer that:
- explains patterns
- identifies weaknesses
- proposes hypotheses
- surfaces improvement opportunities

### It must not become:
- the canonical strategy source
- the admin control source
- the direct owner of operator workflow
- an uncontrolled strategy mutator

### Mandatory alignment
This document must explicitly consume:
- decision audit
- telemetry
- outcomes
- analytics

and present intelligence derived from them.

### Required split
Anything primarily about:
- control panel actions
- Telegram operational command surfaces
- permissioned management UX
belongs under admin / control-plane documents, not here.

---

## 5.7 AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md
**Target status:** Read-only recommendation and evolution layer

This document is directionally useful, but must be strictly bounded for safety and architecture integrity.

### Canonical role
The Autonomous Strategy Evolution System may:
- analyze patterns
- generate hypotheses
- recommend threshold adjustments
- propose experiments
- simulate scenario improvements
- identify recurring failure clusters

### It must not:
- silently rewrite production logic
- override canonical docs
- mutate live strategy without explicit controlled process
- act as the primary source of strategic truth

### Mandatory dependency chain
Autonomous evolution must depend on:
- decision audit
- telemetry
- outcomes
- analytics
- research findings
- governance / change control

### Mandatory governance statement
All proposed changes must pass through documented review, approval, and controlled implementation steps before affecting production behavior.

---

# 6. LEGACY CONCEPTS THAT MUST BE EXPLICITLY DOWNGRADED

The following concepts may still exist historically or operationally, but must be downgraded in D3 documents from “primary truth” to “supporting evidence” unless a specific doc proves otherwise.

## 6.1 focus_history.jsonl
Allowed role:
- historical focus-stage timeline
- operational context
- supplementary analytics input

Disallowed role:
- primary strategic causality source
- canonical learning root

## 6.2 trials.jsonl
Allowed role:
- experiment / validation / performance sample log
- optional research dataset

Disallowed role:
- sole truth of signal quality
- replacement for decision audit
- replacement for market telemetry

## 6.3 PRE_SENT / CONFIRM_SENT / OPEN_NOW_SENT event logic
Allowed role:
- Telegram/distribution stage evidence
- lifecycle emission evidence

Disallowed role:
- definition of the strategy itself
- substitute for candidate evaluation history
- substitute for rejection causality

## 6.4 “Signal existed only if Telegram saw it”
This idea is fully deprecated.

A candidate may be strategically real even if:
- it was rejected
- it died in focus
- it was suppressed before distribution
- it never reached Telegram

---

# 7. REQUIRED CANONICAL TERMINOLOGY

The D3 family must consistently use the following hierarchy:

## 7.1 Candidate
A structurally and temporally evaluated market setup entering strategic evaluation.

## 7.2 Decision
The evaluation output produced before FSM, including score, structural status, temporal status, and strategic eligibility.

## 7.3 Lifecycle state
Operational / stage progression after decision output.

## 7.4 Distribution decision
A separate downstream determination about whether, when, and how the signal is emitted to Telegram or other channels.

## 7.5 Rejection
A failure before becoming an actionable valid signal.

## 7.6 Kill / death
A lifecycle termination after earlier eligibility or partial progression.

## 7.7 Market outcome
Objective market behavior after actionable open.

## 7.8 Operator outcome
Admin / operator / execution-side result recording.

## 7.9 Intelligence finding
A downstream synthesized conclusion derived from canonical evidence.

## 7.10 Evolution proposal
A governed recommendation for future improvement, not an automatic rewrite of truth.

---

# 8. REQUIRED REJECTION / DEATH TAXONOMY UPGRADE

The D3 family must support a richer taxonomy than simplistic `REJECT_*` labels alone.

At minimum, documents should distinguish:

## 8.1 Structural rejection
Examples:
- SR failure
- insufficient corridor
- invalid feasibility
- no movement space

## 8.2 Temporal rejection
Examples:
- weak time profile
- expiry mismatch risk
- poor timing quality
- wrong temporal context

## 8.3 Score rejection
Examples:
- total score below threshold
- confidence insufficient
- regime filter mismatch

## 8.4 Focus-stage death
Examples:
- setup degraded while waiting
- momentum disappeared
- structure broke before confirmation
- signal lost viability before open

## 8.5 Distribution suppression
Examples:
- strategic validity preserved
- but emission suppressed due to policy, overlap, quota, channel rules, anti-spam logic, or admin constraints

## 8.6 Integrity / data rejection
Examples:
- missing price data
- invalid timestamp
- inconsistent symbol state
- incomplete signal object

This taxonomy must be treated as learning-critical.

---

# 9. THREE-TRUTH MODEL THAT MUST BE INSERTED ACROSS D3

A mandatory model for D3 alignment is:

## 9.1 Decision Truth
Source of truth for:
- why candidate passed or failed
- why signal advanced or died
- why distribution happened or not

Primary source:
- `decision_audit.jsonl`

## 9.2 Market Truth
Source of truth for:
- what market actually did after open
- expiry result
- post-expiry continuation
- recovery / timing evidence

Primary source:
- trade temporal telemetry dataset

## 9.3 Operator Truth
Source of truth for:
- what operator/admin/user execution workflow recorded
- executed / missed / won / lost on the human workflow side

Primary source:
- outcome tracking system

All D3 documents must respect this separation.

---

# 10. NEW ROLE OF TELEGRAM IN D3

Telegram must be described as:

- a delivery surface
- a stage communication mechanism
- a user/admin interface layer
- a source of distribution evidence

Telegram must **not** be described as:
- the origin of strategy truth
- the definition of a signal’s existence
- the canonical learning source
- the full lifecycle owner of strategic logic

---

# 11. REQUIRED UPGRADE PROPOSALS TO EMBED DURING PATCHING

While patching, the following upgrades should be proposed directly inside the affected docs where relevant.

## 11.1 Admin / control panel upgrade
Add explicit analytics views for:
- rejection heatmaps
- focus death reasons
- distribution suppression counts
- symbol/session failure clusters
- mismatch between market truth and operator truth
- expiry-too-short discovery

## 11.2 Telegram UX upgrade
Add document-level support for:
- explanation-ready rejection summaries
- internal admin-only signal death diagnostics
- stage-level diagnostic transparency
- safer separation of user-facing messages vs internal forensic logs

## 11.3 Intelligence layer upgrade
Add support for:
- recurring failure motif detection
- symbol-specific expiry recommendation
- corridor-to-expiry compatibility maps
- decision confidence drift detection
- threshold sensitivity simulation

## 11.4 Research upgrade
Add support for:
- rejected-but-later-valid counterfactual sets
- suppressed-but-high-quality opportunity sets
- expiry counterfactual testing
- session-aware failure clustering
- stage death survival analysis

## 11.5 AI / evolution upgrade
Add support for:
- recommendation cards, not auto-mutations
- controlled experiment proposals
- evidence-backed threshold proposals
- rollback-ready change simulation
- governance-gated adoption flow

---

# 12. WHAT MUST BE MARKED AS OUTDATED IF FOUND DURING PATCHING

If any of the D3 documents still state or imply the following, those passages must be patched or annotated as outdated:

- focus history is the canonical root of strategy learning
- Telegram stage emission defines signal reality
- operator-recorded outcomes equal objective market truth
- trials are sufficient to explain strategic quality
- AI evolution can alter production logic without governance
- analytics can infer full causality without decision audit
- FSM is the producer of strategic truth
- time model is implicitly upstream of corridor feasibility
- rejection reasons are secondary rather than central to learning

---

# 13. EXPECTED OUTPUT OF WAVE 2 PATCHING

After this patch is applied, the D3 family should become:

## 13.1 Internally coherent
No conflicting definitions of what counts as strategic truth.

## 13.2 Pipeline-aligned
All downstream docs respect the actual canonical flow.

## 13.3 Rejection-aware
The system learns not only from wins and losses, but from deaths, suppressions, and failed candidates.

## 13.4 Multi-truth aware
Decision truth, market truth, and operator truth remain separate and linkable.

## 13.5 Governance-safe
AI / evolution remains recommendation-driven, not uncontrolled.

## 13.6 Useful for future code implementation
These docs become reliable enough to drive observability and analytics implementation later without re-importing old strategy assumptions.

---

# 14. IMPLEMENTATION ORDER FOR DOC PATCHING

Recommended patch order inside D3:

1. `DECISION_AUDIT_SPEC_v2.0.0.md`
2. `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
3. `OUTCOME_TRACKING_SPEC_v2.0.0.md`
4. `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
5. `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
6. `STRATEGY_INTELLIGENCE_SYSTEM.md`
7. `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

Reason:

- define causality first
- define market truth second
- define operator truth third
- only then patch analytics, learning, intelligence, and evolution layers

---

# 15. FINAL CANONICAL STATEMENT

The new strategy must be documented as:

- **decision-first**
- **pipeline-first**
- **corridor-before-time**
- **DecisionObject-before-FSM**
- **audit-first**
- **rejection-aware**
- **distribution-separated**
- **multi-truth outcome aware**
- **intelligence downstream**
- **AI governed, not sovereign**

Any D3 passage inconsistent with this model must be considered misaligned with the current canonical strategy direction and should be patched accordingly.

---

# 16. STATUS

**Draft result:** Accepted as Wave 2 alignment draft candidate for D3 family review before file-by-file patching.

**Next recommended step:** produce a file-by-file D3 remediation matrix showing for each D3 document:
- what remains valid
- what is outdated
- what must be inserted
- what must be deprecated
- what should be moved to admin/control-plane docs
