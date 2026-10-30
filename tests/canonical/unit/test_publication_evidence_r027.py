from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core import publication_evidence


NOW = int(datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc).timestamp())


def _row(
    signal: str = "SIG-A",
    *,
    ts: int = NOW - 300,
    route: str = "FREE",
    result: str = "PUBLISHED",
    stage: str = "OPEN_NOW",
    version: str = "3.0.0",
    event_type: str = "route_publish_result",
) -> dict:
    return {
        "event_type": event_type,
        "schema_version": version,
        "ts_epoch_ms": ts * 1000,
        "signal_id": signal,
        "route": route,
        "stage": stage,
        "data": {"publish_result": result},
    }


def _write(path: Path, records: list[dict], *, malformed: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.dumps(x) for x in records]
    if malformed:
        rows.insert(1, "{not-json")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_publication_counts_unique_signal_across_tier_routes_not_decisions(tmp_path: Path):
    path = tmp_path / "distribution_events.jsonl"
    rows = [
        _row("SIG-A", route="FREE"),
        _row("SIG-A", route="PRO"),
        _row("SIG-B", result="FAILED"),
        _row("SIG-C", result="SKIPPED_LIMIT"),
        _row("SIG-D", stage="PRE"),
        _row("SIG-E", version="2.0.0"),
        _row("SIG-F", event_type="tier_publish"),
    ]
    _write(path, rows)
    result = publication_evidence.publication_snapshot(
        path=str(path), now_ts=NOW, window_hours=24
    )
    assert result["status"] == "OBSERVED"
    assert result["truth_domain"] == "DISTRIBUTION_TRUTH"
    assert result["unique_open_now_published"] == 1
    assert result["published_route_rows"] == 2
    assert result["deduplicated_publications"] == 1
    assert result["results"]["FAILED"] == 1
    assert result["results"]["SKIPPED_LIMIT"] == 1
    assert result["primary_result_rows"] == 4
    assert result["historical_excluded_count"] == 2
    assert result["published_per_hour_rolling_avg"] == 0.04


