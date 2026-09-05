# LLM Anti-Patterns — Flow Collection Processing

Mistakes AI coding assistants make when choosing or configuring Flow collection elements — Loop,
Collection Filter, Collection Sort, the Map processor, Transform, and the `FlowAssignmentOperator`
set. Use them to self-check generated output before it is presented as an answer.

Three entries below (4, 6, 9) exist because an **earlier version of this skill** stated the wrong
thing. They are kept in corrected form so the wrong version does not come back.

Two neighbouring traps live in siblings and are deliberately not repeated here: inventing
`MapCollectionProcessor` (`flow/flow-loop-element-patterns` Anti-Pattern 8) and quoting the retired
2,000-executed-element ceiling (same file, its unnumbered anti-pattern).

---

## Anti-Pattern 1: Using a Loop to filter a collection instead of Collection Filter

**What the LLM generates:**

```text
[Loop: For each record in allContacts]
    [Decision: Is Status = Active?]
        Yes --> [Assignment: Add to activeContacts collection]
        No  --> (skip)
```

**Why it happens:** loops map onto every imperative language the model has read. The Collection
Filter element does the same job in one node.

**Correct pattern:** a single `collectionProcessors` element with
`collectionProcessorType` = `FilterCollectionProcessor`, `collectionReference` naming the input, and
either `conditions` or `formula` selected by `conditionLogic`.

**Detection hint:** a Loop whose body is only `assignments` and `decisions` — no DML, action,
subflow or screen. `scripts/check_flow_collection_processing.py` rule **W2** is exactly that shape.
`flow/flow-loop-element-patterns` owns the refactor mechanics.

---

## Anti-Pattern 2: Placing DML inside a Loop when processing a collection

**What the LLM generates:** a `recordUpdates` element reachable from a Loop's `nextValueConnector`.

**Why it happens:** per-item update is the simplest mental model, and it is correct in most
languages. Here it converts record volume into DML statement count against a per-transaction budget
of 150 (`apexdev.txt` L19554).

**Correct pattern:** stage into a collection, write once after the loop. This is `flow/flow-bulkification`'s
territory end to end; do not re-derive the scale math in a collection-processing answer.

**Detection hint:** `recordCreates` / `recordUpdates` / `recordDeletes` reachable from a
`nextValueConnector`.

---

## Anti-Pattern 3: Reaching for a Loop when the operation has a named element

**What the LLM generates:** a loop that builds one output record per input record with three or four
Assignment elements, when the operation is a mapping.

**Why it happens:** the model knows `for (x : list) { … }` far better than it knows a five-value
element vocabulary.

**Correct pattern — pick by what the operation *is*, not by how it reads:**

| The operation | The element | Metadata |
|---|---|---|
| keep a subset | Collection Filter | `collectionProcessorType` = `FilterCollectionProcessor` |
| order, or take a top N | Collection Sort | `SortCollectionProcessor` + `sortOptions` + `limit` |
| produce one output record per input record | Map processor | `RecommendationMapCollectionProcessor` + `outputSObjectType` + `mapItems` |
| aggregate a collection to one value | Transform | `transformType` = `Sum` or `Count` |
| join two collections | Transform | `transformType` = `InnerJoin` (API 63.0+) |
| subtract / intersect two collections | Assignment | `RemoveAll` / `RemoveUncommon` |
| count a collection | Assignment | `AssignCount` |
| anything per-record that calls out, writes, or branches to a screen | Loop | — |

**Detection hint:** count the elements. Any loop body of three-plus Assignments that constructs a
record is a Map processor written the long way.

---

## Anti-Pattern 4 (corrected): Dating Collection Sort to the wrong release, or denying it exists

**What the LLM generates:**

> "Flow does not have a native sort capability, so you need Apex to sort the collection before
> displaying it."

or, from a model that has heard of the element:

> "Collection Sort was introduced in Spring '22, so check your org's version."

**Why it happens:** the first is pre-2021 training data. The second is the more dangerous failure —
it *sounds* like a version check, so a reader trusts it, and it is wrong: the guide dates
`SortCollectionProcessor` to **API version 50.0 and later**, with
`RecommendationMapCollectionProcessor` and `FilterCollectionProcessor` both at **API 53.0 and later**
(`api_meta.txt` L69934–L69940). `sortOptions` and `limit` arrived separately, at API 51.0
(L69961–L69967, L69981–L69982).

