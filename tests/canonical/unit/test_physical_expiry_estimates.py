"""Synthetic adjacent evidence only; never verified expiry or strategy efficacy."""
import copy
import importlib

import pytest

from tests.canonical.unit.test_physical_study_delivery import (
    BASE, _capture, _sample, study_setup,
)


def _row(study):
    return next(iter(study._read(study._path())["records"].values()))


def _unknown(setup):
    _, study, _, _, _, _, messages, clock = setup
    _capture(setup)
    entry_ts = BASE + 32
    study.advance(now_ts=entry_ts, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(entry_ts, 1.1))
    target = entry_ts + study.displayed_study_observation(_row(study))["horizon_seconds"]
    clock[0] = target + 18.1
    study.advance(now_ts=target + 18, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: None)
    assert _row(study)["study_observation"]["outcome"] == "UNKNOWN"
    # The exact baseline is already frozen, but result publication waits for
    # a complete estimate or the original bounded presentation deadline.
    assert len(messages) == 1
    assert _row(study)["study_delivery"]["result"] is None
    return study, target


def _bracket(row, target, *, outcome="WIN"):
    sign = 1 if row["direction"] == "BUY" else -1
    if outcome == "LOSS":
        sign = -sign
    before = _sample(target - 5, 1.1 + sign * .0002, buffered=True)
    after = _sample(target + 8, 1.1 + sign * .0003, buffered=True)
    if outcome == "INCONCLUSIVE":
        after["price"] = 1.1 - sign * .0003
    return {"before": before, "after": after}


@pytest.mark.parametrize("estimate_outcome", ["WIN", "LOSS", "INCONCLUSIVE"])
def test_persisted_estimate_never_changes_official_result_or_resends(study_setup, estimate_outcome, capsys):
    study, target = _unknown(study_setup)
    original = copy.deepcopy(_row(study))
    report_before = study.summary(now_ts=target + 18)
    brackets = []
    def load(symbol, expiry, *, max_side_seconds):
        assert symbol == "EUR/USD" and expiry == target and max_side_seconds == 60
        brackets.append(expiry)
        return _bracket(original, target, outcome=estimate_outcome)

    capsys.readouterr()
    study_setup[7][0] = target + 30.1
    study.advance(now_ts=target + 30, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: None, bracket_loader=load)
    enriched = _row(study)
    estimate = enriched.pop("expiry_price_estimate")
    assert enriched == original
    assert estimate["estimated_outcome"] == estimate_outcome
    assert "TSP_PHYSICAL_EXPIRY_PRICE_ESTIMATE " in capsys.readouterr().out
    assert len(study_setup[6]) == 2
    report = study.summary(now_ts=target + 30)
    assert report["baseline_model_observations"] == report_before["baseline_model_observations"]
    assert report["published_study_results"]["wins"] == 0
    assert report["published_study_results"]["losses"] == 0
    assert report["published_study_results"]["unknown"] == 1
    assert report["paired_expiry_observations"] == report_before["paired_expiry_observations"]
    counts = report["published_study_expiry_estimates"]
    assert counts["eligible_unknown"] == counts["estimates_available"] == 1
    assert counts[{"WIN": "estimated_wins", "LOSS": "estimated_losses",
                   "INCONCLUSIVE": "inconclusive"}[estimate_outcome]] == 1
    assert sum(counts[key] for key in ("estimated_wins", "estimated_losses", "inconclusive", "unavailable")) == 1

    # A restart and a later favorable exact quote do not rewrite the historic
    # result, replace the first complete pair, or resend its accepted message.
    study = importlib.reload(study)
    study_setup[7][0] = target + 31.1
    study.advance(now_ts=target + 31, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: _sample(target, 1.2, buffered=True),
                  bracket_loader=load)
    assert brackets == [target]
    assert _row(study)["expiry_price_estimate"] == estimate
    assert _row(study)["study_observation"] == original["study_observation"]
    assert len(study_setup[6]) == 2
    assert "TSP_PHYSICAL_EXPIRY_PRICE_ESTIMATE " not in capsys.readouterr().out


def test_incomplete_estimate_upgrades_only_when_missing_side_arrives(study_setup, capsys):
    study, target = _unknown(study_setup)
    row = _row(study)
    bracket = _bracket(row, target)
    after = bracket.pop("after")
    load = lambda *args, **kwargs: bracket
    study_setup[7][0] = target + 20.1
    study.advance(now_ts=target + 20, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=load)
    partial = _row(study)["expiry_price_estimate"]
    assert partial["estimated_outcome"] == "UNAVAILABLE"
    assert partial["reason"] == "AFTER_QUOTE_UNAVAILABLE"
    capsys.readouterr()
    study_setup[7][0] = target + 21.1
    study.advance(now_ts=target + 21, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=load)
    assert _row(study)["expiry_price_estimate"] == partial
    assert "TSP_PHYSICAL_EXPIRY_PRICE_ESTIMATE " not in capsys.readouterr().out
    bracket["after"] = after
    study_setup[7][0] = target + 22.1
    study.advance(now_ts=target + 22, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=load)
    assert _row(study)["expiry_price_estimate"]["estimated_outcome"] == "WIN"
    assert len(study_setup[6]) == 2


