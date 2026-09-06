import time
import traceback

from core import distribution_router_primary_v3
from core import signal_engine
from core.observability_logger import log_event, log_error


# R-021: the active runtime binds Signal Engine distribution to the primary-v3
# boundary.  The underlying v3 mechanics remain unchanged; only fresh legacy
# distribution event writes are excluded from the live path.
signal_engine.distribution_router = distribution_router_primary_v3
run_once = signal_engine.run_once


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
