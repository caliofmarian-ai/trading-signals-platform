"""Synthetic failed/deferred lookups must not prematurely publish UNKNOWN.

Uses the real capture, persistence, enrichment and delivery functions, with the
existing offline market/transport fixture. No production prices or trades.
"""
from copy import deepcopy
import importlib
import json

import pytest

from tests.canonical.unit.test_physical_study_delivery import BASE, _capture, _sample, study_setup


def _saved(study):
    return next(iter(study._read(study._path())["records"].values()))


def _opened(setup):
    _, study, _, _, _, _, messages, _ = setup
    _capture(setup)
    study.advance(now_ts=BASE + 32, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(BASE + 32, 1.1))
    row = _saved(study)
    target = row["entry"]["observed_ts"] + study.displayed_study_observation(row)["horizon_seconds"]
    assert len(messages) == 1
    return row, target


def _advance(setup, now, loader):
    _, study, _, _, _, _, _, clock = setup
    clock[0] = now + .1
    study.advance(now_ts=now, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: None, bracket_loader=loader)
    return _saved(study)


def _failed(*args, **kwargs):
    raise RuntimeError("synthetic archive lookup failure")


def _pair(row, target, outcome="WIN"):
    sign = 1 if row["direction"] == "BUY" else -1
    if outcome == "LOSS":
        sign *= -1
    return {"before": _sample(target - 1, 1.1 + sign * .0001, buffered=True),
            "after": _sample(target + 4, 1.1 + (-sign if outcome == "INCONCLUSIVE" else sign) * .0002, buffered=True)}


@pytest.mark.parametrize("outcome", ["WIN", "LOSS", "INCONCLUSIVE"])
def test_first_lookup_failure_retries_before_once_only_publication(study_setup, outcome, capsys):
    _, study, delivery, _, _, _, messages, clock = study_setup
    original, target = _opened(study_setup)
    row = _advance(study_setup, target + 18, _failed)
    terminal = deepcopy(study.displayed_study_observation(row))
    assert terminal["outcome"] == "UNKNOWN" and terminal["quote"] is None
    assert "expiry_price_estimate" not in row
    assert row["study_delivery"]["result"] is None and len(messages) == 1
    before = study.summary(now_ts=target + 18)
    assert before["study_results_api_accepted"] == 0
    # A sender running independently of the observer cannot reserve it early.
    delivery.dispatch(now_ts=target + 19, active_provider="FINNHUB")
    assert len(messages) == 1 and _saved(study)["study_delivery"]["result"] is None
    pair = _pair(original, target, outcome)
    row = _advance(study_setup, target + 25, lambda *args, **kwargs: pair)
    assert row["expiry_price_estimate"]["estimated_outcome"] == outcome
    assert study.displayed_study_observation(row) == terminal
    for field in ("entry", "buffer_snapshot", "policies", "quote_recovery_policy"):
        assert row[field] == original[field]
    assert row["study_delivery"]["result"]["status"] == "API_ACCEPTED"
    expected = {"WIN": "WIN estimat", "LOSS": "LOSS estimat", "INCONCLUSIVE": "neconcludentă"}[outcome]
    assert len(messages) == 2 and expected in messages[-1]["text"]
    after = study.summary(now_ts=target + 25)
    assert after["published_study_results"]["wins"] == after["published_study_results"]["losses"] == 0
    assert after["published_study_results"]["unknown"] == 1
    assert after["paired_expiry_observations"] == before["paired_expiry_observations"]
    clock[0] = target + 30.1
    delivery.dispatch(now_ts=target + 30, active_provider="FINNHUB")
    assert len(messages) == 2
    evidence = [json.loads(line.split(" ", 1)[1]) for line in capsys.readouterr().out.splitlines()
                if line.startswith("TSP_PHYSICAL_STUDY_DELIVERY ")]
    result = [item for item in evidence if item["phase"] == "result"]
    assert len(result) == 1
    assert result[0]["estimate_wait_contract"] == "MISSING_ESTIMATE_BOUNDED_WAIT_V1"


