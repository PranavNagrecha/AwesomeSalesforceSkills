# Gotchas — Flow Collection Processing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Every claim is cited to the Metadata API Developer Guide extract (`api_meta.txt`) or the Apex
Developer Guide extract (`apexdev.txt`); anything that cannot be grounded there carries an explicit
`UNVERIFIED (2026-09-05)` marker beside it.

Two gotchas that stood in earlier versions of this file are **corrected** below rather than kept
(Gotchas 3 and 4). Both were platform claims the guide contradicts.

---

## Gotcha 1: The Sort processor accepts three collection shapes, and each one wants a different `sortOptions`

**What happens:** `FlowCollectionSortOption.sortField` is "required for record collections and
collections of Apex-defined variables", and "if the collection is a primitive data type, such as a
list of string or integer values, `sortField` isn't supported" (`api_meta.txt` L69994–L69998). So
the same element takes three shapes: a record collection and an Apex-defined collection **must**
name a `sortField`; a Text or Number collection **must not**. Copy a working Sort from a record
collection onto a Text collection and the `sortField` that made it work is now the thing that
breaks it — and the reverse omission leaves a record collection with a `sortOptions` block the
schema rejects.

**When it occurs:** Refactoring a record collection into a projected list of Ids or codes, and
carrying the Sort element across unchanged. Also when a Sort is copied out of a sample built on
`Account` and pointed at an Apex-defined variable.

**How to avoid:** Read the collection variable's `dataType` before writing `sortOptions`.
`FlowVariable.dataType` is `String`/`Number`/`Apex`/`sObject`/etc. with `isCollection` `true`
(`api_meta.txt` L72850–L72884); `sObject` and `Apex` take a `sortField`, the primitives do not.
`doesPutEmptyStringAndNullFirst` and `sortOrder` are legal in all three shapes.

---

## Gotcha 2: `AddItem` is a multi-select-picklist operator, not the "add an item to a collection" operator

**What happens:** The name is the trap. `AddItem` is "supported only when the `assignToReference`
field is a variable of type **multipicklist**. Adds the value to the picklist, including the
semicolon that's required to mark a value as a separate item" (`api_meta.txt` L69799–L69802). It has
nothing to do with collections. The operator that appends to a collection variable is `Add` — "when
the `assignToReference` field is a collection variable, this operator appends the value to the end
of the collection" (L69786–L69790) — or `AddAtStart`, which "adds the value as a new item at the
beginning of the collection" (L69794–L69797). Writing `AddItem` against a record collection
produces an operator the runtime will not apply to that target type.

**When it occurs:** Any hand-authored or generated Assignment element where the author reasoned
from the operator's English name rather than from the enum table. It is the most plausible-sounding
wrong answer in the whole `FlowAssignmentOperator` list, because in every other language `addItem`
is exactly what you would call it.

**How to avoid:** Match the operator to the target's `dataType`, not to its role in your sentence.
Collections take `Add`, `AddAtStart`, `AssignCount`, `RemoveAll`, `RemoveUncommon`, `RemoveFirst`,
`RemoveAfterFirst`, `RemoveBeforeFirst` and `RemovePosition`; `AddItem` takes `Multipicklist` and
nothing else. `flow/flow-loop-element-patterns` Gotcha 10 covers `Add`'s other three meanings.

---

## Gotcha 3 (corrected): Transform mappings **do** take formula expressions — two fields exist for exactly that

**What the earlier version of this file said:** that the Transform element cannot use formula
expressions in field mappings, and that a formula-style mapping "silently falls through to an empty
or null value".

**What the guide says:** `FlowElementReferenceOrValue` — the type of a Transform's `value` and of a
`FlowCollectionMapItem`'s `value` alike — declares `formulaExpression`, "the formula expression that
transforms the data in the flow. In Flow Builder, it corresponds to the target data field in the
**Transform element**. This field requires the `formulaDataType` field. This field is available in
API version 59.0 and later. **See FlowTransform**" (`api_meta.txt` L70479–L70482). Its partner
`formulaDataType` carries the same "See FlowTransform" cross-reference and the same 59.0 floor
(L70464–L70477). API 59.0 is also the version in which `FlowTransform` itself was introduced
(L72685–L72687) — the two formula fields shipped *with* the Transform element, for the Transform
element.

**Why the wrong version is sticky:** the Map *processor*
(`RecommendationMapCollectionProcessor`, API 53.0) predates the formula fields by six releases, and
advice written against it generalises to "Flow's declarative mapping surfaces can't compute". The
generalisation is now false for `FlowTransform`.

