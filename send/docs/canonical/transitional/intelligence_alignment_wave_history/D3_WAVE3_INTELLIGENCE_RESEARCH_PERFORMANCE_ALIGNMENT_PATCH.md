# D3 WAVE 3 — Intelligence / Research / Performance Alignment Patch

## Status
Draft canonical alignment document for Wave 3 documentation cleanup.

## Scope
This document defines the canonical alignment and patch plan for the following seven documents:

1. `DECISION_AUDIT_SPEC_v2.0.0.md`
2. `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
3. `OUTCOME_TRACKING_SPEC_v2.0.0.md`
4. `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
5. `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
6. `STRATEGY_INTELLIGENCE_SYSTEM.md`
7. `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

This patch document is written after audit against the newer canonical architecture direction already established in the project, especially the following truths:

- `DecisionObject` is produced before FSM.
- `Corridor Engine` is before `Time Model` in the strategic pipeline.
- Intelligence is a downstream analytical layer, not part of runtime-critical execution.
- Owner authority remains supreme over all approval, strategy evolution, and control operations.
- Documentation must be unified, reduced in ambiguity, and cleaned before code changes.

---

# 1. Objective of this patch

The purpose of this patch is not merely to rename terms or cosmetically refresh older specs.
The real objective is to establish one coherent truth model across:

- runtime decision production
- market-truth observability
- operational outcome recording
- analytical performance interpretation
- research and learning workflows
- strategy evolution proposals
- owner/admin approval authority

The seven audited documents contain strong material, but they currently reflect mixed generations of architecture.
Some are already close to canonical form, while others still preserve older assumptions:

- admin feedback treated as main truth source
- community/user voting models influencing analytics
- Telegram-first workflows used as canonical backend logic
- research artifacts detached from objective telemetry
- intelligence described too close to runtime or too close to engine event logs

This patch resolves those inconsistencies.

---

# 2. Canonical truth layers after alignment

## 2.1 Runtime truth

Runtime truth is the layer that governs live decision production and signal lifecycle progression.
It includes the strategic pipeline and execution path that may lead to PRE, CONFIRM, OPEN_NOW, and downstream FSM handling.

Canonical properties:

- runtime is deterministic as much as possible
- runtime must not depend on research or analytics outputs in real time unless explicitly promoted into approved strategy rules
- runtime produces decisions, states, reasons, and transitions
- runtime is not the place for retrospective interpretation

Runtime truth includes, conceptually:

- strategy pipeline
- gate evaluation
- DecisionObject production
- FSM progression
- signal emission/distribution hooks

## 2.2 Observability truth

Observability truth is the layer that records what actually happened to a signal or candidate across its lifecycle.
This layer must be factual, timestamped, auditable, and reconstructible.

It includes:

- decision audit records
- rejection reasons
- lifecycle stage transitions
- distribution attempts and outcomes
- temporal telemetry after candidate creation or OPEN_NOW
- market checkpoints and expiry checks
- status reconciliation metadata

This layer answers:

- why did this candidate die?
- why did it advance?
- what happened after OPEN_NOW?
- what did the market objectively do?
- did distribution occur?
- where exactly in the funnel was it lost?

## 2.3 Intelligence truth

Intelligence truth is the analytical interpretation layer built downstream from observability truth.
It is not the source of raw facts; it is the layer that aggregates, compares, diagnoses, and proposes.

It includes:

- performance analytics
- diagnostics dashboards
- pattern mining
- drift detection
- quality scoring summaries
- research reports
- strategy improvement suggestions
- experiment comparisons
- approval-ready recommendation packages

This layer answers:

- which gates reject too much or too little?
- where does quality decay by symbol, session, timeframe, or corridor?
- which reject reasons correlate with later favorable market moves?
- are expiries too short or too long?
- are focus/watchlist constraints killing high-value opportunities?
- which strategy branch performs better under approved experimental conditions?

## 2.4 Human authority truth

