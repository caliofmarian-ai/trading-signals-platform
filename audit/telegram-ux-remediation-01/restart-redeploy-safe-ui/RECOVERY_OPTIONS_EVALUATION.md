# Recovery Options Evaluation

## Option A — In-memory only
- Pros: simplest runtime behavior.
- Cons: cannot reuse active UI after restart/redeploy; higher duplicate UI message risk.
- Verdict: rejected.

## Option B — Persist all UI payloads
- Pros: maximal replay detail.
- Cons: violates minimal-data principle; unnecessary privacy/security risk.
- Verdict: rejected.

## Option C — Hybrid minimal metadata persistence
- Persist only `(chat_id, user_id, thread_id, message_id, updated_ts)` with versioned state.
- Keep runtime map in memory; restore candidates on startup.
- Clear stale entries and fall back to replacement send when Telegram says message is deleted/not editable.
- Verdict: **approved**.