**How to avoid getting it wrong in either direction:** put the formula in
`value/formulaExpression` and always pair it with `formulaDataType` — the guide states the pairing
is required. **UNVERIFIED (2026-09-05):** whether the Flow Builder UI surfaces a formula editor on
every Transform mapping row is a help.salesforce.com question and cannot be read from the Metadata
API guide; the metadata field is unambiguous, the UI affordance is not.

---

## Gotcha 4 (corrected): a collection processor writes a **generated** collection; it does not sort or filter in place

**What the earlier version of this file said:** that Collection Sort "operates in place on the
input collection", that "there is no output variable separate from the input", and that the
original order is therefore destroyed.

**What the guide says:** the processor reads `collectionReference`, "the collection being sorted,
filtered, or assigned to recommendations" (`api_meta.txt` L69942–L69943), and `limit` is described
throughout as "the maximum number of records to include in the **generated collection**"
(L69961–L69963). `outputSObjectType` is "the sObject type of the **output** collection" (L69979).
The guide's vocabulary is input-plus-generated-output, not mutation. There is no field on
`FlowCollectionProcessor` that names an output variable, which is why every element downstream of a
processor in `references/metadata-examples.md` references the **processor's own name** as the
collection.

**Why it matters practically:** the "in place" version makes you build a defensive copy before
every Sort. That copy is an `Add` of one collection variable into another, which the guide says is
"available in API version 43.0 and later, but only via Metadata API. From Flow Builder, you can't
save an Assignment element that contains a collection variable in the Value column for the `Add`
operator" (`api_meta.txt` L69786–L69790) — so the defensive copy is the thing that makes the flow
un-editable in Builder, and it was never needed.

**UNVERIFIED (2026-09-05):** the guide ships no sample XML for `FlowCollectionProcessor`, so
"reference the processor by its element name to read its output" is inferred from the absence of
any output-variable field plus the shape Flow Builder emits. Retrieve one Builder-authored
processor and confirm before relying on it in generated XML.

---

## Gotcha 5: a collection processor and a Transform have no fault path, so their neighbours own the failure

**What happens:** `FlowCollectionProcessor` "extends `FlowNode` and inherits all its fields"
(`api_meta.txt` L69926–L69928), and `FlowNode` declares only `elementSubtype`, `label`, `locationX`
and `locationY` (L70741–L70756). `FlowTransform` likewise extends `FlowNode` (L72685–L72687).
Neither type declares a `faultConnector`. The guide declares `faultConnector` on
`FlowRecordCreate` (L70965), `FlowRecordDelete` (L71046), `FlowRecordLookup` (L71120) and
`FlowRecordUpdate` (L71283). A Filter, Sort, Map or Transform therefore cannot route its own
failure anywhere — a fault surfaces at the next element that has a fault path, or terminates the
interview.

**When it occurs:** Reviewing a flow for fault coverage and finding processors "missing" fault
paths, then adding a `faultConnector` to one — which fails the deploy on an unexpected field
rather than a clear message.

**How to avoid:** Fault-cover the Get Records that produces the collection and the DML that
consumes it, and treat the processor chain between them as a single non-faulting span. That is what
`templates/flow/FaultPath_Template.md` does; the pattern is unchanged, only the placement.

---

## Gotcha 6: `collectionFilterCriteria` is a root-level Flow field that is not the Collection Filter

**What happens:** The `Flow` type's field table lists `collectionFilterCriteria`
(`FlowCollectionFilterCriteria[]`) immediately above `collectionProcessors`, and its entire
documented description is **"Reserved for future use"** (`api_meta.txt` L68090). The Collection
Filter element lives in `collectionProcessors`, "an array of nodes that process collections…
available in API version 50.0 and later" (L68092–L68093), with
`collectionProcessorType` set to `FilterCollectionProcessor`. XML that puts filter criteria under
`collectionFilterCriteria` is syntactically plausible, deploys as inert metadata, and filters
nothing.

**When it occurs:** Any XML written by scanning the `Flow` field table top-to-bottom for something
named after the Builder element. The name is a closer match to "Collection Filter" than the field
that actually implements it.

**How to avoid:** Two root arrays carry collection work and only two: `collectionProcessors` (API
50.0+) and `transforms` (`FlowTransform[]`, API 59.0+ — `api_meta.txt` L68435–L68436). Anything
else with "collection" in the name is not one of them.