Human authority truth is the approval and governance layer.
No analytics component, no learning component, and no AI-assisted module is allowed to become canonical authority for live strategic change by itself.

Authority order remains:

1. Owner
2. Primary Admin
3. Role-based functional admins
4. Restricted auxiliary roles such as affiliate/influencer admin

Canonical governance rules:

- analytics can inform but cannot auto-govern production strategy
- AI can propose but cannot autonomously alter live strategy
- experimental branches require explicit human approval
- production promotion requires explicit approval and change audit trail
- all major evolution proposals must be reviewable in the control panel hierarchy

---

# 3. Canonical relationship between the seven documents

The seven documents must no longer be read as parallel, semi-independent systems.
They must be reinterpreted as components of one chain.

## 3.1 Correct downstream chain

Canonical chain after patch:

`Decision Audit -> Trade Temporal Telemetry -> Outcome Reconciliation -> Performance Analytics -> Research & Learning -> Strategy Intelligence Views -> Autonomous Evolution Suggestions`

This chain does not mean strict synchronous runtime dependency.
It means conceptual downstream dependence.

## 3.2 Meaning of that chain

### Decision Audit
Records why candidates advanced, stalled, or died.
It is the primary rejection/decision funnel truth.

### Trade Temporal Telemetry
Records what market reality did across time checkpoints.
It is the primary post-decision objective market-truth layer.

### Outcome Reconciliation
Adds controlled operational/admin interpretation where objective telemetry alone is insufficient.
It must not replace telemetry truth.

### Performance Analytics
Aggregates reconciled data into trends, metrics, diagnostics, and comparative views.

### Research & Learning
Uses analytics plus raw audit/telemetry evidence to generate structured insights, hypotheses, and experiment plans.

### Strategy Intelligence Views
Surfaces the above in admin dashboards, diagnostics, reporting, and investigation tools.

### Autonomous Evolution Suggestions
Produces candidate recommendations for change, simulation, and controlled experimentation, but never self-authorizes production mutation.

---

# 4. File-by-file canonical verdict and patch directives

## 4.1 `DECISION_AUDIT_SPEC_v2.0.0.md`

### Verdict
Near-canonical. Requires alignment patch, not rewrite.

### Why it is strong
This document already captures the most important missing capability in the new architecture:

- explicit rejection reasoning
- stage-by-stage funnel interpretation
- visibility into why signals die
- distinction between advancement and rejection states
- support for downstream learning

It already aligns naturally with the user’s requirement that reasons for signal death or rejection must be recorded for later analysis and strategy optimization.

### Canonical role after patch
`DECISION_AUDIT_SPEC_v2.0.0.md` must become the canonical root document for decision-funnel observability.
It should define:

- candidate evaluation events
- gate decisions
- stage transitions
- rejection reasons
- promotion reasons
- confidence/score snapshots where applicable
- focus/watchlist-related loss reasons
- feasibility / spike / SR / PRE / CONFIRM / OPEN_NOW stage-specific outcomes

### Required patch actions

1. Explicitly state that Decision Audit begins before FSM, because `DecisionObject` is produced before FSM.
2. Ensure terminology reflects the canonical strategic order where Corridor Engine is before Time Model.
3. Clarify relationship with telemetry:
   - Decision Audit explains decision logic outcome.
   - Telemetry explains objective market aftermath.
4. Clarify relationship with outcome tracking:
   - Outcome tracking is supplementary reconciliation, not replacement for decision truth.
5. Clarify relationship with intelligence layer:
   - Decision Audit is upstream source material for analytics and research.

### Upgrade proposals

- Add canonical reject-reason taxonomy versioning.
- Add support for grouped reject families: score, structure, timing, focus capacity, distribution gating, market invalidation.
- Add audit correlation IDs that can link decision records to telemetry and distribution records.
- Add “counterfactual eligibility” fields for later research such as “passed all but one gate.”

---

## 4.2 `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

### Verdict
Strong but currently too isolated. Requires medium alignment patch.

