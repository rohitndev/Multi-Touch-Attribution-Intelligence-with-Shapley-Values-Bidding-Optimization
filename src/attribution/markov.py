"""Markov-chain attribution via the *removal effect*.

We model the customer journey as an absorbing Markov chain over the states
``{START}`` -> channels -> ``{CONVERSION, NULL}``. Transition probabilities are
estimated directly from the observed ordered paths.

A channel's **removal effect** is the relative drop in overall conversion
probability when that channel is removed from the graph (all its in/out
transitions redirected to the ``NULL`` absorbing state). Channels whose removal
collapses conversions are the ones genuinely carrying the journey; normalising
the removal effects yields each channel's attribution share.

This is a lightweight, exact linear-algebra implementation (no MCMC needed for
estimation); PyMC is listed as an optional dependency for Bayesian credible
intervals on the transition matrix but is not required here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

START = "(start)"
CONV = "(conversion)"
NULL = "(null)"


def build_transition_matrix(
    journeys: pd.DataFrame, channels: list[str]
) -> tuple[np.ndarray, list[str]]:
    """Estimate the transition-probability matrix from observed paths.

    Returns the row-stochastic matrix and the ordered list of state labels.
    States: START, each channel, CONV, NULL.
    """
    states = [START] + list(channels) + [CONV, NULL]
    sidx = {s: i for i, s in enumerate(states)}
    counts = np.zeros((len(states), len(states)))

    for path, conv in zip(journeys["path"], journeys["converted"]):
        seq = [START] + [c for c in path.split(" > ") if c in sidx]
        seq.append(CONV if conv else NULL)
        for a, b in zip(seq[:-1], seq[1:]):
            counts[sidx[a], sidx[b]] += 1

    # Absorbing states transition to themselves.
    counts[sidx[CONV], sidx[CONV]] = 1.0
    counts[sidx[NULL], sidx[NULL]] = 1.0

    row_sums = counts.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    trans = counts / row_sums
    return trans, states


def _conversion_probability(trans: np.ndarray, states: list[str]) -> float:
    """Absorption probability of reaching CONV starting from START.

    Solved exactly via the fundamental matrix of the absorbing chain:
    B = N R, where N = (I - Q)^-1.
    """
    sidx = {s: i for i, s in enumerate(states)}
    absorbing = [sidx[CONV], sidx[NULL]]
    transient = [i for i in range(len(states)) if i not in absorbing]

    Q = trans[np.ix_(transient, transient)]
    R = trans[np.ix_(transient, absorbing)]
    fundamental = np.linalg.inv(np.eye(len(transient)) - Q)
    B = fundamental @ R  # absorption probabilities per transient state

    start_row = transient.index(sidx[START])
    conv_col = absorbing.index(sidx[CONV])
    return float(B[start_row, conv_col])


def markov_attribution(
    journeys: pd.DataFrame, channels: list[str]
) -> pd.DataFrame:
    """Compute removal-effect attribution for every channel."""
    trans, states = build_transition_matrix(journeys, channels)
    sidx = {s: i for i, s in enumerate(states)}
    base_p = _conversion_probability(trans, states)

    removal: dict[str, float] = {}
    for ch in channels:
        ci = sidx[ch]
        t2 = trans.copy()
        # Redirect everything that flowed *into* this channel straight to NULL,
        # and stop the channel from converting (remove it from the graph).
        incoming = t2[:, ci].copy()
        t2[:, ci] = 0.0
        t2[:, sidx[NULL]] += incoming
        t2[ci, :] = 0.0
        t2[ci, sidx[NULL]] = 1.0
        # Re-normalise rows that were touched.
        rs = t2.sum(axis=1, keepdims=True)
        rs[rs == 0] = 1.0
        t2 = t2 / rs

        p_without = _conversion_probability(t2, states)
        removal[ch] = max(0.0, (base_p - p_without) / base_p) if base_p > 0 else 0.0

    re = pd.Series(removal)
    share = re / re.sum() if re.sum() > 0 else pd.Series(
        np.full(len(channels), 1.0 / len(channels)), index=channels
    )

    total_conversions = int(journeys["converted"].sum())
    total_revenue = float(journeys.loc[journeys["converted"] == 1, "revenue"].sum())

    out = pd.DataFrame(
        {
            "removal_effect": re,
            "credit_share": share,
            "attributed_conversions": share * total_conversions,
            "attributed_revenue": share * total_revenue,
        }
    )
    out.index.name = "channel"
    return out.sort_values("credit_share", ascending=False)
