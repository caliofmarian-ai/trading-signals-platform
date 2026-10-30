"""Bounded repeated-market-unavailable warning evidence, no strategy changes."""

from __future__ import annotations

import pytest


def _unavailable(code: str, text: str = "SENSITIVE-API-PARAMETER") -> RuntimeError:
    outer = RuntimeError(text)
    cause = type(code, (RuntimeError,), {})(text)
    outer.__cause__ = cause
    return outer


def test_identical_finnhub_history_gap_logs_first_and_five_minute_summary(
    canonical_runtime_root, fresh_imports, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = fresh_imports("core.signal_engine")
    events: list[dict] = []
    monkeypatch.setattr(engine.observability_logger, "log_warning", lambda **kwargs: events.append(kwargs))
    engine._mark_market_data_unavailable_recovered()

    err = _unavailable("FinnhubInsufficientHistory", "SENSITIVE-API-PARAMETER 3/201")
    engine._log_market_data_unavailable_warning("EURUSD", err, 1000)
    engine._log_market_data_unavailable_warning("EURUSD", _unavailable("FinnhubInsufficientHistory", "SENSITIVE-API-PARAMETER 4/201"), 1002)
    engine._log_market_data_unavailable_warning("EURUSD", err, 1299)
    assert len(events) == 1

    engine._log_market_data_unavailable_warning("EURUSD", err, 1300)
    assert len(events) == 2
    assert events[0]["warn_type"] == "MARKET_DATA_UNAVAILABLE"
    assert events[0]["context"] == {
        "symbol": "EURUSD", "reason_code": "FinnhubInsufficientHistory"
    }
    assert events[1]["context"]["suppressed_repeated_warnings"] == 2
    assert "SENSITIVE-API-PARAMETER" not in str(events)


def test_changed_failure_reason_is_reported_immediately(
    canonical_runtime_root, fresh_imports, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = fresh_imports("core.signal_engine")
    events: list[dict] = []
    monkeypatch.setattr(engine.observability_logger, "log_warning", lambda **kwargs: events.append(kwargs))
    engine._mark_market_data_unavailable_recovered()

    engine._log_market_data_unavailable_warning("EURUSD", _unavailable("FinnhubInsufficientHistory"), 1000)
    engine._log_market_data_unavailable_warning("EURUSD", _unavailable("FinnhubInsufficientHistory"), 1002)
    engine._log_market_data_unavailable_warning("EURUSD", _unavailable("FinnhubStaleMarketData"), 1004)

    assert len(events) == 2
    assert events[1]["context"]["reason_code"] == "FinnhubStaleMarketData"
    assert events[1]["context"]["previous_reason_suppressed_warnings"] == 1


def test_recovery_rearms_initial_warning_and_resets_counts(
    canonical_runtime_root, fresh_imports, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = fresh_imports("core.signal_engine")
    events: list[dict] = []
    monkeypatch.setattr(engine.observability_logger, "log_warning", lambda **kwargs: events.append(kwargs))
    engine._mark_market_data_unavailable_recovered()
    err = _unavailable("FinnhubStaleMarketData")

    engine._log_market_data_unavailable_warning("EURUSD", err, 1000)
    engine._log_market_data_unavailable_warning("EURUSD", err, 1002)
    engine._mark_market_data_unavailable_recovered()
    engine._log_market_data_unavailable_warning("EURUSD", err, 1004)

    assert len(events) == 2
    assert "suppressed_repeated_warnings" not in events[1]["context"]


def test_unknown_cause_and_clock_rollback_fail_safe(
    canonical_runtime_root, fresh_imports, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = fresh_imports("core.signal_engine")
    events: list[dict] = []
    monkeypatch.setattr(engine.observability_logger, "log_warning", lambda **kwargs: events.append(kwargs))
    engine._mark_market_data_unavailable_recovered()

    err = RuntimeError("SECRET-TOKEN-IN-PROVIDER-EXCEPTION")
    engine._log_market_data_unavailable_warning("EURUSD", err, 1000)
    engine._log_market_data_unavailable_warning("EURUSD", err, 900)

    assert len(events) == 2
    assert events[0]["context"]["reason_code"] == "OTHER_UNAVAILABLE"
    assert "SECRET-TOKEN" not in str(events)
