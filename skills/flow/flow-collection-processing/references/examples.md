# Examples — Flow Collection Processing

Narrative walk-throughs of the element-selection decision. The deployable XML lives in
`references/metadata-examples.md`; nothing here is a copy of it.

---

## Example 1: Bulk Status Update — and why the Loop is optional

**Context:** A record-triggered after-save Flow fires when `Order__c` records are marked
`Submitted`. It must set `Status__c = 'Pending Review'` on all related `Order_Line__c` records.

**Problem:** The naive design queries Order Lines inside the loop for each Order and issues an
`Update Records` per iteration. With a data load of 200 Orders that is up to 200 SOQL queries and
200 DML statements — against per-transaction budgets of 100 synchronous queries and 150 DML
statements (`apexdev.txt` L19544, L19554).

**The usual fix — Loop and accumulate:**

```text
[Get Records: OrderLines]
  Filter: Order__c IN {!$Record.Id}       ← single query outside the loop

[Loop: OrderLines]  →  currentItem = {!currentLine}

  [Assignment: Set Status]
    {!currentLine.Status__c} = "Pending Review"   (Assign)
    {!updatedLines}          Add {!currentLine}   (Add)

[After Last] → [Update Records: {!updatedLines}]  ← one DML for the whole collection
```

**The fix this skill adds — no Loop at all.** The mutation above is uniform: same field, same value,
every record. A Map processor whose `outputSObjectType` is the *input* type produces a collection
carrying `Id` plus the changed field, and `Update Records` keys off the mapped `Id`:

```text
[Get Records: OrderLines]  →  {!orderLines}

[Map: Stamp_Order_Lines]
  collectionProcessorType : RecommendationMapCollectionProcessor
  collectionReference     : orderLines
  assignNextValueToReference : currentLine
  outputSObjectType       : Order_Line__c
  mapItems                : Id           ← currentLine.Id
                            Status__c    ← "Pending Review"  (literal)

[Update Records: Stamp_Order_Lines]      ← one DML, zero loops
```

**When the Loop still wins:** the moment the new value differs per record — a branch, a lookup, a
per-record calculation the mapping cannot express. Uniform stamp → Map. Conditional stamp → Loop.
`flow/flow-loop-element-patterns` owns the Loop side of that line.

---

## Example 2: Filter then map — and where the computed value goes

**Context:** An autolaunched Flow runs after a batch of `Lead` records is converted. For each
converted Lead with `Rating = 'Hot'`, create a follow-up `Task` owned by the Lead owner, with a
subject that combines the company and the lead source.

**Problem:** The original design loops, checks `Rating` in a Decision, builds the Task across three
Assignment elements, and calls `Create Records` inside the loop.

**Solution:**

```text
[Collection Filter: HotLeads]
  collectionReference : {!ConvertedLeads}
  conditionLogic      : And
  conditions          : Rating EqualTo "Hot"

[Transform: LeadsToTasks]
  dataType     : sObject     objectType : Task     isCollection : true
  transformValues → transformValueActions:
      outputFieldApiName : WhoId
      transformType      : Map
      value              : elementReference currentHotLead.Id
      ---
      outputFieldApiName : Subject
      transformType      : Map
      value              : formulaExpression  "Follow up: " & {!currentHotLead.Company}
                                              & " (" & {!currentHotLead.LeadSource} & ")"
                           formulaDataType    String

[Create Records: LeadsToTasks]   ← one DML for all tasks
```

**The point of this example is the `Subject` row.** A Map *processor* has no formula surface, so a
computed subject would have to be prepared in an Assignment beforehand. A **Transform** does:
`formulaExpression` requires `formulaDataType` and both are documented at API version 59.0 and
later, cross-referenced to `FlowTransform` (`api_meta.txt` L70464–L70482). Choosing between the two
"mapping" elements is therefore not a style question — it is decided by whether any target field
needs to be computed.

`flow/flow-formula-and-expression-patterns` owns whether that formula string is *correct*; this
skill only owns which element it belongs in.

---

## Example 3: The two ways to take a top N, and the query plan behind them

**Context:** A Screen Flow shows the five largest open `Opportunity` records for the current user.

**Route A — cap in the database:**

```soql
SELECT Id, Name, Amount, CloseDate
FROM Opportunity
WHERE OwnerId = :userId AND IsClosed = false
ORDER BY Amount DESC
LIMIT 5
```

