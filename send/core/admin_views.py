from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
from collections import Counter

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
    decision_object = data.get("decision_object") if isinstance(data.get("decision_object"), dict) else {}
    setup = decision_object.get("setup") if isinstance(decision_object.get("setup"), dict) else {}
    market = decision_object.get("market_context") if isinstance(decision_object.get("market_context"), dict) else {}
    structure = decision_object.get("structure") if isinstance(decision_object.get("structure"), dict) else {}
    time_context = decision_object.get("time") if isinstance(decision_object.get("time"), dict) else {}
    score = decision_object.get("score") if isinstance(decision_object.get("score"), dict) else {}
    trade_physics = score.get("trade_physics") if isinstance(score.get("trade_physics"), dict) else {}
    reject = decision_object.get("reject") if isinstance(decision_object.get("reject"), dict) else {}
    debug = data.get("debug", {}) if isinstance(data.get("debug"), dict) else {}
    gates = data.get("gates", {}) if isinstance(data.get("gates"), dict) else {}
    sr_gate = gates.get("sr_gate", {}) if isinstance(gates.get("sr_gate"), dict) else {}

    reject_reason = (
        reject.get("reason")
        or
        sr_gate.get("reason")
        or data.get("rejected_reason")
        or data.get("reject_reason")
        or "N/A"
    )

    lines: List[str] = [
        "Signal Debug",
        "",
        *([f"Evidence: {availability}", ""] if availability else []),
        f"PAIR: {_clean(decision_event.get('symbol') or setup.get('symbol') or data.get('symbol'))}",
        f"TIMEFRAME: {_clean(decision_event.get('timeframe') or setup.get('timeframe') or debug.get('tf'))}",
        f"DIRECTION: {_clean(data.get('direction') or setup.get('direction'))}",
        f"SCORE: {_clean(data.get('score_total') if data.get('score_total') is not None else score.get('total'))}",
        f"SCORE TIER: {_clean(data.get('score_tier') or score.get('tier'))}",
        f"RESULT: {_clean(data.get('decision_kind'))}",
        f"REASON: {_clean(reject_reason)}",
    ]

    components = score.get("components") if isinstance(score.get("components"), dict) else {}
    if components:
        lines.extend(["", "Score Composition"])
        for key, value in components.items():
            lines.append(f"{key}: {_clean(value)}")

    if structure:
        lines.extend([
            "",
            "S/R Corridor",
            f"Feasibility: {_clean(structure.get('feasibility_state'))}",
            f"Available distance: {_clean(structure.get('available_distance'))}",
            f"Required distance: {_clean(structure.get('required_distance'))}",
            f"Room ratio: {_clean(structure.get('room_ratio'))}",
            f"Relevant levels: support {_clean(structure.get('support_level_count'))}; resistance {_clean(structure.get('resistance_level_count'))}",
        ])

    if time_context:
        lines.extend([
            "",
            "Time Model",
            f"State: {_clean(time_context.get('time_state'))}",
            f"Time needed: {_clean(time_context.get('t_needed'))}",
            f"Adjusted time needed: {_clean(time_context.get('t_needed_adjusted'))}",
            f"Model reach ratio: {_clean(time_context.get('model_time_reach_ratio'))}",
        ])

    if trade_physics:
        lines.extend([
            "",
            "Trade Physics",
            f"Readiness: {_clean(trade_physics.get('readiness_state'))}",
            f"TPS: {_clean(trade_physics.get('TPS'))}",
            f"S/T/P/V: {_clean(trade_physics.get('S'))} / {_clean(trade_physics.get('T'))} / {_clean(trade_physics.get('P'))} / {_clean(trade_physics.get('V'))}",
            f"Space ratio: {_clean(trade_physics.get('space_to_buffer_ratio'))}",
            f"Time ratio: {_clean(trade_physics.get('time_to_buffer_ratio'))}",
        ])

    blockers = reject.get("hard_blockers")
    if isinstance(blockers, list):
        lines.extend(["", "Hard Blockers"])
        lines.extend([f"- {item}" for item in blockers] or ["NONE"])

    if market:
        lines.extend([
            "",
            "Market Model",
            f"Trend: {_clean(market.get('trend_context'))}",
            f"Volatility: {_clean(market.get('volatility_state'))}",
            f"Noise: {_clean(market.get('noise_context'))}",
            f"Average M1 range: {_clean(market.get('average_m1_range'))}",
            f"Minimum M1 range: {_clean(market.get('minimum_m1_range'))}",
            f"M5 ATR: {_clean(market.get('atr_m5'))}",
        ])

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


