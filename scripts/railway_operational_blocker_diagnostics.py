"""Privacy-safe one-shot diagnosis of provider/strategy runtime blockers.

Reads bounded historical error JSONL suffix and two small persisted state
documents, without changing provider selection, strategy, runtime status or
Telegram. Values are allowlisted aggregates only. Historical preboot state is
NOT the health state of the newly started process.
"""

from __future__ import annotations

import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ERROR_TAIL_MAX_BYTES = 512 * 1024
STATE_FILE_MAX_BYTES = 64 * 1024

_CODES = frozenset({
    "MARKET_DATA_UNAVAILABLE",
    "MARKET_DATA_LIMITED",
    "NO_ACTIVE_SYMBOLS",
    "ALGO_PARAMS_VALIDATION_FAILED",
    "STRATEGY_STATUS_UPDATE_FAILED",
    "TWELVE_DATA_HTTP_429",
    "POLLER_HEARTBEAT_STALLED",
    "TELEGRAM_POLLER_STARTUP",
    "CONFIG_LOAD_ERROR",
    "OBSERVABILITY_LOG_FAILED",
    "ENGINE_LOOP",
    "SIGNAL_ENGINE",
    "MARKET_CLIENT",
})
_DECISION_KINDS = frozenset({"PRE", "CONFIRM", "OPEN_NOW", "REJECT", "NO_SIGNAL"})
_PROVIDER_NAMES = frozenset({"FINNHUB", "TWELVE_DATA"})
_STATE_PHASES = frozenset({
    "STARTING", "RUNNING", "STOPPING", "STOPPED", "UNSAFE_BLOCKED",
    "BLOCKED", "DEGRADED_SAFE",
})


