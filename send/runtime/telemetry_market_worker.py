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
from intelligence import shadow_gate_timebox_research as timebox_research
from runtime.observation_timing import LoopTimingEvidence


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
    last_timebox_update = None
    timebox_finished = False
    try:
        loop_timing=LoopTimingEvidence(poll_seconds)
    except Exception:
        loop_timing=None
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
        if loop_timing is not None:
            try:
                loop_timing.begin()
            except Exception:
                loop_timing=None
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
        try:
            from intelligence import owner_open_now_result
            owner_open_now_result.dispatch_async()
        except Exception as exc:
            _warn_once_per_window(
                warning_cache,
                "owner_open_now_result",
                now_ts=now,
                warn_type="OWNER_OPEN_NOW_RESULT_UNAVAILABLE",
                message="Private OPEN_NOW expiry report is unavailable",
                context={"error_class": type(exc).__name__},
            )
        # This experiment has separate storage and labels. It cannot register
        # canonical telemetry, supply execution calibration or publish a signal.
        try:
            from intelligence import owner_timing_session
            owner_timing_session.report_if_due(now_ts=float(clock()))
        except Exception as exc:
            _warn_once_per_window(
                warning_cache, "owner_timing_session", now_ts=float(clock()),
                warn_type="OWNER_TIMING_SESSION_REPORT_UNAVAILABLE",
                message="Private timing observation report could not be delivered",
                context={"error_class": type(exc).__name__},
            )
        if shadow_research.enabled():
            try:
                from core.physical_params import physical_runtime_enabled
                if physical_runtime_enabled():
                    from intelligence import physical_expiry_calibration
                    physical_expiry_calibration.advance(now_ts=float(clock()),
                        active_provider=market_client.configured_provider(),
                        price_loader=market_client.get_latest_price_sample,
                        observation_loader=market_client.get_price_sample_at_or_after)
            except Exception as exc:
                _warn_once_per_window(warning_cache, "physical_v3_expiry", now_ts=float(clock()),
                    warn_type="PHYSICAL_V3_CALIBRATION_UNAVAILABLE", message="Physical V3 quote observations unavailable",
                    context={"error_class": type(exc).__name__})
            try:
                from intelligence import lifecycle_cadence_research
                lifecycle_cadence_research.advance(now_ts=float(clock()),
                    active_provider=market_client.configured_provider(),price_loader=market_client.get_latest_price_sample)
            except Exception as exc:
                _warn_once_per_window(warning_cache,"lifecycle_cadence",now_ts=float(clock()),
                    warn_type="LIFECYCLE_CADENCE_UNAVAILABLE",message="Research cadence observations are unavailable",
                    context={"error_class":type(exc).__name__})
            try:
                from intelligence import execution_expiry_calibration
                execution_expiry_calibration.advance(
                    now_ts=float(clock()), active_provider=market_client.configured_provider(),
                    price_loader=market_client.get_latest_price_sample,
                )
            except Exception as exc:
                _warn_once_per_window(
                    warning_cache, "execution_expiry_calibration", now_ts=float(clock()),
                    warn_type="EXECUTION_EXPIRY_CALIBRATION_UNAVAILABLE",
                    message="Expiry calibration observations are unavailable; production gates are unchanged",
                    context={"error_class":type(exc).__name__},
                )
            try:
                from intelligence import live_score_severity_research
                live_score_severity_research.advance_paper_trades(
                    now_ts=float(clock()), active_provider=market_client.configured_provider(),
                    price_loader=market_client.get_latest_price_sample,
                )
            except Exception as exc:
                _warn_once_per_window(
                    warning_cache, "score_severity_paper", now_ts=float(clock()),
                    warn_type="SCORE_SEVERITY_PAPER_UNAVAILABLE",
                    message="Paper observation is unavailable; no outcome was invented",
                    context={"error_class": type(exc).__name__},
                )
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
        # The Owner's short test has a fixed wall-clock deadline, even with no
        # accepted OPEN, no source changes, a restart or an interrupted feed.
        timebox_now = float(clock())
        if timebox_research.enabled() and not timebox_finished and (
            last_timebox_update is None
            or timebox_now - last_timebox_update >= timebox_research.REPORT_INTERVAL_SECONDS
            or timebox_now >= timebox_research.DEADLINE
        ):
            try:
                short_report = timebox_research.update(
                    now_ts=timebox_now, price_loader=market_client.get_latest_price_sample,
                    active_provider=market_client.configured_provider(),
                )
                if short_report.get("status") != "BEFORE_REQUEST_WINDOW":
                    print("TSP_GATE_TIMEBOX_RESEARCH_EVIDENCE " + json.dumps({
                        "component": "shadow_gate_timebox_research", "observed_at": timebox_now,
                        "summary": timebox_research.evidence_summary(short_report),
                    }, sort_keys=True), flush=True)
                timebox_finished = short_report.get("status") in {"TIMEBOX_COMPLETE", "EXPIRED_BEFORE_ACTIVATION"}
                last_timebox_update = timebox_now
            except Exception as exc:
                _warn_once_per_window(
                    warning_cache, "gate_timebox", now_ts=timebox_now,
                    warn_type="SHADOW_GATE_TIMEBOX_UNAVAILABLE",
                    message="Fixed-window gate research is unavailable; no result was invented",
                    context={"error_class": type(exc).__name__},
                )
                if last_timebox_update is None or timebox_now - last_timebox_update >= 60:
                    print("TSP_GATE_TIMEBOX_UNAVAILABLE " + json.dumps({
                        "observed_at": timebox_now, "error_class": type(exc).__name__,
                    }, sort_keys=True), flush=True)
                    last_timebox_update = timebox_now
        if loop_timing is not None:
            try:
                evidence=loop_timing.finish(now_ts=float(clock()),provider=market_client.configured_provider())
                if evidence is not None:
                    print("TSP_TELEMETRY_LOOP_TIMING "+json.dumps(evidence,sort_keys=True,allow_nan=False),flush=True)
            except Exception:
                # Optional diagnostics cannot interrupt observation or sleep.
                loop_timing=None
        sleep(float(poll_seconds))
