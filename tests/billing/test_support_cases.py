from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import notification_scheduler, payment_ledger, support_cases
from core import storage

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


def _open_case(
    paths,
    *,
    subscriber: str = "support-sub",
    intent_id: str | None = "support-intent",
) -> dict:
    return support_cases.open_case(
        subscriber_ref=subscriber,
        strategy_product_id=PRODUCT,
        payment_intent_id=intent_id,
        reason="Payment review requested",
        now_ts=BASE,
        path=str(paths["support"]),
    )["record"]


def _proof(
    paths,
    case_id: str,
    *,
    subscriber: str = "support-sub",
    intent_id: str | None = "support-intent",
    content: bytes = b"proof-image-content",
    declared: bool = True,
) -> dict:
    kwargs = {}
    if declared:
        kwargs.update(
            declared_amount_minor=1200,
            declared_currency="EUR",
        )
    return support_cases.add_payment_proof(
        case_id=case_id,
        subscriber_ref=subscriber,
        payment_intent_id=intent_id,
        content_bytes=content,
        telegram_file_id="restricted-file-id",
        telegram_file_unique_id="unique-file-id",
        file_name="receipt.png",
        mime_type="image/png",
        file_size=len(content),
        caption="Payment proof",
        now_ts=BASE + 10,
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
        **kwargs,
    )["record"]


def _settle(
    payment_path: Path,
    *,
    intent_id: str = "support-intent",
    amount: int = 1200,
    suffix: str = "a",
) -> dict:
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


def test_payment_proof_is_hashed_restricted_duplicate_safe_and_client_redacted(paths) -> None:
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
        telegram_file_id="rotated-file-id",
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
    proof = first["record"]
    assert proof["proof_restricted"] is True
    assert proof["proof_sha256"] == hashlib.sha256(b"same-proof").hexdigest()
    assert proof["restricted_telegram_file_id"] == "secret-telegram-file-id"

    safe = support_cases.client_safe_case_view(
        case_id=case["case_id"],
        subscriber_ref="support-sub",
        path=str(paths["support"]),
    )
    serialized = json.dumps(safe)
    assert "secret-telegram-file-id" not in serialized
    assert "file-unique" not in serialized
    assert "support-intent" not in serialized
    assert str(REVIEWER) not in serialized


def test_unlinked_proof_can_be_correlated_later_and_verify_requires_link(paths) -> None:
    case = _open_case(paths, intent_id=None)
    proof = _proof(paths, case["case_id"], intent_id=None)
    assert proof["payment_intent_id"] is None

    with pytest.raises(
        support_cases.BillingSupportError,
        match="payment-intent correlation",
    ):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            action="VERIFY",
            reason="Cannot verify before deterministic payment correlation",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )

    _intent(paths["payment"])
    linked = support_cases.link_payment_intent(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        payment_intent_id="support-intent",
        reason="Payment intent matched to subscriber and proof evidence",
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    assert linked["record"]["payment_intent_id"] == "support-intent"
    reviewed = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="VERIFY",
        reason="Linked proof reviewed against payment intent",
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    assert reviewed["status"] == "VERIFIED"


def test_link_rejects_declared_amount_conflict(paths) -> None:
    case = _open_case(paths, intent_id=None)
    support_cases.add_payment_proof(
        case_id=case["case_id"],
        subscriber_ref="support-sub",
        content_bytes=b"proof",
        telegram_file_id="file-id",
        telegram_file_unique_id="unique-id",
        declared_amount_minor=1300,
        declared_currency="EUR",
        path=str(paths["support"]),
    )
    _intent(paths["payment"], amount=1200)
    with pytest.raises(
        support_cases.BillingSupportError,
        match="Proof amount conflicts",
    ):
        support_cases.link_payment_intent(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            payment_intent_id="support-intent",
            reason="Attempt deterministic correlation",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )


def test_verify_requires_authorized_reviewer_proof_and_meaningful_reason(paths) -> None:
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
    with pytest.raises(support_cases.BillingSupportError, match="payment proof"):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            action="VERIFY",
            reason="No proof exists yet",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )
    with pytest.raises(support_cases.BillingSupportError, match="meaningful"):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            action="REJECT",
            reason="x",
            path=str(paths["support"]),
        )


