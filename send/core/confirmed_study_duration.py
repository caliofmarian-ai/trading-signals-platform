"""Versioned, prospective private-study duration plans frozen at CONFIRM.

This consumes the strategy's adjusted movement time; the internal Model Time
window and calibrated Execution Time are not replaced. Existing opportunities
without the policy marker retain their original minute-based study contract.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

from intelligence.second_precision_duration import POLICY, prepare_candidate

LEGACY_POLICY = "CONFIRM_INTEGER_MINUTE_V1"
LEGACY_OPEN_POLICY = "LEGACY_OPEN_MODEL_TIME"
SOURCE = "CONFIRM_MODEL_TIME"  # producer family; policy identifies its exact formula
POLICY_FIELD = "physical_study_duration_policy"
PLAN_FIELD = "physical_confirm_study_plan"
_CANDIDATE_KEYS = {"policy", "adjusted_minutes", "minimum_minutes", "maximum_minutes",
                   "duration_seconds", "parameter_sha256"}
_PLAN_KEYS = _CANDIDATE_KEYS | {"signal_id", "symbol", "direction", "pre_ts", "confirmed_ts",
                               "decision_id", "decision_audit_id", "plan_id"}


def _digest(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(dict(value), sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def _positive(value: Any) -> bool:
    return type(value) in (int, float) and isfinite(value) and value > 0


def _hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_candidate(candidate: Mapping[str, Any]) -> None:
    if (not isinstance(candidate, Mapping) or set(candidate) != _CANDIDATE_KEYS
            or candidate.get("policy") != POLICY or not _hash(candidate.get("parameter_sha256"))
            or type(candidate.get("duration_seconds")) is not int
            or not 0 < candidate["duration_seconds"] <= 86400):
        raise ValueError("INVALID_SECOND_DURATION_CANDIDATE")
    derived = prepare_candidate(candidate["adjusted_minutes"],
        minimum_minutes=candidate["minimum_minutes"], maximum_minutes=candidate["maximum_minutes"])
    if derived.duration_seconds != candidate["duration_seconds"]:
        raise ValueError("SECOND_DURATION_CANDIDATE_CHANGED")


def annotate_decision(decision: Any, params: Mapping[str, Any]) -> Any:
    """Add explicit candidate evidence without changing kind or physical gates."""
    if (decision.fsm_inputs.get("decision_policy") != "PHYSICAL_ONLY_V3"
            or decision.kind not in {"PRE", "CONFIRM", "OPEN_NOW"}):
        return decision
    from core.decision_assembly import FrozenInputs
    from core.runtime_execution_calibration import algo_params_sha256

    candidate = None
    try:
        bounds = params["expiry_limits_minutes"]
        prepared = prepare_candidate(decision.time.t_needed_adjusted,
            minimum_minutes=bounds["min"], maximum_minutes=bounds["max"])
        candidate = {"policy": POLICY, "adjusted_minutes": decision.time.t_needed_adjusted,
                     "minimum_minutes": bounds["min"], "maximum_minutes": bounds["max"],
                     "duration_seconds": prepared.duration_seconds,
                     "parameter_sha256": algo_params_sha256(params)}
        validate_candidate(candidate)
    except (KeyError, TypeError, ValueError, OverflowError):
        candidate = None  # never invent a substitute duration
    inputs = dict(decision.fsm_inputs)
    inputs.update(study_duration_policy=POLICY,
                  study_duration_candidate=FrozenInputs(candidate) if candidate is not None else None)
    return replace(decision, fsm_inputs=FrozenInputs(inputs))


def validate_plan(plan: Mapping[str, Any], *, row: Mapping[str, Any] | None = None) -> None:
    if not isinstance(plan, Mapping) or set(plan) != _PLAN_KEYS:
        raise ValueError("INVALID_CONFIRMED_SECONDS_PLAN")
    validate_candidate({key: plan[key] for key in _CANDIDATE_KEYS})
    for name in ("signal_id", "symbol", "decision_id", "decision_audit_id"):
        if not isinstance(plan[name], str) or not plan[name].strip():
            raise ValueError("INVALID_CONFIRMED_SECONDS_IDENTITY")
    if (plan["direction"] not in {"BUY", "SELL"} or not _positive(plan["pre_ts"])
            or not _positive(plan["confirmed_ts"]) or plan["confirmed_ts"] <= plan["pre_ts"]
            or plan["plan_id"] != _digest({k: v for k, v in plan.items() if k != "plan_id"})):
        raise ValueError("CONFIRMED_SECONDS_PLAN_CHANGED")
    if row is not None and (row.get(POLICY_FIELD) != POLICY
            or row.get("physical_signal_id") != plan["signal_id"]
            or row.get("physical_direction") != plan["direction"]
            or row.get("physical_pre_ts") != plan["pre_ts"]
            or row.get("physical_confirm_ts") != plan["confirmed_ts"]):
        raise ValueError("CONFIRMED_SECONDS_PLAN_IDENTITY_MISMATCH")


def record_stage(row: dict, previous_row: Mapping[str, Any], decision: Any, *, now_ts: float) -> None:
    """Called only after exact-stage FSM acceptance, before the state is saved."""
    if decision.kind == "PRE":
        if (previous_row.get("physical_signal_id") == decision.signal_id
                and previous_row.get("physical_pre_ts") is not None):
            # A retry cannot upgrade a chain that began before deployment.
            for key in (POLICY_FIELD, PLAN_FIELD):
                if key in previous_row:
                    row[key] = deepcopy(previous_row[key])
                else:
                    row.pop(key, None)
            return
        row.pop(PLAN_FIELD, None)
        row.pop(POLICY_FIELD, None)
        if decision.fsm_inputs.get("study_duration_policy") == POLICY:
            row[POLICY_FIELD], row[PLAN_FIELD] = POLICY, None
        return
    if decision.kind != "CONFIRM" or POLICY_FIELD not in row:
        return
    if row[POLICY_FIELD] != POLICY:
        raise ValueError("UNKNOWN_STUDY_DURATION_POLICY")
    if row.get(PLAN_FIELD) is not None:
        validate_plan(row[PLAN_FIELD], row=row)
        return
    if row.get("physical_confirm_ts") != now_ts:
        return  # no late backfill of a missing historical preparation
    candidate = decision.fsm_inputs.get("study_duration_candidate")
    if candidate is None or decision.time.time_state != "READY":
        return  # policy marker prevents fallback into the legacy model horizon
    validate_candidate(candidate)
    plan = dict(candidate)
    plan.update(signal_id=decision.signal_id, symbol=decision.setup.symbol,
                direction=decision.setup.direction, pre_ts=row["physical_pre_ts"],
                confirmed_ts=row["physical_confirm_ts"], decision_id=decision.decision_id,
                decision_audit_id=decision.decision_audit_id)
    plan["plan_id"] = _digest(plan)
    validate_plan(plan, row=row)
    row[PLAN_FIELD] = plan


def event_fields(plan: Mapping[str, Any]) -> dict:
    validate_plan(plan)
    return {"study_duration_minutes": plan["duration_seconds"] / 60,
            "study_duration_seconds": plan["duration_seconds"],
            "study_confirmed_ts": plan["confirmed_ts"], "study_duration_source": SOURCE,
            "study_duration_policy": POLICY, "study_plan_id": plan["plan_id"]}


def validate_event_fields(event: Mapping[str, Any]) -> None:
    seconds = event.get("study_duration_seconds")
    minutes = event.get("study_duration_minutes")
    if (event.get("study_duration_policy") != POLICY or event.get("study_duration_source") != SOURCE
            or type(seconds) is not int or not 0 < seconds <= 86400
            or not _positive(minutes) or minutes != seconds / 60
            or not _positive(event.get("study_confirmed_ts")) or not _hash(event.get("study_plan_id"))
            or event.get("execution_time_available") is True):
        raise ValueError("INVALID_CONFIRMED_SECONDS_EVENT")


def matching_receipt(event: Mapping[str, Any], receipt: Mapping[str, Any]) -> bool:
    try:
        validate_event_fields(event)
        validate_event_fields(receipt)
    except (ValueError, TypeError, OverflowError):
        return False
    return all(event.get(key) == receipt.get(key) for key in (
        "study_duration_policy", "study_duration_seconds", "study_plan_id", "study_confirmed_ts"))


def validate_observation(row: Mapping[str, Any], scope: Mapping[str, Any]) -> None:
    observation = row["study_observation"]
    plan = observation.get("duration_plan")
    validate_plan(plan)
    context = row["policies"]["PHYSICAL_ONLY_V3"]
    # The runtime accepts EURUSD while the quote-study scope stores EUR/USD.
    # Compare this explicit alias pair without rewriting the frozen plan/digest.
    symbol_matches = (plan["symbol"] == scope["symbol"] or
                      (plan["symbol"] in ("EURUSD", "EUR/USD")
                       and scope["symbol"] in ("EURUSD", "EUR/USD")))
    if (observation.get("duration_policy") != POLICY
            or type(observation.get("duration_seconds")) is not int
            or observation["duration_seconds"] != plan["duration_seconds"]
            or observation["horizon_seconds"] != plan["duration_seconds"]
            or observation.get("confirmed_ts") != plan["confirmed_ts"]
            or plan["confirmed_ts"] != context["confirm_ts"] or plan["pre_ts"] != context["pre_ts"]
            or plan["signal_id"] != context["opportunity_signal_id"]
            or plan["direction"] != row["direction"] or not symbol_matches
            or plan["parameter_sha256"] != scope["parameter_sha256"]
            or plan["minimum_minutes"] != scope["model_limits_minutes"]["min"]
            or plan["maximum_minutes"] != scope["model_limits_minutes"]["max"]):
        raise ValueError("CONFIRMED_SECONDS_OBSERVATION_CHANGED")


def observation_policy(row: Mapping[str, Any]) -> str:
    observation = row.get("study_observation")
    if observation is None:
        return LEGACY_OPEN_POLICY
    return observation.get("duration_policy", LEGACY_POLICY)