def _v3_decisions(events: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not isinstance(events, list):
        return []
    return [
        event for event in events
        if isinstance(event, dict) and event.get("event_type") == "decision_evaluated"
        and isinstance(event.get("data"), dict)
    ]


def _unique_candle_decisions(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep the latest evaluation for each symbol/timeframe/candle.

    Engine ticks are operational evidence, but repeated evaluations of one M1
    candle are not independent strategy samples.
    """
    unique: Dict[tuple[str, str, int], Dict[str, Any]] = {}
    unkeyed: List[Dict[str, Any]] = []
    for event in decisions:
        data = event.get("data", {})
        symbol = str(event.get("symbol") or "").strip().upper()
        timeframe = str(event.get("timeframe") or "").strip().upper()
        candle_ts = data.get("candle_ts")
        if symbol and timeframe and isinstance(candle_ts, int) and not isinstance(candle_ts, bool):
            unique[(symbol, timeframe, candle_ts)] = event
        else:
            unkeyed.append(event)
    return list(unique.values()) + unkeyed


def _decision_blockers(event: Dict[str, Any]) -> List[str]:
    data = event.get("data", {})
    decision_object = data.get("decision_object") if isinstance(data.get("decision_object"), dict) else {}
    reject = decision_object.get("reject") if isinstance(decision_object.get("reject"), dict) else {}
    blockers = reject.get("hard_blockers")
    return [str(item) for item in blockers] if isinstance(blockers, list) else []


def render_research_analytics_panel(recent_events: Optional[List[Dict[str, Any]]]) -> str:
    """Descriptive v3 strategy analytics; never strategy mutation authority."""
    if recent_events is None:
        return _lines(["Research & Analytics", "", "UNAVAILABLE (engine event log absent or invalid)."])
    raw_decisions = _v3_decisions(recent_events)
    decisions = _unique_candle_decisions(raw_decisions)
    if not decisions:
        return _lines([
            "Research & Analytics", "", "No v3 strategy evaluations are recorded in the selected evidence window.",
            "No threshold conclusion can be made.",
        ])

    kinds = Counter(str(event["data"].get("decision_kind") or "UNKNOWN").upper() for event in decisions)
    blockers = Counter(blocker for event in decisions for blocker in _decision_blockers(event))
    scores = [float(event["data"]["score_total"]) for event in decisions if isinstance(event["data"].get("score_total"), (int, float)) and not isinstance(event["data"].get("score_total"), bool)]
    tps_values = []
    for event in decisions:
        trade_physics = event["data"].get("trade_physics")
        tps = trade_physics.get("TPS") if isinstance(trade_physics, dict) else None
        if isinstance(tps, (int, float)) and not isinstance(tps, bool):
            tps_values.append(float(tps))

    lines = [
        "Research & Analytics", "",
        f"Evidence window: latest {len(recent_events)} engine events",
        f"Raw strategy evaluations: {len(raw_decisions)}",
        f"V3 strategy evaluations (unique candles): {len(decisions)}",
        f"REJECT: {kinds['REJECT']}",
        f"NO_SIGNAL: {kinds['NO_SIGNAL']}",
        f"PRE: {kinds['PRE']}",
        f"CONFIRM: {kinds['CONFIRM']}",
        f"OPEN_NOW: {kinds['OPEN_NOW']}",
        f"Average classical score: {round(sum(scores) / len(scores), 2) if scores else 'UNAVAILABLE'}",
        f"Average ready TPS: {round(sum(tps_values) / len(tps_values), 2) if tps_values else 'UNAVAILABLE'}",
        "", "Top Hard Blockers",
    ]
    lines.extend([f"- {reason}: {count}" for reason, count in blockers.most_common(5)] or ["- NONE RECORDED"])
    lines.extend([
        "", "Evidence qualification",
        "Descriptive only. The window and sample count are shown explicitly.",
        "No threshold or production-strategy change is authorized by this view.",
    ])
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

    raw_decisions = _v3_decisions(events)
    decisions = _unique_candle_decisions(raw_decisions)
    rejects = [e for e in events if e.get("event_type") in ("reject", "signal_reject")]
    all_kinds = [str(e.get("data", {}).get("decision_kind", "") or "").upper() for e in decisions if isinstance(e.get("data"), dict)]
    open_now_count = sum(1 for k in all_kinds if k == "OPEN_NOW")
    confirm_count = sum(1 for k in all_kinds if k == "CONFIRM")
    pre_count = sum(1 for k in all_kinds if k == "PRE")
    reject_count = len(rejects) + sum(1 for k in all_kinds if k in ("REJECT", "REJECTED"))

    lines.extend([
        "Decision Intelligence",
        f"Recent events analyzed: {len(events)}",
        f"Raw strategy evaluations: {len(raw_decisions)}",
        f"V3 strategy evaluations (unique candles): {len(decisions)}",
        f"  OPEN_NOW signals: {open_now_count}",
        f"  CONFIRM signals: {confirm_count}",
        f"  PRE signals: {pre_count}",
        f"  Rejections: {reject_count}",
    ])

    reject_reasons: Dict[str, int] = {}
    for e in decisions:
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

        total_reject_reasons = sum(reject_reasons.values())
        dominant_reason, dominant_count = max(reject_reasons.items(), key=lambda item: item[1])
        dominant_share = dominant_count / total_reject_reasons if total_reject_reasons else 0.0
        lines.extend([
            "", "Bottleneck Observation",
            f"Dominant blocker set: {dominant_reason}",
            f"Observed share: {dominant_count}/{total_reject_reasons} ({dominant_share:.1%})",
            "Interpretation: descriptive candidate bottleneck; evidence adequacy is not yet certified.",
            "Recommendation: continue evidence collection and investigate this layer before changing score thresholds.",
        ])

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
