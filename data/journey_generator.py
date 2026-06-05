"""Synthetic multi-channel customer-journey generator.

Produces realistic clickstream-style journeys (a user touches an ordered
sequence of marketing channels and either converts or not, with a revenue
value on conversion). This stands in for the GA4 -> BigQuery export so the
whole platform runs offline; the schema mirrors what the GA4 BigQuery export
and the ``dbt`` path-construction models produce in production.

Each channel is assigned a latent "conversion strength" so that some channels
(e.g. Paid Search, Email) genuinely drive incremental conversions while others
(e.g. Display, Direct) are mostly assists or last-mile. This latent structure
is what the Shapley and Markov models are expected to recover.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Latent per-channel parameters. ``strength`` drives the incremental
# conversion contribution; ``intro`` is the relative likelihood of *starting*
# a journey on that channel (top-of-funnel vs. bottom-of-funnel).
_CHANNEL_PRIORS: dict[str, dict[str, float]] = {
    "Paid Search":    {"strength": 0.55, "intro": 0.20},
    "Organic Search": {"strength": 0.45, "intro": 0.18},
    "Display":        {"strength": 0.12, "intro": 0.16},
    "Paid Social":    {"strength": 0.30, "intro": 0.17},
    "Email":          {"strength": 0.50, "intro": 0.06},
    "Video":          {"strength": 0.18, "intro": 0.10},
    "Referral":       {"strength": 0.28, "intro": 0.05},
    "Direct":         {"strength": 0.20, "intro": 0.08},
}


@dataclass
class JourneyDataset:
    """In-memory representation of the generated journeys."""

    events: pd.DataFrame      # one row per touchpoint (GA4-style event log)
    journeys: pd.DataFrame    # one row per user with the ordered channel path
    channels: list[str]


def _channel_params(channels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    strength = np.array(
        [_CHANNEL_PRIORS.get(c, {"strength": 0.25})["strength"] for c in channels]
    )
    intro = np.array(
        [_CHANNEL_PRIORS.get(c, {"intro": 0.1})["intro"] for c in channels]
    )
    intro = intro / intro.sum()
    return strength, intro


def generate_journeys(
    channels: list[str],
    n_users: int = 20000,
    max_touchpoints: int = 8,
    avg_order_value: float = 85.0,
    attribution_window_days: int = 30,
    seed: int = 42,
) -> JourneyDataset:
    """Generate ``n_users`` synthetic customer journeys.

    Returns a :class:`JourneyDataset` containing both a GA4-style event log and
    a one-row-per-journey table with the ordered channel path and conversion
    label/value.
    """
    rng = np.random.default_rng(seed)
    strength, intro = _channel_params(channels)
    n_ch = len(channels)

    journey_rows: list[dict] = []
    event_rows: list[dict] = []

    base_ts = np.datetime64("2024-01-01T00:00:00")
    minute = np.timedelta64(1, "m")

    for uid in range(n_users):
        # Path length is right-skewed: most journeys are short.
        path_len = int(min(max_touchpoints, 1 + rng.poisson(1.6)))

        # First touch drawn from the "intro" distribution; subsequent touches
        # are drawn with a mild stickiness so paths look correlated.
        path_idx: list[int] = [int(rng.choice(n_ch, p=intro))]
        for _ in range(path_len - 1):
            probs = np.full(n_ch, 1.0)
            probs[path_idx[-1]] *= 0.4  # discourage immediate repeats
            probs = probs / probs.sum()
            path_idx.append(int(rng.choice(n_ch, p=probs)))

        unique_idx = sorted(set(path_idx))
        # Conversion probability: saturating function of the summed strength of
        # the *distinct* channels touched (diminishing returns via tanh).
        coalition_strength = strength[unique_idx].sum()
        p_conv = float(np.tanh(0.55 * coalition_strength))
        converted = int(rng.random() < p_conv)

        # Spread touches across the attribution window.
        offsets = np.sort(
            rng.integers(0, attribution_window_days * 24 * 60, size=path_len)
        )
        revenue = 0.0
        if converted:
            revenue = float(max(5.0, rng.gamma(shape=4.0, scale=avg_order_value / 4.0)))

        path_channels = [channels[i] for i in path_idx]
        journey_rows.append(
            {
                "user_id": f"u{uid:06d}",
                "path": " > ".join(path_channels),
                "path_length": path_len,
                "n_unique_channels": len(unique_idx),
                "converted": converted,
                "revenue": round(revenue, 2),
                "first_touch": path_channels[0],
                "last_touch": path_channels[-1],
            }
        )

        for step, (idx, off) in enumerate(zip(path_idx, offsets)):
            event_rows.append(
                {
                    "user_id": f"u{uid:06d}",
                    "event_timestamp": base_ts + int(off) * minute,
                    "step": step,
                    "channel": channels[idx],
                    "is_conversion": int(converted and step == path_len - 1),
                    "event_value": round(revenue, 2)
                    if (converted and step == path_len - 1)
                    else 0.0,
                }
            )

    journeys = pd.DataFrame(journey_rows)
    events = pd.DataFrame(event_rows).sort_values(
        ["user_id", "event_timestamp"]
    ).reset_index(drop=True)

    return JourneyDataset(events=events, journeys=journeys, channels=list(channels))


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    ds = generate_journeys(list(_CHANNEL_PRIORS.keys()), n_users=5000)
    print(ds.journeys.head())
    print(
        f"\nconversion rate: {ds.journeys['converted'].mean():.2%} | "
        f"total revenue: {ds.journeys['revenue'].sum():,.0f}"
    )