### Why it matters
This document is essential because it establishes objective truth after signal emergence.
Without it, the system falls back into subjective or operator-only interpretations of performance.

### Canonical role after patch
This document must define the factual market-behavior record associated with a candidate or an OPEN_NOW signal, including time checkpoints, expiry-aligned observations, and post-expiry aftermath where required.

It must become the canonical answer to:

- what did price actually do?
- did the move continue, reverse, stall, or whipsaw?
- what was visible at expiry and after expiry?
- was OPEN_NOW aligned with subsequent market reality?

### Required patch actions

1. Explicitly bind telemetry records to Decision Audit identifiers.
2. Clarify whether telemetry is recorded only for OPEN_NOW or also for pre-open candidates and rejected candidates under selected sampling rules.
3. Clarify checkpoint taxonomy:
   - pre-expiry checkpoints
   - expiry checkpoint
   - post-expiry checkpoints
4. Clarify objective-vs-interpreted separation:
   - telemetry stores market facts and derived neutral measurements
   - analytics interprets them downstream
5. Clarify relationship to outcome tracking:
   - admin-labeled outcomes cannot overwrite telemetry facts
6. Clarify role in expiry optimization research.

### Upgrade proposals

- Add corridor-aware and time-model-aware telemetry slices.
- Add volatility / excursion / adverse excursion / favorable excursion schema.
- Add “late winner” and “early invalidation” flags for strategy refinement.
- Add configurable telemetry retention tiers for runtime-light vs research-rich environments.

---

## 4.3 `OUTCOME_TRACKING_SPEC_v2.0.0.md`

### Verdict
Conceptually outdated in current form. Requires major patch.

### Current problem
The older model appears to treat admin-only or message-button-based recording as the main source of trade outcome truth.
That is no longer sufficient.

Operational/admin outcome reporting remains useful, but it is not allowed to stand above telemetry truth.
If a button says one thing and the market telemetry says another, the system must preserve both but not confuse them.

### Canonical role after patch
This document must be reframed as an outcome reconciliation layer.
Its role is to capture:

- operator-confirmed operational status
- manual corrections where needed
- broker/platform execution reality when available
- reasons for discrepancy between signal intent and practical outcome
- structured classification of operational success/failure

### What it must no longer claim

- It must not claim to be the sole truth of performance.
- It must not imply that Telegram button interaction is the canonical truth source.
- It must not define analytics in isolation from telemetry.

### Required patch actions

1. Rename conceptual role from pure outcome truth to outcome reconciliation / operational outcome layer.
2. Separate at least three classes of outcome:
   - market outcome truth
   - operational execution outcome
   - admin/manual correction
3. Clarify how discrepancies are stored, not overwritten.
4. Remove any language that suggests admin-only buttons are sufficient as canonical outcome infrastructure.
5. Reposition Telegram actions as UX surface, not architecture root.
6. Add audit trail for who changed what outcome state and why.

### Upgrade proposals

- Add discrepancy categories such as late entry, missed entry, distribution delay, broker mismatch, manual override.
- Add confidence level on manually entered outcomes.
- Add reconciliation status lifecycle: unresolved, partially reconciled, reconciled, disputed.
- Add admin panel views specifically for unresolved discrepancies.

---

## 4.4 `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`

### Verdict
Useful foundation but major conceptual cleanup required.

### Current problem
The document reportedly mixes solid analytics ideas with older community or elite-user feedback concepts.
That introduces noise into the canonical model.

Community sentiment may exist as a separate optional commercial or engagement module, but it must not be baked into canonical performance truth unless explicitly scoped as non-authoritative metadata.

### Canonical role after patch
This document must become the canonical aggregator and interpreter of:

- decision funnel metrics
- telemetry-derived market response metrics
- reconciled operational outcomes
- symbol/session/timeframe diagnostics
- drift and stability tracking
- branch comparison analytics

### Required patch actions

