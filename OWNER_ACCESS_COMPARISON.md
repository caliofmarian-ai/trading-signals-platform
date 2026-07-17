# OWNER_ACCESS_COMPARISON

## Scope
Comparison of owner/admin Telegram access between:
- Hetzner-era imported implementation (`0fb9112`, pre-Railway migration phase),
- BATCH-05 canonicalization (`d7e7213`),
- Runtime remediation (`49aaeb4`),
- Current (`64345ae`+).

## Side-by-side matrix

| Dimension | Hetzner-import (`0fb9112`) | BATCH-05 (`d7e7213`) | Remediation (`49aaeb4`) | Current (`64345ae`+) |
|---|---|---|---|---|
| Slash `/admin` chat gate | No slash gate in dispatcher (`0fb9112:548-556`) | No slash gate (`d7e7213:156-168`) | **Yes** (`49aaeb4:239-243`) | Context gate via `_can_run_admin_command` (`send/core/bot_service.py:398-401`) |
| Owner identity source | Legacy RBAC + `ADMIN_USER_ID` fallback in old panel (`0fb9112:50-70`), canonical roles for `/admin` command path | Canonical roles + env fallback `OWNER_TELEGRAM_ID` | Same | Same |
| Password prompt | None | None | None | None |
| Session/token auth | None | None | None | None |
| Private owner `/admin` UX | Works via slash path (permission-based, no chat gate) | Works similarly | **Regressed** (wrong-chat before permission) | Partially restored for owner command subset |
| Supergroup enforcement | Legacy panel callbacks gated by `in_admin_context`; fail-open when chat id unset (`0fb9112:78-83`) | Fail-closed context for callbacks (`d7e7213:34-40,130-132`) | Slash + callback gating | Topic-aware admin context + owner private subset |
| Wrong-chat denial trigger | Legacy callback mismatch only | Callback mismatch | Slash and callback mismatch | Non-owner or non-allowed owner-private contexts |

## Behavior change timeline
1. `0fb9112` (Hetzner-imported baseline): slash admin path had no chat gate.
2. `d7e7213`: callback context hardening (fail-closed), slash still ungated by chat.
3. `49aaeb4`: slash admin commands now require admin chat context (`Access denied (wrong chat)` introduced for private owner flow).
4. `64345ae`: owner-private subset access reintroduced while keeping canonical context checks for everything else.

## Root-cause statement for reported owner denial
The denial message was caused by the slash-level context gate added in `49aaeb4`, which executes before role/permission evaluation. This changed UX from identity/permission-first to context-first.

## Net assessment
- Security posture improved (explicit context gate, fail-closed).
- Hetzner owner private `/admin` ergonomics regressed at `49aaeb4`.
- Current state is a compromise: limited owner-private allowlist, full context enforcement otherwise.
