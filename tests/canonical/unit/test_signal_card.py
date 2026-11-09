"""Signal-photo data boundaries and the approved directional/button rendering."""

from datetime import datetime, timezone
from io import BytesIO

from PIL import Image, ImageColor, ImageFont
import pytest

from core import signal_card as cards


LABEL = "09.11.2026 · 21:25:00 · nr. 2"
NOW = datetime(2026, 11, 9, 21, 25, tzinfo=timezone.utc).timestamp()


def event(stage="OPEN_NOW", direction="SELL"):
    return {"stage": stage, "direction": direction, "symbol": "EUR/USD",
            "signal_id": "private-uuid-must-never-appear", "created_ts": NOW,
            "entry_price": 1.12221, "execution_time_available": True,
            "open_now_expiry_minutes": 5, "confirm_expiry_min_minutes": 4.5,
            "confirm_expiry_max_minutes": 5.25, "model_expiry": 99}


@pytest.mark.parametrize("direction", ["BUY", "SELL"])
@pytest.mark.parametrize("stage", ["PRE", "CONFIRM", "OPEN_NOW"])
def test_actual_png_uses_direction_color_for_top_and_only_active_bottom_button(direction, stage):
    png = cards.render_signal_card(event(stage, direction), LABEL, shadow=True)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    picture = Image.open(BytesIO(png)).convert("RGB")
    assert picture.size == (1200, 1320)
    accent = ImageColor.getrgb(cards.ACCENTS[direction])
    inactive = ImageColor.getrgb(cards.INACTIVE)
    assert picture.getpixel((75, 235)) == accent
    for target, x in zip(("PRE", "CONFIRM", "OPEN_NOW"), (70, 370, 750)):
        assert picture.getpixel((x, 1110)) == (accent if target == stage else inactive)
    colors = {color for _, color in picture.getcolors(picture.width * picture.height)}
    opposite = "BUY" if direction == "SELL" else "SELL"
    assert ImageColor.getrgb(cards.ACCENTS[opposite]) not in colors


def test_short_identifier_and_actual_values_are_shared_by_card_and_caption():
    fields = cards.build_card_fields(event(), LABEL)
    assert fields["number"] == "#2" and fields["date"] == "09.11.2026"
    assert fields["stage_label"] == "OPEN NOW"
    assert fields["price"] == "1.1222100" and fields["duration"] == "5 MIN"
    assert fields["entry_time"] == "21:25" and fields["expiry_time"] == "21:30"
    assert fields["entry_label"] == "REFERINȚĂ"
    assert fields["expiry_label"] == "EXPIRARE ESTIMATĂ"
    caption = cards.render_signal_caption(event(), LABEL, shadow=True)
    for expected in ("#2", "09.11.2026", "OPEN NOW", "SELL", "1.1222100", "5 MIN", "Dublin", "OBSERVARE PRIVATĂ"):
        assert expected in caption
    assert "private-uuid" not in caption and "99" not in caption and "Score" not in caption
    assert len(caption) < 1024


@pytest.mark.parametrize("stage", ["PRE", "CONFIRM"])
def test_pre_and_uncalibrated_confirm_never_invent_duration_or_entry_clocks(stage):
    candidate = event(stage)
    candidate["execution_time_available"] = False
    fields = cards.build_card_fields(candidate, LABEL)
    assert fields["duration"] == fields["entry_time"] == fields["expiry_time"] == "—"
    assert "AȘTEAPTĂ OPEN NOW" in fields["footer"]
    assert "99" not in cards.render_signal_caption(candidate, LABEL)


def test_confirm_projects_exact_validated_interval_without_creating_open_clock():
    fields = cards.build_card_fields(event("CONFIRM"), LABEL)
    assert fields["duration"] == "4.5–5.25 MIN"
    assert fields["entry_time"] == fields["expiry_time"] == "—"


@pytest.mark.parametrize("duration", [None, 0, -1, True, float("nan"), float("inf")])
def test_open_rejects_missing_or_invalid_execution_duration(duration):
    candidate = event()
    candidate["open_now_expiry_minutes"] = duration
    with pytest.raises(ValueError, match="VALIDATED_EXECUTION_TIME"):
        cards.render_signal_card(candidate, LABEL)


def test_model_duration_never_masquerades_as_canonical_execution_time():
    candidate = event()
    candidate.update(execution_time_available=False, study_duration_minutes=5,
                     entry_ts=NOW, expiry_ts=NOW + 300)
    with pytest.raises(ValueError, match="VALIDATED_EXECUTION_TIME"):
        cards.render_signal_card(candidate, LABEL)
    fields = cards.build_card_fields(candidate, LABEL, study=True)
    assert fields["duration"] == "5 MIN" and fields["footer"] == "STUDIU · SIMULARE"
    caption = cards.render_signal_caption(candidate, LABEL, study=True)
    assert "STUDIU · SIMULARE" in caption and "INTRARE: 21:25" in caption


def test_study_rejects_contradictory_expiry_and_preserves_fractional_observation_time():
    candidate = event()
    candidate.update(study_duration_minutes=2.375, entry_ts=NOW + 3.25,
                     expiry_ts=NOW + 145.75)
    fields = cards.build_card_fields(candidate, LABEL, study=True)
    assert fields["entry_time"] == "21:25:03.25"
    assert fields["expiry_time"] == "21:27:25.75"
    assert fields["duration"] == "2.375 MIN"
    candidate["expiry_ts"] += 1
    with pytest.raises(ValueError, match="INCONSISTENT_SIGNAL_CARD_STUDY_EXPIRY"):
        cards.render_signal_card(candidate, LABEL, study=True)


def test_reserved_day_survives_midnight_and_clocks_use_dublin_summer_time():
    candidate = event()
    candidate["created_ts"] = datetime(2026, 7, 1, 22, 59, 40, tzinfo=timezone.utc).timestamp()
    label = "01.07.2026 · 23:55:00 · nr. 0"
    fields = cards.build_card_fields(candidate, label)
    assert fields["date"] == "01.07.2026" and fields["number"] == "#0"
    assert fields["entry_time"] == "23:59:40"
    assert fields["expiry_time"] == "00:04:40"
    assert fields["expiry_date"] == "02.07.2026"
    assert "00:04:40 (02.07.2026)" in cards.render_signal_caption(candidate, label)
    candidate["created_ts"] += 86400
    assert cards.build_card_fields(candidate, label)["date"] == "01.07.2026"


@pytest.mark.parametrize("label", [None, "sig-v3-long-uuid", "#2", "32.11.2026 · 21:25:00 · nr. 2"])
def test_missing_or_malformed_daily_number_is_not_replaced_with_a_long_id(label):
    with pytest.raises(ValueError, match="INVALID_SIGNAL_CARD_NUMBER"):
        cards.render_signal_card(event(), label)


def test_bundled_font_has_romanian_glyphs_and_long_values_fit_inside_card():
    font = ImageFont.truetype(str(cards._FONT), size=40)
    replacement = list(font.getmask("\uFFFD"))
    assert all(list(font.getmask(char)) != replacement for char in "ȚĂȘ")
    candidate = event()
    candidate.update(symbol="LONG-SYMBOL/EXAMPLE", entry_price=123456789.123456,
                     open_now_expiry_minutes=123.456789012345)
    picture = Image.open(BytesIO(cards.render_signal_card(candidate, LABEL))).convert("RGB")
    background = ImageColor.getrgb(cards.BACKGROUND)
    for edge in (picture.crop((0, 0, 15, 1320)), picture.crop((1185, 0, 1200, 1320))):
        assert edge.getcolors(edge.width * edge.height) == [(edge.width * edge.height, background)]
