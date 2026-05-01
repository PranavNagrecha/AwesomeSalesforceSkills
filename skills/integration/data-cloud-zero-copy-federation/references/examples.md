# Examples — Data Cloud Zero Copy Federation

## Example 1: Federate a Snowflake transaction history into Data Cloud

**Context:** A retailer has 2.4 billion order-line rows in Snowflake (`ANALYTICS.SALES.ORDER_LINE`). Marketing wants to segment customers by 90-day spend bands. The Snowflake table is owned by the data-engineering team and is the system of record. Physical ingestion would breach the 100M row / 50 GB ceiling and create a duplicate authority.

**Problem:** Without federation the team builds a chunked bulk-API pipeline that re-syncs the table nightly, and segments lag by ~24h. Storage doubles. Source schema changes break the pipeline silently.

**Solution:**

```sql
-- Snowflake side: minimal share, filter to needed columns only
CREATE SHARE SFDC_DATACLOUD_ORDERLINES;
GRANT USAGE ON DATABASE ANALYTICS TO SHARE SFDC_DATACLOUD_ORDERLINES;
GRANT USAGE ON SCHEMA ANALYTICS.SALES TO SHARE SFDC_DATACLOUD_ORDERLINES;

CREATE SECURE VIEW ANALYTICS.SALES.ORDER_LINE_DC AS
SELECT customer_id, order_id, order_date, line_amount_usd
FROM ANALYTICS.SALES.ORDER_LINE
WHERE order_date >= DATEADD(year, -3, CURRENT_DATE());

GRANT SELECT ON VIEW ANALYTICS.SALES.ORDER_LINE_DC TO SHARE SFDC_DATACLOUD_ORDERLINES;
ALTER SHARE SFDC_DATACLOUD_ORDERLINES ADD ACCOUNTS = ('<sfdc-managed-snowflake-account>');
```

In Data Cloud Setup → Data Streams → New → Lakehouse (Snowflake), authenticate with the share, mount `ANALYTICS.SALES.ORDER_LINE_DC` as an external DLO `OrderLine_dlm`, and map it to a `Order_Line__dlm` DMO related (lookup) to `Individual`.

**Why it works:** The view scopes both the columns and the row history exposed to Data Cloud. The share lives entirely in Snowflake — no data leaves. Segments push their predicates down to Snowflake at query time, and segment build cost is governed by Snowflake credit dashboards, not Data Cloud storage.

---

## Example 2: BigQuery ad-spend with a 90-day acceleration cache

**Context:** Marketing builds Last-Touch Attribution segments compiled 30+ times a day. The source table is `paid-media-prod.attribution.touch_events` in BigQuery, ~800M rows over five years, but only the trailing 90 days are ever queried.

**Problem:** A naive federation over the full table runs 30 queries/day across 800M rows. BigQuery on-demand pricing turns this into a 4-figure monthly bill that the team didn't budget for.

**Solution:**

```yaml
# Data Cloud federated DLO definition (illustrative)
external_dlo: TouchEvent_dlm
  source_connector: BIGQUERY_ATTRIBUTION
  source_table: paid-media-prod.attribution.touch_events
  acceleration:
    enabled: true
    filter: "event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)"
    refresh: every 4h
    materialized_columns:
      - customer_id
      - channel
      - touch_amount_usd
      - event_ts
```

Segments that ask for "spend in last 90 days by channel" hit the cache. A monthly-business-review query that needs five-year history bypasses the cache and goes through the federated path.

**Why it works:** BigQuery is touched only on the 4-hourly refresh. Hot-path segment compiles run against the cache, which is a Data Cloud-managed materialization. Cost is bounded; freshness is explicit (4 hours, not "live").

---

## Anti-Pattern: Federate everything, then add identity resolution

**What practitioners do:** Federate the unified-customer table from Snowflake and immediately map it to the `Individual` DMO as the source of identity-resolution keys. Skip the acceleration cache because "federation is live, that's the point."

**What goes wrong:** Identity resolution must read the matching keys deterministically across many tables and many rule passes. Federated reads add network + warehouse latency to every pass. The IR job either takes hours instead of minutes, blows past internal SLAs, and starts contending with other Snowflake workloads — or, on some platforms, simply errors out with "field not materialized."

**Correct approach:** Materialize the resolution keys (email, phone, customer ID) into a query-acceleration cache, even if the rest of the columns stay federated. Identity resolution runs against the cache; non-key columns remain live. The two-tier model preserves the single-source-of-truth property without making IR pay the federation tax.
