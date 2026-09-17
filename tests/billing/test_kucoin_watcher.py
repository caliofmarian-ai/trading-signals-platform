from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import kucoin_watcher, payment_ledger

SUBSCRIBER = "kucoin-test-subscriber"
PRODUCT = "BINARY_TRADING"
PLAN = "BINARY_TRADING_BASIC"
CURRENCY = "BTC"
SCALE = 8
AMOUNT_MINOR = 123_456_789
AMOUNT_TEXT = "1.23456789"
BASE_MS = 1_700_000_000_000
API_KEY = "fake-kucoin-key"
API_SECRET = "fake-kucoin-secret"
API_PASSPHRASE = "fake-kucoin-passphrase"
API_VERSION = "3"


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    return {
        "adapter": tmp_path / "billing" / "kucoin_watcher_events.jsonl",
        "payment": tmp_path / "billing" / "payment_ledger.jsonl",
    }


def _intent(
    payment_path: Path,
    *,
    intent_id: str = "intent-kucoin-1",
    amount_minor: int = AMOUNT_MINOR,
    currency: str = CURRENCY,
) -> dict:
    return payment_ledger.create_payment_intent(
        subscriber_ref=f"{SUBSCRIBER}:{intent_id}",
        strategy_product_id=PRODUCT,
        plan_id=PLAN,
        amount_minor=amount_minor,
        currency=currency,
        payment_method="CRYPTO",
        provider=kucoin_watcher.PROVIDER,
        idempotency_key=f"create:{intent_id}",
        payment_intent_id=intent_id,
        audit_correlation_id=f"audit:{intent_id}",
        now_ts=BASE_MS / 1000,
        path=str(payment_path),
    )["record"]


def _deposit(
    *,
    deposit_id: str = "deposit-1",
    status: str = "SUCCESS",
    amount: str = AMOUNT_TEXT,
    currency: str = CURRENCY,
    updated_at: int = BASE_MS + 10_000,
) -> dict:
    return {
        "id": deposit_id,
        "currency": currency,
        "chain": "btc",
        "status": status,
        "address": "bc1q-fake-address",
        "memo": "",
        "amount": amount,
        "walletTxId": "fake-wallet-tx-001",
        "createdAt": BASE_MS,
        "updatedAt": updated_at,
        "preConfirms": 1,
        "confirms": 3,
        "currentConfirms": 3,
    }


class FakeResponse:
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


def _b64_hmac(secret: str, message: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def test_private_rest_signature_uses_raw_query_and_safe_config_hides_credentials() -> None:
    calls: list[dict] = []

    def request(method, url, **kwargs):
        calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse(200, {"code": "200000", "data": {}})

    client = kucoin_watcher.KuCoinClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=API_PASSPHRASE,
        api_key_version=API_VERSION,
        site="eu",
        request_fn=request,
        clock_ms_fn=lambda: BASE_MS,
        allow_live_reads=True,
    )
    client._request("GET", "/api/v1/example", params=[("value", "abc!@#11")])

    call = calls[0]
    assert call["url"] == "https://api.kucoin.eu/api/v1/example?value=abc%21%40%2311"
    prehash = f"{BASE_MS}GET/api/v1/example?value=abc!@#11"
    assert call["headers"]["KC-API-SIGN"] == _b64_hmac(API_SECRET, prehash)
    assert call["headers"]["KC-API-PASSPHRASE"] == _b64_hmac(
        API_SECRET, API_PASSPHRASE
    )
    safe = json.dumps(client.safe_config(), sort_keys=True)
    assert "https://api.kucoin.eu" in safe
    assert API_KEY not in safe
    assert API_SECRET not in safe
    assert API_PASSPHRASE not in safe


def test_live_reads_disabled_by_default_and_uta_fails_closed() -> None:
    client = kucoin_watcher.KuCoinClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=API_PASSPHRASE,
        api_key_version=API_VERSION,
    )
    with pytest.raises(kucoin_watcher.KuCoinError, match="explicit"):
        client.get_deposit_history()
    with pytest.raises(kucoin_watcher.KuCoinError, match="Classic Account"):
        kucoin_watcher.KuCoinClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            api_passphrase=API_PASSPHRASE,
            api_key_version=API_VERSION,
            account_mode="uta",
        )


def test_retry_resigns_each_attempt_and_redacts_credentials() -> None:
    calls: list[dict] = []
    timestamps = iter([BASE_MS, BASE_MS + 1, BASE_MS + 2])

    def request(method, url, **kwargs):
        calls.append({"method": method, "url": url, **kwargs})
        raise RuntimeError(f"network {API_KEY} {API_SECRET} {API_PASSPHRASE}")

    client = kucoin_watcher.KuCoinClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=API_PASSPHRASE,
        api_key_version=API_VERSION,
        request_fn=request,
        sleep_fn=lambda _seconds: None,
        clock_ms_fn=lambda: next(timestamps),
        max_retries=2,
        allow_live_reads=True,
    )
    with pytest.raises(kucoin_watcher.KuCoinProviderUnavailable) as exc:
        client.get_private_ws_token()
    assert len(calls) == 3
    assert [c["headers"]["KC-API-TIMESTAMP"] for c in calls] == [
        str(BASE_MS), str(BASE_MS + 1), str(BASE_MS + 2)
    ]
    message = str(exc.value)
    assert API_KEY not in message
    assert API_SECRET not in message
    assert API_PASSPHRASE not in message
    assert "[REDACTED]" in message


