---
name: commerce-analytics-data
description: "Use when analyzing B2C Commerce storefront metrics (conversion funnel, cart abandonment, product performance, revenue trends) via the Business Manager Reports and Dashboards app, or when deriving B2B Commerce analytics via SOQL on core platform objects or the CRM Analytics B2B Commerce template. NOT for CRM Analytics platform configuration, Einstein Analytics, Experience Cloud analytics, or general Salesforce report builder usage."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "How do I see my storefront conversion rate in Business Manager"
  - "Where can I find cart abandonment data for our B2C Commerce site"
  - "How do I track product performance and revenue trends for our online store"
  - "What reports exist for B2C Commerce order and checkout analytics"
  - "How do I get B2B Commerce cart abandonment metrics without CRM Analytics"
  - "Why can't I find Commerce sales data in standard Salesforce reports"
  - "How do I export conversion funnel data from Business Manager to CSV"
tags:
  - commerce
  - b2c-commerce
  - b2b-commerce
  - analytics
  - conversion-funnel
  - cart-abandonment
  - product-performance
  - revenue-metrics
inputs:
  - "Commerce platform in use: B2C Commerce (SFCC) or B2B Commerce on Core"
  - "Business unit or site ID in Business Manager (for B2C)"
  - "Date range for the analysis"
  - "Specific metric focus: conversion, cart abandonment, product performance, or revenue"
  - "Whether CRM Analytics is licensed (relevant only for B2B)"
outputs:
  - "Step-by-step guidance for accessing the correct analytics surface"
  - "SOQL query for B2B Commerce WebCart abandonment analysis"
  - "Decision table mapping metric needs to the right tool and data source"
  - "Export and scheduling approach for ongoing reporting"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Commerce Analytics Data

Use this skill when a practitioner needs to measure storefront performance — conversion funnels, cart abandonment rates, product revenue, or order trends — and needs guidance on which analytics surface to use for B2C Commerce vs. B2B Commerce on Core. This skill covers the native reporting tools for each platform and the SOQL-based fallbacks; it does not cover CRM Analytics configuration or Einstein Analytics setup.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which Commerce platform is in use?** B2C Commerce (Salesforce Commerce Cloud / SFCC) and B2B Commerce on Core are architecturally separate: B2C runs in a separate SaaS realm with its own Business Manager UI; B2B Commerce runs natively on the Salesforce platform. The analytics approach differs completely between them.
- **Is the legacy Business Manager Analytics still referenced?** The legacy Business Manager Analytics module was retired on January 1, 2021. Any guidance referencing it is outdated. The current surface is the Reports and Dashboards app inside Business Manager.
- **Is CRM Analytics licensed?** For B2B Commerce, native analytics UI does not exist. CRM Analytics with the B2B Commerce template (`bi_template_b2bcommerce`) is the productized option; SOQL queries against WebCart and related objects are the free-tier alternative.
- **What is the volume of data?** B2C Commerce Business Manager CSV export is hard-capped at 1,000 rows per export. Any analysis requiring more rows must either use the SFTP feed, the reporting API, or an external data pipeline.

---

## Core Concepts

### B2C Commerce Analytics: Business Manager Reports and Dashboards App

B2C Commerce analytics live entirely within the **Business Manager Reports and Dashboards** application. This is a purpose-built analytics UI inside the Business Manager administration portal — it is separate from the Salesforce platform and is not accessible via Lightning Experience, standard Salesforce Reports, or SOQL.

The app ships with nine dashboard types:
1. **Conversion** — funnel from visit to order, broken down by step (cart, checkout, payment, order placed)
2. **Revenue** — gross merchandise value (GMV), average order value (AOV), net sales
3. **Orders** — order counts, cancellations, returns
4. **Products** — top products by revenue, units, and view-to-purchase rate
5. **Promotions** — discount usage, revenue impact
6. **Customers** — new vs. returning, registration conversion
7. **Search** — internal site search queries, null-result rates, click-through
8. **Storefront** — page views, bounce rate, session counts
9. **A/B Tests** — experiment conversion lift (requires A/B Testing module)

All dashboards support date-range filters, site (business unit) filters, and some support locale or device breakdowns. Data refreshes on a near-real-time cadence (typically 15–60 minutes lag, not true real-time).

### B2C Commerce CSV Export Cap

Every Business Manager dashboard and report supports CSV export. The export is **hard-capped at 1,000 rows**. This is a platform constraint, not a configuration. If an analysis requires row counts above 1,000 (e.g., per-SKU product performance with a large catalog), you must use one of:

