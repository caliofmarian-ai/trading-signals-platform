"""Synthetic end-to-end evidence. No market-performance or broker claim."""
from copy import deepcopy
import hashlib
import json

import pytest

BASE = 1_800_000_000


@pytest.fixture
def seconds_pipeline(canonical_runtime_root, monkeypatch):
    for key, value in {"OWNER_SIGNAL_DELIVERY_ENABLED": "true", "OWNER_TELEGRAM_ID": "123456789",
            "SHADOW_MODE": "true", "SHADOW_MODEL_TIME_RESEARCH_ENABLED": "true",
            "ENABLE_BROKER_EXECUTION": "false", "MARKET_DATA_PROVIDER": "FINNHUB"}.items():
        monkeypatch.setenv(key, value)
    from core import confirmed_study_duration as plans, owner_signal_delivery as owner
    from core import distribution_router_v3 as router, telegram_publisher
    from core.physical_params import migrate_physical_params
    from intelligence import physical_expiry_calibration as study, physical_study_delivery as delivery
    from state_store import state_store as state_store

    params = migrate_physical_params(json.loads((canonical_runtime_root / "config" / "algo_params.json").read_text()))
    clock, photos = [BASE + .1], []
    monkeypatch.setattr(owner.time, "time", lambda: clock[0])
    def photo(**kwargs):
        photos.append(kwargs)
        return {"ok": True, "result": {"message_id": len(photos)}}
    monkeypatch.setattr(telegram_publisher, "send_photo", photo)
    monkeypatch.setattr(telegram_publisher, "send_message", lambda **_: pytest.fail("expected photo transport"))
    monkeypatch.setattr(delivery, "dispatch_async", lambda **kw: delivery.dispatch(**kw))
    return dict(root=canonical_runtime_root, params=params, clock=clock, photos=photos,
                plans=plans, owner=owner, router=router, study=study, delivery=delivery,
                store=state_store, state=state_store.default_fsm_state())


def _step(ctx, stage, offset, *, needed=8.6, new_policy=True, publish=True):
    from tests.canonical.unit.test_confirmed_execution_duration import _decision
    from core.execution_model import derive_execution_time
    from core.fsm_decision_adapter import interpret_decision
    from core.v2_fsm_orchestrator import advance_persistent_fsm, bind_confirmed_execution_time
    from core.signal_event import build_signal_event

    now = BASE + offset
    ctx["clock"][0] = now + .1
    decision = _decision(stage, now, model=10.0, needed=needed)
    if new_policy:
        decision = ctx["plans"].annotate_decision(decision, ctx["params"])
    execution = derive_execution_time(decision, interpret_decision(decision))
    handoff = advance_persistent_fsm(ctx["state"], decision, now_ts=now)
    handoff, execution = bind_confirmed_execution_time(handoff, decision, execution)
    assert handoff.stage_handoff_ready
    ctx["store"].save_fsm_state(handoff.next_state)
    ctx["state"] = ctx["store"].load_fsm_state()  # actual persistence/reload boundary
    if stage in {"PRE", "CONFIRM"} and publish:
        event = build_signal_event(decision, buffer_mode="SMALL", created_ts=now,
                                   execution_time=execution).to_dict()
        event = ctx["owner"].project_confirmed_study(event, handoff)
        summary = ctx["router"].route(event, now_ts=now)
        assert summary["published_count"] == 1
        ctx.setdefault("events", []).append(event)
    return decision, handoff, execution


def _capture(ctx, *, needed=8.6):
    decision, handoff, execution = _step(ctx, "OPEN_NOW", 35, needed=needed)
    assert not execution.available  # this experiment cannot activate execution
    assert ctx["study"].observe_accepted_chain(decision, handoff, ctx["params"],
        now_ts=BASE + 35, provider="FINNHUB", buffer_mode="SMALL", publish_study=True)
    return next(iter(ctx["study"]._read(ctx["study"]._study_paths(ctx["study"]._path())[0])["records"].values()))


