from __future__ import annotations

import hashlib
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


def _latest_bindings(notification_path: str | None = None) -> Dict[tuple[str, str], Dict[str, Any]]:
    latest: Dict[tuple[str, str], Dict[str, Any]] = {}
    for row in notification_scheduler.load_events(notification_path):
        if row.get("event_type") != notification_scheduler.EVENT_TARGET_BOUND:
            continue
        key = (str(row.get("subscriber_ref")), str(row.get("strategy_product_id")))
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
        for (subscriber, product), row in _latest_bindings(notification_path).items()
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


def handle_private_text_message(
    message: Mapping[str, Any],
    *,
    now_ts: float | int | None = None,
    support_path: str | None = None,
    notification_path: str | None = None,
) -> Dict[str, Any]:
    chat = message.get("chat")
    sender = message.get("from")
    if not isinstance(chat, Mapping) or not isinstance(sender, Mapping):
        return {"handled": False, "reason": "MISSING_IDENTITY"}
    if str(chat.get("type") or "") != "private":
        return {"handled": False, "reason": "NOT_PRIVATE_CHAT"}
    text = message.get("text")
    if not isinstance(text, str) or not text.strip() or text.lstrip().startswith("/"):
        return {"handled": False, "reason": "NOT_SUPPORT_TEXT"}
    try:
        user_id = _positive_id(sender.get("id"), label="from.id")
        chat_id = _positive_id(chat.get("id"), label="chat.id")
    except SupportRuntimeError:
        return {"handled": False, "reason": "INVALID_IDENTITY"}
    identity = resolve_private_subscriber(
        telegram_user_id=user_id,
        telegram_chat_id=chat_id,
        notification_path=notification_path,
    )
    if identity is None:
        return {"handled": False, "reason": "NO_UNIQUE_SUBSCRIBER_BINDING"}
    case = _active_case_for_identity(
        subscriber_ref=identity["subscriber_ref"],
        strategy_product_id=identity["strategy_product_id"],
        support_path=support_path,
    )
    if case is None:
        return {"handled": False, "reason": "NO_UNIQUE_ACTIVE_SUPPORT_CASE"}
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


def _telegram_get_file(file_id: str, *, request_get=requests.get) -> Dict[str, Any]:
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
            raise SupportRuntimeError("Telegram proof exceeds 20 MB download boundary")
    file_path = result.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        raise SupportRuntimeError("Telegram getFile response is missing file_path")
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
                raise SupportRuntimeError("Telegram proof exceeds 20 MB download boundary")
        except ValueError:
            pass
    body = bytearray()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        body.extend(chunk)
        if len(body) > MAX_PROOF_BYTES:
            raise SupportRuntimeError("Telegram proof exceeds 20 MB download boundary")
    if not body:
        raise SupportRuntimeError("Telegram proof download returned no bytes")
    raw = bytes(body)
    return {
        "content_bytes": raw,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "file_path": file_path,
        "file_size": len(raw),
    }
