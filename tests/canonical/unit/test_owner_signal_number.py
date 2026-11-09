from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import importlib
import json

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


def test_lifecycle_keeps_pre_identifier_after_midnight_and_restart(canonical_runtime_root):
    from core import owner_signal_number as numbers

    pre_time = _utc("2026-07-01T22:59:59")
    later_stage = _utc("2026-07-01T23:00:35")
    pre_label = numbers.reserve_lifecycle("one-opportunity", pre_time)
    assert pre_label == "01.07.2026 · 23:59:59 · nr. 0"
    assert numbers.reserve_lifecycle("one-opportunity", later_stage) == pre_label
    assert numbers.lookup_lifecycle("one-opportunity") == pre_label
    assert numbers.reserve_lifecycle("next-day-opportunity", later_stage) == "02.07.2026 · 00:00:35 · nr. 0"

    restarted = importlib.reload(numbers)
    assert restarted.reserve_lifecycle("one-opportunity", later_stage + 300) == pre_label
    assert restarted.lookup_lifecycle("one-opportunity") == pre_label
    assert restarted.lookup_lifecycle("missing-opportunity") is None
    # New signal records are canonical; the study ledger holds only a counter.
    assert restarted.lookup("one-opportunity", study=True) is None
    assert restarted.lookup("one-opportunity") == pre_label


def test_lifecycle_adopts_legacy_study_label_and_uses_both_counters(canonical_runtime_root):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    canonical = numbers.reserve("old-canonical", issued)
    for index in range(4):
        numbers.reserve(f"old-study-{index}", issued + index, study=True)
    legacy = numbers.lookup("old-study-3", study=True)
    assert legacy == "09.11.2026 · 18:35:15 · nr. 3"
    assert numbers.lookup_lifecycle("old-study-3") == legacy
    assert numbers.lookup("old-study-3") is None

    assert numbers.reserve_lifecycle("old-study-3", issued + 60) == legacy
    assert numbers.lookup("old-study-3") == legacy
    assert numbers.lookup("old-study-3", study=True) == legacy
    assert numbers.lookup("old-canonical") == canonical
    assert numbers.reserve_lifecycle("new-pre", issued + 61).endswith("nr. 4")
    # An old study writer still running during deployment cannot reuse nr. 4.
    assert numbers.reserve("late-legacy-study", issued + 62, study=True).endswith("nr. 5")
    assert numbers.reserve_lifecycle("next-pre", issued + 63).endswith("nr. 6")


def test_conflicting_historical_labels_remain_unchanged(canonical_runtime_root):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    canonical = numbers.reserve("shared-historical-id", issued)
    numbers.reserve("earlier-study", issued, study=True)
    study = numbers.reserve("shared-historical-id", issued + 1, study=True)
    assert canonical != study
    assert numbers.reserve_lifecycle("shared-historical-id", issued + 60) == canonical
    assert numbers.lookup_lifecycle("shared-historical-id") == canonical
    assert numbers.lookup("shared-historical-id", study=True) == study
    assert numbers.reserve_lifecycle("new-signal", issued + 61).endswith("nr. 2")


def test_competing_lifecycle_stages_share_one_identifier(canonical_runtime_root):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    attempts = ["same-signal", "new-a", "same-signal", "new-b", "new-c", "same-signal"]
    with ThreadPoolExecutor(max_workers=len(attempts)) as pool:
        labels = list(pool.map(lambda signal_id: numbers.reserve_lifecycle(signal_id, issued), attempts))
    assert labels[0] == labels[2] == labels[5]
    assert set(labels) == {f"09.11.2026 · 18:35:12 · nr. {index}" for index in range(4)}
    assert numbers.lookup_lifecycle("same-signal") == labels[0]


def test_lifecycle_and_legacy_study_threads_do_not_reuse_numbers(canonical_runtime_root):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")

    def reserve_attempt(index):
        if index % 2:
            return numbers.reserve(f"legacy-{index}", issued, study=True)
        return numbers.reserve_lifecycle(f"lifecycle-{index}", issued)

    with ThreadPoolExecutor(max_workers=6) as pool:
        labels = list(pool.map(reserve_attempt, range(6)))
    assert set(labels) == {f"09.11.2026 · 18:35:12 · nr. {index}" for index in range(6)}


