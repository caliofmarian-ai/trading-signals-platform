from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.canonical.helpers.builders import make_signal_event


def _evidence(suffix: str = "1", route: str = "ELITE") -> dict[str, object]:
    return {
        "route_result_event_id": f"route-{suffix}",
        "visibility_event_id": f"visible-{suffix}",
        "route": route,
        "destination_id": 1004 if route == "ELITE" else 2001,
        "message_id": 800 + int(suffix),
    }


def _register(telemetry, event=None, *, provider="TWELVE_DATA", evidence=None):
    event = event or make_signal_event("sig-objective")
    return telemetry.register_open_now_trade(
        event,
        market_provider=provider,
        publication_evidence=evidence or _evidence(),
        now_ts=event["created_ts"],
    )


def _sample(provider: str, symbol: str, price: float, ts: float) -> dict[str, object]:
    return {
        "provider": provider,
        "symbol": symbol,
        "price": price,
        "observed_ts": ts,
    }


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_registration_requires_effective_open_now_visibility_and_governed_execution_time(
    canonical_runtime_root: Path,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")

    pre = make_signal_event("sig-pre", stage="PRE")
    with pytest.raises(ValueError, match="stage must be OPEN_NOW"):
        _register(telemetry, pre)

    missing_execution = make_signal_event("sig-no-exec")
    missing_execution["execution_time_available"] = False
    with pytest.raises(ValueError, match="governed Execution Time"):
        _register(telemetry, missing_execution)

    event = make_signal_event("sig-no-proof")
    with pytest.raises(ValueError, match="route_result_event_id"):
        telemetry.register_open_now_trade(
            event,
            market_provider="TWELVE_DATA",
            publication_evidence={},
            now_ts=event["created_ts"],
        )


def test_registration_is_one_trade_chain_with_multiple_publication_evidence(
    canonical_runtime_root: Path,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    event = make_signal_event("sig-multi-route")

    first = _register(telemetry, event, evidence=_evidence("1", "ELITE"))
    second = _register(telemetry, event, evidence=_evidence("2", "ADMIN_SIGNALS_LIVE"))
    replay = _register(telemetry, event, evidence=_evidence("2", "ADMIN_SIGNALS_LIVE"))

    assert first["status"] == "registered"
    assert second["status"] == "updated_publication_evidence"
    assert replay["status"] == "already_registered"
    record = telemetry.get_open_trade("sig-multi-route")
    assert record is not None
    assert len(record["publication_evidence"]) == 2
    assert record["truth_domain"] == "MARKET_TRUTH"
    assert record["checkpoint_selection_policy"] == "FIRST_REAL_OBSERVATION_AT_OR_AFTER_TARGET"
    assert record["linkage_state"] == "DEGRADED"
    assert "decision_audit_id" in record["missing_linkage_fields"]


def test_buy_trade_records_all_real_checkpoints_and_finalizes_once(
    canonical_runtime_root: Path,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    event = make_signal_event("sig-buy", entry_price=1.1000)
    record = _register(telemetry, event)["record"]
    targets = {key: value["target_ts"] for key, value in record["checkpoints"].items()}

    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.1005, targets["mid_expiry"] + 0.25))
    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.1007, targets["expiry"] + 0.5))
    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.1008, targets["post_1m"] + 0.1))
    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.1009, targets["post_3m"] + 0.2))
    final_result = telemetry.observe_market_sample(
        _sample("TWELVE_DATA", "EURUSD", 1.1010, targets["post_5m"] + 0.3)
    )

    assert final_result["finalized_trade_count"] == 1
    finalized = telemetry.get_open_trade("sig-buy")
    assert finalized is not None
    assert finalized["telemetry_status"] == "FINALIZED"
    assert finalized["result_at_expiry"] == "WIN"
    assert finalized["mid_direction_correct"] is True
    assert finalized["would_win_at_plus_1m"] is True
    assert finalized["checkpoints"]["expiry"]["observed_ts"] == pytest.approx(targets["expiry"] + 0.5)
    assert finalized["checkpoints"]["expiry"]["observation_lag_seconds"] == pytest.approx(0.5)
    assert finalized["checkpoints"]["expiry"]["provider"] == "TWELVE_DATA"

    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.2, targets["post_5m"] + 10))
    rows = _rows(canonical_runtime_root / "observability" / "trade_temporal_telemetry.jsonl")
    assert len(rows) == 1
    assert rows[0]["trade_id"] == "sig-buy"
    assert rows[0]["result_at_expiry"] == "WIN"


