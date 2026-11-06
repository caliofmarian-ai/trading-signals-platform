"""Descriptive 10-minute sequences, including overlaps; never entry selection."""
from collections import defaultdict

WINDOW_SECONDS = 600


def summarize(records):
    eligible = sorted((r for r in records if r.get("decision_snapshot") and r.get("entry")),
                      key=lambda r: (r["entry"]["observed_ts"], r["created_ts"]))
    groups, active = [], {}
    for row in eligible:
        symbol = row["entry"]["symbol"]
        stamp = row["entry"]["observed_ts"]
        group = active.get(symbol)
        if group is None or stamp - group[0]["entry"]["observed_ts"] >= WINDOW_SECONDS:
            group = []
            active[symbol] = group
            groups.append(group)
        group.append(row)
    by_position = defaultdict(list)
    known_loss_before_next = []
    overlapping_pairs = 0
    for group in groups:
        for position, row in enumerate(group, 1):
            by_position[position].append(row)
            if position > 1:
                previous = group[position - 2]
                candidate = previous["candidates"][0]
                target = previous["entry"]["observed_ts"] + candidate["horizon_seconds"]
                if target > row["entry"]["observed_ts"]:
                    overlapping_pairs += 1
                if (candidate["outcome"] == "LOSS" and candidate.get("quote")
                    and candidate["quote"]["observed_ts"] <= row["entry"]["observed_ts"]):
                    known_loss_before_next.append(row)

    def counts(rows):
        outcomes = [r["candidates"][0]["outcome"] for r in rows]
        wins, losses = outcomes.count("WIN"), outcomes.count("LOSS")
        return {"entries": len(rows), "wins": wins, "losses": losses,
                "draws": outcomes.count("DRAW"), "unknown": outcomes.count("UNKNOWN"),
                "pending": outcomes.count("PENDING"), "infeasible": outcomes.count("INFEASIBLE"),
                "decisive": wins + losses,
                "observed_win_rate": wins / (wins + losses) if wins + losses else None}

    return {"protocol": "SAME_SYMBOL_FIXED_10MIN_OBSERVATION_V1", "window_seconds": WINDOW_SECONDS,
            "rate_truth_domain": "DIRECTION_AT_PREDECLARED_MODEL_EXPIRY",
            "buffer_measurements_separate": True,
            "grouping": "FIXED_FROM_FIRST_OBSERVED_ENTRY_PER_SYMBOL",
            "groups": len(groups), "eligible_entries": len(eligible),
            "positions": [{"position": p, **counts(rows)} for p, rows in sorted(by_position.items())],
            "after_already_observed_loss": counts(known_loss_before_next),
            "overlapping_adjacent_pairs": overlapping_pairs,
            "overlaps_are_independent": False, "predictive_probability_proven": False,
            "changes_strategy_or_calibration": False, "broker_executed": False}
