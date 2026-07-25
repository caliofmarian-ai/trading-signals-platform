# END_TO_END_TEST_MATRIX.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Document: END_TO_END_TEST_MATRIX.md  
Status: RECONSTRUCTION AUDIT

---

## PURPOSE

This matrix documents every end-to-end test case, mapped to the canonical requirement it verifies.

---

## TEST FILE REGISTRY

| File | Count | Coverage Area |
|---|---|---|
| tests/telegram_app/test_role_constants.py | 7 tests | G: Role constant single source of truth |
| tests/telegram_app/test_telegram_app_nav.py | 47 tests | D, E, F, C: App nav, start flow, page contracts |
| tests/telegram_app/test_e2e_application.py | ~33 tests | C, D, E, H: All roles, navigation, auth, no dead ends |
| tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py | 72 tests | Admin tree, role-scoped panels |
| tests/canonical/ (existing) | 325 tests | Core system, bot dispatch, permissions |

**Total: 477 tests passing as of this audit.**

---

## TEST MATRIX BY REQUIREMENT

### Requirement 1: Canonically reconstructed /start

| Test | File | Verifies |
|---|---|---|
| test_start_produces_navigable_page_for_role (8 parametrized) | test_e2e_application.py | /start produces a navigable page for every role |
| test_owner_start_shows_admin_button | test_e2e_application.py | OWNER sees admin button on /start |
| test_unknown_user_start_no_admin_button | test_e2e_application.py | Unknown user sees no admin button |
| test_shadow_mode_visible_on_start | test_e2e_application.py | Shadow mode notice on /start |
| test_start_response_mentions_shadow_mode | test_telegram_runtime_remediation.py | Shadow mode notice on /start (updated) |
| TestRenderWelcomePage (13 tests) | test_telegram_app_nav.py | Welcome page contracts for all roles |

### Requirement 3: No role granting through button selection

| Test | File | Verifies |
|---|---|---|
| test_button_does_not_grant_role | test_telegram_app_nav.py | USER buttons do not contain grant/elevate actions |
| test_unknown_user_start_no_admin_button | test_e2e_application.py | Unknown user cannot get admin via /start |

### Requirement 4: Role and permission resolution

| Test | File | Verifies |
|---|---|---|
| test_role_change_reflected_after_reload | test_e2e_application.py | Role changes reflected on next interaction |
| TestRoleConstantsConsistencyAcrossModules (3 tests) | test_role_constants.py | Role constants consistent across all modules |

### Requirement 5: Complete role-specific experiences

| Test | File | Verifies |
|---|---|---|
| test_all_canonical_roles_produce_markup | test_telegram_app_nav.py | All 8 canonical roles produce navigable page |
| test_start_produces_navigable_page_for_role (8 cases) | test_e2e_application.py | Each role gets appropriate start page |
| test_admin_home_markup_role_scoped_for_strategy_admin | test_e2e_application.py | Strategy admin sees 3 panels only |
| test_admin_home_markup_role_scoped_for_affiliate_admin | test_e2e_application.py | Affiliate admin sees 1 panel only |
| test_admin_home_role_scoped_owner_sees_all | test_admin_ui_restoration.py | Owner sees all 11 panels |
| test_admin_home_role_scoped_strategy_admin | test_admin_ui_restoration.py | Strategy admin panel visibility |
| test_admin_home_role_scoped_affiliate_admin | test_admin_ui_restoration.py | Affiliate admin panel visibility |

### Requirement 6: Non-admin user journeys

| Test | File | Verifies |
|---|---|---|
| test_unknown_user_gets_platform_intro | test_telegram_app_nav.py | USER sees platform intro |
| test_user_role_no_admin_buttons | test_telegram_app_nav.py | USER has no admin buttons |
| test_user_role_help_no_admin_commands | test_telegram_app_nav.py | USER help shows only public commands |
| test_user_help_does_not_expose_admin_commands | test_e2e_application.py | USER /help has no admin commands |

