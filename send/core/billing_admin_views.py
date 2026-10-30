from __future__ import annotations

import hashlib
import re
import time
from collections import Counter
from typing import Any, Dict, Mapping, Optional, Sequence

from billing import billing_observability, support_cases


_CASE_TOKEN_RE = re.compile(r"^[0-9a-f]{16}$")
_SAFE_PROVIDER_NAMES = frozenset({"REVOLUT_MERCHANT", "KUCOIN"})


def _case_token(case_id: Any) -> str | None:
    if not isinstance(case_id, str) or not case_id.strip():
        return None
    return hashlib.sha256(case_id.strip().encode("utf-8")).hexdigest()[:16]


def _safe_support_provider(raw: Any) -> str:
    provider = str(raw or "").strip().upper()
    return provider if provider in _SAFE_PROVIDER_NAMES else "UNKNOWN"


def _safe_case_time(row: Mapping[str, Any]) -> int:
    value = row.get("occurred_at_epoch")
    if isinstance(value, bool):
        return 0
    try:
        stamp = int(value)
    except (ValueError, TypeError, OverflowError):
        return 0
    return stamp if 0 < stamp <= 253402300799 else 0


TRUTH_BOUNDARY = (
    "PAYMENT != SUBSCRIPTION != ENTITLEMENT != TELEGRAM MEMBERSHIP"
)
_NO_DIRECT_OVERRIDE = (
    "No direct tier/channel override. Changes must flow through the governed "
    "billing, entitlement and membership authorities."
)


def _lines(lines: Sequence[str]) -> str:
    return "\n".join(str(line) for line in lines)


def _text(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    value = str(value).strip()
    return value or default


def _count(value: Any) -> str:
    return "UNKNOWN" if value is None else str(value)


def _mask_ref(value: Any, *, prefix: str = "REF") -> str:
    text = _text(value, "")
    if not text:
        return "MASKED / UNKNOWN"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8].upper()
    return f"{prefix}-…{digest}"


def _latest_by(
    rows: Sequence[Mapping[str, Any]],
    key: str,
) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            latest[text] = dict(row)
    return latest


def _safe_context() -> Dict[str, Any]:
    collected = billing_observability.collect_source_records()
    snapshot = billing_observability.build_snapshot(
        collected["records"],
        collected["source_status"],
    )
    timeline = billing_observability.normalize_timeline(collected["records"])
    return {
        "records": collected["records"],
        "source_status": collected["source_status"],
        "snapshot": snapshot,
        "timeline": timeline,
    }


def _context_or_unavailable(
    context: Optional[Mapping[str, Any]],
) -> tuple[Optional[Mapping[str, Any]], Optional[str]]:
    if context is not None:
        return context, None
    try:
        return _safe_context(), None
    except Exception as exc:
        return None, type(exc).__name__[:120] or "Exception"


def render_billing_overview(
    context: Optional[Mapping[str, Any]] = None,
) -> str:
    ctx, error = _context_or_unavailable(context)
    lines = [
        "Billing & Access",
        "",
        "Truth Boundary",
        TRUTH_BOUNDARY,
        "",
    ]
    if ctx is None:
        lines.extend(
            [
                "Evidence: UNAVAILABLE",
                f"Reason: {error or 'UNKNOWN'}",
                "",
                _NO_DIRECT_OVERRIDE,
            ]
        )
        return _lines(lines)

    snapshot = ctx.get("snapshot") if isinstance(ctx, Mapping) else None
    if not isinstance(snapshot, Mapping):
        lines.extend(["Evidence: UNKNOWN", "", _NO_DIRECT_OVERRIDE])
        return _lines(lines)

    lines.extend(
        [
            billing_observability.render_operator_summary(snapshot),
            "",
            "Safety",
            _NO_DIRECT_OVERRIDE,
        ]
    )
    return _lines(lines)


