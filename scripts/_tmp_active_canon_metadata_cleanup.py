from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "send" / "docs" / "canonical"
ACTIVE = CANON / "active"
SUPERSEDED = CANON / "superseded"
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


def _field_index(lines: list[str], labels: tuple[str, ...], max_lines: int = 35) -> int | None:
    for i in range(min(len(lines), max_lines)):
        stripped = lines[i].strip()
        if any(stripped.startswith(label) for label in labels):
            return i
    return None


def _replace_known_paths(text: str, active_names: set[str], superseded_names: set[str]) -> tuple[str, int, int]:
    proposed_to_active = 0
    active_to_superseded = 0

    for name in sorted(active_names, key=len, reverse=True):
        candidates = (
            (f"/opt/binarybot/docs/canonical/proposed/{name}", f"/opt/binarybot/docs/canonical/active/{name}"),
            (f"send/docs/canonical/proposed/{name}", f"send/docs/canonical/active/{name}"),
            (f"canonical/proposed/{name}", f"canonical/active/{name}"),
        )
        for old, new in candidates:
            count = text.count(old)
            if count:
                text = text.replace(old, new)
                proposed_to_active += count

    for name in sorted(superseded_names - active_names, key=len, reverse=True):
        candidates = (
            (f"/opt/binarybot/docs/canonical/active/{name}", f"/opt/binarybot/docs/canonical/superseded/{name}"),
            (f"send/docs/canonical/active/{name}", f"send/docs/canonical/superseded/{name}"),
            (f"canonical/active/{name}", f"canonical/superseded/{name}"),
        )
        for old, new in candidates:
            count = text.count(old)
            if count:
                text = text.replace(old, new)
                active_to_superseded += count

    return text, proposed_to_active, active_to_superseded


