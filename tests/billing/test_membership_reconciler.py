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

SUBSCRIBER = "membership-subscriber"
PRODUCT = "BINARY_TRADING"
USER_ID = 10101
CHANNELS = {
    "FREE": -1001001,
    "BASIC": -1001002,
    "PRO": -1001003,
    "ELITE": -1001004,
}
BASE = 1_700_000_000


class FakeAPI:
    def __init__(self, memberships=None) -> None:
        self.memberships = {
            channel: dict(value)
            for channel, value in (memberships or {}).items()
        }
        self.calls: list[tuple] = []
        self.invite_count = 0
        self.keep_member_after_ban: set[int] = set()
        self.fail_methods: set[str] = set()

    def get_chat_member(self, chat_id: int, user_id: int):
        self.calls.append(("get", chat_id, user_id))
        if "get" in self.fail_methods:
            raise RuntimeError("getChatMember failed safely")
        return dict(self.memberships.get(chat_id, {"status": "left"}))

    def ban_chat_member(self, chat_id: int, user_id: int):
        self.calls.append(("ban", chat_id, user_id))
        if "ban" in self.fail_methods:
            raise RuntimeError("banChatMember failed safely")
        if chat_id not in self.keep_member_after_ban:
            self.memberships[chat_id] = {"status": "kicked"}
        return {"ok": True}

    def unban_chat_member(self, chat_id: int, user_id: int):
        self.calls.append(("unban", chat_id, user_id))
        if "unban" in self.fail_methods:
            raise RuntimeError("unbanChatMember failed safely")
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
        if "invite" in self.fail_methods:
            raise RuntimeError("createChatInviteLink failed safely")
        self.invite_count += 1
        return {
            "invite_link": f"https://t.me/+bounded-{self.invite_count}",
            "expire_date": expire_date,
            "member_limit": member_limit,
        }


@pytest.fixture
def event_path(tmp_path: Path) -> Path:
    return tmp_path / "membership_events.jsonl"


def _entitlement(*, tier="BASIC", access_state="ACTIVE", version=7):
    return {
        "entitlement_id": "entitlement-1",
        "entitlement_version": version,
        "subscriber_ref": SUBSCRIBER,
        "strategy_product_id": PRODUCT,
        "subscription_id": "subscription-1",
        "subscription_state": "ACTIVE",
        "plan_id": f"BINARY_TRADING_{tier}",
        "tier": tier,
        "access_state": access_state,
        "source_subscription_event_id": "subscription-event-1",
    }


def _binding(subscriber=SUBSCRIBER, user_id=USER_ID):
    return {
        "event_type": membership_reconciler.notification_scheduler.EVENT_TARGET_BOUND,
        "subscriber_ref": subscriber,
        "strategy_product_id": PRODUCT,
        "telegram_user_id": user_id,
        "telegram_chat_id": user_id,
    }


def _patch_authorities(monkeypatch, *, entitlement=None, bindings=None, channels=None):
    monkeypatch.setattr(
        membership_reconciler.subscription_registry,
        "resolve_entitlement",
        lambda **_kwargs: dict(entitlement or _entitlement()),
    )
    monkeypatch.setattr(
        membership_reconciler.notification_scheduler,
        "load_events",
        lambda _path=None: list(bindings or [_binding()]),
    )
    monkeypatch.setattr(
        membership_reconciler.distribution_router,
        "load_config",
        lambda: {"channels": dict(channels or CHANNELS)},
    )


def test_negative_telegram_channel_ids_are_valid_and_in_sync(monkeypatch, event_path: Path) -> None:
    _patch_authorities(monkeypatch)
    api = FakeAPI({CHANNELS["BASIC"]: {"status": "member"}})
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=False,
        api=api,
        path=str(event_path),
    )
    assert result["state"] == "IN_SYNC"
    assert result["actions_applied"] is False
    assert api.calls[0][1] == CHANNELS["FREE"]


def test_missing_exclusive_channel_config_fails_unknown_without_mutation(monkeypatch, event_path: Path) -> None:
    partial = dict(CHANNELS)
    partial["ELITE"] = None
    _patch_authorities(monkeypatch, channels=partial)
    api = FakeAPI()
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        path=str(event_path),
    )
    assert result["state"] == "UNKNOWN"
    assert api.calls == []


def test_ambiguous_reverse_telegram_binding_fails_closed(monkeypatch, event_path: Path) -> None:
    _patch_authorities(
        monkeypatch,
        bindings=[_binding(), _binding(subscriber="another-subscriber")],
    )
    api = FakeAPI()
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        path=str(event_path),
    )
    assert result["state"] == "UNKNOWN"
    assert api.calls == []


def test_stale_paid_membership_is_removed_before_bounded_invite(monkeypatch, event_path: Path) -> None:
    _patch_authorities(monkeypatch)
    api = FakeAPI({CHANNELS["PRO"]: {"status": "member"}})
    sent: list[dict] = []
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        send_fn=lambda **kwargs: sent.append(kwargs) or {"ok": True},
        path=str(event_path),
    )
    assert result["state"] == "INVITE_REQUIRED"
    ban_index = next(i for i, call in enumerate(api.calls) if call[0] == "ban")
    invite_index = next(i for i, call in enumerate(api.calls) if call[0] == "invite")
    assert ban_index < invite_index
    assert api.calls[ban_index][1] == CHANNELS["PRO"]
    assert api.calls[invite_index][1] == CHANNELS["BASIC"]
    assert api.calls[invite_index][3] == 1
    assert len(sent) == 1
    assert result["invite_link"] in sent[0]["text"]
    persisted = event_path.read_text(encoding="utf-8")
    assert result["invite_link"] not in persisted
    assert "invite_link_sha256" in persisted


