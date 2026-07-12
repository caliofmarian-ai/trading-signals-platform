# CHANNEL_CONFIG_SPEC_v2.0.0.md

BinaryBot — Destination Configuration, Route Mapping & Delivery Parameter Specification  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/CHANNEL_CONFIG_SPEC_v2.0.0.md

Linked Documents:
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- ADMIN_TREE_MAP_v2.0.0.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 1. PURPOSE

This document defines the canonical configuration layer for governed signal destinations, entitlement routes and delivery parameters.

It exists to centralize the configuration needed by the distribution layer without mixing it into:
- strategy logic
- decision scoring
- market interpretation
- FSM internals
- Telegram message formatting logic

This document governs:
- destination-to-route mapping
- route configuration contract
- tier/route parameterization
- reset-related configuration references
- outcome-capable route flags
- membership verification configuration baselines
- admin-visible configuration state expectations

This specification replaces the older “channel tier config” framing with a more general governed route and destination configuration model.

---

## 2. CONFIGURATION LAYER ROLE

The configuration layer does not decide whether a signal is valid.

It provides the parameter and mapping inputs required so that other governed layers can act correctly.

It supports:
- distribution routing
- Telegram publish targeting
- entitlement counting configuration
- route enable/disable behavior
- outcome eligibility configuration
- membership verification baselines
- admin and observability visibility

Therefore configuration is a supporting canonical layer, not business logic itself.

---

## 3. CANONICAL CONFIGURATION ENTITIES

### 3.1 Route
A route is the canonical governed entitlement path recognized by the distribution layer.

Current baseline route family:
- FREE
- BASIC
- PRO
- ELITE

### 3.2 Destination
A destination is the concrete Telegram publish target associated with a route.

### 3.3 Route mapping
A route mapping binds a canonical route to a concrete publish destination.

### 3.4 Route parameters
Route parameters are configuration values governing route behavior such as:
- enabled/disabled status
- daily OPEN_NOW limit
- outcome capability
- membership verification requirement where applicable

### 3.5 Runtime route state
Runtime route state includes values such as:
- ACTIVE
- SILENT
- DISABLED

These states are partly configuration-driven and partly runtime-driven.
This document defines the config side of the contract.

---

## 4. BASELINE ROUTE FAMILY

The current canonical baseline route family remains:

- FREE
- BASIC
- PRO
- ELITE

These remain the distribution product routes recognized by the system.

However, v2.0.0 treats them as governed entitlement routes rather than merely channel-tier labels.

That means:
- their business meaning comes from the distribution layer
- their concrete Telegram delivery targets come from configuration
- their admin visibility comes from the admin/control layer
- their outcome capability is explicitly governed rather than implied by naming alone

---

## 5. DESTINATION MAPPING CONTRACT

Each governed route must map to a valid Telegram destination if it is intended to publish.

Baseline mapping family inherited from the legacy model:

- FREE_CHANNEL_ID
- BASIC_CHANNEL_ID
- PRO_CHANNEL_ID
- ELITE_CHANNEL_ID

These names remain acceptable baseline configuration keys for now, even though the conceptual model is now route-first rather than channel-first.

Mapping rules:
- destination IDs must not be hardcoded into strategy logic
- destination IDs must be loaded from configuration during startup or controlled refresh
- invalid or missing destination IDs must create admin/observability visibility
- a route with no valid destination mapping is effectively DISABLED for publishing

If a route is effectively DISABLED due to missing mapping:
- it receives no signals
- it consumes no entitlement
- it must not report false delivery success

---

## 6. DELIVERY TARGETING CONFIGURATION

Configuration must support routing of governed lifecycle stages into one or multiple eligible routes.

Baseline routing expectation remains:

- PRE → all ACTIVE eligible routes
- CONFIRM → all ACTIVE eligible routes
- OPEN_NOW → all ACTIVE eligible routes, subject to entitlement and route state

If a route is SILENT:
- PRE blocked
- CONFIRM blocked
- OPEN_NOW blocked

If a route is DISABLED:
- PRE blocked
- CONFIRM blocked
- OPEN_NOW blocked

This preserves the canonical guarantee that a route never receives partial lifecycle visibility after exhaustion or disablement.

---

## 7. DAILY OPEN_NOW LIMIT PARAMETERS

Daily route limits are configuration parameters attached to limited routes.

Baseline values inherited from the legacy canonical version:

- FREE_LIMIT = 6
- BASIC_LIMIT = 20
- PRO_LIMIT = 50
- ELITE_LIMIT = UNLIMITED

