"""Regression coverage for operational JSONL write amplification.

These tests protect log-volume reduction without changing market-data
selection, market-data blocking, strategy calculations, or Telegram RBAC.
"""

from __future__ import annotations

import pytest


def test_successful_ui_navigation_does_not_emit_error_sink_warning(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = fresh_imports("core.bot_service")
    warnings: list[dict] = []
    monkeypatch.setattr(
        bot.observability_logger, "log_warning", lambda **kw: warnings.append(kw)
    )

    payload = {
        "correlation_id": "trace-safe-1",
        "update_id": 123,
        "command_family": "ADMIN_NAV",
        "selected_operation": "edit_preferred",
        "edit_result_category": "edited",
        "chat_id": 987,
        "user_id": 654,
        "resolved_state_file_path": "/data/state/private.json",
    }
    bot._emit_interactive_trace(payload, critical=False)

    assert warnings == []


def test_navigation_anomaly_remains_logged_without_private_identity(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = fresh_imports("core.bot_service")
    warnings: list[dict] = []
    monkeypatch.setattr(
        bot.observability_logger, "log_warning", lambda **kw: warnings.append(kw)
    )

    bot._emit_interactive_trace(
        {
            "correlation_id": "trace-safe-2",
            "update_id": 124,
            "command_family": "ADMIN_NAV",
            "selected_operation": "send_replacement",
            "edit_result_category": "send_failed",
            "chat_id": 987,
            "user_id": 654,
            "resolved_state_file_path": "/data/state/private.json",
            "send_error": "synthetic",
        },
        critical=True,
    )

    assert len(warnings) == 1
    assert warnings[0]["warn_type"] == "telegram_ui_navigation_trace"
    context = warnings[0]["context"]
    assert context["correlation_id"] == "trace-safe-2"
    assert context["error_present"] is True
    assert "chat_id" not in context
    assert "user_id" not in context
    assert "resolved_state_file_path" not in context


def test_market_data_rate_limit_warning_is_bounded_and_aggregated(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = fresh_imports("core.signal_engine")
    warnings: list[dict] = []
    monkeypatch.setattr(
        engine.observability_logger, "log_warning", lambda **kw: warnings.append(kw)
    )
    monkeypatch.setattr(engine, "_MARKET_DATA_LIMITED_LAST_LOG_TS", None)
    monkeypatch.setattr(engine, "_MARKET_DATA_LIMITED_SUPPRESSED_COUNT", 0)

    engine._log_market_data_limited_warning("EURUSD", 1000)
    engine._log_market_data_limited_warning("EURUSD", 1002)
    engine._log_market_data_limited_warning("EURUSD", 1150)
    engine._log_market_data_limited_warning("EURUSD", 1299)
    assert len(warnings) == 1

    engine._log_market_data_limited_warning("EURUSD", 1300)
    assert len(warnings) == 2
    assert all(x["warn_type"] == "MARKET_DATA_LIMITED" for x in warnings)
    assert warnings[0]["context"] == {"symbol": "EURUSD"}
    assert warnings[1]["context"] == {
        "symbol": "EURUSD",
        "suppressed_repeated_warnings": 3,
    }
    assert engine._MARKET_DATA_LIMITED_SUPPRESSED_COUNT == 0


def test_market_data_warning_clock_rollback_emits_new_warning(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = fresh_imports("core.signal_engine")
    warnings: list[dict] = []
    monkeypatch.setattr(
        engine.observability_logger, "log_warning", lambda **kw: warnings.append(kw)
    )
    monkeypatch.setattr(engine, "_MARKET_DATA_LIMITED_LAST_LOG_TS", None)
    monkeypatch.setattr(engine, "_MARKET_DATA_LIMITED_SUPPRESSED_COUNT", 0)

    engine._log_market_data_limited_warning("EURUSD", 1000)
    engine._log_market_data_limited_warning("EURUSD", 900)

    assert len(warnings) == 2
    assert warnings[1]["context"] == {"symbol": "EURUSD"}
