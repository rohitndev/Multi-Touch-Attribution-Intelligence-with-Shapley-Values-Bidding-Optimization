"""Meta (Facebook) Marketing API client for autonomous bid adjustment.

Mirrors :class:`GoogleAdsClient`: uses the official ``facebook-business`` SDK
when ``META_ACCESS_TOKEN`` is configured, otherwise records intended changes to
the shared agent audit log in dry-run mode.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from .google_ads_client import _append_audit


class MetaAdsClient:
    """Adjust ad-set bids on Meta (or simulate when offline)."""

    platform = "meta_marketing"

    def __init__(self, apply_changes: bool = False):
        self.apply_changes = apply_changes
        self._sdk = self._try_load_sdk()

    @property
    def live(self) -> bool:
        return self._sdk is not None and self.apply_changes

    def _try_load_sdk(self):
        token = os.environ.get("META_ACCESS_TOKEN")
        if not token:
            return None
        try:  # pragma: no cover - exercised only with real credentials
            from facebook_business.api import FacebookAdsApi

            FacebookAdsApi.init(
                app_id=os.environ.get("META_APP_ID"),
                app_secret=os.environ.get("META_APP_SECRET"),
                access_token=token,
            )
            return FacebookAdsApi.get_default_api()
        except Exception:
            return None

    def adjust_bid(self, channel: str, current_bid: float, new_bid: float, reason: str):
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
            raise NotImplementedError(
                "Live Meta mutation is intentionally stubbed; wire up your "
                "ad-set IDs before enabling APPLY_BID_CHANGES."
            )
        _append_audit(record)
        return record
