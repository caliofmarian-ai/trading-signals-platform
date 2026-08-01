# Corrective Implementation Contract

- Initialize Telegram active UI persistence explicitly with `initialize_active_ui_state()`.
- Call initialization only after the runtime base directory and Railway path contract are established.
- Keep initialization idempotent and safe for repeated calls.
- Normalize all interactive session keys through one canonical function.
- Preserve only minimal metadata: `chat_id`, `user_id`, `thread_id`, `message_id`, `updated_ts`.
- Log per-interactive-update routing decisions with sanitized identifiers and resolved state path.
- Emit critical startup/recovery diagnostics to both JSONL observability and Railway stderr.
- Guard against accidental duplicate polling in one process.
- Merge persisted state updates under lock instead of overwriting the full file from stale in-memory state.
