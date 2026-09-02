from __future__ import annotations

from pathlib import Path
import re


repo = Path(__file__).resolve().parents[1]
path = repo / "send/core/admin_views.py"
with path.open("r", encoding="utf-8", newline="") as handle:
    text = handle.read()
newline = "\r\n" if "\r\n" in text else "\n"

pattern = re.compile(
    r"def render_distribution_panel\(.*?\r?\n\r?\ndef render_intelligence_panel\(",
    re.S,
)
if len(list(pattern.finditer(text))) != 1:
    raise SystemExit("expected exactly one distribution panel block")

replacement_lf = '''def render_distribution_panel(
    admin_chat_id: int,
    admin_thread_id: int,
    routes: Optional[List[str]] = None,
) -> str:
    """Render effective governed distribution truth for authorized admins.

    R-011 keeps the panel read-only and sources values from the same live
    distribution configuration/state used by routing. Display values are
    never hardcoded. Environment overrides remain supported, but their
    source is made explicit so the effective entitlement is auditable.
    """
    import os
    from core import distribution_router as legacy_distribution
    from core import distribution_router_v3 as live_distribution

    lines: List[str] = ["Distribution Control", "", "Route Status"]

    try:
        cfg = live_distribution._load_effective_config()
        state = legacy_distribution.load_state()
        raw = legacy_distribution._load_channel_config_file()
    except Exception:
        lines.append(
            "Configuration: UNAVAILABLE (effective distribution truth could not be read)."
        )
        return _lines(lines)

    raw = raw if isinstance(raw, dict) else {}
    raw_limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    raw_routes = raw.get("routes") if isinstance(raw.get("routes"), dict) else {}
    limits = cfg.get("limits") if isinstance(cfg.get("limits"), dict) else {}
    channels = cfg.get("channels") if isinstance(cfg.get("channels"), dict) else {}
    enabled = cfg.get("enabled") if isinstance(cfg.get("enabled"), dict) else {}
    tier_state = (
        state.get("tier_state")
        if isinstance(state, dict) and isinstance(state.get("tier_state"), dict)
        else {}
    )
    counters = (
        state.get("open_signals_today")
        if isinstance(state, dict) and isinstance(state.get("open_signals_today"), dict)
        else {}
    )

    def _limit_source(tier: str) -> str:
        if str(os.getenv(f"{tier}_LIMIT") or "").strip():
            return "ENV"
        if f"{tier}_LIMIT" in raw or tier in raw_limits:
            return "PERSISTED_CONFIG"
        route_cfg = raw_routes.get(tier)
        if isinstance(route_cfg, dict) and "daily_open_now_limit" in route_cfg:
            return "PERSISTED_CONFIG"
        return "CANONICAL_DEFAULT"

    for tier in ("FREE", "BASIC", "PRO", "ELITE"):
        route_enabled = bool(enabled.get(tier, True))
        mapped = channels.get(tier) not in (None, "", 0)
        mapping_state = "READY" if route_enabled and mapped else "NOT READY"
        observed_state = str(tier_state.get(tier) or "ACTIVE").upper()
        effective_state = observed_state if route_enabled and mapped else "DISABLED"
        counter = counters.get(tier, 0)
        limit = limits.get(tier)
        limit_text = "UNLIMITED" if limit is None else str(limit)
        counter_text = str(counter) if limit is not None else "unlimited"
        lines.append(
            f"{tier}: {effective_state} | {counter_text}/{limit_text} | "
            f"mapping {mapping_state} | limit source {_limit_source(tier)}"
        )

    reset = cfg.get("reset") if isinstance(cfg.get("reset"), dict) else {}
    timezone_name = str(reset.get("timezone") or legacy_distribution.DEFAULT_RESET_TZ)
    hour = int(reset.get("hour", 8))
    minute = int(reset.get("minute", 10))
    lines.extend(["", f"Reset reference: {hour:02d}:{minute:02d} {timezone_name}"])

    if admin_chat_id and admin_chat_id != 0:
        lines.append(f"Admin control chat: {admin_chat_id}")
        if admin_thread_id:
            lines.append(f"Admin thread: {admin_thread_id}")
    else:
        lines.append("Admin control chat: not configured")

    if routes:
        lines.extend(["", "Configured Routes:"])
        lines.extend(f"- {route}" for route in routes)

    lines.extend([
        "",
        "Publication Controls",
        "Read-only effective configuration view. No distribution mutation is performed here.",
    ])
    return _lines(lines)


def render_intelligence_panel('''
replacement = replacement_lf.replace("\n", newline)
updated = pattern.sub(replacement, text, count=1)
with path.open("w", encoding="utf-8", newline="") as handle:
    handle.write(updated)
