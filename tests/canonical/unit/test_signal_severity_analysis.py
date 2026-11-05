from __future__ import annotations

import copy
import json

import pytest

from tests.canonical.unit.test_owner_timing_analysis import _audit


def test_score_scale_is_monotone_and_preserves_exact_current_control(canonical_runtime_root):
    from scripts.analyze_signal_severity import score_thresholds
    params = _audit(canonical_runtime_root)["owner_timing_calibration_evidence"]["params"]
    before = copy.deepcopy(params)
    rows = [score_thresholds(params, level) for level in range(21)]
    assert rows[0] == {"PRE": 0, "CONFIRM": 5, "OPEN": 10}
    assert rows[14] == params["score_thresholds"]
    assert rows[20] == {"PRE": 90, "CONFIRM": 95, "OPEN": 100}
    for stage in ("PRE", "CONFIRM", "OPEN"):
        assert all(a[stage] < b[stage] for a, b in zip(rows, rows[1:]))
    for row in rows:
        assert row["CONFIRM"] - row["PRE"] == pytest.approx(5)
        assert row["OPEN"] - row["CONFIRM"] == pytest.approx(5)
    assert params == before
    for bad in (-1, 21, True, 1.5, "0"):
        with pytest.raises(ValueError):
            score_thresholds(params, bad)


def test_all_levels_replay_real_pipeline_without_future_data_or_mutation(canonical_runtime_root, monkeypatch):
    from scripts import analyze_owner_signal_timing as replay
    from scripts.analyze_signal_severity import analyze_ladder
    audit = _audit(canonical_runtime_root)
    before = copy.deepcopy(audit)
    files_before = {str(p): p.read_bytes() for p in canonical_runtime_root.rglob("*") if p.is_file()}
    original = replay.decide
    seen = {}

    def checked(m1, m5, params, **kwargs):
        cutoff = kwargs["observation_ts"]
        assert all(row["ts"] + 60 <= cutoff for row in m1)
        assert all(row["ts"] + 300 <= cutoff for row in m5)
        unchanged = copy.deepcopy(params)
        unchanged["score_thresholds"] = before["owner_timing_calibration_evidence"]["params"]["score_thresholds"]
        assert unchanged == before["owner_timing_calibration_evidence"]["params"]
        seen.setdefault(tuple(params["score_thresholds"].values()), []).append(cutoff)
        return original(m1, m5, params, **kwargs)

    monkeypatch.setattr(replay, "decide", checked)
    result = analyze_ladder(audit)
    assert len(result["levels"]) == len(seen) == 21
    assert all(len(cutoffs) == 40 and cutoffs == sorted(cutoffs) for cutoffs in seen.values())
    assert all(row["evaluations"] == 40 and not row["evaluation_errors"] for row in result["levels"])
    # Flat fixture lacks valid corridor/time: permissive arithmetic must not
    # manufacture executable opportunities at any severity.
    assert all(row["fsm_accepted_model_ready_open_opportunities"] == 0 for row in result["levels"])
    assert all(row["hard_blockers"] == result["levels"][14]["hard_blockers"] for row in result["levels"])
    assert result["selected_level"] is None and result["automatic_selection_allowed"] is False
    assert result["telegram_signals_published"] == result["broker_trades_executed"] == 0
    assert result["execution_calibration_proven"] is False
    assert audit == before
    assert files_before == {str(p): p.read_bytes() for p in canonical_runtime_root.rglob("*") if p.is_file()}
    json.dumps(result, allow_nan=False)
