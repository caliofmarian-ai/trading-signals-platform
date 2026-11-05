# Durable personal timing observation

Owner authorized continuous signal/timing work for up to two hours when needed.
Use a distinct explicit `OWNER_TIMING_SESSION_ID`, restricted by the existing
private Owner delivery / shadow / broker-disabled guards. First real strategy
evaluation starts a fixed two-hour wall-clock observation; its persisted deadline
survives restart and is never extended by an outage, missing opportunity or zero
sample. The earlier 4 November gate-timebox study is not reset or overwritten.

The bounded ledger stores aggregate decision/blocker counts, exact-stage accepted
**evaluation** counts (not unique trade counts), successful private publication
counts and up to 512 genuine API request-duration samples. Missing transport
samples remain unknown; internal OPEN acceptance is not actual delivery or an
outcome. Parameter hash drift pauses data collection without parameter mutation
or automatic calibration promotion. Scope remains personal research.

The existing telemetry worker sends a start notice, fifteen-minute progress
notices and a final two-hour summary to the same deployment Owner. Notification
slots are persisted before transport to avoid restart-induced resend loops.
Failures are observable; a reserved notice is not guaranteed phone receipt.
Reports preserve the statement that execution-expiry calibration is unproven.
They never publish test signals, change strategy parameters, enable a broker or
claim that the assistant is still running after the chat turn ends.

Private `/audit_runtime` includes the session status, start/deadline and aggregate
evidence. Measurement failure is isolated from the canonical strategy cycle and
logged with bounded, sanitized diagnostics. Existing real-price Model Time
research continues independently and cannot become approved execution expiry.

Validation: full local repository suite 2,081 passed in 38.83 seconds; final start
notice behavior additionally passed all five focused session tests. Regression
coverage includes fixed deadline/reimport, real zeroes and unknown percentiles,
accepted-versus-published separation, no late receipts, baseline drift pause,
notification dedup and disabled/broker-enabled/path-traversal scope rejection.
Required exact-head CI and actual Railway/Telegram session-start acceptance must
be verified before reporting this observation as active.
