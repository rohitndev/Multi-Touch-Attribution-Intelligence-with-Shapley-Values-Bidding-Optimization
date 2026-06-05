# Shapley vs Last-Click — Worked Comparison

The platform computes both models on the identical journey table so the
contrast is apples-to-apples. The grouped-bar chart is regenerated on every
run at [`outputs/shapley_vs_lastclick.png`](../outputs/shapley_vs_lastclick.png).

## What the contrast shows

| Pattern | Last-click | Shapley |
| --- | --- | --- |
| Awareness channels (Display, Video, Paid Social) | Under-credited — rarely the final touch | Credited for initiating journeys |
| Branded / bottom-funnel (Direct, Paid Search) | Over-credited — usually the last touch | Credited only for genuine marginal lift |
| Assist-only channels | Invisible | Surface as real contributors |

## Business consequence

Reallocating budget on last-click signals pours money into channels that merely
*close* journeys other channels created — the classic "last-click tax". Shapley
re-credits the upper funnel, and the SciPy optimiser then moves spend toward the
channels with the highest *marginal* contribution, lifting blended ROAS.

See the full methodology in
[`attribution_methodology.md`](./attribution_methodology.md).
