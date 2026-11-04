"""Prospective TPS cutoffs 0..20; no production strategy control or publisher.

Consumes only the independently persisted, FSM-accepted OPEN research cohort.
See audit/gate-sweep-research-20261104/PROTOCOL.md for targets and limitations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re

from core import storage
from intelligence import shadow_model_time_research as source


PROTOCOL = "SHADOW_GATE_SWEEP_V1"
LEVELS = tuple(range(21))
MIN_DECISIVE = 100
MIN_UTC_DAYS = 3
MAX_UNKNOWN_FRACTION = 0.05
MAX_BYTES = 128 * 1024
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_FALSE_FLAGS = ("production_gate_changed", "automatic_selection_allowed",
                "broker_executed", "profitability_established")
_STATUSES = {"WAITING_FOR_OPPORTUNITIES", "COLLECTING", "WAITING_EMBARGO",
             "PAUSED_BASELINE_CHANGED", "REVIEW_REQUIRED"}


def _targets() -> dict:
    return {"decisive_nonoverlapping": MIN_DECISIVE, "utc_dates": MIN_UTC_DAYS,
            "max_unknown_fraction": MAX_UNKNOWN_FRACTION}


def enabled() -> bool:
    return (os.getenv("SHADOW_GATE_SWEEP_RESEARCH_ENABLED", "").strip().lower()
            in {"1", "true", "yes", "on"}) and source.enabled() and not source._on(
                "SHADOW_GATE_TIMEBOX_RESEARCH_ENABLED")


def threshold(level: int) -> float:
    if type(level) is not int or level not in LEVELS:
        raise ValueError("research level must be an integer from 0 to 20")
    return float(level * 5)


def _positive(value) -> float:
    if type(value) not in {int, float} or not math.isfinite(value) or value <= 0:
        raise ValueError("invalid research observation time")
    return float(value)


def _digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")).hexdigest()


def _path(name: str) -> Path:
    directory = Path(storage.root_path("analytics", "shadow_gate_sweep_research"))
    path = directory / name
    if directory.is_symlink() or path.is_symlink():
        raise ValueError("research paths cannot be symlinks")
    return path


def _read(path: Path) -> dict:
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("research state exceeds its bound")
    value = json.loads(raw)
    # Reject non-finite JSON recursively rather than silently rewriting it.
    json.dumps(value, allow_nan=False)
    if not isinstance(value, dict):
        raise ValueError("invalid research state")
    return value


def _save(path: Path, value: dict) -> None:
    # Account for the exact pretty-printed bytes produced by atomic storage,
    # otherwise a report can pass this check and exceed the bounded reader.
    if len((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")) > MAX_BYTES:
        raise ValueError("research state exceeds its bound")
    storage.save_json_atomic(str(path), value)


def _wilson(wins: int, decisive: int) -> list[float] | None:
    if not decisive:
        return None
    z = 1.959963984540054
    p = wins / decisive
    denominator = 1 + z * z / decisive
    center = p + z * z / (2 * decisive)
    half = z * math.sqrt(p * (1 - p) / decisive + z * z / (4 * decisive ** 2))
    return [100 * max(0.0, (center - half) / denominator),
            100 * min(1.0, (center + half) / denominator)]


def _metrics(rows: list[dict]) -> dict:
    counts = {name: 0 for name in ("WIN", "LOSS", "DRAW", "UNKNOWN")}
    pending, dates, finalized = 0, set(), []
    for row in rows:
        if row["state"] != "FINAL":
            pending += 1
            continue
        counts[row["outcome"]] += 1
        finalized.append(row["finalized_ts"])
        if row["outcome"] in {"WIN", "LOSS"}:
            dates.add(datetime.fromtimestamp(row["created_ts"], timezone.utc).date())
    decisive = counts["WIN"] + counts["LOSS"]
    total_final = sum(counts.values())
    return {
        "outcomes": counts, "pending": pending, "decisive_sample": decisive,
        "hypothetical_win_rate_percent": 100 * counts["WIN"] / decisive if decisive else None,
        "wilson_95_iid_reference_percent": _wilson(counts["WIN"], decisive),
        "unknown_fraction": counts["UNKNOWN"] / total_final if total_final else None,
        "utc_dates_with_decisive_observations": len(dates),
        "first_registered_ts": min((r["created_ts"] for r in rows), default=None),
        "last_registered_ts": max((r["created_ts"] for r in rows), default=None),
        "first_finalized_ts": min(finalized, default=None),
        "last_finalized_ts": max(finalized, default=None),
    }


def _valid_metrics(value) -> bool:
    if not isinstance(value, dict) or set(value) != set(_metrics([])):
        return False
    counts = value["outcomes"]
    if (not isinstance(counts, dict) or set(counts) != {"WIN", "LOSS", "DRAW", "UNKNOWN"}
        or any(type(n) is not int or n < 0 for n in counts.values())
        or sum(counts.values()) > source.MAX_RECORD_FILES
        or type(value["pending"]) is not int or not 0 <= value["pending"] <= source.MAX_PENDING
        or type(value["decisive_sample"]) is not int
        or value["decisive_sample"] != counts["WIN"] + counts["LOSS"]
        or type(value["utc_dates_with_decisive_observations"]) is not int
        or not 0 <= value["utc_dates_with_decisive_observations"] <= value["decisive_sample"]):
        return False
    decisive, total = value["decisive_sample"], sum(counts.values())
    expected_rate = 100 * counts["WIN"] / decisive if decisive else None
    if (value["hypothetical_win_rate_percent"] != expected_rate
        or (expected_rate is not None and type(value["hypothetical_win_rate_percent"]) not in {int, float})):
        return False
    if value["wilson_95_iid_reference_percent"] != _wilson(counts["WIN"], decisive):
        return False
    if (value["unknown_fraction"] != (counts["UNKNOWN"] / total if total else None)
        or (total and type(value["unknown_fraction"]) not in {int, float})):
        return False
    for field in ("first_registered_ts", "last_registered_ts", "first_finalized_ts", "last_finalized_ts"):
        if value[field] is not None:
            _positive(value[field])
    return True


def _deadline(row: dict) -> float:
    # Chosen from registration-time policy, independent of its eventual label.
    return (row["created_ts"] + source.MAX_ENTRY_DELAY_SECONDS + row["horizon_seconds"]
            + source.MAX_SAMPLE_DELAY_SECONDS)


def _nonoverlapping(rows: list[dict]) -> list[dict]:
    selected, reserved_until = [], 0.0
    for row in sorted(rows, key=lambda r: (r["created_ts"], r["record_id"])):
        if row["created_ts"] > reserved_until:
            selected.append(row)
            reserved_until = _deadline(row)
    return selected


def _features(row: dict) -> tuple[str, float] | None:
    digest = row.get("parameter_bundle_sha256")
    snapshot = row["decision_snapshot"]
    physics = (snapshot.get("score") or {}).get("trade_physics") or {}
    tps = physics.get("TPS")
    if (not isinstance(digest, str) or not _HASH.fullmatch(digest)
        or type(tps) not in {int, float} or not math.isfinite(tps) or not 0 <= tps <= 100
        or any(not isinstance(row.get(key), str) or not row[key].strip()
               for key in ("strategy_version", "strategy_spec"))):
        return None
    signature = _digest({
        "parameter_bundle_sha256": digest, "source_protocol": row["protocol"],
        "decision_schema": snapshot.get("schema_version"),
        "strategy_version": row["strategy_version"], "strategy_spec": row["strategy_spec"],
        "physics_formula": physics.get("formula_version"),
        "physics_feature_schema": physics.get("feature_schema_version"),
    })
    return signature, float(tps)


def _valid_state(state: dict) -> bool:
    if (set(state) != {"protocol", "started_at", "baseline_signature", "active_level",
                      "level_started_at", "completed_levels", "collection_targets"}
        or state["protocol"] != PROTOCOL or not isinstance(state["completed_levels"], list)
        or len(state["completed_levels"]) > len(LEVELS) or state["collection_targets"] != _targets()):
        return False
    _positive(state["started_at"])
    _positive(state["level_started_at"])
    signature = state["baseline_signature"]
    if signature is not None and (not isinstance(signature, str) or not _HASH.fullmatch(signature)):
        return False
    completed = state["completed_levels"]
    expected = len(completed) if len(completed) < len(LEVELS) else None
    if state["active_level"] != expected or (expected is not None and type(state["active_level"]) is not int):
        return False
    previous_end = state["started_at"]
    for level, item in enumerate(completed):
        if (not isinstance(item, dict) or set(item) != {
            "level", "minimum_tps", "started_at", "closed_at", "metrics", "evidence_digest"}
            or type(item["level"]) is not int or item["level"] != level
            or item["minimum_tps"] != threshold(level)
            or not _valid_metrics(item["metrics"])
            or not isinstance(item["evidence_digest"], str) or not _HASH.fullmatch(item["evidence_digest"])):
            return False
        if not previous_end <= _positive(item["started_at"]) <= _positive(item["closed_at"]):
            return False
        if not _ready(item["metrics"]):
            return False
        previous_end = item["closed_at"]
    return state["level_started_at"] >= previous_end


def _ready(metrics: dict) -> bool:
    return (metrics["decisive_sample"] >= MIN_DECISIVE
            and metrics["utc_dates_with_decisive_observations"] >= MIN_UTC_DAYS
            and metrics["pending"] == 0
            and metrics["unknown_fraction"] is not None
            and metrics["unknown_fraction"] <= MAX_UNKNOWN_FRACTION)


def update(*, now_ts: float) -> dict:
    """Observe/retry one research update; persist only this experiment's ledger."""
    if not enabled():
        return {"status": "DISABLED"}
    now = _positive(now_ts)
    with storage.with_lock("shadow_gate_sweep_research", timeout_sec=0.2):
        path = _path("experiment.json")
        if path.exists():
            state = _read(path)
            if not _valid_state(state):
                raise ValueError("invalid experiment ledger; refusing to restart it")
        else:
            state = {"protocol": PROTOCOL, "started_at": now, "baseline_signature": None,
                     "active_level": 0, "level_started_at": now, "completed_levels": [],
                     "collection_targets": _targets()}
            _save(path, state)  # Freeze the prospective boundary before reading outcomes.
        if now < state["started_at"]:
            raise ValueError("experiment clock moved before activation")
        rows, missing, changed, earlier = [], 0, 0, 0
        for row in sorted(source.snapshot_records(), key=lambda r: (r["created_ts"], r["record_id"])):
            if row["created_ts"] < state["started_at"]:
                earlier += 1
                continue
            if row["created_ts"] > now or (row["state"] == "FINAL" and row["finalized_ts"] > now):
                raise ValueError("future research evidence")
            features = _features(row)
            if features is None:
                missing += 1
                continue
            signature, tps = features
            if state["baseline_signature"] is None:
                state["baseline_signature"] = signature
            if signature != state["baseline_signature"]:
                changed += 1
                continue
            rows.append({**row, "research_tps": tps})
        thinned = _nonoverlapping(rows)
        table = [{"level": level, "minimum_tps": threshold(level),
                  "all": _metrics([r for r in rows if r["research_tps"] >= threshold(level)]),
                  "common_nonoverlapping": _metrics([r for r in thinned if r["research_tps"] >= threshold(level)])}
                 for level in LEVELS]
        level = state["active_level"]
        active_rows = [] if level is None else [r for r in rows
            if r["created_ts"] >= state["level_started_at"] and r["research_tps"] >= threshold(level)]
        selected = _nonoverlapping(active_rows)
        active_metrics = _metrics(selected)
        if level is not None and not changed and _ready(active_metrics):
            state["completed_levels"].append({
                "level": level, "minimum_tps": threshold(level),
                "started_at": state["level_started_at"], "closed_at": now,
                "metrics": active_metrics, "evidence_digest": _digest(selected),
            })
            state["active_level"] = level + 1 if level < LEVELS[-1] else None
            state["level_started_at"] = max(now, max((_deadline(r) for r in active_rows), default=now))
            level, active_metrics = state["active_level"], _metrics([])
        status = ("PAUSED_BASELINE_CHANGED" if changed else "REVIEW_REQUIRED" if level is None
                  else "WAITING_EMBARGO" if state["level_started_at"] > now
                  else "COLLECTING" if any(active_metrics["outcomes"].values()) or active_metrics["pending"]
                  else "WAITING_FOR_OPPORTUNITIES")
        report = {
            "protocol": PROTOCOL, "enabled": True, "truth_domain": "HYPOTHETICAL_RESEARCH",
            "cohort": "FSM_ACCEPTED_OPEN_ONLY", "horizon_source": "UNCALIBRATED_MODEL_TIME",
            "status": status, "started_at": state["started_at"], "active_level": level,
            "active_minimum_tps": threshold(level) if level is not None else None,
            "level_started_at": state["level_started_at"], "active_metrics": active_metrics,
            "completed_levels": state["completed_levels"], "levels": table,
            "excluded": {"before_activation": earlier, "missing_provenance_or_tps": missing,
                         "baseline_changed": changed},
            "collection_targets": _targets(),
            **{key: False for key in _FALSE_FLAGS},
        }
        _save(path, state)
        _save(_path("summary.json"), {"protocol": PROTOCOL, "observed_at": now,
                                    "is_heartbeat": False, "summary": report})
        return report


