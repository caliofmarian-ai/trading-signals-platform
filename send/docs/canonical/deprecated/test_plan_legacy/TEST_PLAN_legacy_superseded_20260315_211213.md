# TEST_PLAN.md
BinaryBot — System Validation, Behavioral Verification & Regression Plan
Version: 3.0.0
Status: Canonical

Linked Documents:
- ALGO_SPEC.md
- FSM_SPEC.md
- SYSTEM_INVARIANTS.md
- RISK_MODEL.md
- TELEGRAM_UX.md
- SIGNAL_DISTRIBUTION_SPEC.md
- CHANNEL_CONFIG_SPEC.md
- OBSERVABILITY_LOGGING_SPEC.md
- EVENT_SCHEMA_SPEC.md
- PERFORMANCE_ANALYTICS_SPEC.md
- FAILURE_RECOVERY_SPEC.md
- MODULE_INTERFACE_SPEC.md
- PARAMS_REFERENCE.md
- ARCHITECTURE_CODE_MAPPING.md
- GOVERNANCE_AND_CHANGE_CONTROL.md
- CHECKLIST.md
- CHANGELOG.md

---

## 0. SCOPE & TESTING CONTRACT

This plan is the single authoritative validation protocol for BinaryBot.

It merges:
- the original “System Validation & Behavioral Verification Plan” (v1.0.0 style)
- the expanded architecture-driven test coverage (distribution, outcomes, observability, analytics)

Non-goals:
- This document does not define trading logic rules (see ALGO_SPEC.md / RISK_MODEL.md).
- This document does not define event schemas (see EVENT_SCHEMA_SPEC.md).
- This document does not define operational deployment steps (see CHECKLIST.md / GOVERNANCE_AND_CHANGE_CONTROL.md).

**Hard rule:**
No production activation unless this test plan is executed and PASSED.

---

## 1. PURPOSE

This document defines the complete testing protocol for BinaryBot.

It ensures:

- deterministic behavior (same inputs → same outputs)
- correct FSM lifecycle transitions
- correct signal lifecycle (PRE → CONFIRM → OPEN_NOW)
- correct deduplication (engine + distribution)
- correct risk gate behavior (SR/spike/feasibility)
- correct distribution per tier (limits/silent/reset)
- correct Telegram UX routing + formatting
- correct observability logging (no silent failures)
- correct Elite outcome voting behavior
- correct analytics computation and integrity
- correct restart persistence and failure recovery
- no SYSTEM_INVARIANTS violations

If it is not tested, it is not trusted.

---

## 2. TEST CATEGORIES (MUST PASS ALL)

The system must pass the following categories:

1) Structural & Boot Tests  
2) State Persistence / Restart Tests  
3) Strategy Logic & Gate Tests  
4) FSM Lifecycle & Invariants Tests  
5) Telegram UX & Routing Tests  
6) Distribution (FREE/BASIC/PRO/ELITE) Tests  
7) Elite Outcome System Tests  
8) Observability & Audit Trail Tests  
9) Analytics & Research Validation Tests  
10) Stress & Load Tests  
11) Replay / Regression Tests  
12) Failure Recovery Tests (Crash, API faults, partial writes)

---

## 3. TEST ENVIRONMENTS

### 3.1 Environments

- DEV: local/sandbox environment
- STAGING: production-like, but not public channels
- PROD: live operation

Rule:
- All tests must pass in DEV or STAGING before PROD.

### 3.2 Test Channels

Create separate Telegram test channels (or topics) mirroring:
FREE_TEST, BASIC_TEST, PRO_TEST, ELITE_TEST

Rule:
- Never run destructive tests in real paid channels.

### 3.3 Test Data

Use one of:
- recorded candles (preferred for determinism)
- simulated candles (for spike/SR/feasibility edge cases)
- live feed (only for smoke tests)

---

## 4. STRUCTURAL & BOOT TESTS

### 4.1 Config Integrity Test (PARAMS)

Target: `config/algo_params.json`

Steps:
1. Start engine with valid config.
2. Verify loader prints/logs:
   - version
   - checksum/hash
   - successful load
3. Verify validation rejects:
   - missing keys
   - wrong types
   - unknown keys

Expected:
- Engine starts only with valid config.
- Invalid config causes:
  - ERROR log event
  - SYSTEM_ALERT Telegram message (admin topic)
  - engine halts safely (no scanning)

