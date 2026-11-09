"""Position within the favorable buffer band, separate from trade settlement.

For entry E and frozen positive width B, the band is [E, E+B] for BUY
and [E-B, E] for SELL. A favorable close strictly inside this band is a
fragile WIN; it is not a LOSS. One quote cannot establish the preceding
path, a return into the band, or any guarantee of a winning trade.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
import math


BUFFER_POSITION_LABELS = {
    "BEYOND_BUFFER": "Dincolo de buffer",
    "AT_BUFFER_EDGE": "La limita favorabilă",
    "INSIDE_BUFFER": "În buffer · câștig fragil",
    "AT_ENTRY": "La intrare · egalitate",
    "LOSS_SIDE": "Dincolo de intrare · pierdere",
    "UNAVAILABLE": "Poziție indisponibilă",
}


def _positive_decimal(value):
    if type(value) not in (int, float) or value <= 0:
        return None
    if type(value) is float and not math.isfinite(value):
        return None
    return Decimal(str(value))


def classify_buffer_position(direction, entry_price, buffer_distance, price):
    """Classify a quote using exact serialized decimals, without tolerances.

    Invalid or missing positive price/width inputs are UNAVAILABLE, never a
    favorable position or a loss. Invalid directions raise ValueError.
    Existing directional and buffer MET/NOT_MET settlement labels are not
    changed by this presentation-level classification.
    """
    if not isinstance(direction, str) or direction not in {"BUY", "SELL"}:
        raise ValueError("INVALID_BUFFER_DIRECTION")
    entry, distance, observed = map(
        _positive_decimal, (entry_price, buffer_distance, price)
    )
    if any(value is None for value in (entry, distance, observed)):
        return "UNAVAILABLE"

    with localcontext() as context:
        # 1100 digits cover the serialized range of finite JSON floats. Also
        # retain exactness for integer inputs with a wider decimal span.
        values = (entry, distance, observed)
        context.prec = max(
            1100,
            max(value.adjusted() for value in values)
            - min(value.as_tuple().exponent for value in values) + 3,
        )
        move = observed - entry if direction == "BUY" else entry - observed
        if move < 0:
            return "LOSS_SIDE"
        if move == 0:
            return "AT_ENTRY"
        if move < distance:
            return "INSIDE_BUFFER"
        if move == distance:
            return "AT_BUFFER_EDGE"
        return "BEYOND_BUFFER"
