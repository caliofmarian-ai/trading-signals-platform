# CANON_BATCH_EVALUATION_v2.0.0

## 1. PURPOSE
This document records the canonical evaluation verdict for the newly surfaced satellite and non-active strategy/intelligence documents, in order to decide which of them must be:
- promoted into active canonical truth,
- merged into already-active canonical documents,
- kept outside active canon as satellite/reference material,
- or held as proposed / future-state research specs.

This evaluation is documentation-governance only.  
It does **not** patch code and does **not** itself promote any document.  
It defines the decision basis for the next documentation-alignment step.

---

## 2. EVALUATION METHOD
Each document was evaluated against the following questions:

1. Does it define a distinct canonical concern that is not already sufficiently owned by active docs?
2. Does it duplicate or overlap an already-active canonical cluster?
3. Is it implementation-truth for current production architecture, or future-state / research / AI-extension material?
4. If valuable, is the best destination:
   - direct promotion to active canon,
   - selective merge into active docs,
   - or retention as satellite/supporting material outside active canon?

---

## 3. VERDICT TABLE

| document | verdict | target_active_doc_for_merge_or_alignment | rationale | next_action |
|---|---|---|---|---|
| AI_STRATEGY_AUDITOR_SPEC.md | MERGE_INTO_ACTIVE | RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md ; PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md ; STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md | Valuable for reject analysis, daily audit reporting, bottleneck logic, symbol starvation, and recommendation loops, but these concerns are already part of the active intelligence/research/analytics cluster. Best treated as source material, not root canon. | extract strong sections and merge into active docs; keep original outside active |
| AI_TRADING_INTELLIGENCE_ARCHITECTURE.md | KEEP_OUTSIDE_ACTIVE | STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md (alignment only if needed) | Useful as conceptual architecture for AI/intelligence layer, but substantially overlaps the existing active intelligence cluster and does not need separate active status. | keep as satellite architecture reference; optionally absorb selected framing text |
| INTELLIGENCE_LAYER_ARCHITECTURE.md | KEEP_OUTSIDE_ACTIVE | STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md ; SYSTEM_ARCHITECTURE_MAP_v2.0.0.md (alignment only if needed) | Good layering document, especially for separation of runtime vs intelligence responsibilities, but overlaps with existing active architecture/intelligence docs and should not become separate root truth. | keep outside active; optionally merge a few architectural clarifications |
| INTELLIGENCE_DATA_PIPELINE_DEFINITION.md | MERGE_INTO_ACTIVE | STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md ; MODULE_INTERFACE_SPEC_v2.0.0.md ; OBSERVABILITY_SPEC_v2.0.0.md ; PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md | Strong on pipeline definition, snapshots, aggregation, refresh and admin-facing data paths. Valuable implementation guidance, but better embedded into current active cluster than promoted as a separate canon root. | merge pipeline/snapshot/aggregation truths into active docs; retain original as satellite design doc |
| INTELLIGENCE_FILES_AND_MODULE_MAP.md | MERGE_INTO_ACTIVE | MODULE_INTERFACE_SPEC_v2.0.0.md ; STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md | Highly useful as module-boundary and implementation-target mapping, but this belongs as implementation alignment under active module/interface canon, not as a standalone active document. | absorb ownership/module map into active docs; keep original outside active |
| COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md | PROMOTE_OR_MAJOR_MERGE | OUTCOME_TRACKING_SPEC_v2.0.0.md ; PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md ; TELEGRAM_UX_v2.0.0.md ; governance/security/privacy cluster | Strong candidate because it defines a distinct canonical concern: community feedback handling, privacy boundaries, elite reporting visibility, pseudonymous member references, DM-only stats, and admin/community analytics boundaries. Unlike the other intelligence docs, this has clearer independent domain value. | either promote as active canonical doc or perform a deliberate major merge into outcome/privacy/governance active docs |
| ADAPTIVE_ACTIVITY_GATE_SPEC.md | MERGE_INTO_ACTIVE | ALGO_SPEC_v2.0.0.md ; DECISION_AUDIT_SPEC_v2.0.0.md ; TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md | Important strategic rule refinement replacing fixed activity threshold logic with normalized activity gating. This is strategy-rule truth, not a separate documentation layer. | merge rule, formula, telemetry, and observability requirements into active strategic docs |
| AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md | KEEP_OUTSIDE_ACTIVE | DECISION_AUDIT_SPEC_v2.0.0.md ; PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md (only if some fields are adopted) | Useful conceptual/modeling document for AI and physics-space interpretation, but positioned more as intelligence/research material than current operational truth. | keep as satellite/proposed modeling spec; only extract fields if adopted into current analytics |
| TRADE_PHYSICS_SCORE_SPEC.md | PROPOSED_FUTURE_STATE | none for immediate merge; future relation to strategy scoring / analytics docs | Explicitly future-facing and complementary to current score rather than replacement truth. Suitable for research/proposed state, not active canonical truth now. | move or keep under proposed/future-state research track |
| AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md | PROPOSED_FUTURE_STATE | none for immediate merge; future relation to intelligence/research cluster | Clearly future-state AI self-learning / trade-physics intelligence material intended after strategic stabilization. Not active production-truth canon now. | keep under proposed/future-state research track |

