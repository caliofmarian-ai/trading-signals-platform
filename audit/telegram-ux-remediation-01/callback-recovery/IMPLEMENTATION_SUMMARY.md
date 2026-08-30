# Callback Recovery Implementation Summary

Issue: #42

Parent: #23

## Implementation

### `send/core/bot_service.py`

- Classifies stale, unknown, retired, and unauthorized callback recovery.
- Returns an explicit callback-notification result to the Telegram transport.
- Selects a recovery edit target without reviving an obsolete callback message.
- Rebuilds authorized unknown/retired routes through the canonical role-scoped
  Admin Home renderer.
- Rejects unauthorized routes without any interactive send or edit.
- Preserves normal navigation, vote/outcome processing, file delivery, mutation
  handlers, authorization checks, and active-message persistence.

### `send/runtime/telegram_updates.py`

- Consumes optional recovery notification text returned by `bot_service`.
- Delivers recovery feedback through `answerCallbackQuery`.
- Keeps normal callbacks on an empty acknowledgement.
- Bounds notification text to 200 characters.

### Tests

- Adds focused canonical callback-recovery coverage.
- Updates prior expectations that unauthorized callbacks overwrite the active
  navigation panel.
- Proves that recovery does not widen analyst-visible admin branches.
- Proves that the vote acknowledgement path remains separate.

## Superseded work

Draft PR #40 is not used as the delivery branch. It is based on an older main,
conflicts with the merged Owner Knowledge Layer, and does not enforce the final
active-message target selection or authorized Admin Home recovery contract.
