from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import payment_ledger, subscription_registry


SUBSCRIBER = "subscriber-subscription-tests"
PRODUCT = "BINARY_TRADING"
FREE = "BINARY_TRADING_FREE"
BASIC = "BINARY_TRADING_BASIC"
PRO = "BINARY_TRADING_PRO"
ELITE = "BINARY_TRADING_ELITE"
BASE = 1_700_000_000
MONTH_SECONDS = 30 * 24 * 60 * 60
MONTH_END = BASE + MONTH_SECONDS


@pytest.fixture
def paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    return (
        tmp_path / "billing" / "subscription_events.jsonl",
        tmp_path / "billing" / "payment_ledger.jsonl",
    )


def _create_intent(
    payment_path: Path,
    *,
    plan_id: str,
    intent_id: str,
    amount_minor: int,
    method: str = "FIAT",
) -> dict:
    return payment_ledger.create_payment_intent(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        plan_id=plan_id,
        amount_minor=amount_minor,
        currency="EUR",
        payment_method=method,
        provider="TEST_PROVIDER",
        idempotency_key=f"create:{intent_id}",
        payment_intent_id=intent_id,
        audit_correlation_id=f"audit:{intent_id}",
        now_ts=BASE,
        path=str(payment_path),
    )["record"]


def _settle(
    payment_path: Path,
    *,
    intent_id: str,
    amount_minor: int,
    suffix: str,
    ts: int = BASE + 10,
) -> dict:
    return payment_ledger.ingest_provider_event(
        payment_intent_id=intent_id,
        provider="TEST_PROVIDER",
        payment_state="SETTLED",
        provider_state="settled",
        amount_minor=amount_minor,
        currency="EUR",
        raw_event_hash=(suffix * 32)[:32],
        idempotency_key=f"settle:{intent_id}:{suffix}",
        provider_event_id=f"event:{intent_id}:{suffix}",
        provider_tx_ref=f"tx:{intent_id}",
        settled_at_ts=ts,
        received_at_ts=ts,
        audit_correlation_id=f"audit-settle:{intent_id}",
        path=str(payment_path),
    )["record"]


def _settled_intent(
    payment_path: Path,
    *,
    plan_id: str,
    intent_id: str,
    amount_minor: int,
    suffix: str,
    ts: int = BASE + 10,
) -> dict:
    _create_intent(
        payment_path,
        plan_id=plan_id,
        intent_id=intent_id,
        amount_minor=amount_minor,
    )
    return _settle(
        payment_path,
        intent_id=intent_id,
        amount_minor=amount_minor,
        suffix=suffix,
        ts=ts,
    )


def _activate(
    subscription_path: Path,
    payment_path: Path,
    *,
    intent_id: str,
    start: int = BASE,
    end: int = MONTH_END,
    effective: int = BASE + 10,
    proration: dict | None = None,
) -> dict:
    return subscription_registry.activate_from_settled_payment(
        payment_intent_id=intent_id,
        period_start_ts=start,
        period_end_ts=end,
        effective_at_ts=effective,
        proration_evidence=proration,
        path=str(subscription_path),
        payment_path=str(payment_path),
    )


def _events(subscription_path: Path) -> list[dict]:
    if not subscription_path.exists():
        return []
    return [
        json.loads(line)
        for line in subscription_path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def test_no_subscription_resolves_stable_free_fallback(paths: tuple[Path, Path]) -> None:
    subscription_path, _ = paths
    first = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=BASE,
        path=str(subscription_path),
    )
    second = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=BASE + 100,
        path=str(subscription_path),
    )
    assert first["tier"] == "FREE"
    assert first["plan_id"] == FREE
    assert first["access_state"] == "FREE_FALLBACK"
    assert first["entitlement_version"] == 0
    assert first["entitlement_id"] == second["entitlement_id"]
    assert not subscription_path.exists()


