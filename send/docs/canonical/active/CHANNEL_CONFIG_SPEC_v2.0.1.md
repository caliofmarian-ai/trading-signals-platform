# CHANNEL_CONFIG_SPEC_v2.0.1.md

BinaryBot — Destination Configuration, Route Mapping & Delivery Parameter Specification  
Version: 2.0.1  
Status: PROPOSED COMPLETE PATCH SUCCESSOR — NOT ACTIVE CANONICAL  
Path: `send/docs/canonical/proposed/CHANNEL_CONFIG_SPEC_v2.0.1.md`  
Supersession Intent: `CHANNEL_CONFIG_SPEC_v2.0.0.md`

Linked Documents:
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- TELEGRAM_UX_v2.0.1.md
- ADMIN_CONTROL_SPEC_v2.0.1.md
- ADMIN_OPERATIONS_SPEC_v2.0.1.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md
- ADMIN_TREE_MAP_v2.0.1.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md

---

## 0. Patch status

Until explicit atomic promotion, `CHANNEL_CONFIG_SPEC_v2.0.0.md` remains active.

This v2.0.1 successor is a reference/terminology repair only. It preserves the route/destination configuration semantics of v2.0.0.

No route entitlement, destination limit, reset time, membership policy or strategy behavior is changed.

---

## 1. Purpose

This document defines the canonical configuration layer for governed signal destinations, entitlement routes and delivery parameters.

It centralizes distribution configuration without mixing it into:
- strategy logic;
- Trade Physics;
- DecisionObject/FSM logic;
- Telegram message formatting;
- route entitlement policy.

It governs:
- destination-to-route mapping;
- route configuration contract;
- route/tier parameterization;
- reset-related configuration references;
- outcome/feedback-capable route flags;
- membership-verification configuration baselines;
- admin-visible configuration-state expectations.

---

## 2. Configuration Layer Role

The configuration layer does not decide signal validity.

It provides parameter and mapping inputs needed by governed layers for:
- Distribution routing;
- Telegram publish targeting;
- entitlement counting configuration;
- route enable/disable behavior;
- outcome/feedback eligibility configuration;
- membership verification;
- admin and observability visibility.

Configuration is a supporting canonical layer, not business/strategy logic.

---

## 3. Canonical Configuration Entities

### 3.1 Route
A route is a governed entitlement path recognized by Distribution.

Baseline route family:
- FREE
- BASIC
- PRO
- ELITE

### 3.2 Destination
A destination is the concrete external publish target associated with a route.

### 3.3 Route mapping
A route mapping binds a canonical route to a concrete publish destination.

### 3.4 Route parameters
Configuration values may include:
- enabled/disabled status;
- daily OPEN_NOW limit;
- outcome/feedback capability;
- membership verification requirement;
- destination mapping.

### 3.5 Runtime route state
Runtime states remain:
- ACTIVE
- SILENT
- DISABLED

This document owns configuration-side inputs. Runtime state transitions remain Distribution-owned.

---

## 4. Baseline Route Family

Current canonical baseline remains:
- FREE
- BASIC
- PRO
- ELITE

These are governed entitlement routes, not merely channel labels.

Their:
- business meaning comes from distribution/economics policy;
- concrete external targets come from configuration;
- admin visibility comes from the admin/control layer;
- feedback/outcome capability must be explicit, not inferred from a name.

---

## 5. Destination Mapping Contract

Each publishable route must map to a valid destination.

Baseline Telegram key family remains acceptable:
- FREE_CHANNEL_ID
- BASIC_CHANNEL_ID
- PRO_CHANNEL_ID
- ELITE_CHANNEL_ID

Rules:
- destination IDs are not hardcoded in strategy logic;
- mappings load from governed persistent configuration;
- missing/invalid mappings create admin/observability visibility;
- a route without a valid mapping is effectively DISABLED for publishing;
- no false publish success or entitlement consumption may be recorded for an invalid mapping.

---

## 6. Delivery Targeting Configuration