In Flow this is a Get Records with `sortField` = `Amount`, `sortOrder` = `Desc`, and `limit`
supplied as a `FlowElementReferenceOrValue` — "valid values are between 2 and 20,000. Supported
only when `getFirstRecordOnly` is `false`", API 63.0 and later
(`api_meta.txt` L71177–L71183). Five rows leave the database, five rows enter the heap, five rows
count against the 50,000-row SOQL budget.

**Route B — cap in the flow:** retrieve the full set, then a Sort processor with `sortOptions`
(`sortField` `Amount`, `sortOrder` `Desc`) and `limit` 5. Every matching row is retrieved, held and
counted; five survive.

**Which one:** Route A unless the ranking key is not queryable — a formula the flow computes, a
value assembled from two collections, or an order that depends on something the WHERE clause cannot
see. Route B also wins when the *full* collection is needed elsewhere in the same flow, because
Route A would need a second query to get it back.

**What makes Route B a top N rather than an arbitrary N:** `limit` is "the maximum number of records
to include in the generated collection… If `sortField` and `sortOrder` are also specified, the
records are sorted before the limit takes effect" (`api_meta.txt` L69961–L69967). Drop `sortOptions`
and the same `limit` silently becomes "any five".

---

## Example 4: Two collections, one Assignment

**Context:** A nightly flow has a collection of every active `Contract__c` and a collection of the
ones that already have a renewal task. It needs the ones that do not.

**What practitioners build:** a Loop over the first collection, an inner Loop over the second, a
Decision comparing Ids, and an Assignment on the no-match path. That is `n×m` element executions.

**What the operator table says instead** — one Assignment element, two items:

```text
[Assignment: Derive_Renewal_Gap]
  contractsNeedingRenewal  Add          allActiveContracts        ← seed a copy
  contractsNeedingRenewal  RemoveAll    contractsWithRenewalTask  ← set difference
```

`RemoveAll` "removes all instances of the value from the variable… when the value is a collection
variable, the operator removes all instances of each item from the variable in the
`assignToReference` field", API 43.0 and later (`api_meta.txt` L69823–L69829). Swap `RemoveAll` for
`RemoveUncommon` and you get the intersection instead: it "keeps items that are in both collections
and removes the rest" (L69847–L69851).

**The catch to declare up front:** the seeding `Add` takes a *collection* as its value, which is
"available in API version 43.0 and later, but only via Metadata API. From Flow Builder, you can't
save an Assignment element that contains a collection variable in the Value column for the `Add`
operator" (`api_meta.txt` L69786–L69790). Say so in the flow's `<description>`.
`flow/flow-bulkification` owns the consequences of a Metadata-API-only flow.

---

## Anti-Pattern: `AddItem` and a bare `limit` — two shapes that deploy and misbehave

Both fragments below parse, both look reasonable in review, and both are wrong. Neither appears in
`references/metadata-examples.md`, which only carries correct XML.

```xml
<assignments>
    <name>Stage_Line</name>
    <label>Stage Line</label>
    <locationX>50</locationX>
    <locationY>50</locationY>
    <assignmentItems>
        <assignToReference>linesToUpdate</assignToReference>
        <operator>AddItem</operator>
        <value>
            <elementReference>currentLine</elementReference>
        </value>
    </assignmentItems>
</assignments>
```

`AddItem` is "supported only when the `assignToReference` field is a variable of type multipicklist"
(`api_meta.txt` L69799–L69802). Appending to a collection is `Add`.

```xml
<collectionProcessors>
    <name>Top_Lines</name>
    <label>Top Lines</label>
    <locationX>50</locationX>
    <locationY>158</locationY>
    <collectionProcessorType>SortCollectionProcessor</collectionProcessorType>
    <collectionReference>allLines</collectionReference>
    <limit>10</limit>
</collectionProcessors>
```

No `sortOptions`, so nothing was sorted and `limit` took ten arbitrary rows. The element is named
`Top_Lines` and the reviewer reads the name.

Run both through the checker:

```bash
python3 skills/flow/flow-collection-processing/scripts/check_flow_collection_processing.py \
  --manifest-dir force-app --strict
```

Rule **E6** catches the first (it reads the target variable's declared `dataType` and requires
`Multipicklist`); rule **E2** catches the second. The general defence is the one in
`references/llm-anti-patterns.md`: match the operator to the target's declared `dataType`, and never
let an element's *name* stand in for what its fields actually say.
