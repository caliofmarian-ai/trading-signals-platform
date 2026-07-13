from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.canonical.helpers.builders import make_signal_event


def test_algo_params_validation_rejects_unknown_fields(canonical_runtime_root: Path):
    params_loader = importlib.import_module("core.params_loader")

    params = json.loads((canonical_runtime_root / "config" / "algo_params.json").read_text(encoding="utf-8"))
    params["unexpected"] = True

    with pytest.raises(params_loader.ParamsValidationError, match="unknown top-level parameter keys"):
        params_loader.validate_algo_params(params)


def test_trade_temporal_telemetry_registration_is_idempotent_and_conflict_safe(canonical_runtime_root: Path):
    telemetry = importlib.import_module("core.trade_temporal_telemetry")

    event = make_signal_event("sig-telemetry")
    first = telemetry.register_open_now_trade(event, now_ts=event["created_ts"])
    second = telemetry.register_open_now_trade(event, now_ts=event["created_ts"])

    assert first["status"] == "registered"
    assert second["status"] == "already_registered"

    conflict = dict(event)
    conflict["payload"] = {"price": event["payload"]["price"] + 0.01}
    with pytest.raises(ValueError, match="conflicting OPEN_NOW registration"):
        telemetry.register_open_now_trade(conflict, now_ts=event["created_ts"])
