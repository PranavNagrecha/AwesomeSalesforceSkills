# Gotchas — Flow Loop Element Patterns

Non-obvious Salesforce platform behaviors around the Loop element that cause real production failures. Every gotcha here has bitten a real practitioner; none are theoretical.

Grounding convention: `api_meta.txt` = Metadata API Developer Guide (Summer '26 / v62 PDF,
`https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf`);
`apexdev.txt` = Apex Developer Guide
(`https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf`).
Line numbers are `grep -n` positions in the extracted text.

---

## Gotcha 1: Editing the loop variable persists nothing — the `Add` is what carries the edit out

**What happens:** Inside `Loop: Rank_Applications`, an Assignment sets
`{!currentApp.Rank__c} = {!rankCounter}`. The flow runs green, the debug pane shows the new
value, and the database is unchanged. Practitioners read "I changed the field" as "I saved
the field" and skip both the staging `Add` and the post-loop Update Records.

The metadata is unambiguous about direction. `FlowLoop.assignNextValueToReference` is "The
variable that's assigned to the current value in the collection before navigating to the
target of `nextValueConnector`" (`api_meta.txt` L70701–70702) — the collection's value is
assigned *into* a variable. No field on `FlowLoop` describes a write-back from that
variable into `collectionReference`, and `FlowLoop` has only five fields
(`assignNextValueToReference`, `collectionReference`, `iterationOrder`,
`nextValueConnector`, `noMoreValuesConnector` — `api_meta.txt` L70698–70716). Nothing in
the element is a persistence mechanism.

**UNVERIFIED (2026-09-05):** whether an in-loop write to the loop variable *also* mutates
the item still held in the source collection is stated nowhere in `api_meta.txt` or
`apexdev.txt`. Earlier versions of this skill asserted it does ("a reference, not a copy")
and built the refactor's justification on that aliasing; that justification is withdrawn.
The staged-collection construction is correct whichever way the runtime behaves, which is
precisely why it is the one to build — never write a flow whose correctness depends on the
answer.

**When it occurs:** Any Loop body that uses Assignment to set a field on the loop variable
without a matching `Add` into a separate SObject Collection plus a post-loop Update Records.

**How to avoid:** Treat every Assignment-on-loop-variable as half a refactor. The same
Assignment element should end with `applicationsToStamp` `Add` `{!currentApp}`, and one
`recordUpdates` on `applicationsToStamp` sits after the loop. `references/metadata-examples.md`
§2 is that shape.

---

## Gotcha 2: Loop variables are flow-scoped, so they survive the loop

**What happens:** After the loop's `noMoreValuesConnector` fires, the variable named by
`assignNextValueToReference` is NOT cleared. It holds the last iterated record (or stays
null if the collection was empty). A downstream element that references it gets that value,
with no warning.

**When it occurs:** Reviewers copy-paste merge-field references; developers reuse the loop
variable as scratch space elsewhere in the flow. The empty-collection path is the sharp
edge — the variable is never assigned at all, so downstream references resolve to null.

**How to avoid:** Never reference a loop's variable outside its body. If you genuinely want
"the last record processed", capture it into a clearly-named variable with an Assignment
inside the loop. The one deliberate exception is a `FlowCollectionProcessor` formula placed
inside an outer loop: it references the outer loop's variable *on purpose*, which is what
makes the Filter-instead-of-nested-loop substitution in `references/metadata-examples.md`
§3 legal.

---

## Gotcha 3: The 2,000-executed-element ceiling is absent from the developer guides entirely

**What happens:** Designers decompose a perfectly viable flow, or escalate it to invocable
Apex, to dodge a per-interview limit of 2,000 executed elements.

