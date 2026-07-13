# FINAL_DEPLOYMENT_BLOCKER_REGISTER.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## NOTE ON SCOPE

This register covers only unresolved findings that constitute deployment blockers. "Deployment blocker" means the issue must be resolved BEFORE the specified deployment phase can proceed safely.

Paper trading and broker execution are excluded from the blocker classification for Railway signal-only/shadow deployment because the current canonical scope does not require them for that phase.

---

## BLOCKER REGISTER

### BLOCKER-001

| Field | Value |
|---|---|
| Blocker ID | BLOCKER-001 |
| Severity | HIGH |
| Affected Dimension | Configuration readiness, Railway deployment readiness, Runtime boot readiness |
| Finding Reference | OF-09-002, FA configuration split |
| Description | The system has a dual-path storage architecture: `BINARYBOT_BASE_DIR` controls state/config paths; `OBS_DIR`/`OUTCOMES_LOG`/`ANALYTICS_DIR` (and per-JSONL env vars) independently control observability paths, defaulting to `/opt/binarybot/...` which does not exist on Railway. Without correctly setting ALL path env vars, observability JSONL writes will fail at runtime (directory does not exist), producing silent observability loss and potential error-event storms. |
| Consequence | On Railway without env var configuration: observability events cannot be written; analytics/research have no data; outcome votes cannot be recorded. System degrades severely in observability and outcome dimensions. |
| Exact Remediation | Set the following env vars consistently to the persistent volume mount path (e.g., `/data`): `BINARYBOT_BASE_DIR`, `OBS_DIR`, `OUTCOMES_LOG`, `ANALYTICS_DIR`, `DIST_EVENTS_LOG`, `FSM_EVENTS_LOG`, `ENGINE_EVENTS_LOG`, `ADMIN_PROOFS_LOG`, `ERROR_EVENTS_LOG`. |
| Code Change Required | NO — env var configuration only |
| Canonical Change Required | NO |
| Owner Decision Required | NO |
| Blocks Railway Deployment Preparation | NO (can be resolved during deployment preparation) |
| Blocks Shadow Mode | YES (until resolved) |
| Blocks Paper Trading | N/A (paper trading not implemented) |
| Blocks Production/Live Trading | N/A (broker not implemented) |

---

### BLOCKER-002

| Field | Value |
|---|---|
| Blocker ID | BLOCKER-002 |
| Severity | HIGH |
| Affected Dimension | Telegram deployment readiness, Shadow-mode readiness, Network integration |
| Finding Reference | Telegram credential requirement |
| Description | `TELEGRAM_BOT_TOKEN` is not set. Without this credential, the Telegram polling thread fails immediately on startup, no signals are published to any channel, and outcome voting is disabled. The signal pipeline continues but has no distribution channel. |
| Consequence | No Telegram signal publication. No outcome voting. Distribution router produces SKIPPED_DISABLED for all tiers. |
| Exact Remediation | Set `TELEGRAM_BOT_TOKEN` in Railway secrets. Add bot as admin to all configured channels. |
| Code Change Required | NO |
| Canonical Change Required | NO |
| Owner Decision Required | NO (operator action) |
| Blocks Railway Deployment Preparation | NO (resolved during deployment preparation) |
| Blocks Shadow Mode | YES if Telegram routing desired; NO if shadow mode runs without Telegram (acceptable per shadow mode definition) |
| Blocks Paper Trading | N/A |
| Blocks Production/Live Trading | N/A |

---

### BLOCKER-003

| Field | Value |
|---|---|
| Blocker ID | BLOCKER-003 |
| Severity | MEDIUM |
| Affected Dimension | Outcome tracking readiness, Privacy/security readiness |
| Finding Reference | `COMMUNITY_FEEDBACK_SALT` and `ELITE_CHANNEL_ID` requirement |
| Description | Outcome voting (user WIN/LOSE feedback) requires `COMMUNITY_FEEDBACK_SALT` and `ELITE_CHANNEL_ID`. Without these, `outcome_service._config_ready()` returns `(False, "community_feedback_salt_missing")` for every vote — all votes silently rejected. |
| Consequence | No outcome data collected. Analytics has no outcome records. Win-rate computation returns null (insufficient sample). |
| Exact Remediation | Set `COMMUNITY_FEEDBACK_SALT` (randomly generated secret string, minimum 32 characters) and `ELITE_CHANNEL_ID` in Railway. |
| Code Change Required | NO |
| Canonical Change Required | NO |
| Owner Decision Required | NO (operator action) |
| Blocks Railway Deployment Preparation | NO |
| Blocks Shadow Mode | YES if outcome voting is part of shadow scope; NO if shadow mode operates without outcome collection |
| Blocks Paper Trading | N/A |
| Blocks Production/Live Trading | N/A |

