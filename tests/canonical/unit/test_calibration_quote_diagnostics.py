"""Synthetic quote-gap diagnostics, never market efficacy evidence."""
import copy
import json

import pytest

from tests.canonical.unit.test_execution_expiry_calibration import calibration, _capture, _entry, _advance


@pytest.mark.parametrize("mode,reason",[("entry","ENTRY_OBSERVATION_MISSING"),
                                     ("expiry","EXPIRY_OBSERVATION_MISSING"),
                                     ("provider","PROVIDER_CHANGED")])
def test_unknown_reasons_distinguish_entry_expiry_and_provider(calibration,mode,reason):
    module,params=calibration
    _capture(module,params,[_entry()])
    if mode!="entry":
        _advance(module,1001)
    if mode=="provider":
        _advance(module,1091,provider="TWELVE_DATA")
    else:
        module.advance(now_ts=1124,active_provider="FINNHUB",price_loader=lambda _:None)
    state=module._read(module._path())
    original=copy.deepcopy(state)
    report=module.analyze(state,now_ts=1124)
    assert state==original
    counts=report["paired_expiry_observations"][0]
    assert counts["unknown_reasons"]=={reason:1}
    assert counts["unknown"]==counts["buffer_unavailable"]==1
    assert counts["wins"]==counts["losses"]==counts["buffer_met"]==0


def test_unknown_historical_text_is_bounded_and_never_published(calibration):
    module,_=calibration
    records=[{"entry":None,"candidates":[{"outcome":"UNKNOWN","reason":"private arbitrary provider text"}]}]
    original=copy.deepcopy(records)
    counts=module._counts(records,0)
    assert counts["unknown_reasons"]=={"OTHER":1}
    assert "private arbitrary" not in json.dumps(counts)
    assert records==original


def test_pending_infeasible_and_successful_observations_are_not_quote_gaps(calibration):
    module,params=calibration
    _capture(module,params,[_entry(adjusted_seconds=115)])
    assert all(c["unknown_reasons"]=={} for c in module.summary(now_ts=1000)["paired_expiry_observations"])
    _advance(module,1001);_advance(module,1121,1.2)
    report=module.summary(now_ts=1121)
    assert all(c["unknown_reasons"]=={} for c in report["paired_expiry_observations"])
    assert report["paired_expiry_observations"][0]["wins"]==1
    assert report["paired_expiry_observations"][0]["buffer_met"]==1
