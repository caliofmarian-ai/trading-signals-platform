import math

import pytest

from core.buffer_zone import BUFFER_POSITION_LABELS, classify_buffer_position


@pytest.mark.parametrize(("buy_price", "sell_price", "expected"), [
    (1.1003, 1.0997, "BEYOND_BUFFER"),
    (1.1002, 1.0998, "AT_BUFFER_EDGE"),
    (1.1001, 1.0999, "INSIDE_BUFFER"),
    (1.1, 1.1, "AT_ENTRY"),
    (1.0999, 1.1001, "LOSS_SIDE"),
])
def test_buy_and_sell_use_mirrored_favorable_bands(buy_price, sell_price, expected):
    assert classify_buffer_position("BUY", 1.1, 0.0002, buy_price) == expected
    assert classify_buffer_position("SELL", 1.1, 0.0002, sell_price) == expected


@pytest.mark.parametrize(("direction", "price"), [
    ("BUY", math.nextafter(1.1002, 1.1)),
    ("SELL", math.nextafter(1.0998, 1.1)),
])
def test_shortfall_is_not_rounded_to_the_favorable_edge(direction, price):
    assert classify_buffer_position(direction, 1.1, 0.0002, price) == "INSIDE_BUFFER"


def test_reported_eurusd_close_is_a_fragile_win_inside_the_buffer():
    result = classify_buffer_position("BUY", 1.1222100, 0.0001858, 1.1223450)
    assert result == "INSIDE_BUFFER"
    assert "câștig fragil" in BUFFER_POSITION_LABELS[result]


@pytest.mark.parametrize("field", ["entry_price", "buffer_distance", "price"])
@pytest.mark.parametrize("invalid", [None, 0, -1, float("nan"), float("inf"),
                                     float("-inf"), True, "1.1"])
def test_missing_or_invalid_inputs_cannot_claim_a_position(field, invalid):
    options = {"entry_price": 1.1, "buffer_distance": 0.0002, "price": 1.1003}
    options[field] = invalid
    assert classify_buffer_position("BUY", **options) == "UNAVAILABLE"


@pytest.mark.parametrize("direction", [None, "", "buy", "LONG", [], {}])
def test_invalid_direction_is_rejected(direction):
    with pytest.raises(ValueError, match="INVALID_BUFFER_DIRECTION"):
        classify_buffer_position(direction, 1.1, 0.0002, 1.1003)


def test_initial_quote_stays_at_entry_even_with_the_smallest_positive_float_buffer():
    assert classify_buffer_position("BUY", 1e100, 5e-324, 1e100) == "AT_ENTRY"


def test_integer_inputs_preserve_the_exact_favorable_edge():
    assert classify_buffer_position("BUY", 1, 1, 2) == "AT_BUFFER_EDGE"
