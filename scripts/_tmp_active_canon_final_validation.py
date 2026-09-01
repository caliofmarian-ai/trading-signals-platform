from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "send" / "docs" / "canonical"
ACTIVE = CANON / "active"
SUPERSEDED = CANON / "superseded"
MASTER = ACTIVE / "CANONICAL_MASTER_INDEX_v2.0.0.md"

ALLOWED_HISTORICAL_REFS = {
    ("ALGO_SPEC_v3.0.0.md", "ALGO_SPEC_v2.0.0.md"),
    ("TIME_MODEL_UNIFIED_CANON_v3.0.0.md", "TIME_MODEL_UNIFIED_CANON_v2.0.0.md"),
}

BANNED_CURRENT_STATE_FRAGMENTS = (
    "This document is the proposed unified authority",
    "this document is proposed as the detailed mathematical authority",
    "This proposed canon resolves",
    "Merge of this proposal does not authorize",
    "No runtime code change is authorized by this proposal alone",
    "No code behavior is authorized by this proposal alone",
    "Before this document can become active",
    "Until atomic promotion,",
    "current proposed canonical graph",
    "active/proposed canon",
    "proposed target contract",
    "current proposed defaults are structural constants",
    "initial proposed directional speed uses",
    "This v2 proposal locks the following if promoted",
    "once this successor set is promoted and implemented",
    "once this canon is promoted and implemented",
    "delegated to `TRADE_PHYSICS_MODEL_SPEC_v1.0.0` once promoted",
    "Must use the unified v3 time vocabulary once promoted",
    "The proposed v3 Model Time chain is",
    "in the proposed v3 model",
    "The canonical proposed chain is",
    "The canonical proposed initial weights are",
    "The proposed strategic contract must expose",
    "structural model constants in this proposed v1 contract",
    "Because the proposed canonical v3 Time Model",
)

STATUS_RE = re.compile(r"(?im)^\s*\*{0,2}Status:\*{0,2}\s*ACTIVE CANONICAL\b")
PATH_RE = re.compile(r"(?im)^\s*\*{0,2}(?:Canonical\s+)?Path:\*{0,2}\s*`?([^`\n]+)`?\s*$")


def inventory() -> list[str]:
    text = MASTER.read_text(encoding="utf-8")
    names: list[str] = []
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*`([^`]+\.md)`\s*\|", text, re.MULTILINE):
        n = int(m.group(1))
        name = m.group(2)
        if 1 <= n <= 43 and name not in names:
            names.append(name)
    if len(names) != 43:
        raise SystemExit(f"FAIL master inventory: expected 43, got {len(names)}")
    return names


def family(name: str) -> str:
    return re.sub(r"_v\d+\.\d+\.\d+\.md$", "", name)


def main() -> None:
    active = inventory()
    active_by_family = {family(n): n for n in active}

    old_to_new: dict[str, str] = {}
    for p in SUPERSEDED.glob("*.md"):
        current = active_by_family.get(family(p.name))
        if current and current != p.name:
            old_to_new[p.name] = current

    errors: list[str] = []
    authority_hits = 0
    allowed_history_hits = 0
    declared_paths_checked = 0

    for name in active:
        path = ACTIVE / name
        if not path.exists():
            errors.append(f"missing active file: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        opening = text[:3000]

        if not STATUS_RE.search(opening):
            errors.append(f"{name}: ACTIVE CANONICAL status missing in opening metadata")

        path_match = PATH_RE.search(opening)
        if path_match:
            declared_paths_checked += 1
            declared = path_match.group(1).strip()
            if f"canonical/active/{name}" not in declared:
                errors.append(f"{name}: declared canonical path is not current active path: {declared}")

        for fragment in BANNED_CURRENT_STATE_FRAGMENTS:
            if fragment in text:
                errors.append(f"{name}: stale current-state fragment remains: {fragment}")

        for line_no, line in enumerate(lines[:120], 1):
            low = line.lower()
            if any(marker in low for marker in ("supersedes", "superseded", "historical", "predecessor", "provenance", "/superseded/")):
                continue
            for old, current in old_to_new.items():
                if old not in line:
                    continue
                authority_hits += 1
                if (name, old) in ALLOWED_HISTORICAL_REFS and "active canonical successor to" in low:
                    allowed_history_hits += 1
                    continue
                errors.append(f"{name}:{line_no}: stale current-authority ref {old} -> {current}: {line.strip()}")

    if authority_hits != allowed_history_hits:
        errors.append(f"authority accounting mismatch: hits={authority_hits} allowed_history={allowed_history_hits}")
    if allowed_history_hits != 2:
        errors.append(f"expected exactly 2 allowed predecessor-history refs, got {allowed_history_hits}")

    if errors:
        print("\n".join(f"FAIL: {e}" for e in errors))
        raise SystemExit(f"FAIL final active-canon validation errors={len(errors)}")

    print("PASS: active functional specs checked = 43")
    print(f"PASS: declared active canonical paths checked = {declared_paths_checked}")
    print("PASS: current-authority refs to superseded versions = 0")
    print("PASS: allowed explicit predecessor-history refs = 2")
    print("PASS: banned stale current-state fragments = 0")
    print("PASS: ACTIVE CANONICAL status metadata aligned across all 43 specs")


if __name__ == "__main__":
    main()
