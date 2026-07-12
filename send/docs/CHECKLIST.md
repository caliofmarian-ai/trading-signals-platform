CHECKLIST.md

BinaryBot — Operational Control Checklist
Version: 2.0.0
Status: Canonical

Linked Documents:
DEPLOYMENT_PROTOCOL.md
TEST_PLAN.md
SYSTEM_INVARIANTS_v2.0.0.md
OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
FAILURE_RECOVERY_SPEC_v2.0.0.md
SECURITY_MODEL.md
PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md

---

1. PURPOSE

This checklist defines the operational verification steps required to safely operate BinaryBot.

It protects against:

- behavioral drift
- configuration corruption
- deployment mistakes
- risk protection failure
- system instability

This checklist must be used during:

- system startup
- system deployment
- parameter modification
- code patching
- daily operational monitoring

Failure to follow this checklist may compromise system integrity.

---

2. PATCH CONTROL CHECKLIST

This section must be followed before and after any patch, parameter change or structural modification.

Failure to follow this checklist risks behavioral drift from ALGO_SPEC.

---

BEFORE PATCH

2.1 Environment Control

[ ] Connected to correct server
[ ] Correct working directory (/opt/binarybot)
[ ] Services status checked
[ ] No emergency instability running

---

2.2 Documentation Alignment

[ ] ALGO_SPEC reviewed
[ ] Intended change mapped to specific section
[ ] Version bump type decided (MAJOR / MINOR / PATCH)
[ ] CHANGELOG entry prepared

---

2.3 Safety Backup

[ ] Backup created for modified files
[ ] config/algo_params.json backed up
[ ] focus_state.json backed up
[ ] active_symbols.json backed up
[ ] dist_state.json backed up

No deployment allowed without backups.

---

DURING PATCH

[ ] Only intended files modified
[ ] No hidden side effects introduced
[ ] No hard gates disabled accidentally
[ ] No scoring weights broken
[ ] No parameter removed accidentally

---

AFTER PATCH

2.4 Structural Validation

[ ] ALGO_SPEC updated (if logic changed)
[ ] CHANGELOG updated
[ ] algo_version bumped in config

---

2.5 Technical Validation

[ ] JSON validated (no syntax error)
[ ] Services restarted cleanly
[ ] No crash in runner logs
[ ] No missing imports
[ ] No circular dependency

---

2.6 Telegram Functional Test

[ ] /start works
[ ] /buffer selection works
[ ] Symbol toggle works
[ ] PRE message formatted correctly
[ ] CONFIRM message formatted correctly
[ ] OPEN_NOW formatted correctly
[ ] BUFFER_LOGS entries contain full context

---

2.7 Behavioral Validation

[ ] No signals for deselected symbols
[ ] Focus max 2 respected
[ ] Cooldown blocks repeated entry
[ ] Spike filter blocks unstable market
[ ] SR gate blocks insufficient space
[ ] Expiry remains within configured limits

---

2.8 Final Confirmation

[ ] Engine behavior matches ALGO_SPEC
[ ] No unexpected signal frequency change
[ ] No scoring distortion observed

Patch considered COMPLETE only after all boxes validated.

---

3. SYSTEM STARTUP CHECKLIST

Before starting BinaryBot engine verify:

[ ] Server reachable
[ ] Internet connectivity stable
[ ] Market data API reachable
[ ] Disk usage < 80%
[ ] Configuration files exist

Required files:

[ ] config/algo_params.json
[ ] active_symbols.json
[ ] focus_state.json
[ ] dist_state.json
[ ] settings.json

If any file missing → STOP STARTUP.

---

4. ENGINE START VALIDATION

After engine start verify logs show:

[ ] ENGINE STARTED
[ ] Algo Version printed
[ ] Mode printed (WIDE / FOCUS)
[ ] Parameters loaded successfully
[ ] Active symbols detected

Confirm:

[ ] No startup errors
[ ] No missing parameter warnings

---

5. SIGNAL ENGINE VALIDATION

After startup observe first signals.

Verify:

[ ] PRE signals appear normally
[ ] CONFIRM signals appear normally
[ ] OPEN_NOW signals appear normally

Critical checks:

[ ] No duplicate PRE
[ ] No duplicate OPEN_NOW
[ ] OPEN_NOW only in FOCUS mode

Violation = stop engine immediately.

---

6. FSM STATE VALIDATION

Verify state transitions.

Confirm:

[ ] IDLE → WATCHLIST occurs correctly
[ ] WATCHLIST → LIVE_SENT occurs correctly
[ ] LIVE_SENT → COOLDOWN occurs correctly

Safety checks:

[ ] WATCHLIST size ≤ 2
[ ] Cooldown enforced

---

7. DISTRIBUTION SYSTEM CHECK

Verify signal routing.

Confirm:

[ ] FREE channel receives signals within limits
[ ] BASIC channel receives signals within limits
[ ] PRO channel receives signals within limits
[ ] ELITE channel receives all signals

Also confirm:

[ ] Silent tiers receive nothing

---

8. OUTCOME SYSTEM CHECK

For ELITE signals verify:

[ ] Outcome buttons appear
[ ] WIN accepted
[ ] LOSE accepted
[ ] MISSED accepted

Rules:

[ ] Only one vote per user
[ ] Votes stored successfully
[ ] Statistics updated correctly

---

9. OBSERVABILITY CHECK

Verify logging integrity.

Logs must exist for:

[ ] engine_start
[ ] signal_event
[ ] fsm_transition
[ ] tier_publish
[ ] user_outcome
[ ] admin_change

Logs must be append-only.

---

10. ANALYTICS CHECK

Verify analytics engine functioning.

Confirm:

[ ] Signal counts correct
[ ] Symbol ranking calculated
[ ] Win rate statistics available
[ ] Focus conversion rate visible

---

11. SECURITY CHECK

Verify system access control.

Confirm:

[ ] Admin panel restricted
[ ] Owner access functioning
[ ] Moderator permissions correct
[ ] Analyst access correct

No unauthorized user must access admin functions.

---

12. DAILY OPERATION CHECK

Daily operator tasks:

[ ] Review system alerts
[ ] Review signal statistics
[ ] Review winrate trends
[ ] Verify API stability
[ ] Verify disk space
[ ] Verify log growth

Daily monitoring helps detect strategy drift early.

---

13. INCIDENT RESPONSE CHECK

If abnormal behavior occurs:

1. Activate freeze mode
2. Stop engine if required
3. Review logs
4. Identify root cause
5. Restore backup if needed

Follow FAILURE_RECOVERY_SPEC_v2.0.0.md.

---

14. CHECKLIST GUARANTEE

If this checklist is followed:

- deployments remain safe
- behavior remains aligned with ALGO_SPEC
- system errors become visible immediately
- operational risk is minimized

Operational discipline ensures BinaryBot remains stable in production.

---

End of CHECKLIST.md