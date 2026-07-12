from collections import defaultdict


def extract_reject_reason(event):
    """
    Extract the most relevant reject reason from a decision event.
    """

    data = event.get("data", {})

    direct_reason = data.get("reject_reason")
    if direct_reason:
        return str(direct_reason)

    gates = data.get("gates", {})
    if not isinstance(gates, dict):
        return "UNKNOWN"

    for gate_name, gate_payload in gates.items():
        if not isinstance(gate_payload, dict):
            continue

        reason = gate_payload.get("reason")
        if reason:
            return str(reason)

        if gate_payload.get("ok") is False:
            return str(gate_name)

    return "UNKNOWN"


def classify_reject_reason(reason):
    """
    Map raw reject reasons into canonical diagnostic classes.
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

    if "WATCHLIST" in r or "FOCUS" in r or "COOLDOWN" in r:
        return "FOCUS_CAPACITY"

    if "CHANNEL" in r or "DUPLICATE" in r or "TIER" in r:
        return "DISTRIBUTION"

    return "UNKNOWN"


def diagnose_single_decision(event):
    """
    Produce a detailed diagnostic view for one decision event.
    """

    data = event.get("data", {})
    debug = data.get("debug", {}) if isinstance(data.get("debug"), dict) else {}
    gates = data.get("gates", {}) if isinstance(data.get("gates"), dict) else {}

    reject_reason = extract_reject_reason(event)
    reject_class = classify_reject_reason(reject_reason)

    diagnostics = {
        "symbol": data.get("symbol"),
        "decision_kind": data.get("decision_kind"),
        "score_total": data.get("score_total"),
        "reject_reason": reject_reason,
        "reject_class": reject_class,
        "timeframe": debug.get("tf"),
        "trend": debug.get("trend_class"),
        "gates": gates,
        "raw_debug": debug,
    }

    # Optional convenience extraction for common gates.
    sr_gate = gates.get("sr_gate", {}) if isinstance(gates.get("sr_gate"), dict) else {}
    spike_gate = gates.get("spike_filter", {}) if isinstance(gates.get("spike_filter"), dict) else {}
    feasibility_gate = gates.get("feasibility", {}) if isinstance(gates.get("feasibility"), dict) else {}

    diagnostics["sr_gate"] = sr_gate
    diagnostics["spike_gate"] = spike_gate
    diagnostics["feasibility_gate"] = feasibility_gate

    return diagnostics


def build_diagnostic_distribution(decisions):
    """
    Aggregate diagnostics across all decisions.
    """

    by_reason = defaultdict(int)
    by_class = defaultdict(int)
    by_kind = defaultdict(int)

    for event in decisions:
        data = event.get("data", {})
        kind = data.get("decision_kind", "UNKNOWN")
        by_kind[kind] += 1

        if kind == "REJECT":
            reason = extract_reject_reason(event)
            cls = classify_reject_reason(reason)
            by_reason[reason] += 1
            by_class[cls] += 1

    return {
        "by_reason": dict(by_reason),
        "by_class": dict(by_class),
        "by_kind": dict(by_kind),
    }


def explain_strategy_blockers(decisions):
    """
    Return high-level explanations for dominant blockers.
    """

    distribution = build_diagnostic_distribution(decisions)
    by_class = distribution["by_class"]

    explanations = []

    for cls, count in sorted(by_class.items(), key=lambda kv: kv[1], reverse=True):
        if cls == "STRUCTURE_SR":
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Support/resistance structure is blocking many candidate signals."
            })
        elif cls == "SPIKE":
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Spike detection is filtering unstable market conditions."
            })
        elif cls == "FEASIBILITY":
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Feasibility constraints are preventing signal progression."
            })
        elif cls == "TREND":
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Trend alignment is rejecting setups outside current directional rules."
            })
        elif cls == "SCORE":
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Score thresholds are preventing setups from advancing."
            })
        elif cls == "FOCUS_CAPACITY":
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Focus/watchlist capacity is restricting signal progression."
            })
        elif cls == "DISTRIBUTION":
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Distribution constraints are suppressing signals after evaluation."
            })
        else:
            explanations.append({
                "class": cls,
                "count": count,
                "message": "Unknown blocker category detected and requires manual review."
            })

    return explanations


def latest_signal_diagnostic(decisions):
    """
    Return diagnostic payload for the latest decision event.
    """

    if not decisions:
        return None

    latest = decisions[-1]
    return diagnose_single_decision(latest)


def diagnostics_summary(decisions):
    """
    Full summary payload used by reports or Telegram debug views.
    """

    return {
        "latest": latest_signal_diagnostic(decisions),
        "distribution": build_diagnostic_distribution(decisions),
        "blockers": explain_strategy_blockers(decisions),
    }