**What the guides say: nothing.** `grep -n -i "2,\?000"` across `api_meta.txt`,
`apexdev.txt`, and the Salesforce App Limits Cheat Sheet returns no line that also contains
`element`, `interview`, or `iteration`. The error string `Number of iterations exceeded`
does not appear in any of the three. The cheat sheet has **no Flow or flow-interview limits
of any kind** — its only `flow` matches are the word "workflow" in unrelated rows. The
sibling `flow/flow-bulkification` reached the same conclusion from the same corpus. Neither
is there a debug-log event for executed elements: the Workflow-category event list runs
from `FLOW_ACTIONCALL_DETAIL` through `FLOW_VALUE_ASSIGNMENT` (`apexdev.txt` L38715–38900)
with no element-count entry.

Salesforce's KB "Flow Error 'Number of Iterations Exceeded'" states *"In Salesforce Flow API
version 56.0 and earlier, a maximum of 2000 Flow elements can be executed at runtime"* and
*"In API version 57.0, the limit of 2000 Flow elements was removed"* (API 57.0 = Spring '23).
That KB is the only source for the claim in either direction, and it is not a developer
guide — so a flow whose own `<apiVersion>` is 56.0 or earlier is the one narrow place the
old ceiling can still be in play, and the developer guides will not help you confirm it.

**When it occurs:** Any design conversation that opens with an element-count budget. The
tell for a stale claim is that it names 2,000 without naming an API version — the version
qualifier is the load-bearing half.

**How to avoid:** Estimate `body_elements × expected_iterations` anyway, but read the answer
as a CPU-time proxy, not a check against a ceiling. The real ceilings are documented and
numeric: 10,000 ms synchronous / 60,000 ms asynchronous CPU time, 100 synchronous SOQL
queries, 150 DML statements (`apexdev.txt` L19579, L19544, L19554). Check the flow's own
`<apiVersion>` before ruling the retired limit in or out; the fix there is bumping the
version, not redesigning the loop.

---

## Gotcha 4: DML / SOQL budgets are shared across the WHOLE transaction

**What happens:** The 150-DML and 100-SOQL caps are per-transaction, not per-flow
(`apexdev.txt` L19544, L19554 — the synchronous column). A loop with 1 DML inside that runs
100 iterations uses 100 of the 150 DML statements. If a record-triggered Apex trigger and
three other flows run in the same transaction (very common in mature orgs), the Loop's
"safe-looking" 100 DML pushes the cumulative count past 150 and the LAST automation to fire
takes the failure — often blamed on the wrong code.

**When it occurs:** Mature orgs with stacked automation; record-triggered flows where a
downstream After Save flow chains into a third flow.

**How to avoid:** Treat any in-loop DML as a P0 even if the math says "it would only be 50
statements." Refactor to one DML statement per loop. This is non-negotiable in any flow that
runs in a Bulk API path. `flow/flow-bulkification` owns the full framing.

---

## Gotcha 5: Subflow-in-loop hides DML and SOQL from a casual review

**What happens:** A reviewer scans the parent flow, sees a Loop calling a Subflow, and waves
it through because "the subflow looks reusable." Open the subflow — it does Get Records and
Update Records every invocation. The parent loop bulkifies-fails just as if the DML were
inline, but the failure trace points at the subflow, making diagnosis confusing.

**When it occurs:** Org has many small "utility" subflows that were authored for one-record
callers and got reused inside loops without re-bulkification.

**How to avoid:** Reviewing a loop is incomplete until you have opened every subflow called
inside its body and confirmed the subflow itself contains no DML, no Get Records, and no
Apex Action that issues either. Refactor offending subflows to accept collection inputs and
do bulk DML internally — the contract is in `flow/subflows-and-reusability` and
`templates/flow/Subflow_Pattern.md`.

---

## Gotcha 6: Update Records on an empty collection is not an error

**What happens:** Practitioners over-defensively add a Decision before the post-loop Update
Records to skip the DML when the staged collection is empty. The check is dead code — an
Update Records whose `inputReference` is an empty SObject Collection issues no DML and does
not fault.

**UNVERIFIED (2026-09-05):** `FlowRecordUpdate` (`api_meta.txt` L71264–71292) documents
`inputReference`, `inputAssignments`, `filters`, `object`, `connector` and `faultConnector`
but says nothing about empty-input behaviour, and no line in `apexdev.txt` covers it. The
guidance rests on the practitioner-observed behaviour recorded in earlier versions of this
skill, not on the guides. It is cheap to confirm in a scratch org before you rely on it.

**When it occurs:** Defensive over-engineering; cargo-culted from Apex, where `update` on an
empty list is likewise harmless but *insert* of a null is not, so the instinct travels.

**How to avoid:** Drop the empty-check Decision. If you want observability instead of a
guard, use `AssignCount` into a Number variable and assert on it from a `FlowTest` — the
shape in `references/metadata-examples.md` §4.

---

## Gotcha 7: Collection variables append duplicates silently

**What happens:** Assignment with `Add` does not deduplicate — the operator "appends the
value to the end of the collection" (`api_meta.txt` L69800–69802), unconditionally. If a
loop has two branches that both `Add` the current item, the post-loop Update Records
receives the same record twice.

**UNVERIFIED (2026-09-05):** the runtime error text on a duplicate-Id Update
(`Duplicate id in list`) is not present in `api_meta.txt` or `apexdev.txt`; the operator's
append-without-dedup behaviour *is* grounded, the error string is not. Verify the message
against your own org before quoting it in a runbook.

**When it occurs:** Branching loop bodies; loops whose input collection already contains
duplicates (common when the input came from a many-to-many junction join).

**How to avoid:** Gate the `Add` so only one branch can append per iteration, or dedupe
upstream. For a Text-collection accumulator there is no native dedup element — but
`RemoveUncommon` and `RemoveAll` (Gotcha 14) cover set-intersection and set-subtraction
without a loop, and the leftover cases escalate to invocable Apex.

---

## Gotcha 8: `iterationOrder` reverses the collection, it does not sort it

**What happens:** A designer sets `iterationOrder` to `Desc` expecting "highest score
first". They get the source collection backwards. The enum's own wording is positional, not
comparative: `Asc` means "Iterate through the collection in the order the values are listed
(first to last)" and `Desc` means "Iterate through the collection in the reverse order the
values are listed (last to first)" (`api_meta.txt` L70706–70710). No field is named
anywhere in `FlowLoop`, because ordering is not the Loop's job.

If the collection came from a Get Records without a sort, there is no meaningful order to
reverse: `FlowRecordLookup.filters` states "If `sortField` or `sortOrder` isn't specified,
records aren't returned in any particular order" (`api_meta.txt` L71147–71152). That order
can differ between sandboxes, across releases, after an index change, or after a bulk load
reshuffles storage.

**When it occurs:** "Stamp the first matching record" logic; tests that pass in one sandbox
and fail in another; anyone who reads `Asc`/`Desc` as a sort direction because every other
Salesforce enum spelled that way is one.

**How to avoid:** Put the ordering where ordering belongs — `sortField` + `sortOrder` on the
Get Records (API 25.0+, `api_meta.txt` L71209–71226), or a `SortCollectionProcessor` with
`sortOptions` for an in-memory collection. Use `iterationOrder` only to walk an
already-ordered collection backwards, and say so in the element's description.

---

## Gotcha 9: An empty collection goes straight to `noMoreValuesConnector` — and a missing one strands the interview

**What happens:** `nextValueConnector` is "A reference to the next element in the
collection" and `noMoreValuesConnector` is "The element to navigate to when all entries in
the collection have been iterated through" (`api_meta.txt` L70712–70716). An empty
collection has all zero of its entries iterated on the first evaluation, so the loop body
never executes and the interview lands on `noMoreValuesConnector` immediately.

Two consequences fall out. First, every element on the loop body path is dead on the empty
path, including any Assignment that initialises something the post-loop work depends on —
put initialisation *before* the loop, not in it. Second, `noMoreValuesConnector` is not
required by the schema, so a loop that omits it deploys, and the interview has nowhere to go
when the collection runs out.

**When it occurs:** Hand-authored or LLM-generated Flow XML (Flow Builder always wires the
"After Last Item" path); flows whose Get Records legitimately returns nothing on quiet days,
so the defect only surfaces in production at 2 a.m.

**How to avoid:** Always wire `noMoreValuesConnector`, even when it goes straight to the end
of the flow. `scripts/check_flow_loop_element_patterns.py` fails a loop without one.
Initialise counters and accumulators before the loop.

---

## Gotcha 10: `Add` means three different things depending on the target type — and is illegal on sObject

**What happens:** One `FlowAssignmentOperator` value, three behaviours. On a number or
currency variable `Add` "adds the value to the variable"; on a date it "adds the value in
days"; on a string it "appends the value to the end of the string"; on a collection variable
it "appends the value to the end of the collection" (`api_meta.txt` L69787–69804). Two
`assignmentItems` in the same Assignment element can both say `Add` and do arithmetic and
appending respectively — which is exactly what `references/metadata-examples.md` §2 does
with `rankCounter` and `applicationsToStamp`.

The failure mode is the fourth case: `Add` "isn't supported when the `assignToReference`
field is a variable of type `boolean`, `dateTime`, or `sObject`" (`api_meta.txt`
L69805–69806). Trying to `Add` a record to a *record* variable rather than a *record
collection* variable is the most common version of this, and it reads correct.

