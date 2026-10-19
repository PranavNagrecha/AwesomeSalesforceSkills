# LLM Anti-Patterns — SOQL Query Optimization

Common mistakes AI coding assistants make when generating or advising on Salesforce SOQL query optimization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending an Index Without the Threshold Arithmetic

**What the LLM generates:** "Add a custom index on `Status__c` to improve query performance," with no count of how many rows the filter value matches. When a model does quote thresholds, it often swaps them (a tighter percentage for standard indexes than for custom ones) or quotes flat caps it cannot source.

**Why it happens:** In general-purpose databases an index almost always helps. Salesforce's optimizer runs a pre-query against its statistics and declines an index whose filter matches too many rows.

**Correct pattern:**

```text
Thresholds (LDV guide, "Standard and Custom Indexed Fields"):
  Standard index: < 30% of the first million rows, < 15% of rows beyond
     2M rows -> 450,000    5M rows -> 900,000
  Custom index:   < 10% of the first million rows, < 5% of rows beyond
     500K rows -> 50,000   5M rows -> 300,000

Before asking for an index:
  1. SELECT Status__c, COUNT(Id) FROM Case__c GROUP BY ROLLUP(Status__c)
  2. Compare the target value's count with the row for the object's size
  3. Above the threshold -> the index will not be used; change the filter
  4. Confirm with ?explain= : relativeCost < 1.0, leadingOperationType Index
```

**Detection hint:** An index recommendation with no per-value count, or a low-cardinality field (Status, Type, a checkbox) proposed as the driving filter.

---

## Anti-Pattern 2: Promising That SOSL Supports Any Wildcard Position

**What the LLM generates:** "Replace `LIKE '%Acme%'` with `FIND '*Acme'`" — presenting SOSL as a drop-in substring search with leading wildcards.

**Why it happens:** Models map SQL `LIKE '%x%'` to "full-text search" and assume the search engine accepts the same pattern.

**Correct pattern:** Recommend SOSL for keyword search, with specific terms. In SOSL, asterisks match zero or more characters at the middle or end of a term (SOQL and SOSL Reference, FIND clause), so `*Acme` is not a substring search. The LDV guide's own advice is to keep searches specific and avoid wildcards ("search with Michael instead of Mi*"), to use single-object searches, and to use targeted search groups such as `IN NAME FIELDS`. For a LIKE that must stay in SOQL, capture the plan; the optimizer decides LIKE index use by sampling up to 100,000 rows rather than from statistics.

**Detection hint:** A suggested SOSL string that starts with `*`, or a claim that LIKE with a leading `%` "always" or "never" uses an index without a plan to back it.

---

## Anti-Pattern 3: Selecting Every Field "In Case It Is Needed"

**What the LLM generates:** `SELECT Id, Name, Field1__c, ... Field60__c FROM Account` or `FIELDS(ALL)` in a selector that runs over thousands of rows.

**Why it happens:** Models build SELECT lists from what a caller might want, not from what the transaction uses.

**Correct pattern:**

```text
- Select only the fields this transaction reads.
- Every selected field costs heap: 6 MB synchronous, 12 MB asynchronous.
- Use relationship fields (Account.Name) instead of a second query.
- For admin-configurable lists, build the SELECT from a field set.
- A skinny table only helps queries whose fields are all in it,
  so wide SELECT lists also defeat a skinny table.
```

**Detection hint:** More than about 20 fields, `FIELDS(ALL)`, or long-text fields selected in a loop-driven or batch query where they are never read.

---

## Anti-Pattern 4: Claiming the Plan Is Only Available in Developer Console

**What the LLM generates:** "The Query Plan tool is only in Developer Console, so you cannot check plans from VS Code or CI," or invented setup steps such as "check Use Tooling API to enable Query Plan."

**Why it happens:** Most training text about plans describes the Developer Console panel; the REST resource is less visible because it is marked Beta.

**Correct pattern:**

```bash
# Same plan data, from any REST client (API 30.0+, Beta)
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://MyDomainName.my.salesforce.com/services/data/v67.0/query/?explain=SELECT+Id+FROM+Case+WHERE+Status='New'"
# Read: plans[0].leadingOperationType (Index vs TableScan)
#       plans[0].relativeCost (above 1.0 = not selective)
```

In Developer Console the panel appears once the `Enable Query Plan` preference is on.

**Detection hint:** Advice that says plans cannot be captured outside Developer Console, or that names a menu path or checkbox not in the docs.

---

## Anti-Pattern 5: Getting Skinny-Table Facts Wrong

**What the LLM generates:** "Skinny tables hold up to 100 fields," "skinny tables are available on any standard object," or "every sandbox gets your skinny tables."

**Why it happens:** Skinny tables are Support-managed and rarely appear in public code, so models fill the gaps with plausible numbers.

**Correct pattern:**

```text
Skinny tables (LDV guide):
- Created and changed only by Customer Support
- Up to 200 columns; no fields from other objects
- Custom objects, plus Account, Contact, Opportunity, Lead, Case
- Omit soft-deleted rows; kept in sync with the source table
- Copied to Full sandboxes only
- Can degrade performance in the wrong context
```

**Detection hint:** Any column count other than 200, a standard object outside the five listed, or a sandbox claim that does not single out Full sandboxes.

---

## Anti-Pattern 6: Treating Non-Selectivity in a Trigger as "Just Slow"

**What the LLM generates:** "This query will be slow on a large object; consider an index and monitor the cost," followed by approval to move the query into a trigger handler.

**Why it happens:** The selectivity material models have absorbed is framed around throughput and timeouts. The Apex guide's statement that queries must be selective "particularly for queries inside triggers" is rarely connected to a release gate.

**Correct pattern:** Treat selectivity as a gate for trigger code: the query's plan must show `relativeCost` under 1.0 against production row counts before it ships, and if it cannot, move the work to an asynchronous path. See Gotcha 6 for the failure that shows up in trigger context.

**Detection hint:** A review that approves moving a query into a trigger, trigger handler, or `before`/`after` path citing only wall-clock time or "monitor in production", or that offers `LIMIT` or batching as the fix for a selectivity error.
