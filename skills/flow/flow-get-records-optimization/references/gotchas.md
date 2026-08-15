# Gotchas — Get Records

Non-obvious behaviours that make a Get Records cost more than it looks.

---

## Gotcha 1: The Governor Budget Is Per Transaction, and the Flow Is Batched

**What happens:** A flow with one Get Records fails with `Too many SOQL queries:
101`. The author counts one query and cannot reconcile it.

**When it occurs:** Record-triggered and schedule-triggered flows run one
interview per record, and the platform batches those interviews — up to 200 —
into a single transaction that shares one governor budget. One query per
interview is 200 queries in one transaction.

**Which limit those 200 land against depends on the flow type:**

- A **record-triggered** flow runs inside the triggering transaction. On a
  synchronous DML it gets the synchronous ceiling of 100, and 200 queries fails —
  which is the `101` in the error above.
- A **schedule-triggered** flow gets the **asynchronous** ceiling of 200 from
  runtime version 61.0 onward, under the *Improve Scheduled Flow Performance with
  Updated Limits* release update. The same 200 queries fit — exactly, with nothing
  left for the other automation sharing the transaction — and the error you get
  instead is usually `Too many DML statements: 151`, because the DML limit is 150
  in both columns and did not move.

**How to avoid:** Compute `per-interview cost × batch size`, not the element
count, and read the flow type and runtime version before choosing which ceiling
to compare it to. A scheduled flow costed against 100 gets an Apex rewrite it did
not need. And if that number is comfortably under the limit, stop optimizing the
flow — the budget is shared with every Apex trigger, second flow, and managed
package on the object, and the debug log's cumulative limits section is what
attributes the spend.

---

## Gotcha 2: Zero Rows Is Not a Fault

**What happens:** A fault connector wired off a Get Records to catch "not found"
never fires, and the flow continues with a null that breaks something else
downstream.

**When it occurs:** Always. Zero rows is a successful query. The fault connector
fires on a real platform exception — an invalid filter reference, an object or
field the running user cannot read, a governor breach — not on an empty result.

**How to avoid:** Use a Decision with the `IsNull` operator, and set
`assignNullValuesIfNoRecordsFound` to `true` so the variable is reliably null.
That flag matters most inside a loop, where without it the variable retains the
previous iteration's value and the null check silently passes.

---

## Gotcha 3: A Filter That Looks Narrow Is Often Not Selective

**What happens:** A filter on a status field matching "only one of eight values"
turns out to do a full table scan.

**When it occurs:** Selectivity is measured in absolute rows against documented
thresholds, not in intuitive narrowness. A standard index is selective below 30%
of the first million targeted records and 15% beyond, capping at 1,000,000. A
custom index is selective below 10% of the first million and 5% beyond, capping
at 333,333. One value out of eight on a four-million-row object is roughly
500,000 rows — past the custom index cap, so indexing that field cannot help.

**How to avoid:** Lead with something genuinely narrow — an Id, a foreign key, an
owner, a date range — and let the status filter reduce the small result. Check
rather than guess: Developer Console → Query Plan tool, where a Cost above 1
means the filter is not selective and a full table scan will be used.

**Why this hurts more in Flow:** Apex raises `QueryException: Non-selective query
against large object type` and the developer finds out immediately. A Flow query
is often merely slow, and slowness inside a 200-interview batch surfaces later as
a CPU limit somewhere that looks unrelated.

---

## Gotcha 4: Standard-Indexed Fields Are a Specific, Short List

**What happens:** A team adds a filter on a field they assume is indexed because
it is a standard field, and gets no improvement.

**When it occurs:** "Standard field" and "standard index" are different things.
The standard-indexed set is primary keys (`Id`, `Name`, `OwnerId`), foreign keys
(`CreatedById`, `LastModifiedById`, and lookup and master-detail relationship
fields), and audit fields (`CreatedDate`, `SystemModstamp`). Custom fields marked
Unique or External Id get a custom index.

**How to avoid:** Design filters around that list first. Where a custom field
genuinely needs an index, marking it External Id or Unique is the
self-service route; anything else is a support request.

---

## Gotcha 5: Leading Wildcards Cannot Use an Index

**What happens:** A search screen using the `Contains` operator is fast in a
sandbox with 200 records and unusable in production.

**When it occurs:** `Contains` produces a leading wildcard. No index can serve
it, so the query is a full table scan — in a screen flow, with a user watching.

**How to avoid:** `StartsWith` can use an index and is usually what the user
meant. Genuine "contains" semantics are a search problem, not a query problem:
SOSL, or a pre-computed normalized field a `StartsWith` filter can hit. Bound the
result with a `limit` and tell the user when it was truncated.

