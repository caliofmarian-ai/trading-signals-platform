"""Private, non-published Model Time observations, never executed-trade truth.

This experiment observes one FSM-accepted OPEN_NOW opportunity once, using
the first subsequent real stream tick and the uncalibrated Model Time horizon.
It neither supplies ExecutionCalibration nor changes any production gate.
"""

from __future__ import annotations

import json
import math
import os
import re
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping

from core import storage
from core.decision_object import DecisionObject
from core.v2_fsm_orchestrator import PersistentFSMResult


PROTOCOL = "SHADOW_MODEL_TIME_RESEARCH_V1"
MAX_ENTRY_DELAY_SECONDS = 10.0
MAX_SAMPLE_DELAY_SECONDS = 2.0
MAX_SAMPLE_AGE_SECONDS = 2.0
MAX_PENDING = 256
MAX_RECORD_FILES = 10000
MAX_RECORD_BYTES = 128 * 1024
MAX_SUMMARY_STATUS_BYTES = 8 * 1024
_ID = re.compile(r"[0-9a-f]{64}\Z")
_RECOVERED: set[str] = set()


def _on(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def enabled() -> bool:
    return _on("SHADOW_MODEL_TIME_RESEARCH_ENABLED") and _on("SHADOW_MODE") and not _on("ENABLE_BROKER_EXECUTION")


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("research requires a finite positive number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError("research requires a finite positive number")
    return result


def _root() -> Path:
    root = Path(storage.root_path("analytics", "shadow_model_time_research"))
    if root.is_symlink() or (root / "records").is_symlink():
        raise ValueError("research directory cannot be a symlink")
    return root


def _path(root: Path, record_id: str) -> Path:
    if not isinstance(record_id, str) or not _ID.fullmatch(record_id):
        raise ValueError("invalid research identity")
    path = root / "records" / f"{record_id}.json"
    if path.is_symlink():
        raise ValueError("research record cannot be a symlink")
    return path


def _read(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError("research evidence cannot be a symlink")
    with path.open("rb") as handle:
        data = handle.read(MAX_RECORD_BYTES + 1)
    if len(data) > MAX_RECORD_BYTES:
        raise ValueError("research evidence exceeds its bound")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("invalid research object")
    return value


def _classify(direction: str, entry: float, expiry: float) -> str:
    if expiry == entry:
        return "DRAW"
    return "WIN" if (expiry > entry) == (direction == "BUY") else "LOSS"


def _record(root: Path, record_id: str) -> dict:
    record = _read(_path(root, record_id))
    if (record.get("protocol") != PROTOCOL or record.get("record_id") != record_id
        or record.get("publication_status") != "NOT_PUBLISHED"
        or record.get("truth_domain") != "HYPOTHETICAL_RESEARCH"
        or record.get("execution_calibration_proven") is not False
        or record.get("horizon_source") != "UNCALIBRATED_MODEL_TIME"
        or record.get("authoritative_for_strategy_performance") is not False
        or record.get("broker_executed") is not False
        or record.get("direction") not in {"BUY", "SELL"}
        or record.get("provider") != "FINNHUB"
        or record.get("symbol") != "EUR/USD"
        or record.get("state") not in {"WAITING_ENTRY", "WAITING_EXPIRY", "FINAL"}):
        raise ValueError("invalid or mixed research evidence")
    created = _number(record.get("created_ts"))
    horizon = _number(record.get("horizon_seconds"))
    if horizon > 86400:
        raise ValueError("research horizon exceeds its bound")
    entry = record.get("entry_sample")
    if entry is not None:
        stamp = _number(entry.get("observed_ts"))
        if (_sample(entry, stamp) is None or not created <= stamp <= created + MAX_ENTRY_DELAY_SECONDS
            or not math.isclose(_number(record.get("expiry_ts")), stamp + horizon, abs_tol=1e-6)):
            raise ValueError("invalid research entry evidence")
    if record["state"] == "WAITING_ENTRY" and entry is not None:
        raise ValueError("waiting entry already contains a sample")
    if record["state"] == "WAITING_EXPIRY" and entry is None:
        raise ValueError("missing research entry evidence")
    if record["state"] == "FINAL":
        outcome = record.get("outcome")
        if outcome not in {"WIN", "LOSS", "DRAW", "UNKNOWN"}:
            raise ValueError("invalid research label")
        if outcome != "UNKNOWN":
            entry, expiry = record["entry_sample"], record["expiry_sample"]
            stamp = _number(expiry.get("observed_ts"))
            if (_sample(expiry, stamp) is None
                or not record["expiry_ts"] <= stamp <= record["expiry_ts"] + MAX_SAMPLE_DELAY_SECONDS
                or _number(record.get("finalized_ts")) < stamp):
                raise ValueError("invalid research expiry evidence")
            if _classify(record["direction"], _number(entry["price"]), _number(expiry["price"])) != outcome:
                raise ValueError("research label disagrees with raw prices")
        elif not record.get("outcome_reason") or record.get("expiry_sample") is not None:
            raise ValueError("invalid unknown research evidence")
    return record


def _save(root: Path, record: dict) -> None:
    storage.save_json_atomic(str(_path(root, record["record_id"])), record)


def _index(root: Path) -> list[str]:
    path = root / "active.json"
    if not path.exists():
        return []
    value = _read(path)
    active = value.get("active")
    if (value.get("protocol") != PROTOCOL or not isinstance(active, list)
        or len(active) > MAX_PENDING or len(set(active)) != len(active)
        or any(not isinstance(x, str) or not _ID.fullmatch(x) for x in active)):
        raise ValueError("invalid research active index")
    return active


def _save_index(root: Path, active: list[str]) -> None:
    storage.save_json_atomic(str(root / "active.json"), {"protocol": PROTOCOL, "active": active})


def _files(root: Path) -> list[Path]:
    result = []
    directory = root / "records"
    if directory.exists():
        for path in directory.iterdir():
            if path.suffix != ".json" or not _ID.fullmatch(path.stem) or path.is_symlink():
                raise ValueError("unrecognized research evidence file")
            result.append(path)
            if len(result) > MAX_RECORD_FILES:
                raise ValueError("research inventory exceeds its bound")
    return result


def _finish(record: dict, now: float, outcome: str, reason: str) -> None:
    record.update(state="FINAL", outcome=outcome, outcome_reason=reason, finalized_ts=now)


def _recover_locked(root: Path, now: float) -> None:
    if str(root) in _RECOVERED:
        return
    # Rebuild from authoritative per-opportunity records. This also repairs a
    # crash between an atomic record write and its active-index write.
    active = []
    for path in _files(root):
        record = _record(root, path.stem)
        if record["state"] == "FINAL":
            continue
        target = record["created_ts"] + MAX_ENTRY_DELAY_SECONDS if record["state"] == "WAITING_ENTRY" else record["expiry_ts"] + MAX_SAMPLE_DELAY_SECONDS
        if now > target:
            _finish(record, now, "UNKNOWN", "RESTART_MISSED_OBSERVATION")
            _save(root, record)
        else:
            active.append(record["record_id"])
    if len(active) > MAX_PENDING:
        raise ValueError("research pending capacity exceeded")
    if active or (root / "active.json").exists():
        _save_index(root, active)
    _RECOVERED.add(str(root))


def register_accepted_open(
    decision: DecisionObject, handoff: PersistentFSMResult, *, provider: str, now_ts: float,
) -> dict:
    if not enabled():
        return {"status": "DISABLED", "registered": False}
    now = _number(now_ts)
    if (not isinstance(decision, DecisionObject) or not isinstance(handoff, PersistentFSMResult)):
        raise TypeError("research requires canonical decision and FSM evidence")
    if (provider != "FINNHUB" or decision.setup.symbol.replace("/", "") != "EURUSD"
        or decision.kind != "OPEN_NOW" or not handoff.accepted
        or handoff.accepted_stage != "OPEN_NOW" or handoff.requested_stage != "OPEN_NOW"
        or not handoff.stage_handoff_ready or not handoff.trade_execution_ready
        or handoff.signal_id != decision.signal_id or handoff.decision_id != decision.decision_id
        or handoff.decision_audit_id != decision.decision_audit_id
        or decision.compatibility_mode or decision.setup.evaluated_ts > now
        or decision.time.time_state != "READY" or decision.reject.hard_blockers
        or decision.strategic_flags.rejectable or not decision.strategic_flags.valid_structure
        or not decision.strategic_flags.feasible_time or not decision.strategic_flags.trade_physics_ready
        or decision.score.trade_physics is None or decision.score.trade_physics.readiness_state != "READY"):
        return {"status": "INELIGIBLE", "registered": False}
    horizon = _number(decision.time.model_expiry) * 60.0
    if horizon > 86400:
        raise ValueError("research horizon exceeds its bound")
    record_id = sha256(f"{PROTOCOL}|{provider}|{decision.signal_id}".encode()).hexdigest()
    root = _root()
    with storage.with_lock("shadow_model_time_research", timeout_sec=0.2):
        _recover_locked(root, now)
        if _path(root, record_id).exists():
            _record(root, record_id)
            return {"status": "DUPLICATE_OPPORTUNITY", "registered": False}
        active = _index(root)
        if len(active) >= MAX_PENDING:
            return {"status": "CAPACITY_REACHED", "registered": False}
        record = {
            "protocol": PROTOCOL, "record_id": record_id,
            "truth_domain": "HYPOTHETICAL_RESEARCH", "publication_status": "NOT_PUBLISHED",
            "authoritative_for_strategy_performance": False, "broker_executed": False,
            "execution_calibration_proven": False, "horizon_source": "UNCALIBRATED_MODEL_TIME",
            "provider": provider, "symbol": "EUR/USD", "direction": decision.setup.direction,
            "created_ts": now, "horizon_seconds": horizon, "state": "WAITING_ENTRY",
            "decision_snapshot": decision.to_dict(), "fsm_transition_id": handoff.fsm_transition_id,
            "entry_sample": None, "expiry_sample": None, "outcome": None,
            "observation_policy": {"entry_deadline_seconds": MAX_ENTRY_DELAY_SECONDS,
                "expiry_max_lateness_seconds": MAX_SAMPLE_DELAY_SECONDS,
                "max_sample_age_seconds": MAX_SAMPLE_AGE_SECONDS},
        }
        try:
            _save(root, record)
            _save_index(root, active + [record_id])
        except Exception:
            _RECOVERED.discard(str(root))
            raise
    return {"status": "REGISTERED", "registered": True}


def _sample(raw: Any, now: float) -> dict | None:
    if (not isinstance(raw, Mapping) or raw.get("provider") != "FINNHUB"
        or str(raw.get("symbol", "")).replace("/", "") != "EURUSD"
        or raw.get("source") != "LIVE_STREAM_CURRENT_M1_CLOSE"):
        return None
    try:
        price, stamp = _number(raw.get("price")), _number(raw.get("observed_ts"))
    except ValueError:
        return None
    if not 0 <= now - stamp <= MAX_SAMPLE_AGE_SECONDS:
        return None
    return {"provider": "FINNHUB", "symbol": "EUR/USD", "price": price,
        "observed_ts": stamp, "source": "LIVE_STREAM_CURRENT_M1_CLOSE"}


def run_cycle(*, active_provider: str, now_ts: float, price_loader: Callable[[str], dict]) -> dict:
    if not enabled():
        return {"status": "DISABLED", "changed": False}
    now = _number(now_ts)
    root = _root()
    changed = False
    with storage.with_lock("shadow_model_time_research", timeout_sec=0.2):
        first_cycle = str(root) not in _RECOVERED
        _recover_locked(root, now)
        active = _index(root)
        sample = None
        if active and active_provider == "FINNHUB":
            try:
                sample = _sample(price_loader("EUR/USD"), now)
            except Exception:
                pass  # Missing real evidence becomes UNKNOWN at its deadline.
        remaining = []
        for record_id in active:
            record = _record(root, record_id)
            before = json.dumps(record, sort_keys=True)
            if record["state"] == "FINAL":
                changed = True
                continue
            if active_provider != record["provider"]:
                _finish(record, now, "UNKNOWN", "PROVIDER_CHANGED")
            elif record["state"] == "WAITING_ENTRY":
                if sample and record["created_ts"] <= sample["observed_ts"] <= record["created_ts"] + MAX_ENTRY_DELAY_SECONDS:
                    record.update(state="WAITING_EXPIRY", entry_sample=sample,
                        expiry_ts=sample["observed_ts"] + record["horizon_seconds"])
                elif now > record["created_ts"] + MAX_ENTRY_DELAY_SECONDS:
                    _finish(record, now, "UNKNOWN", "ENTRY_OBSERVATION_MISSING")
            elif record["state"] == "WAITING_EXPIRY":
                if sample and record["expiry_ts"] <= sample["observed_ts"] <= record["expiry_ts"] + MAX_SAMPLE_DELAY_SECONDS:
                    outcome = _classify(record["direction"], record["entry_sample"]["price"], sample["price"])
                    record["expiry_sample"] = sample
                    _finish(record, now, outcome, "OBSERVED_MODEL_TIME_COMPARISON")
                elif now > record["expiry_ts"] + MAX_SAMPLE_DELAY_SECONDS:
                    _finish(record, now, "UNKNOWN", "EXPIRY_OBSERVATION_MISSING")
            if json.dumps(record, sort_keys=True) != before:
                _save(root, record)
                changed = True
            if record["state"] != "FINAL":
                remaining.append(record_id)
        if remaining != active:
            _save_index(root, remaining)
    return {"status": "RUNNING", "changed": changed or first_cycle, "pending": len(remaining)}


def summary() -> dict:
    """Read only aggregate research evidence; never expose prices or identities."""
    counts = {key: 0 for key in ("WIN", "LOSS", "DRAW", "UNKNOWN")}
    pending = 0
    for path in _files(_root()):
        record = _record(_root(), path.stem)
        if record["state"] == "FINAL":
            counts[record["outcome"]] += 1
        else:
            pending += 1
    decisive = counts["WIN"] + counts["LOSS"]
    return {"protocol": PROTOCOL, "enabled": enabled(), "truth_domain": "HYPOTHETICAL_RESEARCH",
        "status": "OBSERVED" if any(counts.values()) else "NO_COMPLETED_OBSERVATIONS",
        "outcomes": counts, "pending": pending, "decisive_sample": decisive,
        "hypothetical_win_rate_percent": 100.0 * counts["WIN"] / decisive if decisive else None,
        "authoritative_for_strategy_performance": False, "broker_executed": False,
        "execution_calibration_proven": False, "broker_quote_equivalence_proven": False,
        "horizon_source": "UNCALIBRATED_MODEL_TIME", "profitability_established": False}


def persist_summary_status(value: dict, *, observed_at: float) -> None:
    """Retain the derived observation outside the shared, racy status snapshot.

    This cache owns no outcome truth. Its timestamp is an observation time,
    not a heartbeat or proof that the worker is currently alive.
    """
    payload = {"protocol": PROTOCOL, "observed_at": _number(observed_at),
               "is_heartbeat": False, "summary": value}
    if not _valid_summary_status(payload):
        raise ValueError("invalid research summary status")
    if len(json.dumps(payload).encode("utf-8")) > MAX_SUMMARY_STATUS_BYTES:
        raise ValueError("research summary status exceeds its bound")
    storage.save_json_atomic(storage.state_path("shadow_research_summary.json"), payload)


def _valid_summary_status(value: Any) -> bool:
    if (not isinstance(value, dict)
        or set(value) != {"protocol", "observed_at", "is_heartbeat", "summary"}
        or value.get("protocol") != PROTOCOL or value.get("is_heartbeat") is not False):
        return False
    _number(value.get("observed_at"))
    item = value.get("summary")
    expected = {"protocol", "enabled", "truth_domain", "status", "outcomes", "pending",
                "decisive_sample", "hypothetical_win_rate_percent", "horizon_source",
                "authoritative_for_strategy_performance", "broker_executed",
                "execution_calibration_proven", "broker_quote_equivalence_proven", "profitability_established"}
    if (not isinstance(item, dict) or set(item) != expected
        or item.get("protocol") != PROTOCOL or type(item.get("enabled")) is not bool
        or item.get("truth_domain") != "HYPOTHETICAL_RESEARCH"
        or item.get("horizon_source") != "UNCALIBRATED_MODEL_TIME"
        or any(item.get(k) is not False for k in (
            "authoritative_for_strategy_performance", "broker_executed",
            "execution_calibration_proven", "broker_quote_equivalence_proven", "profitability_established"))):
        return False
    counts = item.get("outcomes")
    if (not isinstance(counts, dict) or set(counts) != {"WIN", "LOSS", "DRAW", "UNKNOWN"}
        or any(type(n) is not int or n < 0 for n in counts.values())
        or sum(counts.values()) > MAX_RECORD_FILES
        or type(item.get("pending")) is not int or not 0 <= item["pending"] <= MAX_PENDING
        or type(item.get("decisive_sample")) is not int
        or item["decisive_sample"] != counts["WIN"] + counts["LOSS"]
        or item.get("status") != ("OBSERVED" if sum(counts.values()) else "NO_COMPLETED_OBSERVATIONS")):
        return False
    rate = item.get("hypothetical_win_rate_percent")
    decisive = item["decisive_sample"]
    return (rate is None if decisive == 0 else
            type(rate) in {int, float} and math.isfinite(rate)
            and math.isclose(rate, 100.0 * counts["WIN"] / decisive, abs_tol=1e-9))


def read_summary_status() -> dict | None:
    path = Path(storage.state_path("shadow_research_summary.json"))
    if path.is_symlink():
        return None
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_SUMMARY_STATUS_BYTES + 1)
        if len(raw) > MAX_SUMMARY_STATUS_BYTES:
            return None
        value = json.loads(raw)
        return value if _valid_summary_status(value) else None
    except (OSError, ValueError, TypeError):
        return None
