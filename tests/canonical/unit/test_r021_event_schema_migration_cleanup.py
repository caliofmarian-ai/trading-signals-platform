from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path


SEND_ROOT = Path(__file__).resolve().parents[3] / "send"
if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge_scheduler() -> None:
    for name in list(sys.modules):
        if name == "runtime.distribution_scheduler":
            sys.modules.pop(name, None)


def test_distribution_scheduler_delegates_reset_without_duplicate_legacy_event(monkeypatch) -> None:
    _purge_scheduler()
    scheduler = importlib.import_module("runtime.distribution_scheduler")

    calls: list[str] = []
    monkeypatch.setattr(
        scheduler.distribution_router,
        "reset_daily_counters",
        lambda: calls.append("reset"),
    )

    def _unexpected_log_event(event):
        raise AssertionError(f"scheduler must not manufacture a second reset event: {event!r}")

    monkeypatch.setattr(scheduler.observability_logger, "log_event", _unexpected_log_event)

    scheduler.do_daily_reset()

    assert calls == ["reset"]


def test_distribution_scheduler_source_has_no_tier_reset_write() -> None:
    _purge_scheduler()
    scheduler = importlib.import_module("runtime.distribution_scheduler")
    source = inspect.getsource(scheduler.do_daily_reset)

    assert '"event_type": "tier_reset"' not in source
    assert "observability_logger.log_event" not in source