---

## Gotcha 7: half of the Transform metadata surface is documented but inert

**What happens:** `FlowTransformValueAction` declares six fields, and four of them —
`actionName`, `actionType`, `actionVersionString` and `assignToReference` — are documented as
**"Reserved for future use"** (`api_meta.txt` L72758–L72765). `FlowTransformValue` declares
`transformValueName`, `transformValueLabel` and `transformValueDescription`, all three "Reserved for
future use" (L72739–L72743). `FlowTransform.storeOutputAutomatically` is "Reserved for future use"
(L72726). The `transformType` enum has the same problem: `GetItemByIndex` and `InvocableAction` are
listed as valid values and immediately annotated "Reserved for future use" (L72777, L72783).

The consequence that bites: because `assignToReference` and `storeOutputAutomatically` are both
reserved, **there is no documented field that names a Transform's output variable**. A generated
flow that assigns a Transform result to a variable through either field deploys and produces
nothing.

**When it occurs:** Generation that fills every documented field of a type — the reserved
annotation sits at the end of a line in a PDF table and is the easiest thing in the section to drop.

**How to avoid:** Treat four fields as the entire live surface of a Transform action:
`transformType`, `outputFieldApiName`, `inputParameters`, `value`. Read the Transform's result by
its element name. And read `transformType`'s enum as four capabilities (`Count`, `InnerJoin`, `Map`,
`Sum`), not six — with `InnerJoin` further restricted, since it "isn't a valid value for
`FlowInlineTransform`" (L72782).

---

## Gotcha 8: three unrelated things in Flow metadata are called Count

**What happens:** An agent told to "count the collection" has three documented candidates, and they
sit on three different types:

| Where | Field / value | Documented behaviour | Version |
|---|---|---|---|
| `FlowAssignmentItem` | `operator` = `AssignCount` | "Counts the number of stages or items in the collection, and assigns that number to the variable in the `assignToReference` field" — the collection goes in **`value`** (`api_meta.txt` L69813–L69818) | API 43.0+ |
| `FlowTransformValueAction` | `transformType` = `Count` | "Calculates the number of items in a source collection", configured through the `aggregationValues` input key (L72776, L72808–L72814) | API 59.0+ |
| `FlowCondition` | `aggregationOperator` = `Count` | "Operation to apply to the variable reference in the `assignToReference` field. The valid value is: `Count`" (L70048–L70050) | not stated |

They are not interchangeable. `AssignCount` writes a Number variable you can assert on in a
`FlowTest`; a `Count` transform's result has no output-variable field at all (Gotcha 7); and
`FlowCondition.aggregationOperator` refers to an `assignToReference` field that `FlowCondition`'s
own table does not declare.

**When it occurs:** Any "how many records did we process?" requirement, and any generated XML that
reached for the first `Count` it found in the guide.

**How to avoid:** For a countable, testable, assertable number, use `AssignCount` into a
non-collection `Number` variable — `scripts/check_flow_collection_processing.py` rule **E5** fails
the build when the target is anything else. Use the `Count` transform only when the count feeds a
Transform mapping. **UNVERIFIED (2026-09-05):** `FlowCondition.aggregationOperator` has no version
floor and no sample in the guide, and the `assignToReference` it names is not among
`FlowCondition`'s documented fields; its runtime behaviour cannot be established from this corpus.

---

## Gotcha 9: `outputSObjectType` types a processor's output; a **generic** sObject is typed somewhere else entirely, with a mandatory prefix

**What happens:** Two different mechanisms type an sObject collection and they are not
interchangeable. A Map processor names its own output type through `outputSObjectType`, "the sObject
type of the output collection" (`api_meta.txt` L69979). A collection crossing into or out of an
invocable action or a subflow whose parameter is a **generic** sObject is typed through
`FlowDataTypeMapping` instead — and that type requires a prefix: `typeName` is "Required. API name
of the input or output variable. The **`T__` prefix is required for input variables. The `U__`
prefix is required for output variables.** For example, `T__inputCollection` represents the API name
of the input variable `inputCollection`" (L70193–L70199). `dataTypeMappings` appears on
`FlowActionCall` (L68470) and on `<start>` from API 63.0 (L72318). It does **not** appear on
`FlowSubflow` at all: that type declares only `connector`, `flowName`, `inputAssignments`,
`outputAssignments` and `storeOutputAutomatically` (L72625–L72658). The `dataTypeMappings` field
marked "Reserved for future use" at L71632 belongs to `FlowScreenField` (L71583), which is a
different element and a different question.

