"""Composite attribution score.

Blends the game-theoretic Shapley credit with the Markov removal effect into a
single, robust per-channel score:

    composite_share = w_shapley * shapley_share + w_markov * markov_share

Defaults (70% Shapley / 30% Markov) come from ``config.yaml``. The composite
score is what downstream budget optimisation and the Attribution Advisor agent
consume.
"""
from __future__ import annotations

import pandas as pd

from .markov import markov_attribution
from .shapley import shapley_attribution


def composite_attribution(
    journeys: pd.DataFrame,
    channels: list[str],
    weight_shapley: float = 0.70,
    weight_markov: float = 0.30,
) -> pd.DataFrame:
    """Compute the blended Shapley + Markov attribution table."""
    shap = shapley_attribution(journeys, channels)
    mark = markov_attribution(journeys, channels)

    df = pd.DataFrame(index=channels)
    df.index.name = "channel"
    df["shapley_share"] = shap["credit_share"]
    df["markov_share"] = mark["credit_share"]
    df["composite_share"] = (
        weight_shapley * df["shapley_share"] + weight_markov * df["markov_share"]
    )
    # Re-normalise so composite shares sum to exactly 1.
    df["composite_share"] = df["composite_share"] / df["composite_share"].sum()

    total_conversions = int(journeys["converted"].sum())
    total_revenue = float(journeys.loc[journeys["converted"] == 1, "revenue"].sum())
    df["attributed_conversions"] = df["composite_share"] * total_conversions
    df["attributed_revenue"] = df["composite_share"] * total_revenue

    return df.sort_values("composite_share", ascending=False)
