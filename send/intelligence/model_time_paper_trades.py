"""Prospective paper outcomes at the canonical, market-derived Model Time.

Pure ledger operations: no broker, execution-calibration artifact, publisher,
feed requests or parameter writes. The caller atomically persists this ledger.
This horizon is a simulation hypothesis, never calibrated Execution Time.
"""

from __future__ import annotations

from collections import Counter
import math

from core.decision_object import DecisionObject
from core.v2_fsm_orchestrator import PersistentFSMResult
from intelligence import shadow_model_time_research as observations


PROTOCOL = "CANONICAL_MODEL_TIME_PAPER_V1"
MAX_TRADES = 64
OUTCOMES = ("WIN", "LOSS", "DRAW", "UNKNOWN")


def new_ledger() -> dict:
    return {"protocol": PROTOCOL, "trades": {}, "capacity_rejections": 0}


def _positive(value) -> float:
    if type(value) not in {int, float} or not math.isfinite(value) or value <= 0:
        raise ValueError("INVALID_PAPER_TIME_OR_PRICE")
    return float(value)


def _text(value) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 160


def validate(ledger: dict) -> None:
    if (not isinstance(ledger, dict) or set(ledger) != {"protocol", "trades", "capacity_rejections"}
        or ledger["protocol"] != PROTOCOL or not isinstance(ledger["trades"], dict)
        or len(ledger["trades"]) > MAX_TRADES
        or type(ledger["capacity_rejections"]) is not int or ledger["capacity_rejections"] < 0):
        raise ValueError("INVALID_PAPER_LEDGER")
    for identity, trade in ledger["trades"].items():
        if (not _text(identity) or not isinstance(trade, dict)
            or set(trade) != {"direction", "created_ts", "horizon_seconds", "model_time",
                             "decision_id", "decision_audit_id", "fsm_transition_id",
                             "state", "entry_sample", "expiry_ts", "expiry_sample",
                             "outcome", "outcome_reason", "finalized_ts"}
            or trade["direction"] not in {"BUY", "SELL"}
            or trade["state"] not in {"WAITING_ENTRY", "WAITING_EXPIRY", "FINAL"}
            or any(not _text(trade[key]) for key in ("decision_id", "decision_audit_id", "fsm_transition_id"))):
            raise ValueError("INVALID_PAPER_TRADE")
        created = _positive(trade["created_ts"])
        horizon = _positive(trade["horizon_seconds"])
        model = trade["model_time"]
        if (not isinstance(model, dict) or set(model) != {"t_needed_adjusted", "model_expiry"}
            or horizon > 86400 or horizon != _positive(model["model_expiry"]) * 60
            or _positive(model["t_needed_adjusted"]) > model["model_expiry"] + 1e-9):
            raise ValueError("INVALID_PAPER_HORIZON")
        entry, expiry = trade["entry_sample"], trade["expiry_sample"]
        if entry is not None:
            stamp = _positive(entry.get("observed_ts"))
            if (observations._sample(entry, stamp) != entry
                or not created <= stamp <= created + observations.MAX_ENTRY_DELAY_SECONDS
                or trade["expiry_ts"] != stamp + horizon):
                raise ValueError("INVALID_PAPER_ENTRY")
        elif trade["expiry_ts"] is not None or expiry is not None:
            raise ValueError("PAPER_EXPIRY_WITHOUT_ENTRY")
        if trade["state"] == "WAITING_ENTRY" and entry is not None:
            raise ValueError("INVALID_PAPER_ENTRY_STATE")
        if trade["state"] == "WAITING_EXPIRY" and entry is None:
            raise ValueError("MISSING_PAPER_ENTRY")
        if trade["state"] != "FINAL":
            if any(trade[key] is not None for key in ("outcome", "outcome_reason", "finalized_ts", "expiry_sample")):
                raise ValueError("PREMATURE_PAPER_OUTCOME")
        else:
            if (trade["outcome"] not in OUTCOMES or not _text(trade["outcome_reason"])
                or _positive(trade["finalized_ts"]) < created):
                raise ValueError("INVALID_PAPER_OUTCOME")
            if trade["outcome"] == "UNKNOWN":
                if expiry is not None:
                    raise ValueError("UNKNOWN_PAPER_OUTCOME_HAS_QUOTE")
            else:
                if entry is None or not isinstance(expiry, dict):
                    raise ValueError("MISSING_PAPER_OUTCOME_QUOTES")
                stamp = _positive(expiry.get("observed_ts"))
                if (observations._sample(expiry, stamp) != expiry
                    or not trade["expiry_ts"] <= stamp <= trade["expiry_ts"] + observations.MAX_SAMPLE_DELAY_SECONDS
                    or trade["finalized_ts"] < stamp
                    or observations._classify(trade["direction"], entry["price"], expiry["price"]) != trade["outcome"]):
                    raise ValueError("PAPER_OUTCOME_DISAGREES_WITH_QUOTES")


