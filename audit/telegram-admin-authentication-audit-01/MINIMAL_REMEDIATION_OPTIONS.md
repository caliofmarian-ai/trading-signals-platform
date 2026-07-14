# MINIMAL_REMEDIATION_OPTIONS

## Option 1 — Keep current strict chat gate (lowest change)
- No auth model changes.
- Operator guidance: run admin commands only in configured admin control chat.
- Add explicit docs/UX messaging only.

## Option 2 — Owner private-chat allowance, keep role model (small code delta)
- Allow owner ID in private chat for admin commands.
- Keep role/permission checks and audit logging.
- No password/session storage introduced.

## Option 3 — Hybrid chat + private owner (policy-driven)
- Allow admin chat for all authorized roles.
- Allow private chat only for owner or explicitly whitelisted roles.
- Optionally require confirmation for mutating commands.

## Option 4 — Add password/session layer (highest risk/complexity)
- Only if explicitly required by owner.
- Must include throttling, TTL, logout/revoke, secure storage, audit, and rotation.
- Strongly higher security/maintenance burden than options 1-3.