**When it occurs:** Refactoring a single-record variable into an accumulator and forgetting
to set `isCollection` to `true` on the `FlowVariable` (`api_meta.txt` L72888–72892).

**How to avoid:** Check `isCollection` on the target variable before writing the `Add`. A
second trap sits alongside it: a collection variable *as the value* of an `Add` is
"available in API version 43.0 and later, but only via Metadata API. From Flow Builder, you
can't save an Assignment element that contains a collection variable in the Value column for
the Add operator" (`api_meta.txt` L69798–69804) — hand-written XML that concatenates two
collections deploys, then becomes uneditable in Builder.

---

## Gotcha 11: A Collection Filter's `conditionLogic` decides whether `formula` or `conditions` is even read

**What happens:** `FlowCollectionProcessor.conditionLogic` "Defines how the filtering
conditions are evaluated. Valid values are: `And`, `Or`, custom logic such as
`(1 AND (2 OR 3))`, `Formula`" (`api_meta.txt` L69946–69953). The element carries *both* a
`conditions` array and a `formula` string as separate fields (`api_meta.txt` L69954,
L69957–69960). They are alternative routes to the same output collection, selected by
`conditionLogic`. An element that populates both is ambiguous on its face: a reviewer reads
the `conditions`, the runtime reads the `formula`, and the filter appears to ignore criteria
that are visibly present in the XML.