**When it occurs:** Handing a Filter or Map output to a generic-sObject invocable action — a common
shape for "run my Apex over this collection". The mapping is dropped or written without the prefix,
and the action receives an untyped list.

**How to avoid:** If the receiving parameter is a generic sObject, write `dataTypeMappings` on the
`actionCalls` element with `T__`/`U__`-prefixed `typeName` values. If it is a subflow, there is no generic-sObject typing
mechanism documented for `FlowSubflow` — declare a typed collection input on the called flow
instead. `flow/subflows-and-reusability` owns the subflow contract.

---

## Gotcha 10: nothing in the developer guides caps how many items a collection may hold — and the debug log is the proof

**What happens:** Designs get decomposed to stay under a collection-size ceiling that the corpus
does not contain. The Apex Developer Guide's per-transaction limit table lists 100/200 SOQL
queries, **50,000 records retrieved by SOQL**, 150 DML statements, 10,000 DML rows, 6 MB / 12 MB
heap and 10,000 ms / 60,000 ms CPU (`apexdev.txt` L19544–L19579). None of those is a collection
size, and none is per-interview — they are per **transaction**, shared with every trigger, Apex
class and other flow in the same call stack.

The corroborating negative is in the log-event catalogue.
`FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` "displays the usage for one of these limits: SOQL queries,
SOQL query rows, SOSL queries, DML statements, DML rows, CPU time in ms, heap size in bytes,
callouts, email invocations, future calls, jobs in queue, push notifications"
(`apexdev.txt` L38821–L38834). Salesforce's own runtime reports every limit a flow interview can
consume, and neither an element count nor a collection size is among them. A separate grep of
`apexdev.txt` for a retired 2,000-executed-element Flow limit returns **nothing** — the developer
guide makes no statement in either direction, which is the same conclusion the `flow-loop-element-patterns`
and `flow-bulkification` siblings reached independently from the same corpus.

**When it occurs:** Sizing conversations that open with "how many records can a collection hold?".

**How to avoid:** Size against heap and CPU, which are documented, and against the SOQL row budget
if the collection came from a query. `flow/flow-loop-element-patterns` Gotcha 3 owns the full
account of the retired element ceiling and the one narrow case (a flow pinned to `<apiVersion>`
56.0 or earlier) where it can still be in play; `flow/flow-bulkification` owns the escalate-out-of-Flow
threshold. Do not re-derive either here.

---

## Gotcha 11: the loop iteration variable is a flow resource, and adding it to a collection is what carries an edit out

**What happens:** Editing `{!currentItem}` inside a Loop changes a flow variable, not a database
row. The change reaches the database only if the item is appended to a collection that a later DML
element consumes — which is what `Add` does on a collection variable
(`api_meta.txt` L69786–L69790).

**When it occurs:** Any loop-and-accumulate build where the `Add` is dropped, reordered after a
branch, or targets a record variable rather than a record collection variable.

**How to avoid:** This is Loop semantics, and `flow/flow-loop-element-patterns` owns it in full
(its Gotchas 1, 2 and 10). It is retained here only so that a reader who arrived at this file
looking for it is redirected rather than left to invent an answer. If your loop body is doing
nothing but this, the Map processor in `references/metadata-examples.md` §1 removes the loop
entirely — checker rule **W2** flags exactly that shape.

---

## Gotcha 12: an empty collection is silent at every stage of a processor chain

**What happens:** A Get Records that matches nothing produces an empty collection; a Filter over it
produces an empty collection; a Sort with `limit` over that produces an empty collection; a Map over
that produces an empty collection; and the DML at the end writes nothing. No element in the chain
faults, and no element has a fault path to fault into (Gotcha 5). The only observable difference
between "no rows qualified" and "the Filter conditions are wrong" is the count.

**When it occurs:** Whenever the upstream filter is tightened — including by a picklist value being
renamed underneath a `conditions` block that compares against a `stringValue`.

**How to avoid:** Terminate every processor chain with an `AssignCount` into a Number variable and
assert on it in a `FlowTest`, exactly as `references/metadata-examples.md` §3 does. `IsEmpty` — "an
empty collection", a valid `FlowComparisonOperator` from API 61.0 and later
(`api_meta.txt` L70097–L70098) — gives you the Decision-element form of the same check.
`flow/flow-loop-element-patterns` Gotchas 6 and 9 own the Loop-specific version of this.
