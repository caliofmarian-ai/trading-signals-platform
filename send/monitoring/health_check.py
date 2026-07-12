# /opt/binarybot/monitoring/health_check.py
# BinaryBot — Health Check Monitor

import time
import os

from metrics.metrics_collector import uptime_seconds, snapshot

HEALTH_FILE = "/opt/binarybot/monitoring/health_status.json"


def _now():
    return int(time.time())


def health_status():
    """
    Returns basic health information about the bot.
    """
    metrics = snapshot()

    status = {
        "ts": _now(),
        "uptime": uptime_seconds(),
        "signals_generated": metrics.get("signals_generated", 0),
        "trades_opened": metrics.get("trades_opened", 0),
        "errors": metrics.get("errors", 0)
    }

    return status


def write_health_file():
    """
    Writes health status to disk.
    """
    import json

    status = health_status()

    try:
        with open(HEALTH_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        print("Health check write error:", e)


def is_healthy():
    """
    Simple health validation.
    """
    status = health_status()

    # bot considerat sănătos dacă nu are erori excesive
    if status["errors"] > 50:
        return False

    return True