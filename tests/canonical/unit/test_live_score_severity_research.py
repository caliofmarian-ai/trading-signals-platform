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
    assert report["levels"][14]["decision_kinds"] == {evaluation.decision.kind: 1}
    assert report["actual_telegram_publications"] == 0 and report["broker_executed"] is False
    assert report["automatic_selection_allowed"] is False
    assert evaluation.decision.to_dict() == original and params == parameters
    for path, raw in source_files.items():
        assert open(path, "rb").read() == raw
    new_files = [p for p in canonical_runtime_root.rglob("*") if p.is_file() and str(p) not in source_files]
    assert len(new_files) == 1 and "live_score_severity_research" in str(new_files[0])
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
        handoff = advance_persistent_fsm(default_fsm_state(), full.decision, now_ts=1000)
        assert row["decision_kinds"] == {full.decision.kind: 1}
        assert row["fsm_reason_families"] == {handoff.reason_family: 1}
        assert row["blockers"] == dict(Counter(full.decision.reject.hard_blockers))
        expected = {handoff.accepted_stage: 1} if handoff.stage_handoff_ready else {}
        assert row["accepted_unique_stages"] == expected


def test_research_window_survives_restart_and_cannot_recount_same_observation(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    module = importlib.reload(module)
    for stamp in (1000, 999, 1001, 8200, 9000):
        module.observe(evaluation, params, now_ts=stamp, provider="FINNHUB", buffer_mode="SMALL")
    report = module.summary(now_ts=9001)
    assert report["status"] == "COMPLETE"
    assert report["started_ts"] == 1000 and report["deadline_ts"] == 8200
    assert all(row["evaluations"] == 2 for row in report["levels"])
    frozen = module._path().read_bytes()
    params["score_thresholds"]["PRE"] = 69
    module.observe(evaluation, params, now_ts=10000, provider="FINNHUB", buffer_mode="MEDIUM")
    assert module._path().read_bytes() == frozen  # Later changes cannot poison a closed comparison.


@pytest.mark.parametrize("drift", ["params", "buffer"])
def test_baseline_change_pauses_every_level_without_new_window(canonical_runtime_root, monkeypatch, drift):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    module.observe(evaluation, params, now_ts=1000, provider="FINNHUB", buffer_mode="SMALL")
    if drift == "params":
        params["score_thresholds"]["PRE"] = 69
    module.observe(evaluation, params, now_ts=1001, provider="FINNHUB", buffer_mode="MEDIUM" if drift == "buffer" else "SMALL")
    report = module.summary(now_ts=1002)
    assert report["status"] == "PAUSED_BASELINE_CHANGED" and report["deadline_ts"] == 8200
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
