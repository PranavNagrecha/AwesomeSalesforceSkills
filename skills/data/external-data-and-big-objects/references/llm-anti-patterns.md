# LLM Anti-Patterns — External Data and Big Objects

Common mistakes AI coding assistants make when generating or advising on Salesforce Big Objects, Async SOQL, and External Objects.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing Standard SOQL Against Big Objects

**What the LLM generates:** `SELECT Id, Field__c FROM MyBigObject__b WHERE Field__c LIKE '%search%'` or `SELECT COUNT(Id) FROM MyBigObject__b` — using SOQL patterns that are not supported on Big Objects.

**Why it happens:** LLMs generate SOQL using patterns learned from standard and custom objects. Big Object SOQL restrictions (no LIKE, no aggregates, no OR, mandatory composite index field filtering) are a niche topic with limited training data.

**Correct pattern:**

```text
Big Object SOQL constraints:
- Must filter on composite index fields in order (left to right)
- First index field: = (equals) only
- Last index field: can use =, <, >, <=, >=, IN
- Middle index fields: = (equals) only
- NO: LIKE, OR, NOT, HAVING, GROUP BY, COUNT, SUM, AVG
- NO: ORDER BY (results ordered by composite index automatically)
- NO: subqueries or relationship queries

Valid example (assuming index: Account__c, Date__c, Type__c):
  SELECT Id, Amount__c FROM Audit_Log__b
  WHERE Account__c = :accountId
  AND Date__c >= :startDate
  AND Date__c <= :endDate

Invalid: adding WHERE Type__c LIKE '%payment%' (LIKE not supported)
```

**Detection hint:** Flag SOQL against `__b` objects that uses LIKE, OR, GROUP BY, COUNT, ORDER BY, or aggregate functions. Check that WHERE clause filters follow the composite index field order.

---

## Anti-Pattern 2: Expecting Database.insertImmediate() to Return Error Details

**What the LLM generates:** Apex code like `Database.SaveResult[] results = Database.insertImmediate(records);` expecting SaveResult objects, when `Database.insertImmediate()` returns void for Big Objects.

**Why it happens:** Standard DML patterns (`Database.insert()` returns `SaveResult[]`) are deeply ingrained in training data. LLMs apply the same pattern to Big Object DML without noting the different return type.

**Correct pattern:**

```text
Big Object DML behavior:

// Standard object DML (returns results):
Database.SaveResult[] results = Database.insert(accounts, false);

// Big Object DML (returns void, fire-and-forget):
Database.insertImmediate(bigObjectRecords);
// No return value — no per-record success/failure information
// Failures appear in debug logs only

Error handling for Big Object inserts:
1. Validate all composite index fields are populated before insertion
2. Validate data types match the Big Object field definitions
3. Log the batch size and record identifiers for reconciliation
4. Query the Big Object after insertion to verify records exist
5. Monitor debug logs for UNABLE_TO_INSERT errors
```

**Detection hint:** Flag `Database.insertImmediate()` calls that assign the result to a variable or check for errors in the return value. The method returns void.

---

## Anti-Pattern 3: Recommending Big Objects When External Objects Are More Appropriate

**What the LLM generates:** "Store your ERP transaction history in a Big Object for access from Salesforce" when the data lives in an external system and should remain there, making External Objects (via Salesforce Connect) a better fit.

**Why it happens:** Big Objects and External Objects both handle "large or external data" use cases, and LLMs conflate them. The key distinction — Big Objects store data IN Salesforce, External Objects virtualize data FROM external systems — is not always clear in training data.

**Correct pattern:**

```text
Big Objects vs External Objects:

Big Objects (__b):
- Data stored IN Salesforce (counts toward Big Object storage, not data storage)
- Best for: audit logs, historical data archive, IoT telemetry
- Insert via Apex (Database.insertImmediate) or Bulk API
- Read via standard SOQL / Batch Apex / Bulk API query (NOT Async SOQL - retired Summer '23)
- Severe SOQL query constraints (composite index only)
- No UI support for standard list views or reports

External Objects (__x):
- Data remains in EXTERNAL system (no Salesforce storage consumed)
- Best for: real-time virtual access to ERP, warehouse, or database data
- Requires Salesforce Connect license and adapter (OData, Cross-Org, Custom)
- Supports indirect lookups to Salesforce objects
- Better reporting support than Big Objects

Decision: if the data originates externally and can be queried in place,
use External Objects. If you need to archive Salesforce data for long-term
storage, use Big Objects.
```

