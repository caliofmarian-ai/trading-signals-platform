from core.status_interpretation import human_status_summary


def test_ready_evidence_is_explained_without_promising_profit() -> None:
    lines = human_status_summary({
        "runtime_phase": "RUNNING",
        "market_data_state": "READY",
        "market_data_history_ready": True,
        "recovery_state": "READY",
        "shadow_mode": "ON",
        "broker_state": "DISABLED (configured)",
        "market_data_persistence_state": "ACTIVE",
        "market_data_integrity_state": "VALID",
    })
    text = "\n".join(lines)

    assert "enough recorded history" in text
    assert "Real trading: impossible" in text
    assert "Required action: none" in text
    assert "candle file was read or saved successfully" in text
    assert "timestamps and prices passed integrity checks" in text
    assert "profit" not in text.lower()
    assert "guarante" not in text.lower()


def test_unavailable_market_is_plainly_blocked() -> None:
    text = "\n".join(human_status_summary({
        "runtime_phase": "RUNNING",
        "market_data_state": "MARKET_DATA_UNAVAILABLE",
        "market_data_history_ready": False,
        "recovery_state": "DEGRADED_SAFE",
        "shadow_mode": "ON",
        "broker_state": "DISABLED",
    }))

    assert "unusable right now" in text
    assert "decisions are blocked" in text
    assert "protecting itself" in text


def test_persistence_error_overrides_no_action_message() -> None:
    text = "\n".join(human_status_summary({
        "runtime_phase": "RUNNING",
        "market_data_state": "MARKET_DATA_COLLECTING",
        "market_data_history_ready": False,
        "recovery_state": "DEGRADED_SAFE",
        "shadow_mode": "ON",
        "broker_state": "DISABLED",
        "market_data_persistence_state": "ERROR",
    }))

    assert "collected history may be lost" in text
    assert "Required action: inspect persistent storage" in text


def test_invalid_candles_require_attention() -> None:
    text = "\n".join(human_status_summary({
        "runtime_phase": "RUNNING",
        "market_data_state": "MARKET_DATA_UNAVAILABLE",
        "market_data_history_ready": True,
        "recovery_state": "DEGRADED_SAFE",
        "shadow_mode": "ON",
        "broker_state": "DISABLED",
        "market_data_persistence_state": "ACTIVE",
        "market_data_integrity_state": "INVALID",
    }))

    assert "invalid history was detected" in text
    assert "Required action: inspect invalid candle evidence" in text