Canonical counting semantics are governed by `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`, but the parameter values themselves belong to the config layer.

Important:
- PRE does not consume entitlement
- CONFIRM does not consume entitlement
- only successful OPEN_NOW publish consumes entitlement on limited routes
- unlimited routes do not ordinarily become SILENT through entitlement exhaustion

These values may later become admin-governed configurable values, but until superseded they remain the baseline configuration reference.

---

## 8. ROUTE ENABLEMENT / DISABLEMENT PARAMETERS

Each route must expose configuration-level enablement semantics.

Minimum expected config meanings:
- enabled and correctly mapped → route can become ACTIVE at runtime
- enabled but unmapped/invalid → route becomes effectively DISABLED
- disabled by config/policy → route is DISABLED

Configuration alone does not set a route to SILENT for daily exhaustion.
SILENT is a runtime distribution state caused by governed entitlement logic.

Therefore:

```text
CONFIG/POLICY → can enable or disable a route
RUNTIME DISTRIBUTION → can silence an enabled route after exhaustion
```

This separation is important and must remain clear in admin UX and operational reasoning.

---

## 9. DAILY RESET CONFIGURATION REFERENCE

The baseline reset reference inherited from the legacy canonical model remains:

- 08:10 Europe/London

This is the configuration reference point for daily route-limit reset behavior.

Configuration requirements:
- timezone reference must be explicit
- DST handling must rely on the timezone, not fixed offsets
- reset reference must remain inspectable by admin surfaces
- reset execution must remain idempotent at runtime

The reset mechanism itself belongs to runtime/distribution behavior, but the configured reference belongs here.

---

## 10. RESET EFFECT EXPECTATIONS

At the governed daily reset reference:
- limited route counters return to zero
- SILENT limited routes may return to ACTIVE
- unlimited routes remain operationally normal
- config-disabled routes remain DISABLED
- unmapped routes remain effectively DISABLED until valid mapping exists

The old intuition that all tier counters reset daily remains valid, but v2.0.0 distinguishes:
- route configuration
from
- route runtime state
more explicitly.

---

## 11. CONFIGURATION STORAGE PRINCIPLES

Configuration must live in a persistent source that survives restarts.

Acceptable storage patterns may include:
- JSON configuration file
- environment variables
- secure configuration service
- admin-controlled persisted config source
- other governed persistent configuration mechanisms

Legacy example location remains acceptable as an implementation pattern:

`config/channel_config.json`

However, the conceptual truth is not tied to any one file name.

Hard requirements:
- configuration must survive restart
- configuration must be loadable deterministically
- partial or invalid configuration must be detectable
- configuration source changes must be auditable where operationally important

---

## 12. EXAMPLE CONFIG SHAPE (BASELINE)

A legacy-style baseline shape remains acceptable:

```json
{
  "FREE_CHANNEL_ID": -1003510282695,
  "BASIC_CHANNEL_ID": -1003769019175,
  "PRO_CHANNEL_ID": -1003823255426,
  "ELITE_CHANNEL_ID": -1003776464915
}
```

A more explicit v2-style conceptual shape may evolve toward something like:

```json
{
  "routes": {
    "FREE": {
      "destination_id": -1003510282695,
      "enabled": true,
      "daily_open_now_limit": 6,
      "outcome_capable": false
    },
    "BASIC": {
      "destination_id": -1003769019175,
      "enabled": true,
      "daily_open_now_limit": 20,
      "outcome_capable": false
    },
    "PRO": {
      "destination_id": -1003823255426,
      "enabled": true,
      "daily_open_now_limit": 50,
      "outcome_capable": false
    },
    "ELITE": {
      "destination_id": -1003776464915,
      "enabled": true,
      "daily_open_now_limit": null,
      "outcome_capable": true,
      "membership_verification_required": true
    }
  },
  "reset": {
    "time": "08:10",
    "timezone": "Europe/London"
  }
}
```

This document does not require a specific serialized structure yet, but it defines the canonical meaning of the fields.

---

## 13. ADMIN VISIBILITY REQUIREMENTS

Authorized admin/control surfaces must be able to inspect current route configuration truth.

Expected visible values include:
- route name
- destination mapping status
- configured daily limit
- current runtime counter
- route runtime state
- outcome capability
- reset reference
- config validity status

Illustrative admin output:

- FREE → ACTIVE (2/6 today)
- BASIC → ACTIVE (7/20 today)
- PRO → ACTIVE (13/50 today)
- ELITE → ACTIVE (unlimited)