Configuration supports routing of governed lifecycle candidates to one or more eligible routes.

Baseline expectation:
- PRE -> all ACTIVE eligible routes;
- CONFIRM -> all ACTIVE eligible routes;
- OPEN_NOW -> all ACTIVE eligible routes subject to route state/entitlement.

If route is SILENT or DISABLED:
- PRE blocked;
- CONFIRM blocked;
- OPEN_NOW blocked.

Candidate eligibility itself comes from upstream Signal Engine/FSM contracts; configuration does not create eligibility.

---

## 7. Daily OPEN_NOW Limit Parameters

Baseline values remain:
- FREE_LIMIT = 6
- BASIC_LIMIT = 20
- PRO_LIMIT = 50
- ELITE_LIMIT = UNLIMITED

Counting semantics belong to `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`.

Unchanged rules:
- PRE does not consume entitlement;
- CONFIRM does not consume entitlement;
- only successful OPEN_NOW publication consumes limited-route entitlement;
- unlimited routes do not ordinarily become SILENT through entitlement exhaustion.

---

## 8. Route Enablement / Disablement

Minimum config meanings:
- enabled + valid mapping -> route may become ACTIVE;
- enabled + invalid/missing mapping -> effectively DISABLED;
- explicitly disabled -> DISABLED.

Configuration does not set SILENT due to daily exhaustion.

```text
CONFIG/POLICY -> can enable or disable a route
RUNTIME DISTRIBUTION -> can silence an enabled route after governed exhaustion
```

---

## 9. Daily Reset Configuration Reference

Baseline reset reference remains:
- 08:10 Europe/London

Requirements:
- timezone explicit;
- DST handled by timezone, not fixed offset;
- reset reference inspectable by admin surfaces;
- runtime reset idempotent.

---

## 10. Reset Effect Expectations

At governed reset:
- limited-route counters return to zero;
- SILENT limited routes may return to ACTIVE;
- unlimited route behavior remains normal;
- config-disabled routes remain DISABLED;
- unmapped routes remain effectively DISABLED until mapping is valid.

---

## 11. Configuration Storage Principles

Configuration must persist across restarts.

Acceptable patterns include:
- JSON file;
- environment variables;
- secure configuration service;
- admin-controlled persisted source;
- another governed persistent mechanism.

Legacy example `config/channel_config.json` remains an implementation option, not canonical identity.

Hard requirements:
- deterministic load;
- persistence;
- invalid/partial config detectable;
- material config changes auditable.

---

## 12. Example Configuration Shapes

Legacy baseline shape remains acceptable:

```json
{
  "FREE_CHANNEL_ID": -1003510282695,
  "BASIC_CHANNEL_ID": -1003769019175,
  "PRO_CHANNEL_ID": -1003823255426,
  "ELITE_CHANNEL_ID": -1003776464915
}
```

An explicit route-first representation may be:

```json
{
  "routes": {
    "FREE": {
      "destination_id": -1003510282695,
      "enabled": true,
      "daily_open_now_limit": 6,
      "feedback_capable": false
    },
    "BASIC": {
      "destination_id": -1003769019175,
      "enabled": true,
      "daily_open_now_limit": 20,
      "feedback_capable": false
    },
    "PRO": {
      "destination_id": -1003823255426,
      "enabled": true,
      "daily_open_now_limit": 50,
      "feedback_capable": false
    },
    "ELITE": {
      "destination_id": -1003776464915,
      "enabled": true,
      "daily_open_now_limit": null,
      "feedback_capable": true,
      "membership_verification_required": true
    }
  },
  "reset": {
    "time": "08:10",
    "timezone": "Europe/London"
  }
}
```

Serialization shape may evolve; field meaning remains governed.

---

## 13. Admin Visibility Requirements

Authorized control surfaces should expose:
- route name;
- destination mapping status;
- configured daily limit;
- current runtime counter;
- route runtime state;
- feedback/outcome capability;
- reset reference;
- config validity.

