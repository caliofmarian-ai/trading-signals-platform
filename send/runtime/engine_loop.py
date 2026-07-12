import time
import traceback

from core.signal_engine import run_once
from core.observability_logger import log_event, log_error


ENGINE_TICK_SECONDS = 2


def start_engine():
    log_event({
        "event_type": "engine_start",
        "message": "BinaryBot engine loop started"
    })

    while True:
        try:
            now_ts = int(time.time())

            run_once(now_ts)

        except Exception as e:
            log_error({
                "event_type": "error",
                "module": "engine_loop",
                "error": str(e),
                "trace": traceback.format_exc()
            })

        time.sleep(ENGINE_TICK_SECONDS)