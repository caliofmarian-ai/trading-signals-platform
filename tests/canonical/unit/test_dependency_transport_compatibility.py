from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import requests
import websocket


EXPECTED_REQUESTS = "2.34.2"
EXPECTED_WEBSOCKET_CLIENT = "1.9.2"
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_direct_dependency_pins_match_reviewed_targets():
    pins = {}
    for raw_line in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        pins[name] = version

    assert pins == {
        "requests": EXPECTED_REQUESTS,
        "websocket-client": EXPECTED_WEBSOCKET_CLIENT,
    }


def test_requests_runtime_version_and_tls_verification_default():
    assert requests.__version__ == EXPECTED_REQUESTS

    session = requests.Session()
    try:
        assert session.verify is True
    finally:
        session.close()


def test_telegram_post_contract_survives_requests_upgrade(monkeypatch):
    publisher = importlib.import_module("core.telegram_publisher")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:compatibility-test-token")
    calls = []

    class _Response:
        status_code = 200

        @staticmethod
        def json():
            return {"ok": True, "result": {"message_id": 42}}

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return _Response()

    monkeypatch.setattr(publisher.requests, "post", fake_post)

    result = publisher.send_message(chat_id=77, text="compatibility")

    assert result["ok"] is True
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://api.telegram.org/bot123456:compatibility-test-token/sendMessage"
    assert kwargs["timeout"] == 10
    assert kwargs["json"] == {"chat_id": 77, "text": "compatibility"}
    assert "verify" not in kwargs


def test_telegram_request_exception_remains_fail_closed(monkeypatch):
    publisher = importlib.import_module("core.telegram_publisher")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:compatibility-test-token")

    def fail_post(*args, **kwargs):
        raise requests.exceptions.Timeout("simulated timeout")

    monkeypatch.setattr(publisher.requests, "post", fail_post)

    result = publisher.delete_message(chat_id=77, message_id=42)

    assert result["outcome"] == publisher.DELETE_OUTCOME_TRANSPORT
    assert result["description"] == "simulated timeout"


def test_finnhub_low_level_websocket_contract_survives_upgrade(monkeypatch, tmp_path):
    assert websocket.__version__ == EXPECTED_WEBSOCKET_CLIENT
    module = importlib.import_module("runtime.finnhub_market_data")
    calls = []
    marker = object()

    def fake_create_connection(url, timeout=None, **kwargs):
        calls.append((url, timeout, kwargs))
        return marker

    monkeypatch.setattr(websocket, "create_connection", fake_create_connection)
    feed = module.FinnhubForexFeed(
        token="compatibility-test-token",
        store_path=tmp_path / "finnhub.json",
        minimum_candles=2,
    )

    assert feed._connect() is marker
    assert calls == [
        ("wss://ws.finnhub.io?token=compatibility-test-token", 30, {})
    ]


def test_twelvedata_low_level_websocket_contract_survives_upgrade(monkeypatch, tmp_path):
    module = importlib.import_module("runtime.twelvedata_market_data")
    calls = []
    marker = object()

    def fake_create_connection(url, timeout=None, **kwargs):
        calls.append((url, timeout, kwargs))
        return marker

    monkeypatch.setattr(websocket, "create_connection", fake_create_connection)
    feed = module.TwelveDataRealtimeFeed(
        symbol="EUR/USD",
        token="compatibility-test-token",
        store_path=tmp_path / "twelvedata.json",
        minimum_candles=2,
    )

    assert feed._connect() is marker
    assert calls == [
        (
            "wss://ws.twelvedata.com/v1/quotes/price?apikey=compatibility-test-token",
            30,
            {},
        )
    ]
