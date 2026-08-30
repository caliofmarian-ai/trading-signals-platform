import os
import requests
from datetime import datetime, timezone

from core import observability_logger
from runtime import runtime_status

BASE_URL = "https://api.twelvedata.com/time_series"
RATE_LIMIT_BACKOFF_SECONDS = 60
_RATE_LIMIT_STATE = {
    "active": False,
    "retry_after_ts": 0,
    "first_seen_ts": 0,
    "latest_seen_ts": 0,
    "count": 0,
}


class MarketDataRateLimitError(RuntimeError):
    pass


class MarketDataUnavailableError(RuntimeError):
    pass


_FINNHUB_FEED = None


def configured_provider() -> str:
    provider = os.getenv("MARKET_DATA_PROVIDER", "TWELVE_DATA").strip().upper()
    if provider not in {"TWELVE_DATA", "FINNHUB"}:
        raise RuntimeError(f"Unsupported MARKET_DATA_PROVIDER: {provider}")
    return provider


def configured_symbols():
    if configured_provider() == "FINNHUB":
        return ["EUR/USD"]
    return None


def _finnhub_feed():
    global _FINNHUB_FEED
    if _FINNHUB_FEED is None:
        from runtime.finnhub_market_data import FinnhubForexFeed

        _FINNHUB_FEED = FinnhubForexFeed()
    return _FINNHUB_FEED


def _api_key() -> str:
    token = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not token:
        raise RuntimeError("TWELVE_DATA_API_KEY missing")
    return token


