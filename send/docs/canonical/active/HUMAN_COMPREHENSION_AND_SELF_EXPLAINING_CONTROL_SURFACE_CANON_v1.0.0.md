# HUMAN COMPREHENSION AND SELF-EXPLAINING CONTROL SURFACE CANON

**Document ID:** HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON
**Version:** 1.0.0
**Status:** ACTIVE CANON
**Domain:** Admin Surface / Human Comprehension / Operational Memory
**Primary Surface:** Telegram
**Authority Root:** ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0

---

## 1. Purpose

This canon defines the mandatory human-comprehension contract for every stable human-facing control surface of the system.

The system must not assume that the Owner or another authorized operator remembers previous conversations, implementation history, internal terminology, acronyms, parameters, lifecycle states, architectural relationships, or the consequences of available controls.

The interface itself must preserve enough operational knowledge for an authorized human to understand and safely operate the system after an extended absence.

This requirement makes the human interface simultaneously:

- a control surface;
- an observation surface;
- a contextual operational manual;
- a persistent operational memory.

This canon governs presentation and comprehension.

It does not transfer canonical ownership of strategy, execution, distribution, analytics, permissions, research, or governance into the presentation layer.

---

## 2. Canonical Authority

This document extends the active control-plane authority defined by:

- `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md`
- `ADMIN_CONTROL_SPEC_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`
- `ADMIN_TREE_MAP_v2.0.0.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`
- `SYSTEM_INVARIANTS_v2.0.0.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`

For domain-specific concepts, explanatory content must derive its meaning from the active canonical owner of that domain.

Presentation must never become an alternate source of system truth.

---

## 3. No Naked Operational Concept Principle

No stable human-facing operational concept may be presented without sufficient contextual explanation for correct interpretation.

A naked operational concept includes an unexplained:

- subsystem;
- page;
- acronym;
- lifecycle state;
- runtime state;
- threshold;
- score;
- multiplier;
- metric;
- mode;
- health condition;
- control;
- action;
- warning;
- risk;
- role;
- permission;
- file;
- report;
- audit artifact;
- distribution result;
- outcome result.

Terms such as:

- Engine;
- Strategy;
- FSM;
- WIDE_SCAN;
- FOCUS_MODE;
- PRE;
- CONFIRM;
- OPEN;
- WATCHLIST;
- COOLDOWN;
- SR;
- Corridor;
- ATR;
- Spike;
- Distribution;
- Outcome;
- Analytics;
- Research;
- Recovery;
- DEGRADED_SAFE;
- Shadow Mode;
- Broker Execution;

must be understandable from the human control surface without requiring remembered chat history.

---

## 4. Interface as Operational Memory Principle

Historical chat conversations are not an operational dependency.

Developer memory is not an operational dependency.

Operator folklore is not an operational dependency.

An authorized Owner returning after an extended absence must be able to reconstruct from the interface:

1. what a component is;
2. why it exists;
3. where it sits in the architecture;
4. what it receives;
5. what it produces;
6. what its current state means;
7. what displayed values mean;
8. what controls are available;
9. what those controls change;
10. what they do not change;
11. what consequences or risks exist;
12. which canonical source owns the concept.

---

## 5. Mandatory Human Comprehension Contract

Every stable primary page must provide or contextually expose the following information.

### 5.1 Identity

What is this component or capability?

### 5.2 Purpose

Why does it exist?

What operational problem does it solve?

### 5.3 Pipeline Position

Where does it sit in the system?

Where meaningful, identify its important upstream and downstream relationships.

### 5.4 Current State

What is happening now?

Static definition and live state must remain distinguishable.

### 5.5 Interpretation

What do the displayed:

- states;
- values;
- counters;
- scores;
- thresholds;
- timestamps;
- metrics;
- warnings

mean?

### 5.6 Controls

What can the authorized human do here?

Read-only visibility must not imply mutation authority.

### 5.7 Consequences

What is the expected consequence of each material control?

### 5.8 Limitations

What does this page, state, metric, or result NOT prove?

### 5.9 Canonical Source

Which active canonical document owns the meaning?

### 5.10 Learn More

How can the human obtain a deeper explanation?

---

## 6. Two-Layer Presentation Model

The preferred presentation contract contains two layers.

### Layer A — Operational Summary

Displayed directly on the primary page.

It must answer at minimum:

- What is this?
- What is happening now?
- What should I understand immediately?

### Layer B — Contextual Knowledge

Accessible through a discoverable interaction such as:

- `What is this?`
- `Help`
- `Learn more`
- an information button;
- an equivalent interaction.

Layer B may contain:

- detailed definitions;
- pipeline relationships;
- parameter explanations;
- examples;
- limitations;
- consequences;
- canonical references.

Layer A must not become an unexplained technical dump merely because Layer B exists.

---

## 7. Parameter Explanation Contract

Every human-visible configurable parameter must expose, where applicable:

- canonical name;
- plain-language meaning;
- unit or scale;
- current value;
- allowed range or governed choices;
- effect of increasing the value;
- effect of decreasing the value;
- safety boundary;
- owning canonical specification.

A raw numeric value is not sufficient explanation.

For example, displaying a threshold such as `PRE = 70` is incomplete unless the human can understand what PRE represents and what the threshold generally controls.

---

## 8. Status Explanation Contract

Human-visible statuses must have stable semantic meaning.

This includes states such as:

- RUNNING;
- STOPPED;
- UNKNOWN;
- HEALTHY;
- DEGRADED;
- DEGRADED_SAFE;
- LIMITED;
- BLOCKED;
- WIDE_SCAN;
- FOCUS_MODE;
- WATCHLIST;
- CONFIRMED;
- LIVE_SENT;
- COOLDOWN;
- SHADOW;
- BROKER DISABLED.

