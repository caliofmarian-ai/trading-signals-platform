from __future__ import annotations

import json
from pathlib import Path

from core import analytics_engine


def _write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def _v3_result(*, result: str = "PUBLISHED", message_id: int = 42) -> dict:
    return {
        "event_type": "route_publish_result",
        "schema_version": "3.0.0",
        "signal_id": "SIG-1",
        "route": "ELITE",
        "stage": "OPEN_NOW",
        "destination_id": 1004,
        "data": {
            "publish_result": result,
            "transport": {"ok": result == "PUBLISHED", "message_id": message_id, "error": None},
        },
    }


def _legacy_result(*, result: str = "PUBLISHED", message_id: int = 42) -> dict:
    return {
        "event_type": "tier_publish",
        "schema_version": "3.0.0",
        "signal_id": "SIG-1",
        "route": "ELITE",
        "tier": "ELITE",
        "stage": "OPEN_NOW",
        "destination_id": 1004,
        "message_id": message_id,
        "data": {
            "publish_result": result,
            "transport": {"ok": result == "PUBLISHED", "message_id": message_id, "error": None},
        },
    }


def test_v3_primary_and_matching_legacy_adapter_count_once(tmp_path: Path) -> None:
    path = tmp_path / "distribution.jsonl"
    _write(path, [_v3_result(), _legacy_result()])

    metrics = analytics_engine._load_distribution_metrics(str(path))

    assert metrics["PUBLISHED"] == 1
    assert metrics["total_distribution_events"] == 1
    assert metrics["primary_v3_count"] == 1
    assert metrics["legacy_fallback_count"] == 0
    assert metrics["legacy_duplicate_suppressed_count"] == 1


def test_legacy_only_history_remains_countable_as_fallback(tmp_path: Path) -> None:
    path = tmp_path / "distribution.jsonl"
    _write(path, [_legacy_result(result="FAILED", message_id=0)])

    metrics = analytics_engine._load_distribution_metrics(str(path))

    assert metrics["FAILED"] == 1
    assert metrics["total_distribution_events"] == 1
    assert metrics["primary_v3_count"] == 0
    assert metrics["legacy_fallback_count"] == 1
    assert metrics["legacy_duplicate_suppressed_count"] == 0


def test_v2_named_route_result_is_historical_not_relabelled_primary(tmp_path: Path) -> None:
    path = tmp_path / "distribution.jsonl"
    record = _v3_result()
    record["schema_version"] = "2.0.0"
    _write(path, [record])

    metrics = analytics_engine._load_distribution_metrics(str(path))

    assert metrics["PUBLISHED"] == 1
    assert metrics["total_distribution_events"] == 1
    assert metrics["primary_v3_count"] == 0
    assert metrics["historical_named_route_result_count"] == 1
    assert metrics["legacy_fallback_count"] == 1


def test_non_matching_legacy_evidence_is_not_guessed_as_duplicate(tmp_path: Path) -> None:
    path = tmp_path / "distribution.jsonl"
    legacy = _legacy_result(message_id=99)
    _write(path, [_v3_result(message_id=42), legacy])

    metrics = analytics_engine._load_distribution_metrics(str(path))

    assert metrics["PUBLISHED"] == 2
    assert metrics["total_distribution_events"] == 2
    assert metrics["primary_v3_count"] == 1
    assert metrics["legacy_fallback_count"] == 1
    assert metrics["legacy_duplicate_suppressed_count"] == 0
