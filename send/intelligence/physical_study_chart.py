"""Render a settled, hypothetical V3 trade without manufacturing market data."""

from datetime import datetime, timezone
from decimal import Decimal, localcontext
from functools import lru_cache
from io import BytesIO
import math
import unicodedata

from PIL import Image, ImageDraw, ImageFont


_UP = "#48d3a2"
_DOWN = "#ff8591"
_ENTRY = "#8bbcff"
_BUFFER = "#f4c871"
_TEXT = "#eff5fc"
_MUTED = "#a3b4ca"
_STUDY_TITLE = "OPEN NOW  /  STUDIU V3"
_ENTRY_LABEL = "PREȚ INTRARE"
_EXPIRY_OBSERVATION_LABEL = "COTAȚIE PENTRU EXPIRARE"


@lru_cache(maxsize=8)
def _font(size):
    return ImageFont.load_default(size=size)


def _time(stamp, *, milliseconds=False):
    observed = datetime.fromtimestamp(stamp, timezone.utc)
    return observed.isoformat(timespec="milliseconds")[11:23] if milliseconds else observed.strftime("%H:%M:%S")


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _bars_in_trade(candles, entry_ts, expiry_ts):
    bars = {}
    for candle in candles:
        stamp = candle.get("ts")
        prices = tuple(candle.get(key) for key in ("open", "high", "low", "close"))
        if (not _positive(stamp) or not entry_ts <= stamp <= expiry_ts - 60
            or candle.get("complete") is False or not all(map(_positive, prices))):
            continue
        opened, high, low, close = prices
        if low <= min(opened, close) <= max(opened, close) <= high:
            bars[stamp] = prices
    return sorted(bars.items())


