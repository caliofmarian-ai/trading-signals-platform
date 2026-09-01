from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "send" / "docs" / "canonical" / "active"
MASTER = ACTIVE / "CANONICAL_MASTER_INDEX_v2.0.0.md"
OUT = ROOT / "audit" / "active-canon-metadata-cleanup-20260901" / "PROMOTION_LANGUAGE_FINDINGS.md"

PATTERNS = (
    "proposed",
    "proposal",
    "promotion",
    "promoted",
    "promote",
    "pending",
    "until atomic",
    "once promoted",
    "after promotion",
    "before promotion",
)


def inventory() -> list[str]:
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


def main() -> None:
    findings: list[tuple[str, int, str, str]] = []
    for name in inventory():
        for line_no, line in enumerate((ACTIVE / name).read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            matches = sorted({pattern for pattern in PATTERNS if pattern in low})
            if matches:
                findings.append((name, line_no, ", ".join(matches), line.strip()))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ACTIVE CANON PROMOTION-LANGUAGE FINDINGS",
        "",
        "Active specs checked: **43**",
        f"Lines requiring classification: **{len(findings)}**",
        "",
        "| File | Line | Match | Source line |",
        "|---|---:|---|---|",
    ]
    for name, line_no, matches, text in findings:
        safe = text.replace("|", "\\|")
        lines.append(f"| `{name}` | {line_no} | {matches} | {safe} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PROMOTION_LANGUAGE_FINDINGS={len(findings)}")


if __name__ == "__main__":
    main()