**When it occurs:** Editing a condition-based filter into a formula-based one and leaving
the old `conditions` behind; LLM-generated XML that fills every documented field.

**How to avoid:** Pick one. `conditionLogic` = `Formula` → `formula` only, and the formula
needs `assignNextValueToReference` to have something to name the current item with
(`api_meta.txt` L69931–69933). `conditionLogic` = `And`/`Or`/custom → `conditions` only.
`scripts/check_flow_loop_element_patterns.py` flags processors carrying both.

---

## Gotcha 12: The Map element's metadata enum is `RecommendationMapCollectionProcessor`

**What happens:** Flow Builder calls the element **Map**. The metadata enum does not.
`collectionProcessorType` accepts exactly three values: `SortCollectionProcessor` (API 50.0+),
`RecommendationMapCollectionProcessor` (API 53.0+), and `FilterCollectionProcessor` (API
53.0+) — `api_meta.txt` L69934–69941. There is no `MapCollectionProcessor`. Hand-authored
XML that guesses the obvious name fails deployment on an enum error that names the field but
not the legal values.

The name is a fossil of the element's Einstein Recommendation Builder origin, and it is the
single most reliable tell that a Flow XML sample was generated rather than retrieved.

Two limitations travel with it. The processor produces a **new** collection of
`outputSObjectType` (`api_meta.txt` L69977–69980) — it does not edit the input collection in
place, so nothing about a Map replaces a post-loop DML. And every `FlowCollectionMapItem`
requires all three of `assignToFieldReference`, `operator` and `value` (`api_meta.txt`
L70161–70172); a mapping with no `assignNextValueToReference` on the processor has no way to
name the source item those `value` expressions read from.

