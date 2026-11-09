from io import BytesIO

import pytest
from PIL import Image


BASE = 1_800_000_000


def _chart_options(**overrides):
    return {"candles": [], "direction": "BUY", "entry_ts": BASE + 10, "entry_price": 1.1,
            "expiry_ts": BASE + 190, "expiry_quote_ts": None, "expiry_price": None,
            "buffer_distance": 0.0002, "outcome": "UNKNOWN", **overrides}


def _candle(offset, *, complete=True):
    return {"ts": BASE + offset, "open": 1.1, "high": 1.1003, "low": 1.0997,
            "close": 1.1001, "complete": complete}


def test_chart_does_not_draw_boundary_future_or_incomplete_candles(canonical_runtime_root):
    from intelligence.physical_study_chart import render_trade_chart

    whole_bar = _candle(60)
    expected = render_trade_chart(**_chart_options(candles=[whole_bar]))
    stale_or_partial = [_candle(0), _candle(120, complete=False), _candle(180), _candle(240)]
    assert render_trade_chart(**_chart_options(candles=stale_or_partial + [whole_bar])) == expected
    assert render_trade_chart(**_chart_options()) != expected
    with Image.open(BytesIO(expected)) as image:
        assert image.format == "PNG"
        assert image.size == (1200, 800)


@pytest.mark.parametrize(("direction", "hit", "shortfall"), [
    ("BUY", 1.1002, 1.10019999), ("SELL", 1.0998, 1.09980001),
])
def test_chart_marks_only_genuine_in_time_buffer_price(canonical_runtime_root, direction, hit, shortfall):
    from intelligence.physical_study_chart import render_trade_chart

    options = _chart_options(direction=direction)
    no_hit = render_trade_chart(**options)
    assert render_trade_chart(**options, first_buffer_hit={"observed_ts": BASE + 70.3, "price": hit}) != no_hit
    assert render_trade_chart(**options, first_buffer_hit={"observed_ts": BASE + 70.3, "price": shortfall}) == no_hit
    assert render_trade_chart(**options, first_buffer_hit={"observed_ts": BASE + 191, "price": hit}) == no_hit
