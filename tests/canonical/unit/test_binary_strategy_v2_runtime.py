from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

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


def test_v2_preserves_real_input_evidence(canonical_runtime_root: Path) -> None:
    m1, m5 = _candles(220, "M1", 60), _candles(220, "M5", 300)
    before_m1, before_m5 = copy.deepcopy(m1), copy.deepcopy(m5)
    result = decide(m1, m5, _params(canonical_runtime_root), cycle_id="preserve-inputs")
    assert isinstance(result, BinaryStrategyV2Evaluation)
    assert m1 == before_m1
    assert m5 == before_m5


def test_runtime_uses_v2_evaluation_and_never_routes_it(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(signal_engine.distribution_router, "route", lambda *_args: (_ for _ in ()).throw(AssertionError("route must remain blocked")))
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)

    signal_engine.run_once(now_ts=1_800_000_000)
    assert len(errors) == 1
    assert "object has no attribute 'decision'" in errors[0]["error"]
    # Even a malformed V2 evaluation fails closed before distribution.


def test_runtime_records_governed_execution_gate_without_distribution(monkeypatch: pytest.MonkeyPatch) -> None:
    signal_engine = importlib.import_module("core.signal_engine")
    market_client = importlib.import_module("runtime.market_client")
    m1, m5 = _candles(220, "M1", 60), _candles(220, "M5", 300)
    events: list[dict] = []
    errors: list[dict] = []
    calls: list[tuple] = []

    decision = SimpleNamespace(
        kind="OPEN_NOW",
        signal_id="sig-v2-live-observability",
        setup=SimpleNamespace(evaluated_ts=1_720_010_000, direction="BUY"),
        score=SimpleNamespace(total=86.0),
        to_dict=lambda: {"kind": "OPEN_NOW", "signal_id": "sig-v2-live-observability"},
    )
    fsm = SimpleNamespace(
        outcome="OPEN_NOW",
        reason_family="EXECUTION_READY",
        execution_ready=True,
        reasons=(),
        explanation="Canonical OPEN_NOW candidate.",
    )
    evaluation = SimpleNamespace(
        strategy_version="2.0.0",
        canonical_spec="ALGO_SPEC_v2.0.0",
        cycle_id="cycle-live-observability",
        decision=decision,
        fsm=fsm,
        signal_handoff_ready=False,
    )
    persistent = SimpleNamespace(
        accepted=True,
        state_changed=False,
        transition_event=None,
        candidate_ready=True,
        reason="SIGNAL_EVENT_CANDIDATE_READY",
    )
    execution_trace = {
        "outcome": "DEFERRED",
        "reason": "V2_DISTRIBUTION_NOT_ENABLED",
        "signal_id": decision.signal_id,
        "stage": "OPEN_NOW",
        "execution_attempt_id": "binary-v2:sig-v2-live-observability:OPEN_NOW:1800000000",
        "created_ts": 1_800_000_000,
        "distribution_allowed": False,
        "candidate": {"signal_id": decision.signal_id, "stage": "OPEN_NOW"},
    }
    execution = SimpleNamespace(
        outcome="DEFERRED",
        reason="V2_DISTRIBUTION_NOT_ENABLED",
        distribution_allowed=False,
        to_dict=lambda: execution_trace,
    )

    monkeypatch.setattr(signal_engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(signal_engine, "_load_algo_params", lambda: {})
    monkeypatch.setattr(signal_engine, "_load_active_symbols", lambda: ["EUR/USD"])
    monkeypatch.setattr(signal_engine.fsm_runtime, "load_state", lambda: {})
    monkeypatch.setattr(signal_engine.fsm_runtime, "reconcile_state", lambda state, now_ts, active_symbols: (state, []))
    monkeypatch.setattr(market_client, "configured_symbols", lambda: None)
    monkeypatch.setattr(market_client, "get_candles", lambda symbol, interval: list(reversed(m1 if interval == "1min" else m5)))
    monkeypatch.setattr(signal_engine, "decide", lambda **kwargs: evaluation)
    monkeypatch.setattr(signal_engine, "advance_persistent_fsm", lambda state, decision_arg, now_ts: persistent)

    def fake_prepare(persistent_arg, decision_arg, *, buffer_mode, created_ts):
        calls.append((persistent_arg, decision_arg, buffer_mode, created_ts))
        return execution

    monkeypatch.setattr(signal_engine, "prepare_signal_execution", fake_prepare)
    monkeypatch.setattr(signal_engine.distribution_router, "route", lambda *_args: (_ for _ in ()).throw(AssertionError("distribution must remain blocked")))
    monkeypatch.setattr(signal_engine.observability_logger, "log_event", events.append)
    monkeypatch.setattr(signal_engine.observability_logger, "log_error", errors.append)

    signal_engine.run_once(now_ts=1_800_000_000)

    assert errors == []
    assert calls == [(persistent, decision, "MEDIUM", 1_800_000_000)]
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "decision"
    assert event["data"]["decision_kind"] == "OPEN_NOW"
    assert event["data"]["signal_id"] == "sig-v2-live-observability"
    assert event["data"]["debug"]["execution_outcome"] == "DEFERRED"
    assert event["data"]["debug"]["execution_reason"] == "V2_DISTRIBUTION_NOT_ENABLED"
    assert event["data"]["debug"]["distribution_allowed"] is False
    assert event["data"]["debug"]["execution_gate"] == execution_trace
    assert "strategy" not in event["data"]