def render_subscriber_inventory(
    context: Optional[Mapping[str, Any]] = None,
    *,
    now_ts: Optional[int] = None,
    attention_limit: int = 6,
) -> str:
    ctx, error = _context_or_unavailable(context)
    lines = [
        "Subscriber Billing",
        "",
        "Expected access vs Telegram membership",
        "Drift is visible and auditable; UNKNOWN stays UNKNOWN.",
        "",
    ]
    if ctx is None:
        lines.extend(
            [
                "Inventory: UNKNOWN",
                f"Reason: {error or 'UNKNOWN'}",
                "",
                _NO_DIRECT_OVERRIDE,
            ]
        )
        return _lines(lines)

    records = ctx.get("records") if isinstance(ctx, Mapping) else None
    statuses = ctx.get("source_status") if isinstance(ctx, Mapping) else None
    if not isinstance(records, Mapping) or not isinstance(statuses, Mapping):
        lines.extend(["Inventory: UNKNOWN", "", _NO_DIRECT_OVERRIDE])
        return _lines(lines)

    subscription_status = statuses.get("subscription_registry")
    membership_status = statuses.get("membership_reconciler")
    subscription_ok = (
        isinstance(subscription_status, Mapping)
        and subscription_status.get("status") == "PASS"
    )
    membership_ok = (
        isinstance(membership_status, Mapping)
        and membership_status.get("status") == "PASS"
    )

    latest_subscribers: Dict[str, Dict[str, Any]] = {}
    if subscription_ok:
        latest_subscribers = _latest_by(
            records.get("subscription_registry", ()), "subscriber_ref"
        )

    if subscription_ok:
        counts = Counter(
            _text(row.get("tier"))
            for row in latest_subscribers.values()
            if _text(row.get("tier")) in {"FREE", "BASIC", "PRO", "ELITE"}
        )
        lines.extend(
            [
                "Inventory Counters",
                f"TOTAL: {len(latest_subscribers)}",
                f"FREE: {counts.get('FREE', 0)}",
                f"BASIC: {counts.get('BASIC', 0)}",
                f"PRO: {counts.get('PRO', 0)}",
                f"ELITE: {counts.get('ELITE', 0)}",
            ]
        )
    else:
        lines.extend(
            [
                "Inventory Counters",
                "TOTAL: UNKNOWN",
                "FREE: UNKNOWN",
                "BASIC: UNKNOWN",
                "PRO: UNKNOWN",
                "ELITE: UNKNOWN",
            ]
        )

    snapshot = ctx.get("snapshot")
    backlog = (
        snapshot.get("reconciliation_backlog")
        if isinstance(snapshot, Mapping)
        else None
    )
    lines.extend(
        [
            "",
            "Attention Counters",
            "GRACE / PAYMENT HOLD: "
            + _count(
                backlog.get("subscription_hold_states")
                if isinstance(backlog, Mapping)
                else None
            ),
            "MEMBERSHIP NOT IN SYNC: "
            + _count(
                backlog.get("membership_not_in_sync")
                if isinstance(backlog, Mapping)
                else None
            ),
            "ACCESS LEAK RISK: "
            + _count(
                backlog.get("access_leak_risk")
                if isinstance(backlog, Mapping)
                else None
            ),
        ]
    )

    now = int(time.time() if now_ts is None else now_ts)
    attention: Dict[str, str] = {}
    if subscription_ok:
        for subscriber_ref, row in latest_subscribers.items():
            state = _text(row.get("state"))
            if state in {
                "GRACE_HOLD",
                "PAYMENT_FAILED",
                "CHARGEBACK_OPEN",
                "REFUND_HOLD",
                "INTENT_PAYMENT_PENDING",
            }:
                attention[subscriber_ref] = state
                continue
            expiry = row.get("expires_at_epoch")
            tier = _text(row.get("tier"))
            if (
                tier != "FREE"
                and isinstance(expiry, (int, float))
                and not isinstance(expiry, bool)
                and 0 < int(expiry) - now <= 3 * 24 * 60 * 60
            ):
                attention[subscriber_ref] = "EXPIRING_SOON"

    if membership_ok:
        final_rows = [
            row
            for row in records.get("membership_reconciler", ())
            if row.get("event_type") == "TELEGRAM_MEMBERSHIP_RECONCILIATION"
        ]
        latest_membership = _latest_by(final_rows, "subscriber_ref")
        for subscriber_ref, row in latest_membership.items():
            state = _text(row.get("reconciliation_state"))
            if state != "IN_SYNC":
                attention[subscriber_ref] = state

    lines.extend(["", "Subscribers Requiring Attention"])
    if not subscription_ok and not membership_ok:
        lines.append("UNKNOWN — subscriber/membership sources are not validated.")
    elif not attention:
        lines.append("0 observed from validated available sources.")
    else:
        for subscriber_ref, reason in list(attention.items())[: max(1, attention_limit)]:
            row = latest_subscribers.get(subscriber_ref, {})
            lines.append(
                f"- {_mask_ref(subscriber_ref, prefix='SUB')}: "
                f"{_text(row.get('tier'))} | {reason}"
            )

    lines.extend(["", _NO_DIRECT_OVERRIDE])
    return _lines(lines)


