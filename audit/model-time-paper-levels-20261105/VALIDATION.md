# Offline validation

Base: `7fe4c1778bad732b3ccf880206322bd604a165c0`.

- Focused paper ledger, live severity and complete Binary Strategy pipeline:
  **41 passed**.
- Complete repository: `python -m pytest -q`: **2,139 passed** in 46.33s.
- `git diff --check`: passed.

The new tests cover BUY/SELL/DRAW, different prospectively locked fractional
model durations, absent execution calibration, PRE/CONFIRM/OPEN with 30-second
PRE lead, hard gates and lineage, a high initial score at permissive levels,
one shared cached quote across all levels, stale/future/historical/cross-provider
quotes, missed endpoints, corrupt evidence, bounded capacity, immutable finalized
outcomes, and settlement after collection closes and after module reload.

These are offline verification results, not live efficacy or live delivery
claims. Exact-head CI, deployment status and new prospective runtime evidence
must be observed separately.
