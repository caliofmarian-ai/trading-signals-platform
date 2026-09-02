from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(rel_path: str, pattern: str, replacement: str) -> None:
    path = ROOT / rel_path
    text = path.read_bytes().decode("utf-8")
    rx = re.compile(pattern, re.S)
    matches = list(rx.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"{rel_path}: expected exactly one match, found {len(matches)}")
    updated = rx.sub(lambda _: replacement, text, count=1)
    path.write_bytes(updated.encode("utf-8"))


# 1. Remove legacy named production profile bundles from live mutation authority.
replace_once(
    "send/core/admin_commands.py",
    r"# ---------------------------------------------------------------------------\r?\n# Canonical strategy-profile definitions .*?\r?\n# ---------------------------------------------------------------------------\r?\nSTRATEGY_PROFILES: Dict\[str, Dict\[str, Any\]\] = \{.*?\r?\n\}\r?\n\r?\n(?=# Legacy fallback only\.)",
    '''# ---------------------------------------------------------------------------
# Strategy-profile authority (R-012)
# ---------------------------------------------------------------------------
# Active v3 parameter-control canon does not define named production presets or
# production-safe preset ranges.  The former CONSERVATIVE/BALANCED/AGGRESSIVE
# bundles are therefore intentionally absent from live mutation authority.
STRATEGY_PROFILES: Dict[str, Dict[str, Any]] = {}
STRATEGY_PROFILES_STATUS = "NOT_AVAILABLE"
STRATEGY_PROFILES_REASON = (
    "Named production strategy profiles are not defined by the active canonical "
    "parameter-control authority. Legacy CONSERVATIVE/BALANCED/AGGRESSIVE bundles "
    "are disabled until a versioned canonical preset contract is approved."
)

''',
)

replace_once(
    "send/core/admin_commands.py",
    r"# ---------------------------------------------------------------------------\r?\n# Strategy-profile helpers\r?\n# ---------------------------------------------------------------------------.*?(?=# ---------------------------------------------------------------------------\r?\n# File-delivery security)",
    '''# ---------------------------------------------------------------------------
# Strategy-profile helpers
# ---------------------------------------------------------------------------

def get_current_strategy_profile() -> Optional[str]:
    """No named production profile is active under the current v3 authority."""
    return None


def get_current_strategy_profile_observation() -> str:
    params = _load_algo_params_observation()
    if params is None:
        return "UNAVAILABLE (strategy configuration absent or invalid)"
    return (
        "NOT AVAILABLE (named production strategy profiles are not defined by "
        "the active canonical parameter-control authority)"
    )


def handle_strategy_profile(profile: str, user_id: int) -> str:
    """Fail closed for legacy named-profile mutations while preserving audit proof."""
    ok, reason = require_permission(user_id, "strategy.thresholds.write")
    if not ok:
        return render_error(reason)

    requested = str(profile or "").upper().strip() or "UNSPECIFIED"
    _audit(
        user_id,
        "/strategy profile",
        "REJECTED",
        {
            "profile": requested,
            "reason": "NON_CANONICAL_PROFILE_DISABLED",
            "parameter_mutation": False,
        },
    )
    return render_error(
        "Strategy profiles are NOT AVAILABLE under the active canonical "
        "parameter-control authority. No strategy parameter was changed."
    )


''',
)

# 2. Keep Strategy Profile as an informative Telegram surface only.
replace_once(
    "send/core/telegram_admin_ui.py",
    r"def strategy_quick_markup\(.*?(?=def engine_markup\()",
    '''def strategy_quick_markup(current_profile: Optional[str]) -> dict[str, list[list[dict[str, str]]]]:
    """Read-only strategy-profile surface while named presets are undefined."""
    return _kb([
        [_btn("🔄 Refresh", "PROFILE_HOME")],
        [_knowledge_btn("strategy", "PROFILE_HOME")],
        [_btn("⬅️ Strategy", "STRATEGY")],
    ])


def strategy_profile_confirm_markup(profile: str) -> dict[str, list[list[dict[str, str]]]]:
    """Safe recovery markup for stale legacy profile callbacks; never executes."""
    return _kb([
        [_btn("⬅️ Profiles", "PROFILE_HOME")],
        [_btn("⬅️ Strategy", "STRATEGY")],
    ])


''',
)

