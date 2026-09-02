from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


admin_path = ROOT / "send/core/admin_commands.py"
admin = admin_path.read_text(encoding="utf-8")

old = '''def _symbols_add(symbol: str) -> str:
    if _provider_control.get_active_provider() == _provider_control.PROVIDER_FINNHUB:
        return _finnhub_symbol_lock_message()
    preferred = _matching_known_symbol(symbol) or str(symbol).strip().upper()
    if not _valid_symbol(preferred):
        return f"Invalid symbol: {symbol!r}"
    with _storage.with_lock("active_symbols"):
        symbols = _load_active_symbols()
        keys = {_symbol_key(item) for item in symbols}
        if _symbol_key(preferred) not in keys:
            symbols.append(preferred)
            _save_active_symbols(symbols)
    return f"Added symbol {preferred}."


def _symbols_remove(symbol: str) -> str:
    if _provider_control.get_active_provider() == _provider_control.PROVIDER_FINNHUB:
        return _finnhub_symbol_lock_message()
    key = _symbol_key(symbol)
    with _storage.with_lock("active_symbols"):
        symbols = [s for s in _load_active_symbols() if _symbol_key(s) != key]
        _save_active_symbols(symbols)
    return f"Removed symbol {symbol}."
'''
new = '''def _provider_block_message(reason: str) -> str:
    return (
        "Market data provider state is BLOCKED: "
        f"{reason} Select Finnhub or Twelve Data explicitly to recover. "
        "No symbol setting was changed."
    )


def _current_provider_for_symbols() -> Tuple[Optional[str], Optional[str]]:
    try:
        return _provider_control.get_active_provider(), None
    except _provider_control.MarketDataProviderControlError as exc:
        return None, _provider_block_message(str(exc))


def _symbols_add(symbol: str) -> str:
    provider, blocked = _current_provider_for_symbols()
    if blocked:
        return blocked
    if provider == _provider_control.PROVIDER_FINNHUB:
        return _finnhub_symbol_lock_message()
    preferred = _matching_known_symbol(symbol) or str(symbol).strip().upper()
    if not _valid_symbol(preferred):
        return f"Invalid symbol: {symbol!r}"
    with _storage.with_lock("active_symbols"):
        symbols = _load_active_symbols()
        keys = {_symbol_key(item) for item in symbols}
        if _symbol_key(preferred) not in keys:
            symbols.append(preferred)
            _save_active_symbols(symbols)
    return f"Added symbol {preferred}."


def _symbols_remove(symbol: str) -> str:
    provider, blocked = _current_provider_for_symbols()
    if blocked:
        return blocked
    if provider == _provider_control.PROVIDER_FINNHUB:
        return _finnhub_symbol_lock_message()
    key = _symbol_key(symbol)
    with _storage.with_lock("active_symbols"):
        symbols = [s for s in _load_active_symbols() if _symbol_key(s) != key]
        _save_active_symbols(symbols)
    return f"Removed symbol {symbol}."
'''
admin = replace_once(admin, old, new, "admin symbol helper block")

old = '''def _provider_status_text() -> str:
    summary = _provider_control.provider_summary()
    provider = summary["active_provider"]
    if provider == _provider_control.PROVIDER_FINNHUB:
        return (
            "Market data provider: FINNHUB (EXCLUSIVE)\\n"
            "Effective symbols: EUR/USD only\\n"
            "Symbol controls: LOCKED by current Finnhub API mode\\n"
            "Twelve Data: inactive"
        )
    return (
        "Market data provider: TWELVE_DATA (EXCLUSIVE)\\n"
        "Effective symbols: active selection from configured project universe\\n"
        "Symbol controls: ENABLED\\n"
        "Finnhub: inactive"
    )
'''
new = '''def _provider_status_text() -> str:
    summary = _provider_control.provider_summary()
    provider = summary["active_provider"]
    if provider is None:
        return (
            "Market data provider: BLOCKED\\n"
            f"Provider state: {summary['readiness_reason']}\\n"
            "Effective symbols: NONE while provider authority is invalid\\n"
            "Symbol controls: BLOCKED\\n"
            "Recovery: explicitly select Finnhub or Twelve Data"
        )
    if provider == _provider_control.PROVIDER_FINNHUB:
        return (
            "Market data provider: FINNHUB (EXCLUSIVE)\\n"
            "Effective symbols: EUR/USD only\\n"
            "Symbol controls: LOCKED by current Finnhub API mode\\n"
            "Twelve Data: inactive"
        )
    return (
        "Market data provider: TWELVE_DATA (EXCLUSIVE)\\n"
        "Effective symbols: active selection from configured project universe\\n"
        "Symbol controls: ENABLED\\n"
        "Finnhub: inactive"
    )
'''
admin = replace_once(admin, old, new, "provider status")

