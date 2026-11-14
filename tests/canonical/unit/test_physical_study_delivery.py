"""Synthetic observations and transport mocks; never production calibration evidence."""
import copy
import hashlib
import importlib
import json

import pytest

BASE = 1_800_000_000


@pytest.fixture
def study_setup(canonical_runtime_root, monkeypatch):
    for key, value in {"OWNER_SIGNAL_DELIVERY_ENABLED":"true", "OWNER_TELEGRAM_ID":"123456789",
        "SHADOW_MODE":"true", "SHADOW_MODEL_TIME_RESEARCH_ENABLED":"true",
        "ENABLE_BROKER_EXECUTION":"false"}.items():
        monkeypatch.setenv(key, value)
    from tests.canonical.integration.test_binary_strategy_v2 import _inputs
    from core.physical_params import migrate_physical_params
    from core.strategy_v3 import decide, lifecycle_context
    from core.v2_fsm_orchestrator import advance_persistent_fsm, bind_confirmed_execution_time
    from state_store.state_store import default_fsm_state
    from core import owner_signal_delivery as owner
    from intelligence import physical_expiry_calibration as study, physical_study_delivery as delivery
    m1, m5, old = _inputs(canonical_runtime_root)
    params, state = migrate_physical_params(old), default_fsm_state()
    for now in (BASE, BASE+2, BASE+31):
        result = decide(m1, m5, params, buffer_mode="SMALL",
                        context=lifecycle_context(state, "EUR/USD", now_ts=now))
        handoff = advance_persistent_fsm(state, result.decision, now_ts=now)
        handoff, _ = bind_confirmed_execution_time(handoff, result.decision, result.execution_time)
        state = handoff.next_state
    assert handoff.accepted_stage == "OPEN_NOW"
    key = hashlib.sha256(result.decision.signal_id.encode()).hexdigest()
    owner.storage.save_json_atomic(str(owner._timing_path()), {"schema_version":"1.0.0", "opportunities":{
        key: {"PRE":{"api_accepted_ts": BASE+.1}, "CONFIRM":{
            "api_accepted_ts":BASE+2.1,
            "study_duration_minutes": state["per_symbol"]["EUR/USD"]["physical_confirm_model_seconds"] / 60,
            "study_confirmed_ts": BASE+2,
            "study_duration_source": "CONFIRM_MODEL_TIME",
        }}}})
    messages = []
    clock = [BASE+32.1]
    monkeypatch.setattr(delivery.time, "time", lambda: clock[0])
    def transport(**kwargs):
        messages.append(kwargs)
        return {"ok":True, "result":{"message_id":len(messages)}}
    def photo_transport(*, chat_id, photo, caption, reply_to_message_id):
        return transport(chat_id=chat_id, photo=photo, text=caption, reply_to_message_id=reply_to_message_id)
    monkeypatch.setattr(delivery.telegram_publisher, "send_message", transport)
    monkeypatch.setattr(delivery.telegram_publisher, "send_photo", photo_transport)
    monkeypatch.setattr(delivery, "dispatch_async", lambda **kwargs: delivery.dispatch(**kwargs))
    return canonical_runtime_root, study, delivery, result, handoff, params, messages, clock


def _capture(setup, *, publish=True):
    _, study, _, result, handoff, params, _, _ = setup
    assert study.observe_accepted_chain(result.decision, handoff, params, now_ts=BASE+31,
        provider="FINNHUB", buffer_mode="SMALL", market_evidence=result.market.evidence,
        publish_study=publish)
    return next(iter(study._read(study._path())["records"].values()))


def _sample(stamp, price, *, buffered=False):
    return {"provider":"FINNHUB", "symbol":"EUR/USD", "price":price, "observed_ts":float(stamp),
            "source":"LIVE_STREAM_PROVIDER_TICK_BUFFER_V1" if buffered else "LIVE_STREAM_CURRENT_M1_CLOSE"}


def test_compact_calibration_reports_exact_fixed_training_gate_failures(study_setup):
    _, study, _, _, _, params, _, _ = study_setup
    entries = []
    for index in range(60):
        created = BASE + index * 180
        entries.append({
            "policy": "PHYSICAL_ONLY_V3", "direction": "BUY",
            "opportunity_signal_id": f"sig-v3-test-{index}",
            "created_ts": created, "open_ts": created, "pre_ts": created - 32,
            "confirm_ts": created - 30, "confirm_model_seconds": 120,
            "model_seconds": 120, "adjusted_seconds": 100 if index < 32 else 90,
            "buffer_distance": 0.0002 if index < 54 else None,
        })
    study.capture(entries, params=params, buffer_mode="SMALL", strategy_version="3.0.0",
                  canonical_spec="V3_SCORELESS_OWNER_AMENDMENT_v1.1.0", now_ts=BASE + 10800)
    state = study._read(study._path())
    pending_report = study._compact(study.analyze(state, now_ts=BASE + 10800))
    assert all(candidate["blocking_gates"] == ["TRAINING_LOT_INCOMPLETE"]
               for candidate in pending_report["policies"][0]["training_candidate_quality"])

    for index, row in enumerate(state["records"].values()):
        entry = _sample(row["created_ts"] + 1, 1.1)
        row.update(state="FINAL", entry=entry)
        for position, candidate in enumerate(row["candidates"]):
            if candidate["outcome"] == "INFEASIBLE":
                continue
            if (position == 0 and index >= 53) or (position == 1 and index < 6):
                candidate.update(outcome="UNKNOWN", reason="EXPIRY_OBSERVATION_MISSING")
                continue
            draw = position == 3 and index < 31
            price = 1.1 if draw else 1.1003
            candidate.update(outcome="DRAW" if draw else "WIN", reason="OBSERVED_PAIRED_EXPIRY",
                             quote=_sample(entry["observed_ts"] + candidate["horizon_seconds"], price))

    original_state = copy.deepcopy(state)
    report = study.analyze(state, now_ts=BASE + 10800)
    row = study._compact(report)["policies"][0]
    evidence = row["training_candidate_quality"]
    assert state == original_state
    assert row["training_selected_bias"] == 0.10
    assert len(evidence) == len(study.BIASES)
    assert evidence[0]["blocking_gates"] == [
        "DIRECTION_UNKNOWN_FRACTION_ABOVE_MAXIMUM", "BUFFER_UNKNOWN_FRACTION_ABOVE_MAXIMUM",
    ]
    assert evidence[0]["unknown_reasons"] == {"EXPIRY_OBSERVATION_MISSING": 7}
    assert evidence[1]["unknown_fraction"] == 0.10
    assert evidence[1]["blocking_gates"] == ["BUFFER_UNKNOWN_FRACTION_ABOVE_MAXIMUM"]
    assert evidence[2]["buffer_unknown_fraction"] == 0.10
    assert evidence[2]["blocking_gates"] == []
    assert evidence[3]["blocking_gates"] == ["DIRECTION_DECISIVE_COUNT_BELOW_MINIMUM"]
    assert evidence[4]["infeasible"] == 32
    assert evidence[4]["blocking_gates"] == [
        "DIRECTION_DECISIVE_COUNT_BELOW_MINIMUM", "BUFFER_KNOWN_COUNT_BELOW_MINIMUM",
        "BUFFER_UNKNOWN_FRACTION_ABOVE_MAXIMUM",
    ]
    assert "train_candidates" not in row and "buffer_coverage" not in evidence[0]
    assert "sig-v3-test-" not in json.dumps(evidence)


