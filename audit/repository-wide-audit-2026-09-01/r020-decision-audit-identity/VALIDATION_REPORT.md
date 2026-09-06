# R-020 — Decision Audit Identity Validation Report

Status: FINAL VALIDATION PENDING EXACT-HEAD CI
Issue: #146
PR: #147
Branch: `remediation/audit-2026-09-01-r020-decision-audit-identity`
Base main: `4bfb770ee8a380ce49d03fd46e9617c515227128`

## Scope validated

R-020 materializes and propagates audit identity without changing trading behavior.

Validated implementation surfaces:

- `send/core/decision_object.py`
- `send/core/v2_fsm_orchestrator.py`
- `send/core/signal_execution_gate.py`
- `send/core/signal_event.py`
- objective Trade Temporal Telemetry consumption of the production SignalEvent lineage
- canonical DecisionObject contract regression
- Signal Execution Gate identity mismatch regression
- remediation authority documentation and master-plan state

## Identity invariants

The tests and code review validate these boundaries:

1. `setup_correlation_id` remains the setup/cycle correlation identity.
2. `decision_id` and `decision_audit_id` are materialized before FSM from the exact semantic DecisionObject truth.
3. Exact semantic retry/replay yields the same decision identities.
4. Changed pre-FSM truth during another two-second evaluation on the same setup/candle yields a different decision identity.
5. FSM never recalculates the DecisionObject identity; it propagates it and materializes its own bounded `fsm_transition_id` from the upstream decision identity plus actual FSM result semantics.
6. Signal Execution Gate refuses a DecisionObject/FSM identity mismatch fail-closed.
7. The existing `execution_attempt_id` remains Execution Gate-owned and is propagated into SignalEvent rather than regenerated there.
8. SignalEvent preserves setup, decision, decision-audit, FSM-transition and execution-attempt identity.
9. Objective OPEN_NOW Trade Temporal Telemetry receives the materialized lineage plus Distribution-owned publication evidence and reaches `linkage_state=COMPLETE` in regression coverage.
10. Legacy or genuinely unlinked evidence remains explicit; R-020 does not fabricate missing identity.

## Safety review

Confirmed by code review and regression scope:

- no score threshold changes;
- no SR/corridor rule changes;
- no Model Time or Execution Time formula changes;
- no provider-selection changes;
- no Finnhub/Twelve Data mixing;
- no change to the governed two-second evaluation cadence;
- no distribution entitlement changes;
- no Telegram role/permission changes;
- no broker execution enablement;
- identifiers are hashes/opaque references and contain no secret values.

## CI history during implementation

### Expected contract-regression discovery

An early full-suite run exposed one old DecisionObject test that required the exact pre-R-020 key set. The production implementation was not weakened; the canonical contract regression was updated to require `decision_id` and `decision_audit_id`.

A later full-suite run exposed a test that changed DecisionObject truth after FSM acceptance and reused the old FSM result. R-020 correctly rejected this as an identity mismatch. Coverage was split so both behaviors are now explicit:

- changed truth + prior FSM result => fail-closed identity mismatch;
- incomplete truth + matching FSM result => SignalEvent remains unavailable / not emitted.

### Successful implementation validation

GitHub Actions run `34019608862` completed successfully on implementation/documentation head `5f7731747d45235b60833f1604ca7b88fbaea8bf`:

- provider selector: **5 passed**;
- Telegram Admin restoration: **72 passed**;
- full repository suite: **1207 passed**.

The remediation master plan was then reconciled on commit `1512fe17feabdb87615a49e9181b8b0682bc39a3` to close R-019 factually and mark R-020 in progress.

This validation report is the final repository-content change planned before exact-head CI. The PR must not be marked Ready for Review until GitHub Actions succeeds on the commit containing this report.

## Final acceptance gate

Before Ready for Review:

- exact final branch head must be recorded;
- provider selector must pass;
- Telegram Admin regression must pass;
- full repository suite must pass;
- PR diff must be re-reviewed against main;
- no unrelated runtime or canonical changes may be present.

After a successful exact-head run, PR/Issue metadata may be updated with the evidence because metadata updates do not alter the tested commit.
