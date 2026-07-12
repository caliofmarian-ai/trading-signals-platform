# OUTCOME_TRACKING_SPEC_v2.0.0

Version: 2.0.0  
Path: /opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md


Status: Active Canonical  
Path target: `/opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md`  
Supersedes: `/opt/binarybot/docs/OUTCOME_TRACKING_SPEC.md`  
Related canonical documents:
- `/opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`

---

## 1. PURPOSE

This document defines the canonical **Outcome Tracking and Reconciliation Layer** for BinaryBot / DROPi Signals.

Its role is to record the operational outcome associated with an executable signal after it has already entered downstream reality.

This specification upgrades the older v1.0.0 document into a v2.0.0 canonical form aligned with the newer architectural truths already fixed in the project:

1. `DecisionObject` is produced before FSM.
2. `Corridor Engine` is before `Time Model`.
3. Decision truth, telemetry truth, and operational/admin truth must remain separate.
4. Telegram button interaction is a surface, not the architecture root.
5. Outcome tracking must no longer be treated as sole ground truth of strategy performance.

This document therefore reframes outcome tracking from a simple admin WIN / LOSE / MISSED button model into a controlled **operational reconciliation layer**.

It still preserves the useful parts of the old design:

- admin-only handling
- stable signal identity
- persistent storage
- analytics value
- explicit handling of `MISSED`

But in v2.0.0, outcome tracking is no longer allowed to overwrite:

- strategy decision truth
- market telemetry truth
- decision audit truth

Instead, it complements them.

---

## 2. CANONICAL POSITION IN THE ARCHITECTURE

Outcome Tracking is **downstream** of:

- decision generation
- decision audit
- FSM lifecycle progression
- executable emission (`OPEN_NOW`)
- trade temporal telemetry collection

Outcome Tracking sits conceptually after the strategy has already:

- evaluated the candidate
- produced a `DecisionObject`
- passed through FSM
- emitted an executable signal
- entered observable post-decision life

High-level canonical chain:

`DecisionObject -> FSM -> OPEN_NOW -> Decision Audit linkage -> Trade Temporal Telemetry -> Outcome Reconciliation -> Performance Analytics -> Research -> Intelligence`

Important consequence:

Outcome Tracking is not the source of why the signal existed.  
Outcome Tracking is not the source of what the market objectively did.  
Outcome Tracking is the source of what the operator/admin side recorded, corrected, or reconciled.

---

## 3. WHY THIS DOCUMENT MUST CHANGE FROM V1.0.0

The older version correctly introduced:

- WIN
- LOSE
- MISSED
- admin-only access
- `SIGNAL_ID` stability
- persistent storage
- observability integration
- analytics integration fileciteturn26file0

However, that older model is no longer sufficient as the project architecture matures.

### 3.1 Main limitation of v1.0.0

In the old model, outcome tracking risks being read as the main “truth layer” for performance because:

- it records final outcome
- it is persistent
- analytics uses it as “ground truth” fileciteturn26file0

That is now too simplistic.

### 3.2 New canonical truth separation

The project now requires at least three separate truth layers:

#### A. Decision truth
Why the signal was produced, promoted, rejected, stalled, or killed.

Primary source:
- `DECISION_AUDIT_SPEC_v2.0.0.md`

#### B. Market truth
What the market objectively did after executable emission.

Primary source:
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

#### C. Operational/admin truth
What the operator/admin execution reality recorded, including missed trades, manual reconciliation, and discrepancy handling.

Primary source:
- this document

### 3.3 Consequence

Outcome Tracking must become a reconciliation and operational reporting layer, not the sole performance truth layer.

---

## 4. CORE PURPOSE OF OUTCOME TRACKING

Outcome Tracking exists to answer questions such as:

- Did the operator/admin actually execute the trade?
- Was the signal missed operationally?
- Was there a broker/platform mismatch?
- Was there a manual correction after review?
- Did admin classify this signal differently from objective telemetry?
- Are there recurring discrepancies between market-truth outcomes and operational outcomes?
- Is poor perceived performance caused by strategy or by execution / workflow issues?

It is therefore essential for:

- execution accountability
- admin workflow auditability
- discrepancy handling
- operational reliability analysis
- support diagnostics
- performance reconciliation

---

## 5. OUTCOME TYPES

Each executable signal may be associated with one operational outcome record.

Baseline canonical outcome classes:

- `WIN`
- `LOSE`
- `MISSED`

### 5.1 Meaning of WIN
The trade was considered operationally successful from the tracked execution perspective.

### 5.2 Meaning of LOSE
The trade was considered operationally unsuccessful from the tracked execution perspective.

