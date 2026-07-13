# BATCH_06_FSM_CONTRACT

- Owner decision applied: OWNER-003 = A
- Prior decision applied: OWNER-004
- Findings addressed: GAP-002, GAP-014

## Canonical FSM owner

`core.fsm_runtime` is the authoritative state-access and transition layer for FSM lifecycle state.

## Live states used in BATCH-06

- `IDLE`
- `WATCHLIST`
- `CONFIRMED`
- `LIVE_SENT`
- `COOLDOWN`

## Transition rules implemented

| Input | Allowed previous state(s) | Result |
|---|---|---|
| `PRE` | `IDLE`, `WATCHLIST`, `CONFIRMED` | enters or refreshes watchlist with bounded lease |
| `CONFIRM` | `WATCHLIST`, `CONFIRMED` | moves to `CONFIRMED` |
| `OPEN_NOW` | `WATCHLIST`, `CONFIRMED`, `LIVE_SENT` | moves to `LIVE_SENT` before final release |
| `REJECT` | any | if focused/live, releases symbol into `COOLDOWN`; otherwise records reject evidence |
| `NO_SIGNAL` | any | no direct promotion; maintenance handles lease/cooldown expiry |

## Additional lifecycle behavior

- Missing `scan_scheduler` dependency removed.
- `_focus_state_path` dependency removed.
- Replacement-score updates now go through `fsm_runtime.update_symbol_replacement_score()`.
- Watchlist entries carry bounded lease metadata (`focus_enter_ts`, `focus_ttl_seconds`).
- Lease expiry triggers deterministic release into cooldown.
- Completed OPEN_NOW flow triggers watchlist removal and cooldown activation.
- Duplicate PRE refreshes do not create duplicate watchlist entries.
- Over-capacity PRE candidates may replace the weakest resident symbol deterministically; otherwise the transition is blocked explicitly.
- Cooldown is an absolute block for PRE/CONFIRM/OPEN_NOW until expiry.
- Cooldown expiry returns the symbol to `IDLE` explicitly.

## Observability

Every material FSM lifecycle mutation emits a canonical `fsm_transition` event payload validated by the BATCH-03 event schema.
