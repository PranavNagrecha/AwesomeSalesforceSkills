# LLM Anti-Patterns — Flow Bulkification

Common mistakes AI coding assistants make when generating or advising on Flow bulkification.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Placing Get Records inside a Loop element

**What the LLM generates:**

```
[Get Records: Get all Contacts] --> [Loop: For each Contact]
                                         |
                                         v
                                    [Get Records: Get Account for this Contact]
                                         |
                                         v
                                    [Update Records: Update Account]
```

**Why it happens:** LLMs model the logic sequentially — for each contact, look up the account, then update. This works for one record but causes N SOQL queries and N DML statements when the flow processes a batch of 200 records.

**Correct pattern:**

```
[Get Records: Get all Contacts with Account fields (or use a related record lookup)]
[Loop: For each Contact]
    [Assignment: Add modified Account to collection variable]
[Update Records: Update all Accounts in collection variable (one DML)]
```

Move all Get Records and DML outside the loop. Use collection variables to batch operations.

**Detection hint:** `Get Records` or `Update/Create/Delete Records` element inside a `Loop` element.

---

## Anti-Pattern 2: Using individual record DML inside a loop instead of collection DML

**What the LLM generates:**

```
[Loop: For each record in collection]
    [Update Records: Update this single record]
```

**Why it happens:** LLMs process items individually because it maps to simple procedural logic. Each Update Records inside a loop consumes a separate DML statement toward the 150 DML limit.

**Correct pattern:**

```
[Loop: For each record in collection]
    [Assignment: Add record to updateCollection]
[Update Records: Update all records in updateCollection]
```

Accumulate records in a collection variable inside the loop, then perform one bulk DML after the loop exits.

**Detection hint:** DML element (Create/Update/Delete Records) that is a direct child of a Loop element.

---

## Anti-Pattern 3: Claiming Flow auto-bulkifies all elements

**What the LLM generates:**

```
"Flow automatically bulkifies DML operations, so you don't need to worry about
putting Update Records inside a loop."
```

**Why it happens:** Salesforce does interview-level bulkification for record-triggered flows — batching multiple interviews' DML into fewer calls. But within a single interview, each DML element in a loop still counts separately. LLMs conflate these two levels.

**Correct pattern:**

Flow bulkification works across interviews (200 records trigger 200 interviews, and the platform batches their DML). But within a single interview that loops over records, each DML call in the loop is a separate call. Always move DML outside loops for within-interview efficiency.

**Detection hint:** Claims that "Flow handles bulkification automatically" as justification for DML inside loops.

---

## Anti-Pattern 4: Not adding entry conditions to filter which records trigger the flow

**What the LLM generates:**

```
Object: Opportunity
Trigger: A record is created or updated
Entry Conditions: None
```

**Why it happens:** LLMs create the broadest trigger to ensure the flow runs. Without entry conditions, the flow fires on every Opportunity save, including irrelevant updates, wasting governor limits.

**Correct pattern:**

```
Object: Opportunity
Trigger: A record is created or updated
Entry Conditions: StageName IsChanged AND StageName Equals "Closed Won"
```

Always add the most specific entry conditions possible to reduce unnecessary flow executions.

**Detection hint:** Record-triggered flow with no entry conditions or with `All Conditions Are Met (No conditions)`.

---

## Anti-Pattern 5: Using formula resources for calculations that could be done in assignments

**What the LLM generates:**

```
[Formula: Calculate discount — SOQL-like logic referencing {!Get_Account.AnnualRevenue}]
```

**Why it happens:** LLMs use formula resources because they are powerful. But formulas that reference Get Records results can cause the Get Records to re-execute per evaluation in bulk contexts, depending on the flow's structure.

**Correct pattern:**

Store intermediate values in variables via Assignment elements. Reference those variables in formulas rather than re-querying:

```
[Get Records: Get Account] --> [Assignment: Set localRevenue = {!Get_Account.AnnualRevenue}]
[Formula: Calculate discount using {!localRevenue}]
```

**Detection hint:** Formula resources that directly reference `{!Get_<element>.<field>}` in performance-critical paths.

---

## Anti-Pattern 6: Recommending Flow for batch processing above 2,000 records

**What the LLM generates:**

```
"Use a Scheduled Flow to process all 50,000 inactive contacts nightly."
```

**Why it happens:** LLMs recommend Flow for everything because it is low-code. Scheduled Flows process records in batches of 200, but at very high volumes (tens of thousands of records), they can hit org-wide governor limits, take too long, or fail silently.

**Correct pattern:**

For processing above ~2,000 records per run, evaluate whether Batch Apex is more appropriate:

- Scheduled Flow: good for < 2,000 records, simple logic, admin-maintained
- Batch Apex: better for 2,000+ records, complex logic, developer-maintained

```
"For 50,000 contacts, use a Batch Apex job. It processes in configurable batch sizes
with independent transactions and better error isolation."
```

**Detection hint:** Scheduled Flow design advice for record sets described as "tens of thousands" or "all records" without a volume-based escalation discussion.
