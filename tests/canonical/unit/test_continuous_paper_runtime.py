from __future__ import annotations

import copy
import importlib
import json

import pytest

from tests.canonical.unit.test_live_score_severity_research import _prepare
from tests.canonical.unit.test_shadow_model_time_research import _opportunity, _sample


def _state_with_finalized_batch(module, params, evaluation):
    state = module._new(params, evaluation, 1000, "SMALL")
    ledger = state["levels"][0]["paper_trades"]
    for index in range(module.paper.MAX_TRADES):
        decision, handoff = _opportunity(signal_id=f"completed-{index}")
        assert module.paper.register(ledger, decision, handoff, now_ts=1062)
    module.paper.advance(ledger, _sample(1063), now_ts=1063, active_provider="FINNHUB")
    module.paper.advance(ledger, _sample(1183, 1.2), now_ts=1183, active_provider="FINNHUB")
    module.paper.validate(ledger)
    return state


def test_legacy_v2_continues_with_pending_expiry_without_editing_source(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    legacy = module._new(params, evaluation, 1000, "SMALL")
    legacy.update(protocol=module.LEGACY_PROTOCOL, deadline_ts=8200)
    legacy.pop("operating_mode")
    for row in legacy["levels"]:
        row.pop("archived_paper")
    decision, handoff = _opportunity()
    ledger = legacy["levels"][0]["paper_trades"]
    assert module.paper.register(ledger, decision, handoff, now_ts=1062)
    module.paper.advance(ledger, _sample(1063), now_ts=1063, active_provider="FINNHUB")
    old = canonical_runtime_root / "analytics/live_score_severity_research_v2/owner-live-severity.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps(legacy))
    before = old.read_bytes()
    module.observe(evaluation, params, now_ts=1100, provider="FINNHUB", buffer_mode="SMALL")
    path = module._path()
    assert path.is_file() and old.read_bytes() == before
    assert module.summary(now_ts=1101)["levels"][0]["paper_trades"]["pending"] == 1
    # A later session rename is irrelevant to persisted runtime identity.
    monkeypatch.setenv("OWNER_TIMING_SESSION_ID", "different-diagnostic")
    module = importlib.reload(module)
    module.advance_paper_trades(now_ts=1183, active_provider="FINNHUB", price_loader=lambda _: _sample(1183, 1.2))
    result = module.summary(now_ts=100000)
    assert result["status"] == "OBSERVING" and result["started_ts"] == 1000
    assert result["levels"][0]["paper_trades"]["outcomes"]["WIN"] == 1
    assert old.read_bytes() == before


def test_archiving_frees_capacity_preserves_raw_quotes_totals_and_new_pending(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    state = _state_with_finalized_batch(module, params, evaluation)
    path = module._path()
    originals = copy.deepcopy(state["levels"][0]["paper_trades"]["trades"])
    module._save(path, state)
    module.observe(evaluation, params, now_ts=1200, provider="FINNHUB", buffer_mode="SMALL")
    state = module._read(path)
    ledger = state["levels"][0]["paper_trades"]
    assert not ledger["trades"]
    archive = path.parent / "finalized/level-00/000000000001.json"
    raw = archive.read_bytes()
    assert json.loads(raw)["ledger"]["trades"] == originals
    # More than a lifetime 64 opportunities; completed evidence stays durable.
    for index in range(module.paper.MAX_TRADES):
        decision, handoff = _opportunity(signal_id=f"next-{index}", candle_ts=1200)
        assert module.paper.register(ledger, decision, handoff, now_ts=1262)
    module._save(path, state)
    module = importlib.reload(module)
    result = module.summary(now_ts=1263)["levels"][0]["paper_trades"]
    assert result["registered"] == 128 and result["pending"] == 64
    assert result["outcomes"]["WIN"] == 64
    assert result["capacity_rejections"] == 0 and result["archived_registered"] == 64
    assert archive.read_bytes() == raw


def test_archive_commit_recovers_after_interruption_without_loss_or_double_count(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    state = _state_with_finalized_batch(module, params, evaluation)
    path = module._path()
    module._save(path, state)
    before = path.read_bytes()
    module._archive_finalized(path, state)
    # Crash before the subsequent state commit. The checkpoint still has all
    # final records and zero archived totals, alongside a durable archive.
    assert path.read_bytes() == before
    module = importlib.reload(module)
    for _ in range(2):
        result = module.summary(now_ts=1200)["levels"][0]["paper_trades"]
        assert result["registered"] == 64 and result["outcomes"]["WIN"] == 64
    module.observe(evaluation, params, now_ts=1201, provider="FINNHUB", buffer_mode="SMALL")
    resumed = module._read(path)
    assert resumed["levels"][0]["archived_paper"]["batches"] == 1
    assert not resumed["levels"][0]["paper_trades"]["trades"]
    assert len(list(path.parent.glob("finalized/level-00/*.json"))) == 1


def test_archive_failure_preserves_live_checkpoint_and_all_quotes(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    state = _state_with_finalized_batch(module, params, evaluation)
    path = module._path()
    module._save(path, state)
    original = path.read_bytes()
    def disk_full(*_args, **_kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(module.storage, "save_json_atomic", disk_full)
    with pytest.raises(OSError):
        module.observe(evaluation, params, now_ts=1200, provider="FINNHUB", buffer_mode="SMALL")
    assert path.read_bytes() == original


def test_long_running_counter_is_not_limited_to_old_research_sample_size(canonical_runtime_root, monkeypatch):
    module, evaluation, params = _prepare(canonical_runtime_root, monkeypatch)
    state = module._new(params, evaluation, 1000, "SMALL")
    for row in state["levels"]:
        row.update(evaluations=100000, decision_kinds={"REJECT": 100000},
                   fsm_reason_families={"FSM_TRANSITION": 100000})
    module._save(module._path(), state)
    module.observe(evaluation, params, now_ts=1000000, provider="FINNHUB", buffer_mode="SMALL")
    result = module.summary(now_ts=1000001)
    assert result["status"] == "OBSERVING"
    assert all(row["evaluations"] == 100001 for row in result["levels"])


def test_legacy_timing_monitor_preserves_counts_and_keeps_reporting(canonical_runtime_root, monkeypatch):
    _prepare(canonical_runtime_root, monkeypatch)
    from intelligence import owner_timing_session as timing
    from tests.canonical.unit.test_owner_timing_session import _observe
    legacy = timing._new(1000, "a" * 64)
    legacy.update(protocol="OWNER_TIMING_SESSION_V1", deadline_ts=8200, evaluations=1,
                  decision_kinds={"REJECT": 1}, last_evaluation_ts=1000)
    legacy.pop("operating_mode")
    old = canonical_runtime_root / "analytics/owner_timing_sessions/owner-live-severity.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps(legacy))
    raw = old.read_bytes()
    _observe(timing, 100000)
    result = timing.summary(now_ts=100001)
    assert result["evaluations"] == 2 and result["deadline_ts"] is None
    assert result["started_ts"] == 1000 and result["status"] == "OBSERVING"
    assert old.read_bytes() == raw
