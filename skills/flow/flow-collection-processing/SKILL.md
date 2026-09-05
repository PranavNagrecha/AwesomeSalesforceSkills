---
name: flow-collection-processing
description: "Use when building or reviewing Flow logic that processes lists of records using Loop, Assignment, Collection Filter, Collection Sort, or Transform elements. Triggers: 'iterate over collection in flow', 'flow loop add to collection', 'collection filter element', 'transform element flow', 'update records from collection variable', 'collection sort flow', 'collection processor', 'RecommendationMapCollectionProcessor', 'transformType Sum', 'InnerJoin flow', 'AssignCount', 'RemoveUncommon', 'sortOptions', 'outputSObjectType'. NOT for pulling DML or SOQL out of a Loop element — use flow/flow-loop-element-patterns. NOT for transaction-budget and bulkification analysis — use flow/flow-bulkification."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
triggers:
  - "how do I iterate over a collection in a flow and modify each record"
  - "flow loop is causing DML inside loop or too many DML statements error"
  - "how do I filter a collection without using a loop in flow"
  - "how to sort records in a collection variable before displaying in a screen flow"
  - "how do I use the transform element to create related records from a collection"
  - "flow collections isn't working"
  - "pick between the Transform element and the Map collection processor"
  - "aggregate a collection to a total in a flow without an Apex invocable"
  - "join two collections in a flow without a nested loop"
  - "sort a text collection in a flow and sortField is rejected"
  - "write the Flow XML for a Collection Filter in formula mode"
  - "assert on a collection processor output in a flow test"
  - "stamp the same field value on every record in a collection without a loop"
  - "which assignment operator appends a record to a collection variable"
  - "flow transform element sums a currency field across a collection"
tags:
  - flow-collections
  - loop-element
  - collection-filter
  - collection-sort
  - transform-element
  - bulk-dml
inputs:
  - "Flow type (record-triggered, autolaunched, screen flow)"
  - "Source collection: SObject Collection or primitive collection variable"
  - "Operations needed: filter, sort, transform, accumulate, or DML"
  - "Target SObject type if Transform is involved"
outputs:
  - "Correct element selection and configuration for the collection operation"
  - "Pattern for loop-and-accumulate vs. Collection Filter vs. Transform"
  - "DML strategy: single Update Records on collection vs. loop+individual DML"
  - "Review findings on anti-patterns in existing Flow logic"
dependencies: []
version: 2.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Collection Processing

This skill answers one question: **given a collection and a task, which element does the task?**
Flow has five documented answers — Collection Filter, Collection Sort, the Map processor, Transform,
and the `FlowAssignmentOperator` set — plus the Loop, which does anything but costs
`body_elements × iterations` to do it.

Loop *mechanics* (refactoring DML and SOQL out of a body, `noMoreValuesConnector`, iteration
variables) belong to `flow/flow-loop-element-patterns`; transaction budgets belong to
`flow/flow-bulkification`. This skill owns the selection, the configuration, and the shape of the
XML that results.

---

## Before Starting

- What is the collection variable's declared `dataType` and `isCollection`? Record, Text/Number and
  Apex-defined collections are accepted by different elements with different required fields.
- What is the flow's `<apiVersion>`, and what is the highest version floor among the elements you
  intend to use? Sort is API 50.0, Filter and Map are 53.0, `sortOptions` and processor `limit` are
  51.0, Transform is 59.0, Transform's scalar output types are 62.0, `InnerJoin` and Get Records
  `limit` are 63.0.
- Where does the collection come from, and how large is it at p99? A collection from a Get Records
  spends the transaction's SOQL row budget; one assembled in memory spends heap.
- What consumes the result — a DML, a screen table, a subflow, an invocable action? The consumer
  decides the required type, and a generic-sObject consumer needs a separate typing mechanism.
