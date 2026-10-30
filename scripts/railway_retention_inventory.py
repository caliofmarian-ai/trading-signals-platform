"""Read-only, bounded production volume inventory for future safe archiving.

This tool NEVER opens event contents, truncates or deletes files, writes to
/data, or treats an existing live JSONL file as a deletable archive. It is
intentionally one-shot, not a new background daemon. It cannot attest to
live-runner health or make historical data eligible for deletion. The output contains
allowlisted category counts and sizes only; never actual file names, event
records, identifiers, paths, symbols, prices, or secrets.

Retention minimums from send/docs/DATA_RETENTION_POLICY.md:
- routine observability: >=30 days
- admin proof/audit: >=365 days
- outcome truth: permanent
- analytics aggregates/reports: >=365 days
- configuration snapshots: >=180 days
- crash reports: >=90 days.
"""

from __future__ import annotations

import json
import os
import re
import stat
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


VERSION = "1.0.0"
EVENT_PREFIX = "TSP_STORAGE_RETENTION_DRY_RUN "
MAX_DIRECTORY_ENTRIES = 256

# Only the base names created by our append-only sinks can be considered dated
# segmented log archives. Current unsegmented files are ALWAYS kept untouched.
_EVENT_STEMS = frozenset({
    "engine_events", "fsm_events", "error_events",
    "distribution_events", "admin_events", "admin_proofs",
})
_LOG_FILENAME = re.compile(
    r"^(engine_events|fsm_events|error_events|distribution_events|"
    r"admin_events|admin_proofs)(?:_(\d{4}-\d{2}-\d{2}))?\.jsonl(?:\.gz)?$"
)
_FAMILIES = (
    "operational_observability", "administrative_proofs", "outcome_truth",
    "analytics_reports", "config_snapshots", "crash_reports",
)
_POLICY_DAYS = {
    "operational_observability": 30,
    "administrative_proofs": 365,
    "outcome_truth": None,
    "analytics_reports": 365,
    "config_snapshots": 180,
    "crash_reports": 90,
}


def _blank(family: str) -> dict[str, Any]:
    return {
        "policy_min_days": _POLICY_DAYS[family],
        "observed_files": 0,
        "observed_mib": 0.0,
        "active_unsegmented_mib": 0.0,
        "archival_candidates_unverified_mib": 0.0,
        "archival_candidates_unverified_count": 0,
        "unknown_or_protected_count": 0,
    }


def _category(directory: str, name: str) -> str:
    if directory == "observability":
        if name.startswith("admin_proofs") or name.startswith("admin_events"):
            return "administrative_proofs"
        return "operational_observability"
    return {
        "outcomes": "outcome_truth",
        "analytics/reports": "analytics_reports",
        "config_snapshots": "config_snapshots",
        "crash_reports": "crash_reports",
    }[directory]


def _archival_candidate(
    *, directory: str, name: str, family: str, now_utc: datetime
) -> bool:
    # A filename alone is NEVER permission to delete. This is a candidate for
    # separately verified backup/archive/restore, not for local cleanup.
    if directory != "observability":
        return False
    match = _LOG_FILENAME.fullmatch(name)
    if not match or match.group(1) not in _EVENT_STEMS or not match.group(2):
        return False  # protects current live *_events.jsonl
    try:
        segment_day = datetime.strptime(match.group(2), "%Y-%m-%d").date()
    except ValueError:
        return False
    if segment_day > now_utc.date():
        return False
    return segment_day < (now_utc - timedelta(days=_POLICY_DAYS[family])).date()


def collect_retention_inventory(
    *, base_dir: Path, now_ts: int | None = None, max_directory_entries: int = MAX_DIRECTORY_ENTRIES
) -> dict[str, Any]:
    """Stat only a bounded number of allowlisted entries; never read file bytes."""
    now = int(time.time()) if now_ts is None else now_ts
    if isinstance(now, bool) or not isinstance(now, int) or now <= 0:
        raise ValueError("invalid observation timestamp")
    if isinstance(max_directory_entries, bool) or not isinstance(max_directory_entries, int) or not 1 <= max_directory_entries <= 4096:
        raise ValueError("invalid entry limit")

    now_utc = datetime.fromtimestamp(now, timezone.utc)
    categories: dict[str, dict[str, Any]] = {f: _blank(f) for f in _FAMILIES}
    scopes: dict[str, str] = {}
    had_partial = False
    for directory in ("observability", "outcomes", "analytics/reports", "config_snapshots", "crash_reports"):
        location = Path(base_dir) / directory
        try:
            if location.is_symlink() or not location.is_dir():
                scopes[directory.replace("/", "_")] = "NOT_A_REAL_DIRECTORY"
                had_partial = True
                continue
            observed = 0
            with os.scandir(location) as entries:
                for entry in entries:
                    observed += 1
                    if observed > max_directory_entries:
                        had_partial = True
                        scopes[directory.replace("/", "_")] = "PARTIAL_ENTRY_CAP"
                        break
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        had_partial = True
                        continue
                    if not stat.S_ISREG(st.st_mode):
                        continue
                    family = _category(directory, entry.name)
                    row = categories[family]
                    mib = max(0, int(st.st_size)) / (1024 * 1024)
                    row["observed_files"] += 1
                    row["observed_mib"] += mib
                    match = _LOG_FILENAME.fullmatch(entry.name) if directory == "observability" else None
                    if match and not match.group(2):
                        row["active_unsegmented_mib"] += mib
                    elif _archival_candidate(
                        directory=directory, name=entry.name,
                        family=family, now_utc=now_utc,
                    ):
                        row["archival_candidates_unverified_mib"] += mib
                        row["archival_candidates_unverified_count"] += 1
                    else:
                        row["unknown_or_protected_count"] += 1
                else:
                    scopes[directory.replace("/", "_")] = "COMPLETE_BOUNDED"
        except OSError:
            scopes[directory.replace("/", "_")] = "UNREADABLE"
            had_partial = True

    for row in categories.values():
        for name in ("observed_mib", "active_unsegmented_mib", "archival_candidates_unverified_mib"):
            row[name] = round(row[name], 2)

    return {
        "component": "tsp_storage_retention_dry_run",
        "version": VERSION,
        "scope": "BOUNDED_STAT_ONLY_NO_DELETION",
        "coverage": "PARTIAL" if had_partial else "BOUNDED_COMPLETE",
        "checkpoint_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scopes": scopes,
        "categories": categories,
        "actual_freed_bytes": 0,
        "eligible_for_deletion": False,
        "unverified_candidate_bytes_are_not_reclaimable_yet": True,
        "requires_off_volume_backup_checksum_and_restore": True,
        "requires_reader_replay_compatibility": True,
    }


def main() -> None:
    root = Path(os.getenv("BINARYBOT_BASE_DIR") or "/data")
    try:
        report = collect_retention_inventory(base_dir=root)
    except Exception:
        report = {
            "component": "tsp_storage_retention_dry_run",
            "version": VERSION,
            "scope": "BOUNDED_STAT_ONLY_NO_DELETION",
            "coverage": "UNKNOWN",
            "reason": "INVENTORY_FAILED",
            "actual_freed_bytes": 0,
            "eligible_for_deletion": False,
        }
    print(EVENT_PREFIX + json.dumps(report, sort_keys=True, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
