"""Interactive budget-reallocation simulator (Streamlit).

Optional companion to the backend pipeline. A marketer adjusts the channel mix
with sliders and immediately sees the predicted blended-ROAS impact, computed
from the same Shapley marginal-contribution curves used by the optimiser.

Run with:
    pip install -r requirements-cloud.txt
    streamlit run dashboards/streamlit_simulator.py
"""
from __future__ import annotations

import streamlit as st

from src.attribution import composite_attribution
from src.config import load_config
from src.optimization import compare_scenarios, optimize_budget
from data.journey_generator import generate_journeys


@st.cache_data
def _load(n_users: int):
    cfg = load_config()
    journeys = generate_journeys(cfg.channels, n_users=n_users, seed=cfg.data["seed"]).journeys
    comp = composite_attribution(journeys, cfg.channels)
    return cfg, comp


def main() -> None:
    st.set_page_config(page_title="Budget Reallocation Simulator", layout="wide")
    st.title("Budget Reallocation Simulator")
    st.caption("Shapley-driven marginal contribution curves • predicted ROAS impact")

    cfg, comp = _load(10000)
    budget = st.sidebar.number_input(
        "Total monthly budget ($)", value=float(cfg.optimization["total_budget"]),
        step=50000.0,
    )

    st.sidebar.header("Channel mix (%)")
    mix = {}
    for ch in cfg.channels:
        default = float(comp.loc[ch, "composite_share"] * 100)
        mix[ch] = st.sidebar.slider(ch, 0.0, 100.0, round(default, 1))

    opt = optimize_budget(comp, total_budget=budget)
    scen = compare_scenarios(
        comp, total_budget=budget,
        scenarios={
            "Your mix": mix,
            "Shapley-optimised": opt.allocation["optimized_spend"].to_dict(),
            "Even split": {c: 1.0 for c in cfg.channels},
        },
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Composite attribution")
        st.bar_chart(comp["composite_share"])
    with col2:
        st.subheader("Predicted ROAS by scenario")
        st.bar_chart(scen["predicted_roas"])

    st.subheader("Scenario comparison")
    st.dataframe(scen)


if __name__ == "__main__":
    main()
