from __future__ import annotations

import json
import os
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from billing import (
    kucoin_watcher,
    membership_reconciler,
    notification_scheduler,
    payment_ledger,
    revolut_merchant,
    subscription_registry,
    support_cases,
)
from core import storage

SCHEMA_VERSION = "1.0.0"
TRUTH_AUTHORITY = "READ_ONLY_DERIVED"
DEFAULT_PROVIDER_FAILURE_THRESHOLD = 3
DEFAULT_MAX_SNAPSHOTS = 200
MAX_SNAPSHOTS_LIMIT = 10_000

_SOURCE_PAYMENT = "payment_ledger"
_SOURCE_SUBSCRIPTION = "subscription_registry"
_SOURCE_NOTIFICATION = "notification_scheduler"
_SOURCE_SUPPORT = "support_cases"
_SOURCE_MEMBERSHIP = "membership_reconciler"
_SOURCE_REVOLUT = "revolut_merchant"
_SOURCE_KUCOIN = "kucoin_watcher"

SOURCE_NAMES = (
    _SOURCE_PAYMENT,
    _SOURCE_SUBSCRIPTION,
    _SOURCE_NOTIFICATION,
    _SOURCE_SUPPORT,
    _SOURCE_MEMBERSHIP,
    _SOURCE_REVOLUT,
    _SOURCE_KUCOIN,
)
SOURCE_STATES = frozenset({"PASS", "FAIL", "UNKNOWN"})

CORRELATION_FIELDS = (
    "payment_intent_id",
    "case_id",
    "subscriber_ref",
    "subscription_id",
    "entitlement_id",
    "reconciliation_id",
    "audit_correlation_id",
)

_CORRELATION_ALIASES = {
    "payment_intent_id": (
        "payment_intent_id",
        "pending_payment_intent_id",
        "last_payment_intent_id",
    ),
    "case_id": ("case_id",),
    "subscriber_ref": ("subscriber_ref",),
    "subscription_id": ("subscription_id",),
    "entitlement_id": ("entitlement_id",),
    "reconciliation_id": ("reconciliation_id",),
    "audit_correlation_id": ("audit_correlation_id",),
}

_SOURCE_ID_FIELDS = {
    _SOURCE_PAYMENT: ("ledger_event_id", "ledger_seq"),
    _SOURCE_SUBSCRIPTION: ("subscription_event_id", "subscription_seq"),
    _SOURCE_NOTIFICATION: (
        "billing_notification_event_id",
        "billing_notification_seq",
    ),
    _SOURCE_SUPPORT: ("case_event_id", "case_seq"),
    _SOURCE_MEMBERSHIP: ("membership_event_id", "membership_seq"),
    _SOURCE_REVOLUT: ("revolut_event_id", "revolut_seq"),
    _SOURCE_KUCOIN: ("kucoin_event_id", "kucoin_seq"),
}

_SAFE_DETAIL_FIELDS = (
    "provider",
    "payment_state",
    "provider_state",
    "reconciliation_result",
    "reconciliation_reason",
    "case_state",
    "review_action",
    "delivery_result",
    "client_action",
    "state",
    "tier",
    "plan_id",
    "strategy_product_id",
    "reconciliation_state",
    "entitlement_access_state",
    "entitlement_tier",
    "target_tier",
    "normalized_payment_state",
    "ledger_status",
    "status",
)

_PROVIDER_FAILURE_TYPES = {
    "REVOLUT_MERCHANT": frozenset({revolut_merchant.EVENT_PROVIDER_UNAVAILABLE}),
    "KUCOIN": frozenset({kucoin_watcher.EVENT_PROVIDER_UNAVAILABLE}),
}
_PROVIDER_SUCCESS_TYPES = {
    "REVOLUT_MERCHANT": frozenset(
        {
            revolut_merchant.EVENT_ORDER_BOUND,
            revolut_merchant.EVENT_ORDER_RECOVERED,
            revolut_merchant.EVENT_RECONCILED,
            revolut_merchant.EVENT_RECURRING_PAYMENT_INITIATED,
        }
    ),
    "KUCOIN": frozenset(
        {
            kucoin_watcher.EVENT_WS_TRIGGER,
            kucoin_watcher.EVENT_DEPOSIT_RECONCILED,
        }
    ),
}
_PROVIDER_SOURCE = {
    "REVOLUT_MERCHANT": _SOURCE_REVOLUT,
    "KUCOIN": _SOURCE_KUCOIN,
}

