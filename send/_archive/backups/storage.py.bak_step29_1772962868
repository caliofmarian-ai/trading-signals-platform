# /opt/binarybot/core/storage.py
# BinaryBot — Atomic Persistence Layer (canonical)
# - JSON load/save atomic
# - JSONL append-only
# - cross-process locks (simple lockfiles)
#
# Hard rules:
# - no module writes JSON directly (must use this)
# - JSON writes must be atomic (tmp + fsync + replace)
# - JSONL is append-only
#
from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
from typing import Any, Dict, Iterator, List, Optional, Union

JsonType = Union[Dict[str, Any], List[Any]]


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def _fsync_dir(dir_path: str) -> None:
    # Ensure directory entry is durable after os.replace on Linux.
    try:
        fd = os.open(dir_path, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception:
        # best effort
        pass


def load_json(path: str, default: Optional[JsonType] = None) -> JsonType:
    """
    Load JSON file. If missing or invalid, returns default (or {}).
    Never raises on missing file; may raise on permission errors.
    """
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        # If corrupted, return default but do NOT overwrite automatically.
        return default


def save_json_atomic(path: str, obj: JsonType) -> None:
    """
    Atomic JSON write:
    - write to temp file in same directory
    - fsync temp
    - replace target
    - fsync directory
    """
    _ensure_dir(path)
    dir_path = os.path.dirname(path) or "."
    # Use temp in same directory so os.replace is atomic on same filesystem.
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=dir_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)
        _fsync_dir(dir_path)
    finally:
        # If something failed before replace, remove tmp file.
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def append_jsonl(path: str, record: Dict[str, Any]) -> None:
    """
    Append a single JSON record as one line (append-only).
    - ensures directory exists
    - flush + fsync for durability (safe but slightly slower)
    """
    _ensure_dir(path)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


@contextlib.contextmanager
def with_lock(lock_name: str, base_dir: str = "/opt/binarybot/state/.locks", timeout_sec: float = 10.0) -> Iterator[None]:
    """
    Cross-process lock using lockfile + O_EXCL create.
    This works fine for a single host.

    lock_name examples:
      - "focus_state"
      - "dist_state"
      - "settings"
      - "active_symbols"
      - "outcomes"
    """
    os.makedirs(base_dir, exist_ok=True)
    lock_path = os.path.join(base_dir, f"{lock_name}.lock")

    start = time.time()
    fd: Optional[int] = None

    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            if (time.time() - start) >= timeout_sec:
                raise TimeoutError(f"Timed out acquiring lock: {lock_name}")
            time.sleep(0.05)

    try:
        # Write pid + ts for debugging
        try:
            os.write(fd, f"pid={os.getpid()} ts={time.time():.3f}\n".encode("utf-8"))
        except Exception:
            pass
        yield
    finally:
        try:
            if fd is not None:
                os.close(fd)
        except Exception:
            pass
        try:
            os.remove(lock_path)
        except Exception:
            pass