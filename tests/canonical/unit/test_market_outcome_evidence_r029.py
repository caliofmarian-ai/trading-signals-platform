from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core import market_outcome_evidence as market


NOW = int(datetime(2026, 10, 30, 9, 0, tzinfo=timezone.utc).timestamp())


def _trade(
    trade_id: str = "S-1",
    *,
    outcome: str = "WIN",
    symbol: str = "EUR/USD",
    provider: str = "FINNHUB",
    timeframe: str = "M1",
    strategy_version: str | None = "2.0.0",
    direction: str = "BUY",
    open_ts: int = NOW - 1000,
    expiry_lag: int = 1,
) -> dict:
    entry = 1.1
    price = entry if outcome == "DRAW" else (
        entry + 0.0002 if (outcome == "WIN") == (direction == "BUY")
        else entry - 0.0002
    )
    expiry = open_ts + 300
    observed = expiry + expiry_lag
    return {
        "trade_id": trade_id,
        "signal_id": trade_id,
        "truth_domain": "MARKET_TRUTH",
        "telemetry_status": "FINALIZED",
        "telemetry_version": "3.0.0",
        "telemetry_specification": "TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0",
        "symbol": symbol,
        "timeframe": timeframe,
        "market_provider": provider,
        "strategy_version": strategy_version,
        "direction": direction,
        "entry_price": entry,
        "open_ts": open_ts,
        "finalized_ts": max(open_ts + 601, observed + 1),
        "expiry_price": price,
        "result_at_expiry": outcome,
        "label_observation_ts": observed,
        "checkpoints": {
            "mid_expiry": {
                "state": "OBSERVED", "price": price,
                "target_ts": open_ts + 150, "observed_ts": open_ts + 151,
                "provider": provider,
            },
            "post_1m": {
                "state": "OBSERVED", "price": price,
                "target_ts": expiry + 60, "observed_ts": expiry + 61,
                "provider": provider,
            },
            "post_3m": {
                "state": "OBSERVED", "price": price,
                "target_ts": expiry + 180, "observed_ts": expiry + 181,
                "provider": provider,
            },
            "post_5m": {
                "state": "OBSERVED", "price": price,
                "target_ts": expiry + 300, "observed_ts": expiry + 301,
                "provider": provider,
            },
            "expiry": {
                "state": "OBSERVED",
                "price": price,
                "target_ts": expiry,
                "observed_ts": observed,
                "provider": provider,
                "directional_result": outcome,
            }
        },
    }


def _write(path: Path, rows: list[dict], *, malformed=False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row) for row in rows]
    if malformed:
        lines.append("{bad-json")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _snapshot(tmp_path: Path, rows: list[dict], *, days: int = 7, malformed=False):
    path = _write(tmp_path / "telemetry.jsonl", rows, malformed=malformed)
    return market.build_market_snapshot(range_days=days, now_ts=NOW, path=path)


def test_valid_finalized_market_truth_segment_has_bounded_descriptive_rate(tmp_path: Path):
    rows = [_trade(f"WIN-{i}") for i in range(5)]
    rows += [_trade(f"LOSS-{i}", outcome="LOSS") for i in range(2)]
    rows += [_trade("DRAW-1", outcome="DRAW")]
    result = _snapshot(tmp_path, rows)
    assert result["status"] == "OBSERVED"
    assert result["truth_domain"] == "MARKET_TRUTH"
    assert result["verified_finalized_trade_count"] == 8
    seg = result["segments"][0]
    assert (seg["wins"], seg["losses"], seg["draws"]) == (5, 2, 1)
    assert seg["decisive_sample"] == 7
    assert seg["descriptive_win_rate_percent"] == 71.43
    ci = seg["wilson_95_interval_percent"]
    assert 0 < ci["lower"] < 71.43 < ci["upper"] < 100
    assert seg["statistical_proof_or_live_payout"] is False
    assert result["profit_or_broker_performance"] is None


def test_small_decisive_sample_never_produces_win_rate(tmp_path: Path):
    result = _snapshot(tmp_path, [_trade("A"), _trade("B", outcome="LOSS")])
    assert result["status"] == "OBSERVED"
    seg = result["segments"][0]
    assert seg["decisive_sample"] == 2
    assert seg["insufficient_sample"] is True
    assert seg["descriptive_win_rate_percent"] is None
    assert seg["wilson_95_interval_percent"] is None


def test_draws_never_increase_decisive_win_rate_denominator(tmp_path: Path):
    rows = [_trade(f"W{i}") for i in range(5)]
    rows += [_trade(f"D{i}", outcome="DRAW") for i in range(7)]
    result = _snapshot(tmp_path, rows)
    seg = result["segments"][0]
    assert seg["decisive_sample"] == 5
    assert seg["total_finalized"] == 12
    assert seg["descriptive_win_rate_percent"] == 100.0
    assert seg["wilson_95_interval_percent"]["lower"] < 100.0


