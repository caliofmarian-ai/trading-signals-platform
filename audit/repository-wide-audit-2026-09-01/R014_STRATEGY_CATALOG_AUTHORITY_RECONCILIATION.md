# R-014 — Strategy Catalog / Owner UI Authority Reconciliation

Status: IMPLEMENTED ON REMEDIATION BRANCH — VALIDATION PENDING
Issue: #124
Parent: #97
Base main commit: `f37694b640071af4273134b506dda660345ad991`

## Defect

The live strategy catalog still identified the selected Binary Trading family with `ALGO_SPEC_v2.0.0`, and `render_strategy_choice()` separately hardcoded `Strategy version: 2.0.0`.

The authoritative `CANONICAL_MASTER_INDEX_v2.0.0.md` declares `ALGO_SPEC_v3.0.0` version `3.0.0` as the active canonical trading-algorithm / strategy evaluation, scoring and gating authority. The Master Index explicitly governs status when lower-level promoted files retain stale pre-promotion header wording.

## R-014 decision

- keep `Binary Trading` as the installed strategy-family name;
- do not reinterpret the internal `Binary Strategy V2` implementation label as the canonical specification version;
- change the selected catalog authority to `ALGO_SPEC_v3.0.0`;
- derive the displayed canonical specification version from the versioned canonical specification filename;
- label the UI value `Canonical specification version` rather than the ambiguous `Strategy version`;
- require every AVAILABLE catalog strategy to reference a versioned canonical specification filename;
- preserve `Forex Strategy` as `UNAVAILABLE` / `NOT_IMPLEMENTED` and non-selectable.

## Safety boundary

R-014 changes catalog/control-plane authority metadata only. It does not alter strategy mathematics, score thresholds, SR/Corridor, Trade Physics, Time Model, FSM, Signal Engine, provider selection, distribution, market data, broker execution, or future Forex implementation.

Historical, superseded and deprecated references are outside R-014 and remain owned by later documentation/governance cleanup items.

## Validation targets

- selected catalog entry is `ALGO_SPEC_v3.0.0`;
- selected canonical specification version is derived as `3.0.0`;
- Owner Choose Strategy page shows the active authority and unambiguous version label;
- stale `Strategy version: 2.0.0` is absent from the Owner strategy-selection page;
- malformed AVAILABLE canonical implementation metadata fails closed;
- future Forex stays blocked;
- strategy navigation, Owner Knowledge, Telegram admin and full repository regressions pass before Ready for Review.
