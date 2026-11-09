"""Deterministic signal photos; project validated values without trading logic."""

from datetime import datetime
from functools import lru_cache
from io import BytesIO
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


DUBLIN = ZoneInfo("Europe/Dublin")
SIZE = (1200, 1320)
BACKGROUND = "#071125"
TEXT = "#f7f9ff"
MUTED = "#b6bfd1"
INACTIVE = "#26324d"
ACCENTS = {"BUY": "#008c60", "SELL": "#e70028"}
STAGES = ("PRE", "CONFIRM", "OPEN_NOW")
_FONT = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "DejaVuSans-Bold.ttf"
_LABEL = re.compile(r"(\d{2}\.\d{2}\.\d{4}) · (\d{2}:\d{2}:\d{2}) · nr\. (\d{1,9})")


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _instant(value):
    if not _positive(value):
        raise ValueError("INVALID_SIGNAL_CARD_TIMESTAMP")
    try:
        return datetime.fromtimestamp(value, DUBLIN)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("INVALID_SIGNAL_CARD_TIMESTAMP") from exc


def _clock(value):
    moment = _instant(value)
    clock = moment.strftime("%H:%M")
    if moment.second or moment.microsecond:
        clock += moment.strftime(":%S")
    if moment.microsecond:
        clock += f".{moment.microsecond:06d}".rstrip("0")
    return clock


def _number(value):
    return format(value, ".15g")


