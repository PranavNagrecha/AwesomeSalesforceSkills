# LLM Anti-Patterns — Get Records

Mistakes AI assistants reliably make when writing or reviewing a Flow query.

---

## Anti-Pattern 1: Get Records Inside a Loop

**What the LLM generates:** a Loop whose body contains a `recordLookups` element
filtered on the current loop item.

**Why it happens:** the imperative "for each X, fetch its Y" shape is the
dominant pattern in the model's training data and reads naturally on the canvas.
Nothing about the Flow editor discourages it.

**Correct pattern:** collect the Ids in an Assignment inside the loop, run one
Get Records with an `In` filter after it, and match in a second loop. Flow has no
map, so the match is a nested loop — O(n×m) CPU and zero extra queries, which is
the right trade given SOQL is budgeted at 100 and CPU at 10,000 ms.

**Detection hint:** a `<recordLookups>` reachable from a `<loops>` element's
`nextValueConnector` before the loop's `noMoreValuesConnector`.

---

## Anti-Pattern 2: Counting Queries Per Interview Instead of Per Transaction

**What the LLM generates:** "this flow issues 2 SOQL queries, comfortably within
the limit of 100."

**Why it happens:** the element count is visible on the canvas and the limit is
stated per transaction. The interview-to-transaction batching sits between the
two and is invisible in the metadata.

**Correct pattern:** record-triggered and schedule-triggered flows batch up to
200 interviews into one transaction sharing one budget. Two queries per interview
is 400 per transaction. Always state the multiplication — and always name which
ceiling you are multiplying against, because they differ: a record-triggered flow
gets the synchronous 100, a schedule-triggered flow on runtime version 61.0+ gets
the asynchronous 200. Quoting 100 at a scheduled flow is the mirror-image error
and produces an unnecessary Apex rewrite.

**Detection hint:** a limits analysis with no batch-size multiplier in it, or one
that names a ceiling without naming the flow type and runtime version it belongs
to.

---

## Anti-Pattern 3: Fault Path for "No Records Found"

**What the LLM generates:** a `faultConnector` on the Get Records pointing at a
branch labelled "no record found."

**Why it happens:** lookups that find nothing raise in most languages and ORMs,
so the fault path is the natural analogue.

**Correct pattern:** zero rows is a successful query. Handle not-found with a
Decision using `IsNull`, and set `assignNullValuesIfNoRecordsFound` to `true` so
the variable is reliably null — which matters inside a loop, where otherwise it
retains the previous iteration's value. Reserve the fault connector for real
exceptions.

**Detection hint:** a `<faultConnector>` inside `<recordLookups>` whose target
label contains "not found", "none", "missing", or "empty".

---

## Anti-Pattern 4: "Add an Index to Make It Selective"

**What the LLM generates:** a recommendation to index the filter field whenever a
query is slow, with no reference to how many rows the filter matches.

**Why it happens:** "slow query, add an index" is the reflex from every relational
database, and it is usually right there.

**Correct pattern:** Salesforce selectivity is measured in absolute rows against
documented thresholds. A custom index is selective below 10% of the first million
targeted records and 5% beyond, capping at 333,333 records; a standard index
below 30% / 15%, capping at 1,000,000. A filter matching 500,000 rows on a
four-million-row object cannot be made selective by indexing. Lead with a
genuinely narrow filter instead, and verify with the Developer Console Query Plan
tool, where a Cost above 1 means a full table scan.

**Detection hint:** an indexing recommendation with no estimate of matched row
count.

---

## Anti-Pattern 5: Assuming Any Standard Field Is Indexed

**What the LLM generates:** "filter on a standard field, which is indexed."

**Why it happens:** "standard field" and "standard index" are one word apart and
the distinction is not obvious.

**Correct pattern:** the standard-indexed set is specific — `Id`, `Name`,
`OwnerId`, `CreatedById`, `LastModifiedById`, lookup and master-detail
relationship fields, `CreatedDate`, `SystemModstamp`. Custom fields marked Unique
or External Id get a custom index. Nothing else is indexed by default.

**Detection hint:** a claim that a standard field other than those is indexed.

---

## Anti-Pattern 6: `Contains` for a Search Screen

**What the LLM generates:** a search screen whose Get Records filters a text
field with the `Contains` operator against user input.

**Why it happens:** it is what the user asked for semantically, and it works
flawlessly in a sandbox with 200 records.

**Correct pattern:** `Contains` produces a leading wildcard that no index can
serve — a full table scan, with a user watching. `StartsWith` can use an index
and is usually what was meant. True contains semantics need SOSL or a
pre-computed normalized field. Bound the result with a `limit` and tell the user
when it was truncated.

**Detection hint:** the `Contains` operator on a text field in a screen flow.

---

## Anti-Pattern 7: Blanket "Always Name Your Fields"

**What the LLM generates:** a rule that `storeOutputAutomatically` should always
be `false` with an explicit `queriedFields` list, applied to every lookup
including single-record ones.

**Why it happens:** "select only what you need" is correct SQL hygiene and
generalizes cleanly — which hides the trade.

**Correct pattern:** naming fields has a real cost: add a field to a downstream
element and forget the query, and you get a silent null rather than an error.
Name fields where the heap saving is real — large collections on wide objects,
against a 6 MB synchronous heap, with a screen flow re-serializing between
screens. Accept automatic storage on single-record lookups.

**Detection hint:** a `queriedFields` list on a lookup with
`getFirstRecordOnly` true and no collection downstream.

---

## Anti-Pattern 8: `limit` Presented as a Performance Fix

**What the LLM generates:** "add a limit of 10 to the query to make it fast."

**Why it happens:** the limit bounds the result set, and bounded results feel
cheap.

**Correct pattern:** the limit bounds what is *returned*, not what the optimizer
must consider to determine the top N. With a non-selective filter, a limit does
not rescue the query. Make the filter selective first; then the limit is a
correctness and heap measure, not a performance one.

**Detection hint:** a `limit` offered as the remedy for a slow query with no
change to the filter.

---

## Anti-Pattern 9: Traversing Relationships From `$Record`

**What the LLM generates:** `{!$Record.Account.Industry}` in a Case flow, or
`$Record__Prior` with a related-object path.

**Why it happens:** cross-object dot notation is a real Salesforce idiom in
formulas and validation rules, so it looks portable into Flow.

**Correct pattern:** the triggering record's own fields are available without a
query; related-record traversal beyond what the trigger context loaded needs an
explicit Get Records on the foreign key. That is cheap per query — foreign keys
are standard-indexed — and it is one query per interview, so it re-enters the
batch-size arithmetic.

**Detection hint:** a dotted relationship path more than one level deep on
`$Record` or `$Record__Prior`.

---

## Anti-Pattern 10: Optimizing the Flow When the Transaction Is the Problem

**What the LLM generates:** a query-merging refactor in response to `Too many
SOQL queries: 101`, based only on the flow's own element list.

**Why it happens:** the flow is the artifact in the prompt, so it is where the
model looks. The other consumers of the budget are not in context.

**Correct pattern:** the budget is per transaction and shared with every Apex
trigger, second record-triggered flow, and managed package on the object. If
`per-interview cost × batch size` is comfortably under the limit, the flow is not
the consumer. Inventory the object's automation and read the debug log's
cumulative limits section, which attributes the spend.

**Detection hint:** a governor-limit remediation that never mentions any
automation other than the flow in question.
