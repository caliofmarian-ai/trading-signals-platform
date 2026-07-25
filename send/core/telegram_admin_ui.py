from __future__ import annotations

from typing import List, Optional

CALLBACK_PREFIX = "ADMIN_NAV:"

# Canonical short dir keys used in file-browse callbacks (max 3 chars for callback budget).
DIR_KEY_OBS = "obs"
DIR_KEY_OUT = "out"
DIR_KEY_ANA = "ana"
DIR_KEY_RPT = "rpt"
DIR_KEY_DOC = "doc"
DIR_KEY_AUD = "aud"
DIR_KEY_SNP = "snp"

# Maximum files per page in the file-list UI.
FILES_PER_PAGE = 8

# ---------------------------------------------------------------------------
# Canonical role constants — must stay in sync with admin_permissions.py.
# Duplicated here to avoid circular imports (telegram_admin_ui has no deps).
# ---------------------------------------------------------------------------
_ROLE_OWNER = "OWNER"
_ROLE_PRIMARY_ADMIN = "PRIMARY_ADMIN"
_ROLE_STRATEGY_ADMIN = "STRATEGY_ADMIN"
_ROLE_RESEARCH_ADMIN = "RESEARCH_ADMIN"
_ROLE_ANALYST = "ANALYST"
_ROLE_MODERATOR = "MODERATOR"
_ROLE_AFFILIATE_ADMIN = "AFFILIATE_ADMIN"

# Canonical panel action keys — correspond to ADMIN_TREE_MAP_v2.0.0.md §4.
_PANEL_OPERATIONS = "OPERATIONS"
_PANEL_SYMBOLS_COV = "SYMBOLS_COV"
_PANEL_DECISION_VIS = "DECISION_VIS"
_PANEL_DISTRIBUTION = "DISTRIBUTION"
_PANEL_RESEARCH = "RESEARCH"
_PANEL_INTELLIGENCE = "INTELLIGENCE"
_PANEL_AFFILIATE = "AFFILIATE"
_PANEL_ROLES = "ROLES"
_PANEL_SYSHEALTH = "SYSHEALTH"
_PANEL_GOVDOCS = "GOVDOCS"
_PANEL_SECAUDIT = "SECAUDIT"

# Ordered canonical panel definitions: (action_key, button_label).
# Order follows ADMIN_TREE_MAP_v2.0.0.md §4.
_CANONICAL_PANELS: list[tuple[str, str]] = [
    (_PANEL_OPERATIONS,   "⚙️ Operations"),
    (_PANEL_SYMBOLS_COV,  "💱 Symbols & Coverage"),
    (_PANEL_DECISION_VIS, "🔍 Decision Visibility"),
    (_PANEL_DISTRIBUTION, "📡 Distribution"),
    (_PANEL_RESEARCH,     "📊 Research & Analytics"),
    (_PANEL_INTELLIGENCE, "🧠 Intelligence"),
    (_PANEL_AFFILIATE,    "🤝 Affiliate / Partner"),
    (_PANEL_ROLES,        "👥 Roles & Identity"),
    (_PANEL_SYSHEALTH,    "🩺 System Health"),
    (_PANEL_GOVDOCS,      "📖 Governance & Docs"),
    (_PANEL_SECAUDIT,     "🔒 Security & Audit"),
]

# Role → allowed panel action keys.
# Source: ADMIN_TREE_MAP_v2.0.0.md §7; ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §10.
_ALL_PANEL_KEYS: frozenset[str] = frozenset(k for k, _ in _CANONICAL_PANELS)

_PANEL_VISIBILITY: dict[str, frozenset[str]] = {
    _ROLE_OWNER: _ALL_PANEL_KEYS,
    _ROLE_PRIMARY_ADMIN: _ALL_PANEL_KEYS,
    _ROLE_STRATEGY_ADMIN: frozenset({_PANEL_OPERATIONS, _PANEL_SYMBOLS_COV, _PANEL_DECISION_VIS}),
    _ROLE_RESEARCH_ADMIN: frozenset({_PANEL_DECISION_VIS, _PANEL_RESEARCH, _PANEL_INTELLIGENCE}),
    _ROLE_ANALYST: frozenset({_PANEL_DECISION_VIS, _PANEL_RESEARCH, _PANEL_INTELLIGENCE}),
    _ROLE_MODERATOR: frozenset({_PANEL_SYSHEALTH}),
    _ROLE_AFFILIATE_ADMIN: frozenset({_PANEL_AFFILIATE}),
}


