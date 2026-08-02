# /opt/binarybot/core/storage.py
# BinaryBot — Atomic Persistence Layer (canonical)
# - JSON load/save atomic
# - JSONL append-only
# - cross-process locks (simple lockfiles) with stale-lock recovery
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
import socket
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

JsonType = Union[Dict[str, Any], List[Any]]
_PACKAGE_BASE_DIR = Path(__file__).resolve().parents[1]


class StoragePathError(ValueError):
    pass


def base_dir() -> str:
    raw = os.getenv("BINARYBOT_BASE_DIR", "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            raise StoragePathError(f"BINARYBOT_BASE_DIR must be an absolute path: {raw}")
        if not candidate.exists():
            raise StoragePathError(f"BINARYBOT_BASE_DIR does not exist: {candidate}")
        if not candidate.is_dir():
            raise StoragePathError(f"BINARYBOT_BASE_DIR must point to a directory: {candidate}")
        return str(candidate)
    return str(_PACKAGE_BASE_DIR)


def root_path(*parts: str) -> str:
    return os.path.join(base_dir(), *parts)


def config_path(name: str) -> str:
    config_dir = Path(root_path("config"))
    if not config_dir.is_dir():
        raise StoragePathError(f"config directory not found under base dir: {config_dir}")
    return str(config_dir / name)


def state_path(name: str) -> str:
    return root_path("state", name)


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


# ---------------------------------------------------------------------------
# Stale-lock detection helpers
# ---------------------------------------------------------------------------

def _current_deployment_id() -> str:
    """Return a deployment-scoped identifier for ownership comparison."""
    for name in ("RAILWAY_DEPLOYMENT_ID", "RAILWAY_SERVICE_ID", "RUN_ID"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _safe_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return ""


def _read_lock_metadata(lock_path: str) -> Dict[str, Any]:
    """Parse ownership metadata written into a lock file.

    Format:  ``key=value`` tokens separated by whitespace.
    Returns an empty dict on any read or parse failure (treated as malformed).
    """
    try:
        with open(lock_path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except Exception:
        return {}
    result: Dict[str, Any] = {}
    for token in content.split():
        if "=" in token:
            k, _, v = token.partition("=")
            result[k.strip()] = v.strip()
    return result


def _is_pid_alive(pid: int) -> bool:
    """Return True when *pid* refers to a running process in the current OS context."""
    # PID 0 and negative PIDs are not real owning processes.
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # PID exists but belongs to a different UID — consider alive to be safe.
        return True
    except Exception:
        return False


# A lock is always considered stale when it is older than this threshold,
# even if the PID appears alive (e.g. PID reuse).
_LOCK_STALE_AGE_SEC: float = 300.0


def _lock_is_stale(lock_path: str) -> bool:
    """Return True when the lock at *lock_path* can be safely reclaimed.

    A lock is stale when ANY of the following are true:
    1. Its owning PID is no longer running in this OS context.
    2. Its deployment ID differs from the current deployment (different Redeploy).
    3. It is older than ``_LOCK_STALE_AGE_SEC`` seconds.
    4. Its metadata is malformed and it is at least 60 seconds old.

    A lock is NOT reclaimed when the PID is alive AND the deployment matches.
    """
    try:
        meta = _read_lock_metadata(lock_path)
        if not meta:
            # Malformed or empty — fall back to age check.
            try:
                age = time.time() - os.path.getmtime(lock_path)
                return age > 60.0
            except Exception:
                return True

        lock_pid_str = meta.get("pid", "")
        lock_deploy = meta.get("deploy", "")
        lock_ts_str = meta.get("ts", "")

        current_deploy = _current_deployment_id()

        # Different deployment → always stale (cross-redeploy orphan).
        if lock_deploy and current_deploy and lock_deploy != current_deploy:
            return True

        # Explicit age threshold (handles PID reuse on long-lived systems).
        if lock_ts_str:
            try:
                lock_age = time.time() - float(lock_ts_str)
                if lock_age > _LOCK_STALE_AGE_SEC:
                    return True
            except ValueError:
                pass

        # Dead PID.
        if lock_pid_str:
            try:
                lock_pid = int(lock_pid_str)
                if not _is_pid_alive(lock_pid):
                    return True
            except ValueError:
                pass

        return False
    except Exception:
        return False


def _reclaim_stale_lock(lock_path: str, lock_name: str) -> None:
    """Atomically remove a lock file that has been confirmed stale.

    Emits a structured diagnostic to stderr so that Railway log aggregation
    captures the reclaim event without requiring a full logging stack.
    """
    try:
        meta = _read_lock_metadata(lock_path)
        payload = {
            "event": "stale_lock_reclaimed",
            "component": "storage_lock",
            "lock_name": lock_name,
            "lock_path": lock_path,
            "stale_pid": meta.get("pid"),
            "stale_deploy": meta.get("deploy"),
            "stale_ts": meta.get("ts"),
            "current_pid": os.getpid(),
            "current_deploy": _current_deployment_id(),
            "reclaim_ts": time.time(),
        }
        try:
            print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)
        except Exception:
            pass
        os.remove(lock_path)
    except FileNotFoundError:
        # Already removed by a concurrent reclaim — that is fine.
        pass
    except Exception:
        pass


@contextlib.contextmanager
def with_lock(lock_name: str, base_dir: Optional[str] = None, timeout_sec: float = 10.0) -> Iterator[None]:
    """Cross-process exclusive lock using O_EXCL lockfile creation.

    Ownership metadata written to the lock file enables safe stale-lock
    detection and reclaim when:

    - The owning PID no longer exists (killed process, crash, SIGKILL).
    - The lock was created by a different Railway deployment.
    - The lock is older than ``_LOCK_STALE_AGE_SEC`` (300 s by default).

    A lock held by a demonstrably live process on the current deployment
    is never stolen.

    lock_name examples:
      - "focus_state"
      - "dist_state"
      - "settings"
      - "active_symbols"
      - "outcomes"
      - "telegram_ui_state"
      - "restart_guard"
    """
    lock_dir = base_dir or state_path(".locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_path = os.path.join(lock_dir, f"{lock_name}.lock")

    start = time.time()
    fd: Optional[int] = None

    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            elapsed = time.time() - start
            if elapsed >= timeout_sec:
                # One last stale check before giving up — the PID may have died
                # during our wait and the reclaim was not triggered yet.
                if _lock_is_stale(lock_path):
                    _reclaim_stale_lock(lock_path, lock_name)
                    continue
                raise TimeoutError(
                    f"Timed out acquiring lock '{lock_name}' after {elapsed:.1f}s"
                )
            # Check for stale lock on every contention cycle.
            if _lock_is_stale(lock_path):
                _reclaim_stale_lock(lock_path, lock_name)
                continue
            time.sleep(0.05)

    try:
        # Write rich ownership metadata for stale-detection on future acquisitions.
        try:
            meta_line = (
                f"pid={os.getpid()} "
                f"ts={time.time():.3f} "
                f"deploy={_current_deployment_id()} "
                f"host={_safe_hostname()}\n"
            )
            os.write(fd, meta_line.encode("utf-8"))
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