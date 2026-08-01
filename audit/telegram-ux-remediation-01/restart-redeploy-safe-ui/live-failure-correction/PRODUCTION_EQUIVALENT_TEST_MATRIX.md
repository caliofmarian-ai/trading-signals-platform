# Production Equivalent Test Matrix

- [x] Import before runtime path, then explicit initialization after path setup, reloads persisted state.
- [x] Restart with persisted active message reuses the original message.
- [x] Restart with deleted active message sends exactly one replacement.
- [x] Restart plus repeated `/admin` remains single-message.
- [x] Private chat key normalization treats missing thread, `None`, `0`, and persisted `null` identically.
- [x] Stale cross-instance session writes preserve both independent sessions.
- [x] Poller startup is blocked when a duplicate in-process poller tries to start.
- [x] System boot initializes active UI state before polling thread startup.
- [x] Existing Telegram transport/recovery regression suite still passes.
- [x] Existing Railway deployment preparation suite still passes.
