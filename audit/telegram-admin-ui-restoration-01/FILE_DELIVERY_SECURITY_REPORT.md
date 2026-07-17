# FILE DELIVERY SECURITY REPORT

## Overview

File delivery is implemented in `send/core/admin_commands.py` and uses the existing
`telegram_publisher.send_document()` transport.

---

## Allowed File Roots

Files are served only from explicitly allowlisted subdirectories under `BINARYBOT_BASE_DIR`:

| Short key | Directory | Notes |
|---|---|---|
| `obs` | `observability/` | Engine events, admin events, error events |
| `out` | `outcomes/` | Trade outcome records |
| `ana` | `analytics/` | Analytics output |
| `rpt` | `analytics/reports/` | Daily strategy audit reports |
| `doc` | `docs/` | Documentation files |
| `aud` | `audit/` | Audit deliverables |
| `snp` | `snapshots/` | Snapshot files |

---

## Allowed Extensions

Only the following file extensions are accepted for delivery:

```
.md  .txt  .json  .jsonl  .log
```

Any other extension is rejected with an error message and an audit entry.

---

## Security Validations (`_is_path_safe`)

Every file download request is validated in this order:

1. **Path traversal check:** Reject any path containing `..`.
2. **Filename secret pattern check:** Reject filenames matching any of:
   `.env`, `token`, `secret`, `password`, `passwd`, `.key`, `credential`,
   `private`, `.pem`, `.p12`, `.pfx`, `.cer`, `id_rsa`, `id_ed25519`, `id_ecdsa`,
   `salt`, `.htpasswd`.
3. **Extension check:** Reject unsupported extensions.
4. **Real-path resolution:** Resolve symlinks via `os.path.realpath()`.
5. **Root containment:** The resolved real path must start with the resolved allowed root.
6. **Symlink escape check:** If the path is a symlink, its target must also be within the root.
7. **File existence:** The resolved path must be a regular file.
8. **Size check:** File size must not exceed `MAX_DELIVERY_FILE_SIZE` (default: 5 MB).

If any check fails, the request is rejected, an audit entry is written, and the
user receives a clear error message.

---

## `MAX_DELIVERY_FILE_SIZE`

Configurable via the `MAX_DELIVERY_FILE_SIZE` environment variable (bytes).
Default: 5,242,880 bytes (5 MB).

---

## Audit Trail

Every download request (allowed or rejected) generates an `admin_change` event
written to `ADMIN_EVENTS_PATH` and `ADMIN_PROOFS_PATH`. The event includes:
- `user_id`
- `dir_key`
- `filename` (sanitized)
- `result` (`OK`, `DENIED`, `REJECTED`)
- `reason` (for rejections)

---

## File Listing

`handle_files_list(user_id, dir_key, page)` provides paginated file listing:
- Only lists files with allowed extensions.
- Skips files matching secret patterns.
- Returns at most `FILES_PER_PAGE` (8) filenames per page.

---

## Secret Files Never Exposed

The following are never delivered under any circumstances:
- `.env` files
- Any file whose name contains: `token`, `secret`, `password`, `key`, `credential`,
  `private`, `salt`, or known private-key file extensions.
- Files outside the explicitly allowlisted directories.
- Files whose real path escapes the allowed root via symlinks.

---

## `/report` Enhancement

The `/report` command retains its current text summary and, when a report file is available
and the user is authorized, also shows a `📥 Download Report` button in the markup.

---

## `/log` Delivery

`/log` exports a bounded, sanitized diagnostic log:
- Reads from `engine_events.jsonl` and `admin_events.jsonl`.
- Takes only the last `LOG_EXPORT_MAX_LINES` (200) lines from each.
- Redacts values for keys matching: `token`, `secret`, `password`, `key`, `salt`,
  `credential`, `api_key`, `telegram_bot_token`, `twelve_data_api_key`, `community_feedback_salt`.
- Writes to a temporary file and delivers via `send_document`.
- Temporary file is deleted after delivery.

---

## Commands

| Command | Access | Notes |
|---|---|---|
| `/files [dir]` | `files.view` | Browse files; shows directory chooser or lists a specific dir |
| `/docs` | `files.view` | Browse docs directory |
| `/download <dir> <filename>` | `files.view` | Download specific file |
| `/log` | `diagnostics.view` | Export bounded, sanitized log |