def _sample(stamp, price):
    return {"provider": "FINNHUB", "symbol": "EUR/USD", "price": price,
            "observed_ts": float(stamp), "source": "LIVE_STREAM_CURRENT_M1_CLOSE"}


def _advance(ctx, stamp, price):
    ctx["clock"][0] = stamp + .1
    ctx["study"].advance(now_ts=stamp, active_provider="FINNHUB",
                        price_loader=lambda _: _sample(stamp, price) if price is not None else None)
    return next(iter(ctx["study"]._read(ctx["study"]._study_paths(ctx["study"]._path())[0])["records"].values()))


def test_confirm_photo_open_result_chart_and_summary_use_one_primary_seconds_plan(seconds_pipeline, monkeypatch):
    ctx = seconds_pipeline
    _step(ctx, "PRE", 0)
    decision, _, _ = _step(ctx, "CONFIRM", 3)
    event = ctx["events"][-1]
    assert event["study_duration_seconds"] == 516
    assert event["study_duration_minutes"] == 8.6
    assert event["study_duration_policy"] == ctx["plans"].POLICY
    label = ctx["router"].owner_signal_number.lookup_lifecycle(decision.signal_id)
    assert label and label.endswith("nr. 0")
    receipt_ledger = json.loads(ctx["owner"]._timing_path().read_text())
    receipt = next(iter(receipt_ledger["opportunities"].values()))["CONFIRM"]
    assert receipt["format"] == "PHOTO" and ctx["plans"].matching_receipt(event, receipt)
    frozen = deepcopy(ctx["state"]["per_symbol"]["EUR/USD"][ctx["plans"].PLAN_FIELD])
    captured = _capture(ctx, needed=8.5)  # fresh requirement changed, confirmed duration did not
    assert captured["model_seconds"] == 600
    assert captured["study_observation"]["horizon_seconds"] == 516
    saved = _advance(ctx, BASE + 36, 1.1)
    projected = ctx["delivery"]._entry_event(saved)
    assert projected["study_duration_seconds"] == 516
    assert projected["expiry_ts"] == BASE + 36 + 516
    assert projected["study_plan_id"] == frozen["plan_id"]
    assert len(ctx["photos"]) == 3
    assert all("#0" in call["caption"] for call in ctx["photos"])
    assert all(call["photo"].startswith(b"\x89PNG") for call in ctx["photos"])
    from core.signal_card import build_card_fields
    assert build_card_fields(event, label, study=True)["duration"] == "8 MIN 36 S"
    assert build_card_fields(projected, label, study=True)["duration"] == "8 MIN 36 S"
    from intelligence import physical_study_chart
    chart_calls = []
    monkeypatch.setattr(physical_study_chart, "render_market_chart",
                        lambda **kw: chart_calls.append(kw) or b"\x89PNG\r\n\x1a\nsynthetic-chart")
    expiry = BASE + 36 + 516
    saved = _advance(ctx, expiry, 1.1025)
    assert saved["study_observation"]["outcome"] == "WIN"
    assert saved["candidates"][0]["outcome"] == "PENDING"  # research grid is still independent
    assert len(ctx["photos"]) == 4
    assert ctx["photos"][-1]["reply_to_message_id"] == 3
    assert "8 MIN 36 S" in ctx["photos"][-1]["caption"]
    assert "Rezultat: WIN" in ctx["photos"][-1]["caption"]
    assert chart_calls[0]["expiry_ts"] == expiry and chart_calls[0]["outcome"] == "WIN"
    assert saved["study_observation"]["duration_plan"] == frozen
    report = ctx["study"].summary(now_ts=expiry)
    assert report["published_study_results_by_duration_policy"][ctx["plans"].POLICY]["wins"] == 1
    assert report["baseline_model_observations"]["wins"] == 0
    assert not report["execution_calibration_proven"] and not report["broker_executed"]


