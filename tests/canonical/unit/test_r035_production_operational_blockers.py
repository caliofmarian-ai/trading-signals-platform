"""R-035: safe, bounded production error and prior-state diagnostics."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import railway_operational_blocker_diagnostics as blockers
from scripts import railway_observability_checkpoint as checkpoint
from scripts import railway_source_tail_diagnostics as tails


NOW = 1793358000


def _evt(
    code: str,
    *,
    kind: str = "warning",
    ts: int = NOW - 30,
    secret: str = "SECRET-USER-TOKEN-123",
) -> dict:
    return {
        "event_id": f"EV-{code}",
        "schema_version": "3.0.0",
        "event_type": kind,
        "ts_epoch_ms": ts * 1000,
        "user_id": 99999999,
        "chat_id": -100777,
        "data": {
            "code": code,
            "error_type": code,
            "message": "private message " + secret,
            "stack": secret,
            "context": {"api_key": secret},
        },
    }


def _write(path: Path, rows: list[dict], *, corrupt: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = [json.dumps(row) + "\n" for row in rows]
    if corrupt:
        content.insert(0, "{invalid: private data}\n")
    path.write_text("".join(content), encoding="utf-8")
    return path


def test_missing_and_empty_error_logs_are_not_fabricated_healthy(tmp_path: Path):
    missing = blockers.inspect_error_tail(path=tmp_path / "absent", now_ts=NOW)
    assert missing["status"] == "ERROR_LOG_NOT_FOUND"
    assert missing["warning_or_error_rows_in_tail_24h"] is None
    assert missing["coverage"] == "NONE"
    file = tmp_path / "empty.jsonl"
    file.touch()
    empty = blockers.inspect_error_tail(path=file, now_ts=NOW)
    assert empty["status"] == "EMPTY_FILE"
    assert empty["coverage"] == "FULL_FILE"
    assert empty["warning_or_error_rows_in_tail_24h"] == 0


def test_live_market_blockers_categorized_by_code_without_source_pii(tmp_path: Path):
    source = _write(tmp_path / "errors.jsonl", [
        _evt("MARKET_DATA_UNAVAILABLE"),
        _evt("MARKET_DATA_UNAVAILABLE", ts=NOW - 40),
        _evt("MARKET_DATA_LIMITED", kind="error"),
        _evt("unknown_code_SENSITIVE_BOT_TOKEN"),
        _evt("OLD_WARNING", ts=NOW - 86401),
    ])
    before = source.read_bytes()
    report = blockers.inspect_error_tail(path=source, now_ts=NOW)
    assert report["status"] == "OBSERVED_TAIL"
    assert report["coverage"] == "FULL_FILE"
    assert report["warning_or_error_rows_in_tail_24h"] == 4
    assert report["allowlisted_code_counts_in_tail_24h"] == {
        "MARKET_DATA_LIMITED": 1,
        "MARKET_DATA_UNAVAILABLE": 2,
    }
    assert report["other_codes_in_tail_24h"] == 1
    assert report["not_a_complete_24h_error_rate"] is True
    payload = json.dumps(report)
    for forbidden in (
        "SECRET-USER-TOKEN-123", "99999999", "-100777",
        "unknown_code_SENSITIVE_BOT_TOKEN", "private message", "api_key",
        str(source),
    ):
        assert forbidden not in payload
    assert source.read_bytes() == before


def test_capped_large_error_log_returns_suffix_only(tmp_path: Path):
    source = tmp_path / "large_errors.jsonl"
    with source.open("wb") as handle:
        handle.truncate(18 * 1024 * 1024)
        handle.seek(18 * 1024 * 1024)
        handle.write(b"\n")
        handle.write((json.dumps(_evt("NO_ACTIVE_SYMBOLS")) + "\n").encode())
    report = blockers.inspect_error_tail(path=source, now_ts=NOW)
    assert report["status"] == "OBSERVED_TAIL"
    assert report["coverage"] == "SUFFIX_ONLY"
    assert report["size_mib"] > 16
    assert report["warning_or_error_rows_in_tail_24h"] == 1
    assert report["allowlisted_code_counts_in_tail_24h"]["NO_ACTIVE_SYMBOLS"] == 1


def test_malformed_and_incomplete_tail_rows_never_trigger_output_leak(tmp_path: Path):
    source = _write(tmp_path / "errors.jsonl", [_evt("ALGO_PARAMS_VALIDATION_FAILED")], corrupt=True)
    with source.open("ab") as handle:
        handle.write(b'{"message":"SECRET-UNTERMINATED')
    report = blockers.inspect_error_tail(path=source, now_ts=NOW)
    assert report["invalid_tail_rows"] == 2
    assert report["allowlisted_code_counts_in_tail_24h"]["ALGO_PARAMS_VALIDATION_FAILED"] == 1
    assert "SECRET" not in json.dumps(report)


def test_preboot_status_is_explicitly_historical_and_excludes_sensitive_fields(tmp_path: Path):
    path = tmp_path / "runtime_status.json"
    _write(path, [{
        "phase": "RUNNING",
        "market_data_provider": "TWELVE_DATA",
        "last_strategy_decision_kind": "NO_SIGNAL",
        "last_strategy_evaluation_ts": NOW - 100_000,
        "strategy_evaluation_count": 123,
        "updated_ts": NOW - 60,
        "last_strategy_symbol": "PRIVATE-CUSTOMER-IDENTIFIER",
        "api_key": "PRIVATE-TOKEN",
        "message": "SECRET-MESSAGE",
    }])
    # The fixture above is JSONL; the runtime status is one JSON object file.
    path.write_text(json.dumps({
        "phase": "RUNNING", "market_data_provider": "TWELVE_DATA",
        "last_strategy_decision_kind": "NO_SIGNAL",
        "last_strategy_evaluation_ts": NOW - 100_000,
        "strategy_evaluation_count": 123, "updated_ts": NOW - 60,
        "last_strategy_symbol": "PRIVATE-CUSTOMER-IDENTIFIER",
        "message": "SECRET-MESSAGE", "api_key": "PRIVATE-TOKEN",
    }), encoding="utf-8")
    report = blockers.inspect_preboot_runtime_status(path=path, now_ts=NOW)
    assert report["status"] == "PERSISTED_SNAPSHOT"
    assert report["scope"] == "PREBOOT_PERSISTED_NOT_CURRENT_LIVE"
    assert report["prior_process_provider"] == "TWELVE_DATA"
    assert report["prior_process_last_strategy_kind"] == "NO_SIGNAL"
    assert report["prior_process_strategy_evaluation_count"] == 123
    assert report["prior_process_last_strategy_evaluation_utc"] == datetime.fromtimestamp(
        NOW - 100_000, timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert report["no_current_runtime_health_claim"] is True
    serialized = json.dumps(report)
    for sensitive in ("PRIVATE-CUSTOMER-IDENTIFIER", "PRIVATE-TOKEN", "SECRET-MESSAGE"):
        assert sensitive not in serialized


def test_invalid_preboot_status_is_unknown_not_running(tmp_path: Path):
    path = tmp_path / "broken.json"
    path.write_text("{invalid_json", encoding="utf-8")
    assert blockers.inspect_preboot_runtime_status(path=path, now_ts=NOW)["status"] == "UNKNOWN"
    path.write_bytes(b"x" * (blockers.STATE_FILE_MAX_BYTES + 1))
    assert blockers.inspect_preboot_runtime_status(path=path, now_ts=NOW)["status"] == "UNKNOWN"


def test_persisted_owner_provider_precedence_is_visible_without_owner_id(tmp_path: Path):
    path = tmp_path / "market_data_provider.json"
    path.write_text(
        json.dumps({
            "active_provider": "TWELVE_DATA", "mode": "EXCLUSIVE",
            "selection_source": "TELEGRAM_ADMIN",
            "selected_by": 6766369444,
            "api_key": "SECRET-NOT-TO-PRINT",
        }),
        encoding="utf-8",
    )
    payload = blockers.inspect_provider_selection(path=path)
    assert payload["status"] == "VALID_HEADER"
    assert payload["effective_selection_source"] == "PERSISTED_OWNER_SELECTION"
    assert payload["persisted_provider"] == "TWELVE_DATA"
    assert payload["persisted_mode"] == "EXCLUSIVE"
    serialized = json.dumps(payload)
    assert "6766369444" not in serialized
    assert "SECRET-NOT-TO-PRINT" not in serialized
    assert "selected_by" not in serialized


def test_no_persisted_provider_state_is_not_reported_as_owner_selection(tmp_path: Path):
    result = blockers.inspect_provider_selection(path=tmp_path / "missing")
    assert result["status"] == "ABSENT"
    assert result["effective_selection_source"] == "ENVIRONMENT_BOOTSTRAP_ONLY"


def test_last_target_event_date_is_separate_from_fresh_system_boot(tmp_path: Path):
    now_evt = {
        "event_id": "CURRENT-BOOT", "schema_version": "3.0.0",
        "event_type": "engine_start", "ts_epoch_ms": NOW * 1000,
    }
    old_decision = {
        "event_id": "LAST-DECISION", "schema_version": "3.0.0",
        "event_type": "decision_evaluated",
        "ts_epoch_ms": (NOW - 86401) * 1000,
    }
    log = _write(tmp_path / "engine.jsonl", [old_decision, now_evt])
    result = tails.inspect_source(source="engine", path=log, now_ts=NOW)
    assert result["last_event_utc"] == datetime.fromtimestamp(
        NOW, timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert result["last_target_event_utc"] == datetime.fromtimestamp(
        NOW - 86401, timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert result["tail_utc_24h_header_rows"] == 0
    assert "LAST-DECISION" not in json.dumps(result)


def test_combined_operational_diagnostics_never_write_or_print_private_data(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ERROR_EVENTS_LOG", raising=False)
    root = tmp_path
    errors = _write(
        root / "observability" / "error_events.jsonl",
        [_evt("MARKET_DATA_UNAVAILABLE")],
    )
    provider = root / "config" / "market_data_provider.json"
    provider.parent.mkdir(parents=True, exist_ok=True)
    provider.write_text(
        json.dumps({"active_provider": "TWELVE_DATA", "mode": "EXCLUSIVE",
                    "selected_by": "PRIVATE-USER"}),
        encoding="utf-8",
    )
    before_errors, before_provider = errors.read_bytes(), provider.read_bytes()
    result = blockers.collect_blocker_diagnostics(base_dir=root, now_ts=NOW)
    assert result["scope"] == "ONE_SHOT_READ_ONLY_PREBOOT_BLOCKER_EVIDENCE"
    assert result["error_event_tail"]["allowlisted_code_counts_in_tail_24h"] == {
        "MARKET_DATA_UNAVAILABLE": 1
    }
    assert result["provider_selection"]["persisted_provider"] == "TWELVE_DATA"
    assert result["prior_runtime_state"]["status"] == "UNKNOWN"
    serialized = json.dumps(result)
    assert "PRIVATE-USER" not in serialized
    assert str(root) not in serialized
    assert errors.read_bytes() == before_errors
    assert provider.read_bytes() == before_provider


def test_production_checkpoint_includes_error_diagnostics_without_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import core
    import importlib

    for n in ("publication_evidence", "lifecycle_funnel_evidence",
              "market_outcome_evidence", "focus_history_evidence"):
        mod = importlib.import_module("core." + n)
        monkeypatch.setattr(core, n, mod, raising=False)
    monkeypatch.delenv("ERROR_EVENTS_LOG", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "PRIVATE-BOT-TOKEN")
    result = checkpoint.collect_checkpoint(base_dir=tmp_path, now_ts=NOW)
    assert "operational_blockers" in result
    assert result["operational_blockers"]["scope"] == "ONE_SHOT_READ_ONLY_PREBOOT_BLOCKER_EVIDENCE"
    assert result["operational_blockers"]["error_event_tail"]["status"] in {
        "ERROR_LOG_NOT_FOUND", "EMPTY_FILE",
    }
    assert "PRIVATE-BOT-TOKEN" not in json.dumps(result)


@pytest.mark.parametrize("bad_time", [True, -1, 0, 2.4, "1793358000"])
def test_error_reader_rejects_invalid_time(bad_time, tmp_path: Path):
    with pytest.raises(ValueError):
        blockers.inspect_error_tail(
            path=tmp_path / "errors.jsonl", now_ts=bad_time
        )
