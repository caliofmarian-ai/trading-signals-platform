from pathlib import Path

bot = Path("send/core/bot_service.py")
text = bot.read_text(encoding="utf-8")
block = '''    # Admin-topic membership is context, not authorization. Every live
    # non-Owner ADMIN_NAV action requires the governed admin.view grant.
    if not owner_private:
        from core.admin_permissions import has_permission
        if not has_permission(user_id, "admin.view"):
            return {
                "text": "Access denied (missing admin permission).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }

'''
if block not in text:
    raise SystemExit("admin.view navigation block not found")
text = text.replace(block, "", 1)
marker = '''        return {
            "text": render_contextual_knowledge(entry.key),
            "reply_markup": telegram_admin_ui.knowledge_detail_markup(return_action),
        }

    # ---- RELOAD_ROLES flow (admin-topic only) ----
'''
replacement = '''        return {
            "text": render_contextual_knowledge(entry.key),
            "reply_markup": telegram_admin_ui.knowledge_detail_markup(return_action),
        }

    # Contextual knowledge is governed by knowledge_visible_for_role above.
    # Every remaining live non-Owner ADMIN_NAV action requires admin.view.
    if not owner_private:
        from core.admin_permissions import has_permission
        if not has_permission(user_id, "admin.view"):
            return {
                "text": "Access denied (missing admin permission).",
                "reply_markup": None,
                _CALLBACK_RECOVERY_KEY: _RECOVERY_UNAUTHORIZED,
            }

    # ---- RELOAD_ROLES flow (admin-topic only) ----
'''
if marker not in text:
    raise SystemExit("knowledge return insertion marker not found")
text = text.replace(marker, replacement, 1)
bot.write_text(text, encoding="utf-8")

test = Path("tests/canonical/unit/test_telegram_runtime_remediation.py")
text = test.read_text(encoding="utf-8")
exact = '''def test_admin_topic_reload_confirmation_dialog_uses_callback_navigation(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
    edits: list[dict] = []
'''
fixed = '''def test_admin_topic_reload_confirmation_dialog_uses_callback_navigation(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    roles_path = canonical_runtime_root / "config" / "admin_roles.json"
    roles = json.loads(roles_path.read_text(encoding="utf-8"))
    primary = list(roles.get("primary_admin", []))
    if 2002 not in primary:
        primary.append(2002)
    roles["primary_admin"] = primary
    roles_path.write_text(json.dumps(roles, indent=2), encoding="utf-8")
    monkeypatch.setenv("ADMIN_ROLES_CONFIG", str(roles_path))
    monkeypatch.setenv(
        "ADMIN_PERMISSIONS_CONFIG",
        str(canonical_runtime_root / "config" / "admin_permissions.json"),
    )
    bot = fresh_imports("core.bot_service")
    edits: list[dict] = []
'''
if exact not in text:
    raise SystemExit("exact reload confirmation test block not found")
text = text.replace(exact, fixed, 1)
test.write_text(text, encoding="utf-8")
