from __future__ import annotations

import json
from pathlib import Path

from core.shadow_strategy_observer import observe_and_persist


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int) -> list[dict]:
    candles = []
    for index in range(count):
        wave = 0.0 if index == count - 1 else ((index % 20) - 10) * 0.00008
        base = 1.1000 + wave
        candles.append({
            "symbol": "EUR/USD", "timeframe": timeframe, "ts": 1_720_000_000 + index * step,
            "open": base, "high": base + 0.00035, "low": base - 0.00035,
            "close": base + 0.00002, "volume": 100 + index,
        })
    return list(reversed(candles))


def _inputs(runtime_root: Path):
    m1 = _candles(220, timeframe="M1", step=60)
    m1[0]["close"] = m1[0]["open"] + 0.00015
    m5 = _candles(220, timeframe="M5", step=300)
    for candle in m5:
        candle["high"], candle["low"] = 1.1015, 1.0985
    return m1, m5, _params(runtime_root)


def test_observer_uses_existing_candles_and_writes_only_latest_snapshot(
    canonical_runtime_root: Path, tmp_path: Path
) -> None:
    m1, m5, params = _inputs(canonical_runtime_root)
    output = tmp_path / "canonical_shadow_snapshot.json"
    live = {
        "kind": "CONFIRM", "symbol": "EUR/USD", "direction": "BUY",
        "score_total": 77.0, "expiry_minutes": 5, "candle_ts": m1[0]["ts"],
    }

    first = observe_and_persist(
        m1, m5, params, live, observed_ts=1_800_000_000,
        buffer_mode="SMALL", output_path=str(output),
    )
    second = observe_and_persist(
        m1, m5, params, live, observed_ts=1_800_000_002,
        buffer_mode="SMALL", output_path=str(output),
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == second.to_dict()
    assert payload["observed_ts"] == 1_800_000_002
    assert first.candle_ts == second.candle_ts == m1[0]["ts"]
    assert payload["canonical_shadow_only"] is True
    assert payload["signal_handoff_ready"] is False


def test_observer_exposes_real_comparison_fields(canonical_runtime_root: Path, tmp_path: Path) -> None:
    m1, m5, params = _inputs(canonical_runtime_root)
    live = {
        "kind": "PRE", "symbol": "EUR/USD", "direction": "SELL",
        "score_total": 71.0, "expiry_minutes": 4,
    }
    result = observe_and_persist(
        m1, m5, params, live, observed_ts=1_800_000_000,
        buffer_mode="SMALL", output_path=str(tmp_path / "snapshot.json"),
    )

    assert result.live_kind == "PRE"
    assert result.canonical_outcome in {"WAIT", "PREPARE", "CONFIRM", "OPEN_NOW", "REJECT", "DEGRADED"}
    assert result.live_direction == "SELL"
    assert result.canonical_direction in {"BUY", "SELL"}
    assert result.score_difference == result.canonical_score - 71.0
    assert result.signal_handoff_ready is False
