# DISTRIBUTION_TELEGRAM_AND_OUTCOME_READINESS_REPORT.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## 1. CHANNEL CONFIGURATION LOADING

- **Loader:** `core.distribution_router._load_channel_config()`
- **Config paths tried (in order):**
  1. `storage.config_path("channel_config.json")` — canonical path under `BINARYBOT_BASE_DIR/config/`
  2. `storage.config_path("channel-config.json")` — alternate hyphenated name
  3. `/opt/binarybot/config/channel_config.json` — legacy fallback
  4. `/opt/binarybot/config/channel-config.json` — legacy alternate fallback
- **Fallback behavior:** If all paths fail, uses default limits (FREE=5, BASIC=20, PRO=50, ELITE=unlimited).
- **Current deployed config:** `send/config/channel_config.json` — present and valid. Contains real Telegram channel IDs.
- **Channel IDs in config:** FREE, BASIC, PRO, ELITE channel IDs, ADMIN_GROUP_ID, SIGNALS_LIVE_TOPIC_ID.
- **Bot token:** NOT in channel_config.json — loaded separately from `TELEGRAM_BOT_TOKEN` env var.

---

## 2. TIER ENABLE/DISABLE

- All 4 tiers active: FREE, BASIC, PRO, ELITE.
- Limits: FREE=5, BASIC=20, PRO=50, ELITE=null (unlimited).
- Daily reset at 08:10 London time via `distribution_scheduler`.
- Tier disabled if: channel ID is 0 or not configured in channel_config; produces `SKIPPED_DISABLED`.
- Limit reached: produces `SKIPPED_LIMIT`.
- Silent channel (no message sent but counted): produces `SKIPPED_SILENT`.

---

## 3. PUBLISH RESULT TAXONOMY

Canonical publish_result values (verified against `event_schema.json`):
- `PUBLISHED` — signal sent to Telegram channel successfully
- `FAILED` — Telegram API call failed
- `SKIPPED_SILENT` — intentionally not published (e.g., silent mode)
- `SKIPPED_LIMIT` — daily limit reached for tier
- `SKIPPED_DISABLED` — tier disabled or channel not configured
- `DUPLICATE_SUPPRESSED` — signal already distributed for this tier

All 6 results emitted as observability events to `distribution_events.jsonl`.

---

## 4. DUPLICATE SUPPRESSION

- Per-signal, per-tier deduplication using `seen_signals` set in distribution state.
- State persisted in `dist_state.json`.
- On restart: state reloaded; previously distributed signals remain suppressed.
- Confirmed: `tests/canonical/end_to_end/test_offline_end_to_end_flows.py::test_restart_lifecycle_preserves_dedup_and_no_duplicate_irreversible_action` — PASS.

---

## 5. OBSERVABILITY EVENTS

Distribution events emitted to `distribution_events.jsonl` for every routing decision (per tier). All events validated against `event_schema.json` before write.

---

## 6. MISSING TELEGRAM CREDENTIALS BEHAVIOR

- `TELEGRAM_BOT_TOKEN` missing: `telegram_publisher._get_token()` returns `""` → `send_message()` sends to `api.telegram.org/bot/sendMessage` — API returns error; publish_result = `FAILED`.
- `outcome_service._config_ready()` checks for token explicitly: if missing, returns `(False, "bot_token_missing")` — outcome voting silently fails with observability event.
- Telegram thread: raises `RuntimeError("TELEGRAM_BOT_TOKEN missing")` on first poll — thread terminates; other threads continue.

---

## 7. MALFORMED TELEGRAM CONFIGURATION BEHAVIOR

- Malformed `channel_config.json` (invalid JSON): `storage.load_json()` returns `{}` default → distribution_router uses default limits.
- Missing required tier channel IDs: tier treated as disabled → `SKIPPED_DISABLED`.

---

## 8. CALLBACK HANDLING

