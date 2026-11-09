"""Durable Dublin daily identifiers, shared by each signal's visible stages.

The original per-ledger APIs remain available for historical reports. New
lifecycle numbers are stored in the canonical ledger and honor both ledgers'
high-water marks so already delivered study numbers are never reissued.
"""

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
    _validate_ledger(ledger)
    return ledger


def _validate_ledger(ledger: dict) -> None:
    if (not isinstance(ledger, dict) or type(ledger.get("version")) is not int
            or ledger["version"] != 1
            or not isinstance(ledger.get("next_numbers"), dict)
            or not isinstance(ledger.get("signals"), dict)
            or len(ledger["next_numbers"]) > RETENTION_DAYS
            or len(ledger["signals"]) > MAX_NUMBERS):
        raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_LEDGER")
    try:
        for day, number in ledger["next_numbers"].items():
            if (date.fromisoformat(day).isoformat() != day
                    or type(number) is not int or number < 0):
                raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_COUNTER")
        for key, record in ledger["signals"].items():
            if (not isinstance(key, str) or len(key) != 64
                    or any(char not in "0123456789abcdef" for char in key)):
                raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_KEY")
            _label(record)
            day = datetime.fromisoformat(record["issued_at"]).date().isoformat()
            if (record["issued_at"][:10] != day
                    or ledger["next_numbers"].get(day, 0) <= record["number"]):
                raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_COUNTER")
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_LEDGER") from exc


def _check_saveable(ledger: dict) -> None:
    _validate_ledger(ledger)
    # Match storage.save_json_atomic's UTF-8 representation, including newline.
    size = len((json.dumps(ledger, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if size > MAX_BYTES:
        raise ValueError("OWNER_SIGNAL_NUMBER_STORAGE_LIMIT")


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
        _check_saveable(ledger)
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


def _prune_before(ledger: dict, cutoff: str) -> bool:
    obsolete = {day for day in ledger["next_numbers"] if day < cutoff}
    if not obsolete:
        return False
    ledger["next_numbers"] = {day: number for day, number in ledger["next_numbers"].items()
                              if day not in obsolete}
    ledger["signals"] = {key: record for key, record in ledger["signals"].items()
                         if record["issued_at"][:10] not in obsolete}
    return True


def reserve_lifecycle(signal_id: str, now_ts: float) -> str:
    """Reuse one daily identifier from PRE through OPEN and the final result.

    Both existing lock names are acquired in a fixed order. Calling reserve()
    here would reacquire a non-reentrant lock, so allocation is performed under
    those locks directly. Existing study records are adopted without changing
    their original timestamp or number; new records live only in the canonical
    ledger. Study counters are advanced first, so a failed second write can
    leave a harmless gap but cannot let an old study writer reuse this number.
    """
    key = _key(signal_id)
    if type(now_ts) not in (int, float) or not isfinite(now_ts) or now_ts <= 0:
        raise ValueError("INVALID_OWNER_SIGNAL_NUMBER_TIMESTAMP")
    issued = datetime.fromtimestamp(now_ts, DUBLIN)
    day = issued.date().isoformat()
    canonical_path = Path(storage.state_path("owner_signal_numbers.json"))
    study_path = Path(storage.state_path("owner_study_numbers.json"))
    with storage.with_lock("owner_signal_numbers", timeout_sec=1.0):
        with storage.with_lock("owner_study_numbers", timeout_sec=1.0):
            canonical = _read(canonical_path)
            study = _read(study_path)
            record = canonical["signals"].get(key) or study["signals"].get(key)
            latest_day = date.fromisoformat(max(
                day, max(canonical["next_numbers"], default=day),
                max(study["next_numbers"], default=day)))
            cutoff = (latest_day - timedelta(days=RETENTION_DAYS - 1)).isoformat()
            if record is not None and record["issued_at"][:10] < cutoff:
                # A delayed lookup may still reference an old retained report.
                # Return its original label without extending retention or
                # assigning a replacement number in the current day.
                return _label(record)
            if record is None and day < cutoff:
                raise ValueError("OWNER_SIGNAL_NUMBER_TIMESTAMP_TOO_OLD")

            canonical_changed = _prune_before(canonical, cutoff)
            study_changed = _prune_before(study, cutoff)
            if record is None:
                number = max(canonical["next_numbers"].get(day, 0),
                             study["next_numbers"].get(day, 0))
                record = {"issued_at": issued.isoformat(timespec="seconds"), "number": number}
            record_day = record["issued_at"][:10]
            if key not in canonical["signals"]:
                if len(canonical["signals"]) >= MAX_NUMBERS:
                    raise ValueError("OWNER_SIGNAL_NUMBER_STORAGE_LIMIT")
                canonical["signals"][key] = dict(record)
                canonical_changed = True
            high_water = max(canonical["next_numbers"].get(record_day, 0),
                             study["next_numbers"].get(record_day, 0), record["number"] + 1)
            if canonical["next_numbers"].get(record_day) != high_water:
                canonical["next_numbers"][record_day] = high_water
                canonical_changed = True
            if study["next_numbers"].get(record_day) != high_water:
                study["next_numbers"][record_day] = high_water
                study_changed = True
            _check_saveable(canonical)
            _check_saveable(study)
            if study_changed:
                storage.save_json_atomic(str(study_path), study)
            if canonical_changed:
                storage.save_json_atomic(str(canonical_path), canonical)
            return _label(record)


def lookup_lifecycle(signal_id: str) -> str | None:
    """Read an original lifecycle label, including an unadopted legacy study.

    If a signal has distinct historical labels in both old ledgers, canonical
    takes precedence here. A legacy study result must first use lookup(...,
    study=True) to preserve the particular label it originally displayed.
    Corrupt or unavailable ledgers fail closed and are never reset.
    """
    try:
        key = _key(signal_id)
        with storage.with_lock("owner_signal_numbers", timeout_sec=1.0):
            with storage.with_lock("owner_study_numbers", timeout_sec=1.0):
                canonical = _read(Path(storage.state_path("owner_signal_numbers.json")))
                study = _read(Path(storage.state_path("owner_study_numbers.json")))
                record = canonical["signals"].get(key) or study["signals"].get(key)
                return _label(record) if record is not None else None
    except (KeyError, OSError, TypeError, ValueError):
        return None
