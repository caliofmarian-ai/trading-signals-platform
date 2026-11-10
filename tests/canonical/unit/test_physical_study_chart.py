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
        assert image.size == (1200, 940)


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
def test_chart_keeps_plain_win_and_explains_buffer_position_separately(
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
    assert "REZULTAT  /  STUDIU V3" in labels
    assert "WIN · Castig" in labels
    assert not any(label.startswith("WIN fragil") for label in labels)
    assert any("In buffer · castig fragil" in label for label in labels) is fragile
    assert any(f"Marja completa la expirare: {'NU' if fragile else 'DA'}" in label for label in labels)
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


def _capture_rendering(monkeypatch):
    labels, boxes, markers = [], [], []
    original_text = ImageDraw.ImageDraw.text
    original_ellipse = ImageDraw.ImageDraw.ellipse

    def text(self, xy, value, *args, **kwargs):
        labels.append(value)
        box = self.textbbox(xy, value, font=kwargs.get("font"), anchor=kwargs.get("anchor"))
        boxes.append((xy, value, box))
        return original_text(self, xy, value, *args, **kwargs)

    def ellipse(self, xy, *args, **kwargs):
        markers.append((xy, kwargs.get("fill")))
        return original_ellipse(self, xy, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", text)
    monkeypatch.setattr(ImageDraw.ImageDraw, "ellipse", ellipse)
    return labels, boxes, markers


@pytest.mark.parametrize("direction,hit", [("BUY", 1.1003), ("SELL", 1.0997)])
def test_favorable_earlier_evidence_cannot_imply_a_missing_expiry_price(
    monkeypatch, direction, hit
):
    from intelligence.physical_study_chart import render_trade_chart

    labels, boxes, markers = _capture_rendering(monkeypatch)
    render_trade_chart(**_chart_options(
        direction=direction,
        candles=[_candle(60)],
        first_buffer_hit={"observed_ts": BASE + 121.3, "price": hit},
    ))
    assert "UNKNOWN · Date incomplete" in labels
    assert "LIPSA" in labels
    assert not any(label.startswith(("WIN ·", "LOSS ·", "DRAW ·")) for label in labels)
    assert any("intrare 1/1" in label and "expirare 0/1 · LIPSA" in label for label in labels)
    assert any("Pretul pentru expirare lipseste" in label for label in labels)
    assert any("Context M1: 1 complete" in label and "08:01:00-08:02:00" in label
               and "08:03:10" in label for label in labels)
    assert any("nu inlocuiesc cotatia pentru expirare" in label for label in labels)
    assert "PRET INTRARE · REPER" in labels and "LIMITA BUFFER · REPER" in labels
    assert any("Orizontale: albastru = intrare" in label and "(repere)" in label for label in labels)
    assert all(fill != "#eff5fc" for _, fill in markers)  # No white expiry-price marker.
    assert any(fill == "#8bbcff" for _, fill in markers)  # Genuine entry remains visible.
    assert any(fill == "#f4c871" for _, fill in markers)  # Genuine prior contact remains context.
    assert all(0 <= box[0] < box[2] <= 1200 and 0 <= box[1] < box[3] <= 940
               for _, _, box in boxes)


@pytest.mark.parametrize("direction,price,comparison,outcome", [
    ("BUY", 1.10000001, ">", "WIN"),
    ("SELL", 1.09999999, "<", "WIN"),
    ("BUY", 1.09999999, "<", "LOSS"),
    ("SELL", 1.10000001, ">", "LOSS"),
    ("BUY", 1.1, "=", "DRAW"),
    ("SELL", 1.1, "=", "DRAW"),
])
def test_numeric_directional_comparison_preserves_small_moves_and_equal_prices(
    monkeypatch, direction, price, comparison, outcome
):
    from intelligence.physical_study_chart import render_trade_chart

    labels, boxes, _ = _capture_rendering(monkeypatch)
    render_trade_chart(**_chart_options(direction=direction, expiry_price=price,
                                      expiry_quote_ts=BASE + 191, outcome=outcome))
    formula = next(label for label in labels if label.startswith("Comparatie "))
    assert formula.startswith(f"Comparatie {direction}:")
    assert f"{comparison} intrare 1.1000000" in formula and formula.endswith(outcome)
    if price != 1.1:
        assert str(price) in formula
        assert str(price) in labels  # Unrounded observed expiry cell too.
    assert any("expirare 1/1, la 08:03:11 UTC" in label for label in labels)
    assert not any("LIPSA" in label or "UNKNOWN" in label for label in labels)
    assert all(0 <= box[0] < box[2] <= 1200 and 0 <= box[1] < box[3] <= 940
               for _, _, box in boxes)


def test_long_observed_prices_fit_cells_and_tiny_buffer_boundary_is_honestly_approximated(monkeypatch):
    from intelligence.physical_study_chart import render_trade_chart

    labels, boxes, _ = _capture_rendering(monkeypatch)
    entry, close = 1.123456789012345, 1.1234567890123457
    render_trade_chart(**_chart_options(entry_price=entry, expiry_price=close,
                                      expiry_quote_ts=BASE + 190, buffer_distance=1e-200, outcome="WIN"))
    assert str(entry) in labels and str(close) in labels
    assert any("LIMITA BUFFER (~ = aprox.)" == label for label in labels)
    computed = next(value for (xy, value, _) in boxes if xy == (340, 155))
    assert computed.startswith("~") and len(computed) <= 22
    widths = {48: 270, 340: 263, 625: 325, 972: 180}
    for (x, y), _, box in boxes:
        if y == 155:
            assert box[2] <= x + widths[x]
    assert all(0 <= box[0] < box[2] <= 1200 and 0 <= box[1] < box[3] <= 940
               for _, _, box in boxes)