- Is any part of the operation per-record conditional? That is the one thing no processor does.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is this collection's declared `dataType` — a record collection, a Text/Number collection, or Apex-defined?" | `sortField` is "required for record collections and collections of Apex-defined variables" and "isn't supported" for primitives (`api_meta.txt` L69994–L69998). The same Sort element needs opposite configuration for the two shapes | The `<variables>` block itself — `dataType`, `isCollection`, `objectType` — rather than a description of the data (Gotcha 1) |
| "Does any field in the mapping need to be computed, or is every target value a direct copy or a literal?" | It decides Map processor vs Transform. `formulaExpression` + `formulaDataType` are documented at API 59.0 on the Transform surface (`api_meta.txt` L70464–L70482); the Map processor predates them | A per-field list marking which targets are copies, which are literals, and which are formulas — the third column is the one that picks the element (Gotcha 3) |
| "Do you need the collection in its *original* order or *unfiltered* form later in this same flow?" | A processor emits a **generated** collection and leaves its input alone (`api_meta.txt` L69942–L69963), so no defensive copy is needed — and the copy costs a Metadata-API-only `Add` that makes the flow un-editable in Builder | A "no" that removes an element, or a "yes" that is satisfied by referencing the original variable, not by copying it (Gotcha 4) |
| "Which element owns the fault path for this collection work?" | `FlowCollectionProcessor` and `FlowTransform` extend `FlowNode`, which declares no `faultConnector` (`api_meta.txt` L69926, L70741–L70756). A processor cannot route its own failure | A named Get Records and a named DML element carrying the `faultConnector`, and an explicit note that the processors between them are one non-faulting span (Gotcha 5) |
| "What number proves this ran correctly, and which variable holds it?" | `FlowTestPoint.elementApiName` accepts only `Start` and `Finish` (`api_meta.txt` L74139–L74146). Nothing between the Filter and the DML is assertable unless a count survives to the end | A Number variable fed by `AssignCount`, named in advance, that the `FlowTest` asserts on (Gotchas 8 and 12) |
| "What `<apiVersion>` will this flow carry, and does it clear every element's floor?" | Each element has a documented floor and the deploy fails on the field, not on the element. There is no API-version-to-release-name table in the developer guides, so a seasonal release name in the answer is unsourced | An explicit number, chosen as the maximum of the floors listed in `references/metadata-examples.md` §1 (`references/llm-anti-patterns.md` Anti-Pattern 4) |
| "Does any downstream action or subflow take a **generic** sObject collection?" | A generic parameter is typed by `FlowDataTypeMapping`, whose `typeName` requires a `T__` prefix for inputs and `U__` for outputs (`api_meta.txt` L70193–L70199) — and `FlowSubflow` has no such field at all | Either a `dataTypeMappings` block on the `actionCalls` element, or a decision to give the subflow a typed input instead (Gotcha 9) |

**What a proper configuration adds over just doing it:** an element chosen from what the operation
*is* rather than from what it reads like, an `<apiVersion>` that clears every floor it depends on,
and a count that a `FlowTest` can fail on — so the flow's silence when it processes zero records
becomes a test failure instead of a support ticket.

---

## Element Selection

The decision this skill exists to make. Read the middle column, not the left one.

| The operation | Element | Metadata shape | Floor |
|---|---|---|---|
| Keep a subset of a collection | Collection Filter | `collectionProcessorType` `FilterCollectionProcessor` + `conditions` **or** `formula`, selected by `conditionLogic` | API 53.0 |
| Order a collection | Collection Sort | `SortCollectionProcessor` + `sortOptions` (`sortField`, `sortOrder`, `doesPutEmptyStringAndNullFirst`) | API 50.0; `sortOptions` API 51.0 |
| Take the top N | Collection Sort | the same, **plus** `limit` — sort applies first | `limit` API 51.0 |
| One output record per input record, values copied or literal | Map processor | `RecommendationMapCollectionProcessor` + `assignNextValueToReference` + `outputSObjectType` + `mapItems` | API 53.0 |
| One output record per input record, some value computed | Transform | `transformType` `Map` + `outputFieldApiName` + `value/formulaExpression` | API 59.0 |
| Collapse a collection to one number | Transform | `transformType` `Sum` or `Count` + `inputParameters` `aggregationValues` / `aggregationField` | API 59.0; `inputParameters` API 60.0 |
| Join two collections | Transform | `transformType` `InnerJoin` + `complexValueType` `JoinDefinition` | API 63.0 |
| Set difference (A − B) | Assignment | `operator` `RemoveAll`, value = the other collection | API 43.0 |
| Set intersection (A ∩ B) | Assignment | `operator` `RemoveUncommon`, both sides collections | API 43.0 |
| Append one record | Assignment | `operator` `Add` (**not** `AddItem`) | — |
| Count a collection | Assignment | `operator` `AssignCount`, collection in `value`, Number in `assignToReference` | API 43.0 |
| Set the *same* field value on every record | Map processor | `outputSObjectType` = the input type, `mapItems` = `Id` + the changed field, then one DML | API 53.0 |
| Anything per-record conditional, or that writes / calls out / shows a screen inside the iteration | Loop | see `flow/flow-loop-element-patterns` | API 30.0 |

