# R-026 — Production documentation reality evidence

## Scope

Issue #154 — refresh root README and operator documentation after upstream repository/runtime remediation.

Documentation-only ownership is preserved. This lane does not change provider behavior, strategy mathematics, Telegram permission authority, canonical-active content, CI workflow mechanics, Railway runtime code, production variables, or broker execution.

## Source baseline used for the refresh

Branch baseline: `ad76434a66dce6bdf1ae274c289d81d91bd02161`.

Relevant completed upstream work visible in that baseline:

- R-022 permanent repository CI/protected-main gate;
- R-023 dependency security compatibility upgrade;
- R-024 active-canonical status reconciliation and inventory guard;
- R-025 repository backup/orphan hygiene;
- R-017 source/config reconciliation for the verified live PRIMARY_ADMIN identity and real Admin topic context.

## Canonical evidence

`send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md` declares itself the sole authoritative Master Index and declares 43 unique active functional specifications.

Issue #137 remains open. Its four temporal-market-intelligence specifications are stored under `send/docs/canonical/transitional/` and remain non-active. The Issue #137 promotion contract states that activating all four would require a coherent successor canonical update and would change the active functional inventory from 43 to 47.

Therefore R-026 documents 43 as active and explicitly labels the four temporal candidates non-active.

## Runtime/source evidence

- `send/runtime/engine_loop.py` defines `ENGINE_TICK_SECONDS = 2` and calls the governed signal-engine path on that cadence.
- Provider control supports `FINNHUB` and `TWELVE_DATA`.
- Finnhub has an explicit effective-symbol lock to `EUR/USD`.
- `send/config/active_symbols.json` contains a broader configured symbol universe; the documentation explicitly separates configured universe from provider-effective scope.
- `scripts.railway_start` is the production start module referenced by `railway.json`.
- `scripts.railway_init` preserves existing `/data/config/` files instead of overwriting them on every deploy.
- Strategy Auditor local scheduling requires a valid runtime enable flag plus local `HH:MM` and IANA timezone inputs, and can also be disabled by Admin settings.

## CI evidence

`.github/workflows/repository-ci.yml` defines stable job/check name `Required Repository CI`, checks out and verifies the exact change-head SHA, and executes critical compilation/regressions plus the full repository test suite.

R-026 adds `tests/repository_governance/test_r026_documentation_reality.py` so future documentation drift is mechanically detectable.

## Live Railway evidence used

During the R-026 refresh, production Railway directly reported:

- project/service `trading-signals-platform`;
- branch `main` as the source;
- one persistent volume mounted at `/data`, 5 GB, region `europe-west4-drams3a`;
- deployment `9c59d1d4-4e85-4520-b50a-0a120325baef` for commit `ad76434a66dce6bdf1ae274c289d81d91bd02161` reached terminal `SUCCESS`;
- Telegram UI state initialized from `/data/state/telegram_ui_state.json` with payload status `ok`;
- Telegram poller emitted `poller_started`.

Railway OAuth exposes variable names but redacts values. R-026 therefore does not claim current selected provider value, `SHADOW_MODE`, or broker-execution value from connector inspection alone. The operator documentation requires runtime evidence for those effective values.

## Telegram acceptance truth

Issue #131 remains open.

R-017 is currently:

- `SOURCE VERIFIED`;
- `CI VERIFIED`;
- `DEPLOYED` on the corrected production commit;
- final real post-fix PRIMARY_ADMIN `/admin` journey in the actual `ADMIN_COMMANDS` topic: `PENDING`.

R-026 keeps that distinction explicit. Automated tests or a successful container deployment are not represented as live Telegram acceptance.

## Known separate observability finding

Issue #174 records that healthy `TELEGRAM_UI_STATE_INITIALIZED` / `poller_started` events are currently emitted on stderr and surfaced by Railway as error severity, and that `runtime_instance_id` may prefer placeholder `RUN_ID=replace-me` over the real deployment ID.

R-026 documents this as a known observability defect rather than misreporting the successful deployment as failed.

## Acceptance contract

R-026 is ready for integration only when:

1. root README and operator runbook match this verified source/runtime evidence;
2. no stale Master Index v1 link is presented as current authority;
3. UNKNOWN/PENDING evidence remains explicit;
4. temporal candidates remain non-active in documentation;
5. broker execution is not enabled or instructed by the documentation;
6. documentation regression checks pass;
7. `Required Repository CI` passes on the exact current PR head.