The interface must distinguish:

- observed state;
- inferred state;
- unknown state;
- unavailable evidence.

`UNKNOWN` must not be displayed when sufficient canonical runtime evidence exists to determine the state.

When evidence is genuinely insufficient, the interface must make the uncertainty understandable.

---

## 9. Pipeline Explanation Contract

Pages representing pipeline components must expose their relationship to the larger operational system.

Human-facing explanations must remain aligned with active canonical architecture.

They must not invent simplified lifecycle semantics that contradict active canonical contracts.

Where implementation is undergoing controlled migration, the interface must not falsely present legacy behavior as completed canonical architecture.

---

## 10. Truth-Domain Separation

Human explanation must preserve the distinction between:

- runtime truth;
- market-data state;
- strategy evaluation;
- decision truth;
- FSM state;
- execution outcome;
- distribution truth;
- community feedback;
- objective market truth;
- analytics;
- research;
- governance authority.

Examples:

- Engine running does not mean trading is profitable.
- Distribution success does not mean the signal was profitable.
- A configured symbol does not mean a signal exists.
- Community feedback is not objective Market Truth.
- Analytics do not automatically have strategy authority.
- Research recommendations are not automatic canonical changes.
- Shadow operation is not live broker execution.

---

## 11. Role-Aware Explanation

Explanation visibility and operational authority are separate concerns.

A role may be allowed to understand a concept while being prohibited from changing it.

Contextual help must not expose:

- secrets;
- credentials;
- protected identities;
- restricted payloads;
- unauthorized operational information.

The interface must distinguish:

- knowledge visibility;
- operational visibility;
- mutation authority;
- governance authority.

---

## 12. Telegram Requirement

Telegram is a human presentation and interaction surface over the canonical control plane.

Every stable Telegram command page and interactive admin page must comply with this canon.

Coverage includes, where applicable:

- Home;
- Status;
- Operations;
- Engine;
- Strategy;
- Thresholds;
- SR / Corridor;
- Spike / instability filtering;
- Symbols & Coverage;
- WIDE / FOCUS;
- Decision Visibility;
- FSM;
- Distribution;
- Outcomes;
- Research;
- Analytics;
- Intelligence;
- Affiliate / Partner;
- Roles & Identity;
- Files;
- Reports;
- Documentation;
- Audit;
- Diagnostics;
- System Health;
- Recovery;
- Security;
- Governance.

---

## 13. Self-Explaining Navigation

Navigation labels must support comprehension and discovery.

Major branches must expose concise purpose descriptions.

Stable functionality must not depend on an authorized human remembering an undocumented slash command.

The Home surface must explain that it is the entry point into the Owner/operator control environment.

---

## 14. Canonical Knowledge Source Model

Explanatory content must not become scattered prose without ownership.

Implementation must provide a maintainable mapping conceptually equivalent to:

`surface/concept -> explanation -> canonical owner`

The exact software representation is implementation-defined.

However:

- duplicated definitions should be minimized;
- canonical ownership must be traceable;
- presentation text must not silently redefine behavior;
- material semantic changes require canonical review.

---

## 15. Drift Prevention

Incorrect explanation is more dangerous than sparse explanation.

Therefore:

1. explanatory content must be reviewed when owning canonical semantics change;
2. tests must verify explanatory coverage;
3. stable pages must not regress into unexplained technical dumps;
4. deprecated or superseded documents must not be presented as active authority;
5. observed runtime values must remain distinct from static definitions;
6. canonical references must remain traceable.

---

## 16. Required Acceptance Evidence

Implementation of this canon must eventually prove that:

1. every stable primary Telegram/admin page has a basic definition;
2. every stable primary page states its purpose;
3. every stable primary page exposes deeper contextual help;
4. important parameters have semantic explanations;
5. important statuses have semantic explanations;
6. governed concepts map to active canonical sources;
7. explanation visibility does not grant mutation permission;
8. help text does not expose secrets;
9. truth-domain boundaries remain explicit;
10. deprecated canon is not presented as active truth.

---

## 17. Owner Comprehension Acceptance

The final human acceptance criterion is:

> An authorized Owner who has forgotten previous project discussions must be able to open the control interface, understand what each major area is for, correctly interpret its important values and states, understand available controls and their consequences, and locate deeper canonical explanation without depending on historical chat memory.

This is an operational requirement.

It is not optional UX decoration.

---

## 18. Implementation Order

Implementation should proceed incrementally:

1. canonical knowledge registry;
2. common explanation rendering contract;
3. Home;
4. Operations and Engine;
5. Strategy and parameters;
6. SR / Corridor and instability filtering;
7. Symbols and WIDE / FOCUS;
8. Decision Visibility and FSM;
9. Distribution and Outcomes;
10. Analytics and Research;
11. Affiliate, Roles and Identity;
12. Files, Reports, Audit and Documentation;
13. System Health, Recovery, Security and Governance;
14. complete tree coverage audit.

Existing verified operational behavior must be preserved while explanatory coverage is added.

---

## 19. Non-Goals

This canon does not authorize:

- automatic broker execution;
- autonomous canonical strategy mutation;
- permission escalation;
- strategy redesign through UI prose;
- analytics reinterpretation;
- replacement of canonical specifications with Telegram text;
- exposure of secrets for educational purposes.

---

## 20. Canonical Rule

A human control surface is not complete merely because it displays state or executes commands.

It is complete only when an authorized human can correctly understand the meaning, purpose, current state, consequences, limitations, and canonical ownership of the capability being presented.
