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


def _publication_evidence() -> dict[str, object]:
    return {
        "route_result_event_id": "evt-route-contract",
        "visibility_event_id": "evt-visible-contract",
        "route": "ELITE",
        "destination_id": 1004,
        "message_id": 808,
    }


def test_trade_temporal_telemetry_registration_is_idempotent_and_conflict_safe(canonical_runtime_root: Path):
    telemetry = importlib.import_module("core.trade_temporal_telemetry")

    event = make_signal_event("sig-telemetry")
    kwargs = {
        "market_provider": "TWELVE_DATA",
        "publication_evidence": _publication_evidence(),
        "now_ts": event["created_ts"],
    }
    first = telemetry.register_open_now_trade(event, **kwargs)
    second = telemetry.register_open_now_trade(event, **kwargs)

    assert first["status"] == "registered"
    assert second["status"] == "already_registered"
    assert first["record"]["truth_domain"] == "MARKET_TRUTH"
    assert first["record"]["entry_price_source"] == "signal_event.entry_price"

    conflict = dict(event)
    conflict["entry_price"] = event["entry_price"] + 0.01
    with pytest.raises(ValueError, match="conflicting OPEN_NOW registration"):
        telemetry.register_open_now_trade(conflict, **kwargs)
