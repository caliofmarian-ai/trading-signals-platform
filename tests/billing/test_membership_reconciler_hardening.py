from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import membership_reconciler

SUBSCRIBER = "membership-hardening-subscriber"
PRODUCT = "BINARY_TRADING"
USER_ID = 20202
BASE = 1_700_100_000
CHANNELS = {
    "FREE": -1002001,
    "BASIC": -1002002,
    "PRO": -1002003,
    "ELITE": -1002004,
}


class FakeAPI:
    def __init__(self, memberships=None) -> None:
        self.memberships = {
            channel: dict(value)
            for channel, value in (memberships or {}).items()
        }
        self.calls: list[tuple] = []

    def get_chat_member(self, chat_id: int, user_id: int):
        self.calls.append(("get", chat_id, user_id))
        return dict(self.memberships.get(chat_id, {"status": "left"}))

    def ban_chat_member(self, chat_id: int, user_id: int):
        self.calls.append(("ban", chat_id, user_id))
        if self.memberships.get(chat_id, {}).get("_keep_after_ban"):
            return {"ok": True}
        self.memberships[chat_id] = {"status": "kicked"}
        return {"ok": True}

    def unban_chat_member(self, chat_id: int, user_id: int):
        self.calls.append(("unban", chat_id, user_id))
        self.memberships[chat_id] = {"status": "left"}
        return {"ok": True}

    def create_chat_invite_link(
        self,
        chat_id: int,
        *,
        expire_date: int,
        member_limit: int,
        name: str,
    ):
        self.calls.append(("invite", chat_id, expire_date, member_limit, name))
        return {
            "invite_link": "https://t.me/+sensitive-bounded-capability",
            "expire_date": expire_date,
            "member_limit": member_limit,
        }


def _entitlement(*, tier="BASIC", access_state="ACTIVE", version=3):
    return {
        "entitlement_id": "ent-hardening",
        "entitlement_version": version,
        "subscriber_ref": SUBSCRIBER,
        "strategy_product_id": PRODUCT,
        "subscription_id": "sub-hardening",
        "subscription_state": "ACTIVE",
        "plan_id": f"BINARY_TRADING_{tier}",
        "tier": tier,
        "access_state": access_state,
        "source_subscription_event_id": "source-event-hardening",
    }


def _binding():
    return {
        "event_type": membership_reconciler.notification_scheduler.EVENT_TARGET_BOUND,
        "subscriber_ref": SUBSCRIBER,
        "strategy_product_id": PRODUCT,
        "telegram_user_id": USER_ID,
        "telegram_chat_id": USER_ID,
    }


def _patch(monkeypatch, *, entitlement=None, channels=None):
    monkeypatch.setattr(
        membership_reconciler.subscription_registry,
        "resolve_entitlement",
        lambda **_kwargs: dict(entitlement or _entitlement()),
    )
    monkeypatch.setattr(
        membership_reconciler.notification_scheduler,
        "load_events",
        lambda _path=None: [_binding()],
    )
    monkeypatch.setattr(
        membership_reconciler.distribution_router,
        "load_config",
        lambda: {"channels": dict(channels or CHANNELS)},
    )


def test_duplicate_exclusive_channel_ids_fail_unknown_before_api_calls(
    monkeypatch, tmp_path: Path
) -> None:
    duplicate = dict(CHANNELS)
    duplicate["PRO"] = duplicate["BASIC"]
    _patch(monkeypatch, channels=duplicate)
    api = FakeAPI()
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        path=str(tmp_path / "membership.jsonl"),
    )
    assert result["state"] == "UNKNOWN"
    assert api.calls == []


def test_restricted_member_with_is_member_true_counts_as_current_membership(
    monkeypatch, tmp_path: Path
) -> None:
    _patch(monkeypatch)
    api = FakeAPI(
        {
            CHANNELS["BASIC"]: {
                "status": "restricted",
                "is_member": True,
            }
        }
    )
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=False,
        api=api,
        path=str(tmp_path / "membership.jsonl"),
    )
    assert result["state"] == "IN_SYNC"


def test_free_channel_removal_failure_is_action_failed_not_paid_access_leak(
    monkeypatch, tmp_path: Path
) -> None:
    _patch(monkeypatch)
    api = FakeAPI(
        {
            CHANNELS["FREE"]: {
                "status": "member",
                "_keep_after_ban": True,
            }
        }
    )
    critical: list[dict] = []
    monkeypatch.setattr(
        membership_reconciler.observability_logger,
        "log_error",
        lambda payload: critical.append(payload),
    )
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        path=str(tmp_path / "membership.jsonl"),
    )
    assert result["state"] == "ACTION_FAILED"
    assert critical == []
    assert not any(call[0] == "invite" for call in api.calls)


def test_invite_delivery_failure_is_action_failed_and_raw_link_is_not_persisted(
    monkeypatch, tmp_path: Path
) -> None:
    _patch(monkeypatch)
    api = FakeAPI()
    path = tmp_path / "membership.jsonl"

    def fail_send(**_kwargs):
        raise RuntimeError("client blocked bot")

    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        send_fn=fail_send,
        path=str(path),
    )
    assert result["state"] == "ACTION_FAILED"
    raw = path.read_text(encoding="utf-8")
    assert "https://t.me/+sensitive-bounded-capability" not in raw
    assert "invite_link_sha256" in raw
    rows = [json.loads(line) for line in raw.splitlines() if line]
    invite_rows = [
        row
        for row in rows
        if row.get("event_type") == membership_reconciler.EVENT_INVITE
    ]
    assert invite_rows[-1]["invite_delivery_result"] == "FAILED"


def test_telegram_api_transport_error_redacts_bot_token(monkeypatch) -> None:
    token = "123456789:SecretToken_Value"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", token)

    def fail_post(url, **_kwargs):
        raise RuntimeError(f"network failure at {url}")

    api = membership_reconciler.TelegramMembershipAPI(request_post=fail_post)
    with pytest.raises(membership_reconciler.MembershipReconciliationError) as exc:
        api.get_chat_member(CHANNELS["BASIC"], USER_ID)
    message = str(exc.value)
    assert token not in message
    assert "[REDACTED]" in message


def test_dry_run_reconcile_all_known_subscribers_does_not_mutate_membership(
    monkeypatch, tmp_path: Path
) -> None:
    subscription_rows = [
        {"subscriber_ref": "subscriber-a", "strategy_product_id": PRODUCT},
        {"subscriber_ref": "subscriber-b", "strategy_product_id": PRODUCT},
    ]
    monkeypatch.setattr(
        membership_reconciler.subscription_registry,
        "load_subscription_events",
        lambda _path=None: subscription_rows,
    )
    calls: list[dict] = []

    def fake_reconcile(**kwargs):
        calls.append(kwargs)
        return {"state": "UNKNOWN", "actions_applied": False}

    monkeypatch.setattr(
        membership_reconciler,
        "reconcile_membership",
        fake_reconcile,
    )
    results = membership_reconciler.reconcile_all_known_subscribers(
        apply_actions=False,
        now_ts=BASE,
        path=str(tmp_path / "membership.jsonl"),
    )
    assert len(results) == 2
    assert all(call["apply_actions"] is False for call in calls)
