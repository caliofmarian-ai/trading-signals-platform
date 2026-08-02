# Navigation State Model

## APP runtime state
- Key: `(chat_id, user_id, thread_id)` after normalization.
- State elements:
  - active message id
  - bounded APP history stack
  - current APP page id
  - current APP navigation generation
- APP history is in-memory and bounded.
- Active message state remains persisted as before.

## APP generation model
- `/start` increments the session generation.
- Live APP buttons embed that generation in callback data.
- A stale generation is rejected and the session falls back to Home.

## Admin state model
- Admin navigation is callback-contract based.
- Parent preservation is encoded into canonical admin callbacks where needed.
- Authorization is re-evaluated at render time; no admin history item is trusted on its own.
