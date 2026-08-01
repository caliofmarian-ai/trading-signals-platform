# Persistence Path Trace

## Canonical path
- Active UI persistence is stored only at `state/telegram_ui_state.json` under the resolved runtime base directory.
- The resolved path is exposed in runtime diagnostics and navigation trace logs.

## Audit result
- Save and load now use the same resolved canonical path after `BINARYBOT_BASE_DIR` is established.
- Initialization is deferred until the runtime path is available.
- The corrective implementation avoids a pre-init load from a fallback repository path.

## Multi-process preservation
- State updates now use locked read-modify-write merging instead of stale whole-file overwrite.
- Independent session entries are preserved across overlapping writers.