1. Remove or isolate user-voting/community-execution concepts from canonical performance truth.
2. Rebuild KPI definitions on top of Decision Audit + Telemetry + Reconciliation.
3. Clarify metric classes:
   - funnel metrics
   - market-response metrics
   - operational execution metrics
   - strategy health metrics
   - branch comparison metrics
4. Clarify that analytics is downstream and non-authoritative for live changes.
5. Ensure metrics can be sliced by symbol, session, timeframe, corridor, expiry profile, and gate family.

### Upgrade proposals

- Add gate friction metrics and false-negative suspicion metrics.
- Add expiry-fit metrics using post-expiry telemetry.
- Add focus-capacity waste metrics.
- Add deterioration and recovery dashboards by market regime.
- Add owner-facing “change justification packs” generated from analytics.

---

## 4.5 `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`

### Verdict
Important concept, but major repositioning required.

### Current problem
The older research framework appears too dependent on manual workflows, isolated trial artifacts, or legacy Telegram-driven experimentation mechanics.
That is no longer enough for the architecture being built.

### Canonical role after patch
Research & Learning must become the structured experimentation and hypothesis layer that consumes:

- audit evidence
- telemetry evidence
- reconciled outcomes
- analytics summaries
- intelligence diagnostics

and outputs:

- hypotheses
- experiment definitions
- parameter test proposals
- branch recommendations
- confidence assessments
- promotion / rejection recommendations for changes

### Required patch actions

1. Reframe research as downstream from observability and analytics, not as a sidecar log system.
2. Reduce dependence on manual trial command concepts as canonical mechanism.
3. Clarify distinction between:
   - exploratory analysis
   - controlled experiment
   - approved experimental branch
   - promoted production rule
4. Define evidence standards for strategy-change proposals.
5. Clarify integration with owner/admin approval hierarchy.

### Upgrade proposals

- Add hypothesis templates linked to reject reasons and telemetry outcomes.
- Add branch experiment registry.
- Add experiment success criteria with rollback rules.
- Add canonical comparison reports for branch A vs branch B.
- Add “not enough evidence” state to prevent overfitting.

---

## 4.6 `STRATEGY_INTELLIGENCE_SYSTEM.md`

### Verdict
Valuable bridge document, but requires medium patch and repositioning.

### Current problem
The document reportedly leans too heavily on older engine-event-centric framing.
That can still be useful operationally, but it is not the cleanest canonical definition for the intelligence layer anymore.

A newer architecture direction already establishes that intelligence is a downstream analytical layer outside the runtime critical path.
This older document should therefore become an applied system view, not the root of truth.

### Canonical role after patch
This document should describe how strategy intelligence is surfaced operationally across dashboards, diagnostics, admin tools, and investigation workflows.
It should stand as a bridge between raw canonical data sources and admin-facing usage.

### Required patch actions

1. Explicitly state it is subordinate to the broader intelligence-layer architecture.
2. Replace engine-events-only framing with multi-source intelligence inputs:
   - decision audit
   - telemetry
   - outcome reconciliation
   - performance analytics
   - distribution observability
3. Clarify it is outside the runtime critical path.
4. Clarify that intelligence dashboards are interpretive tools, not strategy-authority engines.
5. Align panel terminology with hierarchical admin model.

### Upgrade proposals

- Add Strategy Heatmap as a canonical intelligence view sourced from analytics, not raw opinion.
- Add signal debug pages tied to audit correlation IDs.
- Add regime diagnostics and gate bottleneck explorers.
- Add separate operational, research, and executive views in the admin tree.

---

## 4.7 `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

### Verdict
Promising concept, but must be tightly governed. Requires medium-to-major patch.

### Current problem
The document is directionally correct if it already states that the system does not auto-modify live strategy. That principle must now be made stricter and more explicit.

### Canonical role after patch
This document should define the controlled recommendation and experiment-orchestration layer that can:

- detect candidates for optimization
- package evidence
- suggest experiments
- compare branches
- propose promotions or reversions

but cannot unilaterally mutate live production strategy.

