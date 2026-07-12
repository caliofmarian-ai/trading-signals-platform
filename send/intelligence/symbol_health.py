from collections import defaultdict


def extract_reject_reason(event):
    """
    Extract reject reason from decision event.
    """

    data = event.get("data", {})

    reason = data.get("reject_reason")
    if reason:
        return reason

    gates = data.get("gates", {})

    if isinstance(gates, dict):

        for gate_name, gate_data in gates.items():

            if not isinstance(gate_data, dict):
                continue

            r = gate_data.get("reason")
            if r:
                return r

            if gate_data.get("ok") is False:
                return gate_name

    return "UNKNOWN"


def build_symbol_index(decisions):
    """
    Group decision events by symbol.
    """

    symbols = defaultdict(list)

    for event in decisions:

        symbol = event.get("data", {}).get("symbol")

        if not symbol:
            continue

        symbols[symbol].append(event)

    return symbols


def compute_symbol_metrics(events):

    total = len(events)

    if total == 0:
        return None

    pre = 0
    confirm = 0
    open_now = 0

    reject_reasons = defaultdict(int)

    for e in events:

        data = e.get("data", {})
        kind = data.get("decision_kind")

        if kind == "PRE":
            pre += 1

        elif kind == "CONFIRM":
            confirm += 1

        elif kind == "OPEN_NOW":
            open_now += 1

        elif kind == "REJECT":

            reason = extract_reject_reason(e)
            reject_reasons[reason] += 1

    reject_total = sum(reject_reasons.values())

    dominant_reason = None
    dominant_share = 0

    if reject_total > 0:

        dominant_reason = max(reject_reasons, key=reject_reasons.get)
        dominant_share = reject_reasons[dominant_reason] / reject_total

    return {
        "total_decisions": total,
        "pre": pre,
        "confirm": confirm,
        "open_now": open_now,
        "reject_total": reject_total,
        "pre_rate": pre / total,
        "confirm_rate": confirm / total,
        "open_rate": open_now / total,
        "dominant_reject": dominant_reason,
        "dominant_reject_share": dominant_share,
        "reject_distribution": dict(reject_reasons),
    }


def classify_symbol_status(metrics, settings):

    healthy_pre = settings["symbol_health"]["healthy_pre_rate_min"]
    starved_pre = settings["symbol_health"]["starved_pre_rate_max"]
    blocked_share = settings["symbol_health"]["blocked_same_reason_share_min"]

    pre_rate = metrics["pre_rate"]
    dominant_share = metrics["dominant_reject_share"]

    if pre_rate >= healthy_pre:
        return "HEALTHY"

    if pre_rate < starved_pre:
        return "STARVED"

    if dominant_share >= blocked_share:
        return "BLOCKED"

    return "NORMAL"


def analyze_symbol_health(decisions, settings):
    """
    Full symbol health analysis.
    """

    index = build_symbol_index(decisions)

    results = {}

    for symbol, events in index.items():

        metrics = compute_symbol_metrics(events)

        if not metrics:
            continue

        status = classify_symbol_status(metrics, settings)

        results[symbol] = {
            "status": status,
            "metrics": metrics,
        }

    return results


def top_problematic_symbols(symbol_health, top_n=5):
    """
    Return symbols that are blocked or starved.
    """

    problems = []

    for symbol, data in symbol_health.items():

        status = data["status"]

        if status in ("BLOCKED", "STARVED"):

            metrics = data["metrics"]

            problems.append({
                "symbol": symbol,
                "status": status,
                "pre_rate": metrics["pre_rate"],
                "dominant_reject": metrics["dominant_reject"],
            })

    problems.sort(key=lambda x: x["pre_rate"])

    return problems[:top_n]