"""Reconciled delivery summaries, never strategy or calibration authority.

Only API-accepted published-study counts are consumed. Research observations,
missing fields and absent policy cohorts cannot become replacement outcomes.
"""
from __future__ import annotations

from collections.abc import Mapping


_OUTCOMES = ("wins", "losses", "draws", "unknown")
_MAX_COUNT = 1_000_000_000
_UNAVAILABLE = "Rezultate studiu: statistici indisponibile."


def _count(value):
    if type(value) is not int or not 0 <= value <= _MAX_COUNT:
        raise ValueError("INVALID_STUDY_SUMMARY_COUNT")
    return value


def _counts(row):
    if not isinstance(row, Mapping):
        raise ValueError("PUBLISHED_STUDY_COUNTS_REQUIRED")
    result = {key: _count(row.get(key)) for key in _OUTCOMES}
    if "decisive" in row and _count(row["decisive"]) != result["wins"] + result["losses"]:
        raise ValueError("INCONSISTENT_DECISIVE_COUNT")
    return result


def _line(name, counts):
    total = sum(counts.values())
    return (f"{name} · {total} rezultate: WIN {counts['wins']}, LOSS {counts['losses']}, "
            f"DRAW {counts['draws']}, UNKNOWN {counts['unknown']}")


def _quote_details(row, counts, *, explicit_missing=False):
    total = sum(counts.values())
    observed = total - counts["unknown"]
    lines = [f"Cotație la expirare: {observed}/{total}; fără rezultat observat: {counts['unknown']}."]
    if total == 0:
        lines = ["Cotație la expirare: fără rezultate publicate încă."]
    # UNKNOWN may have several causes. Never call all of it missing expiry
    # quotes unless that reason is actually supplied by the source summary.
    reasons = row.get("unknown_reasons")
    if isinstance(reasons, Mapping):
        try:
            values = {key: _count(value) for key, value in reasons.items()}
            if sum(values.values()) != counts["unknown"]:
                raise ValueError("INCONSISTENT_UNKNOWN_REASONS")
            missing = values.get("EXPIRY_OBSERVATION_MISSING", 0)
            if missing or explicit_missing:
                lines.append(f"Fără cotație în fereastra expirării: {missing}.")
            if explicit_missing and counts["unknown"] > missing:
                lines.append(f"UNKNOWN din alte cauze: {counts['unknown'] - missing}.")
        except ValueError:
            lines.append("Cauzele UNKNOWN: statistici neconcordante.")
    elif explicit_missing:
        lines.append("Lipsa cotației la expirare: statistici indisponibile.")
    return lines


def _details(row, counts, *, explicit_missing=False):
    total = sum(counts.values())
    lines = _quote_details(row, counts, explicit_missing=explicit_missing)
    try:
        met, not_met, unavailable = (_count(row.get(key)) for key in
                                    ("buffer_met", "buffer_not_met", "buffer_unavailable"))
        if met + not_met + unavailable != total or met > counts["wins"]:
            raise ValueError("INCONSISTENT_BUFFER_COUNTS")
        if unavailable < counts["unknown"]:
            raise ValueError("BUFFER_WITHOUT_EXPIRY_OBSERVATION")
        lines.append(f"Marjă completă la expirare: DA {met}, NU {not_met}, indisponibilă {unavailable}")
        fragile = _count(row.get("win_buffer_not_met"))
        if fragile > counts["wins"] - met or fragile > not_met:
            raise ValueError("INCONSISTENT_FRAGILE_WIN_COUNT")
        lines.append(f"WIN fragil (în buffer): {fragile}")
    except ValueError:
        # A malformed optional metric does not erase valid outcome counts.
        lines.append("Marja bufferului: statistici indisponibile sau neconcordante.")
    return lines


def _reconciled_cohorts(cohorts, identities, counts):
    if not isinstance(cohorts, Mapping) or not cohorts:
        raise ValueError("POLICY_COHORTS_REQUIRED")
    if (any(type(policy) is not str or not policy for policy in identities)
            or len(set(identities)) != len(identities)):
        raise ValueError("POLICY_IDENTITIES_REQUIRED")
    # Never discard a future policy family, expose arbitrary labels or accept
    # equal row totals whose WIN/LOSS/DRAW/UNKNOWN columns disagree.
    if set(cohorts) - set(identities):
        raise ValueError("UNKNOWN_POLICY_FAMILY")
    by_policy = {policy: _counts(row) for policy, row in cohorts.items()}
    if any(sum(row[key] for row in by_policy.values()) != counts[key] for key in _OUTCOMES):
        raise ValueError("COHORT_OUTCOME_TOTAL_MISMATCH")
    return by_policy


