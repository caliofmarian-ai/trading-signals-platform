# COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0

Canonical Name: COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Supersedes: `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md`  
Scope: community/self-reported feedback, member execution experience, private member statistics, optional leaderboard, privacy, and reconciliation with objective/operational truth

Linked authorities:
- `SIGNAL_DISTRIBUTION_SPEC` current promoted successor
- `CHANNEL_CONFIG_SPEC` current promoted successor
- `TELEGRAM_UX` current promoted successor
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL` current promoted successor
- `SECURITY_MODEL` current promoted successor
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`

---

## 0. Authority and promotion status

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

This v3 successor is required because v2 describes Admin Outcome as the single canonical truth used for strategy evaluation. The current canonical graph separates:
- objective market truth;
- operational/admin reconciliation truth;
- community/self-reported truth.

This is a structural truth-model correction and therefore requires a major version.

No broker execution or automatic strategy mutation is authorized by this document.

---

## 1. Purpose

This document governs the community feedback and member privacy layer.

It preserves the useful v2 capabilities:
- member feedback on signals;
- ELITE outcome/reason reporting;
- private member statistics;
- optional self-reported leaderboard;
- pseudonymous member references;
- anti-gaming controls;
- strict privacy;
- admin review and export;
- feedback observability.

It also establishes the mandatory multi-truth model required for Trade Physics analytics and learned-model safety.

---

## 2. Truth-layer separation

Four truth classes may coexist and MUST remain distinguishable.

### 2.1 Strategy truth
What the strategy believed before FSM/execution.

Primary authorities:
- DecisionObject;
- Decision Audit;
- Trade Physics strategic snapshot.

### 2.2 Objective market truth
What the market objectively did after the governed executable event.

Primary authority:
- Trade Temporal Telemetry.

This is the default source for market-outcome labels used to evaluate strategy/Trade Physics predictive behavior.

### 2.3 Operational/admin truth
What the authorized operational/admin execution path recorded or reconciled.

Primary authority:
- Outcome Tracking / Reconciliation.

Examples:
- WIN;
- LOSE;
- MISSED;
- correction/dispute state.

Operational/admin truth does not overwrite objective market truth.

### 2.4 Community/self-reported truth
What an eligible member says happened in their own execution experience.

This is supportive/user-experience evidence.

It does not overwrite:
- objective market truth;
- operational/admin reconciliation;
- original strategy truth.

No layer may silently collapse these truth classes into one unlabeled outcome.

---

## 3. Community feedback scope

Community feedback may apply to governed eligible routes such as:
- FREE;
- BASIC;
- PRO;
- ELITE.

Purpose:
- collect user execution experience;
- detect visibility/latency/expiry misunderstandings;
- detect recurring operational friction;
- support member self-analysis;
- support aggregate product/UX diagnostics.

Community feedback is not strategy ground truth.

---

## 4. ELITE execution-experience dataset

ELITE may retain richer member-reported experience data where entitlement policy allows.

Eligible members may report:
- outcome experienced;
- reason for loss;
- reason for missed trade;
- optional bounded execution-context classifications;
- private statistics.

This dataset is named and treated as **self-reported execution experience**, not objective market outcome data.

---

## 5. Self-reported outcome types

Baseline self-reported outcomes remain:

| Outcome | Meaning |
|---|---|
| WIN | Member reports that they executed and won. |
| LOSE | Member reports that they executed and lost. |
| MISSED | Member reports that they did not execute or entered too late. |

These values MUST be stored/labelled with a source such as `COMMUNITY_SELF_REPORT` or equivalent.

They MUST NOT be stored as if they were telemetry market labels.

---

## 6. Stable signal identity

Every feedback entry must reference a known governed signal identity.

Minimum:
- `signal_id`;
- member/user identity in protected storage;
- feedback timestamp;
- route/tier context where relevant.

If `signal_id` is missing or invalid, feedback submission must be disabled/rejected.

Feedback must not create a new signal identity.

---

## 7. Feedback interface

Feedback may be exposed under eligible OPEN_NOW messages or through another governed member interface.

Baseline buttons:
- WIN;
- LOSE;
- MISSED.

For eligible ELITE workflows, a second-stage reason selection may appear after LOSE or MISSED.

UI is not truth authority. It must preserve source labels and entitlement rules.

---

## 8. Two-step ELITE feedback

### Step 1 — self-reported outcome
- WIN
- LOSE
- MISSED

### Step 2 — bounded reason when applicable
If LOSE -> show governed LOSE reasons.
If MISSED -> show governed MISSED reasons.
WIN need not require a reason.

Optional execution-timing descriptors may be introduced only if clearly self-reported and versioned.

---

## 9. Reason taxonomy

### 9.1 LOSE reasons
Baseline:
- LATE_ENTRY
- WRONG_EXPIRY
- WRONG_DIRECTION
- SIGNAL_DELAY
- PLATFORM_LAG
- OTHER

