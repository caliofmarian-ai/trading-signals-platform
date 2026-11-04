# Local validation — 2026-11-04

Base main: `023f6e54ec2bfd25ce21da6005f88f659f5611a6`.

The seven new integration cases first failed on the unchanged implementation: four actual-writer cases reproduced the exact production strict-schema exception, and three `run_once` cases proved the execution events disappeared before routing.

After the repair:

- Focused lineage, distribution, calibration, execution-gate and event-schema regression: **78 passed in 4.67 s**.
- Full repository suite: **1,872 passed in 58.02 s**.
- Diff check and Signal Engine compilation: passed.
- PRE, CONFIRM, calibrated OPEN_NOW and uncalibrated OPEN_NOW event construction use the real logger and strict schema. No schema rule is weakened.
- Actual `run_once` fixture tests preserve canonical DecisionObject/strategy identity, FSM identity, pre/post attempt identity and distinct event IDs. Real Finnhub routing still blocks publication; its expected WARNING is distinct from an engine ERROR. Missing execution calibration still blocks OPEN_NOW before routing. Test-only inputs are not live market opportunities.
- The existing publication-success fixture now supplies the identity fields required by the actual execution contract and checks their persisted locations. Publication evidence remains required for EMITTED.

Private pre-repair runtime audit generated `2026-11-04T08:24:15Z`: SHA-256 `bff8d54b89368d7a62ee2a4de39a821be630594001e086b08c5c1a53e9fb0236`. Latest bounded decision cohort: 50 rows from 08:22:03.140Z through 08:23:56.570Z, all REJECT; activity blocker 50, structural and time blockers 41 each. These are correlated evaluations over a short interval, not independent trades, strategy failure rates or performance labels. Raw audit data, market quotes and private identifiers are not committed.

Required exact-head CI and post-deployment proof are recorded on the PR after publication. Neither passing tests nor this fix establish live manual signal delivery, approved calibration, broker compatibility or profitability. #208/#217 remain open.
