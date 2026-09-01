# CANONICAL_PROMOTION_RISK_RECLASSIFICATION_ADDENDUM_20260901

Status: SUPPORTING GOVERNANCE / PROMOTION PREFLIGHT — NOT CANONICAL AUTHORITY  
Date: 2026-09-01  
Program: combined Trade Physics + staged-execution canonical promotion

## 1. Purpose

This addendum records a fresh-main semantic preflight finding for `RISK_MODEL_v2.0.0.md`.

Earlier impact planning treated Risk as a possible reference-only PATCH consumer. Full semantic inspection shows that classification is insufficient.

## 2. Conflict found

Active `RISK_MODEL_v2.0.0.md` contains strategy mathematics and primary vocabulary that would conflict with the proposed Trade Physics / Time Model graph, including:

- `buffer_price` as primary risk vocabulary;
- a local formula `t_needed = buffer / (ATR * momentum_factor) * trend_time_adjust`;
- risk-owned timing interpretation that overlaps the unified Time Model;
- classical-score-only framing that does not recognize mandatory current-scope Trade Physics evidence.

These are semantic/structural conflicts, not stale-link-only issues.

## 3. Required classification

`RISK_MODEL_v2.0.0.md` -> `RISK_MODEL_v3.0.0.md`

Classification: **MAJOR — structural risk contract reconciliation**.

A PATCH version is forbidden because it would imply that the change is non-structural while materially changing risk ownership, time authority, vocabulary and Trade Physics evidence requirements.

## 4. Risk v3 ownership

The proposed successor must:

- consume SR/Corridor structural truth;
- consume Time Model time/speed truth instead of defining a parallel time formula;
- consume deterministic Trade Physics readiness/TPS without redefining TPS;
- preserve classical score as distinct from TPS;
- prevent high score/high TPS from overriding hard structural/time/instability/integrity blockers;
- reject fabrication of learned probability or TPS when required evidence is unavailable;
- preserve cooldown/focus/dedup protections under their canonical owners;
- use `buffer_distance` as primary vocabulary.

## 5. Inventory impact

The intended functional authority count remains 43 because Risk v3 replaces Risk v2; it does not add a new domain.

Before active promotion:
- proposed Root Stack must name `RISK_MODEL_v3.0.0.md` as the current intended Risk authority;
- proposed Master Index must list Risk v3 at the existing Risk inventory position;
- `RISK_MODEL_v2.0.0.md` must be included in supersession targets;
- all current normative references to Risk v2 must be classified and repaired where necessary.

## 6. No-code rule

This finding authorizes documentation remediation only.

No runtime risk formula, Trade Physics implementation, Signal Engine code or broker/distribution behavior may be changed until active canonical promotion and post-promotion re-audit complete.

PR #73 remains on canonical hold.

End of addendum.