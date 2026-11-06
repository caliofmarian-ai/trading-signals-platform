import importlib
import json

import pytest


def test_measured_loop_spacing_is_separate_from_sleep_and_work(canonical_runtime_root):
    module=importlib.import_module("runtime.observation_timing")
    times=iter([0,.1,1.1,1.2,3.5,3.8])
    metrics=module.LoopTimingEvidence(1,monotonic=lambda:next(times))
    metrics.begin();first=metrics.finish(now_ts=1000,provider="FINNHUB")
    assert first["loop_interval_seconds"]["sample"]==0
    metrics.begin();assert metrics.finish(now_ts=1001,provider="FINNHUB") is None
    metrics.begin();report=metrics.finish(now_ts=1061,provider="FINNHUB")
    assert report["configured_sleep_seconds"]==1
    assert report["loop_interval_seconds"]["sample"]==2
    assert report["loop_interval_seconds"]["max"]==pytest.approx(2.4)
    assert report["loop_intervals_gt_2s"]==1
    assert report["loop_work_seconds"]["max"]==pytest.approx(.3)


def test_loop_timing_is_bounded_and_invalid_provider_is_not_echoed(canonical_runtime_root):
    module=importlib.import_module("runtime.observation_timing")
    ticks=iter(range(2000))
    metrics=module.LoopTimingEvidence(1,monotonic=lambda:next(ticks)/2)
    for index in range(300):
        metrics.begin();report=metrics.finish(now_ts=1000+index*60,provider="private-provider-text")
    assert report["loop_interval_seconds"]["sample"]==128
    assert report["loop_work_seconds"]["sample"]==128
    assert report["provider"]=="UNAVAILABLE"
    assert "private-provider-text" not in json.dumps(report)


@pytest.mark.parametrize("failure",["init","begin","finish"])
def test_optional_timing_failure_cannot_stop_worker(canonical_runtime_root,monkeypatch,failure):
    worker=importlib.import_module("runtime.telemetry_market_worker")
    monkeypatch.setattr(worker,"run_telemetry_cycle",lambda **kwargs:{})
    monkeypatch.setattr(worker.trade_temporal_telemetry,"recover_after_restart",lambda _: {})
    monkeypatch.setattr(worker.shadow_research,"enabled",lambda:False)
    monkeypatch.setattr(worker.gate_research,"enabled",lambda:False)
    monkeypatch.setattr(worker.timebox_research,"enabled",lambda:False)
    monkeypatch.setattr(worker.market_client,"configured_provider",lambda:"FINNHUB")
    class BrokenTiming:
        def __init__(self,*a,**k):
            if failure=="init":raise RuntimeError("fixture-only")
        def begin(self):
            if failure=="begin":raise RuntimeError("fixture-only")
        def finish(self,**kwargs):
            if failure=="finish":raise RuntimeError("fixture-only")
            return None
    monkeypatch.setattr(worker,"LoopTimingEvidence",BrokenTiming)
    def stop(seconds):
        assert seconds==1
        raise SystemExit
    with pytest.raises(SystemExit):
        worker.telemetry_market_loop(clock=lambda:1000,sleep=stop)
