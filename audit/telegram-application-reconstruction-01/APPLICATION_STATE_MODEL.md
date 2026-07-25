# APPLICATION_STATE_MODEL.md

BinaryBot — Application State Model  
Audit: telegram-application-reconstruction-01

---

## 1. STATE MODEL OVERVIEW

The Telegram application maintains state through Telegram's own inline keyboard infrastructure. There is no separate server-side session state per user because:
- Telegram's inline keyboard provides navigation context via `callback_query.message`
- The bot dispatches on callback action strings to determine which panel to render
- Panel content is generated fresh on each navigation action using live system state

This is the correct Telegram application pattern: lightweight, stateless server, with navigation state encoded in the message+keyboard pair.

---

## 2. NAVIGATION STATE

Navigation state is maintained implicitly:
- The current "page" is determined by which inline keyboard is attached to the bot message
- Navigating back uses the `HOME` action which re-renders the admin home with the canonical tree
- Sub-panel navigation uses dedicated action strings (e.g., `OPERATIONS`, `DECISION_VIS`)

### State Transition Model

```
Entry: /admin command or HOME callback
  → Admin Home rendered with role-scoped canonical tree
  → User selects a panel (e.g., OPERATIONS)
  → Operations panel rendered, back button present
  → User selects a sub-action (e.g., OPS_ENGINE)
  → Engine state rendered, back button returns to Admin Home
```

Each callback action results in:
1. Panel content text being generated
2. Appropriate panel markup (keyboard) being returned
3. Existing message being edited (if message_id available) or new message sent

---

## 3. SYSTEM STATE (READ-ONLY VISIBILITY)

The admin UX exposes read-only views of the following system state:

| State Component | Source | Panel |
|---|---|---|
| Engine running/paused/frozen | runtime_status.read_status() | Operations, System Health |
| FSM watchlist/mode | fsm_runtime.load_state() | Operations |
| Market data state | runtime_status.read_status() | System Health |
| Last decision event | _last_decision_event() (engine_events.jsonl) | Decision Visibility |
| Active symbols | _load_active_symbols() (active_symbols.json) | Symbols & Coverage |
| Strategy parameters | _load_algo_params() (algo_params.json) | Operations (via strategy refs) |
| Latest report | _find_latest_report_json() (analytics/reports/) | Research & Analytics |
| Docs list | handle_docs_list() (docs/) | Governance & Docs |
| Affiliate scope | get_affiliate_scope() | Affiliate / Partner |
| Role configuration | load_roles_config() | Roles & Identity |
| Admin events log | admin_events.jsonl | Security & Audit |

---

## 4. MUTATION STATE

Mutations affect future system state (canonical requirement: future-facing mutation only).

| Mutation | Panel | Handler | Audit |
|---|---|---|---|
| Symbol toggle | Symbols & Coverage | handle_symbols_toggle() | _audit() via admin_commands |
| Symbols all/none | Symbols & Coverage | handle_symbols_all/none() | _audit() via admin_commands |
| Strategy profile | Operations → Strategy | handle_strategy_profile() | _audit() via admin_commands |
| Threshold change | Operations → Strategy | handle_admin_command("/thresholds ...") | _audit() via admin_commands |
| SR multiplier change | Operations → Strategy | handle_admin_command("/sr ...") | _audit() via admin_commands |
| Spike filter change | Operations → Strategy | handle_admin_command("/spike ...") | _audit() via admin_commands |
| Roles reload | Roles & Identity | reload_roles_config() | logged in admin_events |

---

## 5. RATE LIMIT STATE

Per-operation rate limiting is enforced via `_RATE_STORE` in bot_service.py:

| Operation | Limit |
|---|---|
| files_list | 20/minute |
| file_download | 10/minute |
| diagnose | 5/minute |
| audit_runtime | 3/minute |
| mutation | 30/minute |

This state is in-memory and per-process. It is not persisted across restarts.

---

## 6. OUTCOME VOTE STATE

Outcome votes are persisted through outcome_service.py. The application state for outcomes:
- Signal ID → outcome mapping stored in outcomes.json
- Single-vote rule enforced: once accepted, subsequent votes for same user+signal are rejected
- Voting window enforced: delayed activation, bounded window

---

## 7. MISSING CANONICAL STATE (GAPS NOT DEFINED IN CANONICAL DOCS)

The following state management aspects are NOT explicitly defined in the canonical documentation:

| State Aspect | Status | Justification |
|---|---|---|
| Per-user panel navigation history | Not defined canonically | Implementation decision: not tracked; HOME always returns to root |
| Sub-panel return target | Not defined canonically | Implementation decision: all back buttons return to Admin Home (root) |
| Server-side session per user | Not defined canonically | Implementation decision: stateless; Telegram message carries state |
| Panel auto-refresh interval | Not defined canonically | Implementation decision: manual refresh via Refresh button |
