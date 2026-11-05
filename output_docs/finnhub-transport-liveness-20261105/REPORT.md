# Finnhub transport liveness — 2026-11-05

## Purpose and authority

Repair the receiver's treatment of idle socket reads. The installed baseline
`b5ef444cd20f6d8aa0baaf34b5222a8497962a54` reconnects on every 30-second
`WebSocketTimeoutException`, without testing whether the WebSocket still responds.
A quiet stream is not by itself proof of failed transport. Production diagnostics
previously demonstrated 27 failures / 28 connection attempts and two M1 gaps with
five missing intervals. Those observations do not prove the origin of every gap.

This is a bounded implementation correction under active
`CANONICAL_MASTER_INDEX_v2.0.0.md`, `FAILURE_RECOVERY_SPEC_v2.0.1.md`,
`OBSERVABILITY_SPEC_v3.0.0.md`, and `DEPLOYMENT_PROTOCOL_v2.0.1.md`.
ALGO v3, Time Model v3, Signal Engine v3, Research v3 and the strategy/FSM
contracts retain their existing authority. Transport liveness does not establish
fresh quotes, contiguous history, an eligible opportunity, delivery, or profit.

## Intended delta

- Keep the existing 30-second connection handshake timeout and one subscription.
- Poll receiving at five seconds without disconnecting merely for an idle read.
- Send a WebSocket Ping every 20 seconds and require its matching Pong within
  ten seconds, measured with a monotonic clock. These are transport guardrails.
- Reconnect on missed Pong, close, protocol/provider error, or send failure.
- Let websocket-client handle protocol Ping replies and fragmented messages.
- Expose bounded, price-free transport evidence independently of quote evidence.
- Preserve the 10-second quote gate, minimum 201 contiguous real M1/M5 candles,
  provider, symbol, persistent candle format, strategy, FSM, distribution,
  calibration and expired research window.

The change cannot restore missed market data or guarantee an interruption-free
provider. No price bars are fabricated or backfilled.

## Pre-scan, backup and declared surfaces

The isolated worktree is based on the live main commit above, tree
`73d4ec3c0b324a0b165950113c95f214b2143760`. That immutable parent is the source
backup. The existing successful Railway deployment is
`d6b2e14c-a348-4995-8a26-2dd0b16adfba`.

Declared surfaces: `send/runtime/finnhub_market_data.py`, its stream test fixtures,
new transport regression tests, and this evidence package. No persistent runtime
file, configuration, service identity or variable is edited.

Production target: project `54752c90-3929-4854-9b50-049b5c63ab98`, production
`c8e55f1a-7518-4e7b-ae38-bad46b0a4171`, service
`c2c41294-4eca-4092-8cdf-94ba57511c6e`. Release via squash of the tested PR after
Required Repository CI succeeds on its exact head; retain the existing volume.

## Validation and acceptance

Offline tests must demonstrate quiet-but-responsive transport survival, matching
and missing/late/mismatched Pong, finite retries, send/close failures, fragmented
frames and automatic peer Ping replies, monotonic deadlines, and no promotion of
heartbeats into quote/history/recovery evidence. Run the relevant feed regressions
and full repository suite. Test results are software evidence only.

Deployment acceptance requires exact main/deployment provenance, SUCCESS, Online
1/1, restored real candle history, a fresh real tick, and observed matching Pong.
No production disconnect is induced. Sustained transport reliability and rebuilding
201 contiguous M1 candles remain prospective unless independently observed.
The timebox must remain TIMEBOX_COMPLETE at deadline 1793815500 with its frozen
2,452 evaluations and zero eligible observations.

Offline validation completed:

- 12 of the initial 13 transport cases failed against the unchanged baseline;
  the pinned-library fragmentation case already passed.
- The final 14 transport cases pass, including a partial-frame receive timeout.
- 52 focused feed/recovery/history tests passed in 0.62 seconds.
- Full repository regression: 2,012 tests passed in 62.18 seconds.
- Source compilation and `git diff --check` passed.

Current release status: exact-head GitHub CI and production acceptance PENDING.

## Rollback and evidence

If acceptance fails, revert only this patch to the backed-up source through the
same main/CI release path. Do not delete/replace candle, FSM or research state.
Record exact tested tree, PR/head CI, merge SHA, deployment ID, startup and transport
markers in the PR release evidence. Do not infer market performance from tests.

Primary implementation reference:
https://websocket-client.readthedocs.io/en/latest/core.html — `recv_data` with
`control_frame=True`, `ping`, automatic peer Ping replies and frame reassembly.
The pinned runtime dependency is websocket-client 1.9.2; its installed source is
checked during validation.
