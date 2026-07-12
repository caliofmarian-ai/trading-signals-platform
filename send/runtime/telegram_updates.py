# /opt/binarybot/runtime/telegram_updates.py
# BinaryBot — Telegram Updates Poller

from __future__ import annotations

import os
import time
import requests
from typing import Dict, Any

from core import bot_service
from core import outcome_service
from core import observability_logger


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

POLL_INTERVAL = 1.5

LAST_UPDATE_ID = None


def poll_updates():
    global LAST_UPDATE_ID

    while True:
        try:
            params = {
                "timeout": 30
            }

            if LAST_UPDATE_ID:
                params["offset"] = LAST_UPDATE_ID

            r = requests.get(
                f"{BASE_URL}/getUpdates",
                params=params,
                timeout=35
            )

            data = r.json()

            if not data.get("ok"):
                time.sleep(POLL_INTERVAL)
                continue

            updates = data.get("result", [])

            for update in updates:

                LAST_UPDATE_ID = update["update_id"] + 1

                process_update(update)

        except Exception as e:

            observability_logger.log_error({
                "event_type": "error",
                "module": "telegram_updates",
                "error": str(e)
            })

            time.sleep(3)


def process_update(update: Dict[str, Any]):

    # message
    if "message" in update:
        bot_service.process_update(update)
        return

    # callback button
    if "callback_query" in update:

        cb = update["callback_query"]

        data = cb.get("data")
        user_id = cb["from"]["id"]

        if data and data.startswith("VOTE_"):

            parts = data.split("|")

            if len(parts) == 3:
                signal_id = parts[1]
                outcome = parts[2]

                outcome_service.handle_vote_callback(
                    user_id=user_id,
                    signal_id=signal_id,
                    outcome=outcome,
                    now_ts=int(time.time())
                )

        bot_service.process_update(update)