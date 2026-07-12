# /opt/binarybot/experiments/parameter_search.py
# BinaryBot — Parameter Search (research only)

from __future__ import annotations

import itertools
import time
from typing import Dict, Any, List

from experiments.experiment_runner import run_experiment


def _now_ts() -> int:
    return int(time.time())


def generate_param_grid(param_space: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """
    Generates all combinations of parameters from a param space.

    Example:
    param_space = {
        "rsi_period": [7, 14, 21],
        "threshold": [0.6, 0.7]
    }
    """
    keys = list(param_space.keys())
    values = list(param_space.values())

    combos = []
    for combination in itertools.product(*values):
        combos.append(dict(zip(keys, combination)))

    return combos


def run_parameter_search(
    experiment_name: str,
    param_space: Dict[str, List[Any]],
    base_config: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Runs parameter grid search experiments.

    Returns list of experiment summaries.
    """
    base_config = base_config or {}
    grid = generate_param_grid(param_space)

    results: List[Dict[str, Any]] = []

    for params in grid:
        config = dict(base_config)
        config["params"] = params
        config["search_ts"] = _now_ts()

        result = run_experiment(
            experiment_name=experiment_name,
            config=config,
        )

        results.append(result)

    return results