---

### BLOCKER-004

| Field | Value |
|---|---|
| Blocker ID | BLOCKER-004 |
| Severity | MEDIUM |
| Affected Dimension | Railway deployment readiness |
| Finding Reference | Config seeding requirement |
| Description | On first Railway deploy, the config directory on the persistent volume (`/data/config/`) must be seeded with the config files from `send/config/`. If the config directory does not exist or is empty, `storage.config_path()` raises `StoragePathError` and the engine cannot load params or channel config. |
| Consequence | System fails to start on first deploy without config seeding. |
| Exact Remediation | During deployment preparation: create a start script or Railway deploy hook that copies `send/config/` to `$BINARYBOT_BASE_DIR/config/` on first run (checking if config already exists before copying). |
| Code Change Required | YES — deploy-time initialization script needed (not application code change) |
| Canonical Change Required | NO |
| Owner Decision Required | NO |
| Blocks Railway Deployment Preparation | YES — must be resolved before first deploy |
| Blocks Shadow Mode | YES — same requirement |
| Blocks Paper Trading | N/A |
| Blocks Production/Live Trading | N/A |

---

### BLOCKER-005

| Field | Value |
|---|---|
| Blocker ID | BLOCKER-005 |
| Severity | MEDIUM |
| Affected Dimension | Canonical integrity |
| Finding Reference | OF-09-001, OWNER-DECISION-BATCH09-001 |
| Description | `TEST_PLAN_v2.0.0.md` is truncated at section 17 heading. Sections 17+ body and 18+ entirely missing. Canonical document set is incomplete. |
| Consequence | Canonical validation requirements for analytics, research, and any subsequent sections are undefined. Test coverage for these areas exists but is not formally canonically mapped. |
| Exact Remediation | Owner must supply the missing section 17+ content for TEST_PLAN_v2.0.0.md. |
| Code Change Required | NO |
| Canonical Change Required | YES — TEST_PLAN must be completed |
| Owner Decision Required | YES — OWNER-DECISION-BATCH09-001 |
| Blocks Railway Deployment Preparation | NO |
| Blocks Shadow Mode | NO |
| Blocks Paper Trading | N/A |
| Blocks Production/Live Trading | NO (already not ready for independent reasons) |

---

### BLOCKER-006

| Field | Value |
|---|---|
| Blocker ID | BLOCKER-006 |
| Severity | LOW |
| Affected Dimension | Market data (network integration) |
| Finding Reference | TWELVE_DATA_API_KEY requirement |
| Description | `runtime.market_client.fetch_klines()` requires `TWELVE_DATA_API_KEY`. Without it, market data requests fail with API errors. No candle data → no signals generated. |
| Consequence | Engine runs but generates zero signals (no market data available). |
| Exact Remediation | Obtain TwelveData API key (free tier available). Set as Railway secret. |
| Code Change Required | NO |
| Canonical Change Required | NO |
| Owner Decision Required | NO |
| Blocks Railway Deployment Preparation | NO (resolved during preparation) |
| Blocks Shadow Mode | YES — no signals without market data |
| Blocks Paper Trading | N/A |
| Blocks Production/Live Trading | N/A |

---

## BLOCKER SUMMARY TABLE

| Blocker | Severity | Code Change? | Owner Decision? | Blocks Deployment Prep | Blocks Shadow Mode |
|---|---|---|---|---|---|
| BLOCKER-001 | HIGH | NO | NO | NO (resolve during prep) | YES (until resolved) |
| BLOCKER-002 | HIGH | NO | NO | NO (resolve during prep) | Conditional |
| BLOCKER-003 | MEDIUM | NO | NO | NO | Conditional |
| BLOCKER-004 | MEDIUM | YES (deploy script) | NO | YES | YES |
| BLOCKER-005 | MEDIUM | NO | YES | NO | NO |
| BLOCKER-006 | LOW | NO | NO | NO | YES |

**CRITICAL unresolved blockers:** 0  
**HIGH blockers requiring code change:** 0  
**All HIGH/MEDIUM blockers:** Resolvable through deployment preparation (env vars, config seeding, deploy script) except BLOCKER-005 which requires owner action on canonical document.

**Railway signal-only/shadow deployment can proceed once BLOCKER-001, BLOCKER-002, BLOCKER-003, BLOCKER-004, and BLOCKER-006 are addressed during deployment preparation.**  
**BLOCKER-005 is the only item requiring owner action and does not block deployment.**
