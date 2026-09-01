# RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0

Version: 2.0.0  
Path: /opt/binarybot/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- /opt/binarybot/docs/canonical/active/AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md


Status: Active Canonical  
Path target: `/opt/binarybot/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md`  
Supersedes: `/opt/binarybot/docs/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`

Related canonical documents:
- `/opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

---

## 1. PURPOSE

This document defines the canonical **Research and Learning Framework** for BinaryBot / DROPi Signals.

Its purpose is to transform runtime evidence into structured understanding, validated hypotheses, controlled experiments, and governance-safe strategy improvement.

Research is not the same thing as:
- raw logging
- outcome capture
- ad-hoc chart watching
- operator intuition
- emotional reaction to streaks

Research is the disciplined layer that converts evidence into controlled learning.

The older v1.0.0 document correctly established several important goals:
- identify profitable symbols
- evaluate conversion quality
- detect weak symbols and wasted setups
- validate edge using real outcomes
- support controlled parameter experimentation
- guide long-term strategy evolution fileciteturn30file0

Those goals remain valid.

What changes in v2.0.0 is that research is no longer treated as a narrow extension of `focus_history` plus trial outcomes. It becomes a cross-layer framework that consumes multiple truth domains and feeds multiple consumers.

---

## 2. WHY V1.0.0 IS NO LONGER SUFFICIENT

The older document is useful as a first-generation framework, but it is now too narrow for the current architecture.

Its limitations include:

1. It centers the research pipeline around:
   - engine signal events
   - focus history dataset
   - trial results dataset
   - research analytics
   - strategy optimization fileciteturn30file0

2. It assumes trial outcome validation as the main evidence model.

3. It does not explicitly separate:
   - decision truth
   - market truth
   - operational/admin truth
   - community truth
   - business truth

4. It does not define a formal:
   - hypothesis registry
   - experiment governance model
   - evidence confidence model
   - research-to-admin/control-panel feedback loop
   - research-to-intelligence feedback loop
   - research-to-AI guardrail model

5. It treats Telegram result commands and pending trial workflow as central to research, whereas in the newer architecture those belong primarily to outcome tracking / operational truth layers. fileciteturn30file0

For the current strategy stack, research must become broader, stricter, and more governance-safe.

---

## 3. CANONICAL POSITION IN THE ARCHITECTURE

Research and Learning is downstream of evidence generation and upstream of governance, intelligence, and controlled improvement.

Canonical chain:

`Strategy Logic -> DecisionObject -> FSM -> Signal Execution -> Observability -> Telemetry -> Outcome Reconciliation -> Performance Analytics -> Research & Learning -> Intelligence / Governance / Controlled Evolution`

Research does not produce raw truth.
Research interprets truth, tests hypotheses, detects patterns, and proposes controlled changes.

---

## 4. CANONICAL RESEARCH PHILOSOPHY

### 4.1 Research must be evidence-led
No strategic conclusion may be justified only by:
- intuition
- one bad day
- one good day
- trader frustration
- Telegram complaints alone
- isolated streaks

### 4.2 Research must preserve truth separation
Research may analyze multiple truth layers, but it must not collapse them into one unlabeled dataset.

### 4.3 Research must produce actionable understanding
Research is only useful if it can support:
- parameter governance
- symbol rotation governance
- admin workflow improvement
- Telegram UX improvement
- intelligence and AI audits
- future controlled evolution

### 4.4 Research must not directly mutate production strategy
Research may propose.
Governance decides.
Implementation applies.
Validation confirms.

---

## 5. RESEARCH INPUT DOMAINS

The older document focused mostly on:
- focus lifecycle events
- trial outcomes
- symbol/buffer/session analytics fileciteturn30file0

Those remain useful, but v2.0.0 expands research inputs.

Research may consume from the following domains:

### 5.1 Decision evidence
Examples:
- candidate generation
- PRE / CONFIRM / OPEN_NOW progression
- rejection reasons
- score distributions
- corridor decisions
- timing decisions
- feasibility decisions

Primary source:
- `DECISION_AUDIT_SPEC_v2.0.0.md`

### 5.2 Market evidence
Examples:
- post-emission path shape
- favorable/adverse excursion
- expiry result
- time-to-target / time-to-fail
- post-entry stability

Primary source:
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

### 5.3 Operational evidence
Examples:
- admin outcomes
- missed trades
- corrections
- overrides
- discrepancy queues

Primary source:
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`

### 5.4 Performance evidence
Examples:
- segmented win rates
- expectancy
- drift
- lifecycle conversion
- discrepancy rates
- drawdown clusters

