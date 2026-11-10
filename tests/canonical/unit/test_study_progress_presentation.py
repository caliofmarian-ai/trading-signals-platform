"""Summary arithmetic and real periodic-report wiring; all transport is mocked."""
from contextlib import nullcontext
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

from intelligence.study_progress_presentation import render_published_study_progress

ACTIVE = "ADJUSTED_MOVEMENT_SECOND_CEILING_V1"
LEGACY = "CONFIRM_INTEGER_MINUTE_V1"
OLD = "LEGACY_OPEN_MODEL_TIME"


def render(observed):
    return render_published_study_progress(observed, active_policy=ACTIVE,
        legacy_policy=LEGACY, legacy_open_policy=OLD)


def counts(wins=7, losses=4, draws=0, unknown=12, *, met=6):
    return dict(wins=wins, losses=losses, draws=draws, unknown=unknown,
        decisive=wins + losses, buffer_met=met,
        buffer_not_met=wins + losses + draws - met, buffer_unavailable=unknown,
        win_buffer_not_met=wins - met,
        unknown_reasons={"EXPIRY_OBSERVATION_MISSING": unknown})


def evidence():
    return dict(study_open_now_api_accepted=351, study_results_api_accepted=351,
        published_study_results=counts(122, 100, 6, 123, met=43),
        published_study_results_by_duration_policy={ACTIVE: counts(),
            LEGACY: counts(4, 1, 0, 3, met=3), OLD: counts(111, 95, 6, 108, met=34)},
        baseline_model_observations=counts(999, 0, 0, 0, met=999))


def test_draws_reconcile_total_and_current_policy_precedes_history():
    source = evidence()
    before = deepcopy(source)
    text = render(source)
    assert "La secundă · 23 rezultate: WIN 7, LOSS 4, DRAW 0, UNKNOWN 12" in text
    assert "Total istoric · 351 rezultate: WIN 122, LOSS 100, DRAW 6, UNKNOWN 123" in text
    assert text.index("La secundă") < text.index("Istoric · minute") < text.index("Total istoric")
    assert "Cotație la expirare: 11/23" in text
    assert "Fără cotație în fereastra expirării: 12." in text
    assert "Marjă completă la expirare: DA 6, NU 5, indisponibilă 12" in text
    assert "WIN fragil (în buffer): 1" in text
    assert "999" not in text and "%" not in text
    assert source == before
    assert len(text) < 2000


def test_explicit_empty_cohort_is_not_100_percent_coverage():
    source = dict(study_open_now_api_accepted=0, study_results_api_accepted=0,
        published_study_results=counts(0, 0, 0, 0, met=0),
        published_study_results_by_duration_policy={ACTIVE: counts(0, 0, 0, 0, met=0)})
    text = render(source)
    assert "La secundă · 0 rezultate" in text
    assert "fără rezultate publicate încă" in text
    assert "0/0" not in text and "100" not in text


@pytest.mark.parametrize("key", ["wins", "losses", "draws", "unknown"])
@pytest.mark.parametrize("bad", [None, True, -1, 1.5, "7", float("nan"), 10**12])
def test_invalid_counts_do_not_produce_fabricated_zeroes_or_research_fallback(key, bad):
    source = evidence()
    source["published_study_results"][key] = bad
    text = render(source)
    assert "Rezultate studiu: statistici indisponibile." in text
    assert "WIN " not in text and "999" not in text


@pytest.mark.parametrize("missing", ["draws", "study_results_api_accepted"])
def test_missing_essential_fields_are_unavailable_not_zero(missing):
    source = evidence()
    if missing == "draws":
        source["published_study_results"].pop("draws")
    else:
        source.pop(missing)
    text = render(source)
    assert "Rezultate studiu: statistici indisponibile." in text
    assert "WIN " not in text


@pytest.mark.parametrize("change", ["aggregate_total", "cohort_total", "decisive", "too_many_results"])
def test_inconsistent_totals_are_explicit_not_silently_combined(change):
    source = evidence()
    if change == "aggregate_total":
        source["study_results_api_accepted"] += 1
    elif change == "cohort_total":
        source["published_study_results_by_duration_policy"][ACTIVE]["unknown"] += 1
    elif change == "decisive":
        source["published_study_results_by_duration_policy"][ACTIVE]["decisive"] += 1
    else:
        source["study_open_now_api_accepted"] = 1
    text = render(source)
    assert "indisponibile" in text or "neconcordante" in text
    assert "La secundă ·" not in text