- **Vote callbacks** (`VOTE_WIN_<signal_id>`, `VOTE_LOSE_<signal_id>`, etc.): dispatched to `outcome_service.handle_vote_callback()`.
- **OUTCOME: legacy callbacks**: forwarded to `outcome_service` without independent mutation.
- **Retired admin panel callbacks**: rejected with clear message (no mutation).
- All callbacks validated for admin context (`in_admin_context()`) before admin mutations.

---

## 9. SINGLE OUTCOME MUTATION AUTHORITY

- `outcome_service` is the single write authority for outcomes.
- `bot_service` forwards callbacks; does NOT write independently.
- `bot_service.OUTCOMES_PATH` is a documentation remnant — no write occurs.
- Confirmed: `tests/canonical/integration/test_fsm_distribution_outcome_integration.py::test_outcome_flow_records_vote_and_deduplicates` — PASS.

---

## 10. ADMIN SECURITY BOUNDARY

- `bot_service.in_admin_context(chat_id)` returns False when `ADMIN_CONTROL_CHAT_ID == 0` (fail-closed).
- All admin mutations require `in_admin_context()` to return True.
- Confirmed: `tests/canonical/security/test_security_boundaries.py::test_unauthorized_admin_command_cannot_mutate_config` — PASS.

---

## 11. MEMBERSHIP/CONTEXT VALIDATION

- Outcome vote callbacks: `outcome_service` validates membership in ELITE channel via `_check_membership()` Telegram API call.
- Requires: `TELEGRAM_BOT_TOKEN`, `ELITE_CHANNEL_ID`.
- Non-members receive `SKIPPED_NOT_MEMBER` result.
- Requires network access at vote time (not at import time).

---

## 12. PRIVACY/PSEUDONYMIZATION

- User ID pseudonymized via `SHA-256(user_id + ":" + COMMUNITY_FEEDBACK_SALT)`.
- Raw Telegram user IDs NOT persisted in outcomes.jsonl — only pseudonymized `member_ref` stored.
- Salt required: if `COMMUNITY_FEEDBACK_SALT` is missing, vote returns `community_feedback_salt_missing`.
- Confirmed: `tests/canonical/security/test_security_boundaries.py::test_outcome_rejects_unauthorized_callback_context` — PASS.
- Confirmed: `tests/batch_04/` privacy tests — PASS.

---

## 13. TELEGRAM SIGNAL MODE READINESS DETERMINATION

**Can Telegram signal mode be safely configured next?**

Prerequisites confirmed present:
- Distribution router: implemented and tested
- Channel config: present with real channel IDs
- Telegram publisher: implemented
- Duplicate suppression: active
- Publish result taxonomy: complete
- Privacy/pseudonymization: active
- Admin security boundary: fail-closed

Prerequisites STILL REQUIRED before activation:
1. `TELEGRAM_BOT_TOKEN` must be set in Railway environment (not in repository — correct).
2. `COMMUNITY_FEEDBACK_SALT` must be set in Railway secrets.
3. `OWNER_TELEGRAM_ID` and `ADMIN_CONTROL_CHAT_ID` must be configured.
4. `ELITE_CHANNEL_ID` must be set (for outcome voting).
5. Railway persistent volume must be configured and all env vars set.
6. Bot must be added as admin to all configured channels.

**Verdict:** Telegram signal mode can be safely configured as the NEXT step after Railway deployment preparation. No code changes required.

---

## 14. VERDICT

| Dimension | Verdict | Notes |
|---|---|---|
| Distribution readiness | READY | Full tier distribution, duplicate suppression, publish result taxonomy implemented and tested |
| Outcome tracking readiness | READY | Atomic outcome writes, pseudonymization, deduplication, vote window all implemented and tested |
| Telegram deployment readiness | CONDITIONALLY READY | Code complete; requires env var configuration (BOT_TOKEN, COMMUNITY_FEEDBACK_SALT, ELITE_CHANNEL_ID, OWNER_TELEGRAM_ID, ADMIN_CONTROL_CHAT_ID) and Railway deployment before activation |