def test_lifecycle_prunes_both_ledgers_and_preserves_pending_study(canonical_runtime_root, monkeypatch):
    from core import owner_signal_number as numbers

    monkeypatch.setattr(numbers, "RETENTION_DAYS", 2)
    old = _utc("2026-11-08T23:50:00")
    pending = _utc("2026-11-09T23:55:00")
    current = _utc("2026-11-10T00:05:12")
    numbers.reserve("old-canonical", old)
    numbers.reserve("old-study", old, study=True)
    pending_label = numbers.reserve("pending-study", pending, study=True)
    assert numbers.reserve_lifecycle("today", current).endswith("nr. 0")

    assert numbers.lookup("old-canonical") is None
    assert numbers.lookup("old-study", study=True) is None
    assert numbers.lookup_lifecycle("pending-study") == pending_label
    assert numbers.reserve_lifecycle("pending-study", current) == pending_label
    assert numbers.reserve_lifecycle("late-yesterday", pending).endswith("nr. 1")
    assert numbers.reserve_lifecycle("today-next", current).endswith("nr. 1")
    with pytest.raises(ValueError, match="TIMESTAMP_TOO_OLD"):
        numbers.reserve_lifecycle("late-expired-day", old)
    for name in ("owner_signal_numbers", "owner_study_numbers"):
        ledger = json.loads((canonical_runtime_root / "state" / f"{name}.json").read_text())
        assert set(ledger["next_numbers"]) == {"2026-11-09", "2026-11-10"}


@pytest.mark.parametrize("ledger_name", ["owner_signal_numbers", "owner_study_numbers"])
def test_lifecycle_refuses_either_corrupt_ledger_without_reset(canonical_runtime_root, ledger_name):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    numbers.reserve_lifecycle("already-issued", issued)
    paths = [canonical_runtime_root / "state" / f"{name}.json"
             for name in ("owner_signal_numbers", "owner_study_numbers")]
    corrupt = canonical_runtime_root / "state" / f"{ledger_name}.json"
    corrupt.write_text("{corrupt}")
    before = {path: path.read_bytes() for path in paths}

    assert numbers.lookup_lifecycle("already-issued") is None
    with pytest.raises(ValueError):
        numbers.reserve_lifecycle("new", issued)
    with pytest.raises(ValueError):
        numbers.reserve_lifecycle("already-issued", issued)
    assert {path: path.read_bytes() for path in paths} == before


@pytest.mark.parametrize("bad_counter", [-1, True, "1", 0])
def test_lifecycle_rejects_invalid_or_regressed_counter(canonical_runtime_root, bad_counter):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    numbers.reserve("legacy-study", issued, study=True)
    path = canonical_runtime_root / "state" / "owner_study_numbers.json"
    ledger = json.loads(path.read_text())
    ledger["next_numbers"]["2026-11-09"] = bad_counter
    path.write_text(json.dumps(ledger))
    before = path.read_bytes()

    assert numbers.lookup_lifecycle("legacy-study") is None
    with pytest.raises(ValueError):
        numbers.reserve_lifecycle("new", issued)
    assert path.read_bytes() == before
    assert not (canonical_runtime_root / "state" / "owner_signal_numbers.json").exists()


def test_lifecycle_capacity_failure_does_not_change_either_ledger(canonical_runtime_root, monkeypatch):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    monkeypatch.setattr(numbers, "MAX_NUMBERS", 2)
    numbers.reserve_lifecycle("first", issued)
    numbers.reserve_lifecycle("second", issued)
    paths = [canonical_runtime_root / "state" / f"{name}.json"
             for name in ("owner_signal_numbers", "owner_study_numbers")]
    before = {path: path.read_bytes() for path in paths}
    with pytest.raises(ValueError, match="STORAGE_LIMIT"):
        numbers.reserve_lifecycle("third", issued)
    assert {path: path.read_bytes() for path in paths} == before
    assert numbers.lookup_lifecycle("first").endswith("nr. 0")


def test_lifecycle_checks_serialized_size_before_any_write(canonical_runtime_root, monkeypatch):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    numbers.reserve_lifecycle("first", issued)
    paths = [canonical_runtime_root / "state" / f"{name}.json"
             for name in ("owner_signal_numbers", "owner_study_numbers")]
    before = {path: path.read_bytes() for path in paths}
    monkeypatch.setattr(numbers, "MAX_BYTES", max(map(len, before.values())) + 1)
    with pytest.raises(ValueError, match="STORAGE_LIMIT"):
        numbers.reserve_lifecycle("second", issued)
    assert {path: path.read_bytes() for path in paths} == before


def test_failed_canonical_write_leaves_safe_gap_for_legacy_writer(canonical_runtime_root, monkeypatch):
    from core import owner_signal_number as numbers

    issued = _utc("2026-11-09T18:35:12")
    save = numbers.storage.save_json_atomic

    def fail_canonical(path, ledger):
        if path.endswith("owner_signal_numbers.json"):
            raise OSError("simulated interrupted canonical write")
        return save(path, ledger)

    monkeypatch.setattr(numbers.storage, "save_json_atomic", fail_canonical)
    with pytest.raises(OSError, match="interrupted canonical write"):
        numbers.reserve_lifecycle("interrupted", issued)
    monkeypatch.setattr(numbers.storage, "save_json_atomic", save)

    assert numbers.lookup_lifecycle("interrupted") is None
    assert numbers.reserve("legacy-after-interruption", issued, study=True).endswith("nr. 1")
    assert numbers.reserve_lifecycle("next-lifecycle", issued).endswith("nr. 2")
