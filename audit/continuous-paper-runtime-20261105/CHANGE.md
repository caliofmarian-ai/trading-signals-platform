# Continuous paper observation and timing monitoring

Owner clarification, 2026-11-05: two hours was a deadline for the assistant's
work, not a simulator lifetime. PRE / CONFIRM / OPEN_NOW processing and paper
outcome observation must continue while the service runs.

The main engine already loops every two seconds. The accidental two-hour
cutoffs were in the severity paper observer and the supplemental Owner timing
monitor. Both now use stable runtime state, without a session identity or an
automatic stop. Reporting intervals control notifications only.

The first read continues the installed V2 paper state and V1 timing state when
the old session identity points to valid persisted evidence. Original files are
preserved byte for byte. Pending expiries, locked Model Time horizons, FSM
histories, counters and the original start time carry forward. Subsequent
restarts and changes to the old diagnostic session identity cannot reset them.

Finalized paper records move into immutable, numbered per-level archives before
hot state is reclaimed. Raw entry/expiry quotes and decision/FSM references stay
in those archives; cumulative outcome totals stay in the runtime checkpoint.
An archive written before an interrupted checkpoint commit is recovered exactly
once. A failed archive write cannot discard the live checkpoint. Pending trades
never move, and capacity now bounds concurrent/unarchived trades rather than
the lifetime number of opportunities. Duration histograms explicitly describe
unarchived trades; exact older durations remain in the archives.

The existing rules for fresh provider evidence, exact-stage FSM acceptance,
ordered stages, PRE lead time, stable comparison parameters and explicit
UNKNOWN outcomes remain in force. A parameter/buffer/specification change still
pauses the comparison to avoid mixing baselines; that does not pause the main
strategy loop. This change does not select a production severity, change the
execution-expiry contract or create Telegram publication evidence. These remain
paper observations and genuine delivery timing respectively.

Validation requires the focused continuity, migration and recovery tests, the
full repository suite, exact-head required CI and observed Railway SUCCESS.
Production acceptance must distinguish a running continuous observer from
actually completed paper trades or actually published signal stages.

Rollback source: preceding main commit
`2274352ed6c64da21edaf07571454f771001ed81`. Legacy state remains preserved, but
rolling back the observer would restore its old time limit and would not settle
trades first registered in the newer continuous checkpoint. Retain continuous
state and archives for recovery; do not delete evidence during rollback.
