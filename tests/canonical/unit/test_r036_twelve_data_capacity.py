"""R-036: persisted symbol count vs Twelve Data local REST request budget.

These tests never call market provider APIs and never mutate selected symbols.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import railway_twelve_data_capacity as cap
from scripts import railway_observability_checkpoint as checkpoint


def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path


def _read(tmp_path, monkeypatch, symbols=None, focus=None):
    root = Path(tmp_path)
    active = _write(root / "config" / "active_symbols.json",
                    {"symbols": symbols if symbols is not None else ["EUR/USD"]})
    fsm = _write(root / "state" / "focus_state.json",
                 {"watchlist": focus if focus is not None else []})
    monkeypatch.setenv("TWELVE_DATA_REST_REQUESTS_PER_MINUTE", "8")
    monkeypatch.setenv("TWELVE_DATA_REST_CACHE_SECONDS", "55")
    monkeypatch.setenv("TWELVE_DATA_STREAMING_ENABLED", "1")
    return cap.estimate_request_demand(
        active_symbols_path=active, focus_state_path=fsm,
        provider="TWELVE_DATA"
    )


def test_27_symbols_exceed_default_8_request_budget_even_two_live_focus_symbols(tmp_path, monkeypatch):
    symbols = [
        "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD",
        "AUD/USD", "NZD/USD", "EUR/JPY", "GBP/JPY", "AUD/JPY",
        "NZD/JPY", "EUR/GBP", "EUR/AUD", "EUR/CAD", "GBP/AUD",
        "GBP/CAD", "AUD/NZD", "BTC/USD", "ETH/USD", "SOL/USD",
        "BNB/USD", "XRP/USD", "ADA/USD", "DOGE/USD", "LTC/USD",
        "DOT/USD", "AVAX/USD",
    ]
    observed = _read(tmp_path, monkeypatch, symbols, ["EUR/USD", "GBP/USD"])
    assert observed["active_symbol_count"] == 27
    assert observed["focus_active_symbol_count"] == 2
    assert observed["wide_rest_symbol_count_lower_bound"] == 25
    assert observed["uncapped_rest_calls_per_wide_cycle_lower_bound"] == 50
    assert observed["twelve_rest_budget_requests_per_60s"] == 8
    assert observed["structural_budget_exceeded_if_all_wide_scanned"] is True
    assert observed["actual_rest_http_calls_observed"] is None
    assert observed["provider_http429_verified"] is False


def test_unknown_focus_still_gives_conservative_overbudget_lower_bound(tmp_path, monkeypatch):
    state = _read(tmp_path, monkeypatch,
                  ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD", "AUD/USD"])
    (tmp_path / "state" / "focus_state.json").unlink()
    result = cap.estimate_request_demand(
        active_symbols_path=tmp_path / "config" / "active_symbols.json",
        focus_state_path=tmp_path / "state" / "focus_state.json",
        provider="TWELVE_DATA",
    )
    assert result["focus_active_symbol_count"] is None
    assert result["wide_rest_symbol_count_lower_bound"] == 4
    assert result["uncapped_rest_calls_per_wide_cycle_lower_bound"] == 8
    assert result["uncapped_rest_calls_per_wide_cycle_upper_bound"] == 12
    assert result["structural_budget_exceeded_if_all_wide_scanned"] is False
    assert result["focus_source_status"] == "FILE_NOT_FOUND"


def test_active_5_with_zero_focus_requires_10_and_exceeds_default_budget(tmp_path, monkeypatch):
    result = _read(
        tmp_path, monkeypatch,
        ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD"], []
    )
    assert result["uncapped_rest_calls_per_wide_cycle_lower_bound"] == 10
    assert result["structural_budget_exceeded_if_all_wide_scanned"] is True


def test_finnhub_does_not_misapply_twelve_data_rest_budget(tmp_path, monkeypatch):
    value = _read(tmp_path, monkeypatch, ["EUR/USD"] * 2)
    assert value["active_symbol_count"] == 1  # stable dedup
    finnhub = cap.estimate_request_demand(
        active_symbols_path=tmp_path / "config" / "active_symbols.json",
        focus_state_path=tmp_path / "state" / "focus_state.json",
        provider="FINNHUB"
    )
    assert finnhub["provider"] == "FINNHUB"
    assert finnhub["structural_budget_exceeded_if_all_wide_scanned"] is None


def test_cache_ttl_gte_60_prevents_fabricated_request_estimate(tmp_path, monkeypatch):
    _read(tmp_path, monkeypatch, ["EUR/USD", "GBP/USD", "USD/JPY"])
    monkeypatch.setenv("TWELVE_DATA_REST_CACHE_SECONDS", "120")
    val = cap.collect_request_capacity(base_dir=tmp_path)
    assert val["demand_basis"] == "CACHE_TTL_MAY_COVER_NEXT_WIDE_CYCLE"
    assert val["uncapped_rest_calls_per_wide_cycle_lower_bound"] is None
    assert val["structural_budget_exceeded_if_all_wide_scanned"] is None


def test_streaming_disabled_does_not_discount_focused_symbols(tmp_path, monkeypatch):
    _read(tmp_path, monkeypatch, ["EUR/USD", "GBP/USD", "USD/JPY"], ["EUR/USD"])
    monkeypatch.setenv("TWELVE_DATA_STREAMING_ENABLED", "0")
    result = cap.collect_request_capacity(base_dir=tmp_path)
    assert result["twelve_live_focus_stream_enabled_by_config"] is False
    assert result["wide_rest_symbol_count_lower_bound"] == 3
    assert result["uncapped_rest_calls_per_wide_cycle_lower_bound"] == 6


def test_bad_config_unknown_instead_of_invalid_provider_switch(tmp_path, monkeypatch):
    _read(tmp_path, monkeypatch)
    monkeypatch.setenv("TWELVE_DATA_REST_REQUESTS_PER_MINUTE", "SECRET-API-KEY")
    report = cap.collect_request_capacity(base_dir=tmp_path)
    assert report["twelve_rest_budget_requests_per_60s"] is None
    assert report["structural_budget_exceeded_if_all_wide_scanned"] is None
    assert "SECRET" not in json.dumps(report)
    assert report["provider"] != "FINNHUB"


def test_absent_invalid_and_large_active_symbols_not_coerced(tmp_path, monkeypatch):
    _read(tmp_path, monkeypatch)
    source = tmp_path / "config" / "active_symbols.json"
    source.unlink()
    missing = cap.collect_request_capacity(base_dir=tmp_path)
    assert missing["active_symbol_count"] is None
    assert missing["active_symbols_source_status"] == "FILE_NOT_FOUND"
    _write(source, {"symbols": ["EUR/USD", 1]})
    invalid = cap.collect_request_capacity(base_dir=tmp_path)
    assert invalid["active_symbol_count"] is None
    assert invalid["active_symbols_source_status"] == "INVALID_SYMBOLS"
    source.write_bytes(b"x" * (cap.MAX_INPUT_BYTES + 1))
    oversized = cap.collect_request_capacity(base_dir=tmp_path)
    assert oversized["active_symbol_count"] is None
    assert oversized["active_symbols_source_status"] == "SOURCE_TOO_LARGE"


def test_all_raw_symbols_and_selected_by_ids_hidden(tmp_path, monkeypatch):
    _read(tmp_path, monkeypatch, ["BTC/USD", "EUR/USD"], ["BTC/USD"])
    before_symbols = (tmp_path / "config" / "active_symbols.json").read_bytes()
    before_state = (tmp_path / "state" / "focus_state.json").read_bytes()
    output = cap.collect_request_capacity(base_dir=tmp_path)
    raw = json.dumps(output)
    assert output["active_symbol_count"] == 2
    assert "BTC/USD" not in raw
    assert "EUR/USD" not in raw
    assert str(tmp_path) not in raw
    assert (tmp_path / "config" / "active_symbols.json").read_bytes() == before_symbols
    assert (tmp_path / "state" / "focus_state.json").read_bytes() == before_state


def test_incomplete_focus_bad_membership_unknown_not_overconfidence(tmp_path, monkeypatch):
    _read(tmp_path, monkeypatch, ["EUR/USD", "GBP/USD", "USD/JPY"])
    _write(tmp_path / "state" / "focus_state.json", {"watchlist": ["SECRET-NOT-A-SYMBOL"]})
    report = cap.collect_request_capacity(base_dir=tmp_path)
    assert report["focus_source_status"] == "INVALID_FOCUS_MEMBERSHIP"
    assert report["focus_active_symbol_count"] is None
    assert report["wide_rest_symbol_count_lower_bound"] == 1
    assert "SECRET" not in json.dumps(report)


def test_startup_checkpoint_includes_capacity_with_no_secrets(tmp_path, monkeypatch):
    import core
    import importlib
    for name in ("publication_evidence", "lifecycle_funnel_evidence",
                 "market_outcome_evidence", "focus_history_evidence"):
        mod = importlib.import_module("core." + name)
        monkeypatch.setattr(core, name, mod, raising=False)
    _read(tmp_path, monkeypatch, ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD"])
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "TWELVE_DATA")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "SECRET-TOKEN")
    report = checkpoint.collect_checkpoint(base_dir=tmp_path, now_ts=1793358000)
    assert "market_request_capacity" in report
    assert report["market_request_capacity"]["active_symbol_count"] == 5
    assert report["market_request_capacity"]["structural_budget_exceeded_if_all_wide_scanned"] is True
    raw = json.dumps(report)
    assert "SECRET-TOKEN" not in raw
    assert "EUR/USD" not in json.dumps(report["market_request_capacity"])


@pytest.mark.parametrize("bad", ["bad", "EUR/USD\nSECRET", None, 123])
def test_invalid_symbol_data_fails_closed_without_echoing_it(tmp_path, monkeypatch, bad):
    _read(tmp_path, monkeypatch)
    _write(tmp_path / "config" / "active_symbols.json", {"symbols": [bad]})
    out = cap.collect_request_capacity(base_dir=tmp_path)
    assert out["active_symbol_count"] is None
    assert out["active_symbols_source_status"] == "INVALID_SYMBOLS"
    assert "SECRET" not in json.dumps(out)
