"""Synthetic real-tick path fixtures; never market-performance evidence."""
import importlib


def _row(direction="BUY"):
    evidence = importlib.import_module("intelligence.buffer_expiry_evidence")
    return {
        "direction": direction,
        "entry": {"provider": "FINNHUB", "symbol": "EUR/USD", "price": 1.1,
                  "observed_ts": 1000.25, "source": "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1",
                  "provider_tick_ms": 1_000_250, "received_ts": 1000.3},
        "buffer_snapshot": evidence.snapshot(0.0002, "a" * 64),
        "study_observation": {"horizon_seconds": 120},
    }


def _tick(stamp, price, *, source="LIVE_STREAM_PROVIDER_TICK_BUFFER_V1", received=None):
    return {"provider": "FINNHUB", "symbol": "EUR/USD", "price": price,
            "observed_ts": stamp, "source": source,
            "provider_tick_ms": round(stamp * 1000),
            "received_ts": stamp + .1 if received is None else received}


def test_first_exact_tick_at_buffer_edge_is_frozen_without_interpolation():
    module = importlib.import_module("intelligence.buffer_first_hit_time")
    row = _row()
    observation = module.pending(horizon_seconds=120, captured_ts=999)
    ticks = [_tick(1010.5, 1.1001), _tick(1030.125, 1.1002),
             _tick(1020.25, 1.1003), _tick(1121, 9),  # after the true horizon
             {"observed_ts": 1015, "price": 1.2}]  # not genuine tick evidence
    assert module.settle(observation, row, now_ts=1136, active_provider="FINNHUB", ticks=ticks)
    assert observation["status"] == "OBSERVED_HIT"
    assert observation["first_hit"]["provider_tick_ms"] == 1_020_250
    assert observation["seconds_from_entry"] == 20
    assert observation["horizon_fraction"] == 1 / 6
    assert observation["observed_tick_count"] == 3
    assert not observation["execution_authority"] and not observation["calibration_authority"]
    module.validate(observation, row)


def test_no_observed_crossing_and_missing_path_remain_distinct():
    module = importlib.import_module("intelligence.buffer_first_hit_time")
    row = _row("SELL")
    observed = module.pending(horizon_seconds=120, captured_ts=999)
    assert module.settle(observed, row, now_ts=1136, active_provider="FINNHUB",
                         ticks=[_tick(1010, 1.1001), _tick(1100, 1.0999)])
    assert observed["status"] == "NO_OBSERVED_HIT"
    assert observed["reason"] == "NO_OBSERVED_BUFFER_HIT"

    missing = module.pending(horizon_seconds=120, captured_ts=999)
    assert module.settle(missing, row, now_ts=1136, active_provider="FINNHUB", ticks=[])
    assert missing["status"] == "UNAVAILABLE"
    assert missing["reason"] == "PATH_OBSERVATION_MISSING"


def test_diagnostic_waits_for_late_real_ticks_and_never_changes_provider():
    module = importlib.import_module("intelligence.buffer_first_hit_time")
    row = _row()
    waiting = module.pending(horizon_seconds=120, captured_ts=999)
    assert not module.settle(waiting, row, now_ts=1135.25, active_provider="FINNHUB", ticks=[])
    assert waiting["status"] == "PENDING"
    assert module.settle(waiting, row, now_ts=1135.251, active_provider="TWELVE_DATA", ticks=[])
    assert waiting["status"] == "UNAVAILABLE" and waiting["reason"] == "PROVIDER_CHANGED"