def cleanup_file(path: Path, active_names: set[str], superseded_names: set[str]) -> list[str]:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    changes: list[str] = []
    limit = min(len(lines), 90)

    status_i = _field_index(lines, ("Status:", "**Status:**"))
    if status_i is None:
        raise SystemExit(f"{path.name}: no Status field in first 35 lines")
    status = lines[status_i].strip()
    if "ACTIVE CANONICAL" not in status.upper() or "PROPOSED" in status.upper() or "NOT ACTIVE" in status.upper():
        newline = "\n" if lines[status_i].endswith("\n") else ""
        if status.startswith("**Status:**"):
            lines[status_i] = "**Status:** ACTIVE CANONICAL" + newline
        else:
            lines[status_i] = "Status: ACTIVE CANONICAL  " + newline
        changes.append("status -> ACTIVE CANONICAL")

    path_i = _field_index(lines, ("Path:", "Canonical Path:", "**Canonical Path:**"))
    if path_i is not None and "canonical/proposed/" in lines[path_i]:
        lines[path_i] = lines[path_i].replace("canonical/proposed/", "canonical/active/")
        changes.append("canonical path proposed -> active")

    supersession_i = _field_index(lines, ("Supersession Intent:", "**Supersession Intent:**"), max_lines=40)
    if supersession_i is not None:
        stripped = lines[supersession_i].strip()
        newline = "\n" if lines[supersession_i].endswith("\n") else ""
        if stripped.startswith("**Supersession Intent:**"):
            value = stripped[len("**Supersession Intent:**"):].strip()
            lines[supersession_i] = f"**Supersedes:** {value}" + newline
        else:
            value = stripped.split(":", 1)[1].strip()
            lines[supersession_i] = f"Supersedes: {value}  " + newline
        changes.append("supersession intent -> supersedes")

    stale_markers = (
        "until explicit promotion",
        "until explicit active promotion",
        "until explicit atomic promotion",
        "until explicit canonical promotion",
        "until explicit atomic canonical promotion",
    )
    authority_repair_count = 0
    predecessor_repair_count = 0
    for i in range(limit):
        low = lines[i].strip().lower()
        if "active predecessor until explicit promotion" in low:
            lines[i] = lines[i].replace(
                "active predecessor until explicit promotion",
                "superseded predecessor after the executed 2026-09-01 promotion",
            )
            predecessor_repair_count += 1
            continue
        if any(marker in low for marker in stale_markers) and (
            low.startswith("until ")
            or low.startswith("promotion remains")
            or " remains authoritative" in low
            or " remains active" in low
        ):
            newline = "\n" if lines[i].endswith("\n") else ""
            lines[i] = (
                f"Promotion status: ACTIVE CANONICAL under `{ACTIVATION}` and `{MASTER_NAME}`."
                + newline
            )
            authority_repair_count += 1

    if authority_repair_count:
        changes.append(f"pre-promotion authority statements -> active ({authority_repair_count})")
    if predecessor_repair_count:
        changes.append(f"predecessor status wording -> superseded ({predecessor_repair_count})")

    updated = "".join(lines)
    updated, proposed_refs, superseded_refs = _replace_known_paths(updated, active_names, superseded_names)
    if proposed_refs:
        changes.append(f"known active references proposed -> active ({proposed_refs})")
    if superseded_refs:
        changes.append(f"known predecessor references active -> superseded ({superseded_refs})")

    old_lines = original.splitlines()
    new_lines = updated.splitlines()
    if len(old_lines) != len(new_lines):
        raise SystemExit(f"{path.name}: cleanup changed line count")

    status_i_after = _field_index(new_lines, ("Status:", "**Status:**"))
    if status_i_after is None or "ACTIVE CANONICAL" not in new_lines[status_i_after].upper():
        raise SystemExit(f"{path.name}: active status not established")
    if "PROPOSED" in new_lines[status_i_after].upper() or "NOT ACTIVE" in new_lines[status_i_after].upper():
        raise SystemExit(f"{path.name}: stale proposed/not-active status remains")

    path_i_after = _field_index(new_lines, ("Path:", "Canonical Path:", "**Canonical Path:**"))
    if path_i_after is not None and "canonical/proposed/" in new_lines[path_i_after]:
        raise SystemExit(f"{path.name}: canonical Path field still points to proposed")

    for name in active_names:
        if f"canonical/proposed/{name}" in updated:
            raise SystemExit(f"{path.name}: active authority still referenced as proposed: {name}")

    for line in new_lines[:90]:
        low = line.strip().lower()
        if any(marker in low for marker in stale_markers) and (
            " remains authoritative" in low or " remains active" in low or low.startswith("until ")
        ):
            raise SystemExit(f"{path.name}: stale pre-promotion authority wording remains in opening block")

    if changes:
        path.write_text(updated, encoding="utf-8")
    return changes


def main() -> None:
    names = inventory()
    active_names = set(names)
    superseded_names = {p.name for p in SUPERSEDED.glob("*.md") if p.is_file()}

    rows: list[tuple[str, list[str]]] = []
    unchanged: list[str] = []
    for name in names:
        changes = cleanup_file(ACTIVE / name, active_names, superseded_names)
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
        "Eligible changes are limited to promotion/status/path metadata, opening authority wording, and exact path repairs for filenames whose active/superseded classification is proven by the Master Index plus repository placement. No formulas, thresholds, lifecycle rules, routing policy, permissions, Trade Physics mathematics, signal logic, runtime code, or broker behavior are changed.",
        "",
        f"Active functional inventory checked: **{len(names)}**",
        f"Files with stale promotion metadata/references repaired: **{len(rows)}**",
        f"Files already clean: **{len(unchanged)}**",
        "",
        "## Repaired files",
        "",
    ]
    if rows:
        report_lines.extend(["| File | Non-semantic repairs |", "|---|---|"])
        for name, file_changes in rows:
            report_lines.append(f"| `{name}` | {'; '.join(file_changes)} |")
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
        "PASS requires: exactly 43 Master-Index-listed active files checked; no active file declaring PROPOSED/NOT ACTIVE in its status field; no canonical Path field pointing to proposed; no reference to an active filename through a proposed path; no opening authority statement claiming a predecessor remains active pending promotion; and no runtime-code change.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
