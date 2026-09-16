from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import payment_ledger


INTENT_ID = "intent-test-001"
SUBSCRIBER = "subscriber-test-001"
PRODUCT_ID = "BINARY_TRADING"
PLAN_ID = "BINARY_TRADING_BASIC"
PROVIDER = "TEST_PROVIDER"
AMOUNT = 1200
CURRENCY = "EUR"


@pytest.fixture
def ledger_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    return tmp_path / "billing" / "payment_ledger.jsonl"


def _create_intent(path: Path, *, idempotency_key: str = "intent-idem-001") -> dict:
    return payment_ledger.create_payment_intent(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT_ID,
        plan_id=PLAN_ID,
        amount_minor=AMOUNT,
        currency=CURRENCY,
        payment_method="FIAT",
        provider=PROVIDER,
        idempotency_key=idempotency_key,
        payment_intent_id=INTENT_ID,
        audit_correlation_id="audit-intent-001",
        now_ts=1_700_000_000,
        path=str(path),
    )


def _provider_event(
    path: Path,
    *,
    payment_state: str = "SETTLED",
    provider_state: str | None = None,
    idempotency_key: str = "provider-idem-001",
    provider_event_id: str = "provider-event-001",
    provider_tx_ref: str = "provider-tx-001",
    wallet_tx_id: str | None = None,
    raw_event_hash: str = "0123456789abcdef0123456789abcdef",
    amount_minor: int = AMOUNT,
    currency: str = CURRENCY,
    provider: str = PROVIDER,
    payment_intent_id: str = INTENT_ID,
    received_at_ts: int = 1_700_000_100,
) -> dict:
    return payment_ledger.ingest_provider_event(
        payment_intent_id=payment_intent_id,
        provider=provider,
        payment_state=payment_state,
        provider_state=provider_state or payment_state,
        amount_minor=amount_minor,
        currency=currency,
        raw_event_hash=raw_event_hash,
        idempotency_key=idempotency_key,
        provider_event_id=provider_event_id,
        provider_tx_ref=provider_tx_ref,
        wallet_tx_id=wallet_tx_id,
        settled_at_ts=received_at_ts if payment_state == "SETTLED" else None,
        audit_correlation_id=f"audit-{idempotency_key}",
        received_at_ts=received_at_ts,
        path=str(path),
    )


def _lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_create_intent_is_append_only_and_idempotent(ledger_file: Path) -> None:
    created = _create_intent(ledger_file)
    replay = _create_intent(ledger_file)

    assert created["status"] == "CREATED"
    assert created["appended"] is True
    assert replay["status"] == "DUPLICATE"
    assert replay["appended"] is False
    records = _lines(ledger_file)
    assert len(records) == 1
    record = records[0]
    assert record["ledger_seq"] == 1
    assert record["event_type"] == payment_ledger.EVENT_INTENT_CREATED
    assert record["payment_state"] == "CREATED"
    assert record["payment_intent_id"] == INTENT_ID
    assert record["subscriber_ref"] == SUBSCRIBER
    assert record["strategy_product_id"] == PRODUCT_ID
    assert record["plan_id"] == PLAN_ID
    assert record["amount_minor"] == AMOUNT
    assert record["currency"] == CURRENCY
    assert record["reconciliation_result"] == "NOT_APPLICABLE"
    assert "entitlement_id" not in record
    assert "entitlement_version" not in record


def test_free_plan_cannot_create_paid_payment_intent(ledger_file: Path) -> None:
    with pytest.raises(payment_ledger.PaymentLedgerError):
        payment_ledger.create_payment_intent(
            subscriber_ref=SUBSCRIBER,
            strategy_product_id=PRODUCT_ID,
            plan_id="BINARY_TRADING_FREE",
            amount_minor=0,
            currency=CURRENCY,
            payment_method="FIAT",
            provider=PROVIDER,
            idempotency_key="free-intent",
            payment_intent_id="free-intent-id",
            path=str(ledger_file),
        )
    assert not ledger_file.exists()


