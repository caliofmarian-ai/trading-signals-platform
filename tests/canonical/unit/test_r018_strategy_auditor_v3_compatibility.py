from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from core import observability_logger, strategy_v2
from intelligence import report_loader
from tools import strategy_auditor_lib as lib


def _settings(tmp_path: Path) -> Dict[str, Any]:
    reports_dir = tmp_path / "analytics" / "reports"
    return {
        "reports": {
            "enabled": True,
            "output_dir": str(reports_dir),
            "cache_dir": str(tmp_path / "analytics" / "cache"),
            "write_json": True,
            "write_markdown": True,
        },
        "sources": {
            "engine_events": str(tmp_path / "observability" / "engine_events.jsonl"),
            "fsm_events": str(tmp_path / "observability" / "fsm_events.jsonl"),
            "distribution_events": str(tmp_path / "observability" / "distribution_events.jsonl"),
            "error_events": str(tmp_path / "observability" / "error_events.jsonl"),
            "outcomes": str(tmp_path / "outcomes" / "outcomes.jsonl"),
        },
        "heatmap": {
            "enabled": True,
            "score_buckets": [[50, 55], [55, 60], [60, 65], [65, 70], [70, 75], [75, 80], [80, 100]],
        },
        "bottleneck_detection": {
            "enabled": True,
            "dominant_reject_share_threshold": 0.6,
        },
        "symbol_health": {
            "enabled": True,
            "healthy_pre_rate_min": 0.15,
            "starved_pre_rate_max": 0.03,
            "blocked_same_reason_share_min": 0.6,
        },
        "report_defaults": {
            "timezone": "UTC",
            "top_n_rejects": 10,
            "top_n_symbols": 10,
        },
    }


