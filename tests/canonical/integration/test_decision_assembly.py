from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.decision_assembly import DecisionAssemblyUnavailable, assemble_decision
from core.market_model import evaluate_market
from core.scoring_model import evaluate_score
from core.sr_corridor_engine import evaluate_corridor
from core.time_model import evaluate_time


def _params(runtime_root: Path) -> dict:
    return json.loads((runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))


def _candles(count: int, *, timeframe: str, step: int) -> list[dict]:
    candles = []
    for index in range(count):
        wave = 0.0 if index == count - 1 else ((index % 20) - 10) * 0.00008
        base = 1.1000 + wave
        candles.append({
            "symbol": "EUR/USD", "timeframe": timeframe, "ts": 1_720_000_000 + index * step,
            "open": base, "high": base + 0.00035, "low": base - 0.00035,
            "close": base + 0.00002, "volume": 100 + index,
        })
    return list(reversed(candles))


def _stack(runtime_root: Path):
    params = _params(runtime_root)
    m1 = _candles(220, timeframe="M1", step=60)
    m1[0]["close"] = m1[0]["open"] + 0.00015
    m5 = _candles(220, timeframe="M5", step=300)
    for candle in m5:
        candle["high"], candle["low"] = 1.1015, 1.0985
    market = evaluate_market(m1, m5, params, buffer_mode="SMALL")
    corridor = evaluate_corridor(m5, market, params)
    time = evaluate_time(market, corridor, params)
    scoring = evaluate_score(market, corridor, time, params)
    return market, corridor, time, scoring


def test_complete_stack_builds_one_pre_fsm_decision(canonical_runtime_root: Path) -> None:
    market, corridor, time, scoring = _stack(canonical_runtime_root)
    decision = assemble_decision(market, corridor, time, scoring, timeframe="M1", cycle_id="cycle-001")

    assert decision.setup.symbol == "EUR/USD"
    assert decision.setup.direction == market.direction_bias
    assert decision.market_context.target_distance == corridor.structure.available_distance
    assert decision.structure == corridor.structure
    assert decision.time == time.context
    assert decision.score == scoring.context
    assert decision.fsm_inputs["strategy_eligible"] is True
    assert decision.kind in {"PRE", "CONFIRM", "OPEN_NOW"}
    assert decision.signal_id.startswith("sig-v2-")
    assert not hasattr(decision, "fsm_state")
    assert not hasattr(decision, "signal")


def test_blockers_are_materialized_as_reject_semantics(canonical_runtime_root: Path) -> None:
    market, corridor, time, _ = _stack(canonical_runtime_root)
    unstable = replace(market, context=replace(market.context, noise_context="UNSTABLE"))
    from core.scoring_model import evaluate_score
    params = _params(canonical_runtime_root)
    scoring = evaluate_score(unstable, corridor, time, params)
    decision = assemble_decision(unstable, corridor, time, scoring, timeframe="M1", cycle_id="cycle-blocked")

    assert decision.strategic_flags.rejectable is True
    assert decision.strategic_flags.unstable_market is True
    assert "MARKET_NOISE_UNSTABLE" in decision.reject.hard_blockers
    assert decision.reject.stage == "PRE_FSM"
    assert decision.fsm_inputs["strategy_eligible"] is False
    assert decision.kind == "REJECT"
    assert decision.signal_id is None


def test_decision_serializes_to_plain_json_ready_evidence(canonical_runtime_root: Path) -> None:
    decision = assemble_decision(*_stack(canonical_runtime_root), timeframe="M1", cycle_id="cycle-json")
    payload = decision.to_dict()

    encoded = json.dumps(payload, sort_keys=True)
    assert '"producer": "binary_strategy_v2_decision_assembly"' in encoded
    assert payload["compatibility_mode"] is False
    assert payload["kind"] in {"PRE", "CONFIRM", "OPEN_NOW"}
    assert payload["signal_id"].startswith("sig-v2-")
    assert isinstance(payload["score"]["components"], dict)
    assert isinstance(payload["fsm_inputs"], dict)
    assert isinstance(payload["reject"]["hard_blockers"], list)