def register(ledger: dict, decision: DecisionObject, handoff: PersistentFSMResult, *, now_ts: float) -> bool:
    now = _positive(now_ts)
    if (decision.kind != "OPEN_NOW" or decision.setup.symbol.replace("/", "") != "EURUSD"
        or decision.setup.direction not in {"BUY", "SELL"} or decision.compatibility_mode
        or decision.setup.evaluated_ts > now or decision.time.time_state != "READY"
        or decision.reject.hard_blockers or decision.strategic_flags.rejectable
        or not decision.strategic_flags.valid_structure or not decision.strategic_flags.feasible_time
        or not decision.strategic_flags.trade_physics_ready
        or decision.score.trade_physics is None or decision.score.trade_physics.readiness_state != "READY"
        or not handoff.accepted or not handoff.stage_handoff_ready or not handoff.trade_execution_ready
        or handoff.requested_stage != "OPEN_NOW" or handoff.accepted_stage != "OPEN_NOW"
        or handoff.signal_id != decision.signal_id or handoff.decision_id != decision.decision_id
        or handoff.decision_audit_id != decision.decision_audit_id):
        return False
    horizon = _positive(decision.time.model_expiry) * 60
    adjusted = _positive(decision.time.t_needed_adjusted)
    if horizon > 86400 or adjusted > decision.time.model_expiry + 1e-9:
        raise ValueError("INFEASIBLE_PAPER_HORIZON")
    if decision.signal_id in ledger["trades"]:
        return False
    if len(ledger["trades"]) >= MAX_TRADES:
        ledger["capacity_rejections"] += 1
        return False
    ledger["trades"][decision.signal_id] = {
        "direction": decision.setup.direction, "created_ts": now, "horizon_seconds": horizon,
        "model_time": {"t_needed_adjusted": adjusted, "model_expiry": decision.time.model_expiry},
        "decision_id": decision.decision_id, "decision_audit_id": decision.decision_audit_id,
        "fsm_transition_id": handoff.fsm_transition_id, "state": "WAITING_ENTRY",
        "entry_sample": None, "expiry_ts": None, "expiry_sample": None,
        "outcome": None, "outcome_reason": None, "finalized_ts": None,
    }
    return True


def pending(ledger: dict) -> bool:
    return any(trade["state"] != "FINAL" for trade in ledger["trades"].values())


def advance(ledger: dict, sample: dict | None, *, now_ts: float, active_provider: str) -> bool:
    now = _positive(now_ts)
    sample = observations._sample(sample, now)
    changed = False
    for trade in ledger["trades"].values():
        if trade["state"] == "FINAL":
            continue
        outcome = reason = None
        if now < trade["created_ts"]:
            continue
        if active_provider != "FINNHUB":
            outcome, reason = "UNKNOWN", "PROVIDER_CHANGED"
        elif trade["state"] == "WAITING_ENTRY":
            deadline = trade["created_ts"] + observations.MAX_ENTRY_DELAY_SECONDS
            if sample and trade["created_ts"] <= sample["observed_ts"] <= deadline:
                trade.update(state="WAITING_EXPIRY", entry_sample=dict(sample),
                             expiry_ts=sample["observed_ts"] + trade["horizon_seconds"])
                changed = True
            elif now > deadline:
                outcome, reason = "UNKNOWN", "ENTRY_OBSERVATION_MISSING"
        elif trade["state"] == "WAITING_EXPIRY":
            deadline = trade["expiry_ts"] + observations.MAX_SAMPLE_DELAY_SECONDS
            if sample and trade["expiry_ts"] <= sample["observed_ts"] <= deadline:
                trade["expiry_sample"] = dict(sample)
                outcome = observations._classify(trade["direction"], trade["entry_sample"]["price"], sample["price"])
                reason = "OBSERVED_MODEL_TIME_COMPARISON"
            elif now > deadline:
                outcome, reason = "UNKNOWN", "EXPIRY_OBSERVATION_MISSING"
        if outcome is not None:
            trade.update(state="FINAL", outcome=outcome, outcome_reason=reason, finalized_ts=now)
            changed = True
    return changed


def summary(ledger: dict) -> dict:
    trades = list(ledger["trades"].values())
    counts = Counter(trade["outcome"] for trade in trades if trade["state"] == "FINAL")
    decisive = counts["WIN"] + counts["LOSS"]
    return {"protocol": PROTOCOL, "truth_domain": "HYPOTHETICAL_RESEARCH",
            "registered": len(trades), "pending": sum(trade["state"] != "FINAL" for trade in trades),
            "outcomes": {key: counts[key] for key in OUTCOMES}, "decisive_sample": decisive,
            "hypothetical_win_rate_percent": 100 * counts["WIN"] / decisive if decisive else None,
            "horizon_seconds_counts": dict(sorted(Counter(str(t["horizon_seconds"]) for t in trades).items())),
            "horizon_source": "CANONICAL_MODEL_TIME_SIMULATION_ONLY",
            "execution_calibration_required": False, "execution_calibration_proven": False,
            "broker_executed": False, "actual_telegram_publications": 0,
            "capacity_rejections": ledger["capacity_rejections"]}
