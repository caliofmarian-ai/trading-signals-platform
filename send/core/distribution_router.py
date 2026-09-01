# /opt/binarybot/core/distribution_router.py
# BinaryBot — Tier Distribution Router (Channels + Admin Signals_Live topic)

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from core import storage
from core import telegram_publisher
from core import observability_logger
from core import outcome_service
from state_store import state_store as runtime_state_store

# -----------------------------
# Paths / timezone
# -----------------------------

DIST_STATE_PATH = runtime_state_store.DIST_STATE_PATH
CHANNEL_CONFIG_PATHS = [
    storage.config_path("channel_config.json"),
    storage.config_path("channel-config.json"),
    "/opt/binarybot/config/channel_config.json",
    "/opt/binarybot/config/channel-config.json",
]

DEFAULT_RESET_TIME = "08:10"
DEFAULT_RESET_TZ = "Europe/London"

TIERS = ("FREE", "BASIC", "PRO", "ELITE")


# -----------------------------
# Defaults (can be overridden by env)
# -----------------------------

DEFAULT_LIMITS = {
    "FREE": 6,
    "BASIC": 20,
    "PRO": 50,
    "ELITE": None,  # unlimited
}


def _safe_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _parse_limit(value: Any, default: Optional[int]) -> Optional[int]:
    if value is None or value == "":
        return default
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in ("UNLIMITED", "NONE", "INF"):
            return None
    try:
        return int(value)
    except Exception:
        return default


def _parse_reset_config(cfg_file: Dict[str, Any]) -> Dict[str, Any]:
    timezone_name = str(cfg_file.get("TZ") or DEFAULT_RESET_TZ)
    reset_time = str(cfg_file.get("RESET_TIME") or DEFAULT_RESET_TIME).strip()
    hour = 8
    minute = 10

    try:
        hh, mm = reset_time.split(":", 1)
        hour = int(hh)
        minute = int(mm)
    except Exception:
        hour = 8
        minute = 10

    return {
        "timezone": timezone_name,
        "hour": hour,
        "minute": minute,
    }


def _normalize_legacy_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(cfg, dict):
        return cfg

    normalized = dict(cfg)
    tiers_cfg = normalized.get("tiers", {}) or {}

    if "channels" not in normalized:
        normalized["channels"] = {t: (tiers_cfg.get(t, {}) or {}).get("channel_id") for t in TIERS}
    if "limits" not in normalized:
        normalized["limits"] = {t: (tiers_cfg.get(t, {}) or {}).get("daily_limit") for t in TIERS}

    admin = normalized.get("admin", {}) or {}
    if isinstance(admin, dict) and "signals_live_topic_id" not in admin:
        topics = admin.get("topics", {}) or {}
        if isinstance(topics, dict):
            if "signals_live" in topics:
                admin["signals_live_topic_id"] = topics.get("signals_live")
            elif "signals_live_topic_id" in topics:
                admin["signals_live_topic_id"] = topics.get("signals_live_topic_id")
        normalized["admin"] = admin

    return normalized


# -----------------------------
# State helpers
# -----------------------------

def _default_state() -> Dict[str, Any]:
    return runtime_state_store.default_dist_state()


def load_state() -> Dict[str, Any]:
    return runtime_state_store.load_dist_state(path=DIST_STATE_PATH)


def save_state(state: Dict[str, Any]) -> None:
    runtime_state_store.save_dist_state(state, path=DIST_STATE_PATH)


# -----------------------------
# Config helpers
# -----------------------------

def _load_channel_config_file() -> Dict[str, Any]:
    for p in CHANNEL_CONFIG_PATHS:
        try:
            cfg = storage.load_json(p, default=None)
            if isinstance(cfg, dict) and cfg:
                return cfg
        except Exception:
            continue
    return {}


