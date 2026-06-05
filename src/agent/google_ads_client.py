"""Google Ads API client for autonomous bid adjustment.

Wraps the official ``google-ads`` library when credentials are present, and
falls back to a fully functional **mock** that records intended bid changes to
an audit log otherwise. This lets the closed-loop optimisation run end-to-end
in development without touching a live ad account.

Every bid change — real or simulated — is appended to the agent audit log
(``outputs/agent_audit_log.jsonl``) for review, satisfying the "all API bid
changes logged" monitoring requirement.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..config import OUTPUT_DIR

AUDIT_LOG = OUTPUT_DIR / "agent_audit_log.jsonl"


class GoogleAdsClient:
    """Adjust campaign bids on Google Ads (or simulate when offline)."""

    platform = "google_ads"

    def __init__(self, apply_changes: bool = False):
        self.apply_changes = apply_changes
        self._sdk = self._try_load_sdk()

    @property
    def live(self) -> bool:
        return self._sdk is not None and self.apply_changes

    def _try_load_sdk(self):
        token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
        if not token:
            return None
        try:  # pragma: no cover - exercised only with real credentials
            from google.ads.googleads.client import GoogleAdsClient as _GAClient

            return _GAClient.load_from_env()
        except Exception:
            return None

    def adjust_bid(self, channel: str, current_bid: float, new_bid: float, reason: str):
        """Apply (or simulate) a bid-modifier change for a channel/campaign."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": self.platform,
            "channel": channel,
            "current_bid": round(current_bid, 4),
            "new_bid": round(new_bid, 4),
            "change_pct": round((new_bid - current_bid) / current_bid, 4)
            if current_bid
            else 0.0,
            "reason": reason,
            "mode": "live" if self.live else "dry_run",
        }
        if self.live:  # pragma: no cover - requires live account
            self._push_bid_modifier(channel, new_bid)
        _append_audit(record)
        return record

    def _push_bid_modifier(self, channel: str, new_bid: float):  # pragma: no cover
        # Real implementation would build a CampaignCriterionOperation here and
        # call self._sdk.get_service("CampaignService").mutate_campaigns(...).
        raise NotImplementedError(
            "Live Google Ads mutation is intentionally stubbed; wire up your "
            "campaign IDs before enabling APPLY_BID_CHANGES."
        )


def _append_audit(record: dict) -> None:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
