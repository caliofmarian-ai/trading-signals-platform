MASTER_DOCUMENT_INDEX.md

BinaryBot — Master Documentation Index
Version: 1.0.0
Status: Canonical

Linked Documents:
All documents located in "/opt/binarybot/docs/ (root docs; active canon lives under /opt/binarybot/docs/canonical/active/)"

---

1. PURPOSE

This document provides a complete index of all canonical documentation used by BinaryBot.

The purpose of the Master Document Index is to:

- provide a single entry point into the documentation system
- show the structure of the architecture documentation
- define the relationship between documents
- prevent documentation fragmentation
- help developers locate the correct document quickly

This file acts as the table of contents for the entire BinaryBot architecture.

---

2. DOCUMENTATION STRUCTURE

BinaryBot documentation is organized into the following categories:

1. Core Architecture
2. Strategy & Trading Logic
3. System Operation
4. Distribution & UX
5. Observability & Analytics
6. Security & Governance
7. Testing & Validation
8. Deployment & Versioning
9. Operational Control

Each document has a specific responsibility.

No document should overlap responsibilities.

---

3. CORE ARCHITECTURE DOCUMENTS

These documents define the fundamental system structure.

ARCHITECTURE_CODE_MAPPING.md

Defines how architecture maps to actual source code modules.

Includes:

- folder structure
- module responsibilities
- code ownership boundaries
- internal system diagrams

This is the primary engineering reference.

---

MODULE_INTERFACE_SPEC_v2.0.0.md

Defines how modules communicate with each other.

Includes:

- function interfaces
- data contracts
- module boundaries
- dependency rules

Prevents module coupling errors.

---

SYSTEM_INVARIANTS_v2.0.0.md

Defines the non-negotiable rules of the system.

Examples:

- maximum watchlist size
- no OPEN in wide mode
- cooldown enforcement
- deterministic behavior

Violating an invariant means the system is compromised.

---

4. STRATEGY & TRADING LOGIC

These documents define the trading algorithm.

ALGO_SPEC_v2.0.0.md

Defines the trading strategy.

Includes:

- scoring system
- signal lifecycle
- buffer logic
- expiry calculation
- gate conditions
- signal classification

The algorithm must match this document exactly.

---

RISK_MODEL.md

Defines the protection layers preventing unsafe trades.

Includes:

- spike rejection
- support/resistance protection
- feasibility analysis
- volatility filtering

Risk protection overrides signal frequency.

---

PARAMS_REFERENCE.md

Defines all configurable parameters.

Includes:

- thresholds
- multipliers
- limits
- buffer ratios
- expiry constraints

All adjustable behavior must be defined here.

---

5. SIGNAL LIFECYCLE CONTROL

These documents control how signals move through the system.

FSM_DECISION_ENGINE_SPEC_v1.0.0.md

Defines the finite state machine controlling signal lifecycle.

States include:

- IDLE
- WATCHLIST
- LIVE_SENT
- COOLDOWN

Also defines state transitions and invariants.

---

SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md

Defines how signals are distributed to Telegram tiers.

Includes:

- FREE / BASIC / PRO / ELITE routing
- signal limits
- silent tier mode
- reset schedule
- deduplication rules

---

CHANNEL_CONFIG_SPEC_v2.0.0.md

Defines channel identifiers and configuration.

Includes:

- Telegram channel IDs
- tier configuration
- channel mapping
- visibility rules

---

6. USER EXPERIENCE

These documents define how users interact with BinaryBot.

TELEGRAM_UX_v2.0.0.md

Defines all Telegram message formats.

Includes:

- PRE signal format
- CONFIRM signal format
- OPEN_NOW format
- command behavior
- anti-spam rules

---

ADMIN_CONTROL_SPEC_v2.0.0.md

Defines the Admin Control Panel.

Includes:

- admin commands
- system control buttons
- research dashboard
- documentation viewer
- symbol selection interface

