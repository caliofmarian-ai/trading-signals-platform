from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from typing import Any, Dict, Optional

from billing import membership_reconciler
from core import observability_logger

DEFAULT_SCAN_INTERVAL_SECONDS = 5 * 60
MIN_SCAN_INTERVAL_SECONDS = 60
MAX_SCAN_INTERVAL_SECONDS = 60 * 60
_LAST_SCAN_MONOTONIC = 0.0


class MembershipSchedulerError(RuntimeError):
    """Raised when membership runtime orchestration is configured unsafely."""


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def dry_run_enabled() -> bool:
    return _env_flag("BILLING_MEMBERSHIP_RECONCILER_DRY_RUN_ENABLED", False)


def scan_interval_seconds() -> int:
    raw = os.getenv(
        "BILLING_MEMBERSHIP_RECONCILER_SCAN_INTERVAL_SECONDS",
        str(DEFAULT_SCAN_INTERVAL_SECONDS),
    )
    try:
        value = int(str(raw).strip())
    except Exception as exc:
        raise MembershipSchedulerError(
            "BILLING_MEMBERSHIP_RECONCILER_SCAN_INTERVAL_SECONDS must be an integer"
        ) from exc
    if value < MIN_SCAN_INTERVAL_SECONDS or value > MAX_SCAN_INTERVAL_SECONDS:
        raise MembershipSchedulerError(
            "BILLING_MEMBERSHIP_RECONCILER_SCAN_INTERVAL_SECONDS must be "
            f"between {MIN_SCAN_INTERVAL_SECONDS} and {MAX_SCAN_INTERVAL_SECONDS}"
        )
    return value


def runtime_mode() -> str:
    if membership_reconciler.automatic_reconciliation_enabled():
        return "APPLY"
    if dry_run_enabled():
        return "DRY_RUN"
    return "DISABLED"


def _summary(results: list[Dict[str, Any]], *, mode: str) -> Dict[str, Any]:
    states = Counter(str(row.get("state") or "UNKNOWN") for row in results)
    batch_errors = sum(1 for row in results if row.get("batch_error") is True)
    actions_applied = sum(1 for row in results if row.get("actions_applied") is True)
    return {
        "event": "billing_membership_reconciliation_cycle",
        "status": "COMPLETED",
        "mode": mode,
        "subscriber_count": len(results),
        "state_counts": dict(sorted(states.items())),
        "batch_error_count": batch_errors,
        "actions_applied_count": actions_applied,
        "access_leak_risk_count": int(states.get("ACCESS_LEAK_RISK", 0)),
    }


def _emit_summary(summary: Dict[str, Any]) -> None:
    # Aggregate only: never emit subscriber refs, Telegram IDs or channel IDs.
    try:
        print(json.dumps(summary, sort_keys=True), file=sys.stdout, flush=True)
    except Exception:
        pass

    critical = int(summary.get("access_leak_risk_count") or 0)
    batch_errors = int(summary.get("batch_error_count") or 0)
    if critical:
        observability_logger.log_warning(
            warn_type="ACCESS_LEAK_RISK",
            message="Membership reconciliation observed access-leak risk",
            context={
                "component": "billing_membership_scheduler",
                "mode": summary.get("mode"),
                "access_leak_risk_count": critical,
                "subscriber_count": summary.get("subscriber_count"),
            },
            source={
                "module": "membership_scheduler",
                "function": "run_membership_cycle",
            },
        )
    if batch_errors:
        observability_logger.log_warning(
            warn_type="BILLING_MEMBERSHIP_BATCH_ERRORS",
            message="Membership reconciliation batch contained isolated failures",
            context={
                "component": "billing_membership_scheduler",
                "mode": summary.get("mode"),
                "batch_error_count": batch_errors,
                "subscriber_count": summary.get("subscriber_count"),
            },
            source={
                "module": "membership_scheduler",
                "function": "run_membership_cycle",
            },
        )


def run_membership_cycle(
    *,
    now_ts: float | int | None = None,
    api=None,
    send_fn=None,
    path: str | None = None,
    subscription_path: str | None = None,
    notification_path: str | None = None,
) -> Dict[str, Any]:
    mode = runtime_mode()
    if mode == "DISABLED":
        return {
            "event": "billing_membership_reconciliation_cycle",
            "status": "DISABLED",
            "mode": mode,
            "subscriber_count": 0,
            "state_counts": {},
            "batch_error_count": 0,
            "actions_applied_count": 0,
            "access_leak_risk_count": 0,
        }

    kwargs: Dict[str, Any] = {
        "apply_actions": mode == "APPLY",
        "now_ts": now_ts,
        "api": api,
        "path": path,
        "subscription_path": subscription_path,
        "notification_path": notification_path,
    }
    if send_fn is not None:
        kwargs["send_fn"] = send_fn

    results = membership_reconciler.reconcile_all_known_subscribers(**kwargs)
    summary = _summary(results, mode=mode)
    _emit_summary(summary)
    return summary


def maybe_run_membership_cycle(
    *,
    now_ts: float | int | None = None,
    monotonic_now: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    global _LAST_SCAN_MONOTONIC

    if runtime_mode() == "DISABLED":
        return None

    current = time.monotonic() if monotonic_now is None else float(monotonic_now)
    interval = scan_interval_seconds()
    if _LAST_SCAN_MONOTONIC and current - _LAST_SCAN_MONOTONIC < interval:
        return None
    _LAST_SCAN_MONOTONIC = current
    return run_membership_cycle(now_ts=now_ts)
