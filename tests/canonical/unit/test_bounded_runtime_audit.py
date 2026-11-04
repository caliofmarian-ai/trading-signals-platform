from __future__ import annotations

import importlib
import json
import builtins
from pathlib import Path

import pytest


def test_runtime_audit_never_uses_full_history_iterator(tmp_path, monkeypatch):
    admin = importlib.import_module("core.admin_commands")
    status = importlib.import_module("runtime.runtime_status")
    monkeypatch.setattr(admin, "require_permission", lambda *a: (True, ""))
    monkeypatch.setattr(admin, "_audit", lambda *a: None)
    monkeypatch.setattr(status, "read_status", lambda: {"phase": "running"})
    monkeypatch.setattr(admin, "_load_algo_params", lambda: {})
    monkeypatch.setattr(admin, "get_current_strategy_profile_observation", lambda: {})
    monkeypatch.setattr(admin._provider_control, "provider_summary", lambda: {})
    monkeypatch.setattr(admin, "_load_active_symbols_observation", lambda: ["EURUSD"])
    monkeypatch.setattr(admin, "OBS_DIR", str(tmp_path))
    rows = [{"event_type": "signal_execution_result", "event_id": "EXACT-ID",
             "ts_utc": "2026-11-04T08:52:03Z", "data": {"outcome": "BLOCKED"}}]
    rows += [{"event_type": "decision_evaluated", "event_id": f"D-{i}"} for i in range(80)]
    source = tmp_path / "engine.jsonl"
    source.write_text("".join(json.dumps(x) + "\n" for x in rows))
    monkeypatch.setattr(admin, "ENGINE_EVENTS_PATH", str(source))
    monkeypatch.setattr(admin, "ADMIN_EVENTS_PATH", str(tmp_path / "absent"))

    def forbidden(*a, **k):
        raise AssertionError("audit must not scan the complete append-only history")

    monkeypatch.setattr(admin, "_iter_jsonl", forbidden)
    path, error = admin.handle_audit_runtime(123)
    assert not error
    payload = json.loads(Path(path).read_text())
    assert len(payload["recent_engine_events"]) == 50
    assert payload["recent_signal_execution_events"][0] == rows[0]
    assert payload["source_windows"]["engine"]["status"] == "OK"
    assert payload["source_windows"]["admin"]["status"] == "MISSING"


def test_runtime_audit_denies_before_any_evidence_read(monkeypatch):
    admin = importlib.import_module("core.admin_commands")
    monkeypatch.setattr(admin, "require_permission", lambda *a: (False, "denied"))
    monkeypatch.setattr(admin, "_iter_jsonl", lambda *a: pytest.fail("unauthorized read"))
    monkeypatch.setattr(admin, "_read_jsonl_tail", lambda *a, **k: pytest.fail("unauthorized tail read"))
    assert admin.handle_audit_runtime(123) == (None, "denied")


@pytest.fixture
def lifecycle_audit(tmp_path, monkeypatch):
    admin = importlib.import_module("core.admin_commands")
    status = importlib.import_module("runtime.runtime_status")
    monkeypatch.setattr(admin, "require_permission", lambda *a: (True, ""))
    monkeypatch.setattr(admin, "_audit", lambda *a: None)
    monkeypatch.setattr(status, "read_status", lambda: {})
    monkeypatch.setattr(admin, "_load_algo_params", lambda: {})
    monkeypatch.setattr(admin, "get_current_strategy_profile_observation", lambda: {})
    monkeypatch.setattr(admin._provider_control, "provider_summary", lambda: {})
    monkeypatch.setattr(admin, "_load_active_symbols_observation", lambda: ["EURUSD"])
    monkeypatch.setattr(admin, "OBS_DIR", str(tmp_path))
    monkeypatch.setattr(admin, "ENGINE_EVENTS_PATH", str(tmp_path / "engine.jsonl"))
    monkeypatch.setattr(admin, "ADMIN_EVENTS_PATH", str(tmp_path / "admin.jsonl"))
    monkeypatch.delenv("FSM_EVENTS_LOG", raising=False)
    return admin


def _fsm_event(prior, resulting, trigger, number):
    from core import observability_logger as logger

    event = logger.build_event(
        "fsm_transition",
        {"symbol": "EUR/USD", "signal_id": "sig-exact-pre",
         "prev_state": prior, "new_state": resulting, "trigger": trigger,
         "candle_ts": 1793812200},
        source={"module": "tests", "function": "lifecycle_audit"},
        correlation={"decision_id": f"dec-{number}", "decision_audit_id": f"audit-{number}"},
    )
    logger.validate_event(event)
    return event


