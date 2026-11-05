from __future__ import annotations

import copy
import importlib
import json
from collections import Counter

import pytest

from tests.canonical.integration.test_binary_strategy_v2 import _inputs


def _prepare(root, monkeypatch):
    for key, value in {"OWNER_SIGNAL_DELIVERY_ENABLED": "true", "OWNER_TELEGRAM_ID": "123456789",
                       "OWNER_TIMING_SESSION_ID": "owner-live-severity", "SHADOW_MODE": "true",
                       "SHADOW_MODEL_TIME_RESEARCH_ENABLED": "true", "ENABLE_BROKER_EXECUTION": "false"}.items():
        monkeypatch.setenv(key, value)
    from core.strategy_v2 import decide
    m1, m5, params = _inputs(root)
    result = decide(m1, m5, params, cycle_id="live-grid-test", buffer_mode="SMALL")
    return importlib.import_module("intelligence.live_score_severity_research"), result, params


def test_all_live_levels_reuse_canonical_evidence_without_mutating_production(canonical_runtime_root, monkeypatch, capsys):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    original, parameters = evaluation.decision.to_dict(), copy.deepcopy(params)
    source_files = {str(p): p.read_bytes() for p in canonical_runtime_root.rglob("*") if p.is_file()}
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    report = module.summary(now_ts=1001)
    assert report["status"] == "OBSERVING" and len(report["levels"]) == 21
    assert all(row["evaluations"] == 1 for row in report["levels"])
    expected_kind = "PRE" if evaluation.decision.kind in module.STAGES else evaluation.decision.kind
    assert report["levels"][14]["decision_kinds"] == {expected_kind: 1}
    assert report["actual_telegram_publications"] == 0 and report["broker_executed"] is False
    assert report["automatic_selection_allowed"] is False
    assert evaluation.decision.to_dict() == original and params == parameters
    for path, raw in source_files.items():
        assert open(path, "rb").read() == raw
    new_files = [p for p in canonical_runtime_root.rglob("*") if p.is_file() and str(p) not in source_files]
    assert len(new_files) == 1 and "live_score_severity_continuous" in str(new_files[0])
    output = capsys.readouterr().out
    assert "TSP_LIVE_SCORE_SEVERITY" in output and "fsm_state" not in output
    assert "opportunities" not in output and "sig-v2-" not in output