Enum values, version floors and field semantics: `api_meta.txt` L69926–L70002 (processors),
L72685–L72814 (Transform), L69767–L69865 (assignment operators).

---

## Collection Typing

Three collection shapes, and what each element accepts:

| Shape | `FlowVariable` | Sort | Filter | Map processor | Transform |
|---|---|---|---|---|---|
| Record collection | `dataType` `sObject`, `isCollection` `true`, `objectType` set | `sortOptions` **must** carry `sortField` | conditions reference `<item>.<Field__c>` | input and output are both typed by `outputSObjectType` | `dataType` `sObject` + `objectType` + `isCollection` |
| Primitive collection (Text, Number, …) | `dataType` `String` / `Number` / …, `isCollection` `true` | `sortField` "isn't supported" — omit it | there are no fields to compare; use `formula` mode | `outputSObjectType` has no meaning for a primitive target | `dataType` `String` / `Number` etc., API 62.0 |
| Apex-defined collection | `dataType` `Apex`, `apexClass` set | `sortField` **required** | — | — | `dataType` `Apex` + `apexClass` |

`isCollection` is documented from API 30.0, and "in API version 32.0 and later, a collection variable
can be of any data type" (`api_meta.txt` L72880–L72884). A collection with no `objectType` is not a
"broken" record collection — it is a differently-typed variable, and the elements will tell you so at
deploy time rather than at run time.

---

## Common Patterns

### Pattern 1: Declarative pipeline — Filter → Sort+limit → Map → DML

The default shape. Each stage names the previous stage as its `collectionReference`; nothing is
mutated in place; the DML at the end consumes the last processor by name. Fully worked, with the
`<start>` block and the fault routing, in `references/metadata-examples.md` §1.

### Pattern 2: Uniform field stamp without a Loop

`outputSObjectType` equal to the *input* type, `mapItems` carrying `Id` plus the one changed field,
then `Update Records` with `inputReference` naming the processor. One element replaces
Loop + Assignment + Assignment. Only valid when the new value is the same for every record.

### Pattern 3: Aggregate to a scalar

A `FlowTransform` with `dataType` `Number`, `isCollection` `false`, and a `transformValueActions`
whose `transformType` is `Sum` or `Count`. The source collection goes in the `aggregationValues`
input key; for `Sum`, the field goes in `aggregationField`. The result is addressed by the
transform's element name — no output-variable field exists (`references/gotchas.md` Gotcha 7).

### Pattern 4: Set algebra instead of a nested loop

One Assignment element: `Add` to seed a working collection, then `RemoveAll` for difference or
`RemoveUncommon` for intersection. Replaces `n×m` element executions with two assignment items.
Declare in the flow's `<description>` that the seeding `Add` is Metadata-API-only.

### Pattern 5: Terminate every chain with a count

An `AssignCount` into a non-collection `Number` variable at the end of the processor chain. It is
the only artefact of the intermediate collections that survives to the `Finish` test point, and it
converts a silent zero-record run into an assertable value. A Decision that only needs "is there
anything?" uses the `IsEmpty` comparison operator instead (API 61.0 and later,
`api_meta.txt` L70097–L70098) — there is no `.size` accessor.

---

## Review Checklist