def _audit_payload(admin):
    path, error = admin.handle_audit_runtime(123)
    assert not error
    return json.loads(Path(path).read_text())


def test_runtime_audit_keeps_pre_exit_from_dedicated_fsm_sink(lifecycle_audit, tmp_path):
    # An ordinary REJECT closes PRE without creating a signal_execution_result.
    # Subsequent repeated cooldown observations must not hide the actual exit.
    rows = [_fsm_event("IDLE", "WATCHLIST", "watchlist_added", 0),
            _fsm_event("WATCHLIST", "COOLDOWN", "reject_released", 1)]
    rows += [_fsm_event("COOLDOWN", "COOLDOWN", "cooldown_active", i) for i in range(100)]
    (tmp_path / "fsm_events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    payload = _audit_payload(lifecycle_audit)

    assert payload["recent_fsm_events"] == rows[-50:]
    assert payload["recent_fsm_lifecycle_events"] == rows[:2]
    assert payload["recent_signal_execution_events"] == []
    meta = payload["source_windows"]["fsm_lifecycle"]
    assert meta["status"] == "OK"
    assert meta["matching_records_in_window"] == 2
    assert meta["record_limit"] == 5000
    assert not meta["export_truncated"]
    assert meta["absence_is_not_complete_history_proof"]
    assert not meta["complete_history"]


def test_runtime_audit_honors_configured_fsm_sink(lifecycle_audit, tmp_path, monkeypatch):
    configured = tmp_path / "configured.jsonl"
    row = _fsm_event("WATCHLIST", "COOLDOWN", "focus_lease_expired", 0)
    configured.write_text(json.dumps(row) + "\n")
    (tmp_path / "fsm_events.jsonl").write_text("invalid legacy location\n")
    monkeypatch.setenv("FSM_EVENTS_LOG", str(configured))
    payload = _audit_payload(lifecycle_audit)
    assert payload["recent_fsm_lifecycle_events"] == [row]
    assert payload["source_windows"]["fsm"]["status"] == "OK"


@pytest.mark.parametrize("raw,status,reason", [
    (None, "MISSING", "SOURCE_MISSING"),
    ("invalid\n", "UNAVAILABLE", "INVALID_JSONL_RECORD"),
])
def test_runtime_audit_exposes_unavailable_fsm_evidence(lifecycle_audit, tmp_path, raw, status, reason):
    if raw is not None:
        (tmp_path / "fsm_events.jsonl").write_text(raw)
    payload = _audit_payload(lifecycle_audit)
    assert payload["recent_fsm_lifecycle_events"] == []
    meta = payload["source_windows"]["fsm_lifecycle"]
    assert (meta["status"], meta["reason"]) == (status, reason)
    assert meta["absence_is_not_complete_history_proof"]


def test_runtime_audit_reports_truncated_lifecycle_export(lifecycle_audit, tmp_path):
    rows = [_fsm_event("WATCHLIST", "COOLDOWN", "reject_released", i) for i in range(55)]
    (tmp_path / "fsm_events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    payload = _audit_payload(lifecycle_audit)
    assert payload["recent_fsm_lifecycle_events"] == rows[-50:]
    meta = payload["source_windows"]["fsm_lifecycle"]
    assert meta["matching_records_in_window"] == 55
    assert meta["export_limit"] == 50
    assert meta["export_truncated"]


def test_runtime_audit_does_not_invent_state_change_for_missing_fields(lifecycle_audit, tmp_path):
    rows = [{"event_type": "fsm_transition", "data": {"prev_state": "WATCHLIST"}},
            {"event_type": "fsm_transition", "data": "malformed"},
            {"event_type": "other", "data": {"prev_state": "WATCHLIST", "new_state": "COOLDOWN"}}]
    (tmp_path / "fsm_events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    payload = _audit_payload(lifecycle_audit)
    assert payload["recent_fsm_events"] == rows[:2]
    assert payload["recent_fsm_lifecycle_events"] == []


def test_tail_keeps_exact_identity_and_observed_interval(tmp_path):
    from core.jsonl_tail import read_tail
    source = tmp_path / "events.jsonl"
    rows = [{"event_id": f"E-{i}", "schema_version": "3.0.0", "ts_utc": str(i)} for i in range(100)]
    source.write_text("".join(json.dumps(x) + "\n" for x in rows))
    snapshot = read_tail(str(source), limit=3)
    assert snapshot["records"] == rows[-3:]
    meta = snapshot["metadata"]
    assert meta["status"] == "OK"
    assert meta["record_limited"] and not meta["complete_history"]
    assert (meta["first_event_ts"], meta["last_event_ts"]) == ("97", "99")


def test_large_history_is_never_read_past_byte_budget(tmp_path, monkeypatch):
    from core.jsonl_tail import read_tail
    source = tmp_path / "large.jsonl"
    with source.open("wb") as handle:
        handle.seek(32 * 1024 * 1024)
        handle.write(b'\n{"event_id":"retained"}\n')
    actual_open = builtins.open
    widths = []

    class Measured:
        def __init__(self, handle): self.handle = handle
        def __enter__(self): return self
        def __exit__(self, *args): self.handle.close()
        def __getattr__(self, name): return getattr(self.handle, name)
        def read(self, size=-1):
            assert size > 0, "unbounded read"
            widths.append(size)
            return self.handle.read(size)

    monkeypatch.setattr(builtins, "open", lambda *a, **k: Measured(actual_open(*a, **k)))
    snapshot = read_tail(str(source), limit=50, max_bytes=128 * 1024)
    assert snapshot["records"] == [{"event_id": "retained"}]
    assert sum(widths) <= 128 * 1024
    assert snapshot["metadata"]["byte_limited"]
    assert snapshot["metadata"]["status"] == "OK"


@pytest.mark.parametrize("raw", [b'{"event_id":', b'[]\n', b'\xff\n', b'{"value":NaN}\n'])
def test_bad_tail_is_unavailable_not_zero_events(tmp_path, raw):
    from core.jsonl_tail import read_tail
    source = tmp_path / "bad.jsonl"
    source.write_bytes(raw)
    snapshot = read_tail(str(source))
    assert snapshot["metadata"]["status"] == "UNAVAILABLE"
    assert snapshot["metadata"]["reason"] == "INVALID_JSONL_RECORD"


def test_missing_empty_and_oversized_record_are_distinct(tmp_path):
    from core.jsonl_tail import read_tail
    source = tmp_path / "events.jsonl"
    assert read_tail(str(source))["metadata"]["status"] == "MISSING"
    source.write_bytes(b"")
    assert read_tail(str(source))["metadata"]["status"] == "OK"
    source.write_bytes(b'{"payload":"' + b'x' * 2000 + b'"}\n')
    assert read_tail(str(source), max_bytes=100)["metadata"]["status"] == "UNAVAILABLE"


@pytest.mark.parametrize("limit,budget", [(0, 100), (True, 100), (5001, 100), (1, 0), (1, True), (1, 17*1024*1024)])
def test_invalid_bounds_fail_before_open(limit, budget, monkeypatch):
    from core.jsonl_tail import read_tail
    monkeypatch.setattr(builtins, "open", lambda *a, **k: pytest.fail("invalid bound opened source"))
    assert read_tail("unused", limit=limit, max_bytes=budget)["metadata"]["reason"] == "INVALID_BOUND"


@pytest.mark.parametrize("change", ["append", "truncate", "rotate"])
def test_source_change_has_explicit_snapshot_semantics(tmp_path, monkeypatch, change):
    from core.jsonl_tail import read_tail
    source = tmp_path / "events.jsonl"
    source.write_text('{"event_id":"before"}\n')
    actual_open = builtins.open

    class Changed:
        def __init__(self, handle): self.handle = handle
        def __enter__(self): return self
        def __exit__(self, *args): self.handle.close()
        def __getattr__(self, name): return getattr(self.handle, name)
        def read(self, size):
            result = self.handle.read(size)
            if change == "append":
                with actual_open(source, "ab") as out: out.write(b'{"event_id":"after"}\n')
            elif change == "truncate":
                source.write_bytes(b"")
            else:
                source.rename(tmp_path / "rotated")
                source.write_text('{"event_id":"replacement"}\n')
            return result

    monkeypatch.setattr(builtins, "open", lambda *a, **k: Changed(actual_open(*a, **k)))
    snapshot = read_tail(str(source))
    if change == "append":
        assert snapshot["records"] == [{"event_id": "before"}]
        assert snapshot["metadata"]["source_grew_during_read"]
    else:
        assert snapshot["metadata"]["status"] == "UNAVAILABLE"
        assert snapshot["metadata"]["reason"] == "SOURCE_CHANGED_DURING_READ"
