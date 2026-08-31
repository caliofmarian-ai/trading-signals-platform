from core import signal_engine


def test_shadow_observer_can_be_disabled_without_work(monkeypatch) -> None:
    monkeypatch.setenv("CANONICAL_SHADOW_ENABLED", "false")
    monkeypatch.setattr(
        signal_engine.observability_logger,
        "log_error",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected error")),
    )

    signal_engine._observe_canonical_shadow([], [], {}, {}, now_ts=1, buffer_mode="SMALL")


def test_shadow_waits_silently_for_complete_inputs(monkeypatch) -> None:
    monkeypatch.setenv("CANONICAL_SHADOW_ENABLED", "true")
    errors = []
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)

    signal_engine._observe_canonical_shadow([], [], {}, {"symbol": "EUR/USD"}, now_ts=1, buffer_mode="SMALL")

    assert errors == []


def test_shadow_failure_never_escapes_into_live_engine(monkeypatch) -> None:
    from core import shadow_strategy_observer

    monkeypatch.setenv("CANONICAL_SHADOW_ENABLED", "true")
    errors = []
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)
    monkeypatch.setattr(
        shadow_strategy_observer,
        "observe_and_persist",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("shadow failed")),
    )
    params = {
        "strategy_v2": {"rsi_period": 14, "ema_slow": 200},
        "score_thresholds": {}, "expiry_limits_minutes": {}, "buffer_multipliers": {},
        "spike_filters": {}, "trend_time_adjust": {}, "structure_factor": {},
    }
    candles = [{} for _ in range(201)]

    signal_engine._observe_canonical_shadow(
        candles, candles, params, {"symbol": "EUR/USD"}, now_ts=1, buffer_mode="SMALL"
    )

    assert len(errors) == 1
    assert errors[0]["error_type"] == "canonical_shadow_observation_unavailable"
