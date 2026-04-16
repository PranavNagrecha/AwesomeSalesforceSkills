# LLM Anti-Patterns — Flow Large Data Volume Patterns

Common mistakes AI coding assistants make when generating or advising on Flow Large Data Volume Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating this skill with generic bulkification only

**What the LLM generates:** “Just move `Get Records` outside the loop” as the complete answer to a `Too many query rows` error, without asking how many rows that single query returns.

**Why it happens:** Training data emphasizes loop + SOQL **count** patterns and under-emphasizes **aggregate rows returned** across all queries in the transaction.

**Correct pattern:**

```
First quantify each Get Records (filters, first-record-only vs collection, field count).
Then sum worst-case rows across all elements in the same transaction before proposing structure changes.
```

**Detection hint:** The assistant mentions loop bulkification but never mentions row totals, caps, or “50,000” class ceilings.

---

## Anti-Pattern 2: Prescribing Batch Apex when the user asked for Flow-only fixes

**What the LLM generates:** “Switch this to Batch Apex” for every LDV symptom, including cases solvable with caps, filters, or async handoffs still orchestrated in Flow.

**Why it happens:** Batch Apex is a memorized hammer for volume; the model defaults to code before evaluating declarative caps.

**Correct pattern:**

```
1. Tighten Get Records (filters, fields, sort, explicit row cap where supported).
2. If business needs full scans, then recommend Apex/async with clear boundaries — not as the first line for bounded reporting.
```

**Detection hint:** Immediate Batch Apex recommendation with no row-budget analysis or Flow limit citation.

---

## Anti-Pattern 3: Claiming a single `Get Records` cannot return “that many” rows

**What the LLM generates:** “One query is safe; Salesforce will stop at 200 records” — mixing up bulk trigger size with **query row** limits.

**Why it happens:** Confusion between **records in the trigger collection** and **rows returned by SOQL** inside the flow.

**Correct pattern:**

```
Explain that bulk size (for example 200 Accounts in one transaction) is separate from how many Case rows one Get Records can return per Account or in aggregate across the interview.
```

**Detection hint:** Mentions “200” as a universal maximum for all Flow retrieval.

---

## Anti-Pattern 4: Designing “get all related” for rollups in synchronous Flow

**What the LLM generates:** A flow diagram: `Get Records` → `Loop` all children → `Assignment` to sum → `Update Records` on parent, with `Get Records` set to retrieve **all** child rows.

**Why it happens:** Declarative rollups are natural to express as “load everything and add,” which ignores LDV ceilings.

**Correct pattern:**

```
Use platform rollups where possible, aggregate off-platform, or cap + document truncation. If full precision is required at massive scale, move aggregation out of the synchronous interview.
```

**Detection hint:** No mention of roll-up summary fields, async aggregation, or row caps when child volume is unbounded.

---

## Anti-Pattern 5: Ignoring co-resident automation in the same transaction

**What the LLM generates:** “Your flow only has 20,000 rows of queries; you are fine” while ignoring Apex triggers and other flows that also query in the same DML transaction.

**Why it happens:** Models analyze one artifact file at a time without a whole-transaction inventory.

**Correct pattern:**

```
List other automation on the same object and related paths; assume shared governor budgets unless explicitly isolated (rare for record-triggered paths).
```

**Detection hint:** Analysis references a single Flow XML or narrative with no mention of triggers, other flows, or managed package automation.