**Correct version:** state API version numbers, not release names. This corpus — the Metadata API
Developer Guide, the Apex Developer Guide, the App Limits Cheat Sheet — contains **no
API-version-to-release-name mapping**, so any sentence of the form "API 53.0, which is Winter '22"
is being supplied from memory, not from the docs. If the release name matters to the reader, say
which API version the guide states and let them map it.

**Detection hint:** a seasonal release name attached to a Flow element capability, with no API
number beside it.

---

## Anti-Pattern 5: Adding to a collection variable that was never declared

**What the LLM generates:** an Assignment with `operator` `Add` targeting `outputCollection`, and no
matching `<variables>` block.

**Why it happens:** in most languages the accumulator is declared where it is first used. In Flow it
is a separate resource with `dataType`, `isCollection` `true`, and — for a record collection —
`objectType` (`api_meta.txt` L72850–L72884).

**Correct pattern:** declare the variable first. `Add` "isn't supported when the `assignToReference`
field is a variable of type `boolean`, `dateTime`, or `sObject`" (L69791–L69792) — so an accumulator
declared as a record variable rather than a record *collection* variable fails at the operator, and
the XML looks right.

**Detection hint:** every `assignToReference` and every `collectionReference` must resolve to a
`<variables>` name or another element name. Checker rule **W3** reports the ones that do not.

---

## Anti-Pattern 6 (corrected): Inventing a `.size` property on a collection

**What the LLM generates:**

```text
[Decision: {!myCollection.size} > 10]
```

often introduced, as here, as the *fix* for a counter loop — which makes it doubly convincing,
because the diagnosis is right and only the cure is fabricated.

**Why it happens:** `.size` reads like a property, and Apex genuinely has `List.size()`. Flow
formula syntax has no such accessor documented in this corpus, and no element exposes one.

**Correct version:** one Assignment element, `operator` `AssignCount`, with the **collection in
`value`** and a non-collection `Number` variable in `assignToReference`
(`api_meta.txt` L69813–L69818). For a pure emptiness test, the `IsEmpty` comparison operator —
"an empty collection", API 61.0 and later (L70097–L70098) — works directly in a Decision without
counting anything.

**Detection hint:** grep generated Flow guidance for `.size`, `COUNT(` and `.length` applied to a
Flow collection. None of the three is a documented Flow accessor.

---

## Anti-Pattern 7: Using `AddItem` to append to a collection

**What the LLM generates:**

```xml
<assignmentItems>
    <assignToReference>legsToUpdate</assignToReference>
    <operator>AddItem</operator>
    <value><elementReference>currentLeg</elementReference></value>
</assignmentItems>
```

**Why it happens:** it is the best-named operator in the enum for the job it is not for. `AddItem`
is "supported only when the `assignToReference` field is a variable of type multipicklist"
(`api_meta.txt` L69799–L69802). The model picks it over `Add` because `Add` is overloaded across
number, date, string, picklist and collection targets, and therefore reads less specific.

**Correct pattern:** `Add` on a collection variable appends to it (L69786–L69790); `AddAtStart`
prepends (L69794–L69797).

**Detection hint:** `<operator>AddItem</operator>` whose `assignToReference` names a variable with
`isCollection` `true` or `dataType` other than `Multipicklist`.

---

## Anti-Pattern 8: Filling in every documented field of a Transform

**What the LLM generates:** a `<transforms>` element carrying `actionName`, `actionType`,
`assignToReference` and `storeOutputAutomatically`, on the reasoning that a documented field is a
usable field.

**Why it happens:** the "Reserved for future use" annotation is the last phrase on a line in a PDF
table and is the easiest thing in the section to lose. Four fields of
`FlowTransformValueAction`, three of `FlowTransformValue`, and `FlowTransform.storeOutputAutomatically`
all carry it (`api_meta.txt` L72726, L72739–L72743, L72758–L72765). Two `transformType` values —
`GetItemByIndex` and `InvocableAction` — carry it too (L72777, L72783).