def load_config() -> Dict[str, Any]:
    """
    Returns:
      {
        "channels": { "FREE": int|None, "BASIC":..., "PRO":..., "ELITE":... },
        "admin": { "group_id": int|None, "signals_live_topic_id": int|None },
        "limits": { "FREE": int, "BASIC": int, "PRO": int, "ELITE": None },
      }
    """
    cfg_file = _normalize_legacy_config(_load_channel_config_file())

    def _env_int(name: str) -> Optional[int]:
        return _safe_int(os.getenv(name))

    def _prefer_env(env_name: str, file_value: Any) -> Optional[int]:
        env_value = _env_int(env_name)
        if env_value is not None:
            return env_value
        return _safe_int(file_value)

    channels = {
        "FREE": _prefer_env("FREE_CHANNEL_ID", cfg_file.get("FREE_CHANNEL_ID") or (cfg_file.get("channels", {}) or {}).get("FREE")),
        "BASIC": _prefer_env("BASIC_CHANNEL_ID", cfg_file.get("BASIC_CHANNEL_ID") or (cfg_file.get("channels", {}) or {}).get("BASIC")),
        "PRO": _prefer_env("PRO_CHANNEL_ID", cfg_file.get("PRO_CHANNEL_ID") or (cfg_file.get("channels", {}) or {}).get("PRO")),
        "ELITE": _prefer_env("ELITE_CHANNEL_ID", cfg_file.get("ELITE_CHANNEL_ID") or (cfg_file.get("channels", {}) or {}).get("ELITE")),
    }

    admin_cfg = cfg_file.get("admin", {}) if isinstance(cfg_file.get("admin"), dict) else {}
    admin = {
        "group_id": (
            _env_int("ADMIN_SUPERGROUP_ID")
            or _env_int("ADMIN_GROUP_ID")
            or _safe_int(cfg_file.get("ADMIN_GROUP_ID"))
            or _safe_int(admin_cfg.get("group_id"))
        ),
        "signals_live_topic_id": _env_int("SIGNALS_LIVE_TOPIC_ID")
        or _safe_int(cfg_file.get("SIGNALS_LIVE_TOPIC_ID"))
        or _safe_int(admin_cfg.get("signals_live_topic_id")),
    }

    limits = {
        "FREE": _parse_limit(os.getenv("FREE_LIMIT"), _parse_limit(cfg_file.get("FREE_LIMIT") or (cfg_file.get("limits", {}) or {}).get("FREE"), DEFAULT_LIMITS["FREE"])),
        "BASIC": _parse_limit(os.getenv("BASIC_LIMIT"), _parse_limit(cfg_file.get("BASIC_LIMIT") or (cfg_file.get("limits", {}) or {}).get("BASIC"), DEFAULT_LIMITS["BASIC"])),
        "PRO": _parse_limit(os.getenv("PRO_LIMIT"), _parse_limit(cfg_file.get("PRO_LIMIT") or (cfg_file.get("limits", {}) or {}).get("PRO"), DEFAULT_LIMITS["PRO"])),
        "ELITE": _parse_limit(os.getenv("ELITE_LIMIT"), _parse_limit(cfg_file.get("ELITE_LIMIT") or (cfg_file.get("limits", {}) or {}).get("ELITE"), DEFAULT_LIMITS["ELITE"])),
    }

    return {
        "channels": channels,
        "admin": admin,
        "limits": limits,
        "reset": _parse_reset_config(cfg_file),
    }


# -----------------------------
# Reset logic
# -----------------------------

def maybe_daily_reset(state: Dict[str, Any], now_ts: int, reset_cfg: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], bool]:
    reset_cfg = reset_cfg or {"timezone": DEFAULT_RESET_TZ, "hour": 8, "minute": 10}
    try:
        reset_tz = ZoneInfo(str(reset_cfg.get("timezone") or DEFAULT_RESET_TZ))
    except Exception:
        reset_tz = ZoneInfo(DEFAULT_RESET_TZ)
    reset_hour = int(reset_cfg.get("hour", 8))
    reset_minute = int(reset_cfg.get("minute", 10))

    now_ldn = datetime.fromtimestamp(now_ts, tz=reset_tz)
    today_str = now_ldn.date().isoformat()

    # Only after 08:10 London
    if (now_ldn.hour, now_ldn.minute) < (reset_hour, reset_minute):
        return state, False

    if state.get("last_reset_london_date") == today_str:
        return state, False

    before = {
        "tier_state": dict(state.get("tier_state", {})),
        "open_signals_today": dict(state.get("open_signals_today", {})),
        "last_reset_london_date": state.get("last_reset_london_date"),
    }

    # reset counters and states (ELITE stays ACTIVE)
    state["last_reset_london_date"] = today_str
    state["open_signals_today"] = {t: 0 for t in TIERS}
    state["tier_state"] = {t: "ACTIVE" for t in TIERS}

    save_state(state)

    observability_logger.log_event(observability_logger.build_event(
        event_type="tier_reset",
        data={
            "reset_time_london": f"{reset_hour:02d}:{reset_minute:02d} {reset_tz.key}",
            "effective_date_london": today_str,
            "before": before,
            "after": {
                "tier_state": dict(state["tier_state"]),
                "open_signals_today": dict(state["open_signals_today"]),
                "last_reset_london_date": state["last_reset_london_date"],
            },
        },
        source={"module": "distribution_router", "function": "maybe_daily_reset"}
    ))

    return state, True


