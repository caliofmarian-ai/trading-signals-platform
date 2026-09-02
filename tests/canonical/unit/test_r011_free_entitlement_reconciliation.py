from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _live_modules():
    """Resolve current core modules at test execution time.

    Some legacy batch tests deliberately purge and re-import the core package to
    prove restart recovery. Resolving here prevents stale module references from
    making R-011 fixtures patch an object that the admin view no longer uses.
    """
    admin_views = importlib.import_module("core.admin_views")
    distribution_router = importlib.import_module("core.distribution_router")
    distribution_router_v3 = importlib.import_module("core.distribution_router_v3")
    return admin_views, distribution_router, distribution_router_v3


def test_repository_free_baseline_is_canonical_six() -> None:
    _, distribution_router, distribution_router_v3 = _live_modules()
    env_lines = (REPO_ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    free_env = [line for line in env_lines if line.startswith("FREE_LIMIT=")]
    assert free_env == ["FREE_LIMIT=6"]

    channel_cfg = json.loads(
        (SEND_ROOT / "config/channel_config.json").read_text(encoding="utf-8")
    )
    assert channel_cfg["FREE_LIMIT"] == 6
    assert distribution_router.DEFAULT_LIMITS["FREE"] == 6
    assert distribution_router_v3.DEFAULT_LIMITS["FREE"] == 6


def _effective_cfg(free_limit: int) -> dict:
    return {
        "channels": {"FREE": 1001, "BASIC": 1002, "PRO": 1003, "ELITE": 1004},
        "limits": {"FREE": free_limit, "BASIC": 20, "PRO": 50, "ELITE": None},
        "enabled": {"FREE": True, "BASIC": True, "PRO": True, "ELITE": True},
        "feedback_capable": {
            "FREE": False,
            "BASIC": False,
            "PRO": False,
            "ELITE": True,
        },
        "reset": {"timezone": "Europe/London", "hour": 8, "minute": 10},
        "admin": {},
    }


def _state() -> dict:
    return {
        "tier_state": {
            "FREE": "ACTIVE",
            "BASIC": "ACTIVE",
            "PRO": "ACTIVE",
            "ELITE": "ACTIVE",
        },
        "open_signals_today": {"FREE": 2, "BASIC": 3, "PRO": 4, "ELITE": 0},
    }


def test_distribution_admin_view_shows_persisted_effective_free_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_views, distribution_router, distribution_router_v3 = _live_modules()
    monkeypatch.delenv("FREE_LIMIT", raising=False)
    monkeypatch.setattr(
        distribution_router_v3, "_load_effective_config", lambda: _effective_cfg(6)
    )
    monkeypatch.setattr(distribution_router, "load_state", _state)
    monkeypatch.setattr(
        distribution_router, "_load_channel_config_file", lambda: {"FREE_LIMIT": 6}
    )

    rendered = admin_views.render_distribution_panel(123, 0)

    assert (
        "FREE: ACTIVE | 2/6 | mapping READY | limit source PERSISTED_CONFIG"
        in rendered
    )
    assert "ELITE: ACTIVE | 0/UNLIMITED | mapping READY" in rendered
    assert "Reset reference: 08:10 Europe/London" in rendered


def test_distribution_admin_view_exposes_governed_env_override_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_views, distribution_router, distribution_router_v3 = _live_modules()
    monkeypatch.setenv("FREE_LIMIT", "9")
    monkeypatch.setattr(
        distribution_router_v3, "_load_effective_config", lambda: _effective_cfg(9)
    )
    monkeypatch.setattr(distribution_router, "load_state", _state)
    monkeypatch.setattr(
        distribution_router, "_load_channel_config_file", lambda: {"FREE_LIMIT": 6}
    )

    rendered = admin_views.render_distribution_panel(123, 0)

    assert "FREE: ACTIVE | 2/9 | mapping READY | limit source ENV" in rendered
    assert "2/6" not in rendered


def test_distribution_admin_view_does_not_claim_invalid_env_as_effective_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_views, distribution_router, distribution_router_v3 = _live_modules()
    monkeypatch.setenv("FREE_LIMIT", "not-a-limit")
    monkeypatch.setattr(
        distribution_router_v3, "_load_effective_config", lambda: _effective_cfg(6)
    )
    monkeypatch.setattr(distribution_router, "load_state", _state)
    monkeypatch.setattr(
        distribution_router, "_load_channel_config_file", lambda: {"FREE_LIMIT": 6}
    )

    rendered = admin_views.render_distribution_panel(123, 0)

    assert (
        "FREE: ACTIVE | 2/6 | mapping READY | limit source PERSISTED_CONFIG"
        in rendered
    )
    assert "FREE: ACTIVE | 2/6 | mapping READY | limit source ENV" not in rendered


def test_distribution_admin_view_fails_visibly_when_truth_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_views, _, distribution_router_v3 = _live_modules()

    def _boom() -> dict:
        raise RuntimeError("unavailable")

    monkeypatch.setattr(distribution_router_v3, "_load_effective_config", _boom)
    rendered = admin_views.render_distribution_panel(123, 0)
    assert "Configuration: UNAVAILABLE" in rendered
    assert "ACTIVE |" not in rendered
