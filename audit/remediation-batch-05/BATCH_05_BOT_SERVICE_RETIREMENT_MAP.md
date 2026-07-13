# BATCH_05_BOT_SERVICE_RETIREMENT_MAP

**Owner Decision Applied:** OWNER-002 = A
**Original Findings:** GAP-013

---

## bot_service.py Retirement Classification (Pre → Post BATCH-05)

| Component | Pre-BATCH-05 | Classification | Post-BATCH-05 |
|-----------|-------------|----------------|---------------|
| `OUTCOMES_PATH` constant | Module-level path attribute | KEEP TEMPORARILY | Retained as module attribute; NOT written by bot_service |
| `in_admin_context(chat_id)` | Fail-OPEN when ADMIN_CONTROL_CHAT_ID==0 | FIX | Fail-CLOSED — returns False when env var not set |
| `get_role(user_id)` | Independent RBAC via rbac.json or ADMIN_USER_ID env | RETIRE | Removed |
| `require_role(user_id, allowed)` | Independent role check | RETIRE | Removed |
| `_load_rbac()` | Reads config/rbac.json | RETIRE | Removed |
| `render_admin_panel(user_id)` | Legacy inline keyboard builder | RETIRE | Removed |
| `handle_admin_command(chat_id, user_id)` | Legacy panel entry point (NOT called by process_update) | RETIRE | Removed |
| `_record_outcome(...)` | Independent outcome mutation bypassing outcome_service | RETIRE | Removed — legacy OUTCOME: callbacks now delegate to outcome_service |
| `_load_outcomes_store()` | Reads outcomes.json (separate from outcome_service) | RETIRE | Removed |
| `_save_outcomes_store()` | Writes outcomes.json atomically | RETIRE | Removed |
| `_proof(...)` | observability proof for legacy mutations | RETIRE | Removed (mutations retired) |
| `_load_settings()` / `_save_settings()` | settings.json read/write | RETIRE | Removed (only used by buffer mode — not canonical) |
| `_load_active_symbols()` / `_save_active_symbols()` | symbols.json read/write | RETIRE | Removed (use admin_commands path) |
| `_load_focus_state()` | focus_state.json read | RETIRE | Removed (only used by _ui_status) |
| `_load_dist_state()` | dist_state.json read | RETIRE | Removed (only used by _ui_status) |
| `kb()` / `btn()` | Inline keyboard helpers | RETIRE | Removed (panel UI retired) |
| `_ui_set_buffer()` | Buffer mode selection UI | RETIRE | Removed (not canonical) |
| `_ui_symbols_menu()` | Symbol toggle UI | RETIRE | Removed (use /symbols slash command) |
| `_ui_status()` | System status inline view | RETIRE | Removed (use /engine slash command) |
| `_ui_docs_menu()` | Documentation viewer UI | RETIRE | Removed (not in canonical v2) |
| `_do_set_buffer(user_id, mode)` | Admin mutation: settings.json buffer_mode | RETIRE | Removed (not in canonical v2) |
| `_do_toggle_symbol(user_id, symbol)` | Admin mutation: symbols.json add/remove | RETIRE | Removed (use /symbols slash command) |
| `_do_send_doc(doc_filename)` | File serving from docs/ | RETIRE | Removed (not in canonical v2) |
| `handle_callback(ADMIN_STATUS)` | Status view via callback | RETIRE | Returns retirement message |
| `handle_callback(ADMIN_SET_BUFFER)` | Buffer selection via callback | RETIRE | Returns retirement message |
| `handle_callback(BUFFER_*)` | Buffer mode mutation via callback | RETIRE | Returns retirement message |
| `handle_callback(ADMIN_SET_SYMBOLS)` | Symbol menu via callback | RETIRE | Returns retirement message |
| `handle_callback(SYM_TOGGLE:*)` | Symbol toggle mutation via callback | RETIRE | Returns retirement message |
| `handle_callback(ADMIN_RESEARCH)` | Research placeholder via callback | RETIRE | Returns retirement message |
| `handle_callback(ADMIN_DOCS)` | Docs viewer via callback | RETIRE | Returns retirement message |
| `handle_callback(DOC:*)` | Document serving via callback | RETIRE | Returns retirement message |
| `handle_callback(ADMIN_BACK)` | Navigation back | RETIRE | Returns retirement message |
| `handle_callback(VOTE_\|sig\|outcome)` | VOTE forwarding to outcome_service | KEEP (DELEGATE) | Preserved — delegates to outcome_service |
| `handle_callback(VOTE_*)` | Generic VOTE forwarding | KEEP (DELEGATE) | Preserved — delegates to outcome_service |
| `handle_callback(OUTCOME:outcome:sig)` | Legacy outcome mutation | MIGRATE | Now delegates to outcome_service instead of _record_outcome |
| `process_update(update)` | Telegram update dispatcher | KEEP (MODIFIED) | Preserved — dispatches slash commands to admin_commands, callbacks to handle_callback |
| `ROLE_OWNER, ROLE_ADMIN, ROLE_ANALYST, ROLE_MODERATOR` | Legacy role constants | RETIRE | Removed |
| `ALLOWED_BUFFER_MODES` | Buffer mode validation set | RETIRE | Removed |
| `BASE_DIR, DOCS_DIR, CONFIG_DIR, STATE_DIR` | Path constants for retired functions | RETIRE | Removed |
| `SETTINGS_PATH, ACTIVE_SYMBOLS_PATH, FOCUS_STATE_PATH, DIST_STATE_PATH` | Path constants for retired functions | RETIRE | Removed |
| `CHANNEL_CONFIG_PATH, RBAC_PATH` | Path constants for retired functions | RETIRE | Removed |
| `ADMIN_PROOFS_CHAT_ID, ADMIN_PROOFS_THREAD_ID, ADMIN_USER_ID, ENV` | Env constants for retired functions | RETIRE | Removed |