def _recovery_lines(observed, counts, recovery_policy, legacy_recovery_policy):
    labels = ((recovery_policy, "Politica nouă de cotații"),
              (legacy_recovery_policy, "Istoric · politica anterioară de cotații"))
    cohorts = observed.get("published_study_results_by_quote_recovery_policy")
    try:
        by_policy = _reconciled_cohorts(cohorts, (recovery_policy, legacy_recovery_policy), counts)
    except (TypeError, ValueError):
        return [f"{label}: statistici indisponibile." for _, label in labels] + [
            "Grupele de cotații: sursă absentă sau neconcordantă."]
    lines = []
    for policy, label in labels:
        if policy not in by_policy:
            # An absent family is not evidence for an explicit zero cohort.
            lines.append(f"{label}: statistici indisponibile.")
            continue
        lines.append(_line(label, by_policy[policy]))
        details = _details if policy == recovery_policy else _quote_details
        lines.extend(details(cohorts[policy], by_policy[policy], explicit_missing=True))
    return lines


def _estimate_lines(observed, counts):
    """An estimate partitions missing results; it never increases observed WIN."""
    row = observed.get("published_study_expiry_estimates")
    if row is None:
        return []
    try:
        if (not isinstance(row, Mapping)
                or row.get("contract") != "ADJACENT_SOURCE_QUOTES_ESTIMATE_V1"):
            raise ValueError("ESTIMATE_SUMMARY_CONTRACT_REQUIRED")
        eligible = _count(row.get("eligible_unknown"))
        values = {key: _count(row.get(key)) for key in
                  ("estimated_wins", "estimated_losses", "inconclusive", "unavailable")}
        available = _count(row.get("estimates_available"))
        if (eligible > counts["unknown"] or sum(values.values()) != eligible
                or available != eligible - values["unavailable"]):
            raise ValueError("INCONSISTENT_ESTIMATE_COUNTS")
    except (TypeError, ValueError):
        return ["Estimări din cotații vecine: statistici indisponibile sau neconcordante."]
    return [(f"Dintre {eligible} UNKNOWN eligibile: WIN estimat {values['estimated_wins']}, "
             f"LOSS estimat {values['estimated_losses']}, neconcludente {values['inconclusive']}, "
             f"fără estimare {values['unavailable']}."),
            "Estimările sunt separate; nu intră în rata WIN verificată."]


def render_published_study_progress(observed, *, active_policy, legacy_policy, legacy_open_policy,
                                    recovery_policy=None, legacy_recovery_policy=None):
    """Separate quote-recovery history before showing duration groupings.

    Each policy grouping independently reconciles to the same published total;
    the two groupings must never be added together. Policy families are supplied
    by their authoritative modules, not inferred from dates or outcome counts.
    No win percentage is inferred from a subset that drops UNKNOWN or DRAW.
    Missing source evidence is unavailable, never silently replaced with zero.
    """
    if not isinstance(observed, Mapping):
        return _UNAVAILABLE
    lines = []
    for key, title in (("study_open_now_api_accepted", "OPEN_NOW · STUDIU"),
                       ("study_results_api_accepted", "rezultate")):
        try:
            value = str(_count(observed.get(key)))
        except ValueError:
            value = "indisponibile"
        lines.append(f"{title}: {value}")
    header = "; ".join(lines)
    try:
        counts = _counts(observed.get("published_study_results"))
        results = _count(observed.get("study_results_api_accepted"))
        if sum(counts.values()) != results:
            raise ValueError("PUBLISHED_OUTCOME_TOTAL_MISMATCH")
        if "study_open_now_api_accepted" in observed:
            if results > _count(observed["study_open_now_api_accepted"]):
                raise ValueError("MORE_RESULTS_THAN_ENTRIES")
    except ValueError:
        return header + "\n" + _UNAVAILABLE

    lines = [header, *_estimate_lines(observed, counts),
             *_recovery_lines(observed, counts, recovery_policy, legacy_recovery_policy),
             "Aceleași rezultate, grupate după durată (nu se adună cu grupele de cotații):"]
    cohorts = observed.get("published_study_results_by_duration_policy")
    if not isinstance(cohorts, Mapping) or not cohorts:
        return "\n".join([*lines, "La secundă: statistici indisponibile.",
                          _line("Total istoric", counts),
                          *_details(observed["published_study_results"], counts)])
    try:
        by_policy = _reconciled_cohorts(cohorts, (active_policy, legacy_policy, legacy_open_policy), counts)
    except (TypeError, ValueError):
        return "\n".join([*lines, "Grupele de durată: statistici neconcordante.",
                          _line("Total istoric", counts)])

    if active_policy in by_policy:
        lines.append(_line("La secundă", by_policy[active_policy]))
        lines.extend(_details(cohorts[active_policy], by_policy[active_policy]))
    else:
        lines.append("La secundă: statistici indisponibile.")
    for policy, label in ((legacy_policy, "Istoric · minute întregi"),
                          (legacy_open_policy, "Istoric · OPEN")):
        if policy in by_policy:
            lines.append(_line(label, by_policy[policy]))
    lines.append(_line("Total istoric", counts))
    return "\n".join(lines)
