RELEASE_VERSIONING_POLICY.md

BinaryBot — Release Versioning & Change Management Policy
Version: 1.0.0
Status: Canonical

Linked Documents:
DEPLOYMENT_PROTOCOL.md
CHANGELOG.md
ALGO_SPEC.md (active canonical successor: ALGO_SPEC_v2.0.0.md)
FSM_SPEC.md (active canonical successor: FSM_DECISION_ENGINE_SPEC_v1.0.0.md)
PARAMS_REFERENCE.md
SYSTEM_INVARIANTS.md (active canonical successor: SYSTEM_INVARIANTS_v2.0.0.md)
TEST_PLAN.md
GOVERNANCE_AND_CHANGE_CONTROL.md

---

1. PURPOSE

This document defines the official versioning system used by BinaryBot.

Versioning ensures that:

- every system change is traceable
- deployments are predictable
- documentation and code remain aligned
- strategy evolution is transparent
- rollback is possible

Without versioning discipline, system behavior becomes impossible to audit.

All BinaryBot releases must follow this versioning policy.

---

2. VERSION FORMAT

BinaryBot uses semantic versioning:

MAJOR.MINOR.PATCH

Example:

1.0.0
1.1.0
1.1.3
2.0.0

Each number represents a different level of change.

---

3. PATCH RELEASES

Format:

x.x.PATCH

Example:

1.0.0 → 1.0.1

Patch releases are used for minor corrections.

Examples:

- bug fixes
- logging improvements
- documentation fixes
- monitoring adjustments
- analytics display corrections

Patch releases must not change trading logic.

---

3.1 Patch Requirements

Required steps:

- Update CHANGELOG.md
- Confirm TEST_PLAN basic tests pass
- Verify no change in trading behavior

Patch releases must never modify:

- scoring model
- FSM structure
- risk filters
- signal thresholds

---

4. MINOR RELEASES

Format:

x.MINOR.x

Example:

1.0.0 → 1.1.0

Minor releases introduce controlled improvements.

Examples:

- parameter tuning
- threshold adjustments
- buffer multipliers
- expiry calculations
- analytics improvements
- distribution improvements

Minor releases may affect trading behavior but must preserve system structure.

---

4.1 Minor Release Requirements

Required steps:

1. Update CHANGELOG.md
2. Update PARAMS_REFERENCE.md
3. Run full TEST_PLAN.md
4. Verify no SYSTEM_INVARIANTS violations
5. Update version inside configuration

Example:

algo_version = "1.1.0"

---

5. MAJOR RELEASES

Format:

MAJOR.x.x

Example:

1.2.4 → 2.0.0

Major releases indicate structural changes to the system.

Examples:

- new scoring model
- new signal lifecycle
- FSM redesign
- risk model overhaul
- new trading architecture
- new strategy modules

Major releases change system behavior significantly.

---

5.1 Major Release Requirements

Major releases require:

- ALGO_SPEC.md (active canonical successor: ALGO_SPEC_v2.0.0.md) update
- FSM_SPEC.md (active canonical successor: FSM_DECISION_ENGINE_SPEC_v1.0.0.md) update
- RISK_MODEL.md review
- PERFORMANCE_ANALYTICS_SPEC.md (active canonical successor: PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md) review
- Full TEST_PLAN execution
- Manual dry-run validation

Major releases require careful verification before production deployment.

---

6. VERSION LOCATION

BinaryBot version must appear in three locations.

6.1 Engine Startup

On engine startup logs:

ENGINE STARTED
Algo Version: x.x.x

This confirms runtime version.

---

6.2 Configuration File

The strategy version must appear in:

config/algo_params.json

Example:

"algo_version": "1.1.0"

---

6.3 CHANGELOG

All releases must be documented in:

CHANGELOG.md

The changelog describes what changed in each release.

---

7. CHANGELOG REQUIREMENTS

Every version release must include an entry.

Example format:

Version 1.1.0
Date: 2026-03-05

Changes:

- Adjusted buffer multiplier
- Improved spike rejection filter
- Updated analytics metrics

Bug fixes:

- Corrected duplicate PRE log issue

---

8. PARAMETER CHANGE RULE

Any modification to strategy parameters requires:

Version increment.

Examples:

- score thresholds
- ATR multipliers
- expiry limits
- feasibility thresholds

These changes affect strategy behavior and must be versioned.

---

9. UNDOCUMENTED CHANGE PROHIBITION

Changing system behavior without documentation is forbidden.

If code changes without:

- version bump
- changelog update

the release is considered invalid.

This protects system governance.

---

10. VERSION CONSISTENCY

Version numbers must remain consistent across:

- codebase
- configuration files
- deployment logs
- documentation

Mismatch indicates deployment error.

---

11. VERSION DISPLAY REQUIREMENT

Whenever the engine starts, it must display:

ENGINE STARTED
Algo Version: x.x.x
Mode: WIDE_SCAN / FOCUS_MODE

This ensures operators know which version is active.

---

12. ROLLBACK VERSION RULE

Rollback must restore:

- previous code
- previous configuration
- previous version number

Example:

Deployment version: 1.2.0
Rollback version: 1.1.4

Rollback must never leave version state ambiguous.

---

13. EXPERIMENTAL FEATURES

Experimental features must never be deployed directly to production.

Instead:

- test in development environment
- validate via TEST_PLAN
- include documentation update

Only then may they enter official version releases.

---

14. VERSION GOVERNANCE

The OWNER role is responsible for approving:

- major releases
- strategy modifications
- structural system changes

This ensures long-term stability of the trading engine.

---

15. VERSIONING GUARANTEE

If this policy is followed:

- every release becomes traceable
- strategy evolution remains documented
- debugging becomes easier
- rollback remains safe
- governance remains intact

Version discipline ensures BinaryBot evolves without losing structural integrity.

---

End of RELEASE_VERSIONING_POLICY.md