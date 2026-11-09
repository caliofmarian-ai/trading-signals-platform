"""Deterministic signal photos; project validated values without trading logic."""

from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from io import BytesIO
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


DUBLIN = ZoneInfo("Europe/Dublin")
SIZE = (1200, 1200)
BACKGROUND = "#071125"
TEXT = "#f7f9ff"
MUTED = "#b6bfd1"
INACTIVE = "#26324d"
DIRECTION_ACCENTS = {"BUY": "#008c60", "SELL": "#e70028"}
# Preparation colors are independent of direction. Only OPEN uses BUY/SELL.
STAGE_ACCENTS = {"PRE": "#c8bd81", "CONFIRM": "#a69abb"}
OPEN_STAGE_ACCENTS = {"BUY": "#3e7565", "SELL": "#945663"}
STAGE_INKS = {"PRE": BACKGROUND, "CONFIRM": BACKGROUND, "OPEN_NOW": TEXT}
STAGES = ("PRE", "CONFIRM", "OPEN_NOW")
STAGE_BANNER = (48, 150, 1152, 320)
NUMBER_BADGE = (70, 174, 320, 296)
STAGE_BUTTONS = ((48, 975, 330, 1087), (346, 975, 724, 1087), (740, 975, 1152, 1087))
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
    clock = moment.strftime("%H:%M:%S")
    if moment.microsecond:
        clock += f".{moment.microsecond:06d}".rstrip("0")
    return clock


def _number(value):
    return format(value, ".15g")


