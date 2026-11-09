"""Synthetic canonical OPEN_NOW data and mocked private Telegram transport."""

import pytest

from tests.canonical.helpers.builders import make_signal_event


OWNER = 123456789
NUMBER = "09.11.2026 · 18:35:12 · nr. 1"


@pytest.fixture
def reports(canonical_runtime_root, monkeypatch):
    from core import owner_signal_number, trade_temporal_telemetry as telemetry
    from intelligence import owner_open_now_result as delivery

    for key, value in {
        "OWNER_SIGNAL_DELIVERY_ENABLED": "true", "OWNER_TELEGRAM_ID": str(OWNER),
        "SHADOW_MODE": "true", "ENABLE_BROKER_EXECUTION": "false",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(owner_signal_number, "lookup", lambda _: NUMBER)
    chart_calls, photo_calls = [], []

    def render(**fields):
        chart_calls.append(fields)
        return b"chart"

    def send(**fields):
        photo_calls.append(fields)
        return {"ok": True, "result": {"message_id": 321}}

    monkeypatch.setattr(delivery.physical_study_chart, "render_market_chart", render)
    monkeypatch.setattr(delivery.telegram_publisher, "send_photo", send)
    monkeypatch.setattr(delivery.telegram_publisher, "send_message", lambda **_: pytest.fail("unexpected text send"))
    return telemetry, delivery, chart_calls, photo_calls


def _register(telemetry, signal_id="sig-v3-test", *, provider="FINNHUB", route="OWNER_PRIVATE",
              destination=OWNER, message_id=123, physical=True):
    event = make_signal_event(signal_id)
    if physical:
        event["payload"].update(decision_policy="PHYSICAL_ONLY_V3", strategy_version="3.0.0")
    return telemetry.register_open_now_trade(event, market_provider=provider, publication_evidence={
        "route_result_event_id": "route-proof", "visibility_event_id": "visible-proof",
        "route": route, "destination_id": destination, "message_id": message_id,
    })["record"]


def _observe_expiry(telemetry, record):
    return telemetry.observe_market_sample({"provider": record["market_provider"], "symbol": record["symbol"],
                                            "price": 1.1010, "observed_ts": record["expiry_ts"] + 0.25})


def test_private_canonical_result_sends_once_at_expiry_before_followups(reports):
    telemetry, delivery, chart_calls, photo_calls = reports
    record = _register(telemetry)
    assert delivery.dispatch_async() is None

    assert _observe_expiry(telemetry, record)["finalized_trade_count"] == 0
    thread = delivery.dispatch_async()
    assert thread is not None
    thread.join(timeout=3)
    assert not thread.is_alive()

    stored = telemetry.get_open_trade(record["trade_id"])
    assert stored["checkpoints"]["post_1m"]["state"] == "PENDING"
    assert stored["result_at_expiry"] == "WIN"
    assert len(photo_calls) == len(chart_calls) == 1
    assert photo_calls[0]["chat_id"] == OWNER
    assert photo_calls[0]["reply_to_message_id"] == 123
    assert NUMBER in photo_calls[0]["caption"] and record["trade_id"] not in photo_calls[0]["caption"]
    assert "Preț de referință" in photo_calls[0]["caption"] and "Buffer la cotația observată: ATINS" in photo_calls[0]["caption"]
    assert "+0.250 s" in photo_calls[0]["caption"]
    assert chart_calls[0]["outcome"] == "WIN"
    assert chart_calls[0]["signal_label"] == NUMBER
    assert chart_calls[0]["expiry_ts"] == record["expiry_ts"]
    assert chart_calls[0]["expiry_quote_ts"] == record["expiry_ts"] + 0.25
    assert telemetry._load_registry()["owner_expiry_reports"][record["trade_id"]]["status"] == "API_ACCEPTED"
    assert delivery.dispatch() is None


@pytest.mark.parametrize("details", [
    {"provider": "TWELVE_DATA"}, {"route": "ELITE"}, {"destination": OWNER + 1},
    {"message_id": None}, {"physical": False},
])
def test_market_evidence_without_current_private_v3_publication_cannot_send(reports, details):
    telemetry, delivery, _, photo_calls = reports
    _observe_expiry(telemetry, _register(telemetry, **details))
    assert delivery.dispatch() is None and not photo_calls


def test_existing_trade_is_not_retroactively_armed_by_registration_retry(reports):
    telemetry, delivery, _, photo_calls = reports
    record = _register(telemetry)
    legacy = telemetry._load_registry()
    legacy.pop("owner_expiry_reports")
    telemetry._save_registry(legacy)
    _register(telemetry)
    _observe_expiry(telemetry, record)
    assert delivery.dispatch() is None and not photo_calls


@pytest.mark.parametrize("after_expiry", [False, True])
def test_new_private_publication_is_armed_only_while_expiry_is_pending(reports, after_expiry):
    telemetry, delivery, _, photo_calls = reports
    record = _register(telemetry, route="ELITE", message_id=12)
    if after_expiry:
        _observe_expiry(telemetry, record)
    _register(telemetry, message_id=34)
    if not after_expiry:
        _observe_expiry(telemetry, record)
        assert delivery.dispatch() == "API_ACCEPTED"
        assert photo_calls[0]["reply_to_message_id"] == 34
    else:
        assert delivery.dispatch() is None and not photo_calls


def test_recorded_expiry_gap_sends_unknown_without_inventing_a_quote(reports):
    telemetry, delivery, chart_calls, photo_calls = reports
    record = _register(telemetry)
    telemetry.mark_due_provider_mismatch("TWELVE_DATA", now_ts=int(record["expiry_ts"]))
    assert delivery.dispatch() == "API_ACCEPTED"
    assert chart_calls[0]["outcome"] == "UNKNOWN"
    assert chart_calls[0]["expiry_price"] is None and chart_calls[0]["expiry_quote_ts"] is None
    assert "Prima cotație la sau după expirare: indisponibilă" in photo_calls[0]["caption"]
    assert telemetry.get_open_trade(record["trade_id"])["result_at_expiry"] is None


def test_ambiguous_transport_is_never_retried_or_followed_by_text(reports, monkeypatch):
    telemetry, delivery, chart_calls, _ = reports
    _observe_expiry(telemetry, _register(telemetry))

    def timeout(**_):
        raise TimeoutError("acceptance unknown")

    monkeypatch.setattr(delivery.telegram_publisher, "send_photo", timeout)
    assert delivery.dispatch() == "UNKNOWN"
    assert delivery.dispatch() is None and len(chart_calls) == 1
