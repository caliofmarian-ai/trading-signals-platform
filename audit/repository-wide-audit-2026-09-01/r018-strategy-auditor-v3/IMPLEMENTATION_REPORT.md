# R-018 Implementation Report

## Root cause

The strategy auditor still treated legacy `event_type = decision` as the only decision input. Current main emits canonical v3 `decision_evaluated` events from `send/core/signal_engine.py`, so valid strategy evaluations could be present while the report displayed zero decisions.

## Implemented remediation

- Added an explicit normalization boundary in `send/tools/strategy_auditor_lib.py`.
- Made canonical v3 `decision_evaluated` the primary path.
- Retained legacy `decision` support only through an explicit compatibility adapter.
- Deduplicated by canonical `event_id`, with canonical v3 precedence over legacy when both describe the same event id.
- Preserved existing report keys while adding transparent `event_compatibility` provenance metadata.
- Added explicit handling for `NO_SIGNAL`, unsupported schemas, unknown event families, malformed records, conflicting field evidence, and missing optional fields.
- Extended markdown report output so compatibility/provenance state is visible to operators.

## Files changed

- `send/tools/strategy_auditor_lib.py`
- `tests/canonical/unit/test_r018_strategy_auditor_v3_compatibility.py`
- `audit/repository-wide-audit-2026-09-01/REMEDIATION_MASTER_PLAN.md`
- `audit/repository-wide-audit-2026-09-01/r018-strategy-auditor-v3/*`

## Safety boundaries preserved

- No strategy arithmetic changed.
- No thresholds changed.
- No provider policy changed.
- No broker execution behavior changed.
- No live acceptance or Railway evidence was fabricated.
