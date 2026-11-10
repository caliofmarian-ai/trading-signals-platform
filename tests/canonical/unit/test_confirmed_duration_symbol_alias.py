"""Explicit symbol aliases preserve, rather than rewrite, frozen plan identity."""
from copy import deepcopy

import pytest

from core import confirmed_study_duration as plans


def observation(plan_symbol, scope_symbol):
    plan = {
        "policy": plans.POLICY, "adjusted_minutes": 8.6,
        "minimum_minutes": 1, "maximum_minutes": 15, "duration_seconds": 516,
        "parameter_sha256": "a" * 64, "signal_id": "sig-v3-seconds",
        "symbol": plan_symbol, "direction": "BUY", "pre_ts": 1000,
        "confirmed_ts": 1003, "decision_id": "decision-confirm",
        "decision_audit_id": "audit-confirm",
    }
    plan["plan_id"] = plans._digest(plan)
    row = {"direction": "BUY", "policies": {"PHYSICAL_ONLY_V3": {
        "pre_ts": 1000, "confirm_ts": 1003, "opportunity_signal_id": "sig-v3-seconds"}},
        "study_observation": {"duration_policy": plans.POLICY,
            "duration_seconds": 516, "horizon_seconds": 516,
            "confirmed_ts": 1003, "duration_plan": plan}}
    scope = {"symbol": scope_symbol, "parameter_sha256": "a" * 64,
             "model_limits_minutes": {"min": 1, "max": 15}}
    return row, scope


@pytest.mark.parametrize("plan_symbol,scope_symbol", [
    ("EUR/USD", "EUR/USD"), ("EURUSD", "EUR/USD"),
    ("EUR/USD", "EURUSD"), ("EURUSD", "EURUSD"),
])
def test_known_eurusd_aliases_preserve_digest_and_original_symbol(plan_symbol, scope_symbol):
    row, scope = observation(plan_symbol, scope_symbol)
    original = deepcopy(row)
    plans.validate_observation(row, scope)
    assert row == original
    assert row["study_observation"]["duration_plan"]["symbol"] == plan_symbol


@pytest.mark.parametrize("other", ["GBP/USD", "EUR//USD", "EUR_USD", "eurusd", "EURUSD "])
def test_other_or_malformed_symbols_cannot_reuse_eurusd_plan(other):
    for plan_symbol, scope_symbol in ((other, "EUR/USD"), ("EUR/USD", other)):
        row, scope = observation(plan_symbol, scope_symbol)
        with pytest.raises(ValueError, match="CONFIRMED_SECONDS_OBSERVATION_CHANGED"):
            plans.validate_observation(row, scope)