def _confirmed_duration(setup, seconds):
    """Simulate a previously delivered CONFIRM whose horizon differs at OPEN."""
    _, _, _, _, handoff, _, _, _ = setup
    handoff.next_state["per_symbol"]["EUR/USD"]["physical_confirm_model_seconds"] = seconds
    from core import owner_signal_delivery as owner
    ledger = json.loads(owner._timing_path().read_text())
    for stages in ledger["opportunities"].values():
        stages["CONFIRM"]["study_duration_minutes"] = seconds / 60
    owner.storage.save_json_atomic(str(owner._timing_path()), ledger)


def test_confirmed_duration_survives_changed_open_model_restart_and_independent_result(study_setup, monkeypatch):
    _, study, delivery, result, _, params, messages, clock = study_setup
    model_seconds = result.decision.time.model_expiry * 60
    confirmed_seconds = model_seconds + 60
    assert confirmed_seconds <= params["expiry_limits_minutes"]["max"] * 60
    _confirmed_duration(study_setup, confirmed_seconds)
    row = _capture(study_setup)
    assert row["model_seconds"] == model_seconds
    assert row["candidates"][0]["horizon_seconds"] == model_seconds
    assert row["study_observation"]["horizon_seconds"] == confirmed_seconds

    entry_ts = BASE + 32
    study.advance(now_ts=entry_ts, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(entry_ts, 1.1))
    saved = next(iter(study._read(study._path())["records"].values()))
    projected = delivery._entry_event(saved)
    assert projected["study_duration_minutes"] == confirmed_seconds / 60
    assert projected["expiry_ts"] == entry_ts + confirmed_seconds
    assert projected["study_confirmed_ts"] == BASE + 2
    assert projected["study_duration_source"] == "CONFIRM_MODEL_TIME"
    assert len(messages) == 1

    direction = 1 if row["direction"] == "BUY" else -1
    model_target = entry_ts + model_seconds
    clock[0] = model_target + .1
    study.advance(now_ts=model_target, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(model_target, 1.1 + direction * .01))
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["candidates"][0]["outcome"] == "WIN"
    assert saved["state"] == "FINAL"  # research completion must not stop the promised study horizon
    assert saved["study_observation"]["outcome"] == "PENDING"
    assert len(messages) == 1
    report = study.summary(now_ts=model_target)
    assert report["baseline_model_observations"]["wins"] == 1
    assert report["published_study_results"]["decisive"] == 0

    study = importlib.reload(study)
    from intelligence import physical_study_chart
    rendered, original = [], physical_study_chart.render_market_chart

    def chart(**kwargs):
        rendered.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(physical_study_chart, "render_market_chart", chart)
    confirmed_target = entry_ts + confirmed_seconds
    clock[0] = confirmed_target + .1
    study.advance(now_ts=confirmed_target, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(confirmed_target, 1.1 - direction * .01))
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["candidates"][0]["outcome"] == "WIN"
    assert saved["study_observation"]["outcome"] == "LOSS"
    assert saved["study_observation"]["quote"]["observed_ts"] == confirmed_target
    assert len(messages) == 2 and "Rezultat: LOSS" in messages[1]["text"]
    assert rendered[0]["expiry_ts"] == confirmed_target
    assert rendered[0]["outcome"] == "LOSS"
    report = study.summary(now_ts=confirmed_target)
    assert report["baseline_model_observations"]["wins"] == 1
    assert report["published_study_results"]["wins"] == 0
    assert report["published_study_results"]["losses"] == 1
    assert report["published_study_results"]["buffer_not_met"] == 1
    unaccepted = study._read(study._path())
    next(iter(unaccepted["records"].values()))["study_delivery"]["result"]["status"] = "UNKNOWN"
    report = study.analyze(unaccepted, now_ts=confirmed_target)
    assert report["baseline_model_observations"]["wins"] == 1
    assert report["published_study_results"]["decisive"] == 0


def test_confirmed_study_that_no_longer_fits_open_physics_is_not_published(study_setup):
    _, study, _, result, _, _, messages, _ = study_setup
    _confirmed_duration(study_setup, result.decision.time.t_needed_adjusted * 30)
    row = _capture(study_setup)
    assert row["study_observation"]["outcome"] == "INFEASIBLE"
    assert row["candidates"][0]["outcome"] == "PENDING"
    study.advance(now_ts=BASE + 32, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(BASE + 32, 1.1))
    assert not messages
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["study_delivery"]["entry"]["status"] == "SKIPPED_DURATION_INFEASIBLE"
    assert saved["study_delivery"]["entry"]["resolution_reason"] == "OPEN_ADJUSTED_TIME_EXCEEDS_CONFIRMED_DURATION"



def test_open_market_duration_report_reconciles_frozen_confirm_plan_and_open_adjusted_time():
    from intelligence import physical_expiry_calibration as study

    policy = study.second_duration.POLICY
    rows = [
        {
            "adjusted_seconds": 150.0,
            "study_observation": {
                "duration_policy": policy, "horizon_seconds": 120,
                "outcome": "INFEASIBLE",
                "duration_plan": {"adjusted_minutes": 1.5},
            },
            "open_market_duration": {"horizon_seconds": 180, "outcome": "PENDING"},
            "study_delivery": {"entry": {
                "status": "SKIPPED_DURATION_INFEASIBLE", "attempted_ts": BASE + 32,
            }},
        },
        {
            "adjusted_seconds": 150.0,
            "study_observation": {
                "duration_policy": policy, "horizon_seconds": 180,
                "outcome": "PENDING",
                "duration_plan": {"adjusted_minutes": 2.0},
            },
            "open_market_duration": {"horizon_seconds": 180, "outcome": "PENDING"},
            "study_delivery": {"entry": {
                "status": "API_ACCEPTED", "attempted_ts": BASE + 32,
                "message_id": 2, "api_accepted_ts": BASE + 32.1,
            }},
        },
    ]

    reconciliation = study._duration_reconciliation_report(rows)
    bucket = reconciliation["by_duration_policy"][policy]

    assert reconciliation["protocol"] == "CONFIRM_TO_OPEN_DURATION_RECONCILIATION_V1"
    assert bucket["observations"] == 2
    assert bucket["confirmed_duration_infeasible"] == 1
    assert bucket["study_feasibility"] == {"INFEASIBLE": 1, "PENDING": 1}
    assert bucket["entry_delivery_statuses"] == {
        "API_ACCEPTED": 1, "SKIPPED_DURATION_INFEASIBLE": 1,
    }
    assert bucket["terminal_reason_counts"] == {
        "OPEN_ADJUSTED_TIME_EXCEEDS_CONFIRMED_DURATION": 1,
    }
    assert bucket["confirm_plan_rows"] == 2
    assert bucket["confirm_adjusted_time_seconds"]["sample"] == 2
    assert bucket["open_adjusted_time_seconds"]["sample"] == 2
    assert bucket["open_minus_confirm_adjusted_seconds"]["min"] == 30
    assert bucket["open_minus_confirm_adjusted_seconds"]["max"] == 60
    assert bucket["confirmed_duration_minus_open_adjusted_seconds"]["min"] == -30
    assert bucket["confirmed_duration_minus_open_adjusted_seconds"]["max"] == 30
    assert bucket["entry_receipt_attempts"] == 1
    assert bucket["entry_api_acceptance_rate"] == 1.0
    assert bucket["entry_api_accepted_per_observed_open"] == 0.5
    assert reconciliation["no_strategy_change"] is True
    assert reconciliation["automatic_parameter_change"] is False
    assert reconciliation["broker_executed"] is False


