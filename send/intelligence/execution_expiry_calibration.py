"""Prospective, paired expiry calibration; never a production execution authority.

Every candidate is declared before its entry quote. Real quotes, exact horizons,
unknown observations and independent chronological holdouts remain separate.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import time
from pathlib import Path
from statistics import NormalDist

from core import storage
from intelligence import shadow_model_time_research as quotes
from intelligence import buffer_expiry_evidence as buffer_evidence

PROTOCOL = "PROSPECTIVE_EXECUTION_EXPIRY_CALIBRATION_V1"
BIASES = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25)
MAX_RECORDS = 512
MAX_BYTES = 4 * 1024 * 1024
MIN_TRAIN = 30
MIN_VALIDATION = 30
TRAIN_ENTRIES = 60
HOLDOUT_ENTRIES = 60
TARGET_WIN_RATE = 0.80
MAX_UNKNOWN_FRACTION = 0.10
VALIDATION_Z = NormalDist().inv_cdf(1 - 0.05 / (2 * 21))
REPORT_SECONDS = 60
_last_report: dict[str, int] = {}


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
    path = Path(storage.root_path("analytics", "execution_expiry_calibration", "state.json"))
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
    validate(state)
    if len(json.dumps(state, allow_nan=False).encode()) > MAX_BYTES:
        raise ValueError("CALIBRATION_SIZE_LIMIT")
    storage.save_json_atomic(str(path), state)


def validate(state):
    if (not isinstance(state, dict) or state.get("protocol") != PROTOCOL
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
        or scope.get("buffer_mode") not in {"SMALL", "MEDIUM", "LARGE"}
        or not isinstance(scope.get("parameter_sha256"), str) or len(scope["parameter_sha256"]) != 64):
        raise ValueError("INVALID_CALIBRATION_SCOPE")
    for identity, row in state["records"].items():
        if (not isinstance(identity, str) or len(identity) != 64 or row.get("direction") not in {"BUY", "SELL"}
            or row.get("state") not in {"WAITING_ENTRY", "OBSERVING", "FINAL"}
            or not isinstance(row.get("levels"), dict) or not row["levels"]):
            raise ValueError("INVALID_CALIBRATION_RECORD")
        created, model, adjusted = (_number(row[k]) for k in ("created_ts", "model_seconds", "adjusted_seconds"))
        if adjusted > model or model > 86400:
            raise ValueError("INFEASIBLE_CALIBRATION_MODEL")
        if identity != _digest({**{k:row[k] for k in ("direction","created_ts","model_seconds","adjusted_seconds")}, "scope":scope}):
            raise ValueError("CALIBRATION_SOURCE_IDENTITY_CHANGED")
        if "buffer_snapshot" in row:
            if "buffer_objective" not in state:
                raise ValueError("BUFFER_OBJECTIVE_MISSING")
            frozen = row["buffer_snapshot"]
            buffer_evidence.validate_snapshot(frozen, scope["parameter_sha256"])
            if row.get("buffer_snapshot_sha256") != _digest(frozen):
                raise ValueError("BUFFER_SNAPSHOT_CHANGED")
        for level, context in row["levels"].items():
            if not isinstance(level, str) or not level.isdecimal() or not 0 <= int(level) <= 20:
                raise ValueError("INVALID_CALIBRATION_LEVEL")
            pre, confirm, opened = (_number(context[k]) for k in ("pre_ts", "confirm_ts", "open_ts"))
            _number(context["confirm_model_seconds"])
            for key in ("open_decision_id", "open_decision_audit_id"):
                if key in context and (not isinstance(context[key], str) or not context[key].strip()):
                    raise ValueError("INVALID_BUFFER_DECISION_SOURCE")
            if not pre <= confirm <= opened == created or opened - pre < 30:
                raise ValueError("INVALID_CALIBRATION_STAGE_ORDER")
        entry = row["entry"]
        if entry is not None:
            stamp = _number(entry.get("observed_ts"))
            if quotes._sample(entry, stamp) != entry or not created <= stamp <= created + quotes.MAX_ENTRY_DELAY_SECONDS:
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
                if (entry is None or quotes._sample(expiry, stamp) != expiry
                    or not entry["observed_ts"] + horizon <= stamp <= entry["observed_ts"] + horizon + quotes.MAX_SAMPLE_DELAY_SECONDS
                    or quotes._classify(row["direction"], entry["price"], expiry["price"]) != outcome):
                    raise ValueError("INVALID_CALIBRATION_LABEL")
            elif expiry is not None:
                raise ValueError("UNOBSERVED_CALIBRATION_LABEL")
        if (row["state"] == "FINAL") != all(c["outcome"] != "PENDING" for c in candidates):
            raise ValueError("INVALID_CALIBRATION_FINAL_STATE")


def capture(entries, *, params, buffer_mode, strategy_version, canonical_spec, now_ts):
    """Capture only first accepted research chains; identical entries share one quote experiment."""
    path = _path()
    if path is None or not entries:
        return
    now = _number(now_ts)
    from core.runtime_execution_calibration import algo_params_sha256
    from intelligence.signal_severity_scale import score_thresholds
    scope = {"provider": "FINNHUB", "symbol": "EUR/USD", "buffer_mode": buffer_mode,
             "parameter_sha256": algo_params_sha256(params), "strategy_version": strategy_version,
             "canonical_spec": canonical_spec, "model_limits_minutes": params["expiry_limits_minutes"]}
    with storage.with_lock("execution_expiry_calibration", timeout_sec=0.2):
        state = _read(path) or {"protocol": PROTOCOL, "bias_grid": list(BIASES), "scope": scope,
                               "started_ts": now, "records": {}, "capacity_rejections": 0}
        if state["scope"] != scope:
            raise ValueError("CALIBRATION_SCOPE_CHANGED")
        _install_buffer_policy(state, now)
        variants = {str(level):{"score_thresholds":score_thresholds(params,level),
                               "parameter_sha256":algo_params_sha256({**params,"score_thresholds":score_thresholds(params,level)})}
                    for level in range(21)}
        # Deterministic source metadata may be enriched without changing old
        # observations or their source identity. Never reuse a level-0 fit as a
        # calibration approved for unchanged level-14 production parameters.
        if state.get("variant_scopes",variants) != variants:
            raise ValueError("CALIBRATION_VARIANT_SCOPE_CHANGED")
        state["variant_scopes"] = variants
        for item in entries:
            # No backfilled PRE/CONFIRM evidence for chains begun before this release.
            if item.get("confirm_model_seconds") is None:
                continue
            row = {key: item[key] for key in ("direction", "created_ts", "model_seconds", "adjusted_seconds")}
            identity = _digest({**row, "scope": scope})
            context = {key: item[key] for key in ("pre_ts", "confirm_ts", "open_ts", "confirm_model_seconds")}
            for key in ("open_decision_id", "open_decision_audit_id"):
                if key in item:
                    if not isinstance(item[key], str) or not item[key].strip():
                        raise ValueError("INVALID_BUFFER_DECISION_SOURCE")
                    context[key] = item[key]
            frozen = buffer_evidence.snapshot(item.get("buffer_distance"), scope["parameter_sha256"])
            level = str(item["level"])
            if identity in state["records"]:
                # An old entry is never upgraded using today's ATR/buffer.
                existing = state["records"][identity]
                if "buffer_snapshot" in existing and existing["buffer_snapshot"] != frozen:
                    raise ValueError("BUFFER_SNAPSHOT_REWRITE")
                if "buffer_snapshot" not in existing:
                    context = {key: item[key] for key in ("pre_ts", "confirm_ts", "open_ts", "confirm_model_seconds")}
                prior = state["records"][identity]["levels"].get(level)
                if prior is not None and prior != context:
                    raise ValueError("CALIBRATION_CHAIN_REWRITE")
                state["records"][identity]["levels"][level] = context
                continue
            if len(state["records"]) >= MAX_RECORDS:
                state["capacity_rejections"] += 1
                continue
            row.update(levels={level: context}, state="WAITING_ENTRY", entry=None,
                       buffer_snapshot=frozen, buffer_snapshot_sha256=_digest(frozen),
                       candidates=[{"bias": bias, "horizon_seconds": row["model_seconds"] * (1 - bias),
                                    "outcome": "INFEASIBLE" if row["model_seconds"] * (1 - bias) < row["adjusted_seconds"] else "PENDING",
                                    "reason": None, "quote": None} for bias in BIASES])
            state["records"][identity] = row
        _save(path, state)


def advance(*, now_ts, active_provider, price_loader):
    path = _path()
    if path is None:
        return None
    now = _number(now_ts)
    with storage.with_lock("execution_expiry_calibration", timeout_sec=0.2):
        state = _read(path)
        if state is None:
            state = None
        else:
            pending = [r for r in state["records"].values() if r["state"] != "FINAL"]
            sample = None
            if pending and active_provider == "FINNHUB":
                try:
                    sample = quotes._sample(price_loader("EUR/USD"), now)
                except Exception:
                    pass
            changed = _install_buffer_policy(state, now)
            for row in pending:
                if now < row["created_ts"]:
                    continue
                reason = "PROVIDER_CHANGED" if active_provider != "FINNHUB" else None
                if row["entry"] is None and reason is None:
                    if sample and row["created_ts"] <= sample["observed_ts"] <= row["created_ts"] + quotes.MAX_ENTRY_DELAY_SECONDS:
                        row.update(entry=dict(sample), state="OBSERVING")
                        changed = True
                    elif now > row["created_ts"] + quotes.MAX_ENTRY_DELAY_SECONDS:
                        reason = "ENTRY_OBSERVATION_MISSING"
                for candidate in row["candidates"]:
                    if candidate["outcome"] != "PENDING":
                        continue
                    if reason:
                        candidate.update(outcome="UNKNOWN", reason=reason)
                        changed = True
                    elif row["entry"] is not None:
                        target = row["entry"]["observed_ts"] + candidate["horizon_seconds"]
                        if sample and target <= sample["observed_ts"] <= target + quotes.MAX_SAMPLE_DELAY_SECONDS:
                            candidate.update(quote=dict(sample), outcome=quotes._classify(row["direction"], row["entry"]["price"], sample["price"]), reason="OBSERVED_PAIRED_EXPIRY")
                            changed = True
                        elif now > target + quotes.MAX_SAMPLE_DELAY_SECONDS:
                            candidate.update(outcome="UNKNOWN", reason="EXPIRY_OBSERVATION_MISSING")
                            changed = True
                if all(c["outcome"] != "PENDING" for c in row["candidates"]):
                    row["state"] = "FINAL"
            if changed:
                _save(path, state)
    slot = int(now // REPORT_SECONDS)
    if _last_report.get(str(path), -1) < slot:
        report = analyze(state, now_ts=now)
        print("TSP_EXECUTION_EXPIRY_CALIBRATION " + json.dumps(_compact(report), sort_keys=True), flush=True)
        _last_report[str(path)] = slot
        return report
    return None


def _wilson(wins, n, *, z=1.959963984540054):
    if n == 0:
        return None
    proportion = wins / n
    return max(0.0, (proportion + z*z/(2*n) - z*math.sqrt(proportion*(1-proportion)/n + z*z/(4*n*n))) / (1 + z*z/n))


def _counts(records, index):
    counter = Counter(row["candidates"][index]["outcome"] for row in records)
    decisive = counter["WIN"] + counter["LOSS"]
    eligible = sum(counter[k] for k in ("WIN", "LOSS", "DRAW", "UNKNOWN"))
    prospective = [r for r in records if "buffer_snapshot" in r
                   and r["candidates"][index]["outcome"] in {"WIN", "LOSS", "DRAW", "UNKNOWN"}]
    measured = [(r, buffer_evidence.measure(r["direction"], r["entry"], r["candidates"][index]["quote"],
                                          r["buffer_snapshot"])) for r in prospective]
    met = sum(m["status"] == "MET" for _,m in measured)
    not_met = sum(m["status"] == "NOT_MET" for _,m in measured)
    unavailable = len(measured) - met - not_met
    known = met + not_met
    known_reasons = {"ENTRY_OBSERVATION_MISSING", "EXPIRY_OBSERVATION_MISSING", "PROVIDER_CHANGED"}
    unknown_reasons = Counter(r["candidates"][index].get("reason")
        if r["candidates"][index].get("reason") in known_reasons else "OTHER"
        for r in records if r["candidates"][index]["outcome"] == "UNKNOWN")
    return {"decisive": decisive, "wins": counter["WIN"], "losses": counter["LOSS"],
            "unknown": counter["UNKNOWN"], "draws": counter["DRAW"],
            "unknown_reasons":dict(unknown_reasons),
            "infeasible": counter["INFEASIBLE"],
            "unknown_fraction": counter["UNKNOWN"] / eligible if eligible else None,
            "win_rate": counter["WIN"] / decisive if decisive else None,
            "wilson_95_lower": _wilson(counter["WIN"], decisive),
            "buffer_met":met, "buffer_not_met":not_met, "buffer_unavailable":unavailable,
            "buffer_sample":known, "buffer_met_rate":met/known if known else None,
            "buffer_unknown_fraction":unavailable/len(measured) if measured else None,
            "buffer_wilson_95_lower":_wilson(met, known),
            "win_buffer_met":sum(r["candidates"][index]["outcome"] == "WIN" and m["status"] == "MET" for r,m in measured),
            "win_buffer_not_met":sum(r["candidates"][index]["outcome"] == "WIN" and m["status"] == "NOT_MET" for r,m in measured),
            "win_buffer_unavailable":counter["WIN"]-sum(r["candidates"][index]["outcome"] == "WIN"
                                                        and m["status"] != "UNAVAILABLE" for r,m in measured),
            "legacy_buffer_unavailable":sum("buffer_snapshot" not in r and r["candidates"][index]["outcome"]
                                           in {"WIN", "LOSS", "DRAW", "UNKNOWN"} for r in records),
            "buffer_coverage":_quantiles([m["buffer_coverage"] for _,m in measured if m["buffer_coverage"] is not None])}


def _quantiles(values):
    if not values:
        return {"sample": 0, "p50": None, "p95": None, "min": None, "max": None}
    values = sorted(values)
    return {"sample":len(values), "p50":values[math.ceil(.5*len(values))-1],
            "p95":values[math.ceil(.95*len(values))-1], "min":values[0], "max":values[-1]}


def _compact(report):
    return {**report, "levels":[{k:v for k,v in row.items() if k not in {"train_candidates", "proposal_only", "buffer_expiry_observations"}}
                                for row in report["levels"]]}


def analyze(state, *, now_ts):
    report = {"protocol": PROTOCOL, "truth_domain": "HYPOTHETICAL_RESEARCH", "observed_at": now_ts,
              "status": "WAITING_FIRST_COMPLETE_CHAIN", "bias_grid": list(BIASES),
              "unique_entry_experiments": 0, "pending": 0, "levels": [],
              "observed_entry_quotes":0, "finalized_entry_experiments":0,
              "entry_quote_delay_seconds":_quantiles([]), "paired_expiry_observations":[],
              "buffer_objective":_buffer_policy(), "legacy_directional_only_entries":0,
              "prospective_buffer_entries":0, "buffer_collection_started_ts":None,
              "readiness_policy": {"minimum_train_decisive": MIN_TRAIN, "minimum_validation_decisive": MIN_VALIDATION,
                                   "fixed_train_entries":TRAIN_ENTRIES, "fixed_holdout_entries":HOLDOUT_ENTRIES,
                                   "target_win_rate": TARGET_WIN_RATE,
                                   "primary_target":buffer_evidence.CONTRACT,
                                   "minimum_buffer_validation_familywise_95_lower":TARGET_WIN_RATE,
                                   "minimum_validation_familywise_95_lower": TARGET_WIN_RATE,
                                   "multiple_level_correction":"BONFERRONI_21_LEVELS_FIXED_HOLDOUT",
                                   "maximum_unknown_fraction": MAX_UNKNOWN_FRACTION,
                                   "split": "CHRONOLOGICAL_NONOVERLAPPING_TRAIN_THEN_UNTOUCHED_HOLDOUT"},
              "execution_calibration_proven": False, "automatic_activation_allowed": False,
              "production_parameters_changed": False, "broker_executed": False,
              "actual_telegram_publications": 0}
    if state is None:
        return report
    validate(state)
    records = list(state["records"].values())
    report.update(scope=state["scope"], unique_entry_experiments=len(records),
                  pending=sum(r["state"] != "FINAL" for r in records),
                  capacity_rejections=state["capacity_rejections"],
                  status="CAPACITY_REACHED" if len(records) >= MAX_RECORDS else "COLLECTING")
    report["observed_entry_quotes"] = sum(r["entry"] is not None for r in records)
    report["finalized_entry_experiments"] = sum(r["state"] == "FINAL" for r in records)
    report["legacy_directional_only_entries"] = sum("buffer_snapshot" not in r for r in records)
    report["prospective_buffer_entries"] = sum("buffer_snapshot" in r for r in records)
    report["buffer_collection_started_ts"] = state.get("buffer_collection_started_ts")
    report["entry_quote_delay_seconds"] = _quantiles([
        r["entry"]["observed_ts"]-r["created_ts"] for r in records if r["entry"] is not None])
    report["paired_expiry_observations"] = [{"pressure_bias":bias, **_counts(records,index),
        "pending":sum(r["candidates"][index]["outcome"] == "PENDING" for r in records),
        "expiry_quote_delay_seconds":_quantiles([
            r["candidates"][index]["quote"]["observed_ts"]-r["entry"]["observed_ts"]-r["candidates"][index]["horizon_seconds"]
            for r in records if r["candidates"][index]["quote"] is not None])}
        for index,bias in enumerate(BIASES)]
    for level in range(21):
        rows = sorted((r for r in records if str(level) in r["levels"]), key=lambda r:r["created_ts"])
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
        eligible = [i for i,c in enumerate(train_counts) if training_complete and c["decisive"] >= MIN_TRAIN
                    and c["unknown_fraction"] <= MAX_UNKNOWN_FRACTION and c["buffer_sample"] >= MIN_TRAIN
                    and c["buffer_unknown_fraction"] <= MAX_UNKNOWN_FRACTION]
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
                        [abs(r["levels"][str(level)]["confirm_model_seconds"] -
                             r["model_seconds"] * (1 - selected_bias))/60 for r in train])
            minimum, maximum = bounds["min"]*(1-selected_bias), bounds["max"]
            violations = sum(not max(minimum,r["levels"][str(level)]["confirm_model_seconds"]/60-delta)
                             <= r["model_seconds"]*(1-selected_bias)/60
                             <= min(maximum,r["levels"][str(level)]["confirm_model_seconds"]/60+delta)
                             for r in holdout)
        passed = bool(len(holdout) == HOLDOUT_ENTRIES and all(r["state"] == "FINAL" for r in holdout)
                      and validation and validation["decisive"] >= MIN_VALIDATION
                      and validation["unknown_fraction"] <= MAX_UNKNOWN_FRACTION
                      and validation["familywise_95_lower"] >= TARGET_WIN_RATE
                      and validation["buffer_sample"] >= MIN_VALIDATION
                      and validation["buffer_unknown_fraction"] <= MAX_UNKNOWN_FRACTION
                      and validation["buffer_familywise_95_lower"] >= TARGET_WIN_RATE and violations == 0)
        variant_scope = state.get("variant_scopes",{}).get(str(level))
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
        row_summary = {"level":level, "unique_entries":len(rows), "prospective_buffer_entries":len(buffer_rows),
                       "legacy_directional_only_entries":len(rows)-len(buffer_rows), "nonoverlapping_entries":len(independent),
                       "train_entries":len(train), "holdout_entries":len(holdout),
                       "train_candidates":[{"pressure_bias":b,**c} for b,c in zip(BIASES,train_counts)],
                       "buffer_expiry_observations":[{"pressure_bias":b,**_counts(rows,i)} for i,b in enumerate(BIASES)],
                       "training_selected_bias":BIASES[selected] if selected is not None else None,
                       "holdout_confirm_interval_violations":violations,
                       "untouched_holdout":validation, "status":status,
                       "timing_seconds":{name:_quantiles([r["levels"][str(level)][after]-r["levels"][str(level)][before] for r in rows])
                           for name,before,after in (("pre_to_confirm","pre_ts","confirm_ts"),
                                                    ("confirm_to_open","confirm_ts","open_ts"),
                                                    ("pre_to_open","pre_ts","open_ts"))}}
        if passed:
            row_summary["proposal_only"] = {"pressure_bias":BIASES[selected],
                "objective_contract":buffer_evidence.CONTRACT, "validated_buffer_target_rate":TARGET_WIN_RATE,
                "validated_level":level, "validated_parameter_sha256":variant_scope["parameter_sha256"],
                "validated_score_thresholds":variant_scope["score_thresholds"],
                "confirm_delta_minutes":delta,
                "minimum_expiry_minutes":bounds["min"]*(1-BIASES[selected]),
                "maximum_expiry_minutes":bounds["max"], "source_evidence_sha256":_digest(state)}
        report["levels"].append(row_summary)
    report["ready_levels"] = [r["level"] for r in report["levels"] if r["status"] == "READY_FOR_REVIEW"]
    if report["ready_levels"]:
        report["status"] = "PROPOSALS_REQUIRE_REVIEW"
    return report


def summary(*, now_ts=None):
    path = _path()
    with storage.with_lock("execution_expiry_calibration", timeout_sec=0.2):
        state = _read(path) if path else None
    return analyze(state, now_ts=time.time() if now_ts is None else now_ts)
