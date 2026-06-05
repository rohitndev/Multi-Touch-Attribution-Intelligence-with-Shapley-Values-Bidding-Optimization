"""Heuristic baseline attribution models for comparison with Shapley.

These are the rule-based models that dominate the market (and that the
platform is designed to replace): last-click, first-click and linear. They are
computed on the same journey table so the README's "Shapley vs last-click"
comparison is an apples-to-apples contrast.
"""
from __future__ import annotations

import pandas as pd


def _empty_credit(channels: list[str]) -> dict[str, float]:
    return {c: 0.0 for c in channels}


def last_click(journeys: pd.DataFrame, channels: list[str]) -> pd.Series:
    """100% of credit to the final touch before conversion."""
    credit = _empty_credit(channels)
    conv = journeys[journeys["converted"] == 1]
    for path in conv["path"]:
        credit[path.split(" > ")[-1]] += 1.0
    return _to_share(credit, channels)


def first_click(journeys: pd.DataFrame, channels: list[str]) -> pd.Series:
    """100% of credit to the first touch of the journey."""
    credit = _empty_credit(channels)
    conv = journeys[journeys["converted"] == 1]
    for path in conv["path"]:
        credit[path.split(" > ")[0]] += 1.0
    return _to_share(credit, channels)


def linear(journeys: pd.DataFrame, channels: list[str]) -> pd.Series:
    """Equal credit split across every distinct channel in the journey."""
    credit = _empty_credit(channels)
    conv = journeys[journeys["converted"] == 1]
    for path in conv["path"]:
        touched = list(dict.fromkeys(path.split(" > ")))  # distinct, ordered
        w = 1.0 / len(touched)
        for c in touched:
            credit[c] += w
    return _to_share(credit, channels)


def _to_share(credit: dict, channels: list[str]) -> pd.Series:
    total = sum(credit.values())
    if total <= 0:
        return pd.Series({c: 1.0 / len(channels) for c in channels})
    return pd.Series({c: credit[c] / total for c in channels})


def baseline_attributions(
    journeys: pd.DataFrame, channels: list[str]
) -> pd.DataFrame:
    """Return a DataFrame of credit shares for each baseline model."""
    out = pd.DataFrame(
        {
            "last_click": last_click(journeys, channels),
            "first_click": first_click(journeys, channels),
            "linear": linear(journeys, channels),
        }
    )
    out.index.name = "channel"
    return out
