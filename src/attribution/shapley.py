"""Exact Shapley-value attribution (cooperative game theory).

We treat marketing channels as *players* in a cooperative game. The worth of a
coalition ``S`` of channels is the empirical conversion rate of customer
journeys whose set of touched channels is a (non-empty) subset of ``S`` — the
data-driven characteristic function of Shao & Li (2011), the same formulation
Google Analytics 4 uses for its data-driven attribution.

The Shapley value of channel *i* is its average marginal contribution across
every ordering of the players:

    phi_i = sum_{S subset N\\{i}} |S|!(n-|S|-1)!/n! * (v(S u {i}) - v(S))

Because the platform caps journeys at 8 distinct channels, the coalition space
is at most ``2**8 = 256`` subsets, so we compute the value **exactly** (no
Monte-Carlo permutation sampling / approximation).
"""
from __future__ import annotations

from itertools import combinations
from math import factorial

import numpy as np
import pandas as pd


def _conversion_rate_by_subset(
    journeys: pd.DataFrame, channels: list[str]
) -> dict[frozenset, float]:
    """Map each observed channel-set -> conversion rate of those journeys."""
    idx = {c: i for i, c in enumerate(channels)}
    sets: dict[frozenset, list[int]] = {}
    for path, conv in zip(journeys["path"], journeys["converted"]):
        cset = frozenset(idx[c] for c in path.split(" > ") if c in idx)
        if not cset:
            continue
        sets.setdefault(cset, []).append(int(conv))
    return {k: float(np.mean(v)) for k, v in sets.items()}


def _characteristic_function(subset_rates: dict[frozenset, float]):
    """Build v(S): conversion rate among journeys whose channel-set ⊆ S.

    Returns a callable taking a frozenset coalition and returning its worth.
    Memoised over the (at most 2**n) coalitions actually queried.
    """
    cache: dict[frozenset, float] = {}

    def v(coalition: frozenset) -> float:
        if coalition in cache:
            return cache[coalition]
        total = 0.0
        count = 0
        for cset, rate in subset_rates.items():
            if cset <= coalition:  # cset is a subset of the coalition
                total += rate
                count += 1
        worth = total / count if count else 0.0
        cache[coalition] = worth
        return worth

    return v


def shapley_attribution(
    journeys: pd.DataFrame, channels: list[str]
) -> pd.DataFrame:
    """Compute exact Shapley credit per channel.

    Parameters
    ----------
    journeys:
        One row per journey with ``path`` (``"A > B > C"``), ``converted`` and
        ``revenue`` columns.
    channels:
        The full list of channel names (the players ``N``).

    Returns
    -------
    DataFrame indexed by channel with columns ``shapley_value`` (raw marginal
    contribution), ``credit_share`` (normalised to sum to 1) and
    ``attributed_conversions`` / ``attributed_revenue`` (credit_share scaled by
    the dataset totals).
    """
    n = len(channels)
    subset_rates = _conversion_rate_by_subset(journeys, channels)
    v = _characteristic_function(subset_rates)

    players = list(range(n))
    phi = np.zeros(n)

    # Pre-compute the Shapley weights |S|! (n-|S|-1)! / n!.
    weights = {
        s: factorial(s) * factorial(n - s - 1) / factorial(n) for s in range(n)
    }

    for i in players:
        others = [p for p in players if p != i]
        for size in range(len(others) + 1):
            w = weights[size]
            for combo in combinations(others, size):
                S = frozenset(combo)
                marginal = v(S | {i}) - v(S)
                phi[i] += w * marginal

    phi = np.clip(phi, 0.0, None)  # negative contributions floored at zero
    total = phi.sum()
    share = phi / total if total > 0 else np.full(n, 1.0 / n)

    total_conversions = int(journeys["converted"].sum())
    total_revenue = float(journeys.loc[journeys["converted"] == 1, "revenue"].sum())

    out = pd.DataFrame(
        {
            "shapley_value": phi,
            "credit_share": share,
            "attributed_conversions": share * total_conversions,
            "attributed_revenue": share * total_revenue,
        },
        index=channels,
    )
    out.index.name = "channel"
    return out.sort_values("credit_share", ascending=False)
