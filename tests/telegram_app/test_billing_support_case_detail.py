"""Issue #166 — masked billing support case drilldown and authorization boundary.

These are offline tests. They never call providers, mutate entitlements, send
Telegram messages, or expose sensitive proof/message/source identifiers.
"""

from __future__ import annotations

from billing import support_cases
from core import billing_admin_views, bot_service, telegram_admin_ui
from core.role_constants import ROLE_ANALYST, ROLE_OWNER


def _case_event(
    *,
    case_id: str = "case-raw-secret",
    kind: str = support_cases.EVENT_CASE_OPENED,
    state: str = "OPEN",
    timestamp: int = 1800000000,
    provider: str = "KUCOIN",
    payment_intent_id: str | None = None,
) -> dict:
    return {
        "event_type": kind,
        "case_id": case_id,
        "case_state": state,
        "provider": provider,
        "payment_intent_id": payment_intent_id,
        "subscriber_ref": "subscriber-raw-secret",
        "message_text": "customer-secret-text-with-phone-1234567890",
        "restricted_telegram_file_id": "telegram-proof-secret",
        "proof_file_name": "private-bank-statement.pdf",
        "occurred_at_epoch": timestamp,
    }


def _context(rows: list[dict], *, status: str = "PASS") -> dict:
    return {
        "records": {"support_cases": rows},
        "source_status": {"support_cases": {"status": status}},
    }


def _callbacks(markup: dict) -> list[str]:
    return [
        button["callback_data"]
        for row in markup["inline_keyboard"]
        for button in row
    ]


def test_open_support_case_has_only_opaque_hash_callback_and_masked_details():
    rows = [
        _case_event(),
        _case_event(kind=support_cases.EVENT_CLIENT_MESSAGE, state="UNDER_REVIEW", timestamp=1800000010),
        _case_event(kind=support_cases.EVENT_PAYMENT_PROOF, state="UNDER_REVIEW", timestamp=1800000020, payment_intent_id="payment-secret"),
        _case_event(kind=support_cases.EVENT_ADMIN_MESSAGE, state="UNDER_REVIEW", timestamp=1800000030, payment_intent_id="payment-secret"),
    ]
    ctx = _context(rows)
    tokens = billing_admin_views.support_case_navigation(ctx)
    assert len(tokens) == 1
    label, token = tokens[0]
    assert label.startswith("CASE-…")
    assert len(token) == 16
    assert token.isalnum()

    keyboard = telegram_admin_ui.billing_support_queue_markup(tokens)
    callbacks = _callbacks(keyboard)
    assert f"ADMIN_NAV:BILLING_CASE:{token}" in callbacks
    assert "ADMIN_NAV:BILLING_SUPPORT" in callbacks
    assert all(len(value.encode("utf-8")) <= 64 for value in callbacks)
    assert telegram_admin_ui.is_distribution_subpage_action(f"BILLING_CASE:{token}")

    detail = billing_admin_views.render_support_case_detail(token, ctx)
    assert "State: UNDER_REVIEW" in detail
    assert "Provider: KUCOIN" in detail
    assert "Payment intent: LINKED" in detail
    assert "Client messages: 1" in detail
    assert "Admin replies: 1" in detail
    assert "Payment-proof submissions: 1" in detail
    assert "PAYMENT PROOF SUBMITTED != PAYMENT VERIFIED" in detail

    for confidential in (
        "case-raw-secret", "subscriber-raw-secret", "payment-secret",
        "customer-secret-text", "1234567890", "telegram-proof-secret",
        "private-bank-statement.pdf",
    ):
        assert confidential not in detail
        assert confidential not in str(keyboard)


def test_closed_case_not_in_open_selector_but_keeps_safe_read_only_history():
    rows = [
        _case_event(case_id="case-closed"),
        _case_event(
            case_id="case-closed",
            kind=support_cases.EVENT_REVIEW,
            state="RESOLVED",
            timestamp=1800000040,
        ),
    ]
    ctx = _context(rows)
    assert billing_admin_views.support_case_navigation(ctx) == []
    token = billing_admin_views._case_token("case-closed")
    detail = billing_admin_views.render_support_case_detail(token, ctx)
    assert "State: RESOLVED" in detail
    assert "Review events: 1" in detail
    assert "case-closed" not in detail