def test_intent_idempotency_key_cannot_be_reused_for_different_evidence(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    with pytest.raises(payment_ledger.PaymentLedgerError):
        payment_ledger.create_payment_intent(
            subscriber_ref="different-subscriber",
            strategy_product_id=PRODUCT_ID,
            plan_id=PLAN_ID,
            amount_minor=AMOUNT,
            currency=CURRENCY,
            payment_method="FIAT",
            provider=PROVIDER,
            idempotency_key="intent-idem-001",
            payment_intent_id="different-intent",
            path=str(ledger_file),
        )
    assert len(_lines(ledger_file)) == 1


def test_matching_pending_and_settled_events_preserve_attribution(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    pending = _provider_event(
        ledger_file,
        payment_state="PENDING",
        idempotency_key="pending-idem",
        provider_event_id="event-pending",
        provider_tx_ref="tx-shared",
        raw_event_hash="11111111111111111111111111111111",
        received_at_ts=1_700_000_050,
    )
    settled = _provider_event(
        ledger_file,
        payment_state="SETTLED",
        idempotency_key="settled-idem",
        provider_event_id="event-settled",
        provider_tx_ref="tx-shared",
        raw_event_hash="22222222222222222222222222222222",
        received_at_ts=1_700_000_100,
    )

    assert pending["status"] == "PENDING"
    assert settled["status"] == "SETTLED"
    record = settled["record"]
    assert record["subscriber_ref"] == SUBSCRIBER
    assert record["strategy_product_id"] == PRODUCT_ID
    assert record["plan_id"] == PLAN_ID
    assert record["reconciliation_result"] == "MATCHED"
    assert record["settled_at"].endswith("Z")
    authoritative = payment_ledger.settled_payment_record(INTENT_ID, str(ledger_file))
    assert authoritative is not None
    assert authoritative["ledger_event_id"] == record["ledger_event_id"]


def test_same_provider_event_with_different_idempotency_key_is_not_appended(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    first = _provider_event(ledger_file)
    second = _provider_event(ledger_file, idempotency_key="provider-idem-replayed")

    assert first["status"] == "SETTLED"
    assert second["status"] == "DUPLICATE_PROVIDER_EVENT"
    assert second["appended"] is False
    records = _lines(ledger_file)
    assert len(records) == 2
    assert len([r for r in records if r.get("payment_state") == "SETTLED"]) == 1


def test_provider_event_identity_collision_routes_to_one_contradiction(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    _provider_event(ledger_file)
    collision = _provider_event(
        ledger_file,
        idempotency_key="collision-idem-1",
        provider_event_id="provider-event-001",
        provider_tx_ref="provider-tx-002",
        raw_event_hash="33333333333333333333333333333333",
        payment_state="REFUNDED",
        received_at_ts=1_700_000_200,
    )
    replay = _provider_event(
        ledger_file,
        idempotency_key="collision-idem-2",
        provider_event_id="provider-event-001",
        provider_tx_ref="provider-tx-002",
        raw_event_hash="33333333333333333333333333333333",
        payment_state="REFUNDED",
        received_at_ts=1_700_000_300,
    )

    assert collision["status"] == "CONTRADICTORY"
    assert collision["record"]["payment_state"] == "UNKNOWN"
    assert collision["record"]["reconciliation_result"] == "CONTRADICTORY"
    assert "PROVIDER_EVENT_IDENTITY_COLLISION" in collision["record"]["reconciliation_reason"]
    assert replay["status"] == "CONTRADICTORY"
    assert replay["appended"] is False
    contradictions = [
        r for r in _lines(ledger_file)
        if r.get("event_type") == payment_ledger.EVENT_RECONCILIATION
        and r.get("reconciliation_result") == "CONTRADICTORY"
    ]
    assert len(contradictions) == 1


def test_second_distinct_settlement_is_contradictory_not_second_settlement(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    first = _provider_event(ledger_file)
    second = _provider_event(
        ledger_file,
        idempotency_key="settlement-2",
        provider_event_id="provider-event-002",
        provider_tx_ref="provider-tx-002",
        raw_event_hash="44444444444444444444444444444444",
        received_at_ts=1_700_000_200,
    )

    assert first["status"] == "SETTLED"
    assert second["status"] == "CONTRADICTORY"
    assert second["record"]["payment_state"] == "UNKNOWN"
    assert second["record"]["reconciliation_reason"] == "SECOND_SETTLEMENT_ATTEMPT_FOR_INTENT"
    matched_settlements = [
        r for r in _lines(ledger_file)
        if r.get("payment_state") == "SETTLED"
        and r.get("reconciliation_result") == "MATCHED"
    ]
    assert len(matched_settlements) == 1


def test_unmatched_provider_event_is_reconciliation_only_and_replay_dedupes(ledger_file: Path) -> None:
    first = _provider_event(
        ledger_file,
        payment_intent_id="missing-intent",
        idempotency_key="unmatched-1",
    )
    replay = _provider_event(
        ledger_file,
        payment_intent_id="missing-intent",
        idempotency_key="unmatched-2",
        received_at_ts=1_700_000_300,
    )

    assert first["status"] == "UNMATCHED"
    assert first["record"]["payment_state"] == "UNKNOWN"
    assert first["record"]["reconciliation_result"] == "UNMATCHED"
    assert first["record"]["reconciliation_reason"] == "PAYMENT_INTENT_NOT_FOUND"
    assert "entitlement_id" not in first["record"]
    assert replay["status"] == "UNMATCHED"
    assert replay["appended"] is False
    assert len(_lines(ledger_file)) == 1


def test_provider_amount_currency_or_provider_mismatch_is_contradictory(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    mismatch = _provider_event(
        ledger_file,
        provider="OTHER_PROVIDER",
        amount_minor=AMOUNT + 1,
        currency="USD",
        provider_event_id="mismatch-event",
        provider_tx_ref="mismatch-tx",
        raw_event_hash="55555555555555555555555555555555",
    )

    assert mismatch["status"] == "CONTRADICTORY"
    assert mismatch["record"]["payment_state"] == "UNKNOWN"
    reason = mismatch["record"]["reconciliation_reason"]
    assert "provider" in reason
    assert "amount_minor" in reason
    assert "currency" in reason
    assert payment_ledger.settled_payment_record(INTENT_ID, str(ledger_file)) is None


def test_refund_is_compensating_append_and_original_settlement_is_immutable(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    settlement = _provider_event(ledger_file)
    before = json.loads(json.dumps(settlement["record"]))
    refund = _provider_event(
        ledger_file,
        payment_state="REFUNDED",
        idempotency_key="refund-1",
        provider_event_id="refund-event-1",
        provider_tx_ref="provider-tx-001",
        raw_event_hash="66666666666666666666666666666666",
        received_at_ts=1_700_000_200,
    )

    assert refund["status"] == "REFUNDED"
    assert refund["record"]["event_type"] == payment_ledger.EVENT_REVERSAL
    assert refund["record"]["reversal_of_ledger_event_id"] == settlement["record"]["ledger_event_id"]
    records = _lines(ledger_file)
    original = next(r for r in records if r["ledger_event_id"] == settlement["record"]["ledger_event_id"])
    assert original == before
    assert len(records) == 3


def test_reversal_replay_with_different_idempotency_does_not_append(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    _provider_event(ledger_file)
    first = _provider_event(
        ledger_file,
        payment_state="CHARGEBACK",
        idempotency_key="chargeback-1",
        provider_event_id="chargeback-event",
        provider_tx_ref="provider-tx-001",
        raw_event_hash="77777777777777777777777777777777",
        received_at_ts=1_700_000_200,
    )
    replay = _provider_event(
        ledger_file,
        payment_state="CHARGEBACK",
        idempotency_key="chargeback-2",
        provider_event_id="chargeback-event",
        provider_tx_ref="provider-tx-001",
        raw_event_hash="77777777777777777777777777777777",
        received_at_ts=1_700_000_300,
    )

    assert first["status"] == "CHARGEBACK"
    assert replay["status"] == "DUPLICATE_PROVIDER_EVENT"
    assert replay["appended"] is False
    reversals = [r for r in _lines(ledger_file) if r.get("event_type") == payment_ledger.EVENT_REVERSAL]
    assert len(reversals) == 1


def test_second_distinct_reversal_is_contradictory(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    _provider_event(ledger_file)
    _provider_event(
        ledger_file,
        payment_state="REFUNDED",
        idempotency_key="refund-1",
        provider_event_id="refund-event-1",
        provider_tx_ref="provider-tx-001",
        raw_event_hash="88888888888888888888888888888888",
        received_at_ts=1_700_000_200,
    )
    second = _provider_event(
        ledger_file,
        payment_state="CHARGEBACK",
        idempotency_key="chargeback-distinct",
        provider_event_id="chargeback-event-distinct",
        provider_tx_ref="provider-tx-001",
        raw_event_hash="99999999999999999999999999999999",
        received_at_ts=1_700_000_300,
    )

    assert second["status"] == "CONTRADICTORY"
    assert second["record"]["reconciliation_reason"] == "SECOND_REVERSAL_ATTEMPT_FOR_INTENT"
    reversals = [r for r in _lines(ledger_file) if r.get("event_type") == payment_ledger.EVENT_REVERSAL]
    assert len(reversals) == 1


def test_reversal_without_settlement_is_contradictory(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    reversal = _provider_event(
        ledger_file,
        payment_state="REFUNDED",
        idempotency_key="refund-before-settle",
        provider_event_id="refund-before-event",
        provider_tx_ref="refund-before-tx",
        raw_event_hash="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )

    assert reversal["status"] == "CONTRADICTORY"
    assert reversal["record"]["reconciliation_reason"] == "REVERSAL_WITHOUT_MATCHED_SETTLEMENT"
    assert not any(r.get("event_type") == payment_ledger.EVENT_REVERSAL for r in _lines(ledger_file))


def test_provider_event_rejects_missing_provider_reference(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    with pytest.raises(payment_ledger.PaymentLedgerError):
        payment_ledger.ingest_provider_event(
            payment_intent_id=INTENT_ID,
            provider=PROVIDER,
            payment_state="PENDING",
            provider_state="pending",
            amount_minor=AMOUNT,
            currency=CURRENCY,
            raw_event_hash="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            idempotency_key="missing-provider-ref",
            path=str(ledger_file),
        )
    assert len(_lines(ledger_file)) == 1


def test_ledger_stores_hash_reference_not_raw_provider_payload(ledger_file: Path) -> None:
    _create_intent(ledger_file)
    _provider_event(ledger_file)
    for record in _lines(ledger_file):
        assert "raw_event" not in record
        assert "raw_payload" not in record
        assert "provider_secret" not in record
        if record["event_type"] != payment_ledger.EVENT_INTENT_CREATED:
            assert record["raw_event_hash"]


def test_invalid_json_corruption_fails_closed(ledger_file: Path) -> None:
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    ledger_file.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(payment_ledger.PaymentLedgerError):
        payment_ledger.load_ledger(str(ledger_file))
    with pytest.raises(payment_ledger.PaymentLedgerError):
        _create_intent(ledger_file)


def test_duplicate_sequence_corruption_fails_closed(ledger_file: Path) -> None:
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    first = {
        "ledger_event_id": "event-1",
        "ledger_seq": 1,
        "event_type": payment_ledger.EVENT_INTENT_CREATED,
    }
    second = {
        "ledger_event_id": "event-2",
        "ledger_seq": 1,
        "event_type": payment_ledger.EVENT_PROVIDER,
    }
    ledger_file.write_text(
        json.dumps(first) + "\n" + json.dumps(second) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(payment_ledger.PaymentLedgerError):
        payment_ledger.load_ledger(str(ledger_file))