def test_private_token_contract_accepts_dynamic_secure_endpoint() -> None:
    def request(_method, _url, **_kwargs):
        return FakeResponse(
            200,
            {
                "code": "200000",
                "data": {
                    "token": "fake-private-token",
                    "instanceServers": [{
                        "endpoint": "wss://ws-api-spot.kucoin.test/",
                        "pingInterval": 18000,
                        "pingTimeout": 10000,
                    }],
                },
            },
        )

    client = kucoin_watcher.KuCoinClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=API_PASSPHRASE,
        api_key_version=API_VERSION,
        request_fn=request,
        allow_live_reads=True,
    )
    token = client.get_private_ws_token()
    assert token == {
        "token": "fake-private-token",
        "endpoint": "wss://ws-api-spot.kucoin.test",
        "ping_interval_ms": 18000,
        "ping_timeout_ms": 10000,
    }


def test_exact_success_settles_and_replay_deduplicates(paths) -> None:
    _intent(paths["payment"])
    deposit = _deposit()
    first = kucoin_watcher.reconcile_deposit(
        deposit,
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        trigger="TEST",
    )
    replay = kucoin_watcher.reconcile_deposit(
        deposit,
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        trigger="TEST-REPLAY",
    )
    assert first["status"] == "SETTLED"
    assert first["ledger_appended"] is True
    assert replay["status"] == "DUPLICATE_PROVIDER_EVENT"
    settlement = payment_ledger.settled_payment_record(
        "intent-kucoin-1", str(paths["payment"])
    )
    assert settlement["wallet_tx_id"] == "fake-wallet-tx-001"
    assert settlement["provider_tx_ref"] == "deposit-1"
    events = kucoin_watcher.load_events(str(paths["adapter"]))
    assert len(events) == 1
    assert events[0]["address"] == "bc1q-fake-address"
    assert events[0]["network"] == "btc"
    assert events[0]["current_confirms"] == 3


