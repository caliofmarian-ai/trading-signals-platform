# /opt/binarybot/runtime/distribution_scheduler.py
# BinaryBot — Background Scheduler (tier reset, maintenance)

from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from core import distribution_router
from core import observability_logger


LONDON_TZ = ZoneInfo("Europe/London")

CHECK_INTERVAL = 30

LAST_RESET_DATE = None


def scheduler_loop():

    global LAST_RESET_DATE

    while True:
        try:

            now = datetime.now(LONDON_TZ)

            if now.hour == 8 and now.minute >= 10:

                today = now.date()

                if LAST_RESET_DATE != today:

                    do_daily_reset()

                    LAST_RESET_DATE = today

            time.sleep(CHECK_INTERVAL)

        except Exception as e:

            observability_logger.log_error({
                "event_type": "error",
                "module": "distribution_scheduler",
                "error": str(e)
            })

            time.sleep(5)


def do_daily_reset():

    distribution_router.reset_daily_counters()

    observability_logger.log_event({
        "event_type": "tier_reset",
        "message": "Daily tier counters reset"
    })