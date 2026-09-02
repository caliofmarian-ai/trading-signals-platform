"""Canonical, deterministic description of the observed market.

This layer calculates market facts only.  It does not score a setup, choose an
expiry, emit a signal, or execute a trade. Inputs follow the repository-wide
newest-first candle contract. Direction-aware movement evidence is derived here
for the active Time Model and Trade Physics contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Any, Mapping, Sequence

from .decision_object import MarketContext


SCHEMA_VERSION = "2.0.0"
ATR_PERIOD = 14
ATR_REQUIRED_CANDLES = ATR_PERIOD + 1


class MarketModelUnavailable(ValueError):
    """Raised when real evidence is insufficient or invalid."""


@dataclass(frozen=True)
class IndicatorEvidence:
    ema_fast: float
    ema_slow: float
    rsi: float
    atr_m5: float
    average_m1_range: float
    minimum_m1_range: float
    wick_body_ratio: float
    range_z_score: float
    jump_vs_atr: float
    latest_body: float
    average_body_last_10: float


@dataclass(frozen=True)
class MarketModelResult:
    schema_version: str
    symbol: str
    evaluated_ts: int
    direction_bias: str
    context: MarketContext
    evidence: IndicatorEvidence
    noise_reasons: tuple[str, ...]


def _required_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MarketModelUnavailable(f"{name} configuration is required")
    return value


def _required_number(mapping: Mapping[str, Any], key: str, name: str) -> float:
    if key not in mapping or isinstance(mapping[key], bool):
        raise MarketModelUnavailable(f"{name}.{key} configuration is required")
    try:
        value = float(mapping[key])
    except (TypeError, ValueError) as exc:
        raise MarketModelUnavailable(f"{name}.{key} must be numeric") from exc
    if not isfinite(value):
        raise MarketModelUnavailable(f"{name}.{key} must be finite")
    return value


def _ema(values: Sequence[float], period: int) -> float:
    factor = 2.0 / (period + 1.0)
    result = values[0]
    for value in values[1:]:
        result = value * factor + result * (1.0 - factor)
    return result


def _rsi(values: Sequence[float], period: int) -> float:
    gains = 0.0
    losses = 0.0
    for index in range(1, period + 1):
        difference = values[-index] - values[-index - 1]
        if difference >= 0:
            gains += difference
        else:
            losses += abs(difference)
    average_loss = losses / period
    if average_loss == 0:
        return 100.0
    relative_strength = (gains / period) / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def _atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = ATR_PERIOD) -> float:
    true_ranges = []
    for index in range(1, period + 1):
        high = highs[-index]
        low = lows[-index]
        previous_close = closes[-index - 1]
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return sum(true_ranges) / period


def _validate_candles(candles: Sequence[Mapping[str, Any]], label: str, minimum: int) -> None:
    if len(candles) < minimum:
        raise MarketModelUnavailable(f"{label} requires {minimum} real candles; received {len(candles)}")
    previous_ts: int | None = None
    for index, candle in enumerate(candles):
        try:
            timestamp = int(candle["ts"])
            open_price, high, low, close = (float(candle[key]) for key in ("open", "high", "low", "close"))
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketModelUnavailable(f"{label}[{index}] is not a complete real candle") from exc
        if timestamp <= 0 or not all(isfinite(value) for value in (open_price, high, low, close)):
            raise MarketModelUnavailable(f"{label}[{index}] contains invalid evidence")
        if low > min(open_price, close) or high < max(open_price, close) or high < low:
            raise MarketModelUnavailable(f"{label}[{index}] has invalid OHLC geometry")
        if previous_ts is not None and timestamp >= previous_ts:
            raise MarketModelUnavailable(f"{label} must be strictly newest-first")
        previous_ts = timestamp


def _recent_contiguous_candles(
    candles: Sequence[Mapping[str, Any]],
    label: str,
    minimum: int,
    timeframe_seconds: int,
) -> list[Mapping[str, Any]]:
    """Return newest exact-cadence evidence required by time-normalized math."""
    contiguous_count = 1
    first_delta: int | None = None
    for index in range(1, len(candles)):
        newer_ts = int(candles[index - 1]["ts"])
        older_ts = int(candles[index]["ts"])
        delta = newer_ts - older_ts
        if delta != timeframe_seconds:
            first_delta = delta
            break
        contiguous_count += 1

    usable = list(candles[:contiguous_count])
    if len(usable) < minimum:
        raise MarketModelUnavailable(
            f"{label} requires {minimum} contiguous real candles at "
            f"{timeframe_seconds}s cadence for temporal evidence; received "
            f"{len(usable)} before first discontinuity (observed_delta={first_delta}s)"
        )
    return usable


def _is_crypto(symbol: str) -> bool:
    normalized = symbol.upper().strip()
    crypto_bases = {"BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "LTC", "DOT", "AVAX"}
    return "/" in normalized and normalized.split("/", 1)[0] in crypto_bases


def _directional_movement(
    recent_closes_chronological: Sequence[float], direction: str
) -> tuple[float, float, float | None]:
    """Return canonical recency-weighted directional speed, gross speed and flow efficiency."""

    if len(recent_closes_chronological) != 21:
        raise MarketModelUnavailable("directional movement requires exactly 21 M1 closes")
    if direction not in {"BUY", "SELL"}:
        raise MarketModelUnavailable("directional movement requires BUY or SELL")

    directional_total = 0.0
    gross_total = 0.0
    weighted_time = 0.0
    for index in range(1, 21):
        weight = float(index)
        delta = recent_closes_chronological[index] - recent_closes_chronological[index - 1]
        gross_delta = abs(delta)
        directional_delta = max(delta, 0.0) if direction == "BUY" else max(-delta, 0.0)
        directional_total += weight * directional_delta
        gross_total += weight * gross_delta
        weighted_time += weight

    directional_effective_speed = directional_total / weighted_time
    weighted_gross_speed = gross_total / weighted_time
    flow_efficiency = (
        directional_effective_speed / weighted_gross_speed
        if weighted_gross_speed > 0
        else None
    )
    return directional_effective_speed, weighted_gross_speed, flow_efficiency


def evaluate_market(
    candles_m1: Sequence[Mapping[str, Any]],
    candles_m5: Sequence[Mapping[str, Any]],
    params: Mapping[str, Any],
    *,
    buffer_mode: str = "MEDIUM",
) -> MarketModelResult:
    """Build a market description from real candles and versioned parameters."""

    strategy = _required_mapping(params.get("strategy_v2"), "strategy_v2")
    ema_fast_period = int(_required_number(strategy, "ema_fast", "strategy_v2"))
    ema_slow_period = int(_required_number(strategy, "ema_slow", "strategy_v2"))
    rsi_period = int(_required_number(strategy, "rsi_period", "strategy_v2"))
    if min(ema_fast_period, ema_slow_period, rsi_period) <= 1:
        raise MarketModelUnavailable("indicator periods must be greater than one")

    minimum_m1 = max(21, rsi_period + 1)
    minimum_m5 = max(ATR_REQUIRED_CANDLES, ema_slow_period + 1)
    _validate_candles(candles_m1, "candles_m1", minimum_m1)
    _validate_candles(candles_m5, "candles_m5", minimum_m5)
    _recent_contiguous_candles(candles_m1, "candles_m1", minimum_m1, 60)
    temporal_m5 = _recent_contiguous_candles(
        candles_m5, "candles_m5", ATR_REQUIRED_CANDLES, 300
    )

    latest = candles_m1[0]
    symbol = str(latest.get("symbol", "")).upper().strip()
    if not symbol:
        raise MarketModelUnavailable("latest candle symbol is required")

    m1_chronological = list(reversed(candles_m1))
    m5_chronological = list(reversed(candles_m5))
    atr_m5_chronological = list(reversed(temporal_m5))
    closes_m1 = [float(candle["close"]) for candle in m1_chronological]
    closes_m5 = [float(candle["close"]) for candle in m5_chronological]
    atr_closes_m5 = [float(candle["close"]) for candle in atr_m5_chronological]
    atr_highs_m5 = [float(candle["high"]) for candle in atr_m5_chronological]
    atr_lows_m5 = [float(candle["low"]) for candle in atr_m5_chronological]

    latest_price = float(latest["close"])
    ema_fast_value = _ema(closes_m5, ema_fast_period)
    ema_slow_value = _ema(closes_m5, ema_slow_period)
    rsi_value = _rsi(closes_m1, rsi_period)
    atr_value = _atr(atr_highs_m5, atr_lows_m5, atr_closes_m5)
    if atr_value <= 0:
        raise MarketModelUnavailable("M5 ATR cannot be established from real movement")

    epsilon = max(1e-9, abs(latest_price) * 0.00002)
    if abs(ema_fast_value - ema_slow_value) <= epsilon:
        trend_context = "FLAT"
        direction = "BUY" if rsi_value >= 50 else "SELL"
    elif ema_fast_value > ema_slow_value:
        if latest_price >= ema_fast_value and latest_price >= ema_slow_value:
            trend_context, direction = "WITH_TREND", "BUY"
        else:
            trend_context = "COUNTER_TREND"
            direction = "SELL" if rsi_value < 50 else "BUY"
    elif latest_price <= ema_fast_value and latest_price <= ema_slow_value:
        trend_context, direction = "WITH_TREND", "SELL"
    else:
        trend_context = "COUNTER_TREND"
        direction = "BUY" if rsi_value > 50 else "SELL"

    buffer_multipliers = _required_mapping(params.get("buffer_multipliers"), "buffer_multipliers")
    normalized_mode = buffer_mode.upper().strip()
    buffer_multiplier = _required_number(buffer_multipliers, normalized_mode, "buffer_multipliers")
    buffer_distance = atr_value * buffer_multiplier

    recent_ranges = [float(candle["high"]) - float(candle["low"]) for candle in candles_m1[:10]]
    average_range = sum(recent_ranges) / len(recent_ranges)
    minimum_ranges = _required_mapping(strategy.get("min_avg_range"), "strategy_v2.min_avg_range")
    if _is_crypto(symbol):
        minimum_range = _required_number(minimum_ranges, "CRYPTO_USD", "strategy_v2.min_avg_range")
    elif "JPY" in symbol:
        minimum_range = _required_number(minimum_ranges, "FOREX_JPY", "strategy_v2.min_avg_range")
    else:
        minimum_range = _required_number(minimum_ranges, "FOREX_DEFAULT", "strategy_v2.min_avg_range")
    volatility_state = "ACTIVE" if average_range >= minimum_range else "BELOW_MINIMUM_ACTIVITY"

    open_price, high, low = (float(latest[key]) for key in ("open", "high", "low"))
    body = abs(latest_price - open_price)
    previous_bodies = [
        abs(float(candle["close"]) - float(candle["open"])) for candle in candles_m1[1:11]
    ]
    average_body_last_10 = sum(previous_bodies) / len(previous_bodies)
    wick = max(0.0, high - max(open_price, latest_price)) + max(0.0, min(open_price, latest_price) - low)
    wick_body_ratio = wick / max(body, 1e-9)
    ranges_chronological = list(reversed([
        float(candle["high"]) - float(candle["low"]) for candle in candles_m1[:50]
    ]))
    mean_range = sum(ranges_chronological) / len(ranges_chronological)
    variance = sum((value - mean_range) ** 2 for value in ranges_chronological) / len(ranges_chronological)
    range_z_score = (ranges_chronological[-1] - mean_range) / sqrt(max(variance, 1e-12))
    jump_vs_atr = abs(latest_price - float(candles_m1[1]["close"])) / atr_value

    spike_filters = _required_mapping(params.get("spike_filters"), "spike_filters")
    noise_reasons = []
    if wick_body_ratio > _required_number(spike_filters, "wick_body_ratio_max", "spike_filters"):
        noise_reasons.append("WICK_BODY_RATIO")
    if range_z_score > _required_number(spike_filters, "range_z_max", "spike_filters"):
        noise_reasons.append("RANGE_Z")
    if jump_vs_atr > _required_number(spike_filters, "jump_vs_atr_max", "spike_filters"):
        noise_reasons.append("JUMP_VS_ATR")

    recent_closes = [float(candle["close"]) for candle in reversed(candles_m1[:21])]
    price_speed = sum(abs(recent_closes[index] - recent_closes[index - 1]) for index in range(1, 21)) / 20
    directional_effective_speed, weighted_gross_speed, flow_efficiency = _directional_movement(
        recent_closes, direction
    )

    context = MarketContext(
        latest_price=latest_price,
        price_speed=price_speed,
        buffer_distance=buffer_distance,
        trend_context=trend_context,
        volatility_state=volatility_state,
        noise_context="UNSTABLE" if noise_reasons else "STABLE",
        target_distance=None,
        directional_effective_speed=directional_effective_speed,
        weighted_gross_speed=weighted_gross_speed,
        flow_efficiency=flow_efficiency,
    )
    return MarketModelResult(
        schema_version=SCHEMA_VERSION,
        symbol=symbol,
        evaluated_ts=int(latest["ts"]),
        direction_bias=direction,
        context=context,
        evidence=IndicatorEvidence(
            ema_fast=ema_fast_value,
            ema_slow=ema_slow_value,
            rsi=rsi_value,
            atr_m5=atr_value,
            average_m1_range=average_range,
            minimum_m1_range=minimum_range,
            wick_body_ratio=wick_body_ratio,
            range_z_score=range_z_score,
            jump_vs_atr=jump_vs_atr,
            latest_body=body,
            average_body_last_10=average_body_last_10,
        ),
        noise_reasons=tuple(noise_reasons),
    )