_SNAPSHOTS_RELATIVE = ("observability", "billing_observability_snapshots.json")
_SNAPSHOT_LOCK = "billing_observability_snapshots"


class BillingObservabilityError(RuntimeError):
    """Raised when a derived billing-observability view cannot be built safely."""


def snapshots_path() -> str:
    return storage.root_path(*_SNAPSHOTS_RELATIVE)


def _source_specs(paths: Mapping[str, str] | None = None):
    overrides = dict(paths or {})
    specs = {
        _SOURCE_PAYMENT: (payment_ledger.ledger_path(), payment_ledger.load_ledger),
        _SOURCE_SUBSCRIPTION: (
            subscription_registry.events_path(),
            subscription_registry.load_subscription_events,
        ),
        _SOURCE_NOTIFICATION: (
            notification_scheduler.events_path(),
            notification_scheduler.load_events,
        ),
        _SOURCE_SUPPORT: (support_cases.cases_path(), support_cases.load_case_events),
        _SOURCE_MEMBERSHIP: (
            membership_reconciler.events_path(),
            membership_reconciler.load_events,
        ),
        _SOURCE_REVOLUT: (
            revolut_merchant.events_path(),
            revolut_merchant.load_events,
        ),
        _SOURCE_KUCOIN: (kucoin_watcher.events_path(), kucoin_watcher.load_events),
    }
    unknown = sorted(set(overrides) - set(specs))
    if unknown:
        raise BillingObservabilityError(
            "Unknown billing observability source path override(s): "
            + ",".join(unknown)
        )
    return {
        name: (str(overrides.get(name) or default_path), loader)
        for name, (default_path, loader) in specs.items()
    }


def _safe_error_type(exc: BaseException) -> str:
    return type(exc).__name__[:120] or "Exception"