def test_unvalidated_source_is_unknown_not_zero_or_invented_case():
    ctx = _context([_case_event()], status="UNKNOWN")
    token = billing_admin_views._case_token("case-raw-secret")
    assert billing_admin_views.support_case_navigation(ctx) == []
    assert "UNKNOWN" in billing_admin_views.render_support_case_detail(token, ctx)
    assert "Client messages: 0" not in billing_admin_views.render_support_case_detail(token, ctx)


def test_case_token_hash_collision_fails_closed(monkeypatch):
    ctx = _context([
        _case_event(case_id="case-A"),
        _case_event(case_id="case-B", timestamp=1800000100),
    ])
    monkeypatch.setattr(
        billing_admin_views,
        "_case_token",
        lambda case_id: "0123456789abcdef" if case_id else None,
    )
    assert billing_admin_views.support_case_navigation(ctx) == []
    detail = billing_admin_views.render_support_case_detail("0123456789abcdef", ctx)
    assert "Case evidence: UNAVAILABLE" in detail


def test_forged_case_callback_is_denied_before_accessing_billing_source(monkeypatch):
    token = billing_admin_views._case_token("case-raw-secret")
    monkeypatch.setattr(bot_service, "get_primary_role", lambda uid: ROLE_ANALYST)

    def forbidden_read():
        raise AssertionError("unauthorized user reached billing evidence source")

    monkeypatch.setattr(billing_admin_views, "_safe_context", forbidden_read)
    result = bot_service._handle_admin_navigation_action(
        f"BILLING_CASE:{token}",
        111,
        {"chat": {"id": -100888, "type": "supergroup"}, "from": {"id": 111}},
    )
    assert result["text"] == "Access denied (missing panel permission)."
    assert result["reply_markup"] is None


def test_owner_case_callback_is_read_only_with_safe_parent(monkeypatch):
    token = billing_admin_views._case_token("case-raw-secret")
    ctx = _context([_case_event()])
    monkeypatch.setattr(bot_service, "get_primary_role", lambda uid: ROLE_OWNER)
    monkeypatch.setattr(bot_service, "_is_owner_private_for_message", lambda *_args: True)
    monkeypatch.setattr(billing_admin_views, "_safe_context", lambda: ctx)
    result = bot_service._handle_admin_navigation_action(
        f"BILLING_CASE:{token}",
        111,
        {"chat": {"id": 111, "type": "private"}, "from": {"id": 111}},
    )
    assert "Case: CASE-…" in result["text"]
    assert "case-raw-secret" not in result["text"]
    callbacks = _callbacks(result["reply_markup"])
    assert "ADMIN_NAV:BILLING_SUPPORT" in callbacks
    assert f"ADMIN_NAV:BILLING_CASE:{token}" in callbacks
    assert "ADMIN_NAV:VERIFY" not in callbacks


def test_queue_panel_uses_one_validated_source_read_and_masks_case(monkeypatch):
    ctx = _context([_case_event()])
    reads = []
    monkeypatch.setattr(billing_admin_views, "_safe_context", lambda: reads.append(1) or ctx)
    text, cases = billing_admin_views.render_support_queue_panel()
    assert reads == [1]
    assert "OPEN CASES: 1" in text
    assert "case-raw-secret" not in text
    assert len(cases) == 1


def test_unsafe_provider_content_is_not_rendered_and_bad_timestamp_does_not_crash():
    row = _case_event(provider="KUCOIN token-secret", timestamp=1800000000)
    row["occurred_at_epoch"] = "invalid-timestamp-and-phone-1234"
    ctx = _context([row])
    assert "KUCOIN token-secret" not in billing_admin_views.render_support_queue(ctx)
    token = billing_admin_views._case_token("case-raw-secret")
    detail = billing_admin_views.render_support_case_detail(token, ctx)
    assert "Provider: UNKNOWN" in detail
    assert "token-secret" not in detail


def test_malformed_case_token_has_no_navigation_authority():
    for token in ("", "123", "I" * 16, "../" * 5, "0" * 17):
        action = "BILLING_CASE:" + token
        assert telegram_admin_ui.is_billing_case_detail_action(action) is False
        assert telegram_admin_ui.is_distribution_subpage_action(action) is False
        assert "Case evidence: UNAVAILABLE" in billing_admin_views.render_support_case_detail(token, {})
