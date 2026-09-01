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
    names=[]
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*`([^`]+\.md)`\s*\|", text, re.MULTILINE):
        n=int(m.group(1))
        if 1 <= n <= 43 and m.group(2) not in names:
            names.append(m.group(2))
    if len(names) != 43:
        raise SystemExit(f"expected 43 active specs, found {len(names)}")
    return names


def family(name: str) -> str:
    return re.sub(r"_v\d+\.\d+\.\d+\.md$", "", name)


def main() -> None:
    active = active_inventory()
    by_family = {family(n): n for n in active}
    superseded = [p.name for p in SUPERSEDED.glob("*.md")]
    old_to_new = {
        old: by_family[family(old)]
        for old in superseded
        if family(old) in by_family and by_family[family(old)] != old
    }
    findings=[]
    skip_markers=("supersedes", "superseded", "historical", "predecessor", "provenance", "/superseded/")
    for name in active:
        lines=(ACTIVE/name).read_text(encoding="utf-8").splitlines()
        for line_no,line in enumerate(lines[:120],1):
            low=line.lower()
            if any(m in low for m in skip_markers):
                continue
            for old,new in old_to_new.items():
                if old in line:
                    findings.append((name,line_no,old,new,line.strip()))
    for row in findings:
        print(f"{row[0]}:{row[1]}: {row[2]} -> {row[3]} :: {row[4]}")
    print(f"TOTAL_STALE_AUTHORITY_REFS={len(findings)}")

if __name__ == "__main__":
    main()
