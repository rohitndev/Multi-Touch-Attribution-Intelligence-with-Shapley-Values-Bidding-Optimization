# Dashboards

Three reporting surfaces sit on top of the attribution warehouse. All read from
the BigQuery `attribution` dataset (or the local Parquet/CSV exports in
`data/generated/`).

| Dashboard | Tool | Purpose | File |
| --- | --- | --- | --- |
| Budget Reallocation Simulator | Streamlit | Interactive channel-mix what-if with predicted ROAS | [`streamlit_simulator.py`](./streamlit_simulator.py) |
| Channel ROAS & Journey Sankey | Looker Studio | Channel ROAS, journey Sankey diagram | [`looker_studio_config.json`](./looker_studio_config.json) |
| Shapley Attribution Comparison | Tableau Public | Shapley vs last-click, Markov chains | [`tableau_workbook.md`](./tableau_workbook.md) |

## Run the simulator locally

```bash
pip install -r requirements-cloud.txt
streamlit run dashboards/streamlit_simulator.py
```

The Sankey diagram exported by the pipeline (`outputs/journey_sankey.html`) can
be embedded directly into Looker Studio as a community visualisation or
screenshot.
