"""Fail-closed runtime boundary for governed algorithm parameters.

The canonical loader owns schema/type/range/cross-field validation. This module
adds the runtime compatibility check that the persisted algo parameter bundle
matches the strategy engine version that will actually consume it.
"""

from __future__ import annotations

from typing import Any, Dict

from . import params_loader
from .strategy_v2 import STRATEGY_VERSION


class RuntimeParameterError(ValueError):
    """Raised when governed parameters are unsafe for live strategy evaluation."""


def load_runtime_algo_params(path: str) -> Dict[str, Any]:
    """Load canonical params and prove compatibility with the live strategy.

    No defaults, fallback bundle, or silent repair is permitted here. The caller
    must treat RuntimeParameterError as a blocked strategy-evaluation state.
    """
    try:
        params = params_loader.load_algo_params(path)
    except (params_loader.ParamsValidationError, params_loader.ParamsMigrationError) as exc:
        raise RuntimeParameterError(str(exc)) from exc

    configured_version = params.get("algo_version")
    if configured_version != STRATEGY_VERSION:
        raise RuntimeParameterError(
            "algo_version is incompatible with live strategy runtime: "
            f"configured={configured_version!r}, required={STRATEGY_VERSION!r}"
        )

    return params
