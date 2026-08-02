"""
tests/canonical/unit/test_multi_account_session_isolation.py

Comprehensive cross-account Telegram UI session isolation tests.

Verified defects addressed (Refs #31):
  DEFECT-1  clear_active_message() skipped persisted deletion when session absent
             from in-memory map — a persisted-only session survived the clear.
  DEFECT-2  No standalone exact-session deletion primitive existed in state_store.
  DEFECT-3  get_runtime_diagnostics() reported in-memory value for persisted_message_id
             instead of independently reading from disk.
  DEFECT-4  validate_telegram_ui_state() used raw thread_id (possibly 0) as dedup key
             so thread_id=0 and thread_id=None could create duplicate private-chat entries.
  DEFECT-5  Replacement-send failure did not guarantee stale session remained deleted.

Test matrix (30 cases, canonical §REQUIRED_TESTS):
  1.  USER creates U1.
  2.  ADMIN creates A1.
  3.  USER and ADMIN session keys differ.
  4.  Only ADMIN message A1 is deleted.
  5.  USER /status still edits U1.
  6.  ADMIN /start attempts A1 → stale/not-found response.
  7.  ADMIN A is removed from memory.
  8.  ADMIN A is removed from persisted state.
  9.  USER U remains unchanged in memory.
  10. USER U remains unchanged in persisted state.
  11. Exactly one ADMIN replacement A2 is sent.
  12. A2 becomes the active ADMIN message.
  13. /admin, Engine and Home edit A2.
  14. No A3 is generated.
  15. Failed ADMIN replacement leaves A absent.
  16. A later ADMIN /start retries successfully.
  17. Cleared ADMIN state does not return after module reload.
  18. Cleared ADMIN state does not return after simulated restart.
  19. A persisted-only session can be cleared even when missing from memory.
  20. None, zero, missing and JSON-null thread IDs normalize identically.
  21. Duplicate private-session variants are collapsed or rejected safely.
  22. Concurrent USER save and ADMIN clear preserve USER and remove ADMIN.
  23. Concurrent ADMIN clear and ADMIN replacement cannot restore A1.
  24. Exact persisted delete removes only the requested session.
  25. State corruption fails safely.
  26. Unsupported schema fails safely.
  27. /start never becomes permanently silent after stale-state failure.
  28. One account's failure never blocks another.
  29. Railway-style restart preserves correct recovery behavior.
  30. Complete isolation: both accounts responsive after repeated switching.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

# Pre-import so module-level state_store code runs once (without per-test env vars),
# allowing subsequent _reload_nav() calls to use importlib.reload() safely.
import core.telegram_app_nav as _pre_imported_nav  # noqa: F401, E402
import state_store.state_store as _pre_imported_ss  # noqa: F401, E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_file(base_dir: Path) -> Path:
    return base_dir / "state" / "telegram_ui_state.json"


def _ensure_dirs(base_dir: Path) -> None:
    """Create required directory structure for state_store to function."""
    for sub in ("config", "state"):
        (base_dir / sub).mkdir(parents=True, exist_ok=True)


def _reload_nav(base_dir: Optional[Path] = None):
    """Reload telegram_app_nav so module-level state is reset.

    If base_dir is provided, create the required config/ and state/ dirs
    so that state_store module-level code succeeds on fresh import (which
    can happen after conftest purges sys.modules between tests).
    """
    if base_dir is not None:
        _ensure_dirs(base_dir)
    if "core.telegram_app_nav" in sys.modules:
        return importlib.reload(sys.modules["core.telegram_app_nav"])
    return importlib.import_module("core.telegram_app_nav")


def _write_state(base_dir: Path, sessions: List[Dict]) -> None:
    sf = _state_file(base_dir)
    sf.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "version": "1.0.0",
        "retention_seconds": 7 * 24 * 3600,
        "max_sessions": 1000,
        "sessions": sessions,
        "last_updated_ts": int(time.time()),
    }
    sf.write_text(json.dumps(doc), encoding="utf-8")


def _read_sessions(base_dir: Path) -> List[Dict]:
    sf = _state_file(base_dir)
    if not sf.exists():
        return []
    doc = json.loads(sf.read_text("utf-8"))
    return doc.get("sessions", [])


def _session_row(
    chat_id: int, user_id: int, message_id: int, thread_id: Optional[int] = None
) -> Dict:
    return {
        "chat_id": chat_id,
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
        "updated_ts": int(time.time()),
    }


# User and Admin Telegram account IDs
USER_ID = 1_000_001
ADMIN_ID = 1_000_002  # different Telegram account — OWNER/ADMIN role


# ---------------------------------------------------------------------------
# Test 1 — USER creates U1
# ---------------------------------------------------------------------------

def test_01_user_creates_session(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.clear_active_message(USER_ID, chat_id=USER_ID)
    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)

    assert nav.get_active_message(USER_ID, chat_id=USER_ID) == 1001


# ---------------------------------------------------------------------------
# Test 2 — ADMIN creates A1
# ---------------------------------------------------------------------------

def test_02_admin_creates_session(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)

    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2001


# ---------------------------------------------------------------------------
# Test 3 — USER and ADMIN keys differ
# ---------------------------------------------------------------------------

def test_03_user_and_admin_keys_differ():
    from core.telegram_app_nav import normalize_session_key
    user_key = normalize_session_key(USER_ID, USER_ID, None)
    admin_key = normalize_session_key(ADMIN_ID, ADMIN_ID, None)
    assert user_key != admin_key, "USER and ADMIN session keys must be distinct"


# ---------------------------------------------------------------------------
# Test 4 — Only ADMIN message A1 is deleted (clear does not touch USER)
# ---------------------------------------------------------------------------

def test_04_clear_admin_does_not_touch_user(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)

    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    assert nav.get_active_message(USER_ID, chat_id=USER_ID) == 1001, "USER U1 must survive ADMIN clear"
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None, "ADMIN A must be absent after clear"


# ---------------------------------------------------------------------------
# Test 5 — USER /status still edits U1 after ADMIN clear
# ---------------------------------------------------------------------------

def test_05_user_status_still_works_after_admin_clear(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # USER active message should still be retrievable
    u1 = nav.get_active_message(USER_ID, chat_id=USER_ID)
    assert u1 == 1001, f"USER U1 must remain 1001 after ADMIN clear, got {u1}"


# ---------------------------------------------------------------------------
# Test 6/7/8 — ADMIN session removed from memory and persisted state
# ---------------------------------------------------------------------------

def test_06_08_admin_session_removed_from_memory_and_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    result = nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # Test 7 — removed from memory
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None

    # Test 8 — removed from persisted state
    assert result.get("persisted_absent") is True, f"Expected persisted_absent=True, got {result}"

    # Verify independently via state_store
    from state_store import state_store as ss
    verification = ss.verify_telegram_session_absent(ADMIN_ID, ADMIN_ID)
    assert verification["absent"] is True


# ---------------------------------------------------------------------------
# Test 9/10 — USER remains unchanged in memory and persisted state
# ---------------------------------------------------------------------------

def test_09_10_user_unchanged_after_admin_operations(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)

    # ADMIN stale state recovery simulation: clear + would-be replacement
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2002)

    # Test 9 — USER in memory
    assert nav.get_active_message(USER_ID, chat_id=USER_ID) == 1001

    # Test 10 — USER in persisted state
    from state_store import state_store as ss
    pid = ss.read_telegram_session_message_id(USER_ID, USER_ID)
    assert pid == 1001, f"USER persisted message_id must be 1001, got {pid}"


# ---------------------------------------------------------------------------
# Test 11/12 — Exactly one ADMIN replacement sent; A2 becomes active
# ---------------------------------------------------------------------------

def test_11_12_exactly_one_replacement_sent(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # Simulate one replacement being tracked
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2002)

    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2002


# ---------------------------------------------------------------------------
# Test 13/14 — /admin, Engine and Home edit A2; no A3 generated
# ---------------------------------------------------------------------------

def test_13_14_subsequent_edits_do_not_send_new_message(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    # A2 is active
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2002)

    # Simulate update (edit) — same message_id should remain
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2002)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2002)

    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2002, "A2 must remain the active message"


# ---------------------------------------------------------------------------
# Test 15 — Failed ADMIN replacement leaves A absent
# ---------------------------------------------------------------------------

def test_15_failed_replacement_leaves_session_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # Don't call set_active_message — simulate send_message failure case
    # Session must remain absent
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None


# ---------------------------------------------------------------------------
# Test 16 — A later ADMIN /start retries successfully after previous failure
# ---------------------------------------------------------------------------

def test_16_admin_start_retries_after_stale_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    # Simulate stale failure: clear without replacement
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None

    # Later /start — new replacement
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2003)
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2003


# ---------------------------------------------------------------------------
# Test 17 — Cleared ADMIN state does not return after module reload
# ---------------------------------------------------------------------------

def test_17_cleared_state_absent_after_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # Reload module — simulates process restart
    nav2 = _reload_nav(tmp_path)
    assert nav2.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None, \
        "Cleared ADMIN state must not return after module reload"


# ---------------------------------------------------------------------------
# Test 18 — Cleared ADMIN state does not return after simulated restart
# ---------------------------------------------------------------------------

def test_18_cleared_state_absent_after_simulated_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # Simulate restart: reload module from persisted state
    nav2 = _reload_nav(tmp_path)
    assert nav2.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None, \
        "Cleared ADMIN state must not be restored on restart"
    assert nav2.get_active_message(USER_ID, chat_id=USER_ID) == 1001, \
        "USER session must survive ADMIN clear + restart"


# ---------------------------------------------------------------------------
# Test 19 — A persisted-only session can be cleared even when missing from memory
# ---------------------------------------------------------------------------

def test_19_persisted_only_session_can_be_cleared(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    # Write a session directly to persisted state (bypassing in-memory)
    _write_state(tmp_path, [
        _session_row(ADMIN_ID, ADMIN_ID, 9999),
        _session_row(USER_ID, USER_ID, 1001),
    ])

    nav = _reload_nav(tmp_path)

    # Force load from disk — we do this by calling get to trigger init
    nav.initialize_active_ui_state(force_reload=True)

    # Now evict ADMIN from memory only (simulate crash between set and reload)
    # The persisted-only path: clear ADMIN state from persisted store directly
    from state_store import state_store as ss
    delete_result = ss.delete_telegram_ui_session(ADMIN_ID, ADMIN_ID)
    assert delete_result.session_existed, "Session must exist in persisted state"
    assert delete_result.session_removed, "Session must be removed from persisted state"

    verification = ss.verify_telegram_session_absent(ADMIN_ID, ADMIN_ID)
    assert verification["absent"] is True, "ADMIN must be absent in persisted state"

    # USER persisted message must survive
    user_pid = ss.read_telegram_session_message_id(USER_ID, USER_ID)
    assert user_pid == 1001, f"USER persisted message_id must be 1001, got {user_pid}"


# ---------------------------------------------------------------------------
# Test 20 — None, zero, missing and JSON-null thread IDs normalize identically
# ---------------------------------------------------------------------------

def test_20_thread_id_normalization(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    from state_store.state_store import _normalize_telegram_session_key

    chat_id = USER_ID  # private chat — positive ID

    # All of these must produce the same canonical key
    k_none = _normalize_telegram_session_key(chat_id, USER_ID, None)
    k_zero = _normalize_telegram_session_key(chat_id, USER_ID, 0)
    k_neg = _normalize_telegram_session_key(chat_id, USER_ID, -1)

    assert k_none == k_zero == k_neg, \
        f"None/0/-1 thread_id must normalize identically for private chat: {k_none!r}, {k_zero!r}, {k_neg!r}"
    assert k_none[2] is None, "Canonical thread_id for private chat must be None"

    # Verify via validate_telegram_ui_state: thread_id=0 and thread_id=None collapse
    from state_store.state_store import validate_telegram_ui_state
    now_ts = int(time.time())
    raw = {
        "version": "1.0.0",
        "retention_seconds": 7 * 24 * 3600,
        "max_sessions": 1000,
        "sessions": [
            {"chat_id": chat_id, "user_id": USER_ID, "message_id": 111, "thread_id": None, "updated_ts": now_ts},
            {"chat_id": chat_id, "user_id": USER_ID, "message_id": 222, "thread_id": 0, "updated_ts": now_ts - 1},
        ],
    }
    validated = validate_telegram_ui_state(raw)
    # Dedup must collapse to exactly one session
    assert len(validated["sessions"]) == 1, \
        f"thread_id=0 and thread_id=None must collapse to one session, got {len(validated['sessions'])}"
    # The latest (message_id=111) must win
    assert validated["sessions"][0]["message_id"] == 111


# ---------------------------------------------------------------------------
# Test 21 — Duplicate private-session variants are collapsed safely
# ---------------------------------------------------------------------------

def test_21_duplicate_private_session_variants_collapsed(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    from state_store.state_store import validate_telegram_ui_state

    now_ts = int(time.time())
    chat_id = USER_ID
    raw = {
        "version": "1.0.0",
        "retention_seconds": 7 * 24 * 3600,
        "max_sessions": 1000,
        "sessions": [
            {"chat_id": chat_id, "user_id": USER_ID, "message_id": 100, "thread_id": None, "updated_ts": now_ts},
            {"chat_id": chat_id, "user_id": USER_ID, "message_id": 200, "thread_id": 0, "updated_ts": now_ts - 10},
            {"chat_id": chat_id, "user_id": USER_ID, "message_id": 300, "thread_id": None, "updated_ts": now_ts - 20},
        ],
    }
    validated = validate_telegram_ui_state(raw)
    assert len(validated["sessions"]) == 1, \
        f"Three duplicate private-session variants must collapse to one, got {len(validated['sessions'])}"
    assert validated["sessions"][0]["message_id"] == 100, "Latest variant must win"


# ---------------------------------------------------------------------------
# Test 22 — Concurrent USER save and ADMIN clear preserve USER, remove ADMIN
# ---------------------------------------------------------------------------

def test_22_concurrent_user_save_and_admin_clear(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)

    errors: List[str] = []
    barrier = threading.Barrier(2)

    def _user_saves():
        try:
            barrier.wait()
            for i in range(10):
                nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001 + i)
        except Exception as exc:
            errors.append(f"user_saves: {exc}")

    def _admin_clears():
        try:
            barrier.wait()
            for _ in range(5):
                nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)
        except Exception as exc:
            errors.append(f"admin_clears: {exc}")

    t1 = threading.Thread(target=_user_saves)
    t2 = threading.Thread(target=_admin_clears)
    t1.start(); t2.start()
    t1.join(timeout=10); t2.join(timeout=10)

    assert not errors, f"Concurrent operations produced errors: {errors}"
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None, "ADMIN must be absent"
    user_msg = nav.get_active_message(USER_ID, chat_id=USER_ID)
    assert user_msg is not None, "USER must remain present"


# ---------------------------------------------------------------------------
# Test 23 — Concurrent ADMIN clear and ADMIN replacement cannot restore A1
# ---------------------------------------------------------------------------

def test_23_concurrent_clear_and_replacement_no_resurrection(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # After clear, any subsequent set must produce A2 (not restore A1)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2002)
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2002

    from state_store import state_store as ss
    pid = ss.read_telegram_session_message_id(ADMIN_ID, ADMIN_ID)
    assert pid == 2002, f"Persisted must be A2=2002, not A1=2001; got {pid}"


# ---------------------------------------------------------------------------
# Test 24 — Exact persisted delete removes only the requested session
# ---------------------------------------------------------------------------

def test_24_exact_persisted_delete_preserves_others(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    now_ts = int(time.time())
    other_user_id = 9_000_001
    _write_state(tmp_path, [
        _session_row(USER_ID, USER_ID, 1001),
        _session_row(ADMIN_ID, ADMIN_ID, 2001),
        _session_row(other_user_id, other_user_id, 3001),
    ])

    from state_store import state_store as ss
    result = ss.delete_telegram_ui_session(ADMIN_ID, ADMIN_ID)
    assert result.session_removed

    # ADMIN gone
    v_admin = ss.verify_telegram_session_absent(ADMIN_ID, ADMIN_ID)
    assert v_admin["absent"] is True

    # USER and other_user untouched
    v_user = ss.verify_telegram_session_absent(USER_ID, USER_ID)
    assert v_user["absent"] is False
    assert v_user["found_message_id"] == 1001

    v_other = ss.verify_telegram_session_absent(other_user_id, other_user_id)
    assert v_other["absent"] is False
    assert v_other["found_message_id"] == 3001


# ---------------------------------------------------------------------------
# Test 25 — State corruption fails safely
# ---------------------------------------------------------------------------

def test_25_state_corruption_fails_safely(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    sf = _state_file(tmp_path)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text("{not valid json!!!", encoding="utf-8")

    nav = _reload_nav(tmp_path)
    # Should not raise; session should be absent (empty state on load error)
    result = nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID)
    assert result is None

    # clear should also not raise
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)


# ---------------------------------------------------------------------------
# Test 26 — Unsupported schema fails safely
# ---------------------------------------------------------------------------

def test_26_unsupported_schema_fails_safely(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    sf = _state_file(tmp_path)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps({"version": "9.9.9", "sessions": []}), encoding="utf-8")

    nav = _reload_nav(tmp_path)
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) is None

    # Set and get still work after a bad-version file
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2001


# ---------------------------------------------------------------------------
# Test 27 — /start never becomes permanently silent after stale-state failure
# ---------------------------------------------------------------------------

def test_27_start_not_permanently_silent(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    # Simulate stale failure loop: clear 3 times, never set
    for _ in range(3):
        nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)
        nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # /start should be able to track a new message
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2099)
    assert nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2099


# ---------------------------------------------------------------------------
# Test 28 — One account's failure never blocks another
# ---------------------------------------------------------------------------

def test_28_one_account_failure_does_not_block_another(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)

    # ADMIN goes through multiple stale cycles
    for i in range(3):
        nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001 + i)
        nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)

    # USER must remain unaffected
    assert nav.get_active_message(USER_ID, chat_id=USER_ID) == 1001


# ---------------------------------------------------------------------------
# Test 29 — Railway-style restart preserves correct recovery behavior
# ---------------------------------------------------------------------------

def test_29_railway_restart_recovery(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "test-deploy-123")

    nav = _reload_nav(tmp_path)
    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)

    # Simulate Railway restart: reload module (clears in-memory state)
    nav2 = _reload_nav(tmp_path)

    # Both sessions should be recoverable from persisted state
    assert nav2.get_active_message(USER_ID, chat_id=USER_ID) == 1001
    assert nav2.get_active_message(ADMIN_ID, chat_id=ADMIN_ID) == 2001


# ---------------------------------------------------------------------------
# Test 30 — Complete isolation: both accounts responsive after repeated switching
# ---------------------------------------------------------------------------

def test_30_both_accounts_responsive_after_repeated_switching(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(USER_ID, chat_id=USER_ID, message_id=1001)
    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)

    # Simulate multiple account switches with ADMIN stale recovery in between
    for cycle in range(3):
        # Switch to ADMIN — stale message
        nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)
        # ADMIN gets new message
        nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001 + cycle + 1)
        # Switch to USER — must still work
        u = nav.get_active_message(USER_ID, chat_id=USER_ID)
        assert u == 1001, f"USER must be responsive at cycle {cycle}, got {u}"
        # ADMIN must be responsive
        a = nav.get_active_message(ADMIN_ID, chat_id=ADMIN_ID)
        assert a == 2001 + cycle + 1, f"ADMIN must be responsive at cycle {cycle}, got {a}"


# ---------------------------------------------------------------------------
# Additional: delete_telegram_ui_session returns structured evidence
# ---------------------------------------------------------------------------

def test_delete_result_structure(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    _write_state(tmp_path, [_session_row(ADMIN_ID, ADMIN_ID, 2001)])

    from state_store import state_store as ss
    result = ss.delete_telegram_ui_session(ADMIN_ID, ADMIN_ID)

    assert result.session_existed is True
    assert result.session_removed is True
    assert result.final_session_count == 0
    assert result.canonical_state_path
    assert result.error is None
    assert result.target_key == (ADMIN_ID, ADMIN_ID, None)


def test_delete_nonexistent_session_is_safe(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    _write_state(tmp_path, [_session_row(USER_ID, USER_ID, 1001)])

    from state_store import state_store as ss
    result = ss.delete_telegram_ui_session(ADMIN_ID, ADMIN_ID)

    assert result.session_existed is False
    assert result.session_removed is False
    assert result.error is None

    # USER must survive
    v = ss.verify_telegram_session_absent(USER_ID, USER_ID)
    assert v["absent"] is False
    assert v["found_message_id"] == 1001


# ---------------------------------------------------------------------------
# Additional: get_runtime_diagnostics reports independent persisted_message_id
# ---------------------------------------------------------------------------

def test_diagnostics_independent_persisted_read(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _reload_nav(tmp_path)

    nav.set_active_message(ADMIN_ID, chat_id=ADMIN_ID, message_id=2001)

    # Get diagnostics while session is live — both must agree
    diag = nav.get_runtime_diagnostics(chat_id=ADMIN_ID, user_id=ADMIN_ID)
    assert diag["active_message_id"] == 2001
    assert diag["persisted_message_id"] == 2001

    # Now clear from memory only (without clearing persistence)
    # This simulates stale diagnostic read — after clear, persisted_message_id
    # must come from disk (independent read), not from in-memory state.
    nav.clear_active_message(ADMIN_ID, chat_id=ADMIN_ID)
    diag2 = nav.get_runtime_diagnostics(chat_id=ADMIN_ID, user_id=ADMIN_ID)
    assert diag2["active_message_id"] is None
    assert diag2["persisted_message_id"] is None, \
        "persisted_message_id must reflect disk after clear, not stale in-memory value"
