from io import BytesIO

import pytest
from PIL import Image, ImageDraw


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


@pytest.mark.parametrize("direction", ["BUY", "SELL"])
def test_buffer_band_is_between_entry_and_favorable_edge(direction):
    from intelligence.physical_study_chart import render_trade_chart

    png = render_trade_chart(**_chart_options(direction=direction))
    with Image.open(BytesIO(png)) as image:
        # Read the actual rendered reference lines away from ticks/candles.
        x = 61
        entry_rows = [y for y in range(218, 587) if image.getpixel((x, y)) == (139, 188, 255)]
        edge_rows = [y for y in range(218, 587) if image.getpixel((x, y)) == (244, 200, 113)]
        assert entry_rows and edge_rows
        entry_y, edge_y = entry_rows[0], edge_rows[0]
        assert (edge_y < entry_y) is (direction == "BUY")
        upper, lower = sorted((entry_y, edge_y))
        band_color = (61, 52, 37)
        assert image.getpixel((x, upper + 8)) == band_color
        assert image.getpixel((x, (upper + lower) // 2)) == band_color
        assert image.getpixel((x, lower - 8)) == band_color
        # Neither the favorable region beyond the edge nor the losing region
        # beyond entry is itself the buffer.
        background = (19, 34, 55)
        assert image.getpixel((x, upper - 8)) == background
        assert image.getpixel((x, lower + 8)) == background


@pytest.mark.parametrize(("direction", "price", "fragile"), [
    ("BUY", 1.1001, True), ("SELL", 1.0999, True),
    ("BUY", 1.1002, False), ("SELL", 1.0998, False),
    ("BUY", 1.1003, False), ("SELL", 1.0997, False),
])
def test_chart_explains_fragile_win_without_changing_directional_result(
    monkeypatch, direction, price, fragile,
):
    from intelligence.physical_study_chart import render_trade_chart

    labels = []
    original = ImageDraw.ImageDraw.text

    def capture(self, xy, text, *args, **kwargs):
        labels.append(text)
        return original(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    render_trade_chart(**_chart_options(direction=direction, expiry_price=price,
                                      expiry_quote_ts=BASE + 190, outcome="WIN"))
    assert ("WIN fragil · In buffer" in labels) is fragile
    assert ("WIN · Castig" in labels) is not fragile
    assert not any("LOSS" in label for label in labels)
    assert any("Banda galbena" in label and "Buffer langa intrare" in label for label in labels)
    assert not any("Buffer atins" in label or "Buffer la cotatia observata" in label for label in labels)


def test_chart_names_observed_contact_as_buffer_edge_not_band_entry(monkeypatch):
    from intelligence.physical_study_chart import render_trade_chart

    labels = []
    original = ImageDraw.ImageDraw.text

    def capture(self, xy, text, *args, **kwargs):
        labels.append(text)
        return original(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    render_trade_chart(**_chart_options(), first_buffer_hit={"observed_ts": BASE + 70.3, "price": 1.1002})
    assert any("Limita buffer atinsa in cotatie" in label for label in labels)
    assert not any("reintrare" in label.lower() for label in labels)


@pytest.mark.parametrize("direction", ["BUY", "SELL"])
def test_complete_candle_starting_at_entry_can_prove_edge_contact(monkeypatch, direction):
    from intelligence.physical_study_chart import render_trade_chart

    labels = []
    original = ImageDraw.ImageDraw.text

    def capture(self, xy, text, *args, **kwargs):
        labels.append(text)
        return original(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    render_trade_chart(**_chart_options(direction=direction, entry_ts=BASE, candles=[_candle(0)]))
    assert any("Limita buffer atinsa in lumanarea" in label for label in labels)
    assert not any("nu este confirmata" in label for label in labels)

