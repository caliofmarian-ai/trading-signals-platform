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


def render_symbols(symbols: Optional[List[str]], title: str = "Active Symbols") -> str:
    lines: List[str] = [title, ""]
    if symbols is None:
        lines.append("UNAVAILABLE (active-symbol configuration absent or invalid).")
    elif not symbols:
        lines.append("No active symbols configured in the available persisted configuration.")
    else:
        for sym in symbols:
            lines.append(f"- {sym}")
    return _lines(lines)


def render_engine_status(status: Dict[str, Any]) -> str:
    lines: List[str] = [
        "Engine Status",
        "",
        f"Runtime phase: {_clean(status.get('runtime_phase'))}",
        f"Tick interval: {_clean(status.get('tick_interval'))}",
        f"Last decision ts: {_clean(status.get('last_decision_ts'))}",
        f"Decision count: {_clean(status.get('decision_count'))}",
    ]
    return _lines(lines)


def render_debug_last(
    decision_event: Optional[Dict[str, Any]],
    *,
    availability: Optional[str] = None,
) -> str:
    if availability and availability.startswith("UNAVAILABLE"):
        return _lines(["Signal Debug", "", availability])
    if not decision_event:
        if availability:
            return _lines(
                [
                    "Signal Debug",
                    "",
                    f"Evidence: {availability}",
                    "No decision is recorded in the available event log.",
                ]
            )
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
        *([f"Evidence: {availability}", ""] if availability else []),
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
    availability = _clean(summary.get("availability"), "UNAVAILABLE (not reported)")
    if availability.startswith("UNAVAILABLE"):
        return _lines(["Strategy Report", "", availability])

    lines: List[str] = [
        "Strategy Report",
        "",
        f"Evidence: {availability}",
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


# ---------------------------------------------------------------------------
# Canonical panel renderers — one per new canonical admin tree node.
# Source: ADMIN_TREE_MAP_v2.0.0.md §6; ADMIN_CONTROL_SPEC_v2.0.0.md §9–§14.
# ---------------------------------------------------------------------------

def render_distribution_panel(
    admin_chat_id: int,
    admin_thread_id: int,
    routes: Optional[List[str]] = None,
) -> str:
    """
    Distribution Control panel view.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.5; ADMIN_CONTROL_SPEC_v2.0.0.md §9
    Visibility: read-only; no mutation controls.
    Data source: environment configuration (no live routing backend available).

    Implementation decision: reads available routing configuration from env vars
    because no live distribution-router query API exists at this time.
    """
    lines: List[str] = [
        "Distribution Control",
        "",
        "Route Status",
    ]

    if admin_chat_id and admin_chat_id != 0:
        lines.append(f"Admin control chat: {admin_chat_id}")
        if admin_thread_id:
            lines.append(f"Admin thread: {admin_thread_id}")
    else:
        lines.append("Admin control chat: not configured")

    if routes:
        lines.extend(["", "Configured Routes:"])
        for route in routes:
            lines.append(f"- {route}")
    else:
        lines.extend(["", "No additional routes configured."])

    lines.extend([
        "",
        "Publication Controls",
        "Distribution mutation controls require backend support.",
        "Review SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md for full specification.",
    ])
    return _lines(lines)


def render_intelligence_panel(recent_events: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Intelligence panel view.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.7; ADMIN_CONTROL_SPEC_v2.0.0.md §11
    Visibility: read-only; no mutation controls.
    Data source: recent engine decision events.

    Implementation decision: derives intelligence indicators from available engine
    event data because no dedicated intelligence backend exists at this time.
    """
    lines: List[str] = [
        "Intelligence",
        "",
    ]

    if recent_events is None:
        lines.append("UNAVAILABLE (engine event log absent or invalid).")
        return _lines(lines)

    events = recent_events
    if not events:
        lines.append("No decision events are recorded in the available event log.")
        lines.extend([
            "",
            "Intelligence views become available once the engine has processed signals.",
            "See Decision Visibility panel for the latest decision state.",
        ])
        return _lines(lines)

    decisions = [e for e in events if e.get("event_type") in ("decision", "signal_decision", "decision_evaluated")]
    rejects = [e for e in events if e.get("event_type") in ("reject", "signal_reject")]
    all_kinds = [str(e.get("data", {}).get("decision_kind", "") or "").upper() for e in events if isinstance(e.get("data"), dict)]
    open_now_count = sum(1 for k in all_kinds if k == "OPEN_NOW")
    confirm_count = sum(1 for k in all_kinds if k == "CONFIRM")
    pre_count = sum(1 for k in all_kinds if k == "PRE")
    reject_count = len(rejects) + sum(1 for k in all_kinds if k in ("REJECT", "REJECTED"))

    lines.extend([
        "Decision Intelligence",
        f"Recent events analyzed: {len(events)}",
        f"  OPEN_NOW signals: {open_now_count}",
        f"  CONFIRM signals: {confirm_count}",
        f"  PRE signals: {pre_count}",
        f"  Rejections: {reject_count}",
    ])

    reject_reasons: Dict[str, int] = {}
    for e in events:
        data = e.get("data") if isinstance(e.get("data"), dict) else {}
        reason = (
            data.get("rejected_reason")
            or data.get("reject_reason")
            or (data.get("gates", {}) or {}).get("sr_gate", {}).get("reason")
        )
        if not reason:
            decision_object = data.get("decision_object") if isinstance(data.get("decision_object"), dict) else {}
            reject = decision_object.get("reject") if isinstance(decision_object.get("reject"), dict) else {}
            blockers = reject.get("hard_blockers")
            if isinstance(blockers, list) and blockers:
                reason = ", ".join(str(item) for item in blockers)
        if reason:
            reject_reasons[str(reason)] = reject_reasons.get(str(reason), 0) + 1

    if reject_reasons:
        lines.extend(["", "Rejection Pattern Summary:"])
        for reason, count in sorted(reject_reasons.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"  {reason}: {count}")

    lines.extend([
        "",
        "Drift / Anomaly Indicators",
        "Detailed drift detection requires extended history analysis.",
        "See Research & Analytics panel for performance trends.",
    ])
    return _lines(lines)


def render_system_health_summary(snapshot: Dict[str, Any]) -> str:
    """
    System Health panel summary view.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.10; ADMIN_CONTROL_SPEC_v2.0.0.md §14
    Visibility: read-only; sub-navigation to Engine/Diagnose/Audit available.
    """
    lines: List[str] = [
        "System Health",
        "",
        f"Overall state: {_clean(snapshot.get('overall_state'))}",
        f"Runtime phase: {_clean(snapshot.get('runtime_phase'))}",
        f"Market data: {_clean(snapshot.get('market_data_state'))}",
        f"Market provider: {_clean(snapshot.get('market_data_provider'))}",
        f"Market symbol: {_clean(snapshot.get('market_data_symbol'))}",
        f"History bootstrap: {_clean(snapshot.get('market_data_bootstrap_state'))}",
        f"Live stream: {_clean(snapshot.get('market_data_stream_state'))}",
        f"Provider rate limit: {_clean(snapshot.get('market_data_rate_limit_state'))}",
        f"REST usage (rolling minute): {_clean(snapshot.get('market_data_rest_requests_last_minute'))}/{_clean(snapshot.get('market_data_rest_requests_per_minute_limit'))}",
        f"Recovery state: {_clean(snapshot.get('recovery_state'))}",
        f"Telegram: {_clean(snapshot.get('telegram_state'))}",
        f"FSM state: {_clean(snapshot.get('fsm_state'))}",
        f"Shadow mode: {_clean(snapshot.get('shadow_mode'))}",
    ]
    note = str(snapshot.get("market_data_note") or "").strip()
    if note:
        lines.extend(["", f"Note: {note}"])
    return _lines(lines)


def render_security_audit_panel() -> str:
    """
    Security & Audit panel view.

    Source: ADMIN_TREE_MAP_v2.0.0.md §6.12
    Visibility: read-only summary; audit artifact download available via sub-navigation.
    """
    return _lines([
        "Security & Audit",
        "",
        "Audit surfaces available in this panel:",
        "- Runtime Audit: generates a sanitized audit artifact",
        "- File Browser: browse observability and audit directories",
        "",
        "Admin action logs are stored in admin_events.jsonl and admin_proofs.jsonl.",
        "Use Runtime Audit to generate a downloadable audit artifact.",
        "",
        "Role change audit is performed via the Roles & Identity panel.",
    ])
