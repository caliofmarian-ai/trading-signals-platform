# CALLBACK_AND_ROUTE_REGISTER.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Document: CALLBACK_AND_ROUTE_REGISTER.md  
Status: RECONSTRUCTION AUDIT

---

## PURPOSE

This register documents every callback and slash command route in the Telegram application,
including dispatch order, handler, authorization requirement, and response model.

---

## DISPATCH ORDER IN process_update()

1. Message (text command path)
   a. `/start` → `telegram_app_nav.render_welcome_page` → `_send_app_nav_reply`
   b. `/help` → `telegram_app_nav.render_help_page` → `_send_app_nav_reply`
   c. `/status` → `telegram_app_nav.render_status_page` → `_send_app_nav_reply`
   d. Admin commands → `_can_run_admin_command` gate → `_render_panel_for_command`
   e. Unknown → "Unknown command. Use /help to view available commands."

2. Callback query path
   a. `APP:*` prefix → `telegram_app_nav.parse_app_action` → `handle_app_action` → edit message
   b. `ADMIN_NAV:*` prefix → `telegram_admin_ui.parse_action` + admin context gate → `_handle_admin_navigation_action` → edit message
   c. `VOTE_|*` prefix → `outcome_service.handle_vote_callback`
   d. `VOTE_*` prefix → `outcome_service.handle_vote_callback_data`
   e. `OUTCOME:*` prefix → `outcome_service.handle_vote_callback`
   f. Retired callbacks → retired message
   g. Unknown → "Unknown action."

---

## APP: CALLBACK REGISTER

Prefix: `APP:`  
Handler: `telegram_app_nav.handle_app_action`  
Context: Any chat (no admin context check)  
Message model: Edit originating message; fallback send new

| Callback | Action Constant | Handler Page | Roles |
|---|---|---|---|
| APP:HOME | ACT_HOME | render_welcome_page | All |
| APP:STATUS | ACT_STATUS | render_status_page | All |
| APP:HELP | ACT_HELP | render_help_page | All |
| APP:ADMIN | ACT_ADMIN | Admin info page | OWNER (informational for others) |

---

## ADMIN_NAV: CALLBACK REGISTER

Prefix: `ADMIN_NAV:`  
Handler: `bot_service._handle_admin_navigation_action`  
Context: Admin control topic OR owner private DM  
Message model: Edit originating message; fallback send new

| Callback | Handler | Roles |
|---|---|---|
| ADMIN_NAV:HOME | admin_home_markup | Admin tiers |
| ADMIN_NAV:OPERATIONS | operations_markup | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:OPS_ENGINE | engine state | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:OPS_DIAGNOSE | diagnose | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:SYMBOLS_COV | symbols toggle markup | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:DECISION_VIS | debug snapshot | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST |
| ADMIN_NAV:DISTRIBUTION | distribution panel | OWNER, PRIMARY_ADMIN |
| ADMIN_NAV:RESEARCH | research panel | OWNER, PRIMARY_ADMIN, RESEARCH_ADMIN, ANALYST |
| ADMIN_NAV:INTELLIGENCE | intelligence panel | OWNER, PRIMARY_ADMIN, RESEARCH_ADMIN, ANALYST |
| ADMIN_NAV:AFFILIATE | affiliate scope | OWNER, PRIMARY_ADMIN, AFFILIATE_ADMIN |
| ADMIN_NAV:ROLES | roles panel | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST, MODERATOR, AFFILIATE_ADMIN |
| ADMIN_NAV:ROLES_RELOAD | reload roles | OWNER, PRIMARY_ADMIN |
| ADMIN_NAV:SYSHEALTH | system health | OWNER, PRIMARY_ADMIN, MODERATOR |
| ADMIN_NAV:SH_ENGINE | engine state | OWNER, PRIMARY_ADMIN, MODERATOR |
| ADMIN_NAV:SH_DIAGNOSE | diagnose | OWNER, PRIMARY_ADMIN, MODERATOR |
| ADMIN_NAV:SH_AUDIT | audit | OWNER, PRIMARY_ADMIN |
| ADMIN_NAV:GOVDOCS | docs list | OWNER, PRIMARY_ADMIN |
| ADMIN_NAV:SECAUDIT | security audit | OWNER, PRIMARY_ADMIN |
| ADMIN_NAV:SECAUDIT_AUDIT | runtime audit | OWNER, PRIMARY_ADMIN |
| ADMIN_NAV:DIAGNOSE | diagnose (universal) | Admin tiers with diagnostics.view |
| ADMIN_NAV:AUDIT | runtime audit (universal) | Admin tiers with diagnostics.view |
| ADMIN_NAV:SYM_TOGGLE:* | symbol toggle | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:SYM_ALL | all symbols on | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:SYM_NONE | all symbols off | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:FILES:* | file list | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN |
| ADMIN_NAV:FILE_DL:* | file download | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN |
| ADMIN_NAV:PROFILE_CONFIRM:* | confirm profile | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:PROFILE_EXEC:* | execute profile | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| ADMIN_NAV:REPORT_DL | download report | OWNER, PRIMARY_ADMIN, RESEARCH_ADMIN, ANALYST |

---

## SLASH COMMAND REGISTER

| Command | Access | Handler | Response Model |
|---|---|---|---|
| /start | All | render_welcome_page | Send (tracked as active UI message) |
| /help | All | render_help_page | Send (tracked as active UI message) |
| /status | All | render_status_page | Send (tracked as active UI message) |
| /admin | Admin context / owner DM | admin_home_markup | Send (not tracked as app nav message) |
| /strategy | Admin context | strategy panel | Send |
| /thresholds | Admin context | thresholds panel | Send |
| /sr | Admin context | SR panel | Send |
| /spike | Admin context | spike filter panel | Send |
| /symbols | Admin context | symbols toggle | Send |
| /engine | Admin context | engine state | Send |
| /debug | Admin context | debug snapshot | Send |
| /report | Admin context | research panel | Send |
| /files | Admin context | file browser | Send |
| /docs | Admin context | docs list | Send |
| /download | Admin context | file download | send_document |
| /log | Admin context | log export | send_document |
| /diagnose | Admin context | diagnose panel | Send |
| /audit_runtime | Admin context | audit panel | Send |
| /roles | Admin context | roles panel | Send |
| /affiliate | Admin context | affiliate panel | Send |
| /roles_reload | Admin context | reload roles | Send |

---

## OUTCOME VOTE CALLBACKS (Unrelated to admin/app nav)

| Callback prefix | Handler | Access |
|---|---|---|
| VOTE_|*|* | outcome_service.handle_vote_callback | Public (any user who can see signal message) |
| VOTE_* | outcome_service.handle_vote_callback_data | Public |
| OUTCOME:* | outcome_service.handle_vote_callback | Public (legacy format) |

---

## RETIRED CALLBACKS (Intercepted with safe message)

```python
_RETIRED_ADMIN_CALLBACKS = frozenset({
    "ADMIN_STATUS",
    "ADMIN_SET_BUFFER",
    "ADMIN_SET_SYMBOLS",
    "ADMIN_RESEARCH",
    "ADMIN_DOCS",
    "ADMIN_BACK",
})
_RETIRED_ADMIN_PREFIXES = ("BUFFER_", "SYM_TOGGLE:", "DOC:")
```

These stale callbacks return a clear "retired panel" message and no keyboard.

---

End of CALLBACK_AND_ROUTE_REGISTER.md
