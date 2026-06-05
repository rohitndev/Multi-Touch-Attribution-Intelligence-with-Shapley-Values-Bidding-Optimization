# Tableau Public Workbook — Shapley Attribution Comparison

This workbook visualises the model-comparison output of the pipeline.

## Data source

Connect Tableau to either:
- The BigQuery `attribution.channel_attribution` table, **or**
- The local export produced by the pipeline (`data/generated/*.parquet`).

## Sheets

1. **Shapley vs Last-Click** — side-by-side bars of `shapley_share` and
   `last_click_share` per channel (recreates `outputs/shapley_vs_lastclick.png`).
2. **Model Comparison Matrix** — heat map of credit share across Shapley,
   Markov, composite, last-click, first-click and linear models.
3. **Markov Transition Chains** — matrix view of channel-to-channel transition
   probabilities (`outputs/markov_transitions.png`).
4. **Budget Reallocation** — current vs optimised spend, coloured by delta.

Publish to Tableau Public and link the URL here once live.
