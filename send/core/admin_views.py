from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from core.telegram_runtime import command_registry


def _clean(value: Any, fallback: str = "N/A") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _lines(items: Iterable[str]) -> str:
    return "\n".join(str(x) for x in items)


def render_unauthorized() -> str:
    return "Unauthorized command."


def render_error(message: str) -> str:
    return f"Error\n\n{_clean(message, 'Unknown error')}"


def render_admin_home(identity: Dict[str, Any]) -> str:
    roles = identity.get("roles", [])
    primary_role = identity.get("primary_role", "USER")
    command_lines = [spec.usage for spec in command_registry() if spec.access == "admin"]

    lines: List[str] = [
        "BinaryBot Admin Panel",
        "",
        f"Primary role: {primary_role}",
        f"All roles: {', '.join(roles) if roles else 'USER'}",
        "",
        "Available commands:",
    ]
    lines.extend(command_lines)
    return _lines(lines)


def render_strategy_status(params: Dict[str, Any]) -> str:
    thresholds = params.get("score_thresholds", {})
    spike = params.get("spike_filters", {})

    lines: List[str] = [
        "Strategy Status",
        "",
        f"PRE threshold: {_clean(thresholds.get('PRE'))}",
        f"CONFIRM threshold: {_clean(thresholds.get('CONFIRM'))}",
        f"OPEN threshold: {_clean(thresholds.get('OPEN'))}",
        "",
        f"SR required multiplier: {_clean(params.get('sr_required_multiplier'))}",
        f"Spike wick_body_ratio_max: {_clean(spike.get('wick_body_ratio_max'))}",
        f"Spike range_z_max: {_clean(spike.get('range_z_max'))}",
        f"Spike jump_vs_atr_max: {_clean(spike.get('jump_vs_atr_max'))}",
    ]
    return _lines(lines)


def render_ok(message: str) -> str:
    return f"OK\n\n{_clean(message)}"


def render_symbols(symbols: List[str], title: str = "Active Symbols") -> str:
    lines: List[str] = [title, ""]
    if not symbols:
        lines.append("No active symbols.")
    else:
        for sym in symbols:
            lines.append(f"- {sym}")
    return _lines(lines)


def render_engine_status(status: Dict[str, Any]) -> str:
    lines: List[str] = [
        "Engine Status",
        "",
        f"Running: {_clean(status.get('running'))}",
        f"Tick interval: {_clean(status.get('tick_interval'))}",
        f"Last decision ts: {_clean(status.get('last_decision_ts'))}",
        f"Decision count: {_clean(status.get('decision_count'))}",
    ]
    return _lines(lines)


def render_debug_last(decision_event: Optional[Dict[str, Any]]) -> str:
    if not decision_event:
        return "Signal Debug\n\nNo recent decision found."

    data = decision_event.get("data", {}) if isinstance(decision_event, dict) else {}
    debug = data.get("debug", {}) if isinstance(data.get("debug"), dict) else {}
    gates = data.get("gates", {}) if isinstance(data.get("gates"), dict) else {}
    sr_gate = gates.get("sr_gate", {}) if isinstance(gates.get("sr_gate"), dict) else {}

    reject_reason = (
        sr_gate.get("reason")
        or data.get("rejected_reason")
        or data.get("reject_reason")
        or "N/A"
    )

    lines: List[str] = [
        "Signal Debug",
        "",
        f"PAIR: {_clean(data.get('symbol'))}",
        f"TIMEFRAME: {_clean(debug.get('tf'))}",
        f"SCORE: {_clean(data.get('score_total'))}",
        f"RESULT: {_clean(data.get('decision_kind'))}",
        f"REASON: {_clean(reject_reason)}",
    ]

    if sr_gate:
        lines.extend(
            [
                "",
                "SR Gate",
                f"OK: {_clean(sr_gate.get('ok'))}",
                f"Required space: {_clean((sr_gate.get('details') or {}).get('required_space'))}",
                f"Available space: {_clean((sr_gate.get('details') or {}).get('available_space'))}",
            ]
        )

    return _lines(lines)


def render_report_summary(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "Strategy Report",
        "",
        f"Date: {_clean(summary.get('date'))}",
        f"Decisions: {_clean(summary.get('decisions'))}",
        f"Rejects: {_clean(summary.get('rejects'))}",
        f"PRE: {_clean(summary.get('pre'))}",
        f"CONFIRM: {_clean(summary.get('confirm'))}",
        f"OPEN_NOW: {_clean(summary.get('open_now'))}",
        f"Avg score: {_clean(summary.get('avg_score'))}",
    ]

    top_rejects = summary.get("top_rejects", [])
    if top_rejects:
        lines.extend(["", "Top Reject Reasons:"])
        for item in top_rejects:
            lines.append(f"- {_clean(item)}")

    return _lines(lines)


def render_roles(identity: Dict[str, Any], known_roles: Dict[str, List[str]]) -> str:
    lines: List[str] = [
        "Role Matrix",
        "",
        f"Your primary role: {_clean(identity.get('primary_role'))}",
        f"Your roles: {', '.join(identity.get('roles', [])) if identity.get('roles') else 'USER'}",
        "",
        "Configured role membership:",
    ]

    for key, values in known_roles.items():
        lines.append("")
        lines.append(f"{key}:")
        if not values:
            lines.append("- none")
        else:
            for value in values:
                lines.append(f"- {value}")

    return _lines(lines)


def render_affiliate_scope(scope: Optional[Dict[str, Any]]) -> str:
    if not scope:
        return "Affiliate Scope\n\nNo affiliate scope assigned."

    lines: List[str] = [
        "Affiliate Scope",
        "",
        f"Affiliate code: {_clean(scope.get('affiliate_code'))}",
        f"Telegram ID: {_clean(scope.get('telegram_id'))}",
        f"Display name: {_clean(scope.get('display_name'))}",
        f"Commission %: {_clean(scope.get('commission_percent'))}",
    ]
    return _lines(lines)