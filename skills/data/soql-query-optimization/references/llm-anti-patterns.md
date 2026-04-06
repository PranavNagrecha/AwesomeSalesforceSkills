# LLM Anti-Patterns — SOQL Query Optimization

Common mistakes AI coding assistants make when generating or advising on Salesforce SOQL query optimization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Adding Indexes Without Checking Selectivity Thresholds

**What the LLM generates:** "Add a custom index on the Status field to improve query performance" without assessing whether the filter on Status is selective. A custom index on a field where 90% of records share the same value (e.g., Status = 'Active') will not be used by the query optimizer.

**Why it happens:** In traditional databases, indexes generally improve query performance. LLMs apply this generic principle without understanding Salesforce's selectivity threshold: an indexed filter must match fewer than 10% of records (or 333,333 records for standard indexes, 100,000 for custom indexes) to be considered selective.

**Correct pattern:**

```text
Salesforce query selectivity rules:

Standard index selectivity threshold:
- Filter must match < 30% of total records for the first 1M records
- AND < 1,000,000 total matching records

Custom index selectivity threshold:
- Filter must match < 10% of total records
- AND < 333,333 total matching records (varies)

Before requesting a custom index:
1. Determine the cardinality of the field (number of distinct values)
2. Calculate the selectivity: matching records / total records
3. If > 10%, the index will likely not be used
4. Consider compound filters: Status = 'New' AND CreatedDate = TODAY
   (multiple selective filters can combine for selectivity)

Use the Query Plan tool (Developer Console > Query Plan) to verify
whether your filter uses an index.
```

**Detection hint:** Flag custom index recommendations that do not include a selectivity calculation. Look for index suggestions on low-cardinality fields like Status, Type, or Boolean fields.

---

## Anti-Pattern 2: Using LIKE with Leading Wildcards on Indexed Fields

**What the LLM generates:** `WHERE Name LIKE '%searchterm%'` on a large object, expecting it to use an index. Leading wildcards prevent index usage in Salesforce.

**Why it happens:** LIKE with wildcards is a common search pattern in general SQL. LLMs apply it without noting that Salesforce indexes cannot be used for leading wildcard searches — only trailing wildcards (`'searchterm%'`) benefit from standard indexes.

**Correct pattern:**

```text
LIKE and index usage in SOQL:

Index-friendly (trailing wildcard):
  WHERE Name LIKE 'Acme%'           -- uses index
  WHERE Email LIKE 'john@acme%'     -- uses index

NOT index-friendly (leading wildcard):
  WHERE Name LIKE '%Acme'           -- full table scan
  WHERE Name LIKE '%Acme%'          -- full table scan

For full-text search with leading wildcards:
- Use SOSL (FIND 'Acme' IN ALL FIELDS RETURNING Account)
- SOSL uses the search index, not the database index
- SOSL supports wildcards: FIND 'Acme*' or FIND '*Acme'

For programmatic search:
- Search.query() for dynamic SOSL
- Requires search index to be built (new records may have delay)
```

**Detection hint:** Flag SOQL queries with `LIKE '%...` (leading wildcard) on objects with >100K records. Recommend SOSL as an alternative.

---

## Anti-Pattern 3: Querying All Fields Instead of Only Needed Fields

**What the LLM generates:** `SELECT Id, Name, Field1, Field2, ... Field50 FROM Account` or advice to "select all fields you might need" without considering the impact on heap size, network payload, and query performance.

**Why it happens:** LLMs generate SELECT clauses based on what the user might need rather than what is strictly necessary. There is no `SELECT *` in SOQL, but LLMs approximate it by listing many fields.

**Correct pattern:**

```text
SOQL field selection best practices:

1. Select ONLY the fields you will use in the current transaction
2. Each field adds to:
   - Query execution time (more fields = more data retrieved)
   - Heap size consumption (Apex heap limit: 6 MB sync, 12 MB async)
   - Network payload (for API responses)

3. Long Text Area and Rich Text fields are especially expensive:
   - Each can hold up to 131,072 characters
   - Selecting 10 such fields on 200 records could consume >250 MB

4. Use relationship queries instead of separate queries:
   SELECT Id, Name, Account.Name FROM Contact
   (one query instead of two)

5. For dynamic field sets, use FieldSet.getFields() to query only
   the fields configured in the field set.
```

**Detection hint:** Flag SOQL queries that select more than 15-20 fields without justification. Check for Long Text Area or Rich Text fields in the SELECT clause when they are not needed.

---

## Anti-Pattern 4: Not Using the Query Plan Tool to Validate Optimization

**What the LLM generates:** "Add an index and your query will be faster" without recommending validation via the Query Plan tool to confirm that the optimizer actually uses the index.

**Why it happens:** The Query Plan tool is a Salesforce-specific diagnostic accessed through the Developer Console. General database optimization training does not cover it, and LLMs recommend generic index strategies without the validation step.

**Correct pattern:**

```text
Query Plan tool usage:

1. Open Developer Console > Query Editor
2. Enable Query Plan: check "Use Tooling API" or click the Query Plan button
3. Enter your SOQL query (without Apex binding variables — use literal values)
4. Review the plan output:
   - Cost: relative cost (lower is better)
   - Cardinality: estimated number of rows
   - Fields: which indexed fields are used
   - Leading Operation Type: TableScan (bad) vs Index (good)
   - Sobject Cardinality: total records in the object

If the plan shows "TableScan" as the leading operation:
- The query is not selective — add or adjust filters
- Verify that indexed fields are in the WHERE clause
- Check selectivity thresholds (see Anti-Pattern 1)
```

**Detection hint:** Flag query optimization advice that does not mention the Query Plan tool or an equivalent validation step. Recommendations should verify the optimizer's actual plan, not assume index usage.

---

## Anti-Pattern 5: Ignoring Skinny Tables for Frequently Queried Large Objects

**What the LLM generates:** "Add a custom index to improve performance" as the only optimization for large objects, without mentioning skinny tables as an alternative for objects with many fields where queries only need a subset.

**Why it happens:** Skinny tables are a Salesforce-internal feature that must be requested through Salesforce Support. They are not configurable by admins or developers directly, so they appear far less frequently in training data than custom indexes.

**Correct pattern:**

```text
Skinny tables:
- A Salesforce-internal optimization for large objects (>1M records)
- Creates a narrow copy of the object with only specified fields
- Dramatically improves query performance for queries that only need
  those fields
- Must be requested via Salesforce Support (cannot self-serve)
- Supported for: custom objects and some standard objects
- Maximum columns: varies (typically up to 100 fields)
- Maintained automatically by Salesforce (synced with the main table)

When to request a skinny table:
1. Object has >1M records AND >50 fields
2. Common queries only need 5-10 of those fields
3. Custom indexes alone are not sufficient
4. Query Plan tool still shows high cost after indexing

Skinny tables are not visible in Setup — they are a back-end optimization.
```

**Detection hint:** Flag query optimization recommendations for large objects (>1M records) that only suggest custom indexes without mentioning skinny tables as an option.