If a route is invalidly configured, admin views should expose that clearly rather than pretending the route is healthy.

This aligns with:
- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`
- `TELEGRAM_UX_v2.0.0.md`

---

## 14. OBSERVABILITY REQUIREMENTS

Configuration-related events must be observable.

Examples of events that should be logged:
- configuration loaded
- configuration invalid
- destination mapping missing
- route disabled by config
- reset executed
- route became SILENT
- route reactivated on reset
- signal delivered to route
- signal blocked by limit
- Telegram publish failure
- membership verification failure due to permission/config problem

These events belong in operational observability and should align with:
- `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`

---

## 15. OUTCOME-CAPABLE ROUTE CONFIGURATION

Outcome capability must be treated as an explicit route property, not as an accidental side-effect of a route name.

Current baseline inherited from the legacy model:
- ELITE is outcome-capable
- other baseline routes are not outcome-capable

Outcome-capable route config expectations:
- applies only to OPEN_NOW lifecycle stage
- must preserve governed signal identity linkage
- must align with outcome tracking rules
- should be inspectable in admin/control surfaces

This domain aligns with:
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`

---

## 16. ELITE MEMBERSHIP VERIFICATION BASELINE

The legacy document defined a correct baseline rule:
before accepting outcome feedback or returning private personal statistics, the system must verify that the requesting Telegram user is a member of the ELITE destination.

That baseline remains valid in v2.0.0.

Canonical baseline verification method:
- Telegram API membership lookup against the configured ELITE destination

Allowed baseline statuses:
- member
- administrator
- creator

Rejected baseline statuses:
- left
- kicked
- restricted

If membership verification fails:
- outcome feedback must be rejected
- private personal statistics must not be returned
- the user should receive an explanatory private message where the product flow requires it

This document defines the configuration baseline and destination dependency for that rule.
The detailed access behavior belongs with outcome and distribution governance.

---

## 17. ELITE BOT PERMISSION BASELINE

The bot must have sufficient permissions on the ELITE destination to perform membership verification.

Baseline requirement inherited from the legacy document:
the bot should be administrator on the ELITE destination with enough access to verify member status reliably.

If permissions are insufficient:
- outcome-dependent ELITE features become operationally degraded
- a critical admin/observability event must be emitted
- the system must not falsely claim successful verification capability

This requirement may later be generalized for any outcome-capable private route, but ELITE remains the baseline case for now.

---

## 18. PRIVACY EXPECTATIONS

Configuration and membership checks must respect privacy boundaries.

Rules:
- Telegram user IDs must not be exposed publicly in channels
- user-level statistics must be delivered only through authorized private paths
- one user must never access another user’s personal statistics
- aggregated analytics may be visible only to properly authorized admin roles

This document does not define the full privacy model, but route configuration and membership verification must not violate it.

---

## 19. FAILURE MODES

Configuration must safely handle at least the following failure modes:
- missing destination ID
- malformed destination ID
- duplicate destination mapping where disallowed
- disabled route published accidentally
- stale config after restart
- invalid reset reference
- outcome-capable route without membership-verification support
- permission failure during ELITE membership check

Canonical expected behavior:
- fail visibly
- do not fake health
- do not count false deliveries
- do not silently bypass access rules

---

## 20. CONFIGURATION GUARANTEES

If implemented according to this specification, the configuration layer guarantees:
- deterministic destination resolution
- separation between business logic and delivery mapping
- predictable route-limit parameterization
- admin-visible configuration truth
- safer restart behavior
- explicit outcome-capable route semantics
- explicit ELITE membership-verification dependency
- operationally visible configuration failures

---

## 21. MIGRATION NOTES FROM LEGACY VERSION

The legacy CHANNEL_CONFIG_SPEC correctly established:
- per-tier destination IDs
- no hardcoding in strategy logic
- missing mapping means no delivery
- daily limits as configuration values
- reset reference at 08:10 Europe/London
- admin visibility of counters and state
- ELITE membership verification baseline
- privacy expectations around personal stats

However, it was framed too narrowly as a simple Telegram tier config document.

This v2.0.0 specification preserves the useful invariants while upgrading the model into a broader canonical configuration layer centered on:
- governed routes instead of only flat channel tiers
- clearer separation between config and runtime state
- explicit outcome-capable route properties
- explicit membership-verification dependencies
- stronger alignment with the distribution, admin and Telegram UX canonical stack

---

End of CHANNEL_CONFIG_SPEC_v2.0.0.md
