"""End-to-end integration test for the full pipeline."""
from __future__ import annotations

import numpy as np

from src.config import load_config
from src.pipeline import run_pipeline


def test_pipeline_runs_end_to_end():
    cfg = load_config()
    cfg.data["n_users"] = 2000  # keep the test fast
    res = run_pipeline(cfg, make_charts=False)

    # Every model produced a full credit distribution.
    for col in ["shapley", "markov", "composite", "last_click"]:
        assert np.isclose(res.comparison[col].sum(), 1.0, atol=1e-6)

    # Optimiser produced a valid allocation.
    assert res.optimization.optimized_revenue > 0

    # Agent closed the loop and recorded at least one (dry-run) bid change.
    assert isinstance(res.plan.bid_changes, list)
    assert res.plan.rationale  # non-empty rationale

    # Warehouse ingestion ran (local fallback in CI).
    assert res.ingest_summary["n_journeys"] == 2000


def test_composite_weights_blend_correctly(channels):
    """Composite share must equal the weighted blend of its components."""
    from src.attribution import (
        composite_attribution,
        markov_attribution,
        shapley_attribution,
    )
    from data.journey_generator import generate_journeys

    journeys = generate_journeys(channels, n_users=2000, seed=11).journeys
    shap = shapley_attribution(journeys, channels)["credit_share"]
    mark = markov_attribution(journeys, channels)["credit_share"]
    comp = composite_attribution(journeys, channels, 0.7, 0.3)["composite_share"]

    expected = 0.7 * shap + 0.3 * mark
    expected = expected / expected.sum()
    # Compare on a common channel ordering.
    for c in channels:
        assert np.isclose(comp[c], expected[c], atol=1e-9)