def _event_stream(
    *,
    engine: list[Dict[str, Any]] | None = None,
    fsm: list[Dict[str, Any]] | None = None,
    distribution: list[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    return {
        "engine": engine or [],
        "fsm": fsm or [],
        "distribution": distribution or [],
        "errors": [],
        "outcomes": [],
        "invalid_counts": {
            "engine": 0,
            "fsm": 0,
            "distribution": 0,
            "errors": 0,
            "outcomes": 0,
        },
    }


def _v3_event(
    *,
    event_id: str = "evt-1",
    decision_kind: str = "PRE",
    signal_id: str | None = "sig-1",
    setup_correlation_id: str = "cycle-1",
    symbol: str | None = "EUR/USD",
    timeframe: str | None = "M1",
    stage: str | None = "PRE",
    score_total: float | None = 72.0,
    score_object_total: float | None = None,
    strategy: str = "BINARY_STRATEGY_V2",
    strategy_version: str | None = None,
    canonical_spec: str | None = None,
    direction: str = "BUY",
    candle_ts: int = 1725500000,
    hard_blockers: list[str] | None = None,
    reject_reason: str | None = None,
    schema_version: str = "3.0.0",
    trade_physics: Dict[str, Any] | None = None,
    decision_setup_overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    blockers = hard_blockers or []
    strategy_version = strategy_version or strategy_v2.STRATEGY_VERSION
    canonical_spec = canonical_spec or strategy_v2.CANONICAL_SPEC
    reject_payload = {
        "reason": reject_reason or ("; ".join(blockers) if blockers else None),
        "category": "STRATEGIC_GATE" if blockers or reject_reason else None,
        "stage": "PRE_FSM" if blockers or reject_reason else None,
        "hard_blockers": blockers,
        "soft_blockers": [],
    }
    setup = {
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": direction,
        "evaluated_ts": candle_ts,
        "cycle_id": setup_correlation_id,
    }
    if decision_setup_overrides:
        setup.update(decision_setup_overrides)
    object_score_total = score_total if score_object_total is None else score_object_total
    data = {
        "decision_kind": decision_kind,
        "strategic_kind": decision_kind,
        "strategy": strategy,
        "strategy_version": strategy_version,
        "canonical_spec": canonical_spec,
        "score_total": score_total,
        "score_tier": "OPEN" if decision_kind == "OPEN_NOW" else "PREP",
        "direction": direction,
        "candle_ts": candle_ts,
        "signal_id": signal_id,
        "buffer_mode": "MEDIUM",
        "decision_object": {
            "signal_id": signal_id,
            "setup": setup,
            "score": {
                "total": object_score_total,
                "tier": "OPEN" if decision_kind == "OPEN_NOW" else "PREP",
            },
            "reject": reject_payload,
        },
        "trade_physics": trade_physics or {"TPS": 51.0, "readiness_state": "READY"},
    }
    correlation = {
        "setup_correlation_id": setup_correlation_id,
        "signal_id": signal_id,
        "symbol": symbol,
        "timeframe": timeframe,
    }
    if stage is not None:
        correlation["stage"] = stage

    event = observability_logger.build_event(
        "decision_evaluated",
        data,
        source={"module": "signal_engine", "function": "run_once"},
        correlation=correlation,
    )
    event["event_id"] = event_id
    event["schema_version"] = schema_version
    return event


def _legacy_event(
    *,
    decision_kind: str = "PRE",
    event_id: str | None = None,
    signal_id: str | None = "legacy-sig-1",
    symbol: str | None = "GBP/USD",
    timeframe: str | None = "M5",
    score_total: float | None = 61.0,
    reject_reason: str | None = None,
    schema_version: str | None = None,
) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "event_type": "decision",
        "signal_id": signal_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "data": {
            "decision_kind": decision_kind,
            "signal_id": signal_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "score_total": score_total,
        },
    }
    if event_id is not None:
        event["event_id"] = event_id
    if schema_version is not None:
        event["schema_version"] = schema_version
    if reject_reason is not None:
        event["data"]["reject_reason"] = reject_reason
    return event


def _write_jsonl(path: Path, rows: list[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


@pytest.mark.parametrize("decision_kind,expected_key", [
    ("PRE", "pre"),
    ("CONFIRM", "confirm"),
    ("OPEN_NOW", "open_now"),
    ("REJECT", "rejects"),
    ("NO_SIGNAL", "no_signal"),
])
def test_r018_counts_canonical_v3_decision_kinds(tmp_path: Path, decision_kind: str, expected_key: str) -> None:
    event = _v3_event(
        event_id=f"evt-{decision_kind}",
        decision_kind=decision_kind,
        signal_id="sig-open" if decision_kind != "NO_SIGNAL" else None,
        stage=decision_kind if decision_kind in {"PRE", "CONFIRM", "OPEN_NOW"} else None,
        hard_blockers=["TIME_NOT_FEASIBLE"] if decision_kind == "REJECT" else [],
        reject_reason="TIME_NOT_FEASIBLE" if decision_kind == "REJECT" else None,
    )
    report = lib.build_report(_event_stream(engine=[event]), _settings(tmp_path))

    assert report["decisions"] == 1
    assert report[expected_key] == 1
    assert report["decision_kind_counts"][decision_kind] == 1
    assert report["event_compatibility"]["canonical_v3_decision_events_seen"] == 1
    assert report["event_compatibility"]["normalized_by_compatibility_mode"]["CANONICAL_V3"] == 1
    assert report["limitations"] == []


def test_r018_retains_explicit_legacy_compatibility_without_overriding_v3(tmp_path: Path) -> None:
    report = lib.build_report(
        _event_stream(
            engine=[
                _legacy_event(decision_kind="PRE", event_id="shared-id", signal_id="sig-1", symbol="GBP/USD"),
                _v3_event(event_id="shared-id", decision_kind="OPEN_NOW", signal_id="sig-1", symbol="EUR/USD", stage="OPEN_NOW"),
            ],
            fsm=[{
                "event_type": "fsm_transition",
                "schema_version": "3.0.0",
                "data": {"symbol": "EUR/USD", "prev_state": "NONE", "new_state": "PRE", "trigger": "accepted", "signal_id": "sig-1", "candle_ts": 1},
            }],
        ),
        _settings(tmp_path),
    )

    assert report["decisions"] == 1
    assert report["open_now"] == 1
    assert report["event_compatibility"]["legacy_decision_events_seen"] == 1
    assert report["event_compatibility"]["normalized_by_compatibility_mode"]["CANONICAL_V3"] == 1
    assert report["event_compatibility"]["normalized_by_compatibility_mode"]["LEGACY_DECISION"] == 0
    assert report["event_compatibility"]["duplicate_events_suppressed"] == 1
    assert report["event_compatibility"]["supporting_event_counts"]["fsm_transition"] == 1
    assert any("Legacy `decision` compatibility was used" in item for item in report["limitations"])


def test_r018_mixed_stream_surfaces_unknown_event_types_and_unsupported_schema_versions(tmp_path: Path) -> None:
    report = lib.build_report(
        _event_stream(
            engine=[
                _v3_event(event_id="evt-1", decision_kind="PRE", signal_id="sig-1"),
                _legacy_event(decision_kind="REJECT", event_id="legacy-1", reject_reason="SR_BLOCKED"),
                {"event_type": "future_engine_signal", "schema_version": "3.0.0", "data": {}},
                _v3_event(event_id="evt-unsupported", schema_version="4.0.0", signal_id="sig-unsupported"),
                {
                    "event_type": "signal_execution_result",
                    "schema_version": "3.0.0",
                    "execution_attempt_id": "attempt-1",
                    "symbol": "EUR/USD",
                    "data": {
                        "execution_phase": "PRE_DISTRIBUTION",
                        "execution_outcome": "DEFERRED",
                        "execution_reason": "DISTRIBUTION_NOT_INVOKED",
                        "stage_handoff_ready": True,
                        "trade_execution_ready": False,
                        "signal_event_available": True,
                        "destination_state": "PRE_DISTRIBUTION_UNRESOLVED",
                    },
                },
            ],
        ),
        _settings(tmp_path),
    )

    assert report["decisions"] == 2
    assert report["pre"] == 1
    assert report["rejects"] == 1
    assert report["top_reject_reasons"]["SR_BLOCKED"] == 1
    assert report["event_compatibility"]["unsupported_event_types"]["future_engine_signal"] == 1
    assert report["event_compatibility"]["unsupported_schema_versions"]["decision_evaluated@4.0.0"] == 1
    assert report["event_compatibility"]["supporting_event_counts"]["signal_execution_result"] == 1
    assert "Unsupported decision schema versions were observed and excluded from metrics." in report["limitations"]


def test_r018_recognizes_schema_defined_non_decision_events_without_marking_them_unsupported(tmp_path: Path) -> None:
    report = lib.build_report(
        _event_stream(
            engine=[
                observability_logger.build_event("engine_start", {"message": "started"}, source={"module": "tests", "function": "event"}),
                observability_logger.build_event("engine_stop", {"message": "stopped"}, source={"module": "tests", "function": "event"}),
                observability_logger.build_event(
                    "dependency_degraded",
                    {"dependency": "market-data", "reason": "slow"},
                    source={"module": "tests", "function": "event"},
                ),
                observability_logger.build_event(
                    "duplicate_suppressed",
                    {"scope": "signal", "reason": "dedup"},
                    source={"module": "tests", "function": "event"},
                    correlation={"signal_id": "sig-1", "symbol": "EUR/USD", "timeframe": "M1", "stage": "OPEN_NOW"},
                ),
                observability_logger.build_event(
                    "signal_closed",
                    {"reason": "EXPIRED"},
                    source={"module": "tests", "function": "event"},
                    correlation={"signal_id": "sig-1"},
                ),
            ],
            fsm=[
                observability_logger.build_event(
                    "fsm_transition",
                    {"symbol": "EUR/USD", "prev_state": "NONE", "new_state": "PRE", "trigger": "accepted", "signal_id": "sig-1", "candle_ts": 1725500000},
                    source={"module": "tests", "function": "event"},
                ),
            ],
            distribution=[
                observability_logger.build_event(
                    "tier_publish",
                    {
                        "publish_result": "PUBLISHED",
                        "route_state_before": "ACTIVE",
                        "route_state_after": "ACTIVE",
                        "limit": None,
                        "counter_before": 0,
                        "counter_after": 1,
                        "counted": True,
                        "attempted": True,
                        "destination_kind": "telegram_group",
                        "feedback_enabled": True,
                        "transport": {"ok": True, "message_id": 42, "error": None},
                        "dedup": {"key": "sig-1", "was_duplicate": False, "action": "accepted"},
                    },
                    source={"module": "tests", "function": "event"},
                    correlation={"signal_id": "sig-1", "route": "ELITE", "tier": "ELITE", "stage": "OPEN_NOW"},
                ),
            ],
        ),
        _settings(tmp_path),
    )

    assert report["decisions"] == 0
    assert report["event_compatibility"]["unsupported_event_types"] == {}
    assert report["event_compatibility"]["recognized_non_decision_event_counts"]["engine_start"] == 1
    assert report["event_compatibility"]["recognized_non_decision_event_counts"]["engine_stop"] == 1
    assert report["event_compatibility"]["recognized_non_decision_event_counts"]["dependency_degraded"] == 1
    assert report["event_compatibility"]["recognized_non_decision_event_counts"]["duplicate_suppressed"] == 1
    assert report["event_compatibility"]["recognized_non_decision_event_counts"]["signal_closed"] == 1
    assert report["event_compatibility"]["recognized_non_decision_event_counts"]["fsm_transition"] == 1
    assert report["event_compatibility"]["recognized_non_decision_event_counts"]["tier_publish"] == 1


def test_r018_deduplicates_by_event_id_without_collapsing_distinct_signal_id_reuse(tmp_path: Path) -> None:
    decisions, compatibility = lib.normalize_decision_events(
        _event_stream(
            engine=[
                _v3_event(event_id="evt-1", decision_kind="PRE", signal_id="sig-shared", stage="PRE"),
                _v3_event(event_id="evt-1", decision_kind="PRE", signal_id="sig-shared", stage="PRE"),
                _v3_event(event_id="evt-2", decision_kind="CONFIRM", signal_id="sig-shared", stage="CONFIRM"),
                _legacy_event(event_id=None, decision_kind="OPEN_NOW", signal_id="sig-shared", symbol="EUR/USD"),
            ],
        )
    )

    assert [decision["event_id"] for decision in decisions if decision["event_id"]] == ["evt-1", "evt-2"]
    assert any(decision["compatibility_mode"] == "LEGACY_DECISION" and decision["event_id"] is None for decision in decisions)
    assert len(decisions) == 3
    assert compatibility["duplicate_events_suppressed"] == 1


def test_r018_normalizes_field_authority_and_surfaces_conflicts(tmp_path: Path) -> None:
    decisions, compatibility = lib.normalize_decision_events(
        _event_stream(
            engine=[
                _v3_event(
                    event_id="evt-conflict",
                    decision_kind="REJECT",
                    signal_id="sig-9",
                    symbol="EUR/USD",
                    timeframe="M1",
                    stage="PRE",
                    score_total=70.0,
                    score_object_total=65.0,
                    hard_blockers=["TIME_NOT_FEASIBLE", "STRUCTURE_NOT_VALID"],
                    reject_reason="TIME_NOT_FEASIBLE; STRUCTURE_NOT_VALID",
                    decision_setup_overrides={"symbol": "GBP/USD", "timeframe": "M5"},
                )
            ],
        )
    )

    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["symbol"] == "EUR/USD"
    assert decision["timeframe"] == "M1"
    assert decision["stage"] == "PRE"
    assert decision["score_total"] == 70.0
    assert decision["reject_reasons"] == ["TIME_NOT_FEASIBLE", "STRUCTURE_NOT_VALID"]
    assert "conflicting_symbol" in decision["issues"]
    assert "conflicting_timeframe" in decision["issues"]
    assert "conflicting_score_total" in decision["issues"]
    assert compatibility["conflicting_field_events"] == 1
    assert compatibility["conflicting_fields"]["symbol"] == 1
    assert compatibility["conflicting_fields"]["timeframe"] == 1
    assert compatibility["conflicting_fields"]["score_total"] == 1


def test_r018_surfaces_missing_fields_without_inventing_values(tmp_path: Path) -> None:
    malformed = _v3_event(event_id="evt-missing", decision_kind="PRE")
    malformed.pop("event_id")
    partial = _v3_event(event_id="evt-partial", decision_kind="NO_SIGNAL", signal_id=None, stage=None)
    partial.pop("symbol", None)
    partial.pop("timeframe", None)
    partial["data"]["score_total"] = None
    partial["data"]["decision_object"]["setup"]["symbol"] = None
    partial["data"]["decision_object"]["setup"]["timeframe"] = None
    partial["data"]["decision_object"]["score"]["total"] = None

    report = lib.build_report(_event_stream(engine=[malformed, partial]), _settings(tmp_path))
    decisions = lib.filter_decision_events([malformed, partial])

    assert report["decisions"] == 1
    assert report["avg_score"] is None
    assert report["symbol_activity"] == {}
    assert report["event_compatibility"]["malformed_or_unusable_decision_events"] == 1
    assert report["event_compatibility"]["normalization_warnings"]["missing_event_id"] == 1
    assert report["event_compatibility"]["normalization_warnings"]["missing_score_total"] >= 1
    assert report["event_compatibility"]["normalization_warnings"]["missing_symbol"] >= 1
    assert decisions[0]["score_total"] is None
    assert decisions[0]["symbol"] is None


def test_r018_zero_data_semantics_are_distinct(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    empty_report = lib.build_report(_event_stream(engine=[]), settings)
    non_decision_report = lib.build_report(_event_stream(engine=[{"event_type": "engine_start", "schema_version": "3.0.0", "data": {"message": "ok"}}]), settings)
    unsupported_report = lib.build_report(_event_stream(engine=[_v3_event(event_id="evt-unsupported", schema_version="9.9.9")]), settings)

    assert empty_report["limitations"] == ["No engine events found."]
    assert non_decision_report["limitations"][0] == "Engine events exist, but no recognized canonical decision events were found."
    assert unsupported_report["event_compatibility"]["unsupported_schema_versions"]["decision_evaluated@9.9.9"] == 1
    assert unsupported_report["decisions"] == 0
    assert unsupported_report["limitations"][0] in {
        "Decision-like events were observed, but none were usable after canonical/legacy compatibility checks.",
        "Engine events exist, but recognized decision events used unsupported schema versions.",
    }


def test_r018_markdown_and_json_reports_expose_compatibility_state_without_breaking_consumers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path)
    report = lib.build_report(
        _event_stream(
            engine=[
                _v3_event(event_id="evt-1", decision_kind="OPEN_NOW", signal_id="sig-1", stage="OPEN_NOW"),
                _legacy_event(decision_kind="REJECT", reject_reason="TIME_NOT_FEASIBLE"),
            ]
        ),
        settings,
    )

    lib.write_reports(report, settings)
    output_dir = Path(settings["reports"]["output_dir"])
    json_report = json.loads(next(output_dir.glob("daily_strategy_audit_*.json")).read_text(encoding="utf-8"))
    markdown_report = next(output_dir.glob("daily_strategy_audit_*.md")).read_text(encoding="utf-8")

    monkeypatch.setattr(report_loader, "REPORTS_DIR", str(output_dir))
    summary = report_loader.report_summary(report_loader.load_latest_report())

    assert json_report["event_compatibility"]["canonical_v3_decision_events_seen"] == 1
    assert json_report["event_compatibility"]["legacy_decision_events_seen"] == 1
    assert json_report["open_now"] == 1
    assert json_report["rejects"] == 1
    assert json_report["reject_reason_occurrences"]["TIME_NOT_FEASIBLE"] == 1
    assert "## Event Compatibility" in markdown_report
    assert "## Reject Reason Occurrences" in markdown_report
    assert "normalized_decisions" in markdown_report
    assert "Legacy `decision` compatibility was used" in markdown_report
    assert summary["decisions"] == report["decisions"]
    assert summary["open_now"] == 1
    assert summary["rejects"] == 1


def test_r018_load_all_events_and_build_report_from_files(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    sources = settings["sources"]
    _write_jsonl(Path(sources["engine_events"]), [
        _v3_event(event_id="evt-1", decision_kind="PRE"),
        _legacy_event(decision_kind="REJECT", reject_reason="STRUCTURE_NOT_VALID"),
    ])
    _write_jsonl(Path(sources["fsm_events"]), [{
        "event_type": "fsm_transition",
        "schema_version": "3.0.0",
        "data": {"symbol": "EUR/USD", "prev_state": "NONE", "new_state": "PRE", "trigger": "accepted", "signal_id": "sig-1", "candle_ts": 1725500000},
    }])
    _write_jsonl(Path(sources["distribution_events"]), [])
    _write_jsonl(Path(sources["error_events"]), [])
    _write_jsonl(Path(sources["outcomes"]), [])

    events = lib.load_all_events(settings)
    report = lib.build_report(events, settings)

    assert report["input_sources"]["engine_events"]["valid"] == 2
    assert report["event_compatibility"]["supporting_event_counts"]["fsm_transition"] == 1
    assert report["top_reject_reasons"]["STRUCTURE_NOT_VALID"] == 1


def test_r018_preserves_primary_reject_distribution_and_separate_blocker_occurrences(tmp_path: Path) -> None:
    report = lib.build_report(
        _event_stream(
            engine=[
                _v3_event(
                    event_id="evt-reject",
                    decision_kind="REJECT",
                    signal_id=None,
                    stage=None,
                    hard_blockers=["TIME_NOT_FEASIBLE", "STRUCTURE_NOT_VALID"],
                    reject_reason="TIME_NOT_FEASIBLE; STRUCTURE_NOT_VALID",
                ),
            ],
        ),
        _settings(tmp_path),
    )

    assert report["decisions"] == 1
    assert report["rejects"] == 1
    assert sum(report["top_reject_reasons"].values()) == 1
    assert report["top_reject_reasons"]["TIME_NOT_FEASIBLE"] == 1
    assert sum(report["reject_reason_occurrences"].values()) == 2
    assert report["reject_reason_occurrences"]["TIME_NOT_FEASIBLE"] == 1
    assert report["reject_reason_occurrences"]["STRUCTURE_NOT_VALID"] == 1
    assert report["bottleneck"] == {"reason": "TIME_NOT_FEASIBLE", "share": 1.0}
    assert report["symbol_health"]["EUR/USD"]["dominant_reject"] == "TIME_NOT_FEASIBLE"
    assert report["symbol_health"]["EUR/USD"]["dominant_reject_share"] == 1.0


def test_r018_fixture_matches_current_producer_version_contract(tmp_path: Path) -> None:
    event = _v3_event(event_id="evt-real-shape", decision_kind="OPEN_NOW", signal_id="sig-actual", stage="OPEN_NOW")
    report = lib.build_report(_event_stream(engine=[event]), _settings(tmp_path))

    assert event["schema_version"] == "3.0.0"
    assert event["source"]["module"] == "signal_engine"
    assert event["source"]["function"] == "run_once"
    assert event["data"]["strategy_version"] == strategy_v2.STRATEGY_VERSION
    assert strategy_v2.STRATEGY_VERSION == "2.0.0"
    assert event["data"]["canonical_spec"] == strategy_v2.CANONICAL_SPEC
    assert strategy_v2.CANONICAL_SPEC == "ALGO_SPEC_v3.0.0"
    assert report["event_compatibility"]["canonical_v3_decision_events_seen"] == 1