def test_out_of_order_route_events_choose_first_publication_timestamp(tmp_path: Path):
    path = tmp_path / "dist.jsonl"
    older = NOW - 5400
    newer = NOW - 300
    _write(path, [_row("SIG-A", ts=newer), _row("SIG-A", ts=older)])
    result = publication_evidence.publication_snapshot(
        path=str(path), now_ts=NOW, window_hours=3
    )
    hour = datetime.fromtimestamp(older // 3600 * 3600, tz=timezone.utc)
    assert result["unique_open_now_published"] == 1
    assert result["hourly_utc"] == {hour.strftime("%Y-%m-%dT%H:%M:%SZ"): 1}
    assert result["max_observed_utc_hour_count"] == 1


def test_missing_file_is_unknown_not_measured_zero(tmp_path: Path):
    result = publication_evidence.publication_snapshot(
        path=str(tmp_path / "missing.jsonl"), now_ts=NOW
    )
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "DISTRIBUTION_LOG_NOT_FOUND"
    assert result["unique_open_now_published"] is None
    assert result["published_per_hour_rolling_avg"] is None
    assert "UNKNOWN — not zero" in publication_evidence.render_publication_summary(result)


def test_only_historical_evidence_is_unknown_not_upgraded_to_v3(tmp_path: Path):
    path = tmp_path / "dist.jsonl"
    _write(path, [_row("SIG-A", version="2.0.0"), _row("SIG-A", event_type="tier_publish")])
    result = publication_evidence.publication_snapshot(path=str(path), now_ts=NOW)
    assert result["status"] == "UNKNOWN"
    assert result["historical_excluded_count"] == 2
    assert result["unique_open_now_published"] is None


def test_primary_failures_only_show_observed_zero_not_synthetic_success(tmp_path: Path):
    path = tmp_path / "dist.jsonl"
    _write(path, [_row("SIG-A", result="FAILED")])
    result = publication_evidence.publication_snapshot(path=str(path), now_ts=NOW)
    assert result["status"] == "OBSERVED"
    assert result["unique_open_now_published"] == 0
    assert result["results"]["FAILED"] == 1
    assert result["published_per_hour_rolling_avg"] == 0.0


def test_malformed_rows_are_exposed_without_stopping_valid_observation(tmp_path: Path):
    path = tmp_path / "dist.jsonl"
    _write(path, [_row("SIG-A"), _row("SIG-B", result="FAILED")], malformed=True)
    result = publication_evidence.publication_snapshot(path=str(path), now_ts=NOW)
    assert result["status"] == "OBSERVED"
    assert result["invalid_count"] == 1
    assert result["unique_open_now_published"] == 1
    assert "invalid rows 1" in publication_evidence.render_publication_summary(result)


def test_invalid_canonical_timestamps_and_signal_identity_are_not_counted(tmp_path: Path):
    path = tmp_path / "dist.jsonl"
    invalid_timestamp = _row("BAD-BOOL")
    invalid_timestamp["ts_epoch_ms"] = True
    invalid_signal = _row("")
    invalid_outcome = _row("BAD-OUTCOME", result="UNKNOWN_PROVIDER")
    _write(path, [invalid_timestamp, invalid_signal, invalid_outcome, _row("OK")])
    result = publication_evidence.publication_snapshot(path=str(path), now_ts=NOW)
    assert result["invalid_count"] == 3
    assert result["unique_open_now_published"] == 1
    assert result["published_route_rows"] == 1


def test_inclusive_rolling_window_boundaries_and_utc_buckets(tmp_path: Path):
    path = tmp_path / "dist.jsonl"
    _write(
        path,
        [
            _row("START", ts=NOW - 3600),
            _row("END", ts=NOW),
            _row("TOO_OLD", ts=NOW - 3601),
            _row("FUTURE", ts=NOW + 1),
        ],
    )
    result = publication_evidence.publication_snapshot(
        path=str(path), now_ts=NOW, window_hours=1
    )
    assert result["unique_open_now_published"] == 2
    assert result["published_per_hour_rolling_avg"] == 2.0
    assert len(result["hourly_utc"]) == 2


def test_report_never_exposes_raw_signal_route_or_user_identifiers(tmp_path: Path):
    path = tmp_path / "dist.jsonl"
    signal = "PRIVATE-SIGNAL-IDENTIFIER-1234567"
    _write(path, [_row(signal)])
    summary = publication_evidence.render_publication_summary(
        publication_evidence.publication_snapshot(path=str(path), now_ts=NOW)
    )
    assert signal not in summary
    assert "route=" not in summary
    assert "Unique signals published: 1" in summary
    assert "Market WIN/LOSS" in summary


@pytest.mark.parametrize("hours", [0, -1, 169, True, 1.5, "24"])
def test_window_hours_fail_closed(hours):
    with pytest.raises(ValueError):
        publication_evidence.publication_snapshot(window_hours=hours)


@pytest.mark.parametrize("bad_now", [0, -1, True, 1.5, "2026-10-30"])
def test_invalid_now_timestamp_fails_closed(bad_now):
    with pytest.raises(ValueError):
        publication_evidence.publication_snapshot(now_ts=bad_now)


def test_research_panel_shows_read_only_publication_evidence(monkeypatch):
    import core
    from core import admin_permissions, bot_service
    from core.role_constants import ROLE_OWNER

    # Other repository tests reload core modules; force the package attribute
    # used by the function-local import to point at the same instrumented module.
    monkeypatch.setattr(core, "publication_evidence", publication_evidence)
    monkeypatch.setattr(bot_service, "get_primary_role", lambda _id: ROLE_OWNER)
    monkeypatch.setattr(
        admin_permissions,
        "has_permission",
        lambda _user_id, permission: permission == "admin.view",
    )
    monkeypatch.setattr(bot_service, "_iter_recent_engine_events", lambda limit=500: [])
    monkeypatch.setattr(
        publication_evidence,
        "publication_snapshot",
        lambda: {
            "status": "OBSERVED",
            "window_hours": 24,
            "window_start_utc": "2026-10-29T12:00:00Z",
            "window_end_utc": "2026-10-30T12:00:00Z",
            "unique_open_now_published": 2,
            "published_per_hour_rolling_avg": 0.08,
            "published_route_rows": 3,
            "deduplicated_publications": 1,
            "results": {"FAILED": 0},
            "invalid_count": 0,
            "historical_excluded_count": 0,
        },
    )
    response = bot_service._handle_admin_navigation_action(
        "RESEARCH",
        12345,
        {"chat": {"id": -100999, "type": "supergroup"}, "from": {"id": 12345}},
    )
    assert "Unique signals published: 2" in response["text"], (
        "\n".join(response["text"].splitlines()[-18:])
    )
    assert "Observed rolling average per hour: 0.08" in response["text"]
    assert "Market WIN/LOSS" in response["text"]


def test_publication_evidence_inherits_existing_research_role_boundary(monkeypatch):
    from core import bot_service
    from core.role_constants import ROLE_USER

    monkeypatch.setattr(bot_service, "get_primary_role", lambda _id: ROLE_USER)

    def forbidden():
        raise AssertionError("Unauthorized research page must not inspect publication records")

    monkeypatch.setattr(publication_evidence, "publication_snapshot", forbidden)
    response = bot_service._handle_admin_navigation_action(
        "RESEARCH",
        12345,
        {"chat": {"id": -100999, "type": "supergroup"}, "from": {"id": 12345}},
    )
    assert response["text"] == "Access denied (missing panel permission)."



def test_oversized_interactive_log_fails_closed_instead_of_blocking_bot(tmp_path: Path):
    path = tmp_path / "large_distribution_log.jsonl"
    with path.open("wb") as handle:
        handle.truncate(publication_evidence.MAX_INTERACTIVE_SOURCE_BYTES + 1)
    result = publication_evidence.publication_snapshot(path=str(path), now_ts=NOW)
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN"
    assert result["published_per_hour_rolling_avg"] is None


def test_unhashable_publish_result_degrades_row_not_research_surface(tmp_path: Path):
    path = tmp_path / "malformed_results.jsonl"
    bad = _row("SIG-BAD")
    bad["data"]["publish_result"] = {"unexpected": True}
    _write(path, [bad, _row("SIG-VALID")])
    result = publication_evidence.publication_snapshot(path=str(path), now_ts=NOW)
    assert result["status"] == "OBSERVED"
    assert result["invalid_count"] == 1
    assert result["unique_open_now_published"] == 1
