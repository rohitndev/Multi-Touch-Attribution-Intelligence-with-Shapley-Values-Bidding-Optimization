"""Tests for the SciPy budget optimiser and scenario analyser."""
from __future__ import annotations

import numpy as np

from src.attribution import composite_attribution
from src.optimization import compare_scenarios, optimize_budget


def test_allocation_respects_budget_and_bounds(journeys, channels):
    comp = composite_attribution(journeys, channels)
    budget = 1_000_000.0
    res = optimize_budget(comp, total_budget=budget, min_share=0.05, max_share=0.5)
    alloc = res.allocation
    # Budget conserved.
    assert np.isclose(alloc["optimized_spend"].sum(), budget, rtol=1e-6)
    # Bounds respected.
    assert (alloc["optimized_spend"] >= 0.05 * budget - 1).all()
    assert (alloc["optimized_spend"] <= 0.5 * budget + 1).all()


def test_optimised_revenue_not_worse_than_even_split(journeys, channels):
    comp = composite_attribution(journeys, channels)
    res = optimize_budget(comp, total_budget=2_000_000.0)
    # Optimisation should never reduce predicted revenue vs the starting point.
    assert res.optimized_revenue >= res.current_revenue - 1e-6


def test_scenario_ranking(journeys, channels):
    comp = composite_attribution(journeys, channels)
    scen = compare_scenarios(
        comp,
        total_budget=2_000_000.0,
        scenarios={
            "even": {c: 1.0 for c in channels},
            "shapley_weighted": comp["composite_share"].to_dict(),
        },
    )
    assert "predicted_revenue" in scen.columns
    assert scen["predicted_revenue"].is_monotonic_decreasing
