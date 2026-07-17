from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class TelegramTarget:
    chat_id: int
    thread_id: Optional[int] = None


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def env_chat_id(name: str) -> Optional[int]:
    return _safe_int(os.getenv(name, "").strip())


def env_thread_id(name: str) -> Optional[int]:
    return _safe_int(os.getenv(name, "").strip())


def valid_thread_id(chat_id: int, thread_id: Optional[int]) -> Optional[int]:
    if thread_id is None or thread_id <= 0:
        return None
    if chat_id >= 0:
        return None
    return thread_id


def control_target() -> Optional[TelegramTarget]:
    chat_id = env_chat_id("ADMIN_CONTROL_CHAT_ID")
    if chat_id is None:
        return None
    return TelegramTarget(chat_id=chat_id, thread_id=valid_thread_id(chat_id, env_thread_id("ADMIN_CONTROL_THREAD_ID")))


def proof_target() -> Optional[TelegramTarget]:
    chat_id = env_chat_id("ADMIN_PROOF_CHAT_ID")
    if chat_id is None:
        return None
    return TelegramTarget(chat_id=chat_id, thread_id=valid_thread_id(chat_id, env_thread_id("ADMIN_PROOF_THREAD_ID")))


def alerts_target() -> Optional[TelegramTarget]:
    """
    Optional routing target for admin alert messages.

    Uses ADMIN_ALERTS_THREAD_ID if set, otherwise falls back to the
    configured Admin Control target.  Returns None only if ADMIN_CONTROL_CHAT_ID
    is not configured.
    """
    base = control_target()
    if base is None:
        return None
    thread_id = env_thread_id("ADMIN_ALERTS_THREAD_ID")
    if thread_id is not None:
        return TelegramTarget(chat_id=base.chat_id, thread_id=valid_thread_id(base.chat_id, thread_id))
    return base


def errors_target() -> Optional[TelegramTarget]:
    """
    Optional routing target for admin error messages.

    Uses ADMIN_ERRORS_THREAD_ID if set, otherwise falls back to the
    configured Admin Control target.
    """
    base = control_target()
    if base is None:
        return None
    thread_id = env_thread_id("ADMIN_ERRORS_THREAD_ID")
    if thread_id is not None:
        return TelegramTarget(chat_id=base.chat_id, thread_id=valid_thread_id(base.chat_id, thread_id))
    return base


def reports_target() -> Optional[TelegramTarget]:
    """
    Optional routing target for admin report messages.

    Uses ADMIN_REPORTS_THREAD_ID if set, otherwise falls back to the
    configured Admin Proof target (then Admin Control target).
    """
    thread_id = env_thread_id("ADMIN_REPORTS_THREAD_ID")
    base = proof_target() or control_target()
    if base is None:
        return None
    if thread_id is not None:
        return TelegramTarget(chat_id=base.chat_id, thread_id=valid_thread_id(base.chat_id, thread_id))
    return base


def reply_target_from_message(message: dict[str, Any]) -> Optional[TelegramTarget]:
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = _safe_int(chat.get("id"))
    if chat_id is None:
        return None
    thread_id = valid_thread_id(chat_id, _safe_int(message.get("message_thread_id")))
    return TelegramTarget(chat_id=chat_id, thread_id=thread_id)