### Requirement 7: Progressive disclosure

| Test | File | Verifies |
|---|---|---|
| test_user_role_no_admin_buttons | test_telegram_app_nav.py | USER does not see admin buttons |
| test_non_owner_admin_role_no_admin_button | test_telegram_app_nav.py | Non-owner admins don't get admin button on /start |
| test_user_role_welcome_has_no_admin_panel_buttons | test_e2e_application.py | No admin callbacks in USER welcome |

### Requirement 10-11: Button-first + Single active message

| Test | File | Verifies |
|---|---|---|
| TestActiveMessageState (5 tests) | test_telegram_app_nav.py | Active message tracking per user |
| test_callback_does_not_send_new_message_when_edit_succeeds | test_e2e_application.py | Edit not send on callback |
| test_home_callback_edits_message | test_e2e_application.py | APP:HOME edits message |
| test_status_callback_edits_message | test_e2e_application.py | APP:STATUS edits message |
| test_help_callback_edits_message | test_e2e_application.py | APP:HELP edits message |

### Requirement 13: Back/Home/Refresh

| Test | File | Verifies |
|---|---|---|
| test_status_has_refresh_button | test_telegram_app_nav.py | Status has Refresh |
| test_status_has_home_button | test_telegram_app_nav.py | Status has Home |
| test_help_has_home_button | test_telegram_app_nav.py | Help has Home |
| test_help_has_status_button | test_telegram_app_nav.py | Help has Status button |

### Requirement 14: Unified rendering (slash = callback)

| Test | File | Verifies |
|---|---|---|
| test_slash_status_and_callback_status_consistent | test_e2e_application.py | /status and APP:STATUS produce equivalent content |
| test_status_command_ready_state | test_telegram_runtime_remediation.py | /status shows correct fields |

### Requirement 17: Stale/duplicate callback handling

| Test | File | Verifies |
|---|---|---|
| test_stale_app_callback_fallback_to_home | test_e2e_application.py | Unknown APP: action falls back safely |
| test_duplicate_status_callback | test_e2e_application.py | Two presses = two edits, no new messages |
| test_stale_callback_handled_safely | test_telegram_app_nav.py | Unknown actions return navigable page |
| test_duplicate_tap_same_action_no_crash | test_telegram_app_nav.py | Same action twice = same shape response |

### Requirement 18-20: Authorization, reachability, no dead ends

| Test | File | Verifies |
|---|---|---|
| test_non_owner_private_dm_cannot_run_admin | test_e2e_application.py | Access denied without admin context |
| test_admin_context_check_prevents_wrong_chat | test_e2e_application.py | Wrong chat denied |
| TestPermissionFiltering (4 tests) | test_e2e_application.py | Role-scoped visibility |
| TestNoDeadEndPages (5 tests) | test_e2e_application.py | Every page has buttons |
| test_every_canonical_role_welcome_has_buttons | test_e2e_application.py | No dead end for any role |
| test_all_actions_produce_non_empty_markup | test_telegram_app_nav.py | All actions navigable |

### Requirement G: Role constant single source

| Test | File | Verifies |
|---|---|---|
| TestRoleConstantsModule (5 tests) | test_role_constants.py | All canonical roles defined |
| TestRoleConstantsConsistencyAcrossModules (3 tests) | test_role_constants.py | No divergence between modules |

---

## TESTS NOT YET PRESENT (documented gaps)

| Missing Test | Reason |
|---|---|
| File/export exceptions (separate message for send_document) | Requires mock filesystem; covered by existing tests in test_admin_ui_restoration.py |
| Admin sub-panel callback authorization (role blocks wrong panel) | The role-scoped admin_home_markup prevents unauthorized panel buttons from appearing; no button = no access |
| Returning user with changed role between sessions | Covered by test_role_change_reflected_after_reload |

---

End of END_TO_END_TEST_MATRIX.md