def render_support_queue(
    context: Optional[Mapping[str, Any]] = None,
    *,
    limit: int = 8,
) -> str:
    ctx, error = _context_or_unavailable(context)
    lines = [
        "Billing Support Queue",
        "",
        "Admin review is evidence, not direct entitlement.",
        "",
    ]
    if ctx is None:
        lines.extend(["Queue: UNKNOWN", f"Reason: {error or 'UNKNOWN'}"])
        return _lines(lines)

    records = ctx.get("records") if isinstance(ctx, Mapping) else None
    statuses = ctx.get("source_status") if isinstance(ctx, Mapping) else None
    source = statuses.get("support_cases") if isinstance(statuses, Mapping) else None
    if (
        not isinstance(records, Mapping)
        or not isinstance(source, Mapping)
        or source.get("status") != "PASS"
    ):
        lines.append("Queue: UNKNOWN")
        return _lines(lines)

    latest = _latest_by(records.get("support_cases", ()), "case_id")
    open_cases = [
        row
        for row in latest.values()
        if row.get("case_state") not in support_cases.CLOSED_STATES
    ]
    open_cases.sort(
        key=_safe_case_time,
        reverse=True,
    )
    lines.append(f"OPEN CASES: {len(open_cases)}")
    if not open_cases:
        lines.append("No open support cases observed.")
    else:
        for row in open_cases[: max(1, limit)]:
            case_ref = _mask_ref(row.get("case_id"), prefix="CASE")
            state = _text(row.get("case_state"))
            provider = _safe_support_provider(row.get("provider"))
            payment_link = (
                "LINKED"
                if _text(row.get("payment_intent_id"), "") 
                else "NOT LINKED"
            )
            lines.append(f"- {case_ref}: {state} | {provider} | payment {payment_link}")

    lines.extend(
        [
            "",
            "PAYMENT PROOF SUBMITTED != PAYMENT VERIFIED",
            "VERIFY writes governed evidence; it does not directly mutate channels.",
        ]
    )
    return _lines(lines)


def _validated_support_rows(
    context: Mapping[str, Any] | None,
) -> list[Dict[str, Any]] | None:
    """Return the complete verified support source, never a synthesized zero."""
    if not isinstance(context, Mapping):
        return None
    statuses = context.get("source_status")
    records = context.get("records")
    if not isinstance(statuses, Mapping) or not isinstance(records, Mapping):
        return None
    status = statuses.get("support_cases")
    if not isinstance(status, Mapping) or status.get("status") != "PASS":
        return None
    raw = records.get("support_cases")
    if not isinstance(raw, (tuple, list)):
        return None
    if any(not isinstance(row, Mapping) for row in raw):
        return None
    return [dict(row) for row in raw]


