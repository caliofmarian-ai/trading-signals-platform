# Canonical Telegram Callback Recovery Contract

Issue: #42

Parent: #23

Status: Implemented on a dedicated branch; live acceptance pending

## Authority

This corrective contract is subordinate to the active canonical documents:

- `TELEGRAM_UX_v2.0.0.md`
- `SECURITY_MODEL_v2.0.0.md`
- `FAILURE_RECOVERY_SPEC_v2.0.0.md`
- `TEST_PLAN_v2.0.0.md`
- `ADMIN_TREE_MAP_v2.0.0.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`

It also preserves the previously approved single-message and navigation-generation
contracts under `audit/telegram-ux-remediation-01/`.

## Audited pre-change behavior

| Callback family | Previous behavior | Failure |
|---|---|---|
| Stale `APP:` generation | Returned Home without callback feedback | Silent recovery; obsolete message could become the preferred edit target |
| Unknown callback | Replaced the panel with `Unknown action` and no keyboard | Dead end |
| Retired admin callback | Replaced the panel with retirement text and no keyboard | Dead end |
| Unauthorized `ADMIN_NAV:` | Replaced the protected panel with access-denied text | Modified a surface the caller was not authorized to navigate |

## Required behavior

### Stale application callback

- Reject the obsolete generation.
- Return to the role-scoped application Home.
- Display a non-empty callback notification.
- If a different active message is tracked, edit that active message and do not
  reactivate the obsolete callback message.
- If no active message is known, reuse the callback message rather than creating
  an unnecessary second panel.

### Unknown or retired callback in an authorized admin context

- Display a non-empty callback notification.
- Recover to canonical, role-scoped Admin Home.
- Render a valid keyboard from the current role model.
- Do not invoke a mutation handler.

An unknown or malformed `APP:` callback instead recovers to the public,
role-scoped application Home. It must never be reinterpreted as an admin route.

### Unauthorized callback

- Reject fail-closed.
- Display callback notification only.
- Do not send, edit, replace, or reveal an admin panel.
- Do not expose role-hidden buttons or content.

## Transport contract

- `core.bot_service.process_update()` may return `callback_ack_text` for a
  recovery callback.
- `runtime.telegram_updates.process_update()` delivers that text through
  `answerCallbackQuery`.
- Normal navigation retains an empty acknowledgement.
- Callback notification text is bounded to Telegram's 200-character limit.
- Vote/outcome acknowledgements retain their existing independent contract.

## Truth and safety boundaries

- Recovery text is static interaction guidance, not operational state.
- No runtime health, market state, configuration value, FSM state, signal truth,
  broker state, role assignment, or secret is embedded in recovery content.
- Operational pages continue to obtain values from runtime evidence, effective
  configuration, and persisted state.
- Recovery navigation is read-only and cannot bypass authorization or mutation
  audit boundaries.
