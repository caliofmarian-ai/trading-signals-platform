"""Pure Owner research score scale; no production parameter control."""

import copy
from core import params_loader

LEVELS = tuple(range(21))
BASELINE_LEVEL = 14


def score_thresholds(params: dict, level: int) -> dict:
    """Monotone translations preserving stage gaps and the exact baseline.

    Level 0 moves PRE to zero; level 14 is the observed production bundle;
    level 20 moves OPEN to 100. The anchor is a research convention, not a
    probability, provider tier, production setting or calibrated optimum.
    """
    if type(level) is not int or level not in LEVELS:
        raise ValueError("severity level must be an integer from 0 to 20")
    params_loader.validate_algo_params(params)
    original = params["score_thresholds"]
    if level == BASELINE_LEVEL:
        return copy.deepcopy(original)
    offset = (-float(original["PRE"]) * (BASELINE_LEVEL - level) / BASELINE_LEVEL
              if level < BASELINE_LEVEL else
              (100.0 - float(original["OPEN"])) * (level - BASELINE_LEVEL) / (20 - BASELINE_LEVEL))
    # The existing parameter contract requires integer score cutoffs. Round
    # the shared offset once, preserving exact integer stage gaps.
    offset = round(offset)
    return {stage: max(0, min(100, original[stage] + offset))
            for stage in ("PRE", "CONFIRM", "OPEN")}