def test_failed_paid_removal_is_critical_access_leak_and_blocks_invite(monkeypatch, event_path: Path) -> None:
    _patch_authorities(monkeypatch)
    api = FakeAPI({CHANNELS["PRO"]: {"status": "member"}})
    api.keep_member_after_ban.add(CHANNELS["PRO"])
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
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    assert result["state"] == "ACCESS_LEAK_RISK"
    assert not any(call[0] == "invite" for call in api.calls)
    assert critical and critical[0]["severity"] == "CRITICAL"


def test_target_kicked_is_unbanned_only_when_currently_entitled(monkeypatch, event_path: Path) -> None:
    _patch_authorities(monkeypatch)
    api = FakeAPI({CHANNELS["BASIC"]: {"status": "kicked"}})
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    assert result["state"] == "INVITE_REQUIRED"
    assert any(call[0] == "unban" and call[1] == CHANNELS["BASIC"] for call in api.calls)
    assert any(call[0] == "invite" for call in api.calls)


def test_active_invite_is_not_duplicated_before_expiry_and_rotates_after(monkeypatch, event_path: Path) -> None:
    _patch_authorities(monkeypatch)
    api = FakeAPI()
    first = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    assert first["state"] == "INVITE_REQUIRED"
    assert api.invite_count == 1

    second = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE + 60,
        apply_actions=True,
        api=api,
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    assert second["state"] == "INVITE_REQUIRED"
    assert second.get("active_invite") is True
    assert api.invite_count == 1

    third = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE + membership_reconciler.DEFAULT_INVITE_TTL_SECONDS + 1,
        apply_actions=True,
        api=api,
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    assert third["state"] == "INVITE_REQUIRED"
    assert api.invite_count == 2


def test_delayed_join_is_verified_by_get_chat_member(monkeypatch, event_path: Path) -> None:
    _patch_authorities(monkeypatch)
    api = FakeAPI()
    membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    api.memberships[CHANNELS["BASIC"]] = {"status": "member"}
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE + 120,
        apply_actions=True,
        api=api,
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    assert result["state"] == "IN_SYNC"


def test_suspended_paid_entitlement_removes_paid_access_and_creates_no_invite(monkeypatch, event_path: Path) -> None:
    _patch_authorities(
        monkeypatch,
        entitlement=_entitlement(tier="BASIC", access_state="SUSPENDED"),
    )
    api = FakeAPI({CHANNELS["BASIC"]: {"status": "member"}})
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        path=str(event_path),
    )
    assert result["state"] == "IN_SYNC"
    assert any(call[0] == "ban" and call[1] == CHANNELS["BASIC"] for call in api.calls)
    assert not any(call[0] == "invite" for call in api.calls)


def test_free_fallback_targets_free_channel(monkeypatch, event_path: Path) -> None:
    _patch_authorities(
        monkeypatch,
        entitlement=_entitlement(tier="FREE", access_state="FREE_FALLBACK"),
    )
    api = FakeAPI()
    result = membership_reconciler.reconcile_membership(
        subscriber_ref=SUBSCRIBER,
        now_ts=BASE,
        apply_actions=True,
        api=api,
        send_fn=lambda **_kwargs: {"ok": True},
        path=str(event_path),
    )
    assert result["state"] == "INVITE_REQUIRED"
    invite = next(call for call in api.calls if call[0] == "invite")
    assert invite[1] == CHANNELS["FREE"]


def test_chat_member_update_is_idempotent_and_accepts_negative_channel_id(event_path: Path) -> None:
    first = membership_reconciler.record_chat_member_update(
        telegram_update_id=555,
        chat_id=CHANNELS["BASIC"],
        telegram_user_id=USER_ID,
        old_status="left",
        new_status="member",
        now_ts=BASE,
        path=str(event_path),
    )
    replay = membership_reconciler.record_chat_member_update(
        telegram_update_id=555,
        chat_id=CHANNELS["BASIC"],
        telegram_user_id=USER_ID,
        old_status="left",
        new_status="member",
        now_ts=BASE + 1,
        path=str(event_path),
    )
    assert first["status"] == "RECORDED"
    assert replay["status"] == "DUPLICATE"
    assert len(membership_reconciler.load_events(str(event_path))) == 1


def test_corrupt_event_log_fails_closed(event_path: Path) -> None:
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(membership_reconciler.MembershipReconciliationError):
        membership_reconciler.load_events(str(event_path))


def test_automatic_membership_mutation_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("BILLING_MEMBERSHIP_RECONCILER_ENABLED", raising=False)
    assert membership_reconciler.automatic_reconciliation_enabled() is False
    monkeypatch.setenv("BILLING_MEMBERSHIP_RECONCILER_ENABLED", "true")
    assert membership_reconciler.automatic_reconciliation_enabled() is True
