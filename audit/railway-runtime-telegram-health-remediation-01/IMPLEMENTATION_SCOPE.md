# IMPLEMENTATION_SCOPE

## In scope
- Canonical Telegram command restoration and unsupported-command reply behavior.
- Reply-context routing fixes.
- Startup/recovery/operator notification wiring in the active Railway runtime.
- Critical-error and Twelve Data 429 Telegram escalation with aggregation and recovery.
- Observability error-shape hardening and log-failure bounding.
- Admin-proof Telegram reconnection.
- Focused regression tests and remediation documentation.

## Explicitly out of scope
- Broker execution implementation.
- Pocket Option integration.
- Paper trading.
- Strategy parameter, gate, WIDE SCAN, or FOCUS MODE logic changes.
- Normal market-data cadence changes while the provider is healthy.
- Legacy sidecar/runtime restoration.