admin = replace_once(
    admin,
    '        before = _provider_control.get_active_provider()\n        try:\n            _provider_control.set_active_provider(target, selected_by=user_id)\n',
    '        before_summary = _provider_control.provider_summary()\n        before = str(before_summary.get("active_provider") or "BLOCKED")\n        try:\n            _provider_control.set_active_provider(target, selected_by=user_id)\n',
    "provider recovery before-state",
)

admin = replace_once(
    admin,
    '''    if _provider_control.get_active_provider() == _provider_control.PROVIDER_FINNHUB:
        return render_error(_finnhub_symbol_lock_message())

    if not _valid_symbol(action):
''',
    '''    provider, blocked = _current_provider_for_symbols()
    if blocked:
        return render_error(blocked)
    if provider == _provider_control.PROVIDER_FINNHUB:
        return render_error(_finnhub_symbol_lock_message())

    if not _valid_symbol(action):
''',
    "toggle symbol provider gate",
)

admin = replace_once(
    admin,
    '''def handle_symbols_all(user_id: int) -> str:
    ok, reason = require_permission(user_id, "strategy.symbols.write")
    if not ok:
        return render_error(reason)
    if _provider_control.get_active_provider() == _provider_control.PROVIDER_FINNHUB:
        return render_error(_finnhub_symbol_lock_message())
''',
    '''def handle_symbols_all(user_id: int) -> str:
    ok, reason = require_permission(user_id, "strategy.symbols.write")
    if not ok:
        return render_error(reason)
    provider, blocked = _current_provider_for_symbols()
    if blocked:
        return render_error(blocked)
    if provider == _provider_control.PROVIDER_FINNHUB:
        return render_error(_finnhub_symbol_lock_message())
''',
    "symbols all gate",
)

admin = replace_once(
    admin,
    '''def handle_symbols_none(user_id: int) -> str:
    ok, reason = require_permission(user_id, "strategy.symbols.write")
    if not ok:
        return render_error(reason)
    if _provider_control.get_active_provider() == _provider_control.PROVIDER_FINNHUB:
        return render_error(_finnhub_symbol_lock_message())
''',
    '''def handle_symbols_none(user_id: int) -> str:
    ok, reason = require_permission(user_id, "strategy.symbols.write")
    if not ok:
        return render_error(reason)
    provider, blocked = _current_provider_for_symbols()
    if blocked:
        return render_error(blocked)
    if provider == _provider_control.PROVIDER_FINNHUB:
        return render_error(_finnhub_symbol_lock_message())
''',
    "symbols none gate",
)

admin = replace_once(
    admin,
    '''                observed = _load_active_symbols_observation()
                if _provider_control.get_active_provider() == _provider_control.PROVIDER_FINNHUB:
                    observed = list(_provider_control.FINNHUB_EFFECTIVE_SYMBOLS)
                return _provider_status_text() + "\\n\\n" + render_symbols(observed)
''',
    '''                observed = _load_active_symbols_observation()
                provider_summary = _provider_control.provider_summary()
                if provider_summary["active_provider"] == _provider_control.PROVIDER_FINNHUB:
                    observed = list(_provider_control.FINNHUB_EFFECTIVE_SYMBOLS)
                elif provider_summary["active_provider"] is None:
                    observed = []
                return _provider_status_text() + "\\n\\n" + render_symbols(observed)
''',
    "slash symbols observation",
)

