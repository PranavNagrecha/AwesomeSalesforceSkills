# LLM Anti-Patterns — Large Data Volume Architecture

Common mistakes AI coding assistants make when generating or advising on Large Data Volume Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Promising self-service skinny tables

**What the LLM generates:** “Enable skinny tables in Setup under Database settings.”

**Why it happens:** Other platforms expose column stores as toggles; Salesforce requires a Customer Support engagement for skinny tables.

**Correct pattern:**

```
Request skinny tables through Salesforce Customer Support after documenting the object, read paths, and the ≤200 supported columns you need.
```

**Detection hint:** Phrases like “toggle skinny table” or “checkbox in Setup” for skinny tables.

---

## Anti-Pattern 2: Inventing selectivity percentages

**What the LLM generates:** “Custom indexes are selective below 5% of rows always.”

**Why it happens:** Training data mixes database vendor rules with Salesforce's older 10% / 333,333 cap for custom indexes and different standard-index math.

**Correct pattern:**

```
Quote Salesforce LDV rules: standard indexed fields use 30%/15% on the first million plus remainder; custom indexed fields use <10% of the first million and <5% of the remainder (corrected 2026-10-03 from "<10% with a 333,333-row ceiling", per the current LDV guide); AND uses indexes unless one returns >20% of rows, OR unless they all return >10%, and every OR field must be indexed.
```

**Detection hint:** Percentages that do not match the official three-tier story (standard vs custom vs OR/AND notes).

---

## Anti-Pattern 3: Treating Big Objects as drop-in replacements

**What the LLM generates:** “Move the object to a Big Object and keep triggers for validation.”

**Why it happens:** Big Objects resemble tables generically but lack trigger, workflow, and formula support.

**Correct pattern:**

```
Use Big Objects for append-mostly archive or massive ingest; keep transactional rules on standard/custom objects or external orchestration.
```

**Detection hint:** Mentions triggers, Flow record-triggered paths, or roll-ups directly on `__b` objects.

---

## Anti-Pattern 4: Ignoring sharing join cost in “query optimization”

**What the LLM generates:** “Add a LIMIT 50000 and the report will be fine.”

**Why it happens:** LIMIT masks symptoms while leaving non-selective predicates and expensive sharing joins.

**Correct pattern:**

```
Treat sharing as part of the access path: fix skew, reduce rule fan-out, and ensure selective indexed filters so the optimizer can minimize sharing join I/O.
```

**Detection hint:** LIMIT-only fixes with no mention of indexes, skew, or filter distribution.

---

## Anti-Pattern 5: Assuming all sandboxes behave like production for skinny performance

**What the LLM generates:** “Validate skinny performance in your Developer sandbox copy.”

**Why it happens:** Sandboxing assumptions from other products.

**Correct pattern:**

```
Skinny tables copy to Full sandboxes only; other sandbox types do not include them—plan validation in Full or document asymmetry.
```

**Detection hint:** Skinny performance claims tied to scratch or Developer sandboxes without caveat.

---

## Anti-Pattern 6: Requesting an Index for a Filter No Index Can Serve

**What the LLM generates:** "Ask Support for a custom index on `Days_Open__c` (a formula using `TODAY()`) and on `Opportunity.Amount` to speed up the pipeline report."

**Why it happens:** The model assumes any field can be indexed if Support agrees.

**Correct pattern:** The LDV guide says custom indexes work only on deterministic formulas and lists non-indexable cases: cross-object references, dynamic date functions, multi-select picklists, multicurrency currency fields, long text, binary fields, and special standard fields such as Opportunity `Amount`, `IsClosed` and `IsWon`. Materialize the value into a plain field and index that, or change the filter.

**Detection hint:** An index request naming a formula with `TODAY()`/`NOW()`, a cross-object formula, or one of the listed standard fields.

---

## Anti-Pattern 7: Filtering on Null and Expecting the Index to Help

**What the LLM generates:** "Add a custom index on `Driver__c` so `WHERE Driver__c = null` is fast."

**Why it happens:** The model does not know that Salesforce index tables omit null rows by default.

**Correct pattern:** The LDV guide ("Index Tables") says nulls are excluded unless Support builds a null-inclusive index (the `CustomIndex` metadata `allowNullValues` flag), and its SOQL table recommends replacing nulls with a value such as `NA`. Store an explicit state value and filter on it. Two-column indexes are the one case that tolerates nulls, and only in the second column.

**Detection hint:** A performance fix whose key filter is `= null` or `!= null`.

---

## Anti-Pattern 8: Sizing From the Record Count Resource as if It Were Exact

**What the LLM generates:** "Your object has exactly 41,203,377 rows per `/limits/recordCount`, so the custom index threshold is 2,060,168."

**Why it happens:** The resource looks authoritative.

**Correct pattern:** The REST API Developer Guide ("Record Count") says the value is a cached snapshot refreshed at variable intervals that excludes Recycle Bin and archived records. Use it to rank objects, then use `SELECT COUNT()` with filters (results limited to rows visible to the running user) for the threshold decision, and say which number you used.

**Detection hint:** Threshold math quoted to the row from `recordCount`, with no mention that it is a snapshot.