Illustrative:
- FREE -> ACTIVE (2/6 today)
- BASIC -> ACTIVE (7/20 today)
- PRO -> ACTIVE (13/50 today)
- ELITE -> ACTIVE (unlimited)

Invalid configuration must not be presented as healthy.

Aligns with:
- `ADMIN_OPERATIONS_SPEC_v2.0.1.md`
- `ADMIN_CONTROL_SPEC_v2.0.1.md`
- `TELEGRAM_UX_v2.0.1.md`

---

## 14. Observability Requirements

Configuration-related material events must be observable, including as applicable:
- configuration loaded/invalid;
- mapping missing;
- route disabled by config;
- reset executed;
- route became SILENT;
- route reactivated;
- route publication result;
- route blocked by limit;
- transport failure;
- membership verification failure.

Exact event families must conform to:
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`

---

## 15. Feedback / Outcome-Capable Route Configuration

Capability must be explicit.

Baseline remains:
- ELITE is the feedback/outcome-capable route;
- other baseline routes are not unless policy changes canonically.

Capability:
- applies to OPEN_NOW where relevant;
- preserves signal identity;
- follows truth/source rules from Outcome and Community Feedback;
- remains inspectable by admin surfaces.

Aligns with:
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`

---

## 16. ELITE Membership Verification Baseline

Before accepting protected ELITE feedback or returning protected personal statistics, current entitlement must be verified.

Telegram `getChatMember` remains a valid baseline mechanism while Telegram is the surface.

Baseline accepted statuses:
- member
- administrator
- creator

Rejected/non-entitled baseline statuses include:
- left
- kicked
- restricted where not entitled.

If verification fails:
- protected feedback rejected;
- private stats not returned;
- failure surfaced appropriately.

This document governs configuration dependency; detailed user/truth behavior belongs to Community Feedback / Outcome contracts.

---

## 17. Bot Permission Baseline

The bot must have sufficient destination permissions to perform required membership checks.

If permissions are insufficient:
- dependent ELITE functions become degraded/restricted;
- admin/observability evidence is required;
- system must not claim successful verification capability.

---

## 18. Privacy Expectations

Configuration/membership checks must respect:
- no public raw user IDs;
- personal stats only through authorized private surfaces;
- no cross-user private statistics;
- aggregate analytics only to authorized roles;
- protected secrets/mappings not exposed in user-facing output.

---

## 19. Failure Modes

Must safely handle:
- missing/malformed destination ID;
- disallowed duplicate mapping;
- accidental publish attempt to disabled route;
- stale config after restart;
- invalid reset reference;
- feedback-capable route without verification support;
- membership permission failure.

Expected behavior:
- fail visibly;
- no fake health;
- no false delivery count;
- no access bypass.

---

## 20. Configuration Guarantees

Correct implementation guarantees:
- deterministic destination resolution;
- separation of strategy truth from delivery mapping;
- predictable route-limit parameterization;
- admin-visible config truth;
- restart-safe persistent configuration;
- explicit feedback/outcome capability;
- explicit membership-verification dependency;
- observable configuration failure.

---

## 21. PATCH Migration Note

v2.0.1 preserves all v2.0.0 functional configuration semantics.

Changes are limited to:
- final canonical references to v3 structural successors and v2.0.1 adjacent PATCH successors;
- candidate-oriented wording consistent with staged execution;
- outcome/feedback wording consistent with multi-truth Outcome/Community Feedback v3;
- version/path/history metadata.

Unchanged:
- route family;
- destination mapping baseline;
- FREE/BASIC/PRO/ELITE limits;
- 08:10 Europe/London reset reference;
- SILENT/DISABLED meanings;
- ELITE membership-verification baseline;
- privacy expectations.

---

## 22. Version History

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH: canonical cross-reference repair and vocabulary alignment; no configuration-policy change. |
| 2.0.0 | 2026-07-12 | Active canonical governed route/destination configuration specification. |

---

End of CHANNEL_CONFIG_SPEC_v2.0.1.md