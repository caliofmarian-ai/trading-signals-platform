# /opt/binarybot/validation/statistical_proof.py
# BinaryBot — Statistical Validation Utilities

from __future__ import annotations

import math
from typing import List, Dict


def winrate(results: List[int]) -> float:
    """
    results: list of 1 (WIN) / 0 (LOSE)
    """
    if not results:
        return 0.0
    return sum(results) / len(results)


def expectancy(results: List[int], payout: float = 0.8) -> float:
    """
    Binary options expectancy model.

    WIN  -> +payout
    LOSE -> -1
    """
    if not results:
        return 0.0

    wins = sum(results)
    losses = len(results) - wins

    profit = wins * payout
    loss = losses * 1.0

    return (profit - loss) / len(results)


def sharpe_ratio(returns: List[float]) -> float:
    """
    Simplified Sharpe ratio.
    """
    if not returns:
        return 0.0

    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = math.sqrt(variance)

    if std == 0:
        return 0.0

    return mean / std


def compute_summary(results: List[int], payout: float = 0.8) -> Dict[str, float]:
    """
    Returns basic trading performance metrics.
    """
    wr = winrate(results)
    exp = expectancy(results, payout)

    returns = []
    for r in results:
        if r == 1:
            returns.append(payout)
        else:
            returns.append(-1.0)

    sr = sharpe_ratio(returns)

    return {
        "trades": len(results),
        "winrate": wr,
        "expectancy": exp,
        "sharpe": sr,
    }