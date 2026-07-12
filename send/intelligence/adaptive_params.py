# /opt/binarybot/intelligence/adaptive_params.py
# BinaryBot — Adaptive Parameters Engine

from __future__ import annotations

from typing import Dict, Any

from core import params_loader
from intelligence import research_engine


def adjust_parameters() -> Dict[str, Any]:

    params = params_loader.load_algo_params()

    research = research_engine.build_research_report()

    win_rate = research.get("outcomes", {}).get("win_rate", 0)

    thresholds = params.get("thresholds", {})

    pre = thresholds.get("pre", 40)
    confirm = thresholds.get("confirm", 60)
    open_now = thresholds.get("open", 80)

    if win_rate < 45:
        pre += 2
        confirm += 2
        open_now += 2

    elif win_rate > 65:
        pre -= 1
        confirm -= 1
        open_now -= 1

    thresholds["pre"] = max(30, min(pre, 70))
    thresholds["confirm"] = max(40, min(confirm, 80))
    thresholds["open"] = max(60, min(open_now, 95))

    params["thresholds"] = thresholds

    return params