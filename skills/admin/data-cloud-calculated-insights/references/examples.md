# Examples — Data Cloud Calculated Insights

## Example 1: Customer Lifetime Value and 90-Day Purchase Count

**Scenario:** A retail brand wants to segment high-value customers by total lifetime spend and recent purchase frequency for a loyalty upgrade campaign.

**Problem:** Without persisted metrics, every segment refresh re-aggregates purchase history from the raw `SalesOrder` DMO at query time. This slows segment execution and cannot produce a single, audit-auditable metric value per customer that activation teams can report on.

**Solution:**

Before creating the insight, the team locks the following design:

| API Name | Type | Business Definition |
|---|---|---|
| `customer_id` | Text | Unified Individual ID (dimension) |
| `total_lifetime_spend` | Decimal | SUM of all order totals, all time |
| `purchase_count_90d` | Integer | COUNT of orders in the last 90 days |
| `avg_order_value_12m` | Decimal | AVG order total over last 12 months |

SQL authored in the Calculated Insights editor:

```sql
SELECT
    soi.unified_id__c                                AS customer_id,
    SUM(soi.order_total__c)                          AS total_lifetime_spend,
    COUNT(CASE WHEN soi.order_date__c >= DATEADD(DAY, -90, CURRENT_DATE)
               THEN soi.order_id__c END)             AS purchase_count_90d,
    AVG(CASE WHEN soi.order_date__c >= DATEADD(DAY, -365, CURRENT_DATE)
             THEN soi.order_total__c END)            AS avg_order_value_12m
FROM SalesOrderItem__dlm soi
GROUP BY soi.unified_id__c
```

Schedule: 24 hours. After the first successful run, `total_lifetime_spend`, `purchase_count_90d`, and `avg_order_value_12m` appear as filterable measure fields on the Unified Individual object in Segment Builder.

**Why it works:** The GROUP BY on `unified_id__c` (the dimension) aligns the insight output to Unified Individual records. Using `CASE WHEN` for the windowed aggregates (90-day count, 12-month average) in a single SQL pass avoids multiple insight definitions for related metrics and keeps the org well below its 300-insight cap.

---

## Example 2: Engagement Score Dimension for Email Personalization

**Scenario:** A B2B company wants to score each contact by email engagement tier (High / Medium / Low / Unengaged) so that activation targets can suppress unengaged contacts and personalize content for high-engagement ones.

**Problem:** Engagement tier cannot be stored as a segment filter — it needs to be a persistent named field on the Unified Profile so that multiple downstream activations can reference the same computed value without each activation re-deriving the tier logic.

**Solution:**

Design phase locks:

| API Name | Type | Business Definition |
|---|---|---|
| `contact_id` | Text | Unified Individual ID (dimension) |
| `email_opens_30d` | Integer | COUNT of email open events in last 30 days |
| `email_clicks_30d` | Integer | COUNT of email click events in last 30 days |
| `engagement_score` | Decimal | Weighted score: (opens * 1) + (clicks * 3) |

SQL:

```sql
SELECT
    e.contact_id__c                                              AS contact_id,
    COUNT(CASE WHEN e.event_type__c = 'email_open'
               AND e.event_date__c >= DATEADD(DAY, -30, CURRENT_DATE)
               THEN e.event_id__c END)                          AS email_opens_30d,
    COUNT(CASE WHEN e.event_type__c = 'email_click'
               AND e.event_date__c >= DATEADD(DAY, -30, CURRENT_DATE)
               THEN e.event_id__c END)                          AS email_clicks_30d,
    (COUNT(CASE WHEN e.event_type__c = 'email_open'
                AND e.event_date__c >= DATEADD(DAY, -30, CURRENT_DATE)
                THEN e.event_id__c END) * 1.0)
    + (COUNT(CASE WHEN e.event_type__c = 'email_click'
                  AND e.event_date__c >= DATEADD(DAY, -30, CURRENT_DATE)
                  THEN e.event_id__c END) * 3.0)                AS engagement_score
FROM EmailEngagementEvent__dlm e
GROUP BY e.contact_id__c
```

Schedule: 12 hours (email campaigns send daily; 12-hour freshness is adequate).

Downstream segment filters then use `engagement_score >= 10` for High, `3–9` for Medium, `1–2` for Low, and `0` for Unengaged. Activation targets reference these segment definitions directly.

**Why it works:** By computing `engagement_score` as a single Decimal measure, the downstream segment logic stays simple (range filters) rather than duplicating the weighting formula in every segment definition. The 12-hour cadence means that contacts who engage with a morning email campaign are reflected in the score before the afternoon send batch runs.

---

## Anti-Pattern: Creating an Insight to Test Naming, Then Trying to Rename It

**What practitioners do:** A developer creates a Calculated Insight with a placeholder API name like `test_metric_v1` during development, plans to rename it to `total_purchases` before production use, and only discovers the immutability constraint after go-live.

**What goes wrong:** The platform does not allow renaming measure API names after creation. The developer must delete `test_metric_v1` — losing any historical values accumulated during the testing period — and recreate the insight as `total_purchases`. If downstream segment filters or activation configurations reference the old API name, they break and must be updated.

**Correct approach:** Treat Calculated Insight creation as a one-way door. Use the design checklist in SKILL.md to finalize all API names before saving. If exploratory testing is needed, delete test insights immediately after validation and before any downstream references are established.
