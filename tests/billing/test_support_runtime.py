from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))

from billing import notification_scheduler, support_runtime
from runtime import telegram_updates


@pytest.fixture
def tmp_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    return tmp_path


def _bind(path: Path, subscriber: str, user_id: int) -> None:
    notification_scheduler.bind_private_delivery_target(
        subscriber_ref=subscriber,
        strategy_product_id="BINARY_TRADING",
        telegram_user_id=user_id,
        telegram_chat_id=user_id,
        path=str(path),
    )


def test_private_subscriber_resolution_is_explicit_and_fail_closed(tmp_base: Path) -> None:
    path = tmp_base / "billing" / "notification_events.jsonl"
    _bind(path, "subscriber-a", 101)
    resolved = support_runtime.resolve_private_subscriber(
        telegram_user_id=101,
        telegram_chat_id=101,
        notification_path=str(path),
    )
    assert resolved == {
        "subscriber_ref": "subscriber-a",
        "strategy_product_id": "BINARY_TRADING",
    }
    assert support_runtime.resolve_private_subscriber(
        telegram_user_id=101,
        telegram_chat_id=202,
        notification_path=str(path),
    ) is None

    _bind(path, "subscriber-b", 101)
    assert support_runtime.resolve_private_subscriber(
        telegram_user_id=101,
        telegram_chat_id=101,
        notification_path=str(path),
    ) is None


def test_private_support_handler_does_not_capture_commands(monkeypatch) -> None:
    monkeypatch.setattr(
        support_runtime,
        "resolve_private_subscriber",
        lambda **_kwargs: {
            "subscriber_ref": "subscriber-a",
            "strategy_product_id": "BINARY_TRADING",
        },
    )
    result = support_runtime.handle_private_text_message(
        {
            "message_id": 1,
            "chat": {"id": 101, "type": "private"},
            "from": {"id": 101},
            "text": "/start",
        }
    )
    assert result == {"handled": False, "reason": "NOT_SUPPORT_TEXT"}


def test_private_support_handler_requires_unique_support_context(monkeypatch) -> None:
    monkeypatch.setattr(
        support_runtime,
        "resolve_private_subscriber",
        lambda **_kwargs: {
            "subscriber_ref": "subscriber-a",
            "strategy_product_id": "BINARY_TRADING",
        },
    )
    monkeypatch.setattr(
        support_runtime.support_cases,
        "active_cases_for_subscriber",
        lambda *_args, **_kwargs: [],
    )
    result = support_runtime.handle_private_text_message(
        {
            "message_id": 2,
            "chat": {"id": 101, "type": "private"},
            "from": {"id": 101},
            "text": "I need help",
        }
    )
    assert result["handled"] is False
    assert result["reason"] == "NO_UNIQUE_SUPPORT_CONTEXT"


def test_private_support_handler_relays_message_when_context_is_unique(monkeypatch) -> None:
    monkeypatch.setattr(
        support_runtime,
        "resolve_private_subscriber",
        lambda **_kwargs: {
            "subscriber_ref": "subscriber-a",
            "strategy_product_id": "BINARY_TRADING",
        },
    )
    monkeypatch.setattr(
        support_runtime.support_cases,
        "active_cases_for_subscriber",
        lambda *_args, **_kwargs: [{"case_id": "case-1"}],
    )
    relayed: list[dict] = []
    monkeypatch.setattr(
        support_runtime.support_cases,
        "relay_client_message_to_admin",
        lambda **kwargs: relayed.append(kwargs) or {"delivery_result": "SENT"},
    )
    result = support_runtime.handle_private_text_message(
        {
            "message_id": 3,
            "chat": {"id": 101, "type": "private"},
            "from": {"id": 101},
            "text": "Please review the payment",
        },
        now_ts=1700000000,
    )
    assert result["handled"] is True
    assert result["case_id"] == "case-1"
    assert relayed[0]["subscriber_ref"] == "subscriber-a"
    assert relayed[0]["client_message_id"] == "telegram:101:3"


class FakeResponse:
    def __init__(
        self,
        *,
        json_data=None,
        chunks=None,
        status_code=200,
        headers=None,
    ) -> None:
        self._json_data = json_data
        self._chunks = chunks or []
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._json_data

    def iter_content(self, chunk_size=65536):
        del chunk_size
        yield from self._chunks


