"""R-024 read-only self-status gate, using the Master Index inventory guard.

This checks explicit document metadata/current-authority claims, not arbitrary
uses of 'proposed' in model/parameter governance. It never edits documentation,
changes the authority inventory, promotes candidates, or enables runtime code.
"""
from __future__ import annotations

import re
import runpy
from pathlib import Path

import pytest


_REF = re.compile(r"\b([A-Z][A-Z0-9_]+)_v(\d+\.\d+\.\d+)(?:\.md)?\b")
_BAD_STATUS = re.compile(
    r"\b(?:PROPOSED|DRAFT|NOT[ _-]+ACTIVE|INACTIVE|SUPERSEDED|DEPRECATED|PENDING)\b",
    re.IGNORECASE,
)
_FIELD = re.compile(
    r"^(Version|Status|(?:Canonical )?Path|Canonical Name|Document ID|"
    r"Supersedes(?: upon promotion)?|Supersession Intent):\s*(.*)$", re.I,
)
_SELF = r"(?:this (?:document|file|specification|spec|version)|this)"


def _plain(line: str) -> str:
    return line.strip().replace("**", "").replace("`", "")


def _prose(text: str) -> list[tuple[int, str]]:
    """Keep line numbers; fenced examples cannot assert current authority."""
    result = []
    fence = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        marker = re.match(r"(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, suffix = marker.groups()
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1] and not suffix.strip():
                fence = None
            continue
        if fence is None:
            result.append((number, _plain(raw)))
    if fence is not None:
        raise ValueError("Unclosed fenced example hides document metadata")
    return result


def _status_issues(text: str, filename: str, version: str,
                   active_versions: dict[str, str]) -> list[str]:
    """Report bounded contradictions, preserving every normative paragraph."""
    try:
        lines = _prose(text)
    except ValueError as exc:
        return [str(exc)]
    header = []
    for number, line in lines:
        if line.startswith("## "):
            break
        header.append((number, line))
    fields: dict[str, list[tuple[int, str]]] = {}
    for number, line in header:
        match = _FIELD.fullmatch(line)
        if match:
            key = match[1].lower()
            fields.setdefault("path" if key == "canonical path" else key, []).append((number, match[2]))
    issues = []
    for name in ("version", "status"):
        if len(fields.get(name, [])) != 1:
            issues.append(f"header: expected exactly one {name} declaration")
    for number, value in fields.get("version", []):
        if value.removeprefix("v") != version:
            issues.append(f"L{number}: version disagrees with Master Index: {value}")
    for number, value in fields.get("status", []):
        if _BAD_STATUS.search(value) or not re.search(r"\bACTIVE\s+CANON(?:ICAL)?\b", value, re.I):
            issues.append(f"L{number}: contradictory/non-active document status: {value}")
    domain = filename.rsplit("_v", 1)[0]
    identifiers = fields.get("document id", []) + fields.get("canonical name", [])
    if identifiers and (len(identifiers) != 1 or identifiers[0][1] != domain):
        issues.append("header: document identifier disagrees with Master Index domain")
    titles = [line.removeprefix("# ").removesuffix(".md") for _, line in header if line.startswith("# ")]
    if len(titles) != 1 or (not identifiers and titles != [filename.removesuffix(".md")]):
        issues.append("header: missing or mismatched canonical document identity")
    for title in titles:
        for title_domain, title_version in _REF.findall(title):
            if (title_domain, title_version) != (domain, version):
                issues.append("header: versioned title disagrees with Master Index")
    for number, value in fields.get("path", []):
        if "/canonical/active/" not in value or not value.endswith("/" + filename):
            issues.append(f"L{number}: non-active/mismatched current document path: {value}")
    for number, value in fields.get("supersedes upon promotion", []):
        issues.append(f"L{number}: supersession still conditional on promotion: {value}")
    for number, value in fields.get("supersession intent", []):
        issues.append(f"L{number}: supersession still expressed as intent: {value}")
    for number, value in fields.get("supersedes", []):
        if re.search(r"\b(?:upon|after|if|until)\b.*\bpromotion\b", value, re.I):
            issues.append(f"L{number}: conditional supersession: {value}")
        for predecessor, predecessor_version in _REF.findall(value):
            if predecessor == domain and predecessor_version == version:
                issues.append(f"L{number}: document supersedes itself")
    # Header reference lists assert current authority; supersession/provenance
    # fields do not. Historical body references are not globally replaced.
    provenance = False
    for number, line in header:
        if line.lower().startswith(("source provenance:", "historical references:", "predecessor / superseded documents:", "superseded documents:")):
            provenance = True
        elif line.endswith(":") and not line.startswith("-"):
            provenance = False
        if provenance or line.lower().startswith(("supersedes", "supersession intent:")):
            continue
        for referenced_domain, referenced_version in _REF.findall(line):
            current = active_versions.get(referenced_domain)
            if current and "canonical/proposed/" in line:
                issues.append(f"L{number}: active authority referenced under proposed path: {line}")
            if current and referenced_version != current:
                issues.append(f"L{number}: stale current header reference: {referenced_domain}_v{referenced_version}; active v{current}")
    self_identity = re.escape(filename.removesuffix(".md")) + r"(?:\.md)?"
    subject = rf"(?:{_SELF}|{self_identity})"
    denied = re.compile(
        rf"\b{subject}\s+(?:is|remains)\s+(?:(?:a|the)\s+)?"
        r"(?:(?:complete|consolidated|patch)\s+)*(?:proposed\b|not\s+(?:yet\s+)?active\b|draft\b|non-authoritative\b)", re.I,
    )
    conditional = re.compile(
        rf"\b{subject}\b.*\b(?:not authoritative|not active|must not be treated as active)\b.*\b(?:until|before)\b", re.I,
    )
    old_active = re.compile(r"\b(?:remains?|is still|stays?)\s+(?:the\s+)?(?:active|authoritative)\b", re.I)
    for number, line in lines:
        if denied.search(line) or conditional.search(line):
            issues.append(f"L{number}: stale document self-authority claim: {line}")
        for referenced_domain, referenced_version in _REF.findall(line):
            if active_versions.get(referenced_domain) != referenced_version:
                continue
            identity = re.escape(f"{referenced_domain}_v{referenced_version}")
            if re.search(identity + r"(?:\.md)?\s+(?:is|remains)\s+(?:proposed|not active)\b", line, re.I):
                issues.append(f"L{number}: active peer authority denied: {line}")
        if old_active.search(line):
            for referenced_domain, referenced_version in _REF.findall(line):
                if referenced_domain == domain and referenced_version != version:
                    issues.append(f"L{number}: predecessor still asserted active: {line}")
        if re.match(r"(?:Until|Before) (?:explicit |formal |canonical |atomic )*promotion\b", line, re.I) and re.search(r"\b(?:v\d|predecessor|this document|this file)\b", line, re.I):
            issues.append(f"L{number}: stale pre-promotion authority boundary: {line}")
    return list(dict.fromkeys(issues))


