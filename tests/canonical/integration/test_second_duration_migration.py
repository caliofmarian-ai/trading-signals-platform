"""Keep pending historical observations intact when adopting seconds storage."""
from copy import deepcopy
import json

import pytest

from tests.canonical.integration.test_second_duration_pipeline import (
    BASE, _advance, _capture, _step, seconds_pipeline,
)


@pytest.mark.parametrize("protocol", ["PROSPECTIVE_PHYSICAL_V3_EXPIRY_V2", "PROSPECTIVE_PHYSICAL_V3_EXPIRY_V3", "PROSPECTIVE_PHYSICAL_V3_EXPIRY_V4"])
def test_upgrade_backs_up_exact_old_bytes_and_finishes_old_expiry(seconds_pipeline, protocol):
    ctx = seconds_pipeline
    _step(ctx, "PRE", 0, new_policy=False)
    _step(ctx, "CONFIRM", 3, new_policy=False)
    _capture(ctx)
    _advance(ctx, BASE + 36, 1.1)
    path = ctx["study"]._path()
    old = ctx["study"]._read(path)
    old["protocol"] = protocol
    assert "duration_policy" not in next(iter(old["records"].values()))["study_observation"]
    path.write_text(json.dumps(old), encoding="utf-8")
    original = path.read_bytes()
    records = deepcopy(old["records"])
    loaded = ctx["study"]._read(path)
    assert loaded["records"] == records
    ctx["study"]._save(path, loaded)
    backups = list((path.parent / "protocol_backups").glob("*.json"))
    assert len(backups) == 1 and backups[0].read_bytes() == original
    assert ctx["study"]._read(path)["protocol"] == ctx["study"].PROTOCOL
    assert ctx["study"]._read(path)["records"] == records
    expiry = BASE + 36 + 600
    saved = _advance(ctx, expiry, 1.1025)
    assert saved["study_observation"]["horizon_seconds"] == 600
    assert saved["study_observation"]["outcome"] == "WIN"
    assert "10 MIN 00 S" in ctx["photos"][-1]["caption"]
    assert len(list((path.parent / "protocol_backups").glob("*.json"))) == 1
    report = ctx["study"].summary(now_ts=expiry)
    assert ctx["plans"].POLICY not in report["published_study_results_by_duration_policy"]
    assert report["published_study_results_by_duration_policy"][ctx["plans"].LEGACY_POLICY]["wins"] == 1

