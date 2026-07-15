# RESTORATION_PLAN

## Objective
Restore the original owner login/access experience (owner can use `/admin` flow privately) without breaking canonical architecture.

## Guardrails
- Keep canonical authorization in `admin_permissions.py` + `admin_commands.py`.
- Keep fail-closed context requirements for non-owner admin activity.
- Do not reintroduce legacy panel, password auth, or session auth.

## Canonical-safe restoration strategy

1. **Policy baseline definition**
   - Define explicit owner-private allowlist behavior as product policy (which commands are allowed privately, and which require admin topic).
   - Preserve explicit denial for sensitive mutation operations if required (e.g., `/roles_reload`).

2. **Dispatcher gate policy alignment**
   - Keep a single context decision point in `bot_service` (current canonical architecture already has this).
   - Ensure owner-private flow remains only an exception policy layer, not a separate auth stack.

3. **Permission authority preservation**
   - Keep permission truth in `admin_permissions.has_permission` and role config.
   - Keep owner identity from roles config + `OWNER_TELEGRAM_ID` fallback (no new identity store).

4. **Context model stabilization**
   - Keep non-owner admin commands/callbacks constrained to configured admin chat/topic.
   - Keep fail-closed behavior when admin chat is unconfigured.

5. **Regression protection**
   - Add/keep tests that pin:
     - owner private allowed commands,
     - owner private denied commands,
     - non-owner private denied,
     - supergroup+topic allowed path,
     - wrong-chat denial path.

6. **Operational rollout**
   - Validate in staging with production-like env (`ADMIN_CONTROL_CHAT_ID`, `ADMIN_CONTROL_THREAD_ID`, roles config).
   - Roll out with observability checks on denial reasons and command outcomes.

## Risk register (restoration-specific)
- **Risk:** Over-broad owner private access weakens context controls.  
  **Control:** Keep strict allowlist and deny sensitive mutations privately.
- **Risk:** Divergence between dispatcher policy and permission policy.  
  **Control:** Keep dispatcher as context gate only; permission decisions stay in canonical permission layer.
- **Risk:** Silent regressions in future remediations.  
  **Control:** Lock behavior with dedicated tests and audit docs.

## Final verdict
**Yes.** The original owner login/access experience can be restored safely while keeping the current canonical architecture, because the system is ID/role-based (not password/session-based) and restoration only requires policy-level context gating alignment, not architectural rollback.
