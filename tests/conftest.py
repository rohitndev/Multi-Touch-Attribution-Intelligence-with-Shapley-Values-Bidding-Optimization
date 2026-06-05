"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from data.journey_generator import generate_journeys

CHANNELS = ["Paid Search", "Organic Search", "Display", "Email"]


@pytest.fixture(scope="session")
def channels() -> list[str]:
    return CHANNELS


@pytest.fixture(scope="session")
def journeys():
    """A small, deterministic journey dataset for fast tests."""
    ds = generate_journeys(CHANNELS, n_users=3000, max_touchpoints=4, seed=7)
    return ds.journeys
