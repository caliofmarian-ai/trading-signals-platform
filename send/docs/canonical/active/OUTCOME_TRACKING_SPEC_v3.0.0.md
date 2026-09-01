# OUTCOME_TRACKING_SPEC_v3.0.0

Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: operational/admin outcome reconciliation and Trade Physics training-label lineage support  
Supersedes: `OUTCOME_TRACKING_SPEC_v2.0.0.md`  

Linked proposed/current authorities:
- Root Strategy Stack successor
- `ALGO_SPEC_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- Performance Analytics successor
- Research & Learning successor
- Strategy Intelligence successor
- Event/Observability successors

---

## 0. Authority and promotion status

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

The major version reflects a structural expansion of reconciliation lineage so operational outcomes remain distinguishable from market labels while still being usable safely by Trade Physics analytics and intelligence.

This document does not authorize broker execution or automatic strategy mutation.

---

## 1. Purpose

Outcome Tracking defines the operational/admin reconciliation layer for executable signals.

It records what happened from the operator or governed operational path, while preserving separation from:
- strategy decision truth;
- FSM truth;
- signal-execution/distribution truth;
- objective market telemetry truth.

It exists to answer:
- was a signal actually acted on operationally?
- was it missed?
- was there a platform/broker/workflow mismatch?
- was a manual correction required?
- does operator reality disagree with market telemetry?
- are recurring discrepancies strategy problems or operational problems?

---

## 2. Canonical architecture position

High-level chain:

`DecisionObject -> FSM -> governed executable signal -> Telemetry Market Truth -> Outcome Reconciliation -> Performance Analytics -> Research -> Intelligence`

Outcome Reconciliation is downstream operational truth.

It never overwrites upstream decision records or objective market telemetry.

---

## 3. Truth separation

### 3.1 Decision truth
What the strategy believed and why.

### 3.2 Market truth
What the market objectively did, sourced from Trade Temporal Telemetry.

### 3.3 Operational/admin truth
What the operator/admin execution path recorded, including WIN/LOSE/MISSED and corrections.

### 3.4 Community/user truth
Self-reported experience, if supported, remains non-authoritative unless explicitly accepted through a governed reconciliation path.

No analytics or AI dataset may merge these truth classes without explicit labels.

---

## 4. Baseline outcome classes

Canonical operational classes remain:
- `WIN`
- `LOSE`
- `MISSED`

`MISSED` is an operational state, not a market LOSS.

Future classes such as DISPUTED/BROKER_REJECTED may be introduced only through versioned governance.

---

## 5. Access-control rule

Outcome mutation is privileged/admin-controlled by default.

Subscribers/community actors do not set canonical operational outcomes directly.

Every mutation must pass role/permission checks and produce proof evidence.

---

## 6. Stable signal identity

Every canonical outcome record must be linked to a known executable signal.

Minimum linkage:
- `signal_id`
- symbol
- direction
- timeframe
- executable/open timestamp
- correlation id
- telemetry record/reference where available
- decision audit reference where available

If stable identity is missing, canonical write must fail.

---

## 7. Reconciliation lifecycle

Recommended canonical statuses:
- `PENDING`
- `SET`
- `RECONCILED`
- `DISPUTED`
- `OVERRIDDEN`

Meaning:
- PENDING: no operational outcome yet;
- SET: an authorized outcome exists but is not fully reconciled;
- RECONCILED: reviewed/accepted operational state;
- DISPUTED: unresolved mismatch;
- OVERRIDDEN: later authorized correction replaced a prior state.

All transitions must remain reconstructible.

---

## 8. Admin surface

Outcome mutation may be exposed through:
- Telegram admin buttons;
- protected admin command;
- control panel;
- reconciliation dashboard;
- future mobile/web control surface.

UI is not architecture authority.

All surfaces must provide the same:
- authorization;
- validation;
- persistence;
- idempotency;
- audit trail;
- feedback on success/failure.

---

## 9. Idempotency and overwrite discipline

Duplicate submission of the same outcome for the same signal must not create duplicate counters/events.

If an outcome changes:
- previous value is preserved;
- previous timestamp/actor is preserved or reconstructible;
- correction reason is recorded when applicable;
- override is observable.

Silent overwrite is forbidden.

---

## 10. Persistent data contract

Outcome storage must survive restart and support deterministic lookup by signal identity.

Minimum required fields:
- `signal_id`
- `outcome`
- `outcome_set_at_utc`
- authorized actor id
- reconciliation status
- outcome source
- correlation identifiers

Strongly recommended:
- symbol
- direction
- timeframe
- execution/expiry context
- admin message/chat references where applicable
- decision audit id
- telemetry record id
- previous outcome metadata
- correction/discrepancy reason

---

## 11. Trade Physics snapshot linkage

Outcome records may carry or reference the immutable pre-trade Trade Physics snapshot, but must not recompute strategic mathematics themselves.

Recommended linked fields:
- deterministic `TPS`
- TPS component snapshot or snapshot reference
- Trade Physics formula/version
- feature schema version
- classical `score_total`
- corridor state
- time state
- `trade_success_probability` snapshot only if a validated model produced it before the trade
- model id/version/readiness when that probability exists

The authoritative pre-trade feature values come from DecisionObject/Telemetry lineage, not from outcome-time recomputation.

---

## 12. Outcome vs training-label rule

Operational `WIN/LOSE/MISSED` is not automatically the supervised market label for Trade Physics probability modeling.

Default market-truth training label must come from canonical telemetry unless a specific experiment explicitly targets operational execution probability.

Examples:
- telemetry WIN + operational MISSED -> market label WIN, operational label MISSED;
- telemetry LOSS + operational WIN after manual late exit -> market label LOSS, operational label WIN;
- neither label overwrites the other.

Dataset builders must name the target explicitly, e.g.:
- `market_trade_success`
- `operational_execution_success`
- `missed_execution_probability`

Unlabeled target mixing is forbidden.

---

## 13. Discrepancy model

The layer must support explicit comparison with telemetry truth.

Example discrepancy classes:
- `MATCH`
- `MARKET_WIN_OPERATIONAL_MISSED`
- `MARKET_LOSS_OPERATIONAL_WIN`
- `MARKET_WIN_OPERATIONAL_LOSE`
- `TELEMETRY_MISSING`
- `OPERATIONAL_OUTCOME_MISSING`
- `MANUAL_OVERRIDE_REQUIRES_REVIEW`

Exact taxonomy may evolve through versioning, but discrepancy must be explicit rather than inferred.

---

## 14. Observability requirements

Every meaningful outcome mutation/reconciliation action must be observable.

Canonical event naming is governed by Event Schema successor; the outcome layer must provide evidence for at least:
- submission/mutation attempt;
- accepted/rejected mutation result;
- reconciliation completion;
- dispute;
- override/correction.

Required evidence includes:
- signal id;
- actor;
- requested outcome;
- previous outcome;
- final state;
- timestamp;
- authorization result;
- reason;
- correlation id.

---

## 15. Analytics integration

Performance Analytics may use operational outcomes as operational truth.

Default operational counters:
- wins
- losses
- missed

Operational WR baseline:

`wins / (wins + losses)`

MISSED is excluded unless the metric explicitly states otherwise.

Dashboards must label truth layer, e.g.:
- Market WR
- Operational WR
- Execution Rate
- Missed Rate
- Discrepancy Rate

No unlabeled blended WR is allowed.

---

## 16. Trade Physics analytics value

Outcome Reconciliation enables analysis of whether strong/weak Trade Physics contexts are difficult to execute operationally even when market truth is good.

Useful analyses include:
- missed rate by TPS band;
- operational discrepancy by TPS band;
- execution reliability by flow/space/time regime;
- differences between market calibration and operator-realized performance;
- whether high-probability contexts are operationally usable in each channel/session.

These analyses may inform UX/operations and research, but do not silently change deterministic TPS formula or strategy thresholds.

---

## 17. Relationship to Telemetry

Telemetry owns objective market result.

Outcome Reconciliation owns operational/admin result.

They must remain independently persisted and joinable.

Telemetry disagreement does not automatically invalidate an admin record; it creates a discrepancy requiring labeled interpretation.

---

## 18. Relationship to Decision Audit

Decision Audit explains why the setup existed and how it was evaluated.

Outcome Reconciliation records downstream operational reality.

Outcome records do not explain strategy causality and must not rewrite Decision Audit.

---

## 19. Relationship to Research/Intelligence/AI

Research may use outcome records to study:
- execution friction;
- missed-trade clusters;
- admin correction patterns;
- discrepancy patterns;
- operational suitability by symbol/session/regime.

Trade Physics Intelligence may consume these as separately labeled targets/features for operational models, but not as substitutes for objective market labels.

Autonomous Strategy Evolution may propose changes from this evidence, subject to readiness and human approval.

---

## 20. Community feedback boundary

Self-reported member/community outcomes are supportive experience evidence only unless formally accepted through canonical admin reconciliation.

They must be labeled as self-reported/non-authoritative on user-facing and analytical surfaces.

---

## 21. Safety rules

1. Known executable signal required.
2. Stable signal identity required.
3. Authorized actor required.
4. Duplicate writes must be idempotent.
5. Overwrites must preserve history.
6. Telemetry truth must never be overwritten.
7. Decision truth must never be overwritten.
8. Trade Physics features must not be recomputed from post-outcome knowledge.
9. Missing/ambiguous lineage must be visible.
10. Outcome mutation cannot directly mutate strategy parameters.

---

## 22. Future controlled extensions

Possible extensions include:
- broker execution linkage as a separate truth class;
- multi-actor reconciliation;
- richer dispute queues;
- support explanation bundles;
- operational reliability dashboards.

They require governed schema and authority updates.

---

## 23. Non-goals

This document does not define:
- strategy math;
- deterministic TPS formula;
- market telemetry label rules;
- broker execution engine;
- public subscriber voting authority;
- automatic strategy mutation.

---

## 24. Final principle

Outcome Tracking is a governed operational reconciliation layer.

For Trade Physics it provides valuable execution-context labels and discrepancy evidence, but it never replaces objective market telemetry or pre-trade strategic truth.
