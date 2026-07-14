# ADMIN_PROOF_RECONNECTION_REPORT

## Reconnected path
- Successful admin mutation auditing still writes local JSONL proof records.
- The active runtime now also routes admin-proof Telegram messages through `core.observability_logger.send_admin_proof_telegram()`.
- Telegram delivery is best-effort; local proof persistence happens first and is not rolled back on delivery failure.