Failure:
- Engine starts with invalid params.
- Hardcoded constants override params.

---

### 4.2 Channel Config Integrity Test (DISTRIBUTION)

Target: `config/channel_config.json` or env vars

Steps:
1. Start distribution router with all channel IDs present.
2. Remove one tier channel ID (e.g., FREE) and restart.

Expected:
- Missing ID triggers:
  - critical admin proof log
  - tier treated as DISABLED
  - no publish attempts to that tier
- Other tiers continue.

Failure:
- Router tries to publish to missing tier.
- Counters increment for disabled tier.

---

### 4.3 File System Integrity Test (STATE & LOG DIRS)

Targets:
- `settings.json`
- `active_symbols.json`
- `focus_state.json`
- `dist_state.json`
- `observability/*.jsonl`
- `outcomes/outcomes.jsonl`

Steps:
1. Verify required directories exist (create if missing).
2. Verify permissions allow read/write.
3. Force read-only on one file (simulate permission error).

Expected:
- Permission error triggers:
  - ERROR log
  - SYSTEM_ALERT
  - engine freeze (no trading output)

Failure:
- Silent failure or partial operation without persistence.

---

### 4.4 Startup Validation Log Test

On startup, system MUST log:

- version
- parameter checksum
- active_symbols count
- watchlist size
- cooldown active count
- tier counters + tier states
- last reset timestamp in Europe/London

Expected:
- Events present in observability logs and admin proof topic.

Failure:
- Missing startup state summary.

---

## 5. STATE PERSISTENCE / RESTART TESTS

### 5.1 Restart During WATCHLIST

Steps:
1. Generate PRE for symbol A.
2. Confirm symbol A is in WATCHLIST.
3. Restart engine immediately.

Expected:
- WATCHLIST preserved
- No duplicate PRE for same candle after restart
- Engine resumes correctly

Failure:
- WATCHLIST lost
- PRE duplicates

---

### 5.2 Restart During LIVE_SENT (after OPEN_NOW)

Steps:
1. Generate PRE → CONFIRM → OPEN_NOW for symbol A.
2. Confirm LIVE_SENT state.
3. Restart engine immediately.

Expected:
- LIVE_SENT preserved
- No re-send of OPEN_NOW for same candle/SIGNAL_ID
- Dedup store preserved enough to avoid replay spam

Failure:
- OPEN_NOW re-sent after restart

---

### 5.3 Restart During COOLDOWN

Steps:
1. Trigger /open for symbol A (cooldown set).
2. Restart engine.

Expected:
- Cooldown preserved (absolute block)
- No PRE/CONFIRM/OPEN_NOW for A until cooldown expires

Failure:
- Cooldown lost or bypassed

---

### 5.4 Restart With Tier Counters Near Limit

Steps:
1. In FREE tier, publish 5 OPEN_NOW successfully (limit 6).
2. Restart engine.
3. Publish next OPEN_NOW.

Expected:
- Counter preserved (still 5)
- Next OPEN_NOW increments to 6 then tier becomes SILENT
- No further stages delivered to FREE that day

Failure:
- Counter resets on restart

---

## 6. STRATEGY LOGIC & GATE TESTS

These tests validate gates defined by RISK_MODEL.md.

### 6.1 Spike Rejection Test

Input:
- candle with extreme range, abnormal wick/body ratios, ATR acceleration

Steps:
1. Feed candle sequence to strategy decision.
2. Evaluate decision.

Expected:
- Decision = REJECT
- Reason includes spike gate trigger
- No PRE/CONFIRM/OPEN_NOW emitted

Failure:
- Signal emitted during spike

---

### 6.2 SR Compression Test

Input:
- price too close to support/resistance (available space < sr_required_multiplier × buffer)

Expected:
- Decision = REJECT
- sr_ok = False logged
- No signal emitted

Failure:
- PRE/OPEN emitted inside compression

---

### 6.3 Feasibility Failure Test

Input:
- low ATR, large buffer requirement, expiry too short for movement

Expected:
- Decision = REJECT
- feasibility_ok = False logged
- No signal emitted

Failure:
- PRE/OPEN emitted when move cannot complete

---

### 6.4 Trend Risk Adjustment Test (With Trend)

Input:
- EMA alignment + strong trend conditions

Expected:
- higher trend score
- smaller buffer adjustment
- shorter expiry

Failure:
- expiry/buffer not adjusted

