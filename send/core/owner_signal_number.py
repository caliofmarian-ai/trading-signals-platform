"""Independent durable daily numbers for private OPEN_NOW and study reports."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
import json
from math import isfinite
from pathlib import Path
from zoneinfo import ZoneInfo

from core import storage


DUBLIN = ZoneInfo("Europe/Dublin")
RETENTION_DAYS = 14
MAX_NUMBERS = 16_384
MAX_BYTES = 4 * 1024 * 1024


def _key(signal_id: str) -> str:
    if not isinstance(signal_id, str) or not signal_id.strip():
        raise ValueError("INVALID_OWNER_SIGNAL_ID")
    return hashlib.sha256(signal_id.encode()).hexdigest()


def _read(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_PATH")
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    except FileNotFoundError:
        return {"version": 1, "next_numbers": {}, "signals": {}}
    if len(data) > MAX_BYTES:
        raise ValueError("OWNER_SIGNAL_NUMBER_STORAGE_LIMIT")
    ledger = json.loads(data)
    if (not isinstance(ledger, dict) or ledger.get("version") != 1
            or not isinstance(ledger.get("next_numbers"), dict)
            or not isinstance(ledger.get("signals"), dict)
            or len(ledger["next_numbers"]) > RETENTION_DAYS
            or len(ledger["signals"]) > MAX_NUMBERS):
        raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_LEDGER")
    return ledger


def _label(record: dict) -> str:
    issued = datetime.fromisoformat(record["issued_at"])
    number = record["number"]
    if issued.tzinfo is None or type(number) is not int or number < 0:
        raise ValueError("INVALID_OWNER_SIGNAL_NUMBER")
    return f"{issued:%d.%m.%Y} · {issued:%H:%M:%S} · nr. {number}"


def _ledger_name(study: bool) -> str:
    return "owner_study_numbers" if study else "owner_signal_numbers"


def reserve(signal_id: str, now_ts: float, *, study: bool = False) -> str:
    """Assign at most one number to an OPEN attempt, even across restarts."""
    key = _key(signal_id)
    if type(now_ts) not in (int, float) or not isfinite(now_ts) or now_ts <= 0:
        raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_TIMESTAMP")
    issued = datetime.fromtimestamp(now_ts, DUBLIN)
    day = issued.date().isoformat()
    ledger_name = _ledger_name(study)
    path = Path(storage.state_path(f"{ledger_name}.json"))
    with storage.with_lock(ledger_name, timeout_sec=1.0):
        ledger = _read(path)
        signals = ledger["signals"]
        if key in signals:
            return _label(signals[key])

        next_numbers = ledger["next_numbers"]
        latest_day = date.fromisoformat(max(day, max(next_numbers, default=day)))
        cutoff = (latest_day - timedelta(days=RETENTION_DAYS - 1)).isoformat()
        if day < cutoff:
            raise ValueError("OWNER_SIGNAL_NUMBER_TIMESTAMP_TOO_OLD")
        obsolete = {prior_day for prior_day in next_numbers if prior_day < cutoff}
        if obsolete:
            for prior_day in obsolete:
                del next_numbers[prior_day]
            signals = {signal: row for signal, row in signals.items() if row["issued_at"][:10] not in obsolete}
            ledger["signals"] = signals
        if len(signals) >= MAX_NUMBERS:
            raise ValueError("OWNER_SIGNAL_NUMBER_STORAGE_LIMIT")

        number = next_numbers.get(day, 0)
        record = {"issued_at": issued.isoformat(timespec="seconds"), "number": number}
        label = _label(record)
        signals[key] = record
        next_numbers[day] = number + 1
        storage.save_json_atomic(str(path), ledger)
        return label


def lookup(signal_id: str, *, study: bool = False) -> str | None:
    """Read the original OPEN label for an outcome without assigning a number."""
    try:
        path = Path(storage.state_path(f"{_ledger_name(study)}.json"))
        record = _read(path)["signals"].get(_key(signal_id))
        return _label(record) if record is not None else None
    except (KeyError, OSError, TypeError, ValueError):
        return None
