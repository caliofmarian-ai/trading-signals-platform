from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

from tests.canonical.helpers.builders import make_candles


def _load_params(base_dir: Path) -> dict:
    return json.loads((base_dir / "config" / "algo_params.json").read_text(encoding="utf-8"))


def test_strategy_is_deterministic_and_preserves_inputs(canonical_runtime_root: Path):
    strategy = importlib.import_module("core.strategy_v2")

    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")
    params = _load_params(canonical_runtime_root)

    candles_m1_before = copy.deepcopy(candles_m1)
    candles_m5_before = copy.deepcopy(candles_m5)

    first = strategy.decide(candles_m1, candles_m5, params, "MEDIUM", want_open_now=True, context={"decision_timeframe": "M1"})
    second = strategy.decide(candles_m1, candles_m5, params, "MEDIUM", want_open_now=True, context={"decision_timeframe": "M1"})

    assert first == second
    assert candles_m1 == candles_m1_before
    assert candles_m5 == candles_m5_before


def test_threshold_hierarchy_controls_stage_selection(canonical_runtime_root: Path):
    strategy = importlib.import_module("core.strategy_v2")

    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")
    params = _load_params(canonical_runtime_root)

    strict = copy.deepcopy(params)
    strict["score_thresholds"] = {"PRE": 99, "CONFIRM": 100, "OPEN": 101}
    strict_decision = strategy.decide(candles_m1, candles_m5, strict, "MEDIUM", want_open_now=True, context={"decision_timeframe": "M1"})
    assert strict_decision["kind"] in {"NO_SIGNAL", "REJECT"}

    permissive = copy.deepcopy(params)
    permissive["score_thresholds"] = {"PRE": 0, "CONFIRM": 0, "OPEN": 0}
    permissive_decision = strategy.decide(candles_m1, candles_m5, permissive, "MEDIUM", want_open_now=True, context={"decision_timeframe": "M1"})
    assert permissive_decision["kind"] in {"PRE", "CONFIRM", "OPEN_NOW", "REJECT"}
    if permissive_decision["kind"] != "REJECT":
        assert permissive_decision["kind"] == "OPEN_NOW"