**Correct pattern:** write `transformType`, `outputFieldApiName`, `inputParameters` and `value`, and
nothing else. In particular, **do not claim a Transform can write to a named output variable**:
the two fields that would do it are both reserved, so the result is addressed by the element's own
name.

**Detection hint:** any generated Flow XML containing `<assignToReference>` inside `<transforms>`,
or any prose that says "store the Transform output in variable X".

---

## Anti-Pattern 9 (corrected): Asserting that Transform mappings cannot compute

**What the LLM generates:**

> "The Transform element only supports direct field-to-field mapping or literal values. If you need
> to combine two fields, compute the value in an Assignment before the Transform."

**Why it happens:** it is true of the older Map processor, it is the kind of limitation declarative
tools usually have, and — until this revision — **this skill said it**. A claim that a tool *cannot*
do something is rarely challenged, because nobody goes looking for the field that would prove it
wrong.

**Correct version:** `FlowElementReferenceOrValue.formulaExpression` and `formulaDataType` are
documented at API version 59.0 and later and both cross-reference `FlowTransform` explicitly
(`api_meta.txt` L70464–L70482). They are the Transform element's formula surface. The general rule:
before writing "X does not support Y", search the type of the field where Y would live — a
capability that exists usually leaves a field behind.

**Detection hint:** any unqualified "does not support" claim about a Flow element, with no field
name or line reference next to it.

---

## Anti-Pattern 10: Putting collection filter criteria under `collectionFilterCriteria`

**What the LLM generates:** a root-level `<collectionFilterCriteria>` block holding the conditions
for a Collection Filter.

**Why it happens:** it is the closest name in the `Flow` type's field table to the Builder element
"Collection Filter", and it sits directly above the field that actually implements it. Its full
documented description is **"Reserved for future use"** (`api_meta.txt` L68090).

**Correct pattern:** filter criteria go in a `<collectionProcessors>` element with
`collectionProcessorType` = `FilterCollectionProcessor`. Exactly two root arrays do collection work:
`collectionProcessors` (API 50.0+, L68092–L68093) and `transforms` (API 59.0+, L68435–L68436).

**Detection hint:** grep generated Flow XML for `collectionFilterCriteria`. It should never appear.

---

## Anti-Pattern 11: Inventing a Flow "collection element count limit" of 50,000

**What the LLM generates:**

> "The collection element count limit is 50,000 rows per Flow interview — not 10,000 DML rows, but
> 50,000 in-memory records across all collections. A Get Records returning 50k+ will fault."

**Why it happens:** 50,000 *is* a real Salesforce number — the per-transaction cap on **total
records retrieved by SOQL queries** (`apexdev.txt` L19546). The relabelling is self-reinforcing: the
model contrasts it explicitly against the 10,000-DML-row limit, and that contrast makes it read like
a carefully distinguished, separately-named governor. It is not. Flow has no limit called a
collection element count, and nothing caps how many records a collection variable may hold.

The prediction happens to land ("a Get Records returning 50k+ will fault"), which is why it survives
casual review. The *reasoning* is wrong in ways that change real decisions:

- Under the invented limit, splitting one Get Records into three smaller ones looks like it helps.
  It does not — all three draw on the same 50,000 query-row budget.
- Under the invented limit, the budget belongs to the interview. It belongs to the **transaction**,
  shared with every trigger, Apex class and other flow in the same call stack — so a flow can blow
  it without querying 50,000 rows itself.
- Under the invented limit, re-using or copying a collection looks costly. It is not; only the query
  is.

**Correct version:** 50,000 = total records retrieved by SOQL per **transaction**. Collection size
is otherwise bounded by **heap** (6 MB synchronous / 12 MB asynchronous, `apexdev.txt` L19577) —
the limit that actually constrains large in-memory collections. DML rows remain 10,000 per
transaction (L19556).

**Detection hint:** grep for `collection element count`, or for `50,000` described as
per-*interview* rather than per-*transaction*. The generalisable rule: **when a limit is introduced
by contrasting it with another limit ("not X, but Y"), check that Y has a documented name.**
Fabricated governors are frequently born from that construction — the contrast supplies the
appearance of precision that the invented limit lacks on its own. Also flag any per-transaction
Salesforce budget described as belonging to a single flow, trigger or interview; almost all of them
are shared across the whole call stack.
