"""Safe recovery of interrupted private V3 study delivery reservations."""
from tests.canonical.unit.test_physical_study_delivery import BASE, _capture, _sample, study_setup


def _prepared_entry(setup):
    _, study, delivery, _, _, _, messages, clock = setup
    delivery.dispatch_async = lambda **kwargs: None
    _capture(setup, publish=False)
    entry_ts = BASE + 32
    study.advance(now_ts=entry_ts, active_provider="FINNHUB",
                  price_loader=lambda _: _sample(entry_ts, 1.1))
    path = study._path()
    state = study._read(path)
    identity, row = next(iter(state["records"].items()))
    row["study_delivery"] = {"entry": None, "result": None}
    study._save(path, state)
    return identity, path, study, delivery, messages, clock


def _reserve_entry(identity, path, study, delivery):
    reserved = delivery._reserve(path, "entry", BASE + 33, 123456789)
    assert reserved is not None and reserved[0] == identity
    saved = study._read(path)["records"][identity]["study_delivery"]["entry"]
    assert saved["status"] == "RESERVED"
    return saved


def test_recent_reservation_is_not_misclassified_before_recovery_grace(study_setup):
    identity, path, study, delivery, _, _ = _prepared_entry(study_setup)
    reserved = _reserve_entry(identity, path, study, delivery)
    report = delivery._reconcile_receipts(
        path, reserved["attempted_ts"] + delivery.RESERVATION_RECOVERY_GRACE_SECONDS - 1,
        force=True)
    assert report["unresolved_reservations"] == 1
    assert report["orphaned_reservations"] == 0
    assert study._read(path)["records"][identity]["study_delivery"]["entry"]["status"] == "RESERVED"


def test_orphaned_reservation_becomes_audited_unknown_and_is_never_retried(study_setup, capsys):
    identity, path, study, delivery, messages, clock = _prepared_entry(study_setup)
    reserved = _reserve_entry(identity, path, study, delivery)
    now = reserved["attempted_ts"] + delivery.RESERVATION_RECOVERY_GRACE_SECONDS + 1
    report = delivery._reconcile_receipts(path, now, force=True)
    receipt = study._read(path)["records"][identity]["study_delivery"]["entry"]
    assert report["orphaned_reservations"] == 1
    assert report["orphaned_by_phase"] == {"entry": 1, "result": 0}
    assert receipt["status"] == "UNKNOWN"
    assert receipt["resolution_reason"] == "ORPHANED_RESERVATION_RECEIPT_UNAVAILABLE"
    assert receipt["no_retry"] is True
    clock[0] = now + 1
    delivery.dispatch(now_ts=now + 1, active_provider="FINNHUB")
    assert not messages
    evidence = capsys.readouterr().out
    assert "TSP_PHYSICAL_STUDY_DELIVERY_RECONCILIATION " in evidence
    assert identity not in evidence


def test_api_accepted_receipt_is_recovered_after_ledger_commit_interruption_without_duplicate(
        study_setup, monkeypatch):
    identity, path, study, delivery, messages, clock = _prepared_entry(study_setup)
    original_commit = delivery._commit_receipt

    def interrupted_commit(*args, **kwargs):
        raise TimeoutError("synthetic study-ledger contention after API acceptance")

    monkeypatch.setattr(delivery, "_commit_receipt", interrupted_commit)
    clock[0] = BASE + 33.1
    delivery.dispatch(now_ts=BASE + 33, active_provider="FINNHUB")
    assert len(messages) == 1
    assert study._read(path)["records"][identity]["study_delivery"]["entry"]["status"] == "RESERVED"
    journal = delivery._read_receipt_journal(path)
    assert len(journal["records"]) == 1
    record = next(iter(journal["records"].values()))
    assert record["study_id"] == identity and record["phase"] == "entry"
    assert record["receipt"]["status"] == "API_ACCEPTED"

    monkeypatch.setattr(delivery, "_commit_receipt", original_commit)
    recovered = delivery._reconcile_receipts(path, BASE + 34, force=True)
    receipt = study._read(path)["records"][identity]["study_delivery"]["entry"]
    assert recovered["recovered_receipts"] == 1
    assert receipt["status"] == "API_ACCEPTED"
    assert receipt["recovered_from_journal"] is True
    assert study.summary(now_ts=BASE + 34)["study_open_now_api_accepted"] == 1

    clock[0] = BASE + 35
    delivery.dispatch(now_ts=BASE + 35, active_provider="FINNHUB")
    assert len(messages) == 1