def collect_source_records(
    paths: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Read billing truth logs without mutating any truth surface.

    A missing source file is `UNKNOWN`, an existing empty source is `PASS` with
    zero events, and a corrupt/unreadable source is `FAIL`. This preserves the
    required distinction between unknown, failure, and a measured zero.
    """

    records: Dict[str, list[Dict[str, Any]]] = {}
    statuses: Dict[str, Dict[str, Any]] = {}
    for source, (path, loader) in _source_specs(paths).items():
        target = Path(path)
        if not target.exists():
            records[source] = []
            statuses[source] = {
                "status": "UNKNOWN",
                "event_count": None,
                "reason": "SOURCE_FILE_NOT_PRESENT",
            }
            continue
        try:
            loaded = loader(path)
        except Exception as exc:
            records[source] = []
            statuses[source] = {
                "status": "FAIL",
                "event_count": None,
                "reason": "SOURCE_READ_OR_VALIDATION_FAILED",
                "error_type": _safe_error_type(exc),
            }
            continue
        records[source] = [dict(row) for row in loaded if isinstance(row, Mapping)]
        statuses[source] = {
            "status": "PASS",
            "event_count": len(records[source]),
            "reason": "SOURCE_READ_VALIDATED",
        }
    return {"records": records, "source_status": statuses}


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        text = str(value).strip()
        return text or None
    return None


def _correlation_values(record: Mapping[str, Any]) -> Dict[str, list[str]]:
    result: Dict[str, list[str]] = {}
    for canonical, aliases in _CORRELATION_ALIASES.items():
        seen: list[str] = []
        for alias in aliases:
            value = _as_text(record.get(alias))
            if value is not None and value not in seen:
                seen.append(value)
        if seen:
            result[canonical] = seen
    return result


def _iso_epoch(value: Any) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (ValueError, OverflowError):
        return None


def _event_epoch(record: Mapping[str, Any]) -> float | None:
    for field in (
        "occurred_at_epoch",
        "reviewed_at_epoch",
        "created_at_epoch",
        "sent_at_epoch",
        "delivered_at_epoch",
    ):
        value = record.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    for field in ("updated_at_ms", "created_at_ms"):
        value = record.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value) / 1000.0
    for field in ("received_at", "settled_at", "created_at"):
        parsed = _iso_epoch(record.get(field))
        if parsed is not None:
            return parsed
    return None


def normalize_event(source: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    if source not in _SOURCE_ID_FIELDS:
        raise BillingObservabilityError(f"Unknown billing source: {source}")
    event_id_field, sequence_field = _SOURCE_ID_FIELDS[source]
    details = {
        field: record.get(field)
        for field in _SAFE_DETAIL_FIELDS
        if record.get(field) is not None
    }
    sequence = record.get(sequence_field)
    return {
        "source": source,
        "source_event_id": _as_text(record.get(event_id_field)),
        "source_sequence": (
            int(sequence)
            if isinstance(sequence, int) and not isinstance(sequence, bool)
            else None
        ),
        "event_type": _as_text(record.get("event_type")) or "UNKNOWN_EVENT_TYPE",
        "occurred_at_epoch": _event_epoch(record),
        "correlation": _correlation_values(record),
        "details": details,
    }


def normalize_timeline(
    records: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[Dict[str, Any]]:
    timeline: list[Dict[str, Any]] = []
    for source in SOURCE_NAMES:
        for record in records.get(source, ()):
            timeline.append(normalize_event(source, record))
    timeline.sort(
        key=lambda row: (
            row.get("occurred_at_epoch") is None,
            row.get("occurred_at_epoch") or 0.0,
            str(row.get("source") or ""),
            int(row.get("source_sequence") or 0),
        )
    )
    return timeline


def _normalize_filter_values(value: Any) -> set[str]:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        text = str(value).strip()
        return {text} if text else set()
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
        result: set[str] = set()
        for item in value:
            text = _as_text(item)
            if text is not None:
                result.add(text)
        return result
    return set()


def reconstruct_transition(
    timeline: Sequence[Mapping[str, Any]],
    **filters: Any,
) -> list[Dict[str, Any]]:
    """Reconstruct a connected billing transition by governed correlation IDs.

    Correlation is a transitive closure: an event matching the supplied seed can
    introduce another governed identifier, which can then connect evidence from
    another truth layer. No state is inferred beyond the persisted event data.
    """

    unknown = sorted(set(filters) - set(CORRELATION_FIELDS))
    if unknown:
        raise BillingObservabilityError(
            "Unknown correlation filter(s): " + ",".join(unknown)
        )
    known = {
        field: _normalize_filter_values(filters.get(field))
        for field in CORRELATION_FIELDS
    }
    if not any(known.values()):
        raise BillingObservabilityError(
            "At least one governed correlation identifier is required"
        )

    selected: set[int] = set()
    changed = True
    while changed:
        changed = False
        for index, event in enumerate(timeline):
            if index in selected:
                continue
            correlation = event.get("correlation")
            if not isinstance(correlation, Mapping):
                continue
            matched = False
            for field in CORRELATION_FIELDS:
                event_values = _normalize_filter_values(correlation.get(field, ()))
                if event_values and known[field].intersection(event_values):
                    matched = True
                    break
            if not matched:
                continue
            selected.add(index)
            changed = True
            for field in CORRELATION_FIELDS:
                known[field].update(
                    _normalize_filter_values(correlation.get(field, ()))
                )

    return [dict(timeline[index]) for index in sorted(selected)]


def _latest_by(
    rows: Sequence[Mapping[str, Any]], key: str
) -> Dict[str, Mapping[str, Any]]:
    result: Dict[str, Mapping[str, Any]] = {}
    for row in rows:
        value = _as_text(row.get(key))
        if value is not None:
            result[value] = row
    return result


def _latest_payment_states(rows: Sequence[Mapping[str, Any]]) -> Dict[str, str]:
    latest: Dict[str, str] = {}
    for row in rows:
        intent = _as_text(row.get("payment_intent_id"))
        state = _as_text(row.get("payment_state"))
        if intent and state:
            latest[intent] = state
    return latest


def _source_pass(
    source_status: Mapping[str, Mapping[str, Any]], source: str
) -> bool:
    return source_status.get(source, {}).get("status") == "PASS"


def _backlog(
    records: Mapping[str, Sequence[Mapping[str, Any]]],
    source_status: Mapping[str, Mapping[str, Any]],
) -> Dict[str, int | None]:
    payment_rows = records.get(_SOURCE_PAYMENT, ())
    subscription_rows = records.get(_SOURCE_SUBSCRIPTION, ())
    notification_rows = records.get(_SOURCE_NOTIFICATION, ())
    support_rows = records.get(_SOURCE_SUPPORT, ())
    membership_rows = records.get(_SOURCE_MEMBERSHIP, ())
    revolut_rows = records.get(_SOURCE_REVOLUT, ())
    kucoin_rows = records.get(_SOURCE_KUCOIN, ())

    payment_reconciliation = Counter(
        str(row.get("reconciliation_result"))
        for row in payment_rows
        if row.get("event_type") == payment_ledger.EVENT_RECONCILIATION
    )
    latest_payments = _latest_payment_states(payment_rows)
    payment_pending = sum(
        1 for state in latest_payments.values() if state in {"CREATED", "PENDING", "UNKNOWN"}
    )

    latest_cases = _latest_by(support_rows, "case_id")
    support_open = sum(
        1
        for row in latest_cases.values()
        if row.get("case_state") not in support_cases.CLOSED_STATES
    )

    failed_notifications = sum(
        1
        for row in notification_rows
        if row.get("event_type") == notification_scheduler.EVENT_DELIVERY
        and row.get("delivery_result") in {"FAILED", "FAILED_TERMINAL"}
    )

    final_membership = [
        row
        for row in membership_rows
        if row.get("event_type") == membership_reconciler.EVENT_FINAL
    ]
    latest_reconciliations = _latest_by(final_membership, "reconciliation_id")
    membership_not_in_sync = sum(
        1
        for row in latest_reconciliations.values()
        if row.get("reconciliation_state") != "IN_SYNC"
    )
    access_leak_risk = sum(
        1
        for row in latest_reconciliations.values()
        if row.get("reconciliation_state") == "ACCESS_LEAK_RISK"
    )

    latest_subscriptions = _latest_by(subscription_rows, "subscription_id")
    subscription_hold = sum(
        1
        for row in latest_subscriptions.values()
        if row.get("state")
        in {"GRACE_HOLD", "CHARGEBACK_OPEN", "REFUND_HOLD", "PAYMENT_FAILED"}
    )

    return {
        "payment_pending_or_unknown": (
            payment_pending if _source_pass(source_status, _SOURCE_PAYMENT) else None
        ),
        "payment_unmatched": (
            int(payment_reconciliation.get("UNMATCHED", 0))
            if _source_pass(source_status, _SOURCE_PAYMENT)
            else None
        ),
        "payment_contradictory": (
            int(payment_reconciliation.get("CONTRADICTORY", 0))
            if _source_pass(source_status, _SOURCE_PAYMENT)
            else None
        ),
        "kucoin_manual_review_required": (
            sum(
                1
                for row in kucoin_rows
                if row.get("event_type") == kucoin_watcher.EVENT_MANUAL_REVIEW
            )
            if _source_pass(source_status, _SOURCE_KUCOIN)
            else None
        ),
        "revolut_unmatched_webhook": (
            sum(
                1
                for row in revolut_rows
                if row.get("event_type") == revolut_merchant.EVENT_WEBHOOK_UNMATCHED
            )
            if _source_pass(source_status, _SOURCE_REVOLUT)
            else None
        ),
        "support_open_cases": (
            support_open if _source_pass(source_status, _SOURCE_SUPPORT) else None
        ),
        "notification_failed_deliveries": (
            failed_notifications
            if _source_pass(source_status, _SOURCE_NOTIFICATION)
            else None
        ),
        "subscription_hold_states": (
            subscription_hold
            if _source_pass(source_status, _SOURCE_SUBSCRIPTION)
            else None
        ),
        "membership_not_in_sync": (
            membership_not_in_sync
            if _source_pass(source_status, _SOURCE_MEMBERSHIP)
            else None
        ),
        "access_leak_risk": (
            access_leak_risk
            if _source_pass(source_status, _SOURCE_MEMBERSHIP)
            else None
        ),
    }


def _provider_health(
    provider: str,
    records: Mapping[str, Sequence[Mapping[str, Any]]],
    source_status: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    source = _PROVIDER_SOURCE[provider]
    status = str(source_status.get(source, {}).get("status") or "UNKNOWN")
    if status != "PASS":
        return {
            "status": status,
            "evidence_state": "SOURCE_NOT_VALIDATED",
            "consecutive_failures": None,
            "event_count": source_status.get(source, {}).get("event_count"),
        }

    rows = list(records.get(source, ()))
    failures = _PROVIDER_FAILURE_TYPES[provider]
    successes = _PROVIDER_SUCCESS_TYPES[provider]
    significant = [
        row
        for row in rows
        if row.get("event_type") in failures or row.get("event_type") in successes
    ]
    if not significant:
        return {
            "status": "UNKNOWN",
            "evidence_state": "NO_PROVIDER_HEALTH_EVIDENCE",
            "consecutive_failures": 0,
            "event_count": len(rows),
        }

    consecutive_failures = 0
    for row in reversed(significant):
        if row.get("event_type") in failures:
            consecutive_failures += 1
        else:
            break
    last_type = significant[-1].get("event_type")
    return {
        "status": "UNAVAILABLE" if last_type in failures else "OBSERVED",
        "evidence_state": str(last_type),
        "consecutive_failures": consecutive_failures,
        "event_count": len(rows),
    }


def _deduplication(
    records: Mapping[str, Sequence[Mapping[str, Any]]],
    source_status: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    by_source: Dict[str, Dict[str, Any]] = {}
    total_duplicates = 0
    all_sources_validated = True
    for source in SOURCE_NAMES:
        state = str(source_status.get(source, {}).get("status") or "UNKNOWN")
        if state != "PASS":
            all_sources_validated = False
            by_source[source] = {
                "status": state,
                "events_with_idempotency_key": None,
                "persisted_duplicate_idempotency_keys": None,
            }
            continue
        keys = [
            str(row.get("idempotency_key"))
            for row in records.get(source, ())
            if row.get("idempotency_key") is not None
        ]
        counts = Counter(keys)
        duplicates = sum(1 for count in counts.values() if count > 1)
        total_duplicates += duplicates
        by_source[source] = {
            "status": "PASS" if duplicates == 0 else "FAIL",
            "events_with_idempotency_key": len(keys),
            "persisted_duplicate_idempotency_keys": duplicates,
        }
    overall = (
        "FAIL"
        if total_duplicates
        else ("PASS" if all_sources_validated else "UNKNOWN")
    )
    return {
        "status": overall,
        "persisted_duplicate_idempotency_keys": (
            total_duplicates if all_sources_validated or total_duplicates else None
        ),
        "by_source": by_source,
    }


def _incident_correlation(row: Mapping[str, Any]) -> Dict[str, list[str]]:
    return _correlation_values(row)


def _incidents(
    records: Mapping[str, Sequence[Mapping[str, Any]]],
    source_status: Mapping[str, Mapping[str, Any]],
    provider_failure_threshold: int,
) -> list[Dict[str, Any]]:
    incidents: list[Dict[str, Any]] = []

    if _source_pass(source_status, _SOURCE_PAYMENT):
        for row in records.get(_SOURCE_PAYMENT, ()):
            if row.get("reconciliation_result") != "CONTRADICTORY":
                continue
            incidents.append(
                {
                    "severity": "CRITICAL",
                    "incident_type": "CONTRADICTORY_PROVIDER_EVIDENCE",
                    "source": _SOURCE_PAYMENT,
                    "source_event_id": row.get("ledger_event_id"),
                    "correlation": _incident_correlation(row),
                }
            )

    if _source_pass(source_status, _SOURCE_MEMBERSHIP):
        final_membership = [
            row
            for row in records.get(_SOURCE_MEMBERSHIP, ())
            if row.get("event_type") == membership_reconciler.EVENT_FINAL
        ]
        for reconciliation_id, row in _latest_by(
            final_membership, "reconciliation_id"
        ).items():
            if row.get("reconciliation_state") != "ACCESS_LEAK_RISK":
                continue
            incidents.append(
                {
                    "severity": "CRITICAL",
                    "incident_type": "ACCESS_LEAK_RISK",
                    "source": _SOURCE_MEMBERSHIP,
                    "source_event_id": row.get("membership_event_id"),
                    "reconciliation_id": reconciliation_id,
                    "correlation": _incident_correlation(row),
                }
            )

    for provider in sorted(_PROVIDER_SOURCE):
        health = _provider_health(provider, records, source_status)
        failures = health.get("consecutive_failures")
        if isinstance(failures, int) and failures >= provider_failure_threshold:
            incidents.append(
                {
                    "severity": "CRITICAL",
                    "incident_type": "REPEATED_PROVIDER_FAILURE",
                    "provider": provider,
                    "consecutive_failures": failures,
                    "threshold": provider_failure_threshold,
                }
            )
    return incidents


def _positive_threshold(value: Any, *, label: str, maximum: int = 10_000) -> int:
    if isinstance(value, bool):
        raise BillingObservabilityError(f"{label} must be a positive integer")
    try:
        result = int(value)
    except Exception as exc:
        raise BillingObservabilityError(f"{label} must be a positive integer") from exc
    if result <= 0 or result > maximum:
        raise BillingObservabilityError(
            f"{label} must be between 1 and {maximum}"
        )
    return result


def provider_failure_threshold_from_env() -> int:
    raw = os.getenv(
        "BILLING_OBSERVABILITY_PROVIDER_FAILURE_THRESHOLD",
        str(DEFAULT_PROVIDER_FAILURE_THRESHOLD),
    )
    return _positive_threshold(raw, label="provider failure threshold", maximum=100)


def max_snapshots_from_env() -> int:
    raw = os.getenv(
        "BILLING_OBSERVABILITY_MAX_SNAPSHOTS", str(DEFAULT_MAX_SNAPSHOTS)
    )
    return _positive_threshold(
        raw, label="billing observability max snapshots", maximum=MAX_SNAPSHOTS_LIMIT
    )


def _incident_assessment_status(
    source_status: Mapping[str, Mapping[str, Any]],
) -> str:
    states = {
        str(source_status.get(source, {}).get("status") or "UNKNOWN")
        for source in SOURCE_NAMES
    }
    if "FAIL" in states:
        return "FAIL"
    if states == {"PASS"}:
        return "PASS"
    return "UNKNOWN"


def build_snapshot(
    records: Mapping[str, Sequence[Mapping[str, Any]]],
    source_status: Mapping[str, Mapping[str, Any]],
    *,
    now_ts: float | int | None = None,
    provider_failure_threshold: int | None = None,
) -> Dict[str, Any]:
    threshold = _positive_threshold(
        provider_failure_threshold
        if provider_failure_threshold is not None
        else provider_failure_threshold_from_env(),
        label="provider failure threshold",
        maximum=100,
    )
    generated_at = int(time.time() if now_ts is None else now_ts)
    timeline = normalize_timeline(records)
    provider_health = {
        provider: _provider_health(provider, records, source_status)
        for provider in sorted(_PROVIDER_SOURCE)
    }
    incidents = _incidents(records, source_status, threshold)
    severity_counts = Counter(
        str(row.get("severity") or "UNKNOWN") for row in incidents
    )
    validated_source_count = sum(
        1
        for source in SOURCE_NAMES
        if source_status.get(source, {}).get("status") == "PASS"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "truth_authority": TRUTH_AUTHORITY,
        "generated_at_epoch": generated_at,
        "source_status": {
            source: dict(source_status.get(source) or {"status": "UNKNOWN"})
            for source in SOURCE_NAMES
        },
        "validated_source_count": validated_source_count,
        "source_count": len(SOURCE_NAMES),
        "timeline_event_count": len(timeline),
        "provider_health": provider_health,
        "reconciliation_backlog": _backlog(records, source_status),
        "deduplication": _deduplication(records, source_status),
        "incidents": incidents,
        "incident_counts": dict(sorted(severity_counts.items())),
        "incident_assessment_status": _incident_assessment_status(source_status),
        "provider_failure_threshold": threshold,
    }


def collect_snapshot(
    paths: Mapping[str, str] | None = None,
    *,
    now_ts: float | int | None = None,
    provider_failure_threshold: int | None = None,
) -> Dict[str, Any]:
    collected = collect_source_records(paths)
    timeline = normalize_timeline(collected["records"])
    snapshot = build_snapshot(
        collected["records"],
        collected["source_status"],
        now_ts=now_ts,
        provider_failure_threshold=provider_failure_threshold,
    )
    return {"snapshot": snapshot, "timeline": timeline}


def render_operator_summary(snapshot: Mapping[str, Any]) -> str:
    sources = snapshot.get("source_status") or {}
    providers = snapshot.get("provider_health") or {}
    backlog = snapshot.get("reconciliation_backlog") or {}
    incidents = snapshot.get("incidents") or []

    source_bits = []
    for source in SOURCE_NAMES:
        row = sources.get(source) if isinstance(sources, Mapping) else None
        state = str(row.get("status") if isinstance(row, Mapping) else "UNKNOWN")
        count = row.get("event_count") if isinstance(row, Mapping) else None
        count_text = "UNKNOWN" if count is None else str(count)
        source_bits.append(f"{source}={state}({count_text})")

    provider_bits = []
    for provider in sorted(_PROVIDER_SOURCE):
        row = providers.get(provider) if isinstance(providers, Mapping) else None
        state = str(row.get("status") if isinstance(row, Mapping) else "UNKNOWN")
        provider_bits.append(f"{provider}={state}")

    critical = sum(
        1
        for row in incidents
        if isinstance(row, Mapping) and row.get("severity") == "CRITICAL"
    )
    backlog_bits = [
        f"{key}={'UNKNOWN' if value is None else value}"
        for key, value in sorted(backlog.items())
    ]
    return "\n".join(
        (
            f"Billing observability {snapshot.get('truth_authority', TRUTH_AUTHORITY)}",
            "Sources: " + ", ".join(source_bits),
            "Providers: " + ", ".join(provider_bits),
            "Backlog: " + ", ".join(backlog_bits),
            "Critical incidents observed: "
            f"{critical}; assessment={snapshot.get('incident_assessment_status', 'UNKNOWN')}",
        )
    )


def _load_snapshot_ring(path: str) -> Dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "truth_authority": TRUTH_AUTHORITY,
            "dropped_snapshot_count": 0,
            "snapshots": [],
        }
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BillingObservabilityError(
            "Derived billing observability snapshot store is unreadable"
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("snapshots"), list):
        raise BillingObservabilityError(
            "Derived billing observability snapshot store has invalid structure"
        )
    return dict(payload)


def persist_snapshot(
    snapshot: Mapping[str, Any],
    *,
    path: str | None = None,
    max_snapshots: int | None = None,
) -> Dict[str, Any]:
    """Persist a bounded derived snapshot ring, never billing truth.

    Source JSONL truth logs remain untouched. Rotation is performed only on this
    rebuildable JSON projection through the canonical atomic JSON writer.
    """

    if snapshot.get("truth_authority") != TRUTH_AUTHORITY:
        raise BillingObservabilityError(
            "Only READ_ONLY_DERIVED billing observability snapshots may be persisted"
        )
    limit = _positive_threshold(
        max_snapshots if max_snapshots is not None else max_snapshots_from_env(),
        label="billing observability max snapshots",
        maximum=MAX_SNAPSHOTS_LIMIT,
    )
    target = path or snapshots_path()
    record = dict(snapshot)
    record["snapshot_id"] = str(uuid.uuid4())

    with storage.with_lock(_SNAPSHOT_LOCK):
        ring = _load_snapshot_ring(target)
        snapshots = [
            dict(row) for row in ring.get("snapshots", []) if isinstance(row, Mapping)
        ]
        snapshots.append(record)
        dropped_now = max(0, len(snapshots) - limit)
        if dropped_now:
            snapshots = snapshots[-limit:]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "truth_authority": TRUTH_AUTHORITY,
            "max_snapshots": limit,
            "dropped_snapshot_count": int(ring.get("dropped_snapshot_count") or 0)
            + dropped_now,
            "snapshots": snapshots,
        }
        storage.save_json_atomic(target, payload)
    return {
        "status": "PERSISTED",
        "snapshot_id": record["snapshot_id"],
        "retained_snapshot_count": len(snapshots),
        "dropped_snapshot_count": payload["dropped_snapshot_count"],
        "path": target,
    }
