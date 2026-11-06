# Buffer at expiry — research objective contract V1

Status: active bounded research/measurement contract, 6 November 2026.
Owner authorization: install the remediation from the 5 November buffer audit.
Objective identity: `BUFFER_MET_AT_EXPIRY_V1`.
This is an observation/selection correction under the current canonical strategy,
not a second strategy, a change to its formulas or an execution authorization.

## Authority and meaning

The originating ALGO §5.1 defines the buffer as the minimum safety distance
between entry and projected expiry price, with BUY `expiry >= entry + B` and SELL
`expiry <= entry - B`. Provenance is retained in
`_deprecated/ALGO_SPEC.pre_time_model_20260313_144002.md`; it does not reactivate
superseded ATR/time formulas. Current authorities remain Master Index v2,
Trade Physics Model v1 (required space), Time Model v3 (feasibility), Risk v3 §18
(protection), Intelligence v1 §10 (distinct versioned outcome targets), and
Telemetry v3 §7.3 (directional WIN/LOSS/DRAW).

For this objective, **B is the favorable margin sought beyond the observed entry
at the evaluated expiry**. Reaching B earlier and maintaining B at expiry are
different labels. This contract measures only the latter. It never infers an
earlier touch or a guarantee from the feasibility calculation.

## Immutable observation

At the first accepted complete PRE → CONFIRM → OPEN_NOW research chain, copy
`DecisionObject.market_context.buffer_distance` into a versioned snapshot.
Record its source, original parameter hash, a snapshot SHA-256, the accepted
OPEN decision/audit identities per level, direction, stage times and horizons.
The ledger's OPEN timestamp is the snapshot's decision time. Identical entries
across levels share the same physical quote experiment; inconsistent B is rejected.
Later ATR, buffer mode or parameter changes cannot alter that snapshot. Existing
scope-drift gates remain in effect. A missing/invalid B is explicitly unavailable.

Entry and expiry quotes retain the existing real-stream identity, ten-second
entry allowance and zero-to-two-second post-expiry allowance. No new provider
request, interpolation or historical-price substitution is introduced.

For BUY `d = expiry - entry`; for SELL `d = entry - expiry`:

- `buffer_met_at_expiry = (d >= B)`, for frozen `B > 0`;
- `buffer_coverage = d / B`;
- `buffer_margin_at_expiry = d - B`.

Numeric policy `DECIMAL_SERIALIZED_INPUTS_NO_TOLERANCE_V1` uses exact decimal
representations of the persisted finite numeric inputs. There is no epsilon or
price rounding that can turn a shortfall into MET. Exact equality is MET for
both directions. Missing B or an ineligible/missing quote is UNAVAILABLE, never
MET or NOT_MET. The ordinary directional classifier remains unchanged.

## Prospective calibration and reporting

Existing records without snapshots stay byte-for-byte equivalent as record
objects, with their original identities, quotes and outcome labels. They remain
visible as `legacy_directional_only_entries` / `legacy_buffer_unavailable`;
current ATR/B is never used to fill them. Their old directional training results
cannot qualify a buffer proposal. New snapshot-bearing entries, including those
with unavailable B, form the prospective buffer cohort. The ledger start is
preserved; `buffer_collection_started_ts` records the new measurement start.

For every candidate and level, report directional WIN/LOSS/DRAW/UNKNOWN alongside
WIN with buffer MET, WIN with buffer NOT_MET, WIN with unavailable buffer, total
buffer MET/NOT_MET/UNAVAILABLE, coverage quantiles and distinct sample counts.
Raw prices, B and decision identifiers remain in private evidence.

Predeclare the existing Owner target **80%** for the explicitly stronger buffer
objective. This does not claim that canon previously supplied a buffer-specific
statistical threshold. Select on training buffer Wilson 95% lower bound, ties
toward less shortening. Keep the predeclared 60 training + 60 untouched holdout,
chronological nonoverlap, at least 30 decisive directional and 30 known-buffer
observations per split, at most 10% unknown for each target, and the 21-level
Bonferroni familywise correction. LOSS, DRAW and WIN below B all count as observed
buffer failures. Missing B/quotes count in buffer missingness instead of being
silently dropped; infeasible horizons remain separately excluded as before.

READY_FOR_REVIEW requires the fixed holdout's lower confidence bound to meet
80% for the buffer target as well as the existing directional and CONFIRM-interval
gates. Selection never consults holdout outcomes. Proposals bind this objective
identity, tested level/parameters and evidence digest. The existing 512-entry
capacity remains explicit; historical rows are not overwritten to make room.

## Release boundary

The minute-level `TSP_EXECUTION_EXPIRY_CALIBRATION` marker and private Owner audit
expose the new contract/counts. Collection stays continuously gated by the
existing private/shadow opt-ins. No threshold, lifecycle gate, active execution
calibration, destination, Telegram route, app service or broker is changed.
Synthetic tests prove the implementation's behavior. Real prospective observations
and an untouched holdout remain necessary to validate protection/efficacy.