---

### 6.5 Trend Risk Adjustment Test (Flat)

Input:
- flat regime

Expected:
- moderate buffer
- slightly longer expiry

---

### 6.6 Trend Risk Adjustment Test (Counter-trend)

Expected:
- larger buffer
- longer expiry
- lower score bias

---

### 6.7 Score Threshold Hierarchy Test

Expected:
- PRE threshold ≤ CONFIRM threshold ≤ OPEN threshold
- OPEN never lower than PRE

Failure:
- threshold inversion

---

### 6.8 Determinism Test (Strategy)

Steps:
1. Feed identical candles + params + state twice.
2. Compare Decision objects.

Expected:
- identical outputs (bitwise stable fields where applicable)

Failure:
- any difference without input change

---

## 7. FSM LIFECYCLE & INVARIANTS TESTS

### 7.1 IDLE → WATCHLIST on PRE

Condition:
- PRE decision

Expected:
- state transition logged
- watchlist count increments
- PRE message emitted once

---

### 7.2 WATCHLIST → CONFIRM (if used explicitly)

Condition:
- CONFIRM decision (after PRE)

Expected:
- CONFIRM message emitted
- state remains WATCHLIST (or relevant spec state)
- dedup enforced

---

### 7.3 WATCHLIST → LIVE_SENT on OPEN_NOW

Expected:
- OPEN_NOW emitted once
- state → LIVE_SENT
- SIGNAL_ID stable across PRE/CONFIRM/OPEN_NOW

Failure:
- OPEN_NOW without PRE path (INV-21 breach)

---

### 7.4 LIVE_SENT → COOLDOWN on /open

Expected:
- transition logged
- cooldown start stored
- symbol removed from watchlist/live

---

### 7.5 COOLDOWN Absolute Block (INV-13)

Expected:
- any signal attempt blocked
- warning/anomaly event logged if attempted

---

### 7.6 Max Watchlist Size ≤ 2 (INV-10)

Steps:
1. Generate PRE for A and B (watchlist full).
2. Generate PRE for C.

Expected:
- C is ignored/rejected due to watchlist full
- watchlist remains size 2
- warning log optional but recommended

Failure:
- watchlist becomes 3

---

### 7.7 One OPEN_NOW per Candle (INV-11)

Steps:
- Force OPEN condition twice same candle timestamp.

Expected:
- only first publish allowed
- dedup log event present

---

### 7.8 No LIVE in WIDE_SCAN (INV-12)

Steps:
- Force engine into WIDE_SCAN mode
- attempt to meet OPEN threshold

Expected:
- OPEN_NOW blocked
- warning event

---

## 8. TELEGRAM UX & ROUTING TESTS

### 8.1 Message Formatting Tests

Verify PRE/CONFIRM/OPEN_NOW contain required fields:

- stage label
- symbol
- direction
- buffer/buffer_mode
- expiry
- confidence score
- SIGNAL_ID

Failure:
- missing SIGNAL_ID or missing expiry/buffer

---

### 8.2 Topic Routing Tests

Expected routing:

- PRE/CONFIRM/OPEN_NOW → Signals topic (per channel)
- debug breakdown → BUFFER_LOGS topic (admin)
- system errors → SYSTEM_ALERTS topic (admin)
- admin changes → proof topic (admin)

Failure:
- signal posted in system alerts
- debug posted in public channels

---

### 8.3 Command Validation Tests

Test:
- /buffer SMALL|MEDIUM|LARGE

Expected:
- settings updated
- admin proof log emitted (before/after)
- affects future signals only

Test:
- /open SYMBOL invalid

Expected:
- no state change
- warning logged

---

### 8.4 Symbol Selection UI Tests

Steps:
1. Open “Set Symbols”
2. Toggle several symbols
3. Save and exit

Expected:
- active_symbols.json updated atomically
- admin proof log emitted
- WIDE_SCAN uses updated list

Failure:
- list not persisted or partially written

---

## 9. DISTRIBUTION (TIERS) TESTS

### 9.1 Stage Delivery While ACTIVE

For each tier ACTIVE:
- PRE delivered
- CONFIRM delivered
- OPEN_NOW delivered

---

### 9.2 OPEN_NOW Counting Rule

Steps:
1. Deliver PRE and CONFIRM.
2. Verify counter unchanged.
3. Deliver OPEN_NOW successfully.
4. Verify counter increments.