def test_confirmed_study_exact_fit_accepts_only_machine_precision_drift(study_setup):
    from dataclasses import replace

    setup = list(study_setup)
    _, study, _, result, _, _, messages, _ = setup
    adjusted_seconds = 180.00000000000003
    timing = replace(result.decision.time, model_expiry=4.0,
                     t_needed=2.5, t_needed_adjusted=adjusted_seconds / 60,
                     model_time_reach_ratio=(adjusted_seconds / 60) / 4,
                     time_to_buffer_ratio=4 / (adjusted_seconds / 60))
    setup[3] = replace(result, decision=replace(result.decision, time=timing))
    _confirmed_duration(setup, 180.0)
    row = _capture(setup)
    assert row["study_observation"]["horizon_seconds"] == 180.0
    assert row["study_observation"]["outcome"] == "PENDING"
    # The established research grid is not reclassified by this display-study fix.
    assert row["candidates"][-1]["horizon_seconds"] == 180.0
    assert row["candidates"][-1]["outcome"] == "INFEASIBLE"
    study.advance(now_ts=BASE + 32, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(BASE + 32, 1.1))
    assert len(messages) == 1
    assert study._confirmed_study_feasible(180.0, adjusted_seconds)
    assert not study._confirmed_study_feasible(180.0, 180.000001)


@pytest.mark.parametrize("prior_status", [None, "FROZEN", "BLOCKED"])
def test_old_or_calibrated_confirmation_cannot_be_downgraded_to_new_study(study_setup, prior_status):
    _, _, _, _, handoff, _, _, _ = study_setup
    row = handoff.next_state["per_symbol"]["EUR/USD"]
    row["physical_confirm_execution_status"] = prior_status
    if prior_status == "FROZEN":
        row["physical_confirm_execution"] = {"source": "synthetic-calibration"}
    captured = _capture(study_setup)
    assert "study_delivery" not in captured
    assert "study_observation" not in captured


@pytest.mark.parametrize("field,value", [("horizon_seconds", 1), ("confirmed_ts", BASE + 3),
                                         ("duration_source", "OPEN_MODEL_TIME")])
def test_saved_study_cannot_rewrite_previously_confirmed_duration(study_setup, field, value):
    _, study, _, _, _, _, _, _ = study_setup
    _capture(study_setup)
    state = study._read(study._path())
    next(iter(state["records"].values()))["study_observation"][field] = value
    with pytest.raises(ValueError, match="CONFIRMED_STUDY_HORIZON"):
        study.validate(state)


@pytest.mark.parametrize("mismatch", ["missing_duration", "changed_duration", "changed_timestamp", "changed_source"])
def test_study_open_requires_the_same_duration_actually_delivered_at_confirm(study_setup, mismatch):
    _, study, _, _, _, _, messages, _ = study_setup
    _capture(study_setup)
    from core import owner_signal_delivery as owner
    ledger = json.loads(owner._timing_path().read_text())
    for stages in ledger["opportunities"].values():
        confirm = stages["CONFIRM"]
        if mismatch == "missing_duration":
            confirm.pop("study_duration_minutes")
        elif mismatch == "changed_duration":
            confirm["study_duration_minutes"] += 1
        elif mismatch == "changed_timestamp":
            confirm["study_confirmed_ts"] += 1
        else:
            confirm["study_duration_source"] = "OPEN_MODEL_TIME"
    owner.storage.save_json_atomic(str(owner._timing_path()), ledger)
    study.advance(now_ts=BASE + 32, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(BASE + 32, 1.1))
    assert not messages
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["study_delivery"]["entry"]["status"] == "SKIPPED_STAGE_GUARD"
    assert isinstance(saved["study_delivery"]["entry"]["resolution_reason"], str)
    assert saved["study_delivery"]["entry"]["resolution_reason"]


def test_complete_physical_chain_publishes_explicit_study_and_distinct_buffer_result(study_setup, capsys):
    _, study, delivery, result, _, _, messages, clock = study_setup
    row = _capture(study_setup)
    study.advance(now_ts=BASE+32, active_provider="FINNHUB", price_loader=lambda _: _sample(BASE+32,1.1))
    assert len(messages) == 1
    assert messages[0]["chat_id"] == 123456789
    assert "OPEN NOW" in messages[0]["text"] and "STUDIU · SIMULARE" in messages[0]["text"]
    assert messages[0]["photo"].startswith(b"\x89PNG\r\n\x1a\n")
    assert len(messages[0]["text"].splitlines()) <= 2
    assert "Score" not in messages[0]["text"] and "TPS" not in messages[0]["text"]
    label = delivery.owner_signal_number.lookup_lifecycle(result.decision.signal_id)
    assert label is not None and label.endswith("nr. 0")
    assert "#0" in messages[0]["text"] and label.split(" · ")[0] in messages[0]["text"]
    assert result.decision.signal_id not in messages[0]["text"]
    from core import owner_signal_delivery as owner
    ledger = json.loads(owner._timing_path().read_text())
    assert all("OPEN_NOW" not in stages for stages in ledger["opportunities"].values())
    direction = 1 if row["direction"] == "BUY" else -1
    target = BASE+32+row["model_seconds"]
    clock[0] = target+.1
    price = 1.1 + direction*row["buffer_snapshot"]["buffer_distance"]*.5
    study.advance(now_ts=target, active_provider="FINNHUB", price_loader=lambda _: _sample(target,price))
    assert len(messages) == 2 and "REZULTAT STUDIU" in messages[1]["text"]
    assert "Rezultat: WIN\n" in messages[1]["text"]
    assert "Rezultat: WIN fragil" not in messages[1]["text"]
    assert "Poziție buffer: În buffer · câștig fragil" in messages[1]["text"]
    assert "Marjă completă la expirare: NU" in messages[1]["text"]
    assert label in messages[1]["text"]
    assert messages[1]["photo"].startswith(b"\x89PNG\r\n\x1a\n")
    assert messages[1]["reply_to_message_id"] == 1
    report = study.summary(now_ts=target)
    assert report["study_open_now_api_accepted"] == report["study_results_api_accepted"] == 1
    assert report["actual_telegram_publications"] == 0 and not report["execution_calibration_proven"]
    assert report["decision_snapshot_entries"] == 1
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["decision_snapshot"]["decision_id"] == result.decision.decision_id
    assert saved["decision_snapshot"]["indicators"]["atr_m5"] == result.market.evidence.atr_m5
    assert saved["study_delivery"]["entry"]["format"] == "PHOTO"
    assert "resolution_reason" not in saved["study_delivery"]["entry"]
    assert saved["study_delivery"]["result"]["format"] == "PHOTO"
    assert saved["study_delivery"]["entry"]["signal_label"] == label
    assert saved["study_delivery"]["result"]["signal_label"] == label
    evidence = [json.loads(line.split(" ", 1)[1]) for line in capsys.readouterr().out.splitlines()
                if line.startswith("TSP_PHYSICAL_STUDY_DELIVERY ")]
    opened, settled = next(e for e in evidence if e["phase"] == "entry"), next(e for e in evidence if e["phase"] == "result")
    assert "presentation_contract" not in opened
    assert settled["presentation_contract"] == "EXPLICIT_PRICE_EVIDENCE_V1"
    assert settled["direction"] == row["direction"]
    assert settled["entry_price"] == 1.1 and settled["expiry_price"] == price
    assert settled["entry_quote_source"] == settled["expiry_quote_source"] == "LIVE_STREAM_CURRENT_M1_CLOSE"
    assert settled["observation_reason"] == "OBSERVED_PAIRED_EXPIRY"
    assert settled["buffer_position"] == "INSIDE_BUFFER" and settled["buffer_full_margin_status"] == "NOT_MET"
    assert not {"caption", "destination_id", "chat_id", "token"} & settled.keys()
    # A later buffer hit remains a diagnostic; the original label stays unchanged.
    later = target+60
    clock[0] = later+.1
    study.advance(now_ts=later, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(later,1.1+direction*row["buffer_snapshot"]["buffer_distance"]*1.5))
    assert study.summary(now_ts=later)["post_model_diagnostics"][0]["buffer_met"] == 1
    assert study.summary(now_ts=later)["baseline_model_observations"]["buffer_not_met"] == 1
    assert len(messages) == 2