def test_fast_projection_matches_full_canonical_pipeline_at_every_level(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    from core.strategy_v2 import decide
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    m1, m5, _ = _inputs(canonical_runtime_root)
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    report = module.summary(now_ts=1001)
    for row in report["levels"]:
        candidate = copy.deepcopy(params)
        candidate["score_thresholds"] = row["score_thresholds"]
        full = decide(m1, m5, candidate, cycle_id="live-grid-test", buffer_mode="SMALL")
        from core.decision_assembly import assemble_decision
        requested = assemble_decision(full.market, full.corridor, full.time, full.scoring,
            timeframe="M1", cycle_id="live-grid-test", maximum_stage="PRE")
        handoff = advance_persistent_fsm(default_fsm_state(), requested, now_ts=1000)
        assert row["decision_kinds"] == {requested.kind: 1}
        assert row["fsm_reason_families"] == {handoff.reason_family: 1}
        assert row["blockers"] == dict(Counter(full.decision.reject.hard_blockers))
        expected = {handoff.accepted_stage: 1} if handoff.stage_handoff_ready else {}
        assert row["accepted_unique_stages"] == expected


def test_permissive_scores_request_complete_ordered_chain_before_paper_entry(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    from dataclasses import replace
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    from tests.canonical.unit.test_shadow_model_time_research import _opportunity, _sample
    # A READY, high-scoring opportunity does not need a broker or execution
    # calibration to go through all research stages and produce paper evidence.
    opening, _ = _opportunity()
    row = module._new(params, evaluation, 1000, "SMALL")["levels"][0]
    fsm = default_fsm_state()
    for stamp, expected in ((1062, "PRE"), (1064, "CONFIRM"), (1070, "CONFIRM"), (1092, "OPEN_NOW")):
        maximum = module._maximum_stage(row, fsm, "EUR/USD", stamp, "BUY")
        assert maximum == expected
        # Stage capping in assembly uses identical score/structure/time; this
        # fixture supplies a ready score directly so every stage is affordable.
        decision = replace(opening, kind=maximum)
        handoff = advance_persistent_fsm(fsm, decision, now_ts=stamp)
        fsm = handoff.next_state
        module._observe_accepted_stage(row, decision, handoff, stamp)
    assert row["complete_ordered_chains"] == 1
    assert row["stage_gap_samples"][0]["pre_to_open_seconds"] == 30
    assert len(row["paper_trades"]["trades"]) == 1
    assert module._maximum_stage(row, fsm, "EUR/USD", 1100, "SELL") == "PRE"
    row.update(evaluations=4, decision_kinds={"PRE": 1, "CONFIRM": 2, "OPEN_NOW": 1},
               fsm_reason_families={"STAGE_ACCEPTED": 3, "DUPLICATE": 1})
    state = module._new(params, evaluation, 1000, "SMALL")
    state["levels"][0] = row
    module._save(module._path(), state)
    module.advance_paper_trades(now_ts=1093, active_provider="FINNHUB", price_loader=lambda _: _sample(1093))
    module.advance_paper_trades(now_ts=1213, active_provider="FINNHUB", price_loader=lambda _: _sample(1213, 1.2))
    report = module.summary(now_ts=1214)
    assert report["levels"][0]["paper_trades"]["outcomes"]["WIN"] == 1
    assert report["actual_telegram_publications"] == 0


def test_paper_expiry_settles_across_old_deadline_and_survives_reload(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    from tests.canonical.unit.test_shadow_model_time_research import _opportunity, _sample
    state = module._new(params, evaluation, 1000, "SMALL")
    decision, handoff = _opportunity(candle_ts=8100)
    assert module.paper.register(state["levels"][0]["paper_trades"], decision, handoff, now_ts=8190)
    module._save(module._path(), state)
    module.advance_paper_trades(now_ts=8191, active_provider="FINNHUB", price_loader=lambda _: _sample(8191))
    assert module.summary(now_ts=8201)["status"] == "OBSERVING"
    module = importlib.reload(module)
    module.advance_paper_trades(now_ts=8311, active_provider="FINNHUB", price_loader=lambda _: _sample(8311, 1.2))
    report = module.summary(now_ts=8312)
    assert report["status"] == "OBSERVING" and report["deadline_ts"] is None
    assert report["levels"][0]["evaluations"] == 0
    assert report["levels"][0]["paper_trades"]["outcomes"]["WIN"] == 1


def test_stage_ceiling_never_promotes_or_changes_default_strategy_evidence(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    from core.decision_assembly import assemble_decision
    original = evaluation.decision.to_dict()
    capped = assemble_decision(evaluation.market, evaluation.corridor, evaluation.time,
        evaluation.scoring, timeframe="M1", cycle_id=evaluation.cycle_id, maximum_stage="PRE")
    assert capped.score == evaluation.decision.score
    assert capped.reject == evaluation.decision.reject
    assert capped.time == evaluation.decision.time
    assert evaluation.decision.to_dict() == original
    expected = "PRE" if evaluation.decision.kind in module.STAGES else evaluation.decision.kind
    assert capped.kind == expected
    with pytest.raises(ValueError):
        assemble_decision(evaluation.market, evaluation.corridor, evaluation.time,
            evaluation.scoring, timeframe="M1", cycle_id=evaluation.cycle_id, maximum_stage="INVALID")


def test_full_canonical_pipeline_at_all_levels_produces_paper_outcomes_without_calibration(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    from tests.canonical.unit.test_shadow_model_time_research import _sample
    assert evaluation.execution_time.available is False
    assert evaluation.decision.kind == "OPEN_NOW"
    now = evaluation.market.evaluated_ts + 1
    for stamp in (now, now + 2, now + 30):
        module.observe(evaluation, params, now_ts=stamp, provider="FINNHUB", buffer_mode="SMALL")
    report = module.summary(now_ts=now + 31)
    permissive = report["levels"][0]
    assert permissive["accepted_unique_stages"] == {"PRE": 1, "CONFIRM": 1, "OPEN_NOW": 1}
    assert permissive["paper_trades"]["registered"] == 1
    horizon = evaluation.time.context.model_expiry * 60
    assert permissive["paper_trades"]["horizon_seconds_counts"] == {str(horizon): 1}
    calls = []
    def price_loader(symbol):
        calls.append(symbol)
        return _sample(now + 31)
    module.advance_paper_trades(now_ts=now + 31, active_provider="FINNHUB", price_loader=price_loader)
    assert calls == ["EUR/USD"]  # One shared cached sample across all 21 levels.
    endpoint = now + 31 + horizon
    module.advance_paper_trades(now_ts=endpoint, active_provider="FINNHUB", price_loader=lambda _: _sample(endpoint, 1.2))
    final = module.summary(now_ts=endpoint + 1)
    assert final["levels"][0]["paper_trades"]["outcomes"]["WIN"] == 1
    assert final["levels"][20]["paper_trades"]["registered"] == 0


def test_continuous_observation_survives_days_and_cannot_recount_same_observation(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    module = importlib.reload(module)
    for stamp in (1000, 999, 1001, 8200, 9000, 100000, 200000):
        module.observe(evaluation, params, now_ts=stamp, provider="FINNHUB", buffer_mode="SMALL")
    report = module.summary(now_ts=200001)
    assert report["status"] == "OBSERVING" and report["operating_mode"] == "CONTINUOUS"
    assert report["started_ts"] == 1000 and report["deadline_ts"] is None
    assert report["automatic_stop_at"] is None
    assert all(row["evaluations"] == 6 for row in report["levels"])
    path = module._path()
    monkeypatch.delenv("OWNER_TIMING_SESSION_ID")
    module = importlib.reload(module)
    assert module._path() == path
    module.observe(evaluation, params, now_ts=200002, provider="FINNHUB", buffer_mode="SMALL")
    assert all(row["evaluations"] == 7 for row in module.summary(now_ts=200003)["levels"])


@pytest.mark.parametrize("drift", ["params", "buffer"])
def test_baseline_change_pauses_every_level_without_new_window(canonical_runtime_root, monkeypatch, drift):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    if drift == "params":
        params["score_thresholds"]["PRE"] = 69
    module.observe(evaluation, params, now_ts=1001, provider="FINNHUB", buffer_mode="MEDIUM" if drift == "buffer" else "SMALL")
    report = module.summary(now_ts=1002)
    assert report["status"] == "PAUSED_BASELINE_CHANGED" and report["deadline_ts"] is None
    assert all(row["evaluations"] == 1 for row in report["levels"])


def test_research_opt_ins_and_source_scope_are_required(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    module.observe(evaluation, params, now_ts=1000, provider="TWELVE_DATA", buffer_mode="SMALL")
    assert module.summary(now_ts=1001) is None
    monkeypatch.setenv("ENABLE_BROKER_EXECUTION", "true")
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    assert module.summary(now_ts=1001) is None


@pytest.mark.parametrize("corruption", ["protocol", "levels"])
def test_corrupt_research_is_not_reset_and_failure_cannot_escape_engine_hook(canonical_runtime_root, monkeypatch, capsys, corruption):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    path = module._path()
    path.parent.mkdir(parents=True)
    value = module._new(params, evaluation, 1000, "SMALL")
    value[corruption] = "corrupt" if corruption == "protocol" else ["corrupt"]
    path.write_text(json.dumps(value))
    before = path.read_bytes()
    from core import signal_engine
    signal_engine._observe_score_severity(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    assert path.read_bytes() == before
    assert "TSP_LIVE_SCORE_SEVERITY_UNAVAILABLE" in capsys.readouterr().out


def test_inconsistent_counters_are_unavailable_instead_of_false_observations(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    path = module._path()
    value = json.loads(path.read_text())
    value["levels"][0]["decision_kinds"] = {"PRE": 999}
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        module.summary(now_ts=1001)


def test_all_gates_still_reject_invalid_structure_at_permissive_level(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    from dataclasses import replace
    # Keep a real canonical evaluation but invalidate its upstream structure;
    # every score is recalculated by the real scoring/assembly/FSM pipeline.
    corridor = replace(evaluation.corridor, structure=replace(evaluation.corridor.structure, feasibility_state="UNAVAILABLE"))
    invalid = replace(evaluation, corridor=corridor)
    module.observe(invalid, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    report = module.summary(now_ts=1001)
    assert all(row["decision_kinds"] == {"REJECT": 1} for row in report["levels"])
    assert all(row["blockers"]["STRUCTURE_NOT_VALID"] == 1 for row in report["levels"])
    assert all(not row["accepted_unique_stages"] for row in report["levels"])


def test_real_fsm_chain_times_are_unique_and_separate_from_publication(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    from tests.canonical.unit.test_v2_fsm_orchestrator import _decision
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state
    row = module._new(params, evaluation, 1000, "SMALL")["levels"][14]
    state = default_fsm_state()
    for stage, stamp in (("PRE", 1001), ("CONFIRM", 1005), ("OPEN_NOW", 1040)):
        decision = _decision(stage, "private-research-only", 1000)
        handoff = advance_persistent_fsm(state, decision, now_ts=stamp)
        state = handoff.next_state
        assert handoff.stage_handoff_ready and handoff.accepted_stage == stage
        module._observe_accepted_stage(row, decision, handoff, stamp)
        module._observe_accepted_stage(row, decision, handoff, stamp + .1)
        if stage == "CONFIRM":
            assert row["complete_ordered_chains"] == 0
            assert row["stage_pair_gap_samples"]["pre_to_confirm_seconds"] == [4]
    assert row["accepted_unique_stages"] == {"PRE": 1, "CONFIRM": 1, "OPEN_NOW": 1}
    assert row["complete_ordered_chains"] == 1
    assert row["stage_pair_gap_samples"] == {"pre_to_confirm_seconds": [4],
                                             "confirm_to_open_seconds": [35],
                                             "pre_to_open_seconds": [39]}
    assert row["stage_gap_samples"] == [{"pre_to_confirm_seconds": 4,
                                         "confirm_to_open_seconds": 35,
                                         "pre_to_open_seconds": 39}]
