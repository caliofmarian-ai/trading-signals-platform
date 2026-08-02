# Implementation Summary — Issue #38

**Branch:** `copilot/copilotrefs-38-real-navigation-model`  
**Date:** 2026-08-02  
**Issue:** #38 — Implement real Back, Home, and Refresh navigation  
**Parent:** #23  
**PR:** Refs #38

---

## Problem Statement

The Telegram UI navigation had three gaps:

1. `telegram_app_nav` had `ACT_HOME`, `ACT_STATUS`, `ACT_HELP`, `ACT_ADMIN` but no `ACT_BACK` and no bounded navigation history model.
2. Most Admin panel pages mapped Back directly to `ADMIN_NAV:HOME` (admin root) instead of the immediate canonical parent.
3. Context-sensitive pages (Engine from Operations vs. Engine from System Health; Diagnose from Operations vs. Diagnose from System Health) always returned to Admin Home, discarding caller context.

---

## Implementation

### 1. `send/core/telegram_app_nav.py`

**Added:**
- `ACT_BACK = "BACK"` — canonical Back action constant
- `_NAV_HISTORY_MAX_DEPTH = 5` — bounded stack depth
- `_nav_history: Dict[_SessionKey, List[str]]` — per-session navigation history
- `_nav_history_lock: threading.Lock` — concurrency-safe history access
- `push_nav_action(user_id, *, chat_id, action, thread_id)` — push with dedup and bound enforcement
- `pop_nav_action(user_id, *, chat_id, thread_id)` — pop and return, None if empty
- `nav_can_go_back(user_id, *, chat_id, thread_id)` — predicate
- `clear_nav_history(user_id, *, chat_id, thread_id)` — called on /start hard reset

**Updated:**
- `handle_app_action()` — new optional `chat_id` and `thread_id` parameters; handles `ACT_BACK` by popping history and rendering parent (or falling back to Home)
- `prepare_start_hard_reset()` — calls `clear_nav_history()` to prevent stale pre-reset Back navigation

### 2. `send/core/telegram_admin_ui.py`

**Added:**
- `_PANEL_BACK_LABELS: dict[str, str]` — human-readable Back button label suffixes
- `CANONICAL_ADMIN_PARENT_MAP: dict[str, str]` — static canonical parent map for admin tree

**Updated:**
- `strategy_markup()` — Back button changed from `⬅️ Admin` → `HOME` to `⬅️ Operations` → `OPERATIONS`
- `symbols_toggle_markup()` — added `parent_action: str = "HOME"` parameter; Back label/target and Refresh target depend on context
- `engine_markup()` — added `parent_action: str = "HOME"` parameter; Back label/target depends on context
- `diagnose_markup()` — added `parent_action: str = "HOME"` parameter; Back label/target depends on context

### 3. `send/core/bot_service.py`

**Added:**
- `BACK` admin action handler in `_handle_admin_navigation_action` — falls back to HOME

**Updated:**
- `SYMBOLS_COV` action: passes `parent_action="HOME"` to `symbols_toggle_markup`
- `SYMBOLS` action: new explicit handler with `parent_action="STRATEGY"`
- `OPS_ENGINE` action: passes `parent_action="OPERATIONS"` to `engine_markup`
- `SH_ENGINE` action: passes `parent_action="SYSHEALTH"` to `engine_markup`
- `OPS_DIAGNOSE` action: passes `parent_action="OPERATIONS"` to `diagnose_markup`
- `SH_DIAGNOSE` action: passes `parent_action="SYSHEALTH"` to `diagnose_markup`
- `DIAGNOSE` (general): passes `parent_action="HOME"` to `diagnose_markup`
- `_admin_reply_markup("/symbols", ...)`: passes `parent_action="HOME"`
- `_admin_reply_markup("/engine", ...)`: passes `parent_action="HOME"`
- `_admin_reply_markup("/diagnose", ...)`: passes `parent_action="HOME"`

---

## Design Decisions

### APP: History Model vs. Static Parent Map
APP: pages are currently one level deep (Status, Help, Admin from Home). A bounded history stack is implemented for correctness and future extensibility. In practice, BACK from any APP: page returns Home (or the last pushed page before it).

### ADMIN_NAV: Static Parent Map vs. History
The admin tree is a deterministic DAG with a known canonical parent for each node. A static parent map (`CANONICAL_ADMIN_PARENT_MAP`) provides bounded, loop-free, restart-safe Back navigation without runtime state. Context-sensitive pages encode their parent in the markup at render time.

### No Separate BACK Callback for Admin Tree
Admin Back navigation uses the canonical parent action directly (e.g., `ADMIN_NAV:OPERATIONS`, not `ADMIN_NAV:BACK`) so the Back button always encodes the exact destination. This is simpler, more predictable, and eliminates the need for a server-side history in the admin context.

### Refresh Context Preservation
`symbols_toggle_markup` Refresh targets `SYMBOLS_COV` (admin-home context) or `SYMBOLS` (strategy context) based on `parent_action`. This ensures that pressing Refresh on the symbols toggle page preserves the correct Back context for subsequent navigation.

---

## Constraint Verification

| Constraint | Verified |
|-----------|---------|
| Single-message contract preserved | ✅ |
| `/start` visibility repair preserved | ✅ |
| `(chat_id, user_id, thread_id)` isolation | ✅ |
| Owner-private/Admin-topic authorization | ✅ |
| Role-hidden surfaces preserved | ✅ |
| Reuse `telegram_app_nav`, `telegram_admin_ui` | ✅ |
| No second router | ✅ |
| No secrets/message content in nav state | ✅ |
| No automatic merge | ✅ |

---

## Live Checklist

- [x] `ACT_BACK` constant defined
- [x] Bounded navigation history (max depth 5) per session
- [x] `push_nav_action`, `pop_nav_action`, `nav_can_go_back`, `clear_nav_history` implemented
- [x] `handle_app_action(BACK)` returns parent or Home (restart-safe)
- [x] `/start` hard reset clears navigation history
- [x] `CANONICAL_ADMIN_PARENT_MAP` defined
- [x] `strategy_markup()` Back → OPERATIONS
- [x] `symbols_toggle_markup(parent_action)` Back and Refresh context-aware
- [x] `engine_markup(parent_action)` Back context-aware
- [x] `diagnose_markup(parent_action)` Back context-aware
- [x] bot_service.py SYMBOLS_COV, SYMBOLS, OPS_ENGINE, SH_ENGINE, OPS_DIAGNOSE, SH_DIAGNOSE correct parents
- [x] bot_service.py BACK admin handler
- [x] 59 focused Issue #38 tests pass
- [x] 695 total tests pass (all existing + new)
- [x] Audit documents created
- [x] Branch pushed: `copilot/copilotrefs-38-real-navigation-model`
- [x] Draft PR opened targeting main