@pytest.mark.parametrize("render_fails", [True, False])
def test_study_result_render_failure_falls_back_but_ambiguous_upload_does_not(study_setup, monkeypatch, render_fails):
    _, study, delivery, _, _, _, messages, clock = study_setup
    row = _capture(study_setup)
    study.advance(now_ts=BASE+32, active_provider="FINNHUB", price_loader=lambda _: _sample(BASE+32, 1.1))
    attempts = []

    def unavailable(*args, **kwargs):
        attempts.append(True)
        raise TimeoutError("synthetic chart failure")

    if render_fails:
        monkeypatch.setattr(delivery, "_render_chart", unavailable)
    else:
        monkeypatch.setattr(delivery.telegram_publisher, "send_photo", unavailable)
    target = BASE + 32 + row["model_seconds"]
    clock[0] = target + 0.1
    study.advance(now_ts=target, active_provider="FINNHUB", price_loader=lambda _: _sample(target, 1.1))
    delivery.dispatch(now_ts=target + 1, active_provider="FINNHUB")
    saved = next(iter(study._read(study._path())["records"].values()))
    receipt = saved["study_delivery"]["result"]
    assert len(attempts) == 1
    if render_fails:
        assert len(messages) == 2 and "Grafic indisponibil" in messages[1]["text"]
        assert (receipt["status"], receipt["format"]) == ("API_ACCEPTED", "TEXT")
    else:
        assert len(messages) == 1
        assert (receipt["status"], receipt["format"]) == ("UNKNOWN", "PHOTO")


def test_study_result_without_an_expiry_quote_still_sends_a_chart(study_setup, capsys):
    _, study, _, _, _, _, messages, clock = study_setup
    row = _capture(study_setup)
    study.advance(now_ts=BASE + 32, active_provider="FINNHUB", price_loader=lambda _: _sample(BASE + 32, 1.1))
    target = BASE + 32 + row["model_seconds"]
    now = target + study.quotes.MAX_SAMPLE_DELAY_SECONDS + 1
    clock[0] = now + 0.1
    study.advance(now_ts=now, active_provider="FINNHUB", price_loader=lambda _: None)
    assert len(messages) == 1
    deadline = target + 60 + study.EXPIRY_ESTIMATE_ARRIVAL_GRACE_SECONDS
    clock[0] = deadline + 0.1
    study.advance(now_ts=deadline, active_provider="FINNHUB", price_loader=lambda _: None)
    assert len(messages) == 2
    assert messages[1]["photo"].startswith(b"\x89PNG\r\n\x1a\n")
    assert "Cotație expirare: LIPSĂ" in messages[1]["text"]
    assert "Rezultat: Lipsește cotația la expirare" in messages[1]["text"]
    assert "UNKNOWN" not in messages[1]["text"]
    evidence = [json.loads(line.split(" ", 1)[1]) for line in capsys.readouterr().out.splitlines()
                if line.startswith("TSP_PHYSICAL_STUDY_DELIVERY ")]
    settled = next(e for e in evidence if e["phase"] == "result")
    assert settled["entry_price"] == 1.1 and settled["expiry_price"] is None
    assert settled["entry_quote_source"] == "LIVE_STREAM_CURRENT_M1_CLOSE" and settled["expiry_quote_source"] is None
    assert settled["observation_reason"] == "EXPIRY_OBSERVATION_MISSING"
    assert settled["buffer_position"] == settled["buffer_full_margin_status"] == "UNAVAILABLE"


def test_late_worker_recovers_earlier_real_quote_inside_original_tolerance(study_setup):
    _, study, _, _, _, _, messages, clock = study_setup
    row = _capture(study_setup, publish=False)
    study.advance(now_ts=BASE+32, active_provider="FINNHUB", price_loader=lambda _: _sample(BASE+32,1.1))
    target = BASE+32+row["model_seconds"]
    clock[0] = target+10
    def buffered(_symbol, requested, delay):
        return _sample(target+1,1.2,buffered=True) if requested == target else None
    study.advance(now_ts=target+10, active_provider="FINNHUB", observation_loader=buffered,
                  price_loader=lambda _: _sample(target+10,1.0))
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["candidates"][0]["outcome"] == "WIN"
    assert saved["candidates"][0]["quote"]["observed_ts"] == target+1
    assert saved["candidates"][0]["quote"]["source"] == "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1"
    assert not messages


def test_missing_buffered_quote_is_unknown_not_later_win(study_setup):
    _, study, _, _, _, _, _, clock = study_setup
    row = _capture(study_setup, publish=False)
    study.advance(now_ts=BASE+32, active_provider="FINNHUB", price_loader=lambda _: _sample(BASE+32,1.1))
    target = BASE+32+row["model_seconds"]
    after_deadline = target + study.quotes.MAX_SAMPLE_DELAY_SECONDS + study.BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS + 1
    clock[0] = after_deadline
    study.advance(now_ts=after_deadline, active_provider="FINNHUB", observation_loader=lambda *a: None,
                  price_loader=lambda _: _sample(after_deadline,1.2))
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["candidates"][0]["outcome"] == "UNKNOWN"
    assert saved["candidates"][0]["quote"] is None