- [ ] Every `collectionProcessorType` is one of `SortCollectionProcessor`,
      `FilterCollectionProcessor`, `RecommendationMapCollectionProcessor` — checker **E1**.
- [ ] Every Sort carrying `limit` also carries `sortOptions`, or the cap has been pushed onto the
      upstream Get Records instead — checker **E2**.
- [ ] Every Map processor names both `assignNextValueToReference` and `outputSObjectType`, and every
      `mapItems` entry carries all three required fields — checker **E3**.
- [ ] Every `transformType` is one of the documented values, and `GetItemByIndex` / `InvocableAction`
      are not treated as live capabilities — checker **E4**.
- [ ] Every `AssignCount` target is a non-collection `Number` variable — checker **E5**.
- [ ] No `AddItem` targets anything but a `Multipicklist` variable — checker **E6**.
- [ ] No processor carries both `formula` and `conditions` — checker **W1**.
- [ ] No Loop body consists only of Assignments and Decisions — checker **W2**.
- [ ] Every `collectionReference` and aggregation input resolves to a declared variable or element —
      checker **W3**.
- [ ] The fault path hangs off the Get Records and the DML, not off any processor.
- [ ] The flow's `<apiVersion>` clears the highest floor among the elements used.
- [ ] A `FlowTest` asserts on at least one count produced by the chain.

## Recommended Workflow

1. **Classify the operation.** Read the Element Selection table above and name the element before
   writing any XML. If the answer is Loop, stop here and switch to
   `flow/flow-loop-element-patterns`.
2. **Read the collection's typing.** Confirm `dataType`, `isCollection` and `objectType` against the
   Collection Typing table, then set the flow's `<apiVersion>` to the highest floor the chosen
   elements need (the floors are listed per element in `references/metadata-examples.md` §1).
3. **Write the XML from `references/metadata-examples.md` §1**, adapting the object names.
   Round-trip it: `sf project retrieve start --metadata Flow:<name>` and diff, because the guide
   ships no sample XML for `FlowCollectionProcessor` and every shape marked `UNVERIFIED` in that
   file has to come from the org.
4. **Terminate the chain with an `AssignCount`** into a Number variable, and write the `FlowTest`
   from §3 asserting on it. If the collection comes from related records, decide now whether
   `flowTestDataSources` (API 66.0, Apex-backed) is available or the test can only cover the
   triggering record.
5. **Run the checker** —
   `python3 skills/flow/flow-collection-processing/scripts/check_flow_collection_processing.py --manifest-dir <source tree> --strict` —
   and clear every ERROR. Rules map one-to-one onto the Review Checklist above.
6. **Deploy in the order in §4 of `references/metadata-examples.md`** (objects → Apex → Flow →
   FlowTest), then verify with the two SOQL queries and the `FLOW_BULK_ELEMENT_DETAIL` debug-log
   read in §5.
7. **Record anything the guide could not settle** in the flow's `<description>` — the
   Metadata-API-only `Add`, any `UNVERIFIED` shape you confirmed against your own org — using
   `templates/flow-collection-processing-template.md`.

---

## Salesforce-Specific Gotchas

Full statements with grounding in `references/gotchas.md`; the one-line index:

1. The Sort processor accepts three collection shapes and each wants a different `sortOptions`.
2. `AddItem` is a multi-select-picklist operator; `Add` is the collection append.
3. Transform mappings **do** take formula expressions — `formulaExpression` and `formulaDataType`,
   API 59.0.
4. A processor emits a **generated** collection; it does not filter or sort in place.
5. Processors and Transforms have no `faultConnector`; their neighbours own the failure.
6. `collectionFilterCriteria` is a root Flow field named after the Collection Filter and reserved
   for future use.
7. Seven Transform fields and two `transformType` values are documented but inert — including both
   candidates for naming an output variable.
8. Three unrelated things in Flow metadata are called Count.
9. `outputSObjectType` types a processor's output; a *generic* sObject is typed by
   `FlowDataTypeMapping` with a mandatory `T__` / `U__` prefix.
10. Nothing in the developer guides caps collection size — and the flow interview's own limit-usage
    log event is the corroborating negative.
