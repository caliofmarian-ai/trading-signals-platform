# STATISTICAL_PROOF_LAYER

Status: Legacy Superseded Reference
Superseded By: PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md ; RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md ; STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
Canonical Position: Deprecated; do not use as active truth.

---

# STATISTICAL_PROOF_LAYER — Statistical Proof & Edge Validation
Version: 1.0.0
Status: Canonical
Linked: ALGO_SPEC.md, RISK_MODEL.md, PERFORMANCE_ANALYTICS_SPEC.md, OBSERVABILITY_LOGGING_SPEC.md, SYSTEM_INVARIANTS.md, GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 0. PURPOSE (What this layer is)
This layer proves (or rejects) the existence of statistical edge for the signal engine.

It answers, with math:
- Is the observed win-rate statistically distinguishable from random chance?
- Is the edge stable across symbols, sessions, regimes, and time?
- Is performance a short-lived spike or a repeatable property?
- What is the risk of being fooled by small samples?

This layer does NOT change the trading logic directly.
It governs:
- **Evidence thresholds**
- **Readiness gates**
- **Regression detection**
- **Freeze / downgrade policies**

---

## 1. SCOPE & DATA CONTRACT
### 1.1 What counts as a trial
A **trial** is one executed OPEN_NOW event that the user confirms (manual execution).
Each trial must have:
- symbol
- direction (BUY/SELL)
- expiry_seconds
- timestamp_open_utc
- timestamp_expiry_utc
- entry_price (if available; optional)
- result (WIN/LOSS) [mandatory]
- confidence_score (0–100)
- buffer_mode (SMALL/MEDIUM/LARGE)
- buffer_value (pips or points + percent)
- hard-gates snapshot (sr_ok, spike_ok, feasibility_ok)
- session bucket (ASIA/LONDON/NY/LATE)
- algo_version
- params_hash (hash of algo_params.json)

### 1.2 Data sources
- Telegram confirmations (/open SYMBOL) are used to mark “executed”.
- Result capture must be provided via one of:
  A) manual admin command (/result SYMBOL WIN|LOSS), OR
  B) file import (csv/json), OR
  C) interactive buttons (WIN/LOSS) linked to last OPEN_NOW id.

Statistical Proof Layer assumes the result field is truthful and consistent.

### 1.3 Minimal sample size
No statistical claim is allowed below:
- **N_min_global = 200 trials** (engine-level)
- **N_min_symbol = 50 trials** (per-symbol)
- **N_min_session = 50 trials** (per-session bucket)
- **N_min_mode = 50 trials** (per buffer_mode)

Below these thresholds:
- Only descriptive stats (no “edge confirmed” label)

---

## 2. BASELINES & HYPOTHESES
### 2.1 Null baseline (p0)
Binary outcomes have a baseline win probability p0.

We define p0 as:
- **p0 = 0.50** by default.

If payout/commission is known, a break-even baseline may be used:
- break_even = 1 / (1 + payout_ratio)
But payout is not observable by the bot → default remains 0.50 unless user config overrides it.

### 2.2 Primary hypothesis
We test:
- H0: p <= p0
- H1: p > p0

Where p is the true win probability of the engine under current params.

This is a **one-sided test** (we only care if edge is above baseline).

---

## 3. CORE STATISTICS (Must compute)
### 3.1 Win rate
- N = total trials
- W = wins
- L = losses = N - W
- p_hat = W / N

### 3.2 Confidence Interval (Wilson)
We use Wilson score interval for binomial proportions (robust for small N).

For confidence level (1 - alpha):
- z = NormalQuantile(1 - alpha/2)

Wilson:
- center = (p_hat + z^2/(2N)) / (1 + z^2/N)
- half = z * sqrt( (p_hat(1-p_hat)/N) + (z^2/(4N^2)) ) / (1 + z^2/N)

CI = [center - half, center + half]

We report:
- CI_95 by default (alpha=0.05)
- CI_99 for “hard proof” mode (alpha=0.01)

### 3.3 p-value (Exact binomial)
Compute one-sided binomial test:
- p_value = P(X >= W | N, p0)

Decision rule:
- p_value <= alpha_proof implies “statistically significant”.

Default:
- alpha_proof = 0.05 (soft proof)
- alpha_hard  = 0.01 (hard proof)

### 3.4 Effect size vs baseline
- delta = p_hat - p0

We also compute:
- lower_bound_edge = CI_low - p0

This is the strongest “safe edge” estimate:
- If CI_low > p0, then even the worst plausible p is above baseline.

---

## 4. MULTIPLE TESTING CONTROL (Critical)
We evaluate edge in multiple slices:
- global
- per symbol
- per session
- per buffer_mode
- per direction

This creates multiple hypothesis tests → false positives.

We enforce:
- **Global test uses alpha=0.05**
- Slice tests use correction:
  - Benjamini–Hochberg FDR control at q=0.10 (default)
OR (strict mode):
  - Bonferroni: alpha_slice = alpha / m

Policy:
- Edge is considered “confirmed” for slices only if corrected significance passes.

---

