from __future__ import annotations

import json
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Dict, List, Mapping, Optional, Tuple

from core import observability_logger
from core import storage


TELEMETRY_VERSION = "3.0.0"
TELEMETRY_SPECIFICATION = "TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0"
LABEL_DERIVATION_VERSION = "market-expiry-direction-v1"
CHECKPOINT_SELECTION_POLICY = "FIRST_REAL_OBSERVATION_AT_OR_AFTER_TARGET"
OPEN_TRADES_REGISTRY_JSON = storage.root_path("observability", "open_trades_registry.json")
FINALIZED_TELEMETRY_JSONL = storage.root_path("observability", "trade_temporal_telemetry.jsonl")

CHECKPOINT_KEYS: Tuple[str, ...] = (
    "mid_expiry",
    "expiry",
    "post_1m",
    "post_3m",
    "post_5m",
)
_POST_CHECKPOINTS = (
    ("post_1m", "would_win_at_plus_1m", "RECOVERED_AT_1M"),
    ("post_3m", "would_win_at_plus_3m", "RECOVERED_AT_3M"),
    ("post_5m", "would_win_at_plus_5m", "RECOVERED_AT_5M"),
)


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


def _optional_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


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


def _require_positive_number(value: Any, field_name: str) -> float:
    result = _require_number(value, field_name)
    if result <= 0:
        raise ValueError(f"{field_name} must be positive")
    return result


def _extract_entry_price(event: Mapping[str, Any]) -> tuple[float, str]:
    if event.get("entry_price") is not None:
        return _require_positive_number(event.get("entry_price"), "entry_price"), "signal_event.entry_price"
    payload = event.get("payload") if isinstance(event.get("payload"), Mapping) else {}
    for key in ("price", "latest_price"):
        if payload.get(key) is not None:
            return _require_positive_number(payload.get(key), f"payload.{key}"), f"payload.{key}:migration"
    raise ValueError("entry_price is required from SignalEvent evidence")


def _extract_tps(event: Mapping[str, Any]) -> Optional[float]:
    if event.get("TPS") is not None:
        return _require_number(event.get("TPS"), "TPS")
    payload = event.get("payload") if isinstance(event.get("payload"), Mapping) else {}
    physics = payload.get("trade_physics") if isinstance(payload.get("trade_physics"), Mapping) else {}
    if physics.get("TPS") is None:
        return None
    return _require_number(physics.get("TPS"), "payload.trade_physics.TPS")


def _checkpoint_targets(open_ts: float, expiry_duration_seconds: float) -> Dict[str, float]:
    expiry_ts = open_ts + expiry_duration_seconds
    return {
        "mid_expiry": open_ts + (expiry_duration_seconds / 2.0),
        "expiry": expiry_ts,
        "post_1m": expiry_ts + 60.0,
        "post_3m": expiry_ts + 180.0,
        "post_5m": expiry_ts + 300.0,
    }


def _empty_checkpoint(target_ts: float) -> Dict[str, Any]:
    return {
        "state": "PENDING",
        "target_ts": float(target_ts),
        "target_ts_utc": _iso_utc(target_ts),
        "price": None,
        "observed_ts": None,
        "observed_ts_utc": None,
        "observation_lag_seconds": None,
        "provider": None,
        "directional_result": None,
        "gap_reason": None,
        "gap_detected_ts": None,
        "gap_detected_ts_utc": None,
    }


