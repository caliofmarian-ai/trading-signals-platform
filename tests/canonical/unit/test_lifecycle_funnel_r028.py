from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core import lifecycle_funnel_evidence as funnel


NOW = int(datetime(2026, 10, 30, 9, 0, tzinfo=timezone.utc).timestamp())


def _event(
    kind: str,
    *,
    sid: str | None = "S-A",
    stage: str = "PRE",
    ts: int = NOW - 100,
    version: str = "3.0.0",
    data: dict | None = None,
) -> dict:
    row = {
        "event_type": kind,
        "schema_version": version,
        "ts_epoch_ms": ts * 1000,
        "stage": stage,
        "data": data if data is not None else {},
    }
    if sid is not None:
        row["signal_id"] = sid
    return row


def _decision(stage: str, *, sid: str | None = "S-A", ts: int = NOW - 100) -> dict:
    return _event("decision_evaluated", sid=sid, stage=stage, ts=ts, data={"decision_kind": stage})


def _fsm(stage: str, *, sid: str = "S-A", accepted: str | None = None, ready=True) -> dict:
    return _event(
        "fsm_transition",
        sid=sid,
        stage=stage,
        data={
            "requested_stage": stage,
            "accepted_stage": stage if accepted is None else accepted,
            "stage_handoff_ready": ready,
        },
    )


def _candidate(stage: str, *, sid: str = "S-A", available: bool = True, phase: str = "PRE_DISTRIBUTION") -> dict:
    return _event(
        "signal_execution_result", sid=sid, stage=stage,
        data={"execution_phase": phase, "signal_event_available": available},
    )


def _published(stage: str, *, sid: str = "S-A", result: str = "PUBLISHED") -> dict:
    return _event(
        "route_publish_result", sid=sid, stage=stage, data={"publish_result": result}
    )


def _visible(stage: str, *, sid: str = "S-A", ts: int = NOW - 100) -> dict:
    return _event(
        "signal_stage_visible", sid=sid, stage=stage, ts=ts,
        data={"visibility_result": "PUBLISHED"},
    )


def _write(path: Path, events: list[dict], malformed: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.dumps(x) for x in events]
    if malformed:
        rows.append("{not-json")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return str(path)


def _build(tmp_path: Path, engine: list[dict], dist: list[dict], *, days: int = 1):
    e = _write(tmp_path / "eng.jsonl", engine)
    d = _write(tmp_path / "dist.jsonl", dist)
    return funnel.build_funnel(
        range_days=days, now_ts=NOW, engine_path=e, distribution_path=d
    )


def test_stage_evidence_is_truth_separated_and_distinct_across_routes(tmp_path: Path):
    engine = [
        _decision("PRE"), _decision("PRE"), _decision("CONFIRM"),
        _decision("OPEN_NOW"), _decision("REJECT", sid=None),
        _fsm("PRE"), _fsm("CONFIRM", accepted="PRE"),
        _fsm("OPEN_NOW"), _candidate("PRE"),
        _candidate("CONFIRM"), _candidate("OPEN_NOW"),
        _candidate("OPEN_NOW", phase="POST_DISTRIBUTION"),
    ]
    dist = [
        _published("PRE"), _published("PRE"),
        _published("CONFIRM"), _published("OPEN_NOW"),
        _published("OPEN_NOW", result="FAILED"),
        _visible("PRE", ts=NOW - 100),
        _visible("PRE", ts=NOW - 99),
        _visible("OPEN_NOW", ts=NOW - 65),
    ]
    result = _build(tmp_path, engine, dist)
    assert result["status"] == "OBSERVED"
    assert result["strategy_stage_signals"] == {"PRE": 1, "CONFIRM": 1, "OPEN_NOW": 1}
    assert result["fsm_accepted_signals"] == {"PRE": 1, "CONFIRM": 0, "OPEN_NOW": 1}
    assert result["signal_event_candidates"] == {"PRE": 1, "CONFIRM": 1, "OPEN_NOW": 1}
    assert result["published_route_signals"] == {"PRE": 1, "CONFIRM": 1, "OPEN_NOW": 1}
    assert result["visible_stage_signals"] == {"PRE": 1, "CONFIRM": 0, "OPEN_NOW": 1}
    assert result["decision_kind_rows"]["REJECT"] == 1
    assert result["pre_to_open_visible_matched_pairs"] == 1
    assert result["pre_to_open_lead_median_seconds"] == 35
    assert result["pre_to_open_pairs_at_least_30_seconds"] == 1
    assert result["open_candidate_published_overlap"] == 1
    assert result["open_published_visible_overlap"] == 1
    assert result["conversion_rate_percent"] is None
    assert result["market_win_rate_percent"] is None


def test_no_source_files_remains_unknown_not_zero(tmp_path: Path):
    result = funnel.build_funnel(
        now_ts=NOW,
        engine_path=str(tmp_path / "absent_engine"),
        distribution_path=str(tmp_path / "absent_dist"),
    )
    assert result["status"] == "UNKNOWN"
    assert result["sources"]["engine"]["reason"] == "SOURCE_FILE_NOT_FOUND"
    assert result["signal_event_candidates"]["OPEN_NOW"] is None
    assert result["published_route_signals"]["OPEN_NOW"] is None
    assert result["pre_to_open_visible_matched_pairs"] is None
    assert "UNKNOWN" in funnel.render_funnel_summary(result)


def test_present_engine_missing_distribution_is_partial(tmp_path: Path):
    engine = _write(tmp_path / "engine", [_decision("PRE"), _candidate("PRE")])
    result = funnel.build_funnel(
        now_ts=NOW, engine_path=engine,
        distribution_path=str(tmp_path / "missing_dist")
    )
    assert result["status"] == "PARTIAL"
    assert result["strategy_stage_signals"]["PRE"] == 1
    assert result["published_route_signals"]["PRE"] is None
    assert result["pre_to_open_visible_matched_pairs"] is None


