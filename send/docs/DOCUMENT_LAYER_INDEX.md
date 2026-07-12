BINARYBOT — DOCUMENT LAYER INDEX

Version: 1.0
Location: /opt/binarybot/docs/ (root docs; active canon lives under /opt/binarybot/docs/canonical/active/)DOCUMENT_LAYER_INDEX.md

This document classifies every canonical specification
into the system architecture layers defined in:

SYSTEM_ARCHITECTURE_MAP.md

Layers:

ENGINE
FSM
OBSERVABILITY
AUDIT
INTELLIGENCE
ADMIN
DISTRIBUTION
RISK

Additional meta layers:

GOVERNANCE
INFRASTRUCTURE
CORE DOCUMENTATION


------------------------------------------------------------
ENGINE LAYER
------------------------------------------------------------

Responsible for market processing and signal computation.

Documents:

ALGO_SPEC_v2.0.0.md
MODULE_INTERFACE_SPEC_v2.0.0.md
PARAMS_REFERENCE.md
RUNTIME_EXECUTION_TIMELINE.md
SYSTEM_INVARIANTS_v2.0.0.md


------------------------------------------------------------
FSM LAYER
------------------------------------------------------------

Responsible for signal lifecycle state machine.

Documents:

FSM_DECISION_ENGINE_SPEC_v1.0.0.md
SIGNAL_DECISION_FSM_SPEC.md
STATE_PERSISTENCE_SPEC.md


------------------------------------------------------------
OBSERVABILITY LAYER
------------------------------------------------------------

Responsible for logging, telemetry, and event visibility.

Documents:

OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
EVENT_SCHEMA_SPEC_v2.0.0.md
MONITORING_ALERTS_SPEC.md
FAILURE_RECOVERY_SPEC_v2.0.0.md


------------------------------------------------------------
AUDIT LAYER
------------------------------------------------------------

Responsible for explaining why decisions happened.

Documents:

DECISION_AUDIT_SPEC_v2.0.0.md


------------------------------------------------------------
INTELLIGENCE LAYER
------------------------------------------------------------

Transforms audit and observability data into strategy insight.

Documents:

AI_STRATEGY_AUDITOR_SPEC.md
STRATEGY_INTELLIGENCE_SYSTEM.md
PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md


------------------------------------------------------------
ADMIN LAYER
------------------------------------------------------------

Human operational control of the system.

Documents:

ADMIN_CONTROL_SPEC_v2.0.0.md
ADMIN_OPERATIONS_SPEC_v2.0.0.md
CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md


------------------------------------------------------------
DISTRIBUTION LAYER
------------------------------------------------------------

Responsible for delivering signals to Telegram channels.

Documents:

CHANNEL_CONFIG_SPEC_v2.0.0.md
SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
TELEGRAM_UX_v2.0.0.md


------------------------------------------------------------
RISK LAYER
------------------------------------------------------------

Responsible for outcome tracking and exposure control.

Documents:

OUTCOME_TRACKING_SPEC_v2.0.0.md
RISK_MODEL.md


------------------------------------------------------------
INFRASTRUCTURE LAYER
------------------------------------------------------------

Operational runtime and deployment.

Documents:

DEPLOYMENT_PROTOCOL.md
RUNBOOK.md
SECURITY_MODEL.md
DATA_RETENTION_POLICY.md


------------------------------------------------------------
GOVERNANCE LAYER
------------------------------------------------------------

Rules for documentation integrity and change management.

Documents:

GOVERNANCE_AND_CHANGE_CONTROL.md
RELEASE_VERSIONING_POLICY.md


------------------------------------------------------------
CORE DOCUMENTATION
------------------------------------------------------------

High-level project documents and structure.

Documents:

SYSTEM_ARCHITECTURE_MAP.md
ARCHITECTURE.md
ARCHITECTURE_CODE_MAPPING.md
MASTER_DOCUMENT_INDEX.md
FORMAL_SPEC.md
CHECKLIST.md
TEST_PLAN.md
CHANGELOG.md
COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md


------------------------------------------------------------
DEPRECATED
------------------------------------------------------------

Deprecated documents should remain only for historical reference.

Directory:

docs/_deprecated/


------------------------------------------------------------
CANONICAL RULE
------------------------------------------------------------

Every new specification must declare its layer.

Example header requirement:

Layer: ENGINE

or

Layer: INTELLIGENCE

No specification should exist without a layer assignment.

This keeps the documentation architecture deterministic.