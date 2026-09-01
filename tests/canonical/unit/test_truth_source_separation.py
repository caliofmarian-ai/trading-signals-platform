from __future__ import annotations

import json
from pathlib import Path

import pytest

from core import analytics_engine as analytics


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _market(trade_id: str, result: str, *, status: str = "FINALIZED") -> dict:
    return {
        "truth_domain": "MARKET_TRUTH",
        "telemetry_status": status,
        "trade_id": trade_id,
        "signal_id": trade_id,
        "result_at_expiry": result,
    }


def _community(signal_id: str, user_id: str, outcome: str) -> dict:
    return {
        "event_type": "user_outcome_record",
        "record_schema_version": "3.0.0",
        "truth_domain": "COMMUNITY_TRUTH",
        "truth_source": "COMMUNITY_SELF_REPORT",
        "signal_id": signal_id,
        "user_id": user_id,
        "outcome": outcome,
    }


def _operational(signal_id: str, outcome: str, ts: int) -> dict:
    return {
        "truth_domain": "OPERATIONAL_TRUTH",
        "truth_source": "ADMIN_RECONCILIATION",
        "signal_id": signal_id,
        "outcome": outcome,
        "outcome_set_ts": ts,
        "reconciliation_status": "RECONCILED",
    }


def test_market_win_rate_uses_only_finalized_objective_truth(tmp_path: Path) -> None:
    path = tmp_path / "trade_temporal_telemetry.jsonl"
    _write_jsonl(
        path,
        [
            _market("m1", "WIN"),
            _market("m2", "WIN"),
            _market("m3", "WIN"),
            _market("m4", "LOSS"),
            _market("m5", "LOSS"),
            _market("m6", "DRAW"),
            _market("m7", "WIN", status="INCOMPLETE_MARKET_EVIDENCE"),
        ],
    )

    result = analytics._load_market_truth(str(path))

    assert result["truth_domain"] == "MARKET_TRUTH"
    assert result["authoritative_for_strategy_performance"] is True
    assert result["wins"] == 3
    assert result["losses"] == 2
    assert result["draws"] == 1
    assert result["excluded_incomplete"] == 1
    assert result["decisive_sample"] == 5
    assert result["market_win_rate_percent"] == pytest.approx(60.0)


def test_community_feedback_is_non_authoritative_and_missed_is_not_loss(tmp_path: Path) -> None:
    path = tmp_path / "outcomes.jsonl"
    _write_jsonl(
        path,
        [
            _community("s1", "u1", "WIN"),
            _community("s2", "u2", "WIN"),
            _community("s3", "u3", "WIN"),
            _community("s4", "u4", "LOSE"),
            _community("s5", "u5", "LOSE"),
            _community("s6", "u6", "MISSED"),
        ],
    )

    result = analytics._load_community_truth(str(path))

    assert result["truth_domain"] == "COMMUNITY_TRUTH"
    assert result["authoritative_for_strategy_performance"] is False
    assert result["wins"] == 3
    assert result["loses"] == 2
    assert result["missed"] == 1
    assert result["decisive_sample"] == 5
    assert result["community_win_rate_percent"] == pytest.approx(60.0)
    assert result["community_missed_rate_percent"] == pytest.approx(100 / 6)


def test_mixed_and_unknown_truth_cannot_enter_community_metric(tmp_path: Path) -> None:
    path = tmp_path / "outcomes.jsonl"
    community = _community("s1", "u1", "WIN")
    _write_jsonl(
        path,
        [
            community,
            community,
            {
                "truth_domain": "OPERATIONAL_TRUTH",
                "truth_source": "ADMIN_RECONCILIATION",
                "signal_id": "s2",
                "user_id": "admin",
                "outcome": "WIN",
            },
            {
                "truth_domain": "SOMETHING_UNKNOWN",
                "signal_id": "s3",
                "user_id": "x",
                "outcome": "WIN",
            },
        ],
    )

    result = analytics._load_community_truth(str(path))

    assert result["wins"] == 1
    assert result["duplicate_count"] == 1
    assert result["excluded_other_truth"] == 2


def test_legacy_unlabeled_community_rows_are_migrated_only_as_community(tmp_path: Path) -> None:
    path = tmp_path / "outcomes.jsonl"
    _write_jsonl(
        path,
        [
            {"event_type": "user_outcome_record", "signal_id": "s1", "user_id": "u1", "outcome": "WIN"},
            {"signal_id": "s2", "user_id": "u2", "outcome": "LOSE"},
        ],
    )

    result = analytics._load_community_truth(str(path))

    assert result["legacy_inferred_count"] == 2
    assert result["wins"] == 1
    assert result["loses"] == 1
    assert "COMMUNITY_TRUTH" in result["migration_policy"]


