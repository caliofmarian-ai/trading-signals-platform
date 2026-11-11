"""Estimate presentation never manufactures an observed closing price."""
from copy import deepcopy
from io import BytesIO

import pytest
from PIL import Image, ImageDraw
from tests.canonical.unit.test_physical_study_delivery import study_setup, _capture, _sample

BASE = 1_800_000_000.0


def quote(stamp, price):
    return {"provider": "FINNHUB", "symbol": "EUR/USD", "provider_symbol": "OANDA:EUR_USD",
            "observed_ts": stamp, "received_ts": stamp + .1, "price": price,
            "source": "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1"}


def row_with_estimate(direction="BUY", before=1.1001, after=1.1002):
    from intelligence.expiry_price_estimate import build_estimate
    entry = quote(BASE + 10, 1.1)
    target = BASE + 190
    row = {"direction": direction, "created_ts": BASE + 10, "entry": entry,
           "buffer_snapshot": {"buffer_distance": .0002},
           "candidates": [{"horizon_seconds": 180, "quote": None, "outcome": "UNKNOWN",
                           "reason": "EXPIRY_OBSERVATION_MISSING"}]}
    bracket = {"before": quote(target - 1, before) if before is not None else None,
               "after": quote(target + 3, after) if after is not None else None}
    row["expiry_price_estimate"] = build_estimate(direction=direction, entry=entry,
        expiry_ts=target, bracket=bracket, observed_at=target + 18)
    return row


@pytest.mark.parametrize("direction,before,after,label", [
    ("BUY", 1.1001, 1.1002, "WIN estimat"),
    ("BUY", 1.0998, 1.0999, "LOSS estimat"),
    ("SELL", 1.0998, 1.0999, "WIN estimat"),
    ("SELL", 1.1001, 1.1002, "LOSS estimat"),
    ("BUY", 1.0999, 1.1001, "neconcludentă"),
    ("SELL", 1.1, 1.0999, "neconcludentă"),
    ("BUY", None, 1.1001, "indisponibilă"),
])
def test_caption_reports_estimates_without_claiming_settlement(direction, before, after, label):
    from intelligence.physical_study_delivery import render_result, _result_evidence
    row = row_with_estimate(direction, before, after)
    original = deepcopy(row)
    text = render_result("synthetic", row, "10.11.2026 · 11:25:15 · nr. 337")
    assert f"Estimare: {label}" in text
    assert "Rezultat: Lipsește cotația la expirare" in text and "UNKNOWN" not in text
    assert "Prețul dintre observații poate ieși din interval." in text
    assert "Estimarea nu intră în rata WIN verificată." in text
    assert "Interval orientativ" in text and "Înainte:" in text and "După:" in text
    assert row == original
    projected = _result_evidence(row)
    assert projected["study_outcome"] == "UNKNOWN" and projected["expiry_price"] is None
    assert projected["buffer_full_margin_status"] == "UNAVAILABLE"
    assert projected["expiry_price_estimate"] == row["expiry_price_estimate"]
    assert len(text.encode("utf-16-le")) // 2 <= 1024


def test_caption_keeps_close_distinct_prices_and_maximum_unicode_label():
    from intelligence.physical_study_delivery import render_result
    row = row_with_estimate(before=1.1000000000000003, after=1.1000000000000005)
    text = render_result("synthetic", row, "🧪" * 128)
    assert "1.1000000000000003" in text and "1.1000000000000005" in text
    assert "🧪" * 128 in text
    assert len(text.encode("utf-16-le")) // 2 <= 4096
    assert "WIN estimat" in text and "Rezultat: Lipsește cotația la expirare" in text


def test_forged_estimate_and_actual_settlement_cannot_display_estimated_win():
    from intelligence.physical_study_delivery import render_result
    row = row_with_estimate(before=1.0999, after=1.0998)
    row["expiry_price_estimate"]["estimated_outcome"] = "WIN"
    assert "WIN estimat" not in render_result("synthetic", row, None)
    row = row_with_estimate()
    row["candidates"][0].update(quote=quote(BASE + 190, 1.0999), outcome="LOSS",
                                reason="OBSERVED_PAIRED_EXPIRY")
    text = render_result("synthetic", row, None)
    assert "Rezultat: LOSS\n" in text and "WIN estimat" not in text


@pytest.mark.parametrize("before,after,label", [(1.1001, 1.1002, "WIN estimat"),
    (1.0999, 1.0998, "LOSS estimat"), (1.0999, 1.1001, "Estimare neconcludenta"),
    (None, 1.1001, "Estimare indisponibila")])
