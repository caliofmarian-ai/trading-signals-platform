from __future__ import annotations

import copy

from intelligence import adaptive_params
from intelligence import evidence_contract
from intelligence import research_engine
from intelligence import risk_monitor
from intelligence import strategy_optimizer


def _market(*, wins=3, losses=2, draws=0, no_data=False, insufficient=False, rate=60.0):
    return {
        "truth_domain": "MARKET_TRUTH",
        "authoritative_for_strategy_performance": True,
        "no_data": no_data,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "total": wins + losses + draws,
        "decisive_sample": wins + losses,
        "market_win_rate_percent": None if no_data or insufficient else rate,
        "insufficient_sample": insufficient or no_data,
        "invalid_count": 0,
        "excluded_incomplete": 0,
    }


def _community(*, wins=5, loses=0, missed=0, no_data=False):
    return {
        "truth_domain": "COMMUNITY_TRUTH",
        "truth_source": "COMMUNITY_SELF_REPORT",
        "authoritative_for_strategy_performance": False,
        "no_data": no_data,
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "total": wins + loses + missed,
        "community_win_rate_percent": 100.0 if wins and not loses else None,
    }


def _operational(*, no_data=True):
    return {
        "truth_domain": "OPERATIONAL_TRUTH",
        "authoritative_for_strategy_performance": False,
        "no_data": no_data,
        "wins": 0,
        "loses": 0,
        "missed": 0,
    }


def _snapshot(market=None, community=None, operational=None):
    return {
        "schema_version": "1.0.0",
        "truth_separation_enforced": True,
        "strategy_performance_truth_domain": "MARKET_TRUTH",
        "market_truth": market or _market(),
        "community_truth": community or _community(no_data=True, wins=0),
        "operational_truth": operational or _operational(),
        "distribution": {"no_data": True, "FAILED": 0},
    }


def _research_report(market):
    snap = _snapshot(market=market)
    readiness = evidence_contract.assess_readiness(snap)
    return {
        "strategy_performance": market,
        "signal_funnel": {"no_data": False, "PRE": 10, "CONFIRM": 6, "OPEN_NOW": 3},
        "research": {
            "readiness": readiness,
            "advisory_only": True,
            "auto_apply": False,
            "production_mutation_authorized": False,
        },
    }


def test_evidence_contract_rejects_community_as_strategy_performance(monkeypatch):
    monkeypatch.setattr(
        evidence_contract.analytics_engine,
        "_load_market_truth",
        lambda path: {
            "truth_domain": "COMMUNITY_TRUTH",
            "authoritative_for_strategy_performance": False,
            "no_data": False,
            "wins": 99,
            "market_win_rate_percent": 99.0,
        },
    )
    monkeypatch.setattr(evidence_contract.analytics_engine, "_load_operational_truth", lambda path: _operational())
    monkeypatch.setattr(evidence_contract.analytics_engine, "_load_community_truth", lambda path: _community())
    monkeypatch.setattr(evidence_contract.analytics_engine, "_load_distribution_metrics", lambda path: {"no_data": True})

    snapshot = evidence_contract.build_truth_snapshot()
    market = snapshot["market_truth"]
    readiness = evidence_contract.assess_readiness(snapshot)

    assert market["truth_domain"] == "MARKET_TRUTH"
    assert market["invalid_evidence"] is True
    assert market["market_win_rate_percent"] is None
    assert readiness["descriptive_research_ready"] is False
    assert readiness["production_mutation_authorized"] is False


def test_community_only_data_cannot_become_strategy_performance(monkeypatch):
    snap = _snapshot(
        market=_market(wins=0, losses=0, no_data=True, insufficient=True, rate=0.0),
        community=_community(wins=20, loses=0, missed=0),
    )
    monkeypatch.setattr(research_engine.evidence_contract, "build_truth_snapshot", lambda: copy.deepcopy(snap))
    monkeypatch.setattr(research_engine, "compute_signal_funnel", lambda: {"no_data": True, "PRE": 0, "CONFIRM": 0, "OPEN_NOW": 0})

    report = research_engine.build_research_report()

    assert report["strategy_performance_truth_domain"] == "MARKET_TRUTH"
    assert report["strategy_performance"]["no_data"] is True
    assert report["community_truth"]["wins"] == 20
    assert report["community_truth"]["authoritative_for_strategy_performance"] is False
    assert report["outcomes"]["win_rate_truth_domain"] == "MARKET_TRUTH"
    assert report["outcomes"]["win_rate"] is None
    assert report["research"]["production_mutation_authorized"] is False
    assert any("Do not propose strategy-parameter changes" in item for item in report["research"]["recommendations"])


