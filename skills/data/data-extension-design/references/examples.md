# Examples — Data Extension Design

## Example 1: Sendable DE for a Promotional Email Campaign

**Context:** A retail brand wants to send a weekly promotional email to a segment of customers. The marketing team needs to create a sendable Data Extension in Marketing Cloud that holds the subscriber list with personalization fields (first name, loyalty tier, last purchase date).

**Problem:** The team creates a DE with `EmailAddress` as the primary key and maps the Send Relationship to Email Address. Subscribers who change their email address lose their personalization history, and All Subscribers deduplication is inconsistent because some subscribers appear multiple times with different email addresses.

**Solution:**

```
DE Name: Weekly_Promo_Audience
Fields:
  - SubscriberKey   | Text(50)  | Primary Key | Required
  - EmailAddress    | Email     | Required
  - FirstName       | Text(50)
  - LoyaltyTier     | Text(20)
  - LastPurchaseDate | Date

Sendable: Yes
Send Relationship: SubscriberKey (DE field) → Subscriber Key (All Subscribers)
Data Retention: None (populated fresh each week by query activity)
```

AMPscript to use personalization at send time:
```
%%[
  SET @firstName = AttributeValue("FirstName")
  SET @tier = AttributeValue("LoyaltyTier")
]%%
Hello %%=v(@firstName)=%%, as a %%=v(@tier)=%% member...
```

**Why it works:** Mapping to `SubscriberKey` rather than `Email Address` ensures each subscriber is uniquely and stably identified. When subscribers change their email, the SubscriberKey remains the same and their history (suppression, preferences) is preserved. All Subscribers deduplication operates on SubscriberKey, so each subscriber appears exactly once.

---

## Example 2: Event Tracking DE with Composite PK and Row-Based Retention

**Context:** A company uses Marketing Cloud to track customer product view events for personalization. An Automation Studio process imports a nightly file of events — each row represents one product viewed by one customer on one date. The same customer can view multiple products; the same product can be viewed by multiple customers.

**Problem:** The team uses `EventID` (a GUID from the source system) as a single-field PK. When the source system regenerates GUIDs on re-export (a common pattern in ETL pipelines), every nightly import inserts duplicate rows because the PKs never match existing rows. The DE grows without bound and query activities begin timing out.

**Solution:**

```
DE Name: Customer_Product_Views
Fields:
  - CustomerKey     | Text(50)  | Primary Key | Required
  - ProductSKU      | Text(50)  | Primary Key | Required
  - ViewDate        | Date      | Primary Key | Required
  - ViewCount       | Number
  - LastViewTime    | Text(20)

Sendable: No (lookup/personalization use only)
Data Retention: Row-based, delete rows older than 90 days
ResetRetentionPeriodOnImport: true
Import Mode: Add and Update (upsert on composite PK)
```

**Why it works:** The composite PK of (CustomerKey, ProductSKU, ViewDate) is semantically unique — the same customer cannot view the same product on the same date more than once from a business perspective. Upsert on this composite PK means re-importing the same event updates the existing row rather than creating a duplicate. Row-based retention with reset-on-import keeps actively-imported rows alive for 90 days and automatically clears old data without manual cleanup.

---

## Anti-Pattern: Wide DE with No Indexing Strategy

**What practitioners do:** A marketing ops team consolidates all customer attributes into a single DE with 350+ fields, reasoning that having "one source of truth" simplifies AMPscript personalization. Non-PK fields like `SegmentCode`, `RegionCode`, and `ProductInterest` are used as WHERE clause filters in SQL query activities.

**What goes wrong:**

- Query activities filtering on `SegmentCode` or `RegionCode` (non-PK, non-indexed) perform full table scans across millions of rows.
- Automation Studio enforces a 30-minute query timeout. Queries against the wide DE start failing intermittently, then consistently.
- AMPscript `LookupRows` calls at send time are slow (adding seconds per email rendered), causing send timeouts on large batches.
- The DE schema exceeds 200 columns, causing general query degradation even on PK-filtered queries.

**Correct approach:**

1. Split the wide DE into purpose-built DEs: a core identity/contact DE (SubscriberKey + email + name), a segment membership DE (SubscriberKey + SegmentCode + ValidFrom), and a product interest DE (SubscriberKey + ProductInterest + Score).
2. Use SubscriberKey as the shared PK across all DEs to enable JOIN in SQL query activities.
3. Submit a Salesforce Support ticket to add custom indexes on `SegmentCode` and `RegionCode` in the segment DE before go-live, with documented row volume estimates.
4. Keep each DE under 50 columns where possible; only combine fields that are always queried together.