def fetch_klines(symbol: str, interval: str, limit: int = 50):
    """
    Fetch candles from TwelveData API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": limit,
        "apikey": _api_key(),
    }

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if _RATE_LIMIT_STATE["active"] and now_ts < int(_RATE_LIMIT_STATE["retry_after_ts"]):
        _RATE_LIMIT_STATE["latest_seen_ts"] = now_ts
        _RATE_LIMIT_STATE["count"] = int(_RATE_LIMIT_STATE["count"]) + 1
        observability_logger.record_operational_incident(
            incident_type="TWELVE_DATA_HTTP_429",
            component="market_data",
            runtime_state="MARKET_DATA_LIMITED",
            operator_action="Wait for provider recovery; the runtime will resume automatically.",
            severity="WARNING",
            now_ts=now_ts,
        )
        runtime_status.update_status(
            market_data_state="MARKET_DATA_LIMITED",
            market_data_note="Twelve Data HTTP 429 active",
            market_data_retry_after_ts=int(_RATE_LIMIT_STATE["retry_after_ts"]),
            market_data_provider="TWELVE_DATA",
        )
        raise MarketDataRateLimitError("Twelve Data HTTP 429 backoff active")

    last_exc = None
    for attempt in range(3):
        try:
            r = requests.get(BASE_URL, params=params, timeout=20)
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if r.status_code == 429:
                if not _RATE_LIMIT_STATE["active"]:
                    _RATE_LIMIT_STATE["first_seen_ts"] = now_ts
                _RATE_LIMIT_STATE["active"] = True
                _RATE_LIMIT_STATE["latest_seen_ts"] = now_ts
                _RATE_LIMIT_STATE["count"] = int(_RATE_LIMIT_STATE["count"]) + 1
                _RATE_LIMIT_STATE["retry_after_ts"] = now_ts + RATE_LIMIT_BACKOFF_SECONDS
                runtime_status.update_status(
                    market_data_state="MARKET_DATA_LIMITED",
                    market_data_note="Twelve Data HTTP 429 active",
                    market_data_retry_after_ts=int(_RATE_LIMIT_STATE["retry_after_ts"]),
                    market_data_provider="TWELVE_DATA",
                )
                observability_logger.record_operational_incident(
                    incident_type="TWELVE_DATA_HTTP_429",
                    component="market_data",
                    runtime_state="MARKET_DATA_LIMITED",
                    operator_action="Wait for provider recovery; the runtime will resume automatically.",
                    severity="WARNING",
                    now_ts=now_ts,
                )
                raise MarketDataRateLimitError("Twelve Data HTTP 429")
            if r.status_code != 200:
                raise Exception(f"Market API error {r.status_code}: {r.text}")

            data = r.json()

            if "values" not in data:
                raise Exception(f"TwelveData error: {data}")

            if _RATE_LIMIT_STATE["active"]:
                observability_logger.clear_operational_incident(
                    incident_type="TWELVE_DATA_HTTP_429",
                    component="market_data",
                    runtime_state="READY",
                    operator_action="No operator action required.",
                    now_ts=now_ts,
                )
            _RATE_LIMIT_STATE.update({
                "active": False,
                "retry_after_ts": 0,
                "first_seen_ts": 0,
                "latest_seen_ts": 0,
                "count": 0,
            })
            runtime_status.update_status(
                market_data_state="READY",
                market_data_note="Market data available",
                market_data_retry_after_ts=None,
                market_data_provider="TWELVE_DATA",
                last_market_data_success_ts=now_ts,
            )

            return data["values"]

        except requests.exceptions.Timeout as e:
            last_exc = e
            if attempt == 2:
                raise Exception("TwelveData timeout after retries") from e

    if last_exc:
        raise last_exc

    raise Exception("Unknown market_client failure")


def get_candles(symbol: str, timeframe: str):
    """
    Provider-independent wrapper used by the engine.
    """
    if configured_provider() == "FINNHUB":
        feed = _finnhub_feed()
        try:
            candles = feed.get_candles(symbol, timeframe)
        except Exception as exc:
            health = feed.health()
            collecting = exc.__class__.__name__ == "FinnhubInsufficientHistory"
            runtime_status.update_status(
                market_data_state=(
                    "MARKET_DATA_COLLECTING" if collecting else "MARKET_DATA_UNAVAILABLE"
                ),
                market_data_note=str(exc),
                market_data_provider="FINNHUB",
                market_data_symbol=health["symbol"],
                last_market_data_success_ts=health["last_price_ts"],
                market_data_age_seconds=health["price_age_seconds"],
                market_data_freshness_limit_seconds=health["freshness_limit_seconds"],
                market_data_candle_counts=health["candle_counts"],
                market_data_minimum_candles=health["minimum_candles"],
                market_data_history_ready=health["history_ready"],
                market_data_persistence_state=health.get("persistence_state"),
                market_data_store_load_state=health.get("store_load_state"),
                market_data_store_write_state=health.get("store_write_state"),
                market_data_restored_candle_counts=health.get("restored_candle_counts"),
                market_data_last_persisted_ts=health.get("last_persisted_ts"),
            )
            raise MarketDataUnavailableError(str(exc)) from exc

        health = feed.health()
        counts = health["candle_counts"]
        runtime_status.update_status(
            market_data_state="READY",
            market_data_note=(
                "Finnhub live EUR/USD ready; "
                f"real candles M1={counts['M1']}, M5={counts['M5']}"
            ),
            market_data_provider="FINNHUB",
            market_data_symbol=health["symbol"],
            last_market_data_success_ts=health["last_price_ts"],
            market_data_age_seconds=health["price_age_seconds"],
            market_data_freshness_limit_seconds=health["freshness_limit_seconds"],
            market_data_candle_counts=health["candle_counts"],
            market_data_minimum_candles=health["minimum_candles"],
            market_data_history_ready=health["history_ready"],
            market_data_persistence_state=health.get("persistence_state"),
            market_data_store_load_state=health.get("store_load_state"),
            market_data_store_write_state=health.get("store_write_state"),
            market_data_restored_candle_counts=health.get("restored_candle_counts"),
            market_data_last_persisted_ts=health.get("last_persisted_ts"),
        )
        return candles

    raw = fetch_klines(symbol, timeframe)

    candles = []

    for k in raw:
        candles.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "ts": int(
                datetime.strptime(k["datetime"], "%Y-%m-%d %H:%M:%S")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            ),
            "open": float(k["open"]),
            "high": float(k["high"]),
            "low": float(k["low"]),
            "close": float(k["close"]),
            "volume": 0,
        })

    candles.reverse()
    return candles