@pytest.mark.parametrize("phase", ["entry", "expiry"])
@pytest.mark.parametrize("eligible", [True, False])
def test_buffered_quote_grace_preserves_source_time_window(study_setup, phase, eligible):
    _, study, _, _, _, _, _, _ = study_setup
    row = _capture(study_setup, publish=False)
    if phase == "entry":
        target = row["created_ts"]
        window = study.quotes.MAX_ENTRY_DELAY_SECONDS
    else:
        entry_ts = BASE + 32
        study.advance(now_ts=entry_ts, active_provider="FINNHUB",
                      price_loader=lambda _: _sample(entry_ts, 1.1))
        target = entry_ts + row["model_seconds"]
        window = study.quotes.MAX_SAMPLE_DELAY_SECONDS
    deadline = target + window
    grace = study.BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS
    received = None

    def buffered(symbol, requested, delay):
        if requested == target:
            assert symbol == "EUR/USD" and delay == window
            return received

    def advance(now):
        study.advance(now_ts=now, active_provider="FINNHUB", observation_loader=buffered,
                      price_loader=lambda _: None)
        saved = next(iter(study._read(study._path())["records"].values()))
        return saved, saved["candidates"][0]

    _, candidate = advance(deadline + grace / 2)
    assert candidate["outcome"] == "PENDING"

    direction = 1 if row["direction"] == "BUY" else -1
    stamp = deadline if eligible else deadline + grace / 2
    received = _sample(stamp, 1.1 + direction * 0.01, buffered=True)
    saved, candidate = advance(deadline + grace)
    if eligible:
        if phase == "entry":
            assert saved["entry"]["observed_ts"] == stamp
            assert saved["state"] == "OBSERVING"
        else:
            assert candidate["outcome"] == "WIN"
            assert candidate["quote"]["observed_ts"] == stamp
    else:
        assert candidate["outcome"] == "PENDING"
        _, candidate = advance(deadline + grace + 1)
        assert candidate["outcome"] == "UNKNOWN"
        assert candidate["reason"] == f"{phase.upper()}_OBSERVATION_MISSING"
        received = _sample(deadline, 1.1 + direction * 0.01, buffered=True)
        _, candidate = advance(deadline + grace + 2)
        assert candidate["outcome"] == "UNKNOWN"


@pytest.mark.parametrize("condition", ["shadow_disabled", "broker_enabled", "wrong_provider", "missing_confirm", "stale"])
def test_study_publication_guards(study_setup, monkeypatch, condition):
    _, study, delivery, _, _, _, messages, clock = study_setup
    _capture(study_setup)
    # Establish the genuine sample without invoking transport yet.
    path = study._path()
    state = study._read(path)
    record = next(iter(state["records"].values()))
    record.update(entry=_sample(BASE+32,1.1), state="OBSERVING")
    study._save(path,state)
    now, provider = BASE+32, "FINNHUB"
    if condition == "shadow_disabled": monkeypatch.setenv("SHADOW_MODE","false")
    if condition == "broker_enabled": monkeypatch.setenv("ENABLE_BROKER_EXECUTION","true")
    if condition == "wrong_provider": provider = "TWELVE_DATA"
    if condition == "missing_confirm":
        from core import owner_signal_delivery as owner
        ledger=json.loads(owner._timing_path().read_text())
        for stages in ledger["opportunities"].values(): stages.pop("CONFIRM")
        owner.storage.save_json_atomic(str(owner._timing_path()),ledger)
    if condition == "stale": now = BASE+50
    delivery.dispatch(now_ts=now,active_provider=provider)
    assert not messages


def test_ambiguous_transport_is_not_retried(study_setup, monkeypatch):
    _, study, delivery, _, _, _, messages, clock = study_setup
    _capture(study_setup)
    calls=[]
    def uncertain(**kwargs):
        calls.append(kwargs)
        raise TimeoutError("synthetic transport ambiguity")
    monkeypatch.setattr(delivery.telegram_publisher,"send_photo",uncertain)
    study.advance(now_ts=BASE+32,active_provider="FINNHUB",price_loader=lambda _: _sample(BASE+32,1.1))
    clock[0]=BASE+33
    delivery.dispatch(now_ts=BASE+33,active_provider="FINNHUB")
    assert len(calls)==1
    assert not messages
    saved=next(iter(study._read(study._path())["records"].values()))
    assert saved["study_delivery"]["entry"]["status"]=="UNKNOWN"
    assert saved["study_delivery"]["entry"]["format"]=="PHOTO"
    assert saved["study_delivery"]["entry"]["resolution_reason"] == "AMBIGUOUS_TRANSPORT_ACCEPTANCE"


def test_entry_render_crossing_original_window_skips_transport(study_setup, monkeypatch):
    _, study, delivery, _, _, _, messages, clock = study_setup
    _capture(study_setup)
    path = study._path()
    state = study._read(path)
    record = next(iter(state["records"].values()))
    record.update(entry=_sample(BASE + 32, 1.1), state="OBSERVING")
    study._save(path, state)
    clock[0] = BASE + 40.5

    def delayed_card(*_):
        clock[0] = BASE + 41.5
        return b"synthetic photo"

    monkeypatch.setattr(delivery, "_render_entry_card", delayed_card)
    delivery.dispatch(now_ts=clock[0], active_provider="FINNHUB")

    assert not messages
    saved = next(iter(study._read(path)["records"].values()))
    assert saved["study_delivery"]["entry"]["status"] == "SKIPPED_STALE"
    assert saved["study_delivery"]["entry"]["resolution_reason"] == "ENTRY_WINDOW_EXPIRED_DURING_RENDER"
    assert saved["study_delivery"]["result"] is None
    assert saved["entry"] == record["entry"]


def test_photo_entry_reuses_pre_number_and_frozen_observation(study_setup):
    _, study, delivery, result, _, _, messages, _ = study_setup
    numbers = delivery.owner_signal_number
    numbers.reserve_lifecycle("earlier-opportunity", BASE)
    pre_label = numbers.reserve_lifecycle(result.decision.signal_id, BASE)
    assert pre_label.endswith("nr. 1")
    row = _capture(study_setup)

    study.advance(now_ts=BASE + 32, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(BASE + 32, 1.12221))

    assert len(messages) == 1 and "#1" in messages[0]["text"]
    assert "#0" not in messages[0]["text"]
    assert messages[0]["photo"].startswith(b"\x89PNG\r\n\x1a\n")
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["study_delivery"]["entry"]["signal_label"] == pre_label
    assert numbers.lookup_lifecycle(result.decision.signal_id) == pre_label
    assert delivery._entry_event(saved) == {
        "stage": "OPEN_NOW", "symbol": "EUR/USD", "direction": row["direction"],
        "entry_price": 1.12221, "created_ts": row["created_ts"],
        "entry_ts": BASE + 32, "expiry_ts": BASE + 32 + row["model_seconds"],
        "study_duration_minutes": row["model_seconds"] / 60,
        "study_confirmed_ts": BASE + 2,
        "study_duration_source": "CONFIRM_MODEL_TIME",
    }


def test_study_entry_render_failure_uses_same_id_text_once(study_setup, monkeypatch, capsys):
    _, study, delivery, _, _, _, messages, clock = study_setup
    _capture(study_setup)

    def unavailable(*args, **kwargs):
        raise RuntimeError("synthetic card renderer failure")

    monkeypatch.setattr(delivery, "_render_entry_card", unavailable)
    study.advance(now_ts=BASE + 32, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(BASE + 32, 1.1))
    clock[0] = BASE + 33
    delivery.dispatch(now_ts=BASE + 33, active_provider="FINNHUB")

    assert len(messages) == 1 and "photo" not in messages[0]
    assert "#0" in messages[0]["text"] and "STUDIU · SIMULARE" in messages[0]["text"]
    assert "Imagine indisponibilă" in messages[0]["text"]
    assert "1.1000000" in messages[0]["text"] and "MIN" in messages[0]["text"]
    receipt = next(iter(study._read(study._path())["records"].values()))["study_delivery"]["entry"]
    assert (receipt["status"], receipt["format"]) == ("API_ACCEPTED", "TEXT")
    assert "TSP_PHYSICAL_STUDY_CARD_UNAVAILABLE" in capsys.readouterr().out


