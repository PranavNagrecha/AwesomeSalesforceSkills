# Gotchas — Commerce Analytics Data

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: B2C Commerce Analytics Are in a Separate SaaS Realm — Not in the CRM

**What happens:** Standard Salesforce reports, SOQL queries, and Data Export will return zero commerce data for B2C Commerce (SFCC) storefronts, even when the org is fully integrated with a B2C Commerce instance. This causes teams to diagnose phantom "integration failures" when the data is simply in a different system.

**When it occurs:** Any time a practitioner opens Lightning Experience and tries to report on B2C storefront orders, sessions, cart events, or conversion metrics using the standard Salesforce toolset.

**How to avoid:** B2C Commerce analytics are accessed exclusively via the **Business Manager Reports & Dashboards** app, which lives inside the Business Manager administration portal at `https://<instance>.demandware.net`. This surface is separate from the Salesforce CRM. Document this architectural boundary clearly with any stakeholder who expects "everything is in Salesforce."

---

## Gotcha 2: CSV Export in Business Manager is Hard-Capped at 1,000 Rows

**What happens:** Every dashboard export in Business Manager produces a CSV file with at most 1,000 rows. For aggregate dashboard views (one row per day or per dashboard KPI), this is usually sufficient. For row-level product, session, or order exports — especially on sites with large catalogs or high traffic — the export silently truncates at 1,000 rows with no error message. The analyst believes they have the full dataset and makes decisions on incomplete data.

**When it occurs:** Product Performance exports on catalogs with more than 1,000 active SKUs; per-session or per-order granular exports on high-volume sites; any attempt to export raw event data for offline analysis.

**How to avoid:** For exports requiring more than 1,000 rows, use the **Business Manager SFTP Data Feed** (Administration > Site Development > SFTP Data Feed). This delivers raw CSV or XML files to an external server on a scheduled basis with no row cap. Alternatively, use the Commerce API reporting endpoints for programmatic access.

---

## Gotcha 3: Legacy Business Manager Analytics Was Retired January 1, 2021

**What happens:** Documentation written before 2021 (including some Trailhead modules, partner guides, and blog posts) references "Business Manager Analytics" — an older analytics module with a different navigation path and feature set. That module was retired. Practitioners following those instructions will not find the referenced menu items and may conclude their instance is misconfigured.

**When it occurs:** When following older documentation or when a legacy team member guides based on pre-2021 experience.

**How to avoid:** Verify that instructions reference the current **Reports and Dashboards** app. The current path is: Business Manager left navigation > Reports & Dashboards (or Merchant Tools > Reports & Dashboards depending on the site configuration). Any reference to the standalone "Analytics" module or the older chart-heavy UI is outdated.

---

## Gotcha 4: B2B Commerce on Core Has No Native Analytics UI

**What happens:** Practitioners looking for a built-in "analytics" or "reports" section inside a B2B Commerce on Core storefront administration find nothing equivalent to Business Manager's dashboards. There is no native conversion funnel UI, no cart abandonment report, and no product performance dashboard in the standard B2B Commerce product.

**When it occurs:** When scoping analytics for a B2B Commerce on Core implementation without CRM Analytics in the license stack.

**How to avoid:** For B2B Commerce analytics without CRM Analytics, use SOQL directly against WebCart, CartItem, OrderSummary, and related objects. For a productized dashboard solution, confirm whether CRM Analytics is licensed and whether the `bi_template_b2bcommerce` managed package template is installed. Document this gap in the project scope explicitly — it is a licensing conversation, not a configuration gap.

---

## Gotcha 5: WebCart Status Values and Abandonment Definition

**What happens:** SOQL queries for "abandoned carts" using B2B Commerce on Core often use incorrect Status filter values, leading to over-counting or under-counting. `Status = 'Active'` does not distinguish between a cart that is actively being used right now and one that was last touched 90 days ago. `Status = 'PendingDelete'` represents carts queued for system deletion — including some that were abandoned.

**When it occurs:** When writing abandonment SOQL queries without understanding the full WebCart Status picklist lifecycle.

**How to avoid:** Use a combination of Status and CreatedDate (or LastModifiedDate) thresholds. The standard abandonment definition is:
- `Status = 'Active'` (not yet converted)
- `CreatedDate < LAST_N_DAYS:<threshold>` (old enough to be considered abandoned, not just in progress)
- Optionally exclude carts with very recent `LastModifiedDate` (buyer is still active)

Agree on the time threshold (24h, 48h, 72h, 7 days) with the business before writing the query. Document the agreed definition in the metric definition log.

---

## Gotcha 6: Business Manager Dashboard Data Lag Is Not Real-Time

**What happens:** Business Manager dashboards are described as "near-real-time" but reflect a data lag of typically 15–60 minutes. During peak traffic events (major promotions, flash sales), this lag can extend. Teams monitoring conversion during a live launch event see stale metrics and make premature intervention decisions.

**When it occurs:** Real-time monitoring scenarios, live event war rooms, or intra-hour reporting against a high-traffic site.

**How to avoid:** Set stakeholder expectations explicitly: Business Manager is not a real-time monitoring tool. For live event monitoring, consider Commerce API endpoints that surface more current data, or configure alerting at the infrastructure level (CDN logs, order management webhooks). Document the expected lag in the analytics runbook.
