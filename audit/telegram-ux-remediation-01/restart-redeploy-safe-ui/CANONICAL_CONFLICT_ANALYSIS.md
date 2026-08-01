# Canonical Conflict Analysis

## Conflict
- Parent Issue #23 requires restart/redeploy-safe Telegram application behavior.
- Existing implementation documented active UI tracking as in-memory only.

## Canonical review outcome
- Active canonical docs do not require persisting message text/content.
- Active canonical docs require deterministic recovery posture, safe startup behavior, and no unsafe continuation on state issues.
- Runtime state persistence is already canonicalized in the existing storage/state framework.

## Decision
**Hybrid recovery is canonical and approved:**
1. Keep in-memory active UI map as runtime source for fast session routing.
2. Persist only minimal active-session metadata for restart/redeploy recovery.
3. Fail open for UI state corruption/unsupported schema (start with empty UI state) while keeping polling/runtime alive.

## Rationale
- Pure in-memory loses message reuse ability after restart.
- Pure persistence-only lookup is unnecessary and slower.
- Hybrid preserves single-message UX when safe, while avoiding startup hard-block on non-critical UI state corruption.