---

7. OBSERVABILITY & ANALYTICS

These documents define monitoring, logging, and research systems.

OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

Defines system logging.

Includes:

- log event types
- log structure
- crash logging
- anomaly detection
- audit trails

If something is not logged, it does not exist.

---

PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md

Defines statistical analysis of signals.

Includes:

- win rate tracking
- expectancy calculation
- signal funnel analysis
- symbol ranking
- session performance

Analytics supports strategy research.

---

EVENT_SCHEMA_SPEC_v2.0.0.md

Defines the schema of internal system events.

Examples:

- signal_event
- fsm_transition
- tier_publish
- user_outcome
- engine_start
- admin_change

This schema allows analytics and debugging to function.

---

8. SYSTEM OPERATION

These documents define how the system runs in production.

CHECKLIST.md

Defines operational verification steps.

Includes:

- patch control checklist
- startup checklist
- daily monitoring checklist
- incident response checklist

Used by system operators.

---

FAILURE_RECOVERY_SPEC_v2.0.0.md

Defines system recovery procedures.

Includes:

- crash recovery
- state corruption recovery
- rollback procedure
- emergency freeze mode

Ensures system stability during failures.

---

DATA_RETENTION_POLICY.md

Defines data storage policies.

Includes:

- log retention rules
- analytics retention
- backup requirements
- archive rules

Prevents uncontrolled storage growth.

---

9. SECURITY & GOVERNANCE

These documents protect system integrity.

SECURITY_MODEL.md

Defines security architecture.

Includes:

- access control
- role hierarchy
- admin authorization
- data protection
- attack mitigation

Protects against unauthorized access.

---

GOVERNANCE_AND_CHANGE_CONTROL.md

Defines rules for modifying the system.

Includes:

- change approval process
- documentation requirements
- version governance
- audit responsibilities

Ensures controlled system evolution.

---

10. TESTING & VALIDATION

These documents ensure the system behaves correctly.

TEST_PLAN.md

Defines system testing procedures.

Includes:

- structural tests
- FSM tests
- signal logic tests
- Telegram routing tests
- stress tests

No deployment allowed without passing tests.

---

11. DEPLOYMENT & VERSION CONTROL

These documents control system updates.

DEPLOYMENT_PROTOCOL.md

Defines deployment procedure.

Includes:

- release types
- restart protocol
- rollback procedure
- monitoring requirements

Ensures safe production updates.

---

RELEASE_VERSIONING_POLICY.md

Defines version numbering.

Includes:

- semantic versioning
- version bump rules
- changelog requirements
- rollback version control

Prevents version confusion.

---

CHANGELOG.md

Tracks system history.

Every release must include:

- version number
- change description
- bug fixes
- structural modifications

---

12. DOCUMENT RELATIONSHIP MAP

The documentation structure follows this hierarchy:

ALGO_SPEC
→ defines trading logic

FSM_SPEC
→ defines signal lifecycle

SIGNAL_DISTRIBUTION_SPEC
→ defines signal routing

TELEGRAM_UX
→ defines message format

OBSERVABILITY_LOGGING_SPEC
→ records system behavior

PERFORMANCE_ANALYTICS_SPEC
→ analyzes system results

DEPLOYMENT_PROTOCOL
→ controls system updates

CHECKLIST
→ controls daily operations

SYSTEM_INVARIANTS
→ protects system integrity

---

13. DOCUMENT GOVERNANCE RULE

Any modification to system behavior requires updates to:

1. Relevant specification document
2. CHANGELOG entry
3. Version increment

Code must never diverge from documentation.

---

14. MASTER DOCUMENT GUARANTEE

If all documents in this index are implemented correctly:

BinaryBot becomes:

- transparent
- auditable
- deterministic
- maintainable
- safe to evolve

The documentation system ensures long-term structural stability.

---

End of MASTER_DOCUMENT_INDEX.md