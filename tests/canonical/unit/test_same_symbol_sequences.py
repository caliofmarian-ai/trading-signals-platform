from intelligence.same_symbol_sequences import summarize


def _row(ts,outcome,*,symbol="EUR/USD",horizon=60,quote_ts=None):
    return {"created_ts":ts,"decision_snapshot":{"decision_policy":"PHYSICAL_ONLY_V3"},
        "entry":{"symbol":symbol,"observed_ts":ts},
        "candidates":[{"outcome":outcome,"horizon_seconds":horizon,
                       "quote":{"observed_ts":quote_ts or ts+horizon}}]}


def test_positions_keep_unknown_and_overlap_separate_without_recovery_assumption():
    report=summarize([_row(1000,"LOSS",horizon=180),_row(1100,"WIN"),_row(1200,"UNKNOWN"),
                      _row(1600,"WIN"),_row(1050,"LOSS",symbol="GBP/USD")])
    assert report["groups"] == 3 and report["overlapping_adjacent_pairs"] == 1
    assert [r["entries"] for r in report["positions"]] == [3,1,1]
    assert report["positions"][0]["observed_win_rate"] == 1/3
    assert report["positions"][2]["observed_win_rate"] is None
    assert report["after_already_observed_loss"]["entries"] == 0
    assert not report["predictive_probability_proven"]


def test_after_loss_requires_that_loss_was_observed_before_next_entry():
    report=summarize([_row(1000,"LOSS",quote_ts=1062),_row(1061,"WIN"),
                      _row(1700,"LOSS",quote_ts=1762),_row(1763,"LOSS")])
    assert report["after_already_observed_loss"]["entries"] == 1
    assert report["after_already_observed_loss"]["observed_win_rate"] == 0


def test_no_historical_snapshot_or_missing_entry_is_fabricated():
    row=_row(1000,"WIN")
    row.pop("decision_snapshot")
    assert summarize([row])["eligible_entries"] == 0
    assert summarize([])["positions"] == []
