# Examples — Data Cloud Data Streams

## Example 1: Unifying CRM Contacts with Commerce Platform Customer Records

**Context:** A retailer has Salesforce CRM with 500,000 Contact records and a separate e-commerce platform that exports nightly customer CSV files to S3. The goal is to unify these two populations in Data Cloud so that Marketing Cloud journeys can target a single consolidated profile.

**Problem:** After setting up both the CRM connector and the S3 connector, the identity resolution ruleset creation button in Data Cloud remains inactive. The commerce stream was mapped only to the Individual DMO (with `customer_id` → `Individual ID`, `first_name` → `First Name`, `last_name` → `Last Name`), but no Contact Point mapping was created for the commerce stream's email column.

**Solution:**

Open the S3 data stream mapping UI. Add a new object mapping for Contact Point Email. Map:

```
Source field: email          → DMO field: Contact Point Email > Email Address
Source field: customer_id    → DMO field: Contact Point Email > Individual ID (foreign key)
```

After saving the mapping and re-running the DLO population job, navigate to Identity Resolution. The ruleset creation button becomes active. Create a ruleset with a single match rule: Contact Point Email `Email Address` (exact match). Run the ruleset. Unified Individual records are now created wherever a CRM Contact and a commerce customer share the same email address.

**Why it works:** The Contact Point Email mapping gives identity resolution a concrete channel-specific address to match on across both data streams. The Individual DMO alone tells Data Cloud that a person exists, but the Contact Point DMO tells it how to identify that person across systems. Both are required.

---

## Example 2: Ingestion API Upsert for Loyalty Transaction Events

**Context:** A loyalty program backend pushes transaction events (points earned, redemptions) to Data Cloud every few minutes via the Ingestion API. The engineering team wants to ensure that if the same transaction is sent twice (due to retry logic), it is not duplicated in Data Cloud.

**Problem:** The initial integration uses `append` mode. A network retry causes the same 50 transactions to be posted twice, resulting in duplicate records in the loyalty transaction DLO and inflated point balances in Calculated Insights.

**Solution:**

Change the Ingestion API call to use `upsert` mode and ensure each transaction record has a stable, unique `transaction_id` that serves as the DLO primary key:

```http
POST /api/v1/ingest/sources/loyalty_transactions_v1/LoyaltyTransaction
Authorization: Bearer {oauth_token}
Content-Type: application/json

{
  "data": [
    {
      "transaction_id": "TXN-20240315-001234",
      "customer_id": "C-88821",
      "points_earned": 150,
      "transaction_date": "2024-03-15T14:23:00Z",
      "store_id": "STORE-42"
    }
  ],
  "mode": "upsert"
}
```

With `upsert` mode and `transaction_id` as the primary key, re-submitting the same payload overwrites the existing record rather than creating a duplicate.

**Why it works:** Upsert semantics in the Ingestion API behave like a merge: if a record with the specified primary key already exists in the DLO, it is updated; if it does not exist, it is inserted. This makes the integration idempotent and safe under retry conditions. Append mode should only be used for truly immutable event logs where deduplication is handled upstream.

---

## Example 3: Calculated Insight for 90-Day Purchase Frequency

**Context:** A segment builder needs to filter Unified Individual profiles by customers who have made 3 or more purchases in the last 90 days. This metric does not exist natively in the mapped DMOs.

**Problem:** The segment filter editor does not expose raw DLO fields for aggregation. Attempting to build a segment filter directly against the `PurchaseEvent` DMO row count fails because segment filters require scalar attribute values, not aggregations.

**Solution:**

Create a Calculated Insight in Data Cloud that computes the metric:

```sql
SELECT
    ui.Individual_Id__c         AS individual_id,
    COUNT(pe.transaction_id)    AS purchase_count_90d
FROM
    UnifiedIndividual__dlm ui
    JOIN PurchaseEvent__dlm pe
      ON ui.Individual_Id__c = pe.individual_id__c
WHERE
    pe.transaction_date__c >= DATEADD(day, -90, CURRENT_DATE())
GROUP BY
    ui.Individual_Id__c
```

Save and schedule the Calculated Insight to run daily. In the segment builder, the `purchase_count_90d` field is now available as a filterable attribute on the Unified Individual. Apply the filter `purchase_count_90d >= 3`.

**Why it works:** Calculated Insights pre-aggregate metrics on a schedule and attach the result as a scalar attribute to the Unified Individual. The segment builder can then use these scalar values in filter conditions without performing live aggregation at query time.

---

## Anti-Pattern: Mapping DLO Primary Key to Party Identification ID

**What practitioners do:** When configuring a Party Identification DMO mapping for an external loyalty ID, the practitioner maps the source `loyalty_id` field directly to the `Party Identification ID` field on the Party Identification DMO.

**What goes wrong:** `Party Identification ID` is an internal Data Cloud system-generated key, not a field intended for external IDs. Mapping an external value into this field causes the DMO to behave unpredictably: identity resolution may fail to match records, or records may be overwritten unexpectedly when the system regenerates internal IDs.

**Correct approach:** Map `loyalty_id` to the `Identification Number` field on the Party Identification DMO. Map the source person primary key to the `Individual ID` foreign key field. The `Party Identification ID` field should never be populated from an external source.
