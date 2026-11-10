"""Bounded read-only inventory; never prints raw records, prices or secrets."""
from __future__ import annotations
import json
import math
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

IDENTITY = {
    "RAILWAY_PROJECT_ID": "54752c90-3929-4854-9b50-049b5c63ab98",
    "RAILWAY_SERVICE_ID": "c2c41294-4eca-4092-8cdf-94ba57511c6e",
    "RAILWAY_ENVIRONMENT_ID": "c8e55f1a-7518-4e7b-ae38-bad46b0a4171",
}
CUT = datetime.fromisoformat("2026-11-10T13:27:51.140918+00:00").timestamp()
MAX_BYTES = 8 * 1024 * 1024


def emit(value):
    print("TSP_HISTORY_INVENTORY " + json.dumps(value, sort_keys=True), flush=True)


def describe(value):
    if not isinstance(value, dict):
        return {"type": type(value).__name__}
    result = {"keys": sorted(value)}
    for key in ("started_ts", "created_ts", "last_evaluation_ts", "observed_at", "updated_ts"):
        stamp = value.get(key)
        if type(stamp) in (int, float) and math.isfinite(stamp):
            result[key] = stamp
    for key in ("records", "trades", "chains", "published", "items", "active", "policies"):
        rows = value.get(key)
        if not isinstance(rows, (dict, list)):
            continue
        sequence = list(rows.values()) if isinstance(rows, dict) else rows
        shape = {"count": len(sequence)}
        counts = Counter()
        for row in sequence:
            stamp = row.get("created_ts") if isinstance(row, dict) else None
            if type(stamp) in (int, float) and math.isfinite(stamp):
                counts["old" if stamp < CUT else "new"] += 1
            else:
                counts["no_created_ts"] += 1
        shape.update(counts)
        if sequence and isinstance(sequence[0], dict):
            shape["row_keys"] = sorted(sequence[0])
        result[key] = shape
    return result


def main():
    if any(os.environ.get(k) != v for k, v in IDENTITY.items()):
        raise ValueError("Unexpected identity")
    root = Path("/data")
    if os.environ.get("BINARYBOT_BASE_DIR") != str(root) or root.resolve() != root:
        raise ValueError("Unexpected root")
    if not any(line.split()[4] == "/data" for line in Path("/proc/self/mountinfo").read_text().splitlines()):
        raise ValueError("Missing mounted volume")
    receipt = root / "state" / "owner-log-reset-20261110-a1.json"
    raw = receipt.read_bytes()
    evidence = json.loads(raw)
    if evidence.get("status") != "completed" or datetime.fromisoformat(evidence["cutoff_utc"]).timestamp() != CUT:
        raise ValueError("Unverified cutoff")
    emit({"scope": "READ_ONLY_NO_DELETION", "cutoff_utc": evidence["cutoff_utc"]})
    count, total = 0, 0
    for directory in (root / "analytics", root / "observability"):
        for base, dirs, files in os.walk(directory, followlinks=False):
            folder = Path(base)
            dirs[:] = sorted(d for d in dirs if not (folder / d).is_symlink())
            if len(folder.relative_to(root).parts) > 4:
                dirs[:] = []
            for name in sorted(files):
                path = folder / name
                if path.is_symlink() or not path.is_file():
                    continue
                count += 1
                if count > 2000:
                    raise ValueError("Inventory count bound")
                size = path.stat().st_size
                label = str(path.relative_to(root))
                item = {"path": label, "bytes": size}
                if path.suffix == ".json" and size <= MAX_BYTES and total + size <= 48 * MAX_BYTES:
                    total += size
                    try:
                        item.update(describe(json.loads(path.read_bytes())))
                    except (ValueError, TypeError):
                        item["schema"] = "UNREADABLE_JSON"
                elif path.suffix == ".jsonl" and size:
                    with path.open("rb") as f:
                        line = f.readline(256 * 1024)
                    try:
                        row = json.loads(line)
                        item["row_keys"] = sorted(row) if isinstance(row, dict) else []
                        item["nested_keys"] = {k: sorted(v) for k, v in row.items() if isinstance(v, dict)}
                    except (ValueError, TypeError):
                        item["schema"] = "UNREADABLE_FIRST_ROW"
                emit(item)
    emit({"status": "completed", "files": count, "json_bytes_read": total})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        emit({"status": "failed", "error_type": type(exc).__name__})
        raise SystemExit(1)
