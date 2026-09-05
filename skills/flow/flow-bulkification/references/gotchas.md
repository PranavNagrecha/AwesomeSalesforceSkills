# Gotchas — Flow Bulkification

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## A Single UI Test Does Not Prove Bulk Safety

**What happens:** A flow appears correct because it works when one user updates one record in a sandbox.

**When it occurs:** The design was only validated through manual UI testing and never exercised through imports, APIs, or mass updates.

**How to avoid:** Test with realistic batches and review the element sequence for per-record queries or DML.

---

## Subflows Still Consume The Parent Transaction Budget

**What happens:** Teams move logic into a subflow and assume the limits reset.

**When it occurs:** A parent flow calls a subflow from inside a high-volume record-triggered transaction.

**How to avoid:** Treat subflows as organization tools, not limit boundaries. The bulk-safe design still has to exist end to end.

---

## Before-Save And After-Save Are Not Interchangeable

**What happens:** A same-record field update is implemented in after-save, consuming extra DML and sometimes re-triggering automation.

**When it occurs:** Teams default everything to after-save because it feels more flexible.

**How to avoid:** Use before-save whenever the requirement is only to update fields on the triggering record.

---

## Apex In The Middle Of A Bad Flow Is Still A Bad Flow

**What happens:** A loop calls invocable Apex and the team assumes the Flow is now bulkified.

**When it occurs:** Invocable methods are added without checking whether the method accepts lists and handles the batch efficiently.

**How to avoid:** Review the Flow and the Apex boundary together. The number of calls and the list contract both matter.

---

## The Platform Bulkifies Across Interviews, Never Inside One

**What happens:** A 200-record load starts 200 interviews, and the platform executes each
*element* once across the set rather than once per interview — but a Loop inside a single
interview is still stepped one item at a time. Teams read "Flow bulkifies automatically"
and conclude the second half is covered by the first.

The debug log states both halves plainly. `FLOW_START_INTERVIEWS_BEGIN` logs "Requests"
— plural — for the set (`apexdev.txt` L38856–38860). `FLOW_BULK_ELEMENT_DETAIL` and
`FLOW_BULK_ELEMENT_END` log "Interview ID, element type, element name, **number of
records**, and execution time" (L38721–38729), and `FLOW_BULK_ELEMENT_LIMIT_USAGE` logs
"Incremented usage toward a limit for this bulk element" itemised across SOQL queries,
SOQL query rows, DML statements, DML rows, CPU time and heap (L38730–38744). Limit usage
is charged **per bulk element**. And the platform says out loud where bulk execution
stops: `FLOW_BULK_ELEMENT_NOT_SUPPORTED` logs the "Operation, element name, and entity
name that doesn't support bulk operations" (L38746–38747) — an event that would not need
to exist if everything were bulkified. Against that, `FLOW_LOOP_DETAIL` logs "Interview ID,
index, and value. The index is the position in the collection variable for the item that
the loop is operating on" (L38843–38846) — one entry per iteration, with no bulk-element
grouping around it.

**When it occurs:** Any record-triggered flow reached by Data Loader, Bulk API, a
composite REST call, or a mass update from a list view.

**How to avoid:** Read the two log shapes as the definition of what is and is not
automatic. An element on the interview's straight-line path is charged once for the batch;
the same element on a Loop's `nextValueConnector` path is charged once per item per
interview. Design so that every database element sits on the first path.
**UNVERIFIED (2026-09-05):** neither `apexdev.txt` nor `api_meta.txt` states the batching
*mechanism* — how many interviews are grouped into one bulk element, or whether a
`recordUpdates` from twenty interviews becomes one DML statement or twenty. The log events
above prove that elements are executed and charged as bulk units, and
`FLOW_BULK_ELEMENT_NOT_SUPPORTED` proves that some operations are excluded, but neither
names which operations those are. Measure `FLOW_BULK_ELEMENT_LIMIT_USAGE` on a real load
and read the log for `FLOW_BULK_ELEMENT_NOT_SUPPORTED` rather than quoting a ratio.

---

## `getFirstRecordOnly` And `storeOutputAutomatically` Are Coupled, And The Wrong Pair Returns One Row

**What happens:** A Get Records that is supposed to feed a Loop returns a single record.
The flow runs, the Loop iterates once, one child row gets stamped per parent, and nobody
notices until a customer asks why only the first line item updated.

**When it occurs:** When `<getFirstRecordOnly>` is left at `true` on an element cloned
from a single-record lookup, or when `<storeOutputAutomatically>` is flipped without
revisiting the other two fields.