def _btn(text: str, action: str) -> dict[str, str]:
    return {"text": text, "callback_data": f"{CALLBACK_PREFIX}{action}"}


def _kb(rows: list[list[dict[str, str]]]) -> dict[str, list[list[dict[str, str]]]]:
    return {"inline_keyboard": rows}


def parse_action(callback_data: str) -> Optional[str]:
    if not isinstance(callback_data, str) or not callback_data.startswith(CALLBACK_PREFIX):
        return None
    action = callback_data[len(CALLBACK_PREFIX):].strip()
    return action or None


def admin_home_markup(
    *,
    role: str = "",
    include_roles_reload: bool = False,
) -> dict[str, list[list[dict[str, str]]]]:
    """
    Canonical role-scoped admin home keyboard.

    Renders the canonical admin tree (ADMIN_TREE_MAP_v2.0.0.md §4) filtered to
    the panels permitted by the caller's primary role.  When role is empty or
    unrecognised, all panels are shown (fail-safe for backward compatibility).

    Layout: 2 columns, following canonical panel order.
    """
    allowed = _PANEL_VISIBILITY.get(role, _ALL_PANEL_KEYS)
    visible = [(key, label) for key, label in _CANONICAL_PANELS if key in allowed]

    rows: list[list[dict[str, str]]] = []
    # Pair panels into 2-column rows.
    for i in range(0, len(visible), 2):
        row = [_btn(visible[i][1], visible[i][0])]
        if i + 1 < len(visible):
            row.append(_btn(visible[i + 1][1], visible[i + 1][0]))
        rows.append(row)

    if include_roles_reload:
        rows.append([_btn("🔄 Reload Roles", "RELOAD_ROLES_CONFIRM")])

    return _kb(rows)


def status_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("⚙️ Strategy", "STRATEGY"), _btn("🤖 Engine", "ENGINE")],
            [_btn("⬅️ Admin", "HOME")],
        ]
    )


def strategy_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("🎯 Thresholds", "THRESHOLDS"), _btn("📐 S/R", "SR")],
            [_btn("⚡ Spike Filter", "SPIKE"), _btn("💱 Symbols", "SYMBOLS")],
            [_btn("📋 Quick Profile", "PROFILE_HOME"), _btn("⬅️ Admin", "HOME")],
        ]
    )


def symbols_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("🔄 Refresh Symbols", "SYMBOLS"), _btn("⚙️ Strategy", "STRATEGY")],
            [_btn("⬅️ Admin", "HOME")],
        ]
    )