---

## Exact Residual Responsibility of bot_service.py After BATCH-05

`bot_service.py` is now a **thin dispatcher only**. It:

1. Provides `process_update(update)` — the Telegram update entry point
2. Dispatches slash admin commands to `handle_admin_command_v2` (from `admin_commands.py`)
3. Provides `handle_callback()` which:
   - Forwards `VOTE_|...|...` and `VOTE_...` callbacks to `outcome_service` (BATCH-04 canonical path)
   - Forwards legacy `OUTCOME:...:...` callbacks to `outcome_service` (no independent mutation)
   - Rejects all retired Admin panel callbacks with a clear message
   - Enforces `in_admin_context()` (fail-closed) for Admin-context callbacks
4. Retains `OUTCOMES_PATH` as a module attribute for BATCH-04 test/runtime compatibility

**bot_service does NOT:**
- Authorize Admin users independently
- Evaluate Admin permissions independently
- Mutate Admin-controlled state/config
- Maintain a competing Admin command registry
- Persist Admin mutations
- Emit Admin mutation success events

---

## Migration Notes

### Buffer Mode Control (BATCH-05 decision: RETIRE)
The canonical v2 specification explicitly superseded "direct buffer-setting concepts" (ADMIN_CONTROL_SPEC_v2.0.0.md §legacy retirement). The `BUFFER_*` callbacks and `settings.json` write path are retired without migration. If buffer mode control is required in a future batch, it must be implemented through the canonical control plane with a canonical permission.

### Symbol Toggle UI (BATCH-05 decision: RETIRE)
The `/symbols add SYMBOL` and `/symbols remove SYMBOL` slash commands in `admin_commands.py` provide equivalent canonical functionality. The legacy inline keyboard toggle is retired.

### Docs Viewer (BATCH-05 decision: RETIRE)
Not present in the canonical v2 specification. Retired without migration.

### OUTCOME: Legacy Format (BATCH-05 decision: MIGRATE)
`OUTCOME:<outcome>:<signal_id>` callbacks previously called `_record_outcome()` independently. After BATCH-05, they delegate to `outcome_service.handle_vote_callback()`. The mutation authority remains exclusively with BATCH-04 `outcome_service`.
