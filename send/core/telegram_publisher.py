# /opt/binarybot/core/telegram_publisher.py
# BinaryBot — Telegram API Abstraction Layer

from __future__ import annotations
import os
import requests
from typing import Dict, Any, Optional

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(
    chat_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    thread_id: Optional[int] = None
) -> Dict[str, Any]:

    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    if thread_id:
        payload["message_thread_id"] = thread_id

    r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram send_message failed: {data}")

    return data


def edit_message(
    chat_id: int,
    message_id: int,
    text: Optional[str] = None,
    reply_markup: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:

    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id
    }

    if text:
        payload["text"] = text
        payload["parse_mode"] = "HTML"

    if reply_markup:
        payload["reply_markup"] = reply_markup

    r = requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram edit_message failed: {data}")

    return data


def send_document(
    chat_id: int,
    file_path: str,
    caption: Optional[str] = None,
    thread_id: Optional[int] = None
) -> Dict[str, Any]:

    with open(file_path, "rb") as f:

        files = {
            "document": f
        }

        data = {
            "chat_id": chat_id
        }

        if caption:
            data["caption"] = caption

        if thread_id:
            data["message_thread_id"] = thread_id

        r = requests.post(
            f"{BASE_URL}/sendDocument",
            data=data,
            files=files,
            timeout=20
        )

    result = r.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram send_document failed: {result}")

    return result