def test_new_second_plan_never_replaces_a_preexisting_minute_chain(seconds_pipeline):
    ctx = seconds_pipeline
    _step(ctx, "PRE", 0, new_policy=False)
    _step(ctx, "CONFIRM", 3, new_policy=True)
    event = ctx["events"][-1]
    assert event["study_duration_minutes"] == 10
    assert "study_duration_seconds" not in event
    captured = _capture(ctx)
    assert "duration_policy" not in captured["study_observation"]
    saved = _advance(ctx, BASE + 36, 1.1)
    assert ctx["delivery"]._entry_event(saved)["expiry_ts"] == BASE + 36 + 600
    assert len(ctx["photos"]) == 3


def test_new_seconds_plan_invalidated_by_fresh_physics_does_not_open(seconds_pipeline):
    ctx = seconds_pipeline
    _step(ctx, "PRE", 0)
    _step(ctx, "CONFIRM", 3)
    captured = _capture(ctx, needed=9.1)
    assert captured["study_observation"]["outcome"] == "INFEASIBLE"
    saved = _advance(ctx, BASE + 36, 1.1)
    assert len(ctx["photos"]) == 2
    assert saved["study_delivery"]["entry"]["status"] == "SKIPPED_DURATION_INFEASIBLE"
    assert saved["study_observation"]["duration_seconds"] == 516


@pytest.mark.parametrize("field,value", [("study_duration_seconds", 517),
    ("study_duration_policy", None), ("study_plan_id", "b" * 64), ("study_confirmed_ts", BASE + 4)])
def test_second_plan_requires_the_exact_actual_confirm_receipt(seconds_pipeline, field, value):
    ctx = seconds_pipeline
    _step(ctx, "PRE", 0)
    _step(ctx, "CONFIRM", 3)
    path = ctx["owner"]._timing_path()
    ledger = json.loads(path.read_text())
    next(iter(ledger["opportunities"].values()))["CONFIRM"][field] = value
    ctx["owner"].storage.save_json_atomic(str(path), ledger)
    _capture(ctx)
    saved = _advance(ctx, BASE + 36, 1.1)
    assert len(ctx["photos"]) == 2
    assert saved["study_delivery"]["entry"]["status"] == "SKIPPED_STAGE_GUARD"


def test_new_seconds_expiry_without_quote_remains_unknown_not_a_later_win(seconds_pipeline):
    ctx = seconds_pipeline
    _step(ctx, "PRE", 0)
    _step(ctx, "CONFIRM", 3)
    _capture(ctx)
    _advance(ctx, BASE + 36, 1.1)
    expiry = BASE + 36 + 516
    saved = _advance(ctx, expiry + ctx["study"].quotes.MAX_SAMPLE_DELAY_SECONDS + 1, None)
    assert saved["study_observation"]["outcome"] == "UNKNOWN"
    assert saved["study_observation"]["quote"] is None
    saved = _advance(ctx, expiry + 20, 1.2)
    assert saved["study_observation"]["outcome"] == "UNKNOWN"
    report = ctx["study"].summary(now_ts=expiry + 20)
    assert report["published_study_results_by_duration_policy"][ctx["plans"].POLICY]["unknown"] == 1


def test_live_strategy_emits_prospective_seconds_candidate_without_changing_physical_gates(canonical_runtime_root):
    from tests.canonical.integration.test_binary_strategy_v2 import _inputs
    from core.physical_params import migrate_physical_params
    from core.strategy_v3 import decide
    from core import confirmed_study_duration as plans
    m1, m5, old = _inputs(canonical_runtime_root)
    params = migrate_physical_params(old)
    evaluation = decide(m1, m5, params, buffer_mode="SMALL", observation_ts=BASE)
    assert evaluation.decision.kind == "PRE"
    candidate = evaluation.decision.fsm_inputs["study_duration_candidate"]
    plans.validate_candidate(candidate)
    assert candidate["adjusted_minutes"] == evaluation.time.context.t_needed_adjusted
    assert candidate["duration_seconds"] <= evaluation.time.context.model_expiry * 60
    assert evaluation.decision.score.total is None
    assert not evaluation.execution_time.available


