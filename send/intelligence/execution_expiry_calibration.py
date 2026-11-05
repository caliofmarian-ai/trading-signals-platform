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
        for level, context in row["levels"].items():
            if not isinstance(level, str) or not level.isdecimal() or not 0 <= int(level) <= 20:
                raise ValueError("INVALID_CALIBRATION_LEVEL")
            pre, confirm, opened = (_number(context[k]) for k in ("pre_ts", "confirm_ts", "open_ts"))
            _number(context["confirm_model_seconds"])
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
    scope = {"provider": "FINNHUB", "symbol": "EUR/USD", "buffer_mode": buffer_mode,
             "parameter_sha256": algo_params_sha256(params), "strategy_version": strategy_version,
             "canonical_spec": canonical_spec, "model_limits_minutes": params["expiry_limits_minutes"]}
    with storage.with_lock("execution_expiry_calibration", timeout_sec=0.2):
        state = _read(path) or {"protocol": PROTOCOL, "bias_grid": list(BIASES), "scope": scope,
                               "started_ts": now, "records": {}, "capacity_rejections": 0}
        if state["scope"] != scope:
            raise ValueError("CALIBRATION_SCOPE_CHANGED")
        for item in entries:
            # No backfilled PRE/CONFIRM evidence for chains begun before this release.
            if item.get("confirm_model_seconds") is None:
                continue
            row = {key: item[key] for key in ("direction", "created_ts", "model_seconds", "adjusted_seconds")}
            identity = _digest({**row, "scope": scope})
            context = {key: item[key] for key in ("pre_ts", "confirm_ts", "open_ts", "confirm_model_seconds")}
            level = str(item["level"])
            if identity in state["records"]:
                prior = state["records"][identity]["levels"].get(level)
                if prior is not None and prior != context:
                    raise ValueError("CALIBRATION_CHAIN_REWRITE")
                state["records"][identity]["levels"][level] = context
                continue
            if len(state["records"]) >= MAX_RECORDS:
                state["capacity_rejections"] += 1
                continue
            row.update(levels={level: context}, state="WAITING_ENTRY", entry=None,
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
            changed = False
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
    return {"decisive": decisive, "wins": counter["WIN"], "losses": counter["LOSS"],
            "unknown": counter["UNKNOWN"], "draws": counter["DRAW"],
            "infeasible": counter["INFEASIBLE"],
            "unknown_fraction": counter["UNKNOWN"] / eligible if eligible else None,
            "win_rate": counter["WIN"] / decisive if decisive else None,
            "wilson_95_lower": _wilson(counter["WIN"], decisive)}


def _quantiles(values):
    if not values:
        return {"sample": 0, "p50": None, "p95": None, "min": None, "max": None}
    values = sorted(values)
    return {"sample":len(values), "p50":values[math.ceil(.5*len(values))-1],
            "p95":values[math.ceil(.95*len(values))-1], "min":values[0], "max":values[-1]}


def _compact(report):
    return {**report, "levels":[{k:v for k,v in row.items() if k not in {"train_candidates", "proposal_only"}}
                                for row in report["levels"]]}


def analyze(state, *, now_ts):
    report = {"protocol": PROTOCOL, "truth_domain": "HYPOTHETICAL_RESEARCH", "observed_at": now_ts,
              "status": "WAITING_FIRST_COMPLETE_CHAIN", "bias_grid": list(BIASES),
              "unique_entry_experiments": 0, "pending": 0, "levels": [],
              "observed_entry_quotes":0, "finalized_entry_experiments":0,
              "entry_quote_delay_seconds":_quantiles([]), "paired_expiry_observations":[],
              "readiness_policy": {"minimum_train_decisive": MIN_TRAIN, "minimum_validation_decisive": MIN_VALIDATION,
                                   "fixed_train_entries":TRAIN_ENTRIES, "fixed_holdout_entries":HOLDOUT_ENTRIES,
                                   "target_win_rate": TARGET_WIN_RATE,
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
        independent, next_entry = [], 0.0
        # Partition every admitted entry before looking at its eventual outcome.
        # Use the longest declared horizon, even when its quote was missed.
        for row in rows:
            if row["created_ts"] >= next_entry:
                independent.append(row)
                next_entry = row["created_ts"] + quotes.MAX_ENTRY_DELAY_SECONDS + row["model_seconds"] + quotes.MAX_SAMPLE_DELAY_SECONDS
        train, holdout = independent[:TRAIN_ENTRIES], independent[TRAIN_ENTRIES:TRAIN_ENTRIES+HOLDOUT_ENTRIES]
        train_counts = [_counts(train,i) for i in range(len(BIASES))]
        training_complete = len(train) == TRAIN_ENTRIES and all(r["state"] == "FINAL" for r in train)
        eligible = [i for i,c in enumerate(train_counts) if training_complete and c["decisive"] >= MIN_TRAIN and c["unknown_fraction"] <= MAX_UNKNOWN_FRACTION]
        selected = max(eligible,key=lambda i:(train_counts[i]["wilson_95_lower"],-BIASES[i])) if eligible else None
        validation = _counts(holdout,selected) if selected is not None else None
        if validation is not None:
            validation["familywise_95_lower"] = _wilson(validation["wins"],validation["decisive"],z=VALIDATION_Z)
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
                      and validation["familywise_95_lower"] >= TARGET_WIN_RATE and violations == 0)
        if not training_complete:
            status = "COLLECTING_TRAINING"
        elif selected is None:
            status = "TRAINING_DATA_QUALITY_FAILED"
        elif len(holdout) < HOLDOUT_ENTRIES or not all(r["state"] == "FINAL" for r in holdout):
            status = "COLLECTING_HOLDOUT"
        elif validation["decisive"] < MIN_VALIDATION:
            status = "HOLDOUT_SAMPLE_INADEQUATE"
        elif validation["unknown_fraction"] > MAX_UNKNOWN_FRACTION:
            status = "HOLDOUT_DATA_QUALITY_FAILED"
        elif violations:
            status = "CONFIRM_INTERVAL_VALIDATION_FAILED"
        elif passed:
            status = "READY_FOR_REVIEW"
        else:
            status = "EFFICACY_TARGET_NOT_MET"
        row_summary = {"level":level, "unique_entries":len(rows), "nonoverlapping_entries":len(independent),
                       "train_entries":len(train), "holdout_entries":len(holdout),
                       "train_candidates":[{"pressure_bias":b,**c} for b,c in zip(BIASES,train_counts)],
                       "training_selected_bias":BIASES[selected] if selected is not None else None,
                       "holdout_confirm_interval_violations":violations,
                       "untouched_holdout":validation, "status":status,
                       "timing_seconds":{name:_quantiles([r["levels"][str(level)][after]-r["levels"][str(level)][before] for r in rows])
                           for name,before,after in (("pre_to_confirm","pre_ts","confirm_ts"),
                                                    ("confirm_to_open","confirm_ts","open_ts"),
                                                    ("pre_to_open","pre_ts","open_ts"))}}
        if passed:
            row_summary["proposal_only"] = {"pressure_bias":BIASES[selected],
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
