"""Read an explicitly governed calibration without inventing production values.

The file is trusted deployment configuration. Provenance references are required
attestations; their external contents and empirical quality are not validated by
this parser. There is no approval, parameter-write or auto-promotion endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import re
import stat
from typing import Any, Mapping

from .execution_model import ExecutionCalibration
from .strategy_v2 import STRATEGY_VERSION
from .time_model import SCHEMA_VERSION as TIME_MODEL_SCHEMA_VERSION


SCHEMA_VERSION = "1.0.0"
MAX_ARTIFACT_BYTES = 32 * 1024
_FIELDS = frozenset({
    "schema_version", "calibration_id", "status", "strategy_version",
    "time_model_schema_version", "provider", "symbol", "buffer_mode",
    "algo_params_sha256", "valid_from_ts", "valid_until_ts", "governance", "values",
})
_GOVERNANCE_FIELDS = frozenset({
    "change_id", "approval_ref", "evidence_ref", "rollback_ref", "approved_at_ts",
})
_VALUE_FIELDS = frozenset({
    "confirm_delta_minutes", "pressure_bias", "minimum_expiry_minutes", "maximum_expiry_minutes",
})


@dataclass(frozen=True)
class CalibrationInput:
    status: str
    reason: str
    calibration: ExecutionCalibration | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "available": self.calibration is not None,
            "source": self.calibration.source if self.calibration is not None else None,
            "calibration_efficacy_established": False,
            "broker_executed": False,
        }


def algo_params_sha256(params: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(params), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _exact_fields(value: Any, fields: frozenset[str]) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("invalid fields")
    return value


def _text(value: Any) -> str:
    if (
        not isinstance(value, str) or not value or value.strip() != value
        or len(value) > 2048 or any(ord(char) < 32 for char in value)
    ):
        raise ValueError("invalid text")
    return value


def _timestamp(value: Any) -> int:
    if type(value) is not int or not 0 < value < 2**53:
        raise ValueError("invalid timestamp")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON constant")


def _read_bytes(path: str) -> bytes:
    flags = os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ARTIFACT_BYTES:
            raise ValueError("invalid artifact file")
        raw = handle.read(MAX_ARTIFACT_BYTES + 1)
        if len(raw) > MAX_ARTIFACT_BYTES:
            raise ValueError("artifact too large")
        return raw


def load_runtime_execution_calibration(
    path: str,
    *,
    now_ts: int,
    provider: str,
    symbol: str,
    buffer_mode: str,
    params: Mapping[str, Any],
) -> CalibrationInput:
    """Return a matching, in-window attested artifact, or explicit unavailable.

    Reloading on each evaluation makes expiry, suspension, deletion, replacement
    and parameter changes effective without restart. No prior good value is kept.
    """
    try:
        raw = _read_bytes(path)
    except FileNotFoundError:
        return CalibrationInput("MISSING", "NOT_CONFIGURED")
    except (OSError, ValueError):
        return CalibrationInput("INVALID", "ARTIFACT_UNREADABLE")

    try:
        artifact = _exact_fields(json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant,
        ), _FIELDS)
        governance = _exact_fields(artifact["governance"], _GOVERNANCE_FIELDS)
        values = _exact_fields(artifact["values"], _VALUE_FIELDS)
        for key in _FIELDS - {"values", "governance", "valid_from_ts", "valid_until_ts"}:
            _text(artifact[key])
        for key in _GOVERNANCE_FIELDS - {"approved_at_ts"}:
            _text(governance[key])
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", artifact["calibration_id"]) is None:
            raise ValueError("invalid calibration identity")
        if re.fullmatch(r"[0-9a-f]{64}", artifact["algo_params_sha256"]) is None:
            raise ValueError("invalid parameter hash")
        start = _timestamp(artifact["valid_from_ts"])
        end = _timestamp(artifact["valid_until_ts"])
        approved = _timestamp(governance["approved_at_ts"])
        now = _timestamp(now_ts)
        if not approved <= start < end:
            raise ValueError("invalid approval window")
        # Validate values even when the artifact is inactive, without coercion.
        calibration = ExecutionCalibration(
            **values,
            source=f"exec-cal-v1:{artifact['calibration_id']}:{hashlib.sha256(raw).hexdigest()}",
        )
        if artifact["schema_version"] != SCHEMA_VERSION:
            return CalibrationInput("INVALID", "UNSUPPORTED_SCHEMA")
        if artifact["status"] != "APPROVED":
            return CalibrationInput("UNAPPROVED", "APPROVAL_NOT_ACTIVE")
        if (
            artifact["strategy_version"] != STRATEGY_VERSION
            or params.get("algo_version") != STRATEGY_VERSION
            or artifact["time_model_schema_version"] != TIME_MODEL_SCHEMA_VERSION
            or artifact["provider"] != provider
            or artifact["symbol"] != symbol
            or artifact["buffer_mode"] != buffer_mode
            or artifact["algo_params_sha256"] != algo_params_sha256(params)
        ):
            return CalibrationInput("SCOPE_MISMATCH", "RUNTIME_SCOPE_CHANGED")
        # Model Time clamps its horizon to these governed limits. Checking the
        # affine consistency inequalities at both endpoints covers the interval
        # and prevents an artifact from breaking later strategy evaluations.
        limits = params["expiry_limits_minutes"]
        for horizon in (limits["min"], limits["max"]):
            lower = max(calibration.minimum_expiry_minutes, horizon - calibration.confirm_delta_minutes)
            upper = min(calibration.maximum_expiry_minutes, horizon + calibration.confirm_delta_minutes)
            candidate = horizon * (1 - calibration.pressure_bias)
            if not lower <= candidate <= upper:
                return CalibrationInput("INVALID", "EXPIRY_RANGE_INCONSISTENT")
        if now < start:
            return CalibrationInput("NOT_YET_VALID", "VALIDITY_NOT_STARTED")
        if now >= end:
            return CalibrationInput("EXPIRED", "VALIDITY_ENDED")
        return CalibrationInput("AVAILABLE", "MATCHING_APPROVED_ARTIFACT", calibration)
    except (KeyError, ValueError, TypeError, OverflowError, RecursionError):
        return CalibrationInput("INVALID", "ARTIFACT_VALIDATION_FAILED")