def test_repository_active_authorities_have_consistent_self_status():
    inventory = runpy.run_path(str(Path(__file__).with_name("test_r024_active_canonical_inventory.py")))
    master = inventory["MASTER_INDEX"]
    entries = inventory["_parse_inventory"](master.read_text(encoding="utf-8"))
    versions = {filename.rsplit("_v", 1)[0]: version for filename, version in entries}
    versions[master.name.rsplit("_v", 1)[0]] = master.name.rsplit("_v", 1)[1].removesuffix(".md")
    activation = master.parent.parent / "governance_records/CANONICAL_ACTIVATION_RECORD_20260901.md"
    record = activation.read_text(encoding="utf-8")
    assert "Status: EXECUTED CANONICAL PROMOTION RECORD" in record
    counts = re.findall(r"The (\d+) functional specifications listed as Active Canonical", record)
    assert counts == [str(len(entries))], "Activation record and Master Index inventory disagree"
    assert f"`{master.name}` is the sole authoritative Master Index." in record
    findings = []
    for filename, version in entries:
        path = master.parent / filename
        if not path.is_file():
            findings.append(f"{filename}: missing active authority")
            continue
        findings.extend(f"{filename}: {issue}" for issue in _status_issues(
            path.read_text(encoding="utf-8"), filename, version, versions))
    assert not findings, f"Checked all {len(entries)} Master Index authorities:\n" + "\n".join(findings)


_SAMPLE = "# EXAMPLE_SPEC_v2.0.0\n\nVersion: 2.0.0\nStatus: ACTIVE CANONICAL\nSupersedes: `EXAMPLE_SPEC_v1.0.0.md`\n\n## 1. Purpose\n"
_VERSIONS = {"EXAMPLE_SPEC": "2.0.0", "OTHER_SPEC": "3.0.0"}


def _check(text: str) -> list[str]:
    return _status_issues(text, "EXAMPLE_SPEC_v2.0.0.md", "2.0.0", _VERSIONS)


@pytest.mark.parametrize("text", [
    _SAMPLE,
    _SAMPLE + "Proposed parameter changes require approval.\n",
    _SAMPLE + "The proposed model remains inactive until validation.\n",
    _SAMPLE + "This document does not authorize runtime changes.\n",
    _SAMPLE + "Historical baseline: EXAMPLE_SPEC_v1.0.0.md is superseded.\n",
    _SAMPLE + "```markdown\nStatus: PROPOSED\nThis document is not active.\n```\n",
    _SAMPLE + "~~~~markdown\nEXAMPLE_SPEC_v1.0.0.md remains active.\n~~~\n~~~~\n",
    _SAMPLE + "The approved active canonical baseline remains binding.\n",
    _SAMPLE.replace("Status: ACTIVE CANONICAL", "**Status:** **ACTIVE CANONICAL**"),
    _SAMPLE.replace("\n\n## 1.", "\nPath: /opt/binarybot/docs/canonical/active/EXAMPLE_SPEC_v2.0.0.md\n\n## 1."),
    _SAMPLE + "## Version history\n| 1.0.0 | Proposed first version |\n",
])
def test_legitimate_governance_prose_and_history_are_preserved(text):
    assert not _check(text)


