import os
import time
from datetime import datetime, timezone

import requests

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
_TWELVE_DATA_FEED = None
_TWELVE_DATA_REST_CACHE = {}


def configured_provider() -> str:
    provider = os.getenv("MARKET_DATA_PROVIDER", "TWELVE_DATA").strip().upper()
    if provider not in {"TWELVE_DATA", "FINNHUB"}:
        raise RuntimeError(f"Unsupported MARKET_DATA_PROVIDER: {provider}")
    return provider


def _twelve_data_streaming_enabled() -> bool:
    value = os.getenv("TWELVE_DATA_STREAMING_ENABLED", "1").strip().lower()
    return value not in {"0", "false", "off", "no"}


def _twelve_data_stream_symbol() -> str:
    value = os.getenv("TWELVE_DATA_STREAM_SYMBOL", "EUR/USD").strip().upper().replace("_", "/")
    if not value or "/" not in value:
        raise RuntimeError(f"Invalid TWELVE_DATA_STREAM_SYMBOL: {value!r}")
    return value


def configured_symbols():
    provider = configured_provider()
    if provider == "FINNHUB":
        return ["EUR/USD"]
    if provider == "TWELVE_DATA" and _twelve_data_streaming_enabled():
        return [_twelve_data_stream_symbol()]
    return None


def _finnhub_feed():
    global _FINNHUB_FEED
    if _FINNHUB_FEED is None:
        from runtime.finnhub_market_data import FinnhubForexFeed

        _FINNHUB_FEED = FinnhubForexFeed()
    return _FINNHUB_FEED


def _twelve_data_feed():
    global _TWELVE_DATA_FEED
    if _TWELVE_DATA_FEED is None:
        from runtime.twelvedata_market_data import TwelveDataRealtimeFeed

        _TWELVE_DATA_FEED = TwelveDataRealtimeFeed(
            symbol=_twelve_data_stream_symbol(),
            token=_api_key(),
        )
    return _TWELVE_DATA_FEED


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


def _normalize_twelve_data_rows(symbol: str, timeframe: str, raw):
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
            "volume": float(k.get("volume") or 0),
        })
    candles.reverse()
    return candles


def _cached_rest_candles(symbol: str, timeframe: str):
    ttl = max(1, int(os.getenv("TWELVE_DATA_REST_CACHE_SECONDS", "55")))
    key = (str(symbol).strip().upper(), str(timeframe).strip().lower())
    now_ts = int(time.time())
    cached = _TWELVE_DATA_REST_CACHE.get(key)
    if cached and now_ts - int(cached["fetched_ts"]) < ttl:
        return [dict(row) for row in cached["candles"]]

    raw = fetch_klines(symbol, timeframe, limit=205)
    candles = _normalize_twelve_data_rows(symbol, timeframe, raw)
    _TWELVE_DATA_REST_CACHE[key] = {
        "fetched_ts": now_ts,
        "candles": [dict(row) for row in candles],
    }
    return candles


def _update_twelve_data_stream_status(feed, *, state: str, note: str) -> None:
    health = feed.health()
    runtime_status.update_status(
        market_data_state=state,
        market_data_note=note,
        market_data_provider="TWELVE_DATA",
        market_data_symbol=health["symbol"],
        last_market_data_success_ts=health["last_price_ts"],
        market_data_age_seconds=health["price_age_seconds"],
        market_data_freshness_limit_seconds=health["freshness_limit_seconds"],
        market_data_candle_counts=health["candle_counts"],
        market_data_minimum_candles=health["minimum_candles"],
        market_data_history_ready=health["history_ready"],
        market_data_store_load_state=health.get("store_load_state"),
        market_data_store_write_state=health.get("store_write_state"),
        market_data_restored_candle_counts=health.get("restored_candle_counts"),
        market_data_last_persisted_ts=health.get("last_persisted_ts"),
        market_data_stream_state=health.get("stream_state"),
        market_data_bootstrap_state=health.get("bootstrap_state"),
    )


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
                market_data_integrity_state=health.get("integrity_state"),
                market_data_integrity_report=health.get("integrity_report"),
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
            market_data_integrity_state=health.get("integrity_state"),
            market_data_integrity_report=health.get("integrity_report"),
        )
        return candles

    if _twelve_data_streaming_enabled():
        from runtime.twelvedata_market_data import (
            TwelveDataInsufficientHistory,
            TwelveDataMarketDataUnavailable,
            TwelveDataRateLimitError,
            TwelveDataStreamingUnavailable,
        )

        feed = _twelve_data_feed()
        try:
            candles = feed.get_candles(timeframe)
        except TwelveDataRateLimitError as exc:
            now_ts = int(time.time())
            runtime_status.update_status(
                market_data_state="MARKET_DATA_LIMITED",
                market_data_note=str(exc),
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
            raise MarketDataRateLimitError(str(exc)) from exc
        except TwelveDataStreamingUnavailable as exc:
            candles = _cached_rest_candles(symbol, timeframe)
            runtime_status.update_status(
                market_data_state="READY",
                market_data_note=(
                    "Twelve Data WebSocket unavailable; bounded REST cache fallback active: "
                    f"{exc}"
                ),
                market_data_provider="TWELVE_DATA",
                market_data_symbol=str(symbol).strip().upper(),
                market_data_history_ready=True,
                market_data_stream_state="REST_FALLBACK",
            )
            return candles
        except TwelveDataInsufficientHistory as exc:
            _update_twelve_data_stream_status(
                feed, state="MARKET_DATA_COLLECTING", note=str(exc)
            )
            raise MarketDataUnavailableError(str(exc)) from exc
        except TwelveDataMarketDataUnavailable as exc:
            _update_twelve_data_stream_status(
                feed, state="MARKET_DATA_UNAVAILABLE", note=str(exc)
            )
            raise MarketDataUnavailableError(str(exc)) from exc

        health = feed.health()
        counts = health["candle_counts"]
        _update_twelve_data_stream_status(
            feed,
            state="READY",
            note=(
                f"Twelve Data live {health['symbol']} ready; "
                f"real candles M1={counts['M1']}, M5={counts['M5']}"
            ),
        )
        return candles

    return _cached_rest_candles(symbol, timeframe)