def test_symbols_provider_and_strategy_versions_are_never_mixed(tmp_path: Path):
    rows = [_trade(f"F{i}", provider="FINNHUB") for i in range(5)]
    rows += [_trade(f"T{i}", provider="TWELVE_DATA", strategy_version="3.0.0") for i in range(2)]
    rows += [_trade("C1", symbol="BTC/USDT", provider="FINNHUB")]
    result = _snapshot(tmp_path, rows)
    assert result["segment_count"] == 3
    assert result["segments"][0]["market_provider"] == "FINNHUB"
    assert result["segments"][0]["decisive_sample"] == 5
    assert result["ranked_by"] == "DECISIVE_SAMPLE_DESC_NOT_WIN_RATE"


def test_missing_and_oversized_sources_are_unknown_not_zero(tmp_path: Path):
    missing = market.build_market_snapshot(now_ts=NOW, path=str(tmp_path / "missing"))
    assert missing["status"] == "UNKNOWN"
    assert missing["verified_finalized_trade_count"] is None
    assert "UNKNOWN — not zero" in market.render_market_summary(missing)
    big = tmp_path / "oversized.log"
    with big.open("wb") as stream:
        stream.truncate(market.MAX_SOURCE_BYTES + 1)
    oversized = market.build_market_snapshot(now_ts=NOW, path=str(big))
    assert oversized["status"] == "UNKNOWN"
    assert oversized["reason"] == "SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN"


def test_community_and_operational_truth_never_contribute_market_labels(tmp_path: Path):
    fake_community = _trade("USER-VOTE")
    fake_community["truth_domain"] = "COMMUNITY_TRUTH"
    fake_operational = _trade("MANUAL-REPORT")
    fake_operational["truth_domain"] = "OPERATIONAL_TRUTH"
    fake_operational["result_at_expiry"] = "MISSED"
    result = _snapshot(tmp_path, [fake_community, fake_operational, _trade("REAL")])
    assert result["verified_finalized_trade_count"] == 1
    assert result["quality"]["other_truth_excluded"] == 2
    assert result["segments"][0]["descriptive_win_rate_percent"] is None


def test_incomplete_legacy_and_malformed_records_are_visible_as_quality_not_wins(tmp_path: Path):
    incomplete = _trade("OPEN")
    incomplete["telemetry_status"] = "INCOMPLETE_MARKET_EVIDENCE"
    historical = _trade("OLD")
    historical["telemetry_version"] = "2.0.0"
    result = _snapshot(tmp_path, [incomplete, historical, _trade("GOOD")], malformed=True)
    assert result["verified_finalized_trade_count"] == 1
    assert result["quality"]["incomplete_rows"] == 1
    assert result["quality"]["historical_excluded"] == 1
    assert result["quality"]["invalid_rows"] == 1


def test_contradictory_market_result_or_provider_is_not_trusted(tmp_path: Path):
    contradictory = _trade("BAD")
    contradictory["result_at_expiry"] = "LOSS"
    wrong_provider = _trade("PROVIDER")
    wrong_provider["checkpoints"]["expiry"]["provider"] = "TWELVE_DATA"
    negative_lag = _trade("LAG", expiry_lag=-60)
    result = _snapshot(tmp_path, [contradictory, wrong_provider, negative_lag, _trade("GOOD")])
    assert result["quality"]["invalid_rows"] == 3
    assert result["verified_finalized_trade_count"] == 1


def test_duplicate_and_conflicting_trade_identity_are_not_double_counted(tmp_path: Path):
    repeated = _trade("DUP")
    conflicting = _trade("CONFLICT")
    other_conflict = _trade("CONFLICT", outcome="LOSS")
    result = _snapshot(
        tmp_path,
        [repeated, dict(repeated), conflicting, other_conflict, _trade("VALID")],
    )
    assert result["verified_finalized_trade_count"] == 2
    assert result["quality"]["identical_duplicates"] == 1
    assert result["quality"]["conflicting_identities"] == 1


def test_explicit_utc_open_time_window_no_future_or_silent_backfill(tmp_path: Path):
    result = _snapshot(
        tmp_path,
        [_trade("START", open_ts=NOW - 7 * 86400),
         _trade("END", open_ts=NOW - 601),
         _trade("PAST", open_ts=NOW - 7 * 86400 - 1),
         _trade("FUTURE", open_ts=NOW + 1)],
    )
    assert result["verified_finalized_trade_count"] == 2
    assert result["quality"]["out_of_window"] == 1
    assert result["quality"]["future_evidence_excluded"] == 1
    assert result["window_start_utc"] == "2026-10-23T09:00:00Z"


