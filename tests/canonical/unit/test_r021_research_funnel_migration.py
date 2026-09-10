from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


def _write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def _reload_research(monkeypatch, path: Path):
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(path))
    sys.modules.pop("intelligence.research_engine", None)
    return importlib.import_module("intelligence.research_engine")


def _execution(*, phase: str, attempt_id: str = "A-1", stage: str = "OPEN_NOW", available: bool = True) -> dict:
    return {
        "event_type": "signal_execution_result",
        "schema_version": "3.0.0",
        "event_id": f"E-{phase}-{attempt_id}",
        "execution_attempt_id": attempt_id,
        "signal_id": "SIG-1",
        "stage": stage,
        "data": {
            "execution_phase": phase,
            "signal_event_available": available,
        },
    }


def _legacy(*, event_id: str = "L-1", signal_id: str = "OLD-1", stage: str = "PRE") -> dict:
    return {
        "event_type": "signal_event",
        "schema_version": "2.0.0",
        "event_id": event_id,
        "signal_id": signal_id,
        "stage": stage,
        "data": {},
    }


def test_v3_funnel_counts_only_pre_distribution_candidate(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "engine.jsonl"
    _write(
        path,
        [
            _execution(phase="PRE_DISTRIBUTION", attempt_id="A-1"),
            _execution(phase="POST_DISTRIBUTION", attempt_id="A-1"),
        ],
    )
    research = _reload_research(monkeypatch, path)

    funnel = research.compute_signal_funnel()

    assert funnel["OPEN_NOW"] == 1
    assert funnel["total_signal_events"] == 1
    assert funnel["primary_v3_count"] == 1
    assert funnel["legacy_fallback_count"] == 0
    assert funnel["legacy_duplicate_suppressed_count"] == 0


def test_v3_funnel_deduplicates_execution_attempt_identity(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "engine.jsonl"
    event = _execution(phase="PRE_DISTRIBUTION", attempt_id="A-1", stage="CONFIRM")
    duplicate = dict(event)
    duplicate["event_id"] = "E-duplicate"
    _write(path, [event, duplicate])
    research = _reload_research(monkeypatch, path)

    funnel = research.compute_signal_funnel()

    assert funnel["CONFIRM"] == 1
    assert funnel["primary_v3_count"] == 1


def test_matching_legacy_candidate_is_suppressed_when_primary_v3_exists(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "engine.jsonl"
    primary = _execution(phase="PRE_DISTRIBUTION", attempt_id="A-1", stage="OPEN_NOW")
    legacy = _legacy(event_id="L-1", signal_id="SIG-1", stage="OPEN_NOW")
    _write(path, [legacy, primary])
    research = _reload_research(monkeypatch, path)

    funnel = research.compute_signal_funnel()

    assert funnel["OPEN_NOW"] == 1
    assert funnel["total_signal_events"] == 1
    assert funnel["primary_v3_count"] == 1
    assert funnel["legacy_fallback_count"] == 0
    assert funnel["legacy_duplicate_suppressed_count"] == 1


def test_legacy_signal_event_remains_bounded_historical_fallback(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "engine.jsonl"
    event = _legacy(event_id="L-1", stage="PRE")
    _write(path, [event, event])
    research = _reload_research(monkeypatch, path)

    funnel = research.compute_signal_funnel()

    assert funnel["PRE"] == 1
    assert funnel["primary_v3_count"] == 0
    assert funnel["legacy_fallback_count"] == 1
    assert funnel["legacy_duplicate_suppressed_count"] == 0


def test_non_matching_legacy_candidate_remains_fallback(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "engine.jsonl"
    primary = _execution(phase="PRE_DISTRIBUTION", attempt_id="A-1", stage="OPEN_NOW")
    legacy = _legacy(event_id="L-1", signal_id="OLD-1", stage="PRE")
    _write(path, [primary, legacy])
    research = _reload_research(monkeypatch, path)

    funnel = research.compute_signal_funnel()

    assert funnel["OPEN_NOW"] == 1
    assert funnel["PRE"] == 1
    assert funnel["total_signal_events"] == 2
    assert funnel["primary_v3_count"] == 1
    assert funnel["legacy_fallback_count"] == 1
    assert funnel["legacy_duplicate_suppressed_count"] == 0


def test_non_v3_signal_execution_result_is_not_silently_reinterpreted(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "engine.jsonl"
    record = _execution(phase="PRE_DISTRIBUTION")
    record["schema_version"] = "2.0.0"
    _write(path, [record])
    research = _reload_research(monkeypatch, path)

    funnel = research.compute_signal_funnel()

    assert funnel["total_signal_events"] == 0
    assert funnel["primary_v3_count"] == 0
    assert funnel["historical_named_execution_count"] == 1


def test_v3_record_without_candidate_is_not_counted(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "engine.jsonl"
    _write(path, [_execution(phase="PRE_DISTRIBUTION", available=False)])
    research = _reload_research(monkeypatch, path)

    funnel = research.compute_signal_funnel()

    assert funnel["total_signal_events"] == 0
    assert funnel["primary_v3_count"] == 0
