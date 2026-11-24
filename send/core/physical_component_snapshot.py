"""Scoreless V3 physical-component snapshots for prospective CONFIRM/OPEN diagnosis.

Only derived distances, speeds, ratios and canonical state labels are retained.
Raw prices, quote samples, support/resistance levels, signal IDs and score fields
are deliberately excluded.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import isclose, isfinite
from typing import Any, Mapping

PROTOCOL = "V3_PHYSICAL_COMPONENT_SNAPSHOT_V1"

_NUMERIC_RULES = {
    "directional_effective_speed": "nonnegative",
    "weighted_gross_speed": "nonnegative",
    "flow_efficiency": "unit",
    "buffer_distance": "positive",
    "available_distance": "nonnegative",
    "corridor_width": "nonnegative",
    "t_needed_seconds": "positive",
    "t_needed_adjusted_seconds": "positive",
    "model_expiry_seconds": "positive",
    "model_time_reach_ratio": "nonnegative",
    "time_to_buffer_ratio": "nonnegative",
    "adjustment_multiplier": "positive",
    "space_to_buffer_ratio": "nonnegative",
    "trade_space_margin_atr": "signed",
    "atr_speed_reference": "nonnegative",
    "directional_speed_ratio": "nonnegative",
    "movement_stress": "nonnegative",
    "time_identity_residual_seconds": "signed",
}
_TEXT_FIELDS = (
    "trend_context",
    "volatility_state",
    "noise_context",
    "structure_state",
    "time_state",
    "trade_physics_readiness",
)
_KEYS = frozenset({
    "protocol", "evaluated_ts", *_NUMERIC_RULES, *_TEXT_FIELDS,
})


def _optional_seconds(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError(f"INVALID_PHYSICAL_COMPONENT:{field}")
    return float(value) * 60.0


def validate(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, Mapping) or set(snapshot) != _KEYS:
        raise ValueError("INVALID_PHYSICAL_COMPONENT_SNAPSHOT")
    if snapshot.get("protocol") != PROTOCOL:
        raise ValueError("UNKNOWN_PHYSICAL_COMPONENT_PROTOCOL")
    stamp = snapshot.get("evaluated_ts")
    if type(stamp) is not int or stamp <= 0:
        raise ValueError("INVALID_PHYSICAL_COMPONENT_TIMESTAMP")

    normalized = dict(snapshot)
    for field, rule in _NUMERIC_RULES.items():
        value = snapshot[field]
        if value is None:
            continue
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError(f"INVALID_PHYSICAL_COMPONENT:{field}")
        value = float(value)
        if rule == "positive" and value <= 0:
            raise ValueError(f"INVALID_PHYSICAL_COMPONENT:{field}")
        if rule == "nonnegative" and value < 0:
            raise ValueError(f"INVALID_PHYSICAL_COMPONENT:{field}")
        if rule == "unit" and not 0 <= value <= 1:
            raise ValueError(f"INVALID_PHYSICAL_COMPONENT:{field}")
        normalized[field] = value

    for field in _TEXT_FIELDS:
        value = snapshot[field]
        if value is not None and (
            not isinstance(value, str) or not value.strip() or len(value) > 64
        ):
            raise ValueError(f"INVALID_PHYSICAL_COMPONENT:{field}")
        normalized[field] = value.strip() if isinstance(value, str) else None

    speed = normalized["directional_effective_speed"]
    buffer = normalized["buffer_distance"]
    needed = normalized["t_needed_seconds"]
    if speed is not None and speed > 0 and buffer is not None and needed is not None:
        expected = buffer / speed * 60.0
        residual = normalized["time_identity_residual_seconds"]
        if residual is None or not isclose(
            residual, needed - expected, rel_tol=1e-12, abs_tol=1e-9
        ):
            raise ValueError("PHYSICAL_COMPONENT_TIME_RESIDUAL_MISMATCH")
    elif normalized["time_identity_residual_seconds"] is not None:
        raise ValueError("PHYSICAL_COMPONENT_TIME_RESIDUAL_WITHOUT_INPUTS")

    adjusted = normalized["t_needed_adjusted_seconds"]
    multiplier = normalized["adjustment_multiplier"]
    if needed is not None and needed > 0 and adjusted is not None and multiplier is not None:
        if not isclose(multiplier, adjusted / needed, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("PHYSICAL_COMPONENT_ADJUSTMENT_IDENTITY_MISMATCH")

    gross = normalized["weighted_gross_speed"]
    efficiency = normalized["flow_efficiency"]
    if speed is not None and gross is not None and gross > 0 and efficiency is not None:
        if not isclose(efficiency, speed / gross, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("PHYSICAL_COMPONENT_FLOW_IDENTITY_MISMATCH")

    available = normalized["available_distance"]
    room_ratio = normalized["space_to_buffer_ratio"]
    if available is not None and buffer is not None and buffer > 0 and room_ratio is not None:
        if not isclose(room_ratio, available / buffer, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("PHYSICAL_COMPONENT_ROOM_IDENTITY_MISMATCH")

    model = normalized["model_expiry_seconds"]
    reach = normalized["model_time_reach_ratio"]
    time_ratio = normalized["time_to_buffer_ratio"]
    if adjusted is not None and adjusted > 0 and model is not None and model > 0:
        if reach is not None and not isclose(reach, adjusted / model, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("PHYSICAL_COMPONENT_MODEL_REACH_IDENTITY_MISMATCH")
        if time_ratio is not None and not isclose(time_ratio, model / adjusted, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("PHYSICAL_COMPONENT_TIME_BUFFER_IDENTITY_MISMATCH")
    return normalized


def from_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any] | None:
    """Project a V3 DecisionObject dictionary without copying prices or identities."""
    if not isinstance(snapshot, Mapping) or snapshot.get("decision_policy") != "PHYSICAL_ONLY_V3":
        return None
    market = snapshot.get("market_context")
    structure = snapshot.get("structure")
    timing = snapshot.get("time")
    physics = snapshot.get("trade_physics")
    if not all(isinstance(item, Mapping) for item in (market, structure, timing)):
        return None
    physics = physics if isinstance(physics, Mapping) else {}

    t_needed = _optional_seconds(timing.get("t_needed"), "t_needed")
    adjusted = _optional_seconds(timing.get("t_needed_adjusted"), "t_needed_adjusted")
    model_expiry = _optional_seconds(timing.get("model_expiry"), "model_expiry")
    buffer_distance = market.get("buffer_distance")
    available_distance = structure.get("available_distance")
    room_ratio = physics.get("space_to_buffer_ratio")
    if room_ratio is None and type(buffer_distance) in (int, float) and buffer_distance > 0:
        if type(available_distance) in (int, float) and available_distance >= 0:
            room_ratio = available_distance / buffer_distance

    multiplier = adjusted / t_needed if t_needed is not None and t_needed > 0 and adjusted is not None else None
    speed = market.get("directional_effective_speed")
    time_residual = (
        t_needed - float(buffer_distance) / float(speed) * 60.0
        if (type(speed) in (int, float) and speed > 0
            and type(buffer_distance) in (int, float) and buffer_distance > 0
            and t_needed is not None)
        else None
    )
    projected = {
        "protocol": PROTOCOL,
        "evaluated_ts": snapshot.get("candle_ts"),
        "directional_effective_speed": market.get("directional_effective_speed"),
        "weighted_gross_speed": market.get("weighted_gross_speed"),
        "flow_efficiency": market.get("flow_efficiency"),
        "buffer_distance": buffer_distance,
        "available_distance": available_distance,
        "corridor_width": structure.get("corridor_width"),
        "t_needed_seconds": t_needed,
        "t_needed_adjusted_seconds": adjusted,
        "model_expiry_seconds": model_expiry,
        "model_time_reach_ratio": timing.get("model_time_reach_ratio"),
        "time_to_buffer_ratio": timing.get("time_to_buffer_ratio"),
        "adjustment_multiplier": multiplier,
        "space_to_buffer_ratio": room_ratio,
        "trade_space_margin_atr": physics.get("trade_space_margin_atr"),
        "atr_speed_reference": physics.get("atr_speed_reference"),
        "directional_speed_ratio": physics.get("directional_speed_ratio"),
        "movement_stress": physics.get("movement_stress"),
        "time_identity_residual_seconds": time_residual,
        "trend_context": market.get("trend_context"),
        "volatility_state": market.get("volatility_state"),
        "noise_context": market.get("noise_context"),
        "structure_state": structure.get("feasibility_state"),
        "time_state": timing.get("time_state"),
        "trade_physics_readiness": physics.get("readiness_state"),
    }
    return validate(projected)


def from_decision(decision: Any) -> dict[str, Any] | None:
    """Create the same projection from a live DecisionObject."""
    if getattr(decision, "fsm_inputs", {}).get("decision_policy") != "PHYSICAL_ONLY_V3":
        return None
    snapshot = decision.to_dict()
    snapshot["candle_ts"] = decision.setup.evaluated_ts
    return from_snapshot(snapshot)


def digest(snapshot: Mapping[str, Any]) -> str:
    normalized = validate(snapshot)
    encoded = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
