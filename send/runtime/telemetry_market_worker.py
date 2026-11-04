from __future__ import annotations

import time
import json
from typing import Any, Callable, Dict, Optional

from core import observability_logger
from core import trade_temporal_telemetry
from runtime import market_client
from runtime import runtime_status
from intelligence import shadow_model_time_research as shadow_research
from intelligence import shadow_gate_sweep_research as gate_research


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

    Only the currently governed provider may contribute a market sample. When a
    checkpoint becomes due while a different provider is active, that checkpoint
    becomes an explicit evidence gap rather than being backfilled later or mixed.
    """

    resolved_now = float(now_ts if now_ts is not None else time.time())
    active_provider = market_client.configured_provider().strip().upper()
    provider_gap_result = trade_temporal_telemetry.mark_due_provider_mismatch(
        active_provider,
        now_ts=int(resolved_now),
    )
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
        "provider_evidence_gap_count": int(provider_gap_result.get("evidence_gap_count") or 0),
        "provider_gap_finalized_count": int(provider_gap_result.get("finalized_incomplete_count") or 0),
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
    pending_research_status = None
    refresh_gate_research = True
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
        # This experiment has separate storage and labels. It cannot register
        # canonical telemetry, supply execution calibration or publish a signal.
        if shadow_research.enabled():
            try:
                research_result = shadow_research.run_cycle(
                    active_provider=market_client.configured_provider(),
                    now_ts=float(clock()), price_loader=market_client.get_latest_price_sample,
                )
                if research_result.get("changed"):
                    refresh_gate_research = True
                    research_summary = shadow_research.summary()
                    pending_research_status = (research_summary, float(clock()))
                if pending_research_status is not None:
                    research_summary, observed_at = pending_research_status
                    shadow_research.persist_summary_status(research_summary, observed_at=observed_at)
                    runtime_status.update_status(shadow_model_time_research=research_summary)
                    print("TSP_SHADOW_RESEARCH_EVIDENCE " + json.dumps({
                        "component": "shadow_model_time_research", "observed_at": observed_at,
                        "summary": research_summary,
                    }, sort_keys=True), flush=True)
                    pending_research_status = None
            except Exception as exc:
                _warn_once_per_window(
                    warning_cache, "shadow_research", now_ts=float(clock()),
                    warn_type="SHADOW_RESEARCH_UNAVAILABLE",
                    message="Private research failed closed; no market outcome was invented",
                    context={"error_class": type(exc).__name__},
                )
        # A passive research ledger; no gate value is returned to strategy/FSM.
        # Retain the refresh request on failure, independently of source status.
        if gate_research.enabled() and refresh_gate_research:
            try:
                gate_summary = gate_research.update(now_ts=float(clock()))
                print("TSP_GATE_SWEEP_RESEARCH_EVIDENCE " + json.dumps({
                    "component": "shadow_gate_sweep_research", "observed_at": float(clock()),
                    "summary": gate_research.evidence_summary(gate_summary),
                }, sort_keys=True), flush=True)
                refresh_gate_research = False
            except Exception as exc:
                _warn_once_per_window(
                    warning_cache, "gate_research", now_ts=float(clock()),
                    warn_type="SHADOW_GATE_SWEEP_UNAVAILABLE",
                    message="Private gate research is unavailable; its ledger will be retried",
                    context={"error_class": type(exc).__name__},
                )
        sleep(float(poll_seconds))
