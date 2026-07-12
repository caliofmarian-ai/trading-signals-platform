from collections import defaultdict


def build_score_heatmap(decisions, score_buckets):
    """
    Build heatmap for score distribution vs outcomes.

    decisions: list of decision events
    score_buckets: [[min,max], [min,max]...]

    return structure:

    {
        "50-55": {count,rejects,opens,confirms},
        "55-60": {...}
    }
    """

    heatmap = {}

    for b in score_buckets:

        label = f"{b[0]}-{b[1]}"

        heatmap[label] = {
            "count": 0,
            "rejects": 0,
            "opens": 0,
            "confirms": 0,
        }

    for d in decisions:

        data = d.get("data", {})

        score = data.get("score_total")

        if score is None:
            continue

        try:
            score = float(score)
        except Exception:
            continue

        kind = data.get("decision_kind")

        for b in score_buckets:

            if b[0] <= score < b[1]:

                label = f"{b[0]}-{b[1]}"

                heatmap[label]["count"] += 1

                if kind == "REJECT":
                    heatmap[label]["rejects"] += 1

                if kind == "OPEN_NOW":
                    heatmap[label]["opens"] += 1

                if kind == "CONFIRM":
                    heatmap[label]["confirms"] += 1

                break

    return heatmap


def heatmap_success_rate(heatmap):
    """
    Compute open success ratio per bucket.
    """

    result = {}

    for k, v in heatmap.items():

        count = v["count"]

        if count == 0:

            result[k] = {
                "open_rate": None,
                "reject_rate": None,
            }

            continue

        result[k] = {
            "open_rate": v["opens"] / count,
            "reject_rate": v["rejects"] / count,
        }

    return result


def detect_score_threshold_candidates(heatmap):
    """
    Suggest potential thresholds for PRE / CONFIRM / OPEN.

    Example logic:
    choose bucket where open_rate begins to dominate.
    """

    candidates = []

    for bucket, data in heatmap.items():

        count = data["count"]

        if count < 10:
            continue

        open_rate = data["opens"] / count

        if open_rate >= 0.5:
            candidates.append(bucket)

    return candidates


def heatmap_summary(heatmap):

    summary = {}

    for bucket, data in heatmap.items():

        count = data["count"]

        if count == 0:

            summary[bucket] = {
                "status": "NO_DATA"
            }

            continue

        open_rate = data["opens"] / count
        reject_rate = data["rejects"] / count

        if open_rate > 0.6:
            status = "HIGH_SIGNAL_ZONE"

        elif reject_rate > 0.8:
            status = "REJECT_ZONE"

        else:
            status = "NEUTRAL"

        summary[bucket] = {
            "count": count,
            "open_rate": open_rate,
            "reject_rate": reject_rate,
            "status": status,
        }

    return summary