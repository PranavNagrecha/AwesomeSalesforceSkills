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

## Gotcha 6: TYPEOF Is SELECT-Only — Use `.Type` to Filter

**What happens:** `TYPEOF` is generally available (since API version 46.0, Summer '19 — the Developer Preview label applied only to earlier versions), so it needs no "is it enabled?" caveat. The real trap is that it is a **SELECT-clause-only** projection. Per the SOQL reference it is rejected in `WHERE`, in aggregate/`COUNT()` and `GROUP BY`/`HAVING` queries, in Bulk API SOQL, in Streaming API PushTopics, and in the SELECT list of a semi-join subquery. A query that tries to *filter* on a polymorphic type with `TYPEOF` fails to parse.

**When it occurs:** Attempting `WHERE TYPEOF ...`, running a `TYPEOF` query through the Bulk API, or expecting `TYPEOF` to work inside an aggregate/`GROUP BY` query.

**How to avoid:** Project per-type fields with `TYPEOF` in the SELECT clause only. To **filter** rows by polymorphic type, use the `.Type` qualifier instead — it compares against a plain string, has no API-version floor, and is the only legal option in the contexts above: `SELECT Id FROM Event WHERE What.Type IN ('Account', 'Opportunity')`. Once pinned to a single type, that type's fields are reachable by dot notation (`SELECT Id, Owner.Name FROM Event WHERE Owner.Type = 'User'`). Remember that a `.Type` filter silently excludes rows of other types rather than null-padding them.

---

## Gotcha 7: SOQL Reserved Words Are Rejected as Alias Names

**What happens:** Alias notation lets you name an object in the FROM clause (`FROM Contact c, c.Account a`) and reference it by that alias in SELECT and WHERE — an implicit join that filters on a parent without selecting its fields. But SOQL rejects its own reserved keywords as alias identifiers. A tempting short alias such as `in`, `or`, or `not` produces a parse error because it matches the reserved `IN`, `OR`, and `NOT` keywords.

**When it occurs:** Choosing terse, mnemonic aliases derived from an object's name (`Inventory__c in`, `Order or`), or generating aliases programmatically without screening them against the keyword list.

**How to avoid:** Screen every alias against the reserved list before using it: AND, ASC, DESC, EXCLUDES, FIRST, FROM, GROUP, HAVING, IN, INCLUDES, LAST, LIKE, LIMIT, NOT, NULL, NULLS, OR, SELECT, USING, WHERE, WITH. Single letters (`c`, `a`, `o`) and multi-letter tokens that aren't on the list are safe — `inv` instead of `in`, `ord` instead of `or`.