def test_missing_current_cohort_does_not_use_legacy_win_rate():
    source = evidence()
    source["published_study_results"] = deepcopy(source["published_study_results_by_duration_policy"][OLD])
    source["published_study_results_by_duration_policy"] = {OLD: source["published_study_results"]}
    source["study_results_api_accepted"] = 320
    text = render(source)
    assert "La secundă: statistici indisponibile." in text
    assert "Istoric · OPEN · 320 rezultate" in text
    assert "La secundă · 320" not in text


def test_no_cohort_details_are_labelled_historical_not_current():
    source = evidence()
    source.pop("published_study_results_by_duration_policy")
    text = render(source)
    assert "La secundă: statistici indisponibile." in text
    assert "Total istoric · 351" in text and "DRAW 6" in text
    assert "Cotație la expirare: 228/351" in text  # includes draws in observed quotes


def test_unknown_future_policy_is_not_discarded_or_echoed_into_message():
    source = evidence()
    source["published_study_results_by_duration_policy"]["PRIVATE_UNTRUSTED_LABEL"] = counts()
    text = render(source)
    assert "Grupele de durată: statistici neconcordante." in text
    assert "PRIVATE_UNTRUSTED_LABEL" not in text
    assert "La secundă ·" not in text


@pytest.mark.parametrize("field", ["buffer_met", "buffer_unavailable", "win_buffer_not_met"])
def test_invalid_buffer_metrics_do_not_erase_valid_outcomes(field):
    source = evidence()
    source["published_study_results_by_duration_policy"][ACTIVE][field] = 999
    text = render(source)
    assert "La secundă · 23 rezultate" in text
    assert "Marja bufferului: statistici indisponibile sau neconcordante." in text
    assert "DA 999" not in text and "buffer): 999" not in text


def test_unknown_causes_are_not_all_relabelled_as_expiry_quotes():
    source = evidence()
    source["published_study_results_by_duration_policy"][ACTIVE]["unknown_reasons"] = {
        "EXPIRY_OBSERVATION_MISSING": 8, "ENTRY_OBSERVATION_MISSING": 4}
    text = render(source)
    assert "Fără cotație în fereastra expirării: 8." in text
    assert "fără rezultat observat: 12." in text
    source["published_study_results_by_duration_policy"][ACTIVE]["unknown_reasons"]["EXTRA"] = 1
    assert "Cauzele UNKNOWN: statistici neconcordante." in render(source)


@pytest.mark.parametrize("source", [None, [], {}, {"baseline_model_observations": counts()}])
def test_absent_published_source_never_uses_research_results(source):
    text = render(source)
    assert "statistici indisponibile" in text
    assert "WIN 7" not in text and "rezultate: 0" not in text


def test_periodic_report_uses_formatter_keeps_one_send_per_slot_and_does_not_change_results(monkeypatch):
    """Run the actual module; replace only storage/import boundaries and transport."""
    import intelligence
    source = evidence()
    before = deepcopy(source)
    sent, saved = [], []
    fake_core = ModuleType("core")
    fake_core.storage = SimpleNamespace(with_lock=lambda *args, **kw: nullcontext(),
        save_json_atomic=lambda path, state: saved.append(deepcopy(state)))
    fake_core.telegram_publisher = SimpleNamespace(send_message=lambda **kw: sent.append(kw) or {"ok": True})
    fake_core.confirmed_study_duration = SimpleNamespace(POLICY=ACTIVE,
        LEGACY_POLICY=LEGACY, LEGACY_OPEN_POLICY=OLD)
    monkeypatch.setitem(sys.modules, "core", fake_core)
    monkeypatch.setitem(sys.modules, "core.physical_params", SimpleNamespace(physical_runtime_enabled=lambda: True))
    monkeypatch.setitem(sys.modules, "core.owner_signal_delivery", SimpleNamespace(destination=lambda: 12345))
    calibration = SimpleNamespace(summary=lambda **kw: source)
    monkeypatch.setattr(intelligence, "physical_expiry_calibration", calibration, raising=False)
    path = Path(__file__).resolve().parents[3] / "send/intelligence/owner_timing_session.py"
    spec = importlib.util.spec_from_file_location("isolated_real_owner_timing", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = module._new(1000, "a" * 64)
    monkeypatch.setattr(module, "_path", lambda: Path("offline-state.json"))
    monkeypatch.setattr(module, "_read", lambda _: state)
    result = module.report_if_due(now_ts=1001)
    assert result["notification_api_accepted"] is True
    assert result["study_results_by_duration_policy"] == source["published_study_results_by_duration_policy"]
    assert "La secundă · 23 rezultate" in sent[0]["text"]
    assert "DRAW 6" in sent[0]["text"] and "remains unproven" in sent[0]["text"]
    assert len(sent[0]["text"]) < 4096
    assert sent[0]["chat_id"] == 12345
    assert module.report_if_due(now_ts=1002) is None
    assert len(sent) == len(saved) == 1
    assert source == before