### 5.3 Meaning of MISSED
The trade was not executed by the operator or by the intended operational path.

Important canonical rule:

`MISSED` is not equal to a market loss.

It is an operational state.

### 5.4 Optional future extensions

Future versions may extend outcome classes with carefully governed additional values such as:

- `PARTIAL`
- `CANCELLED`
- `DISPUTED`
- `BROKER_REJECTED`
- `MANUAL_OVERRIDE`

But the canonical baseline for v2.0.0 remains:

- `WIN`
- `LOSE`
- `MISSED`

---

## 6. OPERATIONAL SCOPE AND ACCESS CONTROL

### 6.1 Admin-only rule

Outcome setting remains **ADMIN-only** by default, as already correctly established in v1.0.0. fileciteturn26file0

This means:

- subscribers do not set canonical outcomes
- subscriber reactions are not authoritative
- public channels never receive canonical outcome controls

### 6.2 Why admin-only remains correct

Outcome reconciliation is sensitive because it may include:

- manual corrections
- discrepancy handling
- execution realities
- operational failures
- support-side case review

Therefore, canonical outcome authority must remain restricted.

### 6.3 Hard gate

If actor is not authorized by the admin/control hierarchy, the system must reject the outcome change attempt.

This may be implemented through user ID allowlists, control panel roles, or future RBAC extensions.

---

## 7. SIGNAL IDENTITY LINKING (MANDATORY)

The older document already correctly required stable `SIGNAL_ID` linkage across PRE / CONFIRM / OPEN_NOW. fileciteturn26file0

This remains mandatory and is expanded in v2.0.0.

### 7.1 Required identity keys

Every outcome record must be linkable to:

- `signal_id`
- `symbol`
- `direction`
- timeframe
- `open_now_timestamp` or equivalent executable timestamp
- admin message reference if applicable
- telemetry linkage keys if available
- decision audit linkage keys if available

### 7.2 Hard refusal rule

If stable identity is missing, outcome tracking must refuse canonical write.

No anonymous or weakly linked outcome records are allowed in canonical storage.

### 7.3 Correlation requirement

Where possible, the outcome layer should support joinability with:

- decision audit
- telemetry record
- observability event stream
- analytics pipeline

This is essential for discrepancy analysis.

---

## 8. NEW CANONICAL ROLE: OUTCOME RECONCILIATION

### 8.1 Definition

Outcome Reconciliation is the process of recording, updating, and auditing the operator/admin-side outcome associated with an executable signal while preserving separation from objective market truth.

### 8.2 Why “reconciliation” is the correct term

In many cases, the strategy can be correct, but the operator side may still record:

- missed entry
- delayed execution
- platform rejection
- manual override
- execution mismatch

Therefore the layer is not only “outcome tracking”.
It is “outcome reconciliation” between operational reality and the broader truth system.

### 8.3 Canonical non-overwrite rule

Outcome reconciliation must never overwrite:

- the original decision audit record
- the objective telemetry result
- the raw signal identity
- the raw observability trail

It may only add a linked operational interpretation.

---

## 9. UI / UX REQUIREMENTS (ADMIN SURFACE)

The old document required inline admin buttons under the admin version of the OPEN_NOW message:

- ✅ WIN
- ❌ LOSE
- ⏳ MISSED fileciteturn26file0

This remains a valid **surface-level UX option**, but not a canonical architecture dependency.

### 9.1 Canonical rule

Buttons are allowed as UX surfaces.

Buttons are not the architecture root.

### 9.2 Acceptable admin surfaces

Outcome setting may exist through any of the following surfaces:

- inline Telegram admin buttons
- admin panel action sheet
- reconciliation dashboard
- protected admin command
- future mobile/web control plane

### 9.3 Required UX behaviors

When an outcome is set:

- outcome is saved persistently
- the action is logged
- actor identity is preserved
- previous value is preserved if overwritten
- idempotency is respected
- reconciliation status is updated
- related views can refresh safely

### 9.4 Idempotency rule

If the same outcome is submitted twice for the same signal, the system must not duplicate logs or counters.

It may respond with an informational message like:

- “Already set: WIN”
- “Already set: LOSE”
- “Already set: MISSED”

as already suggested in the old document. fileciteturn26file0

---

## 10. DATA STORAGE (PERSISTENT)

The older document stored outcomes in:

`/opt/binarybot/data/outcomes.json` fileciteturn26file0

This path may remain as the canonical baseline storage location unless future normalization moves it under a newer observability or data namespace.

### 10.1 Storage goals

Storage must guarantee:

