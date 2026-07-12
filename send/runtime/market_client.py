import os
import requests
from datetime import datetime, timezone

BASE_URL = "https://api.twelvedata.com/time_series"
API_KEY = os.getenv("TWELVE_DATA_API_KEY")


def fetch_klines(symbol: str, interval: str, limit: int = 50):
    """
    Fetch candles from TwelveData API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": limit,
        "apikey": API_KEY,
    }

    last_exc = None
    for attempt in range(3):
        try:
            r = requests.get(BASE_URL, params=params, timeout=20)
            if r.status_code != 200:
                raise Exception(f"Market API error {r.status_code}: {r.text}")

            data = r.json()

            if "values" not in data:
                raise Exception(f"TwelveData error: {data}")

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
    Wrapper used by engine.
    """
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
