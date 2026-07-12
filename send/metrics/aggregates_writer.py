# /opt/binarybot/metrics/aggregates_writer.py
# BinaryBot — Metrics Aggregates Writer

import json
import time
import os

from metrics.metrics_collector import snapshot, uptime_seconds

METRICS_FILE = "/opt/binarybot/metrics/runtime_metrics.json"


def _now():
    return int(time.time())


def write_metrics():
    """
    Writes current metrics snapshot to disk.
    """
    data = {
        "ts": _now(),
        "uptime": uptime_seconds(),
        "metrics": snapshot()
    }

    try:
        with open(METRICS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Metrics write error:", e)


def append_history():
    """
    Optional: append metrics history.
    """
    history_file = "/opt/binarybot/metrics/metrics_history.jsonl"

    data = {
        "ts": _now(),
        "uptime": uptime_seconds(),
        "metrics": snapshot()
    }

    try:
        with open(history_file, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print("Metrics history error:", e)