### 9.2 MISSED reasons
Baseline:
- NO_TIME
- SAW_TOO_LATE
- DOUBTED_SIGNAL
- TECH_ISSUE
- OTHER

`OTHER` frequency should be monitored; taxonomy extension requires governed versioning where materially used by analytics.

These reasons describe member experience and do not independently prove strategy failure.

---

## 10. Voting window

Feedback is accepted only inside the governed eligibility window.

Baseline retained from v2:

`OPEN_NOW timestamp + expiry + grace_period`

Default grace period remains 10 minutes unless changed by governed configuration/policy.

After the window closes:
- controls may remain visually present if UX chooses;
- submissions must be rejected/ignored safely;
- no historical vote may be silently accepted outside policy.

---

## 11. Deduplication and update rules

One active self-reported outcome per `(signal_id, user_id)`.

Updates may be allowed only within the voting window.

Every accepted update must remain auditable.

After closure, member submissions are locked unless a separately governed correction workflow exists.

---

## 12. ELITE membership verification

ELITE feedback requires active ELITE entitlement.

Telegram membership checking may remain an implementation mechanism where Telegram is the current surface.

Canonical rule:
- entitlement must be validated before accepting protected ELITE feedback;
- membership transport details may evolve without redefining feedback truth.

No hardcoded one-off bypass is allowed outside governed admin/security policy.

---

## 13. Persistent storage

Raw self-reported records must be persistently stored and rebuildable.

Storage must preserve at minimum:
- `signal_id`;
- protected/pseudonymous member identity;
- self-reported outcome;
- reason where applicable;
- timestamp;
- route/entitlement context;
- record schema/version;
- source label indicating self-report.

Counters/leaderboards should be rebuildable from raw immutable or auditable records.

Storage location is an implementation contract and may evolve under Module/Storage governance.

---

## 14. Relationship to Trade Physics datasets

Community feedback may be joined to Trade Physics snapshots for research on **execution experience**, but it is not the default market-success training label.

Permitted examples:
- TPS vs member MISSED rate;
- directional flow vs late-entry reports;
- model probability vs member execution difficulty;
- route/message latency vs SIGNAL_DELAY reports.

Forbidden:
- treating community WIN/LOSE directly as objective market label without explicit experiment target/source labeling;
- overwriting telemetry `market_trade_success` with community self-report;
- using post-outcome community reasons as pre-trade model features.

Anti-leakage rules from Trade Physics Intelligence apply.

---

## 15. Relationship to Outcome Reconciliation

Outcome Reconciliation is operational/admin truth.

Community feedback is self-reported member truth.

If community consensus disagrees with operational/admin outcome:
- both truths remain preserved;
- mismatch may be flagged for review;
- neither record is silently rewritten.

If either disagrees with objective telemetry:
- telemetry market truth also remains preserved;
- discrepancy analytics may compare the layers explicitly.

There is no single unlabeled `canonical outcome` that erases the others.

---

## 16. Member private statistics

Eligible members may access their own self-reported statistics through protected private surfaces.

Baseline commands/surfaces may include:
- `/my_stats`;
- `/my_history`;
- `/my_reasons`;
- `/my_ref`;
- equivalent future web/mobile surfaces.

Rules:
- return only the requesting member's authorized data;
- do not expose other members;
- clearly label statistics as self-reported when based on self-reported records.

---

## 17. Member reference identity

Raw Telegram/user identifiers must not be exposed publicly.

A pseudonymous `MEMBER_REF` may be used.

Requirements:
- stable enough for intended private/admin analysis;
- unique within governed scope;
- not practically guessable;
- generated using a protected secret/salt or equivalent secure pseudonymization;
- reverse mapping, if any, restricted to authorized internal/admin paths.

---

## 18. Private statistics metrics

Minimum self-reported metrics may include:
- total_rated_signals;
- win_count;
- lose_count;
- missed_count;
- self_reported_win_rate;
- participation_rate;
- missed_rate.

Optional breakdowns:
- symbol;
- session;
- buffer mode;
- TPS band;
- Trade Physics readiness;
- execution-experience reason.

Any metric derived from self-report must be labelled accordingly.

---

## 19. Optional leaderboard

Leaderboards remain optional and self-reported.

Example self-reported accuracy:

`WR_self = wins / (wins + losses)`

Eligibility should require a governed minimum sample size.

Activity and reliability views may exist, but:
- they are informational;
- they must say self-reported;
- they are not strategy performance truth;
- they must not expose protected identity beyond the approved pseudonymous/member presentation.

---

## 20. Anti-gaming controls