# 3. Make stale Telegram callbacks explicitly non-mutating.
replace_once(
    "send/core/bot_service.py",
    r"    # ---- Strategy profile callbacks ----.*?(?=    # ---- Files/Docs callbacks ----)",
    '''    # ---- Strategy profile callbacks (R-012: read-only / fail closed) ----
    if action == "PROFILE_HOME":
        current_observation = get_current_strategy_profile_observation()
        return {
            "text": _format_surface(
                "strategy",
                "⚙️ Strategy Profile",
                "Profiles: NOT AVAILABLE\n"
                f"Current profile state: {current_observation}\n\n"
                "Named production presets are not defined by the active canonical "
                "parameter-control authority. Current strategy parameters remain unchanged.",
            ),
            "reply_markup": telegram_admin_ui.strategy_quick_markup(None),
        }

    if action.startswith("PROFILE_CONFIRM:"):
        profile = action[len("PROFILE_CONFIRM:"):].upper().strip() or "UNSPECIFIED"
        return {
            "text": _format_card(
                f"⚙️ {profile}: NOT AVAILABLE",
                "This is a stale legacy profile-selection callback. Named production "
                "profiles are not defined by the active canonical parameter-control "
                "authority. No strategy parameter was changed.",
            ),
            "reply_markup": telegram_admin_ui.strategy_profile_confirm_markup(profile),
        }

    if action.startswith("PROFILE_EXEC:"):
        if not _check_rate_limit(user_id, "mutation"):
            return {"text": "Rate limit exceeded.", "reply_markup": None}
        profile = action[len("PROFILE_EXEC:"):]
        result = handle_strategy_profile(profile, user_id)
        return {
            "text": _format_surface("strategy", "⚙️ Strategy Profile", result),
            "reply_markup": telegram_admin_ui.strategy_quick_markup(None),
        }

''',
)

# 4. Reconcile historical Telegram regression tests to current canonical safety.
replace_once(
    "tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py",
    r"# ---------------------------------------------------------------------------\r?\n# UI-003: Strategy profile markup\r?\n# ---------------------------------------------------------------------------.*?(?=# ---------------------------------------------------------------------------\r?\n# SYM-001:)",
    '''# ---------------------------------------------------------------------------
# UI-003: Strategy profile markup
# ---------------------------------------------------------------------------

class TestStrategyQuickMarkup:
    def test_profile_surface_has_no_legacy_mutation_buttons(self):
        _purge()
        from core.telegram_admin_ui import strategy_quick_markup
        markup = strategy_quick_markup(None)
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert not any("PROFILE_CONFIRM:" in data for data in flat_data)
        assert not any("PROFILE_EXEC:" in data for data in flat_data)
        assert any("PROFILE_HOME" in data for data in flat_data)

    def test_profile_surface_is_read_only_navigation(self):
        _purge()
        from core.telegram_admin_ui import strategy_quick_markup
        markup = strategy_quick_markup("BALANCED")
        flat = [btn["text"] for row in markup["inline_keyboard"] for btn in row]
        assert any("Refresh" in text for text in flat)
        assert not any("MIC / SMALL" in text for text in flat)
        assert not any("MEDIU / MEDIUM" in text for text in flat)
        assert not any("MARE / LARGE" in text for text in flat)

    def test_stale_confirmation_markup_has_no_execute_action(self):
        _purge()
        from core.telegram_admin_ui import strategy_profile_confirm_markup
        markup = strategy_profile_confirm_markup("CONSERVATIVE")
        flat_data = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert not any("PROFILE_EXEC:" in data for data in flat_data)
        assert any("PROFILE_HOME" in data for data in flat_data)


''',
)