## 5. STABILITY & DRIFT (Not optional)
### 5.1 Rolling windows
Compute stats on rolling windows:
- last 50
- last 100
- last 200
- all-time

We report:
- p_hat and CI for each window.

### 5.2 Drift detector (simple)
Define:
- p_long = win rate on last 200 (or all-time if <200)
- p_short = win rate on last 50

If:
- p_short < p_long - drift_threshold
AND N_short >= 50
then trigger “performance degradation”.

Default:
- drift_threshold = 0.08 (8 percentage points)

This does not “prove” anything; it triggers audit mode.

### 5.3 Regression gate
If the last 100 trials fail:
- CI_low <= p0
AND p_value > 0.10
Then engine is not statistically supported in current conditions → “UNPROVEN”.

---

## 6. READINESS STATES (Outputs)
This layer produces one of these states:

### 6.1 UNPROVEN
Conditions:
- N < N_min_global
OR
- CI_low <= p0
OR
- p_value > alpha_proof

Meaning:
- No statistical proof of edge yet.

### 6.2 PROVISIONALLY_PROVEN
Conditions:
- N >= N_min_global
- p_value <= 0.05
- CI_low > p0 (95% CI)

Meaning:
- Edge likely real, still needs more data.

### 6.3 HARD_PROVEN
Conditions:
- N >= 500
- p_value <= 0.01
- CI_low > p0 (99% CI)

Meaning:
- Strong proof, stable edge (global).

### 6.4 DEGRADED
Conditions:
- Drift detector triggered
OR
- Rolling window (last100) becomes UNPROVEN after previously being PROVEN

Meaning:
- Edge may be regressing; requires audit.

---

## 7. OPERATIONAL POLICIES (What happens)
### 7.1 No auto-trading actions
This layer never executes trades.

### 7.2 Governance actions (allowed)
This layer can:
- notify admin
- label engine state
- recommend parameter audit
- trigger a “freeze recommendation” flag

### 7.3 Freeze recommendation
If DEGRADED persists for:
- 2 consecutive rolling checks (e.g., 2 hours or 2 batches)
then recommend:
- freeze new OPEN_NOW signals
- allow only PRE informational until audit.

(Freeze action must be explicitly enabled in algo_params; default OFF.)

---

## 8. REPORTING (Telegram UX)
We produce:

### 8.1 Daily proof report (admin topic)
Format:
- Global N, W, p_hat
- CI95 and CI99
- p_value vs p0
- current readiness state
- rolling windows summary
- worst slice by corrected test
- best slice by corrected test

### 8.2 On-change alerts
Send alert if readiness state changes:
UNPROVEN → PROVISIONALLY_PROVEN → HARD_PROVEN
or any → DEGRADED

Alert includes:
- what changed
- which window/slice triggered it
- recommended next action

### 8.3 Public transparency (signals topic)
Optional (config):
A short message when engine becomes PROVEN/HARD_PROVEN:
- “Engine has statistically confirmed edge at 95% CI”
No raw p-values in public unless enabled.

---

## 9. STORAGE / ARTIFACTS
All computed results must be stored to survive restarts:
- /opt/binarybot/data/trials.jsonl (append-only)
- /opt/binarybot/data/proof_state.json (latest snapshot)
- /opt/binarybot/data/proof_reports/YYYY-MM-DD.json (daily)

Each record must include:
- algo_version
- params_hash
So you can compare edge across updates.

---

## 10. SYSTEM INVARIANTS (Must never break)
1) No claims of edge below N_min_global.
2) No slice claim without multiple-testing correction.
3) CI method must be Wilson (not naive normal approximation).
4) p-value must be exact binomial (not z-approx) unless explicitly allowed.
5) Proof must be tied to algo_version + params_hash.
6) Any significant change in params resets “proof” to UNPROVEN for the new version until N_min reached.

---

## 11. CONFIG (algo_params.json)
This layer reads:
- statistical_proof.enabled (bool)
- statistical_proof.p0 (float default 0.50)
- statistical_proof.alpha_proof (default 0.05)
- statistical_proof.alpha_hard (default 0.01)
- statistical_proof.n_min_global (default 200)
- statistical_proof.n_hard (default 500)
- statistical_proof.window_short (default 50)
- statistical_proof.window_mid (default 100)
- statistical_proof.window_long (default 200)
- statistical_proof.drift_threshold (default 0.08)
- statistical_proof.multiple_testing.method ("BH_FDR" default)
- statistical_proof.multiple_testing.q (default 0.10)
- statistical_proof.freeze_recommendation.enabled (default false)

---

## 12. AUDIT CHECKLIST (When DEGRADED)
Admin must:
- compare params_hash vs last proven hash
- compare per-symbol slices
- check volatility regime change (ATR distributions)
- check spike filter rejection rates
- check SR gate failure rates
- check if a single symbol dominates sample
- decide: tune params, remove symbols, or wait for regime shift

---

End of STATISTICAL_PROOF_LAYER.md

## Deprecation Note

This document has been superseded after bounded extraction into active canonical documents. It must not be used as parallel canonical truth.
