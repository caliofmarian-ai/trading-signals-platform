"""Prospective expiry calibration for the single scoreless physical V3 policy.

Every candidate is declared before its entry quote. Real quotes, exact horizons,
unknown observations and independent chronological holdouts remain separate.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
import time
from pathlib import Path
from statistics import NormalDist

from core import storage
from core import confirmed_study_duration as second_duration
from intelligence import shadow_model_time_research as quotes
from intelligence import buffer_expiry_evidence as buffer_evidence
from intelligence import expiry_price_estimate as expiry_estimate
from core.market_history_policy import HISTORY_POLICY

PROTOCOL = "PROSPECTIVE_PHYSICAL_V3_EXPIRY_V5"
PREVIOUS_PROTOCOL = "PROSPECTIVE_PHYSICAL_V3_EXPIRY_V4"
OLDER_PROTOCOL = "PROSPECTIVE_PHYSICAL_V3_EXPIRY_V3"
LEGACY_PROTOCOL = "PROSPECTIVE_PHYSICAL_V3_EXPIRY_V2"
BIASES = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25)
MAX_RECORDS = 512
MAX_BYTES = 4 * 1024 * 1024
MIN_TRAIN = 30
MIN_VALIDATION = 30
TRAIN_ENTRIES = 60
HOLDOUT_ENTRIES = 60
TARGET_WIN_RATE = 0.80
MAX_UNKNOWN_FRACTION = 0.10
VALIDATION_Z = NormalDist().inv_cdf(1 - 0.05 / 2)
REPORT_SECONDS = 60
# Allow a delayed retained tick to arrive without extending its source-time window.
# Post-isolation production evidence includes receive delays of 7.366 seconds.
# This prospectively frozen allowance addresses receipt latency, not source gaps.
LEGACY_BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS = 4.0
BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS = 15.0
QUOTE_RECOVERY_POLICY = "RETAINED_SOURCE_QUOTE_RECOVERY_V1"
LEGACY_QUOTE_RECOVERY_POLICY = "RETAINED_SOURCE_QUOTE_LEGACY_4S"
_last_report: dict[str, int] = {}
POST_MODEL_OFFSETS = (60, 180, 300)  # existing diagnostic checkpoints; never execution expiry
STUDY_DURATION_SOURCE = "CONFIRM_MODEL_TIME"
MAX_EXPIRY_ESTIMATES_PER_PASS = 8
EXPIRY_ESTIMATE_ARRIVAL_GRACE_SECONDS = 15.0


def _quote_recovery_policy():
    return {"policy": QUOTE_RECOVERY_POLICY,
            "arrival_grace_seconds": BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS,
            "expiry_window_seconds": quotes.MAX_SAMPLE_DELAY_SECONDS,
            "entry_window_seconds": quotes.MAX_ENTRY_DELAY_SECONDS}


def _quote_recovery_identity(row):
    return row.get("quote_recovery_policy", {}).get("policy", LEGACY_QUOTE_RECOVERY_POLICY)


def displayed_study_observation(row):
    """Use the prospectively confirmed horizon; retain old published baselines."""
    return row.get("study_observation", row["candidates"][0])


def _estimate_target(row):
    """Only a published study with a genuinely missing expiry may be enriched."""
    entry = row.get("entry")
    observation = displayed_study_observation(row)
    receipt = ((row.get("study_delivery") or {}).get("entry") or {})
    if (entry is None or receipt.get("status") != "API_ACCEPTED"
        or observation.get("outcome") != "UNKNOWN"
        or observation.get("reason") != "EXPIRY_OBSERVATION_MISSING"
        or observation.get("quote") is not None):
        return None
    return entry["observed_ts"] + observation["horizon_seconds"]


def _enrich_expiry_estimates(state, *, now, active_provider, bracket_loader):
    """Bound optional source lookups; complete and expired estimates never rescan.

    Metadata is independent of every official quote, outcome and duration. An
    unavailable estimate's last timestamp freezes it after the declared arrival
    deadline, including the first inspection of an already old historical gap.
    """
    if active_provider != "FINNHUB" or bracket_loader is None:
        return []
    candidates = []
    for identity, row in state["records"].items():
        target = _estimate_target(row)
        if target is None or now < target:
            continue
        previous = row.get("expiry_price_estimate")
        deadline = target + expiry_estimate.MAX_SIDE_SECONDS + EXPIRY_ESTIMATE_ARRIVAL_GRACE_SECONDS
        if previous is not None and (previous["estimated_outcome"] != "UNAVAILABLE"
                                     or previous["estimated_at"] >= deadline):
            continue
        candidates.append((target, identity, row, previous, deadline))
    updates = []
    # Dictionary checks are cheap; historical archive lookups are capped and
    # persisted, so old UNKNOWN rows do not repeatedly scan retained quote data.
    for target, identity, row, previous, deadline in sorted(
        candidates, key=lambda item: (item[0], item[1]), reverse=True
    )[:MAX_EXPIRY_ESTIMATES_PER_PASS]:
        try:
            bracket = bracket_loader("EUR/USD", target,
                                     max_side_seconds=expiry_estimate.MAX_SIDE_SECONDS)
        except Exception:
            # A transient lookup failure is not evidence that either side is
            # absent. Keep it eligible for a bounded later attempt.
            continue
        estimate = expiry_estimate.build_estimate(
            direction=row["direction"], entry=row["entry"], expiry_ts=target,
            bracket=bracket, observed_at=now)
        if (previous is not None and now < deadline
            and {k: v for k, v in previous.items() if k != "estimated_at"}
            == {k: v for k, v in estimate.items() if k != "estimated_at"}):
            continue
        row["expiry_price_estimate"] = estimate
        updates.append({"study_id": identity,
                        "signal_label": row["study_delivery"]["entry"].get("signal_label"),
                        "expiry_price_estimate": deepcopy(estimate)})
    return updates


def _published_estimate_counts(rows):
    unknown = [row for row in rows if _estimate_target(row) is not None]
    counts = Counter((row.get("expiry_price_estimate") or {}).get("estimated_outcome", "UNAVAILABLE")
                     for row in unknown)
    return {"contract": expiry_estimate.CONTRACT, "eligible_unknown": len(unknown),
            "estimates_available": counts["WIN"] + counts["LOSS"] + counts["INCONCLUSIVE"],
            "estimated_wins": counts["WIN"], "estimated_losses": counts["LOSS"],
            "inconclusive": counts["INCONCLUSIVE"], "unavailable": counts["UNAVAILABLE"]}


def _confirmed_study_feasible(horizon_seconds, adjusted_seconds):
    """Preserve the exact-fit tolerance of Model Time, expressed in minutes."""
    return horizon_seconds >= adjusted_seconds or math.isclose(
        horizon_seconds / 60, adjusted_seconds / 60, rel_tol=1e-12, abs_tol=1e-12
    )


def _buffer_policy():
    return {"contract": buffer_evidence.CONTRACT, "numeric_policy": buffer_evidence.NUMERIC_POLICY,
            "primary_target": "BUFFER_MET_AT_EXPIRY", "target_rate": TARGET_WIN_RATE,
            "selection": "TRAINING_BUFFER_WILSON_95_LOWER_THEN_LESS_PRESSURE",
            "historical_buffers_backfilled": False}


def _install_buffer_policy(state, now):
    if "buffer_objective" not in state:
        state.update(buffer_objective=_buffer_policy(), buffer_collection_started_ts=now)
        return True
    return False


def _number(value, *, zero=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (not zero and value == 0):
        raise ValueError("INVALID_CALIBRATION_NUMBER")
    return float(value)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _path():
    from core.owner_signal_delivery import destination
    if destination() is None or not quotes.enabled():
        return None
    path = Path(storage.root_path("analytics", "physical_v3_expiry_calibration", "recent_history_state.json"))
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("INVALID_CALIBRATION_PATH")
    return path


def _read(path):
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("INVALID_CALIBRATION_PATH")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("CALIBRATION_SIZE_LIMIT")
    state = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_CALIBRATION")))
    validate(state)
    return state


def _save(path, state):
    if state.get("protocol") in {PREVIOUS_PROTOCOL, OLDER_PROTOCOL, LEGACY_PROTOCOL} and path.exists():
        original = path.read_bytes()
        backup_dir = path.parent / "protocol_backups"
        if backup_dir.is_symlink():
            raise ValueError("INVALID_PROTOCOL_BACKUP_PATH")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / ("physical_pre_quote_recovery_" + hashlib.sha256(original).hexdigest() + ".json")
        if not backup.exists():
            with backup.open("xb") as handle:
                handle.write(original)
                handle.flush()
                import os
                os.fsync(handle.fileno())
        elif backup.read_bytes() != original:
            raise ValueError("PROTOCOL_BACKUP_MISMATCH")
    state["protocol"] = PROTOCOL
    validate(state)
    if len(json.dumps(state, allow_nan=False).encode()) > MAX_BYTES:
        raise ValueError("CALIBRATION_SIZE_LIMIT")
    storage.save_json_atomic(str(path), state)


def validate(state):
    if (not isinstance(state, dict) or state.get("protocol") not in {PROTOCOL, PREVIOUS_PROTOCOL, OLDER_PROTOCOL, LEGACY_PROTOCOL}
        or state.get("bias_grid") != list(BIASES) or not isinstance(state.get("records"), dict)
        or len(state["records"]) > MAX_RECORDS or type(state.get("capacity_rejections")) is not int
        or state["capacity_rejections"] < 0):
        raise ValueError("INVALID_CALIBRATION_STATE")
    _number(state["started_ts"])
    if "buffer_objective" in state:
        if state["buffer_objective"] != _buffer_policy():
            raise ValueError("BUFFER_OBJECTIVE_CHANGED")
        _number(state["buffer_collection_started_ts"])
    scope = state["scope"]
    if (scope.get("provider") != "FINNHUB" or scope.get("symbol") != "EUR/USD"
        or scope.get("history_policy") != HISTORY_POLICY
        or scope.get("buffer_mode") not in {"SMALL", "MEDIUM", "LARGE"}
        or not isinstance(scope.get("parameter_sha256"), str) or len(scope["parameter_sha256"]) != 64):
        raise ValueError("INVALID_CALIBRATION_SCOPE")
    seen_opportunities = set()
    for identity, row in state["records"].items():
        if "quote_recovery_policy" in row and row["quote_recovery_policy"] != _quote_recovery_policy():
            raise ValueError("INVALID_QUOTE_RECOVERY_POLICY")
        if (not isinstance(identity, str) or len(identity) != 64 or row.get("direction") not in {"BUY", "SELL"}
            or row.get("state") not in {"WAITING_ENTRY", "OBSERVING", "FINAL"}
            or not isinstance(row.get("policies"), dict) or not row["policies"]):
            raise ValueError("INVALID_CALIBRATION_RECORD")
        created, model, adjusted = (_number(row[k]) for k in ("created_ts", "model_seconds", "adjusted_seconds"))
        if adjusted > model or model > 86400:
            raise ValueError("INFEASIBLE_CALIBRATION_MODEL")
        if identity != _digest({**{k:row[k] for k in ("direction","created_ts","model_seconds","adjusted_seconds")}, "scope":scope}):
            raise ValueError("CALIBRATION_SOURCE_IDENTITY_CHANGED")
        if "buffer_snapshot" not in row:
            raise ValueError("PHYSICAL_BUFFER_SNAPSHOT_REQUIRED")
        if "buffer_snapshot" in row:
            if "buffer_objective" not in state:
                raise ValueError("BUFFER_OBJECTIVE_MISSING")
            frozen = row["buffer_snapshot"]
            buffer_evidence.validate_snapshot(frozen, scope["parameter_sha256"])
            if row.get("buffer_snapshot_sha256") != _digest(frozen):
                raise ValueError("BUFFER_SNAPSHOT_CHANGED")
        if "decision_snapshot" in row:
            frozen = row["decision_snapshot"]
            if (not isinstance(frozen, dict) or row.get("decision_snapshot_sha256") != _digest(frozen)
                or frozen.get("decision_policy") != "PHYSICAL_ONLY_V3"
                or frozen.get("history_policy") != HISTORY_POLICY
                or frozen.get("direction") != row["direction"]
                or frozen.get("market_context", {}).get("buffer_distance") != row["buffer_snapshot"]["buffer_distance"]):
                raise ValueError("PHYSICAL_DECISION_SNAPSHOT_CHANGED")
        for extra, offset in zip(row.get("post_model_observations", []), POST_MODEL_OFFSETS):
            if extra.get("offset_seconds") != offset or extra.get("horizon_seconds") != model + offset:
                raise ValueError("CHANGED_POST_MODEL_HORIZON")
        if "post_model_observations" in row and len(row["post_model_observations"]) != len(POST_MODEL_OFFSETS):
            raise ValueError("INVALID_POST_MODEL_GRID")
        for policy, context in row["policies"].items():
            if policy != "PHYSICAL_ONLY_V3":
                raise ValueError("INVALID_CALIBRATION_POLICY")
            opportunity_id = context.get("opportunity_signal_id")
            if (not isinstance(opportunity_id, str) or not opportunity_id.startswith("sig-v3-")
                or opportunity_id in seen_opportunities):
                raise ValueError("INVALID_OR_REPEATED_PHYSICAL_OPPORTUNITY")
            seen_opportunities.add(opportunity_id)
            if "decision_snapshot" in row:
                snapshot = row["decision_snapshot"]
                if (snapshot.get("signal_id") != opportunity_id
                    or snapshot.get("decision_id") != context.get("open_decision_id")
                    or snapshot.get("decision_audit_id") != context.get("open_decision_audit_id")):
                    raise ValueError("DECISION_SNAPSHOT_SOURCE_MISMATCH")
            pre, confirm, opened = (_number(context[k]) for k in ("pre_ts", "confirm_ts", "open_ts"))
            _number(context["confirm_model_seconds"])
            for key in ("open_decision_id", "open_decision_audit_id"):
                if key in context and (not isinstance(context[key], str) or not context[key].strip()):
                    raise ValueError("INVALID_BUFFER_DECISION_SOURCE")
            if not pre < confirm < opened == created or opened - pre < 30:
                raise ValueError("INVALID_CALIBRATION_STAGE_ORDER")
        entry = row["entry"]
        if entry is not None:
            stamp = _number(entry.get("observed_ts"))
            if _observed_quote(entry, stamp) != entry or not created <= stamp <= created + quotes.MAX_ENTRY_DELAY_SECONDS:
                raise ValueError("INVALID_CALIBRATION_ENTRY")
        if (row["state"] == "WAITING_ENTRY") != (entry is None and any(c["outcome"] == "PENDING" for c in row["candidates"])):
            raise ValueError("INVALID_CALIBRATION_ENTRY_STATE")
        candidates = row["candidates"]
        if len(candidates) != len(BIASES):
            raise ValueError("INVALID_CALIBRATION_GRID")
        for bias, candidate in zip(BIASES, candidates):
            horizon = _number(candidate["horizon_seconds"])
            if candidate["bias"] != bias or not math.isclose(horizon, model * (1 - bias), abs_tol=1e-9):
                raise ValueError("CHANGED_CALIBRATION_HORIZON")
            outcome = candidate["outcome"]
            if outcome not in {"PENDING", "INFEASIBLE", "UNKNOWN", "WIN", "LOSS", "DRAW"}:
                raise ValueError("INVALID_CALIBRATION_OUTCOME")
            if (horizon < adjusted) != (outcome == "INFEASIBLE"):
                raise ValueError("INVALID_CALIBRATION_FEASIBILITY")
            expiry = candidate["quote"]
            if outcome in {"WIN", "LOSS", "DRAW"}:
                stamp = _number(expiry.get("observed_ts"))
                if (entry is None or _observed_quote(expiry, stamp) != expiry
                    or not entry["observed_ts"] + horizon <= stamp <= entry["observed_ts"] + horizon + quotes.MAX_SAMPLE_DELAY_SECONDS
                    or quotes._classify(row["direction"], entry["price"], expiry["price"]) != outcome):
                    raise ValueError("INVALID_CALIBRATION_LABEL")
            elif expiry is not None:
                raise ValueError("UNOBSERVED_CALIBRATION_LABEL")
        if (row["state"] == "FINAL") != all(c["outcome"] != "PENDING" for c in candidates):
            raise ValueError("INVALID_CALIBRATION_FINAL_STATE")
        for extra in row.get("post_model_observations", []):
            outcome, sample = extra["outcome"], extra["quote"]
            if outcome not in {"PENDING", "UNKNOWN", "WIN", "LOSS", "DRAW"}:
                raise ValueError("INVALID_POST_MODEL_OUTCOME")
            if outcome in {"WIN", "LOSS", "DRAW"}:
                stamp = _number(sample.get("observed_ts"))
                if (entry is None or _observed_quote(sample, stamp) != sample
                    or not entry["observed_ts"] + extra["horizon_seconds"] <= stamp
                    <= entry["observed_ts"] + extra["horizon_seconds"] + quotes.MAX_SAMPLE_DELAY_SECONDS
                    or quotes._classify(row["direction"], entry["price"], sample["price"]) != outcome):
                    raise ValueError("INVALID_POST_MODEL_LABEL")
            elif sample is not None:
                raise ValueError("UNOBSERVED_POST_MODEL_LABEL")
        if "study_observation" in row:
            observation = row["study_observation"]
            context = row["policies"]["PHYSICAL_ONLY_V3"]
            horizon = _number(observation.get("horizon_seconds"))
            if (observation.get("duration_source") != STUDY_DURATION_SOURCE
                or observation.get("confirmed_ts") != context["confirm_ts"]
                or horizon > scope["model_limits_minutes"]["max"] * 60):
                raise ValueError("CHANGED_CONFIRMED_STUDY_HORIZON")
            if any(key in observation for key in ("duration_policy", "duration_seconds", "duration_plan")):
                second_duration.validate_observation(row, scope)
            elif horizon != context["confirm_model_seconds"]:
                raise ValueError("CHANGED_CONFIRMED_STUDY_HORIZON")
            outcome, sample = observation.get("outcome"), observation.get("quote")
            if outcome not in {"PENDING", "INFEASIBLE", "UNKNOWN", "WIN", "LOSS", "DRAW"}:
                raise ValueError("INVALID_CONFIRMED_STUDY_OUTCOME")
            if (not _confirmed_study_feasible(horizon, adjusted)) != (outcome == "INFEASIBLE"):
                raise ValueError("INVALID_CONFIRMED_STUDY_FEASIBILITY")
            if outcome in {"WIN", "LOSS", "DRAW"}:
                stamp = _number(sample.get("observed_ts"))
                if (entry is None or _observed_quote(sample, stamp) != sample
                    or not entry["observed_ts"] + horizon <= stamp
                    <= entry["observed_ts"] + horizon + quotes.MAX_SAMPLE_DELAY_SECONDS
                    or quotes._classify(row["direction"], entry["price"], sample["price"]) != outcome):
                    raise ValueError("INVALID_CONFIRMED_STUDY_LABEL")
            elif sample is not None:
                raise ValueError("UNOBSERVED_CONFIRMED_STUDY_LABEL")
        from intelligence.physical_study_delivery import validate_delivery
        validate_delivery(row)
        if "expiry_price_estimate" in row:
            target = _estimate_target(row)
            if target is None:
                raise ValueError("EXPIRY_ESTIMATE_WITHOUT_MISSING_PUBLISHED_EXPIRY")
            expiry_estimate.validate_estimate(row["expiry_price_estimate"],
                direction=row["direction"], entry=entry, expiry_ts=target)


def capture(entries, *, params, buffer_mode, strategy_version, canonical_spec, now_ts):
    """Capture only first accepted research chains; identical entries share one quote experiment."""
    path = _path()
    if path is None or not entries:
        return
    if (params.get("decision_policy") != "PHYSICAL_ONLY_V3" or "score_thresholds" in params
        or params.get("history_policy") != HISTORY_POLICY):
        raise ValueError("PHYSICAL_POLICY_REQUIRED")
    from core.physical_params import validate_physical_params
    validate_physical_params(params)
    now = _number(now_ts)
    from core.runtime_execution_calibration import algo_params_sha256
    scope = {"provider": "FINNHUB", "symbol": "EUR/USD", "buffer_mode": buffer_mode,
             "history_policy": HISTORY_POLICY,
             "parameter_sha256": algo_params_sha256(params), "strategy_version": strategy_version,
             "canonical_spec": canonical_spec, "model_limits_minutes": params["expiry_limits_minutes"]}
    with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=0.2):
        state = _read(path) or {"protocol": PROTOCOL, "bias_grid": list(BIASES), "scope": scope,
                               "started_ts": now, "records": {}, "capacity_rejections": 0}
        if state["scope"] != scope:
            raise ValueError("CALIBRATION_SCOPE_CHANGED")
        _install_buffer_policy(state, now)
        variants = {"PHYSICAL_ONLY_V3": {"decision_policy": "PHYSICAL_ONLY_V3",
                      "parameter_sha256": algo_params_sha256(params)}}
        if state.get("policy_scopes",variants) != variants:
            raise ValueError("CALIBRATION_VARIANT_SCOPE_CHANGED")
        state["policy_scopes"] = variants
        for item in entries:
            # No backfilled PRE/CONFIRM evidence for chains begun before this release.
            if item.get("confirm_model_seconds") is None:
                continue
            row = {key: item[key] for key in ("direction", "created_ts", "model_seconds", "adjusted_seconds")}
            identity = _digest({**row, "scope": scope})
            context = {key: item[key] for key in ("pre_ts", "confirm_ts", "open_ts", "confirm_model_seconds")}
            opportunity_id = item.get("opportunity_signal_id")
            if not isinstance(opportunity_id, str) or not opportunity_id.startswith("sig-v3-"):
                raise ValueError("PHYSICAL_OPPORTUNITY_ID_REQUIRED")
            if any(opportunity_id == prior.get("policies", {}).get("PHYSICAL_ONLY_V3", {}).get("opportunity_signal_id")
                   for prior in state["records"].values()):
                continue  # restart/crash recovery must not multiply one setup
            context["opportunity_signal_id"] = opportunity_id
            for key in ("open_decision_id", "open_decision_audit_id"):
                if key in item:
                    if not isinstance(item[key], str) or not item[key].strip():
                        raise ValueError("INVALID_BUFFER_DECISION_SOURCE")
                    context[key] = item[key]
            frozen = buffer_evidence.snapshot(item.get("buffer_distance"), scope["parameter_sha256"])
            policy = str(item["policy"])
            if identity in state["records"]:
                # An old entry is never upgraded using today's ATR/buffer.
                existing = state["records"][identity]
                if "buffer_snapshot" in existing and existing["buffer_snapshot"] != frozen:
                    raise ValueError("BUFFER_SNAPSHOT_REWRITE")
                if "buffer_snapshot" not in existing:
                    context = {key: item[key] for key in ("pre_ts", "confirm_ts", "open_ts", "confirm_model_seconds")}
                prior = state["records"][identity]["policies"].get(policy)
                if prior is not None and prior != context:
                    raise ValueError("CALIBRATION_CHAIN_REWRITE")
                state["records"][identity]["policies"][policy] = context
                continue
            if len(state["records"]) >= MAX_RECORDS:
                state["capacity_rejections"] += 1
                continue
            row.update(policies={policy: context}, state="WAITING_ENTRY", entry=None,
                       quote_recovery_policy=_quote_recovery_policy(),
                       buffer_snapshot=frozen, buffer_snapshot_sha256=_digest(frozen),
                       candidates=[{"bias": bias, "horizon_seconds": row["model_seconds"] * (1 - bias),
                                    "outcome": "INFEASIBLE" if row["model_seconds"] * (1 - bias) < row["adjusted_seconds"] else "PENDING",
                                    "reason": None, "quote": None} for bias in BIASES])
            if item.get("decision_snapshot") is not None:
                row["decision_snapshot"] = item["decision_snapshot"]
                row["decision_snapshot_sha256"] = _digest(row["decision_snapshot"])
                row["post_model_observations"] = [{"offset_seconds": offset,
                    "horizon_seconds": row["model_seconds"] + offset,
                    "outcome": "PENDING", "reason": None, "quote": None}
                    for offset in POST_MODEL_OFFSETS]
            if (item.get("publish_study") is True
                and item.get("confirm_execution_status") == "UNAVAILABLE"):
                # Only chains marked at PRE use the new seconds plan. Never
                # manufacture a plan at OPEN or fall back after a missing plan.
                duration_policy = item.get("study_duration_policy")
                plan = item.get("confirmed_study_plan")
                if duration_policy is not None and duration_policy != second_duration.POLICY:
                    raise ValueError("UNKNOWN_STUDY_DURATION_POLICY")
                if duration_policy is None and plan is not None:
                    raise ValueError("UNMARKED_CONFIRMED_SECONDS_PLAN")
                if duration_policy is None or plan is not None:
                    if plan is not None:
                        second_duration.validate_plan(plan)
                    confirmed_seconds = (plan["duration_seconds"] if plan is not None
                                         else _number(item["confirm_model_seconds"]))
                    row["study_delivery"] = {"entry": None, "result": None}
                    row["study_observation"] = {
                        "duration_source": STUDY_DURATION_SOURCE,
                        "confirmed_ts": item["confirm_ts"],
                        "horizon_seconds": confirmed_seconds,
                        "outcome": "PENDING" if _confirmed_study_feasible(confirmed_seconds, row["adjusted_seconds"]) else "INFEASIBLE",
                        "reason": None, "quote": None,
                    }
                    if plan is not None:
                        row["study_observation"].update(duration_policy=second_duration.POLICY,
                            duration_seconds=confirmed_seconds, duration_plan=deepcopy(plan))
                        second_duration.validate_observation(row, scope)
            state["records"][identity] = row
        _save(path, state)


def _observed_quote(raw, now):
    """Accept retained genuine provider ticks separately from fresh poll samples."""
    if isinstance(raw, dict) and raw.get("source") in (
        "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1", "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1"
    ):
        if raw.get("provider") != "FINNHUB" or str(raw.get("symbol", "")).replace("/", "") != "EURUSD":
            return None
        try:
            stamp, price = _number(raw.get("observed_ts")), _number(raw.get("price"))
        except ValueError:
            return None
        if stamp > now:
            return None
        return {"provider": "FINNHUB", "symbol": "EUR/USD", "price": price,
                "observed_ts": stamp, "source": raw["source"]}
    return quotes._sample(raw, now)


def _window_quote(loader, latest, target, delay, now):
    if loader is None:
        sample = latest
    else:
        try:
            sample = _observed_quote(loader("EUR/USD", target, delay), now)
        except Exception:
            sample = None
    return sample if sample and target <= sample["observed_ts"] <= target + delay else None


def advance(*, now_ts, active_provider, price_loader, observation_loader=None, bracket_loader=None):
    path = _path()
    if path is None:
        return None
    now = _number(now_ts)
    with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=0.2):
        state = _read(path)
        if state is None:
            state = None
        else:
            pending = [r for r in state["records"].values() if r["state"] != "FINAL"
                       or any(c["outcome"] == "PENDING" for c in r.get("post_model_observations", []))
                       or r.get("study_observation", {}).get("outcome") == "PENDING"]
            sample = None
            if pending and active_provider == "FINNHUB":
                try:
                    sample = quotes._sample(price_loader("EUR/USD"), now)
                except Exception:
                    pass
            changed = _install_buffer_policy(state, now)
            for row in pending:
                arrival_grace = (row.get("quote_recovery_policy", {}).get(
                    "arrival_grace_seconds", LEGACY_BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS
                ) if observation_loader is not None else 0.0)
                if now < row["created_ts"]:
                    continue
                reason = "PROVIDER_CHANGED" if active_provider != "FINNHUB" else None
                if row["entry"] is None and reason is None:
                    entry_quote = _window_quote(observation_loader, sample, row["created_ts"],
                                                quotes.MAX_ENTRY_DELAY_SECONDS, now)
                    if entry_quote:
                        row.update(entry=entry_quote, state="OBSERVING")
                        changed = True
                    elif now > row["created_ts"] + quotes.MAX_ENTRY_DELAY_SECONDS + arrival_grace:
                        reason = "ENTRY_OBSERVATION_MISSING"
                observations = row["candidates"] + row.get("post_model_observations", [])
                if "study_observation" in row:
                    observations += [row["study_observation"]]
                for candidate in observations:
                    if candidate["outcome"] != "PENDING":
                        continue
                    if reason:
                        candidate.update(outcome="UNKNOWN", reason=reason)
                        changed = True
                    elif row["entry"] is not None:
                        target = row["entry"]["observed_ts"] + candidate["horizon_seconds"]
                        expiry_quote = _window_quote(observation_loader, sample, target,
                                                    quotes.MAX_SAMPLE_DELAY_SECONDS, now)
                        if expiry_quote:
                            candidate.update(quote=expiry_quote, outcome=quotes._classify(row["direction"], row["entry"]["price"], expiry_quote["price"]), reason="OBSERVED_PAIRED_EXPIRY")
                            changed = True
                        elif now > target + quotes.MAX_SAMPLE_DELAY_SECONDS + arrival_grace:
                            candidate.update(outcome="UNKNOWN", reason="EXPIRY_OBSERVATION_MISSING")
                            changed = True
                if all(c["outcome"] != "PENDING" for c in row["candidates"]):
                    row["state"] = "FINAL"
            estimate_updates = _enrich_expiry_estimates(state, now=now,
                active_provider=active_provider, bracket_loader=bracket_loader)
            changed = bool(estimate_updates) or changed
            if changed:
                _save(path, state)
                for update in estimate_updates:
                    print("TSP_PHYSICAL_EXPIRY_PRICE_ESTIMATE " + json.dumps(update, sort_keys=True), flush=True)
    if state is not None and any(
        r["entry"] is not None and isinstance(r.get("study_delivery"), dict)
        and (r["study_delivery"]["entry"] is None
             or ((r["study_delivery"]["entry"] or {}).get("status") == "API_ACCEPTED"
                 and r["study_delivery"]["result"] is None
                 and displayed_study_observation(r)["outcome"] not in {"PENDING", "INFEASIBLE"}))
        for r in state["records"].values()
    ):
        from intelligence import physical_study_delivery
        physical_study_delivery.dispatch_async(now_ts=now, active_provider=active_provider)
    slot = int(now // REPORT_SECONDS)
    if _last_report.get(str(path), -1) < slot:
        report = analyze(state, now_ts=now)
        print("TSP_PHYSICAL_V3_EXPIRY_CALIBRATION " + json.dumps(_compact(report), sort_keys=True), flush=True)
        _last_report[str(path)] = slot
        return report
    return None


# Outcome measurement and interval arithmetic are shared with historical
# experiments. No historical decision or score-selection function is called.
from intelligence.execution_expiry_calibration import _wilson, _counts, _quantiles


def _compact(report):
    fields = ("pressure_bias", "blocking_gates", "decisive", "wins", "losses", "draws", "unknown",
              "unknown_fraction", "unknown_reasons", "infeasible", "buffer_sample",
              "buffer_unavailable", "buffer_unknown_fraction", "buffer_met",
              "buffer_not_met", "buffer_wilson_95_lower")
    policies = []
    for row in report["policies"]:
        compact_row = {key: value for key, value in row.items()
                       if key not in {"train_candidates", "proposal_only", "buffer_expiry_observations"}}
        compact_row["training_candidate_quality"] = [
            {key: candidate[key] for key in fields} for candidate in row["train_candidates"]
        ]
        policies.append(compact_row)
    return {**report, "policies": policies}


def _training_blockers(counts, training_complete):
    if not training_complete:
        return ["TRAINING_LOT_INCOMPLETE"]
    blockers = []
    if counts["decisive"] < MIN_TRAIN:
        blockers.append("DIRECTION_DECISIVE_COUNT_BELOW_MINIMUM")
    if counts["unknown_fraction"] is not None and counts["unknown_fraction"] > MAX_UNKNOWN_FRACTION:
        blockers.append("DIRECTION_UNKNOWN_FRACTION_ABOVE_MAXIMUM")
    if counts["buffer_sample"] < MIN_TRAIN:
        blockers.append("BUFFER_KNOWN_COUNT_BELOW_MINIMUM")
    if counts["buffer_unknown_fraction"] is not None and counts["buffer_unknown_fraction"] > MAX_UNKNOWN_FRACTION:
        blockers.append("BUFFER_UNKNOWN_FRACTION_ABOVE_MAXIMUM")
    return blockers


def analyze(state, *, now_ts):
    report = {"protocol": PROTOCOL, "truth_domain": "HYPOTHETICAL_RESEARCH", "observed_at": now_ts,
              "status": "WAITING_FIRST_COMPLETE_CHAIN", "bias_grid": list(BIASES),
              "unique_entry_experiments": 0, "pending": 0, "policies": [],
              "observed_entry_quotes":0, "finalized_entry_experiments":0,
              "entry_quote_delay_seconds":_quantiles([]), "paired_expiry_observations":[],
              "buffer_objective":_buffer_policy(), "legacy_directional_only_entries":0,
              "prospective_buffer_entries":0, "buffer_collection_started_ts":None,
              "buffered_quote_collection": {"entry_source_window_seconds": quotes.MAX_ENTRY_DELAY_SECONDS,
                  "expiry_source_window_seconds": quotes.MAX_SAMPLE_DELAY_SECONDS,
                  "missing_quote_arrival_grace_seconds": BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS,
                  "legacy_missing_quote_arrival_grace_seconds": LEGACY_BUFFERED_QUOTE_ARRIVAL_GRACE_SECONDS,
                  "prospective_recovery_policy": QUOTE_RECOVERY_POLICY},
              "readiness_policy": {"minimum_train_decisive": MIN_TRAIN, "minimum_validation_decisive": MIN_VALIDATION,
                                   "fixed_train_entries":TRAIN_ENTRIES, "fixed_holdout_entries":HOLDOUT_ENTRIES,
                                   "target_win_rate": TARGET_WIN_RATE,
                                   "primary_target":buffer_evidence.CONTRACT,
                                   "minimum_buffer_validation_familywise_95_lower":TARGET_WIN_RATE,
                                   "minimum_validation_familywise_95_lower": TARGET_WIN_RATE,
                                   "multiple_policy_correction":"SINGLE_PREDECLARED_POLICY_FIXED_HOLDOUT",
                                   "maximum_unknown_fraction": MAX_UNKNOWN_FRACTION,
                                   "split": "CHRONOLOGICAL_NONOVERLAPPING_TRAIN_THEN_UNTOUCHED_HOLDOUT"},
              "execution_calibration_proven": False, "automatic_activation_allowed": False,
              "production_parameters_changed": False, "broker_executed": False,
              "actual_telegram_publications": 0, "decision_policy": "PHYSICAL_ONLY_V3",
              "history_policy": HISTORY_POLICY,
              "published_study_results": _counts([], 0),
              "published_study_results_scope": "ALL_HISTORICAL_DURATION_POLICIES",
              "published_study_results_by_duration_policy": {},
              "published_study_results_by_quote_recovery_policy": {},
              "published_study_expiry_estimates": _published_estimate_counts([])}
    if state is None:
        from intelligence.same_symbol_sequences import summarize
        report["same_symbol_10min_sequences"] = summarize([])
        return report
    validate(state)
    records = list(state["records"].values())
    from intelligence.same_symbol_sequences import summarize
    report["same_symbol_10min_sequences"] = summarize(records)
    report.update(scope=state["scope"], unique_entry_experiments=len(records),
                  pending=sum(r["state"] != "FINAL" for r in records),
                  capacity_rejections=state["capacity_rejections"],
                  status="CAPACITY_REACHED" if len(records) >= MAX_RECORDS else "COLLECTING")
    report["observed_entry_quotes"] = sum(r["entry"] is not None for r in records)
    report["finalized_entry_experiments"] = sum(r["state"] == "FINAL" for r in records)
    report["legacy_directional_only_entries"] = sum("buffer_snapshot" not in r for r in records)
    report["prospective_buffer_entries"] = sum("buffer_snapshot" in r for r in records)
    report["buffer_collection_started_ts"] = state.get("buffer_collection_started_ts")
    report["decision_snapshot_entries"] = sum("decision_snapshot" in r for r in records)
    report["entry_quote_sources"] = dict(Counter(r["entry"]["source"] for r in records if r["entry"]))
    report["expiry_quote_sources"] = dict(Counter(c["quote"]["source"] for r in records
                                                for c in r["candidates"] if c["quote"]))
    report["study_open_now_api_accepted"] = sum((r.get("study_delivery") or {}).get("entry", {}).get("status") == "API_ACCEPTED"
        for r in records if (r.get("study_delivery") or {}).get("entry"))
    report["study_results_api_accepted"] = sum((r.get("study_delivery") or {}).get("result", {}).get("status") == "API_ACCEPTED"
        for r in records if (r.get("study_delivery") or {}).get("result"))
    # Published results refer to the duration shown at CONFIRM. Research
    # baseline counts remain separate even when their eventual outcomes differ.
    report["published_study_results"] = _counts([
        {**r, "candidates": [displayed_study_observation(r)]} for r in records
        if ((r.get("study_delivery") or {}).get("result") or {}).get("status") == "API_ACCEPTED"
    ], 0)
    delivered = [r for r in records
                 if ((r.get("study_delivery") or {}).get("result") or {}).get("status") == "API_ACCEPTED"]
    report["published_study_expiry_estimates"] = _published_estimate_counts(delivered)
    report["published_study_results_by_duration_policy"] = {
        policy: _counts([{**r, "candidates": [displayed_study_observation(r)]}
                         for r in delivered if second_duration.observation_policy(r) == policy], 0)
        for policy in sorted({second_duration.observation_policy(r) for r in delivered})
    }
    report["published_study_results_by_quote_recovery_policy"] = {
        policy: _counts([{**r, "candidates": [displayed_study_observation(r)]}
                         for r in delivered if _quote_recovery_identity(r) == policy], 0)
        for policy in sorted({_quote_recovery_identity(r) for r in delivered})
    }
    report["study_delivery_statuses"] = dict(Counter(
        f"{phase}:{receipt['status']}" for r in records
        for phase, receipt in (r.get("study_delivery") or {}).items() if receipt))
    report["post_model_diagnostics"] = [{"offset_seconds": offset, **_counts([
        {**r, "candidates": r["post_model_observations"]} for r in records
        if "post_model_observations" in r], index)} for index, offset in enumerate(POST_MODEL_OFFSETS)]
    report["post_model_execution_authority"] = False
    report["baseline_model_observations"] = _counts(records, 0)
    report["by_observed_trend"] = [{"trend_context": trend, "entries": len(group), **_counts(group, 0)}
        for trend in ("WITH_TREND", "FLAT", "COUNTER_TREND")
        if (group := [r for r in records if (r.get("decision_snapshot") or {}).get("market_context", {}).get("trend_context") == trend])]
    report["entry_quote_delay_seconds"] = _quantiles([
        r["entry"]["observed_ts"]-r["created_ts"] for r in records if r["entry"] is not None])
    report["paired_expiry_observations"] = [{"pressure_bias":bias, **_counts(records,index),
        "pending":sum(r["candidates"][index]["outcome"] == "PENDING" for r in records),
        "expiry_quote_delay_seconds":_quantiles([
            r["candidates"][index]["quote"]["observed_ts"]-r["entry"]["observed_ts"]-r["candidates"][index]["horizon_seconds"]
            for r in records if r["candidates"][index]["quote"] is not None])}
        for index,bias in enumerate(BIASES)]
    for policy in ("PHYSICAL_ONLY_V3",):
        rows = sorted((r for r in records if str(policy) in r["policies"]), key=lambda r:r["created_ts"])
        buffer_rows = [r for r in rows if "buffer_snapshot" in r]
        independent, next_entry = [], 0.0
        # Partition every admitted entry before looking at its eventual outcome.
        # Use the longest declared horizon, even when its quote was missed.
        for row in buffer_rows:
            if row["created_ts"] >= next_entry:
                independent.append(row)
                next_entry = row["created_ts"] + quotes.MAX_ENTRY_DELAY_SECONDS + row["model_seconds"] + quotes.MAX_SAMPLE_DELAY_SECONDS
        train, holdout = independent[:TRAIN_ENTRIES], independent[TRAIN_ENTRIES:TRAIN_ENTRIES+HOLDOUT_ENTRIES]
        train_counts = [_counts(train,i) for i in range(len(BIASES))]
        training_complete = len(train) == TRAIN_ENTRIES and all(r["state"] == "FINAL" for r in train)
        train_blockers = [_training_blockers(counts, training_complete) for counts in train_counts]
        eligible = [i for i, blockers in enumerate(train_blockers) if not blockers]
        selected = max(eligible,key=lambda i:(train_counts[i]["buffer_wilson_95_lower"],-BIASES[i])) if eligible else None
        validation = _counts(holdout,selected) if selected is not None else None
        if validation is not None:
            validation["familywise_95_lower"] = _wilson(validation["wins"],validation["decisive"],z=VALIDATION_Z)
            validation["buffer_familywise_95_lower"] = _wilson(validation["buffer_met"],validation["buffer_sample"],z=VALIDATION_Z)
        selected_bias = BIASES[selected] if selected is not None else None
        delta, violations = None, None
        if selected is not None:
            bounds = state["scope"]["model_limits_minutes"]
            delta = max([bounds["max"] * selected_bias] +
                        [abs(r["policies"][str(policy)]["confirm_model_seconds"] -
                             r["model_seconds"] * (1 - selected_bias))/60 for r in train])
            minimum, maximum = bounds["min"]*(1-selected_bias), bounds["max"]
            violations = sum(not max(minimum,r["policies"][str(policy)]["confirm_model_seconds"]/60-delta)
                             <= r["model_seconds"]*(1-selected_bias)/60
                             <= min(maximum,r["policies"][str(policy)]["confirm_model_seconds"]/60+delta)
                             for r in holdout)
        passed = bool(len(holdout) == HOLDOUT_ENTRIES and all(r["state"] == "FINAL" for r in holdout)
                      and validation and validation["decisive"] >= MIN_VALIDATION
                      and validation["unknown_fraction"] <= MAX_UNKNOWN_FRACTION
                      and validation["familywise_95_lower"] >= TARGET_WIN_RATE
                      and validation["buffer_sample"] >= MIN_VALIDATION
                      and validation["buffer_unknown_fraction"] <= MAX_UNKNOWN_FRACTION
                      and validation["buffer_familywise_95_lower"] >= TARGET_WIN_RATE and violations == 0)
        variant_scope = state.get("policy_scopes",{}).get(str(policy))
        if variant_scope is None:
            passed = False
            status = "VARIANT_SCOPE_UNAVAILABLE"
        elif not training_complete:
            status = "COLLECTING_TRAINING"
        elif selected is None:
            status = "TRAINING_DATA_QUALITY_FAILED"
        elif len(holdout) < HOLDOUT_ENTRIES or not all(r["state"] == "FINAL" for r in holdout):
            status = "COLLECTING_HOLDOUT"
        elif validation["decisive"] < MIN_VALIDATION:
            status = "HOLDOUT_SAMPLE_INADEQUATE"
        elif validation["unknown_fraction"] > MAX_UNKNOWN_FRACTION:
            status = "HOLDOUT_DATA_QUALITY_FAILED"
        elif validation["buffer_sample"] < MIN_VALIDATION or validation["buffer_unknown_fraction"] > MAX_UNKNOWN_FRACTION:
            status = "HOLDOUT_BUFFER_DATA_QUALITY_FAILED"
        elif violations:
            status = "CONFIRM_INTERVAL_VALIDATION_FAILED"
        elif passed:
            status = "READY_FOR_REVIEW"
        elif validation["familywise_95_lower"] >= TARGET_WIN_RATE:
            status = "BUFFER_TARGET_NOT_MET"
        else:
            status = "EFFICACY_TARGET_NOT_MET"
        row_summary = {"policy":policy, "unique_entries":len(rows), "prospective_buffer_entries":len(buffer_rows),
                       "legacy_directional_only_entries":len(rows)-len(buffer_rows), "nonoverlapping_entries":len(independent),
                       "train_entries":len(train), "holdout_entries":len(holdout),
                       "train_candidates": [{"pressure_bias": bias, "blocking_gates": blockers, **counts}
                                            for bias, blockers, counts in zip(BIASES, train_blockers, train_counts)],
                       "buffer_expiry_observations":[{"pressure_bias":b,**_counts(rows,i)} for i,b in enumerate(BIASES)],
                       "training_selected_bias":BIASES[selected] if selected is not None else None,
                       "holdout_confirm_interval_violations":violations,
                       "untouched_holdout":validation, "status":status,
                       "timing_seconds":{name:_quantiles([r["policies"][str(policy)][after]-r["policies"][str(policy)][before] for r in rows])
                           for name,before,after in (("pre_to_confirm","pre_ts","confirm_ts"),
                                                    ("confirm_to_open","confirm_ts","open_ts"),
                                                    ("pre_to_open","pre_ts","open_ts"))}}
        if passed:
            row_summary["proposal_only"] = {"pressure_bias":BIASES[selected],
                "objective_contract":buffer_evidence.CONTRACT, "validated_buffer_target_rate":TARGET_WIN_RATE,
                "validated_policy":policy, "validated_parameter_sha256":variant_scope["parameter_sha256"],
                "decision_policy":variant_scope["decision_policy"],
                "confirm_delta_minutes":delta,
                "minimum_expiry_minutes":bounds["min"]*(1-BIASES[selected]),
                "maximum_expiry_minutes":bounds["max"], "source_evidence_sha256":_digest(state)}
        report["policies"].append(row_summary)
    report["ready_policies"] = [r["policy"] for r in report["policies"] if r["status"] == "READY_FOR_REVIEW"]
    if report["ready_policies"]:
        report["status"] = "PROPOSALS_REQUIRE_REVIEW"
    return report


def summary(*, now_ts=None):
    path = _path()
    with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=0.2):
        state = _read(path) if path else None
    return analyze(state, now_ts=time.time() if now_ts is None else now_ts)



def observe_accepted_chain(decision, handoff, params, *, now_ts, provider, buffer_mode,
                           market_evidence=None, publish_study=True):
    """One prospectively frozen quote experiment per accepted V3 opportunity."""
    if (provider != "FINNHUB" or decision.setup.symbol.replace("/", "") != "EURUSD"
        or handoff.accepted_stage != "OPEN_NOW" or not handoff.stage_handoff_ready or _path() is None):
        return
    row = handoff.next_state["per_symbol"][decision.setup.symbol]
    if row.get("physical_calibration_captured_signal_id") == decision.signal_id:
        return
    from core.strategy_v3 import STRATEGY_VERSION, CANONICAL_SPEC
    exported = decision.to_dict()
    frozen = {key: exported[key] for key in ("decision_policy", "history_policy") if key in exported}
    frozen.update(history_policy=HISTORY_POLICY, direction=decision.setup.direction,
        decision_kind=decision.kind,
        signal_id=decision.signal_id, decision_id=decision.decision_id,
        decision_audit_id=decision.decision_audit_id, candle_ts=decision.setup.evaluated_ts,
        **{key: exported[key] for key in ("market_context", "structure", "time", "trade_physics")})
    if market_evidence is not None:
        frozen["indicators"] = {key: getattr(market_evidence, key, None) for key in
            ("atr_m5", "activity_ratio", "activity_gate_ok", "ema_fast", "ema_slow", "rsi")}
    capture([{
        "policy": "PHYSICAL_ONLY_V3", "direction": decision.setup.direction,
        "opportunity_signal_id": decision.signal_id,
        "created_ts": now_ts, "open_ts": now_ts,
        "pre_ts": row["physical_pre_ts"], "confirm_ts": row["physical_confirm_ts"],
        "confirm_model_seconds": row["physical_confirm_model_seconds"],
        "model_seconds": decision.time.model_expiry * 60,
        "adjusted_seconds": decision.time.t_needed_adjusted * 60,
        "buffer_distance": decision.market_context.buffer_distance,
        "open_decision_id": decision.decision_id, "open_decision_audit_id": decision.decision_audit_id,
        "decision_snapshot": frozen,
        "confirm_execution_status": row.get("physical_confirm_execution_status"),
        "study_duration_policy": row.get(second_duration.POLICY_FIELD),
        "confirmed_study_plan": deepcopy(row.get(second_duration.PLAN_FIELD)),
        "publish_study": (publish_study
            and row.get("physical_confirm_execution_status") == "UNAVAILABLE"
            and row.get("physical_confirm_execution") is None),
    }], params=params, buffer_mode=buffer_mode, strategy_version=STRATEGY_VERSION,
       canonical_spec=CANONICAL_SPEC, now_ts=now_ts)
    row["physical_calibration_captured_signal_id"] = decision.signal_id
    return True
