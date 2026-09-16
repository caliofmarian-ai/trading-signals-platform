from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import notification_scheduler, payment_ledger, subscription_registry


PRODUCT = "BINARY_TRADING"
FREE = "BINARY_TRADING_FREE"
BASIC = "BINARY_TRADING_BASIC"
PRO = "BINARY_TRADING_PRO"
ELITE = "BINARY_TRADING_ELITE"
BASE = 1_700_000_000
MONTH_END = BASE + 30 * 24 * 60 * 60


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    notification_scheduler._LAST_SCAN_MONOTONIC = 0.0
    return (
        tmp_path / "billing" / "notification_events.jsonl",
        tmp_path / "billing" / "subscription_events.jsonl",
        tmp_path / "billing" / "payment_ledger.jsonl",
    )


def _create_settled_payment(
    payment_path: Path,
    *,
    subscriber: str,
    plan_id: str,
    intent_id: str,
    amount_minor: int,
    suffix: str,
    settled_at: int = BASE + 10,
) -> None:
    payment_ledger.create_payment_intent(
        subscriber_ref=subscriber,
        strategy_product_id=PRODUCT,
        plan_id=plan_id,
        amount_minor=amount_minor,
        currency="EUR",
        payment_method="FIAT",
        provider="TEST_PROVIDER",
        idempotency_key=f"create:{intent_id}",
        payment_intent_id=intent_id,
        audit_correlation_id=f"audit:{intent_id}",
        now_ts=BASE,
        path=str(payment_path),
    )
    payment_ledger.ingest_provider_event(
        payment_intent_id=intent_id,
        provider="TEST_PROVIDER",
        payment_state="SETTLED",
        provider_state="settled",
        amount_minor=amount_minor,
        currency="EUR",
        raw_event_hash=(suffix * 64)[:64],
        idempotency_key=f"settle:{intent_id}",
        provider_event_id=f"event:{intent_id}",
        provider_tx_ref=f"tx:{intent_id}",
        settled_at_ts=settled_at,
        received_at_ts=settled_at,
        audit_correlation_id=f"audit-settle:{intent_id}",
        path=str(payment_path),
    )


def _activate(
    subscription_path: Path,
    payment_path: Path,
    *,
    subscriber: str,
    plan_id: str = BASIC,
    intent_id: str = "initial-basic",
    amount_minor: int = 1200,
    suffix: str = "a",
    start: int = BASE,
    end: int = MONTH_END,
) -> dict:
    _create_settled_payment(
        payment_path,
        subscriber=subscriber,
        plan_id=plan_id,
        intent_id=intent_id,
        amount_minor=amount_minor,
        suffix=suffix,
    )
    return subscription_registry.activate_from_settled_payment(
        payment_intent_id=intent_id,
        period_start_ts=start,
        period_end_ts=end,
        effective_at_ts=start + 10,
        path=str(subscription_path),
        payment_path=str(payment_path),
    )["record"]


def _bind(notification_path: Path, *, subscriber: str, telegram_id: int) -> dict:
    return notification_scheduler.bind_private_delivery_target(
        subscriber_ref=subscriber,
        strategy_product_id=PRODUCT,
        telegram_user_id=telegram_id,
        telegram_chat_id=telegram_id,
        now_ts=BASE,
        path=str(notification_path),
    )["record"]


class FakeSender:
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.calls: list[dict] = []
        self.next_message_id = 100

    def __call__(self, *, chat_id, text, reply_markup=None, thread_id=None):
        self.calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
                "thread_id": thread_id,
            }
        )
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("telegram send failed test-token-should-not-leak")
        self.next_message_id += 1
        return {"ok": True, "result": {"message_id": self.next_message_id}}


def _events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sent_deliveries(path: Path) -> list[dict]:
    return [
        row
        for row in _events(path)
        if row.get("event_type") == notification_scheduler.EVENT_DELIVERY
        and row.get("delivery_result") == "SENT"
    ]


def _first_callback(path: Path, *, label_contains: str) -> str:
    # Re-render from the persisted notification context so the test does not
    # depend on FakeSender internals for callback construction.
    sent = _sent_deliveries(path)
    assert sent
    row = sent[0]
    subscription = {
        "strategy_product_id": row["strategy_product_id"],
        "tier": row["tier"],
        "expires_at_epoch": row["period_expires_at_epoch"],
        "plan_id": row["plan_id"],
    }
    _, markup = notification_scheduler._render_notification(
        subscription, row["notification_point"], row["callback_token"]
    )
    for keyboard_row in markup["inline_keyboard"]:
        for button in keyboard_row:
            if label_contains.lower() in button["text"].lower():
                return button["callback_data"]
    raise AssertionError(f"callback button not found: {label_contains}")