---

## 4. GROUPED DECISION SUMMARY

### 4.1 PROMOTE CANDIDATE
- COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md

### 4.2 MERGE INTO ACTIVE, DO NOT PROMOTE AS SEPARATE ACTIVE DOC
- AI_STRATEGY_AUDITOR_SPEC.md
- INTELLIGENCE_DATA_PIPELINE_DEFINITION.md
- INTELLIGENCE_FILES_AND_MODULE_MAP.md
- ADAPTIVE_ACTIVITY_GATE_SPEC.md

### 4.3 KEEP OUTSIDE ACTIVE AS SATELLITE / REFERENCE
- AI_TRADING_INTELLIGENCE_ARCHITECTURE.md
- INTELLIGENCE_LAYER_ARCHITECTURE.md
- AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md

### 4.4 PROPOSED / FUTURE-STATE, NOT ACTIVE NOW
- TRADE_PHYSICS_SCORE_SPEC.md
- AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md

---

## 5. GOVERNANCE INTERPRETATION

### 5.1 Why most documents should not be promoted
Most documents in this batch are useful, but usefulness alone is not enough for active canonical status.  
A document should become active canon only when it provides:
- a distinct domain of truth,
- a stable production-relevant ownership boundary,
- and a non-duplicative role in the canonical graph.

Most of the intelligence documents here fail that test because their substance is already represented by the active cluster around:
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- OBSERVABILITY / OUTCOME / ADMIN documents

Therefore, promotion would likely increase canonical sprawl rather than improve clarity.

### 5.2 Why COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md is different
This document introduces a more distinct concern boundary:
- privacy of member-level statistics,
- visibility limits,
- pseudonymous references,
- community-facing vs admin-facing feedback surfaces,
- optional leaderboard and elite reporting controls,
- and community outcome communication rules.

That is not merely “more intelligence architecture”; it is a governance/analytics/privacy domain.  
Because of that, it has a legitimate claim either to:
- its own active canonical role,
- or a carefully designed major merge into outcome/privacy/governance active docs.

### 5.3 Why ADAPTIVE_ACTIVITY_GATE_SPEC.md should merge instead of promote
It defines a rule improvement inside strategy behavior.  
That means its truth belongs inside:
- strategy canon,
- decision-audit canon,
- and telemetry canon.

It should shape canonical rule documents, not sit beside them as another top-level active spec.

### 5.4 Why trade-physics AI docs should remain future-state
The trade-physics family appears intentionally future-oriented and AI-facing.  
These docs are valuable, but they are not yet the stable operational truth for the current production strategy stack.  
Promoting them now would blur the line between:
- current executable canon,
- and future research/intelligence evolution.

---

## 6. RECOMMENDED NEXT DOCUMENTATION STEP

Recommended next step:

### STEP_X — SATELLITE_DOC_ALIGNMENT_AND_CLASSIFICATION_PATCH
A documentation-only step that should:
1. decide whether COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md is:
   - promoted into active,
   - or major-merged into existing active docs;
2. merge the selected truths from:
   - AI_STRATEGY_AUDITOR_SPEC.md
   - INTELLIGENCE_DATA_PIPELINE_DEFINITION.md
   - INTELLIGENCE_FILES_AND_MODULE_MAP.md
   - ADAPTIVE_ACTIVITY_GATE_SPEC.md
   into their target active canonical documents;
3. explicitly classify the remaining docs as:
   - satellite reference,
   - proposed,
   - or future-state research;
4. update any active references only if needed after the merge/promotion decisions;
5. avoid introducing unnecessary new active canon roots.

---

## 7. FINAL DECISION STATEMENT

The batch does **not** justify mass promotion into active canon.

The correct governance outcome is:

- **one strong promote-or-major-merge candidate**  
  - COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md

- **four strong merge-into-active candidates**  
  - AI_STRATEGY_AUDITOR_SPEC.md  
  - INTELLIGENCE_DATA_PIPELINE_DEFINITION.md  
  - INTELLIGENCE_FILES_AND_MODULE_MAP.md  
  - ADAPTIVE_ACTIVITY_GATE_SPEC.md

- **three satellite/reference documents to keep outside active**  
  - AI_TRADING_INTELLIGENCE_ARCHITECTURE.md  
  - INTELLIGENCE_LAYER_ARCHITECTURE.md  
  - AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md

- **two future-state / proposed documents not to activate now**  
  - TRADE_PHYSICS_SCORE_SPEC.md  
  - AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md

This preserves canonical discipline, avoids active-doc sprawl, and keeps current production-truth documentation cleaner before further code-affecting work.

---
END OF DOCUMENT