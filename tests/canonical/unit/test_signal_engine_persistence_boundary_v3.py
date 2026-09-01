from __future__ import annotations

from types import SimpleNamespace

import pytest


def test_persistence_failure_blocks_execution_and_distribution(monkeypatch: pytest.MonkeyPatch) -> None:
    from core import signal_engine

    decision = SimpleNamespace(
        kind="PRE",
        signal_id="sig-persist-boundary",
        setup=SimpleNamespace(
            symbol="EUR/USD",
            timeframe="M1",
            cycle_id="cycle-persist-boundary",
            evaluated_ts=1_800_000_000,
            direction="BUY",
        ),
    )
    evaluation = SimpleNamespace(decision=decision)
    persistent = SimpleNamespace(state_changed=True, next_state={"watchlist": ["EUR/USD"]})

    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(signal_engine, "_load_algo_params", lambda: {})
    monkeypatch.setattr(signal_engine, "_load_active_symbols", lambda: ["EUR/USD"])
    monkeypatch.setattr(signal_engine.fsm_runtime, "load_state", lambda: {})
    monkeypatch.setattr(
        signal_engine.fsm_runtime,
        "reconcile_state",
        lambda state, now_ts, active_symbols: (state, []),
    )
    monkeypatch.setattr(signal_engine, "decide", lambda **kwargs: evaluation)
    monkeypatch.setattr(signal_engine, "_log_decision_evaluated", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(signal_engine, "advance_persistent_fsm", lambda *_args, **_kwargs: persistent)
    monkeypatch.setattr(
        signal_engine.fsm_runtime,
        "save_state",
        lambda _state: (_ for _ in ()).throw(RuntimeError("persist failed")),
    )

    execution_calls: list[object] = []
    routing_calls: list[object] = []
    errors: list[dict] = []
    monkeypatch.setattr(
        signal_engine,
        "prepare_signal_execution",
        lambda *args, **kwargs: execution_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        signal_engine.distribution_router,
        "route",
        lambda *args, **kwargs: routing_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)

    class _MarketClient:
        @staticmethod
        def configured_symbols():
            return None

        @staticmethod
        def get_candles(symbol, timeframe, **kwargs):
            return [{"stub": True}]

    monkeypatch.setattr("runtime.market_client.configured_symbols", _MarketClient.configured_symbols)
    monkeypatch.setattr("runtime.market_client.get_candles", _MarketClient.get_candles)
    monkeypatch.setattr(signal_engine.candle_adapter, "normalize", lambda raw, symbol, timeframe: raw)
    monkeypatch.setattr(signal_engine.candle_adapter, "validate", lambda candles: None)

    signal_engine.run_once(
        now_ts=1_800_000_001,
        forced_symbols=["EUR/USD"],
        forced_focus_context=False,
    )

    assert execution_calls == []
    assert routing_calls == []
    assert len(errors) == 1
    assert "persist failed" in errors[0]["error"]
