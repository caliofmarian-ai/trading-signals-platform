from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any, Dict, Optional

from core import observability_logger
from core import storage


TELEMETRY_VERSION = "2.0.0"
OPEN_TRADES_REGISTRY_JSON = storage.root_path("observability", "open_trades_registry.json")


def _iso_utc(epoch_seconds: float) -> str:
    value = float(epoch_seconds)
    timespec = "seconds" if value.is_integer() else "microseconds"
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat(timespec=timespec).replace("+00:00", "Z")


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    return cleaned


def _require_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return int(value)


def _require_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _require_expiry_minutes(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("expiry_minutes must be an integer or fractional number")
    result = float(value)
    if not isfinite(result) or result <= 0:
        raise ValueError("expiry_minutes must be finite and positive")
    return result


def _load_registry() -> Dict[str, Any]:
    registry = storage.load_json(OPEN_TRADES_REGISTRY_JSON, default={"version": TELEMETRY_VERSION, "trades": {}})
    if not isinstance(registry, dict):
        return {"version": TELEMETRY_VERSION, "trades": {}}
    registry.setdefault("version", TELEMETRY_VERSION)
    trades = registry.get("trades")
    if not isinstance(trades, dict):
        registry["trades"] = {}
    return registry


def _save_registry(registry: Dict[str, Any]) -> None:
    storage.save_json_atomic(OPEN_TRADES_REGISTRY_JSON, registry)


def _extract_entry_price(event: Dict[str, Any]) -> float:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    entry_price = payload.get("price")
    return _require_number(entry_price, "payload.price")


def _build_trade_record(event: Dict[str, Any], now_ts: int) -> Dict[str, Any]:
    signal_id = _require_str(event.get("signal_id"), "signal_id")
    symbol = _require_str(event.get("symbol"), "symbol")
    timeframe = _require_str(event.get("timeframe"), "timeframe")
    direction = _require_str(event.get("direction"), "direction")
    stage = _require_str(event.get("stage"), "stage")
    if stage != "OPEN_NOW":
        raise ValueError("stage must be OPEN_NOW")

    expiry_minutes = _require_expiry_minutes(event.get("expiry_minutes"))

    open_ts = _require_int(event.get("created_ts"), "created_ts")
    candle_ts = _require_int(event.get("candle_ts"), "candle_ts")
    entry_price = _extract_entry_price(event)
    score_total = _require_number(event.get("score_total"), "score_total")

    tps_value = event.get("TPS")
    if tps_value is not None:
        tps_value = _require_number(tps_value, "TPS")

    expiry_duration_seconds = expiry_minutes * 60.0
    expiry_ts = open_ts + expiry_duration_seconds
    mid_expiry_ts = open_ts + (expiry_duration_seconds / 2.0)
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}

    return {
        "trade_id": signal_id,
        "signal_id": signal_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": direction,
        "stage": stage,
        "entry_price": entry_price,
        "open_ts": open_ts,
        "open_ts_utc": _iso_utc(open_ts),
        "expiry_minutes": expiry_minutes,
        "expiry_duration_seconds": expiry_duration_seconds,
        "expiry_ts": expiry_ts,
        "expiry_ts_utc": _iso_utc(expiry_ts),
        "mid_expiry_ts": mid_expiry_ts,
        "mid_expiry_ts_utc": _iso_utc(mid_expiry_ts),
        "candle_ts": candle_ts,
        "candle_ts_utc": _iso_utc(candle_ts),
        "score_total": score_total,
        "TPS": tps_value,
        "buffer_mode": _require_str(event.get("buffer_mode"), "buffer_mode"),
        "buffer_price": _require_number(event.get("buffer_price"), "buffer_price"),
        "telemetry_status": "OPEN",
        "result_at_expiry": None,
        "mid_expiry_price": None,
        "expiry_price": None,
        "post_1m_price": None,
        "post_3m_price": None,
        "post_5m_price": None,
        "would_win_at_plus_1m": None,
        "would_win_at_plus_3m": None,
        "would_win_at_plus_5m": None,
        "post_expiry_recovery": None,
        "decision_debug": payload,
        "telemetry_version": TELEMETRY_VERSION,
        "registered_ts": int(now_ts),
        "registered_ts_utc": _iso_utc(now_ts),
    }


def _immutable_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "signal_id": record.get("signal_id"),
        "symbol": record.get("symbol"),
        "timeframe": record.get("timeframe"),
        "direction": record.get("direction"),
        "entry_price": record.get("entry_price"),
        "open_ts": record.get("open_ts"),
        "expiry_minutes": record.get("expiry_minutes"),
        "expiry_duration_seconds": record.get("expiry_duration_seconds"),
        "expiry_ts": record.get("expiry_ts"),
        "candle_ts": record.get("candle_ts"),
    }


def _log_registration_event(record: Dict[str, Any], status: str) -> None:
    try:
        event = observability_logger.build_event(
            "decision",
            {
                "decision_kind": "OPEN_NOW_REGISTERED",
                "symbol": record["symbol"],
                "signal_id": record["signal_id"],
                "score_total": record["score_total"],
                "buffer_mode": record["buffer_mode"],
                "expiry_minutes": record["expiry_minutes"],
                "candle_ts": record["candle_ts"],
                "telemetry_register_status": status,
            },
            source={"module": "trade_temporal_telemetry", "function": "register_open_now_trade"},
            correlation={
                "signal_id": record["signal_id"],
                "symbol": record["symbol"],
                "timeframe": record["timeframe"],
                "stage": "OPEN_NOW",
                "candle_ts_epoch": record["candle_ts"],
            },
        )
        observability_logger.log_event(event)
    except Exception:
        pass


def get_open_trade(signal_id: str) -> Optional[Dict[str, Any]]:
    registry = _load_registry()
    trades = registry.get("trades") or {}
    trade = trades.get(str(signal_id))
    return dict(trade) if isinstance(trade, dict) else None


def register_open_now_trade(event: Dict[str, Any], now_ts: Optional[int] = None) -> Dict[str, Any]:
    now_ts = int(now_ts if now_ts is not None else event.get("created_ts") or 0)
    if now_ts <= 0:
        raise ValueError("now_ts must be a positive integer")

    record = _build_trade_record(event, now_ts)

    with storage.with_lock("trade_temporal_telemetry"):
        registry = _load_registry()
        trades = registry.setdefault("trades", {})
        existing = trades.get(record["trade_id"])

        if existing is not None:
            if not isinstance(existing, dict):
                raise ValueError(f"existing telemetry record for {record['trade_id']} is invalid")
            if _immutable_fields(existing) != _immutable_fields(record):
                raise ValueError(f"conflicting OPEN_NOW registration for {record['trade_id']}")
            _log_registration_event(existing, "already_registered")
            return {
                "status": "already_registered",
                "trade_id": record["trade_id"],
                "record": dict(existing),
            }

        trades[record["trade_id"]] = record
        _save_registry(registry)

    _log_registration_event(record, "registered")
    return {
        "status": "registered",
        "trade_id": record["trade_id"],
        "record": dict(record),
    }
