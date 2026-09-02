from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def test_repository_baseline_is_not_lowered_by_r012() -> None:
    params = json.loads((SEND_ROOT / "config/algo_params.json").read_text(encoding="utf-8"))
    assert params["score_thresholds"] == {"PRE": 70, "CONFIRM": 75, "OPEN": 80}


def test_no_named_profile_bundle_has_live_mutation_authority() -> None:
    from core.admin_commands import STRATEGY_PROFILES
    assert STRATEGY_PROFILES == {}


def test_profile_markup_exposes_no_mutation_callback() -> None:
    from core.telegram_admin_ui import strategy_quick_markup, strategy_profile_confirm_markup
    for markup in (strategy_quick_markup(None), strategy_profile_confirm_markup("AGGRESSIVE")):
        callbacks = [
            button["callback_data"]
            for row in markup["inline_keyboard"]
            for button in row
        ]
        assert not any("PROFILE_EXEC:" in callback for callback in callbacks)
        assert not any("PROFILE_CONFIRM:" in callback for callback in callbacks)


def test_authorized_profile_request_is_non_mutating_and_audited(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "runtime"
    (root / "config").mkdir(parents=True)
    (root / "observability").mkdir(parents=True)
    source_params = json.loads((SEND_ROOT / "config/algo_params.json").read_text(encoding="utf-8"))
    params_path = root / "config/algo_params.json"
    params_path.write_text(json.dumps(source_params, indent=2), encoding="utf-8")
    roles_path = root / "config/admin_roles.json"
    roles_path.write_text(json.dumps({"owner": [12345]}), encoding="utf-8")

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "12345")
    monkeypatch.setenv("ADMIN_ROLES_CONFIG", str(roles_path))
    monkeypatch.setenv("OBS_DIR", str(root / "observability"))

    import importlib
    import core.admin_commands as admin_commands
    import core.admin_permissions as admin_permissions
    import core.storage as storage

    importlib.reload(storage)
    importlib.reload(admin_permissions)
    importlib.reload(admin_commands)
    admin_permissions.load_roles_config.cache_clear()

    before = json.loads(params_path.read_text(encoding="utf-8"))
    with patch.object(admin_commands.observability_logger, "send_admin_proof_telegram") as proof:
        result = admin_commands.handle_strategy_profile("AGGRESSIVE", 12345)
    after = json.loads(params_path.read_text(encoding="utf-8"))

    assert "NOT AVAILABLE" in result
    assert after == before
    assert after["score_thresholds"] == {"PRE": 70, "CONFIRM": 75, "OPEN": 80}
    assert after.get("sr_required_multiplier") == before.get("sr_required_multiplier")
    proof.assert_called()
