from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
RUNBOOK = (
    REPO_ROOT
    / "audit"
    / "railway-deployment-preparation-01"
    / "RAILWAY_OPERATOR_RUNBOOK.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_points_to_current_master_index_and_not_v1_authority():
    text = _read(README)
    assert "send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md" in text
    assert "43 unique active functional specifications" in text
    assert "CANONICAL_MASTER_INDEX_v1.0.0.md" not in text


def test_readme_keeps_temporal_candidates_non_active():
    text = _read(README)
    assert "Issue #137 temporal-market-intelligence documents are still **TRANSITIONAL / NON-ACTIVE**" in text
    for filename in (
        "MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0.md",
        "TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC_v1.0.0.md",
        "TEMPORAL_PATTERN_VALIDATION_SPEC_v1.0.0.md",
        "STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC_v1.0.0.md",
    ):
        assert filename in text
    assert "active functional canonical inventory remains 43, not 47" in text


def test_readme_does_not_overstate_r017_live_acceptance():
    text = _read(README)
    assert "final post-fix real Telegram PRIMARY_ADMIN journey is still **PENDING**" in text
    assert "source tests or a successful Railway deployment" in text
    assert "live acceptance proof" in text


def test_readme_explains_two_second_evaluation_without_signal_guarantee():
    text = _read(README)
    assert "ENGINE_TICK_SECONDS = 2" in text
    assert "a signal is guaranteed every two seconds" in text
    assert "a broker order is created every two seconds" in text


def test_runbook_preserves_persistent_config_and_exact_head_ci_contract():
    text = _read(RUNBOOK)
    assert "Existing Owner-controlled files under `/data/config/` are preserved" in text
    assert "Required Repository CI" in text
    assert "exact current PR head" in text
    assert "ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE" in text
    assert "Normal state: `false` / disabled." in text


def test_runbook_requires_runtime_evidence_for_strategy_auditor_and_broker_state():
    text = _read(RUNBOOK)
    assert "STRATEGY_AUDITOR_ENABLED" in text
    assert "STRATEGY_AUDITOR_DAILY_TIME" in text
    assert "STRATEGY_AUDITOR_TIMEZONE" in text
    assert "Treat redacted/unobservable variable values as `UNKNOWN`" in text
    assert "This runbook does not authorize real-money execution." in text
    assert "ENABLE_BROKER_EXECUTION=true" not in text


def test_docs_keep_source_ci_deploy_and_live_acceptance_distinct():
    readme = _read(README)
    runbook = _read(RUNBOOK)
    for status in ("SOURCE VERIFIED", "CI VERIFIED", "DEPLOYED"):
        assert status in runbook
    assert "LIVE ACCEPTED" in runbook
    assert "PENDING" in readme
    assert "Never collapse these states" in runbook
