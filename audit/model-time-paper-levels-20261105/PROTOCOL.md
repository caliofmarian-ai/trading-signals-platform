# Market-derived paper trades at severity levels 0–20

Change ID: `20261105-MODEL-TIME-PAPER-01`. Prospective research protocol
`LIVE_SCORE_SEVERITY_RESEARCH_V2`, with ledger `CANONICAL_MODEL_TIME_PAPER_V1`.
Owner instruction: simulate transactions according to the canon, choosing
opportunities and time from indicators and real market conditions; no broker
connection is needed for this work. This is a research instrumentation change,
not a canonical strategy, commercial distribution or execution-calibration promotion.

## Opportunity and stage policy

All 21 levels consume the same immutable, real Finnhub EUR/USD market,
corridor, directional-speed, Model Time and Trade Physics evidence. Only the
existing classical score thresholds vary by level. All structural, time,
instability, physics, focus, cooldown and canonical FSM checks remain required.

V1 requested the highest score band immediately. At permissive levels this
could repeatedly request OPEN_NOW without a PRE, leaving those levels unable
to establish lifecycle continuity. V2 prospectively caps the requested stage
before DecisionObject construction: PRE first, then CONFIRM, then OPEN_NOW
after at least 30 seconds from the first accepted PRE. It never promotes a
score that cannot afford that stage. The FSM still owns acceptance. A changed
direction cannot promote the prior direction's chain. Score components,
thresholds, Model Time, hard blockers and the production default assembly
behavior are preserved. This common lifecycle policy is explicitly part of
the V2 experiment; V1 and V2 stage counts must not be pooled.

## Automatic simulation duration

An exact-stage accepted OPEN_NOW after an ordered chain registers one paper
opportunity per level/signal identity. READY structure, time and physics and
matching decision/audit/FSM lineage are mandatory. No ExecutionCalibration
file is required, because this is a Model Time experiment.

The duration is fixed prospectively from that opportunity's canonical
`model_expiry * 60`, without additional rounding. The existing Time Model
already derives it after corridor construction from required movement,
recency-weighted intended-direction M1 speed, trend/structure adjustments and
versioned horizon limits. Duration therefore changes with market evidence;
it is not a fixed five-minute simulation. This experiment does not invent a
pressure multiplier or present Model Time as calibrated trader-facing
Execution Time. Every ledger retains decision/audit/FSM references, direction,
adjusted travel time, chosen model horizon and raw entry/expiry observations.

## Prospective settlement and persistence

Entry is the first processed fresh, real, same-provider stream tick at or after
registration, within ten seconds. The expected endpoint is the observed entry
timestamp plus the locked duration. Settlement uses a fresh real tick at/after
that endpoint, at most two seconds late. Tick age is also limited to two
seconds. The existing cached stream sample is read once per worker iteration,
shared across levels; there are no additional market API requests.

BUY compares expiry price to entry; SELL reverses the comparison. Equality is
DRAW. Missing/stale/future/malformed/historical/cross-provider evidence, provider
changes, or missed endpoints yield UNKNOWN. There is no backfill or retrospective
selection of a winning expiry. Finalized records are semantically immutable,
validated against retained quotes before reading, and never removed to make room.

The existing atomic research state now contains a separate ledger for each
level, bounded at 64 opportunities per level and 4 MiB total. Capacity exhaustion
is explicit; prior evidence is preserved. V2 uses a new directory, preserving
all V1 files. Collection has a fixed two-hour window, survives restarts, pauses
new decisions on baseline drift, and cannot silently extend itself. Registered
paper trades continue settlement after collection closes or baseline drift;
SETTLING remains visible until all are final. Storage/observation errors are
isolated from production decisions and distribution.

## Evidence and release

The exact Owner audit now includes per-level WIN/LOSS/DRAW/UNKNOWN, pending,
decisive count, chosen-duration histogram and a separately labeled hypothetical
win rate. Public operational logs contain aggregates, never raw prices or
identities. These are correlated paired paper observations, not independent
performance proof or P&L. This change does not select a production severity,
publish research signals, create a broker connection or claim calibrated
Execution Time. Existing shadow-mode opt-ins remain required.

Release requires focused offline tests, the complete repository suite,
exact-head CI and observed Railway SUCCESS. Git history retains the preceding
source `7fe4c1778bad732b3ccf880206322bd604a165c0`; existing preboot evidence checkpoint
and state-preservation behavior remains in force. Rollback is to that deployed
build; V2 evidence is retained. Live acceptance must report actual new V2
evaluations, registrations, durations and settlements rather than infer them
from a passing offline test.
