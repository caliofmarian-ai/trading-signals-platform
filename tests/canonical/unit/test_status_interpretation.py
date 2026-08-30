from core.status_interpretation import human_status_summary


def test_ready_evidence_is_explained_without_promising_profit() -> None:
    lines = human_status_summary({
        "runtime_phase": "RUNNING",
        "market_data_state": "READY",
        "market_data_history_ready": True,
        "recovery_state": "READY",
        "shadow_mode": "ON",
        "broker_state": "DISABLED (configured)",
    })
    text = "\n".join(lines)

    assert "enough recorded history" in text
    assert "Real trading: impossible" in text
    assert "Required action: none" in text
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
