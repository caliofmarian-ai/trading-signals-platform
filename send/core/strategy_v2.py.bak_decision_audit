# /opt/binarybot/strategy_v2.py
# BinaryBot — Strategy Core (Canonical)
# Implements ALGO_SPEC.md (gates + scoring + buffer + expiry) under MODULE_INTERFACE_SPEC.md contract.
#
# HARD RULES:
# - NO Telegram calls
# - NO file I/O
# - Deterministic for identical inputs
# - Uses params from config/algo_params.json only

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import math
import time


# ----------------------------
# Helpers: safe math utilities
# ----------------------------

def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    if b == 0:
        return default
    return a / b

def _round_up_int(x: float) -> int:
    return int(math.ceil(x))

def _now_epoch() -> int:
    return int(time.time())


# ----------------------------
# Candle extraction / adapters
# ----------------------------

def _get_close(c: Dict[str, Any]) -> float:
    return float(c["close"])

def _get_open(c: Dict[str, Any]) -> float:
    return float(c["open"])

def _get_high(c: Dict[str, Any]) -> float:
    return float(c["high"])

def _get_low(c: Dict[str, Any]) -> float:
    return float(c["low"])

def _get_ts(c: Dict[str, Any]) -> int:
    # Contract expects epoch seconds (int). Upstream must normalize.
    return int(c["ts"])


# ----------------------------
# Indicators: EMA / RSI / ATR
# ----------------------------

def ema(values: List[float], period: int) -> float:
    if not values or period <= 1:
        return values[-1] if values else 0.0
    k = 2.0 / (period + 1.0)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1.0 - k)
    return e

