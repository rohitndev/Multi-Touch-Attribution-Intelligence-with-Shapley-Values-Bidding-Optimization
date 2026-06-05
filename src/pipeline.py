"""End-to-end attribution pipeline orchestration.

Runs the full closed loop:

    generate/ingest journeys
      -> Shapley + Markov + composite attribution
      -> baseline comparison (last-click / first-click / linear)
      -> SciPy budget optimisation
      -> Attribution Advisor agent -> ad-platform bid changes
      -> charts + report artifacts

Designed to run fully offline on synthetic data, and to transparently use
BigQuery / Groq / Google Ads / Meta when their credentials are configured.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .attribution import (
    baseline_attributions,
    composite_attribution,
)
from .attribution.markov import build_transition_matrix, markov_attribution
from .attribution.shapley import shapley_attribution
from .config import Config, load_config
from .ingestion import ingest_events
from .optimization import compare_scenarios, optimize_budget
from .agent import AttributionAdvisor
from data.journey_generator import generate_journeys


@dataclass
class PipelineResult:
    journeys: pd.DataFrame
    shapley: pd.DataFrame
    markov: pd.DataFrame
    composite: pd.DataFrame
    baselines: pd.DataFrame
    comparison: pd.DataFrame
    optimization: object
    scenarios: pd.DataFrame
    plan: object
    ingest_summary: dict


def run_pipeline(cfg: Config | None = None, make_charts: bool = True) -> PipelineResult:
    """Execute the full attribution + optimisation + agent pipeline."""
    cfg = cfg if cfg is not None else load_config()
    assert cfg is not None  # for type-checkers; load_config never returns None
    channels = cfg.channels

    # 1. Data — synthetic journeys (or GA4 export in production) -------------
    ds = generate_journeys(
        channels=channels,
        n_users=cfg.data["n_users"],
        max_touchpoints=cfg.data["max_touchpoints"],
        avg_order_value=cfg.data["avg_order_value"],
        attribution_window_days=cfg.data["attribution_window_days"],
        seed=cfg.data["seed"],
    )

    # 2. Ingestion — persist to warehouse (BigQuery or local) ----------------
    ingest_summary = ingest_events(
        ds.events, ds.journeys, project=cfg.gcp_project,
        dataset=cfg.env.get("BIGQUERY_DATASET", "attribution"),
    )

    # 3. Attribution models --------------------------------------------------
    shapley = shapley_attribution(ds.journeys, channels)
    markov = markov_attribution(ds.journeys, channels)
    composite = composite_attribution(
        ds.journeys, channels,
        weight_shapley=cfg.attribution["weight_shapley"],
        weight_markov=cfg.attribution["weight_markov"],
    )
    baselines = baseline_attributions(ds.journeys, channels)

    comparison = pd.DataFrame(
        {
            "shapley": shapley["credit_share"],
            "markov": markov["credit_share"],
            "composite": composite["composite_share"],
            "last_click": baselines["last_click"],
            "first_click": baselines["first_click"],
            "linear": baselines["linear"],
        }
    ).reindex(channels)

    # 4. Budget optimisation -------------------------------------------------
    opt = optimize_budget(
        composite,
        total_budget=cfg.optimization["total_budget"],
        min_share=cfg.optimization["min_share"],
        max_share=cfg.optimization["max_share"],
        gamma=cfg.optimization["diminishing_returns"],
        baseline_roas=cfg.optimization["baseline_roas"],
    )

    scenarios = compare_scenarios(
        composite,
        total_budget=cfg.optimization["total_budget"],
        scenarios={
            "Even split": {c: 1.0 for c in channels},
            "Last-click led": baselines["last_click"].to_dict(),
            "Shapley-optimised": opt.allocation["optimized_spend"].to_dict(),
        },
        gamma=cfg.optimization["diminishing_returns"],
        baseline_roas=cfg.optimization["baseline_roas"],
    )

    # 5. Attribution Advisor agent -> bid changes ----------------------------
    advisor = AttributionAdvisor(
        top_n=cfg.agent["top_n"],
        bottom_n=cfg.agent["bottom_n"],
        max_bid_shift_pct=cfg.agent["max_bid_shift_pct"],
        apply_changes=cfg.apply_bid_changes,
    )
    plan = advisor.recommend(composite, opt.allocation)

    # 6. Charts --------------------------------------------------------------
    if make_charts:
        from . import visualization as viz

        viz.plot_shapley_vs_lastclick(shapley["credit_share"], baselines["last_click"])
        viz.plot_model_comparison(comparison)
        trans, states = build_transition_matrix(ds.journeys, channels)
        viz.plot_transition_heatmap(trans, states)
        viz.plot_budget_reallocation(opt.allocation)
        viz.plot_roas_uplift(opt.current_revenue, opt.optimized_revenue, opt.total_budget)
        viz.export_sankey(ds.journeys, channels)

    return PipelineResult(
        journeys=ds.journeys,
        shapley=shapley,
        markov=markov,
        composite=composite,
        baselines=baselines,
        comparison=comparison,
        optimization=opt,
        scenarios=scenarios,
        plan=plan,
        ingest_summary=ingest_summary,
    )
