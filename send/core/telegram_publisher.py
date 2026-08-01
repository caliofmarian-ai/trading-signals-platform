# /opt/binarybot/core/telegram_publisher.py
# BinaryBot — Telegram API Abstraction Layer

from __future__ import annotations
import os
import re
import requests
from typing import Dict, Any, Optional


def _get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    return token


def _base_url() -> str:
    return f"https://api.telegram.org/bot{_get_bot_token()}"


# Regex that matches the bot-token segment inside a Telegram API URL so it can
# be redacted from any string before it reaches a log sink or exception message.
_TOKEN_PATTERN = re.compile(r"(?<=/bot)\d+:[A-Za-z0-9_-]+")


def _sanitize(s: str) -> str:
    """Replace any bot-token substring in *s* with a safe placeholder."""
    return _TOKEN_PATTERN.sub("[REDACTED]", s)


def _safe_api_error(data: Dict[str, Any]) -> str:
    """Return a log-safe summary of a Telegram API error response."""
    error_code = data.get("error_code", "?")
    description = data.get("description", "no description")
    return f"code={error_code} description={description!r}"


def send_message(
    chat_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:

    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    if thread_id:
        payload["message_thread_id"] = thread_id

    r = requests.post(f"{_base_url()}/sendMessage", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram send_message failed: {_safe_api_error(data)}")

    return data


def edit_message(
    chat_id: int,
    message_id: int,
    text: Optional[str] = None,
    reply_markup: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Edit an existing Telegram message.

    parse_mode is intentionally omitted so that both edit_message and
    send_message use the same rendering mode (plain text).  Setting HTML mode
    here while send_message uses no mode caused Telegram to reject edits
    whenever the text contained HTML-special characters such as the ``<value>``
    and ``<dir>`` placeholders present in admin command-help strings, producing
    a 400 parse-entities error that was mis-classified as an unexpected failure
    and silently fell through to send_message, violating the single-message
    contract.
    """
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
    }

    if text:
        payload["text"] = text

    if reply_markup:
        payload["reply_markup"] = reply_markup

    r = requests.post(f"{_base_url()}/editMessageText", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram edit_message failed: {_safe_api_error(data)}")

    return data


def answer_callback_query(
    callback_query_id: str,
    text: str = "",
    show_alert: bool = False,
) -> Dict[str, Any]:
    """Acknowledge a Telegram callback query to dismiss the loading spinner."""
    payload: Dict[str, Any] = {
        "callback_query_id": callback_query_id,
        "show_alert": show_alert,
    }
    if text:
        payload["text"] = text

    r = requests.post(f"{_base_url()}/answerCallbackQuery", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram answer_callback_query failed: {_safe_api_error(data)}")

    return data


def send_document(
    chat_id: int,
    file_path: str,
    caption: Optional[str] = None,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:

    with open(file_path, "rb") as f:

        files = {
            "document": f,
        }

        data: Dict[str, Any] = {
            "chat_id": chat_id,
        }

        if caption:
            data["caption"] = caption

        if thread_id:
            data["message_thread_id"] = thread_id

        r = requests.post(
            f"{_base_url()}/sendDocument",
            data=data,
            files=files,
            timeout=20,
        )

    result = r.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram send_document failed: {_safe_api_error(result)}")

    return result