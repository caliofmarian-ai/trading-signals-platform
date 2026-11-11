from __future__ import annotations

import pytest


def test_run_once_reaches_strategy_on_consecutive_finnhub_two_second_ticks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core import signal_engine
    from runtime import market_client

    signal_engine._LAST_PARAM_ERROR_SIGNATURE = None
    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(signal_engine, "_load_algo_params", lambda: {"decision_policy": "PHYSICAL_ONLY_V3"})
    monkeypatch.setattr(
        signal_engine,
        "_load_active_symbols",
        lambda: ["EUR/USD", "GBP/USD", "USD/JPY"],
    )
    monkeypatch.setattr(signal_engine.fsm_runtime, "load_state", lambda: {"watchlist": []})
    monkeypatch.setattr(
        signal_engine.fsm_runtime,
        "reconcile_state",
        lambda state, now_ts, active_symbols: (state, []),
    )
    monkeypatch.setattr(signal_engine, "current_opportunity_signal_id", lambda state, symbol: None)
    monkeypatch.setattr(market_client, "configured_symbols", lambda: ["EUR/USD"])

    monkeypatch.setattr(market_client, "configured_provider", lambda: "FINNHUB")
    snapshot_calls: list[str] = []

    def _get_decision_candles(symbol: str):
        snapshot_calls.append(symbol)
        observed_at = 1_800_000_001 + 2 * len(snapshot_calls) + 0.25
        return [{"stub": "M1"}], [{"stub": "M5"}], observed_at

    monkeypatch.setattr(market_client, "get_finnhub_decision_candles", _get_decision_candles)
    monkeypatch.setattr(market_client, "get_candles", lambda *args, **kwargs: pytest.fail("split read"))
    monkeypatch.setattr(
        signal_engine.candle_adapter,
        "normalize",
        lambda raw, symbol, timeframe: raw,
    )
    monkeypatch.setattr(signal_engine.candle_adapter, "validate", lambda candles: None)

    decide_calls: list[dict] = []

    class StopAfterSelection(RuntimeError):
        pass

    def _decide(**kwargs):
        decide_calls.append(kwargs)
        raise StopAfterSelection("selection reached strategy")

    errors: list[dict] = []
    monkeypatch.setattr(signal_engine, "decide", _decide)
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)

    signal_engine.run_once(now_ts=1_800_000_002)
    signal_engine.run_once(now_ts=1_800_000_004)

    assert len(decide_calls) == 2
    assert [call["want_open_now"] for call in decide_calls] == [False, False]
    assert snapshot_calls == ["EUR/USD", "EUR/USD"]
    assert [call["observation_ts"] for call in decide_calls] == [
        1_800_000_003.25, 1_800_000_005.25,
    ]
    assert all(call["candles_m1"] == [{"stub": "M1"}] for call in decide_calls)
    assert all(call["candles_m5"] == [{"stub": "M5"}] for call in decide_calls)
    assert len(errors) == 2
    assert all("selection reached strategy" in item["error"] for item in errors)


def test_provider_scope_does_not_force_symbol_outside_owner_active_universe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core import signal_engine
    from runtime import market_client

    signal_engine._LAST_PARAM_ERROR_SIGNATURE = None
    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(signal_engine, "_load_algo_params", lambda: {})
    monkeypatch.setattr(signal_engine, "_load_active_symbols", lambda: ["GBP/USD"])
    monkeypatch.setattr(signal_engine.fsm_runtime, "load_state", lambda: {"watchlist": []})
    monkeypatch.setattr(
        signal_engine.fsm_runtime,
        "reconcile_state",
        lambda state, now_ts, active_symbols: (state, []),
    )
    monkeypatch.setattr(market_client, "configured_symbols", lambda: ["EUR/USD"])
    monkeypatch.setattr(
        market_client,
        "get_candles",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("provider scope must not force inactive EUR/USD")
        ),
    )

    signal_engine.run_once(now_ts=1_800_000_002)
