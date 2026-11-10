"""Synthetic recovery evidence; never a claim that missing market ticks existed."""
import copy

import pytest

from tests.canonical.unit.test_physical_only_v3 import (
    _capture,
    physical,
    physical_calibration,
)
from tests.canonical.unit.test_shadow_model_time_research import _sample


RECOVERY_POLICY = {
    "policy": "RETAINED_SOURCE_QUOTE_RECOVERY_V1",
    "arrival_grace_seconds": 15.0,
    "expiry_window_seconds": 2.0,
    "entry_window_seconds": 10.0,
}
RETAINED_SOURCES = (
    "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1",
    "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1",
)


def _row(module):
    return next(iter(module._read(module._path())["records"].values()))


def _timing(row):
    return {
        "created_ts": row["created_ts"],
        "model_seconds": row["model_seconds"],
        "adjusted_seconds": row["adjusted_seconds"],
        "policies": copy.deepcopy(row["policies"]),
        "candidate_horizons": [c["horizon_seconds"] for c in row["candidates"]],
    }


def _opened(module, params, *, legacy=False):
    _capture(module, params)
    if legacy:
        state = module._read(module._path())
        next(iter(state["records"].values())).pop("quote_recovery_policy", None)
        module._save(module._path(), state)
    module.advance(
        now_ts=1001, active_provider="FINNHUB", price_loader=lambda _: _sample(1001, 1.1)
    )
    row = _row(module)
    return row, row["entry"]["observed_ts"] + row["candidates"][0]["horizon_seconds"]


def test_recovery_policy_is_frozen_only_on_new_capture(physical_calibration):
    _, module, params = physical_calibration
    _capture(module, params)
    state = module._read(module._path())
    legacy_id, legacy = next(iter(state["records"].items()))
    legacy.pop("quote_recovery_policy", None)
    module._save(module._path(), state)
    before = copy.deepcopy(legacy)

    _capture(module, params, stamp=2000)
    saved = module._read(module._path())
    assert saved["records"][legacy_id] == before
    new = next(r for r in saved["records"].values() if r["created_ts"] == 2000)
    assert new["quote_recovery_policy"] == RECOVERY_POLICY


@pytest.mark.parametrize("source", RETAINED_SOURCES)
def test_late_in_window_expiry_tick_survives_old_finalization_deadline(
    physical_calibration, source
):
    _, module, params = physical_calibration
    original, target = _opened(module, params)
    timing = _timing(original)
    received = None

    def retained(symbol, requested, delay):
        assert symbol == "EUR/USD" and delay == 2.0
        return received if requested == target else None

    # The previous 2s source window + 4s grace incorrectly finalized here.
    module.advance(now_ts=target + 7, active_provider="FINNHUB",
                   price_loader=lambda _: None, observation_loader=retained)
    assert _row(module)["candidates"][0]["outcome"] == "PENDING"

    # Received 13s after its own source timestamp, still genuinely in-window.
    received = _sample(target + 1, 1.1003, source=source)
    module.advance(now_ts=target + 14, active_provider="FINNHUB",
                   price_loader=lambda _: _sample(target + 14, 1.0),
                   observation_loader=retained)
    saved = _row(module)
    candidate = saved["candidates"][0]
    assert candidate["outcome"] == "WIN"
    assert candidate["quote"]["observed_ts"] == target + 1
    assert candidate["quote"]["source"] == source
    assert candidate["quote"]["price"] == 1.1003
    assert saved["entry"] == original["entry"]
    assert _timing(saved) == timing


def test_entry_recovery_wait_does_not_change_actual_entry_timestamp(physical_calibration):
    _, module, params = physical_calibration
    _capture(module, params)
    timing = _timing(_row(module))
    received = None

    def retained(symbol, requested, delay):
        return received if requested == 1000 and delay == 10.0 else None

    module.advance(now_ts=1015, active_provider="FINNHUB",
                   price_loader=lambda _: None, observation_loader=retained)
    assert _row(module)["state"] == "WAITING_ENTRY"
    received = _sample(1001, 1.1, source=RETAINED_SOURCES[1])
    module.advance(now_ts=1024, active_provider="FINNHUB",
                   price_loader=lambda _: None, observation_loader=retained)
    saved = _row(module)
    assert saved["state"] == "OBSERVING"
    assert saved["entry"]["observed_ts"] == 1001
    assert saved["entry"]["source"] == RETAINED_SOURCES[1]
    assert _timing(saved) == timing


