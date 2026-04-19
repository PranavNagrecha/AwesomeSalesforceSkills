# Gotchas — SOQL Relationship Queries

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: getSObjects() Returns null, Not an Empty List

**What happens:** When a parent record has no related child records matching the subquery, calling `getSObjects('Contacts')` returns `null`. Iterating a `null` reference in an enhanced `for` loop does not silently skip — it throws a `NullPointerException` that bubbles up as an unhandled exception in triggers or surfaces as a 500 in Visualforce/Aura controllers.

**When it occurs:** Any time a parent record legitimately has zero children, or when the subquery filter condition (`WHERE IsEmailBounced = false`) excludes all child rows, the relationship result is `null` rather than an empty list.

**How to avoid:** Always guard before iterating:

```apex
List<SObject> rows = acc.getSObjects('Contacts');
if (rows == null) continue; // or return, depending on context
for (SObject row : rows) { ... }
```

Never rely on `rows != null && !rows.isEmpty()` being equivalent — just use a single null check.

---

## Gotcha 2: Custom __r vs Standard Relationship Name Confusion

**What happens:** Using the object API name (`My_Custom_Child__c`) instead of the child relationship name (`My_Custom_Children__r`) inside a subquery causes a compile-time parse error: `No such column 'My_Custom_Child__c' on entity 'Account'`. Using the wrong name in `getSObjects()` at runtime throws a `System.SObjectException`.

**When it occurs:** Most common when developers copy a flat SOQL query and try to embed it as a subquery, or when a custom object's plural label differs from its singular API name.

**How to avoid:** Look up the child relationship name on the parent object in Setup > Object Manager > [Parent Object] > Fields & Relationships > [Lookup Field] > Child Relationship Name. That exact value (with `__r` appended for custom) is what goes in both the SOQL subquery parentheses and the `getSObjects()` string argument. Standard objects use the registered child relationship name visible in the Schema Explorer — e.g., `Contacts`, `Opportunities`, `Cases`.

---

## Gotcha 3: Subquery Row Limits Are Separate — But the Outer Limit Still Applies

**What happens:** Developers assume the 50,000 outer query row limit is per object, so they expect to retrieve 50,000 Accounts × many Contacts each. In practice the total row count across all records in the result set — outer rows plus all inner subquery rows — must not exceed 50,000. A query returning 10,000 Accounts each with 10 Contacts already hits the limit.

**When it occurs:** Large data volume orgs where parent record counts are high and each parent has many children.

**How to avoid:** Add `LIMIT` clauses to subqueries to cap child rows per parent. Process parents in chunks (via batch or chunked SOQL) rather than loading the whole dataset in one call. Monitor with `Limits.getQueryRows()` in tests.

---

## Gotcha 4: Bulk API Does Not Support Parent-to-Child Subqueries

**What happens:** SOQL with subqueries works in synchronous Apex, anonymous execution, and the standard REST API. When the same query string is used in a Bulk API job (e.g., via `Database.BatchQueryLocator` configured for Bulk API mode, or an external ETL tool using the Bulk API), Salesforce rejects the query at runtime with an error.

**When it occurs:** Batch Apex that calls `Database.getQueryLocator()` with a subquery and is executed by the platform's Bulk API executor path, or external tools (Data Loader, MuleSoft Bulk connector) using Bulk API mode.

**How to avoid:** For Bulk API code paths, issue a flat query for the parent records and a separate query for the child records using a parent ID filter. Join them in memory in Apex.

---

## Gotcha 5: Cross-Object Formula Fields Are Not Filterable in WHERE

**What happens:** A formula field on Contact that references `Account.Industry` (e.g., `Account_Industry_Formula__c`) cannot be used in a WHERE clause. Salesforce throws a `SOQL exception: field 'Account_Industry_Formula__c' can not be filtered in a WHERE clause` error at runtime.

**When it occurs:** When a developer tries to filter on a cross-object formula to avoid typing the dot-notation path, especially when the formula was created for display purposes.

**How to avoid:** Use the direct dot-notation traversal in the WHERE clause: `WHERE Account.Industry = 'Technology'`. Reserve formula fields for display and formula-based calculations, not query filtering.

---

## Gotcha 6: TYPEOF Is a Developer Preview Feature

**What happens:** `TYPEOF` syntax is documented in the Apex and SOQL Developer Guides but is flagged as a developer preview feature. It is not supported in all query execution contexts and may not be enabled in all orgs or API versions.

**When it occurs:** Deploying a class with a `TYPEOF` query to a production org where the feature has not been enabled, or using `TYPEOF` in a Batch Apex query locator.

**How to avoid:** Validate `TYPEOF` queries in a scratch org against the same API version as production before deploying. Check the current release notes for the GA status of `TYPEOF` in your Salesforce version. As a fallback, query `WhatId` alone, then use a separate `WHERE Id IN` query per object type using `getSObjectType()` grouping.
