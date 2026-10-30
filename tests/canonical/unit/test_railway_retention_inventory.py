"""No-write, bounded, privacy-preserving retention dry-run coverage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.railway_retention_inventory import collect_retention_inventory


NOW = int(datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc).timestamp())


def _file(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_existing_live_observability_files_are_never_deletion_candidates(tmp_path: Path):
    live = _file(tmp_path / "observability" / "engine_events.jsonl", "SENSITIVE-BINARY-STRATEGY-ID\n" * 3000)
    old_segment = _file(tmp_path / "observability" / "engine_events_2026-09-01.jsonl", "SENSITIVE-CHAT-ID\n" * 4)
    admin_proof = _file(tmp_path / "observability" / "admin_proofs_2026-09-01.jsonl", "SECRET-ADMIN-KEY\n")
    outcome = _file(tmp_path / "outcomes" / "outcomes.jsonl", "PERMANENT-TRUTH\n")
    contents = [f.read_bytes() for f in (live, old_segment, admin_proof, outcome)]

    report = collect_retention_inventory(base_dir=tmp_path, now_ts=NOW)
    operational = report["categories"]["operational_observability"]
    admin = report["categories"]["administrative_proofs"]
    outcomes = report["categories"]["outcome_truth"]

    assert operational["observed_files"] == 2
    assert operational["active_unsegmented_mib"] > 0
    assert operational["archival_candidates_unverified_count"] == 1
    assert admin["archival_candidates_unverified_count"] == 0
    assert admin["policy_min_days"] == 365
    assert outcomes["policy_min_days"] is None
    assert outcomes["archival_candidates_unverified_count"] == 0
    assert report["eligible_for_deletion"] is False
    assert report["actual_freed_bytes"] == 0

    serialized = json.dumps(report)
    for secret in ("SENSITIVE", "STRATEGY", "SECRET-ADMIN-KEY", "PERMANENT-TRUTH", str(tmp_path)):
        assert secret not in serialized
    assert contents == [f.read_bytes() for f in (live, old_segment, admin_proof, outcome)]


def test_future_invalid_or_unsegmented_names_are_protected(tmp_path: Path):
    obs = tmp_path / "observability"
    _file(obs / "error_events_2026-11-01.jsonl", "future")
    _file(obs / "error_events_2026-02-30.jsonl", "bad-date")
    _file(obs / "error_events.jsonl", "live")
    _file(obs / "unclassified_private_user.jsonl", "private")
    report = collect_retention_inventory(base_dir=tmp_path, now_ts=NOW)
    operational = report["categories"]["operational_observability"]
    assert operational["observed_files"] == 4
    assert operational["archival_candidates_unverified_count"] == 0
    assert operational["unknown_or_protected_count"] == 3


def test_scan_cap_explicitly_marks_partial_not_exhaustive(tmp_path: Path):
    obs = tmp_path / "observability"
    for n in range(4):
        _file(obs / f"engine_events_2026-09-0{n+1}.jsonl", "x")
    report = collect_retention_inventory(
        base_dir=tmp_path, now_ts=NOW, max_directory_entries=1
    )
    assert report["coverage"] == "PARTIAL"
    assert report["scopes"]["observability"] == "PARTIAL_ENTRY_CAP"
    assert report["categories"]["operational_observability"]["observed_files"] == 1


def test_symlink_is_never_followed_and_names_are_not_exposed(tmp_path: Path):
    obs = tmp_path / "observability"
    obs.mkdir()
    hidden = _file(tmp_path / "outside_secret.txt", "RAW-PRIVATE-IDENTIFIER")
    (obs / "engine_events_2026-01-01.jsonl").symlink_to(hidden)
    report = collect_retention_inventory(base_dir=tmp_path, now_ts=NOW)
    assert report["categories"]["operational_observability"]["observed_files"] == 0
    assert "outside_secret" not in json.dumps(report)
    assert "RAW-PRIVATE" not in json.dumps(report)


def test_invalid_observation_time_and_limit_fail_closed(tmp_path: Path):
    import pytest
    for invalid in (True, 0, -1, "tomorrow"):
        with pytest.raises(ValueError):
            collect_retention_inventory(base_dir=tmp_path, now_ts=invalid)
    for invalid_limit in (0, -5, True, 4097):
        with pytest.raises(ValueError):
            collect_retention_inventory(
                base_dir=tmp_path, now_ts=NOW, max_directory_entries=invalid_limit
            )
