"""Read-only, truth-separated canonical-v3 lifecycle observation.

This reports per-stage evidence presence, not causal conversion or profit.
Only actual canonical event families are counted; historical adapters are
explicitly excluded. All counts are bounded by window/source availability.
"""

from __future__ import annotations

import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Callable, Dict, Mapping, Optional

from core import event_schema_migration, storage
from core.jsonl_parser import iter_jsonl


STAGES = ("PRE", "CONFIRM", "OPEN_NOW")
MAX_WINDOW_DAYS = 30
MAX_SOURCE_BYTES = 16 * 1024 * 1024
_ENGINE_EVENT_TYPES = frozenset(
    {"decision_evaluated", "fsm_transition", "signal_execution_result"}
)
_DISTRIBUTION_EVENT_TYPES = frozenset(
    {"route_publish_result", "signal_stage_visible"}
)


def _utc(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _path(name: str) -> str:
    root = os.getenv("OBS_DIR") or storage.root_path("observability")
    override = "ENGINE_EVENTS_LOG" if name == "engine" else "DIST_EVENTS_LOG"
    filename = "engine_events.jsonl" if name == "engine" else "distribution_events.jsonl"
    return os.getenv(override) or str(Path(root) / filename)


def _signal(event: Mapping[str, Any]) -> Optional[str]:
    value = event.get("signal_id")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _stage(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value in STAGES else None


def _stages_snapshot(data: Mapping[str, set[str]], present: bool) -> Dict[str, Optional[int]]:
    return {
        stage: len(data[stage]) if present else None
        for stage in STAGES
    }


def _source(
    path: str,
    event_types: frozenset[str],
    start_ms: int,
    end_ms: int,
    consume: Callable[[Dict[str, Any]], bool],
) -> Dict[str, Any]:
    """Process bounded JSONL without retaining records, raw IDs or file bodies."""
    info: Dict[str, Any] = {
        "status": "UNKNOWN",
        "reason": "NO_PRIMARY_V3_EVIDENCE_IN_WINDOW",
        "primary_rows": 0,
        "invalid_rows": 0,
        "historical_excluded_rows": 0,
        "out_of_window_rows": 0,
        "duplicate_event_rows": 0,
    }
    seen_event_ids: set[str] = set()
    try:
        if Path(path).stat().st_size > MAX_SOURCE_BYTES:
            info["reason"] = "SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN"
            return info
    except FileNotFoundError:
        info["reason"] = "SOURCE_FILE_NOT_FOUND"
        return info
    except OSError:
        info["reason"] = "SOURCE_FILE_UNREADABLE"
        return info

    try:
        for event, error in iter_jsonl(path):
            if error is not None:
                info["invalid_rows"] += 1
                continue
            event_type = event.get("event_type")
            if not isinstance(event_type, str):
                info["invalid_rows"] += 1
                continue
            if event_type not in event_types:
                continue
            if (
                event_schema_migration.classify_event_identity(event)
                != event_schema_migration.PRIMARY_V3
            ):
                info["historical_excluded_rows"] += 1
                continue
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id.strip():
                info["invalid_rows"] += 1
                continue
            event_id = event_id.strip()
            epoch_ms = event.get("ts_epoch_ms")
            if isinstance(epoch_ms, bool) or not isinstance(epoch_ms, int) or epoch_ms <= 0:
                info["invalid_rows"] += 1
                continue
            if not start_ms <= epoch_ms <= end_ms:
                info["out_of_window_rows"] += 1
                continue
            if event_id in seen_event_ids:
                info["duplicate_event_rows"] += 1
                continue
            seen_event_ids.add(event_id)
            if not consume(event):
                info["invalid_rows"] += 1
                continue
            info["primary_rows"] += 1
    except OSError:
        # Do not report a partially scanned file as complete evidence.
        return {
            **info,
            "status": "UNKNOWN",
            "reason": "SOURCE_READ_INTERRUPTED",
            "primary_rows": 0,
        }

    if info["primary_rows"]:
        info["status"] = "OBSERVED"
        info["reason"] = "PRIMARY_V3_EVIDENCE_OBSERVED"
    return info


def build_funnel(
    *,
    range_days: int = 1,
    now_ts: int | None = None,
    engine_path: str | None = None,
    distribution_path: str | None = None,
) -> Dict[str, Any]:
    """Build evidence cohorts. Unobserved stages remain UNKNOWN, not invented zero.

    A stage-level signal ID can appear in more than one family, but those
    families never inherit authority from one another. Cross-stage rates are
    deliberately omitted because window censoring prevents causal inference.
    """
    if isinstance(range_days, bool) or not isinstance(range_days, int):
        raise ValueError("range_days must be an integer")
    if not 1 <= range_days <= MAX_WINDOW_DAYS:
        raise ValueError("range_days must be between 1 and 30")
    if now_ts is None:
        now = int(time.time())
    elif isinstance(now_ts, bool) or not isinstance(now_ts, int) or now_ts <= 0:
        raise ValueError("now_ts must be a positive integer")
    else:
        now = now_ts

    start = now - range_days * 86400
    start_ms, end_ms = start * 1000, now * 1000

    strategy = {stage: set() for stage in STAGES}
    fsm = {stage: set() for stage in STAGES}
    candidates = {stage: set() for stage in STAGES}
    published = {stage: set() for stage in STAGES}
    visible = {stage: set() for stage in STAGES}
    first_visibility: Dict[str, Dict[str, int]] = {stage: {} for stage in STAGES}

    families: Counter[str] = Counter()
    decision_kinds: Counter[str] = Counter()
    unlinked_actionable = 0

    def consume_engine(event: Dict[str, Any]) -> bool:
        nonlocal unlinked_actionable
        kind = event["event_type"]
        data = event.get("data")
        if not isinstance(data, dict):
            return False
        if kind == "decision_evaluated":
            decision_kind = data.get("decision_kind")
            if not isinstance(decision_kind, str) or decision_kind not in (*STAGES, "REJECT", "NO_SIGNAL"):
                return False
            families[kind] += 1
            decision_kinds[decision_kind] += 1
            if decision_kind in STAGES:
                signal_id = _signal(event)
                if signal_id is None:
                    unlinked_actionable += 1
                else:
                    strategy[decision_kind].add(signal_id)
            return True

        stage = _stage(event.get("stage"))
        signal_id = _signal(event)
        if kind == "fsm_transition":
            families[kind] += 1
            requested = _stage(data.get("requested_stage"))
            accepted = _stage(data.get("accepted_stage"))
            if (
                requested is not None
                and requested == accepted
                and stage == requested
                and data.get("stage_handoff_ready") is True
                and signal_id is not None
            ):
                fsm[requested].add(signal_id)
            return True

        if kind == "signal_execution_result":
            phase = data.get("execution_phase")
            if not isinstance(phase, str) or phase not in {"PRE_DISTRIBUTION", "POST_DISTRIBUTION"}:
                return False
            families[kind] += 1
            if (
                phase == "PRE_DISTRIBUTION"
                and data.get("signal_event_available") is True
                and stage is not None
                and signal_id is not None
            ):
                candidates[stage].add(signal_id)
                families["candidate"] += 1
            return True

        return False

    def consume_distribution(event: Dict[str, Any]) -> bool:
        kind = event["event_type"]
        data = event.get("data")
        if not isinstance(data, dict):
            return False
        stage = _stage(event.get("stage"))
        signal_id = _signal(event)
        if stage is None or signal_id is None:
            return False
        if kind == "route_publish_result":
            result = data.get("publish_result")
            if not isinstance(result, str) or result not in {
                "PUBLISHED",
                "FAILED",
                "SKIPPED_SILENT",
                "SKIPPED_LIMIT",
                "SKIPPED_DISABLED",
                "DUPLICATE_SUPPRESSED",
            }:
                return False
            families[kind] += 1
            if result == "PUBLISHED":
                transport = data.get("transport")
                if not isinstance(transport, dict) or transport.get("ok") is not True:
                    return False
                published[stage].add(signal_id)
                families["published_route_row"] += 1
            return True

        if kind == "signal_stage_visible":
            if data.get("visibility_result") != "PUBLISHED":
                return False
            ref = data.get("publication_evidence_ref")
            if not isinstance(ref, str) or not ref.strip():
                return False
            families[kind] += 1
            visible[stage].add(signal_id)
            ts_ms = int(event["ts_epoch_ms"])
            prior = first_visibility[stage].get(signal_id)
            if prior is None or ts_ms < prior:
                first_visibility[stage][signal_id] = ts_ms
            return True
        return False

    source_engine = _source(
        engine_path or _path("engine"),
        _ENGINE_EVENT_TYPES, start_ms, end_ms, consume_engine,
    )
    source_distribution = _source(
        distribution_path or _path("distribution"),
        _DISTRIBUTION_EVENT_TYPES, start_ms, end_ms, consume_distribution,
    )

    # A file whose read is interrupted must never support derived counts.
    engine_ok = source_engine["status"] == "OBSERVED"
    dist_ok = source_distribution["status"] == "OBSERVED"
    strategy_present = engine_ok and families["decision_evaluated"] > 0
    fsm_present = engine_ok and families["fsm_transition"] > 0
    candidate_present = engine_ok and families["candidate"] > 0
    published_present = dist_ok and families["route_publish_result"] > 0
    visible_present = dist_ok and families["signal_stage_visible"] > 0

    lead_times: list[float] = []
    if visible_present:
        for signal_id, pre_ms in first_visibility["PRE"].items():
            open_ms = first_visibility["OPEN_NOW"].get(signal_id)
            if open_ms is not None and open_ms > pre_ms:
                lead_times.append((open_ms - pre_ms) / 1000.0)

    status = "OBSERVED" if engine_ok and dist_ok else (
        "PARTIAL" if engine_ok or dist_ok else "UNKNOWN"
    )
    return {
        "status": status,
        "truth_policy": "SEPARATE_STRATEGY_FSM_EXECUTION_DISTRIBUTION",
        "window_days": range_days,
        "window_start_utc": _utc(start),
        "window_end_utc": _utc(now),
        "sources": {"engine": source_engine, "distribution": source_distribution},
        "decision_evaluation_rows": families["decision_evaluated"] if strategy_present else None,
        "decision_kind_rows": {
            key: decision_kinds[key] for key in (*STAGES, "REJECT", "NO_SIGNAL")
        } if strategy_present else {},
        "unlinked_actionable_strategy_rows": unlinked_actionable if strategy_present else None,
        "strategy_stage_signals": _stages_snapshot(strategy, strategy_present),
        "fsm_accepted_signals": _stages_snapshot(fsm, fsm_present),
        "signal_event_candidates": _stages_snapshot(candidates, candidate_present),
        "published_route_signals": _stages_snapshot(published, published_present),
        "visible_stage_signals": _stages_snapshot(visible, visible_present),
        "pre_to_open_visible_matched_pairs": len(lead_times) if visible_present else None,
        "pre_to_open_lead_median_seconds": (
            round(float(median(lead_times)), 2) if lead_times else None
        ),
        "pre_to_open_pairs_at_least_30_seconds": (
            sum(value >= 30 for value in lead_times) if lead_times else None
        ),
        "open_candidate_published_overlap": (
            len(candidates["OPEN_NOW"] & published["OPEN_NOW"])
            if candidate_present and published_present else None
        ),
        "open_published_visible_overlap": (
            len(published["OPEN_NOW"] & visible["OPEN_NOW"])
            if published_present and visible_present else None
        ),
        "conversion_rate_percent": None,
        "market_win_rate_percent": None,
        "limitations": (
            "Window boundaries can censor earlier stages and later outcomes. "
            "Per-family counts and observed signal-ID overlap do not establish "
            "causal conversion, message receipt, market outcome or broker execution."
        ),
    }


def render_funnel_summary(snapshot: Mapping[str, Any]) -> str:
    """Compact operator text with no sensitive signal/chat identifiers."""
    def shown(row: Any) -> str:
        if not isinstance(row, Mapping):
            return "UNKNOWN"
        vals = [row.get(stage) for stage in STAGES]
        return " / ".join("UNKNOWN" if v is None else str(v) for v in vals)

    sources = snapshot.get("sources") or {}
    eng = sources.get("engine") or {}
    dist = sources.get("distribution") or {}
    pairs = snapshot.get("pre_to_open_visible_matched_pairs")
    lead = snapshot.get("pre_to_open_lead_median_seconds")
    count_30 = snapshot.get("pre_to_open_pairs_at_least_30_seconds")
    source_status = (
        f"engine {eng.get('status', 'UNKNOWN')} / "
        f"distribution {dist.get('status', 'UNKNOWN')}"
    )
    lines = [
        f"Lifecycle evidence — trailing {snapshot.get('window_days', 'UNKNOWN')}d UTC",
        f"Sources: {source_status}",
        "Stage order: PRE / CONFIRM / OPEN_NOW",
        f"Strategy IDs: {shown(snapshot.get('strategy_stage_signals'))}",
        f"FSM accepted IDs: {shown(snapshot.get('fsm_accepted_signals'))}",
        f"SignalEvent candidate IDs: {shown(snapshot.get('signal_event_candidates'))}",
        f"Published route IDs: {shown(snapshot.get('published_route_signals'))}",
        f"Visible stage IDs: {shown(snapshot.get('visible_stage_signals'))}",
        (
            "Observed PRE to OPEN visibility pairs: "
            + ("UNKNOWN" if pairs is None else str(pairs))
        ),
        (
            "Matched-pair median lead (seconds): "
            + ("UNKNOWN" if lead is None else str(lead))
            + " | >=30s: "
            + ("UNKNOWN" if count_30 is None else str(count_30))
        ),
        "Cross-stage conversion, delivery receipt and market win-rate: UNKNOWN.",
    ]
    invalid = sum(int(x.get("invalid_rows") or 0) for x in (eng, dist))
    historic = sum(int(x.get("historical_excluded_rows") or 0) for x in (eng, dist))
    duplicate = sum(int(x.get("duplicate_event_rows") or 0) for x in (eng, dist))
    if invalid or historic or duplicate:
        lines.append(
            f"Evidence quality: invalid {invalid}, historical excluded {historic}, "
            f"duplicate events {duplicate}"
        )
    return "\n".join(lines)
