from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))

from billing import membership_scheduler


def _reset(monkeypatch) -> None:
    monkeypatch.setattr(membership_scheduler, "_LAST_SCAN_MONOTONIC", 0.0)
    monkeypatch.delenv("BILLING_MEMBERSHIP_RECONCILER_ENABLED", raising=False)
    monkeypatch.delenv(
        "BILLING_MEMBERSHIP_RECONCILER_DRY_RUN_ENABLED", raising=False
    )
    monkeypatch.delenv(
        "BILLING_MEMBERSHIP_RECONCILER_SCAN_INTERVAL_SECONDS", raising=False
    )


def test_default_disabled_performs_no_reconciliation(monkeypatch) -> None:
    _reset(monkeypatch)

    def fail_batch(**_kwargs):
        raise AssertionError("disabled scheduler must not observe or mutate membership")

    monkeypatch.setattr(
        membership_scheduler.membership_reconciler,
        "reconcile_all_known_subscribers",
        fail_batch,
    )

    assert membership_scheduler.runtime_mode() == "DISABLED"
    assert (
        membership_scheduler.maybe_run_membership_cycle(monotonic_now=1000.0)
        is None
    )


def test_dry_run_is_read_only_and_aggregated(monkeypatch) -> None:
    _reset(monkeypatch)
    monkeypatch.setenv("BILLING_MEMBERSHIP_RECONCILER_DRY_RUN_ENABLED", "true")
    calls: list[dict] = []
    emitted: list[dict] = []

    def fake_batch(**kwargs):
        calls.append(kwargs)
        return [
            {"state": "IN_SYNC", "actions_applied": False},
            {"state": "UNKNOWN", "actions_applied": False},
        ]

    monkeypatch.setattr(
        membership_scheduler.membership_reconciler,
        "reconcile_all_known_subscribers",
        fake_batch,
    )
    monkeypatch.setattr(
        membership_scheduler, "_emit_summary", lambda summary: emitted.append(summary)
    )

    result = membership_scheduler.maybe_run_membership_cycle(
        monotonic_now=1000.0,
        now_ts=1_800_000_000,
    )

    assert calls[0]["apply_actions"] is False
    assert result["mode"] == "DRY_RUN"
    assert result["subscriber_count"] == 2
    assert result["state_counts"] == {"IN_SYNC": 1, "UNKNOWN": 1}
    assert result["actions_applied_count"] == 0
    assert emitted == [result]
    assert "subscriber_ref" not in str(result)
    assert "telegram_user_id" not in str(result)


def test_mutation_mode_requires_explicit_enable_flag(monkeypatch) -> None:
    _reset(monkeypatch)
    monkeypatch.setenv("BILLING_MEMBERSHIP_RECONCILER_DRY_RUN_ENABLED", "true")
    monkeypatch.setenv("BILLING_MEMBERSHIP_RECONCILER_ENABLED", "true")
    calls: list[dict] = []

    def fake_batch(**kwargs):
        calls.append(kwargs)
        return [{"state": "IN_SYNC", "actions_applied": True}]

    monkeypatch.setattr(
        membership_scheduler.membership_reconciler,
        "reconcile_all_known_subscribers",
        fake_batch,
    )
    monkeypatch.setattr(membership_scheduler, "_emit_summary", lambda _summary: None)

    result = membership_scheduler.run_membership_cycle(now_ts=1_800_000_000)

    assert membership_scheduler.runtime_mode() == "APPLY"
    assert calls[0]["apply_actions"] is True
    assert result["actions_applied_count"] == 1


def test_scheduler_is_throttled(monkeypatch) -> None:
    _reset(monkeypatch)
    monkeypatch.setenv("BILLING_MEMBERSHIP_RECONCILER_DRY_RUN_ENABLED", "true")
    monkeypatch.setenv(
        "BILLING_MEMBERSHIP_RECONCILER_SCAN_INTERVAL_SECONDS", "300"
    )
    calls = 0

    def fake_cycle(**_kwargs):
        nonlocal calls
        calls += 1
        return {"status": "COMPLETED"}

    monkeypatch.setattr(membership_scheduler, "run_membership_cycle", fake_cycle)

    assert membership_scheduler.maybe_run_membership_cycle(monotonic_now=1000.0)
    assert (
        membership_scheduler.maybe_run_membership_cycle(monotonic_now=1299.0)
        is None
    )
    assert membership_scheduler.maybe_run_membership_cycle(monotonic_now=1300.0)
    assert calls == 2


@pytest.mark.parametrize("value", ["0", "59", "3601", "not-an-int"])
def test_scan_interval_is_bounded(monkeypatch, value: str) -> None:
    _reset(monkeypatch)
    monkeypatch.setenv(
        "BILLING_MEMBERSHIP_RECONCILER_SCAN_INTERVAL_SECONDS", value
    )
    with pytest.raises(membership_scheduler.MembershipSchedulerError):
        membership_scheduler.scan_interval_seconds()


def test_summary_flags_access_leak_and_isolated_batch_error(monkeypatch) -> None:
    _reset(monkeypatch)
    monkeypatch.setenv("BILLING_MEMBERSHIP_RECONCILER_DRY_RUN_ENABLED", "true")
    summaries: list[dict] = []
    monkeypatch.setattr(
        membership_scheduler,
        "_emit_summary",
        lambda summary: summaries.append(summary),
    )
    monkeypatch.setattr(
        membership_scheduler.membership_reconciler,
        "reconcile_all_known_subscribers",
        lambda **_kwargs: [
            {"state": "ACCESS_LEAK_RISK", "actions_applied": False},
            {
                "state": "UNKNOWN",
                "actions_applied": False,
                "batch_error": True,
                "error_type": "SyntheticError",
            },
        ],
    )

    result = membership_scheduler.run_membership_cycle()

    assert result["access_leak_risk_count"] == 1
    assert result["batch_error_count"] == 1
    assert result["subscriber_count"] == 2
    assert summaries == [result]
