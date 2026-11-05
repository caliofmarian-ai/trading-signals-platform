"""Explicit personal delivery and measured Telegram transport timing.

Finnhub data never enters a group, tier, affiliate or other user's destination.
This opt-in uses the existing deployment Owner identity, in shadow mode only.
Receipt time is Telegram API acceptance, not proof that a phone displayed it.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from core import storage


TRUE = frozenset({"true", "1", "yes", "on"})
MAX_TIMING_BYTES = 512 * 1024
MAX_OPPORTUNITIES = 128
MIN_PRE_LEAD_SECONDS = 30


def destination() -> int | None:
    if os.getenv("OWNER_SIGNAL_DELIVERY_ENABLED", "").strip().lower() not in TRUE:
        return None
    if os.getenv("SHADOW_MODE", "").strip().lower() not in TRUE:
        return None
    if os.getenv("ENABLE_BROKER_EXECUTION", "").strip().lower() in TRUE:
        return None
    raw = os.getenv("OWNER_TELEGRAM_ID", "").strip()
    # Positive private-user identity only. Never accept a group/channel ID or
    # a destination supplied by a candidate, callback or channel config.
    if len(raw) > 16 or not raw.isascii() or not raw.isdecimal() or not 0 < int(raw) < 2**53:
        return None
    return int(raw)


def _read_object(path: Path, limit: int) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("SOURCE_UNAVAILABLE")
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError("SOURCE_TOO_LARGE")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("INVALID_SOURCE")
    return value


def _timing_path() -> Path:
    return Path(storage.root_path("state", "owner_signal_timing.json"))


def stage_block_reason(event: dict[str, Any], *, now_ts: float) -> str | None:
    """Keep the Owner's requested visible order and minimum PRE advance.

    Missing private receipts cannot be replaced by an internal FSM state. This
    adds no strategic stage and never delays/queues a stale price for later use:
    each later attempt must still pass a fresh complete runtime evaluation.
    """
    if event.get("stage") == "PRE":
        return None
    try:
        ledger = _read_object(_timing_path(), MAX_TIMING_BYTES)
        key = hashlib.sha256(event["signal_id"].encode()).hexdigest()
        stages = ledger["opportunities"].get(key, {})
        pre = stages.get("PRE")
        if pre is None:
            return "OWNER_PRE_RECEIPT_REQUIRED"
        if event.get("stage") == "OPEN_NOW":
            confirm = stages.get("CONFIRM")
            if confirm is None:
                return "OWNER_CONFIRM_RECEIPT_REQUIRED"
            if not pre["api_accepted_ts"] <= confirm["api_accepted_ts"] <= now_ts:
                return "OWNER_STAGE_TIME_ORDER_INVALID"
            if now_ts - pre["api_accepted_ts"] < MIN_PRE_LEAD_SECONDS:
                return "OWNER_PRE_LEAD_TIME_NOT_MET"
        return None
    except (OSError, ValueError, TypeError, KeyError):
        return "OWNER_STAGE_TIMING_UNAVAILABLE"


def render_text(event: dict[str, Any], text: str) -> str:
    created = event.get("created_ts")
    stamp = (
        datetime.fromtimestamp(created, timezone.utc).strftime("%H:%M:%S UTC")
        if type(created) is int and 0 < created < 2**40 else "unavailable"
    )
    lines = ["Personal signals · shadow observation", text, f"Generated: {stamp}"]
    if event.get("stage") == "CONFIRM" and not event.get("execution_time_available"):
        lines.append("Expiry calibration unavailable; this is not an entry instruction.")
    if event.get("stage") == "PRE":
        lines.append("Watch only. Wait for a valid OPEN_NOW; this setup can be cancelled.")
    return "\n".join(lines)


def record_acceptance(event: dict[str, Any], response: dict[str, Any], *,
                      started_ts: float, accepted_ts: float, transport_seconds: float) -> dict[str, Any]:
    """Persist genuine successful API receipts; never create market outcomes."""
    if destination() is None or response.get("ok") is not True:
        raise ValueError("OWNER_DELIVERY_NOT_ACCEPTED")
    stage, signal_id = event["stage"], event["signal_id"]
    if stage not in {"PRE", "CONFIRM", "OPEN_NOW"} or not isinstance(signal_id, str):
        raise ValueError("INVALID_STAGE")
    # Hash opportunity identity in this supplemental timing ledger. Primary
    # distribution events already retain the canonical identity and receipt.
    key = hashlib.sha256(signal_id.encode()).hexdigest()
    path = _timing_path()
    with storage.with_lock("owner_signal_timing"):
        ledger = _read_object(path, MAX_TIMING_BYTES) if path.exists() else {"schema_version": "1.0.0", "opportunities": {}}
        rows = ledger["opportunities"]
        stages = rows.setdefault(key, {})
        prior = stages.get(stage)
        receipt = {
            "generated_ts": event.get("created_ts"),
            "send_started_ts": started_ts,
            "api_accepted_ts": accepted_ts,
            "api_request_seconds": round(transport_seconds, 6),
            "generated_to_api_seconds": round(accepted_ts - event["created_ts"], 6),
            "telegram_message_date": (response.get("result") or {}).get("date"),
            "execution_time_available": event.get("execution_time_available") is True,
            "open_now_expiry_minutes": event.get("open_now_expiry_minutes"),
            "confirm_expiry_min_minutes": event.get("confirm_expiry_min_minutes"),
            "confirm_expiry_max_minutes": event.get("confirm_expiry_max_minutes"),
            "execution_calibration_source": event.get("execution_calibration_source"),
        }
        # First successful stage is the lead-time anchor, not a later repeated
        # PRE on a new candle. Never fabricate missing predecessor timestamps.
        if prior is None:
            stages[stage] = receipt
        pre, confirm, opened = (stages.get(name) for name in ("PRE", "CONFIRM", "OPEN_NOW"))
        gaps = {
            "pre_to_confirm_seconds": round(confirm["api_accepted_ts"] - pre["api_accepted_ts"], 6) if pre and confirm else None,
            "pre_to_open_seconds": round(opened["api_accepted_ts"] - pre["api_accepted_ts"], 6) if pre and opened else None,
            "confirm_to_open_seconds": round(opened["api_accepted_ts"] - confirm["api_accepted_ts"], 6) if confirm and opened else None,
        }
        while len(rows) > MAX_OPPORTUNITIES:
            del rows[next(iter(rows))]
        ledger["updated_ts"] = accepted_ts
        storage.save_json_atomic(str(path), ledger)
    evidence = {
        "stage": stage, "scope": "OWNER_PRIVATE_API_ACCEPTANCE",
        "api_request_seconds": receipt["api_request_seconds"],
        "generated_to_api_seconds": receipt["generated_to_api_seconds"],
        **gaps, "phone_receipt_proven": False, "broker_executed": False,
    }
    print("TSP_OWNER_SIGNAL_TIMING " + json.dumps(evidence, sort_keys=True), flush=True)
    from intelligence import owner_timing_session
    owner_timing_session.observe_receipt(evidence, now_ts=accepted_ts)
    return evidence


def send_activation_receipt() -> None:
    """One clearly labelled transport check per boot; never a synthetic signal."""
    owner = destination()
    if owner is None:
        return
    from core import telegram_publisher
    started = time.perf_counter()
    response = telegram_publisher.send_message(
        chat_id=owner,
        text=("Private signal delivery enabled\n"
              "Valid PRE, CONFIRM and OPEN_NOW stages will arrive here.\n"
              "OPEN_NOW still requires a valid execution-expiry calibration.\n"
              "This message checks delivery only; it is not a signal."),
    )
    print("TSP_OWNER_DELIVERY_ACTIVATION " + json.dumps({
        "accepted": response.get("ok") is True,
        "api_request_seconds": round(time.perf_counter() - started, 6),
        "signal": False, "broker_executed": False,
    }, sort_keys=True), flush=True)


def audit_evidence(user_id: int) -> dict[str, Any]:
    """Bounded personal candle snapshot for chronological offline calibration.

    Accessible only to the existing Owner, through their authorized audit. No
    credentials, new file-access directory, trading action or parameter write.
    """
    if destination() != user_id:
        return {"status": "PERSONAL_DELIVERY_NOT_ENABLED_FOR_OWNER"}
    result: dict[str, Any] = {"status": "UNAVAILABLE", "broker_executed": False}
    try:
        from intelligence import owner_timing_session
        result["timing_session"] = owner_timing_session.summary(now_ts=time.time())
        from intelligence import shadow_model_time_research
        result["model_time_research_evidence"] = shadow_model_time_research.private_calibration_evidence()
        from intelligence import live_score_severity_research
        result["live_score_severity_research"] = live_score_severity_research.summary(now_ts=time.time())
        from intelligence import execution_expiry_calibration
        from intelligence import lifecycle_cadence_research
        try:
            result["lifecycle_cadence_research"]=lifecycle_cadence_research.summary(now_ts=time.time())
        except (OSError,ValueError,TypeError,KeyError,RuntimeError):
            result["lifecycle_cadence_research"]={"status":"SOURCE_UNAVAILABLE_OR_INVALID"}
        try:
            result["execution_expiry_calibration"] = execution_expiry_calibration.summary(now_ts=time.time())
        except (OSError, ValueError, TypeError, KeyError):
            result["execution_expiry_calibration"] = {"status":"SOURCE_UNAVAILABLE_OR_INVALID",
                "execution_calibration_proven":False, "broker_executed":False}
        path = _timing_path()
        result["delivery_timing"] = _read_object(path, MAX_TIMING_BYTES) if path.exists() else {"opportunities": {}}
        from core import market_data_provider_control, runtime_param_gate
        if market_data_provider_control.get_active_provider() != "FINNHUB":
            return {**result, "status": "FINNHUB_NOT_SELECTED"}
        root = Path(storage.base_dir()).resolve()
        source = Path(os.getenv("FINNHUB_CANDLE_STORE", str(root / "market_data" / "finnhub_eurusd.json")))
        if not source.is_absolute():
            source = root / source
        if not source.resolve().is_relative_to(root):
            raise ValueError("SOURCE_OUTSIDE_RUNTIME")
        raw = _read_object(source, 2 * 1024 * 1024)
        if raw.get("provider") != "FINNHUB":
            raise ValueError("PROVIDER_MISMATCH")
        candles = raw["candles"]
        cleaned = {}
        for frame in ("M1", "M5"):
            rows = candles[frame]
            if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
                raise ValueError("INVALID_CANDLE_COUNT")
            cleaned[frame] = [{key: row[key] for key in (
                "ts", "open", "high", "low", "close", "complete", "provider", "symbol", "timeframe"
            )} for row in rows]
            if any(row["provider"] != "FINNHUB" or row["symbol"] not in {"EURUSD", "EUR/USD"}
                   or row["timeframe"] != frame or type(row["complete"]) is not bool for row in cleaned[frame]):
                raise ValueError("INVALID_CANDLE_PROVENANCE")
        from runtime.market_history_integrity import inspect_history
        if inspect_history(cleaned)["state"] != "VALID":
            raise ValueError("INVALID_CANDLE_HISTORY")
        result.update(status="PERSONAL_RESEARCH_SNAPSHOT", provider="FINNHUB", candles=cleaned,
                      params=runtime_param_gate.load_runtime_algo_params(str(root / "config" / "algo_params.json")),
                      observed_at_ts=time.time(), provider_provenance="PERSISTED_FEED_LABEL")
    except (OSError, ValueError, TypeError, KeyError):
        result["status"] = "SOURCE_UNAVAILABLE_OR_INVALID"
    return result