def test_legacy_only_cannot_become_primary_v3_evidence(tmp_path: Path):
    result = _build(
        tmp_path,
        [_decision("PRE") | {"schema_version": "2.0.0"},
         _event("signal_event", version="2.0.0")],
        [_published("OPEN_NOW") | {"schema_version": "2.0.0"},
         _event("tier_publish", version="3.0.0")],
    )
    assert result["status"] == "UNKNOWN"
    assert result["sources"]["engine"]["historical_excluded_rows"] == 1
    assert result["sources"]["distribution"]["historical_excluded_rows"] == 1
    assert result["published_route_signals"]["OPEN_NOW"] is None


def test_bad_json_and_invalid_timestamp_excluded_but_valid_evidence_survives(tmp_path: Path):
    invalid = _decision("PRE")
    invalid["ts_epoch_ms"] = True
    engine = _write(tmp_path / "engine", [invalid, _decision("OPEN_NOW")], malformed=True)
    dist = _write(tmp_path / "dist", [_published("OPEN_NOW")])
    result = funnel.build_funnel(now_ts=NOW, engine_path=engine, distribution_path=dist)
    assert result["status"] == "OBSERVED"
    assert result["sources"]["engine"]["invalid_rows"] == 2
    assert result["strategy_stage_signals"] == {"PRE": 0, "CONFIRM": 0, "OPEN_NOW": 1}


def test_mismatched_fsm_or_false_ready_never_counts_as_accepted(tmp_path: Path):
    result = _build(
        tmp_path,
        [_fsm("OPEN_NOW", accepted="PRE"), _fsm("CONFIRM", ready=False)],
        [_published("OPEN_NOW", result="FAILED")],
    )
    assert result["fsm_accepted_signals"] == {"PRE": 0, "CONFIRM": 0, "OPEN_NOW": 0}
    assert result["published_route_signals"] == {"PRE": 0, "CONFIRM": 0, "OPEN_NOW": 0}
    assert result["visible_stage_signals"]["OPEN_NOW"] is None


def test_pre_after_open_not_misclassified_as_positive_lead(tmp_path: Path):
    result = _build(
        tmp_path, [_decision("PRE")],
        [_visible("OPEN_NOW", ts=NOW - 100), _visible("PRE", ts=NOW - 30)],
    )
    assert result["pre_to_open_visible_matched_pairs"] == 0
    assert result["pre_to_open_lead_median_seconds"] is None
    assert result["pre_to_open_pairs_at_least_30_seconds"] is None


def test_only_visible_published_is_not_synthetic_route_published(tmp_path: Path):
    result = _build(tmp_path, [_candidate("OPEN_NOW")], [_visible("OPEN_NOW")])
    assert result["visible_stage_signals"]["OPEN_NOW"] == 1
    assert result["published_route_signals"]["OPEN_NOW"] is None
    assert result["open_candidate_published_overlap"] is None


def test_window_is_utc_bounded_and_no_future_events(tmp_path: Path):
    result = _build(
        tmp_path,
        [_decision("PRE", ts=NOW - 86400), _decision("CONFIRM", ts=NOW),
         _decision("OPEN_NOW", ts=NOW - 86401), _decision("OPEN_NOW", ts=NOW + 1)],
        [_visible("PRE", ts=NOW - 86400), _visible("OPEN_NOW", ts=NOW)],
    )
    assert result["strategy_stage_signals"] == {"PRE": 1, "CONFIRM": 1, "OPEN_NOW": 0}
    assert result["pre_to_open_lead_median_seconds"] == 86400
    assert result["window_start_utc"] == "2026-10-29T09:00:00Z"
    assert result["window_end_utc"] == "2026-10-30T09:00:00Z"


def test_oversized_source_is_not_partially_interpreted(tmp_path: Path):
    huge = tmp_path / "huge.log"
    with huge.open("wb") as fd:
        fd.truncate(funnel.MAX_SOURCE_BYTES + 1)
    dist = _write(tmp_path / "dist.log", [_published("OPEN_NOW")])
    result = funnel.build_funnel(now_ts=NOW, engine_path=str(huge), distribution_path=dist)
    assert result["status"] == "PARTIAL"
    assert result["sources"]["engine"]["reason"] == "SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN"
    assert result["strategy_stage_signals"]["OPEN_NOW"] is None
    assert result["published_route_signals"]["OPEN_NOW"] == 1


def test_out_of_order_visibility_uses_earliest_observation_and_no_raw_ids(tmp_path: Path):
    secret = "subscriber-like-signal-secret"
    engine = [_decision("PRE", sid=secret)]
    dist = [
        _visible("PRE", sid=secret, ts=NOW - 100),
        _visible("PRE", sid=secret, ts=NOW - 170),
        _visible("OPEN_NOW", sid=secret, ts=NOW - 100),
    ]
    result = _build(tmp_path, engine, dist)
    assert result["pre_to_open_lead_median_seconds"] == 70
    text = funnel.render_funnel_summary(result)
    assert secret not in text
    assert "Stage order: PRE / CONFIRM / OPEN_NOW" in text
    assert "market win-rate: UNKNOWN" in text


@pytest.mark.parametrize("days", [0, -1, True, 31, 2.5, "1"])
def test_invalid_windows_fail_closed(days):
    with pytest.raises(ValueError):
        funnel.build_funnel(range_days=days)


@pytest.mark.parametrize("now", [0, -1, True, 7.5, "2026-10-30"])
def test_invalid_time_fails_closed(now):
    with pytest.raises(ValueError):
        funnel.build_funnel(now_ts=now)
