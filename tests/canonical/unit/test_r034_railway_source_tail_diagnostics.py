"""R-034: production log suffix diagnostics are bounded and never authority.

All counts are labeled as tail samples, not full-window metrics. No raw source
records, sensitive IDs, prices or log paths can reach Railway stdout.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import railway_source_tail_diagnostics as tails
from scripts import railway_observability_checkpoint as probe


NOW = 1793358000


def _event(name: str, *, event_type: str = "fsm_transition", ts: int = NOW - 20) -> dict:
    return {
        "schema_version": "3.0.0",
        "event_id": name,
        "event_type": event_type,
        "ts_epoch_ms": ts * 1000,
        "signal_id": "PRIVATE-SIGNAL-000001",
        "chat_id": -1009876543210,
        "entry_price": 1.2345,
        "data": {
            "symbol": "EUR/USD",
            "trigger": "watchlist_added",
        },
    }


def _write(path: Path, records: list[dict], *, invalid=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record) + "\n" for record in records]
    if invalid:
        lines.insert(0, "invalid json\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path


def test_missing_and_empty_files_are_distinct_and_unknown_not_valid_zero(tmp_path: Path):
    absent = tails.inspect_source(source="engine", path=tmp_path / "absent", now_ts=NOW)
    assert absent["status"] == "FILE_NOT_FOUND"
    assert absent["tail_json_objects"] is None
    assert absent["coverage"] == "NONE"

    empty = tmp_path / "empty.jsonl"
    empty.touch()
    value = tails.inspect_source(source="engine", path=empty, now_ts=NOW)
    assert value["status"] == "EMPTY_FILE"
    assert value["coverage"] == "FULL_FILE"
    assert value["tail_json_objects"] == 0
    assert value["tail_target_family_rows"] == 0


def test_short_fsm_file_diagnostic_counts_only_v3_header_and_known_event_family(
    tmp_path: Path,
):
    path = _write(tmp_path / "fsm.jsonl", [
        _event("SECRET-A"),
        _event("SECRET-B") | {"schema_version": "2.0.0"},
        _event("SECRET-C", event_type="warning"),
    ])
    before = path.read_bytes()
    output = tails.inspect_source(source="fsm", path=path, now_ts=NOW)
    assert output["status"] == "OBSERVED_TAIL"
    assert output["coverage"] == "FULL_FILE"
    assert output["tail_json_objects"] == 3
    assert output["tail_primary_v3_header_rows"] == 2
    assert output["tail_target_family_rows"] == 1
    assert output["tail_utc_24h_header_rows"] == 1
    assert output["over_16_mib"] is False
    assert output["last_event_utc"] == datetime.fromtimestamp(
        NOW - 20, timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert path.read_bytes() == before
    encoded = json.dumps(output)
    for sensitive in ("SECRET-A", "PRIVATE-SIGNAL-000001", "-1009876543210",
                      "1.2345", str(path), "entry_price"):
        assert sensitive not in encoded


def test_distribution_route_row_count_is_not_distinct_signals(tmp_path: Path):
    published = _event("A", event_type="route_publish_result")
    published.update(stage="OPEN_NOW", data={"publish_result": "PUBLISHED"})
    duplicate_tier = published | {"event_id": "B", "route": "PRO"}
    failed = published | {"event_id": "C", "data": {"publish_result": "FAILED"}}
    output = tails.inspect_source(
        source="distribution",
        path=_write(tmp_path / "distribution.jsonl", [
            published, duplicate_tier, failed
        ]),
        now_ts=NOW,
    )
    assert output["tail_open_now_published_route_rows"] == 2
    assert output["tail_target_family_rows"] == 3
    assert output["coverage"] == "FULL_FILE"
    assert "unique_open_now" not in json.dumps(output)


def test_large_file_reads_suffix_only_and_explicitly_cannot_prove_24h(
    tmp_path: Path,
):
    source = tmp_path / "large-fsm-events.jsonl"
    with source.open("wb") as handle:
        handle.truncate(17 * 1024 * 1024)  # sparse historical placeholder
        handle.seek(17 * 1024 * 1024)
        handle.write(b"\n")
        handle.write((json.dumps(_event("TAIL-ONLY")) + "\n").encode("utf-8"))
    output = tails.inspect_source(source="fsm", path=source, now_ts=NOW)
    assert output["status"] == "OBSERVED_TAIL"
    assert output["coverage"] == "SUFFIX_ONLY"
    assert output["size_mib"] > 16.0
    assert output["over_16_mib"] is True
    assert output["tail_read_bytes"] == tails.TAIL_BYTES
    assert output["tail_target_family_rows"] == 1
    assert "PRIVATE-SIGNAL" not in json.dumps(output)


def test_oversized_single_record_is_not_parsed_as_valid_tail(tmp_path: Path):
    source = tmp_path / "one-giant-row.jsonl"
    source.write_text(
        json.dumps({"private": "X" * (tails.TAIL_BYTES + 100)}) + "\n",
        encoding="utf-8"
    )
    report = tails.inspect_source(source="engine", path=source, now_ts=NOW)
    assert report["coverage"] == "SUFFIX_ONLY"
    assert report["status"] == "NO_COMPLETE_ROW_IN_BOUNDED_SUFFIX"
    assert report["tail_target_family_rows"] is None


def test_malformed_or_incomplete_last_line_is_not_primary_truth(tmp_path: Path):
    source = _write(tmp_path / "bad.jsonl", [_event("VALID")], invalid=True)
    with source.open("ab") as h:
        h.write(b'{"event_id":"SECRET-INCOMPLETE"')
    report = tails.inspect_source(source="fsm", path=source, now_ts=NOW)
    assert report["tail_target_family_rows"] == 1
    assert report["invalid_tail_rows"] == 2
    assert "SECRET-INCOMPLETE" not in json.dumps(report)


def test_market_source_uses_separate_truth_contract_not_event_schema(tmp_path: Path):
    record = {
        "trade_id": "PRIVATE-TRADE-555",
        "telemetry_version": "3.0.0",
        "truth_domain": "MARKET_TRUTH",
        "telemetry_status": "FINALIZED",
        "finalized_ts": NOW - 10,
        "result_at_expiry": "WIN",
        "entry_price": 1.22,
    }
    report = tails.inspect_source(
        source="market",
        path=_write(tmp_path / "telemetry.jsonl", [record]),
        now_ts=NOW,
    )
    assert report["tail_target_family_rows"] == 1
    assert report["tail_primary_v3_header_rows"] is None
    assert "WIN" not in json.dumps(report)
    assert "PRIVATE-TRADE-555" not in json.dumps(report)
    assert "1.22" not in json.dumps(report)


def test_all_four_source_paths_are_resolved_but_never_exported(tmp_path: Path, monkeypatch):
    for key in (
        "ENGINE_EVENTS_LOG", "DIST_EVENTS_LOG", "FSM_EVENTS_LOG",
        "TRADE_TEMPORAL_TELEMETRY_LOG",
    ):
        monkeypatch.delenv(key, raising=False)

    obs = tmp_path / "observability"
    expected_files = {
        "engine": "engine_events.jsonl",
        "distribution": "distribution_events.jsonl",
        "fsm": "fsm_events.jsonl",
        "market": "trade_temporal_telemetry.jsonl",
    }
    for k, file_name in expected_files.items():
        if k == "market":
            _write(obs / file_name, [{
                "truth_domain": "MARKET_TRUTH",
                "telemetry_version": "3.0.0",
                "telemetry_status": "FINALIZED",
                "finalized_ts": NOW,
            }])
        else:
            event_type = {
                "engine": "decision_evaluated",
                "distribution": "route_publish_result",
                "fsm": "fsm_transition",
            }[k]
            _write(obs / file_name, [_event(f"SOURCE-{k}", event_type=event_type)])
    report = tails.collect_source_tails(base_dir=tmp_path, now_ts=NOW)
    assert report["purpose"] == "BOUNDED_SUFFIX_DIAGNOSTIC_NOT_FULL_WINDOW_STATISTICS"
    assert set(report["source_tails"]) == set(expected_files)
    assert all(x["status"] == "OBSERVED_TAIL" for x in report["source_tails"].values())
    rendered = json.dumps(report)
    assert str(tmp_path) not in rendered
    assert "PRIVATE-SIGNAL" not in rendered
    assert "SOURCE-" not in rendered


def test_provider_marker_is_allowlisted_and_no_env_secret_escapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import core
    import importlib

    modules = {
        n: importlib.import_module("core." + n)
        for n in (
            "publication_evidence", "lifecycle_funnel_evidence",
            "market_outcome_evidence", "focus_history_evidence",
        )
    }
    for n, mod in modules.items():
        monkeypatch.setattr(core, n, mod, raising=False)

    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "PRIVATE-SENSITIVE-TOKEN")
    report = probe.collect_checkpoint(base_dir=tmp_path, now_ts=NOW)
    assert report["configured_provider_from_env"] == "FINNHUB"
    assert "source_diagnostics" in report
    assert report["source_diagnostics"]["source_tails"]["engine"]["status"] == "FILE_NOT_FOUND"
    serialized = json.dumps(report)
    assert "PRIVATE-SENSITIVE-TOKEN" not in serialized
    assert str(tmp_path) not in serialized

    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB\npassword=SECRET")
    fail_closed = probe.collect_checkpoint(base_dir=tmp_path, now_ts=NOW)
    assert fail_closed["configured_provider_from_env"] == "UNKNOWN"
    assert "password" not in json.dumps(fail_closed)


@pytest.mark.parametrize("source", ["unknown", "", "BACKUP", "ADMIN"])
def test_unsupported_source_fails_closed(source, tmp_path: Path):
    with pytest.raises(ValueError):
        tails.inspect_source(
            source=source, path=tmp_path / "something.jsonl", now_ts=NOW
        )


@pytest.mark.parametrize("invalid_time", [-1, 0, True, 7.5, "1793358000"])
def test_invalid_time_rejected(invalid_time, tmp_path: Path):
    with pytest.raises(ValueError):
        tails.inspect_source(
            source="engine", path=tmp_path / "x", now_ts=invalid_time
        )