replace_once(
    "tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py",
    r"# ---------------------------------------------------------------------------\r?\n# PROF-001: Strategy profile mapping and confirmation\r?\n# ---------------------------------------------------------------------------.*?(?=# ---------------------------------------------------------------------------\r?\n# FILE-001:)",
    '''# ---------------------------------------------------------------------------
# PROF-001: Strategy profile fail-closed reconciliation
# ---------------------------------------------------------------------------

class TestStrategyProfileHandlers:
    OWNER_ID = 333333

    def _setup(self, tmp_path: Path) -> Dict[str, str]:
        _ensure_dirs(tmp_path)
        roles = _make_roles_config(owner_ids=[self.OWNER_ID])
        rc = tmp_path / "roles.json"
        _write_json(rc, roles)
        params = _make_algo_params()
        params_file = tmp_path / "config" / "algo_params.json"
        _write_json(params_file, params)
        return {
            "OWNER_TELEGRAM_ID": str(self.OWNER_ID),
            "ADMIN_ROLES_CONFIG": str(rc),
            "BINARYBOT_BASE_DIR": str(tmp_path),
        }

    def test_legacy_named_profiles_are_not_live_bundles(self):
        _purge()
        from core.admin_commands import STRATEGY_PROFILES
        assert STRATEGY_PROFILES == {}

    def test_authorized_legacy_profile_request_does_not_mutate_params(self, tmp_path):
        env = self._setup(tmp_path)
        params_path = tmp_path / "config" / "algo_params.json"
        before = json.loads(params_path.read_text(encoding="utf-8"))
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_strategy_profile
                for profile in ("CONSERVATIVE", "BALANCED", "AGGRESSIVE"):
                    result = handle_strategy_profile(profile, self.OWNER_ID)
                    assert "NOT AVAILABLE" in result
                    after = json.loads(params_path.read_text(encoding="utf-8"))
                    assert after == before

    def test_profile_request_preserves_thresholds_and_legacy_sr_value(self, tmp_path):
        env = self._setup(tmp_path)
        params_path = tmp_path / "config" / "algo_params.json"
        before = json.loads(params_path.read_text(encoding="utf-8"))
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_strategy_profile
                handle_strategy_profile("AGGRESSIVE", self.OWNER_ID)
        after = json.loads(params_path.read_text(encoding="utf-8"))
        assert after["score_thresholds"] == before["score_thresholds"]
        assert after.get("sr_required_multiplier") == before.get("sr_required_multiplier")

    def test_unknown_profile_is_also_non_mutating(self, tmp_path):
        env = self._setup(tmp_path)
        params_path = tmp_path / "config" / "algo_params.json"
        before = params_path.read_text(encoding="utf-8")
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger"):
                from core.admin_commands import handle_strategy_profile
                result = handle_strategy_profile("UNKNOWN_PROFILE", self.OWNER_ID)
                assert "NOT AVAILABLE" in result
        assert params_path.read_text(encoding="utf-8") == before

    def test_profile_unauthorized(self, tmp_path):
        env = self._setup(tmp_path)
        NON_OWNER = 777777
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import handle_strategy_profile
            result = handle_strategy_profile("BALANCED", NON_OWNER)
            assert "unauthorized" in result.lower() or "Error" in result

    def test_authorized_rejected_profile_emits_admin_proof(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            with patch("core.admin_commands.observability_logger") as mock_obs:
                from core.admin_commands import handle_strategy_profile
                handle_strategy_profile("BALANCED", self.OWNER_ID)
                mock_obs.send_admin_proof_telegram.assert_called()

    def test_current_profile_is_explicitly_not_available(self, tmp_path):
        env = self._setup(tmp_path)
        _purge()
        with patch.dict(os.environ, env, clear=False):
            import core.admin_permissions as ap
            ap.load_roles_config.cache_clear()
            from core.admin_commands import (
                get_current_strategy_profile,
                get_current_strategy_profile_observation,
            )
            assert get_current_strategy_profile() is None
            assert "NOT AVAILABLE" in get_current_strategy_profile_observation()


''',
)

# 5. Add dedicated R-012 canonical regression coverage.
new_test = ROOT / "tests/canonical/unit/test_r012_strategy_profile_reconciliation.py"
new_test.write_text('''from __future__ import annotations

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
''', encoding="utf-8")

