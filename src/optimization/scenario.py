"""Scenario analysis for the budget reallocation simulator.

Given a base attribution table and the optimiser's revenue model, evaluate a
set of "what-if" channel-mix hypotheses and rank them by predicted revenue.
This is the engine behind the interactive budget-reallocation simulator: a
marketer supplies candidate channel mixes and immediately sees the predicted
ROAS impact based on the Shapley marginal-contribution curves.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .budget_optimizer import _calibrate_coefficients


def compare_scenarios(
    attribution: pd.DataFrame,
    total_budget: float,
    scenarios: dict[str, dict[str, float]],
    gamma: float = 0.65,
    baseline_roas: float = 2.8,
) -> pd.DataFrame:
    """Evaluate predicted revenue / ROAS for each named scenario.

    Parameters
    ----------
    scenarios:
        Mapping of scenario name -> {channel: share}. Shares are normalised
        per scenario, so they need not sum to exactly 1.
    """
    channels = list(attribution.index)
    shares = attribution["composite_share"].to_numpy(dtype=float)
    even = np.full(len(channels), total_budget / len(channels))
    k = _calibrate_coefficients(shares, even, gamma, baseline_roas * total_budget)

    def revenue(spend: np.ndarray) -> float:
        return float(np.sum(k * np.power(np.clip(spend, 0, None), gamma)))

    rows = []
    for name, mix in scenarios.items():
        raw = np.array([mix.get(c, 0.0) for c in channels], dtype=float)
        if raw.sum() <= 0:
            raw = np.full(len(channels), 1.0)
        spend = raw / raw.sum() * total_budget
        rev = revenue(spend)
        rows.append(
            {
                "scenario": name,
                "predicted_revenue": rev,
                "predicted_roas": rev / total_budget if total_budget else 0.0,
            }
        )

    df = pd.DataFrame(rows).set_index("scenario")
    df = df.sort_values("predicted_revenue", ascending=False)
    df["revenue_vs_best_pct"] = (
        df["predicted_revenue"] / df["predicted_revenue"].max() - 1.0
    )
    return df