def _duration(minutes, *, seconds=None):
    """Format primary integer seconds, or faithfully convert a legacy duration.

    Never round an expiry here. Only binary representation drift within four
    ULPs (capped at one nanosecond) is normalized at a whole-second boundary.
    """
    if not _positive(minutes):
        raise ValueError("INVALID_SIGNAL_CARD_DURATION")
    if seconds is not None:
        if type(seconds) is not int or seconds <= 0 or minutes != seconds / 60:
            raise ValueError("INCONSISTENT_SIGNAL_CARD_PRIMARY_SECONDS")
        total_seconds = Decimal(seconds)
    else:
        total_seconds = Decimal(str(minutes)) * 60
        nearest = total_seconds.to_integral_value()
        tolerance = min(Decimal(str(4 * math.ulp(float(total_seconds)))), Decimal("0.000000001"))
        if nearest > 0 and abs(total_seconds - nearest) <= tolerance:
            total_seconds = nearest
    whole_minutes, remainder = divmod(total_seconds, 60)
    seconds_text = format(remainder, "f")
    if "." in seconds_text:
        seconds_text = seconds_text.rstrip("0").rstrip(".")
    if remainder < 10:
        seconds_text = "0" + seconds_text
    return f"{int(whole_minutes)} MIN {seconds_text} S"


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
    if stage not in STAGES or direction not in DIRECTION_ACCENTS:
        raise ValueError("INVALID_SIGNAL_CARD_STAGE_OR_DIRECTION")
    symbol = event.get("symbol")
    if (not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 40
            or any(ord(char) < 32 for char in symbol)):
        raise ValueError("INVALID_SIGNAL_CARD_SYMBOL")
    price = event.get("entry_price")
    if not _positive(price):
        raise ValueError("INVALID_SIGNAL_CARD_PRICE")
    issued = _instant(event.get("created_ts"))

    duration = "ÎN CALCUL" if stage == "PRE" else "NEVALIDATĂ"
    entry_ts = expiry_ts = None
    if study:
        minutes = event.get("study_duration_minutes")
        if stage in {"CONFIRM", "OPEN_NOW"} and not _positive(minutes):
            raise ValueError("INVALID_SIGNAL_CARD_STUDY_DURATION")
        if stage in {"CONFIRM", "OPEN_NOW"}:
            duration = _duration(minutes, seconds=event.get("study_duration_seconds"))
        if stage == "OPEN_NOW":
            entry_ts, expiry_ts = event.get("entry_ts"), event.get("expiry_ts")
            _instant(entry_ts)
            _instant(expiry_ts)
            expected_seconds = event.get("study_duration_seconds", minutes * 60)
            if expiry_ts <= entry_ts or not math.isclose(expiry_ts - entry_ts, expected_seconds, rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError("INCONSISTENT_SIGNAL_CARD_STUDY_EXPIRY")
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
        duration = _duration(minutes)
    elif stage == "CONFIRM" and event.get("execution_time_available") is True:
        low, high = event.get("confirm_expiry_min_minutes"), event.get("confirm_expiry_max_minutes")
        if not _positive(low) or not _positive(high) or low > high:
            raise ValueError("INVALID_SIGNAL_CARD_CONFIRM_INTERVAL")
        minutes = event.get("confirm_expiry_minutes")
        if not _positive(minutes) or not low <= minutes <= high:
            raise ValueError("CONFIRM_REQUIRES_EXACT_EXECUTION_TIME")
        duration = _duration(minutes)

    price_text = _number(price)
    # Preserve the familiar FX precision without truncating more precise input.
    if "e" not in price_text and len(price_text.split(".")[-1]) <= 7 and price < 10:
        price_text = f"{price:.7f}"
    mode = "STUDIU · SIMULARE" if study else "OBSERVARE PRIVATĂ" if shadow else ""
    next_action = "AȘTEAPTĂ OPEN NOW" if stage != "OPEN_NOW" else ""
    footer = " · ".join(filter(None, (mode, next_action)))
    opened = stage == "OPEN_NOW"
    return {
        "number": f"#{int(number)}", "date": date, "stage": stage,
        "stage_label": stage.replace("_", " "), "direction": direction,
        "symbol": symbol.strip(), "price": price_text, "duration": duration,
        # The first/second display slots show issuance and the actual next
        # action before OPEN. Neither slot invents a future appointment.
        "entry_time": _clock(entry_ts) if opened else _clock(event["created_ts"]),
        "expiry_time": _clock(expiry_ts) if opened else "LA OPEN NOW",
        "entry_date": _instant(entry_ts).strftime("%d.%m.%Y") if opened else issued.strftime("%d.%m.%Y"),
        "expiry_date": _instant(expiry_ts).strftime("%d.%m.%Y") if opened else None,
        "entry_label": "MOMENT DESCHIDERE" if opened else "EMIS",
        "expiry_label": ("EXPIRARE" if study else "EXPIRARE ESTIMATĂ") if opened else "INTRARE",
        "price_label": "PREȚ INTRARE" if stage == "OPEN_NOW" else "PREȚ DE REFERINȚĂ",
        "duration_label": "DURATĂ STUDIU" if study else "DURATĂ",
        "footer": footer, "mode": mode, "next_action": next_action,
        "stage_accent": OPEN_STAGE_ACCENTS[direction] if opened else STAGE_ACCENTS[stage],
        "stage_ink": STAGE_INKS[stage],
        "direction_accent": DIRECTION_ACCENTS[direction],
    }


def render_signal_caption(event, signal_label, *, study=False, shadow=False):
    """Two searchable lines; values already readable in the photo stay there."""
    fields = build_card_fields(event, signal_label, study=study, shadow=shadow)
    context = " · ".join(filter(None, (fields["symbol"], fields["direction"], fields["mode"])))
    return f"{fields['number']} · {fields['date']} · {fields['stage_label']}\n{context}"


def render_signal_text(event, signal_label, *, study=False, shadow=False):
    """Complete truthful fallback if image rendering fails before transport."""
    fields = build_card_fields(event, signal_label, study=study, shadow=shadow)
    lines = [f"{fields['number']} · {fields['date']} · {fields['stage_label']}",
             f"{fields['symbol']} · {fields['direction']} · {fields['duration']}",
             f"{fields['price_label']}: {fields['price']}"]
    def timed(name):
        date = fields[f"{name}_date"]
        return fields[f"{name}_time"] + (f" ({date})" if date and date != fields["date"] else "")
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
    stage_accent, stage_ink = fields["stage_accent"], fields["stage_ink"]
    direction_accent = fields["direction_accent"]

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
        draw.rounded_rectangle(box, radius=26, fill=stage_accent if active else INACTIVE)
        if active:
            check_size = min(66, (bottom - top) * .38)
            font = fitted(title, size, right - left - check_size - 80)
            bounds = draw.textbbox((0, 0), title, font=font)
            text_width = bounds[2] - bounds[0]
            total = check_size + 24 + text_width
            x = left + (right - left - total) / 2
            check(x, top + (bottom - top - check_size) / 2, check_size, stage_ink)
            label((x + check_size + 24, top, right - 24, bottom), title, font.size, stage_ink)
        else:
            label((left + 18, top, right - 18, bottom), title, size, MUTED, "center")

    # A square, inset composition keeps the identifier within the main banner
    # rather than at the easily clipped upper edge of a chat thumbnail.
    label((64, 62, 1140, 120), fields["date"], 58, MUTED, "center")
    draw.rounded_rectangle(STAGE_BANNER, radius=28, fill=stage_accent)
    draw.rounded_rectangle(NUMBER_BADGE, radius=22, fill=BACKGROUND)
    label((82, 180, 308, 290), fields["number"], 105, TEXT, "center")
    button((338, 164, 1132, 306), fields["stage_label"], True, 95)

    label((58, 358, 686, 478), fields["symbol"], 111)
    draw.line((706, 369, 706, 459), fill=INACTIVE, width=3)
    center_x, center_y = 780, 419
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
    draw.polygon(arrow, fill=direction_accent)
    label((833, 359, 1158, 479), fields["direction"], 105, direction_accent)

    label((68, 517, 614, 565), fields["price_label"], 39, MUTED)
    label((680, 517, 1140, 565), fields["duration_label"], 39, MUTED)
    draw.line((652, 526, 652, 686), fill=INACTIVE, width=3)
    label((65, 583, 617, 697), fields["price"], 104)
    label((678, 583, 1148, 697), fields["duration"], 105)

    draw.line((600, 742, 600, 891), fill=INACTIVE, width=3)
    for name, left, right in (("entry", 64, 568), ("expiry", 633, 1140)):
        label((left, 728, right, 780), fields[f"{name}_label"], 42, MUTED, "center")
        label((left, 790, right, 877), fields[f"{name}_time"], 95, align="center")
        if fields[f"{name}_date"] and fields[f"{name}_date"] != fields["date"]:
            label((left, 881, right, 913), fields[f"{name}_date"], 28, MUTED, "center")
    label((64, 922, 1140, 958), "ORA DUBLIN", 34, MUTED, "center")

    for stage, box in zip(STAGES, STAGE_BUTTONS):
        button(box, stage.replace("_", " "), stage == fields["stage"], 53)
    if fields["mode"]:
        label((48, 1117, 1152, 1164), fields["mode"], 35, MUTED, "center")

    output = BytesIO()
    picture.save(output, format="PNG", optimize=True)
    return output.getvalue()