---

## Gotcha 6: Negative and Null Operators Defeat the Index

**What happens:** A filter such as "Status not equal to Closed" or "Close Date is
null" performs far worse than the equivalent positive filter.

**When it occurs:** Negative operators and null checks force the optimizer to
consider rows the index cannot exclude, so it falls back toward a scan.
`<!-- UNVERIFIED: the precise optimizer behaviour for each operator was not
confirmed against a fetchable official page during authoring. Verify a specific
filter with the Developer Console Query Plan tool rather than reasoning from this
rule. -->`

**How to avoid:** Express the filter positively where the data model allows — a
list of the statuses you *do* want rather than the one you do not — and check the
resulting Cost in the Query Plan tool. Where a null check is genuinely required
on a large object, a formula or a maintained boolean field that can be indexed is
the usual workaround.

---

## Gotcha 7: "Store All Fields" Retrieves Every Field

**What happens:** Heap grows and a screen flow becomes sluggish between screens,
with no obvious culprit in the element list.

**When it occurs:** Automatic field storage retrieves every field on the object.
On a wide object with a large collection that is a lot of memory against a 6 MB
synchronous / 12 MB asynchronous heap — and a screen flow serializes its
variables between screens, so the cost is paid on every transition rather than
once.

**How to avoid:** Name `queriedFields` on large collections. Accept automatic
storage on single-record lookups, where the heap cost is negligible and the
brittleness is not worth it — a named field list silently returns null for a
field you forgot to add rather than erroring.

---

## Gotcha 8: A Paused Interview Serializes Its Collections

**What happens:** A screen flow that pauses with a large collection in scope
resumes slowly, and the org accumulates storage nobody attributed to it.

**When it occurs:** Pausing stores the interview's state, collections included.
A collection that was expensive to hold in memory is now expensive to store and
to rehydrate.

**How to avoid:** Trim collections before a Pause — keep the Ids and re-query on
resume rather than carrying full records across. Re-querying is also more correct
for anything another user might have edited in the meantime.

---

## Gotcha 9: `$Record` Does Not Carry Related Records

**What happens:** `{!$Record.Account.Industry}` in a Case flow returns nothing,
or the flow will not save.

**When it occurs:** The triggering record's own fields are available without a
query. Related-record traversal beyond what the trigger context loaded needs an
explicit Get Records. `$Record__Prior` likewise holds only the triggering
record's prior field values.

**How to avoid:** Get Records the parent, filtered on the foreign key — which is
standard-indexed, so it is cheap. Just remember it is one query per interview and
therefore 200 per full batch, which puts it straight back into Gotcha 1's
arithmetic.

---

## Gotcha 10: A Cross-Object Filter Is Not Free

**What happens:** Filtering child records on a parent field — `Account.Industry`
on a Contact query — performs worse than expected.

**When it occurs:** The filter is evaluated against the related object, and the
index that would help is on the parent, not on the child rows being scanned.

**How to avoid:** Two queries are often cheaper than one clever one: query the
parents on their own indexed field, collect the Ids, then query children with an
`In` filter on the foreign key. That is two SOQL statements instead of one, and
both are selective — a good trade against one non-selective query, given SOQL
statements are budgeted at 100 and rows at 50,000.

---

## Gotcha 11: Sort Cost Follows From Filter Selectivity, Not From the Limit

**What happens:** A query with `limit 10` and a sort on a custom text field is
still slow, and the author concludes the limit is not working.

**When it occurs:** The limit bounds what is *returned*, not what must be
considered to determine the top 10. With a selective filter the candidate set is
small and the sort is trivial; with a non-selective filter it is not, and the
limit cannot rescue it.

**How to avoid:** Make the filter selective first (Gotcha 3), then sort. Sorting
on a standard-indexed field such as `CreatedDate` is the cheapest option
available. Treat a slow sort as evidence about the filter.

---

## Gotcha 12: `getFirstRecordOnly` Changes the Variable's Shape

**What happens:** Downstream elements break with a type mismatch after someone
toggles "how many records to store."

**When it occurs:** `getFirstRecordOnly` set to `true` produces a single record
variable; `false` produces a collection. Every downstream reference — loops,
assignments, decisions, screen components — is bound to one shape or the other.

**How to avoid:** Decide the shape when you create the element and treat changing
it as a refactor of everything downstream. When you only need one record, `true`
plus a `limit` of 1 is both cheaper and clearer than fetching a collection and
taking the first element.