### Required patch actions

1. Explicitly prohibit autonomous production mutation.
2. Clarify owner / primary admin approval checkpoints.
3. Clarify dependency on research evidence and analytics packages.
4. Define safe outputs:
   - recommendations
   - simulation packages
   - experiment proposals
   - rollback suggestions
5. Clarify change history and audit obligations.

### Upgrade proposals

- Add “approval queue” integration in admin hierarchy.
- Add simulation-before-promotion rule.
- Add experiment sandbox and branch provenance tracking.
- Add canonical rollback packet generation.
- Add AI explanation bundle describing why a change is proposed.

---

# 5. New canonical hierarchy among documents

To reduce ambiguity, the seven documents should be interpreted in the following hierarchy.

## 5.1 Root observability sources

1. `DECISION_AUDIT_SPEC_v2.0.0.md`
2. `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
3. `OUTCOME_TRACKING_SPEC_v2.0.0.md` (reframed as reconciliation layer)

These are the factual and near-factual source documents.

## 5.2 Interpretive and analytical layers

4. `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
5. `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
6. `STRATEGY_INTELLIGENCE_SYSTEM.md`

These are downstream interpretive systems.

## 5.3 Governance and change proposal layer

7. `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

This is the recommendation-and-change-governance layer.

---

# 6. Canonical upgrades required in the admin/control panel

The current architecture direction requires these document families to surface clearly inside the hierarchical control panel.

## 6.1 Required panel branches

At minimum, the panel architecture should gain or clarify the following branches:

- Decision Audit
- Temporal Telemetry
- Outcome Reconciliation
- Performance Analytics
- Strategy Diagnostics
- Research Reports
- Experiment Registry
- Evolution Suggestions
- Change Approval Queue
- Rollback & Change History

## 6.2 Role visibility alignment

### Owner
Full visibility and approval authority across all branches.

### Primary Admin
Full operational and analytical visibility, with elevated proposal handling as allowed by Owner policy.

### Functional Admins
Scoped visibility depending on role:

- operations admin
- telemetry/observability admin
- analytics/research admin
- distribution admin
- support/reconciliation admin

### Affiliate / Influencer Admin
Restricted visibility only to affiliate program data and explicitly allowed summaries, with no access to sensitive strategy diagnostics or full observability internals.

## 6.3 Important canonical rule

Telegram buttons, quick admin commands, and lightweight chat UX may remain useful as operational surfaces.
However, none of them should be written canonically as the core architecture itself.
The core architecture lives in backend truth layers and control panel governance.
Telegram is a surface, not the constitution.

---

# 7. Canonical upgrades required in Telegram/admin UX

## 7.1 Required separation

The current and future docs should distinguish clearly between at least four UX classes:

1. operational signal handling
2. diagnostic investigation
3. research and reporting
4. outcome reconciliation/manual correction

These should not all collapse into buttons under an OPEN_NOW message.

## 7.2 Recommended UX direction

### Operational UX
Fast actions for live moderation, distribution inspection, and immediate issue handling.

### Diagnostic UX
Drill-down into why a candidate died, why a signal opened, what telemetry showed, and where a funnel bottleneck exists.

### Research UX
Access to structured reports, hypotheses, experiment results, branch comparisons, and recommendation packages.

### Reconciliation UX
Manual correction, discrepancy handling, and operational outcome resolution with explicit user attribution.

---

# 8. Canonical upgrades required for AI and intelligence governance

## 8.1 Non-negotiable rule

AI is not production authority.
AI may analyze, compare, simulate, summarize, and propose.
AI may not silently or automatically change live production strategy.

## 8.2 Required canonical statements across docs

All related docs should align to these statements:

- AI proposals are advisory.
- Human approval is mandatory before production strategy mutation.
- Experimental branches must be isolated from production.
- Every proposed change must have an evidence pack.
- Every promoted change must have rollback path and audit history.

## 8.3 Why this matters

