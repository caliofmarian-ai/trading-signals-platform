from core.signal_engine import _select_effective_scan_symbols, _select_scan_symbols


def test_focus_is_scanned_every_tick_and_wide_is_not_starved():
    symbols = [f"S{i}" for i in range(27)]
    watchlist = ["S0", "S1"]
    seen_wide = set()
    for now_ts in range(0, 60, 2):
        selected, focus = _select_scan_symbols(symbols, watchlist, now_ts)
        assert selected[:2] == watchlist
        assert focus == {"S0", "S1"}
        seen_wide.update(symbol for symbol in selected if symbol not in focus)
    assert seen_wide == set(symbols[2:])


def test_no_focus_spreads_full_universe_across_one_m1_cycle():
    symbols = [f"S{i}" for i in range(27)]
    seen = []
    for now_ts in range(0, 60, 2):
        selected, focus = _select_scan_symbols(symbols, [], now_ts)
        assert focus == set()
        seen.extend(selected)
    assert set(seen) == set(symbols)
    assert len(seen) == len(symbols)


def test_focus_membership_is_per_symbol_not_global():
    selected, focus = _select_scan_symbols(["EUR/USD", "GBP/USD", "USD/JPY"], ["GBP/USD"], 0)
    assert "GBP/USD" in selected
    assert "GBP/USD" in focus
    assert "EUR/USD" not in focus


def test_finnhub_provider_scope_selects_active_eurusd_on_consecutive_two_second_ticks():
    symbols = ["EUR/USD", "GBP/USD", "USD/JPY"]
    for now_ts in (1_800_000_002, 1_800_000_004, 1_800_000_006):
        selected, focus = _select_effective_scan_symbols(
            symbols,
            [],
            now_ts,
            provider_symbols=["EUR/USD"],
        )
        assert selected == ["EUR/USD"]
        assert focus == set()


def test_finnhub_scope_preserves_focus_semantics_without_broadening_active_symbols():
    selected, focus = _select_effective_scan_symbols(
        ["GBP/USD", "EUR/USD"],
        ["EUR/USD", "USD/JPY"],
        1_800_000_002,
        provider_symbols=["EUR/USD"],
    )
    assert selected == ["EUR/USD"]
    assert focus == {"EUR/USD"}

    missing, missing_focus = _select_effective_scan_symbols(
        ["GBP/USD"],
        ["EUR/USD"],
        1_800_000_002,
        provider_symbols=["EUR/USD"],
    )
    assert missing == []
    assert missing_focus == set()


def test_unconstrained_provider_keeps_existing_multi_symbol_wide_schedule_exactly():
    symbols = [f"S{i}" for i in range(27)]
    watchlist = ["S0", "S1"]
    for now_ts in range(0, 60, 2):
        expected = _select_scan_symbols(symbols, watchlist, now_ts)
        actual = _select_effective_scan_symbols(
            symbols,
            watchlist,
            now_ts,
            provider_symbols=None,
        )
        assert actual == expected
