"""Offline regression: M1 recovery must not wait for the M5 EMA lookback."""

from __future__ import annotations

import importlib
import json

import pytest


NOW = 120_002


def _bar(ts, code, index):
    price = 1.12 - index * 0.00003
    return {
        "symbol": "EUR/USD", "timeframe": code, "ts": ts,
        "open": price, "high": price + 0.0002, "low": price - 0.0001,
        "close": price + 0.0001, "complete": index > 0,
        "provider": "FINNHUB", "volume": 1,
    }


def _feed(tmp_path, monkeypatch, *, m1=21, m5=201):
    module = importlib.import_module("runtime.finnhub_market_data")
    monkeypatch.setenv("FINNHUB_MIN_CANDLES", "201")
    monkeypatch.delenv("FINNHUB_MIN_M1_CANDLES", raising=False)
    feed = module.FinnhubForexFeed(
        token="offline", store_path=tmp_path / "candles.json", clock=lambda: NOW,
    )
    feed._stream_started = True
    feed._last_price_ts = NOW - 2
    feed._valid_trade_tick_count = 1
    feed._candles = {
        "M1": [_bar(120_000 - i * 60, "M1", i) for i in range(m1)],
        "M5": [_bar(120_000 - i * 300, "M5", i) for i in range(m5)],
    }
    return module, feed


def test_21_real_m1_bars_reach_the_unchanged_market_model(
    canonical_runtime_root, tmp_path, monkeypatch, capsys,
):
    from core.market_model import evaluate_market
    from core.strategy_v2 import decide

    _, feed = _feed(tmp_path, monkeypatch)
    params = json.loads((canonical_runtime_root / "config" / "algo_params.json").read_text())
    result = evaluate_market(feed.get_candles("EUR/USD", "M1"),
                             feed.get_candles("EUR/USD", "M5"), params)
    assert result.context.directional_effective_speed > 0
    evaluation = decide(feed.get_candles("EUR/USD", "M1"),
                        feed.get_candles("EUR/USD", "M5"), params)
    assert evaluation.canonical_spec == "ALGO_SPEC_v3.0.0"
    assert evaluation.signal_handoff_ready is False
    assert feed.health()["history_ready"] is True
    assert feed.health()["minimum_candles_by_timeframe"] == {"M1": 21, "M5": 201}
    feed._emit_stream_observation("TRANSPORT_PONG_CONFIRMED")
    record = json.loads(capsys.readouterr().out.strip().split(" ", 1)[1])
    assert record["required_candles_by_timeframe"] == {"M1": 21, "M5": 201}
    assert record["required_candles_each"] is None
    assert record["usable_real_history_and_fresh_tick"] is True


@pytest.mark.parametrize("m1,m5,code,missing", [(20, 201, "M1", "20/21"),
                                               (21, 200, "M5", "200/201")])
def test_short_history_still_blocks_the_required_timeframe(tmp_path, monkeypatch, m1, m5, code, missing):
    module, feed = _feed(tmp_path, monkeypatch, m1=m1, m5=m5)
    assert feed.health()["history_ready"] is False
    with pytest.raises(module.FinnhubInsufficientHistory, match=missing):
        feed.get_candles("EUR/USD", code)


def test_all_available_contiguous_m1_bars_are_used_without_crossing_a_gap(tmp_path, monkeypatch):
    _, feed = _feed(tmp_path, monkeypatch, m1=50)
    feed._candles["M1"].append(_bar(120_000 - 51 * 60, "M1", 51))
    assert len(feed.get_candles("EUR/USD", "M1")) == 50
    assert feed.health()["history_ready"] is True


def test_gap_inside_21_bar_window_cannot_be_hidden_by_older_history(tmp_path, monkeypatch):
    module, feed = _feed(tmp_path, monkeypatch, m1=300)
    del feed._candles["M1"][20]
    with pytest.raises(module.FinnhubInsufficientHistory, match="20/21"):
        feed.get_candles("EUR/USD", "M1")
    assert feed.health()["history_ready"] is False


def test_freshness_and_higher_rsi_requirement_are_not_relaxed(
    canonical_runtime_root, tmp_path, monkeypatch,
):
    from core.market_model import MarketModelUnavailable, evaluate_market

    module, feed = _feed(tmp_path, monkeypatch)
    params = json.loads((canonical_runtime_root / "config" / "algo_params.json").read_text())
    params["strategy_v2"]["rsi_period"] = 30
    with pytest.raises(MarketModelUnavailable, match="31 real candles"):
        evaluate_market(feed.get_candles("EUR/USD", "M1"),
                        feed.get_candles("EUR/USD", "M5"), params)
    feed._last_price_ts = NOW - 11
    with pytest.raises(module.FinnhubStaleMarketData):
        feed.get_candles("EUR/USD", "M1")


def test_m1_override_is_independent_of_legacy_m5_environment(tmp_path, monkeypatch):
    module, _ = _feed(tmp_path, monkeypatch)
    monkeypatch.setenv("FINNHUB_MIN_M1_CANDLES", "31")
    feed = module.FinnhubForexFeed(token="offline", store_path=tmp_path / "empty.json")
    assert feed.minimum_candles_by_timeframe == {"M1": 31, "M5": 201}
    explicit = module.FinnhubForexFeed(token="offline", minimum_candles=2,
                                      store_path=tmp_path / "empty.json")
    assert explicit.minimum_candles_by_timeframe == {"M1": 2, "M5": 2}
    monkeypatch.setenv("FINNHUB_MIN_M1_CANDLES", "501")
    with pytest.raises(module.FinnhubConfigurationError, match="FINNHUB_MIN_M1_CANDLES"):
        module.FinnhubForexFeed(token="offline", store_path=tmp_path / "empty.json")


def test_runtime_snapshot_and_status_show_timeframe_minima_and_contiguous_counts(
    canonical_runtime_root, tmp_path, monkeypatch,
):
    from core.operational_snapshot import build_status_snapshot
    from core.telegram_app_nav import render_status_page
    from runtime import market_client, runtime_status

    _, feed = _feed(tmp_path, monkeypatch)
    monkeypatch.setattr(market_client, "configured_provider", lambda: "FINNHUB")
    monkeypatch.setattr(market_client, "_FINNHUB_FEED", feed)
    market_client.get_candles("EUR/USD", "M1")
    evidence = runtime_status.read_status()
    snapshot = build_status_snapshot(evidence)
    assert snapshot["market_data_minimum_candles_by_timeframe"] == {"M1": 21, "M5": 201}
    assert snapshot["market_data_contiguous_candle_counts"] == {"M1": 21, "M5": 201}
    text, _ = render_status_page(snapshot)
    assert "Real contiguous history: M1 21/21; M5 201/201" in text


def test_provider_without_timeframe_minima_clears_previous_finnhub_requirements():
    from runtime.market_client import _history_status_evidence

    assert _history_status_evidence({"minimum_candles": 201}) == {
        "market_data_minimum_candles_by_timeframe": {"M1": 201, "M5": 201},
        "market_data_contiguous_candle_counts": None,
    }
