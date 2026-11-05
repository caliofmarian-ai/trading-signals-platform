# Owner-requested severity comparison, 0–20

The Owner clarified on 5 November that level 0 must be permissive and level 20
the strictest, and asked for PRE, CONFIRM and OPEN_NOW frequency evidence. The
existing TPS sweep only filters already accepted OPEN research; it cannot test
whether a lower classical-score gate would admit more opportunities.

`scripts/analyze_signal_severity.py` therefore replays all chronological market
windows, including REJECT and NO_SIGNAL, independently at all 21 score settings.
Only copied score thresholds change. Data provenance, activity, noise, structural
availability/room, Model Time, Trade Physics and lifecycle rules remain the same.

The frozen research convention places the exact observed parameter bundle at
level 14. Levels 0–14 subtract `PRE*(14-level)/14` from all three thresholds;
levels 14–20 add `(100-OPEN)*(level-14)/6` to all three. The common offset is
rounded once to the nearest integer (ties to even), as required by the existing
parameter schema. This preserves stage gaps
and monotonically tightens each score requirement. With the current 70/75/80
bundle, level 0 is 0/5/10, level 14 is 70/75/80 and level 20 is 90/95/100.
The anchor is a documented comparison convention, not a previously calibrated
optimum or a prediction. Level 0 does not mean accepting invalid market data.

Every level uses the same real bounded Owner audit, closed M1/M5 bars only and
its own fresh chronological FSM. Reports separate requested score bands from
unique FSM-accepted stages, complete ordered lifecycles, stage gaps, hard gates
and errors. Lowering score cutoffs can skip a PRE band, so accepted lifecycle
counts need not increase monotonically. No fake prior PRE/CONFIRM is inserted.

Run `PYTHONPATH=send python -m scripts.analyze_signal_severity AUDIT.json`.
Input/candidate-bundle hashes identify the exact comparison. The command has no
publisher, runtime configuration writer or broker connection. It neither changes
the previous frozen research studies nor selects a production level. Historical
minute-close stage counts are preliminary evidence, not intrabar timing, expiry
calibration, efficacy, profitability, actual Telegram delivery or broker results.
Keep private quotes and raw audit files out of repository artifacts.

## Prospective live comparison

`intelligence/live_score_severity_research.py` also projects every genuine live
evaluation onto all 21 score settings. It reuses immutable Market/Corridor/Time
evidence and runs the existing scoring, decision assembly and a separate FSM per
level. It makes no extra market request. The production publication path runs
first; the isolated observer cannot replace its decision, params, handoff or
persisted production FSM. Exceptions produce bounded sanitized diagnostics.

Activation requires the existing Owner-private delivery opt-in, Shadow Mode,
broker execution off, existing model-time research opt-in, a valid explicit
Owner timing session ID and real Finnhub EUR/USD scope. The new evidence lives
in a separate `analytics/live_score_severity_research/<session>.json` ledger.
It starts a prospective two-hour comparison at first deployment observation;
it does not reset or extend the earlier Owner receipt observation ending
12:51:59 UTC. A restart preserves its own start/deadline and all 21 FSMs.
Parameter, strategy/spec or buffer-mode drift pauses the complete comparison.

All score requests, blockers and FSM reason families are counted separately.
First accepted research stages are deduplicated per opportunity; complete
ordered PRE/CONFIRM/OPEN chains retain bounded timing-gap samples. The private
projection also retains the latest 32 first-accepted PRE→CONFIRM, CONFIRM→OPEN
and PRE→OPEN intervals separately, including incomplete lifecycle chains. A
missing later stage is not imputed as zero seconds or discarded from counts.
The private
ledger retains at most 128 recent identities per level and the latest 32 full
chains' gaps; aggregate counters continue. At most 1 MiB is read/written.
Only an aggregate projection, with no identities or quotes, enters runtime
logs every 15 minutes and the existing exact-Owner audit. No messages are sent
to subscribers by this experiment. Completion remains research evidence and
does not set a winner, approve expiry or claim actual signal delivery.