def rsi(values: List[float], period: int) -> float:
    if len(values) < period + 1:
        return 50.0
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        diff = values[-i] - values[-i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses += abs(diff)
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def atr(highs: List[float], lows: List[float], closes: List[float], period: int) -> float:
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return 0.0
    trs: List[float] = []
    for i in range(1, period + 1):
        h = highs[-i]
        l = lows[-i]
        prev_close = closes[-i - 1]
        tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        trs.append(tr)
    return sum(trs) / float(period)


# ----------------------------
# Symbol / asset class helpers
# ----------------------------

def _normalize_symbol(symbol: str) -> str:
    # Keep "EUR/USD" style (as used by TwelveData), but compute a stable key for ids.
    return symbol.strip().upper()

def _symbol_key(symbol: str) -> str:
    return _normalize_symbol(symbol).replace("/", "").replace("-", "").replace(" ", "")

def _is_crypto(symbol: str) -> bool:
    s = _normalize_symbol(symbol)
    # Heuristic: common crypto bases
    bases = {"BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "LTC", "DOT", "AVAX"}
    if "/" in s:
        base = s.split("/")[0]
        return base in bases
    return False

def _pip_size(symbol: str) -> float:
    # Forex pip size heuristic
    s = _normalize_symbol(symbol)
    if "JPY" in s:
        return 0.01
    return 0.0001

def _price_to_pips(symbol: str, price_delta: float) -> float:
    return price_delta / _pip_size(symbol)

def _pips_to_price(symbol: str, pips: float) -> float:
    return pips * _pip_size(symbol)


# ----------------------------
# Structure (SR) estimation
# ----------------------------

def _swing_points_from_m5(candles_m5: List[Dict[str, Any]], lookback: int = 60) -> Tuple[List[float], List[float]]:
    """
    Simple swing extraction:
    - collect recent highs/lows as candidates
    - not a full fractal clustering; deterministic & fast
    """
    if not candles_m5:
        return [], []

    n = min(len(candles_m5), lookback)
    highs = [float(candles_m5[i]["high"]) for i in range(n)]
    lows = [float(candles_m5[i]["low"]) for i in range(n)]

    # Candidate levels: recent highs/lows
    # Keep a small unique-ish list by tolerance
    tol = (max(highs) - min(lows)) * 0.002 if (max(highs) - min(lows)) > 0 else 0.0  # 0.2% range
    if tol == 0:
        tol = 1e-9

    def uniq(levels: List[float]) -> List[float]:
        out: List[float] = []
        for x in sorted(levels):
            if not out:
                out.append(x)
            else:
                if abs(x - out[-1]) > tol:
                    out.append(x)
        return out

    sup = uniq(lows)
    res = uniq(highs)
    return sup, res

def _nearest_support_resistance(price: float, supports: List[float], resistances: List[float]) -> Tuple[Optional[float], Optional[float]]:
    sup = [x for x in supports if x < price]
    res = [x for x in resistances if x > price]
    nearest_sup = max(sup) if sup else None
    nearest_res = min(res) if res else None
    return nearest_sup, nearest_res

def _available_space(symbol: str, direction: str, price: float, nearest_sup: Optional[float], nearest_res: Optional[float]) -> float:
    """
    Space in *price units* until nearest SR in the trade direction.
    BUY  -> space to resistance
    SELL -> space to support
    """
    if direction == "BUY":
        if nearest_res is None:
            return float("inf")
        return max(0.0, nearest_res - price)
    else:
        if nearest_sup is None:
            return float("inf")
        return max(0.0, price - nearest_sup)


# ----------------------------
# Spike filter
# ----------------------------

def _candle_features(c: Dict[str, Any]) -> Dict[str, float]:
    o = _get_open(c)
    h = _get_high(c)
    l = _get_low(c)
    cl = _get_close(c)
    body = abs(cl - o)
    rng = max(0.0, h - l)
    upper_wick = max(0.0, h - max(o, cl))
    lower_wick = max(0.0, min(o, cl) - l)
    wick = upper_wick + lower_wick
    wick_body_ratio = _safe_div(wick, max(body, 1e-9), default=999.0)
    return {
        "body": body,
        "range": rng,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
        "wick": wick,
        "wick_body_ratio": wick_body_ratio
    }

def _range_zscore(ranges: List[float]) -> float:
    if len(ranges) < 20:
        return 0.0
    mu = sum(ranges) / len(ranges)
    var = sum((x - mu) ** 2 for x in ranges) / len(ranges)
    sd = math.sqrt(max(var, 1e-12))
    last = ranges[-1]
    return (last - mu) / sd

def _jump_vs_atr(last_close: float, prev_close: float, atr_val: float) -> float:
    if atr_val <= 0:
        return 0.0
    return abs(last_close - prev_close) / atr_val


# ----------------------------
# Time-to-target feasibility
# ----------------------------

def _avg_speed_price_per_minute(candles_m1: List[Dict[str, Any]], lookback: int = 20) -> float:
    """
    Proxy speed: average absolute close-to-close movement per minute (price units).
    """
    if len(candles_m1) < lookback + 1:
        return 0.0
    closes = [float(c["close"]) for c in candles_m1[-(lookback + 1):]]
    diffs = [abs(closes[i] - closes[i - 1]) for i in range(1, len(closes))]
    return sum(diffs) / max(1, len(diffs))

def _estimate_t_needed_minutes(distance_price: float, speed_price_per_min: float) -> float:
    if speed_price_per_min <= 0:
        return float("inf")
    return distance_price / speed_price_per_min


# ----------------------------
# Decision builder (contract)
# ----------------------------

def _make_gate(ok: bool, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"ok": bool(ok), "reason": reason, "details": details or {}}


def decide(
    candles_m1: List[Dict[str, Any]],
    candles_m5: List[Dict[str, Any]],
    params: Dict[str, Any],
    buffer_mode: str,
    want_open_now: bool,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Returns Decision dict matching MODULE_INTERFACE_SPEC.md.
    """

    context = context or {}
    if not candles_m1 or not candles_m5:
        return {
            "kind": "NO_SIGNAL",
            "signal_id": None,
            "symbol": context.get("symbol", "UNKNOWN"),
            "timeframe": context.get("decision_timeframe", "M15"),
            "direction": None,
            "score_total": None,
            "buffer_mode": buffer_mode,
            "buffer_price": None,
            "expiry_minutes": None,
            "want_open_now": bool(want_open_now),
            "gates": {},
            "debug": {"reason": "missing_candles"},
            "candle_ts": int(_now_epoch()),
        }

    symbol = _normalize_symbol(str(candles_m1[-1].get("symbol", context.get("symbol", "UNKNOWN"))))
    tf = str(context.get("decision_timeframe", "M15"))

    # Latest candle timestamp (dedup key)
    candle_ts = _get_ts(candles_m1[-1])

    # ----------------------------
    # Load params (with safe defaults)
    # ----------------------------
    strat = params.get("strategy_v2", {}) if isinstance(params, dict) else {}
    ema_fast_n = int(strat.get("ema_fast", 50))
    ema_slow_n = int(strat.get("ema_slow", 200))
    rsi_n = int(strat.get("rsi_period", 14))
    rsi_call = float(strat.get("rsi_call", 58.0))
    rsi_put = float(strat.get("rsi_put", 42.0))

    score_thresholds = params.get("score_thresholds", {}) if isinstance(params, dict) else {}
    thr_pre = float(score_thresholds.get("PRE", 70))
    thr_confirm = float(score_thresholds.get("CONFIRM", 75))
    thr_open = float(score_thresholds.get("OPEN", 80))

    expiry_limits = params.get("expiry_limits_minutes", {}) if isinstance(params, dict) else {}
    expiry_min = int(expiry_limits.get("min", 2))
    expiry_max = int(expiry_limits.get("max", 15))

    buffer_mults = params.get("buffer_multipliers", {}) if isinstance(params, dict) else {}
    bm = str(buffer_mode).upper().strip()
    buffer_mult = float(buffer_mults.get(bm, 0.55))  # default MEDIUM-ish

    sr_required_multiplier = float(params.get("sr_required_multiplier", 1.5))
    crypto_round = float(params.get("crypto_points_rounding", 0.0))

    spike_cfg = params.get("spike_filters", {}) if isinstance(params, dict) else {}
    # conservative defaults
    spike_wick_body_ratio_max = float(spike_cfg.get("wick_body_ratio_max", 6.0))
    spike_range_z_max = float(spike_cfg.get("range_z_max", 3.0))
    spike_jump_vs_atr_max = float(spike_cfg.get("jump_vs_atr_max", 2.5))

    trend_time_adjust = params.get("trend_time_adjust", {}) if isinstance(params, dict) else {}
    t_adj_with = float(trend_time_adjust.get("WITH_TREND", 0.9))
    t_adj_flat = float(trend_time_adjust.get("FLAT", 1.0))
    t_adj_counter = float(trend_time_adjust.get("COUNTER_TREND", 1.15))

    structure_factor_cfg = params.get("structure_factor", {}) if isinstance(params, dict) else {}
    structure_factor = float(structure_factor_cfg.get("mult", 1.0))

    min_avg_range = strat.get("min_avg_range", {}) if isinstance(strat, dict) else {}
    min_avg_range_fx = float(min_avg_range.get("FOREX_DEFAULT", 0.00025))
    min_avg_range_fx_jpy = float(min_avg_range.get("FOREX_JPY", 0.025))
    min_avg_range_crypto = float(min_avg_range.get("CRYPTO_USD", 8.0))

    # ----------------------------
    # Build indicator series
    # ----------------------------
    closes_m1 = [float(c["close"]) for c in candles_m1]
    closes_m5 = [float(c["close"]) for c in candles_m5]
    highs_m5 = [float(c["high"]) for c in candles_m5]
    lows_m5 = [float(c["low"]) for c in candles_m5]

    price = closes_m1[-1]
    prev_price = closes_m1[-2] if len(closes_m1) >= 2 else price

    ema_fast = ema(closes_m5, ema_fast_n)
    ema_slow = ema(closes_m5, ema_slow_n)
    rsi_val = rsi(closes_m1, rsi_n)
    atr_val = atr(highs_m5, lows_m5, closes_m5, 14)

    # ----------------------------
    # Market activity filter (dead market)
    # ----------------------------
    # avg M1 range over last 10
    m1_n = min(10, len(candles_m1))
    m1_ranges = [float(candles_m1[-i]["high"]) - float(candles_m1[-i]["low"]) for i in range(1, m1_n + 1)]
    avg_range = sum(m1_ranges) / max(1, len(m1_ranges))

    is_crypto = _is_crypto(symbol)
    if is_crypto:
        min_range_thr = min_avg_range_crypto
    else:
        min_range_thr = min_avg_range_fx_jpy if "JPY" in symbol else min_avg_range_fx

    if avg_range < min_range_thr:
        return {
            "kind": "NO_SIGNAL",
            "signal_id": None,
            "symbol": symbol,
            "timeframe": tf,
            "direction": None,
            "score_total": None,
            "buffer_mode": bm,
            "buffer_price": None,
            "expiry_minutes": None,
            "want_open_now": bool(want_open_now),
            "gates": {"activity": _make_gate(False, "MIN_AVG_RANGE", {"avg_range": avg_range, "min_thr": min_range_thr})},
            "debug": {"avg_range": avg_range, "min_thr": min_range_thr},
            "candle_ts": candle_ts,
        }

    # ----------------------------
    # Trend classification & direction candidate
    # ----------------------------
    # Trend signal:
    # - WITH_TREND if ema_fast above ema_slow and price above both -> BUY bias
    # - WITH_TREND if ema_fast below ema_slow and price below both -> SELL bias
    # - FLAT if ema_fast close to ema_slow
    # - COUNTER_TREND otherwise when price contradicts ema direction
    eps = max(1e-9, abs(price) * 0.00002)
    ema_gap = abs(ema_fast - ema_slow)
    flat = ema_gap <= eps

    if flat:
        trend_class = "FLAT"
        # direction from RSI bias (fallback)
        if rsi_val >= 50:
            direction = "BUY"
        else:
            direction = "SELL"
    else:
        if ema_fast > ema_slow:
            if price >= ema_fast and price >= ema_slow:
                trend_class = "WITH_TREND"
                direction = "BUY"
            else:
                trend_class = "COUNTER_TREND"
                direction = "SELL" if rsi_val < 50 else "BUY"
        else:
            if price <= ema_fast and price <= ema_slow:
                trend_class = "WITH_TREND"
                direction = "SELL"
            else:
                trend_class = "COUNTER_TREND"
                direction = "BUY" if rsi_val > 50 else "SELL"

    # ----------------------------
    # Buffer calculation (ALGO_SPEC)
    # buffer_price = ATR_M5 * buffer_multiplier
    # crypto rounding optional
    # ----------------------------
    buffer_price = atr_val * buffer_mult if atr_val > 0 else 0.0
    if is_crypto and crypto_round > 0:
        # round buffer to nearest step (e.g. 0.5 points)
        buffer_price = round(buffer_price / crypto_round) * crypto_round

    # Required SR space in direction:
    required_space = buffer_price * sr_required_multiplier

    # ----------------------------
    # Structure (SR) levels + available space
    # ----------------------------
    supports, resistances = _swing_points_from_m5(candles_m5, lookback=80)
    nearest_sup, nearest_res = _nearest_support_resistance(price, supports, resistances)
    avail_space = _available_space(symbol, direction, price, nearest_sup, nearest_res)

    sr_ok = (avail_space >= required_space) if math.isfinite(avail_space) else True

    # ----------------------------
    # Spike filter (ALGO_SPEC)
    # ----------------------------
    last_candle = candles_m1[-1]
    prev_candle = candles_m1[-2] if len(candles_m1) >= 2 else candles_m1[-1]
    feat = _candle_features(last_candle)
    m1_ranges_all = [float(c["high"]) - float(c["low"]) for c in candles_m1[-50:]] if len(candles_m1) >= 50 else m1_ranges
    rz = _range_zscore(m1_ranges_all)
    jva = _jump_vs_atr(_get_close(last_candle), _get_close(prev_candle), atr_val)

    spike_ok = True
    spike_reasons: List[str] = []
    if feat["wick_body_ratio"] > spike_wick_body_ratio_max:
        spike_ok = False
        spike_reasons.append("WICK_BODY_RATIO")
    if rz > spike_range_z_max:
        spike_ok = False
        spike_reasons.append("RANGE_Z")
    if jva > spike_jump_vs_atr_max:
        spike_ok = False
        spike_reasons.append("JUMP_VS_ATR")

    # ----------------------------
    # Feasibility: estimate time to target (buffer distance)
    # Use speed proxy from M1
    # ----------------------------
    speed = _avg_speed_price_per_minute(candles_m1, lookback=20)
    t_needed = _estimate_t_needed_minutes(distance_price=buffer_price, speed_price_per_min=speed)

    # Trend time adjust
    if trend_class == "WITH_TREND":
        t_adj = t_adj_with
    elif trend_class == "COUNTER_TREND":
        t_adj = t_adj_counter
    else:
        t_adj = t_adj_flat

    t_needed_adj = t_needed * t_adj * structure_factor

    # Expiry selection:
    # - clamp to [min, max]
    # - round up
    if not math.isfinite(t_needed_adj) or t_needed_adj <= 0:
        expiry_minutes = expiry_max
    else:
        expiry_minutes = _round_up_int(_clamp(t_needed_adj, float(expiry_min), float(expiry_max)))

    # Feasibility gate: if t_needed_adj <= expiry_minutes
    feas_ok = (t_needed_adj <= float(expiry_minutes)) if math.isfinite(t_needed_adj) else False

    # ----------------------------
    # SCORING (ALGO_SPEC module maxima):
    # A Trend alignment: max 30
    # B RSI extremes:   max 20
    # C Body expansion: max 15
    # D Structure dist: max 20
    # E Feasibility:    max 15
    # ----------------------------

    # A: Trend score
    if trend_class == "WITH_TREND":
        score_trend = 30.0
    elif trend_class == "FLAT":
        score_trend = 15.0
    else:
        score_trend = 0.0

    # B: RSI score
    if direction == "BUY":
        # scale from 50..rsi_call
        if rsi_val >= rsi_call:
            score_rsi = 20.0
        elif rsi_val <= 50:
            score_rsi = 0.0
        else:
            score_rsi = 20.0 * _safe_div((rsi_val - 50.0), max(rsi_call - 50.0, 1e-9), 0.0)
    else:
        # SELL: scale from 50..rsi_put downward
        if rsi_val <= rsi_put:
            score_rsi = 20.0
        elif rsi_val >= 50:
            score_rsi = 0.0
        else:
            score_rsi = 20.0 * _safe_div((50.0 - rsi_val), max(50.0 - rsi_put, 1e-9), 0.0)

    # C: Body expansion score
    # ratio = last_body / avg_body_last_10
    bodies = []
    for c in candles_m1[-11:-1] if len(candles_m1) >= 11 else candles_m1[:-1]:
        o = float(c["open"]); cl = float(c["close"])
        bodies.append(abs(cl - o))
    avg_body = (sum(bodies) / len(bodies)) if bodies else 0.0
    last_body = feat["body"]
    body_ratio = _safe_div(last_body, max(avg_body, 1e-9), 0.0)
    # 1.0 => 0 pts, 1.4 => full 15 (cap)
    if body_ratio <= 1.0:
        score_body = 0.0
    else:
        score_body = 15.0 * _clamp((body_ratio - 1.0) / 0.4, 0.0, 1.0)

    # D: Structure distance score
    # use avail_space / required_space
    if required_space <= 0:
        score_struct = 0.0
    elif not math.isfinite(avail_space):
        score_struct = 20.0
    else:
        ratio = _safe_div(avail_space, required_space, 0.0)
        score_struct = 20.0 * _clamp(ratio, 0.0, 1.0)

    # E: Feasibility score
    # if t_needed_adj <= expiry*0.8 => full; if <= expiry => scaled; else 0
    if not math.isfinite(t_needed_adj):
        score_feas = 0.0
    else:
        hard = float(expiry_minutes)
        if t_needed_adj <= 0.8 * hard:
            score_feas = 15.0
        elif t_needed_adj <= hard:
            score_feas = 15.0 * _clamp((hard - t_needed_adj) / max(0.2 * hard, 1e-9), 0.0, 1.0)
        else:
            score_feas = 0.0

    score_total = float(score_trend + score_rsi + score_body + score_struct + score_feas)
    score_total = _clamp(score_total, 0.0, 100.0)

    # ----------------------------
    # Gates dictionary (contract)
    # ----------------------------
    gates: Dict[str, Any] = {
        "sr_gate": _make_gate(
            sr_ok,
            None if sr_ok else "SR_SPACE_INSUFFICIENT",
            {
                "available_space": avail_space,
                "required_space": required_space,
                "nearest_support": nearest_sup,
                "nearest_resistance": nearest_res,
            }
        ),
        "spike_filter": _make_gate(
            spike_ok,
            None if spike_ok else "SPIKE_DETECTED",
            {
                "wick_body_ratio": feat["wick_body_ratio"],
                "range_z": rz,
                "jump_vs_atr": jva,
                "reasons": spike_reasons,
                "limits": {
                    "wick_body_ratio_max": spike_wick_body_ratio_max,
                    "range_z_max": spike_range_z_max,
                    "jump_vs_atr_max": spike_jump_vs_atr_max,
                }
            }
        ),
        "feasibility": _make_gate(
            feas_ok,
            None if feas_ok else "FEASIBILITY_FAIL",
            {
                "t_needed_min": t_needed,
                "t_needed_adj_min": t_needed_adj,
                "expiry_min": expiry_minutes,
                "speed_price_per_min": speed,
            }
        ),
    }

    # ----------------------------
    # Decide kind (ALGO_SPEC thresholds)
    # - If any critical gate fails => REJECT
    # - Else: OPEN/CONFIRM/PRE by thresholds
    # ----------------------------
    critical_ok = sr_ok and spike_ok and feas_ok

    # Build stable signal_id for this candle idea
    # NOTE: must be stable across stages (same candle_ts & direction)
    sid = f"{_symbol_key(symbol)}_{tf}_{candle_ts}_{direction}"

    debug = {
        "symbol": symbol,
        "tf": tf,
        "price": price,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "ema_gap": ema_gap,
        "trend_class": trend_class,
        "rsi": rsi_val,
        "atr_m5": atr_val,
        "buffer_mult": buffer_mult,
        "buffer_price": buffer_price,
        "required_space": required_space,
        "scores": {
            "trend": score_trend,
            "rsi": score_rsi,
            "body": score_body,
            "structure": score_struct,
            "feasibility": score_feas,
            "total": score_total,
        },
        "thresholds": {"PRE": thr_pre, "CONFIRM": thr_confirm, "OPEN": thr_open},
        "expiry": {
            "min": expiry_min,
            "max": expiry_max,
            "selected": expiry_minutes,
            "t_needed_adj": t_needed_adj,
            "trend_time_adjust": t_adj,
            "structure_factor": structure_factor,
        },
        "sr": {
            "nearest_support": nearest_sup,
            "nearest_resistance": nearest_res,
            "available_space": avail_space,
        },
        "spike": {
            "wick_body_ratio": feat["wick_body_ratio"],
            "range_z": rz,
            "jump_vs_atr": jva,
            "reasons": spike_reasons,
        },
    }

    if not critical_ok:
        return {
            "kind": "REJECT",
            "signal_id": sid,  # preferred to keep traceability
            "symbol": symbol,
            "timeframe": tf,
            "direction": direction,
            "score_total": score_total,
            "buffer_mode": bm,
            "buffer_price": buffer_price,
            "expiry_minutes": expiry_minutes,
            "want_open_now": bool(want_open_now),
            "gates": gates,
            "debug": debug,
            "candle_ts": candle_ts,
        }

    # Stage selection
    if score_total >= thr_open and want_open_now:
        kind = "OPEN_NOW"
    elif score_total >= thr_confirm:
        kind = "CONFIRM"
    elif score_total >= thr_pre:
        kind = "PRE"
    else:
        kind = "NO_SIGNAL"

    if kind == "NO_SIGNAL":
        return {
            "kind": "NO_SIGNAL",
            "signal_id": None,
            "symbol": symbol,
            "timeframe": tf,
            "direction": None,
            "score_total": None,
            "buffer_mode": bm,
            "buffer_price": None,
            "expiry_minutes": None,
            "want_open_now": bool(want_open_now),
            "gates": gates,
            "debug": debug,
            "candle_ts": candle_ts,
        }

    return {
        "kind": kind,
        "signal_id": sid,
        "symbol": symbol,
        "timeframe": tf,
        "direction": direction,
        "score_total": score_total,
        "buffer_mode": bm,
        "buffer_price": buffer_price,
        "expiry_minutes": expiry_minutes,
        "want_open_now": bool(want_open_now),
        "gates": gates,
        "debug": debug,
        "candle_ts": candle_ts,
    }