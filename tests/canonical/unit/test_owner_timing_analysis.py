from __future__ import annotations

import copy
import importlib
import json

import pytest


def _audit(root):
    t = 1793872800
    candles = {}
    for frame, seconds, count in (("M1", 60, 60), ("M5", 300, 220)):
        candles[frame] = [{"ts": t-i*seconds, "open": 1.1, "high": 1.1002,
                          "low": 1.0998, "close": 1.1, "provider": "FINNHUB",
                          "symbol": "EUR/USD", "timeframe": frame, "complete": True}
                         for i in range(count)]
    return {"owner_timing_calibration_evidence": {
        "status": "PERSONAL_RESEARCH_SNAPSHOT", "provider": "FINNHUB",
        "observed_at_ts": t+60, "buffer_mode": "MEDIUM", "candles": candles,
        "params": json.loads((root / "config" / "algo_params.json").read_text()),
    }}


def test_replay_never_uses_future_m5_or_writes_runtime(canonical_runtime_root, monkeypatch):
    module = importlib.import_module("scripts.analyze_owner_signal_timing")
    audit = _audit(canonical_runtime_root)
    before = copy.deepcopy(audit)
    files_before = sorted(str(p.relative_to(canonical_runtime_root)) for p in canonical_runtime_root.rglob("*") if p.is_file())
    original = module.decide
    cutoffs = []

    def checked(m1, m5, params, **kwargs):
        cutoff = kwargs["observation_ts"]
        assert all(row["ts"]+300 <= cutoff for row in m5)
        assert all(row["ts"]+60 <= cutoff for row in m1)
        cutoffs.append(cutoff)
        return original(m1, m5, params, **kwargs)

    monkeypatch.setattr(module, "decide", checked)
    report = module.analyze(audit)
    assert report["evaluation_errors"] == {}
    assert report["evaluations"] == len(cutoffs) == 40
    assert cutoffs == sorted(cutoffs)
    assert report["execution_calibration_proven"] is False
    assert report["production_parameters_changed"] is False
    assert report["telegram_signals_published"] == report["broker_trades_executed"] == 0
    assert audit == before
    assert files_before == sorted(str(p.relative_to(canonical_runtime_root)) for p in canonical_runtime_root.rglob("*") if p.is_file())


@pytest.mark.parametrize("change", ["wrong_provider", "missing_mode", "oversized", "wrong_candle_provider"])
def test_replay_rejects_unproven_scope(canonical_runtime_root, change):
    module = importlib.import_module("scripts.analyze_owner_signal_timing")
    audit = _audit(canonical_runtime_root)
    source = audit["owner_timing_calibration_evidence"]
    if change == "wrong_provider":
        source["provider"] = "OTHER"
    elif change == "missing_mode":
        del source["buffer_mode"]
    elif change == "oversized":
        source["candles"]["M1"] *= 10
    elif change == "wrong_candle_provider":
        source["candles"]["M1"][0]["provider"] = "OTHER"
    with pytest.raises(ValueError):
        module.analyze(audit)