- **SFTP Data Feed** — Business Manager can push raw order and session data to an external SFTP server on a scheduled basis. This is the primary mechanism for large-volume offline analytics.
- **B2C Commerce Open Commerce API (OCAPI) / Commerce API** — programmatic access to report data, subject to the same underlying data scope.
- **External pipeline** — ingest SFTP feed into a warehouse (Snowflake, BigQuery, etc.) and use BI tools there.

### B2B Commerce Analytics: No Native UI

B2B Commerce on Core does not have a built-in analytics dashboard equivalent to Business Manager. Cart abandonment, order funnel, and product performance data must be derived from CRM (core platform) objects:

- **WebCart** — represents a shopping cart. `Status` field values: `Active` (open cart), `Closed` (purchased), `PendingDelete`.
- **CartItem** — line items on a WebCart.
- **WebOrder** / **OrderSummary** — completed orders.
- **WebStore** — storefront configuration.

Cart abandonment is calculated as carts with `Status = 'Active'` that have not progressed to a WebOrder within a defined time window. This requires a SOQL query or a scheduled Apex/Flow job to stamp a "abandoned" flag.

### CRM Analytics B2B Commerce Template

For B2B Commerce customers who have CRM Analytics licensed, Salesforce ships a managed package template called `bi_template_b2bcommerce`. This template auto-provisions datasets from B2B Commerce objects and builds pre-built dashboards for conversion, revenue, and buyer behavior. It is the productized path to B2B Commerce analytics but requires a CRM Analytics license on top of the B2B Commerce license.

---

## Common Patterns

### Pattern 1: B2C Conversion Funnel Analysis via Business Manager

**When to use:** When the business needs to understand where visitors drop off between site entry and order placement (e.g., high cart-add rate but low checkout completion).

**How it works:**
1. Log in to Business Manager (`https://<your-instance>.demandware.net/on/demandware.store/Sites-Site/default/ViewApplication-DisplayPage`).
2. Navigate to **Reports & Dashboards** (left navigation or Administration menu).
3. Select the **Conversion** dashboard.
4. Set the date range (Business Manager defaults to the last 30 days).
5. Filter by Site (business unit) if multi-site.
6. Read the funnel: Sessions → Visits with Cart Add → Visits with Checkout Start → Orders Placed.
7. Calculate step-over-step conversion rates: `(Next Step / Previous Step) × 100`.
8. Export to CSV (max 1,000 rows) or use the SFTP feed for row counts above that threshold.

**Why not standard Salesforce Reports:** Standard Salesforce reports query the CRM database. B2C Commerce runs on a separate infrastructure and does not write storefront session, cart, or order data to the CRM database unless an explicit integration (e.g., Order Management) syncs records back.

### Pattern 2: B2B Commerce Cart Abandonment via SOQL

**When to use:** When the business wants to identify open carts that were never converted to orders, to power re-engagement campaigns or measure abandonment rate, without paying for a CRM Analytics license.

**How it works:**

Query active carts older than a threshold (commonly 24–72 hours) that have no associated order:

```soql
SELECT Id, Name, AccountId, Account.Name, OwnerId,
       CreatedDate, LastModifiedDate,
       TotalAmount, TotalProductCount,
       WebStore.Name
FROM WebCart
WHERE Status = 'Active'
  AND CreatedDate < LAST_N_DAYS:3
ORDER BY CreatedDate ASC
LIMIT 2000
```

To get abandonment rate: divide the count of carts where `Status = 'Active'` and older than threshold by total carts created in the same window.

For richer analysis join to CartItem:

```soql
SELECT WebCartId, Product2Id, Product2.Name,
       Quantity, SalesPrice, TotalPrice
FROM CartItem
WHERE WebCartId IN (
    SELECT Id FROM WebCart
    WHERE Status = 'Active'
      AND CreatedDate < LAST_N_DAYS:3
)
```