def build_card_fields(event, signal_label, *, study=False, shadow=False):
    """Validate the display contract without inferring unobserved entry times.

    The ledger's original date/number remains attached to the opportunity even
    if a later stage is issued after midnight. Study duration is an explicitly
    labelled simulation; canonical OPEN can use governed Execution Time only.
    """
    match = _LABEL.fullmatch(signal_label) if isinstance(signal_label, str) else None
    if match is None:
        raise ValueError("INVALID_SIGNAL_CARD_NUMBER")
    date, issued_clock, number = match.groups()
    try:
        datetime.strptime(f"{date} {issued_clock}", "%d.%m.%Y %H:%M:%S")
    except ValueError as exc:
        raise ValueError("INVALID_SIGNAL_CARD_NUMBER") from exc
    stage, direction = event.get("stage"), event.get("direction")
    if stage not in STAGES or direction not in ACCENTS:
        raise ValueError("INVALID_SIGNAL_CARD_STAGE_OR_DIRECTION")
    symbol = event.get("symbol")
    if (not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 40
            or any(ord(char) < 32 for char in symbol)):
        raise ValueError("INVALID_SIGNAL_CARD_SYMBOL")
    price = event.get("entry_price")
    if not _positive(price):
        raise ValueError("INVALID_SIGNAL_CARD_PRICE")
    _instant(event.get("created_ts"))

    duration = "—"
    entry_ts = expiry_ts = None
    if study:
        minutes = event.get("study_duration_minutes")
        entry_ts, expiry_ts = event.get("entry_ts"), event.get("expiry_ts")
        if stage != "OPEN_NOW" or not _positive(minutes):
            raise ValueError("INVALID_SIGNAL_CARD_STUDY_DURATION")
        _instant(entry_ts)
        _instant(expiry_ts)
        if expiry_ts <= entry_ts or not math.isclose(expiry_ts - entry_ts, minutes * 60, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("INCONSISTENT_SIGNAL_CARD_STUDY_EXPIRY")
        duration = f"{_number(minutes)} MIN"
    elif stage == "OPEN_NOW":
        minutes = event.get("open_now_expiry_minutes")
        if event.get("execution_time_available") is not True or not _positive(minutes):
            raise ValueError("OPEN_NOW_REQUIRES_VALIDATED_EXECUTION_TIME")
        entry_ts = event.get("entry_ts", event["created_ts"])
        _instant(entry_ts)
        expiry_ts = entry_ts + minutes * 60
        _instant(expiry_ts)
        if expiry_ts <= entry_ts:
            raise ValueError("INVALID_SIGNAL_CARD_EXPIRY")
        duration = f"{_number(minutes)} MIN"
    elif stage == "CONFIRM" and event.get("execution_time_available") is True:
        low, high = event.get("confirm_expiry_min_minutes"), event.get("confirm_expiry_max_minutes")
        if not _positive(low) or not _positive(high) or low > high:
            raise ValueError("INVALID_SIGNAL_CARD_CONFIRM_INTERVAL")
        duration = f"{_number(low)} MIN" if low == high else f"{_number(low)}–{_number(high)} MIN"

    price_text = _number(price)
    # Preserve the familiar FX precision without truncating more precise input.
    if "e" not in price_text and len(price_text.split(".")[-1]) <= 7 and price < 10:
        price_text = f"{price:.7f}"
    footer = "STUDIU · SIMULARE" if study else "OBSERVARE PRIVATĂ" if shadow else ""
    if stage != "OPEN_NOW":
        footer = " · ".join(filter(None, (footer, "AȘTEAPTĂ OPEN NOW")))
    return {
        "number": f"#{int(number)}", "date": date, "stage": stage,
        "stage_label": stage.replace("_", " "), "direction": direction,
        "symbol": symbol.strip(), "price": price_text, "duration": duration,
        "entry_time": _clock(entry_ts) if entry_ts is not None else "—",
        "expiry_time": _clock(expiry_ts) if expiry_ts is not None else "—",
        "entry_date": _instant(entry_ts).strftime("%d.%m.%Y") if entry_ts is not None else date,
        "expiry_date": _instant(expiry_ts).strftime("%d.%m.%Y") if expiry_ts is not None else date,
        "entry_label": "INTRARE" if study else "REFERINȚĂ",
        "expiry_label": "EXPIRARE" if study or stage != "OPEN_NOW" else "EXPIRARE ESTIMATĂ",
        "price_label": "PREȚ INTRARE" if stage == "OPEN_NOW" else "PREȚ DE REFERINȚĂ",
        "footer": footer, "accent": ACCENTS[direction],
    }


def render_signal_caption(event, signal_label, *, study=False, shadow=False):
    """Compact searchable text alongside the photo; no internal identifiers."""
    fields = build_card_fields(event, signal_label, study=study, shadow=shadow)
    lines = [f"{fields['number']} · {fields['date']} · {fields['stage_label']}",
             f"{fields['symbol']} · {fields['direction']} · {fields['duration']}",
             f"{fields['price_label']}: {fields['price']}"]
    if fields["stage"] == "OPEN_NOW":
        def timed(name):
            date = fields[f"{name}_date"]
            return fields[f"{name}_time"] + (f" ({date})" if date != fields["date"] else "")
        lines.append(f"{fields['entry_label']}: {timed('entry')} · {fields['expiry_label']}: {timed('expiry')} · Dublin")
    if fields["footer"]:
        lines.append(fields["footer"])
    return "\n".join(lines)


@lru_cache(maxsize=96)
def _font(size):
    # The licensed font is deployed with the code; no host/font installation.
    return ImageFont.truetype(str(_FONT), size=size)


def render_signal_card(event, signal_label, *, study=False, shadow=False):
    """Return the approved compact card as PNG bytes, never an AI mock signal."""
    fields = build_card_fields(event, signal_label, study=study, shadow=shadow)
    picture = Image.new("RGB", SIZE, BACKGROUND)
    draw = ImageDraw.Draw(picture)
    accent = fields["accent"]

    def fitted(text, size, width):
        while size > 12:
            font = _font(size)
            if draw.textbbox((0, 0), text, font=font)[2] <= width:
                return font
            size -= 1
        raise ValueError("SIGNAL_CARD_TEXT_TOO_WIDE")

    def label(box, text, size, color=TEXT, align="left"):
        left, top, right, bottom = box
        font = fitted(text, size, right - left)
        bounds = draw.textbbox((0, 0), text, font=font)
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        x = left if align == "left" else right - width if align == "right" else left + (right - left - width) / 2
        draw.text((x - bounds[0], top + (bottom - top - height) / 2 - bounds[1]), text, font=font, fill=color)

    def check(x, y, size, color=TEXT):
        draw.line([(x, y + size * .48), (x + size * .32, y + size * .8),
                   (x + size, y)], fill=color, width=max(5, round(size * .17)), joint="curve")

    def button(box, title, active, size):
        left, top, right, bottom = box
        draw.rounded_rectangle(box, radius=32, fill=accent if active else INACTIVE)
        if active:
            check_size = min(66, (bottom - top) * .38)
            font = fitted(title, size, right - left - check_size - 80)
            bounds = draw.textbbox((0, 0), title, font=font)
            text_width = bounds[2] - bounds[0]
            total = check_size + 24 + text_width
            x = left + (right - left - total) / 2
            check(x, top + (bottom - top - check_size) / 2, check_size)
            label((x + check_size + 24, top, right - 24, bottom), title, font.size)
        else:
            label((left + 18, top, right - 18, bottom), title, size, MUTED, "center")

    draw.rounded_rectangle((56, 36, 292, 151), radius=26, fill=INACTIVE)
    label((74, 44, 274, 143), fields["number"], 98, align="center")
    label((322, 42, 1148, 145), fields["date"], 77, align="right")
    button((42, 184, 1158, 352), fields["stage_label"], True, 114)

    label((58, 400, 686, 523), fields["symbol"], 111)
    draw.line((706, 413, 706, 503), fill=INACTIVE, width=3)
    center_x, center_y = 780, 463
    if fields["direction"] == "SELL":
        arrow = [(center_x - 13, center_y - 39), (center_x + 13, center_y - 39),
                 (center_x + 13, center_y + 5), (center_x + 35, center_y + 5),
                 (center_x, center_y + 41), (center_x - 35, center_y + 5),
                 (center_x - 13, center_y + 5)]
    else:
        arrow = [(center_x - 13, center_y + 39), (center_x + 13, center_y + 39),
                 (center_x + 13, center_y - 5), (center_x + 35, center_y - 5),
                 (center_x, center_y - 41), (center_x - 35, center_y - 5),
                 (center_x - 13, center_y - 5)]
    draw.polygon(arrow, fill=accent)
    label((833, 401, 1158, 524), fields["direction"], 105, accent)

    label((68, 558, 614, 609), fields["price_label"], 39, MUTED)
    label((695, 558, 1140, 609), "DURATĂ", 39, MUTED)
    draw.line((652, 574, 652, 738), fill=INACTIVE, width=3)
    label((65, 625, 617, 741), fields["price"], 104)
    label((693, 625, 1148, 741), fields["duration"], 105)

    draw.line((600, 800, 600, 953), fill=INACTIVE, width=3)
    for name, left, right in (("entry", 64, 568), ("expiry", 633, 1140)):
        label((left, 790, right, 847), fields[f"{name}_label"], 42, MUTED, "center")
        label((left, 856, right, 950), fields[f"{name}_time"], 95, align="center")
        if fields[f"{name}_date"] != fields["date"]:
            label((left, 953, right, 988), fields[f"{name}_date"], 28, MUTED, "center")
    label((64, 990, 1140, 1038), "ORA DUBLIN", 39, MUTED, "center")

    for stage, box in zip(STAGES, ((36, 1071, 317, 1204), (336, 1071, 694, 1204), (713, 1071, 1164, 1204))):
        button(box, stage.replace("_", " "), stage == fields["stage"], 53)
    if fields["footer"]:
        label((46, 1245, 1154, 1294), fields["footer"], 37, MUTED, "center")

    output = BytesIO()
    picture.save(output, format="PNG", optimize=True)
    return output.getvalue()
