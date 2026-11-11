"""Render a settled, hypothetical V3 trade without manufacturing market data."""

from datetime import datetime, timezone
from decimal import Decimal, localcontext
from functools import lru_cache
from io import BytesIO
import math
import unicodedata

from PIL import Image, ImageDraw, ImageFont

from core.buffer_zone import BUFFER_POSITION_LABELS, classify_buffer_position
from intelligence.observation_issue_presentation import collection_issue_label


_UP = "#48d3a2"
_DOWN = "#ff8591"
_ENTRY = "#8bbcff"
_BUFFER = "#f4c871"
_BUFFER_BAND = "#3d3425"
_TEXT = "#eff5fc"
_MUTED = "#a3b4ca"
_STUDY_TITLE = "REZULTAT  /  STUDIU V3"
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
                       expiry_observation_label=_EXPIRY_OBSERVATION_LABEL,
                       expiry_estimate=None, observation_reason=None):
    """Return a PNG from observed M1 bars and optional observed quote evidence.

    The buffer is the favorable price band anchored at entry, not the region
    beyond its outer edge. Only whole M1 intervals inside the study are eligible.
    An observed favorable-edge tick carries its recorded time, whereas a candle
    proves an interval only. Neither proves the absence of later re-entry.
    """
    if direction not in {"BUY", "SELL"} or not all(map(_positive, (entry_ts, entry_price, expiry_ts))) or expiry_ts <= entry_ts:
        raise ValueError("Invalid study chart entry or expiry")
    if expiry_price is not None and (not _positive(expiry_price) or not _positive(expiry_quote_ts) or expiry_quote_ts < expiry_ts):
        raise ValueError("Invalid study chart expiry observation")
    if expiry_estimate is not None:
        from intelligence.expiry_price_estimate import validate_estimate
        if outcome != "UNKNOWN" or expiry_price is not None:
            expiry_estimate = None
        else:
            try:
                validate_estimate(expiry_estimate, direction=direction,
                                 entry={"price": entry_price, "observed_ts": entry_ts}, expiry_ts=expiry_ts)
            except (TypeError, ValueError, KeyError):
                expiry_estimate = None
    bars = _bars_in_trade(candles, entry_ts, expiry_ts)
    sign = 1 if direction == "BUY" else -1
    with localcontext() as context:
        context.prec = 1100
        threshold = Decimal(str(entry_price)) + sign * Decimal(str(buffer_distance)) if _positive(buffer_distance) else None

    def at_or_beyond_buffer_edge(price):
        return threshold is not None and (Decimal(str(price)) >= threshold if sign == 1 else Decimal(str(price)) <= threshold)

    expiry_position = classify_buffer_position(direction, entry_price, buffer_distance, expiry_price)

    hit_ts = hit_price = None
    if first_buffer_hit is not None:
        stamp, price = first_buffer_hit.get("observed_ts"), first_buffer_hit.get("price")
        if _positive(stamp) and entry_ts <= stamp <= expiry_ts and _positive(price) and at_or_beyond_buffer_edge(price):
            hit_ts, hit_price = stamp, price
    hit_bar = next((stamp for stamp, (_, high, low, _) in bars
                    if at_or_beyond_buffer_edge(high if sign == 1 else low)), None)

    image = Image.new("RGB", (1200, 1200 if expiry_estimate is not None else 940), "#0d1725")
    draw = ImageDraw.Draw(image)

    def label(x, y, value, *, color=_TEXT, size=23, anchor=None, max_width=None):
        # The bundled font is portable, but omits some Romanian accents.
        readable = "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c))
        if max_width is not None:
            while size > 18 and draw.textbbox((0, 0), readable, font=_font(size))[2] > max_width:
                size -= 1
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
        "DRAW": ("DRAW · Egal", _ENTRY),
    }.get(outcome, ("Verdict indisponibil", _MUTED))
    if outcome == "UNKNOWN":
        outcome_label, outcome_color = collection_issue_label(observation_reason), _BUFFER
    estimate_labels = {"WIN": "WIN estimat", "LOSS": "LOSS estimat",
                       "INCONCLUSIVE": "Estimare neconcludentă", "UNAVAILABLE": "Estimare indisponibilă"}
    if expiry_estimate is not None:
        outcome_label = estimate_labels[expiry_estimate["estimated_outcome"]]
        outcome_color = _BUFFER
    label(48, 29, report_title, color=_ENTRY, size=22)
    label(48, 61, f"EUR/USD  ·  {direction}", size=49)
    label(1152, 73, outcome_label, color=outcome_color, size=29, anchor="ra", max_width=650)
    date_label = (f"{signal_label}  ·  Dublin" if signal_label else
                  datetime.fromtimestamp(entry_ts, timezone.utc).strftime("%d.%m.%Y  ·  UTC"))
    label(1152, 36, date_label, color=_MUTED, size=20, anchor="ra")

    def price_label(value, *, boundary=False):
        if value is None:
            return "LIPSĂ"
        # Preserve the actual serialized quote. Fixed precision can display
        # equal prices for a small real WIN/LOSS or a buffer-edge shortfall.
        decimal = Decimal(str(value))
        if -7 <= decimal.adjusted() <= 7:
            text = format(decimal, "f") if decimal.as_tuple().exponent < -7 else format(decimal, ".7f")
        else:
            text = str(decimal)
        # A computed exact boundary can have hundreds of places when B is
        # tiny. Bound only this reference label, with explicit approximation;
        # observed entry/expiry prices above retain their serialized precision.
        return "~" + format(decimal, ".17g") if boundary and len(text) > 22 else text

    def observation_time(stamp):
        return _time(stamp, milliseconds=stamp % 1 != 0)

    left, right, top, bottom = 57, 1054, 218, 586
    boundary_text = price_label(threshold, boundary=True)
    boundary_heading = "LIMITĂ BUFFER (~ = aprox.)" if boundary_text.startswith("~") else "LIMITĂ BUFFER · REPER"
    for x, heading, value, color, width in (
        (48, entry_label + " · REPER", price_label(entry_price), _ENTRY, 270),
        (340, boundary_heading, boundary_text, _BUFFER, 263),
        (625, expiry_observation_label, price_label(expiry_price), _TEXT if expiry_price is not None else _BUFFER, 325),
        (972, "EXPIRARE UTC", observation_time(expiry_ts), _TEXT, 180),
    ):
        label(x, 133, heading, color=_MUTED, size=16)
        label(x, 155, value, color=color, size=31, max_width=width)

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
        shade_start, shade_end = sorted((y_at(entry_price), boundary))
        draw.rectangle((left, shade_start, right, shade_end), fill=_BUFFER_BAND)
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
        hit_description = f"Limită buffer atinsă în cotație  ·  {_time(hit_ts, milliseconds=hit_ts % 1 != 0)} UTC  ·  {price_label(hit_price)}"
    elif hit_bar is not None:
        hit_description = f"Limită buffer atinsă în lumânarea {_time(hit_bar)}-{_time(hit_bar + 60)} UTC  ·  secunda necunoscută"
    else:
        hit_description = "Atingerea limitei favorabile în interval nu este confirmată."

    if expiry_price is not None:
        comparator = ">" if expiry_price > entry_price else "<" if expiry_price < entry_price else "="
        comparison = (f"Comparație {direction}: expirare {price_label(expiry_price)} "
                      f"{comparator} intrare {price_label(entry_price)}  |  {outcome}")
        label(48, 632, comparison, color=_TEXT, size=23, max_width=1104)
    else:
        missing_label = ("Cotația exactă lipsește; estimarea din cotațiile vecine este prezentată separat."
                         if expiry_estimate is not None else
                         "Verdictul de piață nu poate fi calculat fără cotația de expirare.")
        label(48, 632, missing_label, color=_BUFFER, size=23, max_width=1104)

    expiry_status = BUFFER_POSITION_LABELS[expiry_position]
    complete_margin = ("DA" if expiry_position in {"AT_BUFFER_EDGE", "BEYOND_BUFFER"} else
                       "NU" if expiry_position in {"INSIDE_BUFFER", "AT_ENTRY", "LOSS_SIDE"} else
                       "indisponibilă")
    position_text = f"Poziție: {expiry_status}  |  Marjă completă la expirare: {complete_margin}"
    if expiry_price is None:
        position_text = "Poziția în buffer nu poate fi stabilită fără cotația de expirare."
    elif expiry_position == "UNAVAILABLE":
        position_text = "Limita bufferului este indisponibilă; poziția și marja nu pot fi calculate."
    label(48, 669, position_text,
          color=_BUFFER if expiry_position == "INSIDE_BUFFER" else _TEXT, size=21, max_width=1104)
    expiry_evidence = (f"1/1, la {observation_time(expiry_quote_ts)} UTC"
                       if expiry_price is not None else "0/1 · LIPSĂ")
    label(48, 706, f"Cotații pentru verdict: intrare 1/1  |  expirare {expiry_evidence}",
          color=_TEXT if expiry_price is not None else _BUFFER, size=21, max_width=1104)

    if bars:
        last_bar = bars[-1][0]
        bar_description = (f"Context M1: {len(bars)} complete  |  ultima: {_time(last_bar)}-{_time(last_bar + 60)}"
                           f"  |  expirare: {observation_time(expiry_ts)} UTC")
    else:
        bar_description = "Context M1: 0 lumânări complete în intervalul urmărit."
    label(48, 743, bar_description, color=_MUTED, size=21, max_width=1104)
    label(48, 780, hit_description, color=_BUFFER, size=20, max_width=1104)
    if earlier_candle:
        label(48, 812, f"Contact anterior în M1 {_time(hit_bar)}-{_time(hit_bar + 60)} UTC; secunda nu este cunoscută.",
              color=_BUFFER, size=19, max_width=1104)
    label(48, 845, "Lumânările și atingerea limitei sunt context; nu înlocuiesc cotația pentru expirare.",
          color=_MUTED, size=20, max_width=1104)
    legend = "Orizontale: albastru = intrare, galben = limită buffer (repere). Alb vertical = ora expirării."
    label(48, 876, legend, color=_MUTED, size=19, max_width=1104)
    legend = "Puncte: intrare, expirare și contact confirmat, când sunt disponibile."
    if threshold is not None:
        legend = "Bandă galbenă · Buffer lângă intrare  |  Puncte: intrare, expirare și contact confirmat."
    label(48, 907, legend, color=_MUTED, size=18, max_width=1104)

    if expiry_estimate is not None:
        # Neighbor prices are an auxiliary estimate, never an expiry marker,
        # an interpolated candle or a guaranteed band on the observed chart.
        draw.rounded_rectangle((32, 949, 1168, 1180), radius=14, fill="#253044", outline=_BUFFER)
        label(48, 966, "COTAȚII VECINE · ESTIMARE SEPARATĂ", color=_BUFFER, size=23)
        for y, name, quote in ((1003, "Înainte", expiry_estimate["before"]),
                               (1036, "După", expiry_estimate["after"])):
            if quote is None:
                description = f"{name}: lipsă în limita de 60s de la expirare."
            else:
                provenance = "arhivă" if quote["source"].startswith("DURABLE_") else "flux"
                description = f"{name}: {price_label(quote['price'])} · {observation_time(quote['observed_ts'])} UTC · Finnhub {provenance}"
            label(48, y, description, color=_TEXT, size=21, max_width=1104)
        if expiry_estimate["lower_price"] is not None:
            description = (f"Interval orientativ: {price_label(expiry_estimate['lower_price'])} - "
                           f"{price_label(expiry_estimate['upper_price'])}  |  gol: {expiry_estimate['gap_seconds']:g}s")
        else:
            description = "Interval orientativ indisponibil: sunt necesare ambele cotații vecine."
        label(48, 1069, description, color=_BUFFER, size=22, max_width=1104)
        label(48, 1107, "Prețul dintre observații poate ieși din interval; închiderea exactă nu este confirmată.",
              color=_MUTED, size=21, max_width=1104)
        issue = collection_issue_label("EXPIRY_OBSERVATION_MISSING")
        label(48, 1143, f"{issue}. Estimarea este exclusă din rata WIN verificată.",
              color=_MUTED, size=20, max_width=1104)

    png = BytesIO()
    image.save(png, format="PNG", optimize=True)
    return png.getvalue()


def render_market_chart(*, direction, entry_ts, entry_price, expiry_ts,
                        expiry_quote_ts, expiry_price, buffer_distance, outcome,
                        report_title=_STUDY_TITLE, entry_label=_ENTRY_LABEL,
                        signal_label: str | None = None,
                        expiry_observation_label=_EXPIRY_OBSERVATION_LABEL,
                        expiry_estimate=None, observation_reason=None):
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
        signal_label=signal_label, expiry_observation_label=expiry_observation_label,
        expiry_estimate=expiry_estimate, observation_reason=observation_reason)