def test_operational_win_rate_excludes_missed_and_keeps_latest_reconciliation(tmp_path: Path) -> None:
    path = tmp_path / "operational_outcomes.jsonl"
    _write_jsonl(
        path,
        [
            _operational("o1", "LOSE", 1),
            _operational("o1", "WIN", 2),
            _operational("o2", "WIN", 1),
            _operational("o3", "WIN", 1),
            _operational("o4", "LOSE", 1),
            _operational("o5", "LOSE", 1),
            _operational("o6", "MISSED", 1),
        ],
    )

    result = analytics._load_operational_truth(str(path))

    assert result["truth_domain"] == "OPERATIONAL_TRUTH"
    assert result["wins"] == 3
    assert result["loses"] == 2
    assert result["missed"] == 1
    assert result["operational_win_rate_percent"] == pytest.approx(60.0)
    assert result["execution_rate_percent"] == pytest.approx(100 * 5 / 6)
    assert result["missed_rate_percent"] == pytest.approx(100 / 6)


def test_small_samples_never_present_rate_as_stable_evidence(tmp_path: Path) -> None:
    market_path = tmp_path / "market.jsonl"
    community_path = tmp_path / "community.jsonl"
    _write_jsonl(market_path, [_market("m1", "WIN"), _market("m2", "LOSS")])
    _write_jsonl(community_path, [_community("s1", "u1", "WIN"), _community("s2", "u2", "LOSE")])

    market = analytics._load_market_truth(str(market_path))
    community = analytics._load_community_truth(str(community_path))

    assert market["insufficient_sample"] is True
    assert market["market_win_rate_percent"] is None
    assert community["insufficient_sample"] is True
    assert community["community_win_rate_percent"] is None


def test_recompute_has_no_unlabeled_strategy_win_rate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    market_path = tmp_path / "market.jsonl"
    community_path = tmp_path / "community.jsonl"
    operational_path = tmp_path / "operational.jsonl"
    dist_path = tmp_path / "distribution.jsonl"
    aggregate_path = tmp_path / "analytics" / "aggregates.json"

    _write_jsonl(
        market_path,
        [_market("m1", "WIN"), _market("m2", "WIN"), _market("m3", "WIN"), _market("m4", "LOSS"), _market("m5", "LOSS")],
    )
    _write_jsonl(
        community_path,
        [_community("s1", "u1", "LOSE"), _community("s2", "u2", "LOSE"), _community("s3", "u3", "LOSE"), _community("s4", "u4", "WIN"), _community("s5", "u5", "WIN")],
    )
    _write_jsonl(operational_path, [])
    _write_jsonl(dist_path, [])

    monkeypatch.setattr(analytics, "_MARKET_TELEMETRY_LOG", str(market_path))
    monkeypatch.setattr(analytics, "_OUTCOMES_LOG", str(community_path))
    monkeypatch.setattr(analytics, "_OPERATIONAL_OUTCOMES_LOG", str(operational_path))
    monkeypatch.setattr(analytics, "_DIST_LOG", str(dist_path))
    monkeypatch.setattr(analytics, "AGGREGATES_PATH", str(aggregate_path))

    result = analytics.recompute(123456)

    assert result["truth_separation_enforced"] is True
    assert result["strategy_performance_truth_domain"] == "MARKET_TRUTH"
    assert "win_rate" not in result
    assert "wins" not in result
    assert "loses" not in result
    assert result["market_truth"]["market_win_rate_percent"] == pytest.approx(60.0)
    assert result["community_truth"]["community_win_rate_percent"] == pytest.approx(40.0)
    assert result["operational_truth"]["no_data"] is True


def test_legacy_private_outcome_helper_labels_its_win_rate_as_community(tmp_path: Path) -> None:
    path = tmp_path / "outcomes.jsonl"
    _write_jsonl(
        path,
        [_community("s1", "u1", "WIN"), _community("s2", "u2", "LOSE")],
    )
    result = analytics._load_outcomes(str(path))
    assert result["legacy_compatibility_only"] is True
    assert result["win_rate_truth_domain"] == "COMMUNITY_TRUTH"
    assert result["win_rate"] is None
