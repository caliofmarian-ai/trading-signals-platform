import base64

import pytest

from scripts import app_source_bridge
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


def test_private_study_publisher_reuses_existing_authenticated_app_route(monkeypatch):
    monkeypatch.setenv("APP_SOURCE_BRIDGE_ENABLED", "1")
    monkeypatch.setenv("APP_SOURCE_BRIDGE_ORIGIN", "https://signals-app.example")
    monkeypatch.setenv("APP_SOURCE_BRIDGE_TOKEN", "existing-ingest-secret-" + "x"*40)
    calls = []

    class Response:
        status_code = 200
        def json(self):
            return {"status": "API_ACCEPTED", "receipt_id": "app-study-123456789012345678901234",
                    "phone_receipt_proven": False}

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(app_source_bridge.requests, "post", post)
    payload = {"protocol": "PRIVATE_V3_STUDY_RECEIPT_V1", "phase": "entry",
               "study_id": "a"*64, "created_ts": 1800000000,
               "signal_label": "19.11.2026 · 20:00 · nr. 0",
               "text": "OPEN_NOW · STUDIU V3", "provider": "FINNHUB",
               "symbol": "EUR/USD", "strategy_version": "3.0.0",
               "decision_policy": "PHYSICAL_ONLY_V3", "format": "PHOTO"}
    png = b"\\x89PNG\\r\\n\\x1a\\nfixture"
    assert app_source_bridge.private_study_publisher_ready()
    result = app_source_bridge.publish_private_study(payload, image_bytes=png)
    assert result["status"] == "API_ACCEPTED" and result["phone_receipt_proven"] is False
    url, kwargs = calls[0]
    assert url == "https://signals-app.example/api/internal/signals"
    assert kwargs["headers"]["Authorization"].startswith("Bearer existing-ingest-secret-")
    assert kwargs["allow_redirects"] is False and kwargs["timeout"] == 3
    posted = kwargs["json"]["private_study"]
    assert base64.b64decode(posted["image_base64"]) == png
    assert posted["study_id"] == "a"*64 and posted["phase"] == "entry"


def test_private_study_transport_distinguishes_rejection_from_ambiguity(monkeypatch):
    monkeypatch.setenv("APP_SOURCE_BRIDGE_ENABLED", "1")
    monkeypatch.setenv("APP_SOURCE_BRIDGE_ORIGIN", "https://signals-app.example")
    monkeypatch.setenv("APP_SOURCE_BRIDGE_TOKEN", "x"*48)

    class Response:
        def __init__(self, status): self.status_code = status
        def json(self): return {"detail": "not exposed"}

    payload = {"protocol": "PRIVATE_V3_STUDY_RECEIPT_V1", "phase": "entry",
               "study_id": "b"*64, "created_ts": 1800000000,
               "signal_label": "label", "text": "study", "provider": "FINNHUB",
               "symbol": "EUR/USD", "strategy_version": "3.0.0",
               "decision_policy": "PHYSICAL_ONLY_V3", "format": "TEXT"}
    monkeypatch.setattr(app_source_bridge.requests, "post", lambda *a, **k: Response(409))
    with pytest.raises(app_source_bridge.AppStudyRejected):
        app_source_bridge.publish_private_study(payload)
    monkeypatch.setattr(app_source_bridge.requests, "post", lambda *a, **k: Response(503))
    with pytest.raises(app_source_bridge.AppStudyTransportError):
        app_source_bridge.publish_private_study(payload)
    monkeypatch.setattr(app_source_bridge.requests, "post",
                        lambda *a, **k: (_ for _ in ()).throw(app_source_bridge.requests.Timeout()))
    with pytest.raises(app_source_bridge.AppStudyTransportError):
        app_source_bridge.publish_private_study(payload)


def test_private_study_publisher_refuses_redirects_and_oversized_images(monkeypatch):
    monkeypatch.setenv("APP_SOURCE_BRIDGE_ENABLED", "1")
    monkeypatch.setenv("APP_SOURCE_BRIDGE_ORIGIN", "https://signals-app.example")
    monkeypatch.setenv("APP_SOURCE_BRIDGE_TOKEN", "x"*48)
    payload = {"protocol": "PRIVATE_V3_STUDY_RECEIPT_V1"}
    with pytest.raises(app_source_bridge.AppStudyRejected):
        app_source_bridge.publish_private_study(payload, image_bytes=b"\x89PNG\r\n\x1a\n" + b"x"*(384*1024))
    class Response:
        status_code = 302
    monkeypatch.setattr(app_source_bridge.requests, "post", lambda *a, **k: Response())
    with pytest.raises(app_source_bridge.AppStudyTransportError):
        app_source_bridge.publish_private_study(payload)