def test_periodic_report_separates_new_seconds_results_from_old_minutes(canonical_runtime_root, monkeypatch):
    from tests.canonical.unit.test_owner_timing_session import _prepare, _observe
    module = _prepare(monkeypatch)
    from core import physical_params, telegram_publisher, confirmed_study_duration as plans
    from intelligence import physical_expiry_calibration
    sent = []
    monkeypatch.setattr(physical_params, "physical_runtime_enabled", lambda: True)
    monkeypatch.setattr(telegram_publisher, "send_message", lambda **kw: sent.append(kw) or {"ok": True})
    monkeypatch.setattr(physical_expiry_calibration, "summary", lambda **kw: {
        "study_open_now_api_accepted": 161, "study_results_api_accepted": 161,
        "published_study_results": {"wins": 100, "losses": 50, "draws": 1, "unknown": 10},
        "published_study_results_by_duration_policy": {
            plans.POLICY: {"wins": 2, "losses": 1, "draws": 1, "unknown": 3},
            plans.LEGACY_POLICY: {"wins": 98, "losses": 49, "draws": 0, "unknown": 7}},
    })
    _observe(module, 1000)
    report = module.report_if_due(now_ts=1001)
    text = sent[0]["text"]
    assert "Total istoric · 161 rezultate: WIN 100, LOSS 50, DRAW 1, UNKNOWN 10" in text
    assert "La secundă · 7 rezultate: WIN 2, LOSS 1, DRAW 1, UNKNOWN 3" in text
    assert "Istoric · minute întregi · 154 rezultate: WIN 98, LOSS 49, DRAW 0, UNKNOWN 7" in text
    assert "Cotație la expirare: 4/7" in text
    assert text.index("La secundă") < text.index("Istoric · minute") < text.index("Total istoric")
    assert report["study_results_by_duration_policy"][plans.POLICY]["wins"] == 2


@pytest.mark.parametrize("open_needed,rescued", [(8.59, False), (8.63, True)])
def test_prospective_reserve_is_separate_from_actual_open_and_baseline(seconds_pipeline, open_needed, rescued):
    ctx = seconds_pipeline
    study = ctx["study"]
    study.advance(now_ts=BASE - 1, active_provider="FINNHUB",
                  price_loader=lambda _: None, start_prospective_cohort=True)
    _step(ctx, "PRE", 0)
    _step(ctx, "CONFIRM", 3)
    captured = _capture(ctx, needed=open_needed)
    assert captured["study_observation"]["horizon_seconds"] == 516
    assert captured["confirm_duration_reserve"]["horizon_seconds"] == 519
    assert captured["confirm_duration_reserve"]["outcome"] == "PENDING"
    assert captured["candidates"][0]["horizon_seconds"] == 600

    entry = BASE + 36
    _advance(ctx, entry, 1.1)
    sent_at_open = len(ctx["photos"])
    assert sent_at_open == (2 if rescued else 3)
    saved = _advance(ctx, entry + 516, 1.1)
    assert saved["study_observation"]["outcome"] == ("INFEASIBLE" if rescued else "DRAW")
    assert saved["confirm_duration_reserve"]["outcome"] == "PENDING"
    sent_at_control_expiry = len(ctx["photos"])
    assert sent_at_control_expiry == (2 if rescued else 4)

    saved = _advance(ctx, entry + 519, 1.105)
    assert saved["confirm_duration_reserve"]["outcome"] == "WIN"
    assert saved["candidates"][0]["outcome"] == "PENDING"
    assert len(ctx["photos"]) == sent_at_control_expiry
    evidence = study.summary(now_ts=entry + 519)["confirm_duration_reserve_diagnostic"]
    assert evidence["duration_gate_rescues"] == int(rescued)
    assert evidence["paired_real_quote_count"] == int(not rescued)
    assert evidence["reserve_on_all_chains"]["wins"] == 1
    assert evidence["reserve_on_all_chains"]["buffer_met"] == 1
    assert not evidence["publication_authority"] and not evidence["calibration_authority"]


