DEPLOYMENT_PROTOCOL.md

Deployment & Release Governance Protocol — BinaryBot
Version: 2.0.0
Status: Canonical
Linked Documents: ALGO_SPEC.md, FSM_SPEC.md, TELEGRAM_UX.md, PARAMS_REFERENCE.md, RISK_MODEL.md, TEST_PLAN.md, CHECKLIST.md

---

1. PURPOSE

This document defines the official deployment process for BinaryBot.

It ensures:

- No unstable code reaches production
- No undocumented logic changes
- No parameter drift
- No state corruption during restart
- No silent behavioral changes

No deployment is valid without following this protocol.

---

2. DEPLOYMENT PRINCIPLES

The engine must follow these rules:

1. Never deploy partially updated logic.
2. Never deploy without updated documentation.
3. Never deploy without passing TEST_PLAN.
4. Never modify production without backup.
5. Never restart blindly without state validation.

Deployment is a controlled operation, not an experiment.

---

3. DEPLOYMENT TYPES

3.1 PATCH Release (x.x.PATCH)

Definition:

- Minor bug fix
- No logic change
- No scoring change
- No parameter structural change

Required:

- CHANGELOG entry
- Checklist validation
- Basic restart test

---

3.2 MINOR Release (x.MINOR.x)

Definition:

- Parameter tuning
- Threshold adjustment
- Weight adjustment
- Expiry tuning

Required:

- CHANGELOG entry
- PARAMS_REFERENCE update
- Full TEST_PLAN execution
- Version bump in algo_params.json

---

3.3 MAJOR Release (MAJOR.x.x)

Definition:

- Structural logic change
- New scoring model
- FSM modification
- Risk layer modification
- New signal type

Required:

- ALGO_SPEC update
- FSM_SPEC update
- RISK_MODEL review
- TEST_PLAN full execution
- Manual dry-run validation
- Version bump

---

4. PRE-DEPLOYMENT CHECKLIST

Before deployment:

[ ] Backup all modified files
[ ] Backup config/algo_params.json
[ ] Backup focus_state.json
[ ] Backup active_symbols.json
[ ] Confirm TEST_PLAN passed
[ ] Confirm documentation updated
[ ] Confirm version bump

Failure in any → DO NOT DEPLOY.

---

5. FILE BACKUP RULE

Backup naming convention:

filename.py → filename.py.bak_TIMESTAMP

Config backup:

algo_params.json → algo_params_TIMESTAMP.json

Backups must be stored before restart.

---

6. RESTART PROTOCOL

Restart must follow this sequence:

1. Stop service cleanly
2. Confirm no crash loops
3. Verify state files intact
4. Start service
5. Monitor logs for 60 seconds
6. Confirm:
   - No duplicate LIVE
   - No unexpected PRE flood
   - Cooldown persisted
   - Version printed correctly

---

7. POST-DEPLOYMENT MONITORING

First 30 minutes are critical.

Monitor:

- Signal frequency
- Duplicate signals
- State transitions
- Telegram routing
- Spike rejection behavior
- Cooldown enforcement

If abnormal behavior detected:

→ Stop engine
→ Restore backup
→ Audit logs

---

8. EMERGENCY ROLLBACK

Rollback procedure:

1. Stop engine
2. Restore last backup
3. Restore previous algo_params.json
4. Restart engine
5. Verify state integrity

Rollback must not erase cooldown history.

---

9. PRODUCTION SAFETY RULES

The following are forbidden:

- Editing live files without backup
- Restarting without checking logs
- Modifying algo_params.json during live trading
- Testing new scoring logic in production
- Skipping TEST_PLAN

Violation = deployment failure.

---

10. VERSION DISPLAY RULE

On every restart:

Engine must display:

ENGINE STARTED
Algo Version: {algo_version}
Mode: {WIDE/FOCUS}

This confirms version alignment.

---

11. CONFIGURATION LOCK RULE

During production trading:

Only these may be changed:

- buffer mode (via /buffer)
- active symbols (via toggle)

All structural changes require restart.

---

12. STATE FILE INTEGRITY

Before restart confirm:

focus_state.json exists
cooldown timestamps valid
watchlist size ≤ 2

Corrupted state must be repaired before restart.

---

13. DEPLOYMENT FAILURE CONDITIONS

Deployment is considered failed if:

- Duplicate OPEN_NOW detected
- Watchlist overflow
- Signals appear in wrong topic
- Spike filter not functioning
- Cooldown ignored
- Parameter not applied
- Crash loop occurs

Immediate rollback required.

---

14. FINAL DEPLOYMENT CONFIRMATION

Deployment considered successful when:

- TEST_PLAN passed
- No invariant violation
- 30 minutes stable operation
- Signal frequency consistent with expectations
- Risk gates operating correctly
- No unexpected parameter behavior

Only then is release validated.

---

15. GOVERNANCE RULE

No future changes may be implemented without:

1. Documentation update
2. Version bump
3. Checklist validation
4. Test confirmation

This ensures long-term structural integrity.

---

6. TECHNICAL DEPLOYMENT STEPS

Deployment must follow the exact technical sequence below.

Step 1 — Freeze Engine

Activate freeze mode to prevent signal emission during deployment.

Example command:

/freeze

Verify scanning stops.

---

Step 2 — Stop Service

Stop the bot process.

Example:

systemctl stop binarybot

Verify process stopped.

---

Step 3 — Backup Runtime Directory

Backup:

/opt/binarybot/

Destination example:

/opt/binarybot/backups/version_TIMESTAMP/

This allows complete rollback.

---

Step 4 — Deploy Updated Files

Copy updated code files into the runtime directory.

Typical files:

strategy_v2.py  
signal_engine.py  
distribution_router.py  
bot_service.py  
analytics_engine.py  

Documentation updates may also be deployed.

---

Step 5 — Validate Configuration Compatibility

Verify:

- algo_params.json valid
- no missing parameters
- file structure unchanged

Deployment must stop if configuration mismatch occurs.

---

Step 6 — Start Service

Restart bot service.

Example:

systemctl start binarybot

---

Step 7 — Verify Startup Logs

Confirm:

ENGINE STARTED  
version printed  
parameters loaded  
active symbols detected

Any error must halt deployment.

---

Step 8 — Unfreeze Engine

After verification:

/unfreeze

System resumes normal operation.



End of DEPLOYMENT_PROTOCOL.md