Expected:
- only successful OPEN_NOW increments counter.

Failure:
- PRE/CONFIRM increments counters.

---

### 9.3 Silent Mode Full Block

Steps:
1. Reach tier limit (e.g., FREE 6 successful OPEN_NOW).
2. Attempt next PRE/CONFIRM/OPEN_NOW.

Expected:
- tier blocks ALL stages (silent)
- other tiers continue
- ELITE always continues

Failure:
- PRE/CONFIRM still delivered to silent tier.

---

### 9.4 Publish Failure Does Not Increment

Simulate Telegram publish failure.

Expected:
- counter does NOT increment
- tier remains correct state
- error logged

---

### 9.5 Daily Reset 08:10 Europe/London (DST Safe)

Steps:
1. Set counters to non-zero
2. Wait for reset or simulate time
3. Verify:
   - counters reset to 0
   - tier_state ACTIVE
   - reset event logged once
   - idempotent if called twice

Failure:
- double reset corrupts state

---

### 9.6 Dedup per (tier, SIGNAL_ID, stage)

Steps:
- attempt to re-publish same (tier, SIGNAL_ID, stage)

Expected:
- second publish blocked
- dedup event logged

---

## 10. ELITE OUTCOME SYSTEM TESTS

These tests validate the WIN/LOSE/MISSED reporting workflow.

### 10.1 Buttons Linked to OPEN_NOW SIGNAL_ID

Expected:
- outcome UI references exact SIGNAL_ID of OPEN_NOW.

Failure:
- mismatch breaks analytics and integrity.

---

### 10.2 Activation Timing (After Expiry)

Rule:
- buttons become active only AFTER expiry end.

Test:
1. Send OPEN_NOW with expiry=15m.
2. Before 15m: attempt vote.

Expected:
- vote rejected (too early)
- user informed (optional)
- event logged as blocked_early

After expiry:
- vote accepted.

---

### 10.3 Vote Window

Rule:
- voting open for 5 minutes after expiry end.

Test:
- vote at expiry+2m (accepted)
- vote at expiry+6m (rejected)

Expected:
- correct accept/reject behavior.

---

### 10.4 Single Outcome per User per Signal (LOCK)

Rule:
- first vote wins
- subsequent presses ignored
- no extra “vote changed” noise in logs

Test:
1. User votes WIN.
2. Same user presses LOSE.

Expected:
- LOSE ignored
- only one user_outcome event stored.

---

### 10.5 Buttons Disappear After Vote

Expected:
- after user vote, UI removes buttons for that user context (implementation dependent)
- at minimum: further presses have no effect and UI indicates vote recorded
- after window closes: markup removed for everyone

---

### 10.6 Public Aggregated Stats Per Signal

Expected:
- message shows:
  WIN count + %
  LOSE count + %
  MISSED count + %
  TOTAL votes
- no user IDs exposed publicly

---

### 10.7 Outcome Storage Integrity

Expected:
- outcomes/outcomes.jsonl append-only
- records include:
  timestamp
  signal_id
  user_id (internal only)
  outcome
  expiry
  symbol
- dedup prevents multiple entries per user/signal

---

## 11. OBSERVABILITY & AUDIT TRAIL TESTS

### 11.1 Every Signal Has Logs (INV-40)

For each PRE/CONFIRM/OPEN_NOW:

Must exist:
- decision event log
- fsm_transition log
- tier_publish_result log (for each tier attempted)

Failure:
- Telegram message without log entry
- log entry without Telegram message for successful publish

---

### 11.2 Error Never Silent (INV-41)

Simulate:
- API timeout
- JSON parse error
- Telegram publish error

Expected:
- ERROR log event includes stack/trace summary
- SYSTEM_ALERT message in admin topic

---

### 11.3 Admin Proof Logs

Test:
- change buffer mode
- change active symbols
- tier becomes silent
- reset executed

Expected:
- each produces an admin proof event with before/after and actor (admin user id)

---

### 11.4 Crash Loop Detection

Simulate:
- restart engine >3 times in 60 seconds

Expected:
- CRITICAL event
- optional freeze

---

## 12. ANALYTICS & RESEARCH VALIDATION TESTS

### 12.1 Funnel Reconstruction by SIGNAL_ID

Expected:
- analytics reconstructs:
  PRE → CONFIRM → OPEN_NOW per SIGNAL_ID
