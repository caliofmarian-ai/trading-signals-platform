# Security and Privacy Analysis

## Data minimization
Persisted fields:
- `chat_id`
- `user_id`
- `thread_id`
- `message_id`
- `updated_ts`

Not persisted:
- message content
- bot token
- user text
- private conversation payloads

## Boundary preservation
- Session isolation key unchanged (`chat_id`, `user_id`, `thread_id`).
- No permission/role logic changed.
- No admin boundary widening.

## Integrity controls
- Atomic writes via `save_json_atomic`.
- Lock-based update serialization via `with_lock`.
- Schema validation and strict version gate.
- Corruption-safe startup fallback avoids permanent Telegram silence.

## Secrets posture
- No secrets added to repository.
