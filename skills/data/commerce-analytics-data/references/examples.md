# Examples — Commerce Analytics Data

## Example 1: B2C Commerce Conversion Funnel Analysis

**Context:** A retail brand runs a B2C Commerce storefront on SFCC. The merchandising team reports that revenue is flat despite increased paid traffic. The analytics lead needs to identify where in the purchase funnel visitors are dropping off.

**Problem:** The team opens Lightning Experience and navigates to Reports, but finds no commerce-related data — no orders, no cart activity, no sessions. They also attempt a SOQL query against `Order` and `Cart` objects and return zero rows. They assume the tracking is broken.

**Solution:**

The commerce session and transaction data for B2C Commerce lives in Business Manager, not in the CRM. The analyst must log in to Business Manager directly:

1. Navigate to `https://<instance>.demandware.net/on/demandware.store/Sites-Site`
2. Select the target Site (business unit) from the site selector
3. Go to **Reports & Dashboards** in the left navigation
4. Open the **Conversion** dashboard
5. Set the date range to the analysis window (e.g., last 30 days)
6. Read the funnel steps and calculate step-over-step drop-off rates:

```
Funnel metric reading (example output from dashboard):

Sessions:                       120,000
Visits with cart add:            18,000   →  15.0% add-to-cart rate
Visits with checkout start:       9,500   →  52.8% cart-to-checkout rate
Orders placed:                    6,200   →  65.3% checkout-to-order rate

Overall session-to-order rate:    5.2%
```

To export the underlying data for further analysis in Excel/BI tool:
- Click **Export to CSV** on any dashboard panel
- Note: export is capped at 1,000 rows — sufficient for aggregate dashboard views but not for per-session or per-SKU row-level exports

**Why it works:** Business Manager Reports & Dashboards is the authoritative analytics surface for B2C Commerce. Session, cart, and order events are captured natively by the SFCC infrastructure and surfaced here — they do not flow to the CRM database unless an integration (e.g., Order Management) explicitly syncs them.

---

## Example 2: B2B Commerce Cart Abandonment SOQL Query

**Context:** A B2B manufacturer uses B2B Commerce on Core. The digital commerce team wants to build a weekly re-engagement campaign targeting buyers who added items to a cart but never placed an order in the past 7 days. They do not have CRM Analytics licensed.

**Problem:** There is no built-in B2B Commerce analytics dashboard. The team searches AppExchange but does not want to pay for CRM Analytics. They need a programmatic solution they can run from Apex or schedule via a Flow.

**Solution:**

Query WebCart for active carts created more than a defined number of days ago:

```soql
-- Step 1: Identify abandoned carts (active, older than 7 days)
SELECT
    Id,
    Name,
    AccountId,
    Account.Name,
    OwnerId,
    Owner.Name,
    CreatedDate,
    LastModifiedDate,
    TotalAmount,
    TotalProductCount,
    WebStore.Name
FROM WebCart
WHERE Status = 'Active'
  AND CreatedDate < LAST_N_DAYS:7
ORDER BY TotalAmount DESC NULLS LAST
LIMIT 2000
```

```soql
-- Step 2: Get line items for abandoned carts (for email personalization)
SELECT
    WebCartId,
    Product2Id,
    Product2.Name,
    Product2.ProductCode,
    Quantity,
    SalesPrice,
    TotalPrice,
    Type
FROM CartItem
WHERE Type = 'Product'
  AND WebCartId IN (
      SELECT Id
      FROM WebCart
      WHERE Status = 'Active'
        AND CreatedDate < LAST_N_DAYS:7
  )
ORDER BY WebCartId, TotalPrice DESC NULLS LAST
```

```soql
-- Step 3: Calculate abandonment rate for reporting
SELECT
    Status,
    COUNT(Id) CartCount,
    SUM(TotalAmount) TotalValue
FROM WebCart
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY Status
```

For the re-engagement campaign, the output of Step 1 and Step 2 can be loaded into a Marketing Cloud Journey or a Salesforce Campaign using Apex batch or a scheduled Flow.

**Why it works:** B2B Commerce on Core writes cart data as native Salesforce objects (WebCart, CartItem) within the same CRM database. Standard SOQL has full access to these objects with no special permissions beyond Commerce User or Admin access. The `Status = 'Active'` filter is the key — carts that converted have `Status = 'Closed'`; carts that were explicitly cleared have `Status = 'PendingDelete'`.

---

## Example 3: B2C Commerce Product Performance Export via SFTP Feed

**Context:** A B2C Commerce retailer with 50,000 SKUs wants a weekly product performance report showing units sold, revenue, and view-to-purchase rate per SKU. The Business Manager Products dashboard only exports 1,000 rows — insufficient for their catalog size.

**Problem:** The team keeps exporting the CSV from Business Manager and hitting the 1,000-row cap. They truncate their analysis to the top 1,000 products, missing long-tail catalog insights.

**Solution:**

Configure the Business Manager SFTP Data Feed to push raw order and analytics data to an external server:

1. In Business Manager, navigate to **Administration > Site Development > SFTP Data Feed**
2. Configure the feed endpoint (SFTP server hostname, port, credentials)
3. Select the data feed type: **Orders**, **Inventory**, or **Analytics** (depending on the metric needed)
4. Set the schedule (hourly, daily) and the target remote directory
5. Process the delivered files (CSV or XML) in the downstream BI tool or data warehouse

For view-to-purchase rate at SKU level, the Analytics feed includes impression and click events alongside order line items.

**Why it works:** The SFTP Data Feed bypasses the Business Manager UI export entirely and delivers the raw event-level or transaction-level data directly. There is no row cap on the SFTP feed. This is Salesforce's intended path for large-volume B2C Commerce analytics.

---

## Anti-Pattern: Running SOQL or Standard Reports to Pull B2C Commerce Data

**What practitioners do:** Attempt to find B2C Commerce orders, sessions, or cart data by running SOQL queries against `Order`, `OrderItem`, or custom objects in the CRM org, or by building standard Salesforce Reports expecting to see storefront activity.

**What goes wrong:** The queries return zero results. The practitioner concludes that tracking is broken, data is missing, or the integration is not configured — when in fact B2C Commerce data simply does not live in the CRM database by default. Time is wasted investigating a non-existent integration bug.

**Correct approach:** B2C Commerce storefront data is in Business Manager Reports & Dashboards. Use SOQL only for B2B Commerce on Core, where WebCart and CartItem are genuine CRM objects. If the business wants B2C Commerce data in the CRM (e.g., for unified customer profiles), that requires an explicit integration layer (B2C Commerce Connector, Order Management, or a custom pipeline from the SFTP feed).