# 6. Materialize R-012 audit decision and remediation-plan status.
audit_doc = ROOT / "audit/repository-wide-audit-2026-09-01/R012_STRATEGY_PROFILE_RECONCILIATION.md"
audit_doc.write_text('''# R-012 — Strategy Profile Reconciliation

Status: IMPLEMENTED ON REMEDIATION BRANCH — VALIDATION PENDING
Issue: #120
Parent: #97
Base main commit: `dd04a64506e5b62b98f9b885a01414b1e2b0ac8d`

## Canonical determination

The active canonical Master Index identifies `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` as the governed parameter-control authority. That authority does not define the legacy named production profiles `CONSERVATIVE`, `BALANCED`, or `AGGRESSIVE`, and it explicitly forbids inventing production ranges merely to make a control available.

The legacy profile bundles were therefore not promoted into v3 authority. They are disabled rather than reinterpreted or assigned invented replacement values.

Active SR v3 defines Trade Physics v1 `required_space = buffer_distance`. The current Corridor runtime already prevents legacy `sr_required_multiplier` from tightening or relaxing the hard structural-feasibility gate. R-012 therefore removes the obsolete profile write path instead of attempting to preserve old SR profile semantics.

## Reconciliation

- live named profile bundle registry is empty;
- authorized profile requests fail closed, are audited as rejected, and do not write strategy configuration;
- the Telegram Strategy Profile surface remains visible but read-only and says named profiles are not available;
- new Telegram markup exposes no legacy profile mutation button;
- stale `PROFILE_CONFIRM:*` callbacks recover safely without displaying legacy parameter bundles;
- stale `PROFILE_EXEC:*` callbacks route to the fail-closed audited handler and cannot mutate `algo_params.json`;
- existing direct parameter-control behavior is outside the R-012 scope and is not broadened or redesigned here.

## Safety boundary

R-012 does not lower score thresholds, define new strategy presets, change SR/Trade Physics formulas, change provider selection, alter FSM/execution timing, enable distribution, or enable broker execution.
''', encoding="utf-8")

plan_path = ROOT / "audit/repository-wide-audit-2026-09-01/REMEDIATION_MASTER_PLAN.md"
plan = plan_path.read_bytes().decode("utf-8")
old = '''### R-011 — FREE entitlement limit reconciliation
Severity: HIGH
Status: IN PROGRESS
Issue: #118
Branch: `remediation/audit-2026-09-01-r011-free-entitlement`
Depends on: R-010 — SATISFIED

Required outcome:
- active canon, runtime defaults, channel config, `.env.example`, tests, and admin display agree on FREE limit = 6 unless a governed override is explicitly intended and auditable.

### R-012 — Strategy profile reconciliation
Severity: HIGH
Status: PENDING

Required outcome:
- Admin profiles cannot silently lower active canonical thresholds or mutate obsolete SR semantics;
- profiles either become canonical governed presets or are removed/disabled until canonically defined.
'''
new = '''### R-011 — FREE entitlement limit reconciliation
Severity: HIGH
Status: CLOSED
Issue: #118 — CLOSED
PR: #119
Merged main commit: `dd04a64506e5b62b98f9b885a01414b1e2b0ac8d`
Depends on: R-010 — SATISFIED
Validation: provider selector 5 passed; Telegram admin regression 72 passed; full repository suite 1046 passed.

Required outcome:
- active canon, runtime defaults, channel config, `.env.example`, tests, and admin display agree on FREE limit = 6 unless a governed override is explicitly intended and auditable.

### R-012 — Strategy profile reconciliation
Severity: HIGH
Status: IN PROGRESS
Issue: #120
Branch: `remediation/audit-2026-09-01-r012-strategy-profiles`
Depends on: R-011 — SATISFIED

Required outcome:
- Admin profiles cannot silently lower active canonical thresholds or mutate obsolete SR semantics;
- profiles either become canonical governed presets or are removed/disabled until canonically defined.
'''
if old not in plan:
    raise SystemExit("REMEDIATION_MASTER_PLAN: expected R-011/R-012 block not found")
plan_path.write_bytes(plan.replace(old, new, 1).encode("utf-8"))
