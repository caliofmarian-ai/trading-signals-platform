from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "send" / "docs" / "canonical"
ACTIVE = CANON / "active"
SUPERSEDED = CANON / "superseded"
MASTER = ACTIVE / "CANONICAL_MASTER_INDEX_v2.0.0.md"


def active_inventory() -> list[str]:
    text = MASTER.read_text(encoding="utf-8")
    names: list[str] = []
    for match in re.finditer(r"^\|\s*(\d+)\s*\|\s*`([^`]+\.md)`\s*\|", text, re.MULTILINE):
        number = int(match.group(1))
        name = match.group(2)
        if 1 <= number <= 43 and name not in names:
            names.append(name)
    if len(names) != 43:
        raise SystemExit(f"FAIL: expected 43 active specs, found {len(names)}")
    return names


def family(name: str) -> str:
    return re.sub(r"_v\d+\.\d+\.\d+\.md$", "", name)


def main() -> None:
    active = active_inventory()
    active_by_family = {family(name): name for name in active}
    old_to_new: dict[str, str] = {}
    for path in SUPERSEDED.glob("*.md"):
        old = path.name
        key = family(old)
        current = active_by_family.get(key)
        if current and current != old:
            old_to_new[old] = current

    skip_markers = (
        "supersedes",
        "superseded",
        "historical",
        "predecessor",
        "provenance",
        "/superseded/",
    )
    findings: list[tuple[str, int, str, str, str]] = []
    for name in active:
        lines = (ACTIVE / name).read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines[:120], 1):
            lowered = line.lower()
            if any(marker in lowered for marker in skip_markers):
                continue
            for old, current in old_to_new.items():
                if old in line:
                    findings.append((name, line_no, old, current, line.strip()))

    if findings:
        for name, line_no, old, current, text in findings:
            print(f"{name}:{line_no}: {old} -> {current} :: {text}")
        raise SystemExit(f"FAIL: stale current-authority references found: {len(findings)}")

    print("PASS: 43 active canonical specifications checked")
    print("PASS: stale current-authority references to superseded versions = 0")


if __name__ == "__main__":
    main()