- persistence across restarts
- deterministic per-signal lookup
- overwrite-safe updates
- actor attribution
- audit-friendly change trace
- compatibility with analytics ingestion

### 10.2 Recommended structure

A structured JSON or JSONL-compatible format is acceptable, but the stored schema must preserve both current state and change metadata.

#### Example baseline structure

```json
{
  "meta": {
    "version": "2.0.0"
  },
  "items": {
    "EURUSD_M1_20260304_001": {
      "signal_id": "EURUSD_M1_20260304_001",
      "symbol": "EUR/USD",
      "direction": "BUY",
      "timeframe": "M1",
      "expiry_seconds": 300,
      "buffer_mode": "MEDIUM",
      "created_at_utc": "2026-03-04T08:20:11Z",

      "outcome": "WIN",
      "reconciliation_status": "RECONCILED",
      "outcome_source": "ADMIN_SET",

      "outcome_set_at_utc": "2026-03-04T08:25:18Z",
      "set_by_user_id": 123456789,

      "previous_outcome": null,
      "previous_outcome_set_at_utc": null,

      "admin_message_id": 1111,
      "admin_chat_id": -1001234567890,

      "decision_audit_id": "da_001992",
      "telemetry_record_id": "tt_004882",
      "correlation_id": "corr_9f2d11"
    }
  }
}
```

---

## 11. REQUIRED FIELDS

### 11.1 Mandatory fields
- `signal_id`
- `outcome`
- `outcome_set_at_utc`
- `set_by_user_id`

These were already mandatory in the old document and remain mandatory. fileciteturn26file0

### 11.2 Strongly recommended fields
- `symbol`
- `direction`
- timeframe
- `expiry_seconds`
- `buffer_mode`
- `admin_message_id`
- `admin_chat_id`
- `decision_audit_id`
- `telemetry_record_id`
- `correlation_id`
- `outcome_source`
- `reconciliation_status`

### 11.3 Optional high-value context
- score snapshot
- TPS snapshot
- corridor state
- time model state
- operator notes
- discrepancy note
- correction reason

---

## 12. RECONCILIATION STATUS MODEL

To support future maturity, outcome records should support a reconciliation lifecycle.

Recommended statuses:

- `PENDING`
- `SET`
- `RECONCILED`
- `DISPUTED`
- `OVERRIDDEN`

### 12.1 Meaning

#### `PENDING`
Signal exists, but no operational/admin outcome yet.

#### `SET`
An outcome has been recorded, but not yet validated against additional context.

#### `RECONCILED`
Outcome has been reviewed and considered consistent with available operational context.

#### `DISPUTED`
There is a mismatch or unresolved issue.

#### `OVERRIDDEN`
A later authorized correction replaced a prior value.

This model is not strictly required for a minimal implementation, but it is strongly recommended for canonical readiness.

---

## 13. OBSERVABILITY AND LOGGING

The older document correctly required an `OUTCOME_SET` observability event. fileciteturn26file0

This remains mandatory.

### 13.1 Required event: `OUTCOME_SET`

Fields should include:

- `timestamp_utc`
- `signal_id`
- `outcome`
- `previous_outcome`
- `user_id`
- `symbol`
- `tier`
- `reconciliation_status`
- `correlation_id`

### 13.2 Recommended additional events

- `OUTCOME_DISPUTED`
- `OUTCOME_OVERRIDDEN`
- `OUTCOME_NOTE_ADDED`
- `OUTCOME_RECONCILED`

### 13.3 Canonical logging rule

Every meaningful outcome mutation must be observable and attributable.

No silent changes are allowed.

---

## 14. ANALYTICS INTEGRATION

The old document stated that performance analytics uses outcomes as ground truth. fileciteturn26file0

That statement must now be refined.

### 14.1 Correct canonical interpretation

Performance analytics may use outcome reconciliation as **operational truth**, but not as the only truth.

Analytics must separately preserve:

- decision truth
- telemetry truth
- reconciliation truth

### 14.2 Default counters
- `wins_count`
- `losses_count`
- `missed_count`

### 14.3 Default win rate
By default:

`WR = wins / (wins + losses)`

`MISSED` excluded by default, as already correctly suggested in the older document. fileciteturn26file0

### 14.4 Optional future modes

Analytics may later compute:

- execution-adjusted WR
- market-truth WR
- reconciliation-adjusted WR
- discrepancy-aware WR

These must be clearly separated and labeled.

### 14.5 Important canonical rule

A dashboard must never silently merge telemetry truth and admin-reconciled truth into one unlabeled metric.

If multiple truth models are shown, they must be explicitly named.

---

## 15. SAFETY RULES