def test_free_bootstrap_is_idempotent_and_versioned(paths: tuple[Path, Path]) -> None:
    subscription_path, _ = paths
    created = subscription_registry.ensure_free_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        path=str(subscription_path),
    )
    replay = subscription_registry.ensure_free_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE + 50,
        path=str(subscription_path),
    )
    assert created["status"] == "CREATED"
    assert replay["status"] == "EXISTS"
    assert len(_events(subscription_path)) == 1
    assert created["record"]["entitlement_version"] == 1
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "FREE"
    assert entitlement["access_state"] == "ACTIVE"


def test_paid_activation_requires_unique_settled_matched_payment(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _create_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="pending-only",
        amount_minor=1200,
    )
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        _activate(subscription_path, payment_path, intent_id="pending-only")
    assert not subscription_path.exists()

    _settle(
        payment_path,
        intent_id="pending-only",
        amount_minor=1200,
        suffix="a",
    )
    activated = _activate(subscription_path, payment_path, intent_id="pending-only")
    assert activated["status"] == subscription_registry.EVENT_ACTIVATED
    assert activated["record"]["tier"] == "BASIC"
    assert activated["record"]["state"] == "ACTIVE"
    assert activated["record"]["entitlement_version"] == 1


def test_activation_replay_cannot_increment_entitlement_version(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="activation-replay",
        amount_minor=1200,
        suffix="b",
    )
    first = _activate(subscription_path, payment_path, intent_id="activation-replay")
    replay = _activate(subscription_path, payment_path, intent_id="activation-replay")
    assert first["appended"] is True
    assert replay["status"] == "DUPLICATE"
    assert replay["appended"] is False
    assert len(_events(subscription_path)) == 1
    assert replay["record"]["entitlement_version"] == 1


def test_resolver_suspends_paid_access_at_expiry_even_before_scheduler_runs(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="expiry-safe",
        amount_minor=1200,
        suffix="c",
    )
    _activate(subscription_path, payment_path, intent_id="expiry-safe")
    before = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=MONTH_END - 1,
        path=str(subscription_path),
    )
    after = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=MONTH_END + 1,
        path=str(subscription_path),
    )
    assert before["tier"] == "BASIC"
    assert before["access_state"] == "ACTIVE"
    assert after["tier"] == "BASIC"
    assert after["access_state"] == "SUSPENDED"


def test_plus72_downgrade_requires_notification_policy_evidence(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="deadline-gated",
        amount_minor=1200,
        suffix="d",
    )
    _activate(subscription_path, payment_path, intent_id="deadline-gated")
    now = MONTH_END + subscription_registry.AUTO_DOWNGRADE_SECONDS + 1

    blocked = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=now,
        path=str(subscription_path),
    )
    assert blocked["status"] == "PAYMENT_DUE"
    assert blocked["downgrade_blocked_pending_evidence"] is True
    assert [event["event_type"] for event in blocked["events"]] == [
        subscription_registry.EVENT_GRACE_STARTED,
        subscription_registry.EVENT_PAYMENT_DUE,
    ]
    suspended = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=now,
        path=str(subscription_path),
    )
    assert suspended["tier"] == "BASIC"
    assert suspended["access_state"] == "SUSPENDED"
    assert suspended["reason"] == "AUTO_DOWNGRADE_BLOCKED_PENDING_NOTIFICATION_EVIDENCE"

    evidence_id = "notification-policy-evidence-001"
    released = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=now,
        downgrade_evidence_id=evidence_id,
        path=str(subscription_path),
    )
    assert released["status"] == "EXPIRED"
    assert released["events"][-1]["event_type"] == subscription_registry.EVENT_AUTO_DOWNGRADED
    assert released["record"]["last_downgrade_evidence_id"] == evidence_id
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=now,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "FREE"
    assert entitlement["plan_id"] == FREE
    assert entitlement["access_state"] == "FREE_FALLBACK"

    replay = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=now + 100,
        downgrade_evidence_id=evidence_id,
        path=str(subscription_path),
    )
    assert replay["appended"] is False


