"""Tests for the Markov-chain removal-effect attribution model."""
from __future__ import annotations

import numpy as np

from src.attribution.markov import (
    CONV,
    NULL,
    build_transition_matrix,
    markov_attribution,
)


def test_transition_matrix_is_row_stochastic(journeys, channels):
    trans, states = build_transition_matrix(journeys, channels)
    row_sums = trans.sum(axis=1)
    assert np.allclose(row_sums, 1.0)
    assert set([CONV, NULL]).issubset(set(states))


def test_absorbing_states_are_self_looping(journeys, channels):
    trans, states = build_transition_matrix(journeys, channels)
    sidx = {s: i for i, s in enumerate(states)}
    assert np.isclose(trans[sidx[CONV], sidx[CONV]], 1.0)
    assert np.isclose(trans[sidx[NULL], sidx[NULL]], 1.0)


def test_removal_effect_shares_sum_to_one(journeys, channels):
    res = markov_attribution(journeys, channels)
    assert np.isclose(res["credit_share"].sum(), 1.0)
    assert (res["removal_effect"] >= 0).all()


def test_high_strength_channel_ranks_high(journeys, channels):
    """Paid Search (high latent strength) should out-rank Display."""
    res = markov_attribution(journeys, channels)
    assert res.loc["Paid Search", "credit_share"] > res.loc["Display", "credit_share"]