admin = replace_once(
    admin,
    '''            if _provider_control.get_active_provider() == _provider_control.PROVIDER_FINNHUB:
                return render_error(_finnhub_symbol_lock_message())

            if len(parts) != 3:
''',
    '''            provider, blocked = _current_provider_for_symbols()
            if blocked:
                return render_error(blocked)
            if provider == _provider_control.PROVIDER_FINNHUB:
                return render_error(_finnhub_symbol_lock_message())

            if len(parts) != 3:
''',
    "slash symbols mutation gate",
)

admin_path.write_text(admin, encoding="utf-8")

ui_path = ROOT / "send/core/telegram_admin_ui.py"
ui = ui_path.read_text(encoding="utf-8")
ui = replace_once(
    ui,
    '    provider = _provider_control.get_active_provider()\n    rows: list[list[dict[str, str]]] = []\n',
    '    provider_summary = _provider_control.provider_summary()\n    provider = provider_summary["active_provider"]\n    rows: list[list[dict[str, str]]] = []\n',
    "telegram provider summary",
)
ui = replace_once(
    ui,
    '''    ])

    if provider == _provider_control.PROVIDER_FINNHUB:
''',
    '''    ])

    if provider is None:
        rows.append([
            _btn("⚠ Provider state BLOCKED", "SYMBOLS_COV" if parent_action == "HOME" else "SYMBOLS"),
        ])
        rows.append([
            _btn("🔄 Refresh", "SYMBOLS_COV" if parent_action == "HOME" else "SYMBOLS"),
        ])
        info_return = "SYMBOLS_COV" if parent_action == "HOME" else "SYMBOLS"
        rows.append([_knowledge_btn("symbols_coverage", info_return)])
        back_label = "⬅️ Admin" if parent_action == "HOME" else "⬅️ Strategy"
        rows.append([_btn(back_label, parent_action)])
        return _kb(rows)

    if provider == _provider_control.PROVIDER_FINNHUB:
''',
    "telegram blocked state",
)
ui_path.write_text(ui, encoding="utf-8")

plan_path = ROOT / "audit/repository-wide-audit-2026-09-01/REMEDIATION_MASTER_PLAN.md"
plan = plan_path.read_text(encoding="utf-8")
old = '''### R-012 — Strategy profile reconciliation
Severity: HIGH
Status: IN PROGRESS
Issue: #120
Branch: `remediation/audit-2026-09-01-r012-strategy-profiles`
Depends on: R-011 — SATISFIED

Required outcome:
- Admin profiles cannot silently lower active canonical thresholds or mutate obsolete SR semantics;
- profiles either become canonical governed presets or are removed/disabled until canonically defined.

### R-013 — Provider-state corruption fail-closed behavior
Severity: HIGH
Status: PENDING
'''
new = '''### R-012 — Strategy profile reconciliation
Severity: HIGH
Status: CLOSED
Issue: #120 — CLOSED
PR: #121
Merged main commit: `0993852e7bf6f65e393c31c39a2dc6a36c29c95c`
Depends on: R-011 — SATISFIED
Validation: provider selector 5 passed; Telegram admin regression 72 passed; full repository suite 1050 passed.

Required outcome:
- Admin profiles cannot silently lower active canonical thresholds or mutate obsolete SR semantics;
- profiles either become canonical governed presets or are removed/disabled until canonically defined.

### R-013 — Provider-state corruption fail-closed behavior
Severity: HIGH
Status: IN PROGRESS
Issue: #122
Branch: `remediation/audit-2026-09-01-r013-provider-state-corruption`
Depends on: R-012 — SATISFIED
'''
plan = replace_once(plan, old, new, "master plan R012/R013")
plan_path.write_text(plan, encoding="utf-8")
