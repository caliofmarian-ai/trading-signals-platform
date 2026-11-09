from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import importlib

import pytest


def _utc(value):
    return datetime.fromisoformat(value + "+00:00").timestamp()


def test_dublin_summer_midnight_resets_sequence_and_preserves_original_label(canonical_runtime_root):
    from core import owner_signal_number as numbers

    before_midnight = _utc("2026-07-01T22:59:59")
    after_midnight = _utc("2026-07-01T23:00:00")
    assert numbers.reserve("private-opportunity-a", before_midnight, study=True).endswith("nr. 0")
    first = numbers.reserve("private-opportunity-a", before_midnight)
    assert first == "01.07.2026 · 23:59:59 · nr. 0"
    assert numbers.reserve("private-opportunity-b", before_midnight) == "01.07.2026 · 23:59:59 · nr. 1"
    assert numbers.reserve("private-opportunity-c", after_midnight) == "02.07.2026 · 00:00:00 · nr. 0"
    assert numbers.reserve("private-opportunity-d", after_midnight) == "02.07.2026 · 00:00:00 · nr. 1"
    assert numbers.reserve("private-opportunity-c", after_midnight, study=True).endswith("nr. 0")
    assert numbers.lookup("private-opportunity-d", study=True) is None

    restarted = importlib.reload(numbers)
    assert restarted.reserve("private-opportunity-a", after_midnight) == first
    assert restarted.lookup("private-opportunity-a") == first
    assert restarted.lookup("never-opened") is None
    assert "private-opportunity-a" not in (canonical_runtime_root / "state" / "owner_signal_numbers.json").read_text()


def test_competing_attempts_share_one_number_without_duplicates(canonical_runtime_root):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    attempts = ["same-signal", "new-signal-a", "same-signal", "new-signal-b"]
    with ThreadPoolExecutor(max_workers=len(attempts)) as pool:
        labels = list(pool.map(lambda signal_id: numbers.reserve(signal_id, issued), attempts))

    assert labels[0] == labels[2]
    assert set(labels) == {f"09.11.2026 · 18:35:12 · nr. {index}" for index in range(3)}


def test_prunes_only_old_numbers_and_never_restarts_an_active_day(canonical_runtime_root, monkeypatch):
    from core import owner_signal_number as numbers

    monkeypatch.setattr(numbers, "RETENTION_DAYS", 2)
    previous_day = _utc("2026-11-08T23:50:00")
    result_pending = _utc("2026-11-09T23:55:00")
    current_day = _utc("2026-11-10T00:05:12")
    numbers.reserve("old", previous_day)
    preserved = numbers.reserve("pending", result_pending)
    assert numbers.reserve("current", current_day) == "10.11.2026 · 00:05:12 · nr. 0"

    assert numbers.lookup("old") is None
    assert numbers.lookup("pending") == preserved
    assert numbers.reserve("late-prior-day-attempt", result_pending).endswith("nr. 1")
    assert numbers.reserve("current-next", current_day).endswith("nr. 1")


def test_corrupt_number_ledger_is_preserved_and_cannot_restart_sequence(canonical_runtime_root):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    path = canonical_runtime_root / "state" / "owner_signal_numbers.json"
    path.write_text("{corrupt}")

    assert numbers.lookup("unknown") is None
    with pytest.raises(ValueError):
        numbers.reserve("unissued", issued)
    assert path.read_text() == "{corrupt}"
