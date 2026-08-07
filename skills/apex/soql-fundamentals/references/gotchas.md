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

## Gotcha 5: FIELDS(ALL) and FIELDS(CUSTOM) Are Not Available in Apex — Adding LIMIT Does Not Help

**What happens:** `SELECT FIELDS(ALL) FROM Account` is rejected in Apex, with or without a `LIMIT`. The keyword's *unbounded* forms — `FIELDS(ALL)` and `FIELDS(CUSTOM)` — are documented as "Not supported" for Apex (inline and dynamic) and for Bulk API 2.0. They are supported in REST, SOAP, and the CLI, but only when the result rows are limited: `LIMIT n where n <= 200`, or a `WHERE Id IN` list of up to 200 IDs. The *bounded* form `FIELDS(STANDARD)` is supported everywhere, including Apex, and needs no `LIMIT`.

The near-universal misreading is to treat the 200-row rule as the whole story and conclude that `FIELDS(ALL) ... LIMIT 200` is therefore legal in Apex. It is not: the row rule governs the contexts where the unbounded forms exist at all, and Apex is not one of them. A second, unrelated 200 in the same sentence makes this especially easy to garble — `LIMIT n <= 200` is a row cap, not a field cap.

**When it occurs:** Exploratory Apex ported from a Developer Console REST query or a `sf data query` CLI invocation, where the same query string genuinely worked. It also occurs when moving an Apex query into a Bulk API 2.0 job, which shares the Apex restriction.

Separately, and for a different reason: `QUERY_TOO_COMPLICATED` is a real `StatusCode` and can be returned when a query selects too many fields or has too many filter conditions — currency fields expand the internal query length. `QUERY_TOO_LARGE` is **not** a Salesforce status code; it does not appear in the API `StatusCode` enumeration. Violating the FIELDS() row rule where the unbounded forms *are* supported returns `MALFORMED_QUERY`.

**How to avoid:** In Apex, use `FIELDS(STANDARD)` (no `LIMIT` needed) or enumerate the fields you actually need. Reserve `FIELDS(ALL)` / `FIELDS(CUSTOM)` for REST, SOAP, and CLI exploration, and bound them there:

```sql
-- REST / SOAP / CLI only. Unbounded forms require LIMIT n where n <= 200
-- (or WHERE Id IN <list of up to 200 IDs>). Not available from Apex.
SELECT FIELDS(ALL) FROM Account LIMIT 200
SELECT FIELDS(CUSTOM) FROM Account LIMIT 200

-- Bounded form: supported everywhere including Apex, no LIMIT required
SELECT FIELDS(STANDARD) FROM Contact
```

```apex
// The Apex-safe equivalents
List<Contact> cons = [SELECT FIELDS(STANDARD) FROM Contact];
List<Account> accts = [SELECT Id, Name, Industry, AnnualRevenue FROM Account LIMIT 200];
```