**When it occurs:** Any XML written from memory rather than round-tripped from an org.

**How to avoid:** Retrieve one Builder-authored Map element before hand-authoring another
(`sf project retrieve start --metadata Flow:<name>`). The checker flags an unknown
`collectionProcessorType` and a Map missing `assignNextValueToReference`.

---

## Gotcha 13: `limit` on a collection processor applies *after* the sort, and has no default

**What happens:** `limit` is "The maximum number of records to include in the generated
collection. There's no default value. All items of the collection are kept if it's greater
than the size of the collection. If `sortField` and `sortOrder` are also specified, the
records are sorted before the limit takes effect" (`api_meta.txt` L69961–69967, API 51.0+).
Sort-then-limit is the documented order, so a Sort processor with `limit` really does give
you *top N*. Omit `limit` and there is no implicit cap — the loop downstream inherits the
full collection.

The near-miss is the Get Records `limit`, which is a different field of a different shape:
`FlowElementReferenceOrValue`, not `int`, with "Valid values … between 2 and 20,000.
Supported only when `getFirstRecordOnly` is `false`", available in API version 63.0 and later
(`api_meta.txt` L71180–71187). Writing `<limit>500</limit>` on a `recordLookups` is
malformed; it needs `<limit><numberValue>500.0</numberValue></limit>`.

**When it occurs:** Copying a `limit` between the two element types; assuming an unbounded
Sort is bounded because it "looks like a top-N".

**How to avoid:** Cap at the cheapest layer that can do it — the database first
(`recordLookups` `limit` + `sortField`/`sortOrder`), then the processor, then never the
Loop. Mind the two `limit` shapes.

---

## Gotcha 14: `RemoveAll` and `RemoveUncommon` are set operations that replace whole loops

**What happens:** Practitioners write a Loop-plus-Decision to subtract one collection from
another, or to intersect two. Both are single Assignment operators, available since API 43.0
(`api_meta.txt` L69838–69869):

| Operator | Documented behaviour | Set meaning |
|---|---|---|
| `RemoveAll` | "Removes all instances of the value from the variable… When the value is a collection variable, the operator removes all instances of each item" | difference (A − B) |
| `RemoveUncommon` | "Supported only when `assignToReference` and `value` are **both** collection variables. Keeps items that are in both collections and removes the rest" | intersection (A ∩ B) |
| `RemoveFirst` | "Removes the first instance of the value" | remove one occurrence |
| `RemoveAfterFirst` / `RemoveBeforeFirst` | finds the first instance of the value and removes everything after / before it | truncate |
| `RemovePosition` | "Removes the item at the specified position" — 1-based ("if the collection contains three items… and the value is 2, the second item… is removed") | delete by index |

The traps are asymmetric. `RemoveUncommon` mutates `assignToReference` *in place* and keeps
the intersection — the name reads like it removes the intersection. `RemovePosition` is
1-based and the guide adds "Make sure that the value at run time is a positive integer within
the range of the number of items in the collection variable", so a computed index off by one
is a runtime problem, not a validation one.

**When it occurs:** "Which of these records don't already have a child?" and "which of these
IDs appear in both lists?" — both routinely built as nested loops.

**How to avoid:** Before writing a Loop whose only job is comparing two collections, check
whether one of these operators is the whole answer. They cost one element instead of *n×m*.

---

## Gotcha 15: A counter loop is one `AssignCount`, not a loop

**What happens:** A Loop exists solely to increment a Number variable so a downstream
Decision can branch on "how many". `AssignCount` does it in one element: "Supported only
when the value is a collection variable or the `$Flow.ActiveStages` global variable. Counts
the number of stages or items in the collection, and assigns that number to the variable in
the `assignToReference` field. Corresponds to *equals count* in the user interface. This
operator is available in API version 43.0 and later" (`api_meta.txt` L69826–69830).

