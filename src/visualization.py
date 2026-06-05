"""Static chart generation for the attribution platform.

Produces the figures referenced in the README (Shapley vs last-click
comparison, model comparison, Markov transition heat-map, budget reallocation,
ROAS uplift). All charts are written to ``outputs/`` as PNGs using a clean,
white-background Matplotlib theme. A Sankey diagram of customer journeys is
exported via Plotly when it is installed; otherwise it is skipped gracefully.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless / no display required
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .config import OUTPUT_DIR  # noqa: E402

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
    }
)

_PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed",
            "#0891b2", "#db2777", "#65a30d"]


def _ensure_dir() -> Path:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    return Path(OUTPUT_DIR)


def plot_shapley_vs_lastclick(
    shapley_share: pd.Series, last_click_share: pd.Series, fname: str = "shapley_vs_lastclick.png"
) -> Path:
    """Grouped bar chart contrasting Shapley with last-click credit."""
    out = _ensure_dir() / fname
    channels = list(shapley_share.index)
    x = np.arange(len(channels))
    w = 0.38

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(x - w / 2, shapley_share.values * 100, w, label="Shapley", color="#2563eb")
    ax.bar(x + w / 2, last_click_share.reindex(channels).values * 100, w,
           label="Last-click", color="#94a3b8")
    ax.set_ylabel("Conversion credit (%)")
    ax.set_title("Shapley vs Last-Click Attribution by Channel")
    ax.set_xticks(x)
    ax.set_xticklabels(channels, rotation=30, ha="right")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_model_comparison(
    comparison: pd.DataFrame, fname: str = "model_comparison.png"
) -> Path:
    """Heat-map-style grouped bars of credit share across all models."""
    out = _ensure_dir() / fname
    fig, ax = plt.subplots(figsize=(11, 6))
    comparison_pct = comparison * 100
    comparison_pct.plot(kind="bar", ax=ax, color=_PALETTE[: comparison.shape[1]])
    ax.set_ylabel("Conversion credit (%)")
    ax.set_title("Attribution Model Comparison by Channel")
    ax.set_xticklabels(comparison.index, rotation=30, ha="right")
    ax.legend(frameon=False, title="Model")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_transition_heatmap(
    trans: np.ndarray, states: list[str], fname: str = "markov_transitions.png"
) -> Path:
    """Heat-map of the Markov channel transition-probability matrix."""
    out = _ensure_dir() / fname
    fig, ax = plt.subplots(figsize=(8.5, 7))
    im = ax.imshow(trans, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(states)))
    ax.set_yticks(range(len(states)))
    ax.set_xticklabels(states, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(states, fontsize=8)
    ax.set_title("Markov Chain Channel Transition Matrix")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="P(next state)")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_budget_reallocation(
    allocation: pd.DataFrame, fname: str = "budget_reallocation.png"
) -> Path:
    """Current vs optimised spend per channel."""
    out = _ensure_dir() / fname
    channels = list(allocation.index)
    x = np.arange(len(channels))
    w = 0.38
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(x - w / 2, allocation["current_spend"] / 1000, w,
           label="Current", color="#94a3b8")
    ax.bar(x + w / 2, allocation["optimized_spend"] / 1000, w,
           label="Optimised", color="#16a34a")
    ax.set_ylabel("Monthly spend ($K)")
    ax.set_title("Budget Reallocation: Current vs Shapley-Optimised")
    ax.set_xticks(x)
    ax.set_xticklabels(channels, rotation=30, ha="right")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_roas_uplift(
    current_revenue: float, optimized_revenue: float, total_budget: float,
    fname: str = "roas_uplift.png"
) -> Path:
    """Before/after blended ROAS bar chart."""
    out = _ensure_dir() / fname
    cur_roas = current_revenue / total_budget if total_budget else 0
    opt_roas = optimized_revenue / total_budget if total_budget else 0
    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(["Current mix", "Optimised mix"], [cur_roas, opt_roas],
                  color=["#94a3b8", "#16a34a"], width=0.5)
    for b, v in zip(bars, [cur_roas, opt_roas]):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}x",
                ha="center", va="bottom", fontweight="bold")
    ax.set_ylabel("Blended ROAS")
    uplift = (opt_roas / cur_roas - 1) if cur_roas else 0
    ax.set_title(f"Predicted Blended ROAS Improvement (+{uplift:.0%})")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def export_sankey(
    journeys: pd.DataFrame, channels: list[str], top_n: int = 12,
    fname: str = "journey_sankey.html"
) -> Path | None:
    """Export an interactive customer-journey Sankey diagram (Plotly).

    Returns the output path, or ``None`` if Plotly is not installed.
    """
    try:
        import plotly.graph_objects as go
    except Exception:
        return None

    out = _ensure_dir() / fname
    conv = journeys[journeys["converted"] == 1]
    pairs: dict[tuple[str, str], int] = {}
    for path in conv["path"]:
        seq = path.split(" > ")
        for a, b in zip(seq[:-1], seq[1:]):
            pairs[(a, b)] = pairs.get((a, b), 0) + 1
    top = sorted(pairs.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    labels = sorted({c for (a, b), _ in top for c in (a, b)})
    lidx = {c: i for i, c in enumerate(labels)}
    fig = go.Figure(
        go.Sankey(
            node=dict(label=labels, pad=18, thickness=16),
            link=dict(
                source=[lidx[a] for (a, b), _ in top],
                target=[lidx[b] for (a, b), _ in top],
                value=[v for _, v in top],
            ),
        )
    )
    fig.update_layout(title_text="Customer Journey Flow (converting paths)",
                      paper_bgcolor="white", font_size=11)
    fig.write_html(str(out))
    return out
