# Canonical Analysis

## Verified root causes
- `push_nav_action()` existed but the live APP dispatcher never called it, so runtime APP history stayed empty.
- APP callback handling did not consistently pass `(chat_id, user_id, thread_id)` into navigation state.
- APP markup generated Home and Refresh buttons, but no real APP Back buttons for runtime pages.
- `/start` cleared transport state but did not invalidate old APP callback generations.
- Several admin journeys still lost their immediate parent context (notably roles reload confirm and diagnose → runtime audit variants).

## Final model
- APP navigation uses live per-session state keyed by `(chat_id, user_id, thread_id)`.
- `/start` begins a new navigation generation, clears APP history, and resets the current APP page to Home.
- APP callbacks carry a generation token when rendered from live pages; stale generations fall back safely to Home.
- APP page transitions push only the page being left, never the destination, and only when the destination is a different logical page.
- Admin navigation remains callback-driven and authorization-gated, with context encoded in canonical callbacks where parent preservation matters.
