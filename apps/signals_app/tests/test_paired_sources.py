from concurrent.futures import ThreadPoolExecutor
import json
import time

from fastapi.testclient import TestClient
import pytest

from apps.signals_app.api import create_app
from apps.signals_app.paired_sources import receive_finnhub_status, sources
from apps.signals_app.provider_budget import FreeTierBudgetExceeded, TwelveDataBudget
from apps.signals_app.source import SourceMonitor
from apps.signals_app.store import Store
from apps.signals_app.worker import UtcMarketHttp
from apps.signals_app.tests.test_app import KEY, SETUP


def evidence(now=1000, **changes):
    return dict(provider="FINNHUB", source_id="calibration-runtime", symbols=["EUR/USD"],
                observed_at=now, runtime_current=True, market_data_state="READY", evaluations=3,
                last_market_data_at=now, last_evaluation_at=now, last_decision="REJECT",
                execution_timing_available=False) | changes


def test_provider_health_is_independent_and_bridge_cannot_publish(tmp_path):
    store = Store(tmp_path)
    SourceMonitor(store, ["EUR/USD"]).cycle({}, now=1000)
    receive_finnhub_status(store, evidence(api_key="discard-private-fixture"), now=1000)
    first, second = sources(store, now=1000)
    assert first["provider"] == "FINNHUB" and first["state"] == "OBSERVING"
    assert second["provider"] == "TWELVE_DATA" and second["state"] == "SOURCE_UNAVAILABLE"
    assert first["scope"] == "OWNER_CALIBRATION_STATUS_ONLY"
    assert not first["execution_timing_available"]
    assert "discard-private-fixture" not in json.dumps(store.meta("source_status_finnhub"))
    with store.db() as db:
        assert db.execute("SELECT COUNT(*) FROM signals").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM pushes").fetchone()[0] == 0
    assert sources(store, now=1011)[0]["state"] == "SOURCE_UNAVAILABLE"
    assert sources(store, now=1031)[0]["reason"] == "WORKER_NOT_RESPONDING"


@pytest.mark.parametrize("changes", [{"observed_at": 969}, {"observed_at": 1001},
    {"last_market_data_at": 1006}, {"provider": "TWELVE_DATA"}, {"evaluations": True},
    {"symbols": ["BTC/USD"]}, {"source_id": "other-source"}])
def test_bridge_rejects_stale_future_and_wrong_source_evidence(tmp_path, changes):
    with pytest.raises(ValueError):
        receive_finnhub_status(Store(tmp_path), evidence(**changes), now=1000)


def test_stopped_or_data_only_source_is_not_healthy(tmp_path):
    store = Store(tmp_path)
    for fields in ({"runtime_current": False}, {"evaluations": 0}, {"last_evaluation_at": 800},
                   {"last_market_data_at": None}, {"market_data_state": "MARKET_DATA_UNAVAILABLE"}):
        receive_finnhub_status(store, evidence(**fields), now=1000)
        assert sources(store, now=1000)[0]["state"] != "OBSERVING"


def test_source_endpoint_requires_machine_auth_and_owner_read_access(tmp_path):
    app = create_app(tmp_path, public_url="http://testserver", ingest_token=KEY, setup_token=SETUP)
    with TestClient(app) as client:
        data = evidence(int(time.time()))
        assert client.post("/api/internal/source-status", json=data).status_code == 401
        assert client.post("/api/internal/source-status", json=data,
            headers={"Authorization": "Bearer "+KEY}).json()["state"] == "OBSERVING"
        client.post("/api/register", json={"email":"member@example.com", "password":"member-test-password"})
        assert client.get("/api/admin").status_code == 403
        assert "FINNHUB" not in json.dumps(client.get("/api/session").json())
        client.cookies.clear()
        client.post("/api/setup", json={"email":"owner@example.com", "password":"owner-test-password", "token":SETUP})
        result = client.get("/api/admin").json()
        assert [row["provider"] for row in result["sources"]] == ["FINNHUB", "TWELVE_DATA"]
        assert result["source"]["state"] == "NOT_CONNECTED"


def test_daily_budget_survives_restart_and_resets_at_utc_midnight(tmp_path):
    store = Store(tmp_path)
    current = [86400+100]
    budget = TwelveDataBudget(store, daily_limit=2, clock=lambda: current[0])
    budget.reserve()
    restarted = TwelveDataBudget(Store(tmp_path), daily_limit=2, clock=lambda: current[0])
    restarted.reserve()
    with pytest.raises(FreeTierBudgetExceeded, match="DAILY"):
        restarted.reserve()
    assert restarted.summary()["remaining_today"] == 0
    current[0] = 2*86400
    restarted.reserve()
    assert restarted.summary()["reserved_today"] == 1
    assert restarted.summary()["account_plan"] == "NOT_VERIFIED"


def test_concurrent_history_requests_share_the_same_durable_limit(tmp_path):
    store = Store(tmp_path)
    budget = TwelveDataBudget(store, daily_limit=3, minute_limit=8, clock=lambda: 1000)
    def attempt(_):
        try:
            budget.reserve()
            return True
        except FreeTierBudgetExceeded:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(12))) == 3
    assert budget.summary()["reserved_today"] == 3


def test_minute_cap_never_exceeds_free_tier_and_ages_out(tmp_path):
    current = [1000]
    budget = TwelveDataBudget(Store(tmp_path), daily_limit=9999, minute_limit=9999, clock=lambda:current[0])
    for _ in range(8):
        budget.reserve()
    with pytest.raises(FreeTierBudgetExceeded, match="MINUTE"):
        budget.reserve()
    current[0] += 60
    budget.reserve()
    assert budget.summary()["daily_limit"] == 800
    assert budget.summary()["minute_limit"] == 8


def test_budget_stops_network_io_before_request_and_preserves_utc(tmp_path):
    from types import SimpleNamespace
    from runtime import market_client
    calls = []
    delegate = SimpleNamespace(get=lambda url, **kwargs:calls.append(kwargs))
    budget = TwelveDataBudget(Store(tmp_path), daily_limit=1, clock=lambda:1000)
    adapter = UtcMarketHttp(delegate, "https://provider.invalid/time_series", budget)
    adapter.get("https://provider.invalid/time_series", params={"symbol":"EUR/USD"})
    with pytest.raises(market_client.MarketDataRateLimitError):
        adapter.get("https://provider.invalid/time_series", params={"symbol":"EUR/USD"})
    assert len(calls) == 1 and calls[0]["params"]["timezone"] == "UTC"
