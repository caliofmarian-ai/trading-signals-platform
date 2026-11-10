"""Owner-authorized, single-use reset of three diagnostic logs before boot.

Run only through the temporary maintenance deployment. Any existing durable
receipt prevents replay, including an interrupted previous attempt. This is
not a retention policy or recurring cleanup job.
"""
from __future__ import annotations

import contextlib
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

OPERATION_ID = "owner-log-reset-20261110-a1"
IDENTITY = {
    "RAILWAY_PROJECT_ID": "54752c90-3929-4854-9b50-049b5c63ab98",
    "RAILWAY_SERVICE_ID": "c2c41294-4eca-4092-8cdf-94ba57511c6e",
    "RAILWAY_ENVIRONMENT_ID": "c8e55f1a-7518-4e7b-ae38-bad46b0a4171",
}
TARGETS = (
    ("ENGINE_EVENTS_LOG", "engine_events.jsonl", "observability_engine"),
    ("ERROR_EVENTS_LOG", "error_events.jsonl", "observability_error"),
    ("FSM_EVENTS_LOG", "fsm_events.jsonl", "observability_fsm"),
)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def fsync_directory(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json(fd, payload):
    data = (json.dumps(payload, sort_keys=True) + "\n").encode()
    while data:
        written = os.write(fd, data)
        if written <= 0:
            raise OSError("Short receipt write")
        data = data[written:]
    os.fsync(fd)


def reset_logs(root, environment, lock_factory):
    """Testable core; main separately enforces exact production identity/mount."""
    root = Path(root)
    for directory in (root, root / "observability", root / "state"):
        if directory.resolve(strict=True) != directory or not directory.is_dir():
            raise ValueError("Unexpected or symlinked directory")
    receipt = root / "state" / (OPERATION_ID + ".json")
    if os.path.lexists(receipt):
        return {"operation_id": OPERATION_ID, "status": "already_claimed", "repeated_deletion": False}
    paths = []
    for env_name, name, lock_name in TARGETS:
        path = root / "observability" / name
        if environment.get(env_name, str(path)) != str(path):
            raise ValueError("Unexpected log path override")
        paths.append((path, lock_name))
    with contextlib.ExitStack() as stack:
        for _, lock_name in paths:
            stack.enter_context(lock_factory(lock_name))
        opened = []
        for path, _ in paths:
            fd = os.open(path, os.O_WRONLY | os.O_NOFOLLOW)
            stack.callback(os.close, fd)
            info = os.fstat(fd)
            current = os.stat(path, follow_symlinks=False)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino)
                    or info.st_dev != root.stat().st_dev):
                raise ValueError("Log is not an exclusive regular volume file")
            opened.append((path, fd, info))
        # Validate every target before claiming or truncating any target.
        before = os.statvfs(root)
        report = {
            "operation_id": OPERATION_ID, "status": "claimed",
            "claimed_utc": utc_now(),
            "files": [{"name": p.name, "before_bytes": s.st_size} for p, _, s in opened],
            "disk_free_before_bytes": before.f_bavail * before.f_frsize,
        }
        try:
            receipt_fd = os.open(receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            return {"operation_id": OPERATION_ID, "status": "already_claimed", "repeated_deletion": False}
        try:
            write_json(receipt_fd, report)
        finally:
            os.close(receipt_fd)
        fsync_directory(receipt.parent)
        for row, (_, fd, _) in zip(report["files"], opened):
            os.ftruncate(fd, 0)
            os.fsync(fd)
            row["after_bytes"] = os.fstat(fd).st_size
            if row["after_bytes"] != 0:
                raise RuntimeError("Unexpected writer during exclusive maintenance")
        report["cutoff_utc"] = utc_now()
        after = os.statvfs(root)
        report.update(status="completed", removed_logical_bytes=sum(s.st_size for _, _, s in opened),
                      disk_free_after_bytes=after.f_bavail * after.f_frsize)
        # The durable claim remains present throughout this atomic replacement.
        temporary = receipt.with_name(receipt.name + ".completed.tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            write_json(fd, report)
        finally:
            os.close(fd)
        os.replace(temporary, receipt)
        fsync_directory(receipt.parent)
        return report


def main():
    try:
        if any(os.environ.get(k) != v for k, v in IDENTITY.items()):
            raise ValueError("Unexpected Railway deployment identity")
        root = Path("/data")
        if os.environ.get("BINARYBOT_BASE_DIR") != str(root):
            raise ValueError("Unexpected persistent root")
        # mountinfo also detects bind mounts that os.path.ismount can miss.
        mounted = any(line.split()[4] == "/data" for line in Path("/proc/self/mountinfo").read_text().splitlines())
        if not mounted:
            raise ValueError("Persistent volume is not mounted")
        from core import storage
        report = reset_logs(root, os.environ, storage.with_lock)
        print("TSP_OWNER_LOG_RESET " + json.dumps(report, sort_keys=True), flush=True)
        return 0
    except Exception as exc:
        # Do not print exception messages, environment values or user records.
        print("TSP_OWNER_LOG_RESET " + json.dumps({"operation_id": OPERATION_ID,
              "status": "failed", "error_type": type(exc).__name__}), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