@pytest.mark.parametrize("source_offset", [-1, 3])
def test_arrival_grace_never_admits_price_outside_original_expiry_window(
    physical_calibration, source_offset
):
    _, module, params = physical_calibration
    original, target = _opened(module, params)
    wrong = _sample(target + source_offset, 1.2, source=RETAINED_SOURCES[1])

    def retained(symbol, requested, delay):
        assert delay == 2.0
        return wrong if requested == target else None

    module.advance(now_ts=target + 14, active_provider="FINNHUB",
                   price_loader=lambda _: _sample(target + 14, 1.2),
                   observation_loader=retained)
    assert _row(module)["candidates"][0]["outcome"] == "PENDING"
    module.advance(now_ts=target + 18, active_provider="FINNHUB",
                   price_loader=lambda _: _sample(target + 18, 1.2),
                   observation_loader=retained)
    saved = _row(module)
    assert saved["candidates"][0]["outcome"] == "UNKNOWN"
    assert saved["candidates"][0]["reason"] == "EXPIRY_OBSERVATION_MISSING"
    assert saved["candidates"][0]["quote"] is None
    assert _timing(saved) == _timing(original)


def test_missing_expiry_stays_pending_through_grace_then_finalizes_once(physical_calibration):
    _, module, params = physical_calibration
    _, target = _opened(module, params)
    module.advance(now_ts=target + 17, active_provider="FINNHUB",
                   price_loader=lambda _: None, observation_loader=lambda *a: None)
    assert _row(module)["candidates"][0]["outcome"] == "PENDING"
    module.advance(now_ts=target + 17.001, active_provider="FINNHUB",
                   price_loader=lambda _: None, observation_loader=lambda *a: None)
    finalized = copy.deepcopy(_row(module))
    assert finalized["state"] == "FINAL"
    assert finalized["candidates"][0]["outcome"] == "UNKNOWN"

    module.advance(now_ts=target + 18, active_provider="FINNHUB",
                   price_loader=lambda _: None,
                   observation_loader=lambda *a: _sample(target, 1.2, source=RETAINED_SOURCES[1]))
    assert _row(module) == finalized


def test_legacy_four_second_grace_and_final_unknown_are_preserved(physical_calibration):
    _, module, params = physical_calibration
    original, target = _opened(module, params, legacy=True)
    module.advance(now_ts=target + 6, active_provider="FINNHUB",
                   price_loader=lambda _: None, observation_loader=lambda *a: None)
    assert _row(module)["candidates"][0]["outcome"] == "PENDING"
    module.advance(now_ts=target + 6.001, active_provider="FINNHUB",
                   price_loader=lambda _: None, observation_loader=lambda *a: None)
    finalized = copy.deepcopy(_row(module))
    assert finalized["candidates"][0]["outcome"] == "UNKNOWN"
    assert "quote_recovery_policy" not in finalized
    assert _timing(finalized) == _timing(original)
    module.advance(now_ts=target + 14, active_provider="FINNHUB",
                   price_loader=lambda _: None,
                   observation_loader=lambda *a: _sample(target + 1, 1.2, source=RETAINED_SOURCES[1]))
    assert _row(module) == finalized


def test_provider_switch_cannot_recover_from_any_retained_source(physical_calibration):
    _, module, params = physical_calibration
    _, target = _opened(module, params)

    def forbidden(*args):
        pytest.fail("Provider change must not fetch a replacement quote")

    module.advance(now_ts=target + 1, active_provider="TWELVE_DATA",
                   price_loader=forbidden, observation_loader=forbidden)
    row = _row(module)
    assert all(c["outcome"] == "UNKNOWN" and c["reason"] == "PROVIDER_CHANGED"
               and c["quote"] is None for c in row["candidates"])


@pytest.mark.parametrize("malformed", [
    None,
    {},
    {**RECOVERY_POLICY, "policy": "UNRECOGNIZED_POLICY"},
    {**RECOVERY_POLICY, "arrival_grace_seconds": -1.0},
    {**RECOVERY_POLICY, "arrival_grace_seconds": 16.0},
    {**RECOVERY_POLICY, "expiry_window_seconds": 3.0},
    {**RECOVERY_POLICY, "entry_window_seconds": 11.0},
    {**RECOVERY_POLICY, "arbitrary_fallback": True},
])
def test_malformed_recovery_policy_cannot_enter_persisted_evidence(
    physical_calibration, malformed
):
    _, module, params = physical_calibration
    _capture(module, params)
    state = module._read(module._path())
    next(iter(state["records"].values()))["quote_recovery_policy"] = malformed
    with pytest.raises(ValueError):
        module.validate(state)


@pytest.mark.parametrize("changes", [
    {"provider": "TWELVE_DATA"},
    {"symbol": "GBP/USD"},
    {"observed_ts": 1010},
    {"observed_ts": 0},
    {"price": float("nan")},
    {"price": True},
    {"source": []},
    {"source": {}},
])
def test_durable_provenance_does_not_waive_tick_validation(physical_calibration, changes):
    _, module, _ = physical_calibration
    sample = _sample(1000, 1.1, source=RETAINED_SOURCES[1])
    sample.update(changes)
    assert module._observed_quote(sample, 1001) is None
