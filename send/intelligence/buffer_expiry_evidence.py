"""Versioned buffer-at-expiry label, separate from directional WIN/LOSS/DRAW."""
from __future__ import annotations

from decimal import Decimal, localcontext
import math

CONTRACT = "BUFFER_MET_AT_EXPIRY_V1"
NUMERIC_POLICY = "DECIMAL_SERIALIZED_INPUTS_NO_TOLERANCE_V1"
SOURCE = "ACCEPTED_OPEN_NOW_DECISION_MARKET_CONTEXT"


def snapshot(distance, parameter_sha256):
    reason = None
    if distance is None:
        reason = "BUFFER_DISTANCE_MISSING"
    elif (type(distance) not in (int, float) or not math.isfinite(distance) or distance <= 0):
        reason = "BUFFER_DISTANCE_INVALID"
    return {"contract": CONTRACT, "numeric_policy": NUMERIC_POLICY, "source": SOURCE,
            "parameter_sha256": parameter_sha256,
            "buffer_distance": distance if reason is None else None, "unavailable_reason": reason}


def validate_snapshot(value, parameter_sha256):
    if not isinstance(value, dict):
        raise ValueError("INVALID_BUFFER_SNAPSHOT")
    expected = snapshot(value.get("buffer_distance"), parameter_sha256)
    # Invalid inputs are persisted as null with a reason, never as NaN or zero.
    if value.get("unavailable_reason") == "BUFFER_DISTANCE_INVALID" and value.get("buffer_distance") is None:
        expected["unavailable_reason"] = "BUFFER_DISTANCE_INVALID"
    if value != expected:
        raise ValueError("INVALID_BUFFER_SNAPSHOT")


def measure(direction, entry, expiry, frozen):
    """Compare exact serialized decimals; no epsilon can promote a shortfall."""
    unavailable = {"contract": CONTRACT, "status": "UNAVAILABLE", "buffer_met_at_expiry": None,
                   "directional_move": None, "buffer_coverage": None, "buffer_margin_at_expiry": None}
    if frozen is None:
        return {**unavailable, "reason": "HISTORICAL_BUFFER_UNAVAILABLE"}
    if frozen["buffer_distance"] is None:
        return {**unavailable, "reason": frozen["unavailable_reason"]}
    if entry is None or expiry is None:
        return {**unavailable, "reason": "ELIGIBLE_QUOTES_UNAVAILABLE"}
    if direction not in {"BUY", "SELL"}:
        raise ValueError("INVALID_BUFFER_DIRECTION")
    # Enough precision for exact subtraction of the decimal form of any two
    # finite JSON floats, including small positive buffers. No price rounding.
    with localcontext() as context:
        context.prec = 1100
        move = Decimal(str(expiry["price"])) - Decimal(str(entry["price"]))
        if direction == "SELL":
            move = -move
        distance = Decimal(str(frozen["buffer_distance"]))
        met = move >= distance
        coverage, margin = float(move / distance), float(move - distance)
        # An extreme ratio must not poison JSON persistence/public reporting.
        coverage = coverage if math.isfinite(coverage) else None
        margin = margin if math.isfinite(margin) else None
        return {"contract": CONTRACT, "status": "MET" if met else "NOT_MET", "reason": "OBSERVED_AT_EXPIRY",
                "buffer_met_at_expiry": met, "directional_move": float(move),
                "buffer_coverage": coverage, "buffer_margin_at_expiry": margin}
