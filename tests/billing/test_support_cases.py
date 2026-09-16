from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import notification_scheduler, payment_ledger, subscription_registry, support_cases

PRODUCT = "BINARY_TRADING"
BASIC = "BINARY_TRADING_BASIC"
BASE = 1_700_000_000
REVIEWER = 424242


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(
        support_cases.admin_permissions,
        "is_primary_admin",
        lambda user_id: int(user_id) == REVIEWER,
    )
    return {
        "support": tmp_path / "billing" / "support_case_events.jsonl",
        "payment": tmp_path / "billing" / "payment_ledger.jsonl",
        "subscription": tmp_path / "billing" / "subscription_events.jsonl",
        "notification": tmp_path / "billing" / "notification_events.jsonl",
    }


def _intent(
    payment_path: Path,
    *,
    subscriber: str = "support-sub",
    intent_id: str = "support-intent",
    amount: int = 1200,
) -> dict:
    return payment_ledger.create_payment_intent(
        subscriber_ref=subscriber,
        strategy_product_id=PRODUCT,
        plan_id=BASIC,
        amount_minor=amount,
        currency="EUR",
        payment_method="FIAT",
        provider="TEST_PROVIDER",
        idempotency_key=f"create:{intent_id}",
        payment_intent_id=intent_id,
        audit_correlation_id=f"audit:{intent_id}",
        now_ts=BASE,
        path=str(payment_path),
    )["record"]


def _open_case(paths, *, subscriber="support-sub", intent_id="support-intent") -> dict:
    opened = support_cases.open_case(
        subscriber_ref=subscriber,
        strategy_product_id=PRODUCT,
        payment_intent_id=intent_id,
        reason="Payment review requested",
        now_ts=BASE,
        path=str(paths["support"]),
    )
    return opened["record"]