### Rule 1 — Signal must exist
Outcomes can only be set for known executable signals.

### Rule 2 — Stable identity required
If `signal_id` is missing or invalid, canonical write must fail.

### Rule 3 — Duplicate protection
Duplicate outcome writes for the same signal must not create duplicate counters or duplicate persistent entries.

### Rule 4 — Overwrite must be traceable
If an outcome is changed, the previous value must remain reconstructible.

### Rule 5 — Admin-only mutation
Only authorized operators may mutate canonical outcome reconciliation data.

### Rule 6 — No overwrite of telemetry truth
If admin marks `WIN` but telemetry shows expiry `LOSS`, both truths must remain preserved and joinable.

---

## 16. RELATION TO TRADE TEMPORAL TELEMETRY

This is one of the most important v2.0.0 upgrades.

### 16.1 Telemetry vs reconciliation

Telemetry answers:

- what the market objectively did

Outcome Reconciliation answers:

- what the operator/admin side recorded or resolved

### 16.2 No hierarchy confusion

Outcome Reconciliation must not be documented as a replacement for telemetry.

### 16.3 Discrepancy examples

Possible discrepancies:

- market telemetry says `LOSS at expiry`
- admin marks `WIN` because operator exited later manually

or

- telemetry says `WIN`
- admin marks `MISSED` because no operator entry occurred

Both are meaningful.
Neither should erase the other.

---

## 17. RELATION TO DECISION AUDIT

Decision Audit answers:

- why the signal existed
- why it advanced
- why it was not rejected

Outcome Reconciliation answers:

- what happened from operational/admin execution perspective after executable emission

These layers must remain separate.

Outcome Tracking must never be described as if it explains strategy causality.

---

## 18. RELATION TO PERFORMANCE, RESEARCH, AND INTELLIGENCE

### 18.1 Performance Analytics
Uses outcome reconciliation as one input among several truth layers.

### 18.2 Research & Learning
May analyze discrepancy clusters such as:
- high market-truth winrate but high operator missed rate
- recurring manual overrides by symbol/session
- execution friction hidden behind superficially poor operational outcomes

### 18.3 Strategy Intelligence
May surface:
- mismatch dashboards
- outcome reconciliation drift
- operator availability distortions
- support-side workflow problems

### 18.4 AI / Evolution systems
May consume reconciliation patterns, but cannot treat them as direct license for autonomous strategy mutation.

---

## 19. FUTURE UPGRADE PROPOSALS

This spec should support future controlled expansion.

### 19.1 Broker execution linkage
If broker execution data becomes available, it may be linked as a richer operational truth source.

### 19.2 Multi-actor reconciliation
Support for more than one admin note or multi-step case review.

### 19.3 Support notes and explanation bundles
Add structured note fields for why reconciliation differs from telemetry.

### 19.4 Discrepancy dashboards
Show:
- telemetry vs admin outcome mismatches
- missed trade clusters
- operational reliability by symbol/session/time window

### 19.5 Resolution workflow
A richer queue may later classify unresolved cases before they become fully reconciled.

---

## 20. NON-GOALS

This document does not define:

- strategy decision rules
- telemetry market result rules
- Telegram public subscriber UX
- broker-side execution truth engine
- full dashboard design
- community voting models

It only defines the canonical operational/admin outcome reconciliation layer.

---

## 21. SUMMARY

The old v1.0.0 document correctly introduced a useful admin-only WIN / LOSE / MISSED workflow, stable `SIGNAL_ID`, persistence, and analytics value. fileciteturn26file0

In v2.0.0, this concept is preserved but upgraded.

Outcome Tracking is now formally defined as a **reconciliation layer**, not the sole truth of performance.

It preserves operational/admin reality while remaining cleanly separated from:

- strategy decision truth
- telemetry market truth
- downstream analytics interpretation

This makes the architecture more reliable, more explainable, and safer for future optimization and AI-assisted research.

## 18. Community Feedback Outcome Canonicalization

This section integrates bounded canonical truth from the merged Community Feedback and Privacy intake.

### 18.1 Outcome authority
Three canonical outcomes exist for signal result truth. Self-reported feedback is supportive telemetry only and does not override Admin Outcome. Admin outcome remains canonical whenever self-report and admin review differ.

### 18.2 Elite submission boundary
Elite outcome submission requires active ELITE membership. Elite/member-submitted results are operator-visible inputs for analysis and community transparency, but they do not become canonical truth unless accepted through the canonical admin outcome path.

### 18.3 Labeling rule
Any user-facing self-reported outcome surface must be explicitly labeled as self-reported / non-authoritative.
