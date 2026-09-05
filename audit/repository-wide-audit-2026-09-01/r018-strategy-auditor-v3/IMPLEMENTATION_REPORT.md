# R-018 Implementation Report

## Root cause

The strategy auditor still treated legacy `event_type = decision` as the only decision input. Current main emits canonical v3 `decision_evaluated` events from `send/core/signal_engine.py`, so valid strategy evaluations could be present while the report displayed zero decisions.

The first R-018 pass fixed the v3 primary path but still had three acceptance gaps:

- an incomplete hardcoded non-decision event allowlist could misclassify valid schema-defined events as unsupported;
- primary reject analytics were silently reinterpreted as all-blocker occurrence analytics;
- branch/issue/CI metadata in the R-018 evidence set did not fully match repository reality.

## Hardened remediation

- Derive recognized event families from `send/schema/event_schema.json` instead of relying on an incomplete hardcoded non-decision set.
- Keep canonical v3 `decision_evaluated` as the only primary decision metric event.
- Retain legacy `decision` support only through an explicit compatibility adapter.
- Deduplicate by canonical `event_id`, with canonical v3 precedence over legacy when both describe the same event id.
- Preserve backward-compatible primary reject analytics through one deterministic primary reason per rejected decision.
- Preserve full canonical blocker/reason multiplicity separately in `reject_reason_occurrences`.
- Align the principal v3 fixture with the actual current producer contract, including strategy implementation version `2.0.0` and canonical spec `ALGO_SPEC_v3.0.0`.
- Correct branch/validation/open-finding evidence to match the actual PR branch and current CI truth.

## Deterministic primary reject rule

For rejected decisions, the primary report reason is selected in this order:

1. first ordered `decision_object.reject.hard_blockers` entry when present;
2. first parsed element of `decision_object.reject.reason`;
3. first parsed element of legacy/direct reject reason fields;
4. first explicit failed gate reason.

This preserves one-primary-reason-per-rejected-decision semantics while still surfacing all blocker occurrences separately.

## Safety boundaries preserved

- No strategy arithmetic changed.
- No PRE/CONFIRM/OPEN thresholds changed.
- No provider policy changed.
- No broker execution behavior changed.
- No live Railway/Telegram acceptance evidence was fabricated.
