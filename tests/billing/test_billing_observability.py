from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import (
    billing_observability,
    kucoin_watcher,
    membership_reconciler,
    notification_scheduler,
    payment_ledger,
    revolut_merchant,
)


@pytest.fixture
def base_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    return tmp_path


def _records() -> dict[str, list[dict]]:
    return {name: [] for name in billing_observability.SOURCE_NAMES}


def _statuses(records: dict[str, list[dict]], default: str = "PASS") -> dict[str, dict]:
    return {
        name: {
            "status": default,
            "event_count": len(records.get(name, [])) if default == "PASS" else None,
        }
        for name in billing_observability.SOURCE_NAMES
    }


def test_missing_source_is_unknown_but_existing_empty_source_is_measured_zero(
    base_dir: Path,
) -> None:
    payment_path = base_dir / "billing" / "payment_ledger.jsonl"
    payment_path.parent.mkdir(parents=True, exist_ok=True)
    payment_path.write_text("", encoding="utf-8")

    result = billing_observability.collect_source_records(
        {"payment_ledger": str(payment_path)}
    )

    assert result["source_status"]["payment_ledger"] == {
        "status": "PASS",
        "event_count": 0,
        "reason": "SOURCE_READ_VALIDATED",
    }
    assert result["source_status"]["support_cases"]["status"] == "UNKNOWN"
    assert result["source_status"]["support_cases"]["event_count"] is None


def test_corrupt_source_is_fail_not_unknown_or_zero(base_dir: Path) -> None:
    payment_path = base_dir / "billing" / "payment_ledger.jsonl"
    payment_path.parent.mkdir(parents=True, exist_ok=True)
    payment_path.write_text("{not-json}\n", encoding="utf-8")

    result = billing_observability.collect_source_records(
        {"payment_ledger": str(payment_path)}
    )
    status = result["source_status"]["payment_ledger"]
    assert status["status"] == "FAIL"
    assert status["event_count"] is None
    assert status["reason"] == "SOURCE_READ_OR_VALIDATION_FAILED"
    assert status["error_type"] == "PaymentLedgerError"


def test_normalized_event_is_allowlisted_and_does_not_leak_secrets() -> None:
    raw = {
        "ledger_event_id": "ledger-1",
        "ledger_seq": 1,
        "event_type": payment_ledger.EVENT_PROVIDER,
        "payment_intent_id": "intent-1",
        "subscriber_ref": "subscriber-1",
        "audit_correlation_id": "audit-1",
        "provider": "REVOLUT_MERCHANT",
        "payment_state": "SETTLED",
        "provider_state": "completed",
        "api_secret": "sk_should_never_appear",
        "telegram_bot_token": "123456:SECRET",
        "message_text": "private support message",
        "raw_event_hash": "deadbeef" * 8,
        "received_at": "2026-09-17T09:00:00Z",
    }

    normalized = billing_observability.normalize_event("payment_ledger", raw)
    encoded = json.dumps(normalized, sort_keys=True)

    assert normalized["correlation"]["payment_intent_id"] == ["intent-1"]
    assert normalized["correlation"]["subscriber_ref"] == ["subscriber-1"]
    assert normalized["details"]["payment_state"] == "SETTLED"
    assert "sk_should_never_appear" not in encoded
    assert "123456:SECRET" not in encoded
    assert "private support message" not in encoded
    assert "deadbeef" not in encoded


def test_transition_reconstruction_closes_across_truth_layers() -> None:
    records = _records()
    records["payment_ledger"] = [
        {
            "ledger_event_id": "ledger-1",
            "ledger_seq": 1,
            "event_type": payment_ledger.EVENT_INTENT_CREATED,
            "payment_intent_id": "intent-1",
            "subscriber_ref": "subscriber-1",
            "audit_correlation_id": "audit-payment",
            "payment_state": "CREATED",
            "received_at": "2026-09-17T09:00:00Z",
        }
    ]
    records["support_cases"] = [
        {
            "case_event_id": "case-event-1",
            "case_seq": 1,
            "event_type": "BILLING_SUPPORT_CASE_OPENED",
            "case_id": "case-1",
            "payment_intent_id": "intent-1",
            "subscriber_ref": "subscriber-1",
            "case_state": "OPEN",
            "occurred_at_epoch": 1_789_632_001,
        }
    ]
    records["subscription_registry"] = [
        {
            "subscription_event_id": "sub-event-1",
            "subscription_seq": 1,
            "event_type": "SUBSCRIPTION_ACTIVATED",
            "subscription_id": "subscription-1",
            "entitlement_id": "entitlement-1",
            "subscriber_ref": "subscriber-1",
            "last_payment_intent_id": "intent-1",
            "audit_correlation_id": "audit-subscription",
            "state": "ACTIVE",
            "tier": "BASIC",
            "occurred_at_epoch": 1_789_632_002,
        }
    ]
    records["membership_reconciler"] = [
        {
            "membership_event_id": "membership-event-1",
            "membership_seq": 1,
            "event_type": membership_reconciler.EVENT_FINAL,
            "reconciliation_id": "reconciliation-1",
            "subscription_id": "subscription-1",
            "entitlement_id": "entitlement-1",
            "subscriber_ref": "subscriber-1",
            "reconciliation_state": "IN_SYNC",
            "occurred_at_epoch": 1_789_632_003,
        }
    ]

    timeline = billing_observability.normalize_timeline(records)
    transition = billing_observability.reconstruct_transition(
        timeline, case_id="case-1"
    )

    assert {row["source"] for row in transition} == {
        "payment_ledger",
        "support_cases",
        "subscription_registry",
        "membership_reconciler",
    }
    membership = next(
        row for row in transition if row["source"] == "membership_reconciler"
    )
    assert membership["correlation"]["reconciliation_id"] == ["reconciliation-1"]


