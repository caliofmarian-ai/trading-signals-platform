from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

from core.market_model import MarketModelUnavailable
from core.strategy_v2 import BinaryStrategyV2Evaluation, decide


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, timeframe: str, step: int) -> list[dict]:
    rows = []
    for index in range(count):
        base = 1.1000 + ((index % 25) - 12) * 0.00005
        rows.append({
            "symbol": "EUR/USD", "timeframe": timeframe,
            "ts": 1_720_000_000 + index * step,
            "open": base, "high": base + 0.0004,
            "low": base - 0.0004, "close": base + 0.00004,
            "volume": 100 + index,
        })
    return list(reversed(rows))


@pytest.mark.parametrize("invalid_series", ["m1", "m5"])
def test_v2_rejects_oldest_first_inputs(canonical_runtime_root: Path, invalid_series: str) -> None:
    m1, m5 = _candles(220, "M1", 60), _candles(220, "M5", 300)
    if invalid_series == "m1":
        m1.reverse()
    else:
        m5.reverse()
    with pytest.raises(MarketModelUnavailable, match="newest-first"):
        decide(m1, m5, _params(canonical_runtime_root))


def test_v2_requires_complete_real_history(canonical_runtime_root: Path) -> None:
    with pytest.raises(MarketModelUnavailable, match="201 real candles"):
        decide(_candles(30, "M1", 60), _candles(30, "M5", 300), _params(canonical_runtime_root))


def test_v2_preserves_real_input_evidence_and_exposes_trade_physics(canonical_runtime_root: Path) -> None:
    m1, m5 = _candles(220, "M1", 60), _candles(220, "M5", 300)
    before_m1, before_m5 = copy.deepcopy(m1), copy.deepcopy(m5)
    result = decide(m1, m5, _params(canonical_runtime_root), cycle_id="preserve-inputs")
    assert isinstance(result, BinaryStrategyV2Evaluation)
    assert result.canonical_spec == "ALGO_SPEC_v3.0.0"
    assert result.trade_physics == result.scoring.trade_physics
    assert result.decision.score.trade_physics is not None
    assert m1 == before_m1
    assert m5 == before_m5


def test_runtime_fails_closed_before_execution_for_malformed_v2_evaluation(monkeypatch: pytest.MonkeyPatch) -> None:
    signal_engine = importlib.import_module("core.signal_engine")
    market_client = importlib.import_module("runtime.market_client")
    m1, m5 = _candles(220, "M1", 60), _candles(220, "M5", 300)
    evaluation = object()
    errors: list[dict] = []

    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(signal_engine, "_load_algo_params", lambda: {})
    monkeypatch.setattr(signal_engine, "_load_active_symbols", lambda: ["EUR/USD"])
    monkeypatch.setattr(signal_engine.fsm_runtime, "load_state", lambda: {})
    monkeypatch.setattr(signal_engine.fsm_runtime, "reconcile_state", lambda state, now_ts, active_symbols: (state, []))
    monkeypatch.setattr(market_client, "configured_symbols", lambda: None)
    monkeypatch.setattr(market_client, "get_candles", lambda symbol, interval: list(reversed(m1 if interval == "1min" else m5)))
    monkeypatch.setattr(signal_engine, "decide", lambda **kwargs: evaluation)
    monkeypatch.setattr(
        signal_engine,
        "prepare_signal_execution",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("execution must not run")),
    )
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)

    signal_engine.run_once(now_ts=1_800_000_000)
    assert len(errors) == 1
    assert "object has no attribute 'decision'" in errors[0]["error"]
