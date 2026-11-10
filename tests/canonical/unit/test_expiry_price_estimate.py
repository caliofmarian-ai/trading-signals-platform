"""Neighbor estimates never manufacture a verified expiry observation."""
from copy import deepcopy
import json
import math

import pytest

from intelligence.expiry_price_estimate import build_estimate, validate_estimate


ENTRY = {"price": 1.1, "observed_ts": 800.0}


def quote(stamp, price=1.2, **extra):
    return {"provider": "FINNHUB", "symbol": "EUR/USD", "provider_symbol": "OANDA:EUR_USD",
            "observed_ts": stamp, "price": price,
            "source": "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1", **extra}


def estimate(before=1.2, after=1.3, *, direction="BUY", bracket=None, entry=None):
    return build_estimate(direction=direction, entry=ENTRY if entry is None else entry,
                          expiry_ts=1000.0, observed_at=1010.0,
                          bracket=bracket if bracket is not None else {
                              "before": quote(999.0, before), "after": quote(1004.0, after)})


@pytest.mark.parametrize("direction,before,after,outcome", [
    ("BUY", 1.2, 1.3, "WIN"), ("BUY", 1.0, 0.9, "LOSS"),
    ("SELL", 1.2, 1.3, "LOSS"), ("SELL", 1.0, 0.9, "WIN"),
    ("BUY", 1.0, 1.2, "INCONCLUSIVE"), ("SELL", 1.2, 1.0, "INCONCLUSIVE"),
    ("BUY", 1.1, 1.2, "INCONCLUSIVE"), ("SELL", 1.0, 1.1, "INCONCLUSIVE"),
    ("BUY", 1.1, 1.1, "INCONCLUSIVE"), ("SELL", 1.1, 1.1, "INCONCLUSIVE"),
])
def test_endpoint_direction_is_separate_and_equality_never_invents_draw(direction, before, after, outcome):
    result = estimate(before, after, direction=direction)
    assert result["estimated_outcome"] == outcome
    assert result["truth_domain"] == "APPROXIMATION_ONLY"
    assert result["contract"] == "ADJACENT_SOURCE_QUOTES_ESTIMATE_V1"
    assert result["lower_price"] == min(before, after)
    assert result["upper_price"] == max(before, after)
    assert result["gap_seconds"] == 5.0
    assert not {"expiry_price", "expiry_quote", "probability", "midpoint", "outcome"} & result.keys()
    validate_estimate(result, direction=direction, entry=ENTRY, expiry_ts=1000.0)
    json.dumps(result, allow_nan=False)


def test_serialized_price_precision_is_not_display_rounding():
    entry = {"price": 1.0, "observed_ts": 800.0}
    above = math.nextafter(1.0, math.inf)
    result = estimate(above, above, entry=entry)
    assert result["estimated_outcome"] == "WIN"
    assert result["lower_price"] == above
    validate_estimate(result, direction="BUY", entry=entry, expiry_ts=1000.0)


@pytest.mark.parametrize("field,value", [
    ("provider", "TWELVE_DATA"), ("symbol", "GBP/USD"),
    ("provider_symbol", "OTHER:EUR_USD"), ("source", "LIVE_STREAM_CURRENT_M1_CLOSE"),
    ("source", []), ("price", float("nan")), ("price", float("inf")),
    ("price", True), ("price", 0), ("price", "1.2"),
    ("observed_ts", float("nan")), ("observed_ts", True),
    ("observed_ts", 939.999), ("observed_ts", 1000.0), ("observed_ts", 1001.0),
    ("received_ts", 1011.0), ("received_ts", float("nan")), ("received_ts", True),
    ("provider_tick_ms", 999001.0), ("provider_tick_ms", True),
    ("provider_tick_ms", 1011000),
])
def test_invalid_before_side_is_explicitly_unavailable(field, value):
    bad = quote(999.0)
    bad[field] = value
    result = estimate(bracket={"before": bad, "after": quote(1004.0)})
    assert result["estimated_outcome"] == "UNAVAILABLE"
    assert result["reason"] == "BEFORE_QUOTE_UNAVAILABLE"
    assert result["before"] is None and result["after"] is not None
    assert result["lower_price"] is result["upper_price"] is result["gap_seconds"] is None
    validate_estimate(result, direction="BUY", entry=ENTRY, expiry_ts=1000.0)


@pytest.mark.parametrize("side,stamp", [("before", 940.0), ("after", 1060.0)])
def test_sixty_second_endpoint_is_inclusive(side, stamp):
    bracket = {"before": quote(999.0), "after": quote(1004.0)}
    bracket[side] = quote(stamp)
    result = build_estimate(direction="BUY", entry=ENTRY, expiry_ts=1000,
                            bracket=bracket, observed_at=1060)
    assert result["estimated_outcome"] == "WIN"


