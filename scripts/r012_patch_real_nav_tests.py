from __future__ import annotations

from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests/telegram_app/test_real_navigation.py"
text = path.read_bytes().decode("utf-8")

start = text.index("    def test_profile_confirm_cancel_returns_to_selector_without_mutation")
end = text.index("    def test_files_home_directory_prev_next_and_back_preserve_single_anchor", start)

replacement = '''    def test_profile_surface_and_stale_confirm_are_non_mutating(self, tmp_path, monkeypatch):
        bot, _, pub = self._load_modules(tmp_path, monkeypatch, owner_ids=[9014])
        mutations: list[str] = []
        monkeypatch.setattr(
            bot,
            "handle_strategy_profile",
            lambda profile, user_id: mutations.append(profile) or "unexpected",
        )

        bot.process_update(_message_update(9014, 9014, "/start"))
        active_id = pub.sends[-1]["message_id"]
        admin_cb = _find_callback(pub.sends[-1]["reply_markup"], "ADMIN")
        assert admin_cb is not None

        for action in (admin_cb, "ADMIN_NAV:OPERATIONS", "ADMIN_NAV:STRATEGY", "ADMIN_NAV:PROFILE_HOME"):
            bot.process_update(_callback_update(9014, 9014, action, message_id=active_id))

        assert "Profiles: NOT AVAILABLE" in pub.edits[-1]["text"]
        assert not any("PROFILE_CONFIRM:" in cb for cb in _cbs(pub.edits[-1]["reply_markup"]))
        assert not any("PROFILE_EXEC:" in cb for cb in _cbs(pub.edits[-1]["reply_markup"]))

        bot.process_update(
            _callback_update(
                9014,
                9014,
                "ADMIN_NAV:PROFILE_CONFIRM:BALANCED",
                message_id=active_id,
            )
        )
        assert "BALANCED: NOT AVAILABLE" in pub.edits[-1]["text"]
        assert not any("PROFILE_EXEC:" in cb for cb in _cbs(pub.edits[-1]["reply_markup"]))
        cancel_cb = _find_callback(pub.edits[-1]["reply_markup"], "PROFILE_HOME")
        assert cancel_cb == "ADMIN_NAV:PROFILE_HOME"
        bot.process_update(_callback_update(9014, 9014, cancel_cb, message_id=active_id))

        assert mutations == []
        assert "Profiles: NOT AVAILABLE" in pub.edits[-1]["text"]
        assert len(pub.sends) == 1

    def test_stale_profile_exec_routes_to_fail_closed_handler_and_safe_surface(self, tmp_path, monkeypatch):
        bot, _, pub = self._load_modules(tmp_path, monkeypatch, owner_ids=[9015])
        calls: list[tuple[str, int]] = []

        def _handle_strategy_profile(profile: str, user_id: int) -> str:
            calls.append((profile.upper(), user_id))
            return (
                "Strategy profiles are NOT AVAILABLE under the active canonical "
                "parameter-control authority. No strategy parameter was changed."
            )

        monkeypatch.setattr(bot, "handle_strategy_profile", _handle_strategy_profile)

        bot.process_update(_message_update(9015, 9015, "/start"))
        active_id = pub.sends[-1]["message_id"]
        admin_cb = _find_callback(pub.sends[-1]["reply_markup"], "ADMIN")
        assert admin_cb is not None

        for action in (admin_cb, "ADMIN_NAV:OPERATIONS", "ADMIN_NAV:STRATEGY", "ADMIN_NAV:PROFILE_HOME"):
            bot.process_update(_callback_update(9015, 9015, action, message_id=active_id))

        bot.process_update(
            _callback_update(
                9015,
                9015,
                "ADMIN_NAV:PROFILE_EXEC:BALANCED",
                message_id=active_id,
            )
        )

        assert calls == [("BALANCED", 9015)]
        assert "NOT AVAILABLE" in pub.edits[-1]["text"]
        assert "No strategy parameter was changed." in pub.edits[-1]["text"]
        assert not any("PROFILE_CONFIRM:" in cb for cb in _cbs(pub.edits[-1]["reply_markup"]))
        assert not any("PROFILE_EXEC:" in cb for cb in _cbs(pub.edits[-1]["reply_markup"]))
        assert len(pub.sends) == 1

'''

path.write_bytes((text[:start] + replacement + text[end:]).encode("utf-8"))