def test_telegram_proof_download_is_bounded_and_hashed(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABCDEF_test_token")
    body = b"payment-proof-bytes"
    calls: list[tuple[str, dict]] = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if url.endswith("/getFile"):
            return FakeResponse(
                json_data={
                    "ok": True,
                    "result": {
                        "file_id": "file-1",
                        "file_unique_id": "unique-1",
                        "file_size": len(body),
                        "file_path": "documents/proof.bin",
                    },
                }
            )
        return FakeResponse(
            chunks=[body[:5], body[5:]],
            headers={"Content-Length": str(len(body))},
        )

    result = support_runtime.download_telegram_file_for_hash(
        file_id="file-1",
        request_get=fake_get,
    )
    assert result["content_bytes"] == body
    assert result["sha256"] == hashlib.sha256(body).hexdigest()
    assert result["file_size"] == len(body)
    assert len(calls) == 2


def test_telegram_proof_metadata_over_20mb_is_rejected_before_download(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABCDEF_test_token")
    calls: list[str] = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return FakeResponse(
            json_data={
                "ok": True,
                "result": {
                    "file_id": "file-big",
                    "file_size": support_runtime.MAX_PROOF_BYTES + 1,
                    "file_path": "documents/big.bin",
                },
            }
        )

    with pytest.raises(support_runtime.SupportRuntimeError, match="20 MB"):
        support_runtime.download_telegram_file_for_hash(
            file_id="file-big",
            request_get=fake_get,
        )
    assert len(calls) == 1


def test_telegram_proof_stream_over_20mb_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABCDEF_test_token")

    def fake_get(url, **kwargs):
        if url.endswith("/getFile"):
            return FakeResponse(
                json_data={
                    "ok": True,
                    "result": {
                        "file_id": "file-stream-big",
                        "file_path": "documents/big.bin",
                    },
                }
            )
        return FakeResponse(
            chunks=[b"a" * (support_runtime.MAX_PROOF_BYTES + 1)],
        )

    with pytest.raises(support_runtime.SupportRuntimeError, match="20 MB"):
        support_runtime.download_telegram_file_for_hash(
            file_id="file-stream-big",
            request_get=fake_get,
        )


def test_private_proof_handler_records_restricted_proof_and_safe_admin_notice(monkeypatch) -> None:
    body = b"receipt-bytes"
    proof_sha = hashlib.sha256(body).hexdigest()
    monkeypatch.setattr(
        support_runtime,
        "_private_context",
        lambda *_args, **_kwargs: (
            {"subscriber_ref": "subscriber-a", "strategy_product_id": "BINARY_TRADING"},
            {"case_id": "case-proof", "subscriber_ref": "subscriber-a", "payment_intent_id": None},
            101,
            101,
        ),
    )
    monkeypatch.setattr(
        support_runtime,
        "download_telegram_file_for_hash",
        lambda **_kwargs: {
            "content_bytes": body,
            "sha256": proof_sha,
            "file_path": "documents/proof.jpg",
            "file_size": len(body),
        },
    )
    recorded: list[dict] = []
    monkeypatch.setattr(
        support_runtime.support_cases,
        "add_payment_proof",
        lambda **kwargs: recorded.append(kwargs) or {
            "record": {
                "proof_id": "proof-1",
                "proof_sha256": proof_sha,
                "proof_file_name": "receipt.jpg",
                "proof_mime_type": "image/jpeg",
                "proof_file_size": len(body),
                "payment_intent_id": None,
            }
        },
    )
    monkeypatch.setattr(
        support_runtime,
        "_notify_admin_of_proof",
        lambda **_kwargs: "SENT",
    )
    result = support_runtime.handle_private_proof_message(
        {
            "message_id": 4,
            "chat": {"id": 101, "type": "private"},
            "from": {"id": 101},
            "document": {
                "file_id": "restricted-file-id",
                "file_unique_id": "stable-file-id",
                "file_name": "receipt.jpg",
                "mime_type": "image/jpeg",
            },
        }
    )
    assert result["handled"] is True
    assert result["proof_sha256"] == proof_sha
    assert recorded[0]["telegram_file_id"] == "restricted-file-id"
    assert recorded[0]["telegram_file_unique_id"] == "stable-file-id"
    assert recorded[0]["content_bytes"] == body


def test_runtime_support_message_intercepts_only_when_handled(monkeypatch) -> None:
    generic: list[dict] = []
    client_acks: list[dict] = []
    monkeypatch.setattr(
        telegram_updates.support_runtime,
        "handle_private_text_message",
        lambda *_args, **_kwargs: {
            "handled": True,
            "case_id": "case-runtime",
            "delivery_result": "SENT",
        },
    )
    monkeypatch.setattr(
        telegram_updates.bot_service,
        "process_update",
        lambda update: generic.append(update),
    )
    monkeypatch.setattr(
        telegram_updates.telegram_publisher,
        "send_message",
        lambda **kwargs: client_acks.append(kwargs) or {"ok": True},
    )
    telegram_updates.process_update(
        {
            "message": {
                "message_id": 44,
                "chat": {"id": 101, "type": "private"},
                "from": {"id": 101},
                "text": "support message",
            }
        }
    )
    assert generic == []
    assert client_acks[0]["chat_id"] == 101
    assert "case-runtime" in client_acks[0]["text"]


def test_runtime_payment_proof_intercepts_before_generic_dispatch(monkeypatch) -> None:
    generic: list[dict] = []
    client_acks: list[dict] = []
    monkeypatch.setattr(
        telegram_updates.support_runtime,
        "handle_private_proof_message",
        lambda *_args, **_kwargs: {
            "handled": True,
            "case_id": "case-proof-runtime",
            "proof_id": "proof-runtime",
            "delivery_result": "SENT",
        },
    )
    monkeypatch.setattr(
        telegram_updates.bot_service,
        "process_update",
        lambda update: generic.append(update),
    )
    monkeypatch.setattr(
        telegram_updates.telegram_publisher,
        "send_message",
        lambda **kwargs: client_acks.append(kwargs) or {"ok": True},
    )
    telegram_updates.process_update(
        {
            "message": {
                "message_id": 46,
                "chat": {"id": 101, "type": "private"},
                "from": {"id": 101},
                "document": {"file_id": "file-proof", "file_unique_id": "unique-proof"},
            }
        }
    )
    assert generic == []
    assert client_acks[0]["chat_id"] == 101
    assert "payment proof recorded" in client_acks[0]["text"].lower()


def test_runtime_payment_proof_failure_is_consumed_and_safe(monkeypatch) -> None:
    generic: list[dict] = []
    client_acks: list[dict] = []
    monkeypatch.setattr(
        telegram_updates.support_runtime,
        "handle_private_proof_message",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("secret failure")),
    )
    monkeypatch.setattr(
        telegram_updates.bot_service,
        "process_update",
        lambda update: generic.append(update),
    )
    monkeypatch.setattr(
        telegram_updates.telegram_publisher,
        "send_message",
        lambda **kwargs: client_acks.append(kwargs) or {"ok": True},
    )
    monkeypatch.setattr(
        telegram_updates.observability_logger,
        "log_error",
        lambda *_args, **_kwargs: None,
    )
    telegram_updates.process_update(
        {
            "message": {
                "message_id": 47,
                "chat": {"id": 101, "type": "private"},
                "from": {"id": 101},
                "photo": [{"file_id": "file-proof", "file_unique_id": "unique-proof"}],
            }
        }
    )
    assert generic == []
    assert "could not be recorded" in client_acks[0]["text"].lower()
    assert "secret failure" not in client_acks[0]["text"]


def test_runtime_non_support_message_falls_back_to_existing_dispatch(monkeypatch) -> None:
    generic: list[dict] = []
    monkeypatch.setattr(
        telegram_updates.support_runtime,
        "handle_private_text_message",
        lambda *_args, **_kwargs: {"handled": False, "reason": "NO_CASE"},
    )
    monkeypatch.setattr(
        telegram_updates.bot_service,
        "process_update",
        lambda update: generic.append(update),
    )
    update = {
        "message": {
            "message_id": 45,
            "chat": {"id": 101, "type": "private"},
            "from": {"id": 101},
            "text": "/start",
        }
    }
    telegram_updates.process_update(update)
    assert generic == [update]


def test_runtime_billing_support_intent_opens_case_and_extends_ack(monkeypatch) -> None:
    acknowledgements: list[tuple[object, str]] = []
    monkeypatch.setattr(
        telegram_updates.notification_scheduler,
        "handle_telegram_callback",
        lambda **_kwargs: {
            "accepted": True,
            "reason": "RECORDED",
            "ack_text": "Support request recorded.",
            "client_intent_id": "client-intent-1",
        },
    )
    monkeypatch.setattr(
        telegram_updates.support_runtime,
        "open_case_for_client_intent_if_needed",
        lambda *_args, **_kwargs: {
            "status": "OPENED",
            "record": {"case_id": "case-opened"},
        },
    )
    monkeypatch.setattr(
        telegram_updates,
        "_ack_callback",
        lambda callback_id, text="": acknowledgements.append((callback_id, text)),
    )
    telegram_updates.process_update(
        {
            "callback_query": {
                "id": "callback-support",
                "from": {"id": 101},
                "data": "BILL:I:0123456789abcdef01234567:S",
                "message": {"chat": {"id": 101, "type": "private"}},
            }
        }
    )
    assert acknowledgements
    assert acknowledgements[0][0] == "callback-support"
    assert "case-opened" in acknowledgements[0][1]
