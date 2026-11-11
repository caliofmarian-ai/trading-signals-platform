"""Synthetic fixtures test data boundaries; none are calibration evidence."""
import json

import pytest

NOW = 1_800_000_030


@pytest.fixture
def physical_history(canonical_runtime_root):
    from tests.canonical.integration.test_binary_strategy_v2 import _inputs
    from core.physical_params import migrate_physical_params
    m1, m5, params = _inputs(canonical_runtime_root)
    for step, candles in ((60, m1), (300, m5)):
        for i, bar in enumerate(candles):
            bar.update(ts=1_800_000_000-i*step, complete=i > 0, provider="FINNHUB")
    return canonical_runtime_root, m1, m5, migrate_physical_params(params)


def _feed(physical_history, *, gap=15):
    root, m1, m5, params = physical_history
    from runtime.finnhub_market_data import FinnhubForexFeed
    feed = FinnhubForexFeed(token="OFFLINE_TEST_ONLY", clock=lambda: NOW,
                            store_path=root / "market_data/test.json", physical_params=params)
    feed._stream_started = True
    feed._last_price_ts = NOW
    feed._valid_trade_tick_count = 1
    if gap is not None:
        del m5[gap]
    feed._candles = {"M1": m1, "M5": m5}
    return feed, params


def test_old_gap_does_not_reset_long_context_or_cross_temporal_math(physical_history):
    from core.market_model import evaluate_market, _atr
    feed, params = _feed(physical_history)
    health = feed.health()
    assert health["history_ready"]
    assert health["contiguous_candle_counts"]["M5"] == 15
    assert health["minimum_candles_by_timeframe"]["M5"] == 201
    assert health["minimum_contiguous_candles_by_timeframe"] == {"M1": 22, "M5": 15}
    m1, m5 = feed.get_candles("EUR/USD", "M1"), feed.get_candles("EUR/USD", "M5")
    assert len(m5) == 219 and len(m5) > health["contiguous_candle_counts"]["M5"]
    market = evaluate_market(m1, m5, params, buffer_mode="SMALL", observation_ts=NOW)
    assert market.evidence.m5_context_gap_count == 1
    assert market.evidence.m5_recent_contiguous_candles == 15
    assert market.evidence.m5_context_candles == 219
    recent = list(reversed(m5[:15]))
    assert market.evidence.atr_m5 == _atr([b["high"] for b in recent],
        [b["low"] for b in recent], [b["close"] for b in recent])
    assert market.evidence.m1_speed_window.completed_intervals == 20
    assert market.evidence.m1_speed_window.completed_candles == 21


@pytest.mark.parametrize("gap", [1, 7, 14])
def test_recent_atr_gaps_are_still_blocked(physical_history, gap):
    from runtime.finnhub_market_data import FinnhubInsufficientHistory
    feed, _ = _feed(physical_history, gap=gap)
    assert not feed.health()["history_ready"]
    with pytest.raises(FinnhubInsufficientHistory, match=f"{gap}/15"):
        feed.get_candles("EUR/USD", "M5")


def test_recent_speed_gap_is_not_hidden_by_saved_m1_bars(physical_history):
    from runtime.finnhub_market_data import FinnhubInsufficientHistory
    feed, _ = _feed(physical_history)
    del feed._candles["M1"][20]
    with pytest.raises(FinnhubInsufficientHistory, match="20/22"):
        feed.get_candles("EUR/USD", "M1")
    assert not feed.health()["history_ready"]


def test_no_context_or_stale_price_is_not_made_eligible(physical_history):
    from runtime.finnhub_market_data import FinnhubInsufficientHistory, FinnhubStaleMarketData
    feed, _ = _feed(physical_history)
    original = feed._candles["M5"]
    feed._candles["M5"] = original[:15]
    with pytest.raises(FinnhubInsufficientHistory, match="15/201"):
        feed.get_candles("EUR/USD", "M5")
    feed._candles["M5"] = original
    feed._last_price_ts = NOW-11
    with pytest.raises(FinnhubStaleMarketData):
        feed.get_candles("EUR/USD", "M5")


