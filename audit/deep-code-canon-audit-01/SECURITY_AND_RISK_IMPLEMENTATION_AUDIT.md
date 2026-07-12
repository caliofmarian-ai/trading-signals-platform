# SECURITY_AND_RISK_IMPLEMENTATION_AUDIT

## Security model alignment

### Authentication / secret handling
- Secrets are env-based (`TELEGRAM_BOT_TOKEN`, `TWELVE_DATA_API_KEY`), which is good baseline.
- Gaps:
  - no centralized boot-time required-secret validation;
  - Telegram-dependent modules raise at import time (`telegram_publisher.py:11-13`, `telegram_updates.py:18-19`) rather than controlled degraded startup.

### Authorization and privilege boundaries
- Positive:
  - `admin_permissions.py` defines roles, priorities, and explicit permissions.
  - `require_permission()` returns structured denial reason.
- Negative:
  - `bot_service.py` maintains a second RBAC model (`rbac.json`, `ADMIN_USER_ID`) separate from canonical roles.
  - `bot_service.in_admin_context()` returns `True` when `ADMIN_CONTROL_CHAT_ID` is unset (`79-82`) → fail-open admin boundary.
  - `admin_permissions.json` is unused, so file-based permission governance is illusory.

### Admin mutation paths
- `admin_commands.py` mutates strategy and symbol state directly via `_safe_write_json()`.
- No lock use around read-modify-write threshold/SR/spike updates (`265-285`).
- No call to `params_loader.validate_algo_params()` before save.
- Audit trail is append-only JSONL, but not canonical event-envelope logging.

### Outcome-security path
- Intended secure path:
  - elite membership via `getChatMember`
  - vote window using `activation_ts` / `vote_end_ts`
  - first-write-wins lock
- Broken in practice:
  - `telegram_updates.py` forwards same callback to `bot_service.process_update()` after `outcome_service.handle_vote_callback()`.
  - `bot_service` writes to `state/outcomes.json` without elite membership/window checks.
  - `outcome_service` non-member rejection path itself calls `log_warning` incorrectly (`178-186`), risking exception during denial.

### Fail-open / fail-closed behavior
| Area | Behavior | Assessment |
|---|---|---|
| Admin chat gating | Fail-open if chat id unset (`bot_service.py:79-82`) | Unsafe |
| Telegram boot dependency | Import-time fail-stop on missing token | Safer than silent run, but operationally abrupt |
| Scan scheduler missing | Exceptions swallowed in `update_symbol_replacement_score()` | Unsafe silent failure |
| Logger failures | `observability_logger.log_event()` swallows and reroutes to error log | Operationally survivable, but can mask audit loss |

## Risk model alignment

### Implemented risk controls
- SR gate: `strategy_v2.py:437-448,579-588`
- Spike filter: `strategy_v2.py:452-469,589-603`
- Feasibility/time gate: `strategy_v2.py:475-497,604-613`
- Threshold gating: `strategy_v2.py:688-695`
- Tier OPEN_NOW limits: `distribution_router.py:497-525,585-593`

### Missing / contradicted risk controls
- No active cooldown management despite FSM fields.
- No max concurrent exposure control in active runtime.
- No risk-based engine block/halt path integrated with `risk_monitor`.
- `risk_monitor.evaluate_risk()` is not wired into runtime and uses invalid logger call when tripped (`risk_monitor.py:33-44`).

## System invariants alignment
Major invariant breaches observed:
1. Engine runtime is not bootable because `signal_engine` imports a missing helper.
2. Canonical telemetry layer is absent.
3. Canonical event taxonomy is not respected by several producers.
4. Single-source control plane invariant is broken by dual admin stacks.
5. Signal outcome truth is split across two stores.

## Admin / role / parameter-control specific findings
- Hardcoded permission matrix vs unused config file.
- Hardcoded admin validation ranges vs ignored `admin_settings.json`.
- Hardcoded strategy defaults in `admin_commands._load_algo_params()` do not reflect `strategy_v2` runtime schema.
- Role config cache requires manual reload, with no file-change detection.

## Unsafe defaults
- `admin_commands.py:86-93` injects threshold/SR/spike defaults even if file missing.
- `distribution_router.DEFAULT_LIMITS` plus env-only override means file-configured limits may never apply.
- `strategy_v2.py` default thresholds 70/75/80 override config mismatch.

## External integration risks
- TwelveData client does not distinguish API auth failures from data-shape failures.
- Telegram outcome membership check depends on channel id env var, while distribution config also stores channel ids, creating split truth.

## Recovery / monitoring concerns
- Restart guard double-count bug can lock system unnecessarily.
- Health and metrics utilities are unwired, so operators may not see real failures.

## Security/risk summary
- Overall security posture: **contradictory to canon**.
- Highest-risk items:
  1. duplicate vote path bypassing elite/window controls;
  2. fail-open admin chat boundary in `bot_service`;
  3. unsafe/unlocked admin config writes;
  4. boot/import failures preventing predictable risk enforcement.
