# Failure Mode Matrix

| Failure mode | Detection path | Runtime behavior | Result |
|---|---|---|---|
| Persisted UI file missing | state load default | start with empty cache | safe recovery |
| Persisted UI file corrupt JSON | validator/load exception | warning + empty cache | startup not blocked |
| Unsupported schema version | validator exception | warning + empty cache | startup not blocked |
| Persisted message deleted | Telegram edit stale error | clear active + send one replacement | no permanent silence |
| Edit no-op (`message is not modified`) | failure classifier | keep active session, no extra send | no duplicate spam |
| Unexpected edit error | failure classifier | log error; fallback path can send | resilient behavior |
| Concurrent active-state updates | lockfile serialization | atomic final artifact | consistent state |
| Oversized session set | retention/max pruning | bounded persisted map | controlled storage growth |