def reset_daily_counters() -> None:
    """
    Kept for backwards compatibility with older scheduler_loop().
    Correct reset is handled by maybe_daily_reset() inside route().
    """
    st = load_state()
    now_ts = int(time.time())
    cfg = load_config()
    maybe_daily_reset(st, now_ts, cfg.get("reset"))


# -----------------------------
# Dedup
# -----------------------------

def tier_dedup_key(tier: str, signal_id: str, stage: str) -> str:
    return f"{tier}|{signal_id}|{stage}"


def tier_dedup_check(state: Dict[str, Any], tier: str, signal_id: str, stage: str) -> bool:
    key = tier_dedup_key(tier, signal_id, stage)
    return bool(state.get("dedup", {}).get(key, False))


def tier_dedup_mark(state: Dict[str, Any], tier: str, signal_id: str, stage: str) -> None:
    key = tier_dedup_key(tier, signal_id, stage)
    state.setdefault("dedup", {})[key] = True


# -----------------------------
# Rendering + feedback buttons
# -----------------------------

def render_signal_text(event: Dict[str, Any], tier_label: str) -> str:
    stage = event.get("stage")
    symbol = event.get("symbol")
    direction = event.get("direction")
    tf = event.get("timeframe")
    score = event.get("score_total")
    buffer_mode = event.get("buffer_mode")
    expiry = event.get("expiry_minutes")

    # Minimal, deterministic text (formatting can be upgraded later per TELEGRAM_UX.md)
    lines = []
    lines.append(f"📡 {stage} — {symbol} ({tf})")
    lines.append(f"➡️ {direction} | Score: {score:.1f} | Buffer: {buffer_mode} | Exp: {expiry}m")
    if tier_label:
        lines.append(f"Tier: {tier_label}")
    lines.append(f"ID: {event.get('signal_id')}")
    return "\n".join(lines)


def build_feedback_markup(signal_id: str) -> Dict[str, Any]:
    # callback format expected by runtime/telegram_updates.py:
    # "VOTE_|{signal_id}|WIN" etc.
    return {
        "inline_keyboard": [
            [
                {"text": "✅ WIN", "callback_data": f"VOTE_|{signal_id}|WIN"},
                {"text": "❌ LOSE", "callback_data": f"VOTE_|{signal_id}|LOSE"},
                {"text": "⚪ MISSED", "callback_data": f"VOTE_|{signal_id}|MISSED"},
            ]
        ]
    }


# -----------------------------
# Publishing core
# -----------------------------

