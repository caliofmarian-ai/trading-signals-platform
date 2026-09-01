from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from core import runtime_param_gate
from core.strategy_v2 import STRATEGY_VERSION


def _valid_params() -> dict:
    return {
        "algo_version": STRATEGY_VERSION,
        "score_thresholds": {"PRE": 70, "CONFIRM": 75, "OPEN": 80},
        "expiry_limits_minutes": {"min": 2, "max": 15},
        "buffer_multipliers": {"SMALL": 0.3, "MEDIUM": 0.55, "LARGE": 1.0},
        "strategy_v2": {
            "ema_fast": 50,
            "ema_slow": 200,
            "rsi_period": 14,
            "rsi_call": 58.0,
            "rsi_put": 42.0,
            "min_avg_range": {
                "FOREX_DEFAULT": 0.00025,
                "FOREX_JPY": 0.025,
                "CRYPTO_USD": 8.0,
            },
        },
        "spike_filters": {
            "wick_body_ratio_max": 6.0,
            "range_z_max": 3.0,
            "jump_vs_atr_max": 2.5,
        },
        "sr_required_multiplier": 1.5,
        "crypto_points_rounding": 0.0,
        "trend_time_adjust": {
            "WITH_TREND": 0.9,
            "FLAT": 1.0,
            "COUNTER_TREND": 1.15,
        },
        "structure_factor": {"mult": 1.0},
    }


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_runtime_gate_accepts_current_canonical_bundle(tmp_path: Path) -> None:
    path = tmp_path / "algo_params.json"
    expected = _valid_params()
    _write(path, expected)

    loaded = runtime_param_gate.load_runtime_algo_params(str(path))

    assert loaded == expected
    assert loaded["algo_version"] == STRATEGY_VERSION


@pytest.mark.parametrize(
    "mutator",
    [
        lambda p: p.pop("score_thresholds"),
        lambda p: p["score_thresholds"].__setitem__("PRE", 101),
        lambda p: p["score_thresholds"].update({"PRE": 90, "CONFIRM": 75, "OPEN": 80}),
        lambda p: p.__setitem__("algo_version", "999.0.0"),
        lambda p: p.__setitem__("unknown_runtime_knob", 1),
    ],
    ids=[
        "missing-required-field",
        "out-of-range",
        "cross-field-hierarchy",
        "unsupported-version",
        "unknown-schema-field",
    ],
)
def test_runtime_gate_rejects_invalid_or_incompatible_bundles(
    tmp_path: Path, mutator
) -> None:
    payload = deepcopy(_valid_params())
    mutator(payload)
    path = tmp_path / "algo_params.json"
    _write(path, payload)

    with pytest.raises(runtime_param_gate.RuntimeParameterError):
        runtime_param_gate.load_runtime_algo_params(str(path))


def test_signal_engine_blocks_invalid_params_before_strategy_or_distribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core import signal_engine

    signal_engine._LAST_PARAM_ERROR_SIGNATURE = None
    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(
        signal_engine,
        "_load_algo_params",
        lambda: (_ for _ in ()).throw(
            signal_engine.runtime_param_gate.RuntimeParameterError("invalid bundle")
        ),
    )

    decide_calls: list[object] = []
    route_calls: list[object] = []
    errors: list[dict] = []
    incidents: list[dict] = []

    monkeypatch.setattr(signal_engine, "decide", lambda **kwargs: decide_calls.append(kwargs))
    monkeypatch.setattr(signal_engine.distribution_router, "route", lambda *a, **k: route_calls.append((a, k)))
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)
    monkeypatch.setattr(
        signal_engine.observability_logger,
        "record_operational_incident",
        lambda **kwargs: incidents.append(kwargs) or kwargs,
    )

    signal_engine.run_once(now_ts=1_800_000_000)
    signal_engine.run_once(now_ts=1_800_000_002)

    assert decide_calls == []
    assert route_calls == []
    assert len(errors) == 1
    assert errors[0]["error_type"] == "ALGO_PARAMS_VALIDATION_FAILED"
    assert errors[0]["severity"] == "CRITICAL"
    assert "strategy evaluation blocked" in errors[0]["message"]
    assert len(incidents) == 2
    assert all(item["runtime_state"] == "BLOCKED" for item in incidents)


def test_validated_bundle_reaches_strategy_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core import signal_engine
    from state_store.state_store import default_fsm_state

    path = tmp_path / "algo_params.json"
    expected = _valid_params()
    _write(path, expected)

    signal_engine._LAST_PARAM_ERROR_SIGNATURE = None
    monkeypatch.setattr(signal_engine, "ALGO_PARAMS_PATH", str(path))
    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(signal_engine, "_load_active_symbols", lambda: ["EUR/USD"])
    monkeypatch.setattr(signal_engine.fsm_runtime, "load_state", default_fsm_state)
    monkeypatch.setattr(
        signal_engine.fsm_runtime,
        "reconcile_state",
        lambda state, now_ts, active_symbols: (state, []),
    )
    monkeypatch.setattr("runtime.market_client.configured_symbols", lambda: None)
    monkeypatch.setattr(
        "runtime.market_client.get_candles",
        lambda symbol, timeframe, **kwargs: [{"stub": True}],
    )
    monkeypatch.setattr(signal_engine.candle_adapter, "normalize", lambda raw, symbol, timeframe: raw)
    monkeypatch.setattr(signal_engine.candle_adapter, "validate", lambda candles: None)

    captured: list[dict] = []

    class StopAfterValidatedDecision(RuntimeError):
        pass

    def _capture_decide(**kwargs):
        captured.append(kwargs["params"])
        raise StopAfterValidatedDecision("validated params reached strategy")

    errors: list[dict] = []
    monkeypatch.setattr(signal_engine, "decide", _capture_decide)
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)

    signal_engine.run_once(
        now_ts=1_800_000_001,
        forced_symbols=["EUR/USD"],
        forced_focus_context=False,
    )

    assert captured == [expected]
    assert any("validated params reached strategy" in str(item.get("error")) for item in errors)