def render_trade_chart(*, candles, direction, entry_ts, entry_price, expiry_ts,
                       expiry_quote_ts, expiry_price, buffer_distance, outcome,
                       first_buffer_hit=None, report_title=_STUDY_TITLE,
                       entry_label=_ENTRY_LABEL, signal_label: str | None = None,
                       expiry_observation_label=_EXPIRY_OBSERVATION_LABEL):
    """Return a PNG from observed M1 bars and optional observed quote evidence.

    Only whole M1 intervals inside the study are eligible. A genuine buffer
    tick carries its recorded time, whereas a candle proves an interval only.
    """
    if direction not in {"BUY", "SELL"} or not all(map(_positive, (entry_ts, entry_price, expiry_ts))) or expiry_ts <= entry_ts:
        raise ValueError("Invalid study chart entry or expiry")
    if expiry_price is not None and (not _positive(expiry_price) or not _positive(expiry_quote_ts) or expiry_quote_ts < expiry_ts):
        raise ValueError("Invalid study chart expiry observation")
    bars = _bars_in_trade(candles, entry_ts, expiry_ts)
    sign = 1 if direction == "BUY" else -1
    with localcontext() as context:
        context.prec = 1100
        threshold = Decimal(str(entry_price)) + sign * Decimal(str(buffer_distance)) if _positive(buffer_distance) else None

    def in_buffer(price):
        return threshold is not None and (Decimal(str(price)) >= threshold if sign == 1 else Decimal(str(price)) <= threshold)

    hit_ts = hit_price = None
    if first_buffer_hit is not None:
        stamp, price = first_buffer_hit.get("observed_ts"), first_buffer_hit.get("price")
        if _positive(stamp) and entry_ts <= stamp <= expiry_ts and _positive(price) and in_buffer(price):
            hit_ts, hit_price = stamp, price
    hit_bar = next((stamp for stamp, (_, high, low, _) in bars
                    if stamp > entry_ts and in_buffer(high if sign == 1 else low)), None)

    image = Image.new("RGB", (1200, 800), "#0d1725")
    draw = ImageDraw.Draw(image)

    def label(x, y, value, *, color=_TEXT, size=23, anchor=None):
        # The bundled font is portable, but omits some Romanian accents.
        readable = "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c))
        draw.text((x, y), readable, fill=color, font=_font(size), anchor=anchor)

    def dashed(start, end, color):
        x1, y1 = start
        x2, y2 = end
        if y1 == y2:
            for x in range(x1, x2, 13):
                draw.line((x, y1, min(x + 7, x2), y1), fill=color, width=2)
        else:
            for y in range(y1, y2, 13):
                draw.line((x1, y, x1, min(y + 7, y2)), fill=color, width=2)

    outcome_label, outcome_color = {
        "WIN": ("WIN · Câștig", _UP), "LOSS": ("LOSS · Pierdere", _DOWN),
        "DRAW": ("DRAW · Egal", _ENTRY), "UNKNOWN": ("UNKNOWN · Date lipsă", _BUFFER),
    }.get(outcome, ("Verdict indisponibil", _MUTED))
    label(48, 29, report_title, color=_ENTRY, size=22)
    label(48, 61, f"EUR/USD  ·  {direction}", size=49)
    label(1152, 73, outcome_label, color=outcome_color, size=29, anchor="ra")
    date_label = (f"{signal_label}  ·  Dublin" if signal_label else
                  datetime.fromtimestamp(entry_ts, timezone.utc).strftime("%d.%m.%Y  ·  UTC"))
    label(1152, 36, date_label, color=_MUTED, size=20, anchor="ra")

    def price_label(value):
        return f"{value:.7f}" if value is not None else "—"

    left, right, top, bottom = 57, 1054, 218, 586
    for x, heading, value, color in (
        (48, entry_label, price_label(entry_price), _ENTRY),
        (340, "PRAG BUFFER", price_label(threshold), _BUFFER),
        (625, expiry_observation_label, price_label(expiry_price), _TEXT),
        (972, "EXPIRARE UTC", _time(expiry_ts), _TEXT),
    ):
        label(x, 133, heading, color=_MUTED, size=16)
        label(x, 155, value, color=color, size=31)

    points = [entry_price, *(p for _, bar in bars for p in bar)]
    points.extend(float(p) for p in (threshold, expiry_price, hit_price) if p is not None)
    low, high = min(points), max(points)
    margin = max((high - low) * 0.14, entry_price * 0.000005)
    low, high = low - margin, high + margin
    x_margin = (expiry_ts - entry_ts) * 0.035
    start, end = entry_ts - x_margin, max(expiry_ts, expiry_quote_ts or expiry_ts) + x_margin

    def x_at(stamp):
        return round(left + (stamp - start) / (end - start) * (right - left))

    def y_at(price):
        return round(bottom - (float(price) - low) / (high - low) * (bottom - top))

    draw.rectangle((left, top, right, bottom), fill="#132237")
    if threshold is not None:
        boundary = y_at(threshold)
        shade_start, shade_end = (top, boundary) if sign == 1 else (boundary, bottom)
        draw.rectangle((left, shade_start, right, shade_end), fill="#253831")
    for step in range(6):
        value = low + step * (high - low) / 5
        y = y_at(value)
        draw.line((left, y, right, y), fill="#31435a")
        label(right + 9, y, f"{value:.6f}", color=_MUTED, size=16, anchor="lm")
    for step in range(5):
        stamp = entry_ts + step * (expiry_ts - entry_ts) / 4
        x = x_at(stamp)
        draw.line((x, top, x, bottom), fill="#31435a")
        label(x, bottom + 12, _time(stamp), color=_MUTED, size=17, anchor="ma")

    dashed((left, y_at(entry_price)), (right, y_at(entry_price)), _ENTRY)
    if threshold is not None:
        dashed((left, boundary), (right, boundary), _BUFFER)
    dashed((x_at(expiry_ts), top), (x_at(expiry_ts), bottom), _TEXT)

    half_width = max(2, min(15, (x_at(entry_ts + 60) - x_at(entry_ts)) // 4))
    for stamp, (opened, high_price, low_price, close) in bars:
        x = x_at(stamp + 30)
        candle_color = _UP if close >= opened else _DOWN
        draw.line((x, y_at(high_price), x, y_at(low_price)), fill=candle_color, width=2)
        body_top, body_bottom = sorted((y_at(opened), y_at(close)))
        draw.rectangle((x - half_width, body_top, x + half_width, max(body_top + 2, body_bottom)), fill=candle_color)

    def marker(stamp, price, color, radius):
        x, y = x_at(stamp), y_at(price)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline="#0d1725", width=2)

    marker(entry_ts, entry_price, _ENTRY, 7)
    if expiry_price is not None:
        marker(expiry_quote_ts, expiry_price, _TEXT, 7)
    earlier_candle = hit_bar is not None and hit_ts is not None and hit_bar + 60 <= hit_ts
    if hit_bar is not None and (hit_ts is None or earlier_candle):
        draw.rectangle((x_at(hit_bar), top, x_at(hit_bar + 60), bottom), outline=_BUFFER, width=2)
    if hit_ts is not None:
        marker(hit_ts, hit_price, _BUFFER, 9)
        hit_description = f"Prima atingere observată în cotații  ·  {_time(hit_ts, milliseconds=hit_ts % 1 != 0)} UTC  ·  {price_label(hit_price)}"
    elif hit_bar is not None:
        hit_description = f"Atingere observată în lumânarea {_time(hit_bar)}–{_time(hit_bar + 60)} UTC  ·  secunda este necunoscută"
    else:
        hit_description = "Atingerea bufferului în interval nu este confirmată."

    label(48, 632, hit_description, color=_BUFFER, size=23)
    expiry_status = "DATE LIPSĂ" if threshold is None or expiry_price is None else ("ATINS" if in_buffer(expiry_price) else "NEATINS")
    quote_time = f" la {_time(expiry_quote_ts)} UTC" if expiry_price is not None else ""
    label(48, 665, f"Buffer la cotația observată  ·  {expiry_status}{quote_time}", color=_TEXT, size=22)
    if earlier_candle:
        label(48, 692, f"Lumânarea {_time(hit_bar)}–{_time(hit_bar + 60)} UTC arată o atingere mai devreme, la o secundă necunoscută.", color=_BUFFER, size=18)
    bar_description = ("Lumânări M1 complete în intervalul urmărit. Spațiile goale nu au cotații M1 complete."
                       if bars else "Nicio lumânare M1 completă în intervalul urmărit. Punctele arată cotațiile disponibile.")
    label(48, 716, bar_description, color=_MUTED, size=19)
    legend = "Linie albastră  ·  Preț inițial     |     Linie albă  ·  Expirare programată"
    if threshold is not None:
        legend = "Zonă verde  ·  Buffer atins     |     " + legend
    label(48, 747, legend, color=_MUTED, size=18)

    png = BytesIO()
    image.save(png, format="PNG", optimize=True)
    return png.getvalue()


def render_market_chart(*, direction, entry_ts, entry_price, expiry_ts,
                        expiry_quote_ts, expiry_price, buffer_distance, outcome,
                        report_title=_STUDY_TITLE, entry_label=_ENTRY_LABEL,
                        signal_label: str | None = None,
                        expiry_observation_label=_EXPIRY_OBSERVATION_LABEL):
    """Render a report from the Finnhub process's retained market observations."""
    from intelligence import buffer_expiry_evidence
    from runtime import market_client

    candles, ticks = market_client.get_finnhub_study_chart_evidence(entry_ts, expiry_ts)
    first_hit = None
    if _positive(buffer_distance):
        entry = {"price": entry_price}
        frozen = {"buffer_distance": buffer_distance}
        first_hit = next((tick for tick in ticks
                          if buffer_expiry_evidence.measure(direction, entry, tick, frozen)["buffer_met_at_expiry"]), None)
    return render_trade_chart(candles=candles, direction=direction, entry_ts=entry_ts,
        entry_price=entry_price, expiry_ts=expiry_ts, expiry_quote_ts=expiry_quote_ts,
        expiry_price=expiry_price, buffer_distance=buffer_distance, outcome=outcome,
        first_buffer_hit=first_hit, report_title=report_title, entry_label=entry_label,
        signal_label=signal_label, expiry_observation_label=expiry_observation_label)
