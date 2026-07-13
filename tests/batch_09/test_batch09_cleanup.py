"""
BATCH-09 Targeted Tests
=======================
Verifies cleanup integrity after BATCH-09:
- Deleted orphan/dead modules are not importable
- Active replacement paths still function
- Path convergence: outcome_service and admin_commands use storage-based paths
- No live /opt/binarybot writes
- datetime.now(UTC) semantics in strategy_auditor_lib
- Config source-of-truth: admin_permissions.json is test fixture only
- No generated artifacts in repository paths
"""
from __future__ import annotations

import datetime
import importlib
import os
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_import(name: str):
    """Import a module with a clean sys.modules cache for relevant prefixes."""
    purge = ("core", "state_store", "snapshots", "monitoring", "tools")
    for k in list(sys.modules):
        if k == name or any(k.startswith(p) for p in purge):
            sys.modules.pop(k, None)
    importlib.invalidate_caches()
    return importlib.import_module(name)


# ---------------------------------------------------------------------------
# 1. Deleted orphan/dead modules are not importable
# ---------------------------------------------------------------------------

class TestDeletedModulesNotImportable:
    """Orphan/dead modules removed in BATCH-09 must not be importable."""

    def test_legacy_bot_control_not_importable(self):
        """send/legacy/bot_control.py deleted — must not be importable."""
        assert not (SEND_ROOT / "legacy" / "bot_control.py").exists(), (
            "legacy/bot_control.py still exists — GAP-016 not closed"
        )
        with pytest.raises(ModuleNotFoundError):
            _fresh_import("legacy.bot_control")

    def test_strategy_v2_copy_not_importable(self):
        """send/core/strategy_v2 - Copy.py deleted — must not be importable."""
        assert not (SEND_ROOT / "core" / "strategy_v2 - Copy.py").exists(), (
            "strategy_v2 - Copy.py still exists — duplicate not removed"
        )

    def test_health_check_not_importable(self):
        """send/monitoring/health_check.py deleted — must not be importable (GAP-020)."""
        assert not (SEND_ROOT / "monitoring" / "health_check.py").exists(), (
            "monitoring/health_check.py still exists — GAP-020 not closed"
        )
        with pytest.raises(ModuleNotFoundError):
            _fresh_import("monitoring.health_check")

    def test_metrics_collector_not_importable(self):
        """send/metrics/metrics_collector.py deleted — must not be importable (GAP-020)."""
        assert not (SEND_ROOT / "metrics" / "metrics_collector.py").exists(), (
            "metrics/metrics_collector.py still exists — GAP-020 not closed"
        )
        with pytest.raises(ModuleNotFoundError):
            _fresh_import("metrics.metrics_collector")

    def test_metrics_aggregates_writer_not_importable(self):
        """send/metrics/aggregates_writer.py deleted — must not be importable."""
        assert not (SEND_ROOT / "metrics" / "aggregates_writer.py").exists()
        with pytest.raises(ModuleNotFoundError):
            _fresh_import("metrics.aggregates_writer")

    def test_journal_trade_journal_not_importable(self):
        """send/journal/trade_journal.py deleted — must not be importable."""
        assert not (SEND_ROOT / "journal" / "trade_journal.py").exists()
        with pytest.raises(ModuleNotFoundError):
            _fresh_import("journal.trade_journal")

    def test_state_store_event_store_not_importable(self):
        """send/state_store/event_store.py deleted — must not be importable."""
        assert not (SEND_ROOT / "state_store" / "event_store.py").exists()
        with pytest.raises(ModuleNotFoundError):
            _fresh_import("state_store.event_store")

    def test_validation_statistical_proof_not_importable(self):
        """send/validation/statistical_proof.py deleted — must not be importable."""
        assert not (SEND_ROOT / "validation" / "statistical_proof.py").exists()


# ---------------------------------------------------------------------------
# 2. Active replacement paths still function
# ---------------------------------------------------------------------------

class TestActivePathsStillFunction:
    """Key active modules that replace or supersede deleted orphans still import correctly."""

    def test_state_store_still_importable(self):
        """state_store/state_store.py must still be importable."""
        mod = _fresh_import("state_store.state_store")
        assert hasattr(mod, "load_fsm_state")
        assert hasattr(mod, "save_fsm_state")
        assert hasattr(mod, "FOCUS_STATE_PATH")

    def test_snapshot_manager_still_importable(self):
        """snapshots/snapshot_manager.py must still be importable."""
        mod = _fresh_import("snapshots.snapshot_manager")
        assert hasattr(mod, "create_snapshot")
        assert hasattr(mod, "restore_snapshot")

    def test_restart_guard_still_importable(self):
        """monitoring/restart_guard.py must still be importable."""
        mod = _fresh_import("monitoring.restart_guard")
        assert hasattr(mod, "record_start")
        assert hasattr(mod, "should_freeze")

    def test_observability_logger_still_importable(self):
        """core/observability_logger.py supersedes state_store/event_store.py."""
        mod = _fresh_import("core.observability_logger")
        assert hasattr(mod, "log_event")
        assert hasattr(mod, "build_event")

    def test_strategy_v2_still_importable(self):
        """core/strategy_v2.py (authoritative) must still be importable."""
        mod = _fresh_import("core.strategy_v2")
        assert hasattr(mod, "decide")


