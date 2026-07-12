from collections import defaultdict


def extract_reject_reason(decision_event):
    """
    Extract canonical reject reason from a decision event.
    """

    data = decision_event.get("data", {})

    direct = data.get("reject_reason")
    if direct:
        return str(direct)

    gates = data.get("gates", {})

    if not isinstance(gates, dict):
        return "UNKNOWN"

    for gate_name, gate_payload in gates.items():
        if not isinstance(gate_payload, dict):
            continue

        reason = gate_payload.get("reason")
        if reason:
            return str(reason)

        ok = gate_payload.get("ok")
        if ok is False:
            return str(gate_name)

    return "UNKNOWN"


def compute_reject_reason_distribution(decisions):
    """
    Build reject reason frequency map from decision events.
    """

    dist = defaultdict(int)

    for event in decisions:

        data = event.get("data", {})
        kind = data.get("decision_kind")

        if kind != "REJECT":
            continue

        reason = extract_reject_reason(event)
        dist[reason] += 1

    return dict(dist)


def detect_primary_bottleneck(reject_distribution, dominant_threshold=0.60):
    """
    Detect if one reject reason dominates the pipeline.

    Returns:
    {
        "detected": bool,
        "reason": str|None,
        "share": float,
        "count": int,
        "total_rejects": int
    }
    """

    if not reject_distribution:
        return {
            "detected": False,
            "reason": None,
            "share": 0.0,
            "count": 0,
            "total_rejects": 0,
        }

    total = sum(reject_distribution.values())
    if total == 0:
        return {
            "detected": False,
            "reason": None,
            "share": 0.0,
            "count": 0,
            "total_rejects": 0,
        }

    reason = max(reject_distribution, key=reject_distribution.get)
    count = reject_distribution[reason]
    share = count / total

    return {
        "detected": share >= dominant_threshold,
        "reason": reason,
        "share": share,
        "count": count,
        "total_rejects": total,
    }


def classify_bottleneck_reason(reason):
    """
    Group raw reasons into higher-level bottleneck classes.
    """

    if not reason:
        return "UNKNOWN"

    r = str(reason).upper()

    if "SR" in r or "SUPPORT" in r or "RESISTANCE" in r:
        return "STRUCTURE_SR"

    if "SPIKE" in r or "WICK" in r or "ATR" in r:
        return "SPIKE"

    if "FEASIBILITY" in r or "EXPIRY" in r or "SPEED" in r:
        return "FEASIBILITY"

    if "TREND" in r:
        return "TREND"

    if "SCORE" in r or "THRESHOLD" in r:
        return "SCORE"

    if "FOCUS" in r or "WATCHLIST" in r or "COOLDOWN" in r:
        return "FOCUS_CAPACITY"

    if "DUPLICATE" in r or "TIER" in r or "CHANNEL" in r:
        return "DISTRIBUTION"

    return "UNKNOWN"


def build_bottleneck_report(decisions, dominant_threshold=0.60):
    """
    Full bottleneck report from raw decisions.
    """

    reject_distribution = compute_reject_reason_distribution(decisions)
    primary = detect_primary_bottleneck(
        reject_distribution,
        dominant_threshold=dominant_threshold,
    )

    category = classify_bottleneck_reason(primary["reason"])

    recommendation = None
    if primary["detected"]:
        if category == "STRUCTURE_SR":
            recommendation = "Review SR buffer logic before changing thresholds."
        elif category == "SPIKE":
            recommendation = "Review spike filter sensitivity before loosening score thresholds."
        elif category == "FEASIBILITY":
            recommendation = "Review expiry and feasibility assumptions."
        elif category == "TREND":
            recommendation = "Review trend filter aggressiveness."
        elif category == "SCORE":
            recommendation = "Review score thresholds and score balance."
        elif category == "FOCUS_CAPACITY":
            recommendation = "Review watchlist capacity and focus gating."
        elif category == "DISTRIBUTION":
            recommendation = "Review distribution limits and duplicate suppression."
        else:
            recommendation = "Review dominant reject reason manually."

    return {
        "reject_distribution": reject_distribution,
        "primary_bottleneck": primary,
        "bottleneck_category": category,
        "recommendation": recommendation,
    }


def top_reject_reasons(reject_distribution, top_n=5):
    """
    Return sorted top reject reasons.
    """

    items = sorted(
        reject_distribution.items(),
        key=lambda kv: kv[1],
        reverse=True,
    )
    return items[:top_n]