def test_chart_separates_neighbor_panel_without_a_fake_expiry_marker(monkeypatch, before, after, label):
    from intelligence.physical_study_chart import render_trade_chart
    row = row_with_estimate(before=before, after=after)
    texts, boxes, markers = [], [], []
    original_text, original_ellipse = ImageDraw.ImageDraw.text, ImageDraw.ImageDraw.ellipse

    def text(self, xy, value, *args, **kwargs):
        texts.append(value)
        boxes.append(self.textbbox(xy, value, font=kwargs.get("font"), anchor=kwargs.get("anchor")))
        return original_text(self, xy, value, *args, **kwargs)

    def ellipse(self, xy, *args, **kwargs):
        markers.append(kwargs.get("fill"))
        return original_ellipse(self, xy, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", text)
    monkeypatch.setattr(ImageDraw.ImageDraw, "ellipse", ellipse)
    png = render_trade_chart(candles=[], direction="BUY", entry_ts=BASE + 10, entry_price=1.1,
        expiry_ts=BASE + 190, expiry_quote_ts=None, expiry_price=None, buffer_distance=.0002,
        outcome="UNKNOWN", expiry_estimate=row["expiry_price_estimate"])
    with Image.open(BytesIO(png)) as image:
        assert image.size == (1200, 1200)
    assert label in texts and "LIPSA" in texts
    assert any("Lipseste cotatia la expirare" in item for item in texts)
    assert all("UNKNOWN" not in item for item in texts)
    assert any("Pretul dintre observatii poate iesi din interval" in item for item in texts)
    assert "#eff5fc" not in markers
    assert all(0 <= left < right <= 1200 and 0 <= top < bottom <= 1200
               for left, top, right, bottom in boxes)


def test_summary_estimates_are_a_partition_of_unknown_not_added_wins():
    from tests.canonical.unit.test_study_progress_presentation import evidence, render
    source = evidence()
    source["published_study_expiry_estimates"] = dict(contract="ADJACENT_SOURCE_QUOTES_ESTIMATE_V1",
        eligible_unknown=123, estimates_available=5, estimated_wins=2, estimated_losses=1,
        inconclusive=2, unavailable=118)
    before = deepcopy(source)
    text = render(source)
    assert "WIN estimat 2, LOSS estimat 1, neconcludente 2, fără estimare 118" in text
    assert "Total istoric · 351 rezultate: WIN 122, LOSS 100, DRAW 6, fără verdict 123" in text
    assert "nu intră în rata WIN verificată" in text and source == before
    source["published_study_expiry_estimates"]["estimated_wins"] = 10
    text = render(source)
    assert "Estimări din cotații vecine: statistici indisponibile sau neconcordante." in text
    assert "WIN estimat 10" not in text


@pytest.mark.parametrize("neighbor_arrives", [True, False])
def test_first_report_waits_for_bounded_neighbor_context_without_moving_expiry(study_setup, neighbor_arrives):
    _, study, _, _, _, _, messages, clock = study_setup
    _capture(study_setup)
    entry_ts = BASE + 32
    study.advance(now_ts=entry_ts, active_provider="FINNHUB", price_loader=lambda _: _sample(entry_ts, 1.1))
    saved = next(iter(study._read(study._path())["records"].values()))
    duration = study.displayed_study_observation(saved)["horizon_seconds"]
    target = entry_ts + duration
    sign = 1 if saved["direction"] == "BUY" else -1
    bracket = {"before": quote(target - 1, 1.1 + sign * .0001), "after": None}
    loader = lambda *args, **kwargs: bracket
    clock[0] = target + 18.1
    study.advance(now_ts=target + 18, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: None, bracket_loader=loader)
    saved = next(iter(study._read(study._path())["records"].values()))
    assert study.displayed_study_observation(saved)["outcome"] == "UNKNOWN"
    assert saved["study_delivery"]["result"] is None and len(messages) == 1
    assert saved["expiry_price_estimate"]["estimated_outcome"] == "UNAVAILABLE"
    if neighbor_arrives:
        bracket["after"] = quote(target + 24, 1.1 + sign * .0002)
        report_time = target + 25
    else:
        clock[0] = target + 74.1
        study.advance(now_ts=target + 74, active_provider="FINNHUB", price_loader=lambda _: None,
                      observation_loader=lambda *args: None, bracket_loader=loader)
        assert len(messages) == 1
        report_time = target + 75
    clock[0] = report_time + .1
    study.advance(now_ts=report_time, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: None, bracket_loader=loader)
    saved = next(iter(study._read(study._path())["records"].values()))
    observation = study.displayed_study_observation(saved)
    assert observation["outcome"] == "UNKNOWN" and observation["quote"] is None
    assert observation["horizon_seconds"] == duration and saved["entry"]["observed_ts"] + duration == target
    assert saved["study_delivery"]["result"]["status"] == "API_ACCEPTED"
    assert len(messages) == 2
    assert ("WIN estimat" if neighbor_arrives else "Estimare: indisponibilă") in messages[-1]["text"]
    clock[0] += 10
    study.advance(now_ts=report_time + 10, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=loader)
    assert len(messages) == 2


def test_oversized_caption_preserves_complete_evidence_with_text_fallback(study_setup, monkeypatch):
    _, study, delivery, _, _, _, messages, clock = study_setup
    _capture(study_setup)
    entry_ts = BASE + 32
    study.advance(now_ts=entry_ts, active_provider="FINNHUB", price_loader=lambda _: _sample(entry_ts, 1.1))
    saved = next(iter(study._read(study._path())["records"].values()))
    target = entry_ts + study.displayed_study_observation(saved)["horizon_seconds"]
    sign = 1 if saved["direction"] == "BUY" else -1
    bracket = {"before": quote(target - 1, 1.1 + sign * .0001),
               "after": quote(target + 3, 1.1 + sign * .0002)}
    real_render = delivery.render_result
    rendered = []
    def long_caption(*args):
        text = real_render(*args) + "\n" + "Detaliu sintetic pentru limita de transport. " * 20
        assert 1024 < len(text.encode("utf-16-le")) // 2 < 4096
        rendered.append(text)
        return text
    monkeypatch.setattr(delivery, "render_result", long_caption)
    clock[0] = target + 18.1
    study.advance(now_ts=target + 18, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: None,
                  bracket_loader=lambda *args, **kwargs: bracket)
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["study_delivery"]["result"]["format"] == "TEXT"
    assert saved["study_delivery"]["result"]["status"] == "API_ACCEPTED"
    assert messages[-1]["text"] == rendered[-1] and "photo" not in messages[-1]
