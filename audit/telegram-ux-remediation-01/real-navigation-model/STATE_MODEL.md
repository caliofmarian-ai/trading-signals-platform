# State Model — Issue #38

**Scope:** Navigation state model for App and Admin navigation  
**Date:** 2026-08-02  
**Issue:** #38 — Implement real Back, Home, and Refresh navigation

---

## 1. APP: Navigation State

### Per-Session Bounded History Stack

Location: `send/core/telegram_app_nav.py`

```python
_NAV_HISTORY_MAX_DEPTH: int = 5  # Bounded to prevent loops

_nav_history: Dict[_SessionKey, List[str]] = {}
_nav_history_lock = threading.Lock()
```

**Session key type:** `Tuple[int, int, Optional[int]]` = `(chat_id, user_id, thread_id)`  
Normalized via `normalize_session_key()` — same isolation contract as the active UI message state.

### State Operations

| Function | Description | Thread-safe |
|----------|-------------|-------------|
| `push_nav_action(user_id, *, chat_id, action, thread_id)` | Push action to bounded stack | ✅ |
| `pop_nav_action(user_id, *, chat_id, thread_id)` | Pop most recent action | ✅ |
| `nav_can_go_back(user_id, *, chat_id, thread_id)` | True if history non-empty | ✅ |
| `clear_nav_history(user_id, *, chat_id, thread_id)` | Clear history (on /start reset) | ✅ |

### Stack Invariants

1. **Bounded:** `len(stack) <= _NAV_HISTORY_MAX_DEPTH` at all times
2. **No consecutive duplicates:** Push is suppressed if `stack[-1] == action`
3. **HOME excluded from recursive Back:** `handle_app_action(BACK)` skips ACT_HOME entries
4. **BACK excluded from recursive Back:** `handle_app_action(BACK)` skips ACT_BACK entries
5. **Restart-safe:** History is in-memory only; empty history → safe fallback to Home

### BACK Resolution Algorithm

```
handle_app_action(BACK, user_id, role, ..., chat_id, thread_id):
    parent = pop_nav_action(user_id, chat_id=resolved_chat_id, thread_id=thread_id)
    if parent and parent not in (BACK, HOME):
        return handle_app_action(parent, user_id, role, ...)  # render parent page
    else:
        return render_welcome_page(user_id, role, ...)  # safe fallback
```

---

## 2. ADMIN_NAV: Navigation State

### Static Parent Map

Location: `CANONICAL_ADMIN_PARENT_MAP` in `send/core/telegram_admin_ui.py`

The admin tree parent is **statically defined** (the admin tree is a deterministic DAG).
No runtime state is required for Back navigation in the admin tree.

Context-sensitive pages (OPS_ENGINE, SH_ENGINE, OPS_DIAGNOSE, SH_DIAGNOSE) encode
their parent in the markup at render time via the `parent_action` parameter.

### Context-Sensitive Markup Parameters

| Function | New Parameter | Default | Purpose |
|----------|--------------|---------|---------|
| `symbols_toggle_markup(...)` | `parent_action: str = "HOME"` | `"HOME"` | Back/Refresh target |
| `engine_markup(...)` | `parent_action: str = "HOME"` | `"HOME"` | Back label and target |
| `diagnose_markup(...)` | `parent_action: str = "HOME"` | `"HOME"` | Back label and target |

### Bot Service Dispatch Updates

| Admin Action | parent_action Passed |
|-------------|---------------------|
| SYMBOLS_COV | `"HOME"` |
| SYMBOLS | `"STRATEGY"` |
| OPS_ENGINE | `"OPERATIONS"` |
| SH_ENGINE | `"SYSHEALTH"` |
| OPS_DIAGNOSE | `"OPERATIONS"` |
| SH_DIAGNOSE | `"SYSHEALTH"` |
| DIAGNOSE (general) | `"HOME"` |
| ENGINE (slash cmd) | `"HOME"` |

---

## 3. /start Hard Reset

On `/start`:
1. `prepare_start_hard_reset()` is called
2. This clears the active message state (existing behavior)
3. **New:** `clear_nav_history()` is called to clear navigation history

This prevents Back from navigating into stale pre-reset history after a `/start` hard reset.

---

## 4. Concurrency Safety

| Component | Lock | Scope |
|-----------|------|-------|
| `_nav_history` | `_nav_history_lock` (threading.Lock) | Per-session stack ops |
| `_active_ui` | `_active_ui_lock` (threading.RLock) | Active message ops (pre-existing) |
| `_RESET_GUARDS` | `_RESET_GUARD_LOCK` (threading.Lock) | /start reset guards (pre-existing) |

The navigation history lock is a simple `threading.Lock` (non-reentrant) since no
recursive locking pattern is needed.

---

## 5. Memory Footprint

- Each history entry: one string (action key, typically 6–20 chars)
- Max depth: 5 entries per session
- Same session-count bounds as `_active_ui` (bounded by `_ACTIVE_UI_MAX_SESSIONS`)
- No persistence: in-memory only; negligible footprint

---

## 6. Restart/State-Loss Fallback

| Scenario | Behavior |
|---------|---------|
| Process restart | History lost; BACK returns Home |
| Redeploy | History lost; BACK returns Home |
| `/start` command | History cleared explicitly; BACK returns Home |
| Browser session cleared | History lost; BACK returns Home |
| Empty history (fresh session) | BACK returns Home (no error) |

In all cases, BACK produces a valid, navigable page with no dead ends.