Baseline protections:
- one active vote per signal/member;
- voting-window enforcement;
- entitlement verification;
- minimum sample sizes for leaderboards;
- activity/confidence labels;
- anomaly detection for suspicious reporting patterns where implemented;
- no broker-verification claim when broker truth is absent.

Confidence labels reflect sample/reporting confidence, not proof that self-report is objectively correct.

---

## 21. Privacy model

Members must never receive:
- another member's raw identity;
- another member's private history/statistics unless explicitly public and governed;
- raw Telegram/user IDs;
- private admin reconciliation notes;
- protected model/internal diagnostics not entitled to them.

Allowed identity surfaces:
- protected internal storage;
- authorized admin/audit systems;
- private response to the same member;
- approved pseudonymous leaderboard presentation.

---

## 22. Public/private access boundary

Private member statistics are returned only through governed private/authenticated surfaces.

A public/channel request must not expose private stats.

The interface may direct the user to an authorized private surface.

---

## 23. Admin access

Authorized admins may access governed aggregate/full feedback views according to RBAC/privacy policy.

Possible surfaces:
- global aggregate stats;
- member-specific protected review;
- reason summary;
- privacy-safe export;
- mismatch/discrepancy review.

Admin access does not convert self-reported feedback into objective market truth.

---

## 24. Observability

Material feedback operations must be observable.

Event families may include canonical schema-aligned equivalents for:
- member vote received;
- vote updated;
- reason recorded;
- voting window expired;
- feedback aggregated;
- feedback mismatch flagged;
- private stats viewed;
- public stats request blocked;
- admin member-stats view.

Logs must preserve:
- timestamp;
- signal correlation;
- route/tier where relevant;
- schema/app/algo version where applicable;
- actor/reference identity under privacy rules;
- event source/truth class.

Exact event naming must follow `EVENT_SCHEMA_SPEC_v3.0.0.md` and `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`; this document does not create an alternate event schema.

---

## 25. Consensus and mismatch analysis

Community consensus may be calculated from self-reported WIN/LOSE/MISSED values.

It must be labelled `community_consensus` or equivalent.

If consensus differs from:
- objective market telemetry;
- operational/admin reconciliation;

the mismatch may trigger review/analytics.

No consensus result may overwrite another truth layer.

---

## 26. Analytics use

Permitted analytics include:
- self-reported execution success by route/symbol/session;
- missed-rate analysis;
- reason distributions;
- community-vs-market discrepancy;
- community-vs-operational discrepancy;
- TPS/model prediction vs execution-experience difficulty;
- latency/UX friction analysis.

Dashboards must label truth source explicitly.

---

## 27. AI / research safety

Community feedback can support research questions such as:
- which valid signals are frequently missed by humans?
- which expiry bands are misunderstood?
- does strong Trade Physics correlate with lower execution difficulty?
- are publication delays causing member-reported failures?

It MUST NOT:
- be silently substituted for telemetry labels;
- authorize automatic strategy mutation;
- enter pre-trade model features after the fact;
- create user-specific discriminatory strategy quality.

Any model using community targets must state the target explicitly, e.g. `member_execution_success_probability`, not `trade_success_probability` unless the intended calibrated target truly matches the market-truth definition.

---

## 28. Security requirements

Feedback handling must enforce:
- authorization/entitlement;
- anti-replay/dedup;
- protected identity storage;
- audit logging;
- export access controls;
- protection of pseudonymization secrets;
- no public leakage of individual performance data.

Security failures must not silently downgrade privacy guarantees.

---

## 29. Guarantees

If implemented according to this specification:
- users can provide execution-experience feedback safely;
- members can learn from their own private self-reported statistics;
- admin receives useful execution/UX analytics;
- leaderboards remain transparent and non-authoritative;
- privacy remains protected;
- objective market truth, operational truth and community truth remain separate;
- Trade Physics/AI datasets cannot silently use community outcomes as the wrong target.

---

## 30. Migration from v2

Under the executed promotion:
- v2 becomes Superseded;
- the sentence/semantics that Admin Outcome is the single canonical truth for strategy evaluation are retired;
- community data is explicitly classified as self-reported truth;
- admin outcome is explicitly operational/reconciliation truth;
- telemetry remains objective market truth;
- community consensus becomes a review/analytics signal, not an overwrite authority;
- original privacy, vote, reason, membership, dedup and private-statistics protections are preserved.

---

## 31. Version history

| Version | Date | Description |
|---|---|---|
| 3.0.0 | 2026-09-01 | Proposed structural truth-model successor separating community self-report, operational reconciliation and objective market truth; adds Trade Physics/AI label safety. |
| 2.0.0 | 2026-07-12 | Active canonical community feedback/privacy specification. |

---

## 32. Final principle

Community feedback is valuable because it describes human execution experience.

Its value depends on preserving what it actually is.

The system must never improve apparent certainty by collapsing community reports, admin reconciliation and objective market telemetry into one unlabeled truth.