def test_persistent_lookup_failure_releases_at_original_deadline_without_fabrication(study_setup):
    _, study, delivery, _, _, _, messages, clock = study_setup
    _, target = _opened(study_setup)
    for offset in (18, 40, 74.999):
        row = _advance(study_setup, target + offset, _failed)
        assert row["study_delivery"]["result"] is None and len(messages) == 1
        assert "expiry_price_estimate" not in row
    row = _advance(study_setup, target + 75, _failed)
    assert row["study_delivery"]["result"]["status"] == "API_ACCEPTED"
    assert row["study_delivery"]["result"]["attempted_ts"] == target + 75
    assert len(messages) == 2 and "Cotație expirare: LIPSĂ" in messages[-1]["text"]
    assert "WIN estimat" not in messages[-1]["text"] and "LOSS estimat" not in messages[-1]["text"]
    assert "expiry_price_estimate" not in row  # failure is not proof both quotes are absent
    clock[0] = target + 90.1
    delivery.dispatch(now_ts=target + 90, active_provider="FINNHUB")
    assert len(messages) == 2


def test_restart_does_not_forget_wait_or_reset_deadline(study_setup):
    _, study, delivery, _, _, _, messages, clock = study_setup
    _, target = _opened(study_setup)
    row = _advance(study_setup, target + 18, _failed)
    frozen = deepcopy(study.displayed_study_observation(row))
    study = importlib.reload(study)
    delivery.dispatch(now_ts=target + 74, active_provider="FINNHUB")
    assert len(messages) == 1 and _saved(study)["study_delivery"]["result"] is None
    clock[0] = target + 75.1
    delivery.dispatch(now_ts=target + 75, active_provider="FINNHUB")
    assert len(messages) == 2
    assert study.displayed_study_observation(_saved(study)) == frozen


def test_deferred_unattempted_lookup_also_waits(study_setup):
    _, study, _, _, _, _, messages, _ = study_setup
    original, target = _opened(study_setup)
    row = _advance(study_setup, target + 18, None)
    assert row["study_delivery"]["result"] is None and "expiry_price_estimate" not in row
    row = _advance(study_setup, target + 25,
                   lambda *args, **kwargs: _pair(original, target))
    assert len(messages) == 2 and row["expiry_price_estimate"]["estimated_outcome"] == "WIN"


@pytest.mark.parametrize("outcome", ["WIN", "LOSS", "DRAW"])
def test_observed_results_do_not_wait_for_estimation(study_setup, outcome):
    _, study, _, _, _, _, messages, clock = study_setup
    row, target = _opened(study_setup)
    sign = 1 if row["direction"] == "BUY" else -1
    price = 1.1 + sign * {"WIN": .0001, "LOSS": -.0001, "DRAW": 0}[outcome]
    clock[0] = target + .1
    study.advance(now_ts=target, active_provider="FINNHUB", price_loader=lambda _: None,
                  observation_loader=lambda *args: _sample(target, price, buffered=True),
                  bracket_loader=_failed)
    assert len(messages) == 2 and f"Rezultat: {outcome}" in messages[-1]["text"]
    assert _saved(study)["study_delivery"]["result"]["attempted_ts"] == target


def test_waiting_result_does_not_block_another_ready_result(study_setup, monkeypatch):
    _, study, delivery, _, _, _, _, _ = study_setup
    original, target = _opened(study_setup)
    waiting = _advance(study_setup, target + 18, _failed)
    ready = deepcopy(waiting)
    ready["created_ts"] += .01
    ready["study_observation"].update(outcome="WIN", reason="OBSERVED_PAIRED_EXPIRY",
                                      quote=_sample(target, 1.2, buffered=True))
    state = {"records": {"waiting": waiting, "ready": ready}}
    saves = []
    # Isolate reservation ordering; full store validation is covered above.
    monkeypatch.setattr(study, "_read", lambda _: state)
    monkeypatch.setattr(study, "_save", lambda *args: saves.append(deepcopy(state)))
    reserved = delivery._reserve("synthetic", "result", target + 19, 123456789)
    assert reserved[0] == "ready" and len(saves) == 1
    assert state["records"]["waiting"]["study_delivery"]["result"] is None


def test_other_unknown_reason_does_not_wait_for_missing_expiry_estimate(study_setup, monkeypatch):
    _, study, delivery, _, _, _, _, _ = study_setup
    _, target = _opened(study_setup)
    row = _advance(study_setup, target + 18, _failed)
    row["study_observation"]["reason"] = "PROVIDER_CHANGED"
    state = {"records": {"other": row}}
    monkeypatch.setattr(study, "_read", lambda _: state)
    monkeypatch.setattr(study, "_save", lambda *args: None)
    assert delivery._reserve("synthetic", "result", target + 19, 123456789)[0] == "other"
