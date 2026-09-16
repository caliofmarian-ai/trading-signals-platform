from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, Mapping, Optional

import requests

from billing import notification_scheduler, support_cases
from core import telegram_publisher

MAX_PROOF_BYTES = 20 * 1024 * 1024


class SupportRuntimeError(RuntimeError):
    """Raised when Telegram support transport cannot be proven safe."""


def _positive_id(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise SupportRuntimeError(f"{label} must be a positive integer")
    try:
        result = int(value)
    except Exception as exc:
        raise SupportRuntimeError(f"{label} must be a positive integer") from exc
    if result <= 0:
        raise SupportRuntimeError(f"{label} must be a positive integer")
    return result


def _latest_bindings(
    notification_path: str | None = None,
) -> Dict[tuple[str, str], Dict[str, Any]]:
    latest: Dict[tuple[str, str], Dict[str, Any]] = {}
    for row in notification_scheduler.load_events(notification_path):
        if row.get("event_type") != notification_scheduler.EVENT_TARGET_BOUND:
            continue
        key = (
            str(row.get("subscriber_ref")),
            str(row.get("strategy_product_id")),
        )
        latest[key] = dict(row)
    return latest


def resolve_private_subscriber(
    *,
    telegram_user_id: int,
    telegram_chat_id: int,
    notification_path: str | None = None,
) -> Optional[Dict[str, str]]:
    user_id = _positive_id(telegram_user_id, label="telegram_user_id")
    chat_id = _positive_id(telegram_chat_id, label="telegram_chat_id")
    if user_id != chat_id:
        return None
    matches = [
        {
            "subscriber_ref": subscriber,
            "strategy_product_id": product,
        }
        for (subscriber, product), row in _latest_bindings(
            notification_path
        ).items()
        if int(row.get("telegram_user_id") or 0) == user_id
        and int(row.get("telegram_chat_id") or 0) == chat_id
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def open_case_for_client_intent_if_needed(
    client_intent_id: str,
    *,
    now_ts: float | int | None = None,
    support_path: str | None = None,
    notification_path: str | None = None,
) -> Dict[str, Any]:
    return support_cases.open_case_from_client_intent(
        client_intent_id=client_intent_id,
        now_ts=now_ts,
        path=support_path,
        notification_path=notification_path,
    )


def _active_case_for_identity(
    *,
    subscriber_ref: str,
    strategy_product_id: str,
    support_path: str | None,
) -> Optional[Dict[str, Any]]:
    cases = support_cases.active_cases_for_subscriber(
        subscriber_ref,
        strategy_product_id,
        support_path,
    )
    if len(cases) != 1:
        return None
    return cases[0]


def _private_context(
    message: Mapping[str, Any],
    *,
    support_path: str | None,
    notification_path: str | None,
) -> tuple[Dict[str, str], Dict[str, Any], int, int] | None:
    chat = message.get("chat")
    sender = message.get("from")
    if not isinstance(chat, Mapping) or not isinstance(sender, Mapping):
        return None
    if str(chat.get("type") or "") != "private":
        return None
    try:
        user_id = _positive_id(sender.get("id"), label="from.id")
        chat_id = _positive_id(chat.get("id"), label="chat.id")
    except SupportRuntimeError:
        return None
    identity = resolve_private_subscriber(
        telegram_user_id=user_id,
        telegram_chat_id=chat_id,
        notification_path=notification_path,
    )
    if identity is None:
        return None
    case = _active_case_for_identity(
        subscriber_ref=identity["subscriber_ref"],
        strategy_product_id=identity["strategy_product_id"],
        support_path=support_path,
    )
    if case is None:
        return None
    return identity, case, user_id, chat_id


def handle_private_text_message(
    message: Mapping[str, Any],
    *,
    now_ts: float | int | None = None,
    support_path: str | None = None,
    notification_path: str | None = None,
) -> Dict[str, Any]:
    text = message.get("text")
    if (
        not isinstance(text, str)
        or not text.strip()
        or text.lstrip().startswith("/")
    ):
        return {"handled": False, "reason": "NOT_SUPPORT_TEXT"}
    context = _private_context(
        message,
        support_path=support_path,
        notification_path=notification_path,
    )
    if context is None:
        return {"handled": False, "reason": "NO_UNIQUE_SUPPORT_CONTEXT"}
    identity, case, _, chat_id = context
    message_id = str(message.get("message_id") or "")
    if not message_id:
        return {"handled": False, "reason": "MESSAGE_ID_MISSING"}
    result = support_cases.relay_client_message_to_admin(
        case_id=str(case["case_id"]),
        subscriber_ref=identity["subscriber_ref"],
        text=text.strip(),
        client_message_id=f"telegram:{chat_id}:{message_id}",
        now_ts=now_ts,
        path=support_path,
    )
    return {
        "handled": True,
        "reason": "SUPPORT_MESSAGE_RECORDED",
        "case_id": case["case_id"],
        "delivery_result": result.get("delivery_result"),
    }


def _telegram_get_file(
    file_id: str,
    *,
    request_get=requests.get,
) -> Dict[str, Any]:
    response = request_get(
        f"{telegram_publisher._base_url()}/getFile",
        params={"file_id": file_id},
        timeout=15,
    )
    data = response.json()
    if not data.get("ok") or not isinstance(data.get("result"), dict):
        raise SupportRuntimeError("Telegram getFile failed")
    result = dict(data["result"])
    size = result.get("file_size")
    if size is not None:
        try:
            parsed_size = int(size)
        except Exception as exc:
            raise SupportRuntimeError("Telegram file_size is invalid") from exc
        if parsed_size < 0 or parsed_size > MAX_PROOF_BYTES:
            raise SupportRuntimeError(
                "Telegram proof exceeds 20 MB download boundary"
            )
    file_path = result.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        raise SupportRuntimeError(
            "Telegram getFile response is missing file_path"
        )
    return result


def download_telegram_file_for_hash(
    *,
    file_id: str,
    request_get=requests.get,
) -> Dict[str, Any]:
    """Download a Telegram proof with a hard 20 MB bound.

    Bytes are returned only to the immediate caller for hashing/validation and
    are not persisted by this adapter. Callers must not log the tokenized URL.
    """

    safe_file_id = str(file_id or "").strip()
    if not safe_file_id:
        raise SupportRuntimeError("file_id is required")
    metadata = _telegram_get_file(safe_file_id, request_get=request_get)
    token = telegram_publisher._get_bot_token()
    file_path = str(metadata["file_path"])
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    response = request_get(url, stream=True, timeout=30)
    if getattr(response, "status_code", 200) >= 400:
        raise SupportRuntimeError("Telegram proof download failed")
    content_length = getattr(response, "headers", {}).get("Content-Length")
    if content_length:
        try:
            if int(content_length) > MAX_PROOF_BYTES:
                raise SupportRuntimeError(
                    "Telegram proof exceeds 20 MB download boundary"
                )
        except ValueError:
            pass
    body = bytearray()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        body.extend(chunk)
        if len(body) > MAX_PROOF_BYTES:
            raise SupportRuntimeError(
                "Telegram proof exceeds 20 MB download boundary"
            )
    if not body:
        raise SupportRuntimeError(
            "Telegram proof download returned no bytes"
        )
    raw = bytes(body)
    return {
        "content_bytes": raw,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "file_path": file_path,
        "file_size": len(raw),
    }


def _proof_attachment(message: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    document = message.get("document")
    if isinstance(document, Mapping):
        file_id = str(document.get("file_id") or "").strip()
        unique_id = str(document.get("file_unique_id") or "").strip()
        if not file_id or not unique_id:
            return None
        return {
            "kind": "document",
            "file_id": file_id,
            "file_unique_id": unique_id,
            "file_name": (
                str(document.get("file_name"))
                if document.get("file_name")
                else None
            ),
            "mime_type": (
                str(document.get("mime_type"))
                if document.get("mime_type")
                else None
            ),
            "file_size": document.get("file_size"),
        }

    photos = message.get("photo")
    if isinstance(photos, list) and photos:
        candidates = [row for row in photos if isinstance(row, Mapping)]
        if not candidates:
            return None

        def _score(row: Mapping[str, Any]) -> int:
            try:
                if row.get("file_size") is not None:
                    return int(row.get("file_size") or 0)
                return int(row.get("width") or 0) * int(row.get("height") or 0)
            except Exception:
                return 0

        selected = max(candidates, key=_score)
        file_id = str(selected.get("file_id") or "").strip()
        unique_id = str(selected.get("file_unique_id") or "").strip()
        if not file_id or not unique_id:
            return None
        return {
            "kind": "photo",
            "file_id": file_id,
            "file_unique_id": unique_id,
            "file_name": None,
            "mime_type": "image/jpeg",
            "file_size": selected.get("file_size"),
        }
    return None


def _admin_destination() -> tuple[Optional[int], Optional[int]]:
    raw_chat = os.getenv("ADMIN_CONTROL_CHAT_ID", "").strip()
    raw_thread = os.getenv("ADMIN_CONTROL_THREAD_ID", "").strip()
    try:
        chat_id = int(raw_chat) if raw_chat else None
    except Exception:
        chat_id = None
    try:
        thread_id = int(raw_thread) if raw_thread else None
    except Exception:
        thread_id = None
    return chat_id, thread_id


def _notify_admin_of_proof(
    *,
    case: Mapping[str, Any],
    proof: Mapping[str, Any],
    send_fn=telegram_publisher.send_message,
    now_ts: float | int | None,
    support_path: str | None,
) -> str:
    chat_id, thread_id = _admin_destination()
    result = "FAILED_ADMIN_DESTINATION_MISSING"
    error: str | None = None
    if chat_id is not None:
        subscriber_hash = hashlib.sha256(
            str(case["subscriber_ref"]).encode("utf-8")
        ).hexdigest()[:12]
        try:
            send_fn(
                chat_id=chat_id,
                thread_id=thread_id,
                text=(
                    f"Billing payment proof received\n"
                    f"Case: {case['case_id']}\n"
                    f"Subscriber ref: {subscriber_hash}\n"
                    f"SHA-256: {str(proof['proof_sha256'])[:16]}…\n"
                    f"File name: {proof.get('proof_file_name') or 'photo'}\n"
                    f"MIME: {proof.get('proof_mime_type') or 'unknown'}\n"
                    f"Size: {proof.get('proof_file_size')} bytes\n"
                    f"Payment intent linked: {'yes' if proof.get('payment_intent_id') else 'no'}"
                ),
                reply_markup=None,
            )
            result = "SENT"
        except Exception as exc:
            result = "FAILED"
            error = telegram_publisher._sanitize(str(exc))
    support_cases._record_delivery_event(
        case_id=str(case["case_id"]),
        direction="PROOF_TO_ADMIN",
        result=result,
        message_ref=str(proof["proof_id"]),
        error=error,
        now_ts=now_ts,
        path=support_path,
    )
    return result


def handle_private_proof_message(
    message: Mapping[str, Any],
    *,
    now_ts: float | int | None = None,
    support_path: str | None = None,
    notification_path: str | None = None,
    payment_path: str | None = None,
    request_get=requests.get,
    send_fn=telegram_publisher.send_message,
) -> Dict[str, Any]:
    attachment = _proof_attachment(message)
    if attachment is None:
        return {"handled": False, "reason": "NOT_PAYMENT_PROOF_ATTACHMENT"}
    context = _private_context(
        message,
        support_path=support_path,
        notification_path=notification_path,
    )
    if context is None:
        return {"handled": False, "reason": "NO_UNIQUE_SUPPORT_CONTEXT"}
    identity, case, _, _ = context
    downloaded = download_telegram_file_for_hash(
        file_id=str(attachment["file_id"]),
        request_get=request_get,
    )
    result = support_cases.add_payment_proof(
        case_id=str(case["case_id"]),
        subscriber_ref=identity["subscriber_ref"],
        payment_intent_id=(
            str(case["payment_intent_id"])
            if case.get("payment_intent_id")
            else None
        ),
        content_bytes=downloaded["content_bytes"],
        telegram_file_id=str(attachment["file_id"]),
        telegram_file_unique_id=str(attachment["file_unique_id"]),
        file_name=attachment.get("file_name"),
        mime_type=attachment.get("mime_type"),
        file_size=int(downloaded["file_size"]),
        caption=(
            str(message.get("caption"))
            if message.get("caption")
            else None
        ),
        now_ts=now_ts,
        path=support_path,
        payment_path=payment_path,
    )
    proof = result["record"]
    delivery = _notify_admin_of_proof(
        case=case,
        proof=proof,
        send_fn=send_fn,
        now_ts=now_ts,
        support_path=support_path,
    )
    # Drop the only in-memory reference to proof bytes before returning.
    downloaded.pop("content_bytes", None)
    return {
        "handled": True,
        "reason": "PAYMENT_PROOF_RECORDED",
        "case_id": case["case_id"],
        "proof_id": proof["proof_id"],
        "proof_sha256": proof["proof_sha256"],
        "delivery_result": delivery,
    }