def test_recorded_intent_can_cross_plus72_for_at_most24h(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="old-period",
        amount_minor=1200,
        suffix="e",
    )
    _activate(subscription_path, payment_path, intent_id="old-period")

    # Record the intent at +60h, not +1h. Its 24h window therefore reaches +84h.
    intent_time = MONTH_END + 60 * 60 * 60
    subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=intent_time,
        path=str(subscription_path),
    )
    _create_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="renewal-intent-pending",
        amount_minor=1200,
    )
    pending = subscription_registry.record_payment_intent_pending(
        payment_intent_id="renewal-intent-pending",
        now_ts=intent_time,
        path=str(subscription_path),
        payment_path=str(payment_path),
    )
    assert pending["record"]["intent_pending_until_epoch"] == (
        intent_time + subscription_registry.INTENT_PAYMENT_PENDING_SECONDS
    )

    beyond_plus72_but_pending = MONTH_END + 73 * 60 * 60
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=beyond_plus72_but_pending,
        path=str(subscription_path),
    )
    assert entitlement["subscription_state"] == "INTENT_PAYMENT_PENDING"
    assert entitlement["tier"] == "BASIC"
    assert entitlement["access_state"] == "SUSPENDED"

    after_pending = intent_time + subscription_registry.INTENT_PAYMENT_PENDING_SECONDS + 1
    evaluated = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=after_pending,
        path=str(subscription_path),
    )
    assert evaluated["record"]["state"] == "PAYMENT_DUE"
    assert evaluated["downgrade_blocked_pending_evidence"] is True

    finalized = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=after_pending,
        downgrade_evidence_id="notification-policy-evidence-late-intent",
        path=str(subscription_path),
    )
    assert finalized["record"]["state"] == "EXPIRED"
    final = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=after_pending,
        path=str(subscription_path),
    )
    assert final["tier"] == "FREE"
    assert final["access_state"] == "FREE_FALLBACK"


def test_new_free_subscriber_payment_intent_pending_expires_back_to_free(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _create_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="new-user-pending",
        amount_minor=1200,
    )
    pending = subscription_registry.record_payment_intent_pending(
        payment_intent_id="new-user-pending",
        now_ts=BASE,
        path=str(subscription_path),
        payment_path=str(payment_path),
    )
    assert pending["record"]["tier"] == "FREE"
    assert pending["record"]["state"] == "INTENT_PAYMENT_PENDING"
    result = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=BASE + subscription_registry.INTENT_PAYMENT_PENDING_SECONDS + 1,
        path=str(subscription_path),
    )
    assert result["record"]["state"] == "ACTIVE"
    assert result["record"]["tier"] == "FREE"
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE + subscription_registry.INTENT_PAYMENT_PENDING_SECONDS + 1,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "FREE"
    assert entitlement["access_state"] == "ACTIVE"


def test_cancellation_at_period_end_preserves_access_then_expires_without_grace(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=PRO,
        intent_id="cancel-period",
        amount_minor=2500,
        suffix="f",
    )
    _activate(subscription_path, payment_path, intent_id="cancel-period")
    cancel = subscription_registry.cancel_at_period_end(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=BASE + 100,
        path=str(subscription_path),
    )
    assert cancel["record"]["state"] == "CANCELED_AT_PERIOD_END"
    before = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=MONTH_END - 1,
        path=str(subscription_path),
    )
    assert before["tier"] == "PRO"
    assert before["access_state"] == "ACTIVE"

    result = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=MONTH_END + 1,
        path=str(subscription_path),
    )
    assert [event["event_type"] for event in result["events"]] == [
        subscription_registry.EVENT_AUTO_DOWNGRADED
    ]
    after = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=MONTH_END + 1,
        path=str(subscription_path),
    )
    assert after["tier"] == "FREE"


