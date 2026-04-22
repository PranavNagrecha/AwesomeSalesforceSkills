# LLM Anti-Patterns — Flow Cross Object Updates

Common mistakes AI coding assistants make designing cross-object Flow logic.

## Anti-Pattern 1: Update Records inside a Loop

**What the LLM generates:** A Loop over Contacts with an Update Records element inside, updating one Contact per iteration.

**Why it happens:** Imperative thinking — "for each record, update it" — instead of Flow's bulk model.

**Correct pattern:**

```
Keep Update OUTSIDE the loop:

Get Records → Loop → Assignment (mutate fields in memory)
                  → Add to collection
[after loop] Update Records (collection input)

One DML regardless of collection size. Inside-loop updates hit
SOQL-101 at 101 records.
```

**Detection hint:** A `<loops>` element in a flow-meta.xml where the loop body contains a `<recordUpdates>` element.

---

## Anti-Pattern 2: Extra Get Records when dot-notation would work

**What the LLM generates:** A Get Records on Account filtered by `Id = $Record.AccountId` just to read `Account.Industry`.

**Why it happens:** Model treats Flow like SQL, doesn't know about formula traversal.

**Correct pattern:**

```
Dot-notation resolves the lookup for free:

{!$Record.Account.Industry}

No Get Records needed. Works up to 5 levels of traversal.
```

**Detection hint:** `<recordLookups>` filtering by `Id` equal to a `{!$Record.Xxx__c}` where the only use of the result is reading a field.

---

## Anti-Pattern 3: Recursion via cross-object chain

**What the LLM generates:** Child-triggered flow updates parent; parent-triggered flow runs and updates the child; child-triggered flow fires again.

**Why it happens:** Model doesn't think about the trigger stack.

**Correct pattern:**

```
Guard with entry conditions:

Parent-triggered flow entry: ISCHANGED(Status__c)
Child-triggered flow entry:  ISCHANGED(Status__c)

Or use a transient custom setting "suppress_flow" toggled during
cross-object operations.

Flow recursion limits: 2000 elements per transaction. Chained
triggers eat this budget fast.
```

**Detection hint:** Record-triggered flow A updates a field on object X where flow B (record-triggered on X) writes back a field on A's object.

---

## Anti-Pattern 4: Missing Fault path on Get / Update

**What the LLM generates:**

```
Get Records → Assignment → Update Records
(no fault paths anywhere)
```

**Why it happens:** Model doesn't know Flow fault paths exist, or skips them for "simplicity."

**Correct pattern:**

```
Every data element (Get/Create/Update/Delete) should have a Fault
path to:
- Set an error message (Screen flow) or
- Create an Error_Log__c record (auto flow) or
- Send Email Alert to support

Without Fault paths, a MIXED_DML or sharing-rule blocking error
surfaces as a raw stacktrace to the user.
```

**Detection hint:** `<recordLookups>` or `<recordUpdates>` element with no `faultConnector`.

---

## Anti-Pattern 5: Rollup Summary on a Lookup

**What the LLM generates:** Instructions to "create a Rollup Summary field to count Contacts on Account."

**Why it happens:** Model knows Rollup Summary exists but ignores that it requires master-detail.

**Correct pattern:**

```
Rollup Summary works ONLY on master-detail children. For lookups:

Option 1 — Record-triggered flow on Contact:
  On create/update/delete → Get Records (sibling contacts on parent)
  → CollectionProcessor Count → Update parent

Option 2 — Declarative Lookup Rollup Summaries (DLRS) — free
AppExchange app that generates the triggers for you.

Option 3 — Apex aggregation trigger (for >10k children or complex
aggregations) — see apex-trigger-handler-pattern skill.
```

**Detection hint:** User asks for a rollup on a standard lookup (AccountId, OwnerId) or a custom lookup field.