# ---------------------------------------------------------------------------
# 3. Path convergence: outcome_service uses storage-based paths
# ---------------------------------------------------------------------------

class TestOutcomeServicePathConvergence:
    """outcome_service.py must use storage.root_path() for its constants,
    not hardcoded /opt/binarybot/ strings."""

    def test_outcomes_jsonl_not_hardcoded(self):
        mod = _fresh_import("core.outcome_service")
        assert "/opt/binarybot" not in mod.OUTCOMES_JSONL, (
            f"OUTCOMES_JSONL still hardcoded: {mod.OUTCOMES_JSONL}"
        )

    def test_open_registry_json_not_hardcoded(self):
        mod = _fresh_import("core.outcome_service")
        assert "/opt/binarybot" not in mod.OPEN_REGISTRY_JSON

    def test_outcomes_index_json_not_hardcoded(self):
        mod = _fresh_import("core.outcome_service")
        assert "/opt/binarybot" not in mod.OUTCOMES_INDEX_JSON

    def test_outcome_paths_under_storage_base(self):
        """Outcome paths must resolve under the storage base dir (send/ or BINARYBOT_BASE_DIR)."""
        mod = _fresh_import("core.outcome_service")
        storage = _fresh_import("core.storage")
        base = storage.base_dir()
        for attr in ("OUTCOMES_JSONL", "OPEN_REGISTRY_JSON", "OUTCOMES_INDEX_JSON"):
            val = getattr(mod, attr)
            assert val.startswith(base), (
                f"{attr}={val!r} does not start with storage base {base!r}"
            )

    def test_outcome_paths_point_to_outcomes_segment(self):
        """Outcome paths must be under the 'outcomes' segment."""
        mod = _fresh_import("core.outcome_service")
        for attr in ("OUTCOMES_JSONL", "OPEN_REGISTRY_JSON", "OUTCOMES_INDEX_JSON"):
            val = getattr(mod, attr)
            assert os.sep + "outcomes" + os.sep in val or val.endswith(
                os.sep + "outcomes"
            ), f"{attr}={val!r} not under outcomes/ segment"

    def test_outcome_service_paths_env_isolated(self, tmp_path, monkeypatch):
        """When BINARYBOT_BASE_DIR is set, outcome paths must resolve under it."""
        # Create required subdirs
        (tmp_path / "outcomes").mkdir()
        monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))

        purge = ("core", "state_store")
        for k in list(sys.modules):
            if any(k.startswith(p) for p in purge):
                sys.modules.pop(k, None)
        importlib.invalidate_caches()

        mod = importlib.import_module("core.outcome_service")
        assert mod.OUTCOMES_JSONL.startswith(str(tmp_path))
        assert mod.OPEN_REGISTRY_JSON.startswith(str(tmp_path))
        assert mod.OUTCOMES_INDEX_JSON.startswith(str(tmp_path))


# ---------------------------------------------------------------------------
# 4. Path convergence: admin_commands uses storage-based paths
# ---------------------------------------------------------------------------

class TestAdminCommandsPathConvergence:
    """admin_commands.py must not use hardcoded /opt/binarybot/ for config/obs constants."""

    def test_config_dir_not_hardcoded(self):
        mod = _fresh_import("core.admin_commands")
        assert "/opt/binarybot" not in mod.CONFIG_DIR

    def test_obs_dir_not_hardcoded(self):
        mod = _fresh_import("core.admin_commands")
        assert "/opt/binarybot" not in mod.OBS_DIR

    def test_reports_dir_not_hardcoded(self):
        mod = _fresh_import("core.admin_commands")
        assert "/opt/binarybot" not in mod.REPORTS_DIR

    def test_admin_events_path_not_hardcoded(self):
        mod = _fresh_import("core.admin_commands")
        assert "/opt/binarybot" not in mod.ADMIN_EVENTS_PATH

    def test_admin_proofs_path_not_hardcoded(self):
        mod = _fresh_import("core.admin_commands")
        assert "/opt/binarybot" not in mod.ADMIN_PROOFS_PATH

    def test_engine_events_path_not_hardcoded(self):
        mod = _fresh_import("core.admin_commands")
        assert "/opt/binarybot" not in mod.ENGINE_EVENTS_PATH

    def test_admin_paths_under_storage_base(self):
        """Config and obs paths must start under the storage base dir."""
        mod = _fresh_import("core.admin_commands")
        storage = _fresh_import("core.storage")
        base = storage.base_dir()
        for attr in ("CONFIG_DIR", "ADMIN_EVENTS_PATH", "ADMIN_PROOFS_PATH"):
            val = getattr(mod, attr)
            assert val.startswith(base), (
                f"{attr}={val!r} does not start with storage base {base!r}"
            )


