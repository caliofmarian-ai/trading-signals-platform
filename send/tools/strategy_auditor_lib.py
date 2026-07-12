import os
import json
import datetime
from collections import defaultdict


SETTINGS_PATH = "/opt/binarybot/config/intelligence_settings.json"


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        raise RuntimeError("Missing intelligence_settings.json")

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_jsonl(path):
    if not os.path.exists(path):
        return []

    out = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                obj = json.loads(line)
                out.append(obj)
            except Exception:
                continue

    return out


def load_all_events(settings):

    sources = settings["sources"]

    engine = _read_jsonl(sources["engine_events"])
    fsm = _read_jsonl(sources["fsm_events"])
    distribution = _read_jsonl(sources["distribution_events"])
    errors = _read_jsonl(sources["error_events"])

    outcomes = []
    if os.path.exists(sources["outcomes"]):
        outcomes = _read_jsonl(sources["outcomes"])

    return {
        "engine": engine,
        "fsm": fsm,
        "distribution": distribution,
        "errors": errors,
        "outcomes": outcomes,
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


def build_report(events, settings):

    decisions = filter_decision_events(events["engine"])

    decision_distribution = compute_decision_distribution(decisions)

    reject_distribution = compute_reject_distribution(decisions)

    symbol_activity = compute_symbol_activity(decisions)

    score_stats = compute_average_score(decisions)

    heatmap = compute_heatmap(decisions, settings)

    bottleneck = detect_bottleneck(reject_distribution, settings)

    symbol_health = compute_symbol_health(decisions, settings)

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    report = {
        "date": now,
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
    }

    return report


def write_reports(report, settings):

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
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if settings["reports"]["write_markdown"]:

        with open(md_path, "w", encoding="utf-8") as f:

            f.write("# Strategy Audit\n\n")

            f.write(f"Date: {report['date']}\n\n")

            f.write("## Decision Distribution\n\n")
            f.write(json.dumps({
                "PRE": report["pre"],
                "CONFIRM": report["confirm"],
                "OPEN_NOW": report["open_now"],
                "REJECT": report["rejects"],
            }, indent=2))

            f.write("\n\n## Top Reject Reasons\n\n")
            f.write(json.dumps(report["top_reject_reasons"], indent=2))

            f.write("\n\n## Heatmap\n\n")
            f.write(json.dumps(report["heatmap"], indent=2))

            f.write("\n\n## Bottleneck\n\n")
            f.write(json.dumps(report["bottleneck"], indent=2))

            f.write("\n\n## Symbol Health\n\n")
            f.write(json.dumps(report["symbol_health"], indent=2))