from __future__ import annotations

from typing import List, Optional

from core.owner_knowledge import get_knowledge
from core import market_data_provider_control as _provider_control
from core.role_constants import (
    ROLE_OWNER as _ROLE_OWNER,
    ROLE_PRIMARY_ADMIN as _ROLE_PRIMARY_ADMIN,
    ROLE_STRATEGY_ADMIN as _ROLE_STRATEGY_ADMIN,
    ROLE_RESEARCH_ADMIN as _ROLE_RESEARCH_ADMIN,
    ROLE_ANALYST as _ROLE_ANALYST,
    ROLE_MODERATOR as _ROLE_MODERATOR,
    ROLE_AFFILIATE_ADMIN as _ROLE_AFFILIATE_ADMIN,
)

CALLBACK_PREFIX = "ADMIN_NAV:"
KNOWLEDGE_ACTION_PREFIX = "INFO:"

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

_SAFE_KNOWLEDGE_RETURN_ACTIONS: frozenset[str] = frozenset({
    "HOME",
    "STATUS",
    "OPERATIONS",
    "OPS_ENGINE",
    "OPS_DIAGNOSE",
    "STRATEGY",
    "PROFILE_HOME",
    "THRESHOLDS",
    "SR",
    "SPIKE",
    "SYMBOLS",
    "SYMBOLS_COV",
    "ENGINE",
    "DEBUG",
    "DECISION_VIS",
    "STRATEGY_COMPARE",
    "STRATEGY_CHOOSE",
    "STRATEGY_FOREX_FUTURE",
    "DISTRIBUTION",
    "RESEARCH",
    "REPORT",
    "INTELLIGENCE",
    "AFFILIATE",
    "ROLES",
    "SYSHEALTH",
    "SH_ENGINE",
    "SH_DIAGNOSE",
    "GOVDOCS",
    "DOCS",
    "SECAUDIT",
    "FILES_HOME",
    "DIAGNOSE",
})

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

# Canonical parent map: action → human-readable Back label suffix.
# Used by context-sensitive markup functions that need to label their Back button
# correctly depending on how the page was reached.
# Source: ADMIN_TREE_MAP_v2.0.0.md §6 parent hierarchy.
_PANEL_BACK_LABELS: dict[str, str] = {
    "HOME": "Admin",
    "OPERATIONS": "Operations",
    "SYSHEALTH": "System Health",
    "STRATEGY": "Strategy",
    "PROFILE_HOME": "Profile",
    "FILES_HOME": "Files",
    "SECAUDIT": "Security & Audit",
}

# Canonical static parent map for ADMIN_NAV pages.
# Defines the immediate parent for each page action in the admin tree.
# For pages reachable from multiple parents (OPS_ENGINE, SH_ENGINE, etc.),
# the correct parent is passed dynamically via parent_action parameters.
# Source: ADMIN_TREE_MAP_v2.0.0.md §6.
CANONICAL_ADMIN_PARENT_MAP: dict[str, str] = {
    "STATUS": "HOME",
    "ENGINE": "HOME",
    "STRATEGY": "OPERATIONS",
    "SYMBOLS": "STRATEGY",
    "SYMBOLS_COV": "HOME",
    "PROFILE_HOME": "STRATEGY",
    "THRESHOLDS": "STRATEGY",
    "SR": "STRATEGY",
    "SPIKE": "STRATEGY",
    "OPERATIONS": "HOME",
    "DECISION_VIS": "HOME",
    "STRATEGY_COMPARE": "DECISION_VIS",
    "STRATEGY_CHOOSE": "DECISION_VIS",
    "STRATEGY_FOREX_FUTURE": "STRATEGY_CHOOSE",
    "DISTRIBUTION": "HOME",
    "RESEARCH": "HOME",
    "INTELLIGENCE": "HOME",
    "AFFILIATE": "HOME",
    "ROLES": "HOME",
    "SYSHEALTH": "HOME",
    "GOVDOCS": "HOME",
    "SECAUDIT": "HOME",
    "OPS_ENGINE": "OPERATIONS",
    "OPS_DIAGNOSE": "OPERATIONS",
    "SH_ENGINE": "SYSHEALTH",
    "SH_DIAGNOSE": "SYSHEALTH",
    "SH_AUDIT": "SYSHEALTH",
    "FILES_HOME": "HOME",
    "DIAGNOSE": "HOME",
    "AUDIT": "HOME",
    "SECAUDIT_AUDIT": "SECAUDIT",
    "RELOAD_ROLES_CONFIRM": "ROLES",
}


