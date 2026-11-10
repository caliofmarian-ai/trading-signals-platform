"""Synthetic plan/format invariants, not live calibration evidence."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from core import confirmed_study_duration as plans
from core.signal_card import _duration, build_card_fields


def decision(stage, *, adjusted=8.6, signal_id="sig-v3-seconds", source="a" * 64):
    candidate = plans.prepare_candidate(adjusted, minimum_minutes=1, maximum_minutes=15)
    return SimpleNamespace(kind=stage, signal_id=signal_id,
        setup=SimpleNamespace(symbol="EUR/USD", direction="BUY"),
        time=SimpleNamespace(time_state="READY"), decision_id="dec-confirm", decision_audit_id="audit-confirm",
        fsm_inputs={"study_duration_policy": plans.POLICY, "study_duration_candidate": {
            "policy": plans.POLICY, "adjusted_minutes": adjusted, "minimum_minutes": 1,
            "maximum_minutes": 15, "parameter_sha256": source,
            "duration_seconds": candidate.duration_seconds}})


def prepared():
    row = {"physical_signal_id": "sig-v3-seconds", "physical_direction": "BUY", "physical_pre_ts": 1000}
    plans.record_stage(row, {}, decision("PRE"), now_ts=1000)
    row["physical_confirm_ts"] = 1003
    plans.record_stage(row, {}, decision("CONFIRM"), now_ts=1003)
    return row


def test_second_plan_is_frozen_at_confirm_and_survives_restart():
    row = prepared()
    plan = row[plans.PLAN_FIELD]
    assert plan["duration_seconds"] == 516
    assert plan["confirmed_ts"] == 1003
    restored = json.loads(json.dumps(row))
    plans.validate_plan(restored[plans.PLAN_FIELD], row=restored)
    plans.record_stage(restored, deepcopy(row), decision("CONFIRM", adjusted=9.5), now_ts=1005)
    assert restored[plans.PLAN_FIELD] == plan
    fields = plans.event_fields(plan)
    assert fields["study_duration_seconds"] == 516 and fields["study_duration_minutes"] == 8.6
    assert fields["study_plan_id"] == plan["plan_id"]


def test_old_pre_retry_and_old_confirm_do_not_acquire_new_policy():
    old = {"physical_signal_id": "sig-v3-seconds", "physical_direction": "BUY", "physical_pre_ts": 990}
    row = {**old, "physical_pre_ts": 1000}
    plans.record_stage(row, old, decision("PRE"), now_ts=1000)
    row["physical_confirm_ts"] = 1003
    plans.record_stage(row, old, decision("CONFIRM"), now_ts=1003)
    assert plans.PLAN_FIELD not in row and plans.POLICY_FIELD not in row


def test_new_pre_cannot_inherit_previous_opportunity_plan():
    old = prepared()
    row = {**old, "physical_signal_id": "sig-v3-new", "physical_pre_ts": 2000,
           "physical_confirm_ts": None}
    plans.record_stage(row, old, decision("PRE", signal_id="sig-v3-new"), now_ts=2000)
    assert row[plans.PLAN_FIELD] is None
    assert row[plans.POLICY_FIELD] == plans.POLICY


def test_missing_plan_cannot_be_backfilled_at_later_confirm_or_open():
    row = prepared()
    row[plans.PLAN_FIELD] = None
    for stage in ("CONFIRM", "OPEN_NOW"):
        plans.record_stage(row, {}, decision(stage), now_ts=1005)
        assert row[plans.PLAN_FIELD] is None


@pytest.mark.parametrize("field,value", [("duration_seconds", 517), ("duration_seconds", True),
    ("duration_seconds", 516.0), ("adjusted_minutes", 8), ("signal_id", "different"),
    ("parameter_sha256", "b" * 64), ("confirmed_ts", 1004), ("plan_id", "b" * 64),
    ("minimum_minutes", float("nan")), ("direction", "SELL")])
def test_corrupt_plan_is_rejected(field, value):
    row = prepared()
    row[plans.PLAN_FIELD][field] = value
    with pytest.raises(ValueError):
        plans.validate_plan(row[plans.PLAN_FIELD], row=row)


@pytest.mark.parametrize("field,value", [("physical_signal_id", "other"),
    ("physical_direction", "SELL"), ("physical_pre_ts", 999), ("physical_confirm_ts", 1004),
    (plans.POLICY_FIELD, "unknown")])
def test_plan_is_bound_to_the_opportunity(field, value):
    row = prepared()
    row[field] = value
    with pytest.raises(ValueError):
        plans.validate_plan(row[plans.PLAN_FIELD], row=row)


@pytest.mark.parametrize("field,value", [("study_duration_seconds", 517), ("study_duration_seconds", 516.0),
    ("study_duration_seconds", True), ("study_duration_minutes", 8.61),
    ("study_confirmed_ts", 1004), ("study_plan_id", "b" * 64),
    ("study_duration_policy", "old"), ("execution_time_available", True)])
def test_primary_seconds_and_policy_cannot_change_after_delivered_confirm(field, value):
    expected = plans.event_fields(prepared()[plans.PLAN_FIELD])
    event = {**expected, field: value}
    assert plans.matching_receipt(expected, expected)
    assert not plans.matching_receipt(event, expected)
    assert not plans.matching_receipt(expected, event)


def test_legacy_receipt_cannot_authorize_new_seconds_plan():
    new = plans.event_fields(prepared()[plans.PLAN_FIELD])
    legacy = {k: v for k, v in new.items() if k not in
              {"study_plan_id", "study_duration_seconds", "study_duration_policy"}}
    assert not plans.matching_receipt(new, legacy)
    assert not plans.matching_receipt(legacy, new)


def test_plan_bound_observation_keeps_research_model_distinct():
    plan = prepared()[plans.PLAN_FIELD]
    row = {"direction": "BUY", "model_seconds": 540,
           "policies": {"PHYSICAL_ONLY_V3": {"pre_ts": 1000, "confirm_ts": 1003,
                          "confirm_model_seconds": 540, "opportunity_signal_id": "sig-v3-seconds"}},
           "study_observation": {"duration_source": plans.SOURCE, "duration_policy": plans.POLICY,
                "duration_seconds": 516, "horizon_seconds": 516, "duration_plan": plan, "confirmed_ts": 1003}}
    scope = {"symbol": "EUR/USD", "parameter_sha256": "a" * 64, "model_limits_minutes": {"min": 1, "max": 15}}
    plans.validate_observation(row, scope)
    assert row["model_seconds"] == 540
    assert plans.observation_policy(row) == plans.POLICY
    with pytest.raises(ValueError):
        plans.validate_observation(row, {**scope, "parameter_sha256": "b" * 64})
    changed = deepcopy(row)
    changed["study_observation"]["duration_seconds"] = 517
    with pytest.raises(ValueError):
        plans.validate_observation(changed, scope)
    assert plans.observation_policy({"study_observation": {}}) == plans.LEGACY_POLICY
    assert plans.observation_policy({}) == plans.LEGACY_OPEN_POLICY


@pytest.mark.parametrize("seconds, expected", [(207, "3 MIN 27 S"), (287, "4 MIN 47 S"),
    (516, "8 MIN 36 S"), (60, "1 MIN 00 S"), (1, "0 MIN 01 S"), (86400, "1440 MIN 00 S")])
def test_integer_seconds_render_without_float_tails(seconds, expected):
    assert _duration(seconds / 60, seconds=seconds) == expected
    assert _duration(seconds / 60) == expected


def test_all_whole_seconds_render_exactly_and_real_fractions_are_not_destroyed():
    for seconds in range(1, 3601):
        m, s = divmod(seconds, 60)
        assert _duration(seconds / 60) == f"{m} MIN {s:02d} S"
    assert _duration(4.77) == "4 MIN 46.2 S"
    assert _duration(2.375) == "2 MIN 22.5 S"
    assert _duration(287.000001 / 60) != "4 MIN 47 S"


@pytest.mark.parametrize("seconds", [True, False, 0, -1, 287.0, "287", float("nan")])
def test_primary_seconds_must_be_positive_integers(seconds):
    with pytest.raises(ValueError):
        _duration(287 / 60, seconds=seconds)


def test_study_card_uses_primary_seconds_and_retains_simulation_label():
    fields = plans.event_fields(prepared()[plans.PLAN_FIELD])
    event = {**fields, "stage": "CONFIRM", "symbol": "EUR/USD", "direction": "BUY",
             "entry_price": 1.1, "created_ts": 1794264003}
    label = "09.11.2026 · 22:40:00 · nr. 0"
    confirm = build_card_fields(event, label, study=True)
    opened = build_card_fields({**event, "stage": "OPEN_NOW", "entry_ts": 1794264037,
                               "expiry_ts": 1794264037 + 516}, label, study=True)
    assert confirm["duration"] == opened["duration"] == "8 MIN 36 S"
    assert confirm["mode"] == opened["mode"] == "STUDIU · SIMULARE"
    assert confirm["expiry_time"] == "LA OPEN NOW"
    assert opened["entry_label"] == "MOMENT DESCHIDERE"
