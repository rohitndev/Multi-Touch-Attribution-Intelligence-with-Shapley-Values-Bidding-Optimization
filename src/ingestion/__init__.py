"""Event ingestion: GA4 -> BigQuery streaming with local fallback."""

from .bigquery_loader import BigQueryLoader
from .ga4_stream import ingest_events

__all__ = ["BigQueryLoader", "ingest_events"]