def test_private_delivery_target_is_explicit_and_idempotent(paths: tuple[Path, Path, Path]) -> None:
    notification_path, _, _ = paths
    created = notification_scheduler.bind_private_delivery_target(
        subscriber_ref="sub-a",
        telegram_user_id=111,
        telegram_chat_id=111,
        now_ts=BASE,
        path=str(notification_path),
    )
    replay = notification_scheduler.bind_private_delivery_target(
        subscriber_ref="sub-a",
        telegram_user_id=111,
        telegram_chat_id=111,
        now_ts=BASE + 50,
        path=str(notification_path),
    )
    assert created["appended"] is True
    assert replay["status"] == "DUPLICATE"
    assert len(_events(notification_path)) == 1

    with pytest.raises(notification_scheduler.BillingNotificationError):
        notification_scheduler.bind_private_delivery_target(
            subscriber_ref="sub-a",
            telegram_user_id=111,
            telegram_chat_id=222,
            path=str(notification_path),
        )


def test_scheduler_sends_each_due_point_once(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-schedule"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1001)
    sender = FakeSender()

    t_minus_3d = MONTH_END - 3 * 24 * 60 * 60
    first = notification_scheduler.run_notification_cycle(
        now_ts=t_minus_3d,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    assert len(first["delivery_events"]) == 1
    assert len(sender.calls) == 1
    assert _sent_deliveries(notification_path)[0]["notification_point"] == "T_MINUS_3D"

    replay = notification_scheduler.run_notification_cycle(
        now_ts=t_minus_3d + 10,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    assert replay["delivery_events"] == []
    assert len(sender.calls) == 1

    t_minus_1d = MONTH_END - 24 * 60 * 60
    notification_scheduler.run_notification_cycle(
        now_ts=t_minus_1d,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    assert len(sender.calls) == 2
    assert [row["notification_point"] for row in _sent_deliveries(notification_path)] == [
        "T_MINUS_3D",
        "T_MINUS_1D",
    ]


def test_failed_delivery_retries_and_is_not_silence(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-retry"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1002)
    sender = FakeSender(failures=1)
    due = MONTH_END - 3 * 24 * 60 * 60

    first = notification_scheduler.run_notification_cycle(
        now_ts=due,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    assert first["delivery_events"][0]["delivery_result"] == "FAILED"
    retry_at = first["delivery_events"][0]["next_retry_at_epoch"]
    assert retry_at == due + notification_scheduler.RETRY_DELAYS_SECONDS[0]

    early = notification_scheduler.run_notification_cycle(
        now_ts=retry_at - 1,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    assert early["delivery_events"] == []
    assert len(sender.calls) == 1

    retried = notification_scheduler.run_notification_cycle(
        now_ts=retry_at,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    assert retried["delivery_events"][0]["delivery_result"] == "SENT"
    assert len(sender.calls) == 2


def test_all_required_deliveries_create_plus72_evidence_and_free_downgrade(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-auto-free"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1003)
    sender = FakeSender()
    now = MONTH_END + subscription_registry.AUTO_DOWNGRADE_SECONDS + 1

    result = notification_scheduler.run_notification_cycle(
        now_ts=now,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    assert len(sender.calls) == 5
    assert len(_sent_deliveries(notification_path)) == 5
    evidence = [
        row for row in _events(notification_path)
        if row.get("event_type") == notification_scheduler.EVENT_DOWNGRADE_EVIDENCE
    ]
    assert len(evidence) == 1
    assert len(evidence[0]["delivery_event_ids"]) == 5

    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=subscriber,
        strategy_product_id=PRODUCT,
        now_ts=now,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "FREE"
    assert entitlement["access_state"] == "FREE_FALLBACK"
    assert any(
        row.get("last_downgrade_evidence_id") == evidence[0]["downgrade_evidence_id"]
        for row in subscription_registry.load_subscription_events(str(subscription_path))
    )
    assert result["status"] == "OK"


def test_missing_or_failed_delivery_blocks_auto_downgrade(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-failed-delivery"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1004)
    sender = FakeSender(failures=99)
    now = MONTH_END + subscription_registry.AUTO_DOWNGRADE_SECONDS + 1

    notification_scheduler.run_notification_cycle(
        now_ts=now,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=subscriber,
        now_ts=now,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "BASIC"
    assert entitlement["access_state"] == "SUSPENDED"
    assert not [
        row for row in _events(notification_path)
        if row.get("event_type") == notification_scheduler.EVENT_DOWNGRADE_EVIDENCE
    ]


def test_keep_current_plan_callback_is_identity_bound_and_replay_safe(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-callback"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1005)
    sender = FakeSender()
    notification_scheduler.run_notification_cycle(
        now_ts=MONTH_END - 3 * 24 * 60 * 60,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    callback = _first_callback(notification_path, label_contains="Keep current")

    denied = notification_scheduler.handle_telegram_callback(
        telegram_user_id=9999,
        telegram_chat_id=9999,
        callback_data=callback,
        now_ts=BASE + 20,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )
    assert denied["accepted"] is False
    assert denied["reason"] == "CALLBACK_IDENTITY_MISMATCH"

    first = notification_scheduler.handle_telegram_callback(
        telegram_user_id=1005,
        telegram_chat_id=1005,
        callback_data=callback,
        now_ts=BASE + 20,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )
    replay = notification_scheduler.handle_telegram_callback(
        telegram_user_id=1005,
        telegram_chat_id=1005,
        callback_data=callback,
        now_ts=BASE + 21,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )
    assert first["accepted"] is True
    assert replay["reason"] == "ALREADY_RECORDED"
    assert first["client_intent_id"] == replay["client_intent_id"]


def test_active_client_intent_blocks_plus72_auto_downgrade(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-intent-block"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1006)
    sender = FakeSender()

    notification_scheduler.run_notification_cycle(
        now_ts=MONTH_END - 3 * 24 * 60 * 60,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    callback = _first_callback(notification_path, label_contains="Keep current")
    recorded = notification_scheduler.handle_telegram_callback(
        telegram_user_id=1006,
        telegram_chat_id=1006,
        callback_data=callback,
        now_ts=MONTH_END - 3 * 24 * 60 * 60 + 1,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )
    assert recorded["accepted"] is True

    now = MONTH_END + subscription_registry.AUTO_DOWNGRADE_SECONDS + 1
    notification_scheduler.run_notification_cycle(
        now_ts=now,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=subscriber,
        now_ts=now,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "BASIC"
    assert entitlement["access_state"] == "SUSPENDED"
    evidence = notification_scheduler.build_auto_downgrade_evidence(
        subscription=subscription_registry.current_subscription(
            subscriber, PRODUCT, str(subscription_path)
        ),
        now_ts=now,
        path=str(notification_path),
        payment_path=str(payment_path),
    )
    assert evidence["ready"] is False
    assert evidence["reason"] == "RECORDED_CLIENT_INTENT_ACTIVE"


def test_upgrade_and_downgrade_callbacks_bind_target_plan(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-plan-actions"
    _activate(subscription_path, payment_path, subscriber=subscriber, plan_id=PRO, intent_id="pro-base", amount_minor=2500, suffix="p")
    _bind(notification_path, subscriber=subscriber, telegram_id=1007)
    sender = FakeSender()
    notification_scheduler.run_notification_cycle(
        now_ts=MONTH_END - 3 * 24 * 60 * 60,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )

    upgrade_cb = _first_callback(notification_path, label_contains="Upgrade to ELITE")
    upgrade = notification_scheduler.handle_telegram_callback(
        telegram_user_id=1007,
        telegram_chat_id=1007,
        callback_data=upgrade_cb,
        now_ts=BASE + 100,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )
    assert upgrade["accepted"] is True

    downgrade_cb = _first_callback(notification_path, label_contains="Downgrade to BASIC")
    downgrade = notification_scheduler.handle_telegram_callback(
        telegram_user_id=1007,
        telegram_chat_id=1007,
        callback_data=downgrade_cb,
        now_ts=BASE + 101,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )
    assert downgrade["accepted"] is True
    latest = subscription_registry.current_subscription(subscriber, PRODUCT, str(subscription_path))
    assert latest["scheduled_plan_id"] == BASIC

    intents = [
        row for row in _events(notification_path)
        if row.get("event_type") == notification_scheduler.EVENT_CLIENT_INTENT
    ]
    assert intents[-2]["requested_plan_id"] == ELITE
    assert intents[-1]["requested_plan_id"] == BASIC


def test_cancel_callback_schedules_period_end_without_immediate_access_loss(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-cancel"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1008)
    sender = FakeSender()
    notification_scheduler.run_notification_cycle(
        now_ts=MONTH_END - 3 * 24 * 60 * 60,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    cancel_cb = _first_callback(notification_path, label_contains="Cancel")
    result = notification_scheduler.handle_telegram_callback(
        telegram_user_id=1008,
        telegram_chat_id=1008,
        callback_data=cancel_cb,
        now_ts=BASE + 200,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )
    assert result["accepted"] is True
    current = subscription_registry.current_subscription(subscriber, PRODUCT, str(subscription_path))
    assert current["state"] == "CANCELED_AT_PERIOD_END"
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=subscriber,
        now_ts=MONTH_END - 1,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "BASIC"
    assert entitlement["access_state"] == "ACTIVE"


def test_payment_handoff_enters_subscription_pending_only_for_matching_intent(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-handoff"
    _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1009)
    sender = FakeSender()
    notification_scheduler.run_notification_cycle(
        now_ts=MONTH_END - 3 * 24 * 60 * 60,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    keep_cb = _first_callback(notification_path, label_contains="Keep current")
    recorded = notification_scheduler.handle_telegram_callback(
        telegram_user_id=1009,
        telegram_chat_id=1009,
        callback_data=keep_cb,
        now_ts=BASE + 300,
        path=str(notification_path),
        subscription_path=str(subscription_path),
    )

    payment_ledger.create_payment_intent(
        subscriber_ref=subscriber,
        strategy_product_id=PRODUCT,
        plan_id=BASIC,
        amount_minor=1200,
        currency="EUR",
        payment_method="FIAT",
        provider="TEST_PROVIDER",
        idempotency_key="create:renew-handoff",
        payment_intent_id="renew-handoff",
        now_ts=BASE + 300,
        path=str(payment_path),
    )
    handoff = notification_scheduler.handoff_payment_intent(
        client_intent_id=recorded["client_intent_id"],
        payment_intent_id="renew-handoff",
        now_ts=BASE + 301,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
    )
    assert handoff["status"] == "PAYMENT_PENDING"
    current = subscription_registry.current_subscription(subscriber, PRODUCT, str(subscription_path))
    assert current["state"] == "INTENT_PAYMENT_PENDING"
    assert current["pending_payment_intent_id"] == "renew-handoff"


def test_unconsumed_settled_payment_blocks_auto_downgrade(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    subscriber = "sub-new-settlement"
    current = _activate(subscription_path, payment_path, subscriber=subscriber)
    _bind(notification_path, subscriber=subscriber, telegram_id=1010)
    sender = FakeSender()
    now = MONTH_END + subscription_registry.AUTO_DOWNGRADE_SECONDS + 1

    # Create a second verified payment that subscription truth has not consumed yet.
    _create_settled_payment(
        payment_path,
        subscriber=subscriber,
        plan_id=BASIC,
        intent_id="unconsumed-renewal",
        amount_minor=1200,
        suffix="z",
        settled_at=MONTH_END + 100,
    )
    notification_scheduler.run_notification_cycle(
        now_ts=now,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    latest = subscription_registry.current_subscription(subscriber, PRODUCT, str(subscription_path))
    evidence = notification_scheduler.build_auto_downgrade_evidence(
        subscription=latest,
        now_ts=now,
        path=str(notification_path),
        payment_path=str(payment_path),
    )
    assert current["last_payment_ledger_event_id"] != payment_ledger.settled_payment_record(
        "unconsumed-renewal", str(payment_path)
    )["ledger_event_id"]
    assert evidence["ready"] is False
    assert evidence["reason"] == "UNCONSUMED_SETTLED_PAYMENT_EXISTS"


def test_two_subscribers_keep_notification_event_sequence_contiguous(paths: tuple[Path, Path, Path]) -> None:
    notification_path, subscription_path, payment_path = paths
    _activate(subscription_path, payment_path, subscriber="sub-one", intent_id="one", suffix="1")
    _activate(subscription_path, payment_path, subscriber="sub-two", intent_id="two", suffix="2")
    _bind(notification_path, subscriber="sub-one", telegram_id=1011)
    _bind(notification_path, subscriber="sub-two", telegram_id=1012)
    sender = FakeSender()

    notification_scheduler.run_notification_cycle(
        now_ts=MONTH_END - 3 * 24 * 60 * 60,
        path=str(notification_path),
        subscription_path=str(subscription_path),
        payment_path=str(payment_path),
        send_fn=sender,
    )
    records = notification_scheduler.load_events(str(notification_path))
    seqs = [row["billing_notification_seq"] for row in records]
    assert seqs == list(range(1, len(records) + 1))
    assert len(_sent_deliveries(notification_path)) == 2
