# Restore normalized activity and expose timing readiness

Change: OWNER-SIGNAL-TIMING-20261105. Owner explicitly confirmed all necessary
signal-delivery and timing-calibration operations on 5 November 2026. Broker
execution remains disabled. This record covers source correction and research;
it does not declare a numeric execution calibration empirically validated.

The Owner-attached ALGO v2 §27 and the repository's absorbed v2 rule require
normalized activity whenever adaptive scale is available. The v3 ALGO successor
omitted the detailed restatement while telemetry v3 §18 retained normalized
activity observability. The retained intake gives `avg_range / atr_reference`
with initial ratio 0.20. The runtime instead used a fixed 0.00025 EUR/USD floor.
Restore the already absorbed rule in Market Model and restate its concrete
initial semantics in active ALGO v3 §6.1. Existing ten-bar M1 decision range and
M5 ATR(14) remain the windows. No new authority file, tunable knob, weight, score
threshold, corridor, speed, Time Model formula or lifecycle bypass is added.

Read-only real-data replay at the current parameter bundle, using only bars
closed before each historical cutoff, evaluated 479 windows. The fixed floor
blocked activity in 477 and produced no accepted stages. Normalized activity
produced 14 unique PRE, 2 CONFIRM and 4 model-ready FSM-accepted OPEN opportunities;
other noise/structure/time blockers still applied. These are retrospective,
minute-resolution research observations, not live messages, broker settlements,
win rate or calibrated expiry evidence. Replays also expose out-of-order stage
observations separately; having all stage labels is not proof of an ordered chain.

Offline tooling performs no network, publication, parameter mutation or model
activation. Its insufficient-sample result must remain unavailable rather than
creating an APPROVED calibration file. Runtime private timing receipts establish
Telegram API acceptance only, not phone receipt. The first real activation
receipt after PR #229 was visible in the Owner's bot conversation at 10:30 UTC;
API request duration was 0.089365 seconds.

Personal visible-order policy additionally requires an actual successful PRE
receipt before CONFIRM, and successful PRE and CONFIRM receipts before OPEN_NOW.
The Owner's standing minimum PRE advance is 30 seconds, measured from first
successful private PRE API acceptance. Missing receipts, invalid time order or
insufficient advance block private publication. A subsequent attempt must still
pass a new full live evaluation; no old candidate is queued for delayed replay.
This is a stricter personal delivery gate, not creation or promotion of a
strategic stage. Public routes are unaffected and Finnhub redistribution remains
blocked. Final local full-suite validation: 2,076 tests passed in 38.69 seconds.

Validation: scale invariance across asset units; low absolute but normal
relative activity; real relative inactivity; exact evidence fields; original
noise/structure/time/expiry gates; chronological replay and no future M5 leakage;
full repository CI on the exact change commit. Rollback: revert the runtime
restoration commit; no persistent parameter rewrite is performed. Monitor real
decision activity ratio, blocker families, stage receipts and timing readiness.
