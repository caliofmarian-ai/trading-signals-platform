from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))

from billing import billing_observability
from core import billing_admin_views, telegram_admin_ui
from core.role_constants import ROLE_ANALYST, ROLE_OWNER, ROLE_PRIMARY_ADMIN


def _callbacks(markup: dict) -> list[str]:
    return [
        button["callback_data"]
        for row in markup.get("inline_keyboard", [])
        for button in row
    ]


def _context(*, subscription_rows=None, support_rows=None, membership_rows=None):
    records = {name: [] for name in billing_observability.SOURCE_NAMES}
    records["subscription_registry"] = list(subscription_rows or [])
    records["support_cases"] = list(support_rows or [])
    records["membership_reconciler"] = list(membership_rows or [])
    statuses = {
        name: {"status": "PASS", "event_count": len(records[name])}
        for name in billing_observability.SOURCE_NAMES
    }
    snapshot = billing_observability.build_snapshot(
        records,
        statuses,
        now_ts=1_800_000_000,
    )
    return {
        "records": records,
        "source_status": statuses,
        "snapshot": snapshot,
        "timeline": billing_observability.normalize_timeline(records),
    }


def test_distribution_keeps_canonical_root_and_adds_billing_subsurface():
    callbacks = _callbacks(telegram_admin_ui.distribution_markup())
    assert "ADMIN_NAV:BILLING_HOME" in callbacks
    assert "ADMIN_NAV:DISTRIBUTION" in callbacks
    assert telegram_admin_ui.CANONICAL_ADMIN_PARENT_MAP["BILLING_HOME"] == "DISTRIBUTION"
    assert not telegram_admin_ui.is_canonical_panel_action("BILLING_HOME")


def test_billing_callbacks_fit_telegram_budget_and_have_safe_parents():
    markups = [
        telegram_admin_ui.billing_home_markup(),
        telegram_admin_ui.billing_subpage_markup("BILLING_SUBSCRIBERS"),
        telegram_admin_ui.billing_subpage_markup("BILLING_SUPPORT"),
        telegram_admin_ui.billing_subpage_markup("BILLING_PROVIDERS"),
        telegram_admin_ui.billing_subpage_markup("BILLING_AUDIT"),
    ]
    for markup in markups:
        for callback in _callbacks(markup):
            assert callback.startswith(telegram_admin_ui.CALLBACK_PREFIX)
            assert len(callback.encode("utf-8")) <= 64

    for action in (
        "BILLING_SUBSCRIBERS",
        "BILLING_SUPPORT",
        "BILLING_PROVIDERS",
        "BILLING_AUDIT",
    ):
        assert telegram_admin_ui.CANONICAL_ADMIN_PARENT_MAP[action] == "BILLING_HOME"
        assert telegram_admin_ui.is_distribution_subpage_action(action)


def test_billing_subpages_inherit_distribution_role_boundary():
    assert telegram_admin_ui.panel_visible_for_role(ROLE_OWNER, "DISTRIBUTION")
    assert telegram_admin_ui.panel_visible_for_role(ROLE_PRIMARY_ADMIN, "DISTRIBUTION")
    assert not telegram_admin_ui.panel_visible_for_role(ROLE_ANALYST, "DISTRIBUTION")
    assert telegram_admin_ui.is_distribution_subpage_action("BILLING_HOME")


def test_subscriber_inventory_masks_identity_and_preserves_attention_truth():
    raw_subscriber = "subscriber-secret-123"
    context = _context(
        subscription_rows=[
            {
                "event_type": "SUBSCRIPTION_GRACE_HOLD_STARTED",
                "subscription_id": "sub-1",
                "subscriber_ref": raw_subscriber,
                "tier": "PRO",
                "state": "GRACE_HOLD",
                "expires_at_epoch": 1_800_010_000,
            }
        ],
        membership_rows=[
            {
                "event_type": "TELEGRAM_MEMBERSHIP_RECONCILIATION",
                "membership_event_id": "membership-1",
                "membership_seq": 1,
                "reconciliation_id": "recon-1",
                "subscriber_ref": raw_subscriber,
                "reconciliation_state": "ACCESS_LEAK_RISK",
            }
        ],
    )

    rendered = billing_admin_views.render_subscriber_inventory(
        context,
        now_ts=1_800_000_000,
    )
    assert raw_subscriber not in rendered
    assert "PRO: 1" in rendered
    assert "ACCESS LEAK RISK: 1" in rendered
    assert "ACCESS_LEAK_RISK" in rendered
    assert "No direct tier/channel override" in rendered


def test_support_queue_masks_case_id_and_does_not_claim_verification():
    raw_case = "case-secret-456"
    context = _context(
        support_rows=[
            {
                "event_type": "BILLING_SUPPORT_CASE_OPENED",
                "case_event_id": "case-event-1",
                "case_seq": 1,
                "case_id": raw_case,
                "case_state": "OPEN",
                "provider": "KUCOIN",
                "occurred_at_epoch": 1_800_000_000,
            }
        ]
    )
    rendered = billing_admin_views.render_support_queue(context)
    assert raw_case not in rendered
    assert "OPEN CASES: 1" in rendered
    assert "PAYMENT PROOF SUBMITTED != PAYMENT VERIFIED" in rendered
    assert "directly mutate channels" in rendered


def test_missing_sources_remain_unknown_not_zero():
    records = {name: [] for name in billing_observability.SOURCE_NAMES}
    statuses = {
        name: {
            "status": "UNKNOWN",
            "event_count": None,
            "reason": "SOURCE_FILE_NOT_PRESENT",
        }
        for name in billing_observability.SOURCE_NAMES
    }
    context = {
        "records": records,
        "source_status": statuses,
        "snapshot": billing_observability.build_snapshot(
            records,
            statuses,
            now_ts=1_800_000_000,
        ),
        "timeline": [],
    }

    overview = billing_admin_views.render_billing_overview(context)
    inventory = billing_admin_views.render_subscriber_inventory(context)
    providers = billing_admin_views.render_provider_status(context)

    assert "UNKNOWN" in overview
    assert "TOTAL: UNKNOWN" in inventory
    assert "FREE: UNKNOWN" in inventory
    assert "REVOLUT_MERCHANT: UNKNOWN" in providers
    assert "KUCOIN: UNKNOWN" in providers


def test_audit_surface_lists_only_normalized_safe_evidence():
    raw_subscriber = "subscriber-secret-789"
    context = _context(
        subscription_rows=[
            {
                "event_type": "SUBSCRIPTION_ACTIVATED",
                "subscription_event_id": "subscription-event-1",
                "subscription_seq": 1,
                "subscription_id": "sub-1",
                "subscriber_ref": raw_subscriber,
                "tier": "BASIC",
                "state": "ACTIVE",
                "occurred_at_epoch": 1_800_000_000,
            }
        ]
    )
    rendered = billing_admin_views.render_billing_audit(context)
    assert "SUBSCRIPTION_ACTIVATED" in rendered
    assert raw_subscriber not in rendered
    assert "subscriber_ref" in rendered
    assert "Raw payment proof" in rendered