**Why not the Conversion dashboard:** B2B Commerce on Core does not have a Conversion dashboard. Business Manager is the B2C Commerce portal; it does not surface B2B Commerce on Core data.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| B2C Commerce conversion funnel, session metrics, or storefront KPIs | Business Manager Reports & Dashboards > Conversion or Revenue dashboard | This is the native, authoritative surface for B2C Commerce analytics |
| B2C Commerce per-SKU product export with 1,000+ rows | SFTP Data Feed from Business Manager | CSV export is hard-capped at 1,000 rows |
| B2B Commerce cart abandonment (no CRM Analytics license) | SOQL on WebCart WHERE Status = 'Active' + date threshold | B2B Commerce data lives in the CRM platform as native objects; SOQL is always available |
| B2B Commerce full analytics dashboards (licensed) | CRM Analytics B2B Commerce template (bi_template_b2bcommerce) | Productized; auto-provisions datasets and pre-built dashboards |
| Combined B2C and CRM data (e.g., orders + customer lifetime value) | External data pipeline: SFTP feed + Salesforce Data Export → warehouse → BI tool | No native cross-platform join; requires custom integration |
| Quick executive KPI view for a B2C site | Business Manager > Revenue dashboard + date filter | Fastest path; no SOQL, no license, built-in |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the Commerce platform.** Confirm whether the org uses B2C Commerce (SFCC/Business Manager) or B2B Commerce on Core (Lightning Experience, WebStore object). They are different products with different analytics approaches. Do not assume.
2. **Route to the correct analytics surface.** For B2C: direct the user to Business Manager > Reports & Dashboards. For B2B without CRM Analytics: confirm the target metric and write the appropriate SOQL query against WebCart, CartItem, or OrderSummary. For B2B with CRM Analytics: check whether `bi_template_b2bcommerce` is installed.
3. **Apply date range and site filters.** In Business Manager, explicitly set the date range and business unit filter before reading any metric. Default date ranges vary and can be misleading if left at the UI default.
4. **Check the row limit before exporting.** If the user needs more than 1,000 rows from Business Manager, switch to the SFTP Data Feed path or advise on the OCAPI/Commerce API reporting endpoints.
5. **Validate SOQL results for B2B.** For cart abandonment queries, confirm the threshold date window with the business (24h? 72h? 7 days?), and confirm whether `Status = 'PendingDelete'` carts should be included or excluded. Test the query in Developer Console or VS Code Salesforce Extension.
6. **Document the metric definition.** Conversion rate, abandonment rate, and AOV have no single universal definition — confirm numerator/denominator with the stakeholder before publishing numbers.
7. **Review data freshness.** Business Manager dashboards are near-real-time with a 15–60 minute lag. SOQL reflects the live database. Set stakeholder expectations on freshness before scheduling reports.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed whether the org is on B2C Commerce (SFCC) or B2B Commerce on Core — do not assume
- [ ] Verified legacy Business Manager Analytics is not being referenced (retired January 1, 2021)
- [ ] Checked CSV export row count — if >1,000 rows needed, SFTP feed path is documented
- [ ] For B2B SOQL queries: confirmed Status filter values and date threshold with the business
- [ ] Metric definitions (conversion rate, abandonment rate, AOV) agreed with stakeholder
- [ ] Data freshness expectations set (Business Manager: 15–60 min lag; SOQL: live)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **B2C Commerce data is not in the CRM database** — B2C Commerce runs on a separate SaaS infrastructure. Running SOQL or standard Salesforce Reports against an org that uses B2C Commerce will return zero commerce data unless an explicit integration (e.g., B2C Commerce Connector or Order Management) has been configured to sync orders back into the CRM. The Business Manager Reports & Dashboards app is the only native surface for B2C storefront analytics.
2. **Legacy Business Manager Analytics was retired January 1, 2021** — Older documentation, blog posts, and Trailhead modules may reference "Business Manager Analytics" (the older module). That module is retired. The current product is the "Reports and Dashboards" app inside Business Manager, which has a different UI and different capabilities.
3. **CSV export hard cap at 1,000 rows** — Every export from Business Manager is capped at 1,000 rows. This limit cannot be raised by configuration. Organizations with large catalogs or high-volume sites who need per-SKU or per-session granularity must use the SFTP Data Feed or the Commerce API.
4. **B2B Commerce has no native analytics UI** — B2B Commerce on Core ships with no built-in conversion funnel or cart analytics dashboard. The CRM Analytics B2B Commerce template requires a separate CRM Analytics license. Without it, all analytics must be derived from SOQL or custom reporting on WebCart, CartItem, and related objects.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Business Manager navigation path | Step-by-step path to the correct dashboard for the requested metric |
| SOQL query (B2B cart abandonment) | Parameterized SOQL query against WebCart and CartItem with configurable date threshold |
| Decision table | Routing guide: B2C vs B2B, licensed vs unlicensed, small vs large data volume |
| Metric definition log | Agreed numerator/denominator definitions for conversion rate, abandonment rate, AOV |

---

## Related Skills

- `architect/b2b-vs-b2c-architecture` — use when the platform choice itself is still being decided; this skill picks up once the platform is confirmed and analytics are needed
- `admin/crm-analytics-app-creation` — use when CRM Analytics is licensed and the B2B Commerce template needs to be provisioned or customized
- `data/analytics-external-data` — use when Commerce data needs to be pushed into CRM Analytics via the External Data API from an SFTP feed or warehouse