def _utc(ts: int | float) -> str:
    return datetime.fromtimestamp(float(ts), timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _count(value: Any) -> int | None:
    if (
        isinstance(value, int) and not isinstance(value, bool)
        and 0 <= value <= 100_000_000_000
    ):
        return value
    return None


def _timestamp(value: Any, now_ts: int) -> int | None:
    # Accept both epoch seconds and epoch milliseconds without reusing the
    # small operational-count upper bound. Never accept booleans/future dates.
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value if value <= now_ts + 300 else None


def _allowed(value: Any, names: frozenset[str]) -> str:
    if not isinstance(value, str):
        return "UNKNOWN"
    candidate = value.strip().upper()
    return candidate if candidate in names else "UNKNOWN"


def _unknown_errors(reason: str) -> dict[str, Any]:
    return {
        "status": reason,
        "coverage": "NONE",
        "size_mib": None,
        "tail_record_count": None,
        "invalid_tail_rows": None,
        "warning_or_error_rows_in_tail_24h": None,
        "allowlisted_code_counts_in_tail_24h": {},
        "other_codes_in_tail_24h": None,
        "last_warning_or_error_utc": None,
        "not_a_complete_24h_error_rate": True,
    }


def inspect_error_tail(*, path: str | Path, now_ts: int) -> dict[str, Any]:
    """Only examine last 512 KiB; ignore message, stack, context and IDs."""
    if isinstance(now_ts, bool) or not isinstance(now_ts, int) or now_ts <= 0:
        raise ValueError("now_ts must be a positive integer")
    try:
        with open(path, "rb") as handle:
            first = os.fstat(handle.fileno())
            size = first.st_size
            width = min(size, ERROR_TAIL_MAX_BYTES)
            start = size - width
            handle.seek(start)
            raw = handle.read(width)
            last = os.fstat(handle.fileno())
            if (
                first.st_size != last.st_size
                or first.st_ino != last.st_ino
                or first.st_mtime_ns != last.st_mtime_ns
                or len(raw) != width
            ):
                return _unknown_errors("SOURCE_CHANGED_WHILE_READING")
    except FileNotFoundError:
        return _unknown_errors("ERROR_LOG_NOT_FOUND")
    except OSError:
        return _unknown_errors("ERROR_LOG_UNREADABLE")

    coverage = "FULL_FILE" if start == 0 else "SUFFIX_ONLY"
    if not raw:
        result = _unknown_errors("EMPTY_FILE")
        result.update(
            coverage="FULL_FILE", size_mib=0, tail_record_count=0,
            invalid_tail_rows=0, warning_or_error_rows_in_tail_24h=0,
            other_codes_in_tail_24h=0,
        )
        return result
    if start:
        first_newline = raw.find(b"\n")
        if first_newline < 0 or first_newline == len(raw) - 1:
            return {
                **_unknown_errors("NO_COMPLETE_ROW_IN_SUFFIX"),
                "coverage": "SUFFIX_ONLY",
                "size_mib": round(size / 1048576, 2),
            }
        raw = raw[first_newline + 1:]
    trailing_incomplete = bool(raw and not raw.endswith(b"\n"))
    lines = raw.split(b"\n")
    if trailing_incomplete:
        lines = lines[:-1]

    parsed = invalid = recent = other = 0
    coded: Counter[str] = Counter()
    last_warning_ts = None
    for encoded in lines:
        if not encoded.strip():
            continue
        try:
            value = json.loads(encoded.decode("utf-8"))
        except (UnicodeError, ValueError):
            invalid += 1
            continue
        if not isinstance(value, dict):
            invalid += 1
            continue
        parsed += 1
        event_type = value.get("event_type")
        if not isinstance(event_type, str) or event_type not in {"warning", "error", "config_load_error"}:
            continue
        # Date/time and source kind are required to attribute a recent warning.
        stamp_ms = _timestamp(value.get("ts_epoch_ms"), now_ts * 1000)
        if stamp_ms is None:
            invalid += 1
            continue
        stamp = stamp_ms / 1000.0
        last_warning_ts = stamp if last_warning_ts is None else max(last_warning_ts, stamp)
        if not now_ts - 86400 <= stamp <= now_ts:
            continue
        recent += 1
        data = value.get("data")
        if not isinstance(data, dict):
            invalid += 1
            continue
        raw_code = data.get("code") if event_type == "warning" else data.get("error_type")
        code = _allowed(raw_code, _CODES)
        if code != "UNKNOWN":
            coded[code] += 1
        else:
            other += 1

    return {
        "status": "OBSERVED_TAIL" if parsed else "NO_VALID_JSON_IN_TAIL",
        "coverage": coverage,
        "size_mib": round(size / 1048576, 2),
        "tail_record_count": parsed,
        "invalid_tail_rows": invalid + int(trailing_incomplete),
        "warning_or_error_rows_in_tail_24h": recent,
        "allowlisted_code_counts_in_tail_24h": dict(sorted(coded.items())),
        "other_codes_in_tail_24h": other,
        "last_warning_or_error_utc": (
            _utc(last_warning_ts) if last_warning_ts is not None else None
        ),
        "not_a_complete_24h_error_rate": True,
    }


def _bounded_json(path: Path) -> dict[str, Any] | None:
    try:
        if path.stat().st_size > STATE_FILE_MAX_BYTES:
            return None
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else None
    except (OSError, UnicodeError, ValueError):
        return None


def inspect_preboot_runtime_status(*, path: str | Path, now_ts: int) -> dict[str, Any]:
    """Report only persisted preboot diagnostics, never current process liveness."""
    value = _bounded_json(Path(path))
    if value is None:
        return {"status": "UNKNOWN", "scope": "PREBOOT_PERSISTED_NOT_CURRENT_LIVE"}
    last_eval = _timestamp(value.get("last_strategy_evaluation_ts"), now_ts)
    last_status = _timestamp(value.get("updated_ts"), now_ts)
    return {
        "status": "PERSISTED_SNAPSHOT",
        "scope": "PREBOOT_PERSISTED_NOT_CURRENT_LIVE",
        "prior_process_phase": _allowed(value.get("phase"), _STATE_PHASES),
        "prior_process_provider": _allowed(
            value.get("market_data_provider"), _PROVIDER_NAMES
        ),
        "prior_process_last_strategy_kind": _allowed(
            value.get("last_strategy_decision_kind"), _DECISION_KINDS
        ),
        "prior_process_last_strategy_evaluation_utc": (
            _utc(last_eval) if last_eval is not None else None
        ),
        "prior_process_strategy_evaluation_count": _count(
            value.get("strategy_evaluation_count")
        ),
        "persisted_status_last_updated_utc": (
            _utc(last_status) if last_status is not None else None
        ),
        "no_current_runtime_health_claim": True,
    }


def inspect_provider_selection(*, path: str | Path) -> dict[str, Any]:
    """Observe only the two safe persisted provider authority fields."""
    file = Path(path)
    if not file.exists():
        return {
            "status": "ABSENT",
            "effective_selection_source": "ENVIRONMENT_BOOTSTRAP_ONLY",
            "persisted_provider": None,
            "persisted_mode": None,
        }
    state = _bounded_json(file)
    if state is None:
        return {
            "status": "UNKNOWN_INVALID_OR_UNREADABLE",
            "effective_selection_source": "PERSISTED_STATE_CANNOT_BE_TRUSTED",
            "persisted_provider": None,
            "persisted_mode": None,
        }
    provider = _allowed(state.get("active_provider"), _PROVIDER_NAMES)
    mode = "EXCLUSIVE" if state.get("mode") == "EXCLUSIVE" else "UNKNOWN"
    return {
        "status": "VALID_HEADER" if provider != "UNKNOWN" and mode == "EXCLUSIVE"
        else "UNKNOWN_INVALID_OR_UNREADABLE",
        "effective_selection_source": "PERSISTED_OWNER_SELECTION",
        "persisted_provider": provider,
        "persisted_mode": mode,
    }


def collect_blocker_diagnostics(*, base_dir: Path, now_ts: int) -> dict[str, Any]:
    """Read only file-sourced diagnostics with independent error isolation."""
    root = Path(base_dir)
    try:
        errors = inspect_error_tail(
            path=os.getenv("ERROR_EVENTS_LOG")
            or root / "observability" / "error_events.jsonl",
            now_ts=now_ts,
        )
    except Exception:
        errors = _unknown_errors("ERROR_INSPECTION_FAILED")
    try:
        status = inspect_preboot_runtime_status(
            path=root / "state" / "runtime_status.json", now_ts=now_ts,
        )
    except Exception:
        status = {"status": "UNKNOWN", "scope": "PREBOOT_PERSISTED_NOT_CURRENT_LIVE"}
    try:
        provider = inspect_provider_selection(
            path=root / "config" / "market_data_provider.json"
        )
    except Exception:
        provider = {
            "status": "UNKNOWN_INVALID_OR_UNREADABLE",
            "effective_selection_source": "PERSISTED_STATE_CANNOT_BE_TRUSTED",
            "persisted_provider": None,
        }
    return {
        "scope": "ONE_SHOT_READ_ONLY_PREBOOT_BLOCKER_EVIDENCE",
        "error_event_tail": errors,
        "prior_runtime_state": status,
        "provider_selection": provider,
    }
