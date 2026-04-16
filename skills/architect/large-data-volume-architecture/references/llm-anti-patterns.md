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

**Why it happens:** Training data mixes database vendor rules with Salesforce’s documented 10% / 333,333 caps for custom indexes and different standard-index math.

**Correct pattern:**

```
Quote Salesforce LDV rules: standard indexed fields use 30%/15% on the first million plus remainder; custom indexed fields use <10% with a 333,333-row ceiling; AND/OR have additional optimizer gates.
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