**How to avoid:** The three fields are one decision, and the guide couples them
explicitly. `getFirstRecordOnly` "Indicates whether to store field values for only one
record, even when multiple records meet the filter criteria. Supported only when
`storeOutputAutomatically` is true. When `storeOutputAutomatically` is false, what
determines whether one or multiple records are stored is whether `outputReference`
specifies a record variable or a record collection variable" (`api_meta.txt`
L71153–71162). `outputReference` and `outputAssignments` are both "Supported only when
`storeOutputAutomatically` is false" (L71195–71200, L71188–71193). So there are exactly
two valid shapes for a collection-feeding Get: auto-output with
`<getFirstRecordOnly>false</getFirstRecordOnly>`, or manual output with an
`<outputReference>` pointing at a variable whose `<isCollection>` is `true`. Any third
combination is a single-record read wearing a collection's clothes.

---

## The Assignment That Merges Two Collections Cannot Survive Flow Builder

**What happens:** A hand-written or generated flow appends one collection to another with
`<operator>Add</operator>`. It deploys, it runs, it is correct. Months later an admin
opens the flow to change a label, saves, and the merge is gone or the save is refused.

**When it occurs:** On any flow whose Assignment element passes a *collection* variable as
the `<value>` of an `Add` — the "combine these two staged lists before the single DML"
shape that bulk designs reach for.

**How to avoid:** The guide is explicit that this is a Metadata-API-only capability:
appending a collection as the value is "available in API version 43.0 and later, but only
via Metadata API. From Flow Builder, you can't save an Assignment element that contains a
collection variable in the Value column for the Add operator" (`api_meta.txt`
L69786–69790). Adding a *single record* to a collection is fine in both surfaces and is
what the worked flows in `references/metadata-examples.md` use. If you genuinely need to
merge two collections, either loop the second one and append item by item, or accept that
the flow is now Metadata-API-owned and say so in its `<description>` so the next admin
does not silently destroy it.

---

## A Scheduled Flow With `<object>` Has No Batch-Size Dial At All

**What happens:** A nightly flow is pointed at an object with a filter, works on 300
records in a sandbox, and in production starts one interview per matching record with no
way to bound the run.

**When it occurs:** The moment `<object>` appears on a `<start>` whose `<triggerType>` is
`Scheduled`.

**How to avoid:** Read what `<object>` means on a Start element: "The object whose records
you want to retrieve from the database. A flow interview starts for each record that meets
the filter conditions" (`api_meta.txt` L72424–72428). Then check `FlowSchedule` for a
batch-size field — it has `frequency`, `startDate`, `startTime`, `dayOfMonthToRun`,
`daysOfWeekToRun`, `endDate`, `endTime` and `frequencyNumber`, and nothing else
(`api_meta.txt` L71335–71386). The only documented batch-size control in the whole Flow
metadata surface is `FlowScheduledPath.maxBatchSize`, "from 1 to 200. Default is 200"
(L71397–71398), which belongs to scheduled *paths* on record-triggered flows — see
`flow/record-triggered-flow-patterns` `references/gotchas.md` § scheduled path batching.
For a scheduled job you need to bound, omit `<object>`, run one interview, and control the
working set with the Get's `<limit>` and a Collection Sort `<limit>`
(`references/metadata-examples.md` § 4).

---

## Update Records Has No All-Or-None Switch — But Create Records In Upsert Mode Does, And It Defaults To All-Or-None

**What happens:** A design assumes Flow has no partial-success mode anywhere, reaches for
invocable Apex to get one, and never notices the switch that already exists on a different
element. Or the opposite: a team turns on upsert, assumes it behaves like the Update
element, and gets a silent partial write where they expected a clean rollback.

**When it occurs:** On any bulk write where some rows can fail validation — which is every
integration path.

**How to avoid:** The two elements are genuinely different, and the difference is visible
in the field lists. `FlowRecordUpdate` has exactly `connector`, `faultConnector`,
`filters`, `inputAssignments`, `inputReference` and `object` (`api_meta.txt`
L71279–71296): no all-or-none field, so one failing row fails the whole collection.
`FlowRecordCreate` carries `doesUpsert` (API 62.0+) and `doesUpsertAllOrNone`: "If set to
true and a record fails, then the transaction rolls back and no records are created or
updated. If set to false, the transaction creates or updates only the records that are
successful. **The default value is true**" (`api_meta.txt` L70953–70963). So partial
success on a bulk write is reachable declaratively — through Create-as-upsert with
`doesUpsertAllOrNone` set to `false`, on API 62.0 and later — and it is off by default.
Decide it explicitly rather than inheriting it.

---

## A Loop Without `noMoreValuesConnector` Throws Away Everything It Staged

