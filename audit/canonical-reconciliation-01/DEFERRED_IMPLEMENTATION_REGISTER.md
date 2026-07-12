# DEFERRED_IMPLEMENTATION_REGISTER.md

**Governance Record:** canonical-reconciliation-01  
**Date:** 2026-07-12  
**Source Audit:** canonical-audit-01  
**Owner Decision:** OWNER-004 = A1 + B2 (Approved; Deferred to dedicated code-remediation task)  

---

## Summary

This document is the authoritative governance record for OWNER-004. The owner has approved the implementation decisions recorded below. However, per the task scope of `canonical-reconciliation-01`, implementation is explicitly deferred to a dedicated code-remediation task.

**No application code was modified in `canonical-reconciliation-01`.**

---

## Deferred Implementation Item 1: trade_temporal_telemetry Module

**Status:** APPROVED — DEFERRED  
**Risk Level:** CRITICAL  
**Conflict Reference:** CON-003 (canonical-audit-01)  
**Gap Reference:** GAP-001 (canonical-audit-01)  

### Problem

`send/core/signal_engine.py` unconditionally imports and calls `trade_temporal_telemetry.register_open_now_trade()`.

The module `send/core/trade_temporal_telemetry.py` does not exist.

This causes a runtime `ImportError` when the open-trade registration code path executes.

### Approved Implementation Decision

**A1:** Implement `send/core/trade_temporal_telemetry.py` according to `send/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`.

### Governing Specification

`send/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` — Active Canonical. This specification is authoritative. The implementation must conform to it without deviation. Any implementation deviation must first be addressed by updating the canonical specification through the governance process.

### Deferred To

A dedicated code-remediation task.

### Risk Status

**CRITICAL runtime risk remains OPEN.**

Until `trade_temporal_telemetry.py` is implemented and tested, the open-trade registration code path in `signal_engine.py` will fail with an ImportError at runtime. This risk is not mitigated by the documentation changes in `canonical-reconciliation-01`.

---

## Deferred Implementation Item 2: scan_scheduler Dependency Refactor

**Status:** APPROVED — DEFERRED  
**Risk Level:** HIGH  
**Conflict Reference:** CON-004 (canonical-audit-01)  
**Gap Reference:** GAP-002 (canonical-audit-01)  

### Problem

`send/core/signal_engine.py` conditionally imports `from core.scan_scheduler import _focus_state_path`.

The module `send/core/scan_scheduler.py` does not exist and has no canonical specification.

The import is wrapped in a try/except, so the error is suppressed — but the function that depends on it (`update_symbol_replacement_score`) fails silently. State update calls have no effect.

### Approved Implementation Decision

**B2:** Refactor the `scan_scheduler` dependency in `signal_engine.py` to use the appropriate `fsm_runtime` state access directly, eliminating the dependency on the non-existent `scan_scheduler` module.

### Governing Note

No canonical specification exists for `scan_scheduler`. The refactoring must be anchored to the `fsm_runtime` state access patterns defined in `send/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md` and the broader strategy stack.

### Deferred To

A dedicated code-remediation task.

### Risk Status

**HIGH runtime risk remains OPEN.**

Until the refactoring is implemented and tested, `update_symbol_replacement_score` calls in `signal_engine.py` silently fail. This is a silent behavioral defect, not a crash, but it means state update logic is non-functional.

---

## What MUST NOT Be Done Before the Dedicated Code-Remediation Task

- Do not create `send/core/trade_temporal_telemetry.py` outside the dedicated code-remediation task.
- Do not modify `send/core/signal_engine.py` to remove or bypass the `trade_temporal_telemetry` import without implementing the module.
- Do not create `send/core/scan_scheduler.py` as a stub or placeholder without proper implementation.
- Do not mark either risk as resolved until implementation is complete and tested.

---

## Recommended Next Step

Begin a dedicated code-remediation task that:

1. Implements `send/core/trade_temporal_telemetry.py` per `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`.
2. Verifies all `signal_engine.py` imports resolve correctly after implementation.
3. Refactors the `scan_scheduler` dependency in `signal_engine.py` to use `fsm_runtime` state access directly.
4. Runs the full test suite (per `TEST_PLAN_v2.0.0.md`) after both changes.
5. Confirms both CRITICAL and HIGH risks are closed.

---

## Code-Remediation Task Preconditions

Before beginning code remediation:

- This governance reconciliation task (`canonical-reconciliation-01`) must be complete.
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` must be reviewed and confirmed as current and complete.
- `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` must be reviewed for `fsm_runtime` state access patterns.
- The code auditor must confirm no other missing module imports exist in `signal_engine.py` or adjacent core modules.

---

*End of DEFERRED_IMPLEMENTATION_REGISTER.md*
