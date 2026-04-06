# Gotchas — Product Catalog Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Standard PricebookEntry Must Exist Before Any Custom PricebookEntry — No Bypass

**What happens:** When you attempt to insert a PricebookEntry referencing a custom Pricebook2 for a product that has no existing PricebookEntry in the Standard Pricebook, Salesforce immediately throws a `FIELD_INTEGRITY_EXCEPTION` with the message: `pricebook entry in standard price book required before this entry can be created`. The insert is rejected — no record is created.

**When it occurs:** Any time a custom PricebookEntry is inserted (via UI, Data Loader, Bulk API 2.0, Apex, or REST API) before the corresponding Standard PricebookEntry for the same Product2. Most commonly hit during bulk catalog loads when the load sequence is wrong, or when custom PBEs are inserted programmatically in Apex without first inserting the Standard PBE in the same or a prior transaction.

**How to avoid:** Always follow the load sequence: Product2 → Standard PBE → custom Pricebook2 → custom PBE. In Apex, insert Standard PBEs in one DML statement and custom PBEs in a separate DML statement after the standard insert. In bulk load pipelines, use separate Bulk API jobs for Standard PBEs and custom PBEs with a verification step between them.

---

## Gotcha 2: UseStandardPrice = true and UnitPrice Are Mutually Exclusive

**What happens:** Setting `UseStandardPrice = true` on a PricebookEntry and also providing a non-null `UnitPrice` value causes an immediate DML error. The platform rejects the combination because `UseStandardPrice = true` signals that the price is inherited from the Standard Pricebook — an additional explicit price would be contradictory.

**When it occurs:** Most commonly during bulk CSV loads where the template includes a `UnitPrice` column for all rows. Rows intended to inherit the standard price have `UseStandardPrice = true` but also carry a price value in the shared `UnitPrice` column. The Bulk API processes them and fails those rows with a field error.

**How to avoid:** Partition your custom PBE CSV into two separate files: one for entries with `UseStandardPrice = false` (include `UnitPrice` column), and one for entries with `UseStandardPrice = true` (omit `UnitPrice` column entirely or ensure the column is blank for all rows). Never use a single combined CSV with mixed `UseStandardPrice` values and a shared `UnitPrice` column.

---

## Gotcha 3: The Standard Pricebook ID Is Org-Specific — Never Hardcode It

**What happens:** The Pricebook2 record with `IsStandard = true` has a different ID in every Salesforce org. Hardcoding the Standard Pricebook ID in a CSV file, a metadata record, an Apex class constant, or a configuration value means the load or code works in one org but fails with an invalid cross-reference error in any other org — including when a sandbox is refreshed, when deploying to production, or when running in a scratch org.

**When it occurs:** During migrations where the analyst queries the Standard Pricebook ID from a sandbox and hardcodes it into the production load CSV. Also common in Apex code where a developer copies the ID from the UI into a static variable. Also occurs in test code that queries the Standard PB via SOQL (see Gotcha 4).

**How to avoid:** Always query the Standard Pricebook ID at runtime: `SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1`. In Apex tests, use `Test.getStandardPricebookId()` instead of querying. In bulk load pipelines, add a pre-load step that queries the ID from the target org and injects it into the CSV before submission.

---

## Gotcha 4: Apex Tests Cannot Query the Standard Pricebook Without SeeAllData

**What happens:** In an Apex unit test, `SELECT Id FROM Pricebook2 WHERE IsStandard = true` returns zero rows unless the test class is annotated with `@isTest(SeeAllData=true)`. Without it, Apex tests run in an isolated data context where the Standard Pricebook is not visible. Any code that relies on the queried Standard Pricebook ID receives null and either throws a NullPointerException or fails with a required field error on PricebookEntry.

**When it occurs:** Apex developer writes a test for a method that creates products and pricebook entries. The method queries the Standard Pricebook ID, but in test context it returns null. The test fails with a confusing error — often a required field missing on PricebookEntry, not an obvious "standard pricebook not found" message.

**How to avoid:** Use `Test.getStandardPricebookId()` in all Apex tests that need the Standard Pricebook ID. This method is designed for test contexts and returns the correct ID without needing `SeeAllData=true`. Never add `SeeAllData=true` to work around this — it breaks test isolation and produces flaky tests that depend on org data.

---

## Gotcha 5: Product2Id + Pricebook2Id Combination Must Be Unique Per PricebookEntry

**What happens:** Attempting to insert a second PricebookEntry with the same `Product2Id` and `Pricebook2Id` combination as an existing entry results in a duplicate record error: `DUPLICATE_VALUE: duplicate value found`. There can be exactly one PricebookEntry per product per pricebook.

**When it occurs:** During re-loads when a previous partial load inserted some Standard PBEs and the retry job re-inserts them using insert instead of upsert. Also occurs when price update logic accidentally creates new PricebookEntry records instead of updating existing ones.

**How to avoid:** Always use upsert logic for PricebookEntry loads. Query existing PricebookEntries for the target products and pricebooks before loading; route existing records to an update job and new records to an insert job. In multi-currency orgs, update the `CurrencyIsoCode` on existing PBE records rather than creating parallel PBE records for the same product/pricebook pair.

---

## Gotcha 6: Inactive PricebookEntry Records Are Not Visible in the UI Product Selector but Remain Queryable

**What happens:** Setting `PricebookEntry.IsActive = false` removes the entry from the Opportunity Line Item product selector in the UI. However, SOQL queries without a `WHERE IsActive = true` filter still return the inactive PBE record. Apex code that retrieves PricebookEntries without filtering on `IsActive` will include inactive entries, potentially surfacing retired products in API responses, custom LWC components, or integration payloads.

**When it occurs:** After a product retirement workflow that sets `IsActive = false` on both Product2 and PricebookEntry. Downstream integrations or custom components that query PricebookEntry without `WHERE IsActive = true` continue to show retired products.

**How to avoid:** Always add `WHERE IsActive = true` to PricebookEntry SOQL queries in production code. When retiring a product, set `IsActive = false` on both `Product2` and all associated `PricebookEntry` records across all pricebooks — not just the Standard PBE.
