import os
import json
import datetime
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


# Default settings path is env-var overridable; no /opt/binarybot/ hard-requirement.
_DEFAULT_SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "intelligence_settings.json",
)
SETTINGS_PATH = os.getenv("STRATEGY_AUDITOR_SETTINGS", _DEFAULT_SETTINGS_PATH)


def load_settings(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load strategy auditor settings.

    Accepts an explicit path argument; falls back to STRATEGY_AUDITOR_SETTINGS
    env var; falls back to project-relative config/intelligence_settings.json.
    Raises RuntimeError clearly if the file is missing.
    """
    resolved = path or SETTINGS_PATH
    if not os.path.exists(resolved):
        raise RuntimeError(
            f"Strategy auditor settings file not found: {resolved}. "
            "Set STRATEGY_AUDITOR_SETTINGS env var to override the path."
        )
    with open(resolved, "r", encoding="utf-8") as f:
        settings = json.load(f)
    return _apply_runtime_path_overrides(settings)


def _apply_runtime_path_overrides(settings: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(settings, dict):
        raise RuntimeError("Strategy auditor settings must be a JSON object")

    normalized = dict(settings)
    analytics_dir = os.getenv("ANALYTICS_DIR", "").strip()
    obs_dir = os.getenv("OBS_DIR", "").strip()
    outcomes_log = os.getenv("OUTCOMES_LOG", "").strip()

    reports = dict(normalized.get("reports", {}) or {})
    if analytics_dir:
        reports["output_dir"] = os.path.join(analytics_dir, "reports")
        reports["cache_dir"] = os.path.join(analytics_dir, "cache")
    if reports:
        normalized["reports"] = reports

    sources = dict(normalized.get("sources", {}) or {})
    if obs_dir:
        sources["engine_events"] = os.getenv("ENGINE_EVENTS_LOG", os.path.join(obs_dir, "engine_events.jsonl"))
        sources["fsm_events"] = os.getenv("FSM_EVENTS_LOG", os.path.join(obs_dir, "fsm_events.jsonl"))
        sources["distribution_events"] = os.getenv("DIST_EVENTS_LOG", os.path.join(obs_dir, "distribution_events.jsonl"))
        sources["error_events"] = os.getenv("ERROR_EVENTS_LOG", os.path.join(obs_dir, "error_events.jsonl"))
    if outcomes_log:
        sources["outcomes"] = outcomes_log
    if sources:
        normalized["sources"] = sources

    return normalized


def _read_jsonl(path: str) -> Tuple[List[Dict[str, Any]], int]:
    """
    Read a JSONL file and return (valid_records, invalid_count).

    Invalid lines are counted and reported, not silently dropped.
    Missing files return ([], 0) without error.
    """
    if not os.path.exists(path):
        return [], 0

    records: List[Dict[str, Any]] = []
    invalid_count = 0

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    invalid_count += 1
                    continue
                records.append(obj)
            except json.JSONDecodeError:
                invalid_count += 1

    return records, invalid_count


def load_all_events(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load all event sources defined in settings["sources"].

    Returns the event collections plus per-source invalid record counts.
    """
    sources = settings["sources"]

    engine_records, engine_invalid = _read_jsonl(sources["engine_events"])
    fsm_records, fsm_invalid = _read_jsonl(sources["fsm_events"])
    distribution_records, distribution_invalid = _read_jsonl(sources["distribution_events"])
    error_records, error_invalid = _read_jsonl(sources["error_events"])

    outcomes: List[Dict[str, Any]] = []
    outcomes_invalid = 0
    if os.path.exists(sources["outcomes"]):
        outcomes, outcomes_invalid = _read_jsonl(sources["outcomes"])

    return {
        "engine": engine_records,
        "fsm": fsm_records,
        "distribution": distribution_records,
        "errors": error_records,
        "outcomes": outcomes,
        "invalid_counts": {
            "engine": engine_invalid,
            "fsm": fsm_invalid,
            "distribution": distribution_invalid,
            "errors": error_invalid,
            "outcomes": outcomes_invalid,
        },
    }


def filter_decision_events(engine_events):

    out = []

    for e in engine_events:
        if e.get("event_type") == "decision":
            out.append(e)

    return out


def extract_reject_reason(event):

    data = event.get("data", {})

    reason = data.get("reject_reason")

    if reason:
        return reason

    gates = data.get("gates", {})

    sr = gates.get("sr_gate")

    if isinstance(sr, dict):
        return sr.get("reason")

    return "UNKNOWN"


def compute_decision_distribution(decisions):

    stats = {
        "total": 0,
        "PRE": 0,
        "CONFIRM": 0,
        "OPEN_NOW": 0,
        "REJECT": 0,
    }

    for d in decisions:

        stats["total"] += 1

        kind = d.get("data", {}).get("decision_kind")

        if kind in stats:
            stats[kind] += 1

    return stats


def compute_reject_distribution(decisions):

    reasons = defaultdict(int)

    for d in decisions:

        kind = d.get("data", {}).get("decision_kind")

        if kind != "REJECT":
            continue

        r = extract_reject_reason(d)

        reasons[r] += 1

    return dict(reasons)


def compute_symbol_activity(decisions):

    symbols = defaultdict(int)

    for d in decisions:

        symbol = d.get("data", {}).get("symbol")

        if not symbol:
            continue

        symbols[symbol] += 1

    return dict(symbols)


def compute_average_score(decisions):

    scores = []

    for d in decisions:

        score = d.get("data", {}).get("score_total")

        if score is None:
            continue

        try:
            scores.append(float(score))
        except Exception:
            continue

    if not scores:
        return {
            "avg": None,
            "min": None,
            "max": None,
        }

    return {
        "avg": sum(scores) / len(scores),
        "min": min(scores),
        "max": max(scores),
    }


def compute_heatmap(decisions, settings):

    buckets = settings["heatmap"]["score_buckets"]

    heatmap = {}

    for b in buckets:

        label = f"{b[0]}-{b[1]}"

        heatmap[label] = {
            "count": 0,
            "rejects": 0,
            "opens": 0,
        }

    for d in decisions:

        score = d.get("data", {}).get("score_total")

        if score is None:
            continue

        try:
            score = float(score)
        except Exception:
            continue

        for b in buckets:

            if b[0] <= score < b[1]:

                label = f"{b[0]}-{b[1]}"

                heatmap[label]["count"] += 1

                kind = d.get("data", {}).get("decision_kind")

                if kind == "REJECT":
                    heatmap[label]["rejects"] += 1

                if kind == "OPEN_NOW":
                    heatmap[label]["opens"] += 1

                break

    return heatmap


def detect_bottleneck(reject_distribution, settings):

    if not reject_distribution:
        return None

    total = sum(reject_distribution.values())

    if total == 0:
        return None

    dominant = max(reject_distribution, key=reject_distribution.get)

    share = reject_distribution[dominant] / total

    threshold = settings["bottleneck_detection"]["dominant_reject_share_threshold"]

    if share >= threshold:
        return {
            "reason": dominant,
            "share": share,
        }

    return None


def compute_symbol_health(decisions, settings):

    per_symbol = defaultdict(list)

    for d in decisions:

        symbol = d.get("data", {}).get("symbol")

        if not symbol:
            continue

        per_symbol[symbol].append(d)

    result = {}

    healthy_min = settings["symbol_health"]["healthy_pre_rate_min"]
    starved_max = settings["symbol_health"]["starved_pre_rate_max"]
    blocked_share = settings["symbol_health"]["blocked_same_reason_share_min"]

    for sym, arr in per_symbol.items():

        total = len(arr)

        if total == 0:
            continue

        pre = 0
        rejects = defaultdict(int)

        for d in arr:

            kind = d.get("data", {}).get("decision_kind")

            if kind == "PRE":
                pre += 1

            if kind == "REJECT":
                r = extract_reject_reason(d)
                rejects[r] += 1

        pre_rate = pre / total

        dominant_reason = None
        dominant_share = 0

        if rejects:

            dominant_reason = max(rejects, key=rejects.get)
            dominant_share = rejects[dominant_reason] / sum(rejects.values())

        status = "NORMAL"

        if pre_rate < starved_max:
            status = "STARVED"

        if dominant_share >= blocked_share:
            status = "BLOCKED"

        if pre_rate >= healthy_min:
            status = "HEALTHY"

        result[sym] = {
            "total": total,
            "pre_rate": pre_rate,
            "dominant_reject": dominant_reason,
            "dominant_reject_share": dominant_share,
            "status": status,
        }

    return result


def build_report(events: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the daily strategy audit report from loaded events.

    The report includes:
    - input_sources: number of valid and invalid records per source
    - period: the UTC date analyzed
    - findings derived only from valid, deduplicated decision events
    - Does not mutate runtime config or live strategy parameters.
    """
    decisions = filter_decision_events(events["engine"])

    decision_distribution = compute_decision_distribution(decisions)

    reject_distribution = compute_reject_distribution(decisions)

    symbol_activity = compute_symbol_activity(decisions)

    score_stats = compute_average_score(decisions)

    heatmap = compute_heatmap(decisions, settings)

    bottleneck = detect_bottleneck(reject_distribution, settings)

    symbol_health = compute_symbol_health(decisions, settings)

    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    invalid_counts = events.get("invalid_counts", {})

    report: Dict[str, Any] = {
        "date": now,
        "input_sources": {
            "engine_events": {
                "valid": len(events.get("engine", [])),
                "invalid": invalid_counts.get("engine", 0),
            },
            "fsm_events": {
                "valid": len(events.get("fsm", [])),
                "invalid": invalid_counts.get("fsm", 0),
            },
            "distribution_events": {
                "valid": len(events.get("distribution", [])),
                "invalid": invalid_counts.get("distribution", 0),
            },
            "error_events": {
                "valid": len(events.get("errors", [])),
                "invalid": invalid_counts.get("errors", 0),
            },
            "outcomes": {
                "valid": len(events.get("outcomes", [])),
                "invalid": invalid_counts.get("outcomes", 0),
            },
        },
        "decisions": decision_distribution["total"],
        "pre": decision_distribution["PRE"],
        "confirm": decision_distribution["CONFIRM"],
        "open_now": decision_distribution["OPEN_NOW"],
        "rejects": decision_distribution["REJECT"],
        "avg_score": score_stats["avg"],
        "min_score": score_stats["min"],
        "max_score": score_stats["max"],
        "top_reject_reasons": reject_distribution,
        "symbol_activity": symbol_activity,
        "heatmap": heatmap,
        "bottleneck": bottleneck,
        "symbol_health": symbol_health,
        "limitations": [] if decision_distribution["total"] > 0 else [
            "No decision events found in engine log."
        ],
    }

    return report


def write_reports(report: Dict[str, Any], settings: Dict[str, Any]) -> None:
    """
    Write report outputs atomically.

    - JSON report: written atomically via tempfile + os.replace to prevent
      partial overwrites. Failed write preserves the last valid report.
    - Markdown report: written atomically in the same manner.
    - Does not mutate runtime config or live strategy parameters.
    """
    import tempfile

    output_dir = settings["reports"]["output_dir"]

    os.makedirs(output_dir, exist_ok=True)

    date = report["date"]

    json_path = os.path.join(
        output_dir,
        f"daily_strategy_audit_{date}.json",
    )

    md_path = os.path.join(
        output_dir,
        f"daily_strategy_audit_{date}.md",
    )

    if settings["reports"]["write_json"]:
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=output_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, json_path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    if settings["reports"]["write_markdown"]:
        content_parts = [
            "# Strategy Audit\n\n",
            f"Date: {report['date']}\n\n",
            "## Decision Distribution\n\n",
            json.dumps({
                "PRE": report["pre"],
                "CONFIRM": report["confirm"],
                "OPEN_NOW": report["open_now"],
                "REJECT": report["rejects"],
            }, indent=2),
            "\n\n## Top Reject Reasons\n\n",
            json.dumps(report["top_reject_reasons"], indent=2),
            "\n\n## Heatmap\n\n",
            json.dumps(report["heatmap"], indent=2),
            "\n\n## Bottleneck\n\n",
            json.dumps(report["bottleneck"], indent=2),
            "\n\n## Symbol Health\n\n",
            json.dumps(report["symbol_health"], indent=2),
        ]
        content = "".join(content_parts)

        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".md", dir=output_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, md_path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass