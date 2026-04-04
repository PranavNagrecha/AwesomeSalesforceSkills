# Gotchas — SOQL Fundamentals

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Results Are Not Ordered Without ORDER BY

**What happens:** A SOQL query without an ORDER BY clause returns records in an unspecified order. The order may appear consistent in development sandboxes but silently change in production, after deployments, or after platform upgrades.

**When it occurs:** Any query without ORDER BY. Code that relies on `results[0]` being the "most recent" or "most relevant" record — without ORDER BY — will produce incorrect, hard-to-reproduce bugs in production. The SOQL and SOSL Reference states: "There's no guarantee of the order of results unless you use an ORDERBY clause in a query."

**How to avoid:** Always add ORDER BY when result order matters. Add a tiebreaker field (typically Id) when sorting by a non-unique field to ensure deterministic ordering:

```sql
SELECT Name, CreatedDate FROM Account ORDER BY CreatedDate DESC, Id DESC LIMIT 1
```

---

## Gotcha 2: OFFSET Maximum Is 2,000 Rows

**What happens:** Queries using OFFSET with a value greater than 2,000 raise a `NUMBER_OUTSIDE_VALID_RANGE` error at runtime, not at compile time. The error only appears when the query executes, so it can pass all tests if the test data set is small.

**When it occurs:** OFFSET-based pagination in Apex controllers, REST integrations, or any code that increments an offset based on page number. The bug surfaces only when a user navigates to page 41+ (with 50 records per page) or when the record set grows large enough.

**How to avoid:** For result sets larger than 2,000 rows, use cursor-based approaches instead of OFFSET:
- **SOAP API:** Use `queryMore()` with the query locator returned by the initial `query()` call.
- **REST API:** Follow the `nextRecordsUrl` in the response.
- **Apex Batch:** Use `Database.QueryLocator` in `start()` — this supports up to 50 million records.
- **Bulk API 2.0:** Use the `Sforce-Locator` header for result pagination.

---

## Gotcha 3: Aggregate Functions Cannot Use LIMIT Without GROUP BY

**What happens:** Queries like `SELECT MAX(CreatedDate) FROM Account LIMIT 1` produce a `MALFORMED_QUERY` error. This is a common attempt to simulate "get me the most recent record's field value" using an aggregate.

**When it occurs:** When a developer wants the min/max value of a field and tries to use LIMIT to restrict to one aggregate result. The pattern is natural in SQL where `SELECT MAX(col) FROM table LIMIT 1` is redundant but valid.

**How to avoid:** Use two different patterns depending on the need:

```sql
-- To get the MAX value of a field (no LIMIT allowed without GROUP BY):
SELECT MAX(CreatedDate) FROM Account

-- To get the most recently created Account record (full record, ORDER BY + LIMIT):
SELECT Id, Name, CreatedDate FROM Account ORDER BY CreatedDate DESC LIMIT 1

-- To aggregate with LIMIT, always add GROUP BY:
SELECT Name, MAX(CreatedDate) FROM Account GROUP BY Name LIMIT 5
```

---

## Gotcha 4: Custom Relationship Fields Use __r Not __c in Dot Notation

**What happens:** A developer traversing a custom lookup field `Parent__c` writes `Parent__c.Name` in a SOQL SELECT or WHERE clause. This produces a `MALFORMED_QUERY` error because `__c` references the field itself, not the relationship.

**When it occurs:** Any child-to-parent traversal of a custom lookup or master-detail field. The naming convention is easy to mix up because the field is stored with `__c` but the relationship is accessed with `__r`.

**How to avoid:** Always use `__r` for relationship traversal in SOQL:

```sql
-- WRONG: using __c for dot notation
SELECT Id, Parent_Account__c.Name FROM Child__c

-- CORRECT: using __r for relationship traversal
SELECT Id, Parent_Account__r.Name FROM Child__c

-- WRONG: WHERE clause with __c dot notation
WHERE Parent_Account__c.Industry = 'Technology'

-- CORRECT:
WHERE Parent_Account__r.Industry = 'Technology'
```

---

## Gotcha 5: FIELDS(ALL) Without LIMIT Causes Errors

**What happens:** `SELECT FIELDS(ALL) FROM Account` without a LIMIT clause causes either a `QUERY_TOO_LARGE` error (result set too many rows) or a `QUERY_TOO_COMPLICATED` error (too many fields expanded internally). The error is not a syntax error — it only appears at runtime when the org has enough records or fields.

**When it occurs:** Exploratory queries in Developer Console or Apex using `FIELDS(ALL)` or `FIELDS(CUSTOM)` without limiting row count. FIELDS(ALL) on objects with many fields (e.g., Account with 200+ fields) can also trigger `QUERY_TOO_COMPLICATED` because currency fields double the internal query length.

**How to avoid:** Always pair `FIELDS(ALL)` and `FIELDS(CUSTOM)` with LIMIT. Use `FIELDS(STANDARD)` (which does not require LIMIT) for objects where custom field count is low:

```sql
-- Safe: always add LIMIT with FIELDS(ALL) or FIELDS(CUSTOM)
SELECT FIELDS(ALL) FROM Account LIMIT 200
SELECT FIELDS(CUSTOM) FROM Account LIMIT 200

-- FIELDS(STANDARD) does not require LIMIT (standard field count is fixed)
SELECT FIELDS(STANDARD) FROM Contact
```
