"""Configuration loader.

Reads ``config.yaml`` and overlays environment variables (``.env``) so the
same code path works locally and against the cloud. Nothing here requires a
credential to import — missing values simply leave the relevant feature in
local/mock mode.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:  # optional: load a local .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
GENERATED_DATA_DIR = PROJECT_ROOT / "data" / "generated"


@dataclass
class Config:
    """Typed view over ``config.yaml`` plus environment-derived credentials."""

    channels: list[str]
    data: dict[str, Any]
    attribution: dict[str, Any]
    optimization: dict[str, Any]
    agent: dict[str, Any]
    env: dict[str, Any] = field(default_factory=dict)

    # ----- cloud / integration availability helpers -----------------------
    @property
    def gcp_project(self) -> str | None:
        return self.env.get("GOOGLE_CLOUD_PROJECT") or None

    @property
    def bigquery_enabled(self) -> bool:
        return bool(self.gcp_project)

    @property
    def groq_enabled(self) -> bool:
        return bool(self.env.get("GROQ_API_KEY"))

    @property
    def google_ads_enabled(self) -> bool:
        return bool(self.env.get("GOOGLE_ADS_DEVELOPER_TOKEN"))

    @property
    def meta_enabled(self) -> bool:
        return bool(self.env.get("META_ACCESS_TOKEN"))

    @property
    def apply_bid_changes(self) -> bool:
        return str(self.env.get("APPLY_BID_CHANGES", "false")).lower() == "true"


def _collect_env() -> dict[str, Any]:
    keys = [
        "GOOGLE_CLOUD_PROJECT",
        "BIGQUERY_DATASET",
        "BIGQUERY_LOCATION",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "PUBSUB_TOPIC",
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        "META_ACCESS_TOKEN",
        "META_AD_ACCOUNT_ID",
        "APPLY_BID_CHANGES",
    ]
    return {k: os.environ.get(k) for k in keys if os.environ.get(k) is not None}


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load and validate the project configuration."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    cfg = Config(
        channels=list(raw["channels"]),
        data=dict(raw["data"]),
        attribution=dict(raw["attribution"]),
        optimization=dict(raw["optimization"]),
        agent=dict(raw["agent"]),
        env=_collect_env(),
    )

    # Light validation so misconfiguration fails loudly and early.
    if cfg.data["max_touchpoints"] > 8:
        raise ValueError("max_touchpoints must be <= 8 for exact Shapley computation")
    w = cfg.attribution["weight_shapley"] + cfg.attribution["weight_markov"]
    if abs(w - 1.0) > 1e-6:
        raise ValueError(f"attribution weights must sum to 1.0 (got {w})")
    return cfg
