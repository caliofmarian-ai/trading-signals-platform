from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "send" / "docs" / "canonical" / "active"

REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "ALGO_SPEC_v3.0.0.md": [
        ("- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`", "- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`"),
        ("Detailed Trade Physics mathematics are delegated to `TRADE_PHYSICS_MODEL_SPEC_v1.0.0` once promoted.", "Detailed Trade Physics mathematics are delegated to the active `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`."),
        ("Trade Physics is current-scope and mandatory once this successor set is promoted and implemented.", "Trade Physics is current-scope and mandatory in the active strategic contract; implementation remains governed by the active change, test, and deployment controls."),
        ("Proposed readiness families include:", "Canonical readiness families include:"),
        ("- incomplete mandatory Trade Physics evidence after promotion;", "- incomplete mandatory Trade Physics evidence;"),
        ("The current runtime TPS calculation inside Signal Engine is implementation drift to be corrected after canonical promotion.", "Any runtime TPS calculation inside Signal Engine that remains primary strategic TPS ownership is implementation drift requiring governed remediation against the active canon."),
        ("After promotion, every implementation patch must prove:", "Every implementation patch under this active canon must prove:"),
        ("If this successor is promoted, implementation order should be:", "Implementation order under this active successor should be:"),
    ],
    "SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md": [
        ("After promotion, code must answer clearly:", "Under this active canon, code must answer clearly:"),
    ],
    "TIME_MODEL_UNIFIED_CANON_v3.0.0.md": [
        ("This document is the proposed unified authority for all BinaryBot time semantics after current Trade Physics integration.", "This document is the active canonical unified authority for all BinaryBot time semantics after current Trade Physics integration."),
        ("The proposed v3 Model Time chain is:", "The canonical v3 Model Time chain is:"),
        ("It is no longer the preferred primary denominator speed for intended-direction `t_needed` in the proposed v3 model.", "It is no longer the preferred primary denominator speed for intended-direction `t_needed` in the active v3 model."),
        ("No TPS score may be calculated using legacy generic `expiry_minutes` as the primary model-time source after v3 promotion.", "Under active v3 canon, no TPS score may be calculated using legacy generic `expiry_minutes` as the primary model-time source."),
        ("- proposed v3 `t_needed = buffer_distance / directional_effective_speed`", "- canonical v3 `t_needed = buffer_distance / directional_effective_speed`"),
        ("- gross absolute speed silently standing in for directional speed after v3 promotion;", "- gross absolute speed silently standing in for directional speed under active v3 canon;"),
        ("After promotion, implementation must:", "Implementation under this active canon must:"),
        ("The canonical proposed chain is:", "The canonical chain is:"),
    ],
    "TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md": [
        ("Proposed authority relationship:", "Authority relationship:"),
        ("- this document is proposed as the detailed mathematical authority for Trade Physics metric derivation and deterministic TPS.", "- this document is the active detailed mathematical authority for Trade Physics metric derivation and deterministic TPS."),
        ("The intake sources contain overlapping and conflicting definitions. This proposed canon resolves them as follows.", "The intake sources contain overlapping and conflicting definitions. This active canon resolves them as follows."),
        ("A learned/calibrated model output is named `trade_success_probability` in this proposal.", "A learned/calibrated model output is named `trade_success_probability` in this specification."),
        ("### 7.1 Proposed v1 deterministic algorithm", "### 7.1 Canonical v1 deterministic algorithm"),
        ("The canonical proposed initial weights are sourced from `TRADE_PHYSICS_SCORE_SPEC.md`:", "The canonical initial weights are sourced from `TRADE_PHYSICS_SCORE_SPEC.md`:"),
        ("Trade Physics is current-scope and mandatory in the strategic contract once this canon is promoted and implemented.", "Trade Physics is current-scope and mandatory in the active strategic contract; implementation remains governed by active change, test, and deployment controls."),
        ("A Trade Physics evaluation must expose one of the following proposed states:", "A Trade Physics evaluation must expose one of the following canonical readiness states:"),
        ("The exact state enum may be adjusted during canonical review, but missing evidence MUST be explicit.", "Any adjustment to the exact state enum requires versioned canonical review/change control, and missing evidence MUST remain explicit."),
        ("The proposed strategic contract must expose a recognizable Trade Physics domain or score subdomain containing at minimum:", "The canonical strategic contract must expose a recognizable Trade Physics domain or score subdomain containing at minimum:"),
        ("Canonical feature mappings proposed for v1:", "Canonical feature mappings for v1:"),
        ("This proposal treats those as approved research candidates, not as a locked library dependency.", "This specification treats those as approved research candidates, not as a locked library dependency."),
        ("Proposed states:\n", "Canonical readiness states:\n"),
        ("The following deterministic defaults are structural model constants in this proposed v1 contract:", "The following deterministic defaults are structural model constants in this active v1 contract:"),
        ("## 24. REQUIRED CODE REALIGNMENT AFTER PROMOTION", "## 24. REQUIRED CODE REALIGNMENT UNDER ACTIVE CANON"),
        ("After promotion, the implementation audit must at minimum inspect and reconcile:", "The governed implementation audit must at minimum inspect and reconcile:"),
        ("## 26. CURRENT STATUS AND PROMOTION GATE", "## 26. CURRENT STATUS AND POST-ACTIVATION GOVERNANCE"),
        ("Before this document can become active:\n", "The executed 2026-09-01 activation record confirms this document is active; the promoted graph resolved the following activation prerequisites:\n"),
        ("No runtime code modification is authorized until that promotion gate is satisfied.", "Canonical activation alone does not authorize runtime modification; code changes remain subject to Governance, Test Plan, Deployment Protocol, and canon-to-code audit controls."),
    ],
    "DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md": [
        ("Must use the unified v3 time vocabulary once promoted:", "Must use the active unified v3 time vocabulary:"),
        ("Proposed readiness families:", "Canonical readiness families:"),
        ("This v2 proposal locks the following if promoted:", "This active v2 canon locks the following:"),
        ("After promotion, implementation must answer:", "Implementation under this active canon must answer:"),
    ],
    "FSM_DECISION_ENGINE_SPEC_v2.0.0.md": [
        ("- `SYSTEM_INVARIANTS_v2.0.0.md`", "- `SYSTEM_INVARIANTS_v3.0.0.md`"),
        ("After promotion, implementation must answer:", "Implementation under this active canon must answer:"),
        ("On promotion:\n", "Under the executed promotion:\n"),
        ("- runtime remains unchanged until post-promotion canonical/code audit.", "- runtime changes remain governed by canon-to-code audit, Test Plan, and Deployment Protocol controls."),
    ],
    "SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md": [
        ("- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`", "- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`"),
        ("- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`", "- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`"),
        ("- `CHANNEL_CONFIG_SPEC_v2.0.0.md`", "- `CHANNEL_CONFIG_SPEC_v2.0.1.md`"),
        ("Merge of this proposal does not authorize runtime changes, distribution activation, Telegram publication, outcome creation, or broker execution.", "This active specification does not by itself authorize runtime changes, distribution activation, Telegram publication, outcome creation, or broker execution."),
        ("If runtime currently computes TPS inside Signal Engine, that behavior is implementation drift to be corrected after canonical promotion.", "If runtime computes primary strategic TPS inside Signal Engine, that behavior is implementation drift requiring governed remediation against the active canon."),
        ("On promotion:\n", "Under the executed promotion:\n"),
    ],
    "RISK_MODEL_v3.0.0.md": [
        ("- `FAILURE_RECOVERY_SPEC_v2.0.0.md`", "- `FAILURE_RECOVERY_SPEC_v2.0.1.md`"),
        ("- `SECURITY_MODEL_v2.0.0.md`", "- `SECURITY_MODEL_v2.0.1.md`"),
        ("- `TELEGRAM_UX_v2.0.0.md`", "- `TELEGRAM_UX_v2.0.1.md`"),
        ("No runtime code change is authorized by this proposal alone.", "No runtime code change is authorized by this active specification alone."),
        ("Any parallel legacy formula inside Risk/Signal Engine that contradicts promoted canon is implementation drift to remediate after canonical promotion.", "Any parallel legacy formula inside Risk/Signal Engine that contradicts active canon is implementation drift requiring governed remediation."),
    ],
    "OBSERVABILITY_SPEC_v3.0.0.md": [
        ("No code behavior is authorized by this proposal alone.", "No code behavior is authorized by this active specification alone."),
        ("Runtime JSON schema, log writers, dashboards and report code are implementations that must be audited against this policy after promotion.", "Runtime JSON schema, log writers, dashboards and report code are implementations that must be audited against this active policy."),
    ],
    "OBSERVABILITY_LOGGING_SPEC_v3.0.0.md": [
        ("After promotion, implementation must demonstrate:", "Implementation under this active canon must demonstrate:"),
    ],
    "EVENT_SCHEMA_SPEC_v3.0.0.md": [
        ("After promotion, `send/schema/event_schema.json` must be re-audited against this canonical spec.", "Under this active canon, `send/schema/event_schema.json` must be audited against this canonical spec."),
        ("Any runtime event type/field drift must be corrected only after canonical promotion and test-plan approval.", "Any runtime event type/field drift must be corrected only through active governance and Test Plan approval."),
    ],
    "DECISION_AUDIT_SPEC_v3.0.0.md": [
        ("After promotion, code must demonstrate:", "Under this active canon, code must demonstrate:"),
    ],
    "TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md": [
        ("## 20. Implementation sequence after promotion", "## 20. Implementation sequence under active canon"),
    ],
    "TELEGRAM_UX_v2.0.1.md": [
        ("Older UX ideas may inform implementation only where consistent with this active/proposed canon.", "Older UX ideas may inform implementation only where consistent with this active canon."),
    ],
    "ADMIN_CONTROL_SPEC_v2.0.1.md": [
        ("Until atomic promotion, `ADMIN_CONTROL_SPEC_v2.0.0.md` remains active.", "`ADMIN_CONTROL_SPEC_v2.0.1.md` is active canonical under the executed atomic promotion; `ADMIN_CONTROL_SPEC_v2.0.0.md` is superseded."),
    ],
    "RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md": [
        ("Because the proposed canonical v3 Time Model materially changes speed semantics, research must maintain an explicit comparison:", "Because the active canonical v3 Time Model materially changes speed semantics, research must maintain an explicit comparison:"),
    ],
    "STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md": [
        ("- active/proposed Performance Analytics, Research/Learning and Autonomous Evolution successors", "- active Performance Analytics, Research/Learning and Autonomous Evolution successors"),
        ("## 24. IMPLEMENTATION REQUIREMENTS AFTER PROMOTION", "## 24. IMPLEMENTATION REQUIREMENTS UNDER ACTIVE CANON"),
    ],
    "AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md": [
        ("The current proposed defaults are structural constants until Parameter Control canon says otherwise.", "The current canonical defaults are structural constants until Parameter Control canon says otherwise."),
        ("The initial proposed directional speed uses:", "The current canonical directional speed uses:"),
    ],
    "COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md": [
        ("The current proposed canonical graph separates:", "The current canonical graph separates:"),
        ("On promotion:\n", "Under the executed promotion:\n"),
    ],
    "SYSTEM_ARCHITECTURE_MAP_v3.0.0.md": [
        ("- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`", "- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`"),
        ("- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`", "- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`"),
        ("- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`", "- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`"),
        ("After promotion, code audit must identify:", "Under this active canon, code audit must identify:"),
        ("On v3 promotion:\n", "Under the executed v3 promotion:\n"),
        ("- runtime code remains unchanged until post-promotion audit.", "- runtime changes remain governed by canon-to-code audit, Test Plan, and Deployment Protocol controls."),
    ],
    "MODULE_INTERFACE_SPEC_v3.0.0.md": [
        ("Any current TPS calculation in Signal Engine is implementation drift against the proposed target contract.", "Any current primary strategic TPS calculation in Signal Engine is implementation drift against the active target contract."),
        ("After promotion, code audit must map each module/function to these owners/contracts and identify:", "Under this active canon, code audit must map each module/function to these owners/contracts and identify:"),
        ("No implementation change occurs before that post-promotion audit.", "Implementation changes remain subject to the governed canon-to-code audit, Test Plan, and Deployment Protocol controls."),
    ],
    "TEST_PLAN_v3.0.0.md": [
        ("- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`", "- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`"),
        ("- `DEPLOYMENT_PROTOCOL_v2.0.0.md`", "- `DEPLOYMENT_PROTOCOL_v2.0.1.md`"),
        ("- `FAILURE_RECOVERY_SPEC_v2.0.0.md`", "- `FAILURE_RECOVERY_SPEC_v2.0.1.md`"),
    ],
}


def main() -> None:
    changed: list[str] = []
    replacement_count = 0
    for name, pairs in REPLACEMENTS.items():
        path = ACTIVE / name
        if not path.exists():
            raise SystemExit(f"FAIL missing active canonical file: {name}")
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in pairs:
            count = text.count(old)
            if count != 1:
                raise SystemExit(f"FAIL {name}: expected exactly 1 occurrence, found {count}: {old!r}")
            text = text.replace(old, new, 1)
            replacement_count += 1
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(name)

    allowed = set(REPLACEMENTS)
    if set(changed) != allowed:
        raise SystemExit(f"FAIL changed file set mismatch: changed={sorted(changed)} expected={sorted(allowed)}")

    print(f"PASS files changed={len(changed)}")
    print(f"PASS exact replacements={replacement_count}")
    for name in sorted(changed):
        print(name)


if __name__ == "__main__":
    main()