def support_case_navigation(
    context: Optional[Mapping[str, Any]] = None,
    *,
    limit: int = 5,
) -> list[tuple[str, str]]:
    """Read-only opaque case selectors for the Owner/Admin queue.

    The callback contains only a fixed-length hash prefix of a case UUID, not
    a raw subscriber, case, payment, Telegram or support message identifier.
    Any hash collision suppresses its selector instead of choosing a case.
    """
    ctx, _error = _context_or_unavailable(context)
    rows = _validated_support_rows(ctx)
    if rows is None:
        return []
    latest = _latest_by(rows, "case_id")
    active = [
        row for row in latest.values()
        if row.get("case_state") in support_cases.CASE_STATES
        and row["case_state"] not in support_cases.CLOSED_STATES
    ]
    active.sort(key=_safe_case_time, reverse=True)
    token_counts = Counter(
        token for row in latest.values()
        if (token := _case_token(row.get("case_id"))) is not None
    )
    out: list[tuple[str, str]] = []
    for row in active:
        token = _case_token(row.get("case_id"))
        if token is None or token_counts[token] != 1:
            continue
        out.append((f"CASE-…{token[:8].upper()}", token))
        if len(out) >= max(1, min(5, int(limit))):
            break
    return out


def render_support_queue_panel() -> tuple[str, list[tuple[str, str]]]:
    """One source read for text + case navigation; no separate unbounded reads."""
    ctx, error = _context_or_unavailable(None)
    if ctx is None:
        return (
            _lines([
                "Billing Support Queue",
                "",
                "Queue: UNKNOWN",
                f"Reason: {error or 'UNKNOWN'}",
                "PAYMENT PROOF SUBMITTED != PAYMENT VERIFIED",
            ]),
            [],
        )
    return render_support_queue(ctx), support_case_navigation(ctx)


def render_support_case_detail(
    case_token: str,
    context: Optional[Mapping[str, Any]] = None,
) -> str:
    """Show a masked, read-only support-case summary, never proofs or messages."""
    token = str(case_token or "").lower()
    preamble = ["Billing Support Case", "", "READ ONLY — No direct entitlement mutation"]
    if not _CASE_TOKEN_RE.fullmatch(token):
        return _lines([*preamble, "Case evidence: UNAVAILABLE"])

    ctx, _error = _context_or_unavailable(context)
    rows = _validated_support_rows(ctx)
    if rows is None:
        return _lines([*preamble, "Case evidence: UNKNOWN — source not validated"])

    latest = _latest_by(rows, "case_id")
    matches = [
        (case_id, row)
        for case_id, row in latest.items()
        if _case_token(case_id) == token
    ]
    if len(matches) != 1:
        return _lines([*preamble, "Case evidence: UNAVAILABLE"])

    case_id, current = matches[0]
    state = current.get("case_state")
    if state not in support_cases.CASE_STATES:
        return _lines([*preamble, "Case evidence: UNKNOWN — invalid state"])
    history = [row for row in rows if row.get("case_id") == case_id]
    events = Counter(str(row.get("event_type") or "") for row in history)
    provider = _safe_support_provider(current.get("provider"))
    return _lines([
        *preamble,
        f"Case: CASE-…{token[:8].upper()}",
        f"State: {state}",
        f"Provider: {provider}",
        f"Payment intent: {'LINKED' if current.get('payment_intent_id') else 'NOT LINKED'}",
        f"Recorded case events: {len(history)}",
        f"Client messages: {events.get(support_cases.EVENT_CLIENT_MESSAGE, 0)}",
        f"Admin replies: {events.get(support_cases.EVENT_ADMIN_MESSAGE, 0)}",
        f"Payment-proof submissions: {events.get(support_cases.EVENT_PAYMENT_PROOF, 0)}",
        f"Review events: {events.get(support_cases.EVENT_REVIEW, 0)}",
        "",
        "PAYMENT PROOF SUBMITTED != PAYMENT VERIFIED",
        "Admin VERIFY writes evidence; it does not grant channels or tiers.",
        "Raw messages, attachments, subscriber IDs and provider references are hidden.",
    ])