@pytest.mark.parametrize("status", [
    "PROPOSED", "PROPOSED COMPLETE CONSOLIDATED SUCCESSOR — NOT ACTIVE CANONICAL",
    "ACTIVE CANONICAL — PROPOSED", "NOT ACTIVE", "NOT_ACTIVE", "INACTIVE",
    "DRAFT", "SUPERSEDED", "DEPRECATED", "PENDING APPROVAL", "",
])
def test_contradictory_document_status_is_rejected(status):
    assert _check(_SAMPLE.replace("ACTIVE CANONICAL", status))


@pytest.mark.parametrize("text", [
    _SAMPLE.replace("Version: 2.0.0", "Version: 1.0.0"),
    _SAMPLE.replace("Version: 2.0.0\n", ""),
    _SAMPLE.replace("Status: ACTIVE CANONICAL\n", ""),
    _SAMPLE.replace("Status: ACTIVE CANONICAL", "Status: ACTIVE CANONICAL\nStatus: ACTIVE CANONICAL"),
    _SAMPLE.replace("# EXAMPLE_SPEC_v2.0.0", "# EXAMPLE_SPEC_v1.0.0"),
    _SAMPLE.replace("Supersedes:", "Supersedes upon promotion:"),
    _SAMPLE.replace("Supersedes: `EXAMPLE_SPEC_v1.0.0.md`", "Supersedes: `EXAMPLE_SPEC_v2.0.0.md`"),
    _SAMPLE.replace("\n\n## 1.", "\nPath: /docs/canonical/proposed/EXAMPLE_SPEC_v2.0.0.md\n\n## 1."),
    _SAMPLE.replace("\n\n## 1.", "\nLinked active authorities:\n- OTHER_SPEC_v2.0.0.md\n\n## 1."),
    _SAMPLE + "This document is proposed current-scope canon.\n",
    _SAMPLE + "This is the proposed logging contract.\n",
    _SAMPLE + "EXAMPLE_SPEC_v2.0.0.md is not active.\n",
    _SAMPLE + "EXAMPLE_SPEC_v1.0.0.md remains active until promotion.\n",
    _SAMPLE + "Until formal promotion, v1 remains active.\n",
    _SAMPLE + "```markdown\nUnclosed history\n",
])
def test_identity_promotion_and_reference_contradictions_are_rejected(text):
    assert _check(text)


@pytest.mark.parametrize("text", [
    _SAMPLE.replace("# EXAMPLE_SPEC_v2.0.0", "# Readable title\n\n**Document ID:** EXAMPLE_SPEC"),
    _SAMPLE.replace("# EXAMPLE_SPEC_v2.0.0", "# Readable title\n\nCanonical Name: EXAMPLE_SPEC"),
    _SAMPLE.replace("\n\n## 1.", "\nCanonical Path: send/docs/canonical/active/EXAMPLE_SPEC_v2.0.0.md\n\n## 1."),
    _SAMPLE.replace("\n\n## 1.", "\nPredecessor / Superseded Documents:\n- canonical/superseded/EXAMPLE_SPEC_v1.0.0.md — historical only\n\n## 1."),
    _SAMPLE.replace("\n\n## 1.", "\nSource provenance:\n- OTHER_SPEC_v1.0.0.md\n\n## 1."),
])
def test_explicit_identity_and_historical_metadata_are_supported(text):
    assert not _check(text)


@pytest.mark.parametrize("text", [
    _SAMPLE.replace("# EXAMPLE_SPEC_v2.0.0", "# Readable title\n\nDocument ID: WRONG_SPEC"),
    _SAMPLE.replace("# EXAMPLE_SPEC_v2.0.0", "# EXAMPLE_SPEC_v1.0.0\n\nDocument ID: EXAMPLE_SPEC"),
    _SAMPLE.replace("Supersedes:", "Supersession Intent:"),
    _SAMPLE.replace("\n\n## 1.", "\nCanonical Path: send/docs/canonical/proposed/EXAMPLE_SPEC_v2.0.0.md\n\n## 1."),
    _SAMPLE.replace("\n\n## 1.", "\nLinked Documents:\n- canonical/proposed/OTHER_SPEC_v3.0.0.md\n\n## 1."),
    _SAMPLE + "This document is a complete proposed successor.\n",
    _SAMPLE + "OTHER_SPEC_v3.0.0.md remains proposed.\n",
])
def test_alias_metadata_and_active_peer_denials_are_rejected(text):
    assert _check(text)
