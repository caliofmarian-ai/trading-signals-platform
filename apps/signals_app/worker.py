"""Opt-in standalone worker. Imports the existing engine inside an isolated process.

Never imports system_boot/engine_loop or starts any Telegram/broker worker.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import time


def run(directory: Path):
    from .store import Store
    directory = directory.resolve()
    engine = directory / "engine"
    config = engine / "config"
    config.mkdir(parents=True, exist_ok=True)
    # Set all paths BEFORE importing the shared engine and its module-level paths.
    source = Path(__file__).resolve().parents[2] / "send" / "config"
    for path in source.glob("*.json"):
        target = config / path.name
        if not target.exists():
            shutil.copyfile(path,target)
    os.environ.update({
        "BINARYBOT_BASE_DIR":str(engine), "OBS_DIR":str(engine/"observability"),
        "ANALYTICS_DIR":str(engine/"analytics"), "ENABLE_TELEGRAM":"0",
        "ENABLE_BROKER_EXECUTION":"0", "SHADOW_MODE":"1",
    })
    for key in list(os.environ):
        if key.startswith("TELEGRAM_") or key.endswith("_CHAT_ID") or key.endswith("_THREAD_ID") or key.endswith("_CHANNEL_ID"):
            os.environ.pop(key,None)
    for subdir in ("state","observability","analytics","outcomes","runtime","research"):
        (engine/subdir).mkdir(exist_ok=True)
    from . import canonical
    from .service import AppService
    from core import signal_engine
    from core import market_data_provider_control
    store = Store(directory)
    service = AppService(store)

    class AppRouter:
        @staticmethod
        def route(candidate, now_ts=None):
            return service.publish(candidate.to_dict(),
                provider=market_data_provider_control.get_active_provider(),now=now_ts)

    # The existing engine has an explicit router boundary. Only this child's
    # in-memory binding changes; no shared Python/config/canonical file changes.
    signal_engine.distribution_router = AppRouter
    provider = market_data_provider_control.get_active_provider()
    ready, _reason = market_data_provider_control.provider_ready(provider)
    if not ready or provider != "TWELVE_DATA":
        store.set_meta("engine_state","PROVIDER_CONFIGURATION_REQUIRED")
        return
    store.set_meta("engine_state","OBSERVING")
    while True:
        try:
            signal_engine.run_once(int(time.time()))
            store.set_meta("last_engine_tick",int(time.time()))
        except Exception as exc:
            # Never persist provider URLs, credentials, or exception messages.
            store.set_meta("engine_state","EVIDENCE_UNAVAILABLE")
            store.audit("ENGINE_CYCLE_ERROR","APP",type(exc).__name__)
        time.sleep(2)
