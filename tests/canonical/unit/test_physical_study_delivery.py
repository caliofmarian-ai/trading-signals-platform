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
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    from core import owner_signal_delivery as owner
    from intelligence import physical_expiry_calibration as study, physical_study_delivery as delivery
    m1, m5, old = _inputs(canonical_runtime_root)
    params, state = migrate_physical_params(old), default_fsm_state()
    for now in (BASE, BASE+2, BASE+31):
        result = decide(m1, m5, params, buffer_mode="SMALL",
                        context=lifecycle_context(state, "EUR/USD", now_ts=now))
        handoff = advance_persistent_fsm(state, result.decision, now_ts=now)
        state = handoff.next_state
    assert handoff.accepted_stage == "OPEN_NOW"
    key = hashlib.sha256(result.decision.signal_id.encode()).hexdigest()
    owner.storage.save_json_atomic(str(owner._timing_path()), {"schema_version":"1.0.0", "opportunities":{
        key: {"PRE":{"api_accepted_ts": BASE+.1}, "CONFIRM":{"api_accepted_ts":BASE+2.1}}}})
    messages = []
    clock = [BASE+32.1]
    monkeypatch.setattr(delivery.time, "time", lambda: clock[0])
    def transport(**kwargs):
        messages.append(kwargs)
        return {"ok":True, "result":{"message_id":len(messages)}}
    monkeypatch.setattr(delivery.telegram_publisher, "send_message", transport)
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


def test_complete_physical_chain_publishes_explicit_study_and_distinct_buffer_result(study_setup):
    _, study, delivery, result, _, _, messages, clock = study_setup
    row = _capture(study_setup)
    study.advance(now_ts=BASE+32, active_provider="FINNHUB", price_loader=lambda _: _sample(BASE+32,1.1))
    assert len(messages) == 1
    assert messages[0]["chat_id"] == 123456789
    assert "OPEN_NOW · STUDIU" in messages[0]["text"] and "Expirare simulată" in messages[0]["text"]
    assert "calibrare în colectare" in messages[0]["text"]
    assert "Score" not in messages[0]["text"] and "TPS" not in messages[0]["text"]
    from core import owner_signal_delivery as owner
    ledger = json.loads(owner._timing_path().read_text())
    assert all("OPEN_NOW" not in stages for stages in ledger["opportunities"].values())
    direction = 1 if row["direction"] == "BUY" else -1
    target = BASE+32+row["model_seconds"]
    clock[0] = target+.1
    price = 1.1 + direction*row["buffer_snapshot"]["buffer_distance"]*.5
    study.advance(now_ts=target, active_provider="FINNHUB", price_loader=lambda _: _sample(target,price))
    assert len(messages) == 2 and "REZULTAT STUDIU" in messages[1]["text"]
    assert "Direcție la expirare: WIN" in messages[1]["text"]
    assert "Buffer la expirare: NEATINS" in messages[1]["text"]
    report = study.summary(now_ts=target)
    assert report["study_open_now_api_accepted"] == report["study_results_api_accepted"] == 1
    assert report["actual_telegram_publications"] == 0 and not report["execution_calibration_proven"]
    assert report["decision_snapshot_entries"] == 1
    saved = next(iter(study._read(study._path())["records"].values()))
    assert saved["decision_snapshot"]["decision_id"] == result.decision.decision_id
    assert saved["decision_snapshot"]["indicators"]["atr_m5"] == result.market.evidence.atr_m5
    # A later buffer hit remains a diagnostic; the original label stays unchanged.
    later = target+60
    clock[0] = later+.1
    study.advance(now_ts=later, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(later,1.1+direction*row["buffer_snapshot"]["buffer_distance"]*1.5))
    assert study.summary(now_ts=later)["post_model_diagnostics"][0]["buffer_met"] == 1
    assert study.summary(now_ts=later)["baseline_model_observations"]["buffer_not_met"] == 1
    assert len(messages) == 2


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
    clock[0] = target+10
    study.advance(now_ts=target+10, active_provider="FINNHUB", observation_loader=lambda *a: None,
                  price_loader=lambda _: _sample(target+10,1.2))
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
    monkeypatch.setattr(delivery.telegram_publisher,"send_message",uncertain)
    study.advance(now_ts=BASE+32,active_provider="FINNHUB",price_loader=lambda _: _sample(BASE+32,1.1))
    clock[0]=BASE+33
    delivery.dispatch(now_ts=BASE+33,active_provider="FINNHUB")
    assert len(calls)==1
    saved=next(iter(study._read(study._path())["records"].values()))
    assert saved["study_delivery"]["entry"]["status"]=="UNKNOWN"


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
