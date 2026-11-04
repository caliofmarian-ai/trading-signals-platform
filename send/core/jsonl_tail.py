"""Bounded read-only observations of existing append-only JSONL evidence."""
from __future__ import annotations

import json
import os
import stat
from typing import Any


CHUNK_BYTES = 64 * 1024
MAX_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 5000


def _nonfinite_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant")


def read_tail(path: str, *, limit: int = 50, max_bytes: int = MAX_BYTES) -> dict[str, Any]:
    """Capture a bounded prefix-at-open tail; never infer complete history.

    Appends after the captured file end are outside this observation. Rotation,
    truncation, short reads, invalid UTF-8/JSON and non-object rows are explicit
    unavailable evidence, rather than silently discarded events.
    """
    meta: dict[str, Any] = {
        "status": "UNAVAILABLE", "scope": "BOUNDED_TAIL_AT_OPEN",
        "complete_history": False, "record_limit": limit, "byte_limit": max_bytes,
        "bytes_read": 0, "records_read": 0, "byte_limited": False,
        "record_limited": False, "source_grew_during_read": False,
    }

    def result(reason: str | None = None, rows: list | None = None) -> dict:
        if reason:
            meta["reason"] = reason
        return {"records": rows or [], "metadata": meta}

    if (isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RECORDS
        or isinstance(max_bytes, bool) or not isinstance(max_bytes, int)
        or not 1 <= max_bytes <= MAX_BYTES):
        return result("INVALID_BOUND")
    try:
        with open(path, "rb") as handle:
            original = os.fstat(handle.fileno())
            if not stat.S_ISREG(original.st_mode):
                return result("NOT_REGULAR_FILE")
            size = original.st_size
            meta["source_size_at_open"] = size
            remaining = min(size, max_bytes)
            chunks = []
            newline_count = 0
            while remaining:
                width = min(CHUNK_BYTES, remaining)
                handle.seek(size - meta["bytes_read"] - width)
                block = handle.read(width)
                if len(block) != width:
                    return result("SOURCE_CHANGED_DURING_READ")
                chunks.append(block)
                meta["bytes_read"] += width
                remaining -= width
                newline_count += block.count(b"\n")
                if newline_count >= limit + 1:
                    break
            after = os.fstat(handle.fileno())
            current = os.stat(path)
            if ((current.st_dev, current.st_ino) != (original.st_dev, original.st_ino)
                or after.st_size < size
                or (after.st_size == size and after.st_mtime_ns != original.st_mtime_ns)):
                return result("SOURCE_CHANGED_DURING_READ")
            meta["source_grew_during_read"] = after.st_size > size
        captured = b"".join(reversed(chunks))
        partial_head = meta["bytes_read"] < size
        if partial_head:
            boundary = captured.find(b"\n")
            if boundary < 0:
                meta["byte_limited"] = True
                return result("NO_COMPLETE_RECORD_WITHIN_BYTE_BOUND")
            captured = captured[boundary + 1:]
            if not captured.strip():
                meta["byte_limited"] = True
                return result("NO_COMPLETE_RECORD_WITHIN_BYTE_BOUND")
        lines = captured.splitlines()
        meta["byte_limited"] = partial_head and meta["bytes_read"] == max_bytes
        meta["record_limited"] = len(lines) > limit or (partial_head and not meta["byte_limited"])
        rows = []
        for line in lines[-limit:]:
            if not line.strip():
                continue
            row = json.loads(line.decode("utf-8"), parse_constant=_nonfinite_constant)
            if not isinstance(row, dict):
                return result("INVALID_JSONL_RECORD")
            rows.append(row)
        meta.update(status="OK", records_read=len(rows))
        meta["first_event_ts"] = rows[0].get("ts_utc") if rows else None
        meta["last_event_ts"] = rows[-1].get("ts_utc") if rows else None
        return result(rows=rows)
    except FileNotFoundError:
        meta["status"] = "MISSING"
        return result("SOURCE_MISSING")
    except (UnicodeError, ValueError, TypeError):
        return result("INVALID_JSONL_RECORD")
    except OSError:
        return result("SOURCE_READ_FAILED")
