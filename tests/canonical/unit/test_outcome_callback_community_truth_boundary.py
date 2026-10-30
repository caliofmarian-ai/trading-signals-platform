"""Issue #97 P0-03: community callback statistics cannot become strategy WR."""

from __future__ import annotations

import importlib
import json

import pytest


def _row(signal: str, member: str, result: str, **extra):
    return {
        "event_type": "user_outcome_record",
        "truth_source": "COMMUNITY_SELF_REPORT",
        "signal_id": signal,
        "member_ref": member,
        "outcome": result,
        **extra,
    }


def _read_stats(monkeypatch, tmp_path, records, signal_id="sig-1"):
    path = tmp_path / "outcomes.jsonl"
    path.write_text(
        "".join(json.dumps(item) + "\n" for item in records),
        encoding="utf-8",
    )
    outcomes = importlib.import_module("core.outcome_service")
    monkeypatch.setattr(outcomes, "OUTCOMES_JSONL", str(path))
    return outcomes.compute_signal_stats(signal_id)


def test_missed_never_counts_as_directional_loss_and_market_rate_is_unavailable(
    tmp_path, monkeypatch
):
    records = (
        [_row("sig-1", f"win-{i}", "WIN") for i in range(3)]
        + [_row("sig-1", f"loss-{i}", "LOSE") for i in range(2)]
        + [_row("sig-1", f"miss-{i}", "MISSED") for i in range(10)]
    )
    result = _read_stats(monkeypatch, tmp_path, records)
    assert result["win_count"] == 3
    assert result["lose_count"] == 2
    assert result["missed_count"] == 10
    assert result["total"] == 15
    assert result["decisive_sample"] == 5
    assert result["self_reported_win_rate_percent"] == pytest.approx(60.0)
    assert result["community_missed_rate_percent"] == pytest.approx(66.67)
    assert result["win_rate_percent"] is None
    assert result["truth_domain"] == "COMMUNITY_TRUTH"
    assert result["truth_source"] == "COMMUNITY_SELF_REPORT"
    assert result["authoritative_for_strategy_performance"] is False


def test_small_self_report_samples_have_no_rate(tmp_path, monkeypatch):
    records = [
        _row("sig-1", "member-A", "WIN"),
        _row("sig-1", "member-B", "MISSED"),
        _row("sig-1", "member-C", "MISSED"),
    ]
    result = _read_stats(monkeypatch, tmp_path, records)
    assert result["no_data"] is False
    assert result["decisive_sample"] == 1
    assert result["insufficient_sample"] is True
    assert result["self_reported_win_rate_percent"] is None
    assert result["win_rate_percent"] is None
    assert result["community_missed_rate_percent"] == pytest.approx(66.67)


def test_no_file_means_unknown_rate_not_false_zero(tmp_path, monkeypatch):
    path = tmp_path / "absent.jsonl"
    module = importlib.import_module("core.outcome_service")
    monkeypatch.setattr(module, "OUTCOMES_JSONL", str(path))
    result = module.compute_signal_stats("sig-1")
    assert result["no_data"] is True
    assert result["total"] == 0
    assert result["decisive_sample"] == 0
    assert result["self_reported_win_rate_percent"] is None
    assert result["community_missed_rate_percent"] is None
    assert result["win_rate_percent"] is None


def test_market_and_operational_labels_never_enter_community_stats(tmp_path, monkeypatch):
    records = (
        [_row("sig-1", f"c{i}", "LOSE") for i in range(5)]
        + [
            {
                "event_type": "market_finalized",
                "truth_domain": "MARKET_TRUTH",
                "signal_id": "sig-1",
                "member_ref": "market",
                "outcome": "WIN",
            },
            {
                "event_type": "user_outcome_record",
                "truth_domain": "OPERATIONAL_TRUTH",
                "truth_source": "ADMIN_RECONCILIATION",
                "signal_id": "sig-1",
                "member_ref": "admin",
                "outcome": "WIN",
            },
        ]
    )
    result = _read_stats(monkeypatch, tmp_path, records)
    assert result["excluded_other_truth"] == 2
    assert result["win_count"] == 0
    assert result["lose_count"] == 5
    assert result["self_reported_win_rate_percent"] == 0.0


def test_first_community_member_vote_wins_and_duplicate_does_not_inflate_sample(
    tmp_path, monkeypatch
):
    records = (
        [_row("sig-1", "member-0", "WIN"), _row("sig-1", "member-0", "LOSE")]
        + [_row("sig-1", f"member-{i}", "WIN") for i in range(1, 5)]
    )
    result = _read_stats(monkeypatch, tmp_path, records)
    assert result["duplicate_count"] == 1
    assert result["win_count"] == 5
    assert result["lose_count"] == 0
    assert result["decisive_sample"] == 5
    assert result["self_reported_win_rate_percent"] == 100.0


def test_legacy_unlabeled_dedicated_community_record_not_mixed_with_other_signal(
    tmp_path, monkeypatch
):
    rows = [
        {"signal_id": "sig-1", "user_id": "legacy-a", "outcome": "WIN"},
        {"signal_id": "other", "user_id": "other-user", "outcome": "LOSE"},
        {"event_type": "user_outcome_record", "truth_source": "COMMUNITY_SELF_REPORT",
         "signal_id": "sig-1", "user_id": "current", "outcome": "LOSE"},
    ]
    result = _read_stats(monkeypatch, tmp_path, rows)
    assert result["win_count"] == 1
    assert result["lose_count"] == 1
    assert result["total"] == 2
    assert result["insufficient_sample"] is True


def test_malformed_rows_do_not_generate_false_market_truth(tmp_path, monkeypatch):
    rows = [
        _row("sig-1", "good", "WIN"),
        _row("sig-1", "bad", "INVALID"),
        _row("sig-1", "", "WIN"),
        {"signal_id": "sig-1", "event_type": "unexpected", "member_ref": "x", "outcome": "WIN"},
        {"signal_id": "sig-1", "event_type": "user_outcome_record", "member_ref": "y", "outcome": "WIN",
         "truth_domain": ["MARKET_TRUTH", "COMMUNITY_TRUTH"]},
    ]
    result = _read_stats(monkeypatch, tmp_path, rows)
    assert result["win_count"] == 1
    assert result["invalid_count"] == 2
    assert result["excluded_other_truth"] == 2
    assert result["authoritative_for_strategy_performance"] is False