**What happens:** The Loop iterates, the Assignment appends every record to the collection
variable, and then the interview ends. No error, no fault, no rows written. The flow looks
busy in the debug log and changes nothing.

**When it occurs:** Whenever the "after last" path is left unconnected — easy to do in
auto-layout, and easy to produce when generating flow XML, because the guide's own
autolaunched sample defines a `<loops>` element with a `<nextValueConnector>` and **no**
`<noMoreValuesConnector>` (`api_meta.txt` L73747–73757).

**How to avoid:** `noMoreValuesConnector` is "The element to navigate to when all entries
in the collection have been iterated through" (`api_meta.txt` L70716–70717). In a
bulkified flow it is not optional decoration — it is where the single DML lives, and it is
the entire payoff of staging into a collection. Treat a Loop with no
`noMoreValuesConnector` in a flow that declares a collection variable as a defect;
`scripts/check_flow_bulkification.py` reports it. Contrast the silent-failure signature
with an empty-collection Update, which is also silent but is genuinely harmless —
`flow/flow-loop-element-patterns` `references/gotchas.md` § empty collection.

---

## "Batches Of 200" Is A DML Chunk Size, Not A Flow Setting — And Limits Reset Per Chunk

**What happens:** A team tests a flow with a 10,000-row Data Loader file, sees it succeed,
and concludes the flow is safe at 10,000. It is safe at 200. The other 9,800 rows proved
nothing except that 200 works fifty times.

**When it occurs:** On every "we load-tested it" claim that does not name the chunk size.

**How to avoid:** The chunking is a platform behaviour, not a Flow feature. "DML
operations that include over 200 records are processed in batches, and the trigger is
invoked for each batch" (`apexdev.txt` L15029–15034), and for the API path: "In Salesforce
API version 21.0 and later, no further splits of API chunks occur. If a Bulk API request
causes a trigger to fire multiple times for chunks of 200 records, **governor limits are
reset between these trigger invocations for the same HTTP request**" (L14904–14907). One
chunk is one transaction with one full budget. That cuts both ways: the good news is a
50,000-row load will not accumulate SOQL across the whole file; the bad news is that a
flow which needs 101 queries for 200 records fails on every single chunk, and the only
load test that means anything is the one where a chunk fits. Size the scale math against
200 unless you have measured otherwise (`SKILL.md` § Scale Math Worksheet).

---

## An Invocable Apex Action Called From A Record-Triggered Flow Gets A List, And A Mismatched Result Corrupts Data Quietly

**What happens:** An invocable method accepts a list, does its work, and returns a list of
a different length or a different order. Nothing throws. Each flow interview reads the
output slot that corresponds to its position, and the wrong answer lands on the wrong
record.

**When it occurs:** Any time an Apex action is called from a record-triggered flow that is
reached in bulk — which the Apex Developer Guide names as the canonical case.

**How to avoid:** "For a correct bulkification implementation, the Inputs and Outputs must
match on both the size and the order. For example, the i-th Output entry must correspond
to the i-th Input entry. Matching entries are required for data correctness when your
action is in bulkified execution, such as when an apex action is used in a record trigger
flow" (`apexdev.txt` L5456–5458). Note the phrasing: *data correctness*, not an exception.
Review the Apex and the flow together — a method that filters its input, skips a row, or
returns early breaks the positional contract even when it looks defensive. See
`apex/invocable-methods` for the method-side rules.

---

## Two `<limit>` Fields, Two Types, Two Meanings

**What happens:** A generated flow puts `<limit>200</limit>` on a Get Records and the
deploy fails, or puts a `<numberValue>` wrapper on a Collection Sort and the same happens.
Worse, a sort limit is read as "process the first 200 rows returned" when it means "keep
200 after sorting".

**When it occurs:** Any time bulk work is bounded — which is the whole point of a batch
flow.

**How to avoid:** They are different fields on different types.
`FlowRecordLookup.limit` is a `FlowElementReferenceOrValue`: "Specifies the maximum number
of records to store. Valid values are between 2 and 20,000. Supported only when
`getFirstRecordOnly` is false", API 63.0+ (`api_meta.txt` L71177–71183) — so it takes a
wrapped `<numberValue>`. `FlowCollectionProcessor.limit` is a plain `int`: "The maximum
number of records to include in the generated collection. There's no default value. All
items of the collection are kept if it's greater than the size of the collection. If
`sortField` and `sortOrder` are also specified, **the records are sorted before the limit
takes effect**", API 51.0+ (`api_meta.txt` L69961–69967). Sort-then-limit is what makes
"the 500 oldest" a meaningful bound; limit-then-sort would be an arbitrary 500 in a tidy
order. Both worked examples are in `references/metadata-examples.md` §§ 3–4.
