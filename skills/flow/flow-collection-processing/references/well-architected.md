# Well-Architected Notes — Flow Collection Processing

## Relevant Pillars

### Performance

Collection processing decides how many elements execute per transaction and how many database calls
back them. A Filter, Sort, Map or Transform is one node regardless of collection size; the Loop it
replaces is `body_elements × iterations`. The measurable difference is CPU time — 10,000 ms
synchronous / 60,000 ms asynchronous (`apexdev.txt` L19579) — not an element count, because no
element count is budgeted. `FLOW_BULK_ELEMENT_END` logs "element type, element name, number of
records, and execution time" (`apexdev.txt` L38727–L38729), which makes the comparison observable
rather than argued.

### Scalability

The declarative elements are flat in record volume by construction: they take a collection in and
emit a generated collection, with no per-record element execution to multiply. What is *not* flat is
anything that re-queries or re-writes per record, which is why the collection-processing question and
the bulkification question have to be answered together — `flow/flow-bulkification` owns the second
one and the escalate-out-of-Flow threshold.

### Reliability

Collection processors carry no `faultConnector` (see `references/gotchas.md` Gotcha 5), so the
reliability design is entirely in their neighbours: the Get Records that fills the collection and the
DML that drains it. A processor chain fails silently rather than loudly — an empty collection
propagates cleanly through Filter, Sort, Map and DML with no fault raised — so the only reliable
signal is a count. That is why `references/metadata-examples.md` terminates its chain with two
`AssignCount` assignments and asserts on both in the `FlowTest`.

### Operational Excellence

A five-element processor chain states what it does in its element names. The Loop equivalent states
it in branch logic a reviewer has to trace. The cost is portability: the guide ships **no sample XML**
for `FlowCollectionProcessor` or `FlowCollectionMapItem`, so the literal reference syntax has to come
from a round-trip retrieve rather than from the documentation. Budget for that retrieve in any plan
that hand-authors collection processors.

---

## Architectural Tradeoffs

| Decision | Cheaper option | More capable option | What decides it |
|---|---|---|---|
| Narrow a collection | Push the criteria into the upstream Get Records `filters` | Collection Filter downstream | Whether the *unfiltered* collection is needed elsewhere in the flow. If not, filter in the database and skip the element |
| Take a top N | Get Records `sortField`/`sortOrder` + `limit` (API 63.0, values 2–20,000, `api_meta.txt` L71177–L71183) | Sort processor with `sortOptions` + `limit` (API 51.0) | Whether the ranking key is a queryable field. Formula-derived or in-flow-computed keys can only be sorted after retrieval |
| Produce records of another type | Map processor (`RecommendationMapCollectionProcessor`, API 53.0) | Transform (`FlowTransform`, API 59.0) | Whether any target field needs a computed value. `formulaExpression` + `formulaDataType` are documented on the Transform surface at API 59.0 (`api_meta.txt` L70464–L70482); the Map processor predates them |
| Stamp a field on every record | Loop + Assignment + `Add`, then one DML | Map processor whose `outputSObjectType` equals the input type, mapping `Id` + the changed field | The Map version is one element and testable at `Finish`; the Loop version can branch per record. Branching decides it |
| Join two collections | Nested Loop | Transform `InnerJoin` (API 63.0, `api_meta.txt` L72778–L72782) | Org API version, and whether the join definition can be retrieved from Builder — `complexValue` has no documented serialisation |
| Subtract or intersect two collections | Nested Loop with a Decision | Assignment `RemoveAll` / `RemoveUncommon` (API 43.0) | Almost always the operators. The loop version is `n×m` element executions for a documented single-element operation |
| Count a collection | Loop incrementing a counter | Assignment `AssignCount` | Always `AssignCount`. The Loop version also produces nothing a `FlowTest` can assert at `Start` or `Finish` |

---

## Anti-Patterns

1. **A Loop whose body only assigns and branches.** It is a Filter, a Sort or a Map written the long
   way. Checker rule **W2**.
2. **`limit` on a Sort processor with no `sortOptions`.** `limit` applies after the sort
   (`api_meta.txt` L69961–L69967), so with nothing to sort by it takes an arbitrary N and reads as a
   top N. Checker rule **E2**.
3. **A Map processor missing `assignNextValueToReference` or `outputSObjectType`.** The `mapItems`
   have no source item to read from, or the generated collection has no type. Checker rule **E3**.
4. **`AssignCount` into anything but a non-collection `Number` variable.** Checker rule **E5**.
5. **Both `formula` and `conditions` on one processor.** `conditionLogic` selects one; the other is
   dead XML that a reviewer reads as live criteria. The guide never states exclusivity, so this is a
   WARN, not an ERROR — checker rule **W1**.
