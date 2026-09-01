from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "send" / "docs" / "canonical" / "active"
MASTER = ACTIVE / "CANONICAL_MASTER_INDEX_v2.0.0.md"
REPORT_DIR = ROOT / "audit" / "active-canon-metadata-cleanup-20260901"
REPORT = REPORT_DIR / "REPORT.md"
ACTIVATION = "CANONICAL_ACTIVATION_RECORD_20260901.md"
MASTER_NAME = "CANONICAL_MASTER_INDEX_v2.0.0.md"


def inventory() -> list[str]:
    text = MASTER.read_text(encoding="utf-8")
    names: list[str] = []
    for match in re.finditer(r"^\|\s*(\d+)\s*\|\s*`([^`]+\.md)`\s*\|", text, re.MULTILINE):
        number = int(match.group(1))
        name = match.group(2)
        if 1 <= number <= 43 and name not in names:
            names.append(name)
    if len(names) != 43:
        raise SystemExit(f"expected 43 active functional specs, found {len(names)}")
    missing = [name for name in names if not (ACTIVE / name).is_file()]
    if missing:
        raise SystemExit(f"master-index active files missing: {missing}")
    return names


def cleanup_file(path: Path) -> list[str]:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    changes: list[str] = []

    # Promotion metadata is constrained to the document preamble / authority block.
    limit = min(len(lines), 90)

    status_seen = False
    for i in range(min(limit, 35)):
        stripped = lines[i].strip()
        if stripped.startswith("Status:") or stripped.startswith("**Status:**"):
            status_seen = True
            if "ACTIVE CANONICAL" not in stripped.upper() or "PROPOSED" in stripped.upper() or "NOT ACTIVE" in stripped.upper():
                newline = "\n" if lines[i].endswith("\n") else ""
                if stripped.startswith("**Status:**"):
                    lines[i] = "**Status:** ACTIVE CANONICAL" + newline
                else:
                    lines[i] = "Status: ACTIVE CANONICAL  " + newline
                changes.append("status -> ACTIVE CANONICAL")
            break

    if not status_seen:
        raise SystemExit(f"{path.name}: no Status field in first 35 lines")

    for i in range(min(limit, 35)):
        stripped = lines[i].strip()
        if stripped.startswith("Path:") or stripped.startswith("**Canonical Path:**"):
            if "/canonical/proposed/" in lines[i] or "canonical/proposed/" in lines[i]:
                lines[i] = lines[i].replace("/canonical/proposed/", "/canonical/active/").replace("canonical/proposed/", "canonical/active/")
                changes.append("path proposed -> active")
            break

    for i in range(min(limit, 40)):
        stripped = lines[i].strip()
        if stripped.startswith("Supersession Intent:"):
            newline = "\n" if lines[i].endswith("\n") else ""
            value = stripped.split(":", 1)[1].strip()
            lines[i] = f"Supersedes: {value}  {newline}"
            changes.append("supersession intent -> supersedes")
            break

    stale_markers = (
        "until explicit promotion",
        "until explicit active promotion",
        "until explicit atomic promotion",
        "until explicit canonical promotion",
        "until explicit atomic canonical promotion",
    )
    authority_repaired = False
    for i in range(limit):
        low = lines[i].strip().lower()
        if any(marker in low for marker in stale_markers) and (
            "remain" in low or "authoritative" in low or "active" in low
        ):
            newline = "\n" if lines[i].endswith("\n") else ""
            lines[i] = (
                f"Promotion status: ACTIVE CANONICAL under `{ACTIVATION}` and `{MASTER_NAME}`."
                + newline
            )
            changes.append("pre-promotion authority sentence -> active authority")
            authority_repaired = True
            break

    updated = "".join(lines)

    # Hard safety: only the first 90 physical lines may change.
    old_lines = original.splitlines()
    new_lines = updated.splitlines()
    if len(old_lines) != len(new_lines):
        raise SystemExit(f"{path.name}: cleanup changed line count")
    changed_indices = [i + 1 for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b]
    if any(i > 90 for i in changed_indices):
        raise SystemExit(f"{path.name}: semantic-body line changed outside metadata window: {changed_indices}")

    # Post-cleanup authority checks for the preamble.
    head35 = "\n".join(new_lines[:35])
    if "Status: PROPOSED" in head35 or "NOT ACTIVE" in head35.upper():
        raise SystemExit(f"{path.name}: stale status remains in preamble")
    if "canonical/proposed/" in head35:
        raise SystemExit(f"{path.name}: stale proposed path remains in preamble")

    if changes:
        path.write_text(updated, encoding="utf-8")
    return changes


def main() -> None:
    names = inventory()
    rows: list[tuple[str, list[str]]] = []
    unchanged: list[str] = []
    for name in names:
        changes = cleanup_file(ACTIVE / name)
        if changes:
            rows.append((name, changes))
        else:
            unchanged.append(name)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# ACTIVE CANON METADATA CLEANUP REPORT — 2026-09-01",
        "",
        "Status: AUDIT / NON-SEMANTIC DOCUMENTATION CLEANUP",
        "",
        "## Canonical basis",
        "",
        f"- `{ACTIVATION}` declares the 43 Master-Index-listed functional specifications active canonical authority and explicitly classifies embedded pre-promotion wording as a documentation-cleanup defect.",
        f"- `{MASTER_NAME}` is the sole authoritative Master Index and lists all 43 active functional specifications.",
        "- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md` classifies non-semantic documentation cleanup as cosmetic and requires traceability without hidden contract mutation.",
        "",
        "## Scope guard",
        "",
        "Only preamble/authority metadata within the first 90 physical lines was eligible for modification. No formulas, thresholds, lifecycle rules, routing policy, permissions, Trade Physics mathematics, signal logic, runtime code, or broker behavior were changed.",
        "",
        f"Active functional inventory checked: **{len(names)}**",
        f"Files with stale promotion metadata repaired: **{len(rows)}**",
        f"Files already clean: **{len(unchanged)}**",
        "",
        "## Repaired files",
        "",
    ]
    if rows:
        report_lines.extend(["| File | Metadata repairs |", "|---|---|"])
        for name, changes in rows:
            report_lines.append(f"| `{name}` | {'; '.join(changes)} |")
    else:
        report_lines.append("None.")

    report_lines += ["", "## Already-clean active files", ""]
    if unchanged:
        report_lines.extend(f"- `{name}`" for name in unchanged)
    else:
        report_lines.append("None.")

    report_lines += [
        "",
        "## Result",
        "",
        "PASS if repository diff contains only the listed active-document metadata fields plus this audit report and temporary automation files used solely to execute/validate the cleanup. Temporary automation must be removed before PR review.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
