"""Correctness tests for the exact Shapley-value attribution engine."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.attribution.shapley import (
    _characteristic_function,
    _conversion_rate_by_subset,
    shapley_attribution,
)


def test_credit_shares_sum_to_one(journeys, channels):
    res = shapley_attribution(journeys, channels)
    assert np.isclose(res["credit_share"].sum(), 1.0)
    assert (res["credit_share"] >= 0).all()


def test_efficiency_axiom_holds():
    """Shapley values must sum to v(grand coalition) - v(empty set).

    This is the *efficiency* axiom — the defining property of the Shapley
    value and the reason it is 'fair'. We verify it on a tiny hand-built game.
    """
    channels = ["A", "B", "C"]
    # Construct journeys where the grand-coalition worth is well defined.
    rows = [
        {"path": "A", "converted": 0, "revenue": 0.0},
        {"path": "A > B", "converted": 1, "revenue": 10.0},
        {"path": "B > C", "converted": 1, "revenue": 10.0},
        {"path": "A > B > C", "converted": 1, "revenue": 10.0},
        {"path": "C", "converted": 0, "revenue": 0.0},
    ]
    journeys = pd.DataFrame(rows * 20)
    res = shapley_attribution(journeys, channels)

    subset_rates = _conversion_rate_by_subset(journeys, channels)
    v = _characteristic_function(subset_rates)
    grand = v(frozenset(range(len(channels))))
    empty = v(frozenset())
    assert np.isclose(res["shapley_value"].sum(), grand - empty, atol=1e-9)


def test_irrelevant_channel_gets_low_credit(channels):
    """A channel that never appears should receive ~zero credit."""
    rows = [
        {"path": "Paid Search > Email", "converted": 1, "revenue": 50.0},
        {"path": "Email", "converted": 1, "revenue": 40.0},
        {"path": "Organic Search", "converted": 0, "revenue": 0.0},
    ]
    journeys = pd.DataFrame(rows * 50)
    res = shapley_attribution(journeys, channels)
    # Display never appears in any path -> negligible credit.
    assert res.loc["Display", "credit_share"] < 0.05


def test_exact_not_sampled_is_deterministic(journeys, channels):
    """Exact computation must be reproducible across runs (no RNG)."""
    a = shapley_attribution(journeys, channels)["shapley_value"]
    b = shapley_attribution(journeys, channels)["shapley_value"]
    pd.testing.assert_series_equal(a, b)