def test_processing_then_success_reconciles_state_evolution(paths) -> None:
    _intent(paths["payment"])
    first = kucoin_watcher.reconcile_deposit(
        _deposit(status="PROCESSING", updated_at=BASE_MS + 5_000),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    second = kucoin_watcher.reconcile_deposit(
        _deposit(status="SUCCESS", updated_at=BASE_MS + 10_000),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert first["status"] == "PENDING"
    assert second["status"] == "SETTLED"
    provider_rows = [
        row for row in payment_ledger.load_ledger(str(paths["payment"]))
        if row.get("event_type") == payment_ledger.EVENT_PROVIDER
    ]
    assert [row["payment_state"] for row in provider_rows] == ["PENDING", "SETTLED"]
    assert provider_rows[0]["provider_event_id"] != provider_rows[1]["provider_event_id"]


@pytest.mark.parametrize(
    ("observed", "expected_reason"),
    [("1.00000000", "UNDERPAID"), ("2.00000000", "OVERPAID")],
)
def test_amount_mismatch_requires_manual_review(
    paths, observed: str, expected_reason: str
) -> None:
    _intent(paths["payment"])
    result = kucoin_watcher.reconcile_deposit(
        _deposit(amount=observed),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert result["status"] == "MANUAL_REVIEW_REQUIRED"
    assert result["reason"] == expected_reason
    assert result["ledger_appended"] is False
    assert payment_ledger.settled_payment_record(
        "intent-kucoin-1", str(paths["payment"])
    ) is None


def test_unmatched_and_ambiguous_deposits_cannot_create_payment_truth(paths) -> None:
    unmatched = kucoin_watcher.reconcile_deposit(
        _deposit(),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert unmatched["reason"] == "UNMATCHED"

    _intent(paths["payment"], intent_id="intent-kucoin-a")
    _intent(paths["payment"], intent_id="intent-kucoin-b")
    ambiguous = kucoin_watcher.reconcile_deposit(
        _deposit(deposit_id="deposit-ambiguous"),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert ambiguous["status"] == "MANUAL_REVIEW_REQUIRED"
    assert ambiguous["reason"] == "AMBIGUOUS"
    provider_rows = [
        row for row in payment_ledger.load_ledger(str(paths["payment"]))
        if row.get("event_type") == payment_ledger.EVENT_PROVIDER
    ]
    assert provider_rows == []


def test_four_letter_asset_fails_closed_at_payment_ledger_boundary(paths) -> None:
    result = kucoin_watcher.reconcile_deposit(
        _deposit(currency="USDT", amount="10.00000000"),
        asset_scales={"USDT": 8},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert result["status"] == "MANUAL_REVIEW_REQUIRED"
    assert result["reason"] == "LEDGER_CURRENCY_CONTRACT_UNSUPPORTED"
    assert result["ledger_appended"] is False
    assert payment_ledger.load_ledger(str(paths["payment"])) == []


class FakeHistoryClient:
    def __init__(self, deposits=None, *, unavailable: bool = False) -> None:
        self.deposits = list(deposits or [])
        self.unavailable = unavailable

    def list_deposit_history(self, **_kwargs):
        if self.unavailable:
            raise kucoin_watcher.KuCoinProviderUnavailable("provider unavailable")
        return [dict(row) for row in self.deposits]

    def get_private_ws_token(self):
        return {
            "token": "fake-ws-token",
            "endpoint": "wss://ws-api-spot.kucoin.test",
            "ping_interval_ms": 18000,
            "ping_timeout_ms": 10000,
        }


def test_provider_outage_never_fabricates_success(paths) -> None:
    _intent(paths["payment"])
    result = kucoin_watcher.reconcile_recent_deposits(
        client=FakeHistoryClient(unavailable=True),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert result["status"] == "PROVIDER_UNAVAILABLE"
    assert result["ledger_appended"] is False
    assert payment_ledger.settled_payment_record(
        "intent-kucoin-1", str(paths["payment"])
    ) is None


def test_websocket_deposit_is_trigger_only_and_rest_is_authority(paths) -> None:
    _intent(paths["payment"])
    message = {
        "type": "message",
        "topic": kucoin_watcher.BALANCE_TOPIC,
        "data": {
            "currency": "BTC",
            "relationEvent": kucoin_watcher.DEPOSIT_RELATION_EVENT,
            "relationEventId": "ws-event-1",
        },
    }
    no_rest = kucoin_watcher.KuCoinAccountWatcher(
        client=FakeHistoryClient([]),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    ).handle_message(message)
    assert no_rest["reconciliation"]["deposit_count"] == 0
    assert payment_ledger.settled_payment_record(
        "intent-kucoin-1", str(paths["payment"])
    ) is None

    with_rest = kucoin_watcher.KuCoinAccountWatcher(
        client=FakeHistoryClient([_deposit()]),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    ).handle_message(message)
    assert with_rest["trigger_appended"] is False
    assert with_rest["reconciliation"]["results"][0]["status"] == "SETTLED"


def test_non_deposit_websocket_message_is_ignored(paths) -> None:
    watcher = kucoin_watcher.KuCoinAccountWatcher(
        client=FakeHistoryClient([_deposit()]),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
    )
    assert watcher.handle_message({
        "type": "message",
        "topic": kucoin_watcher.BALANCE_TOPIC,
        "data": {"relationEvent": "main.transfer"},
    }) == {"status": "IGNORED"}
    assert kucoin_watcher.load_events(str(paths["adapter"])) == []


class FakeWebSocketConnectionClosedException(Exception):
    pass


class FakeWS:
    def __init__(self, messages) -> None:
        self.messages = list(messages)
        self.sent: list[dict] = []
        self.closed = False

    def recv(self):
        if not self.messages:
            raise FakeWebSocketConnectionClosedException("closed")
        item = self.messages.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def send(self, payload: str):
        self.sent.append(json.loads(payload))

    def close(self):
        self.closed = True


def test_watcher_reconnects_on_transport_close_and_subscribes_privately(paths) -> None:
    first = FakeWS([
        json.dumps({"type": "welcome"}),
        FakeWebSocketConnectionClosedException("closed"),
    ])
    second = FakeWS([
        json.dumps({"type": "welcome"}),
        json.dumps({"type": "message", "topic": "/other", "data": {}}),
    ])
    sockets = iter([first, second])
    watcher = kucoin_watcher.KuCoinAccountWatcher(
        client=FakeHistoryClient([]),
        asset_scales={"BTC": SCALE},
        path=str(paths["adapter"]),
        payment_path=str(paths["payment"]),
        ws_connect_fn=lambda _url, _timeout: next(sockets),
        sleep_fn=lambda _seconds: None,
    )
    result = watcher.run_with_reconnect(
        max_reconnects=2,
        max_messages_per_session=1,
    )
    assert result["status"] == "SESSION_COMPLETE"
    assert result["reconnects"] == 1
    assert first.closed is True and second.closed is True
    assert first.sent[0]["topic"] == kucoin_watcher.BALANCE_TOPIC
    assert first.sent[0]["privateChannel"] == "true"
    reconnects = [
        row for row in kucoin_watcher.load_events(str(paths["adapter"]))
        if row.get("event_type") == kucoin_watcher.EVENT_WATCHER_RECONNECT
    ]
    assert len(reconnects) == 1