6. **Claiming a limit the guides do not contain** — a collection element count, a per-interview
   budget, or a release name attached to an element capability with no API version beside it.

---

## Official Sources Used

- **Metadata API Developer Guide — `FlowCollectionProcessor` and `FlowCollectionSortOption`**
  (`api_meta.txt` L69926–L70002): the three `collectionProcessorType` enum values and their API
  version floors; `assignNextValueToReference`; `conditionLogic` including `Formula`; the
  `conditions` / `formula` pair; `limit` applying after the sort with no default; `mapItems`;
  `outputSObjectType`; `sortField` being required for record and Apex-defined collections and
  unsupported for primitives —
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>
- **Metadata API Developer Guide — `FlowTransform`, `FlowTransformValue`,
  `FlowTransformValueAction` and `FlowTransformValueActionInputParameter`**
  (`api_meta.txt` L72685–L72814): the `transformType` enum (`Count`, `GetItemByIndex`, `InnerJoin`,
  `InvocableAction`, `Map`, `Sum`) with `InnerJoin` at API 63.0 and excluded from
  `FlowInlineTransform`; the `aggregationField` / `aggregationValues` input keys; the seven fields
  marked "Reserved for future use" that make a Transform's output un-nameable — same PDF
- **Metadata API Developer Guide — `FlowElementReferenceOrValue`** (`api_meta.txt` L70411–L70525):
  `formulaExpression` and `formulaDataType` at API 59.0 with their explicit "See FlowTransform"
  cross-reference, which is what refutes the "Transform cannot use formulas" claim this skill
  previously carried; `complexValueType` `JoinDefinition` and `complexValue` for `InnerJoin` — same PDF
- **Metadata API Developer Guide — `FlowAssignmentOperator`** (`api_meta.txt` L69767–L69865): `Add`
  and `AddAtStart` as the collection append operators, `AddItem` as multipicklist-only, `AssignCount`
  taking the collection in `value`, `RemoveAll` as difference and `RemoveUncommon` as intersection,
  all at API 43.0 and later — same PDF
- **Metadata API Developer Guide — `FlowTest` and subtypes** (`api_meta.txt` L73960–L74330):
  `elementApiName` restricted to `Start` and `Finish`; `testType` `WithAssertion` required from API
  66.0; `flowTestDataSources` requiring an Apex class as the only documented way to seed non-triggering
  records; the `FlowTestParameter` type enum — same PDF
- **Metadata API Developer Guide — `FlowRecordLookup`** (`api_meta.txt` L71091–L71252): `limit` as a
  `FlowElementReferenceOrValue` with valid values 2–20,000, API 63.0 and later; the
  `getFirstRecordOnly` / `storeOutputAutomatically` / `outputReference` coupling that decides whether
  a Get Records yields a collection at all — same PDF
- **Apex Developer Guide — Execution Governors and Limits** (`apexdev.txt` L19544–L19579): 50,000
  records retrieved by SOQL per transaction, 150 DML statements, 10,000 DML rows, 6 MB / 12 MB heap,
  10,000 ms / 60,000 ms CPU. Used for the limits framing and for the negative: none of these is a
  collection size, and a grep of this guide for a retired 2,000-executed-element Flow limit returns
  nothing in either direction —
  <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>
- **Apex Developer Guide — Flow debug-log events** (`apexdev.txt` L38714–L38850):
  `FLOW_BULK_ELEMENT_DETAIL` / `_END` reporting per-element record counts and execution time, and
  `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` enumerating every limit a flow interview reports against —
  a list that contains no element count and no collection size — same PDF
- **Repo templates** — `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` (the `<start>` block
  and fault-path convention that `references/metadata-examples.md` adapts) and
  `templates/flow/FaultPath_Template.md` (fault routing, which for a processor chain hangs off the
  Get Records and the DML, never off the processors)
- **Salesforce Well-Architected Framework** — pillar framing for the tradeoff table above —
  <https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html>

### Sources deliberately not cited as authority

Flow Builder's element UI — the Transform mapping editor, the Collection Filter condition builder,
and the labels "Map" and "Collection Filter" themselves — is documented only on
help.salesforce.com, which cannot be fetched. Every claim in this skill about **metadata** is
grounded above; every claim about what the **Builder UI** exposes carries an `UNVERIFIED
(2026-09-05)` marker beside it in `references/gotchas.md` and
`references/metadata-examples.md`. There is no API-version-to-release-name table anywhere in this
corpus, which is why this skill states API numbers and not seasonal release names.