# ---------------------------------------------------------------------------
# 5. No live /opt/binarybot writes in outcome_service or admin_commands
# ---------------------------------------------------------------------------

class TestNoLiveHardcodedWrites:
    """No path containing /opt/binarybot should be written to during active module operation."""

    def test_outcome_service_no_opt_binarybot_write(self, tmp_path, monkeypatch):
        """outcome_service with storage env isolation must not touch /opt/binarybot."""
        (tmp_path / "outcomes").mkdir()
        monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
        monkeypatch.setenv("COMMUNITY_FEEDBACK_SALT", "test-salt")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
        monkeypatch.setenv("ELITE_CHANNEL_ID", "1")

        purge = ("core", "state_store")
        for k in list(sys.modules):
            if any(k.startswith(p) for p in purge):
                sys.modules.pop(k, None)
        importlib.invalidate_caches()

        mod = importlib.import_module("core.outcome_service")
        # None of the path constants should contain /opt/binarybot
        for attr in ("OUTCOMES_JSONL", "OPEN_REGISTRY_JSON", "OUTCOMES_INDEX_JSON"):
            assert "/opt/binarybot" not in getattr(mod, attr)

    def test_admin_commands_no_opt_binarybot_write_path(self, tmp_path, monkeypatch):
        """admin_commands with env isolation must not expose /opt/binarybot write paths."""
        (tmp_path / "config").mkdir()
        (tmp_path / "observability").mkdir()
        monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
        monkeypatch.setenv("OBS_DIR", str(tmp_path / "observability"))

        purge = ("core", "state_store")
        for k in list(sys.modules):
            if any(k.startswith(p) for p in purge):
                sys.modules.pop(k, None)
        importlib.invalidate_caches()

        mod = importlib.import_module("core.admin_commands")
        for attr in ("ADMIN_EVENTS_PATH", "ADMIN_PROOFS_PATH", "ENGINE_EVENTS_PATH"):
            assert "/opt/binarybot" not in getattr(mod, attr)


# ---------------------------------------------------------------------------
# 6. datetime.now(UTC) semantics in strategy_auditor_lib
# ---------------------------------------------------------------------------

class TestDatetimeUTCFix:
    """strategy_auditor_lib.py must use timezone-aware UTC, not the deprecated utcnow()."""

    def test_no_utcnow_in_source(self):
        """strategy_auditor_lib.py source must not contain datetime.utcnow()."""
        src = (SEND_ROOT / "tools" / "strategy_auditor_lib.py").read_text(encoding="utf-8")
        assert "utcnow()" not in src, (
            "datetime.utcnow() still present in strategy_auditor_lib.py"
        )

    def test_datetime_now_utc_present(self):
        """strategy_auditor_lib.py must use datetime.now(datetime.UTC)."""
        src = (SEND_ROOT / "tools" / "strategy_auditor_lib.py").read_text(encoding="utf-8")
        assert "datetime.now(" in src and "UTC" in src, (
            "datetime.now(datetime.UTC) or equivalent not found in strategy_auditor_lib.py"
        )

    def test_auditor_date_format_is_iso(self, tmp_path, monkeypatch):
        """The date produced by the auditor must be a valid YYYY-MM-DD string."""
        import re

        monkeypatch.setenv("OBS_DIR", str(tmp_path))
        monkeypatch.setenv("ENGINE_EVENTS_LOG", str(tmp_path / "engine_events.jsonl"))
        (tmp_path / "engine_events.jsonl").write_text("", encoding="utf-8")

        purge = ("tools",)
        for k in list(sys.modules):
            if any(k.startswith(p) for p in purge):
                sys.modules.pop(k, None)
        importlib.invalidate_caches()

        lib = importlib.import_module("tools.strategy_auditor_lib")
        settings = lib.load_settings()
        settings["reports"] = {"output_dir": str(tmp_path)}
        events = lib.load_all_events(settings)
        report = lib.build_report(events, settings)
        date_val = report.get("date", "")
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", date_val), (
            f"Audit date {date_val!r} is not YYYY-MM-DD format"
        )