def _normalize_publication_evidence(value: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("publication_evidence must be a mapping")
    route_result_event_id = _require_str(
        value.get("route_result_event_id"), "publication_evidence.route_result_event_id"
    )
    visibility_event_id = _require_str(
        value.get("visibility_event_id"), "publication_evidence.visibility_event_id"
    )
    route = _require_str(value.get("route"), "publication_evidence.route")
    destination_id = value.get("destination_id")
    if isinstance(destination_id, bool) or not isinstance(destination_id, int):
        raise ValueError("publication_evidence.destination_id must be an integer")
    message_id = value.get("message_id")
    if message_id is not None and (
        isinstance(message_id, bool) or not isinstance(message_id, int)
    ):
        raise ValueError("publication_evidence.message_id must be an integer or null")
    return {
        "route_result_event_id": route_result_event_id,
        "visibility_event_id": visibility_event_id,
        "route": route,
        "destination_id": int(destination_id),
        "message_id": message_id,
    }


def _lineage_snapshot(event: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
    linkage = {
        "setup_correlation_id": _optional_text(payload.get("cycle_id")),
        "decision_id": _optional_text(event.get("decision_id") or payload.get("decision_id")),
        "decision_audit_id": _optional_text(event.get("decision_audit_id") or payload.get("decision_audit_id")),
        "execution_attempt_id": _optional_text(event.get("execution_attempt_id") or payload.get("execution_attempt_id")),
        "fsm_transition_id": _optional_text(event.get("fsm_transition_id") or payload.get("fsm_transition_id")),
    }
    missing = [key for key, value in linkage.items() if value is None]
    return {
        **linkage,
        "linkage_state": "COMPLETE" if not missing else "DEGRADED",
        "missing_linkage_fields": missing,
    }


def _build_trade_record(
    event: Mapping[str, Any],
    *,
    now_ts: int,
    market_provider: str,
    publication_evidence: Mapping[str, Any],
) -> Dict[str, Any]:
    signal_id = _require_str(event.get("signal_id"), "signal_id")
    symbol = _require_str(event.get("symbol"), "symbol")
    timeframe = _require_str(event.get("timeframe"), "timeframe")
    direction = _require_str(event.get("direction"), "direction").upper()
    if direction not in {"BUY", "SELL"}:
        raise ValueError("direction must be BUY or SELL")
    stage = _require_str(event.get("stage"), "stage").upper()
    if stage != "OPEN_NOW":
        raise ValueError("stage must be OPEN_NOW")
    if event.get("execution_time_available") is not True:
        raise ValueError("OPEN_NOW telemetry requires governed Execution Time")

    expiry_minutes = _require_positive_number(
        event.get("open_now_expiry_minutes"), "open_now_expiry_minutes"
    )
    compatibility_expiry = _require_positive_number(event.get("expiry_minutes"), "expiry_minutes")
    if compatibility_expiry != expiry_minutes:
        raise ValueError("telemetry expiry must equal governed OPEN_NOW Execution Time")

    open_ts = _require_int(event.get("created_ts"), "created_ts")
    candle_ts = _require_int(event.get("candle_ts"), "candle_ts")
    entry_price, entry_price_source = _extract_entry_price(event)
    score_total = _require_number(event.get("score_total"), "score_total")
    provider = _require_str(market_provider, "market_provider").upper()
    publication = _normalize_publication_evidence(publication_evidence)
    payload = dict(event.get("payload")) if isinstance(event.get("payload"), Mapping) else {}
    lineage = _lineage_snapshot(event, payload)

    expiry_duration_seconds = expiry_minutes * 60.0
    targets = _checkpoint_targets(float(open_ts), expiry_duration_seconds)
    checkpoints = {key: _empty_checkpoint(targets[key]) for key in CHECKPOINT_KEYS}

    return {
        "trade_id": signal_id,
        "telemetry_record_id": f"market-truth:{signal_id}",
        "signal_id": signal_id,
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": direction,
        "stage": stage,
        "market_provider": provider,
        "entry_price": entry_price,
        "entry_price_source": entry_price_source,
        "open_ts": open_ts,
        "open_ts_utc": _iso_utc(open_ts),
        "expiry_minutes": expiry_minutes,
        "expiry_duration_seconds": expiry_duration_seconds,
        "expiry_ts": targets["expiry"],
        "expiry_ts_utc": _iso_utc(targets["expiry"]),
        "mid_expiry_ts": targets["mid_expiry"],
        "mid_expiry_ts_utc": _iso_utc(targets["mid_expiry"]),
        "post_1m_ts": targets["post_1m"],
        "post_3m_ts": targets["post_3m"],
        "post_5m_ts": targets["post_5m"],
        "candle_ts": candle_ts,
        "candle_ts_utc": _iso_utc(candle_ts),
        "feature_cutoff_ts": candle_ts,
        "feature_cutoff_ts_utc": _iso_utc(candle_ts),
        "score_total": score_total,
        "TPS": _extract_tps(event),
        "buffer_mode": _require_str(event.get("buffer_mode"), "buffer_mode"),
        "buffer_price": _require_number(event.get("buffer_price"), "buffer_price"),
        "execution_calibration_source": _require_str(
            event.get("execution_calibration_source"), "execution_calibration_source"
        ),
        "strategy_version": _optional_text(payload.get("strategy_version")),
        "canonical_specification": _optional_text(payload.get("canonical_specification")),
        **lineage,
        "telemetry_status": "OPEN",
        "truth_domain": "MARKET_TRUTH",
        "result_at_expiry": None,
        "mid_expiry_price": None,
        "mid_direction_correct": None,
        "mid_directional_delta": None,
        "expiry_price": None,
        "post_1m_price": None,
        "post_3m_price": None,
        "post_5m_price": None,
        "would_win_at_plus_1m": None,
        "would_win_at_plus_3m": None,
        "would_win_at_plus_5m": None,
        "post_expiry_recovery": None,
        "label_observation_ts": None,
        "label_observation_ts_utc": None,
        "label_derivation_version": LABEL_DERIVATION_VERSION,
        "checkpoint_selection_policy": CHECKPOINT_SELECTION_POLICY,
        "checkpoints": checkpoints,
        "publication_evidence": [publication],
        "pre_trade_snapshot": payload,
        "telemetry_version": TELEMETRY_VERSION,
        "telemetry_specification": TELEMETRY_SPECIFICATION,
        "registered_ts": int(now_ts),
        "registered_ts_utc": _iso_utc(now_ts),
        "finalized_ts": None,
        "finalized_ts_utc": None,
        "finalized_record_written": False,
    }


def _immutable_fields(record: Mapping[str, Any]) -> Dict[str, Any]:
    keys = (
        "signal_id",
        "symbol",
        "timeframe",
        "direction",
        "market_provider",
        "entry_price",
        "open_ts",
        "expiry_minutes",
        "expiry_duration_seconds",
        "expiry_ts",
        "candle_ts",
        "score_total",
        "TPS",
        "buffer_mode",
        "buffer_price",
        "execution_calibration_source",
        "strategy_version",
        "canonical_specification",
        "pre_trade_snapshot",
    )
    return {key: record.get(key) for key in keys}


def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record.get("checkpoints"), dict):
        try:
            open_ts = float(record["open_ts"])
            duration = float(record["expiry_duration_seconds"])
            targets = _checkpoint_targets(open_ts, duration)
        except (KeyError, TypeError, ValueError):
            return record
        legacy_price_fields = {
            "mid_expiry": "mid_expiry_price",
            "expiry": "expiry_price",
            "post_1m": "post_1m_price",
            "post_3m": "post_3m_price",
            "post_5m": "post_5m_price",
        }
        checkpoints: Dict[str, Any] = {}
        for key in CHECKPOINT_KEYS:
            checkpoint = _empty_checkpoint(targets[key])
            legacy_value = record.get(legacy_price_fields[key])
            if legacy_value is not None:
                checkpoint["state"] = "LEGACY_UNVERIFIED"
                checkpoint["price"] = legacy_value
                checkpoint["gap_reason"] = "LEGACY_PRICE_WITHOUT_RAW_OBSERVATION_TIMESTAMP"
            checkpoints[key] = checkpoint
        record["checkpoints"] = checkpoints
    record.setdefault("truth_domain", "MARKET_TRUTH")
    record.setdefault("label_derivation_version", LABEL_DERIVATION_VERSION)
    record.setdefault("checkpoint_selection_policy", CHECKPOINT_SELECTION_POLICY)
    record.setdefault("telemetry_specification", TELEMETRY_SPECIFICATION)
    record.setdefault("publication_evidence", [])
    record.setdefault("finalized_record_written", False)
    return record


def _load_registry() -> Dict[str, Any]:
    registry = storage.load_json(
        OPEN_TRADES_REGISTRY_JSON,
        default={"version": TELEMETRY_VERSION, "trades": {}},
    )
    if not isinstance(registry, dict):
        registry = {"version": TELEMETRY_VERSION, "trades": {}}
    registry["version"] = TELEMETRY_VERSION
    trades = registry.get("trades")
    if not isinstance(trades, dict):
        trades = {}
        registry["trades"] = trades
    for key, value in list(trades.items()):
        if isinstance(value, dict):
            trades[key] = _normalize_record(value)
    return registry


def _save_registry(registry: Dict[str, Any]) -> None:
    storage.save_json_atomic(OPEN_TRADES_REGISTRY_JSON, registry)


def _market_result(direction: str, entry_price: float, observed_price: float) -> str:
    if observed_price == entry_price:
        return "DRAW"
    if direction == "BUY":
        return "WIN" if observed_price > entry_price else "LOSS"
    if direction == "SELL":
        return "WIN" if observed_price < entry_price else "LOSS"
    raise ValueError(f"unsupported direction: {direction}")


def _all_checkpoints_resolved(record: Mapping[str, Any]) -> bool:
    checkpoints = record.get("checkpoints")
    if not isinstance(checkpoints, Mapping):
        return False
    return all(
        isinstance(checkpoints.get(key), Mapping)
        and checkpoints[key].get("state") != "PENDING"
        for key in CHECKPOINT_KEYS
    )


def _has_evidence_gap(record: Mapping[str, Any]) -> bool:
    checkpoints = record.get("checkpoints")
    if not isinstance(checkpoints, Mapping):
        return True
    return any(
        not isinstance(checkpoints.get(key), Mapping)
        or checkpoints[key].get("state") != "OBSERVED"
        for key in CHECKPOINT_KEYS
    )


def _derive_recovery(record: Dict[str, Any]) -> None:
    expiry_result = record.get("result_at_expiry")
    checkpoints = record.get("checkpoints") if isinstance(record.get("checkpoints"), dict) else {}
    if expiry_result == "WIN":
        observed = [
            checkpoints[key].get("directional_result")
            for key, _flag, _name in _POST_CHECKPOINTS
            if isinstance(checkpoints.get(key), dict)
            and checkpoints[key].get("state") == "OBSERVED"
        ]
        if observed and any(result != "WIN" for result in observed):
            record["post_expiry_recovery"] = "EARLY_CORRECT_THEN_REVERSED"
        return
    if expiry_result not in {"LOSS", "DRAW"}:
        return
    for key, flag_field, recovery_name in _POST_CHECKPOINTS:
        checkpoint = checkpoints.get(key)
        if isinstance(checkpoint, dict) and checkpoint.get("state") == "OBSERVED":
            if checkpoint.get("directional_result") == "WIN":
                record[flag_field] = True
                record["post_expiry_recovery"] = recovery_name
                return
    if all(
        isinstance(checkpoints.get(key), dict)
        and checkpoints[key].get("state") == "OBSERVED"
        for key, _flag, _name in _POST_CHECKPOINTS
    ):
        record["post_expiry_recovery"] = "NO_RECOVERY"


def _finalized_record_exists(trade_id: str) -> bool:
    try:
        with open(FINALIZED_TELEMETRY_JSONL, "r", encoding="utf-8") as handle:
            for raw in handle:
                try:
                    row = json.loads(raw)
                except (ValueError, TypeError):
                    continue
                if isinstance(row, dict) and row.get("trade_id") == trade_id:
                    return True
    except FileNotFoundError:
        return False
    return False


def _append_finalized_once(record: Dict[str, Any]) -> bool:
    trade_id = _require_str(record.get("trade_id"), "trade_id")
    if _finalized_record_exists(trade_id):
        return False
    storage.append_jsonl(FINALIZED_TELEMETRY_JSONL, dict(record))
    return True


def _maybe_finalize(record: Dict[str, Any], now_ts: int) -> bool:
    if record.get("telemetry_status") in {"FINALIZED", "INCOMPLETE_MARKET_EVIDENCE"}:
        if not record.get("finalized_record_written"):
            _append_finalized_once(record)
            record["finalized_record_written"] = True
        return False
    if not _all_checkpoints_resolved(record):
        return False
    record["telemetry_status"] = (
        "INCOMPLETE_MARKET_EVIDENCE" if _has_evidence_gap(record) else "FINALIZED"
    )
    record["finalized_ts"] = int(now_ts)
    record["finalized_ts_utc"] = _iso_utc(now_ts)
    _derive_recovery(record)
    _append_finalized_once(record)
    record["finalized_record_written"] = True
    return True


def _warn_gap(record: Mapping[str, Any], checkpoint_key: str, reason: str) -> None:
    try:
        checkpoint = record.get("checkpoints", {}).get(checkpoint_key, {})
        observability_logger.log_warning(
            warn_type="TRADE_TEMPORAL_TELEMETRY_EVIDENCE_GAP",
            message="Objective market telemetry checkpoint is unavailable and remains unfilled",
            context={
                "signal_id": record.get("signal_id"),
                "symbol": record.get("symbol"),
                "checkpoint": checkpoint_key,
                "target_ts": checkpoint.get("target_ts"),
                "market_provider": record.get("market_provider"),
                "reason": reason,
            },
            source={"module": "trade_temporal_telemetry", "function": "_warn_gap"},
        )
    except Exception:
        pass


def get_open_trade(signal_id: str) -> Optional[Dict[str, Any]]:
    registry = _load_registry()
    trades = registry.get("trades") or {}
    trade = trades.get(str(signal_id))
    return dict(trade) if isinstance(trade, dict) else None


def pending_market_requests() -> List[Dict[str, str]]:
    registry = _load_registry()
    requests: List[Dict[str, str]] = []
    seen = set()
    for record in (registry.get("trades") or {}).values():
        if not isinstance(record, dict):
            continue
        if record.get("telemetry_status") in {"FINALIZED", "INCOMPLETE_MARKET_EVIDENCE"}:
            continue
        checkpoints = record.get("checkpoints")
        if not isinstance(checkpoints, dict) or not any(
            isinstance(checkpoints.get(key), dict) and checkpoints[key].get("state") == "PENDING"
            for key in CHECKPOINT_KEYS
        ):
            continue
        provider = record.get("market_provider")
        symbol = record.get("symbol")
        if not isinstance(provider, str) or not provider.strip() or not isinstance(symbol, str) or not symbol.strip():
            continue
        key = (provider.strip().upper(), symbol.strip().upper())
        if key in seen:
            continue
        seen.add(key)
        requests.append({"provider": key[0], "symbol": symbol.strip()})
    return requests


def register_open_now_trade(
    event: Mapping[str, Any],
    *,
    market_provider: str,
    publication_evidence: Mapping[str, Any],
    now_ts: Optional[int] = None,
) -> Dict[str, Any]:
    if not isinstance(event, Mapping):
        raise TypeError("event must be a mapping")
    resolved_now = int(now_ts if now_ts is not None else event.get("created_ts") or 0)
    if resolved_now <= 0:
        raise ValueError("now_ts must be a positive integer")

    record = _build_trade_record(
        event,
        now_ts=resolved_now,
        market_provider=market_provider,
        publication_evidence=publication_evidence,
    )
    publication = record["publication_evidence"][0]

    with storage.with_lock("trade_temporal_telemetry"):
        registry = _load_registry()
        trades = registry.setdefault("trades", {})
        existing = trades.get(record["trade_id"])
        if existing is not None:
            if not isinstance(existing, dict):
                raise ValueError(f"existing telemetry record for {record['trade_id']} is invalid")
            existing = _normalize_record(existing)
            if _immutable_fields(existing) != _immutable_fields(record):
                raise ValueError(f"conflicting OPEN_NOW registration for {record['trade_id']}")
            evidence = existing.setdefault("publication_evidence", [])
            if publication not in evidence:
                evidence.append(publication)
                trades[record["trade_id"]] = existing
                _save_registry(registry)
                status = "updated_publication_evidence"
            else:
                status = "already_registered"
            output = dict(existing)
        else:
            trades[record["trade_id"]] = record
            _save_registry(registry)
            status = "registered"
            output = dict(record)
    return {"status": status, "trade_id": record["trade_id"], "record": output}


def _observe_checkpoint(
    record: Dict[str, Any],
    key: str,
    *,
    price: float,
    observed_ts: float,
    provider: str,
) -> bool:
    checkpoints = record.get("checkpoints")
    if not isinstance(checkpoints, dict):
        return False
    checkpoint = checkpoints.get(key)
    if not isinstance(checkpoint, dict) or checkpoint.get("state") != "PENDING":
        return False
    target_ts = _require_positive_number(checkpoint.get("target_ts"), f"checkpoints.{key}.target_ts")
    if observed_ts < target_ts:
        return False

    directional_result = _market_result(record["direction"], float(record["entry_price"]), price)
    checkpoint.update({
        "state": "OBSERVED",
        "price": price,
        "observed_ts": observed_ts,
        "observed_ts_utc": _iso_utc(observed_ts),
        "observation_lag_seconds": observed_ts - target_ts,
        "provider": provider,
        "directional_result": directional_result,
        "gap_reason": None,
        "gap_detected_ts": None,
        "gap_detected_ts_utc": None,
    })

    if key == "mid_expiry":
        record["mid_expiry_price"] = price
        record["mid_direction_correct"] = directional_result == "WIN"
        record["mid_directional_delta"] = (
            price - float(record["entry_price"])
            if record["direction"] == "BUY"
            else float(record["entry_price"]) - price
        )
    elif key == "expiry":
        record["expiry_price"] = price
        record["result_at_expiry"] = directional_result
        record["label_observation_ts"] = observed_ts
        record["label_observation_ts_utc"] = _iso_utc(observed_ts)
    else:
        price_field = {
            "post_1m": "post_1m_price",
            "post_3m": "post_3m_price",
            "post_5m": "post_5m_price",
        }[key]
        flag_field = {
            "post_1m": "would_win_at_plus_1m",
            "post_3m": "would_win_at_plus_3m",
            "post_5m": "would_win_at_plus_5m",
        }[key]
        record[price_field] = price
        record[flag_field] = directional_result == "WIN"
    record["telemetry_status"] = "COLLECTING"
    _derive_recovery(record)
    return True


def observe_market_sample(sample: Mapping[str, Any], *, now_ts: Optional[int] = None) -> Dict[str, Any]:
    if not isinstance(sample, Mapping):
        raise TypeError("sample must be a mapping")
    provider = _require_str(sample.get("provider"), "sample.provider").upper()
    symbol = _require_str(sample.get("symbol"), "sample.symbol")
    price = _require_positive_number(sample.get("price"), "sample.price")
    observed_ts = _require_positive_number(sample.get("observed_ts"), "sample.observed_ts")
    resolved_now = int(now_ts if now_ts is not None else observed_ts)
    changed_records: List[Tuple[Dict[str, Any], bool]] = []

    with storage.with_lock("trade_temporal_telemetry"):
        registry = _load_registry()
        trades = registry.get("trades") or {}
        changed = False
        for trade_id, record in trades.items():
            if not isinstance(record, dict):
                continue
            if record.get("telemetry_status") in {"FINALIZED", "INCOMPLETE_MARKET_EVIDENCE"}:
                continue
            if str(record.get("market_provider") or "").upper() != provider:
                continue
            if str(record.get("symbol") or "").upper() != symbol.upper():
                continue
            observed_any = False
            for key in CHECKPOINT_KEYS:
                observed_any = _observe_checkpoint(
                    record,
                    key,
                    price=price,
                    observed_ts=observed_ts,
                    provider=provider,
                ) or observed_any
            if not observed_any:
                continue
            finalized = _maybe_finalize(record, resolved_now)
            trades[trade_id] = record
            changed_records.append((dict(record), finalized))
            changed = True
        if changed:
            _save_registry(registry)

    return {
        "provider": provider,
        "symbol": symbol,
        "observed_ts": observed_ts,
        "updated_trade_count": len(changed_records),
        "finalized_trade_count": sum(1 for _record, finalized in changed_records if finalized),
    }


def _mark_checkpoint_gap(
    record: Dict[str, Any], checkpoint_key: str, *, reason: str, now_ts: int
) -> bool:
    checkpoints = record.get("checkpoints")
    if not isinstance(checkpoints, dict):
        return False
    checkpoint = checkpoints.get(checkpoint_key)
    if not isinstance(checkpoint, dict) or checkpoint.get("state") != "PENDING":
        return False
    checkpoint.update({
        "state": "EVIDENCE_GAP",
        "price": None,
        "observed_ts": None,
        "observed_ts_utc": None,
        "observation_lag_seconds": None,
        "provider": None,
        "directional_result": None,
        "gap_reason": reason,
        "gap_detected_ts": int(now_ts),
        "gap_detected_ts_utc": _iso_utc(now_ts),
    })
    record["telemetry_status"] = "COLLECTING_WITH_GAPS"
    return True


def mark_due_provider_mismatch(active_provider: str, *, now_ts: int) -> Dict[str, Any]:
    provider = _require_str(active_provider, "active_provider").upper()
    resolved_now = _require_int(now_ts, "now_ts")
    gaps: List[Tuple[Dict[str, Any], List[str], bool]] = []

    with storage.with_lock("trade_temporal_telemetry"):
        registry = _load_registry()
        trades = registry.get("trades") or {}
        changed = False
        for trade_id, record in trades.items():
            if not isinstance(record, dict):
                continue
            if record.get("telemetry_status") in {"FINALIZED", "INCOMPLETE_MARKET_EVIDENCE"}:
                continue
            registered_provider = str(record.get("market_provider") or "").upper()
            if not registered_provider or registered_provider == provider:
                continue
            checkpoints = record.get("checkpoints")
            if not isinstance(checkpoints, dict):
                continue
            gap_keys: List[str] = []
            for key in CHECKPOINT_KEYS:
                checkpoint = checkpoints.get(key)
                if not isinstance(checkpoint, dict) or checkpoint.get("state") != "PENDING":
                    continue
                target_ts = checkpoint.get("target_ts")
                if isinstance(target_ts, bool) or not isinstance(target_ts, (int, float)):
                    continue
                if float(target_ts) > resolved_now:
                    continue
                if _mark_checkpoint_gap(
                    record,
                    key,
                    reason="ACTIVE_PROVIDER_CHANGED_BEFORE_CHECKPOINT",
                    now_ts=resolved_now,
                ):
                    gap_keys.append(key)
                    changed = True
            if gap_keys:
                finalized = _maybe_finalize(record, resolved_now)
                trades[trade_id] = record
                gaps.append((dict(record), gap_keys, finalized))
        if changed:
            _save_registry(registry)

    for record, gap_keys, _finalized in gaps:
        for key in gap_keys:
            _warn_gap(record, key, "ACTIVE_PROVIDER_CHANGED_BEFORE_CHECKPOINT")
    return {
        "affected_trade_count": len(gaps),
        "evidence_gap_count": sum(len(keys) for _record, keys, _finalized in gaps),
        "finalized_incomplete_count": sum(1 for _record, _keys, finalized in gaps if finalized),
    }


def recover_after_restart(now_ts: int) -> Dict[str, Any]:
    resolved_now = _require_int(now_ts, "now_ts")
    if resolved_now <= 0:
        raise ValueError("now_ts must be positive")
    gaps: List[Tuple[Dict[str, Any], List[str], bool]] = []

    with storage.with_lock("trade_temporal_telemetry"):
        registry = _load_registry()
        trades = registry.get("trades") or {}
        changed = False
        for trade_id, record in trades.items():
            if not isinstance(record, dict):
                continue
            if record.get("telemetry_status") in {"FINALIZED", "INCOMPLETE_MARKET_EVIDENCE"}:
                continue
            checkpoints = record.get("checkpoints")
            if not isinstance(checkpoints, dict):
                continue
            gap_keys: List[str] = []
            for key in CHECKPOINT_KEYS:
                checkpoint = checkpoints.get(key)
                if not isinstance(checkpoint, dict) or checkpoint.get("state") != "PENDING":
                    continue
                target_ts = checkpoint.get("target_ts")
                if isinstance(target_ts, bool) or not isinstance(target_ts, (int, float)):
                    continue
                if float(target_ts) >= resolved_now:
                    continue
                if _mark_checkpoint_gap(
                    record,
                    key,
                    reason="RUNTIME_RESTART_MISSED_CHECKPOINT",
                    now_ts=resolved_now,
                ):
                    gap_keys.append(key)
                    changed = True
            if gap_keys:
                finalized = _maybe_finalize(record, resolved_now)
                trades[trade_id] = record
                gaps.append((dict(record), gap_keys, finalized))
        if changed:
            _save_registry(registry)

    for record, gap_keys, _finalized in gaps:
        for key in gap_keys:
            _warn_gap(record, key, "RUNTIME_RESTART_MISSED_CHECKPOINT")
    return {
        "recovered_trade_count": len(gaps),
        "evidence_gap_count": sum(len(keys) for _record, keys, _finalized in gaps),
        "finalized_incomplete_count": sum(1 for _record, _keys, finalized in gaps if finalized),
    }
