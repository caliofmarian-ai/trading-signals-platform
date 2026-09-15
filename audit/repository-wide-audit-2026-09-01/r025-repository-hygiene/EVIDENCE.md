# R-025 — Repository hygiene evidence

## Baseline

- Issue: #153 — `R-025 — Quarantine backup and orphan code from active repository authority`
- Branch baseline: `761893eccdb7dff6506995068e42aba3f3e85e76`
- Scope: repository hygiene only; no strategy mathematics, provider policy, Telegram RBAC, production variables, canonical-active content, or broker execution changes.

## Current classification

Existing BATCH-09 evidence already classified and removed the known orphan, dead, duplicate, and temporary artifacts, while preserving active/test-only files and `send/_archive/` as governance/historical evidence.

R-025 found five remaining live-adjacent development backups in `send/core/`:

| Live-adjacent path | Classification | Disposition | Preserved blob SHA |
|---|---|---|---|
| `send/core/signal_engine.py.bak_1772805524` | QUARANTINE/REMOVE from active authority | moved to `send/_archive/backups/` | `346c5565c4f107d9870cf5b2ec0e2e1b19d3b975` |
| `send/core/signal_engine.py.bak_envelope_fix` | QUARANTINE/REMOVE from active authority | moved to `send/_archive/backups/` | `f411b12b02f03bb6b8ad8f68c9c0fca798b68533` |
| `send/core/signal_engine.py.bak_fix` | QUARANTINE/REMOVE from active authority | moved to `send/_archive/backups/` | `f411b12b02f03bb6b8ad8f68c9c0fca798b68533` |
| `send/core/strategy_v2.py.bak_1772804197` | QUARANTINE/REMOVE from active authority | moved to `send/_archive/backups/` | `1cfa99aef34bd476068950a4c6ceada5b271dc0d` |
| `send/core/strategy_v2.py.bak_decision_audit` | QUARANTINE/REMOVE from active authority | moved to `send/_archive/backups/` | `aafb265f67180911cdf045d902ba1f7fc6401bf6` |

The move preserves the exact Git blob objects; it does not rewrite historical contents.

## Preserved historical authority boundaries

The following explicit history areas remain permitted and are not treated as live implementation:

- `send/_archive/**`
- `send/docs/_deprecated/**`
- `send/docs/canonical/deprecated/**`
- `audit/**`

Tracked backup artifacts already inside those explicit history areas are preserved.

## Prevention

`.gitignore` now blocks common tracked backup patterns under `send/**` while explicitly allowing the historical areas above.

`tests/batch_10/test_repository_hygiene.py` now scans the tracked `send/` tree and fails if a backup, editor temporary, patch reject/original, or ` - Copy` duplicate artifact appears outside explicit historical paths.

## Runtime/import safety

Repository code search and prior audit evidence classify the five moved files as development backup artifacts with no runtime impact. Active modules remain at their canonical non-backup paths. The R-025 change does not modify any executable production module.

## Validation contract

Acceptance requires:

1. focused repository-hygiene checks PASS;
2. full repository suite PASS;
3. `Required Repository CI` PASS on the exact PR head;
4. no broker-execution enablement or trading-behavior change.

Live CI evidence is recorded on the pull request / issue because it is generated after the branch head is pushed.
