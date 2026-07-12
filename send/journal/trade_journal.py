# /opt/binarybot/journal/trade_journal.py
# BinaryBot — Trade Journal (Layer 6)

from __future__ import annotations

import os
import time
import json
from typing import Dict, Any, Optional

BASE_DIR = "/opt/binarybot"
JOURNAL_DIR = os.path.join(BASE_DIR, "journal")
JOURNAL_JSONL = os.path.join(JOURNAL_DIR, "trades.jsonl")


def _now_ts() -> int:
    return int(time.time())


def ensure_journal_dir():
    os.makedirs(JOURNAL_DIR, exist_ok=True)


def append_trade(record: Dict[str, Any]) -> None:
    """
    Append a trade/event record to journal (append-only JSONL).
    Minimal fields recommended:
      - ts
      - signal_id
      - symbol
      - stage ("OPEN_NOW" / "CLOSE" / "RESULT")
      - direction
      - expiry_minutes
      - meta (dict)
    """
    ensure_journal_dir()

    rec = dict(record)
    rec.setdefault("ts", _now_ts())

    with open(JOURNAL_JSONL, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_trades(limit: int = 200) -> list[Dict[str, Any]]:
    """
    Read last N journal entries (best-effort).
    """
    ensure_journal_dir()

    if not os.path.exists(JOURNAL_JSONL):
        return []

    # For simplicity: read whole file if small; for large files, tail-like read can be added later.
    with open(JOURNAL_JSONL, "r") as f:
        lines = f.readlines()

    lines = lines[-max(0, int(limit)):] if limit else lines

    out: list[Dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def find_by_signal_id(signal_id: str, limit: int = 2000) -> list[Dict[str, Any]]:
    """
    Return entries matching a signal_id (best-effort).
    """
    items = read_trades(limit=limit)
    return [x for x in items if x.get("signal_id") == signal_id]


def summarize_recent(limit: int = 200) -> Dict[str, Any]:
    """
    Very lightweight summary for quick debugging.
    """
    items = read_trades(limit=limit)

    summary = {
        "count": len(items),
        "by_stage": {},
        "last_ts": items[-1]["ts"] if items else None,
    }

    for it in items:
        st = str(it.get("stage", "UNKNOWN"))
        summary["by_stage"][st] = summary["by_stage"].get(st, 0) + 1

    return summary