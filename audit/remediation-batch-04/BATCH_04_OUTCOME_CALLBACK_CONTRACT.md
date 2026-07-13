# BATCH_04_OUTCOME_CALLBACK_CONTRACT

## Applied authority
- Canon: `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- Canon: `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md`
- Canon: `SECURITY_MODEL_v2.0.0.md`
- OWNER-002 boundary respected: no broad `bot_service.py` retirement

## Canonical callback path
1. `runtime.telegram_updates.process_update(update)`
2. `outcome_service.handle_vote_callback_data(callback_data=..., user_id=..., chat_id=..., message_id=...)`
3. `outcome_service.handle_vote_callback(...)`
4. `telegram_updates._answer_callback_query(...)`

## Legacy forwarding boundary
- `bot_service.py` no longer performs independent VOTE-store mutation
- If the legacy dispatcher receives a VOTE callback, it forwards to `outcome_service`
- Admin/control-plane logic outside VOTE forwarding remains for BATCH-05

## Callback identity and idempotency contract
- Parser expects exact format: `VOTE_|<signal_id>|<outcome>`
- Allowed outcomes:
  - `WIN`
  - `LOSE`
  - `MISSED`
- Stable vote key: `signal_id|member_ref`
- Stable callback dedup key: `signal_id|member_ref|outcome|chat_id|message_id`
- Replay result for the same callback identity: `accepted=True`, `reason=already_processed`
- No duplicate raw vote record is written for replays
- No duplicate accepted `user_outcome` event is emitted for replays

## Security and context validation
- Membership check occurs before mutation
- Missing security configuration fails closed:
  - `TELEGRAM_BOT_TOKEN`
  - `ELITE_CHANNEL_ID`
  - `COMMUNITY_FEEDBACK_SALT`
- Callback context must match a registered `(chat_id, message_id)` pair from `register_open_now(...)`
- Unknown `signal_id` is rejected
- Unauthorized callback context is rejected before mutation

## Privacy and pseudonymization
- Raw Telegram user IDs are not persisted in vote records
- Stable pseudonym format: `M-<8 uppercase hex>`
- Hash source: `sha256(f"{telegram_user_id}:{COMMUNITY_FEEDBACK_SALT}")`
- Persisted raw vote record stores:
  - `user_id = member_ref`
  - `member_ref`
- Downstream per-user analytics compatibility is preserved by hashing runtime user input the same way before lookup

## Persistence behavior
- Raw vote record path: `outcomes/outcomes.jsonl`
- Dedup/index path: `outcomes/outcomes_index.json`
- Vote-window metadata path: `outcomes/open_now_registry.json`
- Vote record is appended only once per accepted callback
- Failed append returns `persistence_failed` and does not acknowledge success

## Observability behavior
- Accepted or rejected canonical vote handling emits `user_outcome` events where applicable
- Security/config/context rejections emit canonical `warning` events
- `outcome_panel_enabled` remains emitted when a callback surface is registered

## Callback acknowledgment behavior
- Success: `Outcome recorded.`
- Safe replay: `Outcome already recorded.`
- Clear rejection texts for invalid action, invalid outcome, unknown signal, unauthorized context, closed window, missing config, and persistence failure

## Compatibility notes
- `distribution_router.py` now passes `symbol`, `direction`, `timeframe`, and route metadata into `register_open_now(...)`
- `analytics_engine.py` and `research_engine.py` continue to read the existing outcomes JSONL shape, with pseudonymous lookup support added for user-scoped stats
