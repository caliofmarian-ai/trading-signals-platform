"""One-shot owner-authorized study cutoff; no strategy/account/log changes.

Run only at service boot, before the ordinary worker, with the volume mounted.
Default is read-only. All current rows are validated with the repository's real
validator. Settled cross-boundary evidence is preserved separately, never mixed
into the new cohort. A durable receipt prevents a second reset on restart.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import stat
import time

OP = "owner-study-cutover-20261110-c1"
SOURCE_OP = "owner-log-reset-20261110-a1"
CUT_TEXT = "2026-11-10T13:27:51.140918+00:00"
CUT = Decimal("1794317271.140918")
MAX_BYTES = 4 * 1024 * 1024
PROTOCOL = "PROSPECTIVE_PHYSICAL_V3_EXPIRY_V5"
MARKER = "owner_history_epoch"
REL = "analytics/physical_v3_expiry_calibration/recent_history_state.json"
IDENTITY = {
    "RAILWAY_PROJECT_ID": "54752c90-3929-4854-9b50-049b5c63ab98",
    "RAILWAY_SERVICE_ID": "c2c41294-4eca-4092-8cdf-94ba57511c6e",
    "RAILWAY_ENVIRONMENT_ID": "c8e55f1a-7518-4e7b-ae38-bad46b0a4171",
}


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("DUPLICATE_KEY")
        out[key] = value
    return out


def strict(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("SIZE_LIMIT")
    def reject(_):
        raise ValueError("NONFINITE_JSON")
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=reject)
    if not isinstance(value, dict):
        raise ValueError("OBJECT_REQUIRED")
    encode(value)
    return value


def stamp(value):
    if type(value) in (int, float):
        result = Decimal(str(value))
    elif isinstance(value, str):
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("TIMEZONE_REQUIRED")
        delta = date.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
        result = Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / 1000000
    else:
        raise ValueError("INVALID_CLOCK")
    if not result.is_finite() or result <= 0:
        raise ValueError("INVALID_CLOCK")
    return result


def clocks(value, depth=0):
    if depth > 64:
        raise ValueError("DEPTH_LIMIT")
    late = pending = False
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"outcome", "status"} and item in ("PENDING", "RESERVED"):
                pending = True
            if key.endswith(("_ts", "_at", "_utc", "_timestamp")) or key == "timestamp":
                if item is not None:
                    late = late or stamp(item) >= CUT
                    # Validate every clock, even after a late one is found.
                    stamp(item)
            else:
                a, b = clocks(item, depth + 1)
                late, pending = late or a, pending or b
    elif isinstance(value, list):
        for item in value:
            a, b = clocks(item, depth + 1)
            late, pending = late or a, pending or b
    return late, pending


def check_receipt(receipt):
    if (receipt.get("operation_id") != SOURCE_OP or receipt.get("status") != "completed"
            or stamp(receipt.get("cutoff_utc")) != CUT):
        raise ValueError("ORIGINAL_CUTOFF_REQUIRED")
    files = receipt.get("files")
    names = {"engine_events.jsonl", "error_events.jsonl", "fsm_events.jsonl"}
    if (not isinstance(files, list) or len(files) != 3
            or any(not isinstance(r, dict) for r in files)
            or {r.get("name") for r in files} != names
            or any(type(r.get("after_bytes")) is not int or r["after_bytes"] != 0 for r in files)):
        raise ValueError("ORIGINAL_RESET_NOT_CONFIRMED")


def plan(state, receipt, validator):
    check_receipt(receipt)
    encode(state)
    if state.get("protocol") != PROTOCOL or not isinstance(state.get("records"), dict):
        raise ValueError("CURRENT_V5_REQUIRED")
    if MARKER in state:
        raise ValueError("EXISTING_EPOCH_REQUIRES_RECEIPT")
    validator(deepcopy(state))
    kept, boundary, removed = {}, {}, {}
    for key, row in state["records"].items():
        if stamp(row["created_ts"]) >= CUT:
            kept[key] = deepcopy(row)
            continue
        late, pending = clocks(row)
        delivery = row.get("study_delivery") or {}
        if (row.get("state") != "FINAL" or pending
                or ((delivery.get("entry") or {}).get("status") == "API_ACCEPTED"
                    and not delivery.get("result"))):
            raise ValueError("OLD_RECORD_STILL_IN_FLIGHT")
        (boundary if late else removed)[key] = deepcopy(row)
    result = {
        "operation_id": OP, "source_operation_id": SOURCE_OP,
        "cutoff_utc": CUT_TEXT, "source_sha256": digest(state),
        "records_before": len(state["records"]), "new_records_preserved": len(kept),
        "old_records_removed": len(removed), "boundary_records_preserved_separately": len(boundary),
        "new_records_sha256": digest(kept), "boundary_records_sha256": digest(boundary),
        "all_post_cutoff_rows_unchanged": True,
        "other_history_files_changed": False,
        "cumulative_timing_counters_changed": False,
        "capacity_rejections_lifetime": state.get("capacity_rejections"),
    }
    candidate = deepcopy(state)
    candidate["records"] = kept
    candidate["started_ts"] = float(CUT)
    candidate[MARKER] = {**result, "boundary_rule": "created_ts >= cutoff",
                         "boundary_evidence_not_used_for_new_cohort": True}
    validator(deepcopy(candidate))
    if len(encode(candidate)) > MAX_BYTES:
        raise ValueError("CANDIDATE_SIZE_LIMIT")
    # Separate complete evidence, including predecessor context, is needed for
    # results/receipts observed after cutoff on an earlier-created study.
    preserved = deepcopy(state)
    preserved["records"] = boundary
    preserved[MARKER] = {"operation_id": OP, "cutoff_utc": CUT_TEXT,
                         "scope": "CROSS_BOUNDARY_EVIDENCE_NOT_ACTIVE_CALIBRATION"}
    validator(deepcopy(preserved))
    result["candidate_sha256"] = digest(candidate)
    result["boundary_file_sha256"] = digest(preserved)
    return result, candidate, preserved


def read_regular(path):
    path = Path(path)
    if path.resolve(strict=True) != path:
        raise ValueError("SYMLINKED_SOURCE")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("EXCLUSIVE_REGULAR_FILE_REQUIRED")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(MAX_BYTES + 1)
        return strict(raw)
    finally:
        os.close(fd)


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def create_durable(path, value):
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("UNSAFE_PARENT")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(encode(value))
        stream.flush()
        os.fsync(stream.fileno())
    sync_dir(path.parent)


def run(root, validator, *, apply=False):
    """Caller MUST hold the canonical study lock with workers stopped."""
    root = Path(root)
    source = root / REL
    original_receipt = root / "state" / (SOURCE_OP + ".json")
    done = root / "state" / (OP + ".json")
    boundary = root / "state" / (OP + "-boundary-evidence.json")
    check_receipt(read_regular(original_receipt))
    if os.path.lexists(done):
        receipt = read_regular(done)
        state = read_regular(source)
        validator(deepcopy(state))
        if (receipt.get("operation_id") != OP or receipt.get("status") != "completed"
                or (state.get(MARKER) or {}).get("operation_id") != OP):
            raise ValueError("INCOMPLETE_OR_CONFLICTING_OPERATION_NO_REPLAY")
        return {"operation_id": OP, "status": "already_completed", "repeated_deletion": False,
                "cutoff_utc": CUT_TEXT, "current_records": len(state["records"])}
    state = read_regular(source)
    result, candidate, cross = plan(state, read_regular(original_receipt), validator)
    if not apply:
        return {**result, "status": "dry_run_validated", "source_modified": False,
                "validator": "canonical_physical_expiry_calibration.validate"}
    # Claim durably before mutation. Any interruption refuses automatic replay.
    # Never re-copy an old snapshot over records created by a resumed worker.
    create_durable(done, {**result, "status": "claimed", "claimed_utc": datetime.now(timezone.utc).isoformat()})
    if cross["records"]:
        create_durable(boundary, cross)
        if digest(read_regular(boundary)) != result["boundary_file_sha256"]:
            raise ValueError("BOUNDARY_PRESERVATION_FAILED")
    temp = source.with_name(source.name + "." + OP + ".tmp")
    create_durable(temp, candidate)
    if (digest(read_regular(source)) != result["source_sha256"]
            or digest(read_regular(temp)) != result["candidate_sha256"]):
        raise ValueError("SOURCE_CHANGED_BEFORE_COMMIT")
    os.replace(temp, source)
    sync_dir(source.parent)
    actual = read_regular(source)
    validator(deepcopy(actual))
    if digest(actual) != result["candidate_sha256"] or digest(actual["records"]) != result["new_records_sha256"]:
        raise ValueError("COMMIT_VERIFICATION_FAILED")
    result.update(status="completed", completed_utc=datetime.now(timezone.utc).isoformat(),
                  source_modified=True, validator="canonical_physical_expiry_calibration.validate")
    complete = done.with_name(done.name + ".completed.tmp")
    create_durable(complete, result)
    os.replace(complete, done)
    sync_dir(done.parent)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if any(os.environ.get(k) != v for k, v in IDENTITY.items()):
            raise ValueError("UNEXPECTED_DEPLOYMENT_IDENTITY")
        root = Path("/data")
        if os.environ.get("BINARYBOT_BASE_DIR") != str(root) or root.resolve(strict=True) != root:
            raise ValueError("UNEXPECTED_ROOT")
        if not any(row.split()[4] == str(root) for row in Path("/proc/self/mountinfo").read_text().splitlines()):
            raise ValueError("VOLUME_NOT_MOUNTED")
        from core import storage
        from intelligence import physical_expiry_calibration as calibration
        if Path(storage.root_path(*REL.split("/"))) != root / REL:
            raise ValueError("CANONICAL_STORAGE_PATH_MISMATCH")
        with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=3):
            report = run(root, calibration.validate, apply=args.apply)
        print("TSP_OWNER_STUDY_CUTOVER " + json.dumps(report, sort_keys=True), flush=True)
        if args.apply and report["status"] in {"completed", "already_completed"}:
            summary = calibration.summary(now_ts=time.time())
            fields = ("unique_entry_experiments", "finalized_entry_experiments", "study_open_now_api_accepted", "study_results_api_accepted")
            print("TSP_OWNER_STUDY_CUTOVER_SUMMARY " + json.dumps({k: summary.get(k) for k in fields}, sort_keys=True), flush=True)
        return 0
    except Exception as exc:
        safe_codes = {"OLD_RECORD_STILL_IN_FLIGHT", "EXISTING_EPOCH_REQUIRES_RECEIPT",
                      "INCOMPLETE_OR_CONFLICTING_OPERATION_NO_REPLAY", "SOURCE_CHANGED_BEFORE_COMMIT"}
        print("TSP_OWNER_STUDY_CUTOVER " + json.dumps({"operation_id": OP,
            "status": "failed", "error_type": type(exc).__name__,
            "reason": str(exc) if str(exc) in safe_codes else "VALIDATION_OR_IO_FAILURE"}), flush=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
