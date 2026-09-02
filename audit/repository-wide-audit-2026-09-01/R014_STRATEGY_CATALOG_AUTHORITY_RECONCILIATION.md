# R-014 — Strategy Catalog / Owner UI Authority Reconciliation

Status: VALIDATED — AWAITING MERGE
Issue: #124
Parent: #97
PR: #125
Base main commit: `f37694b640071af4273134b506dda660345ad991`
Validated implementation head: `741f28d5ea3dcce0da7c4d5fc64866d39f039243`
GitHub-tested merge candidate: `02c8f5fe34a26aa6e1396ac431440411155cfeff`
Validation run: `33658204708` — SUCCESS

## Defect

The live strategy catalog still identified the selected Binary Trading family with `ALGO_SPEC_v2.0.0`, and `render_strategy_choice()` separately hardcoded `Strategy version: 2.0.0`.

The authoritative `CANONICAL_MASTER_INDEX_v2.0.0.md` declares `ALGO_SPEC_v3.0.0` version `3.0.0` as the active canonical trading-algorithm / strategy evaluation, scoring and gating authority. The Master Index explicitly governs status when lower-level promoted files retain stale pre-promotion header wording.

## R-014 decision

- keep `Binary Trading` as the installed strategy-family name;
- do not reinterpret the internal `Binary Strategy V2` implementation label as the canonical specification version;
- change the selected catalog authority to `ALGO_SPEC_v3.0.0`;
- derive the displayed canonical specification version from the versioned canonical specification identifier;
- accept the repository catalog convention with an optional `.md` suffix while requiring an explicit semantic version;
- label the UI value `Canonical specification version` rather than the ambiguous `Strategy version`;
- require every AVAILABLE catalog strategy to reference a versioned canonical specification identifier;
- preserve `Forex Strategy` as `UNAVAILABLE` / `NOT_IMPLEMENTED` and non-selectable.

## Safety boundary

R-014 changes catalog/control-plane authority metadata only. It does not alter strategy mathematics, score thresholds, SR/Corridor, Trade Physics, Time Model, FSM, Signal Engine, provider selection, distribution, market data, broker execution, or future Forex implementation.

Historical, superseded and deprecated references are outside R-014 and remain owned by later documentation/governance cleanup items.

## Regression proof

The repository now proves that:

- selected catalog entry is `ALGO_SPEC_v3.0.0`;
- selected canonical specification version is derived as `3.0.0`;
- Owner Choose Strategy page shows the active authority and unambiguous version label;
- stale `Strategy version: 2.0.0` is absent from the Owner strategy-selection page;
- malformed AVAILABLE canonical implementation metadata fails closed;
- future Forex stays blocked and `NOT_IMPLEMENTED`;
- existing strategy navigation remains intact.

## Validation evidence

Permanent PR validation on the GitHub merge candidate passed:

- provider selector regression: **5 passed**;
- Telegram admin regression: **72 passed**;
- full repository suite: **1061 passed**;
- Python compilation: PASS.

The full repository suite includes the updated strategy-choice tests and the new malformed-authority regression.

A documentation-only evidence commit follows this validated implementation head. The final PR head must receive the permanent PR workflow again before Ready for Review.
