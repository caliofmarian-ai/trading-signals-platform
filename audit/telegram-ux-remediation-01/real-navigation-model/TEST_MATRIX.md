# Test Matrix — Issue #38

**Scope:** Test coverage for Back/Home/Refresh navigation  
**Date:** 2026-08-02  
**Issue:** #38 — Implement real Back, Home, and Refresh navigation

---

## Focused Issue #38 Tests

File: `tests/telegram_app/test_real_navigation.py`  
Tests: **59 passed**

| Test Class | Test | Coverage |
|-----------|------|---------|
| TestActBackConstant | test_act_back_constant_exists | ACT_BACK = "BACK" |
| TestActBackConstant | test_act_back_distinct_from_home | ACT_BACK ≠ ACT_HOME |
| TestActBackConstant | test_make_callback_back | APP:BACK callback format |
| TestActBackConstant | test_parse_app_action_back | parse_app_action handles BACK |
| TestBoundedNavHistory | test_push_and_pop | Basic push/pop |
| TestBoundedNavHistory | test_pop_empty_returns_none | Empty history fallback |
| TestBoundedNavHistory | test_can_go_back_true_after_push | nav_can_go_back true |
| TestBoundedNavHistory | test_can_go_back_false_after_clear | clear_nav_history |
| TestBoundedNavHistory | test_history_stack_is_fifo | LIFO (most recent first) |
| TestBoundedNavHistory | test_duplicate_consecutive_entries_not_pushed | Loop prevention |
| TestBoundedNavHistory | test_history_bounded_at_max_depth | Max depth enforcement |
| TestBoundedNavHistory | test_session_isolation_different_users | User isolation |
| TestBoundedNavHistory | test_session_isolation_different_chats | Chat isolation |
| TestBoundedNavHistory | test_session_isolation_different_thread_ids | Thread isolation |
| TestHandleAppActionBack | test_back_with_empty_history_returns_home | State-loss fallback |
| TestHandleAppActionBack | test_back_with_history_returns_parent | BACK renders parent |
| TestHandleAppActionBack | test_back_from_home_returns_home | HOME excluded from recursive back |
| TestHandleAppActionBack | test_back_fallback_safe_without_chat_id | No chat_id safe |
| TestHandleAppActionBack | test_back_result_has_no_dead_end | No dead ends |
| TestHandleAppActionBack | test_multiple_back_presses_bounded | Bounded repetition |
| TestStartHardResetClearsHistory | test_prepare_start_hard_reset_clears_nav_history | /start clears history |
| TestAdminMarkupParentAction | test_strategy_markup_back_to_operations | strategy Back → OPERATIONS |
| TestAdminMarkupParentAction | test_symbols_toggle_default_parent_home | toggle Back → HOME |
| TestAdminMarkupParentAction | test_symbols_toggle_strategy_parent | toggle Back → STRATEGY |
| TestAdminMarkupParentAction | test_symbols_toggle_strategy_refresh_targets_symbols | Refresh context preservation |
| TestAdminMarkupParentAction | test_symbols_toggle_home_refresh_targets_symbols_cov | Refresh context preservation |
| TestAdminMarkupParentAction | test_engine_markup_default_parent_home | engine Back → HOME |
| TestAdminMarkupParentAction | test_engine_markup_operations_parent | engine Back → OPERATIONS |
| TestAdminMarkupParentAction | test_engine_markup_syshealth_parent | engine Back → SYSHEALTH |
| TestAdminMarkupParentAction | test_diagnose_markup_default_parent_home | diagnose Back → HOME |
| TestAdminMarkupParentAction | test_diagnose_markup_operations_parent | diagnose Back → OPERATIONS |
| TestAdminMarkupParentAction | test_diagnose_markup_syshealth_parent | diagnose Back → SYSHEALTH |
| TestAdminMarkupParentAction | test_all_markup_functions_no_dead_end | No dead ends |
| TestCanonicalAdminParentMap | test_parent_map_exists | Map exported |
| TestCanonicalAdminParentMap | test_strategy_parent_is_operations | STRATEGY → OPERATIONS |
| TestCanonicalAdminParentMap | test_symbols_parent_is_strategy | SYMBOLS → STRATEGY |
| TestCanonicalAdminParentMap | test_operations_parent_is_home | OPERATIONS → HOME |
| TestCanonicalAdminParentMap | test_ops_engine_parent_is_operations | OPS_ENGINE → OPERATIONS |
| TestCanonicalAdminParentMap | test_sh_engine_parent_is_syshealth | SH_ENGINE → SYSHEALTH |
| TestCanonicalAdminParentMap | test_ops_diagnose_parent_is_operations | OPS_DIAGNOSE → OPERATIONS |
| TestCanonicalAdminParentMap | test_sh_diagnose_parent_is_syshealth | SH_DIAGNOSE → SYSHEALTH |
| TestCanonicalAdminParentMap | test_all_panel_pages_have_home_parent | Direct children → HOME |
| TestRefreshBehavior | test_status_refresh_preserves_history | Refresh doesn't modify history |
| TestRefreshBehavior | test_diagnose_refresh_button_is_diagnose | DIAGNOSE refresh |
| TestRefreshBehavior | test_decision_vis_refresh_is_self | DECISION_VIS refresh |
| TestRefreshBehavior | test_distribution_refresh_is_self | DISTRIBUTION refresh |
| TestRefreshBehavior | test_research_refresh_is_self | RESEARCH refresh |
| TestRefreshBehavior | test_intelligence_refresh_is_self | INTELLIGENCE refresh |
| TestRefreshBehavior | test_engine_refresh_is_self | ENGINE refresh |
| TestRefreshBehavior | test_status_refresh_is_self_app_nav | APP:STATUS refresh |
| TestHomeNavigation | test_home_returns_welcome_page | Home renders welcome |
| TestHomeNavigation | test_app_nav_status_page_has_home_button | Status has Home button |
| TestHomeNavigation | test_app_nav_help_page_has_home_button | Help has Home button |
| TestHomeNavigation | test_admin_home_markup_has_home_callback | Admin Home button |
| TestHomeNavigation | test_admin_home_markup_without_home_callback | No spurious Home button |
| TestAdminHomeDistinct | test_admin_nav_prefix_distinct_from_app_prefix | Prefix distinction |
| TestAdminHomeDistinct | test_admin_home_callback_uses_admin_prefix | ADMIN_NAV:HOME |
| TestAdminHomeDistinct | test_app_home_callback_uses_app_prefix | APP:HOME |
| TestAdminHomeDistinct | test_panel_pages_back_to_admin_home | Direct children → admin home |

---

## Updated Existing Tests

File: `tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py`

| Test | Change | Reason |
|------|--------|--------|
| test_back_navigation_buttons_present | Updated: check OPERATIONS in strategy_markup | strategy_markup Back now correctly goes to OPERATIONS |
| test_symbols_toggle_has_all_none_refresh | Updated: check SYMBOLS_COV for default, SYMBOLS for parent_action=STRATEGY | Refresh target depends on context |

---

## Regression Tests

All pre-existing tests continue to pass:

| Suite | Tests | Status |
|-------|-------|--------|
| tests/telegram_app/ | 160 tests | ✅ passed |
| tests/telegram_transport/ | 15 tests | ✅ passed |
| tests/telegram_admin_ui_restoration/ | 20 tests | ✅ passed |
| tests/canonical/ | ~250 tests | ✅ passed |
| tests/batch_*/ | ~250 tests | ✅ passed |
| **Total** | **695 tests** | **✅ all passed** |
