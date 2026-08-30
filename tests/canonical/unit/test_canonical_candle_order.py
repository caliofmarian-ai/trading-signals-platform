from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from tests.canonical.helpers.builders import make_candles


def _load_params(base_dir: Path) -> dict[str, Any]:
    return json.loads((base_dir / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _non_blocking_params(base_dir: Path) -> dict[str, Any]:
    params = copy.deepcopy(_load_params(base_dir))
    params.setdefault("strategy_v2", {}).setdefault("min_avg_range", {})["FOREX_DEFAULT"] = 0.0
    params["spike_filters"] = {
        "wick_body_ratio_max": 1_000_000.0,
        "range_z_max": 1_000_000.0,
        "jump_vs_atr_max": 1_000_000.0,
    }
    return params


def test_canonical_builder_is_newest_first() -> None:
    candles = make_candles()

    timestamps = [candle["ts"] for candle in candles]
    assert timestamps == sorted(timestamps, reverse=True)
    assert candles[0]["ts"] == max(timestamps)


@pytest.mark.parametrize("invalid_series", ["m1", "m5"])
def test_strategy_rejects_oldest_first_inputs(
    canonical_runtime_root: Path,
    invalid_series: str,
) -> None:
    strategy = importlib.import_module("core.strategy_v2")
    params = _load_params(canonical_runtime_root)
    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")
    if invalid_series == "m1":
        candles_m1.reverse()
    else:
        candles_m5.reverse()

    with pytest.raises(ValueError, match=f"candles_{invalid_series} must be newest-first"):
        strategy.decide(
            candles_m1,
            candles_m5,
            params,
            "MEDIUM",
            want_open_now=True,
            context={"decision_timeframe": "M1"},
        )


def test_newest_and_second_newest_drive_decision(
    canonical_runtime_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = importlib.import_module("core.strategy_v2")
    params = _non_blocking_params(canonical_runtime_root)
    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")

    candles_m1[0].update({"open": 1.5000, "high": 1.5012, "low": 1.4998, "close": 1.5010})
    candles_m1[1].update({"open": 1.4000, "high": 1.4005, "low": 1.3998, "close": 1.4002})

    jump_inputs: dict[str, float] = {}

    def capture_jump(last_close: float, prev_close: float, atr_val: float) -> float:
        jump_inputs.update(last_close=last_close, prev_close=prev_close, atr_val=atr_val)
        return 0.0

    monkeypatch.setattr(strategy, "_jump_vs_atr", capture_jump)

    decision = strategy.decide(
        candles_m1,
        candles_m5,
        params,
        "MEDIUM",
        want_open_now=True,
        context={"decision_timeframe": "M1"},
    )

    assert decision["candle_ts"] == candles_m1[0]["ts"]
    assert decision["debug"]["price"] == candles_m1[0]["close"]
    assert jump_inputs["last_close"] == candles_m1[0]["close"]
    assert jump_inputs["prev_close"] == candles_m1[1]["close"]
    assert decision["debug"]["scores"]["body"] > 0.0


def test_indicator_boundaries_receive_chronological_series(
    canonical_runtime_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = importlib.import_module("core.strategy_v2")
    params = _non_blocking_params(canonical_runtime_root)
    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")
    captured: dict[str, Any] = {"ema": []}

    def capture_ema(values: list[float], period: int) -> float:
        captured["ema"].append((list(values), period))
        return values[-1]

    def capture_rsi(values: list[float], period: int) -> float:
        captured["rsi"] = (list(values), period)
        return 50.0

    def capture_atr(
        highs: list[float],
        lows: list[float],
        closes: list[float],
        period: int,
    ) -> float:
        captured["atr"] = (list(highs), list(lows), list(closes), period)
        return 0.001

    monkeypatch.setattr(strategy, "ema", capture_ema)
    monkeypatch.setattr(strategy, "rsi", capture_rsi)
    monkeypatch.setattr(strategy, "atr", capture_atr)

    strategy.decide(
        candles_m1,
        candles_m5,
        params,
        "MEDIUM",
        want_open_now=True,
        context={"decision_timeframe": "M1"},
    )

    expected_m1_closes = [float(candle["close"]) for candle in reversed(candles_m1)]
    expected_m5_closes = [float(candle["close"]) for candle in reversed(candles_m5)]
    expected_m5_highs = [float(candle["high"]) for candle in reversed(candles_m5)]
    expected_m5_lows = [float(candle["low"]) for candle in reversed(candles_m5)]

    assert [values for values, _period in captured["ema"]] == [expected_m5_closes, expected_m5_closes]
    assert captured["rsi"][0] == expected_m1_closes
    assert captured["atr"][0] == expected_m5_highs
    assert captured["atr"][1] == expected_m5_lows
    assert captured["atr"][2] == expected_m5_closes
    assert expected_m1_closes[-1] == candles_m1[0]["close"]
    assert expected_m5_closes[-1] == candles_m5[0]["close"]


def test_activity_gate_uses_ten_most_recent_candles(canonical_runtime_root: Path) -> None:
    strategy = importlib.import_module("core.strategy_v2")
    params = _non_blocking_params(canonical_runtime_root)
    params["strategy_v2"]["min_avg_range"]["FOREX_DEFAULT"] = 0.001
    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")

    for index, candle in enumerate(candles_m1):
        if index < 10:
            candle["high"] = candle["open"] + 0.01
            candle["low"] = candle["open"] - 0.01
        else:
            candle["high"] = candle["open"] + 0.00001
            candle["low"] = candle["open"] - 0.00001

    decision = strategy.decide(
        candles_m1,
        candles_m5,
        params,
        "MEDIUM",
        want_open_now=True,
        context={"decision_timeframe": "M1"},
    )

    assert "activity" not in decision["gates"]


def test_body_expansion_uses_previous_ten_recent_candles(canonical_runtime_root: Path) -> None:
    strategy = importlib.import_module("core.strategy_v2")
    params = _non_blocking_params(canonical_runtime_root)
    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")

    candles_m1[0].update({"open": 1.2000, "high": 1.2030, "low": 1.1990, "close": 1.2020})
    for candle in candles_m1[1:11]:
        candle.update({"open": 1.2000, "high": 1.2020, "low": 1.1990, "close": 1.2010})
    for candle in candles_m1[11:]:
        candle.update({"open": 1.2000, "high": 1.3100, "low": 1.1900, "close": 1.3000})

    decision = strategy.decide(
        candles_m1,
        candles_m5,
        params,
        "MEDIUM",
        want_open_now=True,
        context={"decision_timeframe": "M1"},
    )

    assert decision["debug"]["scores"]["body"] == pytest.approx(15.0)


def test_range_zscore_uses_recent_window_with_current_last(
    canonical_runtime_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = importlib.import_module("core.strategy_v2")
    params = _non_blocking_params(canonical_runtime_root)
    candles_m1 = make_candles(timeframe="M1")
    candles_m5 = make_candles(timeframe="M5")
    oldest_ts = candles_m1[-1]["ts"]
    for offset in range(40):
        candle = copy.deepcopy(candles_m1[-1])
        candle["ts"] = oldest_ts - (offset + 1) * 60
        candle["high"] = 2.0 + offset
        candle["low"] = 1.0
        candles_m1.append(candle)

    captured: dict[str, list[float]] = {}

    def capture_range_zscore(ranges: list[float]) -> float:
        captured["ranges"] = list(ranges)
        return 0.0

    monkeypatch.setattr(strategy, "_range_zscore", capture_range_zscore)

    strategy.decide(
        candles_m1,
        candles_m5,
        params,
        "MEDIUM",
        want_open_now=True,
        context={"decision_timeframe": "M1"},
    )

    expected = [
        float(candle["high"]) - float(candle["low"])
        for candle in reversed(candles_m1[:50])
    ]
    assert captured["ranges"] == expected
    assert captured["ranges"][-1] == pytest.approx(
        candles_m1[0]["high"] - candles_m1[0]["low"]
    )


def test_speed_uses_recent_newest_first_window() -> None:
    strategy = importlib.import_module("core.strategy_v2")
    candles = []
    newest_ts = 1_800_000_000
    for index in range(50):
        close = 2.0 - (index * 0.01) if index < 21 else 1.0
        candles.append({"ts": newest_ts - index * 60, "close": close})

    assert strategy._avg_speed_price_per_minute(candles, lookback=20) == pytest.approx(0.01)


def test_signal_engine_passes_adapter_output_without_inversion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signal_engine = importlib.import_module("core.signal_engine")
    market_client = importlib.import_module("runtime.market_client")
    raw_m1 = list(reversed(make_candles(timeframe="M1")))
    raw_m5 = list(reversed(make_candles(timeframe="M5")))
    captured: dict[str, list[dict[str, Any]]] = {}
    errors: list[dict[str, Any]] = []

    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(signal_engine, "_load_algo_params", lambda: {})
    monkeypatch.setattr(signal_engine, "_load_active_symbols", lambda: ["EURUSD"])
    monkeypatch.setattr(signal_engine.fsm_runtime, "load_state", lambda: {})
    monkeypatch.setattr(
        signal_engine.fsm_runtime,
        "reconcile_state",
        lambda state, now_ts, active_symbols: (state, []),
    )
    monkeypatch.setattr(
        signal_engine.fsm_runtime,
        "apply_transition",
        lambda state, decision, now_ts: (state, None),
    )
    monkeypatch.setattr(signal_engine.fsm_runtime, "save_state", lambda state: None)
    monkeypatch.setattr(signal_engine, "_log_tps_metrics", lambda decision, now_ts: None)
    monkeypatch.setattr(
        signal_engine.observability_logger,
        "build_event",
        lambda event_type, data, source=None: {"event_type": event_type, "data": data},
    )
    monkeypatch.setattr(signal_engine.observability_logger, "log_event", lambda event: None)
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)
    monkeypatch.setattr(
        market_client,
        "get_candles",
        lambda symbol, interval: raw_m1 if interval == "1min" else raw_m5,
    )

    def capture_decide(**kwargs: Any) -> dict[str, Any]:
        captured["m1"] = kwargs["candles_m1"]
        captured["m5"] = kwargs["candles_m5"]
        return {
            "kind": "NO_SIGNAL",
            "signal_id": None,
            "symbol": "EURUSD",
            "score_total": None,
            "buffer_mode": "MEDIUM",
            "expiry_minutes": None,
            "candle_ts": kwargs["candles_m1"][0]["ts"],
            "gates": {},
            "debug": {},
        }

    monkeypatch.setattr(signal_engine, "decide", capture_decide)

    signal_engine.run_once(now_ts=1_800_000_000)

    assert errors == []
    assert [candle["ts"] for candle in captured["m1"]] == sorted(
        (candle["ts"] for candle in raw_m1),
        reverse=True,
    )
    assert [candle["ts"] for candle in captured["m5"]] == sorted(
        (candle["ts"] for candle in raw_m5),
        reverse=True,
    )