def test_reserve_requires_original_confirm_receipt_in_prospective_cohort(seconds_pipeline):
    ctx = seconds_pipeline
    ctx["study"].advance(now_ts=BASE - 1, active_provider="FINNHUB",
                         price_loader=lambda _: None, start_prospective_cohort=True)
    _step(ctx, "PRE", 0)
    _step(ctx, "CONFIRM", 3, publish=False)
    assert "confirm_duration_reserve" not in _capture(ctx)


@pytest.mark.parametrize("needed,seconds,blocked", [(8.50, 510, False), (8.60, 516, False), (8.63, 518, True)])
def test_market_duration_uses_fresh_open_calculation_and_keeps_confirmed_plan(
    seconds_pipeline, needed, seconds, blocked
):
    ctx = seconds_pipeline
    study = ctx["study"]
    samples = {}
    lookups = []

    def loader(symbol, target, delay):
        lookups.append((target, delay))
        return samples.get(target)

    def advance(now, *, start=False):
        ctx["clock"][0] = now + .1
        study.advance(now_ts=now, active_provider="FINNHUB", price_loader=lambda _: None,
                      precise_observation_loader=loader, start_prospective_cohort=start)
        active = study._study_paths(study._path())[0]
        return study._read(active)

    def quote(timestamp, price):
        return {**_sample(timestamp, price), "source": "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1",
                "provider_tick_ms": round(timestamp * 1000), "received_ts": timestamp}

    advance(BASE - 1, start=True)
    _step(ctx, "PRE", 0)
    _step(ctx, "CONFIRM", 3)
    captured = _capture(ctx, needed=needed)
    assert captured["study_observation"]["horizon_seconds"] == 516
    assert captured["candidates"][0]["horizon_seconds"] == 600
    assert captured["confirm_duration_reserve"]["horizon_seconds"] == 519
    assert captured["open_market_duration"]["horizon_seconds"] == seconds

    entry = BASE + 35.2
    samples[BASE + 35] = quote(entry, 1.1)
    advance(entry + .1)
    assert len(ctx["photos"]) == (2 if blocked else 3)
    target = entry + seconds
    samples[target] = quote(target + 2.001, 1.105)
    row = next(iter(advance(target + 3)["records"].values()))
    assert row["open_market_duration"]["outcome"] == "PENDING"

    # A favorable close can use part of B and still be a directional win.
    distance = captured["buffer_snapshot"]["buffer_distance"]
    close = 1.1 + distance * (.5 if blocked else 2)
    samples[target] = quote(target + .25, close)
    lookups.clear()
    row = next(iter(advance(target + 4)["records"].values()))
    assert lookups.count((target, 2)) == 1
    assert row["open_market_duration"]["outcome"] == "WIN"
    assert row["open_market_duration"]["quote"]["provider_tick_ms"] == round((target + .25) * 1000)
    assert row["study_observation"]["outcome"] == (
        "INFEASIBLE" if blocked else "WIN" if seconds == 516 else "PENDING")
    assert row["candidates"][0]["outcome"] == "PENDING"
    assert len(ctx["photos"]) == (2 if blocked else 4 if seconds == 516 else 3)
    diagnostic = study.summary(now_ts=target + 4)["open_market_duration_diagnostic"]
    assert diagnostic["observed_open_chains"] == diagnostic["market_duration_feasible"] == 1
    assert diagnostic["confirmed_duration_blocked"] == int(blocked)
    assert diagnostic["market_on_all_chains"]["wins"] == 1
    assert diagnostic["market_on_all_chains"]["buffer_met"] == int(not blocked)
    assert diagnostic["market_on_all_chains"]["win_buffer_not_met"] == int(blocked)
    assert not diagnostic["publication_authority"] and not diagnostic["calibration_authority"]
