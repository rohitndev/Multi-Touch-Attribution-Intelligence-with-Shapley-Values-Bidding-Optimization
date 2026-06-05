"""GA4 -> BigQuery event ingestion.

In production, GA4 streams customer-journey events to BigQuery natively, and a
GCP Pub/Sub -> Dataflow pipeline adds the intraday real-time layer. For local
development this module takes the synthetic event log and persists it through
:class:`BigQueryLoader` (BigQuery when configured, local Parquet/CSV otherwise),
returning a summary of what was ingested.
"""
from __future__ import annotations

import pandas as pd

from .bigquery_loader import BigQueryLoader


def ingest_events(
    events: pd.DataFrame,
    journeys: pd.DataFrame,
    project: str | None = None,
    dataset: str = "attribution",
) -> dict:
    """Persist the GA4-style event log and journey table to the warehouse."""
    loader = BigQueryLoader(project=project, dataset=dataset)
    events_dest = loader.load_table(events, "ga4_events")
    journeys_dest = loader.load_table(journeys, "customer_journeys")

    return {
        "backend": loader.backend,
        "events_destination": events_dest,
        "journeys_destination": journeys_dest,
        "n_events": int(len(events)),
        "n_journeys": int(len(journeys)),
    }