def test_canceled_subscription_pending_intent_expiry_restores_cancel_and_expires(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="cancel-with-pending-current",
        amount_minor=1200,
        suffix="g",
    )
    _activate(subscription_path, payment_path, intent_id="cancel-with-pending-current")
    subscription_registry.cancel_at_period_end(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=BASE + 100,
        path=str(subscription_path),
    )
    _create_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="cancel-with-pending-next",
        amount_minor=1200,
    )
    intent_time = MONTH_END - 60 * 60
    subscription_registry.record_payment_intent_pending(
        payment_intent_id="cancel-with-pending-next",
        now_ts=intent_time,
        path=str(subscription_path),
        payment_path=str(payment_path),
    )
    result = subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=intent_time + subscription_registry.INTENT_PAYMENT_PENDING_SECONDS + 1,
        path=str(subscription_path),
    )
    assert result["record"]["state"] == "EXPIRED"
    assert result["events"][0]["event_type"] == subscription_registry.EVENT_INTENT_EXPIRED
    assert result["events"][1]["event_type"] == subscription_registry.EVENT_AUTO_DOWNGRADED


def test_scheduled_paid_downgrade_becomes_effective_only_with_verified_next_period_payment(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=PRO,
        intent_id="pro-current",
        amount_minor=2500,
        suffix="h",
    )
    _activate(subscription_path, payment_path, intent_id="pro-current")
    scheduled = subscription_registry.request_downgrade(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        target_plan_id=BASIC,
        now_ts=BASE + 100,
        path=str(subscription_path),
    )
    assert scheduled["record"]["scheduled_plan_id"] == BASIC
    assert subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE + 200,
        path=str(subscription_path),
    )["tier"] == "PRO"

    next_start = MONTH_END
    next_end = MONTH_END + MONTH_SECONDS
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="basic-next-period",
        amount_minor=1200,
        suffix="i",
        ts=next_start,
    )
    effective = _activate(
        subscription_path,
        payment_path,
        intent_id="basic-next-period",
        start=next_start,
        end=next_end,
        effective=next_start,
    )
    assert effective["status"] == subscription_registry.EVENT_DOWNGRADE_EFFECTIVE
    assert effective["record"]["tier"] == "BASIC"
    assert effective["record"]["scheduled_plan_id"] is None


def test_post_expiry_lower_paid_plan_activation_does_not_require_prior_schedule(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=PRO,
        intent_id="pro-expiring",
        amount_minor=2500,
        suffix="j",
    )
    _activate(subscription_path, payment_path, intent_id="pro-expiring")
    lapse_time = MONTH_END + 49 * 60 * 60
    subscription_registry.evaluate_deadlines(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        now_ts=lapse_time,
        path=str(subscription_path),
    )
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="basic-after-lapse",
        amount_minor=1200,
        suffix="k",
        ts=lapse_time,
    )
    activated = _activate(
        subscription_path,
        payment_path,
        intent_id="basic-after-lapse",
        start=lapse_time,
        end=lapse_time + MONTH_SECONDS,
        effective=lapse_time,
    )
    assert activated["status"] == subscription_registry.EVENT_ACTIVATED
    assert activated["record"]["tier"] == "BASIC"


def test_invalid_or_non_owned_downgrade_plan_is_rejected(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=PRO,
        intent_id="invalid-downgrade-current",
        amount_minor=2500,
        suffix="l",
    )
    _activate(subscription_path, payment_path, intent_id="invalid-downgrade-current")
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        subscription_registry.request_downgrade(
            subscriber_ref=SUBSCRIBER,
            strategy_product_id=PRODUCT,
            target_plan_id="FOREX_FUTURE_BASIC",
            now_ts=BASE + 100,
            path=str(subscription_path),
        )


def test_midperiod_direct_downgrade_is_rejected(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=PRO,
        intent_id="pro-midperiod",
        amount_minor=2500,
        suffix="m",
    )
    _activate(subscription_path, payment_path, intent_id="pro-midperiod")
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="basic-too-early",
        amount_minor=1200,
        suffix="n",
        ts=BASE + 200,
    )
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        _activate(
            subscription_path,
            payment_path,
            intent_id="basic-too-early",
            start=BASE,
            end=MONTH_END,
            effective=BASE + 200,
        )


