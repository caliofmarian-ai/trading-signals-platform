"""Historical Finnhub read-only strategy smoke test; NOT a live trading claim."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.railway_finnhub_historical_strategy_probe import (
    _select_no_lookahead_window,
    collect_historical_strategy_probe,
)


T = 1789077300  # Thu 2026-09-10 21:55 UTC, 5min-aligned


def _candle(ts: int, code: str, i: int) -> dict:
    price = 1.1000 + ((i % 25) - 12) * 0.00005
    return {
        "symbol": "EUR/USD",
        "timeframe": code,
        "ts": ts,
        "open": price,
        "high": price + 0.0004,
        "low": price - 0.0004,
        "close": price + 0.00004,
        "volume": 1,
        "complete": True,
        "provider": "FINNHUB",
    }


def _store(path: Path, *, complete: bool = True) -> dict:
    m1 = [_candle(T - i * 60, "M1", i) for i in range(3)]
    # The newest stored head is 3 bars; the older segment is much longer.
    m1 += [_candle(T - (5 + i) * 60, "M1", i) for i in range(451)]
    m5 = [_candle(T - i * 300, "M5", i) for i in range(500)]
    if not complete:
        m1[4]["complete"] = False
    payload = {
        "schema_version": "1.0.0",
        "provider": "FINNHUB",
        "symbol": "EUR/USD",
        "candles": {"M1": m1, "M5": m5},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def _prepare(monkeypatch, canonical_runtime_root: Path):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(canonical_runtime_root))
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "false")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("FINNHUB_MIN_CANDLES", "201")
    filename = canonical_runtime_root / "market_data" / "finnhub_eurusd.json"
    monkeypatch.setenv("FINNHUB_CANDLE_STORE", str(filename))
    return filename


def test_historical_selection_excludes_future_m5_candle():
    m1 = [_candle(T - i * 60, "M1", i) for i in range(25)]
    m5 = [_candle(T - i * 300, "M5", i) for i in range(220)]
    selected = _select_no_lookahead_window(m1, m5, min_m1=21, min_m5=201)
    assert selected is not None
    m1_window, m5_window, cutoff = selected
    assert cutoff == T + 60
    assert len(m1_window) == 21
    assert len(m5_window) == 201
    assert max(row["ts"] + 300 for row in m5_window) <= cutoff
    assert m5_window[0]["ts"] < T


def test_historical_strategy_evaluates_real_window_shape_without_publishing(
    canonical_runtime_root: Path, monkeypatch: pytest.MonkeyPatch
):
    source = _prepare(monkeypatch, canonical_runtime_root)
    _store(source)
    before = source.read_bytes()
    report = collect_historical_strategy_probe(
        base_dir=canonical_runtime_root, now_ts=T + 60 * 60 * 24 * 50,
    )
    assert report["status"] == "HISTORICAL_EVALUATION_COMPLETED"
    assert report["m1_completed_window_bars"] == 201
    assert report["m5_completed_window_bars"] == 201
    assert report["historical_age_days"] >= 49
    assert report["model_decision_object_created"] is True
    assert report["fresh_market_data_proven"] is False
    assert report["telegram_signals_published"] == 0
    assert report["broker_trades_executed"] == 0
    assert report["market_truth_outcomes_created"] == 0
    assert report["hypothetical_win_rate_calculated"] is False
    assert source.read_bytes() == before
    # Neither a market price nor an actionable direction/score leaks to logs.
    result = json.dumps(report)
    for disallowed in ("1.1000", "1.1234", "BUY", "SELL", "score_total", "OPEN_NOW"):
        assert disallowed not in result


def test_missing_store_does_not_create_data_or_decisions(
    canonical_runtime_root: Path, monkeypatch: pytest.MonkeyPatch
):
    source = _prepare(monkeypatch, canonical_runtime_root)
    assert not source.exists()
    report = collect_historical_strategy_probe(base_dir=canonical_runtime_root, now_ts=T + 60)
    assert report["status"] == "STORE_UNAVAILABLE_OR_INVALID"
    assert not source.exists()


def test_only_short_m1_head_yields_no_usable_historical_overlap(
    canonical_runtime_root: Path, monkeypatch: pytest.MonkeyPatch
):
    source = _prepare(monkeypatch, canonical_runtime_root)
    payload = _store(source)
    payload["candles"]["M1"] = payload["candles"]["M1"][:3]
    source.write_text(json.dumps(payload), encoding="utf-8")
    report = collect_historical_strategy_probe(base_dir=canonical_runtime_root, now_ts=T + 3600)
    assert report["status"] == "NO_COMPLETED_HISTORICAL_OVERLAP"


def test_invalid_provenance_and_unsafe_shadow_mode_block(
    canonical_runtime_root: Path, monkeypatch: pytest.MonkeyPatch
):
    source = _prepare(monkeypatch, canonical_runtime_root)
    _store(source)
    monkeypatch.setenv("SHADOW_MODE", "false")
    assert collect_historical_strategy_probe(
        base_dir=canonical_runtime_root, now_ts=T + 3600,
    )["status"] == "SHADOW_MODE_REQUIRED"
    monkeypatch.setenv("SHADOW_MODE", "true")
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["candles"]["M1"][10]["provider"] = "TWELVE_DATA"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = collect_historical_strategy_probe(
        base_dir=canonical_runtime_root, now_ts=T + 3600,
    )
    assert result["status"] == "CANDLE_PROVENANCE_UNVERIFIED"


def test_disallow_symlink_or_outside_runtime_base(
    canonical_runtime_root: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    source = _prepare(monkeypatch, canonical_runtime_root)
    outside = tmp_path / "outside_private_financial_data.json"
    _store(outside)
    source.parent.mkdir(parents=True, exist_ok=True)
    source.symlink_to(outside)
    report = collect_historical_strategy_probe(
        base_dir=canonical_runtime_root, now_ts=T + 3600,
    )
    assert report["status"] == "STORE_PATH_OUTSIDE_GOVERNED_ROOT"
    assert "outside" not in json.dumps(report)
