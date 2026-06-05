"""BigQuery warehouse loader with a transparent local fallback.

In production this loads GA4 journey events into the BigQuery sandbox (the
``attribution`` dataset) that the ``dbt`` models read from. When no GCP project
is configured it writes the same tables to ``data/generated/`` as Parquet/CSV
so the rest of the pipeline is identical offline.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import GENERATED_DATA_DIR


class BigQueryLoader:
    """Load DataFrames to BigQuery, or to local files when offline."""

    def __init__(self, project: str | None = None, dataset: str = "attribution"):
        self.project = project
        self.dataset = dataset
        self._client = self._try_client()

    @property
    def backend(self) -> str:
        return "bigquery" if self._client is not None else "local"

    def _try_client(self):
        if not self.project:
            return None
        try:  # pragma: no cover - requires GCP credentials
            from google.cloud import bigquery

            return bigquery.Client(project=self.project)
        except Exception:
            return None

    def load_table(self, df: pd.DataFrame, table: str) -> str:
        """Write ``df`` to ``<dataset>.<table>`` (BigQuery) or a local file.

        Returns the fully-qualified destination identifier / path.
        """
        if self._client is not None:  # pragma: no cover - requires GCP
            from google.cloud import bigquery

            table_id = f"{self.project}.{self.dataset}.{table}"
            job = self._client.load_table_from_dataframe(
                df,
                table_id,
                job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
            )
            job.result()
            return table_id

        Path(GENERATED_DATA_DIR).mkdir(parents=True, exist_ok=True)
        dest = GENERATED_DATA_DIR / f"{table}.parquet"
        try:
            df.to_parquet(dest, index=False)
        except Exception:
            # pyarrow/fastparquet not installed — fall back to CSV.
            dest = GENERATED_DATA_DIR / f"{table}.csv"
            df.to_csv(dest, index=False)
        return str(dest)
