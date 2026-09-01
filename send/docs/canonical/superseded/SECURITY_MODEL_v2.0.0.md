# SECURITY_MODEL_v2.0.0.md

**Canonical Name:** SECURITY_MODEL  
**Version:** 2.0.0  
**Status:** Active Canonical Specification  
**Owner:** BinaryBot / DROPi Signals  
**Canonical Path:** `send/docs/canonical/active/SECURITY_MODEL_v2.0.0.md`  
**Governance Record:** canonical-reconciliation-01 (OWNER-006 = A)  
**Promoted:** 2026-07-12  

**Authority:** This document is the authoritative canonical specification for the security architecture and threat protection model of BinaryBot / DROPi Signals. All security decisions, implementation choices, and governance actions related to system security must conform to this document.

**Predecessor / Superseded Documents:**  
- `send/docs/SECURITY_MODEL.md` — root-level source document; retained as historical record, superseded by this canonical version.  

**Linked Documents:**  
- `send/docs/canonical/active/ADMIN_OPERATIONS_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/ADMIN_CONTROL_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/TELEGRAM_UX_v2.0.0.md`  
- `send/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/SYSTEM_INVARIANTS_v2.0.0.md`  
- `send/docs/canonical/active/FAILURE_RECOVERY_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/CHANNEL_CONFIG_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`  
- `send/docs/canonical/active/RISK_MODEL_v2.0.0.md`  

---

## 1. PURPOSE

This document defines the complete security architecture of BinaryBot.

Security objectives:

- Prevent unauthorized control of the bot
- Prevent signal manipulation
- Protect user data
- Prevent admin panel compromise
- Ensure audit integrity
- Prevent trading behavior tampering
- Prevent abuse of the outcome voting system
- Protect configuration integrity
- Ensure operational transparency

BinaryBot must be secure against:

- Unauthorized Telegram access
- Role escalation
- Message spoofing
- Outcome manipulation
- Configuration tampering
- Replay attacks
- Log corruption
- Operational sabotage

If security is compromised, the trading engine must immediately halt.

---

## 2. SECURITY PRINCIPLES

### 2.1 Least Privilege

Each user role receives only the permissions required to perform its tasks.

No role may have unnecessary privileges.

### 2.2 Defense in Depth

Security protections exist at multiple layers:

- Telegram access layer
- Role control layer
- Command validation layer
- Storage layer
- Observability layer
- Analytics layer

No single failure should compromise the system.

### 2.3 Deterministic Behavior

Security mechanisms must never alter trading logic.

Security protects the system but does not influence trading decisions.

### 2.4 Full Auditability

Every security-sensitive action must produce:

- Telegram proof log
- JSONL event log

No silent administrative changes are allowed.

---

## 3. SECURITY SURFACE OVERVIEW

BinaryBot has four main attack surfaces:

1. Telegram Control Interface
2. Signal Distribution System
3. Outcome Voting System
4. Server Configuration & Storage

Each surface requires dedicated protections.

---

## 4. TELEGRAM ADMIN ACCESS SECURITY

### 4.1 Role-Based Access Control

Access to the admin control panel is governed by `ADMIN_OPERATIONS_SPEC_v2.0.0.md`.

Supported roles:

- OWNER
- ADMIN
- ANALYST
- MODERATOR

Each role has defined permissions.

Unauthorized access attempts must be rejected.

### 4.2 User ID Validation

Every admin command must validate the Telegram `user_id` against the authorized user list.

Authorization must occur before command execution.

### 4.3 Role Escalation Prevention

A user cannot change their own role.

Role changes require OWNER authorization.

All role changes must generate an `admin_change` event in observability logs.

### 4.4 Admin Topic Restriction

Admin commands must only function inside the designated admin group or topic.

Commands executed outside the admin control environment must be rejected.

### 4.5 Telegram Transport Mode

BinaryBot should operate using long polling by default.

Webhook mode is optional but requires HTTPS endpoint protection.

If webhook mode is used:

- Endpoint must verify Telegram signature
- Endpoint must reject unknown sources

---

## 5. TELEGRAM COMMAND SECURITY

### 5.1 Command Source Validation

All commands must validate:

- Message sender ID
- Role permissions
- Command context (admin topic)

Commands received from unauthorized contexts must be ignored.

### 5.2 Replay Protection

Telegram messages may arrive twice.

The bot must detect duplicate command executions using:

- Message ID
- Timestamp
- Command hash

Duplicate commands must be ignored.

### 5.3 Command Rate Limiting

To prevent abuse or spam, admin commands must be rate limited.

Example limit: max 10 admin commands per minute.

Violations generate a warning event.

---

## 6. CONFIGURATION SECURITY

Configuration files include:

- `algo_params.json`
- `settings.json`
- `active_symbols.json`
- `channel_config.json`
- `dist_state.json`
- `focus_state.json`

### 6.1 Parameter Integrity

Strategy parameters must only change through controlled deployment.

Direct modification of `algo_params.json` during runtime is forbidden.

### 6.2 Atomic File Writes