- conversion rates correct.

---

### 12.2 Symbol Ranking Correctness

Expected:
- symbol ranking matches OPEN_NOW counts
- includes conversion and rejection rates

---

### 12.3 Focus Efficiency

Expected:
- Focus efficiency = OPEN_NOW / FOCUS_ENTER
- computed over configurable window

---

### 12.4 User Stats (Elite Private)

Expected:
- each user can see only own stats via DM
- admin sees global totals and per-signal aggregates
- no user can query another user

---

### 12.5 Drift Detection Alerts

Simulate:
- WR drops below threshold for last 100 outcomes
- rejection rate spikes

Expected:
- drift event logged
- admin alert emitted

---

## 13. STRESS & LOAD TESTS

### 13.1 High Volatility Stress

Expected:
- spike filter blocks majority
- no message storm
- CPU stable
- no crash

---

### 13.2 Low Volatility Compression

Expected:
- fewer signals
- feasibility rejects common
- no spam

---

### 13.3 Wide Universe Load

Steps:
- select many symbols in active_symbols

Expected:
- engine loop remains stable
- rate-limits handled
- no watchdog overflow

---

### 13.4 Telegram Rate Limit Handling

Simulate:
- Telegram 429 errors

Expected:
- publish failures logged
- counters not incremented
- system continues safely or backs off

---

## 14. REPLAY / REGRESSION TESTS (DETERMINISM)

### 14.1 Offline Replay Determinism

Input:
- recorded candles dataset

Steps:
1. run engine, store emitted events
2. patch code
3. run engine again with same dataset

Expected:
- identical emitted events (or differences explained + version bump)
- any difference requires:
  - changelog entry
  - governance approval
  - regression note

---

### 14.2 Golden File Test (Snapshot)

Maintain “golden” expected outputs for:
- decision events
- fsm transitions
- distribution decisions

Expected:
- exact match.

---

## 15. FAILURE RECOVERY TESTS

### 15.1 Partial Write Recovery (State Files)

Simulate:
- crash during write to focus_state.json or dist_state.json

Expected:
- storage layer atomicity prevents corruption
- system loads last valid state

---

### 15.2 Network Failure Recovery (API Candles)

Simulate:
- candle API failure

Expected:
- system logs error
- continues retrying
- does not emit signals on missing data
- does not crash

---

### 15.3 Telegram Publish Failure Recovery

Simulate:
- Telegram API down

Expected:
- logs show failed publish
- counters not incremented
- system continues evaluating but does not “pretend” delivery succeeded

---

### 15.4 Outcome Service Failure Recovery

Simulate:
- failure writing outcomes.jsonl

Expected:
- vote rejected or queued safely
- error logged
- no silent acceptance

---

## 16. FAILURE CRITERIA (IMMEDIATE HALT)

Immediate halt + freeze required if any occurs:

- Duplicate OPEN_NOW per candle (INV-11 breach)
- WATCHLIST > 2 (INV-10 breach)
- OPEN_NOW in WIDE_SCAN (INV-12 breach)
- Cooldown bypass (INV-13 breach)
- OPEN_NOW without PRE path (INV-21 breach)
- Tier silent leaks signals (distribution breach)
- Telegram/log mismatch (INV-90 breach)
- state corruption detected
- crash loop detected

---

## 17. SUCCESS CRITERIA (PRODUCTION READY)

System is production-ready only if:

- all tests pass
- no invariant violations
- determinism confirmed via replay tests
- distribution tiers enforce limits and silent mode correctly
- observability logs complete and consistent
- outcomes workflow stable and abuse-resistant
- analytics reports align with raw logs

---

## 18. TEST EXECUTION CHECKLIST (OPERATOR)

Before production deployment:

1) Run Structural Tests (Section 4)
2) Run Restart Persistence Tests (Section 5)
3) Run Strategy & Gate Tests (Section 6)
4) Run FSM + Invariants Tests (Section 7)
5) Run Telegram UX Tests (Section 8)
6) Run Distribution Tier Tests (Section 9)
7) Run Outcome Tests (Section 10)
8) Run Observability Tests (Section 11)
9) Run Analytics Tests (Section 12)
10) Run Stress Tests (Section 13)
11) Run Replay/Regression Tests (Section 14)
12) Run Failure Recovery Tests (Section 15)

Only after all PASS:
→ production activation allowed.

---

End of TEST_PLAN.md