def test_restart_restores_real_context_without_rebuilding_201_bars(physical_history):
    from runtime.finnhub_market_data import FinnhubForexFeed
    feed, params = _feed(physical_history)
    feed._persist_store()
    persisted = json.loads(feed.store_path.read_text())
    again = FinnhubForexFeed(token="OFFLINE_TEST_ONLY", clock=lambda: NOW,
                            store_path=feed.store_path, physical_params=params)
    again._stream_started = True
    again.ingest_message({"type": "trade", "data": [{"s": "OANDA:EUR_USD",
        "p": feed._candles["M1"][0]["close"], "t": NOW*1000}]})
    assert again.health()["history_ready"]
    assert len(again.get_candles("EUR/USD", "M5")) == 219
    assert again._candles["M5"][16:] == persisted["candles"]["M5"][16:]


def test_pivot_cannot_use_neighbors_across_missing_bars_or_forming_bar():
    from core.sr_corridor_engine import _structural_levels
    bars = [{"ts": 30000-i*300, "open": 1.05, "high": 1.1, "low": 1.0,
             "close": 1.05, "complete": True} for i in range(12)]
    bars[4]["high"] = 1.3
    bars[5]["ts"] -= 300
    for i in range(6, len(bars)):
        bars[i]["ts"] -= 300
    assert 1.3 in _structural_levels(bars)[1]
    assert 1.3 not in _structural_levels(bars, gap_aware=True)[1]
    bars = [{"ts": 30000-i*300, "open": 1.05, "high": 1.1, "low": 1.0,
             "close": 1.05, "complete": i != 0} for i in range(12)]
    bars[2]["high"] = 1.3
    assert 1.3 not in _structural_levels(bars, gap_aware=True)[1]


def test_existing_v3_policy_migrates_once_and_invalidates_old_calibration_hash(physical_history):
    root, _, _, params = physical_history
    from core.physical_params import load_physical_runtime_algo_params
    from core.runtime_execution_calibration import algo_params_sha256
    old = {k: v for k, v in params.items() if k != "history_policy"}
    path = root / "config/algo_params.json"
    path.write_text(json.dumps(old))
    original = path.read_bytes()
    migrated = load_physical_runtime_algo_params(str(path))
    assert migrated == params
    assert algo_params_sha256(migrated) != algo_params_sha256(old)
    assert load_physical_runtime_algo_params(str(path)) == migrated
    backups = list((path.parent / "policy_migrations").glob("v3_before_recent_history_*.json"))
    assert len(backups) == 1 and backups[0].read_bytes() == original


def test_research_does_not_read_old_data_policy_cohort(physical_history, monkeypatch):
    root, _, _, _ = physical_history
    monkeypatch.setenv("OWNER_SIGNAL_DELIVERY_ENABLED", "true")
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "123456789")
    monkeypatch.setenv("SHADOW_MODE", "true")
    monkeypatch.setenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "true")
    from intelligence import physical_expiry_calibration as study
    old = root / "analytics/physical_v3_expiry_calibration/state.json"
    old.parent.mkdir(parents=True)
    old.write_bytes(b'{"preserved":"old policy cohort"}')
    report = study.summary(now_ts=NOW)
    assert report["unique_entry_experiments"] == 0
    assert report["history_policy"] == "RECENT_PHYSICS_WITH_SAVED_CONTEXT_V1"
    assert study._path().name == "recent_history_state.json"
    assert old.read_bytes() == b'{"preserved":"old policy cohort"}'


def test_status_explains_separate_saved_context_and_recent_window(physical_history):
    from runtime.market_client import _history_status_evidence
    from core.telegram_app_nav import render_status_page
    feed, _ = _feed(physical_history)
    health = feed.health()
    evidence = _history_status_evidence(health)
    text, _ = render_status_page({**evidence,
        "market_data_candle_counts": health["candle_counts"], "market_data_history_ready": True})
    assert "Saved market context" in text
    assert "Recent physical window: M1 220/22; M5 15/15" in text


@pytest.mark.parametrize("head_exclusion", ["forming", "isolated"])
def test_flat_structural_boundary_comes_from_a_confirmed_window(head_exclusion):
    from core.sr_corridor_engine import _structural_levels

    bars = [
        {"ts": 30000 - i * 300, "high": 1.1, "low": 1.09, "complete": True}
        for i in range(80)
    ]
    # This unconfirmed candle is close enough to the plateau to trigger
    # the horizontal-level fallback.
    bars[0].update(high=1.100009, low=1.089991)
    if head_exclusion == "forming":
        bars[0]["complete"] = False
    else:
        bars[0]["ts"] += 300

    assert _structural_levels(bars, gap_aware=True) == ((1.09,), (1.1,))
    assert _structural_levels(bars) == ((1.089991,), (1.100009,))