**Detection hint:** Flag Big Object recommendations where the data source is an external system. Look for "store external data in Big Object" when "virtualize via External Object" may be more appropriate.

---

## Anti-Pattern 4: Recommending Async SOQL — a Feature Retired in Summer '23

**What the LLM generates:** "Use Async SOQL to query your Big Object and populate a standard object with the results," typically with a request body containing `query`, `operation`, `targetObject`, and `targetFieldMap`, posted to `/services/data/vXX.0/async-queries/` and polled via `GET .../async-queries/{jobId}`. Frequently it is offered as a *correction* to a standard-SOQL approach — "standard SOQL won't scale on a Big Object, use Async SOQL instead."

**Why it happens:** This is the highest-confidence wrong answer in the Big Object domain, and the confidence is earned rather than random. Async SOQL was the officially documented Big Object query path from its introduction until **Summer '23** — roughly six years of Salesforce documentation, Trailhead content, partner blog posts, Stack Exchange answers, and conference talks all saying the same correct-at-the-time thing. Retirement notices are a single Help article; they do not propagate through the secondary corpus, and they carry almost no weight against six years of consistent signal. So a model that has genuinely learned this domain well produces the retired API *because* it learned it well.

The inverted framing makes it worse. Because the model also learned "standard SOQL on Big Objects has surprising restrictions," it presents Async SOQL as the sophisticated fix for a naive mistake. That framing survives code review — it reads as someone who knows the platform.

**Correct version:** Async SOQL does not exist. `/services/data/vXX.0/async-queries/` returns 404 and there is no `AsyncQueryJob` resource. Per Salesforce Help article 000394892: "You must use the Bulk API or batch Apex to query or report on custom Big Objects."

```text
Big Object read paths (post Summer '23):

1. Standard SOQL       - bounded reads; normal Apex query-row limits apply.
2. Batch Apex          - Database.getQueryLocator over the __b object.
                         Replaces Async SOQL's job semantics for volume.
3. Bulk API query      - extraction off-platform, results as CSV.

All three obey the composite-index rule: the WHERE clause must be a
gapless left-to-right prefix of the index. Fields before the last one
filtered take '=' only; the last one also takes <, >, <=, >=, IN.
!=, LIKE, NOT IN, EXCLUDES, INCLUDES are unsupported.

What you LOSE versus Async SOQL, and must now build yourself:
  Async SOQL wrote aggregate results INTO a target object as a side
  effect of the job (targetObject + targetFieldMap). Nothing does that
  now. Use Database.Stateful, accumulate in execute(), and insert the
  summary records explicitly in finish().
```

**Detection hint:** `grep -rn 'async-queries\|AsyncQueryJob\|asyncQuery' .` — every hit is a dead endpoint, in prose or in code. Two softer signals worth flagging in review: (a) any Big Object design that names a `targetObject` or `targetFieldMap` for query *results* — that is the Async SOQL request shape and no current API has an equivalent; (b) any Big Object query plan containing `GROUP BY` or an aggregate function, since the aggregation Async SOQL performed server-side is now the caller's job.

---

## Anti-Pattern 5: Designing Big Object Composite Index Without Considering Query Patterns

**What the LLM generates:** A Big Object definition with an arbitrary composite index order (e.g., `Type__c, Account__c, Date__c`) without analyzing the actual query patterns that will be used to retrieve data.

**Why it happens:** LLMs create composite indexes based on field importance or alphabetical order rather than query filter patterns. The composite index field order in a Big Object is immutable after creation and determines all possible query shapes.

**Correct pattern:**

```text
Big Object composite index design:

Rule: the composite index defines the ONLY way you can query the Big Object.
SOQL must filter from left to right through the index fields.

Example: if queries always filter by Account, then by Date range:
  Index: Account__c (1st), Date__c (2nd), Record_Key__c (3rd)

  Valid: WHERE Account__c = :acctId AND Date__c >= :start AND Date__c <= :end
  Valid: WHERE Account__c = :acctId (filters on first field only)
  INVALID: WHERE Date__c >= :start (skips first index field)

Design process:
1. List ALL query patterns that will be used against this Big Object
2. Identify the most common filter fields
3. Order index: most selective equality field first, range field last
4. The index CANNOT be changed after Big Object creation
   (you must recreate the Big Object to change the index)
```

**Detection hint:** Flag Big Object definitions where the composite index order does not match the described query patterns. Check for range operator fields placed before equality fields in the index.