Without these statements, older “autonomous evolution” language can become misleading.
The project needs a disciplined owner-controlled evolution system, not an uncontrolled self-modifying bot.

---

# 9. Strategy optimization opportunities revealed by the audit

These are not yet code changes.
They are architecture-guided upgrade opportunities that the patched documents should explicitly support.

## 9.1 Gate tuning from real funnel evidence

Use decision-audit loss distributions to identify:

- gates that reject too aggressively
- gates that allow too much noise
- specific symbol/session gate pathologies

## 9.2 Expiry optimization from telemetry

Use expiry and post-expiry checkpoints to learn:

- whether wins arrive too late
- whether entries are too early
- whether current expiry windows are misfit by regime or symbol

## 9.3 Focus/watchlist capacity optimization

Use focus-related rejection reasons to learn:

- whether capacity is too small
- whether ranking is wrong
- whether priority decay rules need redesign

## 9.4 Corridor and time-model diagnostics

Because Corridor Engine is canonically before Time Model, analytics must allow investigation of:

- corridor suitability by symbol/session
- downstream time-model fit after corridor qualification
- false negatives caused by corridor constraints

## 9.5 Branch experimentation discipline

Every serious tuning idea should be able to become:

1. hypothesis
2. experiment definition
3. controlled branch
4. analytics comparison
5. approval decision
6. promotion or rejection

---

# 10. Recommended order of document patching

To avoid chaos, patch order matters.

## Phase 1 — Root truth cleanup

1. `DECISION_AUDIT_SPEC_v2.0.0.md`
2. `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
3. `OUTCOME_TRACKING_SPEC_v2.0.0.md`

Reason:
Without clean source-truth layers, everything downstream will inherit ambiguity.

## Phase 2 — Interpretation cleanup

4. `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
5. `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
6. `STRATEGY_INTELLIGENCE_SYSTEM.md`

Reason:
These documents must be rewritten to depend on the corrected truth layers.

## Phase 3 — Governance and evolution cleanup

7. `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

Reason:
This document should only be finalized after truth, analytics, and research layers are already aligned.

---

# 11. What we keep, what we demote, what we remove

## 11.1 Keep

Keep and strengthen:

- explicit reject reasons
- funnel stage visibility
- objective temporal telemetry
- admin-facing diagnostics
- structured research workflows
- controlled strategy evolution proposals
- owner approval supremacy

## 11.2 Demote

Demote from canonical truth to optional surface or metadata:

- Telegram-message-first architectural framing
- admin button outcomes as sole truth source
- engine-event-only intelligence framing
- community or elite-user feedback as primary performance truth

## 11.3 Remove or isolate

Remove from canonical core or isolate in optional modules:

- any language implying self-modifying live strategy without approval
- any language implying manual admin records overwrite objective telemetry
- any language that mixes community sentiment into performance truth without explicit non-authoritative labeling

---

# 12. Final canonical conclusion

After audit, the seven documents remain valuable, but they are not equally current.
They must be unified under one architectural interpretation.

The cleanest canonical model is:

- `DECISION_AUDIT_SPEC_v2.0.0.md` = why the bot decided, advanced, or rejected
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` = what the market objectively did afterward
- `OUTCOME_TRACKING_SPEC_v2.0.0.md` = what operationally happened and how discrepancies are reconciled
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` = how evidence is aggregated into diagnostics and metrics
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md` = how evidence becomes hypotheses and experiments
- `STRATEGY_INTELLIGENCE_SYSTEM.md` = how intelligence is surfaced to admins and operators
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md` = how improvement proposals are generated and governed under strict approval control

This is the alignment needed before code implementation.

---

# 13. Immediate next action

Immediate next action after saving this patch document:

Patch the three root truth documents first, in this order:

1. `DECISION_AUDIT_SPEC_v2.0.0.md`
2. `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
3. `OUTCOME_TRACKING_SPEC_v2.0.0.md`

Only after those are canonically clean should the downstream analytics, research, intelligence, and evolution documents be patched.