def _log_tier_publish(
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
    observability_logger.log_event(observability_logger.build_event(
        event_type="tier_publish",
        data={
            "publish_result": publish_result,
            "route_state_before": route_state_before,
            "route_state_after": route_state_after,
            "limit": limit,
            "counter_before": counter_before,
            "counter_after": counter_after,
            "counted": counted,
            "attempted": attempted,
            "destination_kind": destination_kind,
            "feedback_enabled": feedback_enabled,
            "transport": {
                "ok": telegram_ok,
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
        source={"module": "distribution_router", "function": "_log_tier_publish"},
        correlation={
            "signal_id": str(event.get("signal_id") or ""),
            "symbol": event.get("symbol"),
            "timeframe": event.get("timeframe"),
            "stage": event.get("stage"),
            "route": route_name,
            "tier": tier,
            "destination_id": chat_id,
            "thread_id": thread_id,
            "message_id": message_id,
            "candle_ts_epoch": event.get("candle_ts"),
        },
    ))


def _try_register_open_for_outcomes(
    signal_id: str,
    chat_id: int,
    message_id: int,
    open_now_ts: int,
    expiry_minutes: int,
    *,
    symbol: Optional[str] = None,
    direction: Optional[str] = None,
    timeframe: Optional[str] = None,
    callback_route: str = "ELITE",
) -> None:
    """
    Registers mapping once (do not overwrite).
    This enables vote validation in outcome_service even if buttons are clicked from
    another destination (ELITE/admin topic).
    """
    try:
        outcome_service.register_open_now(
            signal_id=signal_id,
            elite_chat_id=chat_id,
            open_message_id=message_id,
            open_now_ts=open_now_ts,
            expiry_minutes=expiry_minutes,
            symbol=symbol,
            direction=direction,
            timeframe=timeframe,
            telemetry_trade_id=signal_id,
            callback_route=callback_route,
        )
    except Exception:
        # outcome registration should never break distribution
        pass


def route(event: Dict[str, Any], now_ts: Optional[int] = None) -> None:
    """
    Rules implemented:
    - Signals go to channels: FREE/BASIC/PRO/ELITE.
    - Daily limits apply ONLY to OPEN_NOW and ONLY for FREE/BASIC/PRO.
    - When tier becomes SILENT it receives NOTHING (PRE/CONFIRM/OPEN_NOW).
    - ELITE is unlimited.
    - Additionally: all signals that go to ELITE also go to ADMIN supergroup topic SIGNALS_LIVE.
      (No limit; treated like ELITE.)
    - Feedback buttons (WIN/LOSE/MISSED) only on OPEN_NOW in:
        - ELITE channel
        - ADMIN SIGNALS_LIVE topic
    """
    if os.getenv("MARKET_DATA_PROVIDER", "TWELVE_DATA").strip().upper() == "FINNHUB":
        observability_logger.log_warning(
            warn_type="FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED",
            message=(
                "Finnhub personal-use market data cannot publish signals to Telegram channels"
            ),
            context={
                "signal_id": event.get("signal_id"),
                "stage": event.get("stage"),
                "provider": "FINNHUB",
            },
            source={"module": "distribution_router", "function": "route"},
        )
        return

    now_ts = int(now_ts or time.time())
    cfg = load_config()
    state = load_state()

    # Daily reset (DST-safe, London time)
    state, _ = maybe_daily_reset(state, now_ts, cfg.get("reset"))

    stage = str(event.get("stage") or "")
    signal_id = str(event.get("signal_id") or "")

    if not stage or not signal_id:
        observability_logger.log_warning(
            warn_type="distribution_invalid_event",
            message="Distribution router rejected signal event missing stage or signal_id",
            context={
                "missing": {"stage": stage, "signal_id": signal_id},
                "event_type": event.get("event_type"),
            },
            source={"module": "distribution_router", "function": "route"},
        )
        return

    # Build destinations:
    # 1) Tier channels
    # 2) Admin Signals_Live topic (mirror of ELITE)
    channels = cfg["channels"]
    limits = cfg["limits"]
    admin_group_id = cfg["admin"].get("group_id")
    admin_topic_id = cfg["admin"].get("signals_live_topic_id")

    destinations = []  # list of dict: {name, chat_id, thread_id, is_tier, tier_name, applies_limits, feedback_enabled}
    for tier in TIERS:
        chat_id = channels.get(tier)
        destinations.append({
            "name": tier,
            "chat_id": chat_id,
            "thread_id": None,
            "is_tier": True,
            "tier_name": tier,
            "applies_limits": tier in ("FREE", "BASIC", "PRO"),
            "feedback_enabled": (tier == "ELITE"),
        })

    # Admin mirror (works like ELITE)
    if admin_group_id and admin_topic_id:
        destinations.append({
            "name": "ADMIN_SIGNALS_LIVE",
            "chat_id": int(admin_group_id),
            "thread_id": int(admin_topic_id),
            "is_tier": False,
            "tier_name": "ELITE",  # treat as elite-like for semantics
            "applies_limits": False,
            "feedback_enabled": True,
        })

    # Publish to each destination
    for dest in destinations:
        chat_id = dest["chat_id"]
        thread_id = dest["thread_id"]
        tier = dest["tier_name"]
        route_name = str(dest["name"])
        destination_kind = "tier_channel" if dest["is_tier"] else "admin_topic"
        feedback_available = bool(dest["feedback_enabled"])

        # Missing destination => DISABLED
        if not chat_id:
            # Log as disabled tier publish (for real tiers only)
            if dest["is_tier"]:
                _log_tier_publish(
                    route_name=route_name,
                    destination_kind=destination_kind,
                    tier=tier,
                    event=event,
                    publish_result="SKIPPED_DISABLED",
                    route_state_before=state["tier_state"].get(tier, "DISABLED"),
                    route_state_after=state["tier_state"].get(tier, "DISABLED"),
                    limit=limits.get(tier),
                    counter_before=state["open_signals_today"].get(tier, 0),
                    counter_after=state["open_signals_today"].get(tier, 0),
                    counted=False,
                    attempted=False,
                    telegram_ok=False,
                    message_id=None,
                    transport_error=None,
                    reason="missing_channel_id",
                    dedup_key=tier_dedup_key(tier, signal_id, stage),
                    was_duplicate=False,
                    dedup_action="skip_disabled",
                    chat_id=None,
                    thread_id=None,
                    feedback_enabled=feedback_available,
                )
            continue

        # Tier state checks (ONLY for actual tier channels)
        tier_state_before = state["tier_state"].get(tier, "ACTIVE")

        if dest["is_tier"]:
            # If tier is SILENT -> block ALL stages
            if tier_state_before == "SILENT":
                _log_tier_publish(
                    route_name=route_name,
                    destination_kind=destination_kind,
                    tier=tier,
                    event=event,
                    publish_result="SKIPPED_SILENT",
                    route_state_before=tier_state_before,
                    route_state_after=tier_state_before,
                    limit=limits.get(tier),
                    counter_before=state["open_signals_today"].get(tier, 0),
                    counter_after=state["open_signals_today"].get(tier, 0),
                    counted=False,
                    attempted=False,
                    telegram_ok=False,
                    message_id=None,
                    transport_error=None,
                    reason="route_silent",
                    dedup_key=tier_dedup_key(tier, signal_id, stage),
                    was_duplicate=False,
                    dedup_action="skip_silent",
                    chat_id=int(chat_id),
                    thread_id=thread_id,
                    feedback_enabled=feedback_available,
                )
                continue

            # If OPEN_NOW and limit reached -> block (and stay SILENT)
            if stage == "OPEN_NOW" and dest["applies_limits"]:
                lim = limits.get(tier)
                if isinstance(lim, int):
                    counter = int(state["open_signals_today"].get(tier, 0))
                    if counter >= lim:
                        state["tier_state"][tier] = "SILENT"
                        save_state(state)

                        _log_tier_publish(
                            route_name=route_name,
                            destination_kind=destination_kind,
                            tier=tier,
                            event=event,
                            publish_result="SKIPPED_LIMIT",
                            route_state_before=tier_state_before,
                            route_state_after="SILENT",
                            limit=lim,
                            counter_before=counter,
                            counter_after=counter,
                            counted=False,
                            attempted=False,
                            telegram_ok=False,
                            message_id=None,
                            transport_error=None,
                            reason="limit_reached",
                            dedup_key=tier_dedup_key(tier, signal_id, stage),
                            was_duplicate=False,
                            dedup_action="skip_limit",
                            chat_id=int(chat_id),
                            thread_id=thread_id,
                            feedback_enabled=feedback_available,
                        )
                        continue

        # Tier dedup (for real tiers) + mirror dedup (use pseudo-tier key)
        dedup_tier_key = tier if dest["is_tier"] else "ADMIN_SIGNALS_LIVE"
        dedup_key = tier_dedup_key(dedup_tier_key, signal_id, stage)
        was_dup = tier_dedup_check(state, dedup_tier_key, signal_id, stage)
        if was_dup:
            _log_tier_publish(
                route_name=route_name,
                destination_kind=destination_kind,
                tier=tier,
                event=event,
                publish_result="DUPLICATE_SUPPRESSED",
                route_state_before=tier_state_before,
                route_state_after=tier_state_before,
                limit=limits.get(tier),
                counter_before=state["open_signals_today"].get(tier, 0),
                counter_after=state["open_signals_today"].get(tier, 0),
                counted=False,
                attempted=False,
                telegram_ok=False,
                message_id=None,
                transport_error=None,
                reason="duplicate_suppressed",
                dedup_key=dedup_key,
                was_duplicate=True,
                dedup_action="suppress",
                chat_id=int(chat_id),
                thread_id=thread_id,
                feedback_enabled=feedback_available,
            )
            continue

        # Build message + optional markup
        text = render_signal_text(event, tier_label=(tier if dest["is_tier"] else "ADMIN"))
        reply_markup = None

        # Feedback buttons only on OPEN_NOW and only in ELITE + admin signals_live mirror
        feedback_enabled = feedback_available and (stage == "OPEN_NOW")
        if feedback_enabled:
            reply_markup = build_feedback_markup(signal_id)

        # Publish
        counter_before = int(state["open_signals_today"].get(tier, 0))
        lim = limits.get(tier)
        tier_state_after = tier_state_before
        counted = False

        try:
            resp = telegram_publisher.send_message(
                chat_id=int(chat_id),
                text=text,
                reply_markup=reply_markup,
                thread_id=thread_id
            )

            ok = bool(resp.get("ok"))
            msg_id = None
            if ok:
                msg_id = resp.get("result", {}).get("message_id")

            # mark dedup on attempt (only if telegram ok)
            if ok:
                tier_dedup_mark(state, dedup_tier_key, signal_id, stage)

                # Count only OPEN_NOW published successfully AND tier is FREE/BASIC/PRO
                if dest["is_tier"] and stage == "OPEN_NOW" and dest["applies_limits"]:
                    state["open_signals_today"][tier] = counter_before + 1
                    counted = True

                    # if reached limit -> SILENT
                    if isinstance(lim, int) and state["open_signals_today"][tier] >= lim:
                        state["tier_state"][tier] = "SILENT"
                        tier_state_after = "SILENT"

                # outcomes register (first successful OPEN_NOW with feedback buttons)
                if stage == "OPEN_NOW" and feedback_enabled and msg_id:
                    _try_register_open_for_outcomes(
                        signal_id=signal_id,
                        chat_id=int(chat_id),
                        message_id=int(msg_id),
                        open_now_ts=int(event.get("created_ts") or now_ts),
                        expiry_minutes=int(event.get("expiry_minutes") or 0),
                        symbol=event.get("symbol"),
                        direction=event.get("direction"),
                        timeframe=event.get("timeframe"),
                        callback_route=route_name,
                    )

                save_state(state)

                _log_tier_publish(
                    route_name=route_name,
                    destination_kind=destination_kind,
                    tier=tier,
                    event=event,
                    publish_result="PUBLISHED",
                    route_state_before=tier_state_before,
                    route_state_after=tier_state_after,
                    limit=lim,
                    counter_before=counter_before,
                    counter_after=int(state["open_signals_today"].get(tier, 0)),
                    counted=counted,
                    attempted=True,
                    telegram_ok=True,
                    message_id=msg_id,
                    transport_error=None,
                    reason=None,
                    dedup_key=dedup_key,
                    was_duplicate=False,
                    dedup_action="publish",
                    chat_id=int(chat_id),
                    thread_id=thread_id,
                    feedback_enabled=feedback_enabled,
                )
            else:
                # failed publish
                _log_tier_publish(
                    route_name=route_name,
                    destination_kind=destination_kind,
                    tier=tier,
                    event=event,
                    publish_result="FAILED",
                    route_state_before=tier_state_before,
                    route_state_after=tier_state_before,
                    limit=lim,
                    counter_before=counter_before,
                    counter_after=counter_before,
                    counted=False,
                    attempted=True,
                    telegram_ok=False,
                    message_id=None,
                    transport_error=str(resp),
                    reason="publisher_returned_not_ok",
                    dedup_key=dedup_key,
                    was_duplicate=False,
                    dedup_action="fail",
                    chat_id=int(chat_id),
                    thread_id=thread_id,
                    feedback_enabled=feedback_enabled,
                )

        except Exception as e:
            _log_tier_publish(
                route_name=route_name,
                destination_kind=destination_kind,
                tier=tier,
                event=event,
                publish_result="FAILED",
                route_state_before=tier_state_before,
                route_state_after=tier_state_before,
                limit=lim,
                counter_before=counter_before,
                counter_after=counter_before,
                counted=False,
                attempted=True,
                telegram_ok=False,
                message_id=None,
                transport_error=str(e),
                reason="publisher_exception",
                dedup_key=dedup_key,
                was_duplicate=False,
                dedup_action="exception",
                chat_id=int(chat_id),
                thread_id=thread_id,
                feedback_enabled=feedback_enabled,
            )
