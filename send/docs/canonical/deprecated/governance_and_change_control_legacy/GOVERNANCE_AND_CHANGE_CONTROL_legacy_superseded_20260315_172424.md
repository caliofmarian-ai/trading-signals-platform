GOVERNANCE_AND_CHANGE_CONTROL.md

Governance, Authority Model & Change Control Framework — BinaryBot
Version: 1.0.0
Status: Canonical
Linked Documents: ALGO_SPEC.md, FSM_SPEC.md, PARAMS_REFERENCE.md, RISK_MODEL.md, TEST_PLAN.md, DEPLOYMENT_PROTOCOL.md, PERFORMANCE_ANALYTICS_SPEC.md

---

1. PURPOSE

This document defines:

- Who has authority over the system
- How changes are proposed
- How changes are evaluated
- How changes are approved
- How changes are documented
- How behavioral drift is prevented

Governance ensures the system evolves deliberately, not emotionally.

---

2. CORE GOVERNANCE PRINCIPLES

1. No undocumented change.
2. No untested change.
3. No emotional parameter tuning.
4. No structural edits without version bump.
5. No production experimentation.
6. Documentation precedes implementation.

The system must remain deterministic and auditable.

---

3. AUTHORITY MODEL

3.1 Strategy Owner

Authority over:

- Vision
- Risk tolerance
- Capital philosophy
- Major structural direction

Cannot:

- Modify code directly without process
- Override hard gates impulsively

---

3.2 Technical Authority

Authority over:

- Implementation integrity
- FSM correctness
- Logging compliance
- Observability compliance
- Structural consistency

Cannot:

- Change risk philosophy without approval

---

3.3 Parameter Authority

Authority over:

- Threshold tuning
- Buffer multipliers
- Expiry limits
- Spike filter values

Constraints:

- Must follow performance analytics
- Must document impact
- Must run TEST_PLAN before deploy

---

4. CHANGE CATEGORIES

All changes fall into one of four types:

4.1 Cosmetic Change

Examples:

- Logging formatting
- Message formatting

Requires:

- CHANGELOG entry

---

4.2 Parameter Change

Examples:

- PRE threshold adjustment
- Buffer multiplier change

Requires:

- Performance comparison
- Version bump (MINOR)
- TEST_PLAN run

---

4.3 Structural Logic Change

Examples:

- New scoring model
- FSM modification
- New risk layer

Requires:

- MAJOR version bump
- Documentation update
- Full regression test
- Deployment protocol

---

4.4 Emergency Fix

Examples:

- Duplicate LIVE bug
- Cooldown bypass
- Crash loop

Requires:

- Immediate patch
- Post-fix documentation update
- Incident log entry

---

5. CHANGE PROPOSAL FORMAT

Every change must be written as:

CHANGE_ID: YYYYMMDD-XX
TYPE: PATCH / MINOR / MAJOR
RATIONALE: Why change needed
EXPECTED IMPACT: What will improve
RISK: What could break
ROLLBACK PLAN: How to revert
TEST PLAN: What tests will run

No informal changes allowed.

---

6. VERSIONING RULE

Version must follow:

MAJOR.MINOR.PATCH

Increment rules:

PATCH → Bug fix
MINOR → Parameter tuning
MAJOR → Structural modification

Version must match:

- algo_params.json
- Engine startup display
- CHANGELOG entry

---

7. CHANGE APPROVAL PROCESS

For each proposed change:

Step 1: Written proposal
Step 2: Performance analysis review
Step 3: Risk impact review
Step 4: Documentation update
Step 5: Controlled deployment
Step 6: Monitoring window

Only after monitoring window success → change validated.

---

8. FORBIDDEN ACTIONS

The following are strictly prohibited:

- Editing code directly in production without backup
- Removing SR gate
- Removing spike filter
- Removing cooldown logic
- Lowering OPEN threshold impulsively
- Testing ideas live

Violation = governance failure.

---

9. INCIDENT MANAGEMENT

If abnormal behavior occurs:

Example incidents:

- Win rate collapse
- Signal flood
- Duplicate LIVE
- Missed OPEN
- State corruption

Procedure:

1. Freeze engine
2. Preserve logs
3. Identify root cause
4. Document incident
5. Fix in controlled patch
6. Update documentation

No silent corrections allowed.

---

10. DRIFT CONTROL POLICY

Drift is defined as:

Engine behavior diverging from ALGO_SPEC.

Drift detection triggers:

- Unexpected signal frequency
- Score distribution change
- Performance degradation
- Gate rejection anomaly

Upon drift detection:

→ Freeze parameter changes
→ Audit recent commits
→ Compare behavior to canonical specs

---

11. CHANGE LIMITATION RULE

Only one structural change per deployment cycle.

Never combine:

- New scoring logic
- Threshold adjustment
- Expiry modification

Multiple simultaneous changes obscure impact analysis.

---

12. DOCUMENT SYNCHRONIZATION RULE

If code changes:

Must update:

- ALGO_SPEC
- PARAMS_REFERENCE
- RISK_MODEL (if relevant)
- TEST_PLAN
- CHANGELOG

Code must never be ahead of documentation.

---

13. PERFORMANCE VALIDATION WINDOW

After any change:

Minimum monitoring window:

- 50 trades (minor change)
- 200 trades (major change)

No conclusions before window complete.

---

14. STRATEGIC FREEZE MODE

When activated:

- No parameter changes
- No logic changes
- Only bug fixes allowed

Used during:

- Performance instability
- High drawdown
- Market anomaly

---

15. LONG-TERM EVOLUTION MODEL

Strategy evolution must follow:

Stability → Measurement → Adjustment → Validation → Stabilization

Never:

Instability → Panic → Over-adjustment → Collapse

---

16. GOVERNANCE GUARANTEE

If this governance framework is respected:

- No chaotic tuning
- No emotional edits
- No undocumented drift
- No silent structural damage
- Predictable evolution
- Institutional-grade discipline

Governance transforms the bot from a tool into a controlled system.

---

End of GOVERNANCE_AND_CHANGE_CONTROL.md