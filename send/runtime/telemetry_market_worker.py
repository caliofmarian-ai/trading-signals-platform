from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from core import observability_logger
from core import trade_temporal_telemetry
from runtime import market_client


TELEMETRY_POLL_SECONDS = 1.0
_WARNING_REMINDER_SECONDS = 60


def _warn_once_per_window(
    cache: Dict[str, float],
    key: str,
    *,
    now_ts: float,
    warn_type: str,
    message: str,
    context: Dict[str, Any],
) -> None:
    last = float(cache.get(key, 0.0))
    if now_ts - last < _WARNING_REMINDER_SECONDS:
        return
    cache[key] = now_ts
    observability_logger.log_warning(
        warn_type=warn_type,
        message=message,
        context=context,
        source={"module": "telemetry_market_worker", "function": "telemetry_market_loop"},
    )


def run_telemetry_cycle(
    *,
    now_ts: Optional[float] = None,
    price_loader: Callable[[str], Dict[str, Any]] = market_client.get_latest_price_sample,
) -> Dict[str, Any]:
    """Process one objective telemetry sampling cycle.

    Only the currently governed provider may contribute a market sample. A
    pending trade registered under another provider is left untouched rather
    than silently mixed with the active feed.
    """

    resolved_now = float(now_ts if now_ts is not None else time.time())
    active_provider = market_client.configured_provider().strip().upper()
    requests = trade_temporal_telemetry.pending_market_requests()
    processed = 0
    updated = 0
    finalized = 0
    skipped_provider_mismatch = 0
    unavailable = []

    for request in requests:
        provider = str(request.get("provider") or "").strip().upper()
        symbol = str(request.get("symbol") or "").strip()
        if not provider or not symbol:
            continue
        if provider != active_provider:
            skipped_provider_mismatch += 1
            continue
        processed += 1
        try:
            sample = price_loader(symbol)
            sample_provider = str(sample.get("provider") or "").strip().upper()
            if sample_provider != provider:
                raise RuntimeError(
                    f"telemetry provider mismatch: expected={provider}, observed={sample_provider or 'EMPTY'}"
                )
            result = trade_temporal_telemetry.observe_market_sample(
                sample,
                now_ts=int(resolved_now),
            )
            updated += int(result.get("updated_trade_count") or 0)
            finalized += int(result.get("finalized_trade_count") or 0)
        except Exception as exc:
            unavailable.append({"provider": provider, "symbol": symbol, "error": str(exc)})

    return {
        "active_provider": active_provider,
        "pending_request_count": len(requests),
        "processed_request_count": processed,
        "updated_trade_count": updated,
        "finalized_trade_count": finalized,
        "skipped_provider_mismatch_count": skipped_provider_mismatch,
        "unavailable": unavailable,
    }


def telemetry_market_loop(
    *,
    poll_seconds: float = TELEMETRY_POLL_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
) -> None:
    """Continuously capture real post-OPEN_NOW market observations."""

    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")

    warning_cache: Dict[str, float] = {}
    try:
        recovery = trade_temporal_telemetry.recover_after_restart(int(clock()))
        if recovery.get("evidence_gap_count"):
            observability_logger.log_warning(
                warn_type="TRADE_TEMPORAL_TELEMETRY_RESTART_GAPS",
                message="Restart recovery preserved missed telemetry checkpoints as explicit evidence gaps",
                context=recovery,
                source={"module": "telemetry_market_worker", "function": "telemetry_market_loop"},
            )
    except Exception as exc:
        observability_logger.log_warning(
            warn_type="TRADE_TEMPORAL_TELEMETRY_RECOVERY_FAILED",
            message="Objective telemetry restart recovery failed; worker remains fail-closed",
            context={"error": str(exc)},
            source={"module": "telemetry_market_worker", "function": "telemetry_market_loop"},
        )

    while True:
        now = float(clock())
        try:
            result = run_telemetry_cycle(now_ts=now)
            if result.get("skipped_provider_mismatch_count"):
                _warn_once_per_window(
                    warning_cache,
                    "provider_mismatch",
                    now_ts=now,
                    warn_type="TRADE_TEMPORAL_TELEMETRY_PROVIDER_MISMATCH",
                    message="Pending telemetry is bound to a different provider; cross-provider sampling is blocked",
                    context={
                        "active_provider": result.get("active_provider"),
                        "skipped_count": result.get("skipped_provider_mismatch_count"),
                    },
                )
            for item in result.get("unavailable") or []:
                key = f"unavailable:{item.get('provider')}:{item.get('symbol')}"
                _warn_once_per_window(
                    warning_cache,
                    key,
                    now_ts=now,
                    warn_type="TRADE_TEMPORAL_TELEMETRY_MARKET_SAMPLE_UNAVAILABLE",
                    message="Objective telemetry could not obtain a current real market observation",
                    context=dict(item),
                )
        except Exception as exc:
            _warn_once_per_window(
                warning_cache,
                "worker_cycle",
                now_ts=now,
                warn_type="TRADE_TEMPORAL_TELEMETRY_WORKER_FAILED",
                message="Objective telemetry worker cycle failed closed",
                context={"error": str(exc)},
            )
        sleep(float(poll_seconds))
