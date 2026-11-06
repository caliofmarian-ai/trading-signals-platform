"""Opt-in standalone worker. Imports the existing engine inside an isolated process.

Never imports system_boot/engine_loop or starts any Telegram/broker worker.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
import shutil
import time
import traceback


class UtcMarketHttp:
    """Specify the timezone already assumed by the shared REST candle parser."""
    def __init__(self, delegate, history_url, budget=None):
        self.delegate, self.history_url, self.budget = delegate, history_url, budget

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def get(self, url, **kwargs):
        if url == self.history_url:
            kwargs["params"] = dict(kwargs.get("params") or {}, timezone="UTC")
            if self.budget is not None:
                from .provider_budget import FreeTierBudgetExceeded
                try:
                    self.budget.reserve()
                except FreeTierBudgetExceeded:
                    from runtime import market_client, runtime_status
                    runtime_status.update_status(market_data_state="MARKET_DATA_LIMITED",
                        market_data_rate_limit_state="APP_FREE_TIER_CAP_REACHED")
                    raise market_client.MarketDataRateLimitError("App free-tier request cap reached") from None
        return self.delegate.get(url, **kwargs)


def prepare_runtime(directory: Path):
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
        "OWNER_SIGNAL_DELIVERY_ENABLED":"0", "ALGO_PARAMS_PATH":str(config/"algo_params.json"),
    })
    for key in list(os.environ):
        if key.startswith("TELEGRAM_") or key.endswith("_CHAT_ID") or key.endswith("_THREAD_ID") or key.endswith("_CHANNEL_ID"):
            os.environ.pop(key,None)
    for subdir in ("state","observability","analytics","outcomes","runtime","research"):
        (engine/subdir).mkdir(exist_ok=True)
    catalog = json.loads((source/"active_symbols.json").read_text())
    known = {symbol for group in catalog.values() for symbol in group if isinstance(symbol, str)}
    symbols = list(dict.fromkeys(s.strip().upper() for s in os.getenv("SIGNALS_APP_SYMBOLS", "GBP/USD").split(",") if s.strip()))
    if len(symbols) != 1 or any(symbol not in known for symbol in symbols):
        raise ValueError("Select exactly one symbol from the existing market catalog.")
    selected = {group: [symbol for symbol in values if symbol in symbols] for group, values in catalog.items()}
    (config/"active_symbols.json").write_text(json.dumps(selected))
    # Deployment variables must never redirect this child's artifacts to another service's state.
    for key, name in {"ENGINE_EVENTS_LOG":"engine_events.jsonl", "DIST_EVENTS_LOG":"distribution_events.jsonl",
                      "FSM_EVENTS_LOG":"fsm_events.jsonl", "ERROR_EVENTS_LOG":"error_events.jsonl"}.items():
        os.environ[key] = str(engine/"observability"/name)
    os.environ["OUTCOMES_LOG"] = str(engine/"outcomes"/"outcomes.jsonl")
    return engine, symbols


def run(directory: Path):
    from .store import Store
    from .source import SourceMonitor
    store = Store(directory)
    monitor = SourceMonitor(store, [])
    try:
        engine, symbols = prepare_runtime(directory)
    except (ValueError, OSError):
        monitor.failure("INVALID_CONFIGURATION", configuration=True)
        return
    monitor = SourceMonitor(store, symbols)
    try:
        run_engine(monitor)
    except Exception as exc:
        monitor.failure("ENGINE_INITIALIZATION_FAILED")
        store.audit("ENGINE_INITIALIZATION_FAILED", "APP", type(exc).__name__)
        print("SIGNALS_APP_SOURCE " + json.dumps({"state":"SOURCE_UNAVAILABLE",
              "reason":"ENGINE_INITIALIZATION_FAILED", "error_class":type(exc).__name__}), flush=True)


def run_engine(monitor):
    store = monitor.store
    from . import canonical
    from .service import AppService
    from core import signal_engine
    from core import market_data_provider_control
    from runtime import market_client
    service = AppService(store)
    from .provider_budget import TwelveDataBudget
    market_client.requests = UtcMarketHttp(market_client.requests, market_client.BASE_URL,
                                         TwelveDataBudget(store))
    # The streaming feed's history bootstrap has a separate HTTP binding.
    # Route it through the same UTC adapter and durable free-tier ledger.
    from runtime.twelvedata_market_data import TwelveDataRealtimeFeed

    def app_twelve_data_feed(symbol):
        normalized = str(symbol).strip().upper().replace("_", "/")
        if normalized not in market_client._TWELVE_DATA_FEEDS:
            market_client._TWELVE_DATA_FEEDS[normalized] = TwelveDataRealtimeFeed(
                symbol=normalized, token=market_client._api_key(), http_get=market_client.requests.get)
        return market_client._TWELVE_DATA_FEEDS[normalized]

    market_client._twelve_data_feed = app_twelve_data_feed

    class AppRouter:
        @staticmethod
        def route(candidate, now_ts=None):
            return service.publish(candidate.to_dict(),
                provider=market_data_provider_control.get_active_provider(),now=now_ts)

    # The existing engine has an explicit router boundary. Only this child's
    # in-memory binding changes; no shared Python/config/canonical file changes.
    signal_engine.distribution_router = AppRouter
    decide = signal_engine.decide

    def observe_decision(**kwargs):
        try:
            result = decide(**kwargs)
        except Exception as exc:
            monitor.evaluation_failed = True
            frame = traceback.extract_tb(exc.__traceback__)[-1]
            # Pure strategy inputs contain candles/parameters, never source credentials.
            # Emit only the public code location and exception class, not values/messages.
            print("SIGNALS_APP_EVALUATION_ERROR " + json.dumps({"error_class":type(exc).__name__,
                  "module":Path(frame.filename).name, "line":frame.lineno}), flush=True)
            raise
        monitor.evaluation(result.decision)
        return result

    signal_engine.decide = observe_decision
    provider = market_data_provider_control.get_active_provider()
    ready, _reason = market_data_provider_control.provider_ready(provider)
    if not ready or provider != "TWELVE_DATA":
        monitor.failure("PROVIDER_NOT_CONFIGURED" if not ready else "PROVIDER_NOT_AUTHORIZED", configuration=True)
        print("SIGNALS_APP_SOURCE " + json.dumps({"state":monitor.data["state"],
              "reason":monitor.data["reason"]}), flush=True)
        return
    from runtime.runtime_status import status_path
    from core import storage
    last_state = None
    while True:
        try:
            signal_engine.run_once(int(time.time()))
            runtime = storage.load_json(status_path(), default={})
            monitor.cycle(runtime if isinstance(runtime, dict) else {},
                          signal_engine._LAST_CALIBRATION_STATE.values())
        except Exception as exc:
            # Never persist provider URLs, credentials, or exception messages.
            monitor.failure("ENGINE_CYCLE_FAILED")
            store.audit("ENGINE_CYCLE_ERROR","APP",type(exc).__name__)
        state = (monitor.data["state"], monitor.data["reason"])
        if state != last_state:
            print("SIGNALS_APP_SOURCE " + json.dumps({"state": state[0], "reason": state[1],
                  "provider": provider, "evaluations": monitor.data["evaluations"]}), flush=True)
            last_state = state
        time.sleep(2)
