"""Separate saved market context from the recent physical measurement windows."""
from .market_model import ATR_REQUIRED_CANDLES
from .sr_corridor_engine import LEGACY_STRUCTURE_LOOKBACK

HISTORY_POLICY = "RECENT_PHYSICS_WITH_SAVED_CONTEXT_V1"


def requirements(params):
    from .physical_params import validate_physical_params
    validate_physical_params(params)
    if params.get("history_policy") != HISTORY_POLICY:
        raise ValueError("recent history policy must be explicitly declared")
    model = params["market_model"]
    m1 = max(22, model["rsi_period"] + 1)
    return {
        "policy": HISTORY_POLICY,
        "context": {"M1": m1, "M5": max(model["ema_slow"] + 1,
                    LEGACY_STRUCTURE_LOOKBACK, ATR_REQUIRED_CANDLES)},
        "recent_contiguous": {"M1": m1, "M5": ATR_REQUIRED_CANDLES},
    }
