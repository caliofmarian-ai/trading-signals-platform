"""Canonical v3 Distribution Router for live SignalEvent publication.

This module consumes a validated SignalEvent candidate after Signal Engine
exact-stage handoff. It owns route evaluation, entitlement, destination state,
deduplication and publisher invocation. It never recalculates strategy,
Trade Physics or FSM truth and it never executes broker trades.

The legacy ``core.distribution_router`` module remains available as an explicit
migration adapter for older analytics/tests. This module emits the v3 primary
event families while also writing the legacy ``tier_publish``/``tier_reset``
adapters required by existing readers during migration.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import os
import time
from typing import Any, Dict, Mapping, Optional
from zoneinfo import ZoneInfo

from core import distribution_router as legacy
from core import observability_logger
from core import outcome_service


TIERS = ("FREE", "BASIC", "PRO", "ELITE")
LIMITED_TIERS = frozenset({"FREE", "BASIC", "PRO"})
SCHEMA_VERSION = "3.0.0"
DEFAULT_LIMITS = {"FREE": 6, "BASIC": 20, "PRO": 50, "ELITE": None}


def _event_dict(event: Any) -> Dict[str, Any]:
    if hasattr(event, "to_dict") and callable(event.to_dict):
        payload = event.to_dict()
    elif isinstance(event, Mapping):
        payload = dict(event)
    else:
        raise TypeError("distribution candidate must be SignalEvent-compatible")
    return dict(payload)


def _build_event(
    event_type: str,
    data: Dict[str, Any],
    *,
    correlation: Optional[Dict[str, Any]] = None,
    source_function: str = "route",
) -> Dict[str, Any]:
    event = observability_logger.build_event(
        event_type,
        data,
        source={"module": "distribution_router_v3", "function": source_function},
        correlation=correlation,
    )
    event["schema_version"] = SCHEMA_VERSION
    return observability_logger.validate_event(event)


def _log_event(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    event = _build_event(*args, **kwargs)
    observability_logger.log_event(event)
    return event


def _safe_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_limit(value: Any, default: Optional[int]) -> Optional[int]:
    if value is None or value == "":
        return default
    if isinstance(value, str) and value.strip().upper() in {"UNLIMITED", "NONE", "INF"}:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_effective_config() -> Dict[str, Any]:
    """Load legacy/env config and accept the optional route-first representation."""

    cfg = legacy.load_config()
    channels = dict(cfg.get("channels") or {})
    limits = dict(DEFAULT_LIMITS)
    limits.update(cfg.get("limits") or {})
    enabled = {tier: True for tier in TIERS}
    feedback_capable = {tier: tier == "ELITE" for tier in TIERS}

    raw = legacy._load_channel_config_file()  # migration-compatible config source
    route_cfgs = raw.get("routes") if isinstance(raw, dict) else None
    if isinstance(route_cfgs, dict):
        for tier in TIERS:
            route_cfg = route_cfgs.get(tier)
            if not isinstance(route_cfg, dict):
                continue
            enabled[tier] = bool(route_cfg.get("enabled", True))
            feedback_capable[tier] = bool(
                route_cfg.get("feedback_capable", tier == "ELITE")
            )
            if not os.getenv(f"{tier}_CHANNEL_ID"):
                route_destination = _safe_int(route_cfg.get("destination_id"))
                if route_destination is not None:
                    channels[tier] = route_destination
            if not os.getenv(f"{tier}_LIMIT") and "daily_open_now_limit" in route_cfg:
                limits[tier] = _parse_limit(
                    route_cfg.get("daily_open_now_limit"), DEFAULT_LIMITS[tier]
                )

    # Canonical baseline wins when no governed override is present.
    if not os.getenv("FREE_LIMIT"):
        raw_free = None
        if isinstance(raw, dict):
            raw_free = raw.get("FREE_LIMIT")
            if raw_free is None and isinstance(raw.get("limits"), dict):
                raw_free = raw["limits"].get("FREE")
            if raw_free is None and isinstance(route_cfgs, dict):
                route_free = route_cfgs.get("FREE")
                if isinstance(route_free, dict):
                    raw_free = route_free.get("daily_open_now_limit")
        if raw_free is None:
            limits["FREE"] = 6

    return {
        "channels": channels,
        "admin": dict(cfg.get("admin") or {}),
        "limits": limits,
        "reset": dict(cfg.get("reset") or {}),
        "enabled": enabled,
        "feedback_capable": feedback_capable,
    }


def _route_is_configured(cfg: Dict[str, Any], tier: str) -> bool:
    return bool(cfg["enabled"].get(tier, True) and cfg["channels"].get(tier))


def _log_route_state_change(route: str, before: str, after: str, reason: str) -> None:
    if before == after:
        return
    _log_event(
        "route_state_changed",
        {"route": route, "before": before, "after": after, "reason": reason},
        source_function="_log_route_state_change",
    )


def _sync_config_states(state: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    changed = False
    for tier in TIERS:
        before = str(state["tier_state"].get(tier) or "ACTIVE").upper()
        configured = _route_is_configured(cfg, tier)
        if not configured:
            after = "DISABLED"
        elif before == "DISABLED":
            after = "ACTIVE"
        else:
            after = before
        if after != before:
            state["tier_state"][tier] = after
            changed = True
            _log_route_state_change(
                tier,
                before,
                after,
                "CONFIG_ROUTE_AVAILABLE" if after == "ACTIVE" else "CONFIG_ROUTE_UNAVAILABLE",
            )
    if changed:
        legacy.save_state(state)
    return state


def _maybe_daily_reset(
    state: Dict[str, Any], cfg: Dict[str, Any], now_ts: int
) -> tuple[Dict[str, Any], bool]:
    reset_cfg = cfg.get("reset") or {}
    timezone_name = str(reset_cfg.get("timezone") or legacy.DEFAULT_RESET_TZ)
    try:
        reset_tz = ZoneInfo(timezone_name)
    except Exception:
        reset_tz = ZoneInfo(legacy.DEFAULT_RESET_TZ)
    hour = int(reset_cfg.get("hour", 8))
    minute = int(reset_cfg.get("minute", 10))
    now_local = datetime.fromtimestamp(int(now_ts), tz=reset_tz)
    today = now_local.date().isoformat()

    if (now_local.hour, now_local.minute) < (hour, minute):
        return state, False
    if state.get("last_reset_london_date") == today:
        return state, False

    before = deepcopy(state)
    state["last_reset_london_date"] = today
    state["open_signals_today"] = {tier: 0 for tier in TIERS}
    for tier in TIERS:
        state["tier_state"][tier] = (
            "ACTIVE" if _route_is_configured(cfg, tier) else "DISABLED"
        )
    legacy.save_state(state)

    # Primary v3 reset/state evidence.
    for tier in TIERS:
        prior = str(before.get("tier_state", {}).get(tier) or "ACTIVE")
        after = str(state["tier_state"].get(tier) or "ACTIVE")
        _log_event(
            "route_reset",
            {
                "route": tier,
                "reason": f"DAILY_RESET_{hour:02d}:{minute:02d}_{reset_tz.key}",
                "before": {
                    "state": prior,
                    "counter": int(before.get("open_signals_today", {}).get(tier, 0)),
                },
                "after": {"state": after, "counter": 0},
            },
            source_function="_maybe_daily_reset",
        )
        _log_route_state_change(tier, prior, after, "DAILY_RESET")

    # Explicit v2 migration adapter retained for existing analytics/readers.
    adapter = observability_logger.build_event(
        "tier_reset",
        {
            "reset_time_london": f"{hour:02d}:{minute:02d} {reset_tz.key}",
            "effective_date_london": today,
            "before": {
                "tier_state": dict(before.get("tier_state", {})),
                "open_signals_today": dict(before.get("open_signals_today", {})),
                "last_reset_london_date": before.get("last_reset_london_date"),
            },
            "after": {
                "tier_state": dict(state.get("tier_state", {})),
                "open_signals_today": dict(state.get("open_signals_today", {})),
                "last_reset_london_date": state.get("last_reset_london_date"),
            },
        },
        source={"module": "distribution_router_v3", "function": "_maybe_daily_reset"},
    )
    adapter["schema_version"] = SCHEMA_VERSION
    observability_logger.log_event(observability_logger.validate_event(adapter))
    return state, True


def _attempt_event(
    event: Dict[str, Any],
    *,
    route: str,
    destination_id: Optional[int],
    route_state: str,
    attempted: bool,
    counter_before: int,
    limit: Optional[int],
    dedup_key: str,
    was_duplicate: bool,
) -> Dict[str, Any]:
    correlation: Dict[str, Any] = {
        "signal_id": str(event["signal_id"]),
        "route": route,
        "stage": str(event["stage"]),
        "symbol": event.get("symbol"),
        "timeframe": event.get("timeframe"),
    }
    if destination_id is not None:
        correlation["destination_id"] = int(destination_id)
    return _log_event(
        "route_publish_attempt",
        {
            "route_state": route_state,
            "attempted": attempted,
            "counter_before": counter_before,
            "limit": limit,
            "mapping": {"destination_resolved": destination_id is not None},
            "dedup": {"key": dedup_key, "was_duplicate": was_duplicate},
        },
        correlation=correlation,
        source_function="route",
    )


def _result_event(
    event: Dict[str, Any],
    *,
    route: str,
    destination_id: Optional[int],
    publish_result: str,
    route_state_before: str,
    route_state_after: str,
    counted: bool,
    counter_before: int,
    counter_after: int,
    transport_ok: bool,
    message_id: Optional[int],
    transport_error: Optional[str],
    dedup_key: str,
    was_duplicate: bool,
    dedup_action: str,
    reason: Optional[str],
) -> Dict[str, Any]:
    correlation: Dict[str, Any] = {
        "signal_id": str(event["signal_id"]),
        "route": route,
        "stage": str(event["stage"]),
        "symbol": event.get("symbol"),
        "timeframe": event.get("timeframe"),
    }
    if destination_id is not None:
        correlation["destination_id"] = int(destination_id)
    return _log_event(
        "route_publish_result",
        {
            "publish_result": publish_result,
            "route_state_before": route_state_before,
            "route_state_after": route_state_after,
            "counter_before": counter_before,
            "counter_after": counter_after,
            "counted": counted,
            "transport": {
                "ok": transport_ok,
                "message_id": message_id,
                "error": transport_error,
            },
            "dedup": {
                "key": dedup_key,
                "was_duplicate": was_duplicate,
                "action": dedup_action,
            },
            "reason": reason,
        },
        correlation=correlation,
        source_function="route",
    )


def _legacy_publish_adapter(
    *,
    route_name: str,
    destination_kind: str,
    tier: str,
    event: Dict[str, Any],
    publish_result: str,
    route_state_before: str,
    route_state_after: str,
    limit: Optional[int],
    counter_before: int,
    counter_after: int,
    counted: bool,
    attempted: bool,
    telegram_ok: bool,
    message_id: Optional[int],
    transport_error: Optional[str],
    reason: Optional[str],
    dedup_key: str,
    was_duplicate: bool,
    dedup_action: str,
    chat_id: Optional[int],
    thread_id: Optional[int],
    feedback_enabled: bool,
) -> None:
    legacy._log_tier_publish(
        route_name=route_name,
        destination_kind=destination_kind,
        tier=tier,
        event=event,
        publish_result=publish_result,
        route_state_before=route_state_before,
        route_state_after=route_state_after,
        limit=limit,
        counter_before=counter_before,
        counter_after=counter_after,
        counted=counted,
        attempted=attempted,
        telegram_ok=telegram_ok,
        message_id=message_id,
        transport_error=transport_error,
        reason=reason,
        dedup_key=dedup_key,
        was_duplicate=was_duplicate,
        dedup_action=dedup_action,
        chat_id=chat_id,
        thread_id=thread_id,
        feedback_enabled=feedback_enabled,
    )


def _visibility_event(
    event: Dict[str, Any],
    *,
    route: str,
    destination_id: int,
    message_id: Optional[int],
    result_event_id: str,
) -> Dict[str, Any]:
    return _log_event(
        "signal_stage_visible",
        {
            "visibility_result": "PUBLISHED",
            "publication_evidence_ref": result_event_id,
            "route": route,
            "destination_id": int(destination_id),
            "message_id": message_id,
        },
        correlation={
            "signal_id": str(event["signal_id"]),
            "stage": str(event["stage"]),
        },
        source_function="route",
    )


def _record_summary_result(
    summary: Dict[str, Any],
    result_event: Dict[str, Any],
    *,
    route: str,
    publish_result: str,
    destination_id: Optional[int],
    message_id: Optional[int],
) -> None:
    item = {
        "event_id": result_event["event_id"],
        "route": route,
        "publish_result": publish_result,
        "destination_id": destination_id,
        "message_id": message_id,
    }
    summary["route_results"].append(item)
    if publish_result == "PUBLISHED":
        summary["published_count"] += 1
        summary["publication_evidence"].append(dict(item))
    elif publish_result == "FAILED":
        summary["failed_count"] += 1
    else:
        summary["skipped_count"] += 1


def route(candidate: Any, now_ts: Optional[int] = None) -> Dict[str, Any]:
    """Evaluate and publish one governed SignalEvent candidate.

    Returns a distribution summary that Signal Engine can use for the
    POST_DISTRIBUTION execution checkpoint. Broker execution is never invoked.
    """

    event = _event_dict(candidate)
    now_ts = int(now_ts or time.time())
    summary: Dict[str, Any] = {
        "published_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "blocked": False,
        "block_reason": None,
        "route_results": [],
        "publication_evidence": [],
    }

    if os.getenv("MARKET_DATA_PROVIDER", "TWELVE_DATA").strip().upper() == "FINNHUB":
        observability_logger.log_warning(
            warn_type="FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED",
            message="Finnhub personal-use market data cannot publish signals to Telegram channels",
            context={
                "signal_id": event.get("signal_id"),
                "stage": event.get("stage"),
                "provider": "FINNHUB",
            },
            source={"module": "distribution_router_v3", "function": "route"},
        )
        summary["blocked"] = True
        summary["block_reason"] = "FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED"
        return summary

    stage = str(event.get("stage") or "").upper()
    signal_id = str(event.get("signal_id") or "").strip()
    if stage not in {"PRE", "CONFIRM", "OPEN_NOW"} or not signal_id:
        observability_logger.log_warning(
            warn_type="distribution_invalid_event",
            message="Distribution router rejected invalid SignalEvent candidate",
            context={
                "signal_id": signal_id,
                "stage": stage,
                "event_type": event.get("event_type"),
            },
            source={"module": "distribution_router_v3", "function": "route"},
        )
        summary["blocked"] = True
        summary["block_reason"] = "INVALID_SIGNAL_EVENT"
        return summary

    event["stage"] = stage
    event["signal_id"] = signal_id
    cfg = _load_effective_config()
    state = legacy.load_state()
    state = _sync_config_states(state, cfg)
    state, _ = _maybe_daily_reset(state, cfg, now_ts)

    destinations: list[Dict[str, Any]] = []
    for tier in TIERS:
        destinations.append(
            {
                "name": tier,
                "tier": tier,
                "chat_id": _safe_int(cfg["channels"].get(tier)),
                "thread_id": None,
                "is_tier": True,
                "applies_limits": tier in LIMITED_TIERS,
                "feedback_enabled": bool(cfg["feedback_capable"].get(tier, tier == "ELITE")),
            }
        )

    admin_group_id = _safe_int(cfg["admin"].get("group_id"))
    admin_topic_id = _safe_int(cfg["admin"].get("signals_live_topic_id"))
    if admin_group_id and admin_topic_id:
        destinations.append(
            {
                "name": "ADMIN_SIGNALS_LIVE",
                "tier": "ELITE",
                "chat_id": admin_group_id,
                "thread_id": admin_topic_id,
                "is_tier": False,
                "applies_limits": False,
                # Community/member buttons belong to the ELITE member route, not admin mirror.
                "feedback_enabled": False,
            }
        )

    for dest in destinations:
        route_name = str(dest["name"])
        tier = str(dest["tier"])
        chat_id = dest["chat_id"]
        thread_id = dest["thread_id"]
        is_tier = bool(dest["is_tier"])
        applies_limits = bool(dest["applies_limits"])
        feedback_available = bool(dest["feedback_enabled"])
        destination_kind = "tier_channel" if is_tier else "admin_topic"
        limit = cfg["limits"].get(tier) if is_tier else None
        counter_before = int(state["open_signals_today"].get(tier, 0))
        route_state_before = (
            str(state["tier_state"].get(tier) or "ACTIVE") if is_tier else "ACTIVE"
        )
        dedup_scope = tier if is_tier else route_name
        dedup_key = legacy.tier_dedup_key(dedup_scope, signal_id, stage)
        was_duplicate = legacy.tier_dedup_check(state, dedup_scope, signal_id, stage)

        if is_tier and (not cfg["enabled"].get(tier, True) or not chat_id):
            if route_state_before != "DISABLED":
                state["tier_state"][tier] = "DISABLED"
                legacy.save_state(state)
                _log_route_state_change(tier, route_state_before, "DISABLED", "MAPPING_OR_CONFIG_DISABLED")
                route_state_before = "DISABLED"
            _log_event(
                "route_mapping_invalid",
                {
                    "route": tier,
                    "reason": "ROUTE_DISABLED_OR_DESTINATION_MISSING",
                    "mapping": {"destination_id": chat_id},
                },
                source_function="route",
            )
            _attempt_event(
                event,
                route=route_name,
                destination_id=chat_id,
                route_state="DISABLED",
                attempted=False,
                counter_before=counter_before,
                limit=limit,
                dedup_key=dedup_key,
                was_duplicate=False,
            )
            result_event = _result_event(
                event,
                route=route_name,
                destination_id=chat_id,
                publish_result="SKIPPED_DISABLED",
                route_state_before="DISABLED",
                route_state_after="DISABLED",
                counted=False,
                counter_before=counter_before,
                counter_after=counter_before,
                transport_ok=False,
                message_id=None,
                transport_error=None,
                dedup_key=dedup_key,
                was_duplicate=False,
                dedup_action="skip_disabled",
                reason="missing_or_disabled_destination",
            )
            _legacy_publish_adapter(
                route_name=route_name,
                destination_kind=destination_kind,
                tier=tier,
                event=event,
                publish_result="SKIPPED_DISABLED",
                route_state_before="DISABLED",
                route_state_after="DISABLED",
                limit=limit,
                counter_before=counter_before,
                counter_after=counter_before,
                counted=False,
                attempted=False,
                telegram_ok=False,
                message_id=None,
                transport_error=None,
                reason="missing_or_disabled_destination",
                dedup_key=dedup_key,
                was_duplicate=False,
                dedup_action="skip_disabled",
                chat_id=chat_id,
                thread_id=thread_id,
                feedback_enabled=feedback_available,
            )
            _record_summary_result(
                summary,
                result_event,
                route=route_name,
                publish_result="SKIPPED_DISABLED",
                destination_id=chat_id,
                message_id=None,
            )
            continue

        if is_tier and route_state_before == "SILENT":
            _attempt_event(
                event,
                route=route_name,
                destination_id=chat_id,
                route_state="SILENT",
                attempted=False,
                counter_before=counter_before,
                limit=limit,
                dedup_key=dedup_key,
                was_duplicate=False,
            )
            result_event = _result_event(
                event,
                route=route_name,
                destination_id=chat_id,
                publish_result="SKIPPED_SILENT",
                route_state_before="SILENT",
                route_state_after="SILENT",
                counted=False,
                counter_before=counter_before,
                counter_after=counter_before,
                transport_ok=False,
                message_id=None,
                transport_error=None,
                dedup_key=dedup_key,
                was_duplicate=False,
                dedup_action="skip_silent",
                reason="route_silent",
            )
            _legacy_publish_adapter(
                route_name=route_name,
                destination_kind=destination_kind,
                tier=tier,
                event=event,
                publish_result="SKIPPED_SILENT",
                route_state_before="SILENT",
                route_state_after="SILENT",
                limit=limit,
                counter_before=counter_before,
                counter_after=counter_before,
                counted=False,
                attempted=False,
                telegram_ok=False,
                message_id=None,
                transport_error=None,
                reason="route_silent",
                dedup_key=dedup_key,
                was_duplicate=False,
                dedup_action="skip_silent",
                chat_id=chat_id,
                thread_id=thread_id,
                feedback_enabled=feedback_available,
            )
            _record_summary_result(
                summary,
                result_event,
                route=route_name,
                publish_result="SKIPPED_SILENT",
                destination_id=chat_id,
                message_id=None,
            )
            continue

        if is_tier and stage == "OPEN_NOW" and applies_limits and isinstance(limit, int):
            if counter_before >= limit:
                state["tier_state"][tier] = "SILENT"
                legacy.save_state(state)
                _log_route_state_change(tier, route_state_before, "SILENT", "ENTITLEMENT_EXHAUSTED")
                _attempt_event(
                    event,
                    route=route_name,
                    destination_id=chat_id,
                    route_state="SILENT",
                    attempted=False,
                    counter_before=counter_before,
                    limit=limit,
                    dedup_key=dedup_key,
                    was_duplicate=False,
                )
                result_event = _result_event(
                    event,
                    route=route_name,
                    destination_id=chat_id,
                    publish_result="SKIPPED_LIMIT",
                    route_state_before=route_state_before,
                    route_state_after="SILENT",
                    counted=False,
                    counter_before=counter_before,
                    counter_after=counter_before,
                    transport_ok=False,
                    message_id=None,
                    transport_error=None,
                    dedup_key=dedup_key,
                    was_duplicate=False,
                    dedup_action="skip_limit",
                    reason="limit_reached",
                )
                _legacy_publish_adapter(
                    route_name=route_name,
                    destination_kind=destination_kind,
                    tier=tier,
                    event=event,
                    publish_result="SKIPPED_LIMIT",
                    route_state_before=route_state_before,
                    route_state_after="SILENT",
                    limit=limit,
                    counter_before=counter_before,
                    counter_after=counter_before,
                    counted=False,
                    attempted=False,
                    telegram_ok=False,
                    message_id=None,
                    transport_error=None,
                    reason="limit_reached",
                    dedup_key=dedup_key,
                    was_duplicate=False,
                    dedup_action="skip_limit",
                    chat_id=chat_id,
                    thread_id=thread_id,
                    feedback_enabled=feedback_available,
                )
                _record_summary_result(
                    summary,
                    result_event,
                    route=route_name,
                    publish_result="SKIPPED_LIMIT",
                    destination_id=chat_id,
                    message_id=None,
                )
                continue

        if was_duplicate:
            _attempt_event(
                event,
                route=route_name,
                destination_id=chat_id,
                route_state=route_state_before,
                attempted=False,
                counter_before=counter_before,
                limit=limit,
                dedup_key=dedup_key,
                was_duplicate=True,
            )
            result_event = _result_event(
                event,
                route=route_name,
                destination_id=chat_id,
                publish_result="DUPLICATE_SUPPRESSED",
                route_state_before=route_state_before,
                route_state_after=route_state_before,
                counted=False,
                counter_before=counter_before,
                counter_after=counter_before,
                transport_ok=False,
                message_id=None,
                transport_error=None,
                dedup_key=dedup_key,
                was_duplicate=True,
                dedup_action="suppress",
                reason="duplicate_suppressed",
            )
            _legacy_publish_adapter(
                route_name=route_name,
                destination_kind=destination_kind,
                tier=tier,
                event=event,
                publish_result="DUPLICATE_SUPPRESSED",
                route_state_before=route_state_before,
                route_state_after=route_state_before,
                limit=limit,
                counter_before=counter_before,
                counter_after=counter_before,
                counted=False,
                attempted=False,
                telegram_ok=False,
                message_id=None,
                transport_error=None,
                reason="duplicate_suppressed",
                dedup_key=dedup_key,
                was_duplicate=True,
                dedup_action="suppress",
                chat_id=chat_id,
                thread_id=thread_id,
                feedback_enabled=feedback_available,
            )
            _record_summary_result(
                summary,
                result_event,
                route=route_name,
                publish_result="DUPLICATE_SUPPRESSED",
                destination_id=chat_id,
                message_id=None,
            )
            continue

        _attempt_event(
            event,
            route=route_name,
            destination_id=chat_id,
            route_state=route_state_before,
            attempted=True,
            counter_before=counter_before,
            limit=limit,
            dedup_key=dedup_key,
            was_duplicate=False,
        )

        text = legacy.render_signal_text(event, tier if is_tier else "ADMIN")
        feedback_enabled = bool(feedback_available and stage == "OPEN_NOW")
        reply_markup = legacy.build_feedback_markup(signal_id) if feedback_enabled else None
        route_state_after = route_state_before
        counted = False
        message_id: Optional[int] = None

        try:
            response = legacy.telegram_publisher.send_message(
                chat_id=int(chat_id),
                text=text,
                reply_markup=reply_markup,
                thread_id=thread_id,
            )
            ok = bool(response.get("ok"))
            if ok:
                message_id = _safe_int((response.get("result") or {}).get("message_id"))
                legacy.tier_dedup_mark(state, dedup_scope, signal_id, stage)
                if is_tier and stage == "OPEN_NOW" and applies_limits:
                    state["open_signals_today"][tier] = counter_before + 1
                    counted = True
                    if isinstance(limit, int) and state["open_signals_today"][tier] >= limit:
                        state["tier_state"][tier] = "SILENT"
                        route_state_after = "SILENT"
                        _log_route_state_change(
                            tier,
                            route_state_before,
                            "SILENT",
                            "ENTITLEMENT_EXHAUSTED_AFTER_PUBLICATION",
                        )
                legacy.save_state(state)

                result_event = _result_event(
                    event,
                    route=route_name,
                    destination_id=chat_id,
                    publish_result="PUBLISHED",
                    route_state_before=route_state_before,
                    route_state_after=route_state_after,
                    counted=counted,
                    counter_before=counter_before,
                    counter_after=int(state["open_signals_today"].get(tier, 0)),
                    transport_ok=True,
                    message_id=message_id,
                    transport_error=None,
                    dedup_key=dedup_key,
                    was_duplicate=False,
                    dedup_action="publish",
                    reason=None,
                )
                _legacy_publish_adapter(
                    route_name=route_name,
                    destination_kind=destination_kind,
                    tier=tier,
                    event=event,
                    publish_result="PUBLISHED",
                    route_state_before=route_state_before,
                    route_state_after=route_state_after,
                    limit=limit,
                    counter_before=counter_before,
                    counter_after=int(state["open_signals_today"].get(tier, 0)),
                    counted=counted,
                    attempted=True,
                    telegram_ok=True,
                    message_id=message_id,
                    transport_error=None,
                    reason=None,
                    dedup_key=dedup_key,
                    was_duplicate=False,
                    dedup_action="publish",
                    chat_id=chat_id,
                    thread_id=thread_id,
                    feedback_enabled=feedback_enabled,
                )
                _visibility_event(
                    event,
                    route=route_name,
                    destination_id=int(chat_id),
                    message_id=message_id,
                    result_event_id=result_event["event_id"],
                )
                if is_tier and tier == "ELITE" and stage == "OPEN_NOW" and feedback_enabled and message_id:
                    outcome_service.register_open_now(
                        signal_id=signal_id,
                        elite_chat_id=int(chat_id),
                        open_message_id=int(message_id),
                        open_now_ts=int(event.get("created_ts") or now_ts),
                        expiry_minutes=int(event.get("expiry_minutes") or 0),
                        symbol=event.get("symbol"),
                        direction=event.get("direction"),
                        timeframe=event.get("timeframe"),
                        telemetry_trade_id=signal_id,
                        callback_route="ELITE",
                    )
                _record_summary_result(
                    summary,
                    result_event,
                    route=route_name,
                    publish_result="PUBLISHED",
                    destination_id=chat_id,
                    message_id=message_id,
                )
                continue

            transport_error = str(response)
        except Exception as exc:
            transport_error = str(exc)

        result_event = _result_event(
            event,
            route=route_name,
            destination_id=chat_id,
            publish_result="FAILED",
            route_state_before=route_state_before,
            route_state_after=route_state_before,
            counted=False,
            counter_before=counter_before,
            counter_after=counter_before,
            transport_ok=False,
            message_id=None,
            transport_error=transport_error,
            dedup_key=dedup_key,
            was_duplicate=False,
            dedup_action="fail",
            reason="publisher_failure",
        )
        _legacy_publish_adapter(
            route_name=route_name,
            destination_kind=destination_kind,
            tier=tier,
            event=event,
            publish_result="FAILED",
            route_state_before=route_state_before,
            route_state_after=route_state_before,
            limit=limit,
            counter_before=counter_before,
            counter_after=counter_before,
            counted=False,
            attempted=True,
            telegram_ok=False,
            message_id=None,
            transport_error=transport_error,
            reason="publisher_failure",
            dedup_key=dedup_key,
            was_duplicate=False,
            dedup_action="fail",
            chat_id=chat_id,
            thread_id=thread_id,
            feedback_enabled=feedback_enabled,
        )
        _record_summary_result(
            summary,
            result_event,
            route=route_name,
            publish_result="FAILED",
            destination_id=chat_id,
            message_id=None,
        )

    return summary
