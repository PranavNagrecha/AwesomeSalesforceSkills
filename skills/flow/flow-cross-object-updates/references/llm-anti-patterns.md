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

One DML regardless of collection size.
```

**Correction (2026-09-05).** An Update inside a Loop spends **DML statements**,
not SOQL queries, so the ceiling it hits is 150 DML statements per synchronous
transaction, not "SOQL-101" (`apexdev.txt` L19550). A *Get Records* inside a
loop is the one that spends SOQL, and that ceiling is 100 (L19542). The
earlier wording of this bullet conflated the two; the fix is the same either
way, but the number you will see in the debug log is not.

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

Recursion budget: CPU time (10,000 ms sync), 150 DML, 100 SOQL,
10,000 DML rows per transaction, and stack depth 16 for recursive
trigger firing. Chained triggers eat these fast.
```

Those five numbers are grounded in the Apex Developer Guide governor-limit
table: 100 SOQL and 150 DML (`apexdev.txt` L19542, L19550), 10,000 records
processed by DML (L19556), stack depth 16 (L19559), 10,000 ms synchronous CPU
(L19579). UNVERIFIED (2026-09-05): the retirement of the 2,000-executed-element
Flow limit in API 57.0 is not stated in any guide reachable from this repo;
`flow/flow-loop-element-patterns` owns that claim — check there before citing it.

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

Option 3 — Apex aggregation trigger (for very large child counts or
aggregations a roll-up cannot express) — see apex/recursive-trigger-prevention
for the guard, and templates/apex/TriggerHandler.cls for the shape.
```

The grounding for "master-detail only" is one sentence in the CustomField
field table: `summaryForeignKey` "represents the master-detail field on the
child that defines the relationship between the parent and the child"
(`api_meta.txt` L43648–43650). Valid `summaryOperation` values are `Count`,
`Min`, `Max`, `Sum` (L43651–43666), and `summarizedField` "can't be null
unless the `summaryOperation` value is `count`" (L43636–43638). DLRS is a
third-party AppExchange package, not a platform feature — it carries its own
support and upgrade story, and no Salesforce documentation covers it.

**Detection hint:** User asks for a rollup on a standard lookup (AccountId, OwnerId) or a custom lookup field.

---

## Anti-Pattern 6: Emitting `filters` and `inputReference` on the same `recordUpdates`

**What the LLM generates:** A `recordUpdates` element carrying `filters`,
`inputAssignments` *and* `inputReference`, on the theory that more fields make
the intent clearer — or, the mirror mistake, an element with `inputReference`
and no `<object>`.

**Why it happens:** The `FlowRecordUpdate` field table lists all of them as
fields of the same type, with no "one of" grouping visible to a model reading
the table row by row.

**Correct pattern:**

```xml
<!-- Filter mode: find the records, then set fields on them -->
<recordUpdates>
    <name>Stamp_Parent</name>
    <label>Stamp Parent</label>
    <locationX>176</locationX>
    <locationY>494</locationY>
    <filterLogic>and</filterLogic>
    <filters>
        <field>Id</field>
        <operator>EqualTo</operator>
        <value><elementReference>$Record.Subscription__c</elementReference></value>
    </filters>
    <inputAssignments>
        <field>Line_Health__c</field>
        <value><stringValue>Attention: Cancelled Line</stringValue></value>
    </inputAssignments>
    <object>Subscription__c</object>
</recordUpdates>
```

The two modes are `filters` + `inputAssignments`, or `inputReference` pointing
at a record/collection variable that already carries the Ids and values
(`api_meta.txt` L71264–71292). `object` is marked **Required** in both cases
(L71292) — it is the one field that is never optional.

**Detection hint:** A `<recordUpdates>` containing both a `<filters>` child and
an `<inputReference>` child, or one with `<inputReference>` and no `<object>`.
`scripts/check_flow_cross_object_updates.py` does not flag this; the deploy
will.

---

## Anti-Pattern 7: Building a roll-up in Flow when the relationship is master-detail

**What the LLM generates:** Get children → Loop → Assignment with the `Add`
operator onto a Number variable → Update the parent with the total. Correct
Flow, wrong layer.

**Why it happens:** The request says "flow", so the model builds a flow. It has
no view of the relationship type, which is where the answer actually lives.

**Correct pattern:**

```xml
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Total_MRR__c</fullName>
    <label>Total MRR</label>
    <summarizedField>Subscription_Line__c.MRR__c</summarizedField>
    <summaryForeignKey>Subscription_Line__c.Subscription__c</summaryForeignKey>
    <summaryOperation>sum</summaryOperation>
    <type>Summary</type>
</CustomField>
```

No flow, no interview, no recursion surface, and the platform maintains it —
roll-up recalculation is step 16 of the save order (`apexdev.txt`
L15471–15473). The flow version costs one interview per triggering record and
adds a node to the cross-object write graph. Reach for it only when the
relationship is a Lookup (then see `flow/flow-collection-processing`) or when
the value is not a Count/Min/Max/Sum.

**Detection hint:** A `<loops>` whose body contains an `<assignmentItems>` with
`<operator>Add</operator>` targeting a Number or Currency variable, in a flow
whose looped object has a `MasterDetail` field pointing at the triggering
object. This is the `ROLLUP_BY_LOOP` ADVISORY in
`scripts/check_flow_cross_object_updates.py`.
