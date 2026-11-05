from scripts.app_source_bridge import start_bridge, status_payload


def test_status_export_uses_current_process_and_allowlisted_evidence():
    raw = dict(pid=123, phase="RUNNING", updated_ts=1000, market_data_provider="FINNHUB",
               market_data_state="READY", last_market_data_success_ts=999,
               last_strategy_evaluation_ts=998, strategy_evaluation_count=3,
               last_strategy_decision_kind="REJECT", api_key="private-test-fixture")
    data = status_payload(raw, now=1000, pid=123, execution_available=True)
    assert data["runtime_current"] and data["evaluations"] == 3
    assert data["last_evaluation_at"] == 998 and data["execution_timing_available"]
    assert "private-test-fixture" not in str(data)
    for updates in ({"pid":122}, {"phase":"STOPPED"}, {"updated_ts":960},
                    {"market_data_provider":"TWELVE_DATA"}):
        wrong = status_payload(raw | updates, now=1000, pid=123, execution_available=True)
        assert not wrong["runtime_current"] and wrong["last_market_data_at"] is None
        assert not wrong["execution_timing_available"]


def test_disabled_bridge_never_creates_transport(monkeypatch):
    monkeypatch.delenv("APP_SOURCE_BRIDGE_ENABLED", raising=False)
    assert start_bridge() is None


def test_bad_destination_or_missing_credential_does_not_start_thread(monkeypatch):
    monkeypatch.setenv("APP_SOURCE_BRIDGE_ENABLED", "1")
    monkeypatch.setenv("APP_SOURCE_BRIDGE_TOKEN", "x"*40)
    for origin in ("http://app.invalid", "https://app.invalid/path", "https://user:pass@app.invalid",
                   "https://app.invalid?key=private-test", "https://app.invalid/#fragment"):
        monkeypatch.setenv("APP_SOURCE_BRIDGE_ORIGIN", origin)
        assert start_bridge() is None
