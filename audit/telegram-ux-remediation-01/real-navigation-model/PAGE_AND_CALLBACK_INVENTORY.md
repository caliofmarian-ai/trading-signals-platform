# Page and Callback Inventory

## APP pages

| Logical page | Live callback shape | Slash entry | Back target | Refresh target |
|---|---|---|---|---|
| Home | `APP:<generation>:HOME` | `/start` | — | — |
| Status | `APP:<generation>:STATUS` | `/status` | APP history parent or Home | `APP:<generation>:STATUS` |
| Help | `APP:<generation>:HELP` | `/help` | APP history parent or Home | — |
| Admin bridge/root entry | `APP:<generation>:ADMIN` | `/admin` | APP history parent or Home when applicable | — |
| Back | `APP:<generation>:BACK` | — | Pops one validated APP parent | — |

Unversioned `APP:ACTION` callbacks remain parser-compatible for legacy/unit coverage, but live renders now emit generation-qualified callbacks.

## Admin pages and context-bearing callbacks

| Surface | Callback(s) | Notes |
|---|---|---|
| Admin root | `ADMIN_NAV:HOME` | Canonical admin root; may also expose APP Back/Home row when reached from APP Home |
| Strategy profile | `PROFILE_HOME`, `PROFILE_CONFIRM:<profile>`, `PROFILE_EXEC:<profile>` | Cancel returns to profile selector; apply returns to selector/current-state page |
| Symbols (admin root) | `SYMBOLS_COV`, `SYM_TOGGLE:<sym>`, `SYMBOLS_ALL`, `SYMBOLS_NONE` | Home-context symbols retain Admin parent |
| Symbols (strategy context) | `SYMBOLS`, `SYM_TOGGLE:STRATEGY:<sym>`, `SYMBOLS_ALL:STRATEGY`, `SYMBOLS_NONE:STRATEGY` | Strategy-context mutations preserve Strategy parent |
| Files | `FILES_HOME`, `FILES:<dir>:<page>`, `FILE_DL:<dir>:<name>` | Prev/Next preserve directory and page |
| Docs | `GOVDOCS`, `DOCS`, `FILE_DL:doc:<name>` | Download keeps the listing message intact |
| Diagnose | `DIAGNOSE`, `OPS_DIAGNOSE`, `SH_DIAGNOSE` | Refresh stays on diagnose |
| Runtime audit | `AUDIT`, `OPS_AUDIT`, `SH_AUDIT`, `DIAG_SH_AUDIT`, `SECAUDIT_AUDIT` | Parent-specific error return path preserved |
| Roles reload | `RELOAD_ROLES_CONFIRM`, `RELOAD_ROLES_EXEC` | Cancel returns to Roles |
