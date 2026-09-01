from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "send" / "docs" / "canonical" / "active"
MASTER = ACTIVE / "CANONICAL_MASTER_INDEX_v2.0.0.md"

PATTERNS = (
    "not active",
    "proposed successor",
    "complete proposed",
    "proposed current-scope",
    "remains authoritative",
    "remains proposed",
    "until successor promotion",
    "until explicit promotion",
    "until explicit active promotion",
    "until explicit canonical promotion",
    "pending promotion",
    "before promotion",
    "promotion-ready",
    "promotion ready",
    "remains on canonical hold",
)


def inventory() -> list[str]:
    text = MASTER.read_text(encoding="utf-8")
    names: list[str] = []
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*`([^`]+\.md)`\s*\|", text, re.MULTILINE):
        n = int(m.group(1))
        if 1 <= n <= 43 and m.group(2) not in names:
            names.append(m.group(2))
    if len(names) != 43:
        raise SystemExit(f"expected 43 active specs, found {len(names)}")
    return names


def main() -> None:
    total = 0
    for name in inventory():
        path = ACTIVE / name
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            matches = [p for p in PATTERNS if p in low]
            if matches:
                total += 1
                print(f"{name}:{line_no}: {','.join(matches)} :: {line.strip()}")
    print(f"TOTAL_SUSPICIOUS_LINES={total}")


if __name__ == "__main__":
    main()