def _proof(paths, case_id: str, *, subscriber="support-sub", intent_id="support-intent", content=b"proof-image-content") -> dict:
    result = support_cases.add_payment_proof(
        case_id=case_id,
        subscriber_ref=subscriber,
        payment_intent_id=intent_id,
        content_bytes=content,
        telegram_file_id="restricted-file-id",
        telegram_file_unique_id="unique-file-id",
        file_name="receipt.png",
        mime_type="image/png",
        declared_amount_minor=1200,
        declared_currency="EUR",
        file_size=len(content),
        caption="Payment proof",
        now_ts=BASE + 10,
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    return result["record"]


def _settle(payment_path: Path, *, intent_id="support-intent", amount=1200, suffix="a") -> dict:
    return payment_ledger.ingest_provider_event(
        payment_intent_id=intent_id,
        provider="TEST_PROVIDER",
        payment_state="SETTLED",
        provider_state="settled",
        amount_minor=amount,
        currency="EUR",
        raw_event_hash=(suffix * 64)[:64],
        idempotency_key=f"settle:{intent_id}:{suffix}",
        provider_event_id=f"provider-event:{intent_id}:{suffix}",
        provider_tx_ref=f"provider-tx:{intent_id}",
        received_at_ts=BASE + 20,
        settled_at_ts=BASE + 20,
        path=str(payment_path),
    )["record"]


def test_payment_proof_is_hashed_restricted_and_duplicate_safe(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    first = support_cases.add_payment_proof(
        case_id=case["case_id"],
        subscriber_ref="support-sub",
        payment_intent_id="support-intent",
        content_bytes=b"same-proof",
        telegram_file_id="secret-telegram-file-id",
        telegram_file_unique_id="file-unique",
        file_name="receipt.png",
        mime_type="image/png",
        declared_amount_minor=1200,
        declared_currency="EUR",
        now_ts=BASE + 10,
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    replay = support_cases.add_payment_proof(
        case_id=case["case_id"],
        subscriber_ref="support-sub",
        payment_intent_id="support-intent",
        content_bytes=b"same-proof",
        telegram_file_id="secret-telegram-file-id-rotated",
        telegram_file_unique_id="file-unique",
        file_name="receipt.png",
        mime_type="image/png",
        declared_amount_minor=1200,
        declared_currency="EUR",
        now_ts=BASE + 11,
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )

    assert first["status"] == "PROOF_RECORDED"
    assert replay["status"] == "DUPLICATE"
    assert len(support_cases.case_history(case["case_id"], str(paths["support"]))) == 2
    proof = first["record"]
    assert proof["proof_restricted"] is True
    assert len(proof["proof_sha256"]) == 64
    assert proof["restricted_telegram_file_id"] == "secret-telegram-file-id"

    safe = support_cases.client_safe_case_view(
        case_id=case["case_id"],
        subscriber_ref="support-sub",
        path=str(paths["support"]),
    )
    serialized = json.dumps(safe)
    assert "secret-telegram-file-id" not in serialized
    assert "file-unique" not in serialized


def test_proof_amount_currency_and_subscriber_must_match_payment_intent(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    with pytest.raises(support_cases.BillingSupportError):
        support_cases.add_payment_proof(
            case_id=case["case_id"],
            subscriber_ref="support-sub",
            payment_intent_id="support-intent",
            content_bytes=b"proof",
            telegram_file_id="file-id",
            telegram_file_unique_id="unique",
            file_name="receipt.png",
            mime_type="image/png",
            declared_amount_minor=1300,
            declared_currency="EUR",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )


def test_verify_requires_authorized_reviewer_and_proof(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    with pytest.raises(support_cases.BillingSupportError):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=999,
            action="VERIFY",
            reason="Unauthorized review attempt",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )
    with pytest.raises(support_cases.BillingSupportError):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            action="VERIFY",
            reason="No proof exists yet",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )


def test_manual_verify_writes_payment_ledger_truth_but_not_entitlement(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    _proof(paths, case["case_id"])

    reviewed = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="VERIFY",
        reason="Proof amount and payment intent evidence reviewed",
        now_ts=BASE + 30,
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    assert reviewed["status"] == "VERIFIED"
    assert reviewed["record"]["reviewer_user_id"] == REVIEWER
    ledger_result = reviewed["payment_ledger_result"]
    assert ledger_result["status"] == "MANUAL_SETTLEMENT_RECORDED"
    ledger_record = ledger_result["record"]
    assert ledger_record["event_type"] == support_cases.PAYMENT_EVENT_MANUAL_VERIFICATION
    assert ledger_record["payment_state"] == "SETTLED"
    assert ledger_record["reconciliation_result"] == "MATCHED"
    assert ledger_record["case_id"] == case["case_id"]

    settled = payment_ledger.settled_payment_record(
        "support-intent", str(paths["payment"])
    )
    assert settled["ledger_event_id"] == ledger_record["ledger_event_id"]
    assert not paths["subscription"].exists()


def test_existing_provider_settlement_gets_review_audit_without_duplicate_settlement(paths) -> None:
    _intent(paths["payment"])
    provider_settlement = _settle(paths["payment"])
    case = _open_case(paths)
    _proof(paths, case["case_id"])

    reviewed = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="VERIFY",
        reason="Existing provider settlement cross-checked against proof",
        now_ts=BASE + 30,
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    assert reviewed["status"] == "VERIFIED"
    assert reviewed["payment_ledger_result"]["status"] == "ALREADY_SETTLED_REVIEW_AUDITED"
    history = payment_ledger.payment_history("support-intent", str(paths["payment"]))
    settlements = [
        row for row in history
        if row.get("payment_state") == "SETTLED"
        and row.get("reconciliation_result") == "MATCHED"
    ]
    assert len(settlements) == 1
    assert settlements[0]["ledger_event_id"] == provider_settlement["ledger_event_id"]
    audits = [
        row for row in history
        if row.get("event_type") == support_cases.PAYMENT_EVENT_MANUAL_REVIEW_AUDIT
    ]
    assert len(audits) == 1
    assert audits[0]["existing_settlement_ledger_event_id"] == provider_settlement["ledger_event_id"]


def test_contradictory_provider_evidence_forces_hold_escalation(paths) -> None:
    _intent(paths["payment"])
    contradiction = payment_ledger.ingest_provider_event(
        payment_intent_id="support-intent",
        provider="TEST_PROVIDER",
        payment_state="SETTLED",
        provider_state="settled",
        amount_minor=999,
        currency="EUR",
        raw_event_hash="c" * 64,
        idempotency_key="contradictory-provider-event",
        provider_event_id="contradictory-event",
        provider_tx_ref="contradictory-tx",
        path=str(paths["payment"]),
    )
    assert contradiction["status"] == "CONTRADICTORY"
    case = _open_case(paths)
    _proof(paths, case["case_id"])

    reviewed = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="VERIFY",
        reason="Attempted verification with contradictory provider evidence",
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    assert reviewed["status"] == "HOLD_ESCALATION"
    assert reviewed["record"]["review_action"] == "ESCALATE"
    assert payment_ledger.settled_payment_record(
        "support-intent", str(paths["payment"])
    ) is None


def test_reviewer_actions_require_reason_and_reopen_creates_new_case(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    with pytest.raises(support_cases.BillingSupportError):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            action="REJECT",
            reason="x",
            path=str(paths["support"]),
        )
    rejected = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="REJECT",
        reason="Proof cannot be validated against available evidence",
        path=str(paths["support"]),
    )
    assert rejected["status"] == "REJECTED"
    with pytest.raises(support_cases.BillingSupportError):
        support_cases.record_client_message(
            case_id=case["case_id"],
            subscriber_ref="support-sub",
            text="Trying to mutate closed case",
            client_message_id="late-message",
            path=str(paths["support"]),
        )

    reopened = support_cases.reopen_case(
        prior_case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        reason="Client supplied new evidence after rejection",
        path=str(paths["support"]),
    )
    assert reopened["record"]["case_id"] != case["case_id"]
    assert reopened["record"]["reopened_from_case_id"] == case["case_id"]
    assert reopened["record"]["case_version"] == 1
    assert support_cases.current_case(case["case_id"], str(paths["support"]))["case_state"] == "REJECTED"


def test_review_detects_concurrent_case_change(paths, monkeypatch) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    _proof(paths, case["case_id"])
    original = support_cases._manual_payment_verification_evidence

    def mutate_case_then_verify(**kwargs):
        support_cases.record_client_message(
            case_id=case["case_id"],
            subscriber_ref="support-sub",
            text="New information arrived during review",
            client_message_id="concurrent-message",
            path=str(paths["support"]),
        )
        return original(**kwargs)

    monkeypatch.setattr(
        support_cases,
        "_manual_payment_verification_evidence",
        mutate_case_then_verify,
    )
    with pytest.raises(
        support_cases.BillingSupportError,
        match="changed concurrently",
    ):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            action="VERIFY",
            reason="Review with concurrent client update",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )


def test_client_message_relay_to_admin_uses_hashed_subscriber_ref(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    sent: list[dict] = []

    def fake_send(**kwargs):
        sent.append(kwargs)
        return {"ok": True}

    result = support_cases.relay_client_message_to_admin(
        case_id=case["case_id"],
        subscriber_ref="support-sub",
        text="Please review my payment",
        client_message_id="client-msg-1",
        admin_chat_id=-100123,
        admin_thread_id=99,
        send_fn=fake_send,
        path=str(paths["support"]),
    )
    assert result["delivery_result"] == "SENT"
    assert len(sent) == 1
    assert "support-sub" not in sent[0]["text"]
    assert "Please review my payment" in sent[0]["text"]
    assert sent[0]["chat_id"] == -100123
    assert sent[0]["thread_id"] == 99


def test_admin_reply_uses_explicit_private_delivery_binding(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    notification_scheduler.bind_private_delivery_target(
        subscriber_ref="support-sub",
        telegram_user_id=12345,
        telegram_chat_id=12345,
        now_ts=BASE,
        path=str(paths["notification"]),
    )
    sent: list[dict] = []

    result = support_cases.relay_admin_reply_to_client(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        text="We need one more document.",
        admin_message_id="admin-msg-1",
        send_fn=lambda **kwargs: sent.append(kwargs) or {"ok": True},
        path=str(paths["support"]),
        notification_path=str(paths["notification"]),
    )
    assert result["delivery_result"] == "SENT"
    assert sent[0]["chat_id"] == 12345
    assert "one more document" in sent[0]["text"]


def test_support_intent_can_open_case_idempotently(paths) -> None:
    subscriber = "support-intent-sub"
    # Build the minimum notification event history that is still a real #163 client intent.
    subscription_id = "sub-id-support-intent"
    notification_path = str(paths["notification"])
    with storage_context(notification_path):
        pass

    # Use a direct append fixture matching #163's governed event schema rather than
    # requiring a paid subscription just to test support-case correlation.
    Path(notification_path).parent.mkdir(parents=True, exist_ok=True)
    row = {
        "billing_notification_event_id": "notif-event-1",
        "billing_notification_seq": 1,
        "event_type": notification_scheduler.EVENT_CLIENT_INTENT,
        "client_intent_id": "client-intent-support",
        "client_intent_status": "SUPPORT_REQUIRED",
        "client_action": "SUPPORT",
        "subscriber_ref": subscriber,
        "strategy_product_id": PRODUCT,
        "subscription_id": subscription_id,
        "source_subscription_event_id": "subscription-event-1",
        "entitlement_version": 1,
        "current_plan_id": BASIC,
        "current_tier": "BASIC",
        "requested_plan_id": None,
        "period_expires_at_epoch": BASE + 1000,
        "notification_key": "n1",
        "source_delivery_event_id": "d1",
        "telegram_user_id": 777,
        "telegram_chat_id": 777,
        "occurred_at_epoch": BASE,
        "idempotency_key": "intent-support-fixture",
        "audit_correlation_id": "audit-support-fixture",
    }
    Path(notification_path).write_text(json.dumps(row) + "\n", encoding="utf-8")

    first = support_cases.open_case_from_client_intent(
        client_intent_id="client-intent-support",
        path=str(paths["support"]),
        notification_path=notification_path,
    )
    replay = support_cases.open_case_from_client_intent(
        client_intent_id="client-intent-support",
        path=str(paths["support"]),
        notification_path=notification_path,
    )
    assert first["status"] == "OPENED"
    assert replay["status"] == "EXISTS"
    assert first["record"]["case_id"] == replay["record"]["case_id"]


class storage_context:
    """No-op context kept explicit so the fixture reads as an event-log setup."""

    def __init__(self, _path: str) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