def test_manual_verify_writes_payment_truth_but_not_subscription_or_entitlement(paths) -> None:
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
    ledger = reviewed["payment_ledger_result"]["record"]
    assert ledger["event_type"] == support_cases.PAYMENT_EVENT_MANUAL_VERIFICATION
    assert ledger["payment_state"] == "SETTLED"
    assert ledger["reconciliation_result"] == "MATCHED"
    assert ledger["case_id"] == case["case_id"]
    assert payment_ledger.settled_payment_record(
        "support-intent", str(paths["payment"])
    )["ledger_event_id"] == ledger["ledger_event_id"]
    assert not paths["subscription"].exists()


def test_manual_verify_replays_preexisting_payment_evidence_after_partial_failure(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    proof = _proof(paths, case["case_id"])
    current = support_cases.current_case(case["case_id"], str(paths["support"]))

    with storage.with_lock("billing_payment_ledger"):
        payment_records = payment_ledger.load_ledger(str(paths["payment"]))
        first = support_cases._manual_payment_verification_evidence_unlocked(
            case=current,
            proof=proof,
            reviewer_user_id=REVIEWER,
            review_reason="Simulate payment append before support append",
            now=BASE + 30,
            payment_target=str(paths["payment"]),
            payment_records=payment_records,
        )
    assert first["status"] == "MANUAL_SETTLEMENT_RECORDED"
    assert support_cases.current_case(
        case["case_id"], str(paths["support"])
    )["case_state"] == "UNDER_REVIEW"

    recovered = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="VERIFY",
        reason="Replay after partial failure",
        now_ts=BASE + 31,
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    assert recovered["status"] == "VERIFIED"
    assert recovered["payment_ledger_result"]["status"] == "DUPLICATE"
    settlements = [
        row
        for row in payment_ledger.payment_history(
            "support-intent", str(paths["payment"])
        )
        if row.get("payment_state") == "SETTLED"
        and row.get("reconciliation_result") == "MATCHED"
    ]
    assert len(settlements) == 1


def test_existing_provider_settlement_gets_audit_without_duplicate_settlement(paths) -> None:
    _intent(paths["payment"])
    provider_settlement = _settle(paths["payment"])
    case = _open_case(paths)
    _proof(paths, case["case_id"])
    reviewed = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="VERIFY",
        reason="Existing provider settlement cross-checked against proof",
        path=str(paths["support"]),
        payment_path=str(paths["payment"]),
    )
    assert reviewed["status"] == "VERIFIED"
    assert (
        reviewed["payment_ledger_result"]["status"]
        == "ALREADY_SETTLED_REVIEW_AUDITED"
    )
    history = payment_ledger.payment_history(
        "support-intent", str(paths["payment"])
    )
    settlements = [
        row
        for row in history
        if row.get("payment_state") == "SETTLED"
        and row.get("reconciliation_result") == "MATCHED"
    ]
    assert len(settlements) == 1
    assert settlements[0]["ledger_event_id"] == provider_settlement["ledger_event_id"]
    audits = [
        row
        for row in history
        if row.get("event_type")
        == support_cases.PAYMENT_EVENT_MANUAL_REVIEW_AUDIT
    ]
    assert len(audits) == 1


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


