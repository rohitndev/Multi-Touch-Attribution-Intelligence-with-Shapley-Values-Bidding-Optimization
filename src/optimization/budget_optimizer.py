"""ROI-maximising budget allocation via SciPy constrained optimisation.

Each channel's revenue response to spend is modelled with a concave
power curve that captures diminishing returns:

    revenue_i(s_i) = k_i * s_i ** gamma          (0 < gamma < 1)

The coefficient ``k_i`` is calibrated from the **composite attribution share**
so that channels which the Shapley/Markov engine found to be genuinely
incremental receive a steeper response curve. We then solve

    maximise   sum_i revenue_i(s_i)
    subject to sum_i s_i = total_budget
               min_share * B <= s_i <= max_share * B

with sequential least-squares programming (SLSQP). The result is the
revenue-optimal reallocation the Attribution Advisor agent acts on.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass
class OptimizationResult:
    """Outcome of a budget-allocation optimisation."""

    allocation: pd.DataFrame          # per-channel current vs optimised spend
    current_revenue: float
    optimized_revenue: float
    total_budget: float

    @property
    def revenue_uplift(self) -> float:
        return self.optimized_revenue - self.current_revenue

    @property
    def uplift_pct(self) -> float:
        if self.current_revenue <= 0:
            return 0.0
        return self.revenue_uplift / self.current_revenue


def _calibrate_coefficients(
    shares: np.ndarray,
    current_spend: np.ndarray,
    gamma: float,
    target_revenue: float,
) -> np.ndarray:
    """Solve k_i so the response curves reproduce a realistic revenue surface.

    Each channel's revenue at its current spend is anchored to its share of a
    target total revenue (``R_i = share_i * target_revenue``), giving
    ``k_i = R_i / current_spend_i ** gamma``. The concave exponent ``gamma``
    then makes reallocating budget toward high-share channels increase total
    revenue with diminishing returns.
    """
    attributed = shares / shares.sum() * target_revenue
    safe_spend = np.where(current_spend <= 0, 1.0, current_spend)
    return attributed / np.power(safe_spend, gamma)


def optimize_budget(
    attribution: pd.DataFrame,
    total_budget: float,
    current_spend: dict[str, float] | None = None,
    min_share: float = 0.02,
    max_share: float = 0.40,
    gamma: float = 0.65,
    baseline_roas: float = 2.8,
) -> OptimizationResult:
    """Optimise channel budget allocation.

    Parameters
    ----------
    attribution:
        Composite attribution table indexed by channel (must contain a
        ``composite_share`` column).
    total_budget:
        Total spend to allocate across channels.
    current_spend:
        Optional mapping of channel -> current spend. Defaults to an even
        split, which represents the naive "spread it evenly" baseline.
    """
    channels = list(attribution.index)
    n = len(channels)
    shares = attribution["composite_share"].to_numpy(dtype=float)

    if current_spend is None:
        current = np.full(n, total_budget / n)
    else:
        current = np.array([current_spend.get(c, total_budget / n) for c in channels])
        current = current / current.sum() * total_budget  # normalise to budget

    target_revenue = baseline_roas * total_budget
    k = _calibrate_coefficients(shares, current, gamma, target_revenue)

    def total_revenue(spend: np.ndarray) -> float:
        return float(np.sum(k * np.power(np.clip(spend, 0, None), gamma)))

    # Minimise the negative revenue (SLSQP minimises).
    def neg_revenue(spend: np.ndarray) -> float:
        return -total_revenue(spend)

    constraints = [{"type": "eq", "fun": lambda s: np.sum(s) - total_budget}]
    bounds = [(min_share * total_budget, max_share * total_budget)] * n

    result = minimize(
        neg_revenue,
        x0=current,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-9},
    )

    optimized = np.clip(result.x, 0, None)
    optimized = optimized / optimized.sum() * total_budget  # enforce budget exactly

    cur_rev = total_revenue(current)
    opt_rev = total_revenue(optimized)

    alloc = pd.DataFrame(
        {
            "composite_share": shares,
            "current_spend": current,
            "optimized_spend": optimized,
            "delta_spend": optimized - current,
            "delta_pct": np.where(current > 0, (optimized - current) / current, 0.0),
        },
        index=channels,
    )
    alloc.index.name = "channel"
    alloc = alloc.sort_values("optimized_spend", ascending=False)

    return OptimizationResult(
        allocation=alloc,
        current_revenue=cur_rev,
        optimized_revenue=opt_rev,
        total_budget=total_budget,
    )