def test_valid_market_sample_is_descriptive_not_mutation_authority(monkeypatch):
    snap = _snapshot(market=_market(wins=4, losses=1, rate=80.0))
    monkeypatch.setattr(research_engine.evidence_contract, "build_truth_snapshot", lambda: copy.deepcopy(snap))
    monkeypatch.setattr(research_engine, "compute_signal_funnel", lambda: {"no_data": False, "PRE": 20, "CONFIRM": 10, "OPEN_NOW": 5, "unsupported_stages": {}})

    report = research_engine.build_research_report()
    readiness = report["research"]["readiness"]

    assert report["strategy_performance"]["market_win_rate_percent"] == 80.0
    assert readiness["descriptive_research_ready"] is True
    assert readiness["evolution_readiness"] == "NOT_READY"
    assert readiness["production_mutation_authorized"] is False
    assert not any("above 55" in item or "below 55" in item for item in report["research"]["hypotheses"])


def test_adaptive_params_never_mutates_or_proposes_heuristic_thresholds(monkeypatch):
    params = {
        "algo_version": "3.0.0",
        "score_thresholds": {"PRE": 70, "CONFIRM": 75, "OPEN": 80},
        "expiry_limits_minutes": {"min": 1, "max": 10},
        "buffer_multipliers": {"SMALL": 0.5, "MEDIUM": 1.0, "LARGE": 1.5},
    }
    before = copy.deepcopy(params)
    market = _market(wins=1, losses=9, rate=10.0)

    monkeypatch.setattr(adaptive_params.params_loader, "load_algo_params", lambda: params)
    monkeypatch.setattr(adaptive_params.research_engine, "build_research_report", lambda: _research_report(market))

    result = adaptive_params.adjust_parameters()

    assert params == before
    assert result["action"] == "NO_AUTOMATIC_PARAMETER_CHANGE"
    assert result["proposed_changes"] == []
    assert result["auto_apply"] is False
    assert result["production_mutation_authorized"] is False
    assert "thresholds" not in result
    assert "score_thresholds" not in result


def test_strategy_optimizer_returns_no_new_params_and_no_legacy_rate_heuristics(monkeypatch):
    market = _market(wins=1, losses=9, rate=10.0)
    report = _research_report(market)
    monkeypatch.setattr(strategy_optimizer.research_engine, "build_research_report", lambda: copy.deepcopy(report))
    monkeypatch.setattr(
        strategy_optimizer.adaptive_params,
        "adjust_parameters",
        lambda: {
            "action": "NO_AUTOMATIC_PARAMETER_CHANGE",
            "auto_apply": False,
            "production_mutation_authorized": False,
            "proposed_changes": [],
        },
    )
    monkeypatch.setattr(strategy_optimizer.observability_logger, "log_event", lambda event: None)

    result = strategy_optimizer.optimize_strategy()

    assert result["new_params"] is None
    assert result["new_params_status"] == "DISABLED_NO_GOVERNED_MUTATION"
    assert result["production_mutation_authorized"] is False
    assert not any("underperforming" in item.lower() for item in result["suggestions"])
    assert not any("threshold may be too strict" in item.lower() for item in result["suggestions"])


def test_risk_monitor_does_not_classify_low_market_wr_as_high_without_canon_threshold(monkeypatch):
    market = _market(wins=1, losses=9, rate=10.0)
    monkeypatch.setattr(risk_monitor.research_engine, "build_research_report", lambda: _research_report(market))

    result = risk_monitor.evaluate_risk()

    assert result["truth_domain"] == "MARKET_TRUTH"
    assert result["market_win_rate_percent"] == 10.0
    assert result["risk_level"] == "UNCLASSIFIED"
    assert result["assessment_status"] == "NO_GOVERNED_PERFORMANCE_RISK_THRESHOLD"
    assert result["production_action_authorized"] is False


def test_insufficient_market_sample_fails_closed_across_intelligence(monkeypatch):
    market = _market(wins=1, losses=1, insufficient=True, rate=50.0)
    monkeypatch.setattr(risk_monitor.research_engine, "build_research_report", lambda: _research_report(market))

    result = risk_monitor.evaluate_risk()

    assert result["risk_level"] == "UNKNOWN"
    assert result["assessment_status"] == "INSUFFICIENT_MARKET_TRUTH"
    assert result["production_action_authorized"] is False