def symbols_toggle_markup(
    all_symbols: List[str],
    active_symbols: List[str],
) -> dict[str, list[list[dict[str, str]]]]:
    """
    Visual symbol-toggle keyboard with checkbox-style indicators.

    Symbols are grouped by category (FOREX / CRYPTO) based on name prefix
    and laid out 3 per row.  Active symbols show ✅, inactive show ⬜.
    """
    active_set = {s.upper() for s in active_symbols}
    forex = [s for s in all_symbols if not s.upper().startswith("BTC")
             and not s.upper().startswith("ETH")
             and not s.upper().startswith("XRP")
             and not s.upper().startswith("LTC")
             and not s.upper().startswith("ADA")
             and not s.upper().startswith("BNB")
             and not s.upper().startswith("SOL")
             and not s.upper().startswith("DOT")
             and not s.upper().endswith("USD") or _is_forex(s)]
    crypto = [s for s in all_symbols if not _is_forex(s)]

    rows: list[list[dict[str, str]]] = []

    def _section_rows(symbols: list[str]) -> list[list[dict[str, str]]]:
        section_rows = []
        row: list[dict[str, str]] = []
        for sym in symbols:
            icon = "✅" if sym.upper() in active_set else "⬜"
            row.append(_btn(f"{icon} {sym}", f"SYM_TOGGLE:{sym}"))
            if len(row) == 3:
                section_rows.append(row)
                row = []
        if row:
            section_rows.append(row)
        return section_rows

    # Separate into forex and crypto lists
    forex_syms = sorted(s for s in all_symbols if _is_forex(s))
    crypto_syms = sorted(s for s in all_symbols if not _is_forex(s))

    if forex_syms:
        rows.extend(_section_rows(forex_syms))
    if crypto_syms:
        rows.extend(_section_rows(crypto_syms))

    # Controls row
    rows.append([
        _btn("✅ All", "SYMBOLS_ALL"),
        _btn("⬜ None", "SYMBOLS_NONE"),
        _btn("🔄 Refresh", "SYMBOLS"),
    ])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def _is_forex(sym: str) -> bool:
    """Classify a symbol as FOREX (6-char currency pair) vs CRYPTO."""
    s = sym.upper()
    forex_suffixes = {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"}
    if len(s) == 6:
        return s[3:] in forex_suffixes and s[:3] in forex_suffixes | {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"}
    return False


def strategy_quick_markup(current_profile: Optional[str]) -> dict[str, list[list[dict[str, str]]]]:
    """
    Three-button strategy-profile selector.

    Profiles: CONSERVATIVE (MIC/SMALL), BALANCED (MEDIU/MEDIUM), AGGRESSIVE (MARE/LARGE).
    Current profile receives a ✅ indicator.
    """
    cp = (current_profile or "").upper()

    def _mark(p: str) -> str:
        return "✅ " if cp == p else ""

    return _kb([
        [
            _btn(f"{_mark('CONSERVATIVE')}MIC / SMALL", "PROFILE_CONFIRM:CONSERVATIVE"),
            _btn(f"{_mark('BALANCED')}MEDIU / MEDIUM", "PROFILE_CONFIRM:BALANCED"),
            _btn(f"{_mark('AGGRESSIVE')}MARE / LARGE", "PROFILE_CONFIRM:AGGRESSIVE"),
        ],
        [_btn("⬅️ Strategy", "STRATEGY")],
    ])


def strategy_profile_confirm_markup(profile: str) -> dict[str, list[list[dict[str, str]]]]:
    """Confirmation screen before applying a strategy profile mutation."""
    return _kb([
        [
            _btn(f"✅ Apply {profile.capitalize()}", f"PROFILE_EXEC:{profile}"),
            _btn("❌ Cancel", "PROFILE_HOME"),
        ],
    ])


def engine_markup(*, include_roles_reload: bool) -> dict[str, list[list[dict[str, str]]]]:
    rows = [[_btn("🔄 Refresh Engine", "ENGINE"), _btn("📊 Status", "STATUS")]]
    if include_roles_reload:
        rows.append([_btn("🔄 Reload Roles", "RELOAD_ROLES_CONFIRM")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def standard_back_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb([[_btn("⬅️ Admin", "HOME")]])


def reload_confirm_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb([[_btn("✅ Confirm Reload", "RELOAD_ROLES_EXEC"), _btn("❌ Cancel", "HOME")]])


def files_home_markup() -> dict[str, list[list[dict[str, str]]]]:
    """Directory chooser for the file browser."""
    return _kb([
        [_btn("📂 Observability", f"FILES:{DIR_KEY_OBS}:0"), _btn("📂 Outcomes", f"FILES:{DIR_KEY_OUT}:0")],
        [_btn("📂 Analytics", f"FILES:{DIR_KEY_ANA}:0"), _btn("📂 Reports", f"FILES:{DIR_KEY_RPT}:0")],
        [_btn("📂 Docs", f"FILES:{DIR_KEY_DOC}:0"), _btn("📂 Audit", f"FILES:{DIR_KEY_AUD}:0")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def files_list_markup(
    filenames: List[str],
    page: int,
    total_pages: int,
    dir_key: str,
) -> dict[str, list[list[dict[str, str]]]]:
    """Paginated file list with download buttons."""
    rows: list[list[dict[str, str]]] = []
    for fname in filenames:
        # Truncate for display but keep full name in callback
        display = fname if len(fname) <= 32 else fname[:29] + "…"
        rows.append([_btn(f"📄 {display}", f"FILE_DL:{dir_key}:{fname}")])

    # Pagination row
    nav: list[dict[str, str]] = []
    if page > 0:
        nav.append(_btn("◀️ Prev", f"FILES:{dir_key}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(_btn("Next ▶️", f"FILES:{dir_key}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn("⬅️ Files", "FILES_HOME"), _btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def docs_list_markup(filenames: List[str]) -> dict[str, list[list[dict[str, str]]]]:
    """Docs viewer: one button per file."""
    rows: list[list[dict[str, str]]] = []
    for fname in filenames:
        display = fname if len(fname) <= 36 else fname[:33] + "…"
        rows.append([_btn(f"📄 {display}", f"FILE_DL:{DIR_KEY_DOC}:{fname}")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def diagnose_markup() -> dict[str, list[list[dict[str, str]]]]:
    """Post-diagnose action buttons."""
    return _kb([
        [_btn("🔍 Runtime Audit", "AUDIT"), _btn("🔄 Refresh", "DIAGNOSE")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def report_markup(*, has_file: bool = False, dir_key: str = DIR_KEY_RPT, filename: str = "") -> dict[str, list[list[dict[str, str]]]]:
    """Report panel markup — optionally includes a download button."""
    rows: list[list[dict[str, str]]] = []
    if has_file and filename:
        rows.append([_btn("📥 Download Report", f"FILE_DL:{dir_key}:{filename}")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


# ---------------------------------------------------------------------------
# Canonical panel markups — one per canonical admin tree node.
# Source: ADMIN_TREE_MAP_v2.0.0.md §6.
# ---------------------------------------------------------------------------

def operations_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    Operations panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.2
    Purpose: engine state, freeze/pause, operational actions.
    """
    return _kb([
        [_btn("🤖 Engine State", "OPS_ENGINE"), _btn("🩺 Diagnose", "OPS_DIAGNOSE")],
        [_btn("📋 Strategy Parameters", "STRATEGY"), _btn("💱 Symbols", "SYMBOLS_COV")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def decision_visibility_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    Decision Visibility panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.4
    Purpose: last decision, gate results, rejection reasons, score composition.
    """
    return _kb([
        [_btn("🔄 Refresh", "DECISION_VIS")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def distribution_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    Distribution Control panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.5
    Purpose: route status, channel readiness, publication controls.
    Read-only: no mutation controls available at this time.
    """
    return _kb([
        [_btn("🔄 Refresh", "DISTRIBUTION")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def research_markup(*, has_file: bool = False, filename: str = "") -> dict[str, list[list[dict[str, str]]]]:
    """
    Research & Analytics panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.6
    Purpose: performance summaries, rejection analytics, outcome analytics.
    """
    rows: list[list[dict[str, str]]] = []
    if has_file and filename:
        rows.append([_btn("📥 Download Report", f"FILE_DL:{DIR_KEY_RPT}:{filename}")])
    rows.append([_btn("🔄 Refresh", "RESEARCH")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def intelligence_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    Intelligence panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.7
    Purpose: decision intelligence, drift signals, anomaly summaries, recommendation queue.
    """
    return _kb([
        [_btn("🔄 Refresh", "INTELLIGENCE")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def roles_identity_markup(*, can_reload: bool = False) -> dict[str, list[list[dict[str, str]]]]:
    """
    Roles & Identity panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.9
    Purpose: my identity, my role, scope summary, role references.
    """
    rows: list[list[dict[str, str]]] = []
    if can_reload:
        rows.append([_btn("🔄 Reload Roles", "RELOAD_ROLES_CONFIRM")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def system_health_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    System Health panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.10
    Purpose: health summary, observability summary, last errors, alerts, diagnostics.
    """
    return _kb([
        [_btn("🤖 Engine State", "SH_ENGINE"), _btn("🩺 Diagnose", "SH_DIAGNOSE")],
        [_btn("🔍 Runtime Audit", "SH_AUDIT")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def governance_docs_markup(filenames: List[str]) -> dict[str, list[list[dict[str, str]]]]:
    """
    Governance & Docs panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.11
    Purpose: active canonical specs, implementation references, change-control references.
    """
    rows: list[list[dict[str, str]]] = []
    for fname in filenames:
        display = fname if len(fname) <= 36 else fname[:33] + "…"
        rows.append([_btn(f"📄 {display}", f"FILE_DL:{DIR_KEY_DOC}:{fname}")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def security_audit_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    Security & Audit panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.12
    Purpose: admin action log, access denials, role change audit, audit exports.
    """
    return _kb([
        [_btn("🔍 Runtime Audit", "SECAUDIT_AUDIT"), _btn("📁 File Browser", "FILES_HOME")],
        [_btn("⬅️ Admin", "HOME")],
    ])
