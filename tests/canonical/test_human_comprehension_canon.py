from pathlib import Path


BASE = Path("send/docs/canonical/active")
ANNEX = "HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md"


def read(name):
    return (BASE / name).read_text(encoding="utf-8")


def test_human_comprehension_canon_is_materialized():
    text = read(ANNEX)

    required = (
        "No Naked Operational Concept Principle",
        "Interface as Operational Memory Principle",
        "Mandatory Human Comprehension Contract",
        "Parameter Explanation Contract",
        "Status Explanation Contract",
        "Pipeline Explanation Contract",
        "Truth-Domain Separation",
        "Role-Aware Explanation",
        "Telegram Requirement",
        "Drift Prevention",
        "Owner Comprehension Acceptance",
    )

    for requirement in required:
        assert requirement in text


def test_active_control_plane_documents_reference_comprehension_canon():
    direct_reference_documents = (
        "ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md",
        "ADMIN_CONTROL_SPEC_v2.0.1.md",
        "CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md",
        "ADMIN_TREE_MAP_v2.0.1.md",
        "CANONICAL_MASTER_INDEX_v2.0.0.md",
    )

    for document in direct_reference_documents:
        assert ANNEX in read(document), document

    invariants = read("SYSTEM_INVARIANTS_v3.0.0.md")
    assert "Human Comprehension" in invariants
    assert "authorit" in invariants.lower()


def test_superseded_control_plane_is_not_used_as_current_authority():
    text = read(ANNEX)

    assert "ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md" in text
    assert "ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md" not in text


def test_truth_boundaries_are_explicit():
    text = read(ANNEX)

    assert "Distribution success does not mean the signal was profitable." in text
    assert "Community feedback is not objective Market Truth." in text
    assert "Shadow operation is not live broker execution." in text


def test_owner_memory_requirement_is_explicit():
    text = read(ANNEX).lower()

    assert "historical chat conversations are not an operational dependency" in text
    assert "developer memory is not an operational dependency" in text
    assert "operator folklore is not an operational dependency" in text


def test_comprehension_does_not_authorize_live_execution():
    text = read(ANNEX)

    assert "automatic broker execution" in text
    assert "autonomous canonical strategy mutation" in text
    assert "permission escalation" in text