def render_provider_status(
    context: Optional[Mapping[str, Any]] = None,
) -> str:
    ctx, error = _context_or_unavailable(context)
    lines = [
        "Payment Provider Operations",
        "",
        "Provider event != subscriber payment attribution",
        "",
    ]
    if ctx is None:
        lines.extend(["Provider evidence: UNKNOWN", f"Reason: {error or 'UNKNOWN'}"])
        return _lines(lines)

    snapshot = ctx.get("snapshot") if isinstance(ctx, Mapping) else None
    if not isinstance(snapshot, Mapping):
        lines.append("Provider evidence: UNKNOWN")
        return _lines(lines)

    health = snapshot.get("provider_health")
    backlog = snapshot.get("reconciliation_backlog")
    health = health if isinstance(health, Mapping) else {}
    backlog = backlog if isinstance(backlog, Mapping) else {}

    for provider in ("REVOLUT_MERCHANT", "KUCOIN"):
        row = health.get(provider)
        if not isinstance(row, Mapping):
            lines.append(f"{provider}: UNKNOWN")
            continue
        lines.append(
            f"{provider}: {_text(row.get('status'))} | "
            f"evidence {_text(row.get('evidence_state'))} | "
            f"events {_count(row.get('event_count'))}"
        )

    lines.extend(
        [
            "",
            "Reconciliation Queue",
            f"Revolut unmatched webhook: {_count(backlog.get('revolut_unmatched_webhook'))}",
            f"KuCoin manual review required: {_count(backlog.get('kucoin_manual_review_required'))}",
            f"Payment unmatched: {_count(backlog.get('payment_unmatched'))}",
            f"Payment contradictory: {_count(backlog.get('payment_contradictory'))}",
            "",
            "Secrets and credentials are never rendered on this surface.",
        ]
    )
    return _lines(lines)


def render_billing_audit(
    context: Optional[Mapping[str, Any]] = None,
    *,
    limit: int = 10,
) -> str:
    ctx, error = _context_or_unavailable(context)
    lines = [
        "Billing Evidence Timeline",
        "",
        "READ_ONLY_DERIVED — evidence view only",
        "",
    ]
    if ctx is None:
        lines.extend(["Timeline: UNKNOWN", f"Reason: {error or 'UNKNOWN'}"])
        return _lines(lines)

    timeline = ctx.get("timeline") if isinstance(ctx, Mapping) else None
    if not isinstance(timeline, Sequence) or isinstance(timeline, (str, bytes)):
        lines.append("Timeline: UNKNOWN")
        return _lines(lines)

    recent = [row for row in timeline if isinstance(row, Mapping)][-max(1, limit):]
    if not recent:
        lines.append("No billing events observed from validated available sources.")
    else:
        for row in reversed(recent):
            correlation = row.get("correlation")
            correlation_fields = (
                sorted(str(key) for key in correlation)
                if isinstance(correlation, Mapping)
                else []
            )
            details = row.get("details")
            state = "UNKNOWN"
            if isinstance(details, Mapping):
                for key in (
                    "reconciliation_state",
                    "case_state",
                    "payment_state",
                    "state",
                    "status",
                    "delivery_result",
                ):
                    if details.get(key) is not None:
                        state = _text(details.get(key))
                        break
            corr_text = ",".join(correlation_fields) if correlation_fields else "none"
            lines.append(
                f"- {_text(row.get('source'))}: {_text(row.get('event_type'))} | "
                f"state {state} | correlation fields {corr_text}"
            )

    lines.extend(
        [
            "",
            "Raw payment proof, Telegram IDs, provider secrets and free-form support "
            "messages are not rendered here.",
        ]
    )
    return _lines(lines)
