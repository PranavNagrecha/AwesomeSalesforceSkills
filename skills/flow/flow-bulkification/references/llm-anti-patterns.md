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

**Why it happens:** There really is a bulk layer, and the model over-generalises from it. The debug log names both halves: `FLOW_BULK_ELEMENT_DETAIL` / `_END` log "Interview ID, element type, element name, **number of records**, and execution time" and `FLOW_BULK_ELEMENT_LIMIT_USAGE` logs "Incremented usage toward a limit for this bulk element" (`apexdev.txt` L38721–38744), while `FLOW_LOOP_DETAIL` logs one entry per iteration — "the position in the collection variable for the item that the loop is operating on" (L38843–38846). Elements are charged as bulk units; loop iterations are not.

**Correct pattern:**

Say what the log says and stop there. An element on the interview's straight-line path is executed and charged as a bulk element across the batch. The same element on a Loop's `nextValueConnector` path is charged per item, per interview. The platform even publishes an event for the exclusions — `FLOW_BULK_ELEMENT_NOT_SUPPORTED`, "Operation, element name, and entity name that doesn't support bulk operations" (`apexdev.txt` L38746–38747) — so "everything is bulkified" is refuted by the log schema itself.

**Detection hint:** Claims that "Flow handles bulkification automatically" as justification for DML inside loops; or any stated ratio ("200 interviews become 1 DML") — the guides document that bulk elements exist and are charged as units, not how many interviews are grouped into one.

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

**Why it happens:** LLMs reach for formula resources because they are expressive, and then justify it with a mechanism that does not exist. **UNVERIFIED (2026-09-05):** the frequently-repeated claim that "a formula referencing a Get Records result re-executes the query per evaluation" appears **nowhere** in `api_meta.txt` or `apexdev.txt`. `FlowFormula` (`api_meta.txt` L70596–70627) documents `dataType`, `expression` and `scale` and says nothing about evaluation frequency or re-querying. Do not repeat the mechanism; the guidance below stands on a documented reason instead.

**Correct pattern:**

The documented reason to stage a value into a variable is CPU, not re-querying. Formula evaluation is Apex-runtime work and CPU time is capped at 10,000 ms synchronous / 60,000 ms asynchronous per transaction (`apexdev.txt` L19579), shared with every other automation in the save. A formula re-evaluated once per loop iteration per interview is a CPU multiplier even if it touches no database:

```
[Get Records: Get Account] --> [Assignment: Set localRevenue = {!Get_Account.AnnualRevenue}]
[Formula: Calculate discount using {!localRevenue}]
```

**Detection hint:** Any answer that explains a Flow performance rule with a database mechanism it cannot cite. Ask for the guide line; if there isn't one, the advice may still be right but the reason is invented.

---

## Anti-Pattern 6: Recommending Flow for batch processing above 2,000 records

**What the LLM generates:**

```
"Use a Scheduled Flow to process all 50,000 inactive contacts nightly."
```

**Why it happens:** LLMs recommend Flow for everything because it is low-code, and then reassure the reader with a batch size that belongs to a different feature. **The claim "Scheduled Flows process records in batches of 200" is a conflation.** The only documented batch-size field anywhere in the Flow metadata is `FlowScheduledPath.maxBatchSize` — "the maximum number of scheduled path interviews to execute in a single batch, from 1 to 200. Default is 200" (`api_meta.txt` L71397–71398) — and a scheduled *path* is a delayed branch of a **record-triggered** flow, not a schedule-triggered flow. `FlowSchedule` (L71335–71386) has no batch-size field at all, and a schedule-triggered flow whose `<start>` carries `<object>` starts "a flow interview … for each record that meets the filter conditions" (L72424–72428).

**Correct pattern:**