def test_missing_estimate_freezes_at_deadline_and_first_historical_check(study_setup):
    study, target = _unknown(study_setup)
    calls = []
    def missing(*args, **kwargs):
        calls.append(args[1])
        return {}
    for stamp in (target + 20, target + 75):
        study_setup[7][0] = stamp + .1
        study.advance(now_ts=stamp, active_provider="FINNHUB", price_loader=lambda _: None,
                      bracket_loader=missing)
    frozen = copy.deepcopy(_row(study)["expiry_price_estimate"])
    assert frozen["estimated_at"] == target + 75
    study_setup[7][0] = target + 76.1
    study.advance(now_ts=target + 76, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=lambda *args, **kwargs: pytest.fail("expired gap rescanned"))
    assert _row(study)["expiry_price_estimate"] == frozen
    assert len(calls) == 2

    # Old rows without new metadata remain readable and receive one bounded
    # unavailable evaluation, then are not rescanned on future sampling passes.
    state = study._read(study._path())
    next(iter(state["records"].values())).pop("expiry_price_estimate")
    study._save(study._path(), state)
    study.advance(now_ts=target + 1000, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=missing)
    study.advance(now_ts=target + 1001, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=lambda *args, **kwargs: pytest.fail("historic gap rescanned"))
    assert len(calls) == 3


def test_estimate_validation_and_published_summary_scope(study_setup):
    study, target = _unknown(study_setup)
    original = _row(study)
    study_setup[7][0] = target + 30.1
    study.advance(now_ts=target + 30, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=lambda *args, **kwargs: _bracket(original, target))
    state = study._read(study._path())
    tampered = copy.deepcopy(state)
    next(iter(tampered["records"].values()))["expiry_price_estimate"]["estimated_outcome"] = "LOSS"
    with pytest.raises(ValueError, match="INVALID_EXPIRY_ESTIMATE"):
        study.validate(tampered)
    unpublished = copy.deepcopy(state)
    next(iter(unpublished["records"].values()))["study_delivery"]["result"]["status"] = "UNKNOWN"
    report = study.analyze(unpublished, now_ts=target + 30)
    assert report["published_study_expiry_estimates"]["eligible_unknown"] == 0
    assert report["published_study_expiry_estimates"]["estimates_available"] == 0
    mismatched = copy.deepcopy(state)
    mismatch_row = next(iter(mismatched["records"].values()))
    mismatch_row.pop("expiry_price_estimate")
    mismatch_row["study_observation"]["reason"] = "PROVIDER_CHANGED"
    assert study.analyze(mismatched, now_ts=target + 30)["published_study_expiry_estimates"]["eligible_unknown"] == 0


def test_bounded_newest_first_backfill_skips_all_frozen_rows(study_setup):
    study, target = _unknown(study_setup)
    template = _row(study)
    rows = {}
    for index in range(12):
        row = copy.deepcopy(template)
        row["entry"]["observed_ts"] += index * 100
        rows[str(index)] = row
    state = {"records": rows}
    calls = []
    def missing(symbol, expiry, *, max_side_seconds):
        calls.append(expiry)
        return {}
    now = target + 5000
    first = study._enrich_expiry_estimates(state, now=now, active_provider="FINNHUB", bracket_loader=missing)
    assert len(first) == 8
    assert calls == [target + index * 100 for index in reversed(range(4, 12))]
    assert len(study._enrich_expiry_estimates(state, now=now + 1, active_provider="FINNHUB", bracket_loader=missing)) == 4
    assert study._enrich_expiry_estimates(state, now=now + 2, active_provider="FINNHUB", bracket_loader=missing) == []
    assert len(calls) == 12


def test_provider_switch_and_lookup_failure_leave_official_evidence_unchanged(study_setup):
    study, target = _unknown(study_setup)
    original = copy.deepcopy(_row(study))
    study_setup[7][0] = target + 30.1
    study.advance(now_ts=target + 30, active_provider="TWELVE_DATA", price_loader=lambda _: None,
                  bracket_loader=lambda *args, **kwargs: pytest.fail("replacement provider queried"))
    switched = _row(study)
    for key in ("entry", "candidates", "study_observation", "study_delivery", "buffer_snapshot", "policies"):
        assert switched[key] == original[key]
    assert "expiry_price_estimate" not in switched
    original = copy.deepcopy(switched)
    def failed(*args, **kwargs):
        raise RuntimeError("synthetic lookup failure")
    study_setup[7][0] = target + 31.1
    study.advance(now_ts=target + 31, active_provider="FINNHUB", price_loader=lambda _: None,
                  bracket_loader=failed)
    assert _row(study) == original
    assert study.summary(now_ts=target + 31)["published_study_expiry_estimates"]["unavailable"] == 1


def test_estimate_is_saved_before_first_unknown_result_delivery(study_setup):
    _, study, _, _, _, _, messages, clock = study_setup
    _capture(study_setup)
    entry_ts = BASE + 32
    study.advance(now_ts=entry_ts, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(entry_ts, 1.1))
    row = _row(study)
    target = entry_ts + study.displayed_study_observation(row)["horizon_seconds"]
    clock[0] = target + 18.1
    study.advance(now_ts=target + 18, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: None,
                  bracket_loader=lambda *args, **kwargs: _bracket(row, target))
    saved = _row(study)
    assert saved["study_observation"]["outcome"] == "UNKNOWN"
    assert saved["expiry_price_estimate"]["estimated_outcome"] == "WIN"
    assert saved["study_delivery"]["result"]["status"] == "API_ACCEPTED"
    assert len(messages) == 2 and "WIN estimat" in messages[-1]["text"]
