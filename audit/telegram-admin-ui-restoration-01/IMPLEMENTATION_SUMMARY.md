# IMPLEMENTATION SUMMARY

## Audit metadata

- **Base commit:** `99cbf3b` (planning commit for this branch)
- **Forensic-audit reference HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **Branch:** `copilot/implement-telegram-admin-ui-restoration`
- **Implementation date:** 2026-07-17

---

## Objective

Restore the useful historical Telegram owner/admin experience inside the current canonical
control plane, without restoring the deleted legacy bot (`send/legacy/bot_control.py`) as a
separate process.

---

## What was changed

### 1. `send/core/admin_permissions.py`
- Added `files.view` permission to `ROLE_OWNER`, `ROLE_PRIMARY_ADMIN`, `ROLE_STRATEGY_ADMIN`, `ROLE_RESEARCH_ADMIN`.
- Added `diagnostics.view` permission to `ROLE_OWNER`, `ROLE_PRIMARY_ADMIN`.
- No existing permissions modified or removed.

### 2. `send/core/telegram_admin_ui.py`
- Updated `admin_home_markup` to expose all 16 canonical admin buttons:
  📊 Status, ⚙️ Strategy, 🎯 Thresholds, 📐 S/R, ⚡ Spike Filter, 💱 Symbols, 🤖 Engine,
  🐞 Debug, 📈 Reports, 📁 Files, 📄 Documents, 🩺 Diagnose, 🔍 Runtime Audit, 👥 Roles,
  🤝 Affiliate, 🔄 Reload Roles.
- Added `symbols_toggle_markup(all_symbols, active_symbols)` — visual checkbox grid with ✅/⬜.
- Added `strategy_quick_markup(current_profile)` — MIC/MEDIU/MARE buttons with current indicator.
- Added `strategy_profile_confirm_markup(profile)` — confirmation screen for mutations.
- Added `files_home_markup()` — directory chooser for file browser.
- Added `files_list_markup(filenames, page, total_pages, dir_key)` — paginated file list.
- Added `docs_list_markup(filenames)` — single-column docs viewer.
- Added `diagnose_markup()` — post-diagnose action buttons.
- Added `report_markup(has_file, dir_key, filename)` — report panel with optional download button.
- Updated `strategy_markup` to include a Quick Profile button.
- Updated `engine_markup` icon from ♻️ to 🔄 for Reload Roles.

### 3. `send/core/admin_commands.py`
- Added `ALLOWED_EXTENSIONS`, `ALLOWED_DIR_NAMES`, `_DIR_KEY_MAP`, `_SECRET_PATTERNS`,
  `MAX_DELIVERY_FILE_SIZE_DEFAULT` constants.
- Added `STRATEGY_PROFILES` dict with CONSERVATIVE/BALANCED/AGGRESSIVE definitions.
- Added `CANONICAL_SYMBOLS` dict with FOREX and CRYPTO symbol lists.
- Added `get_all_known_symbols()` — returns canonical FOREX + CRYPTO symbol list.
- Added `handle_symbols_toggle(symbol, user_id)` — toggle a single symbol on/off with audit.
- Added `handle_symbols_all(user_id)` — activate all canonical symbols.
- Added `handle_symbols_none(user_id)` — deactivate all symbols.
- Added `get_current_strategy_profile()` — detect which profile matches current params.
- Added `handle_strategy_profile(profile, user_id)` — apply a named strategy profile.
- Added `_max_delivery_size()`, `_resolve_dir_path()`, `_is_path_safe()` — file security.
- Added `handle_files_list(user_id, dir_key, page)` — paginated file listing.
- Added `handle_file_download_path(dir_key, filename, user_id)` — secure path resolution.
- Added `handle_docs_list(user_id)` — docs directory listing.
- Added `handle_log_export(user_id)` — bounded, sanitized log export to temp file.
- Added `handle_diagnose(user_id)` — concise operational diagnosis.
- Added `handle_audit_runtime(user_id)` — sanitized runtime audit artifact.
- Extended `handle_admin_command` with `/files`, `/docs`, `/download`, `/log`, `/diagnose`, `/audit_runtime`.
- Added `hashlib` and `tempfile` imports.

### 4. `send/core/bot_service.py`
- Added imports for new admin_commands handlers.
- Extended `_OWNER_PRIVATE_COMMANDS` with `/files`, `/docs`, `/download`, `/log`, `/diagnose`, `/audit_runtime`.
- Added `_RATE_STORE` dict and `_RATE_LIMITS_CONFIG` constants for per-user rate limiting.
- Added `_check_rate_limit(user_id, operation)` function.
- Added `_env_flag` function (re-added after imports section update).
- Added `_send_document_reply(message, file_path, caption)` — document delivery with tmp cleanup.
- Updated `_admin_reply_markup` with new markup functions for all new commands.
- Updated `_render_panel_for_command` with new title mappings and markup selection.
- Completely rewrote `_handle_admin_navigation_action` to handle all new callbacks:
  `SYM_TOGGLE:*`, `SYMBOLS_ALL`, `SYMBOLS_NONE`, `PROFILE_HOME`, `PROFILE_CONFIRM:*`,
  `PROFILE_EXEC:*`, `FILES_HOME`, `FILES:*`, `DOCS`, `FILE_DL:*`, `LOG`, `DIAGNOSE`, `AUDIT`.
- Added graceful fallback in `process_update`: if `edit_message` fails, sends as new message.
- Added `__file_path__` signal handling in `process_update` for document delivery.

### 5. `send/core/telegram_runtime.py`
- Added `CommandSpec` entries for `/files`, `/docs`, `/download`, `/log`, `/diagnose`, `/audit_runtime`.
- Updated `render_help_text` to list the new owner-private commands.

### 6. `send/core/telegram_targets.py`
- Added `alerts_target()` — optional routing using `ADMIN_ALERTS_THREAD_ID`.
- Added `errors_target()` — optional routing using `ADMIN_ERRORS_THREAD_ID`.
- Added `reports_target()` — optional routing using `ADMIN_REPORTS_THREAD_ID`.

### 7. `.env.example`
- Documented `ADMIN_ALERTS_THREAD_ID`, `ADMIN_ERRORS_THREAD_ID`, `ADMIN_REPORTS_THREAD_ID`.
- Documented `MAX_DELIVERY_FILE_SIZE`.

### 8. `tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py`
- 69 new tests across AUTH, UI, SYM, PROF, FILE, DIAG, RATE, REG categories.

---

## What was NOT changed

- `send/legacy/bot_control.py` — not restored (architecture guardrail).
- `send/core/telegram_publisher.py` — no changes needed (already has `send_document`).
- No second Telegram polling process introduced.
- No new Python package dependencies added.
- No password authentication introduced.
- `ADMIN_CONTROL_CHAT_ID` fail-closed behavior preserved.

---

## Test totals

- **Before:** 325 tests passing.
- **After:** 394 tests passing (69 new).
- **Failed:** 0.

---

## Deferred requirements

None of the acceptance criteria were deferred. All 11 required deliverables are present.