def _btn(text: str, action: str) -> dict[str, str]:
    return {"text": text, "callback_data": f"{CALLBACK_PREFIX}{action}"}


def _kb(rows: list[list[dict[str, str]]]) -> dict[str, list[list[dict[str, str]]]]:
    return {"inline_keyboard": rows}


def _safe_knowledge_return_action(return_action: str) -> str:
    action = str(return_action or "HOME").strip()
    if action in _SAFE_KNOWLEDGE_RETURN_ACTIONS:
        return action
    if action.startswith("FILES:"):
        parts = action.split(":")
        allowed_dirs = {
            DIR_KEY_OBS,
            DIR_KEY_OUT,
            DIR_KEY_ANA,
            DIR_KEY_RPT,
            DIR_KEY_DOC,
            DIR_KEY_AUD,
            DIR_KEY_SNP,
        }
        if len(parts) == 3 and parts[1] in allowed_dirs and parts[2].isdigit():
            return action
    return "HOME"


def knowledge_action(knowledge_key: str, return_action: str) -> str:
    key = str(knowledge_key or "").strip().lower()
    parent = _safe_knowledge_return_action(return_action)
    return f"{KNOWLEDGE_ACTION_PREFIX}{key}:{parent}"


def _knowledge_btn(knowledge_key: str, return_action: str) -> dict[str, str]:
    return _btn("ℹ️ What is this?", knowledge_action(knowledge_key, return_action))


def knowledge_detail_markup(return_action: str) -> dict[str, list[list[dict[str, str]]]]:
    parent = _safe_knowledge_return_action(return_action)
    return _kb([[_btn("⬅️ Back", parent)]])


def panel_visible_for_role(role: str, panel_action: str) -> bool:
    allowed = _PANEL_VISIBILITY.get(role, frozenset())
    return str(panel_action or "").strip().upper() in allowed


def knowledge_visible_for_role(role: str, knowledge_key: str) -> bool:
    entry = get_knowledge(knowledge_key)
    if entry is None:
        return False
    if entry.public:
        return True
    if entry.key == "admin_home":
        return role in _PANEL_VISIBILITY
    return any(panel_visible_for_role(role, action) for action in entry.panel_actions)


def parse_action(callback_data: str) -> Optional[str]:
    if not isinstance(callback_data, str) or not callback_data.startswith(CALLBACK_PREFIX):
        return None
    action = callback_data[len(CALLBACK_PREFIX):].strip()
    return action or None


