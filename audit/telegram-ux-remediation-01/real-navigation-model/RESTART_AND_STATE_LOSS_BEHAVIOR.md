# Restart and State Loss Behavior

- Active message persistence remains the source of truth for anchor reuse across restart/redeploy.
- APP history and APP current-page state are intentionally runtime-scoped; after restart/state loss, Back falls back safely to Home.
- `/start` is the hard reset path for private chats and also resets APP generation for every context.
- A stale APP callback from a prior `/start` generation cannot revive old history.