def evidence_summary(report: dict) -> dict:
    """Small deploy marker; the complete paired table remains in the audit cache."""
    keys = ("protocol", "enabled", "truth_domain", "cohort", "horizon_source", "status",
            "started_at", "active_level", "active_minimum_tps", "level_started_at",
            "active_metrics", "excluded", "collection_targets", *_FALSE_FLAGS)
    return {**{key: report[key] for key in keys},
            "completed_level_count": len(report["completed_levels"]),
            "levels": [{"level": row["level"], "minimum_tps": row["minimum_tps"],
                        **{key: row["all"][key] for key in (
                            "outcomes", "pending", "decisive_sample", "hypothetical_win_rate_percent")}}
                       for row in report["levels"]]}


def read_summary_status() -> dict | None:
    """Read bounded aggregates; never overlay malformed or private cache fields."""
    try:
        value = _read(_path("summary.json"))
        if set(value) != {"protocol", "observed_at", "is_heartbeat", "summary"}:
            return None
        report = value["summary"]
        if (value["protocol"] != PROTOCOL or value["is_heartbeat"] is not False
            or not isinstance(report, dict) or set(report) != {
                "protocol", "enabled", "truth_domain", "cohort", "horizon_source", "status",
                "started_at", "active_level", "active_minimum_tps", "level_started_at", "active_metrics",
                "completed_levels", "levels", "excluded", "collection_targets", *_FALSE_FLAGS}
            or report["protocol"] != PROTOCOL or report["enabled"] is not True
            or report["truth_domain"] != "HYPOTHETICAL_RESEARCH"
            or report["cohort"] != "FSM_ACCEPTED_OPEN_ONLY"
            or report["horizon_source"] != "UNCALIBRATED_MODEL_TIME"
            or report["status"] not in _STATUSES
            or any(report[k] is not False for k in _FALSE_FLAGS)):
            return None
        _positive(value["observed_at"])
        state = {k: report[k] for k in ("protocol", "started_at", "active_level", "level_started_at", "completed_levels", "collection_targets")}
        state["baseline_signature"] = None
        if not _valid_state(state) or not _valid_metrics(report["active_metrics"]):
            return None
        level = report["active_level"]
        if report["active_minimum_tps"] != (threshold(level) if level is not None else None):
            return None
        if not isinstance(report["levels"], list) or len(report["levels"]) != len(LEVELS):
            return None
        for level, row in enumerate(report["levels"]):
            if (not isinstance(row, dict) or set(row) != {"level", "minimum_tps", "all", "common_nonoverlapping"}
                or type(row["level"]) is not int or row["level"] != level
                or row["minimum_tps"] != threshold(level)
                or not _valid_metrics(row["all"]) or not _valid_metrics(row["common_nonoverlapping"])):
                return None
        if (report["collection_targets"] != _targets()
            or not isinstance(report["excluded"], dict) or set(report["excluded"]) != {
                "before_activation", "missing_provenance_or_tps", "baseline_changed"}
            or any(type(v) is not int or not 0 <= v <= source.MAX_RECORD_FILES for v in report["excluded"].values())):
            return None
        return value
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return None