The "Supported only when the **value** is a collection" clause is the part people get
backwards: the collection goes in `value`, and the Number variable receiving the count goes
in `assignToReference`.

**When it occurs:** Any flow that reports "N records processed"; validation branches on
collection size; the empty-check Decision from Gotcha 6, rebuilt as a counter.

**How to avoid:** Count with `AssignCount` after the loop, not with an increment inside it.
It also gives a `FlowTest` something to assert on, since test points can only be attached to
`Start` and `Finish` (`api_meta.txt` L74146–74152) and never inside a loop.

---

## Gotcha 16: What you loop over changes how you reference it — `storeOutputAutomatically` vs a record collection variable

**What happens:** `collectionReference` takes a resource name, and the name differs by how
the upstream Get Records stores its output. With `storeOutputAutomatically` = `true`, "the
flow can reference a field by specifying the name of the Get Records element and the record
field, such as `Get_Contacts.AccountId`" (`api_meta.txt` L71229–71239, API 47.0+) — the loop
targets `Get_Applications.records`. With `storeOutputAutomatically` = `false` you must supply
`outputReference`, "the record variable or record collection variable that stores the queried
fields' values" (`api_meta.txt` L71195–71200) — and the loop targets that variable's name
instead.

Three fields interlock and each is documented as conditional on another:
`outputReference`, `outputAssignments` and `assignNullValuesIfNoRecordsFound` are "Supported
only when `storeOutputAutomatically` is `false`"; `getFirstRecordOnly` is "Supported only
when `storeOutputAutomatically` is `true`", and when it is `false`, "what determines whether
one or multiple records are stored is whether `outputReference` specifies a record variable
or a record collection variable" (`api_meta.txt` L71098–71110, L71167–71179, L71190–71200).

The silent failure: a Get Records that stores a **single** record — because
`getFirstRecordOnly` is `true`, or because `outputReference` names a non-collection variable
— still deploys when a Loop points at it, and iterates a one-item collection. Nobody sees a
bug at N=1.

**When it occurs:** Converting a single-record Get Records into a multi-record one and
updating only the filter; `storeOutputAutomatically` is also "Supported only when
`processType` is `Flow` or `AutoLaunchedFlow`", so pasting a flow between process types
breaks the reference shape wholesale.

**How to avoid:** Read the Get Records and the Loop as one unit. If
`storeOutputAutomatically` is `true`, `getFirstRecordOnly` must be `false` and the loop
targets `<ElementName>.records`. If it is `false`, `outputReference` must name a variable
whose `isCollection` is `true`.

---

## Gotcha 17: A Loop cannot fault, so the fault path belongs to its neighbours

**What happens:** Reviewers ask for a fault path "on the loop". There is no such thing —
`FlowLoop` has five fields and `faultConnector` is not among them (`api_meta.txt`
L70698–70716). The elements that *can* fault are the ones on either side:
`FlowRecordLookup.faultConnector` and `FlowRecordUpdate.faultConnector` are both documented
as "Specifies which node to execute if the attempt … results in an error" (`api_meta.txt`
L71114–71117, L71277–71279).

That geometry is what makes an unhandled failure look like it happened at iteration 1: the
loop staged 200 records without incident, and the single post-loop DML failed on one of them,
rolling back everything the interview did.

**When it occurs:** Any collect-then-DML refactor, which is every correct loop in this skill.
Consolidating N in-loop DMLs into one post-loop DML also consolidates N failure points into
one all-or-nothing write.

**How to avoid:** Put `faultConnector` on the Get Records feeding the loop and on the DML
following it, and route both to a logging element that captures `$Flow.FaultMessage`.
`flow/fault-handling` and `templates/flow/FaultPath_Template.md` own the interior of that
path; this skill only insists the two connectors exist.