def test_snapshot_separates_provider_outage_backlog_and_access_leak() -> None:
    records = _records()
    records["payment_ledger"] = [
        {
            "ledger_event_id": "ledger-1",
            "ledger_seq": 1,
            "event_type": payment_ledger.EVENT_RECONCILIATION,
            "payment_intent_id": "intent-1",
            "payment_state": "UNKNOWN",
            "reconciliation_result": "CONTRADICTORY",
            "audit_correlation_id": "audit-1",
        },
        {
            "ledger_event_id": "ledger-2",
            "ledger_seq": 2,
            "event_type": payment_ledger.EVENT_PROVIDER,
            "payment_intent_id": "intent-2",
            "payment_state": "PENDING",
            "reconciliation_result": "MATCHED",
        },
    ]
    records["support_cases"] = [
        {
            "case_event_id": "case-event-1",
            "case_seq": 1,
            "event_type": "BILLING_SUPPORT_CASE_OPENED",
            "case_id": "case-1",
            "case_state": "OPEN",
        }
    ]
    records["notification_scheduler"] = [
        {
            "billing_notification_event_id": "notification-1",
            "billing_notification_seq": 1,
            "event_type": notification_scheduler.EVENT_DELIVERY,
            "delivery_result": "FAILED_TERMINAL",
        }
    ]
    records["subscription_registry"] = [
        {
            "subscription_event_id": "sub-event-1",
            "subscription_seq": 1,
            "event_type": "SUBSCRIPTION_CHARGEBACK_HOLD",
            "subscription_id": "subscription-1",
            "state": "CHARGEBACK_OPEN",
        }
    ]
    records["membership_reconciler"] = [
        {
            "membership_event_id": "member-event-1",
            "membership_seq": 1,
            "event_type": membership_reconciler.EVENT_FINAL,
            "reconciliation_id": "reconciliation-1",
            "subscriber_ref": "subscriber-1",
            "subscription_id": "subscription-1",
            "entitlement_id": "entitlement-1",
            "reconciliation_state": "ACCESS_LEAK_RISK",
        }
    ]
    records["revolut_merchant"] = [
        {
            "revolut_event_id": f"revolut-{index}",
            "revolut_seq": index,
            "event_type": revolut_merchant.EVENT_PROVIDER_UNAVAILABLE,
        }
        for index in range(1, 4)
    ] + [
        {
            "revolut_event_id": "revolut-4",
            "revolut_seq": 4,
            "event_type": revolut_merchant.EVENT_WEBHOOK_UNMATCHED,
        }
    ]
    records["kucoin_watcher"] = [
        {
            "kucoin_event_id": "kucoin-1",
            "kucoin_seq": 1,
            "event_type": kucoin_watcher.EVENT_DEPOSIT_RECONCILED,
        },
        {
            "kucoin_event_id": "kucoin-2",
            "kucoin_seq": 2,
            "event_type": kucoin_watcher.EVENT_MANUAL_REVIEW,
        },
    ]
    statuses = _statuses(records)

    snapshot = billing_observability.build_snapshot(
        records,
        statuses,
        now_ts=1_789_632_100,
        provider_failure_threshold=3,
    )

    assert snapshot["provider_health"]["REVOLUT_MERCHANT"]["status"] == "UNAVAILABLE"
    assert snapshot["provider_health"]["KUCOIN"]["status"] == "OBSERVED"
    backlog = snapshot["reconciliation_backlog"]
    assert backlog["payment_contradictory"] == 1
    assert backlog["payment_pending_or_unknown"] == 2
    assert backlog["kucoin_manual_review_required"] == 1
    assert backlog["revolut_unmatched_webhook"] == 1
    assert backlog["support_open_cases"] == 1
    assert backlog["notification_failed_deliveries"] == 1
    assert backlog["subscription_hold_states"] == 1
    assert backlog["access_leak_risk"] == 1
    incident_types = {row["incident_type"] for row in snapshot["incidents"]}
    assert incident_types == {
        "CONTRADICTORY_PROVIDER_EVIDENCE",
        "ACCESS_LEAK_RISK",
        "REPEATED_PROVIDER_FAILURE",
    }
    assert snapshot["incident_assessment_status"] == "PASS"


