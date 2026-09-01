"""Canonical trader-facing expiry derivation in shadow/live-safe form.

Model Time is internal strategy evidence. Trader-facing expiry may be produced
only by this execution layer and only from an explicit, governed calibration.
No caller may invent an expiry from ``model_expiry`` by copying or rounding it.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import os
from typing import Optional

from .decision_object import DecisionObject
from .fsm_decision_adapter import FSMInterpretation


SCHEMA_VERSION = "1.1.0"


class ExecutionModelError(ValueError):
    """Raised when synchronized evidence or calibration is invalid."""


@dataclass(frozen=True)
class ExecutionCalibration:
    confirm_delta_minutes: float
    pressure_bias: float
    minimum_expiry_minutes: float
    maximum_expiry_minutes: float
    source: str

    def __post_init__(self) -> None:
        values = {
            "confirm_delta_minutes": self.confirm_delta_minutes,
            "pressure_bias": self.pressure_bias,
            "minimum_expiry_minutes": self.minimum_expiry_minutes,
            "maximum_expiry_minutes": self.maximum_expiry_minutes,
        }
        for name, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
                raise ExecutionModelError(f"{name} must be a finite number")
        if self.confirm_delta_minutes < 0:
            raise ExecutionModelError("confirm_delta_minutes must be non-negative")
        if not 0 <= self.pressure_bias < 1:
            raise ExecutionModelError("pressure_bias must be between 0 inclusive and 1 exclusive")
        if self.minimum_expiry_minutes <= 0:
            raise ExecutionModelError("minimum_expiry_minutes must be positive")
        if self.maximum_expiry_minutes < self.minimum_expiry_minutes:
            raise ExecutionModelError("maximum_expiry_minutes must be at least the minimum")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ExecutionModelError("calibration source is required")


@dataclass(frozen=True)
class ExecutionTimeResult:
    schema_version: str
    symbol: str
    cycle_id: str
    fsm_outcome: str
    available: bool
    confirm_expiry_min_minutes: Optional[float]
    confirm_expiry_max_minutes: Optional[float]
    open_now_expiry_minutes: Optional[float]
    calibration_source: Optional[str]
    signal_handoff_ready: bool
    explanation: str


def _is_contract(value: object, name: str, fields: tuple[str, ...]) -> bool:
    return type(value).__name__ == name and all(hasattr(value, field) for field in fields)


def _unavailable_for_stage(decision: DecisionObject, stage: str, explanation: str) -> ExecutionTimeResult:
    return ExecutionTimeResult(
        schema_version=SCHEMA_VERSION,
        symbol=decision.setup.symbol,
        cycle_id=decision.setup.cycle_id,
        fsm_outcome=stage,
        available=False,
        confirm_expiry_min_minutes=None,
        confirm_expiry_max_minutes=None,
        open_now_expiry_minutes=None,
        calibration_source=None,
        signal_handoff_ready=False,
        explanation=explanation,
    )


def load_execution_calibration_from_env() -> Optional[ExecutionCalibration]:
    """Load one explicit execution-time calibration from environment variables.

    No numeric defaults are provided. When all variables are absent the result is
    ``None`` and downstream OPEN_NOW must fail closed. A partial calibration is
    an error rather than an invitation to fill missing values implicitly.
    """

    names = {
        "confirm_delta_minutes": "EXECUTION_CONFIRM_DELTA_MINUTES",
        "pressure_bias": "EXECUTION_PRESSURE_BIAS",
        "minimum_expiry_minutes": "EXECUTION_MIN_EXPIRY_MINUTES",
        "maximum_expiry_minutes": "EXECUTION_MAX_EXPIRY_MINUTES",
        "source": "EXECUTION_CALIBRATION_SOURCE",
    }
    raw = {field: os.getenv(env_name, "").strip() for field, env_name in names.items()}
    present = {field for field, value in raw.items() if value}
    if not present:
        return None
    if present != set(names):
        missing = sorted(names[field] for field in set(names) - present)
        raise ExecutionModelError(
            "execution calibration is partial; missing: " + ", ".join(missing)
        )
    try:
        return ExecutionCalibration(
            confirm_delta_minutes=float(raw["confirm_delta_minutes"]),
            pressure_bias=float(raw["pressure_bias"]),
            minimum_expiry_minutes=float(raw["minimum_expiry_minutes"]),
            maximum_expiry_minutes=float(raw["maximum_expiry_minutes"]),
            source=raw["source"],
        )
    except ValueError as exc:
        raise ExecutionModelError("execution calibration values must be numeric") from exc


def derive_execution_time_for_stage(
    decision: DecisionObject,
    stage: str,
    calibration: Optional[ExecutionCalibration] = None,
) -> ExecutionTimeResult:
    """Derive governed execution time for an already accepted lifecycle stage.

    This helper is intentionally stage-oriented so the persistent FSM execution
    gate can use the same mathematics as the strategy's shadow interpretation.
    It never authorizes signal handoff or broker execution.
    """

    if not isinstance(decision, DecisionObject) and not _is_contract(
        decision, "DecisionObject", ("setup", "time")
    ):
        raise TypeError("decision must be a DecisionObject")
    normalized_stage = str(stage or "").strip().upper()
    if normalized_stage not in {"PRE", "CONFIRM", "OPEN_NOW", "NO_SIGNAL", "REJECT", "WAIT"}:
        raise ExecutionModelError(f"unsupported execution stage: {stage!r}")

    if normalized_stage not in {"CONFIRM", "OPEN_NOW"}:
        return _unavailable_for_stage(
            decision,
            normalized_stage,
            "This lifecycle stage does not expose trader-facing expiry.",
        )
    if decision.time.time_state != "READY" or decision.time.model_expiry is None:
        return _unavailable_for_stage(
            decision,
            normalized_stage,
            "Ready Model Time evidence is required for execution expiry.",
        )
    if calibration is None:
        return _unavailable_for_stage(
            decision,
            normalized_stage,
            "Execution calibration is absent; canonical expiry values are not invented.",
        )

    model_expiry = float(decision.time.model_expiry)
    if not isfinite(model_expiry) or model_expiry <= 0:
        raise ExecutionModelError("model_expiry must be finite and positive")

    confirm_min = max(
        calibration.minimum_expiry_minutes,
        model_expiry - calibration.confirm_delta_minutes,
    )
    confirm_max = min(
        calibration.maximum_expiry_minutes,
        model_expiry + calibration.confirm_delta_minutes,
    )
    if confirm_min > confirm_max:
        raise ExecutionModelError("calibration produces an empty CONFIRM expiry interval")

    open_now = None
    if normalized_stage == "OPEN_NOW":
        candidate = model_expiry * (1 - calibration.pressure_bias)
        if not confirm_min <= candidate <= confirm_max:
            raise ExecutionModelError("OPEN_NOW expiry violates the canonical consistency rule")
        open_now = candidate

    return ExecutionTimeResult(
        schema_version=SCHEMA_VERSION,
        symbol=decision.setup.symbol,
        cycle_id=decision.setup.cycle_id,
        fsm_outcome=normalized_stage,
        available=True,
        confirm_expiry_min_minutes=confirm_min,
        confirm_expiry_max_minutes=confirm_max,
        open_now_expiry_minutes=open_now,
        calibration_source=calibration.source,
        signal_handoff_ready=False,
        explanation=(
            "A calibrated exact OPEN_NOW expiry was derived inside the canonical CONFIRM interval."
            if open_now is not None
            else "A calibrated CONFIRM expiry interval was derived from Model Time."
        ),
    )


def derive_execution_time(
    decision: DecisionObject,
    fsm: FSMInterpretation,
    calibration: Optional[ExecutionCalibration] = None,
) -> ExecutionTimeResult:
    """Derive expiry evidence from the strategy's shadow FSM interpretation."""

    if not isinstance(decision, DecisionObject) and not _is_contract(
        decision, "DecisionObject", ("setup", "time")
    ):
        raise TypeError("decision must be a DecisionObject")
    if not isinstance(fsm, FSMInterpretation) and not _is_contract(
        fsm, "FSMInterpretation", ("symbol", "cycle_id", "outcome", "signal_handoff_ready")
    ):
        raise TypeError("fsm must be a FSMInterpretation")
    if decision.setup.symbol != fsm.symbol or decision.setup.cycle_id != fsm.cycle_id:
        raise ExecutionModelError("decision and FSM evidence must describe the same cycle")
    if fsm.signal_handoff_ready:
        raise ExecutionModelError("shadow FSM must not authorize signal handoff")

    return derive_execution_time_for_stage(decision, fsm.outcome, calibration)
