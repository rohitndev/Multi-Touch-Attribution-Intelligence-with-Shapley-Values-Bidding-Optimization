# API & Cloud Setup

Every integration below is **optional**. With none of them configured the
pipeline runs fully on synthetic data and mock ad clients. Configure only the
ones you need — the pipeline auto-detects each credential and switches the
matching component from mock to live.

Copy [`.env.example`](../.env.example) to `.env` and fill in the relevant keys.

## 1. Google Cloud — GA4 → BigQuery warehouse

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project
```
Set `GOOGLE_CLOUD_PROJECT` (and optionally `GOOGLE_APPLICATION_CREDENTIALS`) in
`.env`. The pipeline then loads events to the `attribution` BigQuery dataset via
[`src/ingestion/bigquery_loader.py`](../src/ingestion/bigquery_loader.py); the
`dbt` models in [`dbt/`](../dbt) do session stitching and path construction.

## 2. Groq — Attribution Advisor LLM

Get a free key at <https://console.groq.com> and set `GROQ_API_KEY`. The agent
([`src/agent/advisor.py`](../src/agent/advisor.py)) then uses the LLM to write
the reallocation rationale; otherwise it falls back to a deterministic
rule-based narrative.

## 3. Google Ads API

Set `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`,
`GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`,
`GOOGLE_ADS_LOGIN_CUSTOMER_ID`. Bid adjustments flow through
[`src/agent/google_ads_client.py`](../src/agent/google_ads_client.py).

### Google Ads bid-adjustment example

```python
from src.agent import GoogleAdsClient

client = GoogleAdsClient(apply_changes=True)   # requires APPLY_BID_CHANGES=true
client.adjust_bid(
    channel="Paid Search",
    current_bid=1.00,
    new_bid=1.20,                              # +20% toward a high-Shapley channel
    reason="composite-attribution reallocation",
)
```

## 4. Meta Marketing API

Set `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`, `META_APP_ID`,
`META_APP_SECRET`. Handled by
[`src/agent/meta_ads_client.py`](../src/agent/meta_ads_client.py).

## Safety: dry-run by default

`APPLY_BID_CHANGES` defaults to `false`, so the agent only **logs** intended bid
changes to `outputs/agent_audit_log.jsonl`. Set it to `true` only when you have
wired real campaign / ad-set IDs and want live mutations.
