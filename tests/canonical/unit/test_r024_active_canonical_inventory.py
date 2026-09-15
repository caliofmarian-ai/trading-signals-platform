"""R-024 inventory guard; document self-status reconciliation is a separate gate.

The functional inventory comes ONLY from the active Master Index's numbered
inventory section. Governance records, historical references and candidates are
not discovered by globbing the active directory or by hardcoding a file list.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ACTIVE_DIR = REPO_ROOT / "send/docs/canonical/active"
MASTER_INDEX = ACTIVE_DIR / "CANONICAL_MASTER_INDEX_v2.0.0.md"
_DECLARATION = re.compile(
    r"^Canonical functional inventory:\s*\*\*(\d+) unique active functional specifications\*\*\.?\s*$",
    re.MULTILINE,
)
_SECTION = re.compile(r"^## 4\. Complete active functional inventory[ \t]*$", re.MULTILINE)
_FILENAME = re.compile(r"`([A-Z][A-Z0-9_]*?)_v(\d+\.\d+\.\d+)\.md`")
_SEPARATOR = re.compile(r":?-{3,}:?")


def _parse_inventory(text: str) -> tuple[tuple[str, str], ...]:
    """Reject ambiguous/incomplete authority inventories without rewriting prose."""
    declarations = _DECLARATION.findall(text)
    sections = list(_SECTION.finditer(text))
    if len(declarations) != 1 or len(sections) != 1:
        raise ValueError("Expected exactly one inventory declaration and section")
    expected = int(declarations[0])
    if expected < 1:
        raise ValueError("Functional inventory must not be empty")
    tail = text[sections[0].end():]
    boundary = re.search(r"^## ", tail, re.MULTILINE)
    if boundary is None:
        raise ValueError("Missing inventory section boundary")
    rows: list[tuple[int, str, str, str]] = []
    fence: tuple[str, int] | None = None
    for raw in tail[:boundary.start()].splitlines():
        line = raw.strip()
        marker = re.match(r"(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, suffix = marker.groups()
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1] and not suffix.strip():
                fence = None
            continue
        if fence is not None or not line.startswith("|"):
            continue
        if not line.endswith("|"):
            raise ValueError("Malformed inventory table row")
        columns = [part.strip() for part in line[1:-1].split("|")]
        if len(columns) != 6:
            raise ValueError("Expected six inventory columns")
        if columns == ["#", "Canonical filename", "Version", "Status", "Domain", "Authority role"]:
            continue
        if all(_SEPARATOR.fullmatch(part) for part in columns):
            continue
        if not re.fullmatch(r"[1-9]\d*", columns[0]):
            raise ValueError("Invalid functional inventory ordinal")
        filename = _FILENAME.fullmatch(columns[1])
        if filename is None:
            raise ValueError("Inventory entry must be a versioned canonical leaf filename")
        domain, version = filename.groups()
        if columns[2] != version:
            raise ValueError("Filename and inventory version disagree")
        if columns[3] != "Active Canonical":
            raise ValueError("Non-active entry in functional authority inventory")
        if not columns[4] or not columns[5]:
            raise ValueError("Missing domain or authority role")
        rows.append((int(columns[0]), columns[1][1:-1], version, domain))
    if fence is not None:
        raise ValueError("Unclosed code fence in inventory section")
    if len(rows) != expected:
        raise ValueError("Declared functional count does not match parsed rows")
    if [row[0] for row in rows] != list(range(1, expected + 1)):
        raise ValueError("Inventory ordinals must be unique, consecutive and ordered")
    if len({row[3] for row in rows}) != expected:
        raise ValueError("More than one active version of the same canonical domain")
    return tuple((row[1], row[2]) for row in rows)


def _index(rows: str, count: int = 1, suffix: str = "") -> str:
    """Synthetic parser input, never runtime or production evidence."""
    return (
        f"Canonical functional inventory: **{count} unique active functional specifications**.\n\n"
        "## 4. Complete active functional inventory\n\n"
        "### 4.1 Functional authorities\n\n"
        "| # | Canonical filename | Version | Status | Domain | Authority role |\n"
        "|---:|---|---:|---|---|---|\n"
        f"{rows}\n\n## 5. Supporting governance records\n{suffix}\n"
    )


_ROW = "| 1 | `EXAMPLE_SPEC_v1.0.0.md` | 1.0.0 | Active Canonical | Example | Authority |"
_SECOND = "| 2 | `OTHER_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Other | Authority |"


def test_repository_master_index_resolves_every_functional_authority():
    entries = _parse_inventory(MASTER_INDEX.read_text(encoding="utf-8"))
    missing = [filename for filename, _version in entries if not (ACTIVE_DIR / filename).is_file()]
    assert not missing, f"Master Index authorities missing from active directory: {missing}"


def test_inventory_is_derived_in_order_without_a_hardcoded_count_or_file_list():
    assert _parse_inventory(_index(_ROW + "\n" + _SECOND, count=2)) == (
        ("EXAMPLE_SPEC_v1.0.0.md", "1.0.0"),
        ("OTHER_SPEC_v2.0.0.md", "2.0.0"),
    )


def test_supporting_records_and_fenced_examples_are_not_functional_authorities():
    text = _index(_ROW + "\n```markdown\n" + _SECOND + "\n```", suffix=_SECOND)
    assert _parse_inventory(text) == (("EXAMPLE_SPEC_v1.0.0.md", "1.0.0"),)


@pytest.mark.parametrize(
    "text",
    [
        _index(_ROW, count=2),
        _index("", count=0),
        _index(_ROW.replace("| 1 |", "| 2 |", 1)),
        _index(_ROW + "\n" + _ROW, count=2),
        _index(_SECOND + "\n" + _ROW, count=2),
        _index(_ROW + "\n" + _SECOND.replace("OTHER_SPEC_v2.0.0", "EXAMPLE_SPEC_v2.0.0"), count=2),
        _index(_ROW.replace("| 1.0.0 |", "| 2.0.0 |")),
        _index(_ROW.replace("Active Canonical", "Proposed")),
        _index(_ROW.replace("`EXAMPLE_SPEC", "`../EXAMPLE_SPEC")),
        _index(_ROW.replace("| 1 |", "| ? |", 1)),
        _index(_ROW[:-1]),
        _index(_ROW.replace(" | Authority |", " | Authority | extra |")),
        _index(_ROW.replace(" | Authority |", " | |")),
        _index(_ROW).replace("## 4. Complete active functional inventory", "## 4. Other section"),
        _index(_ROW).replace("## 5. Supporting governance records", "Supporting records"),
        _index(_ROW) + "\nCanonical functional inventory: **1 unique active functional specifications**.\n",
        _index(_ROW) + "\n## 4. Complete active functional inventory\n",
        _index(_ROW + "\n```markdown\nunclosed example"),
    ],
    ids=[
        "missing-row", "empty-inventory", "missing-ordinal", "duplicate-ordinal",
        "out-of-order", "two-active-versions", "version-mismatch", "proposed-authority",
        "path-traversal", "malformed-ordinal", "missing-table-boundary", "extra-column",
        "missing-authority-role", "missing-section", "missing-section-boundary",
        "duplicate-declaration", "duplicate-section", "unclosed-fence",
    ],
)
def test_inventory_rejects_inconsistent_or_ambiguous_authority(text):
    with pytest.raises(ValueError):
        _parse_inventory(text)