def test_illegal_review_transition_is_rejected_and_reopen_creates_new_case(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    rejected = support_cases.review_case(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        action="REJECT",
        reason="Evidence cannot be validated",
        path=str(paths["support"]),
    )
    assert rejected["status"] == "REJECTED"
    with pytest.raises(support_cases.BillingSupportError, match="illegal"):
        support_cases.review_case(
            case_id=case["case_id"],
            reviewer_user_id=REVIEWER,
            action="VERIFY",
            reason="Illegal verification after rejection",
            path=str(paths["support"]),
            payment_path=str(paths["payment"]),
        )
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
    assert support_cases.current_case(
        case["case_id"], str(paths["support"])
    )["case_state"] == "REJECTED"


def test_message_relays_persist_delivery_evidence_and_hash_subscriber(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    sent: list[dict] = []
    client_result = support_cases.relay_client_message_to_admin(
        case_id=case["case_id"],
        subscriber_ref="support-sub",
        text="Please review my payment",
        client_message_id="client-msg-1",
        admin_chat_id=-100123,
        admin_thread_id=99,
        send_fn=lambda **kwargs: sent.append(kwargs) or {"ok": True},
        path=str(paths["support"]),
    )
    assert client_result["delivery_result"] == "SENT"
    assert "support-sub" not in sent[0]["text"]
    assert client_result["delivery_evidence"]["delivery_direction"] == "CLIENT_TO_ADMIN"

    notification_scheduler.bind_private_delivery_target(
        subscriber_ref="support-sub",
        telegram_user_id=12345,
        telegram_chat_id=12345,
        path=str(paths["notification"]),
    )
    admin_result = support_cases.relay_admin_reply_to_client(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        text="We need one more document.",
        admin_message_id="admin-msg-1",
        send_fn=lambda **kwargs: sent.append(kwargs) or {"ok": True},
        path=str(paths["support"]),
        notification_path=str(paths["notification"]),
    )
    assert admin_result["delivery_result"] == "SENT"
    assert admin_result["delivery_evidence"]["delivery_direction"] == "ADMIN_TO_CLIENT"
    history = support_cases.case_history(case["case_id"], str(paths["support"]))
    assert len(
        [
            row
            for row in history
            if row["event_type"] == support_cases.EVENT_MESSAGE_DELIVERY
        ]
    ) == 2


def test_restricted_case_view_requires_authorization_reason_and_is_audited(paths) -> None:
    _intent(paths["payment"])
    case = _open_case(paths)
    _proof(paths, case["case_id"])
    with pytest.raises(support_cases.BillingSupportError):
        support_cases.restricted_case_view(
            case_id=case["case_id"],
            reviewer_user_id=999,
            access_reason="Unauthorized read",
            path=str(paths["support"]),
        )
    before = len(
        support_cases.case_history(case["case_id"], str(paths["support"]))
    )
    view = support_cases.restricted_case_view(
        case_id=case["case_id"],
        reviewer_user_id=REVIEWER,
        access_reason="Review submitted payment proof",
        path=str(paths["support"]),
        now_ts=BASE + 50,
    )
    assert len(view["history"]) == before + 1
    assert (
        view["history"][-1]["event_type"]
        == support_cases.EVENT_RESTRICTED_ACCESS
    )
    assert view["history"][-1]["accessor_user_id"] == REVIEWER


def test_support_intent_opens_case_idempotently(paths) -> None:
    notification_path = paths["notification"]
    notification_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "billing_notification_event_id": "notif-event-1",
        "billing_notification_seq": 1,
        "event_type": notification_scheduler.EVENT_CLIENT_INTENT,
        "client_intent_id": "client-intent-support",
        "client_intent_status": "SUPPORT_REQUIRED",
        "client_action": "SUPPORT",
        "subscriber_ref": "support-intent-sub",
        "strategy_product_id": PRODUCT,
        "subscription_id": "sub-id-support-intent",
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
    notification_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    first = support_cases.open_case_from_client_intent(
        client_intent_id="client-intent-support",
        path=str(paths["support"]),
        notification_path=str(notification_path),
    )
    replay = support_cases.open_case_from_client_intent(
        client_intent_id="client-intent-support",
        path=str(paths["support"]),
        notification_path=str(notification_path),
    )
    assert first["status"] == "OPENED"
    assert replay["status"] == "EXISTS"
    assert first["record"]["case_id"] == replay["record"]["case_id"]


def test_two_cases_keep_global_sequence_contiguous(paths) -> None:
    first = support_cases.open_case(
        subscriber_ref="one",
        reason="First support request",
        path=str(paths["support"]),
    )
    second = support_cases.open_case(
        subscriber_ref="two",
        reason="Second support request",
        path=str(paths["support"]),
    )
    records = support_cases.load_case_events(str(paths["support"]))
    assert first["record"]["case_id"] != second["record"]["case_id"]
    assert [row["case_seq"] for row in records] == [1, 2]