def test_midperiod_upgrade_requires_and_validates_governed_proration(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="basic-before-upgrade",
        amount_minor=1000,
        suffix="o",
    )
    _activate(subscription_path, payment_path, intent_id="basic-before-upgrade")
    effective_at = BASE + (MONTH_END - BASE) // 2
    calculation = subscription_registry.calculate_proration(
        source_period_price_minor=1000,
        target_period_price_minor=2000,
        period_start_ts=BASE,
        period_end_ts=MONTH_END,
        effective_at_ts=effective_at,
        currency="EUR",
    )
    assert calculation["source_credit_minor"] == 500
    assert calculation["target_prorated_charge_minor"] == 1000
    assert calculation["net_due_minor"] == 500

    _settled_intent(
        payment_path,
        plan_id=PRO,
        intent_id="pro-upgrade",
        amount_minor=500,
        suffix="p",
        ts=effective_at,
    )
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        _activate(
            subscription_path,
            payment_path,
            intent_id="pro-upgrade",
            start=BASE,
            end=MONTH_END,
            effective=effective_at,
        )
    upgraded = _activate(
        subscription_path,
        payment_path,
        intent_id="pro-upgrade",
        start=BASE,
        end=MONTH_END,
        effective=effective_at,
        proration={
            "source_period_price_minor": 1000,
            "target_period_price_minor": 2000,
            "currency": "EUR",
        },
    )
    assert upgraded["status"] == subscription_registry.EVENT_UPGRADED
    assert upgraded["record"]["tier"] == "PRO"
    assert upgraded["record"]["proration_evidence"]["net_due_minor"] == 500


def test_upgrade_rejects_settlement_that_does_not_equal_prorated_net_due(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="basic-proration-mismatch",
        amount_minor=1000,
        suffix="q",
    )
    _activate(subscription_path, payment_path, intent_id="basic-proration-mismatch")
    effective_at = BASE + (MONTH_END - BASE) // 2
    _settled_intent(
        payment_path,
        plan_id=PRO,
        intent_id="pro-wrong-proration",
        amount_minor=501,
        suffix="r",
        ts=effective_at,
    )
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        _activate(
            subscription_path,
            payment_path,
            intent_id="pro-wrong-proration",
            start=BASE,
            end=MONTH_END,
            effective=effective_at,
            proration={
                "source_period_price_minor": 1000,
                "target_period_price_minor": 2000,
                "currency": "EUR",
            },
        )


def test_same_plan_renewal_requires_non_overlapping_next_period(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="basic-renew-current",
        amount_minor=1200,
        suffix="s",
    )
    _activate(subscription_path, payment_path, intent_id="basic-renew-current")
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="basic-renew-next",
        amount_minor=1200,
        suffix="t",
        ts=MONTH_END,
    )
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        _activate(
            subscription_path,
            payment_path,
            intent_id="basic-renew-next",
            start=BASE + 100,
            end=MONTH_END + 100,
            effective=BASE + 100,
        )
    renewed = _activate(
        subscription_path,
        payment_path,
        intent_id="basic-renew-next",
        start=MONTH_END,
        end=MONTH_END + MONTH_SECONDS,
        effective=MONTH_END,
    )
    assert renewed["status"] == subscription_registry.EVENT_RENEWED
    assert renewed["record"]["entitlement_version"] == 2


