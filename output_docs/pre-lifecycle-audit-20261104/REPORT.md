# PRE lifecycle audit and diagnostic root-cause corrections — 2026-11-04

## Problem and canonical basis

`/audit_runtime` exports a bounded engine tail and signal-execution attempts,
but does not read the canonical `fsm_transition` sink. A REJECT or maintenance
event can close an accepted PRE without producing a signal-execution attempt.
Consequently, the existing audit cannot identify that closure.

Active authority is `send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md`.
Relevant requirements are FSM Decision Engine v2 sections 6, 16–17 and 21,
Observability Logging v3 section 7, Event Schema v3 section 10 and Deployment
Protocol v2.0.1 patch-deployment discipline. This is an export correction within
those contracts, not a strategy or lifecycle-policy change.

## Code baseline and reproduction

Public code baseline: `7d5f4150ba38d59dd34661398768473688f7a4cb`, tree
`6ad7be0b2f356d64825ba3f4833f286b4121536e`.

Code inspection confirms that the event schema routes `fsm_transition` to the
FSM sink while the existing audit reads only engine, admin and error sinks.
The regression fixture reproduces an accepted PRE followed by an explicit
REJECT closure and repeated cooldown observations. The fixture contains only
test data. Runtime audits, signal observations, deployment identifiers and
other non-public production metadata are excluded from this report.

## Change

The audit correction changes `send/core/admin_commands.py`, its audit tests and
this evidence report. The private command reads the configured `FSM_EVENTS_LOG`,
or the FSM file under `OBS_DIR`, with the existing 5,000-record / 16 MiB bounds.

It exports the latest 50 FSM observations and separately the latest 50 actual
state changes found inside that same bounded source window. Original event
envelopes, timestamps and decision/signal identities are preserved. Source
status, limits, retained interval, matching count and export truncation are
explicit. Missing, malformed or out-of-window evidence does not establish that
no lifecycle event occurred.

The existing permission check executes before every evidence read. There are
no modifications to strategy thresholds, FSM transitions, providers, delivery
policy, calibration, broker execution or the completed research deadline.

## Additional diagnostic causes reproduced and corrected

### Addressed Telegram commands

The dispatcher strips the `@bot` suffix to recognize and authorize an admin
command, but passed the original text to the downstream admin parser. Therefore
an accepted `/diagnose@bot` reached the parser as an unknown command. The fix
passes the already normalized command while preserving argument case and file
transport behavior. Permission and chat checks remain ahead of dispatch.

Target: `send/core/bot_service.py`. Regression tests cover addressed commands,
mixed command case, download arguments/transport and wrong-chat rejection.

### Runtime status lost updates

`runtime_status.update_status` read, merged and replaced a JSON file without a
shared transaction lock. A worker could read STARTING, boot could write RUNNING,
and the worker could then restore the stale STARTING snapshot. A deterministic
two-thread test reproduced this exact interleaving.

Additionally, the boot-completion full replacement discarded observations
already written by newly started workers. The fix serializes writes and complete
read/modify/write transactions with the existing storage lock, then merges the
boot-completion fields instead of replacing the full document. No status is
inferred from tick counts or forced to RUNNING by a display layer.

Targets: `send/runtime/runtime_status.py`, `send/runtime/system_boot.py`.

### Unbounded diagnostic incident scan

`/diagnose` parsed the whole incident log to display only three recent messages.
It now uses the existing bounded tail reader and explicitly reports corrupt or
missing evidence. The regression test fails on any full-history iteration.

Target: `send/core/admin_commands.py`. Additional reproductions and regressions
are in `tests/canonical/unit/test_diagnostic_root_causes.py`.

## Validation and release criteria

Initial audit/FSM/restart tests: 47 passed. The additional diagnostic reproductions
initially produced seven failures and one passing permission test; all eight pass
after correction. Full repository regression for the combined changes:
1,990 passed in 70.06 seconds. `git diff --check` passed. Exact-head GitHub CI
must pass before merging. Release criteria are the expected main
commit installed in the existing service, SUCCESS / Online 1/1, no
startup errors, and a fresh private audit exposing the FSM source and lifecycle
section. Deployment health alone does not verify command delivery or identify
the historical closure event.

## Backup and rollback

The immutable pre-change main commit above preserves every affected source
file. Runtime release is pending; the existing deployment must remain available
as the pre-release reference. No persistent state or configuration file is
edited by this correction.

Rollback is a reviewed revert of this patch on current main followed by the
existing main deployment path. Retain existing `/data` research and FSM
evidence; do not clear caches, backfill or restart the finished two-hour test.

## Status

Implementation and local validation complete; publication, GitHub CI and
release remain pending. Obtaining the actual FSM event is a separate diagnostic
step; a passing export test does not establish a historical closure cause.