def test_unsafe_symbol_or_ambiguous_version_not_displayed(tmp_path: Path):
    fake = _trade("BAD-SYMBOL", symbol="SECRET\nTELEGRAM")
    other = _trade("BAD-VERSION")
    other["strategy_version"] = "<PRIVATE>"
    result = _snapshot(tmp_path, [fake, other, _trade("REAL")])
    assert result["verified_finalized_trade_count"] == 1
    assert result["quality"]["invalid_rows"] == 2
    rendered = market.render_market_summary(result)
    assert "<PRIVATE>" not in rendered
    assert "SECRET" not in rendered


def test_lag_is_descriptive_quality_not_automatic_label_mutation(tmp_path: Path):
    rows = [_trade(f"A{i}", expiry_lag=35) for i in range(5)]
    result = _snapshot(tmp_path, rows)
    assert result["segments"][0]["expiry_observation_lag_over_30_seconds"] == 5
    assert result["segments"][0]["wins"] == 5


def test_ranking_interface_replaces_placeholder_and_never_invents_provider_data(tmp_path: Path, monkeypatch):
    from core import analytics_engine

    source = _write(tmp_path / "active-telemetry.jsonl", [_trade("REAL")])
    monkeypatch.setenv("TRADE_TEMPORAL_TELEMETRY_LOG", source)
    rows = analytics_engine.get_symbol_ranking(7)
    assert len(rows) == 1
    assert rows[0]["symbol"] == "EUR/USD"
    assert rows[0]["insufficient_sample"] is True


def test_research_shows_read_only_market_evidence_for_authorized_owner(tmp_path: Path, monkeypatch):
    import core
    from core import admin_permissions, bot_service, publication_evidence
    from core import lifecycle_funnel_evidence

    source = _write(tmp_path / "test-market.jsonl", [_trade("REAL")])
    monkeypatch.setenv("TRADE_TEMPORAL_TELEMETRY_LOG", source)
    monkeypatch.setattr(core, "market_outcome_evidence", market, raising=False)
    monkeypatch.setattr(core, "publication_evidence", publication_evidence, raising=False)
    monkeypatch.setattr(core, "lifecycle_funnel_evidence", lifecycle_funnel_evidence, raising=False)
    monkeypatch.setattr(bot_service, "get_primary_role", lambda _id: "OWNER")
    monkeypatch.setattr(
        admin_permissions, "has_permission",
        lambda _id, permission: permission == "admin.view",
    )
    monkeypatch.setattr(bot_service, "_iter_recent_engine_events", lambda limit=500: [])
    result = bot_service._handle_admin_navigation_action(
        "RESEARCH", 12345, {"chat": {"id": -100999, "type": "supergroup"}, "from": {"id": 12345}},
    )
    assert "Objective market outcomes" in result["text"]
    assert "Validated trades: 1" in result["text"]
    assert "n=1; descriptive UNKNOWN (small sample)" in result["text"]


@pytest.mark.parametrize("range_days", [0, 31, True, -1, 2.5, "7"])
def test_invalid_window_fails_closed(range_days):
    with pytest.raises(ValueError):
        market.build_market_snapshot(range_days=range_days)


@pytest.mark.parametrize("now_ts", [0, -3, True, 9.4, "2026-10-30"])
def test_invalid_now_fails_closed(now_ts):
    with pytest.raises(ValueError):
        market.build_market_snapshot(now_ts=now_ts)



def test_future_labels_do_not_leak_into_current_market_stats(tmp_path: Path):
    future_label = _trade("LOOKAHEAD", expiry_lag=2000)
    result = _snapshot(tmp_path, [future_label, _trade("REAL")])
    assert result["verified_finalized_trade_count"] == 1
    assert result["quality"]["future_evidence_excluded"] == 1


def test_claimed_finalized_missing_checkpoint_fails_closed(tmp_path: Path):
    incomplete = _trade("MISSING-CHECKPOINT")
    incomplete["checkpoints"]["post_3m"]["state"] = "PENDING"
    missing_final_ts = _trade("MISSING-FINALIZED-TIME")
    missing_final_ts.pop("finalized_ts")
    result = _snapshot(tmp_path, [incomplete, missing_final_ts, _trade("REAL")])
    assert result["quality"]["invalid_rows"] == 2
    assert result["verified_finalized_trade_count"] == 1



def test_finalized_missing_raw_post_checkpoint_evidence_is_invalid(tmp_path: Path):
    forged = _trade("PARTIAL-POST")
    forged["checkpoints"]["post_5m"].pop("price")
    inconsistent = _trade("WRONG-POST-PROVIDER")
    inconsistent["checkpoints"]["post_3m"]["provider"] = "TWELVE_DATA"
    result = _snapshot(tmp_path, [forged, inconsistent, _trade("VALID")])
    assert result["verified_finalized_trade_count"] == 1
    assert result["quality"]["invalid_rows"] == 2