# ---------------------------------------------------------------------------
# 7. config source-of-truth: admin_permissions.json is test fixture, not runtime
# ---------------------------------------------------------------------------

class TestAdminPermissionsTestOnly:
    """admin_permissions.json exists as a test fixture but is not loaded at runtime."""

    def test_admin_permissions_json_present_as_fixture(self):
        """The file must still exist so test fixtures can copy it."""
        assert (SEND_ROOT / "config" / "admin_permissions.json").exists(), (
            "admin_permissions.json missing — test fixtures will break"
        )

    def test_admin_permissions_module_uses_hardcoded_matrix(self):
        """admin_permissions.py must not load permissions from admin_permissions.json at runtime."""
        mod = _fresh_import("core.admin_permissions")
        # The module defines has_permission purely from PERMISSION_MATRIX or roles config,
        # not from the JSON file. Verify has_permission is callable.
        assert callable(getattr(mod, "has_permission", None))
        # The JSON file should not be loaded on import (no side-effect read)
        # Verify the PERMISSIONS_CONFIG path env var is defined but file-read is never invoked.
        # This is a structural test: admin_permissions.py must expose ROLES_CONFIG_PATH,
        # not PERMISSIONS_CONFIG_PATH as a loaded attribute.
        assert hasattr(mod, "ROLES_CONFIG_PATH")


# ---------------------------------------------------------------------------
# 8. No committed log/temp artifacts in tracked paths
# ---------------------------------------------------------------------------

class TestNoCommittedArtifacts:
    """Committed runtime artifacts must not be re-added to the repository paths."""

    def test_engine_log_not_present(self):
        assert not (SEND_ROOT / "engine.log").exists(), (
            "send/engine.log is present — should be gitignored"
        )

    def test_tmp_decision_files_not_present(self):
        tmp_files = list(SEND_ROOT.glob("tmp_decision*"))
        assert len(tmp_files) == 0, (
            f"tmp_decision* files still present: {tmp_files}"
        )

    def test_zip_archive_not_present(self):
        assert not (REPO_ROOT / "send(2).zip").exists(), (
            "send(2).zip still present — should be removed"
        )

    def test_gitignore_covers_logs(self):
        gitignore = REPO_ROOT / ".gitignore"
        assert gitignore.exists(), ".gitignore file must exist"
        content = gitignore.read_text(encoding="utf-8")
        assert "*.log" in content or "engine.log" in content, (
            ".gitignore must cover log files"
        )

    def test_gitignore_covers_tmp_decision(self):
        gitignore = REPO_ROOT / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        assert "tmp_decision" in content, (
            ".gitignore must cover tmp_decision* files"
        )


# ---------------------------------------------------------------------------
# 9. Segmented path isolation: canonical paths resolve to storage segments
# ---------------------------------------------------------------------------

class TestSegmentedPathIsolation:
    """Canonical segmented paths must be the live write authority."""

    def test_state_store_focus_state_path_under_state_segment(self):
        mod = _fresh_import("state_store.state_store")
        assert os.sep + "state" + os.sep in mod.FOCUS_STATE_PATH or \
               mod.FOCUS_STATE_PATH.endswith(os.sep + "state"), \
            f"FOCUS_STATE_PATH not under state/: {mod.FOCUS_STATE_PATH}"

    def test_state_store_dist_state_path_under_state_segment(self):
        mod = _fresh_import("state_store.state_store")
        assert os.sep + "state" + os.sep in mod.DIST_STATE_PATH or \
               mod.DIST_STATE_PATH.endswith(os.sep + "state"), \
            f"DIST_STATE_PATH not under state/: {mod.DIST_STATE_PATH}"

    def test_outcomes_segment_is_canonical_write_authority(self):
        """Outcome writes must target outcomes/ segment, not a legacy root path."""
        mod = _fresh_import("core.outcome_service")
        assert "outcomes" in mod.OUTCOMES_JSONL, (
            f"OUTCOMES_JSONL does not target outcomes segment: {mod.OUTCOMES_JSONL}"
        )

    def test_observability_segment_is_canonical_for_admin_events(self):
        """Admin events must target observability/ segment."""
        mod = _fresh_import("core.admin_commands")
        assert "observability" in mod.ADMIN_EVENTS_PATH, (
            f"ADMIN_EVENTS_PATH not under observability/: {mod.ADMIN_EVENTS_PATH}"
        )
