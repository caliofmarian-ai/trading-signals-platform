from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "send" / "docs" / "canonical" / "active"

REPAIRS: dict[str, list[tuple[str, str]]] = {
    "ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md": [
        (
            "- updates all normative links to the final proposed successor filenames required by the Trade Physics + staged-execution promotion graph;",
            "- updates all normative links to the active successor filenames established by the Trade Physics + staged-execution promotion;",
        ),
    ],
    "ALGO_SPEC_v3.0.0.md": [
        ("- `canonical/superseded/CANONICAL_STRATEGY_STACK_v1.0.0.md` until successor promotion", "- `canonical/superseded/CANONICAL_STRATEGY_STACK_v1.0.0.md`"),
        ("- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` until successor promotion", "- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`"),
        ("This document is a complete proposed successor, not an amendment to the active file.", "This document is the active canonical successor to `ALGO_SPEC_v2.0.0.md`."),
        ("- `ALGO_SPEC_v2.0.0.md` remains authoritative;", "- `ALGO_SPEC_v2.0.0.md` is superseded and retained for historical provenance;"),
        ("- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` remains proposed;", "- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` is active canonical under the executed 2026-09-01 promotion;"),
        ("- PR #73 remains on canonical hold.", "- PR #73 is historical and was closed without merge as superseded by the promoted canonical/runtime sequence."),
    ],
    "SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md": [
        ("- `canonical/superseded/TIME_MODEL_UNIFIED_CANON_v2.0.0.md` until successor promotion", "- `canonical/superseded/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`"),
        ("- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` until successor promotion", "- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`"),
        ("- `canonical/superseded/OBSERVABILITY_SPEC_v2.0.0.md` until successor promotion", "- `canonical/superseded/OBSERVABILITY_SPEC_v2.0.0.md`"),
    ],
    "TIME_MODEL_UNIFIED_CANON_v3.0.0.md": [
        ("- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` until successor promotion", "- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`"),
        ("- `canonical/superseded/FSM_DECISION_ENGINE_SPEC_v1.0.0.md` until successor promotion", "- `canonical/superseded/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`"),
        ("This document is a complete proposed successor. Until explicit promotion, `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` remains the sole active time authority and no runtime change is authorized by this file.", "This document is the active canonical successor to `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`. Runtime changes remain subject to Governance, Test Plan, and Deployment Protocol controls."),
    ],
    "TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md": [
        ("This section is a technical reconciliation introduced by this proposed successor because the intake source defines the concept but does not provide exact weights.", "This section is a technical reconciliation in this active specification because the intake source defines the concept but does not provide exact weights."),
        ("This document does not authorize code changes before promotion.", "Code changes remain subject to canonical Governance, Test Plan, and Deployment Protocol controls."),
        ("Status now: PROPOSED — NOT ACTIVE.", "Status now: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`."),
    ],
    "DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md": [
        ("- `canonical/superseded/FSM_DECISION_ENGINE_SPEC_v1.0.0.md` until successor promotion", "- `canonical/superseded/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`"),
        ("- `canonical/superseded/OBSERVABILITY_SPEC_v2.0.0.md` until successor promotion", "- `canonical/superseded/OBSERVABILITY_SPEC_v2.0.0.md`"),
        ("- `canonical/superseded/DECISION_AUDIT_SPEC_v2.0.0.md` until successor promotion", "- `canonical/superseded/DECISION_AUDIT_SPEC_v2.0.0.md`"),
        ("Final enum names must be synchronized across Trade Physics model, DecisionObject implementation, Decision Audit and Event Schema before promotion.", "Final enum names must remain synchronized across Trade Physics model, DecisionObject implementation, Decision Audit and Event Schema."),
    ],
    "FSM_DECISION_ENGINE_SPEC_v2.0.0.md": [
        ("This is the complete proposed successor for FSM decision truth.", "This is the active canonical successor for FSM decision truth."),
    ],
    "SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md": [
        ("This document is the complete consolidated proposed successor for the signal-execution domain.", "This document is the active canonical consolidated successor for the signal-execution domain."),
    ],
    "OBSERVABILITY_SPEC_v3.0.0.md": [
        ("This is the complete proposed successor for observability policy.", "This is the active canonical successor for observability policy."),
    ],
    "OBSERVABILITY_LOGGING_SPEC_v3.0.0.md": [
        ("This is the complete proposed implementation-level logging contract.", "This is the active canonical implementation-level logging contract."),
    ],
    "EVENT_SCHEMA_SPEC_v3.0.0.md": [
        ("This document is a complete proposed successor and does not depend on v2 to supply omitted normative behavior.", "This document is the active canonical successor and does not depend on v2 to supply omitted normative behavior."),
    ],
    "DECISION_AUDIT_SPEC_v3.0.0.md": [
        ("This is a complete proposed successor. Until promotion, v2.0.0 remains authoritative. No runtime change is authorized by this proposal alone.", "This is the active canonical successor to v2.0.0. Runtime changes remain subject to Governance, Test Plan, and Deployment Protocol controls."),
    ],
    "AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md": [
        ("Until promotion, v2.0.0 remains authoritative. This proposed successor does not authorize autonomous production mutation.", "This active canonical successor does not authorize autonomous production mutation; any production mutation remains governed."),
    ],
    "SYSTEM_ARCHITECTURE_MAP_v3.0.0.md": [
        ("This document is a complete proposed successor for the top-level system architecture map.", "This document is the active canonical successor for the top-level system architecture map."),
    ],
    "MODULE_INTERFACE_SPEC_v3.0.0.md": [
        ("This is the complete proposed successor for module ownership/interface truth.", "This is the active canonical successor for module ownership/interface truth."),
    ],
    "TEST_PLAN_v3.0.0.md": [
        ("This is a complete proposed validation successor.", "This is the active canonical validation successor."),
    ],
    "HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md": [
        ("This document extends the proposed successor control-plane authority defined by:", "This document extends the active canonical control-plane authority defined by:"),
    ],
}


def main() -> None:
    changed = 0
    replacements = 0
    for name, pairs in REPAIRS.items():
        path = ACTIVE / name
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in pairs:
            count = text.count(old)
            if count != 1:
                raise SystemExit(f"{name}: expected exactly one match for {old!r}, found {count}")
            text = text.replace(old, new, 1)
            replacements += 1
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
    print(f"FILES_REPAIRED={changed}")
    print(f"EXACT_REPLACEMENTS={replacements}")


if __name__ == "__main__":
    main()
