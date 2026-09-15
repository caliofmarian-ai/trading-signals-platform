from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "repository-ci.yml"
HISTORICAL_WORKFLOW = ROOT / ".github" / "workflows" / "provider-selector-validation.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_repository_ci_is_the_single_current_workflow_authority() -> None:
    assert WORKFLOW.is_file()
    assert not HISTORICAL_WORKFLOW.exists()

    text = _workflow_text()
    assert text.startswith("name: Repository CI\n")
    assert "name: Required Repository CI" in text


def test_repository_ci_cannot_silently_bypass_main_validation() -> None:
    text = _workflow_text()

    assert "pull_request:" in text
    assert "push:" in text
    assert "workflow_dispatch:" in text
    assert text.count("branches: [main]") == 2
    assert "pull_request_target:" not in text
    assert "continue-on-error" not in text
    assert not re.search(r"(?m)^\s+paths(?:-ignore)?:\s*", text)


def test_repository_ci_certifies_the_exact_checked_out_sha() -> None:
    text = _workflow_text()
    exact_sha_expression = (
        "${{ github.event_name == 'pull_request' && "
        "github.event.pull_request.head.sha || github.sha }}"
    )

    assert f"ref: {exact_sha_expression}" in text
    assert f'EXPECTED_SHA="{exact_sha_expression}"' in text
    assert 'ACTUAL_SHA="$(git rev-parse HEAD)"' in text
    assert 'if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then' in text


def test_repository_ci_preserves_required_regression_layers() -> None:
    text = _workflow_text()

    required_commands_or_paths = (
        "tests/repository_governance/test_required_ci_gate.py",
        "tests/canonical/unit/test_market_data_provider_control.py",
        "tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py",
        "tests/canonical/contract",
        "tests/canonical/integration/test_r021_primary_distribution_runtime.py",
        "tests/canonical/unit/test_r021_event_schema_migration_cleanup.py",
        "python -m pytest -q\n",
    )

    for required in required_commands_or_paths:
        assert required in text