def test_sell_and_draw_expiry_classification_is_directionally_correct(
    canonical_runtime_root: Path,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")

    sell = make_signal_event("sig-sell", direction="SELL", entry_price=1.2000)
    sell_record = _register(telemetry, sell)["record"]
    telemetry.observe_market_sample(
        _sample("TWELVE_DATA", "EURUSD", 1.1990, sell_record["expiry_ts"])
    )
    assert telemetry.get_open_trade("sig-sell")["result_at_expiry"] == "WIN"

    draw = make_signal_event("sig-draw", entry_price=1.3000)
    draw_record = _register(telemetry, draw, evidence=_evidence("2"))["record"]
    telemetry.observe_market_sample(
        _sample("TWELVE_DATA", "EURUSD", 1.3000, draw_record["expiry_ts"])
    )
    assert telemetry.get_open_trade("sig-draw")["result_at_expiry"] == "DRAW"


def test_expiry_loss_can_recover_at_plus_three_without_overwriting_market_result(
    canonical_runtime_root: Path,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    event = make_signal_event("sig-recovery", entry_price=1.1000)
    record = _register(telemetry, event)["record"]
    targets = {key: value["target_ts"] for key, value in record["checkpoints"].items()}

    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.0998, targets["expiry"]))
    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.0999, targets["post_1m"]))
    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.1002, targets["post_3m"]))

    updated = telemetry.get_open_trade("sig-recovery")
    assert updated["result_at_expiry"] == "LOSS"
    assert updated["would_win_at_plus_1m"] is False
    assert updated["would_win_at_plus_3m"] is True
    assert updated["post_expiry_recovery"] == "RECOVERED_AT_3M"


def test_sample_before_target_is_not_used_and_first_later_observation_preserves_lag(
    canonical_runtime_root: Path,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    record = _register(telemetry, make_signal_event("sig-lag"))["record"]
    target = record["checkpoints"]["mid_expiry"]["target_ts"]

    before = telemetry.observe_market_sample(
        _sample("TWELVE_DATA", "EURUSD", 1.2, target - 0.01)
    )
    assert before["updated_trade_count"] == 0
    assert telemetry.get_open_trade("sig-lag")["mid_expiry_price"] is None

    telemetry.observe_market_sample(_sample("TWELVE_DATA", "EURUSD", 1.2, target + 0.75))
    checkpoint = telemetry.get_open_trade("sig-lag")["checkpoints"]["mid_expiry"]
    assert checkpoint["price"] == pytest.approx(1.2)
    assert checkpoint["observation_lag_seconds"] == pytest.approx(0.75)


def test_restart_marks_missed_checkpoint_as_gap_instead_of_backfilling(
    canonical_runtime_root: Path,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    record = _register(telemetry, make_signal_event("sig-restart-gap"))["record"]
    expiry = int(record["expiry_ts"])

    recovery = telemetry.recover_after_restart(expiry + 1)
    assert recovery["evidence_gap_count"] >= 2
    recovered = telemetry.get_open_trade("sig-restart-gap")
    assert recovered["checkpoints"]["mid_expiry"]["state"] == "EVIDENCE_GAP"
    assert recovered["checkpoints"]["expiry"]["state"] == "EVIDENCE_GAP"
    assert recovered["checkpoints"]["expiry"]["price"] is None
    assert recovered["result_at_expiry"] is None

    telemetry.recover_after_restart(int(record["post_5m_ts"]) + 1)
    final = telemetry.get_open_trade("sig-restart-gap")
    assert final["telemetry_status"] == "INCOMPLETE_MARKET_EVIDENCE"
    assert final["result_at_expiry"] is None
    rows = _rows(canonical_runtime_root / "observability" / "trade_temporal_telemetry.jsonl")
    assert len(rows) == 1


def test_provider_switch_at_due_checkpoint_creates_gap_and_worker_never_mixes(
    canonical_runtime_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    telemetry = importlib.import_module("core.trade_temporal_telemetry")
    worker = importlib.import_module("runtime.telemetry_market_worker")
    record = _register(
        telemetry,
        make_signal_event("sig-provider-switch"),
        provider="TWELVE_DATA",
    )["record"]
    called: list[str] = []

    monkeypatch.setattr(worker.market_client, "configured_provider", lambda: "FINNHUB")
    result = worker.run_telemetry_cycle(
        now_ts=record["expiry_ts"],
        price_loader=lambda symbol: called.append(symbol) or {},
    )

    assert called == []
    assert result["provider_evidence_gap_count"] >= 2
    after = telemetry.get_open_trade("sig-provider-switch")
    assert after["checkpoints"]["expiry"]["state"] == "EVIDENCE_GAP"
    assert after["checkpoints"]["expiry"]["gap_reason"] == "ACTIVE_PROVIDER_CHANGED_BEFORE_CHECKPOINT"
    assert after["expiry_price"] is None


def test_market_client_live_sample_uses_real_feed_timestamp_and_rejects_mismatch(
    canonical_runtime_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_client = importlib.import_module("runtime.market_client")

    class Feed:
        def __init__(self, observed_ts: float):
            self.observed_ts = observed_ts

        def health(self):
            return {"last_price_ts": self.observed_ts}

    candles = [{"ts": 1000, "close": 1.2345}]
    sample = market_client._latest_sample_from_feed(
        "FINNHUB", "EUR/USD", Feed(1030), candles
    )
    assert sample == {
        "provider": "FINNHUB",
        "symbol": "EUR/USD",
        "price": 1.2345,
        "observed_ts": 1030.0,
        "source": "LIVE_STREAM_CURRENT_M1_CLOSE",
    }

    with pytest.raises(market_client.MarketDataUnavailableError, match="does not match"):
        market_client._latest_sample_from_feed(
            "FINNHUB", "EUR/USD", Feed(1061), candles
        )