@pytest.mark.parametrize("legacy_format", [None, "TEXT", "PHOTO"])
def test_legacy_entry_receipts_keep_their_original_study_number(study_setup, legacy_format):
    _, study, delivery, result, _, _, messages, clock = study_setup
    _capture(study_setup)
    numbers = delivery.owner_signal_number
    # Seed the two independent pre-upgrade ledgers with their original API.
    numbers.reserve("earlier-opportunity", BASE)
    canonical_label = numbers.reserve(result.decision.signal_id, BASE)
    original_label = numbers.reserve(result.decision.signal_id, BASE + 32, study=True)
    assert canonical_label.endswith("nr. 1") and original_label.endswith("nr. 0")

    path = study._path()
    state = study._read(path)
    row = next(iter(state["records"].values()))
    row.pop("study_observation")  # persisted pre-upgrade record keeps its original OPEN horizon
    row.pop("buffer_first_hit_time")  # the prospective diagnostic did not exist either
    row.update(entry=_sample(BASE + 32, 1.1), state="OBSERVING")
    receipt = {"status": "API_ACCEPTED", "attempted_ts": BASE + 32,
               "api_accepted_ts": BASE + 32.1, "message_id": 73, "destination_id": 123456789}
    if legacy_format is not None:
        receipt["format"] = legacy_format
    row["study_delivery"]["entry"] = receipt
    study._save(path, state)

    target = BASE + 32 + row["model_seconds"]
    clock[0] = target + 0.1
    study.advance(now_ts=target, active_provider="FINNHUB", price_loader=lambda _: _sample(target, 1.1))

    assert len(messages) == 1 and "REZULTAT STUDIU" in messages[0]["text"]
    assert original_label in messages[0]["text"] and canonical_label not in messages[0]["text"]
    assert messages[0]["reply_to_message_id"] == 73
    assert messages[0]["photo"].startswith(b"\x89PNG\r\n\x1a\n")


def test_frozen_decision_and_declared_diagnostics_cannot_be_rewritten(study_setup):
    _, study, _, _, _, _, _, _ = study_setup
    _capture(study_setup)
    state=study._read(study._path())
    altered=copy.deepcopy(state)
    next(iter(altered["records"].values()))["decision_snapshot"]["market_context"]["buffer_distance"]*=2
    with pytest.raises(ValueError): study.validate(altered)
    altered=copy.deepcopy(state)
    next(iter(altered["records"].values()))["post_model_observations"][0]["horizon_seconds"]+=1
    with pytest.raises(ValueError): study.validate(altered)


def test_old_entries_have_no_retroactive_open_now_intent(study_setup):
    _, study, delivery, _, _, _, messages, _=study_setup
    row=_capture(study_setup,publish=False)
    study.advance(now_ts=BASE+32,active_provider="FINNHUB",price_loader=lambda _: _sample(BASE+32,1.1))
    delivery.dispatch(now_ts=BASE+33,active_provider="FINNHUB")
    assert not messages


def test_old_protocol_is_backed_up_before_upgrade_without_changing_observations(study_setup):
    _, study, _, _, _, _, _, _=study_setup
    _capture(study_setup,publish=False)
    path=study._path()
    old=study._read(path)
    old["protocol"]=study.PREVIOUS_PROTOCOL
    path.write_text(json.dumps(old))
    original=path.read_bytes()
    loaded=study._read(path)
    records=copy.deepcopy(loaded["records"])
    study._save(path,loaded)
    backups=list((path.parent/"protocol_backups").glob("*.json"))
    assert len(backups)==1 and backups[0].read_bytes()==original
    assert study._read(path)["records"]==records
    assert study._read(path)["protocol"]==study.PROTOCOL
    study._save(path,loaded)
    assert len(list((path.parent/"protocol_backups").glob("*.json")))==1


def test_transport_thread_does_not_block_sampling_or_start_a_second_sender(canonical_runtime_root, monkeypatch):
    import threading
    from intelligence import physical_study_delivery as delivery
    entered, release = threading.Event(), threading.Event()
    calls=[]
    def blocked_transport(**kwargs):
        calls.append(kwargs)
        entered.set()
        release.wait(2)
    monkeypatch.setattr(delivery,"dispatch",blocked_transport)
    thread=delivery.dispatch_async(now_ts=BASE,active_provider="FINNHUB")
    assert entered.wait(1)
    assert delivery.dispatch_async(now_ts=BASE+1,active_provider="FINNHUB") is None
    release.set();thread.join(2)
    assert not thread.is_alive() and len(calls)==1


def _report_row(direction, outcome, expiry_price, *, buffer_distance=0.0002):
    """Minimal immutable projection of an observed study for rendering tests."""
    from intelligence import buffer_expiry_evidence

    observation = {"horizon_seconds": 169.0, "duration_seconds": 169,
                   "outcome": outcome, "reason": "OBSERVED_PAIRED_EXPIRY" if expiry_price is not None else "EXPIRY_OBSERVATION_MISSING",
                   "quote": _sample(BASE + 201, expiry_price, buffered=True) if expiry_price is not None else None}
    if observation["quote"] is not None:
        observation["quote"]["source"] = "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1"
    return {"direction": direction, "created_ts": BASE + 31,
            "entry": _sample(BASE + 32, 1.1, buffered=True),
            "study_observation": observation, "candidates": [copy.deepcopy(observation)],
            "buffer_snapshot": buffer_expiry_evidence.snapshot(buffer_distance, "a" * 64),
            "quote_recovery_policy": {"policy": "RETAINED_SOURCE_QUOTE_RECOVERY_V1",
                "arrival_grace_seconds": 15.0, "expiry_window_seconds": 2.0, "entry_window_seconds": 10.0}}


@pytest.mark.parametrize("direction,expiry,outcome,relation,position,margin,edge", [
    ("BUY", 1.1001, "WIN", ">", "În buffer · câștig fragil", "NU", "1.1002"),
    ("BUY", 1.1002, "WIN", ">", "La limita favorabilă", "DA", "1.1002"),
    ("BUY", 1.1003, "WIN", ">", "Dincolo de buffer", "DA", "1.1002"),
    ("BUY", 1.0999, "LOSS", "<", "Dincolo de intrare · pierdere", "NU", "1.1002"),
    ("BUY", 1.1, "DRAW", "=", "La intrare · egalitate", "NU", "1.1002"),
    ("SELL", 1.0999, "WIN", "<", "În buffer · câștig fragil", "NU", "1.0998"),
    ("SELL", 1.0998, "WIN", "<", "La limita favorabilă", "DA", "1.0998"),
    ("SELL", 1.0997, "WIN", "<", "Dincolo de buffer", "DA", "1.0998"),
    ("SELL", 1.1001, "LOSS", ">", "Dincolo de intrare · pierdere", "NU", "1.0998"),
    ("SELL", 1.1, "DRAW", "=", "La intrare · egalitate", "NU", "1.0998"),
])
def test_result_caption_keeps_price_verdict_separate_from_buffer(
    direction, expiry, outcome, relation, position, margin, edge,
):
    from intelligence import physical_study_delivery as delivery

    row = _report_row(direction, outcome, expiry)
    before = copy.deepcopy(row)
    text = delivery.render_result("study", row, "10.11.2026 · nr. 289")
    assert f"Rezultat: {outcome}\n" in text and "Rezultat: WIN fragil" not in text
    assert f"Comparație {direction}: {expiry} {relation} 1.1 → {outcome}" in text
    assert "Intrare colectată: 1.1" in text and f"Cotație expirare colectată: {expiry}" in text
    assert "Surse intrare/expirare: Finnhub memorie / Finnhub arhivă" in text
    assert f"Poziție buffer: {position}" in text
    assert f"Limită buffer: {edge}" in text
    assert f"Marjă completă la expirare: {margin}" in text
    assert row == before


