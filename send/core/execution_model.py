"""Canonical trader-facing expiry derivation in shadow mode.

The active canon defines the relationships but does not provide calibrated
values for the CONFIRM tolerance or OPEN_NOW pressure adjustment.  Callers
must therefore supply those values explicitly; this module never invents
defaults and never authorizes a signal or broker action.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional

from .decision_object import DecisionObject
from .fsm_decision_adapter import FSMInterpretation


SCHEMA_VERSION = "1.0.0"


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


def _unavailable(decision: DecisionObject, fsm: FSMInterpretation, explanation: str) -> ExecutionTimeResult:
    return ExecutionTimeResult(
        schema_version=SCHEMA_VERSION,
        symbol=decision.setup.symbol,
        cycle_id=decision.setup.cycle_id,
        fsm_outcome=fsm.outcome,
        available=False,
        confirm_expiry_min_minutes=None,
        confirm_expiry_max_minutes=None,
        open_now_expiry_minutes=None,
        calibration_source=None,
        signal_handoff_ready=False,
        explanation=explanation,
    )


def derive_execution_time(
    decision: DecisionObject,
    fsm: FSMInterpretation,
    calibration: Optional[ExecutionCalibration] = None,
) -> ExecutionTimeResult:
    """Derive expiry evidence without activating downstream execution."""

    if not isinstance(decision, DecisionObject):
        raise TypeError("decision must be a DecisionObject")
    if not isinstance(fsm, FSMInterpretation):
        raise TypeError("fsm must be an FSMInterpretation")
    if decision.setup.symbol != fsm.symbol or decision.setup.cycle_id != fsm.cycle_id:
        raise ExecutionModelError("decision and FSM evidence must describe the same cycle")
    if fsm.signal_handoff_ready:
        raise ExecutionModelError("shadow FSM must not authorize signal handoff")

    if fsm.outcome not in {"CONFIRM", "OPEN_NOW"}:
        return _unavailable(decision, fsm, "This FSM outcome does not expose trader-facing expiry.")
    if decision.time.time_state != "READY" or decision.time.model_expiry is None:
        return _unavailable(decision, fsm, "Ready Model Time evidence is required for execution expiry.")
    if calibration is None:
        return _unavailable(
            decision,
            fsm,
            "Execution calibration is absent; canonical expiry values are not invented.",
        )

    model_expiry = float(decision.time.model_expiry)
    if not isfinite(model_expiry) or model_expiry <= 0:
        raise ExecutionModelError("model_expiry must be finite and positive")

    confirm_min = max(calibration.minimum_expiry_minutes, model_expiry - calibration.confirm_delta_minutes)
    confirm_max = min(calibration.maximum_expiry_minutes, model_expiry + calibration.confirm_delta_minutes)
    if confirm_min > confirm_max:
        raise ExecutionModelError("calibration produces an empty CONFIRM expiry interval")

    open_now = None
    if fsm.outcome == "OPEN_NOW":
        candidate = model_expiry * (1 - calibration.pressure_bias)
        if not confirm_min <= candidate <= confirm_max:
            raise ExecutionModelError("OPEN_NOW expiry violates the canonical consistency rule")
        open_now = candidate

    return ExecutionTimeResult(
        schema_version=SCHEMA_VERSION,
        symbol=decision.setup.symbol,
        cycle_id=decision.setup.cycle_id,
        fsm_outcome=fsm.outcome,
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