def admin_home_markup(
    *,
    role: str = "",
    include_roles_reload: bool = False,
    home_button_callback: Optional[str] = None,
    back_button_callback: Optional[str] = None,
) -> dict[str, list[list[dict[str, str]]]]:
    """
    Canonical role-scoped admin home keyboard.

    Renders the canonical admin tree (ADMIN_TREE_MAP_v2.0.0.md §4) filtered to
    the panels permitted by the caller's primary role.  When role is empty or
    unrecognised, all panels are shown (fail-safe for backward compatibility).

    Layout: 2 columns, following canonical panel order.

    ``home_button_callback``: when provided, a "🏠 Home" row is appended as the
    last row using that exact callback_data string.  Pass the APP:HOME callback
    so the button navigates back to the role-scoped welcome page.
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

    rows.append([_knowledge_btn("admin_home", "HOME")])

    nav_row: list[dict[str, str]] = []
    if back_button_callback is not None:
        nav_row.append({"text": "⬅️ Back", "callback_data": back_button_callback})
    if home_button_callback is not None:
        nav_row.append({"text": "🏠 Home", "callback_data": home_button_callback})
    if nav_row:
        rows.append(nav_row)

    return _kb(rows)


def status_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("⚙️ Strategy", "STRATEGY"), _btn("🤖 Engine", "ENGINE")],
            [_knowledge_btn("status", "STATUS")],
            [_btn("⬅️ Admin", "HOME")],
        ]
    )


def strategy_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("🎯 Thresholds", "THRESHOLDS"), _btn("📐 S/R", "SR")],
            [_btn("⚡ Spike Filter", "SPIKE"), _btn("💱 Symbols", "SYMBOLS")],
            [_btn("📋 Quick Profile", "PROFILE_HOME"), _btn("⬅️ Operations", "OPERATIONS")],
            [_knowledge_btn("strategy", "STRATEGY")],
        ]
    )


def strategy_parameter_markup(
    knowledge_key: str,
    refresh_action: str,
) -> dict[str, list[list[dict[str, str]]]]:
    return _kb([
        [_btn("🔄 Refresh", refresh_action)],
        [_knowledge_btn(knowledge_key, refresh_action)],
        [_btn("⬅️ Strategy", "STRATEGY")],
    ])


def symbols_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("🔄 Refresh Symbols", "SYMBOLS"), _btn("⚙️ Strategy", "STRATEGY")],
            [_knowledge_btn("symbols_coverage", "SYMBOLS")],
            [_btn("⬅️ Admin", "HOME")],
        ]
    )


def symbols_toggle_markup(
    all_symbols: List[str],
    active_symbols: List[str],
    *,
    parent_action: str = "HOME",
) -> dict[str, list[list[dict[str, str]]]]:
    """Provider selector plus provider-governed symbol controls.

    FINNHUB is exclusive and exposes only EUR/USD.  TWELVE_DATA exposes the
    configured project symbol universe.  Provider buttons reuse the existing
    governed symbol-mutation callback family so no second Telegram control
    plane is introduced.
    """
    active_set = {s.upper() for s in active_symbols}
    provider_summary = _provider_control.provider_summary()
    provider = provider_summary["active_provider"]
    rows: list[list[dict[str, str]]] = []

    def _symbol_action(base: str, value: str = "") -> str:
        if parent_action == "HOME":
            return f"{base}:{value}" if value else base
        return f"{base}:{parent_action}:{value}" if value else f"{base}:{parent_action}"

    rows.append([
        _btn(
            f"{'✅' if provider == _provider_control.PROVIDER_FINNHUB else '⬜'} Finnhub",
            _symbol_action("SYM_TOGGLE", "PROVIDER_FINNHUB"),
        ),
        _btn(
            f"{'✅' if provider == _provider_control.PROVIDER_TWELVE_DATA else '⬜'} Twelve Data",
            _symbol_action("SYM_TOGGLE", "PROVIDER_TWELVE_DATA"),
        ),
    ])

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
        rows.append([
            _btn("🔒 EUR/USD only", _symbol_action("SYM_TOGGLE", "EUR/USD")),
        ])
        rows.append([
            _btn("🔄 Refresh", "SYMBOLS_COV" if parent_action == "HOME" else "SYMBOLS"),
        ])
    else:
        def _section_rows(symbols: list[str]) -> list[list[dict[str, str]]]:
            section_rows = []
            row: list[dict[str, str]] = []
            for sym in symbols:
                icon = "✅" if sym.upper() in active_set else "⬜"
                row.append(_btn(f"{icon} {sym}", _symbol_action("SYM_TOGGLE", sym)))
                if len(row) == 3:
                    section_rows.append(row)
                    row = []
            if row:
                section_rows.append(row)
            return section_rows

        forex_syms = sorted(s for s in all_symbols if _is_forex(s))
        crypto_syms = sorted(s for s in all_symbols if not _is_forex(s))
        if forex_syms:
            rows.extend(_section_rows(forex_syms))
        if crypto_syms:
            rows.extend(_section_rows(crypto_syms))
        rows.append([
            _btn("✅ All", _symbol_action("SYMBOLS_ALL")),
            _btn("⬜ None", _symbol_action("SYMBOLS_NONE")),
            _btn("🔄 Refresh", "SYMBOLS_COV" if parent_action == "HOME" else "SYMBOLS"),
        ])

    info_return = "SYMBOLS_COV" if parent_action == "HOME" else "SYMBOLS"
    rows.append([_knowledge_btn("symbols_coverage", info_return)])
    back_label = "⬅️ Admin" if parent_action == "HOME" else "⬅️ Strategy"
    rows.append([_btn(back_label, parent_action)])
    return _kb(rows)


def _is_forex(sym: str) -> bool:
    """Classify slash/underscore/plain six-letter currency pairs as FOREX."""
    s = sym.upper().replace("/", "").replace("_", "")
    forex_codes = {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"}
    return len(s) == 6 and s[:3] in forex_codes and s[3:] in forex_codes


def strategy_quick_markup(current_profile: Optional[str]) -> dict[str, list[list[dict[str, str]]]]:
    """Read-only strategy-profile surface while named presets are undefined."""
    return _kb([
        [_btn("🔄 Refresh", "PROFILE_HOME")],
        [_knowledge_btn("strategy", "PROFILE_HOME")],
        [_btn("⬅️ Strategy", "STRATEGY")],
    ])


def strategy_profile_confirm_markup(profile: str) -> dict[str, list[list[dict[str, str]]]]:
    """Safe recovery markup for stale legacy profile callbacks; never executes."""
    return _kb([
        [_btn("⬅️ Profiles", "PROFILE_HOME")],
        [_btn("⬅️ Strategy", "STRATEGY")],
    ])


def engine_markup(*, include_roles_reload: bool, parent_action: str = "HOME") -> dict[str, list[list[dict[str, str]]]]:
    """
    Engine panel navigation.

    ``parent_action``: canonical Back destination.  Pass ``"OPERATIONS"`` when
    reached from the Operations panel (OPS_ENGINE) and ``"SYSHEALTH"`` when
    reached from System Health (SH_ENGINE).  Defaults to ``"HOME"``.
    """
    refresh_action = "ENGINE"
    if parent_action == "OPERATIONS":
        refresh_action = "OPS_ENGINE"
    elif parent_action == "SYSHEALTH":
        refresh_action = "SH_ENGINE"
    rows = [[_btn("🔄 Refresh Engine", refresh_action), _btn("📊 Status", "STATUS")]]
    if include_roles_reload:
        rows.append([_btn("🔄 Reload Roles", "RELOAD_ROLES_CONFIRM")])
    rows.append([_knowledge_btn("engine", refresh_action)])
    back_label = "⬅️ Admin" if parent_action == "HOME" else f"⬅️ {_PANEL_BACK_LABELS.get(parent_action, 'Back')}"
    rows.append([_btn(back_label, parent_action)])
    return _kb(rows)


def standard_back_markup(
    *,
    knowledge_key: Optional[str] = None,
    return_action: str = "HOME",
) -> dict[str, list[list[dict[str, str]]]]:
    rows: list[list[dict[str, str]]] = []
    if knowledge_key:
        rows.append([_knowledge_btn(knowledge_key, return_action)])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def reload_confirm_markup(*, cancel_action: str = "ROLES") -> dict[str, list[list[dict[str, str]]]]:
    return _kb([[_btn("✅ Confirm Reload", "RELOAD_ROLES_EXEC"), _btn("❌ Cancel", cancel_action)]])


def files_home_markup() -> dict[str, list[list[dict[str, str]]]]:
    """Directory chooser for the file browser."""
    return _kb([
        [_btn("📂 Observability", f"FILES:{DIR_KEY_OBS}:0"), _btn("📂 Outcomes", f"FILES:{DIR_KEY_OUT}:0")],
        [_btn("📂 Analytics", f"FILES:{DIR_KEY_ANA}:0"), _btn("📂 Reports", f"FILES:{DIR_KEY_RPT}:0")],
        [_btn("📂 Docs", f"FILES:{DIR_KEY_DOC}:0"), _btn("📂 Audit", f"FILES:{DIR_KEY_AUD}:0")],
        [_knowledge_btn("files_reports", "FILES_HOME")],
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
        display = fname if len(fname) <= 32 else fname[:29] + "…"
        rows.append([_btn(f"📄 {display}", f"FILE_DL:{dir_key}:{fname}")])

    nav: list[dict[str, str]] = []
    if page > 0:
        nav.append(_btn("◀️ Prev", f"FILES:{dir_key}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(_btn("Next ▶️", f"FILES:{dir_key}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_knowledge_btn("files_reports", f"FILES:{dir_key}:{page}")])
    rows.append([_btn("⬅️ Files", "FILES_HOME"), _btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def docs_list_markup(filenames: List[str]) -> dict[str, list[list[dict[str, str]]]]:
    """Docs viewer: one button per file."""
    rows: list[list[dict[str, str]]] = []
    for fname in filenames:
        display = fname if len(fname) <= 36 else fname[:33] + "…"
        rows.append([_btn(f"📄 {display}", f"FILE_DL:{DIR_KEY_DOC}:{fname}")])
    rows.append([_knowledge_btn("governance_docs", "DOCS")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def diagnose_markup(*, parent_action: str = "HOME") -> dict[str, list[list[dict[str, str]]]]:
    """Post-diagnose action buttons.

    ``parent_action``: canonical Back destination.  Pass ``"OPERATIONS"`` when
    reached from the Operations panel (OPS_DIAGNOSE) and ``"SYSHEALTH"`` when
    reached from System Health (SH_DIAGNOSE).  Defaults to ``"HOME"``.
    """
    audit_action = "AUDIT"
    refresh_action = "DIAGNOSE"
    if parent_action == "OPERATIONS":
        audit_action = "OPS_AUDIT"
        refresh_action = "OPS_DIAGNOSE"
    elif parent_action == "SYSHEALTH":
        audit_action = "DIAG_SH_AUDIT"
        refresh_action = "SH_DIAGNOSE"
    back_label = "⬅️ Admin" if parent_action == "HOME" else f"⬅️ {_PANEL_BACK_LABELS.get(parent_action, 'Back')}"
    return _kb([
        [_btn("🔍 Runtime Audit", audit_action), _btn("🔄 Refresh", refresh_action)],
        [_knowledge_btn("diagnostics", refresh_action)],
        [_btn(back_label, parent_action)],
    ])


def report_markup(*, has_file: bool = False, dir_key: str = DIR_KEY_RPT, filename: str = "") -> dict[str, list[list[dict[str, str]]]]:
    """Report panel markup — optionally includes a download button."""
    rows: list[list[dict[str, str]]] = []
    if has_file and filename:
        rows.append([_btn("📥 Download Report", f"FILE_DL:{dir_key}:{filename}")])
    rows.append([_knowledge_btn("research_analytics", "REPORT")])
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
        [_knowledge_btn("operations", "OPERATIONS")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def decision_visibility_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    Decision Visibility panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.4
    Purpose: last decision, gate results, rejection reasons, score composition.
    """
    return _kb([
        [_btn("🧭 Choose Strategy", "STRATEGY_CHOOSE")],
        [_btn("🔄 Refresh", "DECISION_VIS")],
        [_knowledge_btn("decision_visibility", "DECISION_VIS")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def strategy_choice_markup() -> dict[str, list[list[dict[str, str]]]]:
    """Trading-strategy family selection navigation."""
    return _kb([
        [_btn("✅ Binary Trading", "STRATEGY_CHOOSE")],
        [_btn("🌍 Forex Strategy — Future", "STRATEGY_FOREX_FUTURE")],
        [_btn("🔄 Refresh", "STRATEGY_CHOOSE")],
        [_knowledge_btn("strategy_selection", "STRATEGY_CHOOSE")],
        [_btn("⬅️ Decision Visibility", "DECISION_VIS")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def future_forex_strategy_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb([
        [_btn("⬅️ Choose Strategy", "STRATEGY_CHOOSE")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def strategy_comparison_markup() -> dict[str, list[list[dict[str, str]]]]:
    """Compatibility alias for Telegram messages created before Choose Strategy."""
    return strategy_choice_markup()


def distribution_markup() -> dict[str, list[list[dict[str, str]]]]:
    """
    Distribution Control panel navigation.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.5
    Purpose: route status, channel readiness, publication controls.
    Read-only: no mutation controls available at this time.
    """
    return _kb([
        [_btn("🔄 Refresh", "DISTRIBUTION")],
        [_knowledge_btn("distribution", "DISTRIBUTION")],
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
    rows.append([_knowledge_btn("research_analytics", "RESEARCH")])
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
        [_knowledge_btn("intelligence", "INTELLIGENCE")],
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
    rows.append([_knowledge_btn("roles_identity", "ROLES")])
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
        [_knowledge_btn("system_health", "SYSHEALTH")],
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
    rows.append([_knowledge_btn("governance_docs", "GOVDOCS")])
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
        [_knowledge_btn("security_audit", "SECAUDIT")],
        [_btn("⬅️ Admin", "HOME")],
    ])


def affiliate_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb([
        [_knowledge_btn("affiliate", "AFFILIATE")],
        [_btn("⬅️ Admin", "HOME")],
    ])