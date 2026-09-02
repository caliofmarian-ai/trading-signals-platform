from pathlib import Path

path = Path("tests/canonical/unit/test_telegram_runtime_remediation.py")
text = path.read_text(encoding="utf-8")
old = '''def test_owner_private_callback_navigation_restores_admin_panels(
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
'''
new = '''def test_owner_private_callback_navigation_restores_admin_panels(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "1001")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1001")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "999")
    bot = fresh_imports("core.bot_service")
'''
if old not in text:
    raise SystemExit("accidental Owner-test block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