All configuration writes must be atomic.

Use temporary files and rename operations to prevent partial writes.

### 6.3 File Permission Rules

Recommended Linux permissions:

- Owner: root or service account
- chmod: 600

No public read/write access allowed.

### 6.4 Configuration Tamper Detection

On startup the engine must validate:

- Parameter checksum
- File structure
- Version compatibility

Mismatch must trigger a critical configuration error and halt the engine.

---

## 7. SIGNAL DISTRIBUTION SECURITY

Signal distribution must prevent:

- Duplicate signals
- Unauthorized channel injection
- Signal replay

### 7.1 Signal ID Integrity

Each signal must include a `SIGNAL_ID`.

All stages (PRE / CONFIRM / OPEN_NOW) must reference the same ID.

### 7.2 Distribution Deduplication

Each tier must reject duplicates based on: `tier + SIGNAL_ID + stage`.

### 7.3 Channel Isolation

Each Telegram channel is treated as an isolated endpoint.

Publishing errors must not leak signals to other tiers.

### 7.4 Signal Authenticity

All official signals originate only from the configured bot account.

Users must be instructed to trust signals only from the official channel.

Signal messages must contain consistent formatting and `SIGNAL_ID`.

No trading decisions should be made based on messages forwarded from unknown sources.

---

## 8. OUTCOME SYSTEM SECURITY

The outcome system collects feedback from ELITE members.

Potential attack vectors include:

- Vote spamming
- Vote manipulation
- Multiple votes
- Automated voting bots

### 8.1 One Vote Per User Per Signal

Outcome service must enforce unique `(user_id, signal_id)`.

Duplicate votes must be rejected.

### 8.2 Vote Window Enforcement

Votes are only allowed during the period: `expiry + 5 minutes`.

Votes outside this window must be rejected.

### 8.3 Early Vote Blocking

Votes submitted before trade expiry must be rejected.

This prevents result prediction manipulation.

### 8.4 Outcome Anomaly Detection

Analytics must detect suspicious patterns:

- Repeated votes from same user
- Abnormal voting clusters
- Bots attempting vote automation

Anomaly events must be logged.

---

## 9. DATA PRIVACY

BinaryBot must protect user identity data.

Rules:

- Public channels must never expose user IDs
- Aggregated statistics only
- Individual stats available only to that user via DM

Outcome logs containing user IDs must remain server-side.

See also: `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` for the full privacy model.

---

## 10. LOG INTEGRITY

Observability logs are critical forensic evidence.

Rules:

- Logs must be append-only
- Log entries must never be overwritten
- Logs must be rotated safely

Log tampering must be detectable.

### 10.1 Log Tamper Detection

Optional but recommended: include hash chain verification.

Example concept: `entry_hash = SHA256(previous_hash + entry_data)`

This allows detection of deleted entries.

---

## 11. SERVER SECURITY

BinaryBot runs on a Linux server.

Recommended protections:

- Firewall enabled
- SSH key authentication only
- Password login disabled
- Regular system updates
- Monitoring for unusual CPU/network usage

---

## 12. API SECURITY

BinaryBot relies on external market data APIs.

Security requirements:

- API keys must not be hardcoded
- Store keys in environment variables
- Do not log API keys
- Handle API failures safely

API downtime must not crash the engine.

### 12.1 Telegram Bot Token Protection

Telegram bot tokens must never be stored inside source code.

Tokens must be stored in secure environment variables.

Example: `BOT_TOKEN` stored in `.env` or server environment.

Bot token must never appear in:

- Logs
- Stack traces
- Admin messages
- Exported datasets

---

## 13. DOS & ABUSE PROTECTION

The system must protect against:

- Command spam
- Vote spam
- Telegram rate-limit loops

Mechanisms:

- Command rate limits
- Message deduplication
- Distribution throttling

---

## 14. INCIDENT RESPONSE

If security compromise is suspected:

Immediate actions:

1. Activate Freeze Mode
2. Notify admin alerts channel
3. Preserve logs
4. Investigate source
5. Apply patch if required
6. Restart system safely

---

## 15. SECURITY MONITORING

The system must monitor:

- Unauthorized admin attempts
- Command spam
- Configuration tampering
- Log anomalies
- Suspicious outcome voting

Security alerts must appear in the ADMIN_ALERTS Telegram topic.

---

## 16. SECURITY GUARANTEE

If this security model is implemented correctly:

- Unauthorized control is prevented
- Signals cannot be manipulated
- Outcome data remains trustworthy
- Configuration integrity is preserved
- Audit trails remain intact
- System abuse becomes detectable

Security ensures BinaryBot remains reliable and trustworthy in a commercial environment.

---

## 17. CANONICAL VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.0 | 2026-07-12 | Promoted to active canonical status (OWNER-006 = A, canonical-reconciliation-01). Cross-references updated to canonical v2.0.0 paths. |
| 1.0.0 | — | Root-level source document: `send/docs/SECURITY_MODEL.md` |

---

*End of SECURITY_MODEL_v2.0.0.md*