def test_missing_expiry_caption_discloses_evidence_and_ignores_favorable_other_horizons():
    from intelligence import physical_study_delivery as delivery

    row = _report_row("BUY", "UNKNOWN", None)
    row["candidates"][0].update(outcome="WIN", quote=_sample(BASE + 180, 1.2))
    row["post_model_observations"] = [{"outcome": "WIN", "quote": _sample(BASE + 400, 1.3)}]
    before = copy.deepcopy(row)
    text = delivery.render_result("study", row, "10.11.2026 · nr. 289")
    assert "Rezultat: Lipsește cotația la expirare" in text
    assert "UNKNOWN" not in text and "Rezultat: WIN" not in text
    assert "Intrare colectată: 1.1" in text and "Cotație expirare: LIPSĂ" in text
    assert "Comparație: indisponibilă; prețuri incomplete." in text
    assert "Surse intrare/expirare: Finnhub memorie / lipsă" in text
    assert "Interval expirare: 08:03:21 UTC – 08:03:23 UTC" in text
    assert "Poziție buffer: Poziție indisponibilă" in text
    assert "Marjă completă la expirare: DATE INDISPONIBILE" in text
    assert "colectată: 1.2" not in text and "colectată: 1.3" not in text
    assert "Comparație BUY:" not in text
    assert "furnizor" not in text.lower()  # generic absence is not proof of vendor failure
    assert row == before


def test_missing_entry_caption_does_not_invent_an_expiry_timestamp():
    from intelligence import physical_study_delivery as delivery

    row = _report_row("BUY", "UNKNOWN", None)
    row["entry"] = None
    row["study_observation"]["reason"] = "ENTRY_OBSERVATION_MISSING"
    text = delivery.render_result("study", row, None)
    assert "Intrare: LIPSĂ" in text and "Cotație expirare: LIPSĂ" in text
    assert "Expirare declarată: nedeterminată fără intrare" in text
    assert "Interval intrare: 08:00:31 UTC – 08:00:41 UTC" in text
    assert "Interval expirare:" not in text
    assert "Rezultat: Lipsește cotația la intrare" in text and "UNKNOWN" not in text


@pytest.mark.parametrize("direction,expiry", [("BUY", 1.1001), ("SELL", 1.0999)])
def test_missing_buffer_does_not_hide_collected_directional_win(direction, expiry):
    from intelligence import physical_study_delivery as delivery

    row = _report_row(direction, "WIN", expiry, buffer_distance=None)
    text = delivery.render_result("study", row, None)
    assert "Rezultat: WIN\n" in text and "UNKNOWN" not in text
    assert "Intrare colectată: 1.1" in text and f"Cotație expirare colectată: {expiry}" in text
    assert "Limită buffer: LIPSĂ" in text and "Marjă completă la expirare: DATE INDISPONIBILE" in text


def test_comparison_keeps_distinct_prices_and_fractional_target_times_visible():
    import math
    from intelligence import physical_study_delivery as delivery

    expiry = math.nextafter(1.1, math.inf)
    row = _report_row("BUY", "WIN", expiry)
    text = delivery.render_result("study", row, None)
    assert f"Comparație BUY: {expiry} > 1.1 → WIN" in text
    row = _report_row("BUY", "UNKNOWN", None)
    row["study_observation"]["horizon_seconds"] = 169.25
    row["study_observation"].pop("duration_seconds")
    text = delivery.render_result("study", row, None)
    assert "Expirare declarată: 08:03:21.25 UTC" in text
    assert "Interval expirare: 08:03:21.25 UTC – 08:03:23.25 UTC" in text


def test_short_exact_buffer_boundary_does_not_look_equal_to_inside_quote():
    from intelligence import physical_study_delivery as delivery

    row = _report_row("BUY", "WIN", 1.0000000000000002, buffer_distance=2.1e-16)
    row["entry"]["price"] = 1.0
    text = delivery.render_result("study", row, None)
    assert "Comparație BUY: 1.0000000000000002 > 1.0 → WIN" in text
    assert "Limită buffer: 1.00000000000000021\n" in text
    assert "Poziție buffer: În buffer · câștig fragil" in text
    assert "Marjă completă la expirare: NU" in text


def test_long_computed_buffer_boundary_marks_approximation_without_rounding_actual_quotes():
    from intelligence import physical_study_delivery as delivery

    row = _report_row("BUY", "WIN", 1.0000000000000002, buffer_distance=2.1e-200)
    row["entry"]["price"] = 1.0
    text = delivery.render_result("study", row, "🧭" * 128)
    assert "Limită buffer: ~1.0000000000000000 (aprox.)\n" in text
    assert "Comparație BUY: 1.0000000000000002 > 1.0 → WIN" in text
    assert "Poziție buffer: Dincolo de buffer" in text
    assert "Marjă completă la expirare: DA" in text
    assert len(text.encode("utf-16-le")) // 2 <= 1024


@pytest.mark.parametrize("outcome,expiry", [("WIN", 1.1001), ("LOSS", 1.0999), ("DRAW", 1.1), ("UNKNOWN", None)])
def test_result_captions_fit_telegram_with_full_maximum_unicode_signal_label(outcome, expiry):
    import math
    from intelligence import physical_study_delivery as delivery

    row = _report_row("BUY", outcome, expiry)
    entry = 1.2345678901234567e-200
    row["entry"]["price"] = entry
    if expiry is not None:
        row["study_observation"]["quote"]["price"] = {
            "WIN": math.nextafter(entry, math.inf), "LOSS": math.nextafter(entry, 0), "DRAW": entry,
        }[outcome]
    label = "🧭" * 128
    text = delivery.render_result("study", row, label)
    assert len(text.encode("utf-16-le")) // 2 <= 1024
    assert f"{label} · Dublin" in text
    assert "Intrare colectată:" in text and "Surse intrare/expirare:" in text


def test_report_evidence_bounds_unknown_source_and_reason_without_disclosing_raw_content():
    from intelligence import physical_study_delivery as delivery

    row = _report_row("BUY", "UNKNOWN", None)
    row["entry"]["source"] = "PRIVATE_RAW_SOURCE"
    row["study_observation"]["reason"] = "PRIVATE_RAW_EXCEPTION"
    text = delivery.render_result("study", row, None)
    evidence = delivery._result_evidence(row)
    assert "PRIVATE" not in text and "PRIVATE" not in json.dumps(evidence)
    assert evidence["entry_quote_source"] == evidence["observation_reason"] == "UNSPECIFIED"
    assert "Rezultat: Cauza lipsei datelor este indisponibilă" in text and "UNKNOWN" not in text


