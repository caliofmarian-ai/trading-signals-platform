BINARYBOT — MASTER DOCUMENTATION INDEX

Version: 1.0  
Status: CANONICAL SPECIFICATION  
Location: /opt/binarybot/docs/ (root docs; active canon lives under /opt/binarybot/docs/canonical/active/)BINARYBOT_MASTER_INDEX.md


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

This document is the master index of the BinaryBot
documentation library.

It provides a structured overview of all canonical
documents in the system.

The index organizes documents by architecture layers
to maintain clarity, traceability, and maintainability.


------------------------------------------------------------
2. SYSTEM ARCHITECTURE OVERVIEW
------------------------------------------------------------

BinaryBot is structured into several functional layers.

Architecture stack:

MARKET DATA
↓
ENGINE
↓
FSM
↓
OBSERVABILITY
↓
DECISION AUDIT
↓
INTELLIGENCE
↓
ADMIN CONTROL
↓
DISTRIBUTION
↓
AFFILIATE NETWORK
↓
ECONOMICS


------------------------------------------------------------
3. ENGINE LAYER
------------------------------------------------------------

The engine layer contains the trading logic that analyzes
market data and generates signal decisions.

Core documents:

SIGNAL_ENGINE_SPEC.md

STRATEGY_LOGIC_SPEC.md

STRATEGY_PARAMETER_CONTROL_SPEC.md


Purpose:

signal generation

strategy evaluation

market analysis


------------------------------------------------------------
4. FSM LAYER
------------------------------------------------------------

The FSM layer defines the lifecycle of a trading signal.

Core document:

SIGNAL_DECISION_FSM_SPEC.md


Signal states:

PRE  
CONFIRM  
OPEN_NOW  
RESULT  


Purpose:

control signal progression

ensure consistent signal lifecycle


------------------------------------------------------------
5. OBSERVABILITY LAYER
------------------------------------------------------------

The observability layer records operational events
for diagnostics and analytics.

Core documents:

EVENT_SCHEMA_SPEC_v2.0.0.md

OBSERVABILITY_LOGGING_SPEC_v2.0.0.md


Primary logs:

/opt/binarybot/observability/engine_events.jsonl

/opt/binarybot/observability/fsm_events.jsonl

/opt/binarybot/observability/distribution_events.jsonl


Purpose:

system transparency

debugging

analytics


------------------------------------------------------------
6. DECISION AUDIT LAYER
------------------------------------------------------------

The decision audit system records why signals
are accepted or rejected.

Core document:

DECISION_AUDIT_SPEC_v2.0.0.md


Purpose:

strategy diagnostics

explain signal decisions

support strategy analysis


------------------------------------------------------------
7. INTELLIGENCE LAYER
------------------------------------------------------------

The intelligence layer analyzes system behavior
and generates insights.

Core documents:

AI_STRATEGY_AUDITOR_SPEC.md

AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md


Purpose:

strategy diagnostics

strategy optimization

long-term analysis


------------------------------------------------------------
8. DEBUG AND DIAGNOSTICS
------------------------------------------------------------

Debugging tools provide real-time visibility
into signal generation.

Core document:

SIGNAL_DEBUG_DASHBOARD_SPEC.md


Purpose:

diagnose strategy behavior

identify signal rejection causes

monitor engine activity


------------------------------------------------------------
9. ADMIN CONTROL LAYER
------------------------------------------------------------

The admin layer provides operational control
over the system.

Core documents:

CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md

ADMIN_CONTROL_SPEC_v2.0.0.md

ADMIN_OPERATIONS_SPEC_v2.0.0.md

ROLE_AND_PERMISSION_MATRIX_SPEC.md


Purpose:

system management

role-based access control

strategy parameter control


------------------------------------------------------------
10. SIGNAL DISTRIBUTION LAYER
------------------------------------------------------------

The distribution layer delivers signals
to users through communication channels.

Core document:

SIGNAL_DISTRIBUTION_ARCHITECTURE.md


Purpose:

route signals to Telegram channels

manage distribution tiers

handle delivery reliability


------------------------------------------------------------
11. AFFILIATE DISTRIBUTION LAYER
------------------------------------------------------------

Affiliate distribution enables signal promotion
through external influencers.

Core document:

AFFILIATE_SIGNAL_DISTRIBUTION_MODEL.md


Purpose:

user acquisition

revenue sharing

affiliate ecosystem


------------------------------------------------------------
12. ECONOMICS LAYER
------------------------------------------------------------

The economics layer defines how the platform
generates revenue.

Core document:

SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL.md


Purpose:

subscription structure

affiliate revenue sharing

platform monetization


------------------------------------------------------------
13. ANALYTICS AND REPORTING
------------------------------------------------------------

Analytics tools generate strategy reports.

Core systems:

Strategy Auditor

Strategy Heatmap

Signal Diagnostics


Report location:

/opt/binarybot/analytics/reports/


Purpose:

strategy evaluation

performance tracking


------------------------------------------------------------
14. CONFIGURATION LAYER
------------------------------------------------------------

System configuration files control
runtime behavior.

Primary configuration files:

/opt/binarybot/config/strategy_params.json


Purpose:

dynamic strategy control

runtime configuration management


------------------------------------------------------------
15. DATA STORAGE
------------------------------------------------------------

BinaryBot uses structured log storage.

Primary directories:

/opt/binarybot/observability/

/opt/binarybot/analytics/

/opt/binarybot/outcomes/


Purpose:

event logging

analytics processing

performance tracking


------------------------------------------------------------
16. DOCUMENTATION STRUCTURE
------------------------------------------------------------

All canonical documents are stored in:

/opt/binarybot/docs/ (root docs; active canon lives under /opt/binarybot/docs/canonical/active/)


Naming convention:

SPEC.md for system specifications

MODEL.md for business models

ARCHITECTURE.md for system architecture


------------------------------------------------------------
17. DOCUMENT RELATIONSHIPS
------------------------------------------------------------

Key document relationships:

SIGNAL_DECISION_FSM_SPEC.md

defines signal lifecycle.


DECISION_AUDIT_SPEC_v2.0.0.md

explains signal rejection reasons.


AI_STRATEGY_AUDITOR_SPEC.md

analyzes strategy behavior.


STRATEGY_PARAMETER_CONTROL_SPEC.md

defines strategy parameter management.


SIGNAL_DISTRIBUTION_ARCHITECTURE.md

defines signal delivery.


------------------------------------------------------------
18. MAINTENANCE RULES
------------------------------------------------------------

All documentation updates must follow
canonical documentation standards.

Rules:

new features require specification updates

deprecated features must be documented

documentation must reflect system behavior


------------------------------------------------------------
19. FUTURE DOCUMENTS
------------------------------------------------------------

Possible future documents:

PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md

RISK_MANAGEMENT_SYSTEM_SPEC.md

BROKER_INTEGRATION_ARCHITECTURE.md


------------------------------------------------------------
20. FINAL STATEMENT
------------------------------------------------------------

The BinaryBot master documentation index ensures
that all components of the system remain organized,
traceable, and understandable.

This document serves as the central navigation
point for the entire BinaryBot architecture.