# BATCH_06_MIGRATION_CONTRACT

- Owner decision applied: OWNER-003 = A
- Findings addressed: GAP-018 (plus BATCH-06 prerequisites for GAP-002/GAP-009/GAP-014)

## Migration sources and targets

| Legacy compatibility source | Canonical target | Behavior |
|---|---|---|
| `focus_state.json` at runtime root | `state/focus_state.json` | Read legacy once, validate, atomically write canonical target, never write legacy |
| `dist_state.json` at runtime root | `state/dist_state.json` | Same |
| `restart_guard.json` at runtime root | `state/restart_guard.json` | Same |
| `active_symbols.json` at runtime root | `config/active_symbols.json` | Same |
| `settings.json` at runtime root | `config/admin_settings.json` | Same, using compatibility-only buffer-mode carry-forward |

## Contract rules implemented

1. Detect legacy artifacts explicitly.
2. Validate legacy JSON before migration.
3. Validate canonical JSON before treating it as authoritative.
4. If canonical and legacy are identical, accept canonical and emit duplicate-state warning evidence.
5. If canonical and legacy conflict, raise `StateConflictError` and stop clearly.
6. If canonical is missing and legacy is valid, atomically materialize canonical state and emit migration warning evidence.
7. Legacy files are retained as rollback evidence but receive no future live writes.
8. Re-running the same migration is idempotent.

## Invalid / ambiguous cases

- Invalid legacy JSON -> `StateValidationError`
- Invalid canonical JSON -> `StateValidationError`
- Conflicting legacy/canonical payloads -> `StateConflictError`
- Multiple conflicting legacy payloads -> `StateConflictError`

## Rollback behavior

- The legacy source file is left untouched.
- The canonical segmented file is the only live authority after migration.
- Snapshot restore logic can restore canonical segmented files only after payload validation.