11. The loop iteration variable is a flow resource; the `Add` is what carries an edit out.
12. An empty collection is silent at every stage of a processor chain.

---

## Proactive Triggers

Surface these WITHOUT being asked:

- **A Loop body of only Assignments and Decisions** → Critical. It is a Filter, Sort or Map written
  the long way; name the replacement element.
- **`limit` on a Sort with no `sortOptions`** → Critical. Reads as top N, behaves as arbitrary N.
- **`AddItem` against a collection variable** → Critical. Wrong operator; use `Add`.
- **A Transform or processor with a `faultConnector`** → High. Not a field of those types; the
  deploy will fail.
- **A Map processor missing `assignNextValueToReference`** → High. The `mapItems` have no source
  item to read.
- **A processor chain with no terminal count** → High. Nothing in it is assertable at the `Finish`
  test point.
- **A seasonal release name attached to a collection element's availability** → Medium. State the
  API version; this corpus has no release-name mapping.
- **`assignToReference` or `storeOutputAutomatically` written on a Transform** → Medium. Both are
  reserved; the output is addressed by element name.
- **A collection-size ceiling quoted as a governor limit** → Medium. None is documented; size
  against heap, CPU and the SOQL row budget.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Element selection | Which of Filter / Sort / Map / Transform / Assignment operator / Loop does the task, with the metadata shape and version floor for the choice |
| Deployable flow XML | A processor chain with fault routing on its Get and DML neighbours, shaped from `references/metadata-examples.md` §1 |
| `FlowTest` | Assertions on the counts the chain produces, at the `Finish` test point |
| Checker report | ERROR/WARN findings from `scripts/check_flow_collection_processing.py`, mapped to the Review Checklist |
| Typing plan | `dataType` / `isCollection` / `objectType` for every collection variable, plus any `dataTypeMappings` needed for a generic-sObject consumer |
| Version floor | The `<apiVersion>` the flow must carry, derived from the highest floor among the elements used |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing actual `*.flow-meta.xml`: a complete loop-free processor chain, the Transform `Map` and `InnerJoin` variants, a `FlowTest` with `flowTestDataSources`, `package.xml`, deploy order, and the SOQL + debug-log verification |
| `references/gotchas.md` | The flow deploys and then does the wrong thing quietly — processor output semantics, missing fault paths, the reserved Transform fields, the three Counts, and the two claims this skill previously got wrong |
| `references/llm-anti-patterns.md` | You are reviewing generated Flow XML or Flow advice, or self-checking your own — including `.size`, `AddItem`, release-name dating, and the invented 50,000 collection limit |
| `references/examples.md` | You want the narrative element-selection walk-through, the two routes to a top N, or a worked set-difference before writing XML |
| `references/well-architected.md` | You need the pillar framing, the tradeoff table, or the source and guide line behind any claim in this skill |
| `templates/flow-collection-processing-template.md` | You are recording the design or the review for someone else to act on |
| `scripts/check_flow_collection_processing.py` | Before every deploy and against any fixture directory. `--manifest-dir <source tree>`, optional `--strict`; exits 1 on any ERROR |

## Related Skills

- **flow/flow-loop-element-patterns** — when the answer is a Loop, or a Loop has to be refactored
  out; owns iteration semantics, `noMoreValuesConnector`, and the retired element-count limit.
- **flow/flow-bulkification** — when transaction budgets, data-load volume, or the escalate-to-Apex
  threshold is the question.
- **flow/flow-formula-and-expression-patterns** — when the `formula` on a Filter or the
  `formulaExpression` on a Transform has to be *correct*, not just placed.
- **flow/flow-testing** — when the `FlowTest` strategy, coverage or `sf flow run test` wiring is the
  question rather than what to assert on.
- **flow/flow-record-save-order-interaction** — when a collection DML re-enters the save order and
  the interaction with triggers, validation rules or roll-ups matters.
- **flow/fault-handling** — when the fault routing around the Get and the DML needs designing.
- **flow/subflows-and-reusability** — when a collection crosses a subflow boundary and the input
  contract has to be typed.