@pytest.mark.parametrize("after", [None, quote(1060.001), quote(1011.0), quote(999.0), quote(1000.0)])
def test_after_side_missing_stale_future_or_wrong_side_stays_unavailable(after):
    result = estimate(bracket={"before": quote(999.0), "after": after})
    assert result["estimated_outcome"] == "UNAVAILABLE"
    assert result["reason"] == "AFTER_QUOTE_UNAVAILABLE"
    validate_estimate(result, direction="BUY", entry=ENTRY, expiry_ts=1000)


def test_empty_or_malformed_bracket_does_not_invent_quotes():
    for bracket in ({}, None, [], {"before": [], "after": "bad"}):
        result = build_estimate(direction="BUY", entry=ENTRY, expiry_ts=1000,
                                bracket=bracket, observed_at=1010)
        assert result["reason"] == "BOTH_QUOTES_UNAVAILABLE"
        assert result["before"] is result["after"] is None
        validate_estimate(result, direction="BUY", entry=ENTRY, expiry_ts=1000)


def test_raw_milliseconds_and_original_receipt_are_preserved_without_input_mutation():
    before = quote(999.0, _provider_tick_ms=999900, _received_ts=1003.25)
    after = quote(1004.0, source="DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1",
                  _provider_tick_ms=1004123, _received_ts=1008.5)
    bracket = {"before": before, "after": after}
    frozen = deepcopy(bracket)
    result = estimate(bracket=bracket)
    assert result["before"]["observed_ts"] == 999.9
    assert result["after"]["observed_ts"] == 1004.123
    assert result["before"]["received_ts"] == 1003.25
    assert result["after"]["received_ts"] == 1008.5
    assert result["after"]["provider_tick_ms"] == 1004123
    assert not any(key.startswith("_") for key in result["before"])
    assert bracket == frozen
    validate_estimate(result, direction="BUY", entry=ENTRY, expiry_ts=1000)


def test_missing_receipt_is_preserved_instead_of_fabricated():
    result = estimate()
    assert "received_ts" not in result["before"] and "received_ts" not in result["after"]
    validate_estimate(result, direction="BUY", entry=ENTRY, expiry_ts=1000)


@pytest.mark.parametrize("extra", [
    {"provider_tick_ms": 999000, "_provider_tick_ms": 998000},
    {"received_ts": 1001, "_received_ts": 1002},
    {"received_ts": 1, "_received_ts": True},
])
def test_conflicting_or_invalid_timestamp_aliases_are_not_hidden(extra):
    result = estimate(bracket={"before": quote(999, **extra), "after": quote(1004)})
    assert result["before"] is None and result["estimated_outcome"] == "UNAVAILABLE"


@pytest.mark.parametrize("field,value", [
    ("estimated_outcome", "LOSS"), ("reason", "CONFIRMED"),
    ("truth_domain", "OBSERVED"), ("contract", "OTHER"), ("lower_price", 1.0),
    ("upper_price", 2.0), ("gap_seconds", 4.0), ("expiry_ts", 1001.0),
    ("max_side_seconds", 120.0), ("before", None), ("after", None),
    ("estimated_at", True), ("gap_seconds", True),
])
def test_stored_estimate_cannot_override_recomputed_evidence(field, value):
    result = estimate()
    result[field] = value
    with pytest.raises(ValueError):
        validate_estimate(result, direction="BUY", entry=ENTRY, expiry_ts=1000)


def test_stored_endpoint_tampering_and_extra_fields_are_rejected():
    for mutate in (
        lambda result: result["before"].update(provider="OTHER"),
        lambda result: result["after"].update(received_ts=1011),
        lambda result: result["before"].update(price=0.5),
        lambda result: result.update(expiry_price=1.25),
    ):
        result = estimate()
        mutate(result)
        with pytest.raises(ValueError):
            validate_estimate(result, direction="BUY", entry=ENTRY, expiry_ts=1000)


@pytest.mark.parametrize("changes", [
    {"direction": "HOLD"}, {"direction": []}, {"entry": None},
    {"entry": {"price": 1.1, "observed_ts": 1000}},
    {"entry": {"price": float("nan"), "observed_ts": 800}},
    {"entry": {**ENTRY, "provider": "OTHER"}}, {"expiry_ts": True},
    {"expiry_ts": float("inf")}, {"observed_at": 999}, {"observed_at": float("nan")},
])
def test_invalid_entry_or_context_cannot_produce_estimated_result(changes):
    args = {"direction": "BUY", "entry": ENTRY, "expiry_ts": 1000,
            "bracket": {"before": quote(999), "after": quote(1004)}, "observed_at": 1010}
    args.update(changes)
    with pytest.raises(ValueError):
        build_estimate(**args)
