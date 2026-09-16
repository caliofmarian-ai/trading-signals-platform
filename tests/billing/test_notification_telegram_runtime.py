from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from runtime import telegram_updates


def test_billing_callback_is_intercepted_before_generic_dispatch(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_billing_callback(**kwargs):
        calls["billing"] = kwargs
        return {
            "accepted": True,
            "reason": "RECORDED",
            "ack_text": "Billing intent recorded.",
        }

    def fail_generic(_update):
        raise AssertionError("generic bot dispatcher must not receive BILL:I callback")

    def fake_ack(callback_id, text=""):
        calls["ack"] = (callback_id, text)

    monkeypatch.setattr(
        telegram_updates.notification_scheduler,
        "handle_telegram_callback",
        fake_billing_callback,
    )
    monkeypatch.setattr(telegram_updates.bot_service, "process_update", fail_generic)
    monkeypatch.setattr(telegram_updates, "_ack_callback", fake_ack)

    telegram_updates.process_update(
        {
            "update_id": 501,
            "callback_query": {
                "id": "callback-501",
                "from": {"id": 12345},
                "data": "BILL:I:0123456789abcdef01234567:K",
                "message": {
                    "message_id": 88,
                    "chat": {"id": 12345, "type": "private"},
                },
            },
        }
    )

    assert calls["billing"] == {
        "telegram_user_id": 12345,
        "telegram_chat_id": 12345,
        "callback_data": "BILL:I:0123456789abcdef01234567:K",
        "now_ts": calls["billing"]["now_ts"],
    }
    assert isinstance(calls["billing"]["now_ts"], int)
    assert calls["ack"] == ("callback-501", "Billing intent recorded.")


def test_billing_callback_failure_is_contained_and_acknowledged(monkeypatch) -> None:
    errors: list[dict] = []
    acknowledgements: list[tuple[object, str]] = []

    def fail_billing_callback(**_kwargs):
        raise RuntimeError("billing callback synthetic failure")

    monkeypatch.setattr(
        telegram_updates.notification_scheduler,
        "handle_telegram_callback",
        fail_billing_callback,
    )
    monkeypatch.setattr(
        telegram_updates.observability_logger,
        "log_error",
        lambda payload: errors.append(payload),
    )
    monkeypatch.setattr(
        telegram_updates,
        "_ack_callback",
        lambda callback_id, text="": acknowledgements.append((callback_id, text)),
    )

    telegram_updates.process_update(
        {
            "callback_query": {
                "id": "callback-fail",
                "from": {"id": 77},
                "data": "BILL:I:0123456789abcdef01234567:S",
                "message": {"chat": {"id": 77, "type": "private"}},
            }
        }
    )

    assert errors
    assert errors[0]["function"] == "billing_callback"
    assert acknowledgements == [
        ("callback-fail", "Billing action could not be recorded.")
    ]


def test_scheduler_failure_is_contained_from_poller(monkeypatch) -> None:
    errors: list[dict] = []

    def fail_scheduler():
        raise RuntimeError("scheduler synthetic failure")

    monkeypatch.setattr(
        telegram_updates.notification_scheduler,
        "maybe_run_notification_cycle",
        fail_scheduler,
    )
    monkeypatch.setattr(
        telegram_updates.observability_logger,
        "log_error",
        lambda payload: errors.append(payload),
    )

    telegram_updates._run_billing_scheduler_safely()

    assert len(errors) == 1
    assert errors[0]["function"] == "billing_notification_scheduler"
    assert "scheduler synthetic failure" in errors[0]["error"]
