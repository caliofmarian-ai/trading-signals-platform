# AUDIT_EXECUTIVE_SUMMARY

## Concise verdict
Railway runtime is up and polling Telegram, but command response and operator alerting gaps are real and code-backed.

## Exact current Railway process model
Single process (`scripts.railway_start`) running `system_boot` with daemon threads: engine, scheduler, optional Telegram poller.

## Is Telegram polling started?
Yes, when `ENABLE_TELEGRAM=true` and token exists.

## Is command dispatch started?
Yes, but only for a narrow admin slash-command set and callback flows.

## Why commands receive no response
- `/start`, `/help`, `/status` are not implemented in active dispatcher.
- Unknown slash commands are silently ignored.
- Even handled commands can fail to send replies if topic thread-id is forced in incompatible chat contexts.

## Implemented command list
`/admin`, `/strategy`, `/thresholds`, `/sr`, `/spike`, `/symbols`, `/engine`, `/debug`, `/report`, `/roles`, `/affiliate`, `/roles_reload`.

## Where commands are accepted
- Slash admin commands: role-permission based (not chat-gated).
- Admin callbacks: only in `ADMIN_CONTROL_CHAT_ID` context (fail-closed).

## `/start` `/help` `/status` existence
Not present in active command router.

## Health mechanisms (active)
Readiness/liveness scripts, runtime status file, restart guard, recovery/engine/error JSONL eventing.

## Automatic Telegram alert/reporting mechanisms (active)
None effectively active for startup/errors; only dormant proof relay exists with zero active callers.

## Why startup/live notification is missing
No startup code path sends Telegram; startup emits JSONL events only.

## Why error notifications are missing
No active error-to-Telegram route in runtime; legacy shell scripts are unwired.

## Did BATCH-09 remove required live functionality?
Not from canonical in-repo callers. However, deleted `legacy/bot_control.py` likely represented historical externally-started behavior that could have provided `/start` UX.

## Hetzner vs Railway difference
Hetzner likely had extra externally-operated runtime pieces (legacy bot/scripts). Railway runs only canonical single-process startup command.

## Exact 429 failure flow
`engine_loop -> signal_engine.run_once -> market_client.fetch_klines(429) -> exception -> malformed log_error -> fallback observability_log_failed` in tight loop.

## Exact observability schema defect
`event_type=error` shorthand payloads lacking `data.severity/error_type/message` at multiple call sites fail schema validation and trigger fallback errors.

## Root-cause ranking
Highest impact: RC-01, RC-02, RC-03, RC-04, RC-05 (see register).

## Tests run
- Full suite: 302 passed
- Targeted scoped suite: 113 passed
- Import/syntax checks: pass