def test_empty_prospective_cohort_reports_zero_current_delivery_counts(study_setup):
    _, study, _, _, _, _, _, _ = study_setup
    path = study._path()

    startup = study.advance(now_ts=BASE, active_provider="FINNHUB",
                            price_loader=lambda _: None, start_prospective_cohort=True)
    assert startup["unique_entry_experiments"] == 0
    assert not study._study_paths(path)[0].exists()

    report = study.summary(now_ts=BASE)
    assert report["status"] == "WAITING_FIRST_COMPLETE_CHAIN"
    assert report["unique_entry_experiments"] == 0
    assert report["finalized_entry_experiments"] == 0
    assert report["study_open_now_api_accepted"] == 0
    assert report["study_results_api_accepted"] == 0
    assert report["study_delivery_statuses"] == {}
    assert report["historical_delivery_counts"] == {
        "study_open_now_api_accepted": 0, "study_results_api_accepted": 0,
    }


def test_prospective_cutover_preserves_pending_history_and_excludes_old_pre(study_setup):
    _, study, _, _, _, params, messages, clock = study_setup
    original = _capture(study_setup)
    history = study._path()
    entry_time = BASE + 32
    study.advance(now_ts=clock[0], active_provider="FINNHUB",
                  price_loader=lambda _: _sample(entry_time, 1.1))
    assert len(messages) == 1
    historical_before = study._read(history)
    historical_id = next(iter(historical_before["records"]))
    old_receipt = historical_before["records"][historical_id]["study_delivery"]["entry"]
    assert old_receipt["status"] == "API_ACCEPTED"

    cutover = BASE + 40
    startup = study.advance(now_ts=cutover, active_provider="FINNHUB",
                            price_loader=lambda _: None, start_prospective_cohort=True)
    assert startup["prospective_cohort"] == {"revision": study.COHORT_REVISION, "starts_at": cutover}
    assert startup["unique_entry_experiments"] == 0
    assert study._read(history) == historical_before

    def candidate(identity, pre):
        return {
            "policy": "PHYSICAL_ONLY_V3", "direction": "BUY",
            "opportunity_signal_id": identity, "created_ts": pre + 31, "open_ts": pre + 31,
            "pre_ts": pre, "confirm_ts": pre + 2, "confirm_model_seconds": 120,
            "model_seconds": 120, "adjusted_seconds": 100, "buffer_distance": 0.0002,
        }

    study.capture([candidate("sig-v3-before-cutover", cutover - 1),
                   candidate("sig-v3-after-cutover", cutover + 1)],
                  params=params, buffer_mode="SMALL", strategy_version="3.0.0",
                  canonical_spec="V3_SCORELESS_OWNER_AMENDMENT_v1.1.0", now_ts=cutover + 32)
    active = study._study_paths(history)[0]
    new_state = study._read(active)
    assert new_state["scope"]["prospective_cohort"] == startup["prospective_cohort"]
    assert new_state["scope"]["parameter_sha256"] == historical_before["scope"]["parameter_sha256"]
    assert len(new_state["records"]) == 1
    assert next(iter(new_state["records"].values()))["policies"]["PHYSICAL_ONLY_V3"][
        "opportunity_signal_id"] == "sig-v3-after-cutover"
    assert study._read(history) == historical_before

    expiry = entry_time + study.displayed_study_observation(original)["horizon_seconds"]
    clock[0] = expiry
    study.advance(now_ts=expiry, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(expiry, 1.1003), start_prospective_cohort=True)
    historical_after = study._read(history)
    row = historical_after["records"][historical_id]
    assert row["study_delivery"]["entry"] == old_receipt
    assert row["study_delivery"]["result"]["status"] == "API_ACCEPTED"
    assert study.displayed_study_observation(row)["outcome"] == "WIN"
    assert len(messages) == 2

    report = study.summary(now_ts=expiry)
    assert report["prospective_cohort"]["starts_at"] == cutover
    assert report["unique_entry_experiments"] == 1
    assert report["policies"][0]["train_entries"] == 1
    assert report["study_open_now_api_accepted"] == 0
    assert report["historical_delivery_counts"] == {
        "study_open_now_api_accepted": 1, "study_results_api_accepted": 1,
    }


def test_exact_source_cutover_keeps_bucket_records_and_uses_fractional_targets(study_setup):
    _, study, _, _, _, params, messages, _ = study_setup
    path = study._path()
    def sample_at(stamp, price, *, received=None):
        return {**_sample(stamp, price, buffered=True), "provider_tick_ms": round(stamp * 1000),
                "received_ts": stamp if received is None else received}
    def advance(now, *, precise=None, legacy=None, start=False):
        return study.advance(now_ts=now, active_provider="FINNHUB", price_loader=lambda _: None,
                             observation_loader=legacy, precise_observation_loader=precise,
                             start_prospective_cohort=start)
    def capture(pre, identity):
        created = pre + 31
        study.capture([{"policy": "PHYSICAL_ONLY_V3", "direction": "BUY",
            "opportunity_signal_id": identity, "created_ts": created, "open_ts": created,
            "pre_ts": pre, "confirm_ts": pre + 2, "confirm_model_seconds": 120,
            "model_seconds": 120, "adjusted_seconds": 100, "buffer_distance": 0.0002}],
            params=params, buffer_mode="SMALL", strategy_version="3.0.0",
            canonical_spec="V3_SCORELESS_OWNER_AMENDMENT_v1.1.0", now_ts=created)
        return created

    advance(BASE, start=True)
    old_open = capture(BASE + 1, "sig-v3-bucket")
    advance(old_open + 1, legacy=lambda *_: _sample(old_open + 1, 1.1, buffered=True))
    bucket_path = study._study_paths(path)[0]
    bucket_before = study._read(bucket_path)
    def unavailable(*_):
        return None

    cutover = BASE + 40
    report = advance(cutover, precise=unavailable, start=True)
    assert report["prospective_cohort"]["revision"] == study.PRECISE_COHORT_REVISION
    capture(cutover - 1, "sig-v3-pre-cutover")
    assert study._read(bucket_path) == bucket_before
    new_open = capture(cutover + 1, "sig-v3-precise")
    active = study._study_paths(path)[0]
    def observe(now, precise):
        advance(now, precise=precise, legacy=unavailable)
        return next(iter(study._read(active)["records"].values()))
    entry = new_open + .192
    assert observe(new_open + .2, lambda *_: _sample(new_open, 1.09, buffered=True))["entry"] is None
    assert observe(new_open + .2, lambda *_: sample_at(entry, 1.1, received=new_open + 1))["entry"] is None
    assert observe(new_open + 1, lambda *_: sample_at(entry, 1.1))["entry"]["observed_ts"] == entry
    old_expiry = old_open + 121
    advance(old_expiry, precise=unavailable, legacy=lambda symbol, target, delay:
            _sample(old_expiry, 1.101, buffered=True) if target == old_expiry else None)
    expiry = entry + 120
    assert observe(expiry + 2.5, lambda *_: sample_at(expiry + 2.456, 1.2))["candidates"][0]["outcome"] == "PENDING"
    saved = observe(expiry + 3, lambda *_: sample_at(expiry + .25, 1.101))
    assert saved["candidates"][0]["outcome"] == "WIN"
    assert saved["candidates"][0]["quote"]["provider_tick_ms"] == round((expiry + .25) * 1000)
    old = next(iter(study._read(bucket_path)["records"].values()))
    assert old["entry"] == next(iter(bucket_before["records"].values()))["entry"]
    assert "provider_tick_ms" not in old["entry"]
    assert old["candidates"][0]["outcome"] == "WIN"
    assert "provider_tick_ms" not in old["candidates"][0]["quote"]
    assert not messages