@pytest.mark.parametrize(
    ("reversal_state", "expected_state"),
    [("REFUNDED", "REFUND_HOLD"), ("CHARGEBACK", "CHARGEBACK_OPEN")],
)
def test_current_payment_reversal_places_entitlement_on_hold(
    paths: tuple[Path, Path], reversal_state: str, expected_state: str
) -> None:
    subscription_path, payment_path = paths
    intent_id = f"reversal-{reversal_state.lower()}"
    suffix = "u" if reversal_state == "REFUNDED" else "v"
    _settled_intent(
        payment_path,
        plan_id=ELITE,
        intent_id=intent_id,
        amount_minor=4000,
        suffix=suffix,
    )
    _activate(subscription_path, payment_path, intent_id=intent_id)
    payment_ledger.ingest_provider_event(
        payment_intent_id=intent_id,
        provider="TEST_PROVIDER",
        payment_state=reversal_state,
        provider_state=reversal_state.lower(),
        amount_minor=4000,
        currency="EUR",
        raw_event_hash=("w" if reversal_state == "REFUNDED" else "x") * 32,
        idempotency_key=f"reverse:{intent_id}",
        provider_event_id=f"reverse-event:{intent_id}",
        provider_tx_ref=f"tx:{intent_id}",
        received_at_ts=BASE + 100,
        path=str(payment_path),
    )
    held = subscription_registry.apply_payment_reversal(
        payment_intent_id=intent_id,
        now_ts=BASE + 101,
        path=str(subscription_path),
        payment_path=str(payment_path),
    )
    assert held["record"]["state"] == expected_state
    entitlement = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE + 102,
        path=str(subscription_path),
    )
    assert entitlement["tier"] == "ELITE"
    assert entitlement["access_state"] == "HOLD"


def test_old_payment_reversal_cannot_hold_newer_subscription_period(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="old-payment",
        amount_minor=1200,
        suffix="y",
    )
    _activate(subscription_path, payment_path, intent_id="old-payment")
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="new-payment",
        amount_minor=1200,
        suffix="z",
        ts=MONTH_END,
    )
    _activate(
        subscription_path,
        payment_path,
        intent_id="new-payment",
        start=MONTH_END,
        end=MONTH_END + MONTH_SECONDS,
        effective=MONTH_END,
    )
    payment_ledger.ingest_provider_event(
        payment_intent_id="old-payment",
        provider="TEST_PROVIDER",
        payment_state="CHARGEBACK",
        provider_state="chargeback",
        amount_minor=1200,
        currency="EUR",
        raw_event_hash="0123456789abcdef0123456789abcdef",
        idempotency_key="old-chargeback",
        provider_event_id="old-chargeback-event",
        provider_tx_ref="tx:old-payment",
        received_at_ts=MONTH_END + 100,
        path=str(payment_path),
    )
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        subscription_registry.apply_payment_reversal(
            payment_intent_id="old-payment",
            now_ts=MONTH_END + 101,
            path=str(subscription_path),
            payment_path=str(payment_path),
        )


def test_payment_failed_before_expiry_does_not_prematurely_remove_paid_access(paths: tuple[Path, Path]) -> None:
    subscription_path, payment_path = paths
    _settled_intent(
        payment_path,
        plan_id=BASIC,
        intent_id="payment-failure-period",
        amount_minor=1200,
        suffix="1",
    )
    _activate(subscription_path, payment_path, intent_id="payment-failure-period")
    failed = subscription_registry.record_payment_status(
        subscriber_ref=SUBSCRIBER,
        strategy_product_id=PRODUCT,
        state="PAYMENT_FAILED",
        reason="RENEWAL_ATTEMPT_FAILED",
        now_ts=MONTH_END - 100,
        path=str(subscription_path),
    )
    assert failed["record"]["state"] == "PAYMENT_FAILED"
    before = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=MONTH_END - 1,
        path=str(subscription_path),
    )
    after = subscription_registry.resolve_entitlement(
        subscriber_ref=SUBSCRIBER,
        now_ts=MONTH_END + 1,
        path=str(subscription_path),
    )
    assert before["access_state"] == "ACTIVE"
    assert after["access_state"] == "SUSPENDED"


def test_subscription_event_log_corruption_fails_closed(paths: tuple[Path, Path]) -> None:
    subscription_path, _ = paths
    subscription_path.parent.mkdir(parents=True, exist_ok=True)
    subscription_path.write_text("{bad-json}\n", encoding="utf-8")
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        subscription_registry.load_subscription_events(str(subscription_path))
    with pytest.raises(subscription_registry.SubscriptionRegistryError):
        subscription_registry.resolve_entitlement(
            subscriber_ref=SUBSCRIBER,
            path=str(subscription_path),
        )