def test_unknown_sources_do_not_turn_into_zero_backlog_or_clean_incident_claim() -> None:
    records = _records()
    statuses = _statuses(records, default="UNKNOWN")
    statuses["payment_ledger"] = {"status": "PASS", "event_count": 0}

    snapshot = billing_observability.build_snapshot(
        records, statuses, now_ts=1_789_632_100
    )
    backlog = snapshot["reconciliation_backlog"]

    assert backlog["payment_unmatched"] == 0
    assert backlog["support_open_cases"] is None
    assert backlog["access_leak_risk"] is None
    assert snapshot["provider_health"]["REVOLUT_MERCHANT"]["status"] == "UNKNOWN"
    assert snapshot["incident_assessment_status"] == "UNKNOWN"
    assert snapshot["deduplication"]["status"] == "UNKNOWN"

    summary = billing_observability.render_operator_summary(snapshot)
    assert "payment_unmatched=0" in summary
    assert "support_open_cases=UNKNOWN" in summary
    assert "assessment=UNKNOWN" in summary


def test_persisted_duplicate_idempotency_is_visible_as_integrity_failure() -> None:
    records = _records()
    records["notification_scheduler"] = [
        {
            "billing_notification_event_id": "event-1",
            "billing_notification_seq": 1,
            "event_type": notification_scheduler.EVENT_DELIVERY,
            "idempotency_key": "same-key",
        },
        {
            "billing_notification_event_id": "event-2",
            "billing_notification_seq": 2,
            "event_type": notification_scheduler.EVENT_DELIVERY,
            "idempotency_key": "same-key",
        },
    ]
    snapshot = billing_observability.build_snapshot(
        records, _statuses(records), now_ts=1_789_632_100
    )

    assert snapshot["deduplication"]["status"] == "FAIL"
    assert snapshot["deduplication"]["persisted_duplicate_idempotency_keys"] == 1
    assert (
        snapshot["deduplication"]["by_source"]["notification_scheduler"]["status"]
        == "FAIL"
    )


def test_bounded_snapshot_ring_rotates_only_derived_projection(base_dir: Path) -> None:
    records = _records()
    snapshot = billing_observability.build_snapshot(
        records, _statuses(records), now_ts=1_789_632_100
    )
    truth_path = base_dir / "billing" / "payment_ledger.jsonl"
    truth_path.parent.mkdir(parents=True, exist_ok=True)
    truth_path.write_text('{"truth":"must-not-change"}\n', encoding="utf-8")
    truth_before = truth_path.read_text(encoding="utf-8")

    ring_path = base_dir / "observability" / "billing_observability_snapshots.json"
    first = billing_observability.persist_snapshot(
        snapshot, path=str(ring_path), max_snapshots=2
    )
    second = billing_observability.persist_snapshot(
        snapshot, path=str(ring_path), max_snapshots=2
    )
    third = billing_observability.persist_snapshot(
        snapshot, path=str(ring_path), max_snapshots=2
    )

    payload = json.loads(ring_path.read_text(encoding="utf-8"))
    assert first["retained_snapshot_count"] == 1
    assert second["retained_snapshot_count"] == 2
    assert third["retained_snapshot_count"] == 2
    assert third["dropped_snapshot_count"] == 1
    assert len(payload["snapshots"]) == 2
    assert payload["truth_authority"] == billing_observability.TRUTH_AUTHORITY
    assert truth_path.read_text(encoding="utf-8") == truth_before


def test_snapshot_store_corruption_fails_closed(base_dir: Path) -> None:
    records = _records()
    snapshot = billing_observability.build_snapshot(
        records, _statuses(records), now_ts=1_789_632_100
    )
    ring_path = base_dir / "observability" / "billing_observability_snapshots.json"
    ring_path.parent.mkdir(parents=True, exist_ok=True)
    ring_path.write_text("{broken", encoding="utf-8")

    with pytest.raises(
        billing_observability.BillingObservabilityError,
        match="snapshot store is unreadable",
    ):
        billing_observability.persist_snapshot(
            snapshot, path=str(ring_path), max_snapshots=2
        )
