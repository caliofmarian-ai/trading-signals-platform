import os
import json
from typing import Optional, Dict, Any


REPORTS_DIR = "/opt/binarybot/analytics/reports"


def _safe_load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_reports():
    """
    Return all strategy audit report filenames sorted by date.
    """

    if not os.path.isdir(REPORTS_DIR):
        return []

    files = []

    for name in os.listdir(REPORTS_DIR):

        if name.startswith("daily_strategy_audit_") and name.endswith(".json"):
            files.append(name)

    files.sort()

    return files


def latest_report_path() -> Optional[str]:
    """
    Return full path to latest report.
    """

    reports = list_reports()

    if not reports:
        return None

    latest = reports[-1]

    return os.path.join(REPORTS_DIR, latest)


def load_latest_report() -> Optional[Dict[str, Any]]:
    """
    Load most recent strategy audit report.
    """

    path = latest_report_path()

    if not path:
        return None

    return _safe_load_json(path)


def load_report_by_date(date_str: str) -> Optional[Dict[str, Any]]:
    """
    Load report by YYYY-MM-DD.
    """

    filename = f"daily_strategy_audit_{date_str}.json"

    path = os.path.join(REPORTS_DIR, filename)

    return _safe_load_json(path)


def report_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metrics from report.
    """

    if not report:
        return {}

    return {
        "date": report.get("date"),
        "decisions": report.get("decisions"),
        "pre": report.get("pre"),
        "confirm": report.get("confirm"),
        "open_now": report.get("open_now"),
        "rejects": report.get("rejects"),
        "avg_score": report.get("avg_score"),
        "bottleneck": report.get("bottleneck"),
    }


def top_reject_reasons(report: Dict[str, Any], top_n: int = 5):
    """
    Return top reject reasons from report.
    """

    reasons = report.get("top_reject_reasons", {})

    if not isinstance(reasons, dict):
        return []

    items = sorted(reasons.items(), key=lambda kv: kv[1], reverse=True)

    return items[:top_n]


def symbol_health(report: Dict[str, Any]):
    """
    Extract symbol health section.
    """

    return report.get("symbol_health", {})


def heatmap(report: Dict[str, Any]):
    """
    Extract heatmap section.
    """

    return report.get("heatmap", {})