def test_mixed_cycles_and_directions_are_rejected(canonical_runtime_root: Path) -> None:
    market, corridor, time, scoring = _stack(canonical_runtime_root)
    with pytest.raises(DecisionAssemblyUnavailable, match="same evaluation"):
        assemble_decision(market, corridor, replace(time, evaluated_ts=time.evaluated_ts + 1), scoring, timeframe="M1", cycle_id="bad")
    with pytest.raises(DecisionAssemblyUnavailable, match="direction disagree"):
        assemble_decision(market, replace(corridor, direction="SELL"), time, scoring, timeframe="M1", cycle_id="bad")


def test_decision_and_fsm_inputs_are_immutable(canonical_runtime_root: Path) -> None:
    decision = assemble_decision(*_stack(canonical_runtime_root), timeframe="M1", cycle_id="cycle-frozen")
    with pytest.raises(FrozenInstanceError):
        decision.compatibility_mode = False  # type: ignore[misc]
    with pytest.raises(TypeError):
        decision.fsm_inputs["strategy_eligible"] = False  # type: ignore[index]


def test_assembly_is_deterministic_and_does_not_mutate_layers(canonical_runtime_root: Path) -> None:
    stack = _stack(canonical_runtime_root)
    first = assemble_decision(*stack, timeframe="M1", cycle_id="cycle-repeat")
    second = assemble_decision(*stack, timeframe="M1", cycle_id="cycle-repeat")
    assert first == second
    assert first.signal_id == second.signal_id
    assert stack[0].context.target_distance is None


def test_signal_identity_follows_real_opportunity_not_runtime_cycle_id(
    canonical_runtime_root: Path,
) -> None:
    stack = _stack(canonical_runtime_root)
    first = assemble_decision(*stack, timeframe="M1", cycle_id="runtime-cycle-a")
    second = assemble_decision(*stack, timeframe="M1", cycle_id="runtime-cycle-b")
    assert first.signal_id == second.signal_id

    later_market = replace(stack[0], evaluated_ts=stack[0].evaluated_ts + 60)
    later_corridor = replace(stack[1], evaluated_ts=stack[1].evaluated_ts + 60)
    later_time = replace(stack[2], evaluated_ts=stack[2].evaluated_ts + 60)
    later_scoring = replace(stack[3], evaluated_ts=stack[3].evaluated_ts + 60)
    later = assemble_decision(
        later_market,
        later_corridor,
        later_time,
        later_scoring,
        timeframe="M1",
        cycle_id="runtime-cycle-c",
    )
    assert later.signal_id != first.signal_id


def test_existing_fsm_opportunity_identity_survives_later_candles(
    canonical_runtime_root: Path,
) -> None:
    stack = _stack(canonical_runtime_root)
    decision = assemble_decision(
        *stack,
        timeframe="M1",
        cycle_id="later-cycle",
        opportunity_signal_id="sig-v2-existing-opportunity",
    )
    assert decision.signal_id == "sig-v2-existing-opportunity"


@pytest.mark.parametrize(
    ("tier", "expected"),
    [
        ("BELOW_PRE", "WAIT"),
        ("SCORE_PRE_BAND", "PREPARE"),
        ("SCORE_CONFIRM_BAND", "CONFIRM"),
    ],
)
def test_normal_maturity_bands_are_not_mislabeled_as_degraded(
    canonical_runtime_root: Path, tier: str, expected: str
) -> None:
    from core.fsm_decision_adapter import interpret_decision

    market, corridor, time, scoring = _stack(canonical_runtime_root)
    scoring = replace(scoring, context=replace(scoring.context, tier=tier), eligible=True, hard_blockers=())
    decision = assemble_decision(
        market, corridor, time, scoring, timeframe="M1", cycle_id=f"cycle-{tier.lower()}"
    )

    assert decision.strategic_flags.degraded_setup is False
    assert interpret_decision(decision).outcome == expected
