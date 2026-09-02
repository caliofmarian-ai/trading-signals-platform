# R-012 — Strategy Profile Reconciliation

Status: IMPLEMENTED ON REMEDIATION BRANCH — VALIDATION PENDING
Issue: #120
Parent: #97
Base main commit: `dd04a64506e5b62b98f9b885a01414b1e2b0ac8d`

## Canonical determination

The active canonical Master Index identifies `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` as the governed parameter-control authority. That authority does not define the legacy named production profiles `CONSERVATIVE`, `BALANCED`, or `AGGRESSIVE`, and it explicitly forbids inventing production ranges merely to make a control available.

The legacy profile bundles were therefore not promoted into v3 authority. They are disabled rather than reinterpreted or assigned invented replacement values.

Active SR v3 defines Trade Physics v1 `required_space = buffer_distance`. The current Corridor runtime already prevents legacy `sr_required_multiplier` from tightening or relaxing the hard structural-feasibility gate. R-012 therefore removes the obsolete profile write path instead of attempting to preserve old SR profile semantics.

## Reconciliation

- live named profile bundle registry is empty;
- authorized profile requests fail closed, are audited as rejected, and do not write strategy configuration;
- the Telegram Strategy Profile surface remains visible but read-only and says named profiles are not available;
- new Telegram markup exposes no legacy profile mutation button;
- stale `PROFILE_CONFIRM:*` callbacks recover safely without displaying legacy parameter bundles;
- stale `PROFILE_EXEC:*` callbacks route to the fail-closed audited handler and cannot mutate `algo_params.json`;
- existing direct parameter-control behavior is outside the R-012 scope and is not broadened or redesigned here.

## Safety boundary

R-012 does not lower score thresholds, define new strategy presets, change SR/Trade Physics formulas, change provider selection, alter FSM/execution timing, enable distribution, or enable broker execution.