Do not offer a batch size the platform does not give you. Bound the run in the flow instead — omit `<object>` so one interview runs, cap the Get with `<limit>` (2–20,000, API 63.0+, `api_meta.txt` L71177–71183) and cap what actually commits with a Collection Sort `<limit>` (`api_meta.txt` L69961–69967). `references/metadata-examples.md` § 4 is the worked shape. Escalate to Batch Apex when the working set cannot be bounded that way, and say why in terms of the limits rather than a folklore threshold:

```
"40,000 stale rows will not fit one interview's DML-row budget (10,000 rows per
transaction, apexdev.txt L19556). Either bound the nightly flow to the oldest 500 and
let it drain over several nights, or move it to Batch Apex, which gets a fresh set of
governor limits per execute() batch."
```

**Detection hint:** Scheduled Flow advice quoting a batch size, or a bare record-count threshold ("above 2,000 use Apex") with no limit named. Thresholds like that are estimating heuristics — useful, but they are not platform facts and must not be written as if they were.


---

## Anti-Pattern 7: Building the collection but never committing it

**What the LLM generates:**

```xml
<loops>
    <name>Loop_Lines</name>
    <collectionReference>Get_Shipment_Lines</collectionReference>
    <nextValueConnector>
        <targetReference>Stage_Line</targetReference>
    </nextValueConnector>
</loops>
```

**Why it happens:** The model learns the collection pattern — loop, assign, append — and stops there, because the *shape* is what it was asked for. The guide's own autolaunched sample reinforces it: that `<loops>` element has a `<nextValueConnector>` and no `<noMoreValuesConnector>` (`api_meta.txt` L73747–73757), because the sample exists to demonstrate iteration, not to write anything.

The result deploys, runs, logs `FLOW_LOOP_DETAIL` for every item, and changes nothing. There is no error, because there is no failure — the interview simply reached the end.

**Correct pattern:**

```xml
<loops>
    <name>Loop_Lines</name>
    <collectionReference>Get_Shipment_Lines</collectionReference>
    <nextValueConnector>
        <targetReference>Stage_Line</targetReference>
    </nextValueConnector>
    <noMoreValuesConnector>
        <targetReference>Update_Shipment_Lines</targetReference>
    </noMoreValuesConnector>
</loops>
```

"The element to navigate to when all entries in the collection have been iterated through" (`api_meta.txt` L70716–70717) is where the single DML lives. Without it the staging was theatre.

**Detection hint:** A flow that declares a collection variable with `<isCollection>true</isCollection>`, appends to it inside a loop, and has no DML element on any `noMoreValuesConnector`. `scripts/check_flow_bulkification.py` reports this shape.

---

## Anti-Pattern 8: Recommending a per-record fix for a per-transaction limit

**What the LLM generates:**

```
"The flow is hitting 'Too many SOQL queries: 101'. Add a Decision before the Get Records
so it only queries when the field is populated — that will cut the query count."
```

**Why it happens:** The model treats the error as a volume problem to be shaved down rather than a structural one. Filtering *reduces* the multiplier; it does not remove it. A Get inside a loop that runs on 60% of iterations still scales with N, and the flow fails at a slightly larger batch instead of the current one — usually in production rather than in the test that "proved the fix".

It also misreads whose budget is being spent. The 100-query and 150-statement caps are per **transaction**, not per flow: "The governor execution limits are per transaction. For example, one transaction can issue up to 100 SOQL queries and up to 150 DML statements" (`apexdev.txt` L20172–20173). Apex triggers, other flows and managed-package automation on the same save draw from the same budget, so the safe margin the model just calculated belongs to someone else too.

**Correct pattern:**

Convert `O(N)` database work to `O(1)` before optimising anything. Query once outside the loop, stage into a collection, write once after it (`references/metadata-examples.md` § 2). Entry criteria and Decisions are worth having — they cut CPU and unnecessary interviews — but they are what you add *after* the structure is right, never instead of fixing it.

**Detection hint:** Advice that answers a limit exception with a filter, a smaller batch size, a `Decision` guard, or "retry with fewer records", while leaving a database element on a loop path.
