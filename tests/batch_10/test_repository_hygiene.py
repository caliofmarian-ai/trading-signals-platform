from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPLICIT_HISTORY_PREFIXES = (
    "send/_archive/",
    "send/docs/_deprecated/",
    "send/docs/canonical/deprecated/",
)


def _tracked_files() -> list[str]:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        text=True,
    ).splitlines()


def _is_live_adjacent_backup_or_temp(path: str) -> bool:
    if not path.startswith("send/"):
        return False
    if path.startswith(EXPLICIT_HISTORY_PREFIXES):
        return False

    name = path.rsplit("/", 1)[-1].lower()
    return (
        name.endswith(".bak")
        or ".bak_" in name
        or ".bak." in name
        or name.endswith((".orig", ".rej", ".tmp", ".temp", ".swp", ".swo", "~"))
        or " - copy." in name
    )


def test_gitignore_covers_repository_hygiene_contract():
    content = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    for needle in (
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache/",
        ".cache/",
        "venv/",
        ".venv/",
        "*.log",
        "send/observability/*.jsonl",
        "send/outcomes/*.jsonl",
        "send/outcomes/open_now_registry.json",
        "send/outcomes/outcomes_index.json",
        "send/state/*.json",
        "*.tmp",
        "*.temp",
        ".idea/",
        ".vscode/",
        ".DS_Store",
        "Thumbs.db",
        "send/**/*.bak",
        "send/**/*.bak_*",
        "send/**/*.bak.*",
        "send/**/*.orig",
        "send/**/*.rej",
        "!send/_archive/**",
        "!send/docs/_deprecated/**",
        "!send/docs/canonical/deprecated/**",
    ):
        assert needle in content


def test_no_tracked_generated_runtime_artifacts():
    matches = []
    for path in _tracked_files():
        if "__pycache__/" in path or path.endswith((".pyc", ".pyo", ".pyd")):
            matches.append(path)
        elif path.startswith("send/venv/"):
            matches.append(path)
        elif path.startswith("send/observability/") and path.endswith(".jsonl"):
            matches.append(path)
        elif path.startswith("send/state/") and path.endswith(".json"):
            matches.append(path)
        elif path.startswith("send/outcomes/") and (
            path.endswith(".jsonl")
            or path.endswith("open_now_registry.json")
            or path.endswith("outcomes_index.json")
        ):
            matches.append(path)
        elif path.startswith("send/analytics/reports/daily_strategy_audit_"):
            matches.append(path)
        elif path == "send/config/.env.example":
            matches.append(path)
        elif path.startswith("send/config/") and ".bak." in path:
            matches.append(path)
    assert matches == []


def test_no_live_adjacent_backup_duplicate_or_temp_artifacts():
    matches = [path for path in _tracked_files() if _is_live_adjacent_backup_or_temp(path)]
    assert matches == []