Primary source:
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`

### 5.5 Observability evidence
Examples:
- instrumentation health
- missingness
- event integrity
- state inconsistency
- latency

### 5.6 Business / UX evidence
Examples:
- channel engagement
- support complaints
- admin response friction
- user trust divergence
- affiliate conversion quality

---

## 6. RESEARCH OUTPUTS

Research must produce outputs in forms that are reusable by the system.

Canonical research outputs include:

1. **Findings**
2. **Hypotheses**
3. **Evidence summaries**
4. **Confidence-rated conclusions**
5. **Experiment proposals**
6. **Governance recommendations**
7. **Risk flags**
8. **Admin / UX / Intelligence recommendations**

Research is not only a reporting layer. It is a structured knowledge-production layer.

---

## 7. CORE RESEARCH QUESTIONS

The older document asked useful questions such as:
- which symbols generate the most valid trades?
- which symbols waste scanning resources?
- which buffer modes perform best?
- which sessions perform best?
- which regimes degrade performance? fileciteturn30file0

These remain valid and are extended.

Canonical research questions now include:

### Strategy quality
- Which filters improve quality versus only reduce frequency?
- Which rejection reasons are protective versus overly harsh?
- Which score bands are truly predictive?

### Symbol quality
- Which symbols are strong, weak, unstable, or deceptive?
- Which symbols are only locally strong by session or regime?

### Session quality
- Which sessions create stable edge?
- Which sessions produce false confidence?

### Corridor / temporal interaction quality
- Which corridor regimes pair well or badly with time constraints?
- Are we rejecting too early or too late?

### Operational distortion
- Where is strategy quality being hidden by admin misses, latency, or reconciliation gaps?

### UX / business distortion
- Where does user experience diverge from market-truth quality?
- Which channels create confusion despite acceptable strategy performance?

### Evolution readiness
- Which parts of the system are safe candidates for experimentation?
- Which parts are too unstable for mutation?

---

## 8. RESEARCH DATASETS

### 8.1 Legacy datasets
The older spec defined:
- `/opt/binarybot/logs/focus_history.jsonl`
- `/opt/binarybot/data/trials.jsonl`
- supporting trial index / pending files fileciteturn30file0

These may still exist as historical or supporting sources.

### 8.2 Canonical v2.0.0 position
No single file is the “research truth” by itself.

Research datasets are composed from labeled evidence streams.

Recommended categories:
- decision audit datasets
- telemetry datasets
- outcome reconciliation datasets
- analytics snapshots
- observability datasets
- optional business / UX datasets
- optional community feedback datasets

### 8.3 Truth labeling rule
Every dataset consumed by research must declare:
- source domain
- truth layer
- time window
- version
- derivation method

No unlabeled merged dataset is allowed.

---

## 9. RESEARCH EVENT AND ENTITY MODEL

The older document focused on lifecycle events such as:
- `FOCUS_ENTER`
- `FOCUS_EXIT`
- `PRE_SENT`
- `CONFIRM_SENT`
- `OPEN_NOW_SENT`
- rejection events
- cooldown events
- operator actions fileciteturn30file0

These remain useful as historical event examples, but the canonical research model should now operate on higher-level entities:

### 9.1 Candidate entity
A potential setup entering strategic evaluation.

### 9.2 Decision entity
The evaluated object with score, gates, and reasons.

### 9.3 Execution entity
The emitted executable signal and its operational context.

### 9.4 Telemetry entity
The post-emission market path evidence.

### 9.5 Outcome entity
The reconciled outcome, including operational and discrepancy context.

### 9.6 Experiment entity
A controlled research object representing a hypothesis under test.

This shift prevents research from being trapped in narrow event logs only.

---

## 10. HYPOTHESIS REGISTRY (NEW MANDATORY CONCEPT)

One of the biggest missing pieces in v1.0.0 is a formal hypothesis system.

Research must maintain a hypothesis registry with entries such as:

- hypothesis_id
- title
- category
- rationale
- evidence basis
- affected symbols/sessions/regimes
- proposed change
- expected effect
- measurement plan
- risk level
- approval status
- final conclusion

Example hypothesis categories:
- score calibration
- corridor strictness
- time gating
- expiry tuning
- symbol inclusion/removal
- buffer mode adaptation
- admin UX improvement
- Telegram communication clarity

Canonical rule:
No important parameter change should happen without being traceable to a hypothesis or equivalent governance artifact.

---

## 11. EVIDENCE CONFIDENCE MODEL

Research findings must not all be treated as equally trustworthy.

Each finding should be confidence-rated.

Suggested classes:
- low confidence
- moderate confidence
- high confidence
- production-ready evidence

Confidence should consider:
- sample size
- truth-layer quality
- discrepancy rate
- missingness
- regime stability
- repeatability across windows
- consistency across segments

This is essential to prevent premature strategic changes.

---

## 12. SYMBOL RESEARCH

The older document correctly emphasized symbol ranking, conversion quality, weak-symbol detection, and symbol rotation. fileciteturn30file0  
That remains mandatory.

Research should evaluate symbols across:

- signal production quality
- decision quality
- market outcome quality
- operational reliability
- discrepancy rate
- session-local behavior
- regime-local behavior
- business usefulness

Possible classifications:
- strong
- stable
- conditional
- deceptive
- weak
- unstable
- operationally expensive

A symbol may be profitable in market truth but still poor in subscriber experience because of poor execution timing or admin friction. Research must be able to detect that.

---

## 13. SESSION RESEARCH

The older document already required session analysis across ASIA, LONDON, NEW YORK, and LATE. fileciteturn30file0  
This remains mandatory.

Research should analyze sessions by:

- candidate density
- decision promotion quality
- executable frequency
- market-truth expectancy
- operational miss rate
- discrepancy rate
- admin load
- user perception / complaint intensity where available

Possible outputs:
- session keep
- session watch
- session downgrade
- session split by symbol
- session-specific parameter investigation

---

## 14. BUFFER / PARAMETER RESEARCH

The older document studied buffer modes SMALL / MEDIUM / LARGE and parameter experimentation. fileciteturn30file0  
That remains useful, but now must be framed inside controlled evidence and truth labeling.

Research may study:
- buffer regimes
- score thresholds
- expiry choices
- corridor strictness
- timing gates
- confirmation thresholds
- focus behavior
- execution messaging timing

Every finding must state:
- compared windows
- sample sizes
- truth layer
- confidence level
- side effects detected

---

## 15. REGIME RESEARCH

The older document required volatility regime analysis. fileciteturn30file0  
That remains valid and should expand.

Research may analyze:
- volatility regime
- trend regime
- corridor regime
- timing regime
- spread/noise regime
- local instability regime

Canonical goal:
Determine not only whether the system wins, but **under what structural conditions it is safe, unsafe, or misleading**.

---

## 16. DRIFT RESEARCH

The older document already identified market structure change, volatility shifts, parameter misconfiguration, and symbol instability as possible causes of degradation. fileciteturn30file0

That remains correct.

Research drift analysis should detect and explain:
- strategy drift
- symbol-local drift
- session-local drift
- operational drift
- discrepancy drift
- UX trust drift
- performance divergence between truth layers

Research must not merely detect drift.
It must attempt to localize it.

---

## 17. EXPERIMENT GOVERNANCE

The older document proposed a simple sequence:
1. define hypothesis
2. apply parameter change
3. collect data
4. compare before/after fileciteturn30file0

That is a good starting point, but v2.0.0 requires stricter governance.

### 17.1 Experiment lifecycle
Recommended lifecycle:
`PROPOSED -> REVIEWED -> APPROVED -> STAGED -> RUNNING -> EVALUATED -> ACCEPTED / REJECTED / EXTENDED`

### 17.2 Experiment record
Every experiment should include:
- experiment_id
- linked hypothesis_id
- owner / reviewer
- scope
- change definition
- affected domains
- success criteria
- failure criteria
- rollback criteria
- minimum sample target
- start/end window
- final conclusion

### 17.3 Canonical rule
No silent production mutation is allowed.
Important strategic changes must be explainable and reviewable later.

---

## 18. ANTI-ILLUSION RULES

The older document already recommended minimum 200 trades and warned against subjective strategy changes. fileciteturn30file0  
That principle remains canonical.

Research must explicitly resist:
- streak panic
- overfitting to one regime
- overfitting to one symbol
- overreacting to one complaint wave
- mixing admin misses with market failure
- confusing low frequency with high quality
- confusing high community excitement with actual edge

Any research report should call out these risks where relevant.

---

## 19. REPORTING MODEL

The older document required periodic research reports with symbol ranking, conversion rates, rejection breakdowns, session statistics, and buffer comparisons. fileciteturn30file0  
That remains useful, but the report structure should be upgraded.

Canonical research report sections:

1. reporting window
2. evidence sources
3. truth layers used
4. data-quality caveats
5. key findings
6. symbol findings
7. session findings
8. parameter findings
9. regime findings
10. drift findings
11. discrepancy findings
12. hypotheses proposed
13. experiments recommended
14. admin / Telegram UX recommendations
15. intelligence / AI recommendations
16. governance recommendation summary

This makes research reporting operationally useful.

---

## 20. ADMIN / CONTROL PANEL / TELEGRAM / UX RESEARCH FEEDBACK

Because you asked that patching should also surface upgrade proposals, this framework formally includes research outputs for adjacent subsystems.

### 20.1 Admin control panel proposals
Research should be able to recommend:
- symbol watchlists
- session watchlists
- discrepancy review queues
- filter-harshness panels
- drift alerts
- experiment tracking panels

### 20.2 Telegram UX proposals
Research should be able to identify:
- messages users misinterpret
- situations where signals arrive too late to be practical
- contexts where admin result entry creates ambiguity
- moments where subscriber trust suffers despite decent market-truth performance

### 20.3 Intelligence proposals
Research should feed intelligence systems with:
- structured findings
- anomaly candidates
- candidate ranking data
- mutation risk estimates
- confidence-rated learning signals

---

## 21. AI AND AUTONOMOUS EVOLUTION GUARDRAILS

The project includes broader interest in AI intelligence and future autonomous evolution.

Research may feed these systems, but strong guardrails are required.

### 21.1 AI may assist with:
- pattern discovery
- hypothesis suggestion
- segmentation analysis
- anomaly clustering
- documentation of findings

### 21.2 AI may not independently do:
- silent parameter mutation
- canonical truth rewriting
- production rollout without approval
- strategic conclusion from unlabeled or low-confidence data

### 21.3 Controlled evolution rule
Autonomous systems may only act within governance-approved boundaries and must remain auditable.

---

## 22. SYMBOL ROTATION AND STRATEGY EVOLUTION

The older document correctly included symbol rotation policy and continuous strategy evolution. fileciteturn30file0  
These remain valid, but require governance framing.

Research may recommend:
- add symbol
- pause symbol
- remove symbol
- narrow symbol to specific sessions
- split symbol by regime treatment
- retune symbol-specific parameters

Research may also recommend:
- preserve strategy component unchanged
- downgrade confidence in a subsystem
- investigate corridor-time interaction
- postpone experimentation until instrumentation quality improves

Evolution should be:
- measured
- reversible
- documented
- versioned
- justified

---

## 23. MINIMUM GUARANTEES

If this framework is implemented correctly, the system gains the following guarantees:

- research conclusions become traceable
- hypotheses become auditable
- parameter changes become reviewable
- weak symbols and weak sessions are identified earlier
- operational distortion stops contaminating strategic conclusions
- admin / UX / intelligence improvements can be driven by evidence
- future AI participation remains bounded by governance

This upgrades the project from “we observed something” to “we learned something reproducible and can act on it safely.”

---

## 24. NON-GOALS

This document does not define:
- the raw strategy logic itself
- corridor computation internals
- time model implementation details
- final public channel product rules
- exact database schema for every dataset
- broker-side execution contracts

It defines the research, learning, evidence interpretation, and experimentation framework.

---

## 25. SUMMARY

The older `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md` correctly established the original research loop:
runtime events -> focus dataset -> trial dataset -> research analytics -> strategy optimization, and it correctly emphasized symbol research, buffer/session/regime analysis, drift detection, parameter experimentation, reports, and continuous improvement. fileciteturn30file0

In v2.0.0, those foundations are preserved but expanded into a more mature architecture.

Research and Learning is now defined as a cross-layer framework that:
- consumes multiple truth domains
- preserves evidence labeling
- generates findings and confidence-rated conclusions
- maintains a hypothesis registry
- governs controlled experiments
- feeds admin, Telegram UX, intelligence, AI audit, and controlled strategy evolution

This makes the research layer compatible with the new strategy architecture rather than trapping it inside the old focus-history + trial-results model.

## 19. Daily Audit Reporting and Bottleneck Review

This section absorbs bounded content from AI_STRATEGY_AUDITOR_SPEC.md.

### 19.1 Daily audit role
Research workflows may produce daily audit summaries describing where signals were accepted, rejected, delayed, suppressed, or degraded.

### 19.2 Bottleneck visibility
Review outputs may highlight repeated bottlenecks such as cooldown_active, channel_inactive, focus starvation, or empty output despite active symbols.

### 19.3 Recommendation boundary
Recommendations remain research-oriented until adopted through canonical governance.

## 20. Research/Proof Intake Clarifications from Statistical Proof Layer

This section absorbs bounded research clarifications extracted from STATISTICAL_PROOF_LAYER.md.

### 20.1 Research utility
Proof-style statistical analysis may be used to evaluate edge persistence, regime behavior, validation confidence, and research hypotheses.

### 20.2 Governance boundary
These proof-oriented outputs remain research/support material until formally adopted through canonical governance and change control.

### 20.3 Evidence continuity
Any proof-oriented analysis must remain traceable to canonical evidence and active observability/analytics sources.
